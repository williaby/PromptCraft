"""
MCP Orchestrator

Unified orchestrator for end-to-end MCP communication workflow, integrating discovery,
connection, protocol communication, and tool execution into a single interface.
"""

from dataclasses import dataclass
import logging
from typing import Any

from src.utils.datetime_compat import to_iso, utc_now
from src.utils.logging_mixin import LoggerMixin

from .config_manager import MCPConfigurationManager
from .connection_bridge import ActiveConnection, MCPConnectionBridge
from .context7_integration import Context7Integration
from .message_router import MCPMessageRouter
from .smart_discovery import SmartMCPDiscovery
from .tool_router import MCPToolRouter


logger = logging.getLogger(__name__)


@dataclass
class MCPWorkflowResult:
    """Result of an MCP workflow execution."""
    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    workflow_steps: list[str] = None
    server_used: str | None = None


class MCPOrchestrator(LoggerMixin):
    """Orchestrates the complete MCP workflow from discovery to tool execution."""
    
    def __init__(self, config_manager: MCPConfigurationManager | None = None) -> None:
        super().__init__()
        
        # Initialize components
        self.config_manager = config_manager or MCPConfigurationManager(enable_discovery=True)
        self.discovery = self.config_manager.discovery or SmartMCPDiscovery()
        self.connection_bridge = self.config_manager.connection_bridge or MCPConnectionBridge(self.discovery)
        self.message_router = MCPMessageRouter()
        self.tool_router = MCPToolRouter(self.message_router)
        self.context7_integration = Context7Integration(self.message_router, self.tool_router)
        
        # Workflow state
        self.initialized = False
        self.connected_servers: dict[str, ActiveConnection] = {}
        
    async def initialize(self) -> bool:
        """Initialize the MCP orchestrator and all components.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing MCP Orchestrator...")
            
            # Initialize Context7 integration
            context7_ready = await self.context7_integration.initialize()
            if context7_ready:
                self.logger.info("Context7 integration initialized successfully")
            else:
                self.logger.warning("Context7 integration not available - using fallback methods")
            
            # Refresh available tools
            self.tool_router.refresh_server_tools()
            
            self.initialized = True
            self.logger.info("MCP Orchestrator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP Orchestrator: {e}")
            return False
    
    async def discover_and_connect(self, server_name: str, force_reconnect: bool = False) -> bool:
        """Discover and connect to an MCP server.
        
        Args:
            server_name: Name of the server to connect to
            force_reconnect: Whether to force reconnection if already connected
            
        Returns:
            True if connection successful
        """
        import time
        start_time = time.time()
        
        try:
            # Check if already connected
            if server_name in self.connected_servers and not force_reconnect:
                connection = self.connected_servers[server_name]
                if connection.health_status == "connected":
                    self.logger.debug(f"Already connected to {server_name}")
                    return True
            
            self.logger.info(f"Discovering and connecting to MCP server: {server_name}")
            
            # Step 1: Discovery
            self.logger.debug(f"Step 1: Discovering {server_name}")
            server_connection = await self.discovery.discover_server(server_name)
            
            if not server_connection:
                self.logger.error(f"Failed to discover server: {server_name}")
                return False
            
            self.logger.info(f"Discovered {server_name}: {server_connection.url} ({server_connection.type})")
            
            # Step 2: Connection Bridge
            self.logger.debug(f"Step 2: Establishing connection to {server_name}")
            active_connection = await self.connection_bridge.connect_to_server(server_name)
            
            if not active_connection:
                self.logger.error(f"Failed to establish connection to {server_name}")
                return False
            
            self.connected_servers[server_name] = active_connection
            
            # Step 3: Protocol Communication
            if server_connection.type == "npx" and active_connection.process:
                self.logger.debug(f"Step 3: Establishing protocol communication with {server_name}")
                protocol_success = await self.message_router.connect_server(server_name, active_connection)
                
                if protocol_success:
                    self.logger.info(f"Successfully established MCP protocol communication with {server_name}")
                    # Refresh tools after successful connection
                    self.tool_router.refresh_server_tools()
                else:
                    self.logger.warning(f"Protocol communication failed for {server_name}, but connection may still be usable")
            
            elapsed = time.time() - start_time
            self.logger.info(f"Connected to {server_name} in {elapsed:.2f}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to discover and connect to {server_name}: {e}")
            return False
    
    async def execute_workflow(self, workflow_type: str, parameters: dict[str, Any]) -> MCPWorkflowResult:
        """Execute a complete MCP workflow.
        
        Args:
            workflow_type: Type of workflow to execute
            parameters: Workflow parameters
            
        Returns:
            Workflow execution result
        """
        import time
        start_time = time.time()
        workflow_steps = []
        
        try:
            if workflow_type == "document_search":
                return await self._execute_document_search_workflow(parameters, workflow_steps)
            if workflow_type == "tool_execution":
                return await self._execute_tool_execution_workflow(parameters, workflow_steps)
            if workflow_type == "context7_search":
                return await self._execute_context7_search_workflow(parameters, workflow_steps)
            return MCPWorkflowResult(
                success=False,
                error=f"Unknown workflow type: {workflow_type}",
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
            )
                
        except Exception as e:
            self.logger.error(f"Workflow {workflow_type} failed: {e}")
            return MCPWorkflowResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
            )
    
    async def _execute_document_search_workflow(self, parameters: dict[str, Any], workflow_steps: list[str]) -> MCPWorkflowResult:
        """Execute document search workflow with Context7 integration.
        
        Args:
            parameters: Search parameters (query, limit, etc.)
            workflow_steps: List to track workflow steps
            
        Returns:
            Search workflow result
        """
        import time
        start_time = time.time()
        
        query = parameters.get("query", "")
        limit = parameters.get("limit", 10)
        use_context7 = parameters.get("use_context7", True)
        
        if not query:
            return MCPWorkflowResult(
                success=False,
                error="Query parameter required for document search",
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
            )
        
        try:
            workflow_steps.append("Starting document search workflow")
            
            # Ensure Context7 is connected if requested
            if use_context7:
                workflow_steps.append("Connecting to Context7 server")
                context7_connected = await self.discover_and_connect("context7")
                if not context7_connected:
                    self.logger.warning("Context7 connection failed, falling back to local search")
                    use_context7 = False
            
            # Execute enhanced search
            workflow_steps.append(f"Executing search for query: {query}")
            search_results = await self.context7_integration.enhanced_document_search(
                query=query,
                use_context7=use_context7,
                limit=limit,
            )
            
            workflow_steps.append(f"Search completed: {search_results['total_results']} results")
            
            return MCPWorkflowResult(
                success=True,
                result=search_results,
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
                server_used="context7" if use_context7 else "local",
            )
            
        except Exception as e:
            workflow_steps.append(f"Search failed: {e!s}")
            raise
    
    async def _execute_tool_execution_workflow(self, parameters: dict[str, Any], workflow_steps: list[str]) -> MCPWorkflowResult:
        """Execute tool execution workflow.
        
        Args:
            parameters: Tool execution parameters
            workflow_steps: List to track workflow steps
            
        Returns:
            Tool execution workflow result
        """
        import time
        start_time = time.time()
        
        tool_name = parameters.get("tool_name", "")
        tool_arguments = parameters.get("arguments", {})
        server_name = parameters.get("server_name")  # Optional specific server
        
        if not tool_name:
            return MCPWorkflowResult(
                success=False,
                error="tool_name parameter required",
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
            )
        
        try:
            workflow_steps.append(f"Starting tool execution workflow for: {tool_name}")
            
            # Connect to specific server if requested
            if server_name:
                workflow_steps.append(f"Connecting to server: {server_name}")
                connected = await self.discover_and_connect(server_name)
                if not connected:
                    return MCPWorkflowResult(
                        success=False,
                        error=f"Failed to connect to server: {server_name}",
                        execution_time=time.time() - start_time,
                        workflow_steps=workflow_steps,
                    )
            
            # Execute tool
            workflow_steps.append(f"Executing tool: {tool_name}")
            tool_result = await self.tool_router.execute_tool(tool_name, tool_arguments)
            
            workflow_steps.append(f"Tool execution {'succeeded' if tool_result.success else 'failed'}")
            
            return MCPWorkflowResult(
                success=tool_result.success,
                result=tool_result.result,
                error=tool_result.error,
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
                server_used=tool_result.server_name,
            )
            
        except Exception as e:
            workflow_steps.append(f"Tool execution failed: {e!s}")
            raise
    
    async def _execute_context7_search_workflow(self, parameters: dict[str, Any], workflow_steps: list[str]) -> MCPWorkflowResult:
        """Execute Context7-specific search workflow.
        
        Args:
            parameters: Context7 search parameters
            workflow_steps: List to track workflow steps
            
        Returns:
            Context7 search workflow result
        """
        import time
        start_time = time.time()
        
        query = parameters.get("query", "")
        limit = parameters.get("limit", 10)
        
        try:
            workflow_steps.append("Starting Context7 search workflow")
            
            # Ensure Context7 is connected
            workflow_steps.append("Discovering and connecting to Context7")
            connected = await self.discover_and_connect("context7")
            
            if not connected:
                return MCPWorkflowResult(
                    success=False,
                    error="Failed to connect to Context7 server",
                    execution_time=time.time() - start_time,
                    workflow_steps=workflow_steps,
                )
            
            # Execute Context7 search
            workflow_steps.append(f"Executing Context7 search for: {query}")
            search_result = await self.context7_integration.context7_client.search_documents(
                query=query,
                limit=limit,
            )
            
            workflow_steps.append(f"Context7 search completed: {len(search_result.documents)} results")
            
            # Format results
            formatted_results = {
                "query": search_result.query,
                "documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                        "url": doc.url,
                        "relevance_score": doc.relevance_score,
                        "metadata": doc.metadata,
                    }
                    for doc in search_result.documents
                ],
                "total_results": search_result.total_results,
                "search_time": search_result.search_time,
                "timestamp": search_result.timestamp.isoformat(),
            }
            
            return MCPWorkflowResult(
                success=True,
                result=formatted_results,
                execution_time=time.time() - start_time,
                workflow_steps=workflow_steps,
                server_used="context7",
            )
            
        except Exception as e:
            workflow_steps.append(f"Context7 search failed: {e!s}")
            raise
    
    async def get_comprehensive_status(self) -> dict[str, Any]:
        """Get comprehensive status of the MCP orchestrator and all components.
        
        Returns:
            Complete status information
        """
        try:
            # Connection bridge status
            bridge_status = await self.connection_bridge.get_connection_status()
            
            # Message router status
            router_status = self.message_router.get_status()
            
            # Tool router status
            tool_status = self.tool_router.get_status()
            
            # Context7 integration status
            context7_status = await self.context7_integration.status()
            
            # Configuration manager health
            config_health = await self.config_manager.health_check()
            
            return {
                "initialized": self.initialized,
                "orchestrator_healthy": self.initialized and config_health["healthy"],
                "connected_servers": len(self.connected_servers),
                "connection_bridge": bridge_status,
                "message_router": router_status,
                "tool_router": tool_status,
                "context7_integration": context7_status,
                "configuration": config_health,
                "available_workflows": [
                    "document_search",
                    "tool_execution", 
                    "context7_search",
                ],
                "timestamp": to_iso(utc_now()),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive status: {e}")
            return {
                "initialized": self.initialized,
                "orchestrator_healthy": False,
                "error": str(e),
                "timestamp": to_iso(utc_now()),
            }
    
    async def shutdown(self) -> None:
        """Shutdown the MCP orchestrator and clean up all resources."""
        self.logger.info("Shutting down MCP Orchestrator...")
        
        try:
            # Shutdown connection bridge
            if self.connection_bridge:
                await self.connection_bridge.shutdown()
            
            # Shutdown configuration manager
            if self.config_manager:
                await self.config_manager.shutdown()
            
            # Clear connected servers
            self.connected_servers.clear()
            
            self.initialized = False
            self.logger.info("MCP Orchestrator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during orchestrator shutdown: {e}")
    
    # Convenience methods for common workflows
    
    async def search_documents(self, query: str, limit: int = 10) -> MCPWorkflowResult:
        """Convenience method for document search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        return await self.execute_workflow("document_search", {
            "query": query,
            "limit": limit,
            "use_context7": True,
        })
    
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any], server_name: str | None = None) -> MCPWorkflowResult:
        """Convenience method for tool execution.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            server_name: Optional specific server to use
            
        Returns:
            Tool execution result
        """
        return await self.execute_workflow("tool_execution", {
            "tool_name": tool_name,
            "arguments": arguments,
            "server_name": server_name,
        })
    
    async def context7_search(self, query: str, limit: int = 10) -> MCPWorkflowResult:
        """Convenience method for Context7 search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Context7 search results
        """
        return await self.execute_workflow("context7_search", {
            "query": query,
            "limit": limit,
        })