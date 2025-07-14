"""Comprehensive fixture library for PromptCraft testing infrastructure.

This module provides reusable fixtures for all test types including:
- Mock ZenClient and ApplicationSettings
- Service mocking for external dependencies (Qdrant, Redis)
- Sample data for CREATE framework testing
- Configuration validation fixtures
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel

# Import application components (with fallback for missing modules)
try:
    from src.config.validation import ApplicationSettings
except ImportError:
    # Create a minimal ApplicationSettings for testing if module doesn't exist
    class ApplicationSettings(BaseModel):
        name: str = "test-app"
        environment: str = "test"
        debug: bool = True


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_zen_client():
    """Mock ZenClient for testing MCP integrations."""
    with patch("src.agents.create_agent.ZenClient") as mock_client:
        # Configure mock client behavior
        mock_instance = Mock()
        mock_instance.process_query = AsyncMock(return_value={"result": "processed", "status": "success"})
        mock_instance.health_check = AsyncMock(return_value=True)
        mock_instance.close = AsyncMock()

        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_application_settings():
    """Sample ApplicationSettings for testing."""
    return ApplicationSettings(name="test-promptcraft", environment="test", debug=True)


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing vector operations."""
    with patch("src.core.vector_store.QdrantClient") as mock_client:
        # Configure mock Qdrant behavior
        mock_instance = Mock()
        mock_instance.search = AsyncMock(
            return_value=[{"id": "test-doc-1", "score": 0.95, "payload": {"content": "Test document content"}}],
        )
        mock_instance.upsert = AsyncMock(return_value={"status": "acknowledged"})
        mock_instance.get_collection_info = AsyncMock(return_value={"status": "green", "vectors_count": 100})

        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing caching operations."""
    with patch("redis.Redis") as mock_redis:
        # Configure mock Redis behavior
        mock_instance = Mock()
        mock_instance.get = Mock(return_value=None)
        mock_instance.set = Mock(return_value=True)
        mock_instance.delete = Mock(return_value=1)
        mock_instance.exists = Mock(return_value=False)
        mock_instance.ping = Mock(return_value=True)

        mock_redis.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_create_request():
    """Sample CREATE framework request for testing."""
    return {
        "context": "You are an AI assistant helping with software development",
        "request": "Generate a Python function that calculates factorial",
        "examples": [
            {
                "input": "factorial(5)",
                "output": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            },
        ],
        "augmentations": ["Include proper error handling", "Add type hints", "Include docstring"],
        "tone_format": {"style": "professional", "format": "python_function"},
        "evaluation": {"criteria": ["correctness", "efficiency", "readability"]},
    }


@pytest.fixture
def sample_create_response():
    """Sample CREATE framework response for testing."""
    return {
        "generated_content": """def factorial(n: int) -> int:
    \"\"\"Calculate the factorial of a positive integer.

    Args:
        n: A positive integer

    Returns:
        The factorial of n

    Raises:
        ValueError: If n is negative
    \"\"\"
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n-1)""",
        "metadata": {"model_used": "test-model", "tokens_used": 150, "processing_time": 1.2},
        "evaluation_results": {"correctness": 0.95, "efficiency": 0.88, "readability": 0.92},
    }


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing integrations."""
    mock_server = Mock()
    mock_server.start = AsyncMock()
    mock_server.stop = AsyncMock()
    mock_server.is_running = Mock(return_value=True)
    mock_server.health_check = AsyncMock(return_value={"status": "healthy"})

    return mock_server


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "description": "A test agent for unit testing",
        "capabilities": ["text_generation", "code_analysis"],
        "models": ["test-model-1", "test-model-2"],
        "max_retries": 3,
        "timeout": 30.0,
    }


@pytest.fixture
def mock_azure_client():
    """Mock Azure AI client for testing cloud integrations."""
    with patch("src.utils.azure_client.AzureAIClient") as mock_client:
        mock_instance = Mock()
        mock_instance.generate_completion = AsyncMock(
            return_value={"content": "Test completion", "usage": {"prompt_tokens": 10, "completion_tokens": 20}},
        )
        mock_instance.get_embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3])

        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def temp_config_file(tmp_path: Path):
    """Create a temporary configuration file for testing."""
    config_content = {
        "app_name": "test-promptcraft",
        "environment": "test",
        "debug": True,
        "database": {"url": "redis://localhost:6379/0"},
        "vector_store": {"url": "http://localhost:6333", "collection_name": "test_collection"},
    }

    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_content, indent=2))
    return config_file


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_text") as mock_read,
        patch("pathlib.Path.write_text") as mock_write,
    ):

        mock_exists.return_value = True
        mock_read.return_value = '{"test": "content"}'
        mock_write.return_value = None

        yield {"exists": mock_exists, "read_text": mock_read, "write_text": mock_write}


@pytest.fixture
def sample_knowledge_document():
    """Sample knowledge document for testing knowledge processing."""
    return {
        "title": "Test Knowledge Document",
        "version": "1.0",
        "status": "published",
        "agent_id": "test_agent",
        "tags": ["testing", "sample"],
        "purpose": "Test document for unit testing.",
        "content": """# Test Knowledge Document

## Overview

This is a test knowledge document for validating the knowledge processing pipeline.

### Key Concepts

- Concept A: Description of concept A
- Concept B: Description of concept B

### Implementation Details

Implementation details would go here.""",
        "metadata": {
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "word_count": 45,
            "complexity_score": 0.3,
        },
    }


@pytest.fixture
def mock_gradio_interface():
    """Mock Gradio interface for testing UI components."""
    mock_interface = Mock()
    mock_interface.launch = Mock()
    mock_interface.close = Mock()
    mock_interface.queue = Mock(return_value=mock_interface)

    return mock_interface


@pytest.fixture(autouse=True)
def isolate_environment_variables(monkeypatch):
    """Automatically isolate environment variables for each test."""
    # Clear potentially problematic environment variables
    test_env_vars = {
        "CODECOV_TOKEN": None,
        "QDRANT_URL": "http://localhost:6333",
        "REDIS_URL": "redis://localhost:6379/0",
        "AZURE_API_KEY": "test-key",
        "ENVIRONMENT": "test",
    }

    for key, value in test_env_vars.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


@pytest.fixture
def error_simulation():
    """Fixture for simulating various error conditions."""
    return {
        "network_error": Exception("Network connection failed"),
        "timeout_error": TimeoutError("Request timed out"),
        "validation_error": ValueError("Invalid input provided"),
        "auth_error": PermissionError("Authentication failed"),
        "service_unavailable": ConnectionError("Service unavailable"),
    }


@pytest.fixture
def performance_metrics():
    """Fixture providing performance measurement utilities."""

    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def assert_max_duration(self, max_seconds: float):
            assert self.elapsed <= max_seconds, f"Operation took {self.elapsed:.3f}s, expected <= {max_seconds}s"

    return PerformanceTracker()


# Parametrized fixtures for edge case testing


@pytest.fixture(
    params=[
        "",  # Empty string
        "a" * 10000,  # Very long string
        "🚀🔥💯",  # Unicode/emoji
        "\x00\x01\x02",  # Binary data
        None,  # None value
        {"nested": {"data": "test"}},  # Complex nested data
    ],
)
def edge_case_inputs(request):
    """Parametrized fixture providing various edge case inputs."""
    return request.param


@pytest.fixture(
    params=[
        {"valid": "config"},
        {},  # Empty config
        None,  # None config
        {"invalid": "structure", "missing": "required_fields"},
    ],
)
def config_edge_cases(request):
    """Parametrized fixture for configuration validation edge cases."""
    return request.param


@pytest.fixture(params=[1, 10, 100, 1000])
def load_test_sizes(request):
    """Parametrized fixture for load testing with different sizes."""
    return request.param
