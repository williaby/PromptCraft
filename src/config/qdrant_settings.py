"""
Qdrant-specific configuration settings for vector database integration.

This module provides configuration management for the Qdrant vector database
connection, embedding models, and collection management.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class QdrantSettings(BaseSettings):
    """Configuration settings for Qdrant vector database integration."""

    # Connection Settings
    qdrant_host: str = Field(default="192.168.1.16", description="Qdrant server host address (external Unraid server)")
    qdrant_port: int = Field(default=6333, description="Qdrant server port")
    qdrant_api_key: str | None = Field(default=None, description="Qdrant API key for authentication (if required)")
    qdrant_timeout: int = Field(default=30, description="Connection timeout in seconds")

    # Embedding Model Settings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for generating embeddings",
    )
    vector_size: int = Field(default=384, description="Vector dimension size for the embedding model")

    # Collection Settings
    create_agent_collection: str = Field(
        default="create_agent",
        description="Collection name for CREATE framework knowledge base",
    )
    hyde_documents_collection: str = Field(
        default="hyde_documents",
        description="Collection name for hypothetical documents",
    )
    domain_knowledge_collection: str = Field(
        default="domain_knowledge",
        description="Collection name for software capability definitions",
    )
    conceptual_patterns_collection: str = Field(
        default="conceptual_patterns",
        description="Collection name for mismatch detection patterns",
    )

    # Performance Settings
    search_limit: int = Field(default=10, description="Default number of results to return from vector search")
    search_threshold: float = Field(default=0.7, description="Minimum similarity score threshold for search results")
    batch_size: int = Field(default=100, description="Batch size for bulk operations")

    # Connection Pool Settings
    max_connections: int = Field(default=10, description="Maximum number of concurrent connections")
    connection_timeout: int = Field(default=5, description="Individual connection timeout in seconds")

    class Config:
        env_prefix = "QDRANT_"
        case_sensitive = False


# Global instance for easy access
qdrant_settings = QdrantSettings()
