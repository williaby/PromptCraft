from src.utils.datetime_compat import utc_now


"""
Tests for smart MCP server discovery system.

Test Coverage for src/mcp_integration/smart_discovery.py:
- ServerConnection and ServerRequirements dataclasses
- ResourceMonitor system resource monitoring
- SmartMCPDiscovery intelligent server discovery and deployment
- Anti-duplication mechanisms and caching
- Multi-strategy deployment detection
- Resource management and requirements checking
- Docker container detection
- NPX server handling
- Health checking and verification
"""

import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pytest

from src.mcp_integration.smart_discovery import (
    ResourceError,
    ResourceMonitor,
    ServerConnection,
    ServerRequirements,
    SmartMCPDiscovery,
)


class TestServerConnection:
    """Test ServerConnection dataclass."""

    def test_server_connection_creation(self):
        """Test creating a ServerConnection instance."""
        discovered_at = utc_now()

        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={"port": 8000, "memory": 512},
            discovered_at=discovered_at,
        )

        assert connection.url == "http://localhost:8000"
        assert connection.type == "external"
        assert connection.health_status == "healthy"
        assert connection.resource_usage == {"port": 8000, "memory": 512}
        assert connection.discovered_at == discovered_at

    def test_server_connection_npx_type(self):
        """Test ServerConnection for NPX type servers."""
        connection = ServerConnection(
            url="npx://@upstash/context7-mcp",
            type="npx",
            health_status="on_demand",
            resource_usage={"package": "@upstash/context7-mcp"},
            discovered_at=utc_now(),
        )

        assert connection.type == "npx"
        assert connection.health_status == "on_demand"
        assert "package" in connection.resource_usage


class TestServerRequirements:
    """Test ServerRequirements dataclass."""

    def test_server_requirements_creation(self):
        """Test creating a ServerRequirements instance."""
        requirements = ServerRequirements(
            memory=512,
            cpu=0.5,
            ports=[8000, 8001],
            dependencies=["python", "poetry"],
        )

        assert requirements.memory == 512
        assert requirements.cpu == 0.5
        assert requirements.ports == [8000, 8001]
        assert requirements.dependencies == ["python", "poetry"]

    def test_server_requirements_minimal(self):
        """Test ServerRequirements with minimal configuration."""
        requirements = ServerRequirements(
            memory=100,
            cpu=0.1,
            ports=[],
            dependencies=["node"],
        )

        assert requirements.memory == 100
        assert requirements.cpu == 0.1
        assert requirements.ports == []
        assert requirements.dependencies == ["node"]


class TestResourceMonitor:
    """Test ResourceMonitor class."""

    @pytest.fixture
    def resource_monitor(self):
        """Create a ResourceMonitor instance for testing."""
        return ResourceMonitor()

    def test_resource_monitor_initialization(self, resource_monitor):
        """Test ResourceMonitor initialization."""
        assert resource_monitor.logger is not None

    def test_get_available_memory(self, resource_monitor):
        """Test getting available memory."""
        with patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value = Mock(available=2048 * 1024 * 1024)  # 2GB in bytes

            available_mb = resource_monitor.get_available_memory()
            assert available_mb == 2048

    def test_get_cpu_usage(self, resource_monitor):
        """Test getting CPU usage."""
        with patch("psutil.cpu_percent", return_value=45.5):
            cpu_usage = resource_monitor.get_cpu_usage()
            assert cpu_usage == 45.5

    def test_is_port_available_true(self, resource_monitor):
        """Test port availability check when port is available."""
        with patch("socket.socket") as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 1  # Connection failed (port available)
            mock_socket.return_value.__enter__.return_value = mock_sock

            result = resource_monitor.is_port_available(8080)
            assert result is True

    def test_is_port_available_false(self, resource_monitor):
        """Test port availability check when port is in use."""
        with patch("socket.socket") as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0  # Connection successful (port in use)
            mock_socket.return_value.__enter__.return_value = mock_sock

            result = resource_monitor.is_port_available(8080)
            assert result is False

    def test_is_port_available_exception(self, resource_monitor):
        """Test port availability check with exception."""
        with patch("socket.socket", side_effect=Exception("Socket error")):
            result = resource_monitor.is_port_available(8080)
            assert result is False

    def test_check_process_exists_by_name(self, resource_monitor):
        """Test process existence check by name."""
        mock_proc1 = Mock()
        mock_proc1.info = {"pid": 1234, "name": "zen-mcp-server", "cmdline": []}

        mock_proc2 = Mock()
        mock_proc2.info = {"pid": 5678, "name": "python", "cmdline": []}

        with patch("psutil.process_iter", return_value=[mock_proc1, mock_proc2]):
            result = resource_monitor.check_process_exists("zen-mcp")
            assert result is True

    def test_check_process_exists_by_cmdline(self, resource_monitor):
        """Test process existence check by command line."""
        mock_proc = Mock()
        mock_proc.info = {
            "pid": 1234,
            "name": "python",
            "cmdline": ["python", "-m", "zen-mcp-server"],
        }

        with patch("psutil.process_iter", return_value=[mock_proc]):
            result = resource_monitor.check_process_exists("zen-mcp-server")
            assert result is True

    def test_check_process_exists_not_found(self, resource_monitor):
        """Test process existence check when process not found."""
        mock_proc = Mock()
        mock_proc.info = {"pid": 1234, "name": "other-process", "cmdline": []}

        with patch("psutil.process_iter", return_value=[mock_proc]):
            result = resource_monitor.check_process_exists("zen-mcp")
            assert result is False

    def test_check_process_exists_exception(self, resource_monitor):
        """Test process existence check with exception."""
        with patch("psutil.process_iter", side_effect=Exception("Process error")):
            result = resource_monitor.check_process_exists("zen-mcp")
            assert result is False


class TestSmartMCPDiscovery:
    """Test SmartMCPDiscovery class."""

    @pytest.fixture
    def discovery_system(self):
        """Create a SmartMCPDiscovery instance for testing."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            return SmartMCPDiscovery()

    @pytest.fixture
    def discovery_system_with_docker(self):
        """Create a SmartMCPDiscovery instance with Docker available."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            return SmartMCPDiscovery()

    def test_smart_mcp_discovery_initialization(self, discovery_system):
        """Test SmartMCPDiscovery initialization."""
        assert discovery_system.config_path.name == "discovery-config.yaml"
        assert isinstance(discovery_system.deployment_cache, dict)
        assert discovery_system.resource_monitor is not None
        assert discovery_system.cache_ttl == timedelta(minutes=5)
        assert discovery_system.docker_client is None

    def test_initialization_with_docker(self, discovery_system_with_docker):
        """Test initialization when Docker is available."""
        assert discovery_system_with_docker.docker_client is not None

    def test_load_server_requirements(self, discovery_system):
        """Test loading server requirements."""
        requirements = discovery_system.server_requirements

        assert "zen-mcp" in requirements
        assert "context7" in requirements
        assert "perplexity" in requirements
        assert "sentry" in requirements

        zen_req = requirements["zen-mcp"]
        assert zen_req.memory == 512
        assert zen_req.cpu == 0.5
        assert 8000 in zen_req.ports
        assert "python" in zen_req.dependencies

    def test_get_cached_connection_not_exists(self, discovery_system):
        """Test getting cached connection when it doesn't exist."""
        result = discovery_system.get_cached_connection("nonexistent")
        assert result is None

    def test_get_cached_connection_expired(self, discovery_system):
        """Test getting cached connection when it's expired."""
        old_connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now() - timedelta(minutes=10),  # Expired
        )
        discovery_system.deployment_cache["test-server"] = old_connection

        result = discovery_system.get_cached_connection("test-server")
        assert result is None
        assert "test-server" not in discovery_system.deployment_cache

    def test_get_cached_connection_unhealthy(self, discovery_system):
        """Test getting cached connection when health check fails."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),  # Fresh
        )
        discovery_system.deployment_cache["test-server"] = connection

        with patch.object(discovery_system, "verify_health", return_value=False):
            result = discovery_system.get_cached_connection("test-server")
            assert result is None
            assert "test-server" not in discovery_system.deployment_cache

    def test_get_cached_connection_valid(self, discovery_system):
        """Test getting cached connection when it's valid."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),  # Fresh
        )
        discovery_system.deployment_cache["test-server"] = connection

        with patch.object(discovery_system, "verify_health", return_value=True):
            result = discovery_system.get_cached_connection("test-server")
            assert result == connection

    @pytest.mark.asyncio
    async def test_discover_server_cached(self, discovery_system):
        """Test server discovery using cached connection."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with patch.object(discovery_system, "get_cached_connection", return_value=connection):
            result = await discovery_system.discover_server("test-server")
            assert result == connection

    @pytest.mark.asyncio
    async def test_discover_server_existing_deployment(self, discovery_system):
        """Test server discovery finding existing deployment."""
        connection = ServerConnection(
            url="http://localhost:8001",
            type="user",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with (
            patch.object(discovery_system, "get_cached_connection", return_value=None),
            patch.object(discovery_system, "find_existing_deployment", return_value=connection),
        ):

            result = await discovery_system.discover_server("test-server")
            assert result == connection
            assert discovery_system.deployment_cache["test-server"] == connection

    @pytest.mark.asyncio
    async def test_discover_server_insufficient_resources(self, discovery_system):
        """Test server discovery with insufficient resources."""
        with (
            patch.object(discovery_system, "get_cached_connection", return_value=None),
            patch.object(discovery_system, "find_existing_deployment", return_value=None),
            patch.object(discovery_system.resource_monitor, "get_available_memory", return_value=100),
            patch.object(discovery_system, "try_cloud_deployment", return_value=None),
            pytest.raises(ResourceError),
        ):
            await discovery_system.discover_server("zen-mcp")  # Requires 512MB

    @pytest.mark.asyncio
    async def test_discover_server_cloud_fallback(self, discovery_system):
        """Test server discovery with cloud fallback."""
        cloud_connection = ServerConnection(
            url="npx://cloud",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with (
            patch.object(discovery_system, "get_cached_connection", return_value=None),
            patch.object(discovery_system, "find_existing_deployment", return_value=None),
            patch.object(discovery_system.resource_monitor, "get_available_memory", return_value=100),
            patch.object(discovery_system, "try_cloud_deployment", return_value=cloud_connection),
        ):

            result = await discovery_system.discover_server("zen-mcp")
            assert result == cloud_connection

    @pytest.mark.asyncio
    async def test_discover_server_new_deployment(self, discovery_system):
        """Test server discovery deploying new server."""
        new_connection = ServerConnection(
            url="http://localhost:8002",
            type="embedded",
            health_status="healthy",
            resource_usage={"port": 8002},
            discovered_at=utc_now(),
        )

        with (
            patch.object(discovery_system, "get_cached_connection", return_value=None),
            patch.object(discovery_system, "find_existing_deployment", return_value=None),
            patch.object(discovery_system.resource_monitor, "get_available_memory", return_value=1024),
            patch.object(discovery_system, "deploy_server", return_value=new_connection),
            patch("filelock.FileLock") as mock_lock,
        ):

            mock_lock.return_value.__enter__.return_value = Mock()

            result = await discovery_system.discover_server("zen-mcp")
            assert result == new_connection

    @pytest.mark.asyncio
    async def test_find_existing_deployment_multiple_strategies(self, discovery_system):
        """Test finding existing deployment using multiple strategies."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="healthy",
            resource_usage={},
            discovered_at=utc_now(),
        )

        # Mock first strategy to fail, second to succeed
        with (
            patch.object(discovery_system, "check_known_ports", return_value=None),
            patch.object(discovery_system, "check_process_list", return_value=connection),
            patch.object(discovery_system, "verify_health", return_value=True),
        ):

            result = await discovery_system.find_existing_deployment("zen-mcp")
            assert result == connection

    @pytest.mark.asyncio
    async def test_find_existing_deployment_unhealthy(self, discovery_system):
        """Test finding existing deployment but health check fails."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="unknown",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with (
            patch.object(discovery_system, "check_known_ports", return_value=connection),
            patch.object(discovery_system, "verify_health", return_value=False),
        ):

            result = await discovery_system.find_existing_deployment("zen-mcp")
            assert result is None

    @pytest.mark.asyncio
    async def test_check_known_ports_success(self, discovery_system):
        """Test checking known ports and finding a healthy server."""
        with (
            patch.object(discovery_system.resource_monitor, "is_port_available", return_value=False),
            patch("requests.get") as mock_get,
        ):

            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await discovery_system.check_known_ports("zen-mcp")
            assert result is not None
            assert result.url == "http://localhost:8000"
            assert result.type == "external"

    @pytest.mark.asyncio
    async def test_check_known_ports_no_servers(self, discovery_system):
        """Test checking known ports when no servers are running."""
        with patch.object(discovery_system.resource_monitor, "is_port_available", return_value=True):
            result = await discovery_system.check_known_ports("zen-mcp")
            assert result is None

    @pytest.mark.asyncio
    async def test_check_known_ports_npx_server(self, discovery_system):
        """Test checking known ports for NPX-based servers."""
        result = await discovery_system.check_known_ports("context7")
        assert result is None  # NPX servers don't have fixed ports

    @pytest.mark.asyncio
    async def test_check_process_list_found(self, discovery_system):
        """Test checking process list and finding a server."""
        with (
            patch.object(discovery_system.resource_monitor, "check_process_exists", return_value=True),
            patch.object(discovery_system, "extract_url_from_process", return_value="http://localhost:8000"),
        ):

            result = await discovery_system.check_process_list("zen-mcp")
            assert result is not None
            assert result.url == "http://localhost:8000"
            assert result.type == "user"

    @pytest.mark.asyncio
    async def test_check_process_list_not_found(self, discovery_system):
        """Test checking process list when no processes found."""
        with patch.object(discovery_system.resource_monitor, "check_process_exists", return_value=False):
            result = await discovery_system.check_process_list("zen-mcp")
            assert result is None

    @pytest.mark.asyncio
    async def test_check_node_modules_binary_exists(self, discovery_system):
        """Test checking node_modules for NPX servers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            node_modules_bin = Path(temp_dir) / "node_modules" / ".bin"
            node_modules_bin.mkdir(parents=True)

            # Create a mock binary
            context7_bin = node_modules_bin / "context7-mcp"
            context7_bin.touch()

            with patch("pathlib.Path.cwd", return_value=Path(temp_dir)):
                result = await discovery_system.check_node_modules("context7")
                assert result is not None
                assert result.url == "npx://@upstash/context7-mcp"
                assert result.type == "npx"

    @pytest.mark.asyncio
    async def test_check_node_modules_package_json(self, discovery_system):
        """Test checking package.json for NPX dependencies when binary not found."""
        import os

        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Create package.json first
                package_json_path = Path(temp_dir) / "package.json"
                package_data = {
                    "dependencies": {
                        "@upstash/context7-mcp": "^1.0.0",
                    },
                }
                package_json_path.write_text(json.dumps(package_data))

                # Change to temp directory to isolate from real node_modules
                os.chdir(temp_dir)

                result = await discovery_system.check_node_modules("context7")
                assert result is not None
                assert result.url == "npx://@upstash/context7-mcp"
                assert result.type == "npx"
                assert result.resource_usage["version"] == "^1.0.0"
            finally:
                # Always restore original directory
                os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_check_node_modules_not_found(self, discovery_system):
        """Test checking node_modules when nothing is found."""
        import os

        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Change to temp directory with no node_modules or package.json
                os.chdir(temp_dir)
                result = await discovery_system.check_node_modules("context7")
                assert result is None
            finally:
                os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_check_docker_containers_found(self, discovery_system_with_docker):
        """Test checking Docker containers and finding a server."""
        mock_container = Mock()
        mock_container.name = "zen-mcp-server"
        mock_container.image = Mock()
        mock_container.short_id = "abc123"
        mock_container.ports = {"8000/tcp": [{"HostPort": "8000"}]}

        discovery_system_with_docker.docker_client.containers.list.return_value = [mock_container]

        result = await discovery_system_with_docker.check_docker_containers("zen-mcp")
        assert result is not None
        assert result.url == "http://localhost:8000"
        assert result.type == "docker"
        assert result.resource_usage["container_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_check_docker_containers_no_docker(self, discovery_system):
        """Test checking Docker containers when Docker is not available."""
        result = await discovery_system.check_docker_containers("zen-mcp")
        assert result is None

    @pytest.mark.asyncio
    async def test_check_lock_files_found(self, discovery_system):
        """Test checking lock files and finding server info."""
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = Path(temp_dir) / ".zen-mcp.lock"
            lock_file.write_text("http://localhost:8000")

            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                result = await discovery_system.check_lock_files("zen-mcp")
                assert result is not None
                assert result.url == "http://localhost:8000"
                assert result.type == "user"

    @pytest.mark.asyncio
    async def test_check_lock_files_not_found(self, discovery_system):
        """Test checking lock files when none exist."""
        result = await discovery_system.check_lock_files("zen-mcp")
        assert result is None

    @pytest.mark.asyncio
    async def test_check_env_variables_found(self, discovery_system):
        """Test checking environment variables for server URLs."""
        with patch.dict(os.environ, {"ZEN_MCP_URL": "http://localhost:8000"}):
            result = await discovery_system.check_env_variables("zen-mcp")
            assert result is not None
            assert result.url == "http://localhost:8000"
            assert result.type == "external"

    @pytest.mark.asyncio
    async def test_check_env_variables_not_found(self, discovery_system):
        """Test checking environment variables when none are set."""
        import os

        # Clear zen-mcp environment variables for this test
        with patch.dict(
            os.environ,
            {
                "ZEN_MCP_URL": "",
                "PROMPTCRAFT_ZEN_MCP_SERVER_URL": "",
            },
            clear=False,
        ):
            result = await discovery_system.check_env_variables("zen-mcp")
            assert result is None

    @pytest.mark.asyncio
    async def test_try_cloud_deployment_supported(self, discovery_system):
        """Test cloud deployment for supported servers."""
        result = await discovery_system.try_cloud_deployment("context7")
        assert result is not None
        assert result.url == "npx://cloud"
        assert result.type == "npx"
        assert result.health_status == "on_demand"

    @pytest.mark.asyncio
    async def test_try_cloud_deployment_unsupported(self, discovery_system):
        """Test cloud deployment for unsupported servers."""
        result = await discovery_system.try_cloud_deployment("zen-mcp")
        assert result is None

    @pytest.mark.asyncio
    async def test_deploy_server_zen_mcp(self, discovery_system):
        """Test deploying zen-mcp server."""
        with patch.object(discovery_system, "deploy_zen_server") as mock_deploy:
            mock_connection = ServerConnection(
                url="http://localhost:8000",
                type="embedded",
                health_status="healthy",
                resource_usage={},
                discovered_at=utc_now(),
            )
            mock_deploy.return_value = mock_connection

            result = await discovery_system.deploy_server("zen-mcp")
            assert result == mock_connection
            mock_deploy.assert_called_once_with("zen-mcp")

    @pytest.mark.asyncio
    async def test_deploy_server_npx(self, discovery_system):
        """Test deploying NPX-based server."""
        result = await discovery_system.deploy_server("context7")
        assert result.url == "npx://cloud"
        assert result.type == "npx"

    @pytest.mark.asyncio
    async def test_deploy_server_unknown(self, discovery_system):
        """Test deploying unknown server type."""
        with pytest.raises(ValueError, match="No deployment strategy"):
            await discovery_system.deploy_server("unknown-server")

    @pytest.mark.asyncio
    async def test_deploy_zen_server_success(self, discovery_system):
        """Test successfully deploying zen-mcp server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            zen_path = Path(temp_dir) / "zen-mcp-server"
            zen_path.mkdir()

            mock_process = Mock()
            mock_process.pid = 12345

            with (
                patch("subprocess.Popen", return_value=mock_process),
                patch("asyncio.sleep"),
                patch.object(discovery_system, "find_available_port", return_value=8000),
                patch.object(discovery_system, "verify_health", return_value=True),
                patch("pathlib.Path.exists", return_value=True),
            ):

                # Mock zen path exists
                original_exists = Path.exists

                def mock_exists(self):
                    if str(self) == str(zen_path):
                        return True
                    return original_exists(self)

                with patch.object(Path, "exists", mock_exists):
                    result = await discovery_system.deploy_zen_server("zen-mcp")

                    assert result is not None
                    assert result.url == "http://localhost:8000"
                    assert result.type == "embedded"
                    assert result.resource_usage["pid"] == 12345

    @pytest.mark.asyncio
    async def test_deploy_zen_server_no_path_found(self, discovery_system):
        """Test deploying zen-mcp server when no valid path is found."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="Could not deploy"):
                await discovery_system.deploy_zen_server("zen-mcp")

    @pytest.mark.asyncio
    async def test_deploy_npx_server(self, discovery_system):
        """Test deploying NPX server."""
        result = await discovery_system.deploy_npx_server("context7")
        assert result.url == "npx://cloud"
        assert result.type == "npx"
        assert result.health_status == "on_demand"

    def test_find_available_port_success(self, discovery_system):
        """Test finding an available port."""
        with patch.object(discovery_system.resource_monitor, "is_port_available") as mock_available:
            mock_available.side_effect = [False, False, True]  # Port 8002 is available

            port = discovery_system.find_available_port(8000, 8010)
            assert port == 8002

    def test_find_available_port_no_ports(self, discovery_system):
        """Test finding available port when none are available."""
        with patch.object(discovery_system.resource_monitor, "is_port_available", return_value=False):
            with pytest.raises(RuntimeError, match="No available ports"):
                discovery_system.find_available_port(8000, 8002)

    def test_verify_health_http_success(self, discovery_system):
        """Test health verification for HTTP server."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="unknown",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = discovery_system.verify_health(connection)
            assert result is True

    def test_verify_health_http_failure(self, discovery_system):
        """Test health verification when HTTP server is unhealthy."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="unknown",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            result = discovery_system.verify_health(connection)
            assert result is False

    def test_verify_health_npx_always_healthy(self, discovery_system):
        """Test health verification for NPX servers (always healthy)."""
        connection = ServerConnection(
            url="npx://cloud",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

        result = discovery_system.verify_health(connection)
        assert result is True

    def test_verify_health_exception(self, discovery_system):
        """Test health verification with network exception."""
        connection = ServerConnection(
            url="http://localhost:8000",
            type="external",
            health_status="unknown",
            resource_usage={},
            discovered_at=utc_now(),
        )

        with patch("requests.get", side_effect=Exception("Network error")):
            result = discovery_system.verify_health(connection)
            assert result is False

    @pytest.mark.asyncio
    async def test_extract_url_from_process_zen_mcp(self, discovery_system):
        """Test extracting URL from zen-mcp process."""
        url = await discovery_system.extract_url_from_process("zen-mcp-server")
        assert url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_extract_url_from_process_unknown(self, discovery_system):
        """Test extracting URL from unknown process."""
        url = await discovery_system.extract_url_from_process("unknown-process")
        assert url is None


class TestResourceError:
    """Test ResourceError exception."""

    def test_resource_error_creation(self):
        """Test creating ResourceError exception."""
        error = ResourceError("Insufficient memory")
        assert str(error) == "Insufficient memory"

    def test_resource_error_raising(self):
        """Test raising ResourceError exception."""
        with pytest.raises(ResourceError, match="Not enough CPU"):
            raise ResourceError("Not enough CPU")


class TestSmartMCPDiscoveryIntegration:
    """Integration tests for SmartMCPDiscovery."""

    @pytest.mark.asyncio
    async def test_complete_discovery_workflow(self):
        """Test complete server discovery workflow."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            discovery = SmartMCPDiscovery()

        # Test discovering an NPX server that should use cloud deployment
        with patch.object(discovery.resource_monitor, "get_available_memory", return_value=2048):
            result = await discovery.discover_server("context7")

            assert result is not None
            assert result.type == "npx"
            assert result.health_status in ["on_demand", "available"]

        # Test that subsequent calls use cache
        cached_result = await discovery.discover_server("context7")
        assert cached_result == result

    @pytest.mark.asyncio
    async def test_resource_constrained_environment(self):
        """Test discovery in resource-constrained environment."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            discovery = SmartMCPDiscovery()

        # Simulate low memory environment
        with patch.object(discovery.resource_monitor, "get_available_memory", return_value=100):
            # Mock find_existing_deployment to return None so we hit resource constraints
            with patch.object(discovery, "find_existing_deployment", return_value=None):
                # Should fall back to cloud for zen-mcp (requires 512MB)
                with patch.object(discovery, "try_cloud_deployment", return_value=None):
                    with pytest.raises(ResourceError):
                        await discovery.discover_server("zen-mcp")

                # Should work for context7 (requires 100MB)
                result = await discovery.discover_server("context7")
                assert result is not None

    @pytest.mark.asyncio
    async def test_multi_strategy_discovery_fallback(self):
        """Test multiple discovery strategies with fallbacks."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            discovery = SmartMCPDiscovery()

        # Mock all strategies to fail except the last one
        with (
            patch.object(discovery, "check_known_ports", return_value=None),
            patch.object(discovery, "check_process_list", return_value=None),
            patch.object(discovery, "check_docker_containers", return_value=None),
            patch.object(discovery, "check_node_modules", return_value=None),
            patch.object(discovery, "check_lock_files", return_value=None),
        ):

            # Mock environment variables strategy to succeed
            env_connection = ServerConnection(
                url="http://localhost:8000",
                type="external",
                health_status="healthy",
                resource_usage={},
                discovered_at=utc_now(),
            )

            with (
                patch.object(discovery, "check_env_variables", return_value=env_connection),
                patch.object(discovery, "verify_health", return_value=True),
            ):

                result = await discovery.find_existing_deployment("zen-mcp")
                assert result == env_connection

    @pytest.mark.asyncio
    async def test_concurrent_discovery_with_locking(self):
        """Test concurrent discovery with file locking."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            discovery = SmartMCPDiscovery()

        # Simulate concurrent discovery attempts
        async def discover_server():
            with (
                patch.object(discovery, "get_cached_connection", return_value=None),
                patch.object(discovery, "find_existing_deployment", return_value=None),
                patch.object(discovery.resource_monitor, "get_available_memory", return_value=1024),
                patch("filelock.FileLock") as mock_lock,
            ):

                mock_lock.return_value.__enter__.return_value = Mock()

                # Mock deployment to return a connection
                mock_connection = ServerConnection(
                    url="http://localhost:8000",
                    type="embedded",
                    health_status="healthy",
                    resource_usage={},
                    discovered_at=utc_now(),
                )

                with patch.object(discovery, "deploy_server", return_value=mock_connection):
                    return await discovery.discover_server("zen-mcp")

        # Run multiple concurrent discoveries
        results = await asyncio.gather(*[discover_server() for _ in range(3)])

        # All should succeed (each uses its own mock)
        assert len(results) == 3
        assert all(r is not None for r in results)

    def test_configuration_and_requirements_loading(self):
        """Test configuration loading and server requirements."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            discovery = SmartMCPDiscovery()

        # Verify all expected servers have requirements
        expected_servers = ["zen-mcp", "context7", "perplexity", "sentry"]
        for server in expected_servers:
            assert server in discovery.server_requirements
            req = discovery.server_requirements[server]
            assert isinstance(req.memory, int)
            assert isinstance(req.cpu, float)
            assert isinstance(req.ports, list)
            assert isinstance(req.dependencies, list)

    def test_resource_monitor_integration(self):
        """Test resource monitor integration."""
        with patch("docker.from_env", side_effect=Exception("Docker not available")):
            discovery = SmartMCPDiscovery()

        monitor = discovery.resource_monitor

        # Test that resource monitor methods work
        with patch("psutil.virtual_memory") as mock_memory, patch("psutil.cpu_percent", return_value=50.0):

            mock_memory.return_value = Mock(available=1024 * 1024 * 1024)  # 1GB

            memory = monitor.get_available_memory()
            cpu = monitor.get_cpu_usage()

            assert memory == 1024  # Should be in MB
            assert cpu == 50.0


class TestSmartMCPDiscoveryModuleExports:
    """Test module exports and imports."""

    def test_module_exports(self):
        """Test that the module exports the expected classes."""
        from src.mcp_integration.smart_discovery import (
            ResourceError,
            ResourceMonitor,
            ServerConnection,
            ServerRequirements,
            SmartMCPDiscovery,
        )

        assert ServerConnection is not None
        assert ServerRequirements is not None
        assert ResourceMonitor is not None
        assert SmartMCPDiscovery is not None
        assert ResourceError is not None
