"""
Smart MCP Server Discovery System

Intelligent discovery system for MCP servers with anti-duplication,
resource management, and intelligent fallback strategies.
"""

import asyncio
import contextlib
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import tempfile
from typing import Any

from filelock import FileLock
import psutil
import requests

from src.utils.datetime_compat import utc_now
from src.utils.logging_mixin import LoggerMixin


# Docker client (optional dependency)
docker: Any = None
with contextlib.suppress(ImportError):
    import docker


logger = logging.getLogger(__name__)


@dataclass
class ServerConnection:
    """Represents a discovered MCP server connection."""

    url: str
    type: str  # 'external', 'user', 'docker', 'npx', 'embedded'
    health_status: str
    resource_usage: dict
    discovered_at: datetime


@dataclass
class ServerRequirements:
    """Server resource requirements."""

    memory: int  # MB
    cpu: float  # CPU cores
    ports: list[int]
    dependencies: list[str]


class ResourceMonitor:
    """Monitor system resources for agent deployment decisions."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

    def get_available_memory(self) -> int:
        """Get available memory in MB."""
        return int(psutil.virtual_memory().available // (1024 * 1024))

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return float(psutil.cpu_percent(interval=1))

    def is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                return result != 0
        except Exception as e:
            self.logger.debug(f"Port check failed for {port}: {e}")
            return False

    def check_process_exists(self, process_name: str) -> bool:
        """Check if a process with given name is running."""
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if process_name.lower() in proc.info["name"].lower():
                    return True
                if proc.info["cmdline"] and any(process_name in arg for arg in proc.info["cmdline"]):
                    return True
        except Exception as e:
            self.logger.debug(f"Process check failed for {process_name}: {e}")
        return False


class SmartMCPDiscovery(LoggerMixin):
    """Smart MCP server discovery with anti-duplication and resource management."""

    def __init__(self, config_path: Path | None = None) -> None:
        super().__init__()
        self.config_path = config_path or Path(".mcp/discovery-config.yaml")
        self.deployment_cache: dict[str, ServerConnection] = {}
        self.resource_monitor = ResourceMonitor()
        self.cache_ttl = timedelta(minutes=5)
        self.server_requirements = self._load_server_requirements()

        # Initialize Docker client if available
        self.docker_client = None
        if docker:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                self.logger.warning(f"Docker not available: {e}")
        else:
            self.logger.warning("Docker package not installed")

    def _load_server_requirements(self) -> dict[str, ServerRequirements]:
        """Load server resource requirements."""
        return {
            "zen-mcp": ServerRequirements(
                memory=512,
                cpu=0.5,
                ports=[8000],
                dependencies=["python", "poetry"],
            ),
            "context7": ServerRequirements(
                memory=100,
                cpu=0.1,
                ports=[],
                dependencies=["node", "npx"],
            ),
            "perplexity": ServerRequirements(
                memory=50,
                cpu=0.1,
                ports=[],
                dependencies=["node", "npx"],
            ),
            "sentry": ServerRequirements(
                memory=75,
                cpu=0.1,
                ports=[],
                dependencies=["node", "npx"],
            ),
        }

    async def discover_server(self, server_name: str) -> ServerConnection:
        """Smart discovery with anti-duplication."""

        # 1. Check cache first
        if cached := self.get_cached_connection(server_name):
            self.logger.debug(f"Using cached connection for {server_name}")
            return cached

        # 2. Check for existing deployments
        if existing := await self.find_existing_deployment(server_name):
            self.logger.info(f"Found existing {server_name} at {existing.url}")
            self.deployment_cache[server_name] = existing
            return existing

        # 3. Check resource availability
        available_memory = self.resource_monitor.get_available_memory()
        server_requirements = self.server_requirements.get(server_name)

        if server_requirements and available_memory < server_requirements.memory:
            # Try cloud/NPX fallback
            if cloud := await self.try_cloud_deployment(server_name):
                return cloud
            raise ResourceError(f"Insufficient resources for {server_name}")

        # 4. Deploy with lock to prevent races
        lock_path = Path(tempfile.gettempdir()) / f".mcp-{server_name}.lock"
        try:
            with FileLock(lock_path, timeout=30):
                # Double-check after acquiring lock
                if existing := await self.find_existing_deployment(server_name):
                    return existing

                return await self.deploy_server(server_name)
        except Exception as e:
            self.logger.error(f"Failed to deploy {server_name}: {e}")
            raise

    def get_cached_connection(self, server_name: str) -> ServerConnection | None:
        """Get cached connection if still valid."""
        if server_name not in self.deployment_cache:
            return None

        connection = self.deployment_cache[server_name]
        if utc_now() - connection.discovered_at > self.cache_ttl:
            del self.deployment_cache[server_name]
            return None

        # Verify connection is still healthy
        if not self.verify_health(connection):
            del self.deployment_cache[server_name]
            return None

        return connection

    async def find_existing_deployment(self, server_name: str) -> ServerConnection | None:
        """Multi-strategy detection for existing deployments."""
        strategies = [
            self.check_known_ports,
            self.check_process_list,
            self.check_docker_containers,
            self.check_node_modules,
            self.check_lock_files,
            self.check_env_variables,
        ]

        for strategy in strategies:
            try:
                if conn := await strategy(server_name):
                    # Verify it's actually responding
                    if self.verify_health(conn):
                        return conn
            except Exception as e:
                self.logger.debug(f"Strategy {strategy.__name__} failed for {server_name}: {e}")

        return None

    async def check_known_ports(self, server_name: str) -> ServerConnection | None:
        """Check known ports for running servers."""
        port_map = {
            "zen-mcp": [8000, 8001, 8002],  # Common zen-mcp ports
            "context7": [],  # NPX-based, no fixed port
            "perplexity": [],
            "sentry": [],
        }

        ports = port_map.get(server_name, [])
        for port in ports:
            if not self.resource_monitor.is_port_available(port):
                # Port is in use, check if it's our server
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=5)
                    if response.status_code == 200:
                        return ServerConnection(
                            url=f"http://localhost:{port}",
                            type="external",
                            health_status="healthy",
                            resource_usage={"port": port},
                            discovered_at=utc_now(),
                        )
                except Exception:
                    pass
        return None

    async def check_process_list(self, server_name: str) -> ServerConnection | None:
        """Check running processes for server."""
        process_patterns = {
            "zen-mcp": ["zen-mcp-server", "poetry run python -m src.main"],
            "context7": ["@upstash/context7-mcp"],
            "perplexity": ["@jschuller/perplexity-mcp"],
            "sentry": ["@sentry/mcp-server"],
        }

        patterns = process_patterns.get(server_name, [])
        for pattern in patterns:
            if self.resource_monitor.check_process_exists(pattern):
                # Try to determine the URL from process
                url = await self.extract_url_from_process(pattern)
                if url:
                    return ServerConnection(
                        url=url,
                        type="user",
                        health_status="unknown",
                        resource_usage={},
                        discovered_at=utc_now(),
                    )
        return None

    async def check_node_modules(self, server_name: str) -> ServerConnection | None:
        """Check node_modules/.bin/ for installed NPX MCP servers."""
        node_modules_bin = Path("node_modules/.bin")

        if not node_modules_bin.exists():
            self.logger.debug("node_modules/.bin not found, checking package.json")

        # NPX package mappings to their binary names
        npx_package_map = {
            "context7": "@upstash/context7-mcp",
            "perplexity": "@jschuller/perplexity-mcp",
            "sentry": "@sentry/mcp-server",
            "tavily": "tavily-mcp",
        }

        package_name = npx_package_map.get(server_name)
        if not package_name:
            return None

        # Check if the binary exists in node_modules/.bin/ (only if directory exists)
        if node_modules_bin.exists():
            # NPX creates symlinks in .bin/ directory
            possible_bin_names = [
                package_name.split("/")[-1],  # Last part of scoped package
                server_name,
                f"{server_name}-mcp",
                package_name.replace("/", "-").replace("@", ""),
            ]

            for bin_name in possible_bin_names:
                bin_path = node_modules_bin / bin_name
                if bin_path.exists() or (bin_path.with_suffix(".cmd").exists() if os.name == "nt" else False):
                    self.logger.info(f"Found NPX binary for {server_name} at {bin_path}")
                    return ServerConnection(
                        url=f"npx://{package_name}",
                        type="npx",
                        health_status="available",
                        resource_usage={"package": package_name, "binary": str(bin_path)},
                        discovered_at=utc_now(),
                    )

        # Also check if package is listed in package.json dependencies
        package_json = Path("package.json")
        if package_json.exists():
            try:
                with Path(package_json).open() as f:
                    pkg_data = json.load(f)

                # Check both dependencies and devDependencies
                all_deps = {}
                all_deps.update(pkg_data.get("dependencies", {}))
                all_deps.update(pkg_data.get("devDependencies", {}))

                if package_name in all_deps:
                    self.logger.info(f"Found {server_name} package {package_name} in package.json")
                    return ServerConnection(
                        url=f"npx://{package_name}",
                        type="npx",
                        health_status="available",
                        resource_usage={"package": package_name, "version": all_deps[package_name]},
                        discovered_at=utc_now(),
                    )
            except Exception as e:
                self.logger.debug(f"Failed to parse package.json: {e}")

        return None

    async def check_docker_containers(self, server_name: str) -> ServerConnection | None:
        """Check Docker containers for running servers."""
        if not self.docker_client:
            return None

        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                if server_name in container.name or server_name in str(container.image):
                    # Get port mapping
                    ports = container.ports
                    if ports:
                        for port_info in ports.values():
                            if port_info:
                                host_port = port_info[0]["HostPort"]
                                return ServerConnection(
                                    url=f"http://localhost:{host_port}",
                                    type="docker",
                                    health_status="running",
                                    resource_usage={"container_id": container.short_id},
                                    discovered_at=utc_now(),
                                )
        except Exception as e:
            self.logger.debug(f"Docker check failed: {e}")

        return None

    async def check_lock_files(self, server_name: str) -> ServerConnection | None:
        """Check for lock files indicating running servers."""
        lock_patterns = [
            Path(tempfile.gettempdir()) / f".mcp-{server_name}.lock",
            Path(tempfile.gettempdir()) / f".{server_name}.lock",
            Path.home() / f".{server_name}.lock",
        ]

        for lock_path in lock_patterns:
            lock_file = Path(str(lock_path))
            if lock_file.exists():
                try:
                    # Try to read connection info from lock file
                    content = lock_file.read_text()
                    if content.startswith("http"):
                        return ServerConnection(
                            url=content.strip(),
                            type="user",
                            health_status="unknown",
                            resource_usage={},
                            discovered_at=utc_now(),
                        )
                except Exception:
                    pass

        return None

    async def check_env_variables(self, server_name: str) -> ServerConnection | None:
        """Check environment variables for server URLs."""
        env_patterns = {
            "zen-mcp": ["ZEN_MCP_URL", "PROMPTCRAFT_ZEN_MCP_SERVER_URL"],
            "context7": ["CONTEXT7_URL"],
            "perplexity": ["PERPLEXITY_URL"],
            "sentry": ["SENTRY_MCP_URL"],
        }

        patterns = env_patterns.get(server_name, [])
        for pattern in patterns:
            if url := os.getenv(pattern):
                return ServerConnection(
                    url=url,
                    type="external",
                    health_status="unknown",
                    resource_usage={},
                    discovered_at=utc_now(),
                )

        return None

    async def try_cloud_deployment(self, server_name: str) -> ServerConnection | None:
        """Try cloud/NPX deployment for supported servers."""
        cloud_servers = ["context7", "perplexity", "sentry"]

        if server_name not in cloud_servers:
            return None

        try:
            # For NPX servers, we don't need to manage them directly
            # They're started on-demand by Claude Code
            return ServerConnection(
                url="npx://cloud",
                type="npx",
                health_status="on_demand",
                resource_usage={},
                discovered_at=utc_now(),
            )
        except Exception as e:
            self.logger.debug(f"Cloud deployment failed for {server_name}: {e}")

        return None

    async def deploy_server(self, server_name: str) -> ServerConnection:
        """Deploy server using appropriate strategy."""
        deployment_strategies = {
            "zen-mcp": self.deploy_zen_server,
            "context7": self.deploy_npx_server,
            "perplexity": self.deploy_npx_server,
            "sentry": self.deploy_npx_server,
        }

        strategy = deployment_strategies.get(server_name)
        if not strategy:
            raise ValueError(f"No deployment strategy for {server_name}")

        return await strategy(server_name)

    async def deploy_zen_server(self, server_name: str) -> ServerConnection:
        """Deploy zen-mcp-server."""
        # Check if zen-mcp-server is available as submodule or in docker
        zen_paths = [
            Path("vendors/zen-mcp-server"),
            Path("../zen-mcp-server"),
            Path.home() / "dev/zen-mcp-server",
        ]

        for zen_path in zen_paths:
            if zen_path.exists():
                # Try to start the server
                try:
                    port = self.find_available_port(8000, 8010)
                    cmd = ["poetry", "run", "python", "-m", "src.main", "--port", str(port)]
                    process = subprocess.Popen(
                        cmd,
                        cwd=zen_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                    # Wait a bit for startup
                    await asyncio.sleep(3)

                    url = f"http://localhost:{port}"
                    if self.verify_health(ServerConnection(url, "embedded", "starting", {}, utc_now())):
                        # Create lock file
                        lock_file = Path(tempfile.gettempdir()) / f".mcp-{server_name}.lock"
                        lock_file.write_text(url)

                        return ServerConnection(
                            url=url,
                            type="embedded",
                            health_status="healthy",
                            resource_usage={"pid": process.pid, "port": port},
                            discovered_at=utc_now(),
                        )
                except Exception as e:
                    self.logger.error(f"Failed to start zen-mcp-server: {e}")

        raise RuntimeError(f"Could not deploy {server_name}")

    async def deploy_npx_server(self, server_name: str) -> ServerConnection:
        """Deploy NPX-based server (context7, perplexity, sentry)."""
        # These are handled by Claude Code directly, so we just return the NPX connection
        return ServerConnection(
            url="npx://cloud",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )

    def find_available_port(self, start: int, end: int) -> int:
        """Find an available port in the given range."""
        for port in range(start, end):
            if self.resource_monitor.is_port_available(port):
                return port
        raise RuntimeError(f"No available ports in range {start}-{end}")

    def verify_health(self, connection: ServerConnection) -> bool:
        """Verify server is healthy and responding."""
        if connection.type == "npx":
            # NPX servers are always considered healthy as they start on demand
            return True

        try:
            if connection.url.startswith("http"):
                response = requests.get(f"{connection.url}/health", timeout=5)
                return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Health check failed for {connection.url}: {e}")

        return False

    async def extract_url_from_process(self, pattern: str) -> str | None:
        """Extract URL from running process."""
        # This would need more sophisticated process inspection
        # For now, return common defaults
        if "zen-mcp" in pattern:
            return "http://localhost:8000"
        return None


class ResourceError(Exception):
    """Raised when insufficient resources are available."""
