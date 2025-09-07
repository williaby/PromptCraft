"""Tests for AnalysisAgent."""

import asyncio
import time
from unittest import mock

import pytest

from src.agents.analysis_agent import AnalysisAgent
from src.agents.models import AgentInput, AgentOutput


class TestAnalysisAgent:
    """Test cases for AnalysisAgent."""

    @pytest.fixture
    def agent_config(self):
        """Standard agent configuration."""
        return {
            "agent_id": "analysis_agent",
            "model": "gpt-4",
            "timeout": 30
        }

    @pytest.fixture
    def analysis_agent(self, agent_config):
        """Create AnalysisAgent instance."""
        return AnalysisAgent(agent_config)

    @pytest.fixture
    def sample_input(self):
        """Sample agent input."""
        return AgentInput(
            content="Analyze the architecture of the payment system",
            context={"files": ["payment.py", "billing.py"]}
        )

    def test_init(self, analysis_agent):
        """Test AnalysisAgent initialization."""
        assert analysis_agent.agent_id == "analysis_agent"
        assert analysis_agent.zen_tools == ["analyze"]
        assert hasattr(analysis_agent, 'config')

    def test_zen_tools_configured(self, analysis_agent):
        """Test that zen tools are properly configured."""
        assert "analyze" in analysis_agent.zen_tools
        assert len(analysis_agent.zen_tools) == 1

    @pytest.mark.asyncio
    async def test_execute_with_tools_success(self, analysis_agent, sample_input):
        """Test successful execution with zen analyze tool."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=True):
            result = await analysis_agent.execute_with_tools(sample_input)
            
            assert isinstance(result, AgentOutput)
            assert result.agent_id == "analysis_agent"
            assert result.confidence == 0.88
            assert "Architecture Analysis" in result.content
            assert "patterns_found" in result.metadata
            assert result.metadata["patterns_found"] == 3
            assert result.metadata["performance_score"] == 0.8
            assert len(result.metadata["recommendations"]) == 3
            assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_execute_with_tools_fallback(self, analysis_agent, sample_input):
        """Test fallback execution when zen tools unavailable."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=False):
            result = await analysis_agent.execute_with_tools(sample_input)
            
            assert isinstance(result, AgentOutput)
            assert result.agent_id == "analysis_agent"
            assert result.confidence == 0.6
            assert "Basic Analysis - Fallback Mode" in result.content
            assert result.metadata["patterns_found"] == 0
            assert result.metadata["performance_score"] == 0.5
            assert "Manual architecture review needed" in result.metadata["recommendations"]

    @pytest.mark.asyncio
    async def test_execute_with_tools_exception(self, analysis_agent, sample_input):
        """Test exception handling in execute_with_tools."""
        with mock.patch.object(analysis_agent, 'is_tool_available', side_effect=RuntimeError("Tool error")):
            result = await analysis_agent.execute_with_tools(sample_input)
            
            assert isinstance(result, AgentOutput)
            assert result.agent_id == "analysis_agent"
            assert result.confidence == 0.3
            assert "Analysis Error" in result.content
            assert "Tool error" in result.content
            assert result.metadata["error"] == "Tool error"
            assert result.metadata["fallback_mode"] is True

    @pytest.mark.asyncio
    async def test_processing_time_tracked(self, analysis_agent, sample_input):
        """Test that processing time is properly tracked."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=True):
            with mock.patch('time.time', side_effect=[1000.0, 1000.5]):  # Mock 0.5 second processing
                result = await analysis_agent.execute_with_tools(sample_input)
                
                assert result.processing_time == 0.5

    @pytest.mark.asyncio
    async def test_analyze_tool_available_path(self, analysis_agent, sample_input):
        """Test the path when analyze tool is available."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=True) as mock_available:
            result = await analysis_agent.execute_with_tools(sample_input)
            
            # Verify tool availability was checked
            mock_available.assert_called_once_with("analyze")
            
            # Verify comprehensive analysis was performed
            assert result.confidence == 0.88
            assert result.metadata["patterns_found"] == 3
            assert "Optimize database queries" in result.metadata["recommendations"]

    @pytest.mark.asyncio
    async def test_analyze_tool_unavailable_path(self, analysis_agent, sample_input):
        """Test the path when analyze tool is unavailable."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=False) as mock_available:
            result = await analysis_agent.execute_with_tools(sample_input)
            
            # Verify tool availability was checked
            mock_available.assert_called_once_with("analyze")
            
            # Verify fallback analysis was performed
            assert result.confidence == 0.6
            assert result.metadata["patterns_found"] == 0
            assert result.metadata["recommendations"] == ["Manual architecture review needed"]

    def test_agent_registration(self):
        """Test that AnalysisAgent is properly registered."""
        from src.agents.registry import agent_registry
        
        # Check if analysis_agent is registered
        registered_agents = agent_registry.list_agents()
        assert "analysis_agent" in registered_agents

    def test_inherits_from_zen_agent_base(self, analysis_agent):
        """Test that AnalysisAgent inherits from ZenAgentBase."""
        from src.agents.zen_agent_base import ZenAgentBase
        assert isinstance(analysis_agent, ZenAgentBase)

    @pytest.mark.asyncio
    async def test_metadata_structure(self, analysis_agent, sample_input):
        """Test that output metadata has expected structure."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=True):
            result = await analysis_agent.execute_with_tools(sample_input)
            
            # Check metadata structure
            required_keys = ["patterns_found", "performance_score", "recommendations"]
            for key in required_keys:
                assert key in result.metadata
            
            # Check data types
            assert isinstance(result.metadata["patterns_found"], int)
            assert isinstance(result.metadata["performance_score"], float)
            assert isinstance(result.metadata["recommendations"], list)

    @pytest.mark.asyncio
    async def test_content_format(self, analysis_agent, sample_input):
        """Test that content output has expected format."""
        with mock.patch.object(analysis_agent, 'is_tool_available', return_value=True):
            result = await analysis_agent.execute_with_tools(sample_input)
            
            # Check content structure
            assert result.content.startswith("# Architecture Analysis")
            assert "Comprehensive analysis of:" in result.content
            assert sample_input.content in result.content
            assert "## Key Findings" in result.content