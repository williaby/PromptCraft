"""Unit tests for Journey2IntelligentSearch."""

from unittest.mock import AsyncMock, patch

import pytest

from src.ui.journeys.journey2_intelligent_search import Journey2IntelligentSearch


@pytest.fixture
def journey2():
    """Create a Journey2IntelligentSearch instance."""
    with patch("src.ui.journeys.journey2_intelligent_search.OpenRouterClient"):
        return Journey2IntelligentSearch()


class TestJourney2IntelligentSearch:
    """Test cases for Journey2IntelligentSearch class."""

    def test_init(self):
        """Test Journey2IntelligentSearch initialization."""
        with patch("src.ui.journeys.journey2_intelligent_search.OpenRouterClient") as mock_client:
            journey = Journey2IntelligentSearch()
            assert journey.openrouter_client is not None
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_prompt_basic(self, journey2):
        """Test basic prompt execution."""
        # Mock the orchestrate_agents method
        from src.mcp_integration.models import WorkflowResult

        mock_response = WorkflowResult(step_id="test", success=True, content="Test response", confidence=0.95)
        journey2.openrouter_client.connect = AsyncMock()
        journey2.openrouter_client.orchestrate_agents = AsyncMock(return_value=[mock_response])

        result = await journey2.execute_prompt(
            enhanced_prompt="Test prompt",
            model_mode="auto",
            custom_model="",
            temperature=0.7,
            max_tokens=1000,
            user_tier="full",
        )

        assert len(result) == 4  # Should return tuple of 4 elements
        assert "Test response" in result[0]  # response_content

    @pytest.mark.asyncio
    async def test_execute_prompt_error_handling(self, journey2):
        """Test error handling in prompt execution."""
        journey2.openrouter_client.connect = AsyncMock(side_effect=Exception("API Error"))

        result = await journey2.execute_prompt(
            enhanced_prompt="Test prompt",
            model_mode="auto",
            custom_model="",
            temperature=0.7,
            max_tokens=1000,
            user_tier="full",
        )

        assert len(result) == 4  # Should return tuple of 4 elements
        assert "Error" in result[3]  # error message should be in last element

    @pytest.mark.asyncio
    async def test_execute_prompt_empty_prompt(self, journey2):
        """Test execution with empty prompt."""
        result = await journey2.execute_prompt(
            enhanced_prompt="",
            model_mode="auto",
            custom_model="",
            temperature=0.7,
            max_tokens=1000,
            user_tier="full",
        )

        assert len(result) == 4
        assert "No prompt provided" in result[3]  # error message

    def test_select_model(self, journey2):
        """Test model selection logic."""
        result = journey2._select_model("auto", "", "full")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_cost(self, journey2):
        """Test cost calculation."""
        cost = journey2._calculate_cost("test-model", 100, 200)
        assert isinstance(cost, float)
        assert cost >= 0

    def test_create_transfer_from_journey1(self, journey2):
        """Test transfer from journey 1."""
        result = journey2.create_transfer_from_journey1("Test prompt", {"topic": "test", "audience": "general"})
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_format_response_for_display(self, journey2):
        """Test response formatting for display."""
        formatted = journey2.format_response_for_display("Test response content")
        assert isinstance(formatted, str)
        assert "Test response content" in formatted

    def test_extract_key_insights(self, journey2):
        """Test key insight extraction."""
        insights = journey2.extract_key_insights("This is a test response with key points.")
        assert isinstance(insights, str)

    def test_validate_prompt_for_execution(self, journey2):
        """Test prompt validation."""
        is_valid, message = journey2.validate_prompt_for_execution("Valid test prompt")
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)

    def test_get_available_models_for_tier(self, journey2):
        """Test getting available models for tier."""
        models = journey2.get_available_models_for_tier("full")
        assert isinstance(models, list)

        # Test limited tier
        models_limited = journey2.get_available_models_for_tier("limited")
        assert isinstance(models_limited, list)

    def test_create_execution_interface(self, journey2):
        """Test execution interface creation."""
        with (
            patch("gradio.Tab"),
            patch("gradio.Row"),
            patch("gradio.Column"),
            patch("gradio.Textbox"),
            patch("gradio.Dropdown"),
            patch("gradio.Button"),
            patch("gradio.Slider"),
            patch("gradio.Number"),
            patch("gradio.HTML"),
            patch("gradio.Markdown"),
        ):

            interface = journey2.create_execution_interface()
            assert interface is not None
