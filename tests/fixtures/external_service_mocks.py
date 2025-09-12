"""External service mocks for CI testing.

This module provides mock implementations for external services like Qdrant and Azure AI
to enable testing in CI environments without requiring actual service connections.
"""

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class MockQdrantClient:
    """Mock implementation of Qdrant client for testing."""

    def __init__(self, host: str = "localhost", port: int = 6333, **kwargs):
        self.host = host
        self.port = port
        self.collections = {}
        self.connected = True

    async def close(self):
        """Mock close connection."""
        self.connected = False

    def create_collection(self, collection_name: str, vectors_config: Any = None, **kwargs):
        """Mock create collection."""
        self.collections[collection_name] = {"vectors_config": vectors_config, "points": {}, "count": 0}
        return {"status": "ok"}

    def get_collection(self, collection_name: str):
        """Mock get collection info."""
        if collection_name in self.collections:
            return {
                "status": "green",
                "vectors_count": self.collections[collection_name]["count"],
                "config": self.collections[collection_name]["vectors_config"],
            }
        raise Exception(f"Collection {collection_name} not found")

    def upsert(self, collection_name: str, points: list[dict], **kwargs):
        """Mock upsert points."""
        if collection_name not in self.collections:
            raise Exception(f"Collection {collection_name} not found")

        for point in points:
            point_id = point.get("id")
            self.collections[collection_name]["points"][point_id] = point

        self.collections[collection_name]["count"] = len(self.collections[collection_name]["points"])
        return {"status": "ok", "operation_id": 12345}

    def search(self, collection_name: str, query_vector: list[float], limit: int = 10, **kwargs):
        """Mock search vectors."""
        if collection_name not in self.collections:
            raise Exception(f"Collection {collection_name} not found")

        # Return mock search results
        return [
            {
                "id": f"test_point_{i}",
                "score": 0.9 - (i * 0.1),
                "payload": {"content": f"Mock content {i}", "metadata": {"source": "test"}},
                "vector": [0.1] * 384,  # Mock 384-dim vector
            }
            for i in range(min(limit, 3))  # Return up to 3 mock results
        ]

    def delete(self, collection_name: str, points_selector: Any, **kwargs):
        """Mock delete points."""
        if collection_name not in self.collections:
            raise Exception(f"Collection {collection_name} not found")

        # Simplified mock deletion
        return {"status": "ok", "operation_id": 12346}


class MockAzureOpenAI:
    """Mock implementation of Azure OpenAI client for testing."""

    def __init__(
        self,
        api_key: str = "test-key",
        api_version: str = "2023-12-01-preview",
        azure_endpoint: str = "https://test.openai.azure.com",
        **kwargs,
    ):
        self.api_key = api_key
        self.api_version = api_version
        self.azure_endpoint = azure_endpoint

    class Chat:
        class Completions:
            @staticmethod
            async def create(model: str, messages: list[dict], **kwargs):
                """Mock chat completion."""
                await asyncio.sleep(0.01)  # Simulate API delay
                return MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(content="This is a mock response from Azure OpenAI", role="assistant"),
                            finish_reason="stop",
                        ),
                    ],
                    usage=MagicMock(
                        prompt_tokens=len(str(messages)),
                        completion_tokens=10,
                        total_tokens=len(str(messages)) + 10,
                    ),
                )

    class Embeddings:
        @staticmethod
        async def create(input: str | list[str], model: str = "text-embedding-ada-002", **kwargs):
            """Mock embeddings creation."""
            await asyncio.sleep(0.01)  # Simulate API delay

            inputs = [input] if isinstance(input, str) else input
            return MagicMock(
                data=[
                    MagicMock(embedding=[0.1] * 1536, index=i) for i in range(len(inputs))  # Mock 1536-dim embedding
                ],
                usage=MagicMock(
                    prompt_tokens=sum(len(inp.split()) for inp in inputs),
                    total_tokens=sum(len(inp.split()) for inp in inputs),
                ),
            )

    def __init_subclass__(cls):
        cls.chat = cls.Chat()
        cls.embeddings = cls.Embeddings()


@pytest.fixture
def mock_qdrant_client():
    """Provide a mock Qdrant client for testing."""
    with patch("qdrant_client.QdrantClient", MockQdrantClient):
        yield MockQdrantClient()


@pytest.fixture
def mock_azure_openai():
    """Provide a mock Azure OpenAI client for testing."""
    mock_client = MockAzureOpenAI()
    mock_client.chat = MockAzureOpenAI.Chat()
    mock_client.embeddings = MockAzureOpenAI.Embeddings()

    with patch("openai.AsyncAzureOpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_external_services(mock_qdrant_client, mock_azure_openai):
    """Provide all external service mocks."""
    return {"qdrant": mock_qdrant_client, "azure_openai": mock_azure_openai}


@pytest.fixture(autouse=True)
def mock_network_calls():
    """Automatically mock all external network calls in CI."""
    if os.environ.get("CI"):
        with patch("httpx.AsyncClient") as mock_httpx, patch("requests.Session") as mock_requests:

            # Configure mock responses
            mock_httpx.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=MagicMock(status_code=200, json=lambda: {"status": "ok"}),
            )
            mock_requests.return_value.get = MagicMock(
                return_value=MagicMock(status_code=200, json=lambda: {"status": "ok"}),
            )

            yield {"httpx": mock_httpx, "requests": mock_requests}
    else:
        yield None


# Environment variable overrides for CI
@pytest.fixture(autouse=True)
def ci_environment_overrides():
    """Override environment variables for CI testing."""
    if os.environ.get("CI"):

        # Set mock values for external services
        test_env = {
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
            "QDRANT_API_KEY": "test-key",
            "AZURE_OPENAI_API_KEY": "test-azure-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_VERSION": "2023-12-01-preview",
            "PROMPTCRAFT_ENVIRONMENT": "test",
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key-for-ci-only",
            "JWT_SECRET_KEY": "test-jwt-secret-for-ci-only",
        }

        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        yield test_env

        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
    else:
        yield None
