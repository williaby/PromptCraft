"""Tests for DeepThinkingAgent."""

import asyncio
import time
from unittest import mock

import pytest

from src.agents.deep_thinking_agent import DeepThinkingAgent
from src.agents.models import AgentInput, AgentOutput


class TestDeepThinkingAgent:
    """Test cases for DeepThinkingAgent."""

    @pytest.fixture
    def agent_config(self):
        """Standard agent configuration."""
        return {
            "agent_id": "deep_thinking_agent",
            "model": "gpt-4",
            "timeout": 30
        }

    @pytest.fixture
    def deep_thinking_agent(self, agent_config):
        """Create DeepThinkingAgent instance."""
        return DeepThinkingAgent(agent_config)

    @pytest.fixture
    def sample_input(self):
        """Sample agent input."""
        return AgentInput(
            content="Analyze the complex decision-making process for feature prioritization",
            context={"domain": "product_management", "complexity": "high"}
        )

    def test_init(self, deep_thinking_agent):
        """Test DeepThinkingAgent initialization."""
        assert deep_thinking_agent.agent_id == "deep_thinking_agent"
        assert deep_thinking_agent.zen_tools == ["thinkdeep"]
        assert hasattr(deep_thinking_agent, 'config')

    def test_zen_tools_configured(self, deep_thinking_agent):
        """Test that zen tools are properly configured."""
        assert "thinkdeep" in deep_thinking_agent.zen_tools
        assert len(deep_thinking_agent.zen_tools) == 1

    @pytest.mark.asyncio
    async def test_execute_with_tools_success(self, deep_thinking_agent, sample_input):
        """Test successful execution with zen thinkdeep tool."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=True):
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            assert isinstance(result, AgentOutput)
            assert result.agent_id == "deep_thinking_agent"
            assert result.confidence == 0.87
            assert "Deep Thinking Analysis" in result.content
            assert "reasoning_steps" in result.metadata
            assert result.metadata["reasoning_steps"] == 8
            assert result.metadata["hypotheses_generated"] == 4
            assert result.metadata["confidence_score"] == 0.85
            assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_execute_with_tools_fallback(self, deep_thinking_agent, sample_input):
        """Test fallback execution when zen tools unavailable."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=False):
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            assert isinstance(result, AgentOutput)
            assert result.agent_id == "deep_thinking_agent"
            assert result.confidence == 0.6
            assert "Basic Problem Analysis" in result.content
            assert result.metadata["reasoning_steps"] == 2
            assert result.metadata["hypotheses_generated"] == 1
            assert result.metadata["confidence_score"] == 0.5

    @pytest.mark.asyncio
    async def test_execute_with_tools_exception(self, deep_thinking_agent, sample_input):
        """Test exception handling in execute_with_tools."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', side_effect=RuntimeError("Tool error")):
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            assert isinstance(result, AgentOutput)
            assert result.agent_id == "deep_thinking_agent"
            assert result.confidence == 0.3
            assert "Deep Thinking Analysis Error" in result.content
            assert "Tool error" in result.content
            assert result.metadata["error"] == "Tool error"
            assert result.metadata["fallback_mode"] is True

    @pytest.mark.asyncio
    async def test_processing_time_tracked(self, deep_thinking_agent, sample_input):
        """Test that processing time is properly tracked."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=True):
            with mock.patch('time.time', side_effect=[1000.0, 1001.0]):  # Mock 1 second processing
                result = await deep_thinking_agent.execute_with_tools(sample_input)
                
                assert result.processing_time == 1.0

    @pytest.mark.asyncio
    async def test_thinkdeep_tool_available_path(self, deep_thinking_agent, sample_input):
        """Test the path when thinkdeep tool is available."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=True) as mock_available:
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            # Verify tool availability was checked
            mock_available.assert_called_once_with("thinkdeep")
            
            # Verify comprehensive thinking was performed
            assert result.confidence == 0.87
            assert result.metadata["reasoning_steps"] == 8
            assert result.metadata["hypotheses_generated"] == 4

    @pytest.mark.asyncio
    async def test_thinkdeep_tool_unavailable_path(self, deep_thinking_agent, sample_input):
        """Test the path when thinkdeep tool is unavailable."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=False) as mock_available:
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            # Verify tool availability was checked
            mock_available.assert_called_once_with("thinkdeep")
            
            # Verify fallback thinking was performed
            assert result.confidence == 0.6
            assert result.metadata["reasoning_steps"] == 2

    def test_agent_registration(self):
        """Test that DeepThinkingAgent is properly registered."""
        from src.agents.registry import agent_registry
        
        # Check if deep_thinking_agent is registered
        registered_agents = agent_registry.list_agents()
        assert "deep_thinking_agent" in registered_agents

    def test_inherits_from_zen_agent_base(self, deep_thinking_agent):
        """Test that DeepThinkingAgent inherits from ZenAgentBase."""
        from src.agents.zen_agent_base import ZenAgentBase
        assert isinstance(deep_thinking_agent, ZenAgentBase)

    @pytest.mark.asyncio
    async def test_metadata_structure(self, deep_thinking_agent, sample_input):
        """Test that output metadata has expected structure."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=True):
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            # Check metadata structure
            required_keys = ["reasoning_steps", "hypotheses_generated", "confidence_score"]
            for key in required_keys:
                assert key in result.metadata
            
            # Check data types
            assert isinstance(result.metadata["reasoning_steps"], int)
            assert isinstance(result.metadata["hypotheses_generated"], int)
            assert isinstance(result.metadata["confidence_score"], float)

    @pytest.mark.asyncio
    async def test_content_format(self, deep_thinking_agent, sample_input):
        """Test that content output has expected format."""
        with mock.patch.object(deep_thinking_agent, 'is_tool_available', return_value=True):
            result = await deep_thinking_agent.execute_with_tools(sample_input)
            
            # Check content structure
            assert result.content.startswith("# Deep Thinking Analysis")
            assert "Multi-step reasoning for:" in result.content
            assert sample_input.content in result.content
            assert "## Problem Decomposition" in result.content
            assert "## Hypothesis Generation" in result.content