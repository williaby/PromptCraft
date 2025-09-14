"""
Tests for MCP Orchestrator
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_integration.config_manager import MCPConfigurationManager
from src.mcp_integration.connection_bridge import ActiveConnection
from src.mcp_integration.context7_integration import Context7Document, Context7SearchResult
from src.mcp_integration.mcp_orchestrator import (
    MCPOrchestrator,
    MCPWorkflowResult,
)
from src.mcp_integration.tool_router import ToolExecutionResult
from src.utils.datetime_compat import utc_now


class TestMCPWorkflowResult:
    """Test MCPWorkflowResult dataclass."""

    def test_workflow_result_default_values(self):
        """Test MCPWorkflowResult with default values."""
        result = MCPWorkflowResult(success=True)

        assert result.success is True
        assert result.result is None
        assert result.error is None
        assert result.execution_time == 0.0
        assert result.workflow_steps is None
        assert result.server_used is None

    def test_workflow_result_with_values(self):
        """Test MCPWorkflowResult with custom values."""
        steps = ["step1", "step2"]
        result = MCPWorkflowResult(
            success=False,
            result={"data": "test"},
            error="Test error",
            execution_time=1.5,
            workflow_steps=steps,
            server_used="test_server",
        )

        assert result.success is False
        assert result.result == {"data": "test"}
        assert result.error == "Test error"
        assert result.execution_time == 1.5
        assert result.workflow_steps == steps
        assert result.server_used == "test_server"


class TestMCPOrchestratorInitialization:
    """Test MCP Orchestrator initialization."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager."""
        config = MagicMock(spec=MCPConfigurationManager)
        config.discovery = MagicMock()
        config.connection_bridge = MagicMock()
        return config

    def test_orchestrator_initialization_with_config(self, mock_config_manager):
        """Test orchestrator initialization with config manager."""
        orchestrator = MCPOrchestrator(mock_config_manager)

        assert orchestrator.config_manager == mock_config_manager
        assert orchestrator.discovery == mock_config_manager.discovery
        assert orchestrator.connection_bridge == mock_config_manager.connection_bridge
        assert hasattr(orchestrator, "message_router")
        assert hasattr(orchestrator, "tool_router")
        assert hasattr(orchestrator, "context7_integration")
        assert orchestrator.initialized is False
        assert isinstance(orchestrator.connected_servers, dict)
        assert len(orchestrator.connected_servers) == 0

    def test_orchestrator_initialization_default_config(self):
        """Test orchestrator initialization with default config."""
        with patch("src.mcp_integration.mcp_orchestrator.MCPConfigurationManager") as mock_config_cls:
            with patch("src.mcp_integration.mcp_orchestrator.SmartMCPDiscovery"):
                with patch("src.mcp_integration.mcp_orchestrator.MCPConnectionBridge"):
                    mock_config = MagicMock()
                    mock_config.discovery = None
                    mock_config.connection_bridge = None
                    mock_config_cls.return_value = mock_config

                    orchestrator = MCPOrchestrator()

        assert orchestrator.config_manager == mock_config
        assert hasattr(orchestrator, "discovery")
        assert hasattr(orchestrator, "connection_bridge")

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful orchestrator initialization."""
        orchestrator = MCPOrchestrator()

        # Mock the dependencies
        orchestrator.context7_integration = MagicMock()
        orchestrator.context7_integration.initialize = AsyncMock(return_value=True)
        orchestrator.tool_router = MagicMock()
        orchestrator.tool_router.refresh_server_tools = MagicMock()

        result = await orchestrator.initialize()

        assert result is True
        assert orchestrator.initialized is True
        orchestrator.context7_integration.initialize.assert_called_once()
        orchestrator.tool_router.refresh_server_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_context7_warning(self):
        """Test initialization with Context7 warning."""
        orchestrator = MCPOrchestrator()

        # Mock Context7 initialization failure
        orchestrator.context7_integration = MagicMock()
        orchestrator.context7_integration.initialize = AsyncMock(return_value=False)
        orchestrator.tool_router = MagicMock()
        orchestrator.tool_router.refresh_server_tools = MagicMock()

        result = await orchestrator.initialize()

        assert result is True
        assert orchestrator.initialized is True

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test initialization failure."""
        orchestrator = MCPOrchestrator()

        # Mock initialization to raise exception
        orchestrator.context7_integration = MagicMock()
        orchestrator.context7_integration.initialize = AsyncMock(side_effect=Exception("Init failed"))

        result = await orchestrator.initialize()

        assert result is False
        assert orchestrator.initialized is False


class TestConnectionAndDiscovery:
    """Test connection and discovery functionality."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator fixture."""
        orch = MCPOrchestrator()
        orch.discovery = MagicMock()
        orch.connection_bridge = MagicMock()
        orch.message_router = MagicMock()
        orch.tool_router = MagicMock()
        return orch

    @pytest.mark.asyncio
    async def test_discover_and_connect_already_connected(self, orchestrator):
        """Test connection when already connected."""
        # Mock existing connection
        mock_connection = MagicMock(spec=ActiveConnection)
        mock_connection.health_status = "connected"
        orchestrator.connected_servers["test_server"] = mock_connection

        result = await orchestrator.discover_and_connect("test_server")

        assert result is True
        # Should not call discovery since already connected
        orchestrator.discovery.discover_server.assert_not_called()

    @pytest.mark.asyncio
    async def test_discover_and_connect_force_reconnect(self, orchestrator):
        """Test force reconnection."""
        # Mock existing connection
        mock_connection = MagicMock(spec=ActiveConnection)
        mock_connection.health_status = "connected"
        orchestrator.connected_servers["test_server"] = mock_connection

        # Mock discovery and connection
        mock_server_connection = MagicMock()
        mock_server_connection.type = "npx"
        mock_server_connection.url = "npx://test"
        orchestrator.discovery.discover_server = AsyncMock(return_value=mock_server_connection)

        mock_active_connection = MagicMock(spec=ActiveConnection)
        mock_active_connection.process = MagicMock()
        orchestrator.connection_bridge.connect_to_server = AsyncMock(return_value=mock_active_connection)

        orchestrator.message_router.connect_server = AsyncMock(return_value=True)
        orchestrator.tool_router.refresh_server_tools = MagicMock()

        result = await orchestrator.discover_and_connect("test_server", force_reconnect=True)

        assert result is True
        orchestrator.discovery.discover_server.assert_called_once_with("test_server")

    @pytest.mark.asyncio
    async def test_discover_and_connect_discovery_failed(self, orchestrator):
        """Test connection when discovery fails."""
        orchestrator.discovery.discover_server = AsyncMock(return_value=None)

        result = await orchestrator.discover_and_connect("test_server")

        assert result is False

    @pytest.mark.asyncio
    async def test_discover_and_connect_connection_failed(self, orchestrator):
        """Test connection when connection bridge fails."""
        # Mock successful discovery but failed connection
        mock_server_connection = MagicMock()
        mock_server_connection.type = "npx"
        mock_server_connection.url = "npx://test"
        orchestrator.discovery.discover_server = AsyncMock(return_value=mock_server_connection)
        orchestrator.connection_bridge.connect_to_server = AsyncMock(return_value=None)

        result = await orchestrator.discover_and_connect("test_server")

        assert result is False

    @pytest.mark.asyncio
    async def test_discover_and_connect_successful_npx(self, orchestrator):
        """Test successful NPX server connection."""
        # Mock discovery
        mock_server_connection = MagicMock()
        mock_server_connection.type = "npx"
        mock_server_connection.url = "npx://test"
        orchestrator.discovery.discover_server = AsyncMock(return_value=mock_server_connection)

        # Mock connection
        mock_active_connection = MagicMock(spec=ActiveConnection)
        mock_active_connection.process = MagicMock()
        orchestrator.connection_bridge.connect_to_server = AsyncMock(return_value=mock_active_connection)

        # Mock protocol communication
        orchestrator.message_router.connect_server = AsyncMock(return_value=True)
        orchestrator.tool_router.refresh_server_tools = MagicMock()

        result = await orchestrator.discover_and_connect("test_server")

        assert result is True
        assert "test_server" in orchestrator.connected_servers
        orchestrator.message_router.connect_server.assert_called_once()
        orchestrator.tool_router.refresh_server_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_and_connect_protocol_warning(self, orchestrator):
        """Test connection with protocol communication warning."""
        # Mock discovery and connection
        mock_server_connection = MagicMock()
        mock_server_connection.type = "npx"
        mock_server_connection.url = "npx://test"
        orchestrator.discovery.discover_server = AsyncMock(return_value=mock_server_connection)

        mock_active_connection = MagicMock(spec=ActiveConnection)
        mock_active_connection.process = MagicMock()
        orchestrator.connection_bridge.connect_to_server = AsyncMock(return_value=mock_active_connection)

        # Mock protocol communication failure
        orchestrator.message_router.connect_server = AsyncMock(return_value=False)

        result = await orchestrator.discover_and_connect("test_server")

        assert result is True  # Still succeeds despite protocol warning
        assert "test_server" in orchestrator.connected_servers

    @pytest.mark.asyncio
    async def test_discover_and_connect_exception(self, orchestrator):
        """Test connection with exception."""
        orchestrator.discovery.discover_server = AsyncMock(side_effect=Exception("Discovery error"))

        result = await orchestrator.discover_and_connect("test_server")

        assert result is False


class TestWorkflowExecution:
    """Test workflow execution methods."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator fixture."""
        orch = MCPOrchestrator()
        orch.context7_integration = MagicMock()
        orch.tool_router = MagicMock()
        return orch

    @pytest.mark.asyncio
    async def test_execute_workflow_unknown_type(self, orchestrator):
        """Test executing unknown workflow type."""
        result = await orchestrator.execute_workflow("unknown_type", {})

        assert result.success is False
        assert "Unknown workflow type" in result.error
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_workflow_exception(self, orchestrator):
        """Test workflow execution with exception."""
        # Mock method to raise exception
        with patch.object(orchestrator, "_execute_document_search_workflow", side_effect=Exception("Test error")):
            result = await orchestrator.execute_workflow("document_search", {"query": "test"})

        assert result.success is False
        assert "Test error" in result.error
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_document_search_workflow_no_query(self, orchestrator):
        """Test document search workflow without query."""
        result = await orchestrator._execute_document_search_workflow({}, [])

        assert result.success is False
        assert "Query parameter required" in result.error

    @pytest.mark.asyncio
    async def test_execute_document_search_workflow_success(self, orchestrator):
        """Test successful document search workflow."""
        parameters = {"query": "test query", "limit": 5, "use_context7": True}
        workflow_steps = []

        # Mock connection
        with patch.object(orchestrator, "discover_and_connect", return_value=True):
            # Mock search results
            mock_search_results = {
                "total_results": 2,
                "documents": ["doc1", "doc2"],
                "search_time": 0.5,
            }
            orchestrator.context7_integration.enhanced_document_search = AsyncMock(return_value=mock_search_results)

            result = await orchestrator._execute_document_search_workflow(parameters, workflow_steps)

        assert result.success is True
        assert result.result == mock_search_results
        assert result.server_used == "context7"
        assert len(workflow_steps) == 4
        orchestrator.context7_integration.enhanced_document_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_document_search_workflow_context7_fallback(self, orchestrator):
        """Test document search workflow with Context7 fallback."""
        parameters = {"query": "test query", "use_context7": True}
        workflow_steps = []

        # Mock connection failure - should fallback
        with patch.object(orchestrator, "discover_and_connect", return_value=False):
            mock_search_results = {
                "total_results": 1,
                "documents": ["doc1"],
            }
            orchestrator.context7_integration.enhanced_document_search = AsyncMock(return_value=mock_search_results)

            result = await orchestrator._execute_document_search_workflow(parameters, workflow_steps)

        assert result.success is True
        assert result.server_used == "local"
        # Should be called with use_context7=False after fallback
        call_args = orchestrator.context7_integration.enhanced_document_search.call_args
        assert call_args[1]["use_context7"] is False

    @pytest.mark.asyncio
    async def test_execute_tool_execution_workflow_no_tool_name(self, orchestrator):
        """Test tool execution workflow without tool name."""
        result = await orchestrator._execute_tool_execution_workflow({}, [])

        assert result.success is False
        assert "tool_name parameter required" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_execution_workflow_success(self, orchestrator):
        """Test successful tool execution workflow."""
        parameters = {
            "tool_name": "test_tool",
            "arguments": {"arg1": "value1"},
            "server_name": "test_server",
        }
        workflow_steps = []

        # Mock connection
        with patch.object(orchestrator, "discover_and_connect", return_value=True):
            # Mock tool execution
            mock_tool_result = ToolExecutionResult(
                success=True,
                result={"output": "success"},
                server_name="test_server",
            )
            orchestrator.tool_router.execute_tool = AsyncMock(return_value=mock_tool_result)

            result = await orchestrator._execute_tool_execution_workflow(parameters, workflow_steps)

        assert result.success is True
        assert result.result == {"output": "success"}
        assert result.server_used == "test_server"
        assert len(workflow_steps) == 4
        orchestrator.tool_router.execute_tool.assert_called_once_with("test_tool", {"arg1": "value1"})

    @pytest.mark.asyncio
    async def test_execute_tool_execution_workflow_connection_failed(self, orchestrator):
        """Test tool execution workflow with connection failure."""
        parameters = {
            "tool_name": "test_tool",
            "arguments": {},
            "server_name": "test_server",
        }
        workflow_steps = []

        # Mock connection failure
        with patch.object(orchestrator, "discover_and_connect", return_value=False):
            result = await orchestrator._execute_tool_execution_workflow(parameters, workflow_steps)

        assert result.success is False
        assert "Failed to connect to server" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_execution_workflow_no_server(self, orchestrator):
        """Test tool execution workflow without specific server."""
        parameters = {
            "tool_name": "test_tool",
            "arguments": {"arg1": "value1"},
        }
        workflow_steps = []

        # Mock tool execution
        mock_tool_result = ToolExecutionResult(
            success=True,
            result={"output": "success"},
            server_name="promptcraft",
        )
        orchestrator.tool_router.execute_tool = AsyncMock(return_value=mock_tool_result)

        result = await orchestrator._execute_tool_execution_workflow(parameters, workflow_steps)

        assert result.success is True
        # Should not call discover_and_connect since no specific server
        assert len(workflow_steps) == 3

    @pytest.mark.asyncio
    async def test_execute_context7_search_workflow_success(self, orchestrator):
        """Test successful Context7 search workflow."""
        parameters = {"query": "test query", "limit": 5}
        workflow_steps = []

        # Mock connection
        with patch.object(orchestrator, "discover_and_connect", return_value=True):
            # Mock Context7 search results
            mock_doc = Context7Document(
                id="doc1",
                title="Test Document",
                content="This is test content" * 50,  # Long content to test truncation
                url="https://example.com",
                relevance_score=0.95,
                metadata={"type": "test"},
            )

            mock_search_result = Context7SearchResult(
                query="test query",
                documents=[mock_doc],
                total_results=1,
                search_time=0.5,
                timestamp=utc_now(),
            )

            orchestrator.context7_integration.context7_client = MagicMock()
            orchestrator.context7_integration.context7_client.search_documents = AsyncMock(
                return_value=mock_search_result,
            )

            result = await orchestrator._execute_context7_search_workflow(parameters, workflow_steps)

        assert result.success is True
        assert result.server_used == "context7"
        assert "documents" in result.result
        assert len(result.result["documents"]) == 1
        assert result.result["documents"][0]["title"] == "Test Document"
        # Check content truncation
        assert result.result["documents"][0]["content"].endswith("...")
        assert len(workflow_steps) == 4

    @pytest.mark.asyncio
    async def test_execute_context7_search_workflow_connection_failed(self, orchestrator):
        """Test Context7 search workflow with connection failure."""
        parameters = {"query": "test query"}
        workflow_steps = []

        # Mock connection failure
        with patch.object(orchestrator, "discover_and_connect", return_value=False):
            result = await orchestrator._execute_context7_search_workflow(parameters, workflow_steps)

        assert result.success is False
        assert "Failed to connect to Context7 server" in result.error


class TestConvenienceMethods:
    """Test convenience methods."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator fixture."""
        return MCPOrchestrator()

    @pytest.mark.asyncio
    async def test_search_documents(self, orchestrator):
        """Test search_documents convenience method."""
        with patch.object(orchestrator, "execute_workflow") as mock_execute:
            mock_result = MCPWorkflowResult(success=True)
            mock_execute.return_value = mock_result

            result = await orchestrator.search_documents("test query", 15)

            assert result == mock_result
            mock_execute.assert_called_once_with(
                "document_search",
                {
                    "query": "test query",
                    "limit": 15,
                    "use_context7": True,
                },
            )

    @pytest.mark.asyncio
    async def test_execute_tool(self, orchestrator):
        """Test execute_tool convenience method."""
        with patch.object(orchestrator, "execute_workflow") as mock_execute:
            mock_result = MCPWorkflowResult(success=True)
            mock_execute.return_value = mock_result

            result = await orchestrator.execute_tool("test_tool", {"arg": "value"}, "server")

            assert result == mock_result
            mock_execute.assert_called_once_with(
                "tool_execution",
                {
                    "tool_name": "test_tool",
                    "arguments": {"arg": "value"},
                    "server_name": "server",
                },
            )

    @pytest.mark.asyncio
    async def test_execute_tool_no_server(self, orchestrator):
        """Test execute_tool convenience method without server."""
        with patch.object(orchestrator, "execute_workflow") as mock_execute:
            mock_result = MCPWorkflowResult(success=True)
            mock_execute.return_value = mock_result

            result = await orchestrator.execute_tool("test_tool", {"arg": "value"})

            assert result == mock_result
            call_args = mock_execute.call_args[0][1]
            assert call_args["server_name"] is None

    @pytest.mark.asyncio
    async def test_context7_search(self, orchestrator):
        """Test context7_search convenience method."""
        with patch.object(orchestrator, "execute_workflow") as mock_execute:
            mock_result = MCPWorkflowResult(success=True)
            mock_execute.return_value = mock_result

            result = await orchestrator.context7_search("test query", 20)

            assert result == mock_result
            mock_execute.assert_called_once_with(
                "context7_search",
                {
                    "query": "test query",
                    "limit": 20,
                },
            )


class TestStatusAndLifecycle:
    """Test status and lifecycle methods."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator fixture."""
        orch = MCPOrchestrator()
        orch.initialized = True
        orch.connection_bridge = MagicMock()
        orch.message_router = MagicMock()
        orch.tool_router = MagicMock()
        orch.context7_integration = MagicMock()
        orch.config_manager = MagicMock()
        return orch

    @pytest.mark.asyncio
    async def test_get_comprehensive_status_success(self, orchestrator):
        """Test getting comprehensive status successfully."""
        # Mock all status calls
        bridge_status = {"active_connections": 2}
        router_status = {"connected_servers": 2}
        tool_status = {"total_tools": 10}
        context7_status = {"status": "connected"}
        config_health = {"healthy": True}

        orchestrator.connection_bridge.get_connection_status = AsyncMock(return_value=bridge_status)
        orchestrator.message_router.get_status = MagicMock(return_value=router_status)
        orchestrator.tool_router.get_status = MagicMock(return_value=tool_status)
        orchestrator.context7_integration.status = AsyncMock(return_value=context7_status)
        orchestrator.config_manager.health_check = AsyncMock(return_value=config_health)

        # Add connected servers
        orchestrator.connected_servers = {"server1": MagicMock(), "server2": MagicMock()}

        status = await orchestrator.get_comprehensive_status()

        assert status["initialized"] is True
        assert status["orchestrator_healthy"] is True
        assert status["connected_servers"] == 2
        assert status["connection_bridge"] == bridge_status
        assert status["message_router"] == router_status
        assert status["tool_router"] == tool_status
        assert status["context7_integration"] == context7_status
        assert status["configuration"] == config_health
        assert "document_search" in status["available_workflows"]
        assert "tool_execution" in status["available_workflows"]
        assert "context7_search" in status["available_workflows"]
        assert "timestamp" in status

    @pytest.mark.asyncio
    async def test_get_comprehensive_status_unhealthy_config(self, orchestrator):
        """Test comprehensive status with unhealthy configuration."""
        # Mock unhealthy config
        config_health = {"healthy": False}
        orchestrator.config_manager.health_check = AsyncMock(return_value=config_health)

        # Mock other status calls
        orchestrator.connection_bridge.get_connection_status = AsyncMock(return_value={})
        orchestrator.message_router.get_status = MagicMock(return_value={})
        orchestrator.tool_router.get_status = MagicMock(return_value={})
        orchestrator.context7_integration.status = AsyncMock(return_value={})

        status = await orchestrator.get_comprehensive_status()

        assert status["orchestrator_healthy"] is False

    @pytest.mark.asyncio
    async def test_get_comprehensive_status_exception(self, orchestrator):
        """Test comprehensive status with exception."""
        orchestrator.connection_bridge.get_connection_status = AsyncMock(side_effect=Exception("Status error"))

        status = await orchestrator.get_comprehensive_status()

        assert status["orchestrator_healthy"] is False
        assert "error" in status
        assert "Status error" in status["error"]

    @pytest.mark.asyncio
    async def test_shutdown_success(self, orchestrator):
        """Test successful shutdown."""
        # Mock connected servers
        orchestrator.connected_servers = {"server1": MagicMock()}

        # Mock shutdown methods
        orchestrator.connection_bridge.shutdown = AsyncMock()
        orchestrator.config_manager.shutdown = AsyncMock()

        await orchestrator.shutdown()

        assert orchestrator.initialized is False
        assert len(orchestrator.connected_servers) == 0
        orchestrator.connection_bridge.shutdown.assert_called_once()
        orchestrator.config_manager.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_exception(self, orchestrator):
        """Test shutdown with exception."""
        orchestrator.connection_bridge.shutdown = AsyncMock(side_effect=Exception("Shutdown error"))
        orchestrator.config_manager.shutdown = AsyncMock()

        # Should not raise exception
        await orchestrator.shutdown()

        # When exception occurs, initialized doesn't get set to False due to early exit
        assert orchestrator.initialized is True


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator fixture."""
        orch = MCPOrchestrator()
        orch.initialized = True
        return orch

    @pytest.mark.asyncio
    async def test_workflow_document_search_integration(self, orchestrator):
        """Test complete document search workflow integration."""
        # Mock all components
        orchestrator.discovery = MagicMock()
        orchestrator.connection_bridge = MagicMock()
        orchestrator.message_router = MagicMock()
        orchestrator.tool_router = MagicMock()
        orchestrator.context7_integration = MagicMock()

        # Mock successful connection flow
        mock_server_connection = MagicMock()
        mock_server_connection.type = "npx"
        orchestrator.discovery.discover_server = AsyncMock(return_value=mock_server_connection)

        mock_active_connection = MagicMock()
        mock_active_connection.process = MagicMock()
        orchestrator.connection_bridge.connect_to_server = AsyncMock(return_value=mock_active_connection)

        orchestrator.message_router.connect_server = AsyncMock(return_value=True)
        orchestrator.tool_router.refresh_server_tools = MagicMock()

        # Mock search results
        mock_search_results = {
            "total_results": 3,
            "documents": ["doc1", "doc2", "doc3"],
            "search_time": 0.8,
        }
        orchestrator.context7_integration.enhanced_document_search = AsyncMock(return_value=mock_search_results)

        # Execute workflow
        result = await orchestrator.execute_workflow(
            "document_search",
            {
                "query": "integration test",
                "limit": 10,
                "use_context7": True,
            },
        )

        assert result.success is True
        assert result.result == mock_search_results
        assert result.server_used == "context7"
        assert len(result.workflow_steps) == 4

    @pytest.mark.asyncio
    async def test_workflow_tool_execution_integration(self, orchestrator):
        """Test complete tool execution workflow integration."""
        # Mock tool execution without specific server
        orchestrator.tool_router = MagicMock()
        mock_tool_result = ToolExecutionResult(
            success=True,
            result={"tool_output": "executed"},
            server_name="promptcraft",
        )
        orchestrator.tool_router.execute_tool = AsyncMock(return_value=mock_tool_result)

        result = await orchestrator.execute_workflow(
            "tool_execution",
            {
                "tool_name": "read_file",
                "arguments": {"file_path": "/test/file.txt"},
            },
        )

        assert result.success is True
        assert result.result == {"tool_output": "executed"}
        assert result.server_used == "promptcraft"

    def test_workflow_result_timing(self):
        """Test workflow result includes timing information."""
        import time

        start_time = time.time()
        time.sleep(0.01)  # Small delay
        end_time = time.time()

        result = MCPWorkflowResult(
            success=True,
            execution_time=end_time - start_time,
        )

        assert result.execution_time > 0.01
        assert result.execution_time < 0.1  # Should be small delay
