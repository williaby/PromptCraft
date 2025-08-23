"""Unit tests for the QwenTestEngineerAgent."""

import pytest

from src.agents.models import AgentInput
from src.agents.qwen_test_engineer_agent import QwenTestEngineerAgent


class TestQwenTestEngineerAgent:
    """Test cases for QwenTestEngineerAgent."""

    @pytest.fixture
    def agent(self):
        """Create a QwenTestEngineerAgent instance for testing."""
        config = {"agent_id": "qwen_test_engineer", "default_test_type": "unit", "coverage_target": 80.0, "timeout": 30}
        return QwenTestEngineerAgent(config)

    def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.agent_id == "qwen_test_engineer"
        assert agent.default_test_type == "unit"
        assert agent.coverage_target == 80.0
        assert agent.timeout == 30

    def test_get_capabilities(self, agent):
        """Test that the agent reports its capabilities correctly."""
        capabilities = agent.get_capabilities()
        assert capabilities["agent_id"] == "qwen_test_engineer"
        assert capabilities["agent_type"] == "QwenTestEngineerAgent"
        assert "generate_tests" in capabilities["operations"]
        assert "run_tests" in capabilities["operations"]

    def test_get_test_file_path(self, agent):
        """Test the _get_test_file_path method."""
        # Test unit test path
        path = agent._get_test_file_path("src/core/query_counselor.py", "unit")
        assert path == "tests/unit/core/test_query_counselor.py"

        # Test integration test path
        path = agent._get_test_file_path("src/api/endpoints.py", "integration")
        assert path == "tests/integration/api/test_endpoints.py"

    def test_create_test_skeleton(self, agent):
        """Test the _create_test_skeleton method."""
        skeleton = agent._create_test_skeleton("src/core/query_counselor.py", "unit")
        assert "class TestQueryCounselor:" in skeleton
        assert "import pytest" in skeleton
        assert "test_basic_functionality" in skeleton

    async def test_execute_help_task(self, agent):
        """Test executing the help task."""
        agent_input = AgentInput(content="help", context={"task": "help"})

        result = await agent.execute(agent_input)
        assert "Qwen Test Engineer Agent Help" in result.content
        assert "## Available Tasks" in result.content
        assert result.confidence == 1.0
