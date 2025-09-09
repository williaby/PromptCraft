"""Comprehensive tests for Journey 2: Intelligent Search Interface."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.mcp_integration.mcp_client import Response
from src.ui.journeys.journey2_intelligent_search import Journey2IntelligentSearch


@pytest.fixture
def journey2_instance():
    """Create Journey2IntelligentSearch instance with mocked dependencies."""
    with (
        patch("src.ui.journeys.journey2_intelligent_search.OpenRouterClient") as mock_openrouter,
        patch("src.ui.journeys.journey2_intelligent_search.ZenStdioMCPClient") as mock_zen,
    ):

        instance = Journey2IntelligentSearch()
        instance.openrouter_client = mock_openrouter.return_value
        instance.zen_client = mock_zen.return_value

        # Mock logging methods from LoggerMixin
        instance.log_info = Mock()
        instance.log_warning = Mock()
        instance.log_error = Mock()
        instance.logger = Mock()

        return instance


@pytest.fixture
def sample_response():
    """Create a sample response object."""
    return Response(
        agent_id="test_agent",
        content="This is a test response from the AI model.",
        metadata={"model": "test-model", "cost": 0.001},
        confidence=0.95,
        processing_time=1.5,
        success=True,
        error_message=None,
    )


@pytest.fixture
def sample_workflow_step():
    """Create a sample workflow step."""
    return {
        "step_id": "journey2_execute",
        "agent_id": "journey2_search",
        "input_data": {
            "query": "Test enhanced prompt",
            "task_type": "general",
            "allow_premium": True,
            "user_tier": "full",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "timeout_seconds": 30.0,
    }


class TestJourney2IntelligentSearch:
    """Test suite for Journey 2 intelligent search functionality."""

    def test_initialization(self, journey2_instance):
        """Test proper initialization of Journey2IntelligentSearch."""
        assert journey2_instance.openrouter_client is not None
        assert journey2_instance.zen_client is not None
        assert journey2_instance.mcp_enabled is True
        assert journey2_instance._routing_metadata == {}

    @pytest.mark.asyncio
    async def test_execute_with_intelligent_routing_zen_success(
        self,
        journey2_instance,
        sample_response,
        sample_workflow_step,
    ):
        """Test successful zen MCP routing."""
        # Mock zen client responses
        journey2_instance.zen_client.connect = AsyncMock(return_value=True)
        journey2_instance.zen_client.disconnect = AsyncMock()
        journey2_instance.zen_client.get_model_recommendations = AsyncMock(
            return_value=Mock(
                primary_recommendation=Mock(model_name="gpt-4"),
                task_type="general",
                complexity_level="medium",
            ),
        )
        journey2_instance.zen_client.execute_with_routing = AsyncMock(
            return_value={
                "success": True,
                "result": {
                    "content": "Zen routing response",
                    "routing_metadata": {"confidence": 0.9, "cost_optimized": True},
                    "response_time": 1.2,
                    "model_used": "gpt-4",
                },
            },
        )

        enhanced_prompt = "Test enhanced prompt"
        user_tier = "full"

        responses, routing_metadata = await journey2_instance._execute_with_intelligent_routing(
            enhanced_prompt,
            user_tier,
            sample_workflow_step,
        )

        # Verify zen routing success
        assert routing_metadata["zen_success"] is True
        assert routing_metadata["routing_method"] == "zen_mcp"
        assert routing_metadata["model_used"] == "gpt-4"
        assert routing_metadata["cost_optimized"] is True
        assert len(responses) == 1
        assert responses[0].content == "Zen routing response"
        assert responses[0].agent_id == "zen_routing"

        # Verify zen client was called
        journey2_instance.zen_client.connect.assert_called_once()
        journey2_instance.zen_client.get_model_recommendations.assert_called_once_with(enhanced_prompt)
        journey2_instance.zen_client.execute_with_routing.assert_called_once_with(enhanced_prompt)
        journey2_instance.zen_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_intelligent_routing_fallback_to_openrouter(
        self,
        journey2_instance,
        sample_response,
        sample_workflow_step,
    ):
        """Test fallback to OpenRouter when zen MCP fails."""
        # Mock zen client failure
        journey2_instance.zen_client.connect = AsyncMock(return_value=False)
        journey2_instance.zen_client.disconnect = AsyncMock()

        # Mock successful OpenRouter fallback
        journey2_instance.openrouter_client.connect = AsyncMock()
        journey2_instance.openrouter_client.orchestrate_agents = AsyncMock(return_value=[sample_response])

        enhanced_prompt = "Test enhanced prompt"
        user_tier = "full"

        responses, routing_metadata = await journey2_instance._execute_with_intelligent_routing(
            enhanced_prompt,
            user_tier,
            sample_workflow_step,
        )

        # Verify fallback was used
        assert routing_metadata["zen_success"] is False
        assert routing_metadata["fallback_used"] is True
        assert routing_metadata["routing_method"] == "openrouter_fallback"
        assert routing_metadata["error_details"] == "Connection failed"
        assert len(responses) == 1
        assert responses[0] == sample_response

        # Verify OpenRouter was called
        journey2_instance.openrouter_client.connect.assert_called_once()
        journey2_instance.openrouter_client.orchestrate_agents.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_intelligent_routing_both_fail(self, journey2_instance, sample_workflow_step):
        """Test when both zen MCP and OpenRouter fail."""
        # Mock zen client failure
        journey2_instance.zen_client.connect = AsyncMock(return_value=False)
        journey2_instance.zen_client.disconnect = AsyncMock()

        # Mock OpenRouter failure
        journey2_instance.openrouter_client.connect = AsyncMock(side_effect=Exception("OpenRouter connection failed"))

        enhanced_prompt = "Test enhanced prompt"
        user_tier = "full"

        with pytest.raises(Exception):
            await journey2_instance._execute_with_intelligent_routing(enhanced_prompt, user_tier, sample_workflow_step)

    @pytest.mark.asyncio
    async def test_execute_prompt_success(self, journey2_instance, sample_response):
        """Test successful prompt execution."""
        # Mock the intelligent routing method
        routing_metadata = {
            "zen_success": True,
            "routing_method": "zen_mcp",
            "model_used": "gpt-4",
            "cost_optimized": True,
            "routing_time_ms": 150.0,
        }

        journey2_instance._execute_with_intelligent_routing = AsyncMock(
            return_value=([sample_response], routing_metadata),
        )

        enhanced_prompt = "Test enhanced prompt"
        model_mode = "premium"
        custom_model = ""
        temperature = 0.7
        max_tokens = 2000
        user_tier = "full"

        response_content, model_attribution, execution_stats, error_message = await journey2_instance.execute_prompt(
            enhanced_prompt,
            model_mode,
            custom_model,
            temperature,
            max_tokens,
            user_tier,
        )

        # Verify successful execution
        assert response_content == sample_response.content
        assert error_message == ""
        assert "zen MCP" in model_attribution
        assert "gpt-4" in model_attribution
        assert "📊 Execution Statistics" in execution_stats
        assert "zen MCP Routing:</strong> Successful" in execution_stats

    @pytest.mark.asyncio
    async def test_execute_prompt_empty_prompt(self, journey2_instance):
        """Test execution with empty prompt."""
        response_content, model_attribution, execution_stats, error_message = await journey2_instance.execute_prompt(
            "",
            "standard",
            "",
            0.7,
            2000,
            "full",
        )

        assert response_content == ""
        assert model_attribution == ""
        assert execution_stats == ""
        assert "No prompt provided" in error_message

    def test_select_model_limited_user_free_mode(self, journey2_instance):
        """Test model selection for limited user in free mode."""
        model = journey2_instance._select_model("free_mode", "", "limited")
        assert model == "deepseek/deepseek-chat:free"

    def test_select_model_limited_user_premium_attempt(self, journey2_instance):
        """Test limited user attempting to use premium model."""
        with patch.object(journey2_instance.logger, "warning") as mock_warning:
            model = journey2_instance._select_model("premium", "", "limited")
            assert model == "deepseek/deepseek-chat:free"
            mock_warning.assert_called_once()

    def test_select_model_full_user_custom(self, journey2_instance):
        """Test full user selecting custom model."""
        custom_model = "anthropic/claude-3-5-sonnet-20241022"
        model = journey2_instance._select_model("custom", custom_model, "full")
        assert model == custom_model

    def test_select_model_admin_user_premium(self, journey2_instance):
        """Test admin user selecting premium model."""
        model = journey2_instance._select_model("premium", "", "admin")
        assert model == "anthropic/claude-3-5-sonnet-20241022"

    def test_calculate_cost_free_model(self, journey2_instance):
        """Test cost calculation for free model."""
        cost = journey2_instance._calculate_cost("deepseek/deepseek-chat:free", 1000, 1000)
        assert cost == 0.0

    def test_calculate_cost_paid_model(self, journey2_instance):
        """Test cost calculation for paid model."""
        cost = journey2_instance._calculate_cost("openai/gpt-4o-mini", 1000, 1000)
        expected_tokens = 2000 / 4  # 4 chars per token
        expected_cost = (expected_tokens / 1000) * 0.00015
        assert cost == expected_cost

    def test_calculate_cost_unknown_model(self, journey2_instance):
        """Test cost calculation for unknown model uses default."""
        cost = journey2_instance._calculate_cost("unknown/model", 1000, 1000)
        expected_tokens = 2000 / 4
        expected_cost = (expected_tokens / 1000) * 0.002  # Default cost
        assert cost == expected_cost

    def test_create_transfer_from_journey1(self, journey2_instance):
        """Test creation of transfer object from Journey 1."""
        enhanced_prompt = "Test enhanced prompt"
        create_breakdown = {
            "context": "Test context",
            "request": "Test request",
            "examples": "Test examples",
            "augmentations": "Test augmentations",
            "tone_format": "Test tone",
            "evaluation": "Test evaluation",
        }

        with patch("time.time", return_value=1234567890):
            transfer = journey2_instance.create_transfer_from_journey1(enhanced_prompt, create_breakdown)

        assert transfer["enhanced_prompt"] == enhanced_prompt
        assert transfer["context"] == create_breakdown["context"]
        assert transfer["source"] == "journey1_smart_templates"
        assert transfer["transfer_timestamp"] == "1234567890"

    def test_format_response_for_display_normal(self, journey2_instance):
        """Test response formatting for normal-length response."""
        content = "This is a normal response."
        formatted = journey2_instance.format_response_for_display(content)
        assert formatted == content

    def test_format_response_for_display_empty(self, journey2_instance):
        """Test response formatting for empty response."""
        formatted = journey2_instance.format_response_for_display("")
        assert formatted == "No response content available."

    def test_format_response_for_display_truncation(self, journey2_instance):
        """Test response formatting with truncation."""
        # Create content longer than MAX_RESPONSE_LENGTH (10000)
        long_content = "A" * 11000
        formatted = journey2_instance.format_response_for_display(long_content)
        assert len(formatted.split("\n")[0]) == 10000  # First line should be truncated to MAX_RESPONSE_LENGTH
        assert "Response truncated for display" in formatted
        assert "11000 characters" in formatted

    def test_extract_key_insights_normal(self, journey2_instance):
        """Test key insights extraction from normal response."""
        content = (
            "This is a substantial line with enough content to be extracted as an insight.\nThis is a second line."
        )
        insights = journey2_instance.extract_key_insights(content)
        assert "substantial line with enough content" in insights

    def test_extract_key_insights_short_response(self, journey2_instance):
        """Test key insights extraction from short response."""
        content = "Short"
        insights = journey2_instance.extract_key_insights(content)
        assert insights == "Response too short for insight extraction."

    def test_extract_key_insights_no_substantial_lines(self, journey2_instance):
        """Test key insights extraction when no substantial lines exist."""
        content = "Short\nlines\nonly"
        insights = journey2_instance.extract_key_insights(content)
        # All lines are too short (< 50 chars), so falls back to first few lines
        # The content is too short (< 100 chars), so it returns the "too short" message
        assert insights == "Response too short for insight extraction."

    def test_extract_key_insights_truncation(self, journey2_instance):
        """Test key insights extraction with truncation."""
        # Create a substantial line longer than RESPONSE_PREVIEW_LENGTH (500)
        long_line = "A" * 600
        insights = journey2_instance.extract_key_insights(long_line)
        assert len(insights) == 503  # 500 chars + "..."
        assert insights.endswith("...")

    def test_validate_prompt_for_execution_valid(self, journey2_instance):
        """Test validation of valid prompt."""
        valid_prompt = "This is a valid prompt with sufficient content."
        is_valid, message = journey2_instance.validate_prompt_for_execution(valid_prompt)
        assert is_valid is True
        assert message == "Prompt is valid for execution."

    def test_validate_prompt_for_execution_empty(self, journey2_instance):
        """Test validation of empty prompt."""
        is_valid, message = journey2_instance.validate_prompt_for_execution("")
        assert is_valid is False
        assert "empty" in message.lower()

    def test_validate_prompt_for_execution_too_long(self, journey2_instance):
        """Test validation of overly long prompt."""
        long_prompt = "A" * 50001  # Exceed 50K character limit
        is_valid, message = journey2_instance.validate_prompt_for_execution(long_prompt)
        assert is_valid is False
        assert "too long" in message.lower()
        assert "50,000" in message

    def test_validate_prompt_for_execution_too_short(self, journey2_instance):
        """Test validation of overly short prompt."""
        short_prompt = "Hi"
        is_valid, message = journey2_instance.validate_prompt_for_execution(short_prompt)
        assert is_valid is False
        assert "too short" in message.lower()

    def test_get_available_models_for_tier_limited(self, journey2_instance):
        """Test available models for limited tier."""
        models = journey2_instance.get_available_models_for_tier("limited")
        assert len(models) == 2
        model_ids = [model[1] for model in models]
        assert "deepseek/deepseek-chat:free" in model_ids
        assert "meta-llama/llama-3.3-70b-instruct:free" in model_ids
        # Verify no paid models
        assert all(":free" in model_id for model_id in model_ids)

    def test_get_available_models_for_tier_full(self, journey2_instance):
        """Test available models for full tier."""
        models = journey2_instance.get_available_models_for_tier("full")
        assert len(models) == 4
        model_ids = [model[1] for model in models]
        assert "deepseek/deepseek-chat:free" in model_ids
        assert "openai/gpt-4o-mini" in model_ids
        assert "anthropic/claude-3-5-sonnet-20241022" in model_ids

    def test_get_available_models_for_tier_admin(self, journey2_instance):
        """Test available models for admin tier."""
        models = journey2_instance.get_available_models_for_tier("admin")
        assert len(models) == 5
        model_ids = [model[1] for model in models]
        assert "deepseek/deepseek-chat:free" in model_ids
        assert "openai/gpt-4o-mini" in model_ids
        assert "anthropic/claude-3-5-sonnet-20241022" in model_ids
        assert "openai/gpt-4o" in model_ids

    def test_create_execution_interface_no_transfer_data(self, journey2_instance):
        """Test creation of execution interface without transfer data."""
        components = journey2_instance.create_execution_interface("full", None)

        # Verify all required components are present
        required_components = [
            "prompt_input",
            "model_selector",
            "temperature",
            "max_tokens",
            "execute_button",
            "clear_button",
            "response_output",
            "model_attribution",
            "execution_stats",
            "error_display",
        ]
        for component in required_components:
            assert component in components

        # Verify empty prompt input when no transfer data
        assert components["prompt_input"].value == ""

    def test_create_execution_interface_with_transfer_data(self, journey2_instance):
        """Test creation of execution interface with transfer data."""
        transfer_data = {"enhanced_prompt": "Test prompt from Journey 1"}
        components = journey2_instance.create_execution_interface("limited", transfer_data)

        # Verify prompt input is pre-filled
        assert components["prompt_input"].value == "Test prompt from Journey 1"

        # Verify limited tier model selection
        assert "Limited Tier" in components["model_selector"].label

    def test_create_execution_interface_model_choices_by_tier(self, journey2_instance):
        """Test model choices are properly set based on user tier."""
        # Test limited tier
        limited_components = journey2_instance.create_execution_interface("limited", None)
        limited_choices = limited_components["model_selector"].choices
        assert len(limited_choices) == 2
        assert all(":free" in choice[1] for choice in limited_choices)

        # Test full tier
        full_components = journey2_instance.create_execution_interface("full", None)
        full_choices = full_components["model_selector"].choices
        assert len(full_choices) == 4

        # Test admin tier
        admin_components = journey2_instance.create_execution_interface("admin", None)
        admin_choices = admin_components["model_selector"].choices
        assert len(admin_choices) == 5

    @pytest.mark.asyncio
    async def test_zen_client_cleanup_on_exception(self, journey2_instance, sample_workflow_step):
        """Test that zen client is properly cleaned up when exceptions occur."""
        # Mock zen client that raises exception during execution
        journey2_instance.zen_client.connect = AsyncMock(return_value=True)
        journey2_instance.zen_client.get_model_recommendations = AsyncMock(side_effect=Exception("Test exception"))
        journey2_instance.zen_client.disconnect = AsyncMock()

        # Mock OpenRouter fallback
        journey2_instance.openrouter_client.connect = AsyncMock()
        journey2_instance.openrouter_client.orchestrate_agents = AsyncMock(return_value=[])

        enhanced_prompt = "Test prompt"
        user_tier = "full"

        # Should raise exception when both zen and OpenRouter fail
        with pytest.raises(Exception):
            await journey2_instance._execute_with_intelligent_routing(enhanced_prompt, user_tier, sample_workflow_step)

        # Verify zen client disconnect was called during cleanup
        journey2_instance.zen_client.disconnect.assert_called()

    def test_routing_metadata_storage(self, journey2_instance):
        """Test that routing metadata is properly stored."""
        # Initially empty
        assert journey2_instance._routing_metadata == {}

        # Set some metadata
        test_metadata = {"routing_method": "zen_mcp", "zen_success": True}
        journey2_instance._routing_metadata = test_metadata

        # Verify it's stored
        assert journey2_instance._routing_metadata == test_metadata

    @pytest.mark.asyncio
    async def test_mcp_disabled_skips_zen_routing(self, journey2_instance, sample_response, sample_workflow_step):
        """Test that zen routing is skipped when MCP is disabled."""
        # Disable MCP routing
        journey2_instance.mcp_enabled = False

        # Mock successful OpenRouter fallback
        journey2_instance.openrouter_client.connect = AsyncMock()
        journey2_instance.openrouter_client.orchestrate_agents = AsyncMock(return_value=[sample_response])

        enhanced_prompt = "Test prompt"
        user_tier = "full"

        responses, routing_metadata = await journey2_instance._execute_with_intelligent_routing(
            enhanced_prompt,
            user_tier,
            sample_workflow_step,
        )

        # Verify zen was not attempted
        assert routing_metadata["zen_attempted"] is False
        assert routing_metadata["fallback_used"] is True
        assert routing_metadata["routing_method"] == "openrouter_fallback"

        # Verify zen client methods were not called
        journey2_instance.zen_client.connect.assert_not_called()
