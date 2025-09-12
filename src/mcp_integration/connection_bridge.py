"""
MCP Connection Bridge

Integrates Smart Discovery with MCP Protocol Clients to establish actual connections
to discovered MCP servers. Provides connection pooling, lifecycle management, and
protocol bridging between discovery results and MCP client implementations.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import subprocess
from typing import Any

from src.utils.datetime_compat import to_iso, utc_now
from src.utils.logging_mixin import LoggerMixin

from .smart_discovery import ServerConnection, SmartMCPDiscovery
from .zen_client.client import ZenMCPStdioClient
from .zen_client.models import FallbackConfig


logger = logging.getLogger(__name__)


@dataclass
class ActiveConnection:
    """Represents an active MCP connection."""

    server_name: str
    connection: ServerConnection
    client: Any | None = None
    process: subprocess.Popen | None = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_health_check: datetime | None = None
    health_status: str = "connecting"
    error_count: int = 0


class NPXProcessManager(LoggerMixin):
    """Manages NPX MCP server processes."""

    def __init__(self) -> None:
        super().__init__()
        self.processes: dict[str, subprocess.Popen] = {}
        self.process_config = {
            "context7": {"package": "@upstash/context7-mcp", "binary": "context7-mcp"},
            "perplexity": {"package": "@jschuller/perplexity-mcp", "binary": "perplexity-mcp"},
            "sentry": {"package": "@sentry/mcp-server", "binary": "sentry-mcp"},
            "tavily": {"package": "tavily-mcp", "binary": "tavily-mcp"},
        }

    async def spawn_npx_server(self, server_name: str, connection: ServerConnection) -> subprocess.Popen | None:
        """Spawn an NPX MCP server process.

        Args:
            server_name: Name of the server to spawn
            connection: ServerConnection with NPX details

        Returns:
            Process if successful, None otherwise
        """
        if server_name in self.processes:
            process = self.processes[server_name]
            if process.poll() is None:  # Still running
                self.logger.info(f"NPX server {server_name} already running (PID: {process.pid})")
                return process
            # Process died, clean up
            del self.processes[server_name]

        config = self.process_config.get(server_name)
        if not config:
            self.logger.error(f"No NPX configuration for server: {server_name}")
            return None

        try:
            # Extract package name from connection URL
            if connection.url.startswith("npx://"):
                package_name = connection.url[6:]  # Remove "npx://" prefix
            else:
                package_name = config["package"]

            # Start NPX process with stdio transport
            cmd = ["npx", package_name]

            self.logger.info(f"Starting NPX server: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
            )

            # Wait a moment for startup
            await asyncio.sleep(2)

            # Check if process started successfully
            if process.poll() is not None:
                stderr_output = process.stderr.read() if process.stderr else ""
                self.logger.error(f"NPX server {server_name} failed to start: {stderr_output}")
                return None

            self.processes[server_name] = process
            self.logger.info(f"NPX server {server_name} started successfully (PID: {process.pid})")
            return process

        except Exception as e:
            self.logger.error(f"Failed to spawn NPX server {server_name}: {e}")
            return None

    def stop_npx_server(self, server_name: str) -> bool:
        """Stop an NPX server process.

        Args:
            server_name: Name of the server to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        if server_name not in self.processes:
            return False

        process = self.processes[server_name]
        try:
            process.terminate()
            # Give it a moment to terminate gracefully
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                process.wait()

            del self.processes[server_name]
            self.logger.info(f"NPX server {server_name} stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop NPX server {server_name}: {e}")
            return False

    def get_process_status(self, server_name: str) -> dict[str, Any]:
        """Get status of an NPX process.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary with process status information
        """
        if server_name not in self.processes:
            return {"status": "not_running", "pid": None}

        process = self.processes[server_name]
        poll_result = process.poll()

        if poll_result is None:
            return {"status": "running", "pid": process.pid}
        # Process died, clean up
        del self.processes[server_name]
        return {"status": "terminated", "pid": None, "return_code": poll_result}


class MCPConnectionBridge(LoggerMixin):
    """Bridge between Smart Discovery and MCP Protocol Clients."""

    def __init__(self, discovery: SmartMCPDiscovery | None = None) -> None:
        super().__init__()
        self.discovery = discovery or SmartMCPDiscovery()
        self.npx_manager = NPXProcessManager()
        self.active_connections: dict[str, ActiveConnection] = {}
        self.connection_pool_size = 10
        self.health_check_interval = timedelta(minutes=5)

    async def connect_to_server(self, server_name: str) -> ActiveConnection | None:
        """Discover and establish connection to an MCP server.

        Args:
            server_name: Name of the server to connect to

        Returns:
            ActiveConnection if successful, None otherwise
        """
        # Check if we already have a healthy connection
        if server_name in self.active_connections:
            active_conn = self.active_connections[server_name]
            if await self._is_connection_healthy(active_conn):
                self.logger.debug(f"Reusing existing connection to {server_name}")
                return active_conn
            # Connection unhealthy, remove it
            await self._cleanup_connection(server_name)

        try:
            # Discover server
            self.logger.info(f"Discovering MCP server: {server_name}")
            connection = await self.discovery.discover_server(server_name)

            if not connection:
                self.logger.error(f"Failed to discover server: {server_name}")
                return None

            self.logger.info(f"Discovered {server_name}: {connection.url} ({connection.type})")

            # Create active connection
            active_conn = ActiveConnection(
                server_name=server_name,
                connection=connection,
            )

            # Establish protocol connection based on type
            if connection.type == "npx":
                success = await self._connect_npx_server(active_conn)
            elif connection.type == "embedded":
                success = await self._connect_embedded_server(active_conn)
            elif connection.type == "external":
                success = await self._connect_external_server(active_conn)
            elif connection.type == "docker":
                success = await self._connect_docker_server(active_conn)
            else:
                self.logger.error(f"Unknown connection type: {connection.type}")
                return None

            if success:
                self.active_connections[server_name] = active_conn
                self.logger.info(f"Successfully connected to {server_name}")
                return active_conn
            self.logger.error(f"Failed to establish protocol connection to {server_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error connecting to server {server_name}: {e}")
            return None

    async def _connect_npx_server(self, active_conn: ActiveConnection) -> bool:
        """Establish connection to NPX-based MCP server.

        Args:
            active_conn: ActiveConnection to NPX server

        Returns:
            True if connection established successfully
        """
        try:
            # Spawn NPX process
            process = await self.npx_manager.spawn_npx_server(
                active_conn.server_name,
                active_conn.connection,
            )

            if not process:
                return False

            active_conn.process = process

            # Create MCP stdio client for the process
            # The zen client expects a server path, but for NPX we use the process directly
            client = ZenMCPStdioClient(
                server_path="npx",  # Placeholder since we manage the process
                env_vars={},
                fallback_config=FallbackConfig(
                    enabled=True,
                    http_base_url="http://localhost:8000",  # Fallback to default
                    fallback_timeout=30.0,
                ),
            )

            # Override the client's process with our NPX process
            client.current_process = process  # type: ignore[assignment]
            active_conn.client = client
            active_conn.health_status = "connected"

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to NPX server {active_conn.server_name}: {e}")
            return False

    async def _connect_embedded_server(self, active_conn: ActiveConnection) -> bool:
        """Establish connection to embedded MCP server (like zen-mcp).

        Args:
            active_conn: ActiveConnection to embedded server

        Returns:
            True if connection established successfully
        """
        try:
            # For embedded servers, the URL should be an HTTP endpoint
            if not active_conn.connection.url.startswith("http"):
                self.logger.error(f"Invalid embedded server URL: {active_conn.connection.url}")
                return False

            # Create HTTP client for embedded server
            # Note: This could be enhanced to use actual MCP protocol over HTTP
            active_conn.client = {
                "type": "http",
                "url": active_conn.connection.url,
                "connection": active_conn.connection,
            }
            active_conn.health_status = "connected"

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to embedded server {active_conn.server_name}: {e}")
            return False

    async def _connect_external_server(self, active_conn: ActiveConnection) -> bool:
        """Establish connection to external MCP server.

        Args:
            active_conn: ActiveConnection to external server

        Returns:
            True if connection established successfully
        """
        try:
            # Similar to embedded, but may have different authentication/config
            active_conn.client = {
                "type": "external",
                "url": active_conn.connection.url,
                "connection": active_conn.connection,
            }
            active_conn.health_status = "connected"

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to external server {active_conn.server_name}: {e}")
            return False

    async def _connect_docker_server(self, active_conn: ActiveConnection) -> bool:
        """Establish connection to Docker-based MCP server.

        Args:
            active_conn: ActiveConnection to Docker server

        Returns:
            True if connection established successfully
        """
        try:
            # Docker servers should expose HTTP endpoints
            active_conn.client = {
                "type": "docker",
                "url": active_conn.connection.url,
                "connection": active_conn.connection,
            }
            active_conn.health_status = "connected"

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Docker server {active_conn.server_name}: {e}")
            return False

    async def _is_connection_healthy(self, active_conn: ActiveConnection) -> bool:
        """Check if a connection is healthy.

        Args:
            active_conn: ActiveConnection to check

        Returns:
            True if connection is healthy
        """
        # Skip health check if done recently
        if active_conn.last_health_check and utc_now() - active_conn.last_health_check < self.health_check_interval:
            return active_conn.health_status == "connected"

        try:
            # Check based on connection type
            if active_conn.connection.type == "npx":
                # Check if NPX process is still running
                if active_conn.process:
                    if active_conn.process.poll() is None:  # Still running
                        healthy = True
                    else:
                        self.logger.warning(f"NPX process for {active_conn.server_name} has died")
                        healthy = False
                else:
                    healthy = False
            else:
                # For HTTP-based servers, could do actual HTTP health check
                # For now, assume healthy if connection exists
                healthy = active_conn.client is not None

            active_conn.last_health_check = utc_now()
            active_conn.health_status = "connected" if healthy else "unhealthy"

            if not healthy:
                active_conn.error_count += 1
            else:
                active_conn.error_count = 0

            return healthy

        except Exception as e:
            self.logger.error(f"Health check failed for {active_conn.server_name}: {e}")
            active_conn.health_status = "unhealthy"
            active_conn.error_count += 1
            return False

    async def _cleanup_connection(self, server_name: str) -> None:
        """Clean up a connection and its resources.

        Args:
            server_name: Name of the server to clean up
        """
        if server_name not in self.active_connections:
            return

        active_conn = self.active_connections[server_name]

        try:
            # Stop NPX process if it exists
            if active_conn.connection.type == "npx" and active_conn.process:
                self.npx_manager.stop_npx_server(server_name)

            # Close client connections
            if hasattr(active_conn.client, "close"):
                await active_conn.client.close()  # type: ignore[misc]
            elif hasattr(active_conn.client, "disconnect"):
                await active_conn.client.disconnect()  # type: ignore[misc]

        except Exception as e:
            self.logger.error(f"Error during cleanup of {server_name}: {e}")
        finally:
            del self.active_connections[server_name]
            self.logger.info(f"Cleaned up connection to {server_name}")

    async def disconnect_server(self, server_name: str) -> bool:
        """Disconnect from an MCP server and clean up resources.

        Args:
            server_name: Name of the server to disconnect from

        Returns:
            True if disconnected successfully
        """
        if server_name not in self.active_connections:
            self.logger.warning(f"No active connection to {server_name}")
            return False

        try:
            await self._cleanup_connection(server_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to disconnect from {server_name}: {e}")
            return False

    async def get_connection_status(self) -> dict[str, Any]:
        """Get status of all active connections.

        Returns:
            Dictionary with connection status information
        """
        status: dict[str, Any] = {
            "total_connections": len(self.active_connections),
            "connections": {},
            "npx_processes": {},
        }

        for server_name, active_conn in self.active_connections.items():
            is_healthy = await self._is_connection_healthy(active_conn)

            status["connections"][server_name] = {
                "type": active_conn.connection.type,
                "url": active_conn.connection.url,
                "health_status": active_conn.health_status,
                "connected_at": active_conn.connected_at.isoformat(),
                "error_count": active_conn.error_count,
                "healthy": is_healthy,
            }

            # Add NPX process info if applicable
            if active_conn.connection.type == "npx":
                status["npx_processes"][server_name] = self.npx_manager.get_process_status(server_name)

        return status

    async def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check of the connection bridge.

        Returns:
            Dictionary with health check results
        """
        try:
            status = await self.get_connection_status()

            healthy_connections = sum(1 for conn_info in status["connections"].values() if conn_info["healthy"])

            overall_healthy = len(self.active_connections) > 0 and healthy_connections == len(self.active_connections)

            return {
                "healthy": overall_healthy,
                "total_connections": status["total_connections"],
                "healthy_connections": healthy_connections,
                "discovery_available": self.discovery is not None,
                "npx_manager_available": self.npx_manager is not None,
                "connections": status["connections"],
                "timestamp": to_iso(utc_now()),
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": to_iso(utc_now()),
            }

    async def shutdown(self) -> None:
        """Shutdown the connection bridge and clean up all resources."""
        self.logger.info("Shutting down MCP Connection Bridge...")

        # Disconnect all active connections
        server_names = list(self.active_connections.keys())
        for server_name in server_names:
            await self.disconnect_server(server_name)

        self.logger.info("MCP Connection Bridge shutdown complete")
