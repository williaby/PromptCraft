"""Shared fixtures for zen_client tests."""

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.mcp_integration.zen_client.models import (
    BridgeMetrics,
    FallbackConfig,
    MCPConnectionConfig,
    MCPConnectionStatus,
    MCPHealthCheck,
    ModelListRequest,
    RouteAnalysisRequest,
    SmartExecutionRequest,
)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.Popen for testing."""
    mock_process = Mock()
    mock_process.pid = 12345
    mock_process.poll.return_value = None  # Process is running
    mock_process.stdin = Mock()
    mock_process.stdout = Mock()
    mock_process.stderr = Mock()
    mock_process.terminate = Mock()
    mock_process.kill = Mock()

    # Mock stdout.readline for MCP responses
    mock_process.stdout.readline = Mock(
        return_value='{"jsonrpc": "2.0", "id": "test-id", "result": {"content": "test response"}}\n',
    )

    with patch("subprocess.Popen", return_value=mock_process):
        yield mock_process


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for HTTP fallback testing."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock successful responses
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "result": "HTTP fallback response", "processing_time": 0.5}
    mock_response.raise_for_status = Mock()

    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def connection_config():
    """Sample MCP connection configuration."""
    return MCPConnectionConfig(
        server_path="./test_server.py",
        env_vars={"TEST_ENV": "test_value"},
        timeout=30.0,
    )


@pytest.fixture
def fallback_config():
    """Sample fallback configuration."""
    return FallbackConfig(
        enabled=True,
        http_base_url="http://localhost:8000",
        fallback_timeout=10.0,
        circuit_breaker_threshold=3,
        circuit_breaker_reset_time=60,
    )


@pytest.fixture
def sample_route_analysis_request():
    """Sample route analysis request."""
    return RouteAnalysisRequest(
        prompt="Test prompt for analysis",
        user_tier="premium",
        task_type="generation",
    )


@pytest.fixture
def sample_smart_execution_request():
    """Sample smart execution request."""
    return SmartExecutionRequest(
        prompt="Test prompt for execution",
        user_tier="premium",
        channel="stable",
        cost_optimization=True,
        include_reasoning=False,
    )


@pytest.fixture
def sample_model_list_request():
    """Sample model list request."""
    return ModelListRequest(
        user_tier="premium",
        channel="stable",
        include_metadata=True,
        format="ui",
    )


@pytest.fixture
def sample_mcp_response():
    """Sample MCP response data."""
    return {
        "content": [
            {
                "text": 'PromptCraft MCP Bridge Result: {"success": true, "analysis": {"complexity_score": 0.7}, "processing_time": 1.2}',
            },
        ],
    }


@pytest.fixture
def sample_http_response():
    """Sample HTTP API response."""
    return {
        "success": True,
        "analysis": {
            "task_type": "generation",
            "complexity_score": 0.7,
            "complexity_level": "medium",
            "indicators": ["long_prompt", "creative_task"],
            "reasoning": "Complex creative generation task",
        },
        "recommendations": {
            "primary_model": "claude-3-5-sonnet-20241022",
            "alternative_models": ["gpt-4-turbo"],
            "estimated_cost": 0.05,
            "confidence": 0.85,
        },
        "processing_time": 1.2,
    }


@pytest.fixture
def bridge_metrics():
    """Sample bridge metrics."""
    return BridgeMetrics(
        total_requests=100,
        successful_requests=95,
        failed_requests=3,
        mcp_requests=70,
        http_fallback_requests=25,
        average_latency_ms=250.0,
        uptime=3600.0,
    )


@pytest.fixture
def health_check_result():
    """Sample health check result."""
    return MCPHealthCheck(
        healthy=True,
        latency_ms=50.0,
        server_version="1.0.0",
        available_tools=["promptcraft_mcp_bridge"],
    )


@pytest.fixture
def connection_status():
    """Sample connection status."""
    return MCPConnectionStatus(
        connected=True,
        process_id=12345,
        uptime=300.0,
        last_activity="2024-01-07T10:30:00Z",
        error_count=0,
    )


@pytest.fixture
def mock_asyncio_sleep():
    """Mock asyncio.sleep to speed up tests."""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        yield mock_sleep


@pytest.fixture
def mock_time():
    """Mock time.time for consistent timestamps."""
    with patch("time.time", return_value=1641547800.0) as mock_time:
        yield mock_time


@pytest.fixture
def mock_uuid():
    """Mock uuid.uuid4 for consistent request IDs."""
    with patch("uuid.uuid4", return_value=Mock(hex="test-request-id")) as mock_uuid:
        yield mock_uuid


@pytest.fixture
def mock_json_loads():
    """Mock json.loads for controlled parsing."""

    def side_effect(data):
        if "test-id" in data:
            return {"jsonrpc": "2.0", "id": "test-id", "result": {"content": [{"text": "Test response"}]}}
        return json.loads(data)

    with patch("json.loads", side_effect=side_effect) as mock_loads:
        yield mock_loads


@pytest.fixture
def temp_server_file(tmp_path):
    """Create a temporary server file for testing."""
    server_file = tmp_path / "test_server.py"
    server_file.write_text("#!/usr/bin/env python3\nprint('Test server')\n")
    server_file.chmod(0o755)
    return server_file


@pytest.fixture
def mock_event_loop():
    """Mock event loop for testing."""
    loop = Mock()
    loop.run_in_executor = AsyncMock(return_value="test response\n")

    with patch("asyncio.get_event_loop", return_value=loop):
        yield loop


@pytest.fixture
def circuit_breaker_scenarios():
    """Test scenarios for circuit breaker states."""
    return {
        "closed": {
            "failure_count": 0,
            "last_failure_time": None,
            "should_fallback": False,
        },
        "open": {
            "failure_count": 5,
            "last_failure_time": "2024-01-07T10:25:00Z",
            "should_fallback": True,
        },
        "half_open": {
            "failure_count": 3,
            "last_failure_time": "2024-01-07T10:20:00Z",
            "should_fallback": False,
        },
    }


@pytest.fixture
def protocol_bridge_endpoints():
    """Test endpoints for protocol bridge."""
    return [
        "/api/promptcraft/route/analyze",
        "/api/promptcraft/execute/smart",
        "/api/promptcraft/models/available",
    ]


@pytest.fixture
def subprocess_scenarios():
    """Test scenarios for subprocess management."""
    return {
        "healthy": {
            "poll_result": None,
            "stderr_data": "",
            "should_restart": False,
        },
        "crashed": {
            "poll_result": 1,
            "stderr_data": "Process crashed",
            "should_restart": True,
        },
        "unresponsive": {
            "poll_result": None,
            "stderr_data": "Warning: high memory usage",
            "should_restart": False,
        },
    }
