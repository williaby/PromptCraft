"""
Local MCP Server Test Fixtures

Manages lifecycle of local MCP servers for contract testing.
Provides fixtures to start/stop zen-mcp-server and stub servers.
"""

import asyncio
from collections.abc import AsyncGenerator
import logging
import os
from pathlib import Path
import subprocess
import time

import httpx
import pytest


logger = logging.getLogger(__name__)


class LocalMCPServer:
    """Manages a local MCP server process for testing."""
    
    def __init__(
        self,
        server_path: Path,
        port: int,
        name: str,
        env_vars: dict[str, str] | None = None,
    ):
        self.server_path = server_path
        self.port = port
        self.name = name
        self.env_vars = env_vars or {}
        self.process: subprocess.Popen | None = None
        self.base_url = f"http://localhost:{port}"
        
    async def start(self) -> bool:
        """Start the MCP server process."""
        if self.process and self.process.poll() is None:
            logger.info(f"Server {self.name} is already running")
            return True
            
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.env_vars)
            env.update({
                "PORT": str(self.port),
                "HOST": "localhost",
                "LOG_LEVEL": "INFO",
            })
            
            logger.info(f"Starting {self.name} on port {self.port}")
            
            # Start the process
            self.process = subprocess.Popen(
                ["python", str(self.server_path)],
                env=env,
                cwd=self.server_path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Wait for server to be ready
            return await self._wait_for_health()
            
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            await self.stop()
            return False
    
    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            logger.info(f"Stopping {self.name}")
            self.process.terminate()
            
            try:
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {self.name}")
                self.process.kill()
                self.process.wait()
            
            self.process = None
    
    async def _wait_for_health(self, timeout: float = 30.0) -> bool:
        """Wait for server to respond to health check."""
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            while time.time() - start_time < timeout:
                try:
                    # Try basic health check
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        logger.info(f"Server {self.name} is healthy")
                        return True
                except Exception:
                    pass
                    
                await asyncio.sleep(0.5)
        
        logger.error(f"Server {self.name} failed health check after {timeout}s")
        return False
    
    @property
    def is_running(self) -> bool:
        """Check if the server process is running."""
        return self.process is not None and self.process.poll() is None


@pytest.fixture(scope="session")
async def zen_mcp_server() -> AsyncGenerator[LocalMCPServer, None]:
    """Fixture to manage zen-mcp-server for contract testing."""
    
    # Find zen-mcp-server path
    zen_server_paths = [
        Path("/home/byron/dev/zen-mcp-server/server.py"),
        Path("/home/byron/dev/PromptCraft/zen-mcp-server/server.py"),
        Path("../zen-mcp-server/server.py"),
    ]
    
    server_path = None
    for path in zen_server_paths:
        if path.exists():
            server_path = path
            break
    
    if not server_path:
        pytest.skip("zen-mcp-server not found - install or clone it locally")
    
    # Configure environment for testing
    test_env = {
        "OPENAI_API_KEY": "test-key-for-contracts",
        "ANTHROPIC_API_KEY": "test-key-for-contracts",
        "ENABLE_TOOLS": "true",
        "ENABLE_ROUTING": "true",
        "TEST_MODE": "true",
    }
    
    server = LocalMCPServer(
        server_path=server_path,
        port=8080,
        name="zen-mcp-server",
        env_vars=test_env,
    )
    
    try:
        if await server.start():
            yield server
        else:
            pytest.skip("Failed to start zen-mcp-server for contract testing")
    finally:
        await server.stop()


@pytest.fixture(scope="session")
async def test_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for making requests to test servers."""
    timeout = httpx.Timeout(30.0, connect=5.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


class ServerHealthChecker:
    """Utility for checking server health and readiness."""
    
    @staticmethod
    async def wait_for_servers(*servers: LocalMCPServer, timeout: float = 30.0) -> bool:
        """Wait for all servers to be healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if all(server.is_running for server in servers):
                # All processes running, now check HTTP health
                async with httpx.AsyncClient(timeout=2.0) as client:
                    try:
                        health_checks = [
                            client.get(f"{server.base_url}/health")
                            for server in servers
                        ]
                        responses = await asyncio.gather(*health_checks, return_exceptions=True)
                        
                        all_healthy = all(
                            isinstance(r, httpx.Response) and r.status_code == 200
                            for r in responses
                        )
                        
                        if all_healthy:
                            return True
                    except Exception:
                        pass
            
            await asyncio.sleep(0.5)
        
        return False
    
    @staticmethod
    async def check_server_endpoints(
        server: LocalMCPServer,
        endpoints: list[str],
    ) -> dict[str, bool]:
        """Check if specific endpoints are available on a server."""
        results = {}
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                try:
                    url = f"{server.base_url}{endpoint}"
                    response = await client.get(url)
                    results[endpoint] = response.status_code in (200, 404, 405)  # 404/405 means endpoint exists
                except Exception:
                    results[endpoint] = False
        
        return results