"""
Contract Test Configuration and Fixtures

Provides pytest fixtures for managing local MCP servers and Pact
contract testing infrastructure.
"""

import asyncio
from collections.abc import AsyncGenerator
import logging
import os
from pathlib import Path
import sys
from typing import Any

import httpx
import pytest
import uvicorn


# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import contextlib

from tests.contract.pact_config import get_contract_test_env, pact_config, pact_settings
from tests.fixtures.heimdall_stub import HeimdallStubServer
from tests.fixtures.local_mcp_servers import LocalMCPServer, ServerHealthChecker


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
async def contract_test_environment() -> dict[str, str]:
    """Set up environment variables for contract testing."""
    env_vars = get_contract_test_env()

    # Apply environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    logger.info("Contract test environment configured")
    return env_vars


@pytest.fixture(scope="session")
async def zen_mcp_server(contract_test_environment) -> AsyncGenerator[LocalMCPServer, None]:
    """Start zen-mcp-server for contract testing."""

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

    # Environment for zen server
    test_env = {
        "OPENAI_API_KEY": "test-contract-key",
        "ANTHROPIC_API_KEY": "test-contract-key",
        "ENABLE_TOOLS": "true",
        "ENABLE_ROUTING": "true",
        "TEST_MODE": "true",
        "PORT": "8080",
        "HOST": "localhost",
    }

    server = LocalMCPServer(
        server_path=server_path,
        port=8080,
        name="zen-mcp-server",
        env_vars=test_env,
    )

    try:
        logger.info("Starting zen-mcp-server for contract tests...")
        success = await server.start()

        if not success:
            pytest.skip("Failed to start zen-mcp-server for contract testing")

        # Verify server is responding
        await asyncio.sleep(2.0)  # Give server time to fully initialize

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get("http://localhost:8080/health")
                if response.status_code != 200:
                    pytest.skip(f"zen-mcp-server health check failed: {response.status_code}")
            except Exception as e:
                pytest.skip(f"zen-mcp-server not responding: {e}")

        logger.info("zen-mcp-server is ready for contract testing")
        yield server

    finally:
        logger.info("Stopping zen-mcp-server...")
        await server.stop()


@pytest.fixture(scope="session")
async def heimdall_stub_server(contract_test_environment) -> AsyncGenerator[tuple, None]:
    """Start Heimdall stub server for contract testing."""

    try:
        logger.info("Starting Heimdall stub server for contract tests...")

        # Start the stub server
        server = HeimdallStubServer(port=8081, host="localhost")

        # Configure uvicorn server
        config = uvicorn.Config(
            server.app,
            host="localhost",
            port=8081,
            log_level="error",  # Reduce noise
            access_log=False,
        )

        server_instance = uvicorn.Server(config)

        # Start server in background task
        task = asyncio.create_task(server_instance.serve())

        # Wait for server to start
        await asyncio.sleep(1.5)

        # Verify server is responding
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get("http://localhost:8081/health")
                if response.status_code != 200:
                    pytest.skip(f"Heimdall stub health check failed: {response.status_code}")
            except Exception as e:
                pytest.skip(f"Heimdall stub not responding: {e}")

        logger.info("Heimdall stub server is ready for contract testing")
        yield server, task

    finally:
        logger.info("Stopping Heimdall stub server...")
        if "task" in locals():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


@pytest.fixture(scope="session")
async def all_test_servers(
    zen_mcp_server: LocalMCPServer,
    heimdall_stub_server: tuple,
) -> dict[str, Any]:
    """Fixture providing all test servers ready for contract testing."""

    stub_server, stub_task = heimdall_stub_server

    # Final health check for all servers
    servers_ready = await ServerHealthChecker.wait_for_servers(
        zen_mcp_server,
        timeout=15.0,
    )

    if not servers_ready:
        pytest.skip("Test servers failed final health check")

    # Check that stub server is also ready
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get("http://localhost:8081/health")
            if response.status_code != 200:
                pytest.skip("Heimdall stub failed final health check")
        except Exception:
            pytest.skip("Heimdall stub not accessible")

    logger.info("All test servers are ready for contract testing")

    return {
        "zen_server": zen_mcp_server,
        "heimdall_stub": stub_server,
        "zen_base_url": "http://localhost:8080",
        "heimdall_base_url": "http://localhost:8081",
    }


@pytest.fixture
async def contract_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client configured for contract testing."""
    timeout = httpx.Timeout(30.0, connect=5.0, read=15.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture(scope="session")
def pact_configuration():
    """Provide Pact configuration to tests."""
    return pact_config


@pytest.fixture(scope="session")
def pact_test_settings():
    """Provide Pact test settings to tests."""
    return pact_settings


def pytest_configure(config):
    """Configure pytest with contract test markers."""
    config.addinivalue_line(
        "markers",
        "contract: mark test as a contract test",
    )
    config.addinivalue_line(
        "markers",
        "pact_consumer: mark test as a Pact consumer test",
    )
    config.addinivalue_line(
        "markers",
        "pact_provider: mark test as a Pact provider verification test",
    )
    config.addinivalue_line(
        "markers",
        "requires_servers: mark test as requiring local test servers",
    )


def pytest_collection_modifyitems(config, items):
    """Add markers automatically based on test location."""
    for item in items:
        # Add contract marker to all tests in contract directory
        if "test_contract" in item.nodeid or "/contract/" in item.nodeid:
            item.add_marker(pytest.mark.contract)

        # Add requires_servers marker to tests that use server fixtures
        if any(
            fixture in item.fixturenames for fixture in ["zen_mcp_server", "heimdall_stub_server", "all_test_servers"]
        ):
            item.add_marker(pytest.mark.requires_servers)
