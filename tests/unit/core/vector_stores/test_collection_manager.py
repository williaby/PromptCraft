"""Test Qdrant collection manager."""

from unittest.mock import Mock, patch

import pytest
from qdrant_client.models import Distance, VectorParams

from src.core.vector_stores.collection_manager import QdrantCollectionManager


class TestQdrantCollectionManager:
    """Test QdrantCollectionManager functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Qdrant client."""
        client = Mock()
        client.get_collections = Mock()
        client.create_collection = Mock()
        client.get_collection = Mock()
        client.delete_collection = Mock()
        return client

    @pytest.fixture
    def manager(self, mock_client):
        """Create collection manager with mock client."""
        return QdrantCollectionManager(mock_client)

    def test_manager_initialization(self, mock_client):
        """Test manager initializes correctly."""
        manager = QdrantCollectionManager(mock_client)

        assert manager.client == mock_client
        assert manager.logger is not None
        assert manager.logger.name == "src.core.vector_stores.collection_manager"

    @pytest.mark.asyncio
    async def test_create_collection_new(self, manager, mock_client):
        """Test creating a new collection."""
        collection_name = "test_collection"
        vector_size = 384

        # Mock no existing collections
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        result = await manager.create_collection(collection_name, vector_size)

        assert result is True
        mock_client.create_collection.assert_called_once_with(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    @pytest.mark.asyncio
    async def test_create_collection_existing(self, manager, mock_client):
        """Test creating collection that already exists."""
        collection_name = "existing_collection"

        # Mock existing collection
        existing_collection = Mock()
        existing_collection.name = collection_name
        mock_collections = Mock()
        mock_collections.collections = [existing_collection]
        mock_client.get_collections.return_value = mock_collections

        result = await manager.create_collection(collection_name)

        assert result is True
        mock_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_collection_error(self, manager, mock_client):
        """Test collection creation error handling."""
        collection_name = "error_collection"

        # Mock error in get_collections
        mock_client.get_collections.side_effect = Exception("Connection error")

        result = await manager.create_collection(collection_name)

        assert result is False

    @pytest.mark.asyncio
    async def test_create_all_collections_success(self, manager, mock_client):
        """Test creating all required collections successfully."""
        # Mock no existing collections
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        results = await manager.create_all_collections()

        assert isinstance(results, dict)
        assert len(results) == 4  # Four collection types
        assert all(result is True for result in results.values())
        assert mock_client.create_collection.call_count == 4

    @pytest.mark.asyncio
    async def test_create_all_collections_partial_failure(self, manager, mock_client):
        """Test creating collections with partial failures."""
        # Mock no existing collections
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        # Make one collection creation fail
        def side_effect(*args, **kwargs):
            if kwargs.get("collection_name") == "hyde_documents":
                raise Exception("Creation failed")

        mock_client.create_collection.side_effect = side_effect

        results = await manager.create_all_collections()

        assert isinstance(results, dict)
        assert len(results) == 4
        # hyde_documents should fail, others should succeed
        assert results["hyde_documents"] is False
        assert sum(1 for result in results.values() if result) == 3

    @pytest.mark.asyncio
    async def test_validate_collections_success(self, manager, mock_client):
        """Test validating existing collections."""
        # Mock collection info
        collection_info = Mock()
        collection_info.config.params.vectors.size = 384
        collection_info.config.params.vectors.distance.value = "cosine"
        collection_info.points_count = 100
        collection_info.segments_count = 1
        collection_info.status.value = "green"

        mock_client.get_collection.return_value = collection_info

        results = await manager.validate_collections()

        assert isinstance(results, dict)
        assert len(results) == 4  # Four required collections

        # Check that all collections are validated successfully
        for collection_name, validation_result in results.items():
            assert validation_result["exists"] is True
            assert validation_result["vector_size"] == 384
            assert validation_result["points_count"] == 100

    @pytest.mark.asyncio
    async def test_validate_collections_missing(self, manager, mock_client):
        """Test validating missing collections."""
        # Mock collection not found error
        mock_client.get_collection.side_effect = Exception("Collection not found")

        results = await manager.validate_collections()

        assert isinstance(results, dict)
        assert len(results) == 4

        # All collections should be marked as not existing
        for validation_result in results.values():
            assert validation_result["exists"] is False
            assert "error" in validation_result

    @pytest.mark.asyncio
    async def test_get_collection_stats_success(self, manager, mock_client):
        """Test getting collection statistics."""
        # Mock collections list
        collection1 = Mock()
        collection1.name = "test_collection_1"
        collection2 = Mock()
        collection2.name = "test_collection_2"

        mock_collections = Mock()
        mock_collections.collections = [collection1, collection2]
        mock_client.get_collections.return_value = mock_collections

        # Mock collection info
        collection_info = Mock()
        collection_info.points_count = 50
        collection_info.segments_count = 2
        collection_info.config.params.vectors.size = 384
        collection_info.config.params.vectors.distance.value = "cosine"
        collection_info.status.value = "green"

        mock_client.get_collection.return_value = collection_info

        stats = await manager.get_collection_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 2

        for collection_name, collection_stats in stats.items():
            assert collection_stats["points_count"] == 50
            assert collection_stats["segments_count"] == 2
            assert collection_stats["vector_size"] == 384
            assert collection_stats["distance"] == "cosine"
            assert collection_stats["status"] == "green"
            assert "disk_usage" in collection_stats

    @pytest.mark.asyncio
    async def test_get_collection_stats_error(self, manager, mock_client):
        """Test error handling in get_collection_stats."""
        mock_client.get_collections.side_effect = Exception("Client error")

        stats = await manager.get_collection_stats()

        assert stats == {}

    @pytest.mark.asyncio
    async def test_cleanup_empty_collections(self, manager, mock_client):
        """Test cleaning up empty collections."""
        # Mock collections list
        empty_collection = Mock()
        empty_collection.name = "empty_collection"
        non_empty_collection = Mock()
        non_empty_collection.name = "non_empty_collection"

        mock_collections = Mock()
        mock_collections.collections = [empty_collection, non_empty_collection]
        mock_client.get_collections.return_value = mock_collections

        # Mock collection info - one empty, one with points
        def get_collection_side_effect(collection_name):
            info = Mock()
            if collection_name == "empty_collection":
                info.points_count = 0
            else:
                info.points_count = 10
            return info

        mock_client.get_collection.side_effect = get_collection_side_effect

        results = await manager.cleanup_empty_collections()

        assert isinstance(results, dict)
        assert len(results) == 2
        assert results["empty_collection"] is True  # Should be deleted
        assert results["non_empty_collection"] is False  # Should be kept

        # Verify delete was called only for empty collection
        mock_client.delete_collection.assert_called_once_with("empty_collection")

    @pytest.mark.asyncio
    async def test_cleanup_empty_collections_error(self, manager, mock_client):
        """Test error handling in cleanup_empty_collections."""
        # Mock collections list
        collection = Mock()
        collection.name = "test_collection"

        mock_collections = Mock()
        mock_collections.collections = [collection]
        mock_client.get_collections.return_value = mock_collections

        # Mock error in get_collection
        mock_client.get_collection.side_effect = Exception("Collection error")

        results = await manager.cleanup_empty_collections()

        assert results["test_collection"] is False

    def test_default_vector_size_from_settings(self, manager, mock_client):
        """Test that default vector size comes from settings."""
        with patch("src.core.vector_stores.collection_manager.qdrant_settings") as mock_settings:
            mock_settings.vector_size = 512

            # Test create_collection with None vector_size
            manager_with_settings = QdrantCollectionManager(mock_client)

            # Mock no existing collections
            mock_collections = Mock()
            mock_collections.collections = []
            mock_client.get_collections.return_value = mock_collections

            # This should use the default from settings
            import asyncio

            result = asyncio.run(manager_with_settings.create_collection("test", None))

            # Verify it used the settings value
            mock_client.create_collection.assert_called_once()
            call_args = mock_client.create_collection.call_args
            assert call_args[1]["vectors_config"].size == 512
