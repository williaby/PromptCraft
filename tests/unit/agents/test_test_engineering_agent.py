"""Comprehensive tests for TestEngineeringAgent.

Tests the test engineering agent functionality including test generation,
analysis, and debugging capabilities using minimal mocking.
"""

from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from src.agents.exceptions import AgentConfigurationError, AgentValidationError
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

    def test_init_with_minimal_config(self):
        """Test agent initialization with minimal required config."""
        config = {"agent_id": "test_engineering"}
        agent = TestEngineeringAgent(config)
        assert agent.config == config
        assert agent.agent_id == "test_engineering"

    def test_init_calls_validation(self):
        """Test that initialization calls configuration validation."""
        config = {"agent_id": "test_engineering"}
        with patch.object(TestEngineeringAgent, "_validate_configuration") as mock_validate:
            TestEngineeringAgent(config)
            mock_validate.assert_called_once()

    def test_validate_configuration_valid(self, agent):
        """Test validation passes with valid configuration."""
        # Should not raise exception
        agent._validate_configuration()

    def test_validate_configuration_missing_agent_id(self):
        """Test validation fails with missing agent_id."""
        config = {}
        with pytest.raises(AgentConfigurationError, match="agent_id is required"):
            TestEngineeringAgent(config)

    def test_validate_configuration_empty_agent_id(self):
        """Test validation fails with empty agent_id."""
        config = {"agent_id": ""}
        with pytest.raises(AgentConfigurationError, match="agent_id is required"):
            TestEngineeringAgent(config)

    def test_validate_input_valid(self, agent):
        """Test input validation passes with valid input."""
        agent_input = AgentInput(content="Create tests for module", context={"task": "generate_tests"})
        # Should not raise exception
        agent._validate_input(agent_input)

    def test_validate_input_empty_content(self, agent):
        """Test input validation fails with empty content."""
        agent_input = AgentInput(content="", context={"task": "generate_tests"})
        with pytest.raises(AgentValidationError, match="Content cannot be empty"):
            agent._validate_input(agent_input)

    def test_validate_input_none_content(self, agent):
        """Test input validation fails with None content."""
        agent_input = AgentInput(content=None, context={"task": "generate_tests"})
        with pytest.raises(AgentValidationError, match="Content cannot be empty"):
            agent._validate_input(agent_input)

    def test_validate_input_whitespace_content(self, agent):
        """Test input validation fails with whitespace-only content."""
        agent_input = AgentInput(content="   \n\t  ", context={"task": "generate_tests"})
        with pytest.raises(AgentValidationError, match="Content cannot be empty"):
            agent._validate_input(agent_input)

    def test_get_capabilities(self, agent):
        """Test that the agent reports its capabilities correctly."""
        capabilities = agent.get_capabilities()
        assert capabilities["agent_id"] == "test_engineering"
        assert capabilities["agent_type"] == "TestEngineeringAgent"
        assert "generate_tests" in capabilities["operations"]
        assert "run_tests" in capabilities["operations"]

    def test_get_capabilities_structure(self, agent):
        """Test capabilities return correct structure."""
        result = agent.get_capabilities()
        assert isinstance(result, dict)
        assert "agent_id" in result
        assert "name" in result
        assert "capabilities" in result
        assert "supported_tasks" in result
        assert result["agent_id"] == "test_engineering"
        assert isinstance(result["capabilities"], list)
        assert isinstance(result["supported_tasks"], list)

    def test_get_capabilities_content(self, agent):
        """Test capabilities contain expected content."""
        result = agent.get_capabilities()
        capabilities = result["capabilities"]
        supported_tasks = result["supported_tasks"]

        # Should contain key capabilities
        assert any("test generation" in cap.lower() for cap in capabilities)
        assert any("coverage analysis" in cap.lower() for cap in capabilities)
        assert any("debug" in cap.lower() for cap in capabilities)

        # Should contain supported tasks
        assert any("generate" in task.lower() for task in supported_tasks)
        assert any("analyze" in task.lower() for task in supported_tasks)

    def test_determine_test_file_path(self, agent):
        """Test the _determine_test_file_path method."""
        # Test unit test path
        path = agent._determine_test_file_path("src/core/query_counselor.py", "unit")
        assert path == "tests/unit/core/test_query_counselor.py"

        # Test integration test path
        path = agent._determine_test_file_path("src/api/endpoints.py", "integration")
        assert path == "tests/integration/api/test_endpoints.py"

    def test_determine_test_path_nested_module(self, agent):
        """Test test path for deeply nested module."""
        module_path = "src/utils/security/validation.py"
        test_type = "unit"
        result = agent._determine_test_file_path(module_path, test_type)
        expected = "tests/unit/utils/security/test_validation.py"
        assert result == expected

    def test_determine_test_path_no_extension(self, agent):
        """Test test path generation for module without .py extension."""
        module_path = "src/core/processor"
        test_type = "unit"
        result = agent._determine_test_file_path(module_path, test_type)
        expected = "tests/unit/core/test_processor.py"
        assert result == expected

    def test_determine_test_path_different_test_types(self, agent):
        """Test path generation for different test types."""
        module_path = "src/database/models.py"
        test_cases = [
            ("unit", "tests/unit/database/test_models.py"),
            ("integration", "tests/integration/database/test_models.py"),
            ("functional", "tests/functional/database/test_models.py"),
            ("performance", "tests/performance/database/test_models.py"),
        ]

        for test_type, expected_path in test_cases:
            result = agent._determine_test_file_path(module_path, test_type)
            assert result == expected_path

    def test_generate_test_skeleton(self, agent):
        """Test the _generate_test_skeleton method."""
        skeleton = agent._generate_test_skeleton("src/core/query_counselor.py", "unit")
        assert "class TestQuery_Counselor:" in skeleton
        assert "import pytest" in skeleton

    def test_generate_test_skeleton_basic(self, agent):
        """Test basic test skeleton generation."""
        module_path = "src/core/processor.py"
        test_type = "unit"
        result = agent._generate_test_skeleton(module_path, test_type)

        # Check for expected skeleton structure
        assert "import pytest" in result
        assert "from src.core.processor import" in result
        assert "class TestProcessor:" in result
        assert "def test_example_functionality(self):" in result
        assert "def test_edge_case(self):" in result
        assert "def test_error_conditions(self):" in result

    def test_generate_test_skeleton_different_module(self, agent):
        """Test skeleton generation for different module."""
        module_path = "src/utils/helpers.py"
        test_type = "integration"
        result = agent._generate_test_skeleton(module_path, test_type)

        assert "from src.utils.helpers import" in result
        assert "class TestHelpers:" in result
        assert "def test_integration_functionality(self):" in result

    def test_generate_test_skeleton_contains_required_elements(self, agent):
        """Test that generated skeleton contains all required elements."""
        module_path = "src/core/service.py"
        test_type = "unit"
        result = agent._generate_test_skeleton(module_path, test_type)

        required_elements = [
            '"""Tests for',
            "import pytest",
            "class TestService:",
            "def test_example_functionality(self):",
            '"""Test basic functionality."""',
            "def test_edge_case(self):",
            '"""Test edge case scenarios."""',
            "def test_error_conditions(self):",
            '"""Test error handling."""',
        ]

        for element in required_elements:
            assert element in result, f"Missing required element: {element}"

    def test_extract_failed_tests_basic(self, agent):
        """Test extraction of failed tests from pytest output."""
        output = """
FAILED tests/unit/test_module.py::TestClass::test_method - AssertionError: Expected True
FAILED tests/integration/test_api.py::test_endpoint - ValueError: Invalid input
========================= 2 failed, 3 passed =========================
        """

        result = agent._extract_failed_tests(output)

        assert len(result) == 2
        assert result[0]["test_file"] == "tests/unit/test_module.py"
        assert result[0]["test_name"] == "TestClass::test_method"
        assert result[0]["error"] == "AssertionError: Expected True"

        assert result[1]["test_file"] == "tests/integration/test_api.py"
        assert result[1]["test_name"] == "test_endpoint"
        assert result[1]["error"] == "ValueError: Invalid input"

    def test_extract_failed_tests_no_failures(self, agent):
        """Test extraction when no tests failed."""
        output = "========================= 5 passed ========================="
        result = agent._extract_failed_tests(output)
        assert result == []

    def test_extract_failed_tests_empty_output(self, agent):
        """Test extraction from empty output."""
        result = agent._extract_failed_tests("")
        assert result == []

    def test_analyze_error_patterns_import_error(self, agent):
        """Test detection of import error patterns."""
        stdout = ""
        stderr = "ImportError: No module named 'missing_module'"

        result = agent._analyze_error_patterns(stdout, stderr)

        assert len(result) >= 1
        import_error = next((r for r in result if r["type"] == "ImportError"), None)
        assert import_error is not None
        assert "missing_module" in import_error["message"]

    def test_analyze_error_patterns_syntax_error(self, agent):
        """Test detection of syntax error patterns."""
        stdout = ""
        stderr = "SyntaxError: invalid syntax (test_file.py, line 10)"

        result = agent._analyze_error_patterns(stdout, stderr)

        syntax_error = next((r for r in result if r["type"] == "SyntaxError"), None)
        assert syntax_error is not None
        assert "test_file.py" in syntax_error["message"]

    def test_analyze_error_patterns_fixture_error(self, agent):
        """Test detection of fixture error patterns."""
        stdout = "fixture 'missing_fixture' not found"
        stderr = ""

        result = agent._analyze_error_patterns(stdout, stderr)

        fixture_error = next((r for r in result if r["type"] == "FixtureError"), None)
        assert fixture_error is not None
        assert "missing_fixture" in fixture_error["message"]

    def test_analyze_error_patterns_no_errors(self, agent):
        """Test analysis when no error patterns found."""
        stdout = "All tests passed successfully"
        stderr = ""
        result = agent._analyze_error_patterns(stdout, stderr)
        assert result == []

    def test_generate_debug_recommendations_failed_tests(self, agent):
        """Test recommendations for failed tests."""
        failed_tests = [{"test_file": "test_module.py", "test_name": "test_method", "error": "AssertionError"}]
        error_patterns = []

        result = agent._generate_debug_recommendations(failed_tests, error_patterns)

        assert len(result) >= 1
        assert any("failed test" in rec.lower() for rec in result)

    def test_generate_debug_recommendations_import_errors(self, agent):
        """Test recommendations for import errors."""
        failed_tests = []
        error_patterns = [{"type": "ImportError", "message": "No module named 'missing_module'"}]

        result = agent._generate_debug_recommendations(failed_tests, error_patterns)

        assert len(result) >= 1
        assert any("import" in rec.lower() for rec in result)

    def test_generate_coverage_recommendations_low_coverage(self, agent):
        """Test recommendations for low coverage."""
        coverage_percent = 45.0
        coverage_data = {
            "missing_lines": {"src/module.py": [10, 15, 20]},
            "uncovered_functions": ["function_a", "function_b"],
        }

        result = agent._generate_coverage_recommendations(coverage_percent, coverage_data)

        assert len(result) >= 1
        assert any("coverage is below" in rec for rec in result)
        assert any("missing lines" in rec for rec in result)

    def test_generate_coverage_recommendations_good_coverage(self, agent):
        """Test recommendations for good coverage."""
        coverage_percent = 85.0
        coverage_data = {}

        result = agent._generate_coverage_recommendations(coverage_percent, coverage_data)

        assert len(result) >= 1
        assert any("coverage is good" in rec for rec in result)

    def test_find_python_files_basic(self, agent):
        """Test finding Python files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test Python files
            files = ["module.py", "helper.py", "test_something.py"]
            for file_name in files:
                file_path = Path(temp_dir) / file_name
                file_path.write_text("# Python code")

            # Create non-Python file
            (Path(temp_dir) / "readme.txt").write_text("Not Python")

            result = agent._find_python_files(temp_dir)

            assert len(result) == 3
            for file_name in files:
                expected_path = str(Path(temp_dir) / file_name)
                assert expected_path in result

    def test_find_python_files_empty_directory(self, agent):
        """Test finding files in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = agent._find_python_files(temp_dir)
            assert result == set()

    def test_find_python_files_nonexistent_directory(self, agent):
        """Test behavior with nonexistent directory."""
        nonexistent = "/path/that/does/not/exist"
        result = agent._find_python_files(nonexistent)
        assert result == set()

    async def test_execute_help_task(self, agent):
        """Test executing the help task."""
        agent_input = AgentInput(content="help", context={"task": "help"})

        result = await agent.execute(agent_input)
        assert "Test Engineering Agent Help" in result.content
        assert "Available Tasks:" in result.content
        assert result.confidence == 1.0
