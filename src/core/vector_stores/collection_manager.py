"""
Collection management for Qdrant vector database.

This module provides collection creation and management functionality for the
Qdrant vector database integration. It handles collection schema definition,
creation, and validation for different types of knowledge stores.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from ...config.qdrant_settings import qdrant_settings


class QdrantCollectionManager:
    """Manages Qdrant collections for different knowledge types."""

    def __init__(self, client: QdrantClient):
        """Initialize collection manager with Qdrant client."""
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def create_all_collections(self) -> dict[str, bool]:
        """Create all required collections for PromptCraft knowledge base."""
        collections = {
            qdrant_settings.create_agent_collection: {
                "vector_size": qdrant_settings.vector_size,
                "distance": Distance.COSINE,
                "description": "CREATE framework knowledge base",
            },
            qdrant_settings.hyde_documents_collection: {
                "vector_size": qdrant_settings.vector_size,
                "distance": Distance.COSINE,
                "description": "Generated hypothetical documents",
            },
            qdrant_settings.domain_knowledge_collection: {
                "vector_size": qdrant_settings.vector_size,
                "distance": Distance.COSINE,
                "description": "Software capability definitions",
            },
            qdrant_settings.conceptual_patterns_collection: {
                "vector_size": qdrant_settings.vector_size,
                "distance": Distance.COSINE,
                "description": "Conceptual mismatch detection patterns",
            },
        }

        results = {}
        for collection_name, config in collections.items():
            try:
                result = await self.create_collection(collection_name, config["vector_size"], config["distance"])
                results[collection_name] = result
                if result:
                    self.logger.info("Created collection '%s': %s", collection_name, config["description"])
            except Exception as e:
                self.logger.error("Failed to create collection '%s': %s", collection_name, str(e))
                results[collection_name] = False

        return results

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = None,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """Create a single collection with specified parameters."""
        if vector_size is None:
            vector_size = qdrant_settings.vector_size

        try:
            # Check if collection already exists
            existing_collections = self.client.get_collections()
            if any(col.name == collection_name for col in existing_collections.collections):
                self.logger.info("Collection '%s' already exists", collection_name)
                return True

            # Create the collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )

            self.logger.info("Successfully created collection '%s' with vector size %d", collection_name, vector_size)
            return True

        except Exception as e:
            self.logger.error("Failed to create collection '%s': %s", collection_name, str(e))
            return False

    async def validate_collections(self) -> dict[str, dict[str, Any]]:
        """Validate all required collections exist and are properly configured."""
        required_collections = [
            qdrant_settings.create_agent_collection,
            qdrant_settings.hyde_documents_collection,
            qdrant_settings.domain_knowledge_collection,
            qdrant_settings.conceptual_patterns_collection,
        ]

        validation_results = {}

        for collection_name in required_collections:
            try:
                collection_info = self.client.get_collection(collection_name)
                validation_results[collection_name] = {
                    "exists": True,
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance.value,
                    "points_count": collection_info.points_count,
                    "segments_count": collection_info.segments_count,
                    "status": collection_info.status.value,
                }
                self.logger.debug("Collection '%s' validated: %d points", collection_name, collection_info.points_count)
            except Exception as e:
                validation_results[collection_name] = {"exists": False, "error": str(e)}
                self.logger.warning("Collection '%s' validation failed: %s", collection_name, str(e))

        return validation_results

    async def get_collection_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all collections."""
        try:
            collections = self.client.get_collections()
            stats = {}

            for collection in collections.collections:
                try:
                    info = self.client.get_collection(collection.name)
                    stats[collection.name] = {
                        "points_count": info.points_count,
                        "segments_count": info.segments_count,
                        "vector_size": info.config.params.vectors.size,
                        "distance": info.config.params.vectors.distance.value,
                        "status": info.status.value,
                        "disk_usage": info.config.params.vectors.size * info.points_count * 4,  # Approximate
                    }
                except Exception as e:
                    stats[collection.name] = {"error": str(e)}

            return stats

        except Exception as e:
            self.logger.error("Failed to get collection stats: %s", str(e))
            return {}

    async def cleanup_empty_collections(self) -> dict[str, bool]:
        """Remove empty collections (useful for development/testing)."""
        collections = self.client.get_collections()
        cleanup_results = {}

        for collection in collections.collections:
            try:
                info = self.client.get_collection(collection.name)
                if info.points_count == 0:
                    self.client.delete_collection(collection.name)
                    cleanup_results[collection.name] = True
                    self.logger.info("Removed empty collection: %s", collection.name)
                else:
                    cleanup_results[collection.name] = False
                    self.logger.debug("Kept collection '%s' with %d points", collection.name, info.points_count)
            except Exception as e:
                cleanup_results[collection.name] = False
                self.logger.error("Failed to cleanup collection '%s': %s", collection.name, str(e))

        return cleanup_results
