"""
Tests for Hybrid Infrastructure API Endpoints
"""

from datetime import datetime, timezone, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import pytest

from src.api.hybrid_infrastructure_endpoints import register_hybrid_infrastructure_routes


class MockAppState:
    """Mock app state that properly handles attribute existence checks."""


class MockApp:
    """Mock FastAPI app for testing."""

    def __init__(self):
        self.state = MockAppState()
        self.routes = []
        self._route_handlers = {}

    def get(self, path: str):
        """Mock GET route decorator."""

        def decorator(func):
            self.routes.append(("GET", path))
            self._route_handlers[("GET", path)] = func
            return func

        return decorator

    def post(self, path: str):
        """Mock POST route decorator."""

        def decorator(func):
            self.routes.append(("POST", path))
            self._route_handlers[("POST", path)] = func
            return func

        return decorator

    def delete(self, path: str):
        """Mock DELETE route decorator."""

        def decorator(func):
            self.routes.append(("DELETE", path))
            self._route_handlers[("DELETE", path)] = func
            return func

        return decorator


class TestRouteRegistration:
    """Test route registration."""

    def test_register_routes(self):
        """Test that all routes are registered."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)

        expected_routes = [
            ("GET", "/api/discovery/agents"),
            ("GET", "/api/discovery/status"),
            ("GET", "/api/discovery/mcp-servers"),
            ("POST", "/api/mcp-servers/{server_name}/connect"),
            ("DELETE", "/api/mcp-servers/{server_name}/disconnect"),
            ("GET", "/api/mcp-servers/connections"),
            ("GET", "/api/mcp-servers/health"),
            ("POST", "/api/agents/{agent_id}/load"),
            ("DELETE", "/api/agents/{agent_id}/unload"),
            ("GET", "/api/discovery/standards"),
            ("GET", "/api/discovery/standards/{standard_id}"),
            ("POST", "/api/standards/validate"),
            ("GET", "/api/discovery/commands"),
            ("GET", "/api/discovery/commands/{command_id}"),
            ("GET", "/api/discovery/commands/category/{category}"),
            ("GET", "/api/commands/search"),
            ("GET", "/api/discovery/scripts"),
            ("GET", "/api/discovery/scripts/{script_id}"),
            ("GET", "/api/discovery/scripts/category/{category}"),
        ]

        assert len(app.routes) == len(expected_routes)
        for route in expected_routes:
            assert route in app.routes


class TestAgentEndpoints:
    """Test agent discovery and management endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app with agent discovery setup."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_available_agents_success(self, app, mock_request):
        """Test successful agent discovery."""
        # Mock app state
        app.state.agent_discovery = MagicMock()
        app.state.agent_discovery.get_available_agents.return_value = [
            {"id": "agent1", "name": "Agent 1"},
            {"id": "agent2", "name": "Agent 2"},
        ]
        app.state.agent_resource_manager = MagicMock()
        app.state.agent_resource_manager.get_resource_usage.return_value = {
            "memory_usage": "45%",
            "cpu_usage": "23%",
        }

        handler = app._route_handlers[("GET", "/api/discovery/agents")]
        result = await handler(mock_request)

        assert "available_agents" in result
        assert result["total_count"] == 2
        assert "resource_usage" in result
        assert result["resource_usage"]["memory_usage"] == "45%"

    @pytest.mark.asyncio
    async def test_get_available_agents_not_initialized(self, app, mock_request):
        """Test agent discovery when not initialized."""
        # Don't set agent_discovery on app.state

        handler = app._route_handlers[("GET", "/api/discovery/agents")]

        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request)

        assert exc_info.value.status_code == 503
        assert "Agent discovery not initialized" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_available_agents_exception(self, app, mock_request):
        """Test agent discovery with exception."""
        app.state.agent_discovery = MagicMock()
        app.state.agent_discovery.get_available_agents.side_effect = Exception("Discovery error")

        handler = app._route_handlers[("GET", "/api/discovery/agents")]

        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve agents" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_load_agent_success(self, app, mock_request):
        """Test successful agent loading."""
        app.state.agent_loader = MagicMock()
        mock_agent = MagicMock()
        mock_agent.get_capabilities.return_value = {"capability1": "value1"}
        app.state.agent_loader.load_agent.return_value = mock_agent

        handler = app._route_handlers[("POST", "/api/agents/{agent_id}/load")]
        result = await handler("test_agent", mock_request)

        assert result["status"] == "loaded"
        assert result["agent_id"] == "test_agent"
        assert "capabilities" in result
        app.state.agent_loader.load_agent.assert_called_once_with("test_agent", {"agent_id": "test_agent"})

    @pytest.mark.asyncio
    async def test_load_agent_not_initialized(self, app, mock_request):
        """Test agent loading when loader not initialized."""
        handler = app._route_handlers[("POST", "/api/agents/{agent_id}/load")]

        with pytest.raises(HTTPException) as exc_info:
            await handler("test_agent", mock_request)

        assert exc_info.value.status_code == 503
        assert "Agent loader not initialized" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_load_agent_no_capabilities(self, app, mock_request):
        """Test agent loading without capabilities method."""
        app.state.agent_loader = MagicMock()
        mock_agent = MagicMock()
        # Mock agent without get_capabilities method
        del mock_agent.get_capabilities
        app.state.agent_loader.load_agent.return_value = mock_agent

        handler = app._route_handlers[("POST", "/api/agents/{agent_id}/load")]
        result = await handler("test_agent", mock_request)

        assert result["capabilities"] == {}

    @pytest.mark.asyncio
    async def test_unload_agent_success(self, app, mock_request):
        """Test successful agent unloading."""
        app.state.agent_loader = MagicMock()

        handler = app._route_handlers[("DELETE", "/api/agents/{agent_id}/unload")]
        result = await handler("test_agent", mock_request)

        assert result["status"] == "unloaded"
        assert result["agent_id"] == "test_agent"
        app.state.agent_loader.unload_agent.assert_called_once_with("test_agent")

    @pytest.mark.asyncio
    async def test_unload_agent_exception(self, app, mock_request):
        """Test agent unloading with exception."""
        app.state.agent_loader = MagicMock()
        app.state.agent_loader.unload_agent.side_effect = Exception("Unload error")

        handler = app._route_handlers[("DELETE", "/api/agents/{agent_id}/unload")]

        with pytest.raises(HTTPException) as exc_info:
            await handler("test_agent", mock_request)

        assert exc_info.value.status_code == 500
        assert "Failed to unload agent" in str(exc_info.value.detail)


class TestInfrastructureStatusEndpoints:
    """Test infrastructure status endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_all_initialized(self, app, mock_request):
        """Test infrastructure status when all components initialized."""
        app.state.mcp_manager = MagicMock()
        app.state.agent_discovery = MagicMock()
        app.state.agent_discovery.get_available_agents.return_value = [{"id": "agent1"}]
        app.state.agent_loader = MagicMock()
        app.state.agent_resource_manager = MagicMock()
        app.state.agent_resource_manager.get_resource_usage.return_value = {"cpu": "20%"}

        handler = app._route_handlers[("GET", "/api/discovery/status")]
        result = await handler(mock_request)

        assert result["mcp_manager_initialized"] is True
        assert result["agent_discovery_initialized"] is True
        assert result["agent_loader_initialized"] is True
        assert result["overall_health"] is True
        assert result["available_agents_count"] == 1
        assert "resource_usage" in result

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_partial(self, app, mock_request):
        """Test infrastructure status when partially initialized."""
        app.state.mcp_manager = MagicMock()
        # Don't set agent_discovery and agent_loader

        handler = app._route_handlers[("GET", "/api/discovery/status")]
        result = await handler(mock_request)

        assert result["mcp_manager_initialized"] is True
        assert result["agent_discovery_initialized"] is False
        assert result["agent_loader_initialized"] is False
        assert result["overall_health"] is False

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_exception(self, app, mock_request):
        """Test infrastructure status with exception."""
        app.state.agent_discovery = MagicMock()
        app.state.agent_discovery.get_available_agents.side_effect = Exception("Status error")

        handler = app._route_handlers[("GET", "/api/discovery/status")]

        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve infrastructure status" in str(exc_info.value.detail)


class TestMCPServerEndpoints:
    """Test MCP server management endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app with MCP manager."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_mcp_servers_status_success(self, app, mock_request):
        """Test successful MCP servers status."""
        app.state.mcp_manager = MagicMock()
        app.state.mcp_manager.configuration = MagicMock()
        app.state.mcp_manager.configuration.mcp_servers = {
            "server1": {"type": "npx"},
            "server2": {"type": "docker"},
        }
        app.state.mcp_manager.discovery = MagicMock()
        app.state.mcp_manager.get_connection_status = AsyncMock(
            return_value={
                "connection_bridge_available": True,
                "total_connections": 2,
                "connections": {"server1": "connected"},
            },
        )

        handler = app._route_handlers[("GET", "/api/discovery/mcp-servers")]
        result = await handler(mock_request)

        assert result["enabled_servers"] == ["server1", "server2"]
        assert result["discovery_enabled"] is True
        assert result["configuration_loaded"] is True
        assert result["active_connections"] == 2

    @pytest.mark.asyncio
    async def test_get_mcp_servers_status_not_initialized(self, app, mock_request):
        """Test MCP servers status when not initialized."""
        handler = app._route_handlers[("GET", "/api/discovery/mcp-servers")]

        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request)

        assert exc_info.value.status_code == 503
        assert "MCP manager not initialized" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_connect_mcp_server_success(self, app, mock_request):
        """Test successful MCP server connection."""
        app.state.mcp_manager = MagicMock()

        # Mock connection object
        mock_connection = MagicMock()
        mock_connection.connection.type = "npx"
        mock_connection.connection.url = "npx://server1"
        mock_connection.connected_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_connection.health_status = "connected"

        app.state.mcp_manager.connect_to_server = AsyncMock(return_value=mock_connection)

        handler = app._route_handlers[("POST", "/api/mcp-servers/{server_name}/connect")]
        result = await handler("server1", mock_request)

        assert result["status"] == "connected"
        assert result["server_name"] == "server1"
        assert result["connection_type"] == "npx"
        assert result["url"] == "npx://server1"
        assert result["health_status"] == "connected"
        app.state.mcp_manager.connect_to_server.assert_called_once_with("server1")

    @pytest.mark.asyncio
    async def test_connect_mcp_server_failed(self, app, mock_request):
        """Test failed MCP server connection."""
        app.state.mcp_manager = MagicMock()
        app.state.mcp_manager.connect_to_server = AsyncMock(return_value=None)

        handler = app._route_handlers[("POST", "/api/mcp-servers/{server_name}/connect")]

        with pytest.raises(HTTPException) as exc_info:
            await handler("server1", mock_request)

        assert exc_info.value.status_code == 404
        assert "Failed to connect to server 'server1'" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_disconnect_mcp_server_success(self, app, mock_request):
        """Test successful MCP server disconnection."""
        app.state.mcp_manager = MagicMock()
        app.state.mcp_manager.disconnect_from_server = AsyncMock(return_value=True)

        handler = app._route_handlers[("DELETE", "/api/mcp-servers/{server_name}/disconnect")]
        result = await handler("server1", mock_request)

        assert result["status"] == "disconnected"
        assert result["server_name"] == "server1"

    @pytest.mark.asyncio
    async def test_disconnect_mcp_server_failed(self, app, mock_request):
        """Test failed MCP server disconnection."""
        app.state.mcp_manager = MagicMock()
        app.state.mcp_manager.disconnect_from_server = AsyncMock(return_value=False)

        handler = app._route_handlers[("DELETE", "/api/mcp-servers/{server_name}/disconnect")]

        with pytest.raises(HTTPException) as exc_info:
            await handler("server1", mock_request)

        assert exc_info.value.status_code == 404
        assert "No active connection to server 'server1'" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_mcp_connections_success(self, app, mock_request):
        """Test getting MCP connections."""
        app.state.mcp_manager = MagicMock()
        connection_status = {
            "total_connections": 2,
            "connections": {"server1": "connected", "server2": "connecting"},
        }
        app.state.mcp_manager.get_connection_status = AsyncMock(return_value=connection_status)

        handler = app._route_handlers[("GET", "/api/mcp-servers/connections")]
        result = await handler(mock_request)

        assert result == connection_status

    @pytest.mark.asyncio
    async def test_get_mcp_health_success(self, app, mock_request):
        """Test getting MCP health status."""
        app.state.mcp_manager = MagicMock()
        health_status = {"overall_health": True, "components": {"discovery": "ok"}}
        app.state.mcp_manager.health_check = AsyncMock(return_value=health_status)

        handler = app._route_handlers[("GET", "/api/mcp-servers/health")]
        result = await handler(mock_request)

        assert result == health_status


class TestStandardsEndpoints:
    """Test standards discovery and validation endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_available_standards_success(self, app, mock_request):
        """Test successful standards discovery."""
        mock_standards = [
            {"id": "python", "name": "Python Standards"},
            {"id": "git", "name": "Git Workflow Standards"},
        ]
        mock_status = {"discovery_enabled": True, "last_scan": "2024-01-01T12:00:00"}

        with patch("src.api.hybrid_infrastructure_endpoints.StandardsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_available_standards.return_value = mock_standards
            mock_discovery.get_discovery_status.return_value = mock_status
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/standards")]
            result = await handler(mock_request)

            assert result["available_standards"] == mock_standards
            assert result["total_count"] == 2
            assert result["discovery_status"] == mock_status

    @pytest.mark.asyncio
    async def test_get_available_standards_existing_manager(self, app, mock_request):
        """Test standards discovery with existing manager."""
        app.state.standards_manager = MagicMock()
        mock_discovery = MagicMock()
        mock_discovery.get_available_standards.return_value = []
        mock_discovery.get_discovery_status.return_value = {}
        app.state.standards_manager.discovery_system = mock_discovery

        handler = app._route_handlers[("GET", "/api/discovery/standards")]
        result = await handler(mock_request)

        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_get_standard_content_success(self, app, mock_request):
        """Test getting standard content successfully."""
        mock_standard = MagicMock()
        mock_standard.standard_id = "python"
        mock_standard.name = "Python Standards"
        mock_standard.description = "Python coding standards"
        mock_standard.source_type = "file"
        mock_standard.version = "1.0"
        mock_standard.last_updated = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        with patch("src.api.hybrid_infrastructure_endpoints.StandardsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_standard.return_value = mock_standard
            mock_discovery.get_standard_content.return_value = "Standard content here"
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/standards/{standard_id}")]
            result = await handler("python", mock_request)

            assert result["standard_id"] == "python"
            assert result["name"] == "Python Standards"
            assert result["content"] == "Standard content here"
            assert result["last_updated"] == "2024-01-01T12:00:00"

    @pytest.mark.asyncio
    async def test_get_standard_content_not_found(self, app, mock_request):
        """Test getting non-existent standard content."""
        with patch("src.api.hybrid_infrastructure_endpoints.StandardsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_standard.return_value = None
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/standards/{standard_id}")]

            with pytest.raises(HTTPException) as exc_info:
                await handler("nonexistent", mock_request)

            assert exc_info.value.status_code == 404
            assert "Standard 'nonexistent' not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_project_standards_success(self, app, mock_request):
        """Test successful project standards validation."""
        compliance_results = {"python": True, "git": False, "security": True}

        with patch("src.api.hybrid_infrastructure_endpoints.StandardsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.validate_project_compliance.return_value = compliance_results
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("POST", "/api/standards/validate")]
            result = await handler(mock_request)

            assert result["compliance_results"] == compliance_results
            assert result["overall_compliance"] is False  # Not all standards comply
            assert result["total_standards_checked"] == 3
            assert result["compliant_standards"] == 2


class TestCommandsEndpoints:
    """Test commands discovery endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_available_commands_success(self, app, mock_request):
        """Test successful commands discovery."""
        mock_commands = [
            {"id": "test", "name": "Test Command"},
            {"id": "lint", "name": "Lint Command"},
        ]

        with patch("src.api.hybrid_infrastructure_endpoints.CommandsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_available_commands.return_value = mock_commands
            mock_discovery.get_discovery_status.return_value = {}
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/commands")]
            result = await handler(mock_request)

            assert result["available_commands"] == mock_commands
            assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_command_content_success(self, app, mock_request):
        """Test getting command content successfully."""
        mock_command = MagicMock()
        mock_command.command_id = "test"
        mock_command.name = "Test Command"
        mock_command.description = "Run tests"
        mock_command.source_type = "file"
        mock_command.category = "testing"
        mock_command.version = "1.0"
        mock_command.parameters = ["--verbose"]
        mock_command.examples = ["test --verbose"]
        mock_command.last_updated = datetime(2024, 1, 1, tzinfo=UTC)

        with patch("src.api.hybrid_infrastructure_endpoints.CommandsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_command.return_value = mock_command
            mock_discovery.get_command_content.return_value = "Command content"
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/commands/{command_id}")]
            result = await handler("test", mock_request)

            assert result["command_id"] == "test"
            assert result["name"] == "Test Command"
            assert result["category"] == "testing"
            assert result["content"] == "Command content"

    @pytest.mark.asyncio
    async def test_get_commands_by_category_success(self, app, mock_request):
        """Test getting commands by category."""
        mock_commands = [
            MagicMock(command_id="test1", name="Test 1", description="First test", source_type="file"),
            MagicMock(command_id="test2", name="Test 2", description="Second test", source_type="file"),
        ]

        with patch("src.api.hybrid_infrastructure_endpoints.CommandsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_commands_by_category.return_value = mock_commands
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/commands/category/{category}")]
            result = await handler("testing", mock_request)

            assert result["category"] == "testing"
            assert result["total_count"] == 2
            assert len(result["commands"]) == 2
            assert result["commands"][0]["command_id"] == "test1"

    @pytest.mark.asyncio
    async def test_search_commands_success(self, app, mock_request):
        """Test searching commands successfully."""
        mock_commands = [
            MagicMock(command_id="test", name="Test", description="Run tests", source_type="file", category="testing"),
        ]

        with patch("src.api.hybrid_infrastructure_endpoints.CommandsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.search_commands.return_value = mock_commands
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/commands/search")]
            result = await handler("test query", mock_request)

            assert result["query"] == "test query"
            assert result["total_count"] == 1
            assert result["commands"][0]["command_id"] == "test"


class TestScriptsEndpoints:
    """Test scripts discovery endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_available_scripts_success(self, app, mock_request):
        """Test successful scripts discovery."""
        mock_scripts = [{"id": "deploy", "name": "Deploy Script"}]

        with patch("src.api.hybrid_infrastructure_endpoints.ScriptsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_available_scripts.return_value = mock_scripts
            mock_discovery.get_discovery_status.return_value = {}
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/scripts")]
            result = await handler(mock_request)

            assert result["available_scripts"] == mock_scripts
            assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_get_script_content_success(self, app, mock_request):
        """Test getting script content successfully."""
        mock_script = MagicMock()
        mock_script.script_id = "deploy"
        mock_script.name = "Deploy Script"
        mock_script.description = "Deploy application"
        mock_script.source_type = "file"
        mock_script.script_type = "bash"
        mock_script.category = "deployment"
        mock_script.version = "1.0"
        mock_script.is_executable = True
        mock_script.dependencies = ["docker"]
        mock_script.parameters = ["--env"]
        mock_script.last_updated = datetime(2024, 1, 1, tzinfo=UTC)

        with patch("src.api.hybrid_infrastructure_endpoints.ScriptsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_script.return_value = mock_script
            mock_discovery.get_script_content.return_value = "#!/bin/bash\necho 'Deploy'"
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/scripts/{script_id}")]
            result = await handler("deploy", mock_request)

            assert result["script_id"] == "deploy"
            assert result["name"] == "Deploy Script"
            assert result["script_type"] == "bash"
            assert result["is_executable"] is True
            assert result["dependencies"] == ["docker"]
            assert "#!/bin/bash" in result["content"]

    @pytest.mark.asyncio
    async def test_get_scripts_by_category_success(self, app, mock_request):
        """Test getting scripts by category."""
        mock_scripts = [
            MagicMock(
                script_id="deploy1",
                name="Deploy 1",
                description="First deploy",
                source_type="file",
                script_type="bash",
                is_executable=True,
            ),
        ]

        with patch("src.api.hybrid_infrastructure_endpoints.ScriptsManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_discovery = MagicMock()
            mock_discovery.get_scripts_by_category.return_value = mock_scripts
            mock_manager.discovery_system = mock_discovery
            mock_manager_cls.return_value = mock_manager

            handler = app._route_handlers[("GET", "/api/discovery/scripts/category/{category}")]
            result = await handler("deployment", mock_request)

            assert result["category"] == "deployment"
            assert result["total_count"] == 1
            assert result["scripts"][0]["script_id"] == "deploy1"


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        app = MockApp()
        register_hybrid_infrastructure_routes(app)
        return app

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_mcp_manager_exception_handling(self, app, mock_request):
        """Test exception handling in MCP manager endpoints."""
        app.state.mcp_manager = MagicMock()
        app.state.mcp_manager.connect_to_server = AsyncMock(side_effect=Exception("Connection error"))

        handler = app._route_handlers[("POST", "/api/mcp-servers/{server_name}/connect")]

        with pytest.raises(HTTPException) as exc_info:
            await handler("server1", mock_request)

        assert exc_info.value.status_code == 500
        assert "Failed to connect" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_http_exception_passthrough(self, app, mock_request):
        """Test that HTTPExceptions are passed through correctly."""
        app.state.mcp_manager = MagicMock()

        # Simulate HTTPException being raised directly
        def raise_http_exception(*args, **kwargs):
            raise HTTPException(status_code=404, detail="Server not found")

        app.state.mcp_manager.connect_to_server = AsyncMock(side_effect=raise_http_exception)

        handler = app._route_handlers[("POST", "/api/mcp-servers/{server_name}/connect")]

        with pytest.raises(HTTPException) as exc_info:
            await handler("server1", mock_request)

        # Should preserve the original HTTPException
        assert exc_info.value.status_code == 404
        assert "Server not found" in str(exc_info.value.detail)
