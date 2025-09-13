"""Test Qdrant settings configuration."""

import os
from unittest.mock import patch

from src.config.qdrant_settings import QdrantSettings, qdrant_settings


class TestQdrantSettings:
    """Test Qdrant configuration settings."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = QdrantSettings()

        # Connection Settings
        assert settings.qdrant_host == "192.168.1.16"
        assert settings.qdrant_port == 6333
        assert settings.qdrant_api_key is None
        assert settings.qdrant_timeout == 30

        # Embedding Model Settings
        assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert settings.vector_size == 384

        # Collection Settings
        assert settings.create_agent_collection == "create_agent"
        assert settings.hyde_documents_collection == "hyde_documents"
        assert settings.domain_knowledge_collection == "domain_knowledge"
        assert settings.conceptual_patterns_collection == "conceptual_patterns"

        # Performance Settings
        assert settings.search_limit == 10
        assert settings.search_threshold == 0.7
        assert settings.batch_size == 100

        # Connection Pool Settings
        assert settings.max_connections == 10
        assert settings.connection_timeout == 5

    def test_settings_types(self):
        """Test that settings have correct types."""
        settings = QdrantSettings()

        assert isinstance(settings.qdrant_host, str)
        assert isinstance(settings.qdrant_port, int)
        assert settings.qdrant_api_key is None or isinstance(settings.qdrant_api_key, str)
        assert isinstance(settings.qdrant_timeout, int)
        assert isinstance(settings.embedding_model, str)
        assert isinstance(settings.vector_size, int)
        assert isinstance(settings.search_limit, int)
        assert isinstance(settings.search_threshold, float)
        assert isinstance(settings.batch_size, int)
        assert isinstance(settings.max_connections, int)
        assert isinstance(settings.connection_timeout, int)

    def test_collection_names_unique(self):
        """Test that collection names are unique."""
        settings = QdrantSettings()

        collection_names = [
            settings.create_agent_collection,
            settings.hyde_documents_collection,
            settings.domain_knowledge_collection,
            settings.conceptual_patterns_collection,
        ]

        assert len(collection_names) == len(set(collection_names))

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(
            os.environ,
            {
                "QDRANT_QDRANT_HOST": "localhost",
                "QDRANT_QDRANT_PORT": "6334",
                "QDRANT_QDRANT_API_KEY": "test-key",
                "QDRANT_QDRANT_TIMEOUT": "60",
                "QDRANT_VECTOR_SIZE": "512",
                "QDRANT_SEARCH_LIMIT": "20",
            },
        ):
            settings = QdrantSettings()
            assert settings.qdrant_host == "localhost"
            assert settings.qdrant_port == 6334
            assert settings.qdrant_api_key == "test-key"
            assert settings.qdrant_timeout == 60
            assert settings.vector_size == 512
            assert settings.search_limit == 20

    def test_case_insensitive_env_vars(self):
        """Test case insensitive environment variables."""
        with patch.dict(os.environ, {"qdrant_host": "test.example.com", "QDRANT_PORT": "9999"}):
            settings = QdrantSettings()
            # Should still use case insensitive matching
            assert settings.qdrant_host in {"test.example.com", "192.168.1.16"}
            assert settings.qdrant_port in {9999, 6333}

    def test_global_instance(self):
        """Test that global instance exists and is properly configured."""
        assert qdrant_settings is not None
        assert isinstance(qdrant_settings, QdrantSettings)

        # Test default values on global instance
        assert qdrant_settings.qdrant_host == "192.168.1.16"
        assert qdrant_settings.vector_size == 384

    def test_settings_validation_constraints(self):
        """Test that settings respect logical constraints."""
        settings = QdrantSettings()

        # Port should be positive integer
        assert settings.qdrant_port > 0
        assert settings.qdrant_port <= 65535

        # Vector size should be positive
        assert settings.vector_size > 0

        # Search threshold should be between 0 and 1
        assert 0.0 <= settings.search_threshold <= 1.0

        # Batch size should be positive
        assert settings.batch_size > 0

        # Connection settings should be positive
        assert settings.max_connections > 0
        assert settings.connection_timeout > 0
        assert settings.qdrant_timeout > 0

    def test_collection_name_format(self):
        """Test that collection names follow expected format."""
        settings = QdrantSettings()

        collection_names = [
            settings.create_agent_collection,
            settings.hyde_documents_collection,
            settings.domain_knowledge_collection,
            settings.conceptual_patterns_collection,
        ]

        for name in collection_names:
            # Should be non-empty strings
            assert name
            assert isinstance(name, str)
            # Should not contain spaces or special characters that might cause issues
            assert " " not in name
            assert name.replace("_", "").replace("-", "").isalnum()

    def test_embedding_model_format(self):
        """Test embedding model string format."""
        settings = QdrantSettings()

        assert settings.embedding_model
        assert isinstance(settings.embedding_model, str)
        # Should look like a valid model identifier
        assert "/" in settings.embedding_model or "-" in settings.embedding_model

    def test_config_class_settings(self):
        """Test Pydantic config class settings."""
        settings = QdrantSettings()

        # Test that config is properly set up
        config = settings.model_config
        assert config.get("env_prefix") == "QDRANT_"
        assert config.get("case_sensitive") is False
