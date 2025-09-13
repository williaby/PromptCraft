"""
Context7 MCP Server Integration

Specialized integration for the Context7 MCP server, providing document retrieval,
semantic search, and context management capabilities for PromptCraft.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import os
import time
from typing import Any

from src.utils.datetime_compat import utc_now
from src.utils.logging_mixin import LoggerMixin

from .message_router import MCPMessageRouter
from .protocol_handler import MCPProtocolError, MCPStandardErrors
from .tool_router import MCPToolRouter


logger = logging.getLogger(__name__)


@dataclass
class Context7Document:
    """Represents a document from Context7."""

    id: str
    title: str
    content: str
    url: str | None = None
    metadata: dict[str, Any] | None = None
    relevance_score: float = 0.0


@dataclass
class Context7SearchResult:
    """Results from Context7 search."""

    query: str
    documents: list[Context7Document]
    total_results: int
    search_time: float
    timestamp: datetime


class Context7Client(LoggerMixin):
    """Client for interacting with Context7 MCP server."""

    def __init__(self, message_router: MCPMessageRouter) -> None:
        super().__init__()
        self.message_router = message_router
        self.server_name = "context7"
        self.api_key = os.getenv("CONTEXT7_API_KEY", "")

        # Context7 specific configuration
        self.default_limit = 10
        self.max_limit = 50
        self.timeout = 30.0

    async def is_connected(self) -> bool:
        """Check if Context7 server is connected and available.

        Returns:
            True if connected and healthy
        """
        return self.server_name in self.message_router.list_connected_servers()

    async def search_documents(
        self,
        query: str,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> Context7SearchResult:
        """Search documents using Context7.

        Args:
            query: Search query
            limit: Maximum number of results
            filters: Additional search filters

        Returns:
            Search results from Context7
        """
        start_time = time.time()

        if not await self.is_connected():
            raise MCPProtocolError(
                MCPStandardErrors.SERVER_ERROR_START,
                "Context7 server not connected",
            )

        # Prepare search parameters
        limit = min(limit or self.default_limit, self.max_limit)
        search_params = {
            "query": query,
            "limit": limit,
        }

        if filters:
            search_params.update(filters)

        # Add API key if available
        if self.api_key:
            search_params["api_key"] = self.api_key

        try:
            # Call Context7 search tool
            result = await self.message_router.call_server_tool(
                self.server_name,
                "search",
                search_params,
            )

            # Parse results
            documents = []
            if result and "documents" in result:
                for doc_data in result["documents"]:
                    doc = Context7Document(
                        id=doc_data.get("id", ""),
                        title=doc_data.get("title", ""),
                        content=doc_data.get("content", ""),
                        url=doc_data.get("url"),
                        metadata=doc_data.get("metadata", {}),
                        relevance_score=doc_data.get("score", 0.0),
                    )
                    documents.append(doc)

            search_result = Context7SearchResult(
                query=query,
                documents=documents,
                total_results=result.get("total", len(documents)) if result else 0,
                search_time=time.time() - start_time,
                timestamp=utc_now(),
            )

            self.logger.info(
                f"Context7 search for '{query}': {len(documents)} results in {search_result.search_time:.2f}s",
            )
            return search_result

        except Exception as e:
            self.logger.error(f"Context7 search failed for '{query}': {e}")
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR,
                f"Context7 search failed: {e!s}",
            ) from e

    async def get_document(self, document_id: str) -> Context7Document | None:
        """Retrieve a specific document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document data or None if not found
        """
        if not await self.is_connected():
            raise MCPProtocolError(
                MCPStandardErrors.SERVER_ERROR_START,
                "Context7 server not connected",
            )

        try:
            result = await self.message_router.call_server_tool(
                self.server_name,
                "get_document",
                {"id": document_id},
            )

            if result and "document" in result:
                doc_data = result["document"]
                return Context7Document(
                    id=doc_data.get("id", document_id),
                    title=doc_data.get("title", ""),
                    content=doc_data.get("content", ""),
                    url=doc_data.get("url"),
                    metadata=doc_data.get("metadata", {}),
                    relevance_score=doc_data.get("score", 0.0),
                )

            return None

        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR,
                f"Failed to get document: {e!s}",
            ) from e

    async def get_collections(self) -> list[dict[str, Any]]:
        """Get available document collections.

        Returns:
            List of available collections
        """
        if not await self.is_connected():
            raise MCPProtocolError(
                MCPStandardErrors.SERVER_ERROR_START,
                "Context7 server not connected",
            )

        try:
            result = await self.message_router.call_server_tool(
                self.server_name,
                "list_collections",
                {},
            )

            return result.get("collections", []) if result else []

        except Exception as e:
            self.logger.error(f"Failed to get collections: {e}")
            return []

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on Context7 connection.

        Returns:
            Health status information
        """
        try:
            connected = await self.is_connected()

            if not connected:
                return {
                    "healthy": False,
                    "error": "Context7 server not connected",
                    "server_name": self.server_name,
                }

            # Try a simple ping or capability check
            server_info = self.message_router.get_server_info(self.server_name)
            if server_info:
                return {
                    "healthy": True,
                    "server_name": self.server_name,
                    "capabilities": server_info.capabilities,
                    "tools_count": len(server_info.tools),
                    "last_ping": server_info.last_ping.isoformat() if server_info.last_ping else None,
                }
            return {
                "healthy": False,
                "error": "No server info available",
                "server_name": self.server_name,
            }

        except Exception as e:
            self.logger.error(f"Context7 health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "server_name": self.server_name,
            }


class Context7Integration(LoggerMixin):
    """High-level integration for Context7 document retrieval in PromptCraft."""

    def __init__(self, message_router: MCPMessageRouter, tool_router: MCPToolRouter) -> None:
        super().__init__()
        self.message_router = message_router
        self.tool_router = tool_router
        self.context7_client = Context7Client(message_router)

        # Register Context7-specific tools
        self._register_context7_tools()

    def _register_context7_tools(self) -> None:
        """Register Context7-specific tools with the tool router."""
        # These tools will be added to the available tools list
        # when Context7 server connects

    async def enhanced_document_search(self, query: str, use_context7: bool = True, limit: int = 10) -> dict[str, Any]:
        """Enhanced document search using Context7 and local search.

        Args:
            query: Search query
            use_context7: Whether to use Context7 for search
            limit: Maximum number of results

        Returns:
            Combined search results
        """
        results: dict[str, Any] = {
            "query": query,
            "sources": [],
            "documents": [],
            "total_results": 0,
            "search_time": 0.0,
        }

        start_time = time.time()

        # Try Context7 search if available and requested
        context7_results = []
        if use_context7:
            try:
                context7_search = await self.context7_client.search_documents(query, limit)
                context7_results = context7_search.documents
                sources_list = results["sources"]
                assert isinstance(sources_list, list)
                sources_list.append(
                    {
                        "name": "Context7",
                        "count": len(context7_results),
                        "search_time": context7_search.search_time,
                    },
                )
                self.logger.info(f"Context7 returned {len(context7_results)} results")
            except Exception as e:
                self.logger.warning(f"Context7 search failed, falling back to local search: {e}")
                sources_list = results["sources"]
                assert isinstance(sources_list, list)
                sources_list.append(
                    {
                        "name": "Context7",
                        "count": 0,
                        "error": str(e),
                    },
                )

        # Fallback to local search
        local_results = []
        if not context7_results or len(context7_results) < limit:
            remaining_limit = limit - len(context7_results)
            try:
                local_search_result = await self.tool_router.execute_tool(
                    "search_documents",
                    {"query": query, "limit": remaining_limit},
                )

                if local_search_result.success and local_search_result.result:
                    # Parse local search results
                    local_content = local_search_result.result.get("content", [])
                    if local_content:
                        local_text = local_content[0].get("text", "")
                        # Create document-like objects from local results
                        local_doc = Context7Document(
                            id=f"local:{hash(query)}",
                            title=f"Local Search Results for '{query}'",
                            content=local_text,
                            metadata={"source": "local_search"},
                        )
                        local_results.append(local_doc)

                sources_list = results["sources"]
                assert isinstance(sources_list, list)
                sources_list.append(
                    {
                        "name": "Local Search",
                        "count": len(local_results),
                    },
                )
            except Exception as e:
                self.logger.error(f"Local search failed: {e}")
                sources_list = results["sources"]
                assert isinstance(sources_list, list)
                sources_list.append(
                    {
                        "name": "Local Search",
                        "count": 0,
                        "error": str(e),
                    },
                )

        # Combine and format results
        all_documents = context7_results + local_results
        results["documents"] = [
            {
                "id": doc.id,
                "title": doc.title,
                "content": doc.content[:1000] + "..." if len(doc.content) > 1000 else doc.content,
                "url": doc.url,
                "source": "Context7" if doc.id.startswith("ctx7:") else "Local",
                "relevance_score": doc.relevance_score,
                "metadata": doc.metadata,
            }
            for doc in all_documents[:limit]
        ]

        results["total_results"] = len(all_documents)
        results["search_time"] = time.time() - start_time

        sources_list = results["sources"]
        assert isinstance(sources_list, list)
        self.logger.info(
            f"Enhanced search for '{query}': {results['total_results']} results from {len(sources_list)} sources",
        )
        return results

    async def get_document_context(self, document_id: str) -> dict[str, Any] | None:
        """Get full context for a document.

        Args:
            document_id: Document identifier

        Returns:
            Document with full context
        """
        try:
            if document_id.startswith(("ctx7:", "context7:")):
                # Get from Context7
                doc = await self.context7_client.get_document(document_id)
                if doc:
                    return {
                        "id": doc.id,
                        "title": doc.title,
                        "content": doc.content,
                        "url": doc.url,
                        "metadata": doc.metadata,
                        "source": "Context7",
                    }
            # Try local document retrieval
            elif document_id.startswith("local:"):
                # Local document - would need to implement local document storage
                return {
                    "id": document_id,
                    "title": "Local Document",
                    "content": "Local document content retrieval not yet implemented",
                    "source": "Local",
                }

            return None

        except Exception as e:
            self.logger.error(f"Failed to get document context for {document_id}: {e}")
            return None

    async def status(self) -> dict[str, Any]:
        """Get Context7 integration status.

        Returns:
            Status information
        """
        context7_health = await self.context7_client.health_check()

        try:
            collections = await self.context7_client.get_collections()
        except Exception:
            collections = []

        return {
            "context7_connected": context7_health["healthy"],
            "context7_health": context7_health,
            "available_collections": len(collections),
            "collections": collections,
            "integration_ready": context7_health["healthy"],
            "message_router_connected": len(self.message_router.list_connected_servers()) > 0,
            "tool_router_tools": len(self.tool_router.get_available_tools()),
        }

    async def initialize(self) -> bool:
        """Initialize Context7 integration.

        Returns:
            True if initialization successful
        """
        try:
            # Check if Context7 server is available
            if await self.context7_client.is_connected():
                self.logger.info("Context7 server is connected and ready")

                # Refresh tool router to pick up Context7 tools
                self.tool_router.refresh_server_tools()

                return True
            self.logger.warning("Context7 server is not connected - integration will use fallback methods")
            return False

        except Exception as e:
            self.logger.error(f"Failed to initialize Context7 integration: {e}")
            return False
