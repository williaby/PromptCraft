"""Comprehensive tests for error handling and fallback mechanisms."""

from datetime import UTC, datetime, timedelta
import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.mcp_integration.zen_client.error_handler import (
    CircuitBreakerState,
    MCPConnectionManager,
    RetryHandler,
)
from src.mcp_integration.zen_client.models import BridgeMetrics, FallbackConfig
from src.utils.datetime_compat import utc_now


class TestCircuitBreakerState:
    """Test CircuitBreakerState enum."""

    def test_circuit_breaker_states(self):
        """Test all circuit breaker states are defined."""
        assert CircuitBreakerState.CLOSED.value == "closed"
        assert CircuitBreakerState.OPEN.value == "open"
        assert CircuitBreakerState.HALF_OPEN.value == "half_open"


class TestMCPConnectionManager:
    """Test MCPConnectionManager functionality."""

    def test_initialization_with_fallback_enabled(self, fallback_config):
        """Test initialization with HTTP fallback enabled."""
        manager = MCPConnectionManager(fallback_config)

        assert manager.fallback_config == fallback_config
        assert manager.circuit_state == CircuitBreakerState.CLOSED
        assert manager.failure_count == 0
        assert manager.last_failure_time is None
        assert manager.next_attempt_time is None
        assert manager.http_client is not None
        assert isinstance(manager.metrics, BridgeMetrics)

    def test_initialization_with_fallback_disabled(self):
        """Test initialization with HTTP fallback disabled."""
        config = FallbackConfig(enabled=False)
        manager = MCPConnectionManager(config)

        assert manager.http_client is None
        assert manager.fallback_config.enabled is False

    @pytest.mark.asyncio
    async def test_with_fallback_mcp_success(self, fallback_config):
        """Test successful MCP operation without fallback."""
        manager = MCPConnectionManager(fallback_config)

        async def mock_mcp_operation():
            return {"result": "mcp success"}

        result, used_mcp = await manager.with_fallback_to_http(mock_mcp_operation, "/test/endpoint", {"test": "data"})

        assert result == {"result": "mcp success"}
        assert used_mcp is True
        assert manager.metrics.mcp_requests == 1
        assert manager.metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_with_fallback_mcp_failure_http_success(self, fallback_config, mock_httpx_client):
        """Test MCP failure with successful HTTP fallback."""
        manager = MCPConnectionManager(fallback_config)

        async def mock_mcp_operation():
            raise Exception("MCP failed")

        result, used_mcp = await manager.with_fallback_to_http(mock_mcp_operation, "/test/endpoint", {"test": "data"})

        assert result["success"] is True
        assert used_mcp is False
        assert manager.metrics.http_fallback_requests == 1
        assert manager.metrics.successful_requests == 1
        assert manager.failure_count == 1

    @pytest.mark.asyncio
    async def test_with_fallback_both_fail(self, fallback_config, mock_httpx_client):
        """Test both MCP and HTTP fallback failing."""
        manager = MCPConnectionManager(fallback_config)

        async def mock_mcp_operation():
            raise Exception("MCP failed")

        # Mock HTTP client to fail
        mock_httpx_client.post.side_effect = httpx.RequestError("HTTP failed")

        with pytest.raises(Exception, match="Both MCP and HTTP failed"):
            await manager.with_fallback_to_http(mock_mcp_operation, "/test/endpoint", {"test": "data"})

        assert manager.metrics.failed_requests == 1

    @pytest.mark.asyncio
    async def test_with_fallback_no_fallback_enabled(self):
        """Test MCP failure with fallback disabled."""
        config = FallbackConfig(enabled=False)
        manager = MCPConnectionManager(config)

        async def mock_mcp_operation():
            raise Exception("MCP failed")

        with pytest.raises(Exception, match="MCP failed"):
            await manager.with_fallback_to_http(mock_mcp_operation, "/test/endpoint", {"test": "data"})

    @pytest.mark.asyncio
    async def test_with_fallback_circuit_breaker_open(self, fallback_config, mock_httpx_client):
        """Test operation with circuit breaker open."""
        manager = MCPConnectionManager(fallback_config)

        # Force circuit breaker open
        manager.circuit_state = CircuitBreakerState.OPEN

        async def mock_mcp_operation():
            return {"result": "should not be called"}

        result, used_mcp = await manager.with_fallback_to_http(mock_mcp_operation, "/test/endpoint", {"test": "data"})

        assert used_mcp is False
        assert manager.metrics.http_fallback_requests == 1

    @pytest.mark.asyncio
    async def test_execute_http_fallback_post_request(self, fallback_config, mock_httpx_client):
        """Test HTTP fallback with POST request."""
        manager = MCPConnectionManager(fallback_config)

        result = await manager._execute_http_fallback("/api/promptcraft/execute/smart", {"prompt": "test"})

        assert result["success"] is True
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_http_fallback_get_request(self, fallback_config, mock_httpx_client):
        """Test HTTP fallback with GET request."""
        manager = MCPConnectionManager(fallback_config)

        result = await manager._execute_http_fallback("/api/promptcraft/models/available", {"user_tier": "premium"})

        assert result["success"] is True
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_http_fallback_no_client(self):
        """Test HTTP fallback without configured client."""
        config = FallbackConfig(enabled=False)
        manager = MCPConnectionManager(config)

        with pytest.raises(Exception, match="HTTP fallback not configured"):
            await manager._execute_http_fallback("/test", {})

    @pytest.mark.asyncio
    async def test_execute_http_fallback_request_error(self, fallback_config, mock_httpx_client):
        """Test HTTP fallback with request error."""
        manager = MCPConnectionManager(fallback_config)

        mock_httpx_client.post.side_effect = httpx.RequestError("Network error")

        with pytest.raises(Exception, match="HTTP request failed"):
            await manager._execute_http_fallback("/test", {})

    @pytest.mark.asyncio
    async def test_execute_http_fallback_http_status_error(self, fallback_config, mock_httpx_client):
        """Test HTTP fallback with HTTP status error."""
        manager = MCPConnectionManager(fallback_config)

        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Server Error",
            request=Mock(),
            response=mock_response,
        )
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(Exception, match="HTTP error 500"):
            await manager._execute_http_fallback("/test", {})

    def test_should_use_fallback_disabled(self):
        """Test fallback decision when fallback is disabled."""
        config = FallbackConfig(enabled=False)
        manager = MCPConnectionManager(config)

        assert manager._should_use_fallback() is False

    def test_should_use_fallback_circuit_closed(self, fallback_config):
        """Test fallback decision with circuit breaker closed."""
        manager = MCPConnectionManager(fallback_config)

        manager.circuit_state = CircuitBreakerState.CLOSED
        assert manager._should_use_fallback() is False

    def test_should_use_fallback_circuit_open(self, fallback_config):
        """Test fallback decision with circuit breaker open."""
        manager = MCPConnectionManager(fallback_config)

        manager.circuit_state = CircuitBreakerState.OPEN
        manager.next_attempt_time = datetime.now(UTC) + timedelta(minutes=1)

        assert manager._should_use_fallback() is True

    def test_should_use_fallback_circuit_half_open(self, fallback_config):
        """Test fallback decision with circuit breaker half-open."""
        manager = MCPConnectionManager(fallback_config)

        manager.circuit_state = CircuitBreakerState.HALF_OPEN

        assert manager._should_use_fallback() is False

    def test_should_use_fallback_circuit_open_ready_to_test(self, fallback_config):
        """Test fallback decision when circuit is ready to test recovery."""
        manager = MCPConnectionManager(fallback_config)

        manager.circuit_state = CircuitBreakerState.OPEN
        manager.next_attempt_time = datetime.now(UTC) - timedelta(seconds=1)

        result = manager._should_use_fallback()

        assert result is False
        assert manager.circuit_state == CircuitBreakerState.HALF_OPEN

    def test_record_success_closed_state(self, fallback_config):
        """Test recording success in closed state."""
        manager = MCPConnectionManager(fallback_config)

        manager._record_success()

        assert manager.metrics.successful_requests == 1

    def test_record_success_half_open_state(self, fallback_config):
        """Test recording success in half-open state (closes circuit)."""
        manager = MCPConnectionManager(fallback_config)

        manager.circuit_state = CircuitBreakerState.HALF_OPEN
        manager.failure_count = 2
        manager.last_failure_time = utc_now()

        manager._record_success()

        assert manager.circuit_state == CircuitBreakerState.CLOSED
        assert manager.failure_count == 0
        assert manager.last_failure_time is None
        assert manager.next_attempt_time is None

    def test_record_failure_below_threshold(self, fallback_config):
        """Test recording failure below circuit breaker threshold."""
        manager = MCPConnectionManager(fallback_config)

        manager._record_failure()

        assert manager.failure_count == 1
        assert manager.last_failure_time is not None
        assert manager.circuit_state == CircuitBreakerState.CLOSED

    def test_record_failure_at_threshold(self, fallback_config):
        """Test recording failure at circuit breaker threshold."""
        manager = MCPConnectionManager(fallback_config)

        # Set failure count just below threshold
        manager.failure_count = fallback_config.circuit_breaker_threshold - 1

        manager._record_failure()

        assert manager.failure_count == fallback_config.circuit_breaker_threshold
        assert manager.circuit_state == CircuitBreakerState.OPEN
        assert manager.next_attempt_time is not None

    @patch("time.time")
    def test_update_metrics(self, mock_time, fallback_config):
        """Test metrics update calculation."""
        mock_time.return_value = 1641547800.0
        manager = MCPConnectionManager(fallback_config)
        manager.metrics.total_requests = 1

        start_time = 1641547799.5  # 0.5 seconds earlier
        manager._update_metrics(start_time, success=True)

        assert manager.metrics.average_latency_ms == 500.0
        assert manager.metrics.last_request_time is not None

    @patch("time.time")
    def test_update_metrics_first_request(self, mock_time, fallback_config):
        """Test metrics update for first request."""
        mock_time.return_value = 1641547800.0
        manager = MCPConnectionManager(fallback_config)

        start_time = 1641547799.8  # 0.2 seconds earlier
        manager._update_metrics(start_time, success=True)

        # Use reasonable tolerance for floating-point latency measurements
        assert abs(manager.metrics.average_latency_ms - 200.0) < 0.1  # 0.1ms tolerance

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, fallback_config):
        """Test health check when system is healthy."""
        manager = MCPConnectionManager(fallback_config)

        # Mock HTTP client health check
        with patch.object(manager.http_client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await manager.health_check()

        assert result.healthy is True
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_health_check_circuit_breaker_open(self, fallback_config):
        """Test health check with circuit breaker open."""
        manager = MCPConnectionManager(fallback_config)
        manager.circuit_state = CircuitBreakerState.OPEN
        manager.failure_count = 5

        result = await manager.health_check()

        assert result.healthy is False
        assert "Circuit breaker open" in result.error

    @pytest.mark.asyncio
    async def test_health_check_http_fallback_unhealthy(self, fallback_config):
        """Test health check with unhealthy HTTP fallback."""
        manager = MCPConnectionManager(fallback_config)

        with patch.object(manager.http_client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            result = await manager.health_check()

        assert "HTTP fallback unhealthy: 500" in result.error

    @pytest.mark.asyncio
    async def test_health_check_http_fallback_unreachable(self, fallback_config):
        """Test health check with unreachable HTTP fallback."""
        manager = MCPConnectionManager(fallback_config)

        with patch.object(manager.http_client, "get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")

            result = await manager.health_check()

        assert "HTTP fallback unreachable" in result.error

    @pytest.mark.asyncio
    async def test_health_check_with_mcp_client(self, fallback_config):
        """Test health check with MCP client provided."""
        manager = MCPConnectionManager(fallback_config)
        mock_client = Mock()

        with patch.object(manager.http_client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await manager.health_check(mock_client)

        assert result.available_tools == ["promptcraft_mcp_bridge"]

    @pytest.mark.asyncio
    async def test_health_check_exception(self, fallback_config):
        """Test health check exception handling."""
        manager = MCPConnectionManager(fallback_config)

        # Force exception during health check by patching the HTTP client's get method
        with patch.object(manager.http_client, "get", side_effect=Exception("Health check error")):
            result = await manager.health_check()

        assert result.healthy is False
        assert "Health check error" in result.error

    def test_get_metrics(self, fallback_config, mock_time):
        """Test getting current metrics."""
        manager = MCPConnectionManager(fallback_config)

        result = manager.get_metrics()

        assert isinstance(result, BridgeMetrics)
        assert result.uptime >= 0

    def test_get_circuit_breaker_status(self, fallback_config):
        """Test getting circuit breaker status."""
        manager = MCPConnectionManager(fallback_config)
        manager.failure_count = 2
        manager.last_failure_time = datetime(2024, 1, 7, 10, 30, 0)

        status = manager.get_circuit_breaker_status()

        assert status["state"] == "closed"
        assert status["failure_count"] == 2
        assert status["last_failure_time"] == "2024-01-07T10:30:00"
        assert status["threshold"] == fallback_config.circuit_breaker_threshold

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker(self, fallback_config):
        """Test manual circuit breaker reset."""
        manager = MCPConnectionManager(fallback_config)

        # Set up failed state
        manager.circuit_state = CircuitBreakerState.OPEN
        manager.failure_count = 5
        manager.last_failure_time = utc_now()
        manager.next_attempt_time = utc_now() + timedelta(minutes=1)

        await manager.reset_circuit_breaker()

        assert manager.circuit_state == CircuitBreakerState.CLOSED
        assert manager.failure_count == 0
        assert manager.last_failure_time is None
        assert manager.next_attempt_time is None

    @pytest.mark.asyncio
    async def test_close_http_client(self, fallback_config):
        """Test closing HTTP client."""
        manager = MCPConnectionManager(fallback_config)

        # Mock the http_client's aclose method
        mock_aclose = AsyncMock()
        manager.http_client.aclose = mock_aclose

        await manager.close()

        mock_aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_http_client(self):
        """Test closing when no HTTP client exists."""
        config = FallbackConfig(enabled=False)
        manager = MCPConnectionManager(config)

        # Should not raise exception
        await manager.close()


class TestRetryHandler:
    """Test RetryHandler functionality."""

    def test_initialization_defaults(self):
        """Test retry handler initialization with defaults."""
        handler = RetryHandler()

        assert handler.max_retries == 3
        assert handler.base_delay == 1.0
        assert handler.max_delay == 10.0

    def test_initialization_custom_values(self):
        """Test retry handler initialization with custom values."""
        handler = RetryHandler(max_retries=5, base_delay=0.5, max_delay=30.0)

        assert handler.max_retries == 5
        assert handler.base_delay == 0.5
        assert handler.max_delay == 30.0

    @pytest.mark.asyncio
    async def test_with_retry_success_first_attempt(self, mock_asyncio_sleep):
        """Test successful operation on first attempt."""
        handler = RetryHandler()

        async def mock_operation():
            return "success"

        result = await handler.with_retry(mock_operation, "test_op")

        assert result == "success"
        mock_asyncio_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_retry_success_after_failures(self, mock_asyncio_sleep):
        """Test successful operation after some failures."""
        handler = RetryHandler()
        call_count = 0

        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return "success"

        result = await handler.with_retry(mock_operation, "test_op")

        assert result == "success"
        assert call_count == 3
        assert mock_asyncio_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_with_retry_all_attempts_fail(self, mock_asyncio_sleep):
        """Test when all retry attempts fail."""
        handler = RetryHandler(max_retries=2)

        async def mock_operation():
            raise Exception("Always fails")

        with pytest.raises(Exception, match="Always fails"):
            await handler.with_retry(mock_operation, "test_op")

        assert mock_asyncio_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_with_retry_exponential_backoff(self, mock_asyncio_sleep):
        """Test exponential backoff delay calculation."""
        handler = RetryHandler(base_delay=1.0, max_delay=10.0)

        async def mock_operation():
            raise Exception("Always fails")

        with pytest.raises(Exception):
            await handler.with_retry(mock_operation, "test_op")

        # Check that delays increase exponentially
        calls = mock_asyncio_sleep.call_args_list
        delays = [call[0][0] for call in calls]

        assert delays[0] == 1.0  # 1.0 * 2^0
        assert delays[1] == 2.0  # 1.0 * 2^1
        assert delays[2] == 4.0  # 1.0 * 2^2

    @pytest.mark.asyncio
    async def test_with_retry_max_delay_cap(self, mock_asyncio_sleep):
        """Test that delay is capped at max_delay."""
        handler = RetryHandler(base_delay=8.0, max_delay=10.0, max_retries=3)

        async def mock_operation():
            raise Exception("Always fails")

        with pytest.raises(Exception):
            await handler.with_retry(mock_operation, "test_op")

        # Check that delay is capped
        calls = mock_asyncio_sleep.call_args_list
        delays = [call[0][0] for call in calls]

        assert delays[0] == 8.0  # 8.0 * 2^0 = 8.0
        assert delays[1] == 10.0  # min(8.0 * 2^1, 10.0) = 10.0
        assert delays[2] == 10.0  # min(8.0 * 2^2, 10.0) = 10.0

    @pytest.mark.asyncio
    async def test_with_retry_operation_name_logging(self, mock_asyncio_sleep):
        """Test that operation name is used in logging."""
        handler = RetryHandler(max_retries=1)

        async def mock_operation():
            raise Exception("Test error")

        with pytest.raises(Exception):
            await handler.with_retry(mock_operation, "custom_operation")

        # The operation name should be used in logging (implicitly tested via no exceptions)

    @pytest.mark.asyncio
    async def test_with_retry_zero_retries(self):
        """Test with zero retries (single attempt only)."""
        handler = RetryHandler(max_retries=0)

        async def mock_operation():
            raise Exception("First attempt fails")

        with pytest.raises(Exception, match="First attempt fails"):
            await handler.with_retry(mock_operation, "test_op")

    @pytest.mark.asyncio
    async def test_with_retry_different_exception_types(self, mock_asyncio_sleep):
        """Test retry behavior with different exception types."""
        handler = RetryHandler(max_retries=2)
        attempt = 0

        async def mock_operation():
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise ValueError("Value error")
            if attempt == 2:
                raise ConnectionError("Connection error")
            return "success"

        result = await handler.with_retry(mock_operation, "test_op")

        assert result == "success"
        assert attempt == 3


class TestErrorHandlerIntegration:
    """Test integration between error handling components."""

    @pytest.mark.asyncio
    async def test_connection_manager_with_retry_handler_integration(self, fallback_config):
        """Test integration between connection manager and retry handler."""
        connection_manager = MCPConnectionManager(fallback_config)
        retry_handler = RetryHandler(max_retries=2)

        # Mock an operation that fails once then succeeds
        call_count = 0

        async def mock_mcp_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Transient failure")
            return {"result": "success"}

        # Use retry handler with connection manager
        async def retry_operation():
            result, used_mcp = await connection_manager.with_fallback_to_http(
                mock_mcp_operation,
                "/test/endpoint",
                {"test": "data"},
            )
            return result

        result = await retry_handler.with_retry(retry_operation, "integrated_test")

        assert result == {"result": "success"}
        assert call_count == 2  # Failed once, succeeded second time

    def test_metrics_tracking_across_operations(self, fallback_config):
        """Test that metrics are properly tracked across multiple operations."""
        manager = MCPConnectionManager(fallback_config)

        # Simulate multiple operations
        for _ in range(5):
            manager._record_success()

        for _ in range(2):
            manager._record_failure()

        # Update some metrics manually for testing
        manager._update_metrics(time.time() - 0.1, success=True)
        manager._update_metrics(time.time() - 0.2, success=False)

        metrics = manager.get_metrics()

        assert metrics.successful_requests == 6
        assert manager.failure_count == 2
        assert metrics.average_latency_ms > 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_transitions(self, fallback_config):
        """Test complete circuit breaker state transition cycle."""
        manager = MCPConnectionManager(fallback_config)

        # Start in CLOSED state
        assert manager.circuit_state == CircuitBreakerState.CLOSED

        # Trigger failures to open circuit
        for _ in range(fallback_config.circuit_breaker_threshold):
            manager._record_failure()

        assert manager.circuit_state == CircuitBreakerState.OPEN

        # Force transition to HALF_OPEN by setting past time
        manager.next_attempt_time = datetime.now(UTC) - timedelta(seconds=1)
        manager._should_use_fallback()

        assert manager.circuit_state == CircuitBreakerState.HALF_OPEN

        # Record success to close circuit
        manager._record_success()

        assert manager.circuit_state == CircuitBreakerState.CLOSED
        assert manager.failure_count == 0
