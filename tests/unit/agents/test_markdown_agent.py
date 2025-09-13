"""
Comprehensive tests for MarkdownAgent functionality.

Tests cover initialization, prompt building, model calling, error handling,
and all public methods to achieve 90%+ coverage.
"""

from unittest.mock import AsyncMock

import pytest

from src.agents.markdown_agent import MarkdownAgent
from src.agents.models import AgentInput, AgentOutput


class TestMarkdownAgent:
    """Test MarkdownAgent implementation."""

    def test_initialization_basic(self):
        """Test basic MarkdownAgent initialization."""
        agent = MarkdownAgent(
            agent_id="test_agent",
            definition="Test agent definition",
            model="sonnet",
            tools=["tool1", "tool2"],
            context="Test context",
            config={"param1": "value1"},
        )

        assert agent.agent_id == "test_agent"
        assert agent.definition == "Test agent definition"
        assert agent.model == "sonnet"
        assert agent.context == "Test context"
        assert agent.config.get("tools") == ["tool1", "tool2"]

    def test_initialization_with_empty_config(self):
        """Test initialization with empty config."""
        agent = MarkdownAgent(
            agent_id="minimal_agent",
            definition="Minimal definition",
            model="haiku",
            tools=[],
            context="",
            config={},
        )

        assert agent.agent_id == "minimal_agent"
        assert agent.definition == "Minimal definition"
        assert agent.model == "haiku"
        assert agent.context == ""
        assert agent.config.get("tools") == []

    def test_initialization_with_complex_config(self):
        """Test initialization with complex configuration."""
        complex_config = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "custom_setting": "value",
        }

        agent = MarkdownAgent(
            agent_id="complex_agent",
            definition="Complex agent with settings",
            model="opus",
            tools=["read", "write", "search"],
            context="Detailed context information",
            config=complex_config,
        )

        assert agent.agent_id == "complex_agent"
        assert agent.definition == "Complex agent with settings"
        assert agent.model == "opus"
        assert agent.context == "Detailed context information"
        assert agent.config.get("tools") == ["read", "write", "search"]

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution using BaseAgent interface."""
        agent = MarkdownAgent(
            agent_id="execute_agent",
            definition="Agent for execution testing",
            model="sonnet",
            tools=["tool1"],
            context="Execute context",
            config={},
        )

        # Mock the _call_model method
        agent._call_model = AsyncMock(return_value="Execution completed successfully")

        agent_input = AgentInput(content="Execute this task")
        result = await agent.execute(agent_input)

        assert isinstance(result, AgentOutput)
        assert result.content == "Execution completed successfully"
        assert result.metadata["success"] is True
        assert result.metadata["agent_id"] == "execute_agent"
        assert result.metadata["model_used"] == "sonnet"
        assert result.confidence == 1.0
        assert result.agent_id == "execute_agent"

    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        """Test execution with additional context."""
        agent = MarkdownAgent(
            agent_id="context_execute_agent",
            definition="Agent for context testing",
            model="haiku",
            tools=[],
            context="Base context",
            config={},
        )

        agent._call_model = AsyncMock(return_value="Context processed")

        agent_input = AgentInput(
            content="Process with context",
            context={"additional": "context data"},
        )
        result = await agent.execute(agent_input)

        assert result.content == "Context processed"
        assert result.metadata["success"] is True

        # Verify _call_model was called with additional context
        agent._call_model.assert_called_once()
        call_args = agent._call_model.call_args
        call_args[0][0]
        input_data = call_args[0][1]

        assert "additional_context" in input_data
        assert str(agent_input.context) in input_data["additional_context"]

    @pytest.mark.asyncio
    async def test_execute_error_handling(self):
        """Test error handling in execute method."""
        agent = MarkdownAgent(
            agent_id="error_execute_agent",
            definition="Agent for error testing",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Mock _call_model to raise an exception
        agent._call_model = AsyncMock(side_effect=Exception("Model call failed"))

        agent_input = AgentInput(content="This will fail")
        result = await agent.execute(agent_input)

        assert isinstance(result, AgentOutput)
        assert "Error: Model call failed" in result.content
        assert result.metadata["success"] is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_execute_internal_exception(self):
        """Test exception handling in execute method itself."""
        agent = MarkdownAgent(
            agent_id="exception_agent",
            definition="Agent for exception testing",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Mock _process_internal to raise an exception
        agent._process_internal = AsyncMock(side_effect=Exception("Internal error"))

        agent_input = AgentInput(content="This will cause internal error")
        result = await agent.execute(agent_input)

        assert isinstance(result, AgentOutput)
        assert "Agent execution failed: Internal error" in result.content
        assert result.metadata["success"] is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_process_success_with_task(self):
        """Test successful processing with task input."""
        agent = MarkdownAgent(
            agent_id="task_agent",
            definition="Agent for task processing",
            model="sonnet",
            tools=["tool1"],
            context="Task context",
            config={},
        )

        # Mock the _call_model method
        agent._call_model = AsyncMock(return_value="Task completed successfully")

        input_data = {"task": "Analyze this data"}
        result = await agent.process(input_data)

        assert result["success"] is True
        assert result["response"] == "Task completed successfully"
        assert result["agent_id"] == "task_agent"
        assert result["model_used"] == "sonnet"

        # Verify _call_model was called with correct prompt
        agent._call_model.assert_called_once()
        call_args = agent._call_model.call_args
        prompt = call_args[0][0]

        assert "# Context" in prompt
        assert "Task context" in prompt
        assert "# Agent Instructions" in prompt
        assert "Agent for task processing" in prompt
        assert "# Task" in prompt
        assert "Analyze this data" in prompt

    @pytest.mark.asyncio
    async def test_process_success_with_query(self):
        """Test successful processing with query input."""
        agent = MarkdownAgent(
            agent_id="query_agent",
            definition="Agent for query processing",
            model="haiku",
            tools=[],
            context="Query context",
            config={},
        )

        agent._call_model = AsyncMock(return_value="Query answered")

        input_data = {"query": "What is the weather?"}
        result = await agent.process(input_data)

        assert result["success"] is True
        assert result["response"] == "Query answered"
        assert result["agent_id"] == "query_agent"
        assert result["model_used"] == "haiku"

        # Verify prompt structure
        call_args = agent._call_model.call_args
        prompt = call_args[0][0]
        assert "# Query" in prompt
        assert "What is the weather?" in prompt

    @pytest.mark.asyncio
    async def test_process_success_with_prompt(self):
        """Test successful processing with prompt input."""
        agent = MarkdownAgent(
            agent_id="prompt_agent",
            definition="Agent for prompt processing",
            model="opus",
            tools=["search"],
            context="Prompt context",
            config={},
        )

        agent._call_model = AsyncMock(return_value="Prompt processed")

        input_data = {"prompt": "Generate a summary"}
        result = await agent.process(input_data)

        assert result["success"] is True
        assert result["response"] == "Prompt processed"

        # Verify prompt structure
        call_args = agent._call_model.call_args
        prompt = call_args[0][0]
        assert "# Request" in prompt
        assert "Generate a summary" in prompt

    @pytest.mark.asyncio
    async def test_process_with_additional_context(self):
        """Test processing with additional context in input."""
        agent = MarkdownAgent(
            agent_id="context_agent",
            definition="Agent with additional context",
            model="sonnet",
            tools=[],
            context="Base context",
            config={},
        )

        agent._call_model = AsyncMock(return_value="Context processed")

        input_data = {
            "task": "Complete this task",
            "additional_context": "Extra information for context",
        }
        result = await agent.process(input_data)

        assert result["success"] is True

        # Verify additional context is included in prompt
        call_args = agent._call_model.call_args
        prompt = call_args[0][0]
        assert "# Additional Context" in prompt
        assert "Extra information for context" in prompt

    @pytest.mark.asyncio
    async def test_process_error_handling(self):
        """Test error handling during processing."""
        agent = MarkdownAgent(
            agent_id="error_agent",
            definition="Agent for error testing",
            model="sonnet",
            tools=[],
            context="Error context",
            config={},
        )

        # Mock _call_model to raise an exception
        agent._call_model = AsyncMock(side_effect=Exception("Model call failed"))

        input_data = {"task": "This will fail"}
        result = await agent.process(input_data)

        assert result["success"] is False
        assert result["error"] == "Model call failed"
        assert result["agent_id"] == "error_agent"
        assert "response" not in result

    def test_build_prompt_with_context(self):
        """Test prompt building with context."""
        agent = MarkdownAgent(
            agent_id="build_agent",
            definition="Test definition",
            model="sonnet",
            tools=[],
            context="Test context",
            config={},
        )

        input_data = {"task": "Test task"}
        prompt = agent._build_prompt(input_data)

        assert "# Context\nTest context\n" in prompt
        assert "# Agent Instructions\nTest definition\n" in prompt
        assert "# Task\nTest task" in prompt

    def test_build_prompt_without_context(self):
        """Test prompt building without context."""
        agent = MarkdownAgent(
            agent_id="no_context_agent",
            definition="No context definition",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        input_data = {"query": "Test query"}
        prompt = agent._build_prompt(input_data)

        assert "# Context" not in prompt
        assert "# Agent Instructions\nNo context definition\n" in prompt
        assert "# Query\nTest query" in prompt

    def test_build_prompt_with_none_context(self):
        """Test prompt building with None context."""
        agent = MarkdownAgent(
            agent_id="none_context_agent",
            definition="None context definition",
            model="sonnet",
            tools=[],
            context=None,
            config={},
        )

        input_data = {"prompt": "Test prompt"}
        prompt = agent._build_prompt(input_data)

        assert "# Context" not in prompt
        assert "# Request\nTest prompt" in prompt

    def test_build_prompt_no_input_fields(self):
        """Test prompt building with no recognized input fields."""
        agent = MarkdownAgent(
            agent_id="no_field_agent",
            definition="No field definition",
            model="sonnet",
            tools=[],
            context="Context",
            config={},
        )

        input_data = {"unknown_field": "Unknown value"}
        prompt = agent._build_prompt(input_data)

        # Should still include context and definition
        assert "# Context\nContext\n" in prompt
        assert "# Agent Instructions\nNo field definition\n" in prompt
        # But no task/query/request section
        assert "# Task" not in prompt
        assert "# Query" not in prompt
        assert "# Request" not in prompt

    @pytest.mark.asyncio
    async def test_call_model_placeholder(self):
        """Test the _call_model placeholder implementation."""
        agent = MarkdownAgent(
            agent_id="model_agent",
            definition="Model test agent",
            model="sonnet",
            tools=["tool1"],
            context="Model context",
            config={},
        )

        input_data = {"task": "Test model call"}
        prompt = "Test prompt"

        # Test the placeholder implementation
        result = await agent._call_model(prompt, input_data)

        expected = "[MarkdownAgent model_agent] Processed with sonnet: Test model call"
        assert result == expected

    def test_get_capabilities(self):
        """Test get_capabilities method."""
        agent = MarkdownAgent(
            agent_id="capability_agent",
            definition="Capability test agent",
            model="opus",
            tools=["read", "write"],
            context="Capability context",
            config={},
        )

        capabilities = agent.get_capabilities()

        expected = {
            "agent_id": "capability_agent",
            "type": "markdown",
            "model": "opus",
            "tools": ["read", "write"],
            "description": "Dynamically created agent from markdown definition",
            "supports_streaming": False,
            "supports_tools": True,
        }

        assert capabilities == expected

    def test_get_capabilities_no_tools(self):
        """Test get_capabilities with no tools."""
        agent = MarkdownAgent(
            agent_id="no_tools_agent",
            definition="No tools agent",
            model="haiku",
            tools=[],
            context="",
            config={},
        )

        capabilities = agent.get_capabilities()

        assert capabilities["supports_tools"] is False
        assert capabilities["tools"] == []

    @pytest.mark.asyncio
    async def test_validate_input_with_task(self):
        """Test input validation with task field."""
        agent = MarkdownAgent(
            agent_id="validate_agent",
            definition="Validation test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Valid input with task
        input_data = {"task": "Test task"}
        result = await agent.validate_input(input_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_input_with_query(self):
        """Test input validation with query field."""
        agent = MarkdownAgent(
            agent_id="validate_agent",
            definition="Validation test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Valid input with query
        input_data = {"query": "Test query"}
        result = await agent.validate_input(input_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_input_with_prompt(self):
        """Test input validation with prompt field."""
        agent = MarkdownAgent(
            agent_id="validate_agent",
            definition="Validation test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Valid input with prompt
        input_data = {"prompt": "Test prompt"}
        result = await agent.validate_input(input_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_input_invalid(self):
        """Test input validation with invalid input."""
        agent = MarkdownAgent(
            agent_id="validate_agent",
            definition="Validation test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Invalid input without required fields
        input_data = {"unknown": "value"}
        result = await agent.validate_input(input_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_input_empty(self):
        """Test input validation with empty input."""
        agent = MarkdownAgent(
            agent_id="validate_agent",
            definition="Validation test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Empty input
        input_data = {}
        result = await agent.validate_input(input_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_input_multiple_fields(self):
        """Test input validation with multiple valid fields."""
        agent = MarkdownAgent(
            agent_id="validate_agent",
            definition="Validation test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        # Input with multiple valid fields
        input_data = {"task": "Test task", "query": "Test query"}
        result = await agent.validate_input(input_data)
        assert result is True

    def test_str_representation(self):
        """Test string representation of MarkdownAgent."""
        agent = MarkdownAgent(
            agent_id="string_agent",
            definition="String test agent",
            model="sonnet",
            tools=[],
            context="",
            config={},
        )

        str_repr = str(agent)
        expected = "MarkdownAgent(id=string_agent, model=sonnet)"
        assert str_repr == expected

    def test_str_representation_different_models(self):
        """Test string representation with different models."""
        models = ["opus", "sonnet", "haiku"]

        for model in models:
            agent = MarkdownAgent(
                agent_id=f"agent_{model}",
                definition=f"Agent using {model}",
                model=model,
                tools=[],
                context="",
                config={},
            )

            str_repr = str(agent)
            expected = f"MarkdownAgent(id=agent_{model}, model={model})"
            assert str_repr == expected

    @pytest.mark.asyncio
    async def test_process_all_input_types_sequentially(self):
        """Test processing different input types in sequence."""
        agent = MarkdownAgent(
            agent_id="sequential_agent",
            definition="Sequential processing agent",
            model="sonnet",
            tools=["tool1"],
            context="Sequential context",
            config={},
        )

        agent._call_model = AsyncMock(
            side_effect=[
                "Task result",
                "Query result",
                "Prompt result",
            ],
        )

        # Test task processing
        task_result = await agent.process({"task": "Do task"})
        assert task_result["success"] is True
        assert task_result["response"] == "Task result"

        # Test query processing
        query_result = await agent.process({"query": "Ask query"})
        assert query_result["success"] is True
        assert query_result["response"] == "Query result"

        # Test prompt processing
        prompt_result = await agent.process({"prompt": "Give prompt"})
        assert prompt_result["success"] is True
        assert prompt_result["response"] == "Prompt result"

        # Verify all calls were made
        assert agent._call_model.call_count == 3

    def test_initialization_inheritance_from_base_agent(self):
        """Test that MarkdownAgent properly inherits from BaseAgent."""
        agent = MarkdownAgent(
            agent_id="inheritance_test",
            definition="Test inheritance",
            model="sonnet",
            tools=["tool1"],
            context="Context",
            config={"test": "value"},
        )

        # Should have inherited BaseAgent attributes
        assert hasattr(agent, "config")
        assert hasattr(agent, "logger")
        assert agent.agent_id == "inheritance_test"
        assert agent.config.get("tools") == ["tool1"]

        # Should have MarkdownAgent specific attributes
        assert agent.definition == "Test inheritance"
        assert agent.context == "Context"
        assert agent.model == "sonnet"
