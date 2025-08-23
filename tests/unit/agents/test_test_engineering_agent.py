"""Unit tests for the TestEngineeringAgent."""

import pytest

from src.agents.models import AgentInput
from src.agents.test_engineering_agent import TestEngineeringAgent


class TestTestEngineeringAgent:
    """Test cases for TestEngineeringAgent."""

    @pytest.fixture
    def agent(self):
        """Create a TestEngineeringAgent instance for testing."""
        config = {
            "agent_id": "test_engineering",
            "default_test_type": "unit",
            "coverage_target": 80.0,
            "timeout": 30,
            "enable_debug_mode": False,
        }
        return TestEngineeringAgent(config)

    def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.agent_id == "test_engineering"
        assert agent.default_test_type == "unit"
        assert agent.coverage_target == 80.0
        assert agent.timeout == 30

    def test_get_capabilities(self, agent):
        """Test that the agent reports its capabilities correctly."""
        capabilities = agent.get_capabilities()
        assert capabilities["agent_id"] == "test_engineering"
        assert capabilities["agent_type"] == "TestEngineeringAgent"
        assert "generate_tests" in capabilities["operations"]
        assert "run_tests" in capabilities["operations"]

    def test_determine_test_file_path(self, agent):
        """Test the _determine_test_file_path method."""
        # Test unit test path
        path = agent._determine_test_file_path("src/core/query_counselor.py", "unit")
        assert path == "tests/unit/core/test_query_counselor.py"

        # Test integration test path
        path = agent._determine_test_file_path("src/api/endpoints.py", "integration")
        assert path == "tests/integration/api/test_endpoints.py"

    def test_generate_test_skeleton(self, agent):
        """Test the _generate_test_skeleton method."""
        skeleton = agent._generate_test_skeleton("src/core/query_counselor.py", "unit")
        assert "class TestQuery_Counselor:" in skeleton
        assert "import pytest" in skeleton

    async def test_execute_help_task(self, agent):
        """Test executing the help task."""
        agent_input = AgentInput(content="help", context={"task": "help"})

        result = await agent.execute(agent_input)
        assert "Test Engineering Agent Help" in result.content
        assert "Available Tasks:" in result.content
        assert result.confidence == 1.0
