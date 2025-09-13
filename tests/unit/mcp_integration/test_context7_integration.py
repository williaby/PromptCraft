"""
Comprehensive tests for Context7 MCP integration functionality.

Tests cover Context7Client and Context7Integration classes with full
method coverage including error handling, search operations, and tool integration.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.mcp_integration.context7_integration import (
    Context7Client,
    Context7Document,
    Context7Integration,
    Context7SearchResult,
)
from src.mcp_integration.message_router import MCPMessageRouter
from src.mcp_integration.protocol_handler import MCPProtocolError, MCPStandardErrors
from src.mcp_integration.tool_router import MCPToolRouter, ToolExecutionResult
from src.utils.datetime_compat import utc_now


class TestContext7Document:
    """Test Context7Document data class."""

    def test_document_creation_basic(self):
        """Test basic document creation."""
        doc = Context7Document(
            id="doc123",
            title="Test Document",
            content="This is test content",
        )

        assert doc.id == "doc123"
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.url is None
        assert doc.metadata is None
        assert doc.relevance_score == 0.0

    def test_document_creation_with_all_fields(self):
        """Test document creation with all fields."""
        metadata = {"category": "test", "author": "user"}
        doc = Context7Document(
            id="doc456",
            title="Full Document",
            content="Complete content",
            url="https://example.com/doc456",
            metadata=metadata,
            relevance_score=0.95,
        )

        assert doc.id == "doc456"
        assert doc.title == "Full Document"
        assert doc.content == "Complete content"
        assert doc.url == "https://example.com/doc456"
        assert doc.metadata == metadata
        assert doc.relevance_score == 0.95


class TestContext7SearchResult:
    """Test Context7SearchResult data class."""

    def test_search_result_creation(self):
        """Test search result creation."""
        documents = [
            Context7Document(id="1", title="Doc 1", content="Content 1"),
            Context7Document(id="2", title="Doc 2", content="Content 2"),
        ]

        timestamp = utc_now()
        result = Context7SearchResult(
            query="test query",
            documents=documents,
            total_results=2,
            search_time=1.5,
            timestamp=timestamp,
        )

        assert result.query == "test query"
        assert result.documents == documents
        assert result.total_results == 2
        assert result.search_time == 1.5
        assert result.timestamp == timestamp


class TestContext7Client:
    """Test Context7Client functionality."""

    @pytest.fixture
    def mock_message_router(self):
        """Create mock message router."""
        router = Mock(spec=MCPMessageRouter)
        router.list_connected_servers = Mock(return_value=["context7"])
        router.get_server_info = Mock()
        router.call_server_tool = AsyncMock()
        return router

    @pytest.fixture
    def context7_client(self, mock_message_router):
        """Create Context7Client with mock dependencies."""
        return Context7Client(mock_message_router)

    def test_initialization(self, mock_message_router):
        """Test Context7Client initialization."""
        client = Context7Client(mock_message_router)

        assert client.message_router == mock_message_router
        assert client.server_name == "context7"
        assert client.default_limit == 10
        assert client.max_limit == 50
        assert client.timeout == 30.0

    @pytest.mark.asyncio
    async def test_is_connected_true(self, context7_client, mock_message_router):
        """Test is_connected returns True when server is connected."""
        mock_message_router.list_connected_servers.return_value = ["context7", "other"]

        result = await context7_client.is_connected()

        assert result is True
        mock_message_router.list_connected_servers.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected_false(self, context7_client, mock_message_router):
        """Test is_connected returns False when server is not connected."""
        mock_message_router.list_connected_servers.return_value = ["other_server"]

        result = await context7_client.is_connected()

        assert result is False

    @pytest.mark.asyncio
    async def test_search_documents_success(self, context7_client, mock_message_router):
        """Test successful document search."""
        # Mock successful connection
        mock_message_router.list_connected_servers.return_value = ["context7"]

        # Mock search response
        mock_response = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "Test Doc 1",
                    "content": "Test content 1",
                    "url": "https://example.com/1",
                    "metadata": {"type": "test"},
                    "score": 0.9,
                },
                {
                    "id": "doc2",
                    "title": "Test Doc 2",
                    "content": "Test content 2",
                    "score": 0.8,
                },
            ],
            "total": 2,
        }
        mock_message_router.call_server_tool.return_value = mock_response

        result = await context7_client.search_documents("test query", limit=5)

        assert isinstance(result, Context7SearchResult)
        assert result.query == "test query"
        assert len(result.documents) == 2
        assert result.total_results == 2
        assert result.search_time > 0

        # Check first document
        doc1 = result.documents[0]
        assert doc1.id == "doc1"
        assert doc1.title == "Test Doc 1"
        assert doc1.content == "Test content 1"
        assert doc1.url == "https://example.com/1"
        assert doc1.metadata == {"type": "test"}
        assert doc1.relevance_score == 0.9

        # Verify call to message router
        mock_message_router.call_server_tool.assert_called_once_with(
            "context7",
            "search",
            {"query": "test query", "limit": 5},
        )

    @pytest.mark.asyncio
    async def test_search_documents_with_filters(self, context7_client, mock_message_router):
        """Test document search with filters."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.return_value = {"documents": [], "total": 0}

        filters = {"category": "technical", "date": "recent"}
        await context7_client.search_documents("query", limit=15, filters=filters)

        expected_params = {
            "query": "query",
            "limit": 15,
            "category": "technical",
            "date": "recent",
        }
        mock_message_router.call_server_tool.assert_called_once_with(
            "context7",
            "search",
            expected_params,
        )

    @pytest.mark.asyncio
    async def test_search_documents_with_api_key(self, context7_client, mock_message_router):
        """Test document search with API key."""
        # Set API key
        context7_client.api_key = "test_api_key"

        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.return_value = {"documents": [], "total": 0}

        await context7_client.search_documents("query")

        call_args = mock_message_router.call_server_tool.call_args[0][2]
        assert call_args["api_key"] == "test_api_key"

    @pytest.mark.asyncio
    async def test_search_documents_limit_enforcement(self, context7_client, mock_message_router):
        """Test that search limit is enforced to max_limit."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.return_value = {"documents": [], "total": 0}

        await context7_client.search_documents("query", limit=100)  # Above max_limit of 50

        call_args = mock_message_router.call_server_tool.call_args[0][2]
        assert call_args["limit"] == 50  # Should be capped at max_limit

    @pytest.mark.asyncio
    async def test_search_documents_not_connected(self, context7_client, mock_message_router):
        """Test search when server is not connected."""
        mock_message_router.list_connected_servers.return_value = ["other_server"]

        with pytest.raises(MCPProtocolError) as exc_info:
            await context7_client.search_documents("query")

        assert exc_info.value.code == MCPStandardErrors.SERVER_ERROR_START
        assert "Context7 server not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_documents_call_failure(self, context7_client, mock_message_router):
        """Test search when server call fails."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.side_effect = Exception("Server error")

        with pytest.raises(MCPProtocolError) as exc_info:
            await context7_client.search_documents("query")

        assert exc_info.value.code == MCPStandardErrors.INTERNAL_ERROR
        assert "Context7 search failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_documents_empty_response(self, context7_client, mock_message_router):
        """Test search with empty response."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.return_value = None

        result = await context7_client.search_documents("query")

        assert result.documents == []
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_get_document_success(self, context7_client, mock_message_router):
        """Test successful document retrieval."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_response = {
            "document": {
                "id": "doc123",
                "title": "Retrieved Doc",
                "content": "Retrieved content",
                "url": "https://example.com/doc123",
                "metadata": {"retrieved": True},
                "score": 1.0,
            },
        }
        mock_message_router.call_server_tool.return_value = mock_response

        result = await context7_client.get_document("doc123")

        assert isinstance(result, Context7Document)
        assert result.id == "doc123"
        assert result.title == "Retrieved Doc"
        assert result.content == "Retrieved content"
        assert result.url == "https://example.com/doc123"
        assert result.metadata == {"retrieved": True}
        assert result.relevance_score == 1.0

        mock_message_router.call_server_tool.assert_called_once_with(
            "context7",
            "get_document",
            {"id": "doc123"},
        )

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, context7_client, mock_message_router):
        """Test document retrieval when document not found."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.return_value = None

        result = await context7_client.get_document("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_not_connected(self, context7_client, mock_message_router):
        """Test document retrieval when not connected."""
        mock_message_router.list_connected_servers.return_value = []

        with pytest.raises(MCPProtocolError) as exc_info:
            await context7_client.get_document("doc123")

        assert exc_info.value.code == MCPStandardErrors.SERVER_ERROR_START
        assert "Context7 server not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_document_error(self, context7_client, mock_message_router):
        """Test document retrieval error handling."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.side_effect = Exception("Retrieval error")

        with pytest.raises(MCPProtocolError) as exc_info:
            await context7_client.get_document("doc123")

        assert exc_info.value.code == MCPStandardErrors.INTERNAL_ERROR
        assert "Failed to get document" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_collections_success(self, context7_client, mock_message_router):
        """Test successful collections retrieval."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_response = {
            "collections": [
                {"id": "coll1", "name": "Collection 1"},
                {"id": "coll2", "name": "Collection 2"},
            ],
        }
        mock_message_router.call_server_tool.return_value = mock_response

        result = await context7_client.get_collections()

        assert len(result) == 2
        assert result[0]["id"] == "coll1"
        assert result[1]["name"] == "Collection 2"

    @pytest.mark.asyncio
    async def test_get_collections_not_connected(self, context7_client, mock_message_router):
        """Test collections retrieval when not connected."""
        mock_message_router.list_connected_servers.return_value = []

        with pytest.raises(MCPProtocolError):
            await context7_client.get_collections()

    @pytest.mark.asyncio
    async def test_get_collections_error(self, context7_client, mock_message_router):
        """Test collections retrieval error handling."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.call_server_tool.side_effect = Exception("Collections error")

        result = await context7_client.get_collections()

        assert result == []

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, context7_client, mock_message_router):
        """Test health check when server is healthy."""
        mock_message_router.list_connected_servers.return_value = ["context7"]

        # Mock server info
        mock_server_info = Mock()
        mock_server_info.capabilities = {"search": True, "documents": True}
        mock_server_info.tools = ["search", "get_document"]
        mock_server_info.last_ping = utc_now()
        mock_message_router.get_server_info.return_value = mock_server_info

        result = await context7_client.health_check()

        assert result["healthy"] is True
        assert result["server_name"] == "context7"
        assert result["capabilities"] == {"search": True, "documents": True}
        assert result["tools_count"] == 2
        assert "last_ping" in result

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, context7_client, mock_message_router):
        """Test health check when server is not connected."""
        mock_message_router.list_connected_servers.return_value = []

        result = await context7_client.health_check()

        assert result["healthy"] is False
        assert result["error"] == "Context7 server not connected"
        assert result["server_name"] == "context7"

    @pytest.mark.asyncio
    async def test_health_check_no_server_info(self, context7_client, mock_message_router):
        """Test health check when server info is not available."""
        mock_message_router.list_connected_servers.return_value = ["context7"]
        mock_message_router.get_server_info.return_value = None

        result = await context7_client.health_check()

        assert result["healthy"] is False
        assert result["error"] == "No server info available"

    @pytest.mark.asyncio
    async def test_health_check_exception(self, context7_client, mock_message_router):
        """Test health check exception handling."""
        mock_message_router.list_connected_servers.side_effect = Exception("Health check error")

        result = await context7_client.health_check()

        assert result["healthy"] is False
        assert result["error"] == "Health check error"


class TestContext7Integration:
    """Test Context7Integration functionality."""

    @pytest.fixture
    def mock_message_router(self):
        """Create mock message router."""
        router = Mock(spec=MCPMessageRouter)
        router.list_connected_servers = Mock(return_value=[])
        return router

    @pytest.fixture
    def mock_tool_router(self):
        """Create mock tool router."""
        router = Mock(spec=MCPToolRouter)
        router.get_available_tools = Mock(return_value=[])
        router.execute_tool = AsyncMock()
        return router

    @pytest.fixture
    def context7_integration(self, mock_message_router, mock_tool_router):
        """Create Context7Integration with mock dependencies."""
        return Context7Integration(mock_message_router, mock_tool_router)

    def test_initialization(self, mock_message_router, mock_tool_router):
        """Test Context7Integration initialization."""
        integration = Context7Integration(mock_message_router, mock_tool_router)

        assert integration.message_router == mock_message_router
        assert integration.tool_router == mock_tool_router
        assert integration.context7_client is not None

    @pytest.mark.asyncio
    async def test_enhanced_document_search_context7_success(self, context7_integration, mock_tool_router):
        """Test enhanced search with successful Context7 results."""
        # Mock Context7 search - return enough results to meet the limit
        mock_docs = [
            Context7Document(
                id=f"ctx7:doc{i}",
                title=f"Context7 Doc {i}",
                content=f"Context7 content {i}",
                relevance_score=0.9 - i * 0.1,
            )
            for i in range(1, 4)  # 3 documents
        ]
        mock_search_result = Context7SearchResult(
            query="test query",
            documents=mock_docs,
            total_results=3,
            search_time=0.5,
            timestamp=utc_now(),
        )

        context7_integration.context7_client.search_documents = AsyncMock(return_value=mock_search_result)

        # Mock local search (it shouldn't be called if Context7 returns enough results)
        local_result = ToolExecutionResult(success=True, result={"content": [{"text": "Local results"}]})
        mock_tool_router.execute_tool.return_value = local_result

        result = await context7_integration.enhanced_document_search("test query", limit=3)

        assert result["query"] == "test query"
        assert len(result["documents"]) == 3
        assert result["total_results"] == 3
        # Should only have Context7 source since it satisfied the limit
        assert len(result["sources"]) == 1
        assert result["sources"][0]["name"] == "Context7"
        assert result["sources"][0]["count"] == 3

    @pytest.mark.asyncio
    async def test_enhanced_document_search_context7_fallback(self, context7_integration, mock_tool_router):
        """Test enhanced search with Context7 failure and local fallback."""
        # Mock Context7 failure
        context7_integration.context7_client.search_documents = AsyncMock(
            side_effect=Exception("Context7 failed"),
        )

        # Mock local search success
        local_result = ToolExecutionResult(
            success=True,
            result={
                "content": [{"text": "Local search results for test query"}],
            },
        )
        mock_tool_router.execute_tool.return_value = local_result

        result = await context7_integration.enhanced_document_search("test query", limit=5)

        assert result["query"] == "test query"
        assert len(result["documents"]) == 1
        assert result["documents"][0]["source"] == "Local"
        assert len(result["sources"]) == 2  # Context7 (failed) and Local Search
        assert result["sources"][0]["name"] == "Context7"
        assert result["sources"][0]["count"] == 0
        assert "error" in result["sources"][0]

    @pytest.mark.asyncio
    async def test_enhanced_document_search_no_context7(self, context7_integration, mock_tool_router):
        """Test enhanced search without using Context7."""
        # Mock local search
        local_result = ToolExecutionResult(
            success=True,
            result={
                "content": [{"text": "Local results only"}],
            },
        )
        mock_tool_router.execute_tool.return_value = local_result

        result = await context7_integration.enhanced_document_search(
            "test query",
            use_context7=False,
            limit=3,
        )

        assert result["query"] == "test query"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["name"] == "Local Search"

    @pytest.mark.asyncio
    async def test_enhanced_document_search_local_fallback_failure(self, context7_integration, mock_tool_router):
        """Test enhanced search when both Context7 and local search fail."""
        # Mock Context7 failure
        context7_integration.context7_client.search_documents = AsyncMock(
            side_effect=Exception("Context7 failed"),
        )

        # Mock local search failure
        mock_tool_router.execute_tool.side_effect = Exception("Local search failed")

        result = await context7_integration.enhanced_document_search("test query", limit=5)

        assert result["query"] == "test query"
        assert result["total_results"] == 0
        assert len(result["sources"]) == 2
        assert all("error" in source for source in result["sources"])

    @pytest.mark.asyncio
    async def test_get_document_context_context7(self, context7_integration):
        """Test getting document context from Context7."""
        mock_doc = Context7Document(
            id="ctx7:doc123",
            title="Context7 Document",
            content="Full context content",
            url="https://example.com/doc123",
            metadata={"type": "context7"},
        )

        context7_integration.context7_client.get_document = AsyncMock(return_value=mock_doc)

        result = await context7_integration.get_document_context("ctx7:doc123")

        assert result["id"] == "ctx7:doc123"
        assert result["title"] == "Context7 Document"
        assert result["content"] == "Full context content"
        assert result["source"] == "Context7"
        assert result["metadata"] == {"type": "context7"}

    @pytest.mark.asyncio
    async def test_get_document_context_local(self, context7_integration):
        """Test getting document context for local document."""
        result = await context7_integration.get_document_context("local:doc456")

        assert result["id"] == "local:doc456"
        assert result["title"] == "Local Document"
        assert result["source"] == "Local"
        assert "not yet implemented" in result["content"]

    @pytest.mark.asyncio
    async def test_get_document_context_not_found(self, context7_integration):
        """Test getting document context when document not found."""
        context7_integration.context7_client.get_document = AsyncMock(return_value=None)

        result = await context7_integration.get_document_context("context7:nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_context_error(self, context7_integration):
        """Test error handling in get_document_context."""
        context7_integration.context7_client.get_document = AsyncMock(
            side_effect=Exception("Document error"),
        )

        result = await context7_integration.get_document_context("ctx7:doc123")

        assert result is None

    @pytest.mark.asyncio
    async def test_status(self, context7_integration):
        """Test status method."""
        # Mock health check
        health_result = {
            "healthy": True,
            "server_name": "context7",
            "capabilities": {"search": True},
        }
        context7_integration.context7_client.health_check = AsyncMock(return_value=health_result)

        # Mock collections
        collections = [{"id": "coll1", "name": "Collection 1"}]
        context7_integration.context7_client.get_collections = AsyncMock(return_value=collections)

        result = await context7_integration.status()

        assert result["context7_connected"] is True
        assert result["context7_health"] == health_result
        assert result["available_collections"] == 1
        assert result["collections"] == collections
        assert result["integration_ready"] is True

    @pytest.mark.asyncio
    async def test_status_collections_error(self, context7_integration):
        """Test status method when collections retrieval fails."""
        health_result = {"healthy": True}
        context7_integration.context7_client.health_check = AsyncMock(return_value=health_result)
        context7_integration.context7_client.get_collections = AsyncMock(
            side_effect=Exception("Collections error"),
        )

        result = await context7_integration.status()

        assert result["available_collections"] == 0
        assert result["collections"] == []

    @pytest.mark.asyncio
    async def test_initialize_success(self, context7_integration):
        """Test successful initialization."""
        context7_integration.context7_client.is_connected = AsyncMock(return_value=True)
        context7_integration.tool_router.refresh_server_tools = Mock()

        result = await context7_integration.initialize()

        assert result is True
        context7_integration.tool_router.refresh_server_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_not_connected(self, context7_integration):
        """Test initialization when Context7 is not connected."""
        context7_integration.context7_client.is_connected = AsyncMock(return_value=False)

        result = await context7_integration.initialize()

        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_error(self, context7_integration):
        """Test initialization error handling."""
        context7_integration.context7_client.is_connected = AsyncMock(
            side_effect=Exception("Connection error"),
        )

        result = await context7_integration.initialize()

        assert result is False

    def test_register_context7_tools(self, context7_integration):
        """Test _register_context7_tools method (currently empty)."""
        # This method is currently a pass, but we test it exists and can be called
        context7_integration._register_context7_tools()
        # No assertions needed as method is currently empty
