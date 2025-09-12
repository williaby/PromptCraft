"""
Tests for MCP Connection Bridge system.

Test Coverage for src/mcp_integration/connection_bridge.py:
- ActiveConnection dataclass
- NPXProcessManager process lifecycle management
- MCPConnectionBridge discovery and connection management
- Connection health checking and monitoring
- Resource cleanup and shutdown procedures
- Connection pooling and lifecycle management
- Multi-type server connection handling (NPX, embedded, external, Docker)
"""

from datetime import datetime, timedelta
import subprocess
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest

from src.mcp_integration.connection_bridge import (
    ActiveConnection,
    MCPConnectionBridge,
    NPXProcessManager,
)
from src.mcp_integration.smart_discovery import ServerConnection
from src.utils.datetime_compat import utc_now


class TestActiveConnection:
    """Test ActiveConnection dataclass."""

    def test_active_connection_creation(self):
        """Test creating an ActiveConnection instance."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
            client=Mock(),
            process=Mock(),
            health_status="connected",
            error_count=2,
        )

        assert active_conn.server_name == "test-server"
        assert active_conn.connection == connection
        assert active_conn.client is not None
        assert active_conn.process is not None
        assert active_conn.health_status == "connected"
        assert active_conn.error_count == 2
        assert isinstance(active_conn.connected_at, datetime)
        assert active_conn.last_health_check is None

    def test_active_connection_defaults(self):
        """Test ActiveConnection with default values."""
        connection = ServerConnection(
            url="npx://test",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="npx-server",
            connection=connection,
        )

        assert active_conn.client is None
        assert active_conn.process is None
        assert active_conn.health_status == "connecting"
        assert active_conn.error_count == 0
        assert active_conn.last_health_check is None
        assert isinstance(active_conn.connected_at, datetime)


class TestNPXProcessManager:
    """Test NPXProcessManager class."""

    @pytest.fixture
    def npx_manager(self):
        """Create an NPXProcessManager instance for testing."""
        return NPXProcessManager()

    def test_npx_process_manager_initialization(self, npx_manager):
        """Test NPXProcessManager initialization."""
        assert isinstance(npx_manager.processes, dict)
        assert len(npx_manager.processes) == 0
        assert "context7" in npx_manager.process_config
        assert "perplexity" in npx_manager.process_config
        assert "sentry" in npx_manager.process_config
        assert "tavily" in npx_manager.process_config

    def test_process_config_structure(self, npx_manager):
        """Test process configuration structure."""
        for _server_name, config in npx_manager.process_config.items():
            assert "package" in config
            assert "binary" in config
            assert isinstance(config["package"], str)
            assert isinstance(config["binary"], str)

    @pytest.mark.asyncio
    async def test_spawn_npx_server_already_running(self, npx_manager):
        """Test spawning NPX server when already running."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        mock_process.pid = 12345

        npx_manager.processes["context7"] = mock_process

        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        result = await npx_manager.spawn_npx_server("context7", connection)

        assert result == mock_process
        mock_process.poll.assert_called_once()

    @pytest.mark.asyncio
    async def test_spawn_npx_server_process_died(self, npx_manager):
        """Test spawning NPX server when previous process died."""
        mock_dead_process = Mock()
        mock_dead_process.poll.return_value = 1  # Process died

        npx_manager.processes["context7"] = mock_dead_process

        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_new_process = Mock()
        mock_new_process.poll.return_value = None  # Running
        mock_new_process.pid = 54321

        with patch("subprocess.Popen", return_value=mock_new_process), patch("asyncio.sleep"):

            result = await npx_manager.spawn_npx_server("context7", connection)

            assert result == mock_new_process
            assert "context7" not in npx_manager.processes or npx_manager.processes["context7"] == mock_new_process

    @pytest.mark.asyncio
    async def test_spawn_npx_server_success(self, npx_manager):
        """Test successfully spawning NPX server."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.pid = 12345
        mock_process.stderr = None

        with patch("subprocess.Popen", return_value=mock_process), patch("asyncio.sleep"):

            result = await npx_manager.spawn_npx_server("context7", connection)

            assert result == mock_process
            assert npx_manager.processes["context7"] == mock_process

    @pytest.mark.asyncio
    async def test_spawn_npx_server_from_url(self, npx_manager):
        """Test spawning NPX server extracting package from URL."""
        connection = ServerConnection(
            url="npx://@custom/package-name",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_process.stderr = None

        with patch("subprocess.Popen", return_value=mock_process) as mock_popen, patch("asyncio.sleep"):

            await npx_manager.spawn_npx_server("context7", connection)

            # Should use package name from URL
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            assert args[0] == ["npx", "@custom/package-name"]

    @pytest.mark.asyncio
    async def test_spawn_npx_server_unknown_server(self, npx_manager):
        """Test spawning NPX server for unknown server type."""
        connection = ServerConnection(
            url="npx://unknown",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        result = await npx_manager.spawn_npx_server("unknown-server", connection)
        assert result is None

    @pytest.mark.asyncio
    async def test_spawn_npx_server_startup_failure(self, npx_manager):
        """Test NPX server startup failure."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process failed
        mock_stderr = Mock()
        mock_stderr.read.return_value = "NPX startup error"
        mock_process.stderr = mock_stderr

        with patch("subprocess.Popen", return_value=mock_process), patch("asyncio.sleep"):

            result = await npx_manager.spawn_npx_server("context7", connection)
            assert result is None

    @pytest.mark.asyncio
    async def test_spawn_npx_server_exception(self, npx_manager):
        """Test NPX server spawning with exception."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with patch("subprocess.Popen", side_effect=Exception("Process error")):
            result = await npx_manager.spawn_npx_server("context7", connection)
            assert result is None

    def test_stop_npx_server_success(self, npx_manager):
        """Test successfully stopping NPX server."""
        mock_process = Mock()
        mock_process.wait.return_value = None
        npx_manager.processes["context7"] = mock_process

        result = npx_manager.stop_npx_server("context7")

        assert result is True
        assert "context7" not in npx_manager.processes
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    def test_stop_npx_server_force_kill(self, npx_manager):
        """Test stopping NPX server with force kill."""
        mock_process = Mock()
        mock_process.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]
        npx_manager.processes["context7"] = mock_process

        result = npx_manager.stop_npx_server("context7")

        assert result is True
        assert "context7" not in npx_manager.processes
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert mock_process.wait.call_count == 2

    def test_stop_npx_server_not_running(self, npx_manager):
        """Test stopping NPX server that's not running."""
        result = npx_manager.stop_npx_server("nonexistent")
        assert result is False

    def test_stop_npx_server_exception(self, npx_manager):
        """Test stopping NPX server with exception."""
        mock_process = Mock()
        mock_process.terminate.side_effect = Exception("Terminate error")
        npx_manager.processes["context7"] = mock_process

        result = npx_manager.stop_npx_server("context7")
        assert result is False

    def test_get_process_status_not_running(self, npx_manager):
        """Test getting process status when not running."""
        status = npx_manager.get_process_status("nonexistent")

        assert status["status"] == "not_running"
        assert status["pid"] is None

    def test_get_process_status_running(self, npx_manager):
        """Test getting process status when running."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        mock_process.pid = 12345
        npx_manager.processes["context7"] = mock_process

        status = npx_manager.get_process_status("context7")

        assert status["status"] == "running"
        assert status["pid"] == 12345

    def test_get_process_status_terminated(self, npx_manager):
        """Test getting process status when terminated."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Terminated with code 1
        mock_process.pid = 12345
        npx_manager.processes["context7"] = mock_process

        status = npx_manager.get_process_status("context7")

        assert status["status"] == "terminated"
        assert status["pid"] is None
        assert status["return_code"] == 1
        assert "context7" not in npx_manager.processes  # Should be cleaned up


class TestMCPConnectionBridge:
    """Test MCPConnectionBridge class."""

    @pytest.fixture
    def mock_discovery(self):
        """Create a mock SmartMCPDiscovery instance."""
        discovery = Mock()
        discovery.discover_server = AsyncMock()
        return discovery

    @pytest.fixture
    def connection_bridge(self, mock_discovery):
        """Create an MCPConnectionBridge instance for testing."""
        return MCPConnectionBridge(discovery=mock_discovery)

    def test_connection_bridge_initialization(self, connection_bridge, mock_discovery):
        """Test MCPConnectionBridge initialization."""
        assert connection_bridge.discovery == mock_discovery
        assert isinstance(connection_bridge.npx_manager, NPXProcessManager)
        assert isinstance(connection_bridge.active_connections, dict)
        assert len(connection_bridge.active_connections) == 0
        assert connection_bridge.connection_pool_size == 10
        assert connection_bridge.health_check_interval == timedelta(minutes=5)

    def test_connection_bridge_default_discovery(self):
        """Test MCPConnectionBridge with default discovery."""
        with patch("src.mcp_integration.connection_bridge.SmartMCPDiscovery") as mock_discovery_cls:
            mock_discovery = Mock()
            mock_discovery_cls.return_value = mock_discovery

            bridge = MCPConnectionBridge()
            assert bridge.discovery == mock_discovery

    @pytest.mark.asyncio
    async def test_connect_to_server_reuse_healthy(self, connection_bridge):
        """Test connecting to server with existing healthy connection."""
        # Setup existing connection
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
            health_status="connected",
        )

        connection_bridge.active_connections["test-server"] = active_conn

        with patch.object(connection_bridge, "_is_connection_healthy", return_value=True):
            result = await connection_bridge.connect_to_server("test-server")

            assert result == active_conn
            # Should not call discovery since connection was reused
            connection_bridge.discovery.discover_server.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_to_server_cleanup_unhealthy(self, connection_bridge):
        """Test connecting to server cleaning up unhealthy connection."""
        # Setup existing unhealthy connection
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="unhealthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
            health_status="unhealthy",
        )

        connection_bridge.active_connections["test-server"] = active_conn

        # Mock new discovery and connection
        new_connection = ServerConnection(
            url="http://localhost:8001",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = new_connection

        with (
            patch.object(connection_bridge, "_is_connection_healthy", return_value=False),
            patch.object(connection_bridge, "_cleanup_connection") as mock_cleanup,
            patch.object(connection_bridge, "_connect_external_server", return_value=True),
        ):

            result = await connection_bridge.connect_to_server("test-server")

            mock_cleanup.assert_called_once_with("test-server")
            assert result is not None
            assert result.connection == new_connection

    @pytest.mark.asyncio
    async def test_connect_to_server_discovery_failure(self, connection_bridge):
        """Test connecting to server when discovery fails."""
        connection_bridge.discovery.discover_server.return_value = None

        result = await connection_bridge.connect_to_server("nonexistent-server")
        assert result is None

    @pytest.mark.asyncio
    async def test_connect_to_server_npx(self, connection_bridge):
        """Test connecting to NPX server."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = connection

        with patch.object(connection_bridge, "_connect_npx_server", return_value=True):
            result = await connection_bridge.connect_to_server("context7")

            assert result is not None
            assert result.server_name == "context7"
            assert result.connection == connection
            assert "context7" in connection_bridge.active_connections

    @pytest.mark.asyncio
    async def test_connect_to_server_embedded(self, connection_bridge):
        """Test connecting to embedded server."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="embedded",
            health_status="healthy",
            resource_usage={"port": 8000},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = connection

        with patch.object(connection_bridge, "_connect_embedded_server", return_value=True):
            result = await connection_bridge.connect_to_server("zen-mcp")

            assert result is not None
            assert result.connection.type == "embedded"

    @pytest.mark.asyncio
    async def test_connect_to_server_external(self, connection_bridge):
        """Test connecting to external server."""
        connection = ServerConnection(
            url="http://remote:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = connection

        with patch.object(connection_bridge, "_connect_external_server", return_value=True):
            result = await connection_bridge.connect_to_server("external-server")

            assert result is not None
            assert result.connection.type == "external"

    @pytest.mark.asyncio
    async def test_connect_to_server_docker(self, connection_bridge):
        """Test connecting to Docker server."""
        connection = ServerConnection(
            url="http://localhost:8080",
            type="docker",
            health_status="running",
            resource_usage={"container_id": "abc123"},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = connection

        with patch.object(connection_bridge, "_connect_docker_server", return_value=True):
            result = await connection_bridge.connect_to_server("docker-server")

            assert result is not None
            assert result.connection.type == "docker"

    @pytest.mark.asyncio
    async def test_connect_to_server_unknown_type(self, connection_bridge):
        """Test connecting to server with unknown type."""
        connection = ServerConnection(
            url="unknown://localhost",
            type="unknown",
            health_status="unknown",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = connection

        result = await connection_bridge.connect_to_server("unknown-server")
        assert result is None

    @pytest.mark.asyncio
    async def test_connect_to_server_connection_failure(self, connection_bridge):
        """Test connecting to server when protocol connection fails."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection_bridge.discovery.discover_server.return_value = connection

        with patch.object(connection_bridge, "_connect_external_server", return_value=False):
            result = await connection_bridge.connect_to_server("failed-server")
            assert result is None

    @pytest.mark.asyncio
    async def test_connect_to_server_exception(self, connection_bridge):
        """Test connecting to server with exception."""
        connection_bridge.discovery.discover_server.side_effect = Exception("Discovery error")

        result = await connection_bridge.connect_to_server("error-server")
        assert result is None

    @pytest.mark.asyncio
    async def test_connect_npx_server_success(self, connection_bridge):
        """Test successful NPX server connection."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="context7",
            connection=connection,
        )

        mock_process = Mock()
        mock_process.pid = 12345

        with (
            patch.object(connection_bridge.npx_manager, "spawn_npx_server", return_value=mock_process),
            patch("src.mcp_integration.connection_bridge.ZenMCPStdioClient") as mock_client_cls,
        ):

            mock_client = Mock()
            mock_client_cls.return_value = mock_client

            result = await connection_bridge._connect_npx_server(active_conn)

            assert result is True
            assert active_conn.process == mock_process
            assert active_conn.client == mock_client
            assert active_conn.health_status == "connected"

    @pytest.mark.asyncio
    async def test_connect_npx_server_spawn_failure(self, connection_bridge):
        """Test NPX server connection when spawn fails."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="context7",
            connection=connection,
        )

        with patch.object(connection_bridge.npx_manager, "spawn_npx_server", return_value=None):
            result = await connection_bridge._connect_npx_server(active_conn)
            assert result is False

    @pytest.mark.asyncio
    async def test_connect_npx_server_exception(self, connection_bridge):
        """Test NPX server connection with exception."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="context7",
            connection=connection,
        )

        with patch.object(connection_bridge.npx_manager, "spawn_npx_server", side_effect=Exception("Spawn error")):
            result = await connection_bridge._connect_npx_server(active_conn)
            assert result is False

    @pytest.mark.asyncio
    async def test_connect_embedded_server_success(self, connection_bridge):
        """Test successful embedded server connection."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="embedded",
            health_status="healthy",
            resource_usage={"port": 8000},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="zen-mcp",
            connection=connection,
        )

        result = await connection_bridge._connect_embedded_server(active_conn)

        assert result is True
        assert active_conn.client["type"] == "http"
        assert active_conn.client["url"] == "http://localhost:8000"
        assert active_conn.health_status == "connected"

    @pytest.mark.asyncio
    async def test_connect_embedded_server_invalid_url(self, connection_bridge):
        """Test embedded server connection with invalid URL."""
        connection = ServerConnection(
            url="invalid://localhost",
            type="embedded",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="invalid-server",
            connection=connection,
        )

        result = await connection_bridge._connect_embedded_server(active_conn)
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_embedded_server_exception(self, connection_bridge):
        """Test embedded server connection with exception."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="embedded",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="zen-mcp",
            connection=connection,
        )

        # Force an exception by creating a mock that raises when url property is accessed
        mock_connection = Mock()
        type(mock_connection).url = PropertyMock(side_effect=Exception("Connection error"))
        active_conn.connection = mock_connection

        result = await connection_bridge._connect_embedded_server(active_conn)
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_external_server_success(self, connection_bridge):
        """Test successful external server connection."""
        connection = ServerConnection(
            url="http://remote:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="external-server",
            connection=connection,
        )

        result = await connection_bridge._connect_external_server(active_conn)

        assert result is True
        assert active_conn.client["type"] == "external"
        assert active_conn.client["url"] == "http://remote:8000"
        assert active_conn.health_status == "connected"

    @pytest.mark.asyncio
    async def test_connect_docker_server_success(self, connection_bridge):
        """Test successful Docker server connection."""
        connection = ServerConnection(
            url="http://localhost:8080",
            type="docker",
            health_status="running",
            resource_usage={"container_id": "abc123"},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="docker-server",
            connection=connection,
        )

        result = await connection_bridge._connect_docker_server(active_conn)

        assert result is True
        assert active_conn.client["type"] == "docker"
        assert active_conn.client["url"] == "http://localhost:8080"
        assert active_conn.health_status == "connected"

    @pytest.mark.asyncio
    async def test_is_connection_healthy_recent_check(self, connection_bridge):
        """Test connection health check skipped when done recently."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
            health_status="connected",
            last_health_check=utc_now() - timedelta(minutes=1),  # Recent
        )

        result = await connection_bridge._is_connection_healthy(active_conn)
        assert result is True  # Should return based on cached status

    @pytest.mark.asyncio
    async def test_is_connection_healthy_npx_running(self, connection_bridge):
        """Test health check for NPX connection with running process."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running

        active_conn = ActiveConnection(
            server_name="context7",
            connection=connection,
            process=mock_process,
            health_status="connected",
        )

        result = await connection_bridge._is_connection_healthy(active_conn)

        assert result is True
        assert active_conn.health_status == "connected"
        assert active_conn.error_count == 0

    @pytest.mark.asyncio
    async def test_is_connection_healthy_npx_died(self, connection_bridge):
        """Test health check for NPX connection with dead process."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process died

        active_conn = ActiveConnection(
            server_name="context7",
            connection=connection,
            process=mock_process,
            health_status="connected",
        )

        result = await connection_bridge._is_connection_healthy(active_conn)

        assert result is False
        assert active_conn.health_status == "unhealthy"
        assert active_conn.error_count == 1

    @pytest.mark.asyncio
    async def test_is_connection_healthy_http_server(self, connection_bridge):
        """Test health check for HTTP-based server."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="external-server",
            connection=connection,
            client={"type": "external"},
            health_status="connected",
        )

        result = await connection_bridge._is_connection_healthy(active_conn)

        assert result is True
        assert active_conn.health_status == "connected"

    @pytest.mark.asyncio
    async def test_is_connection_healthy_no_client(self, connection_bridge):
        """Test health check with no client."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="external-server",
            connection=connection,
            client=None,
            health_status="connected",
        )

        result = await connection_bridge._is_connection_healthy(active_conn)

        assert result is False
        assert active_conn.health_status == "unhealthy"

    @pytest.mark.asyncio
    async def test_is_connection_healthy_exception(self, connection_bridge):
        """Test health check with exception."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="external-server",
            connection=connection,
            health_status="connected",
        )

        # Force exception by accessing process on non-NPX connection
        with patch.object(active_conn, "process", side_effect=Exception("Health check error")):
            result = await connection_bridge._is_connection_healthy(active_conn)

            assert result is False
            assert active_conn.health_status == "unhealthy"
            assert active_conn.error_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_connection_npx(self, connection_bridge):
        """Test cleaning up NPX connection."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_process = Mock()
        mock_client = Mock()
        mock_client.close = AsyncMock()

        active_conn = ActiveConnection(
            server_name="context7",
            connection=connection,
            client=mock_client,
            process=mock_process,
        )

        connection_bridge.active_connections["context7"] = active_conn

        with patch.object(connection_bridge.npx_manager, "stop_npx_server", return_value=True):
            await connection_bridge._cleanup_connection("context7")

            assert "context7" not in connection_bridge.active_connections
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_connection_disconnect_method(self, connection_bridge):
        """Test cleaning up connection with disconnect method."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_client = Mock(spec=["disconnect"])  # Only has disconnect method
        mock_client.disconnect = AsyncMock()

        active_conn = ActiveConnection(
            server_name="external-server",
            connection=connection,
            client=mock_client,
        )

        connection_bridge.active_connections["external-server"] = active_conn

        await connection_bridge._cleanup_connection("external-server")

        assert "external-server" not in connection_bridge.active_connections
        mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_connection_not_exists(self, connection_bridge):
        """Test cleaning up connection that doesn't exist."""
        # Should not raise exception
        await connection_bridge._cleanup_connection("nonexistent")

    @pytest.mark.asyncio
    async def test_cleanup_connection_exception(self, connection_bridge):
        """Test cleaning up connection with exception."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        mock_client = Mock()
        mock_client.close = AsyncMock(side_effect=Exception("Close error"))

        active_conn = ActiveConnection(
            server_name="external-server",
            connection=connection,
            client=mock_client,
        )

        connection_bridge.active_connections["external-server"] = active_conn

        # Should not raise exception, just log error and clean up
        await connection_bridge._cleanup_connection("external-server")

        assert "external-server" not in connection_bridge.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_server_success(self, connection_bridge):
        """Test successfully disconnecting from server."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
        )

        connection_bridge.active_connections["test-server"] = active_conn

        with patch.object(connection_bridge, "_cleanup_connection") as mock_cleanup:
            result = await connection_bridge.disconnect_server("test-server")

            assert result is True
            mock_cleanup.assert_called_once_with("test-server")

    @pytest.mark.asyncio
    async def test_disconnect_server_not_connected(self, connection_bridge):
        """Test disconnecting from server that's not connected."""
        result = await connection_bridge.disconnect_server("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_server_exception(self, connection_bridge):
        """Test disconnecting from server with exception."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
        )

        connection_bridge.active_connections["test-server"] = active_conn

        with patch.object(connection_bridge, "_cleanup_connection", side_effect=Exception("Cleanup error")):
            result = await connection_bridge.disconnect_server("test-server")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_connection_status(self, connection_bridge):
        """Test getting connection status."""
        # Setup multiple connections
        connection1 = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection2 = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn1 = ActiveConnection(
            server_name="external-server",
            connection=connection1,
            health_status="connected",
            error_count=0,
        )

        active_conn2 = ActiveConnection(
            server_name="context7",
            connection=connection2,
            health_status="connected",
            error_count=1,
        )

        connection_bridge.active_connections["external-server"] = active_conn1
        connection_bridge.active_connections["context7"] = active_conn2

        with (
            patch.object(connection_bridge, "_is_connection_healthy", return_value=True),
            patch.object(
                connection_bridge.npx_manager,
                "get_process_status",
                return_value={"status": "running", "pid": 12345},
            ),
        ):

            status = await connection_bridge.get_connection_status()

            assert status["total_connections"] == 2
            assert "external-server" in status["connections"]
            assert "context7" in status["connections"]
            assert "context7" in status["npx_processes"]

            ext_conn = status["connections"]["external-server"]
            assert ext_conn["type"] == "external"
            assert ext_conn["healthy"] is True
            assert ext_conn["error_count"] == 0

    @pytest.mark.asyncio
    async def test_health_check_success(self, connection_bridge):
        """Test successful health check."""
        # Setup healthy connections
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn = ActiveConnection(
            server_name="test-server",
            connection=connection,
            health_status="connected",
        )

        connection_bridge.active_connections["test-server"] = active_conn

        mock_status = {
            "total_connections": 1,
            "connections": {
                "test-server": {"healthy": True},
            },
        }

        with patch.object(connection_bridge, "get_connection_status", return_value=mock_status):
            health = await connection_bridge.health_check()

            assert health["healthy"] is True
            assert health["total_connections"] == 1
            assert health["healthy_connections"] == 1
            assert health["discovery_available"] is True
            assert health["npx_manager_available"] is True

    @pytest.mark.asyncio
    async def test_health_check_no_connections(self, connection_bridge):
        """Test health check with no connections."""
        mock_status = {
            "total_connections": 0,
            "connections": {},
        }

        with patch.object(connection_bridge, "get_connection_status", return_value=mock_status):
            health = await connection_bridge.health_check()

            assert health["healthy"] is False  # No connections means unhealthy

    @pytest.mark.asyncio
    async def test_health_check_mixed_health(self, connection_bridge):
        """Test health check with mixed connection health."""
        mock_status = {
            "total_connections": 2,
            "connections": {
                "healthy-server": {"healthy": True},
                "unhealthy-server": {"healthy": False},
            },
        }

        # Setup connections
        connection_bridge.active_connections["healthy-server"] = Mock()
        connection_bridge.active_connections["unhealthy-server"] = Mock()

        with patch.object(connection_bridge, "get_connection_status", return_value=mock_status):
            health = await connection_bridge.health_check()

            assert health["healthy"] is False  # Not all connections healthy
            assert health["total_connections"] == 2
            assert health["healthy_connections"] == 1

    @pytest.mark.asyncio
    async def test_health_check_exception(self, connection_bridge):
        """Test health check with exception."""
        with patch.object(connection_bridge, "get_connection_status", side_effect=Exception("Status error")):
            health = await connection_bridge.health_check()

            assert health["healthy"] is False
            assert "error" in health
            assert health["error"] == "Status error"

    @pytest.mark.asyncio
    async def test_shutdown(self, connection_bridge):
        """Test shutting down connection bridge."""
        # Setup connections
        connection1 = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        connection2 = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        active_conn1 = ActiveConnection(server_name="server1", connection=connection1)
        active_conn2 = ActiveConnection(server_name="server2", connection=connection2)

        connection_bridge.active_connections["server1"] = active_conn1
        connection_bridge.active_connections["server2"] = active_conn2

        with patch.object(connection_bridge, "disconnect_server", return_value=True) as mock_disconnect:
            await connection_bridge.shutdown()

            # Should disconnect all servers
            assert mock_disconnect.call_count == 2
            calls = [call.args[0] for call in mock_disconnect.call_args_list]
            assert "server1" in calls
            assert "server2" in calls


class TestConnectionBridgeIntegration:
    """Integration tests for MCPConnectionBridge."""

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        # Setup mock discovery
        mock_discovery = Mock()
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )
        mock_discovery.discover_server = AsyncMock(return_value=connection)

        bridge = MCPConnectionBridge(discovery=mock_discovery)

        # Mock NPX process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.pid = 12345

        with (
            patch("subprocess.Popen", return_value=mock_process),
            patch("asyncio.sleep"),
            patch("src.mcp_integration.connection_bridge.ZenMCPStdioClient") as mock_client_cls,
        ):

            mock_client = Mock()
            mock_client_cls.return_value = mock_client

            # Connect to server
            active_conn = await bridge.connect_to_server("context7")
            assert active_conn is not None
            assert active_conn.server_name == "context7"
            assert active_conn.health_status == "connected"

            # Check connection status
            status = await bridge.get_connection_status()
            assert status["total_connections"] == 1
            assert "context7" in status["connections"]

            # Health check
            health = await bridge.health_check()
            assert health["healthy"] is True

            # Disconnect
            result = await bridge.disconnect_server("context7")
            assert result is True

            # Verify cleanup
            status = await bridge.get_connection_status()
            assert status["total_connections"] == 0

    @pytest.mark.asyncio
    async def test_multiple_connection_types(self):
        """Test handling multiple connection types simultaneously."""
        mock_discovery = Mock()

        # Setup different connection types
        npx_connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        external_connection = ServerConnection(
            url="http://remote:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        docker_connection = ServerConnection(
            url="http://localhost:8080",
            type="docker",
            health_status="running",
            resource_usage={"container_id": "abc123"},
            discovered_at=utc_now(),
        )

        def mock_discover(server_name):
            if server_name == "context7":
                return npx_connection
            if server_name == "external-server":
                return external_connection
            if server_name == "docker-server":
                return docker_connection
            return None

        mock_discovery.discover_server = AsyncMock(side_effect=mock_discover)
        bridge = MCPConnectionBridge(discovery=mock_discovery)

        # Mock NPX process for context7
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345

        with (
            patch("subprocess.Popen", return_value=mock_process),
            patch("asyncio.sleep"),
            patch("src.mcp_integration.connection_bridge.ZenMCPStdioClient"),
        ):

            # Connect to all server types
            npx_conn = await bridge.connect_to_server("context7")
            external_conn = await bridge.connect_to_server("external-server")
            docker_conn = await bridge.connect_to_server("docker-server")

            assert npx_conn is not None
            assert external_conn is not None
            assert docker_conn is not None

            # Verify all connections are tracked
            status = await bridge.get_connection_status()
            assert status["total_connections"] == 3
            assert "context7" in status["connections"]
            assert "external-server" in status["connections"]
            assert "docker-server" in status["connections"]

            # NPX should have process info
            assert "context7" in status["npx_processes"]

            # Clean shutdown
            await bridge.shutdown()

            final_status = await bridge.get_connection_status()
            assert final_status["total_connections"] == 0

    @pytest.mark.asyncio
    async def test_connection_resilience(self):
        """Test connection resilience and recovery."""
        mock_discovery = Mock()
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )
        mock_discovery.discover_server = AsyncMock(return_value=connection)

        bridge = MCPConnectionBridge(discovery=mock_discovery)

        # Initial connection
        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.pid = 12345

        with (
            patch("subprocess.Popen", return_value=mock_process),
            patch("asyncio.sleep"),
            patch("src.mcp_integration.connection_bridge.ZenMCPStdioClient"),
        ):

            active_conn = await bridge.connect_to_server("context7")
            assert active_conn is not None

            # Simulate process dying
            mock_process.poll.return_value = 1  # Process died

            # Health check should detect failure
            is_healthy = await bridge._is_connection_healthy(active_conn)
            assert is_healthy is False
            assert active_conn.health_status == "unhealthy"

            # Reconnection attempt should clean up and create new connection
            mock_process.poll.return_value = None  # New process running
            new_active_conn = await bridge.connect_to_server("context7")
            assert new_active_conn is not None
            assert new_active_conn.health_status == "connected"


class TestConnectionBridgeModuleExports:
    """Test module exports and imports."""

    def test_module_exports(self):
        """Test that the module exports the expected classes."""
        from src.mcp_integration.connection_bridge import ActiveConnection, MCPConnectionBridge, NPXProcessManager

        assert ActiveConnection is not None
        assert NPXProcessManager is not None
        assert MCPConnectionBridge is not None
