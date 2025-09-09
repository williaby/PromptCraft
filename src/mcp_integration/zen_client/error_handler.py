"""
Error Handling and Fallback for PromptCraft MCP Client

Provides comprehensive error handling, HTTP fallback, and circuit breaker patterns
to ensure reliable operation even when MCP connections fail.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any

import httpx

from .models import BridgeMetrics, FallbackConfig, MCPHealthCheck


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states for fallback management."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, using fallback
    HALF_OPEN = "half_open"  # Testing if service recovered


class MCPConnectionManager:
    """
    Connection manager with error handling, fallback, and circuit breaker patterns.

    Features:
    - Automatic HTTP fallback on MCP failures
    - Circuit breaker pattern to prevent cascading failures
    - Retry logic with exponential backoff
    - Health monitoring and auto-recovery
    - Metrics collection for performance monitoring
    """

    def __init__(self, fallback_config: FallbackConfig) -> None:
        self.fallback_config = fallback_config

        # Circuit breaker state
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.next_attempt_time: datetime | None = None

        # Metrics tracking
        self.metrics = BridgeMetrics()
        self.start_time = time.time()

        # HTTP client for fallback
        self.http_client: httpx.AsyncClient | None = None
        if self.fallback_config.enabled:
            self.http_client = httpx.AsyncClient(
                timeout=self.fallback_config.fallback_timeout,
                base_url=self.fallback_config.http_base_url,
            )

    async def with_fallback_to_http(
        self,
        mcp_operation: Callable[[], Any],
        endpoint: str,
        request_data: dict[str, Any],
    ) -> tuple[Any, bool]:
        """
        Execute MCP operation with automatic HTTP fallback.

        Args:
            mcp_operation: Async function that performs MCP operation
            endpoint: HTTP endpoint for fallback
            request_data: Request data for fallback

        Returns:
            Tuple[Any, bool]: (result, used_mcp)
        """
        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Check circuit breaker state
            if self._should_use_fallback():
                logger.info("Circuit breaker open, using HTTP fallback directly")
                result = await self._execute_http_fallback(endpoint, request_data)
                self.metrics.http_fallback_requests += 1
                self._update_metrics(start_time, success=True)
                return result, False

            # Try MCP operation
            try:
                logger.debug("Attempting MCP operation...")
                result = await mcp_operation()

                # MCP success - reset circuit breaker
                self._record_success()
                self.metrics.mcp_requests += 1
                self._update_metrics(start_time, success=True, skip_success_count=True)
                logger.debug("✅ MCP operation successful")
                return result, True

            except Exception as mcp_error:
                logger.warning(f"MCP operation failed: {mcp_error}")
                self._record_failure()

                # Try HTTP fallback if enabled
                if self.fallback_config.enabled:
                    logger.info("Falling back to HTTP API...")
                    try:
                        result = await self._execute_http_fallback(endpoint, request_data)
                        self.metrics.http_fallback_requests += 1
                        self._update_metrics(start_time, success=True)
                        logger.info("✅ HTTP fallback successful")
                        return result, False

                    except Exception as http_error:
                        logger.error(f"HTTP fallback also failed: {http_error}")
                        self.metrics.failed_requests += 1
                        self._update_metrics(start_time, success=False)
                        raise Exception(f"Both MCP and HTTP failed: MCP={mcp_error}, HTTP={http_error}")
                else:
                    # No fallback enabled, re-raise MCP error
                    self.metrics.failed_requests += 1
                    self._update_metrics(start_time, success=False)
                    raise mcp_error

        except Exception as e:
            # Don't double-count failures that were already counted in inner exception handlers
            # The inner handlers already increment failed_requests, so we just update timing metrics
            self._update_metrics(start_time, success=False)
            logger.error(f"Operation failed completely: {e}")
            raise

    async def _execute_http_fallback(self, endpoint: str, request_data: dict[str, Any]) -> dict[str, Any]:
        """Execute HTTP fallback request."""
        if not self.http_client:
            raise Exception("HTTP fallback not configured")

        try:
            # Determine HTTP method and prepare request
            if endpoint.endswith("/models/available"):
                # GET request for model listing
                response = await self.http_client.get(
                    endpoint,
                    params=request_data,
                )
            else:
                # POST request for analysis and execution
                response = await self.http_client.post(
                    endpoint,
                    json=request_data,
                )

            response.raise_for_status()
            result = response.json()
            return result if isinstance(result, dict) else {"content": str(result)}

        except httpx.RequestError as e:
            raise Exception(f"HTTP request failed: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")

    def _should_use_fallback(self) -> bool:
        """Check if we should use HTTP fallback based on circuit breaker state."""
        if not self.fallback_config.enabled:
            return False

        now = datetime.now(UTC)

        if self.circuit_state == CircuitBreakerState.OPEN:
            # Check if it's time to test recovery
            if self.next_attempt_time and now >= self.next_attempt_time:
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker moving to half-open state")
                return False
            return True

        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # In half-open state, try MCP but be ready to fallback quickly
            return False

        # CLOSED
        return False

    def _record_success(self) -> None:
        """Record successful operation for circuit breaker."""
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Success in half-open state - close the circuit
            self.circuit_state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.next_attempt_time = None
            logger.info("✅ Circuit breaker closed - MCP service recovered")

        # Always update successful requests counter when recording success
        self.metrics.successful_requests += 1

    def _record_failure(self) -> None:
        """Record failed operation for circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        # Open circuit if threshold reached
        if self.failure_count >= self.fallback_config.circuit_breaker_threshold:
            self.circuit_state = CircuitBreakerState.OPEN
            self.next_attempt_time = datetime.now(UTC) + timedelta(
                seconds=self.fallback_config.circuit_breaker_reset_time,
            )
            logger.warning(
                f"🔴 Circuit breaker opened - {self.failure_count} failures, "
                f"will retry at {self.next_attempt_time}",
            )

    def _update_metrics(self, start_time: float, success: bool, skip_success_count: bool = False) -> None:
        """Update performance metrics."""
        latency_ms = (time.time() - start_time) * 1000

        # Update average latency using running average
        if self.metrics.total_requests > 0:
            self.metrics.average_latency_ms = (
                self.metrics.average_latency_ms * (self.metrics.total_requests - 1) + latency_ms
            ) / self.metrics.total_requests
        else:
            self.metrics.average_latency_ms = latency_ms

        # Update success/failure counters
        if success and not skip_success_count:
            self.metrics.successful_requests += 1

        self.metrics.last_request_time = datetime.now(UTC)
        self.metrics.uptime = time.time() - self.start_time

    async def health_check(self, mcp_client: Any | None = None) -> MCPHealthCheck:
        """
        Perform comprehensive health check.

        Args:
            mcp_client: Optional MCP client for testing

        Returns:
            MCPHealthCheck: Health check result
        """
        try:
            health_start = time.time()

            # Basic health indicators
            is_healthy = True
            error_messages = []

            # Check circuit breaker state
            if self.circuit_state == CircuitBreakerState.OPEN:
                is_healthy = False
                error_messages.append(f"Circuit breaker open due to {self.failure_count} failures")

            # Check HTTP fallback if enabled
            if self.fallback_config.enabled and self.http_client:
                try:
                    health_response = await self.http_client.get("/health", timeout=5.0)
                    if health_response.status_code != 200:
                        is_healthy = False
                        error_messages.append(f"HTTP fallback unhealthy: {health_response.status_code}")
                except Exception as e:
                    is_healthy = False
                    error_messages.append(f"HTTP fallback unreachable: {e}")

            # Test MCP client if provided and circuit is not open
            available_tools = None
            if mcp_client and self.circuit_state != CircuitBreakerState.OPEN:
                try:
                    # This would be implemented based on actual MCP client interface
                    available_tools = ["promptcraft_mcp_bridge"]  # Placeholder
                except Exception as e:
                    is_healthy = False
                    error_messages.append(f"MCP client unhealthy: {e}")

            # Calculate latency
            latency_ms = (time.time() - health_start) * 1000

            return MCPHealthCheck(
                healthy=is_healthy,
                latency_ms=latency_ms,
                server_version="1.0.0",  # Would be retrieved from actual server
                available_tools=available_tools,
                error="; ".join(error_messages) if error_messages else None,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return MCPHealthCheck(
                healthy=False,
                error=str(e),
            )

    def get_metrics(self) -> BridgeMetrics:
        """Get current performance metrics."""
        # Update uptime
        self.metrics.uptime = time.time() - self.start_time
        return self.metrics

    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """Get circuit breaker status information."""
        return {
            "state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "next_attempt_time": self.next_attempt_time.isoformat() if self.next_attempt_time else None,
            "threshold": self.fallback_config.circuit_breaker_threshold,
            "reset_time_seconds": self.fallback_config.circuit_breaker_reset_time,
        }

    async def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        logger.info("🔄 Circuit breaker manually reset to closed state")

    async def close(self) -> None:
        """Clean up resources."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed")


class RetryHandler:
    """
    Retry handler with exponential backoff for transient failures.
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def with_retry(self, operation: Callable[[], Any], operation_name: str = "operation") -> Any:
        """
        Execute operation with exponential backoff retry.

        Args:
            operation: Async function to execute
            operation_name: Name for logging

        Returns:
            Operation result
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await operation()
                if attempt > 0:
                    logger.info(f"✅ {operation_name} succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e

                if attempt >= self.max_retries:
                    logger.error(f"❌ {operation_name} failed after {attempt + 1} attempts: {e}")
                    break

                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2**attempt), self.max_delay)
                logger.warning(
                    f"⚠️ {operation_name} failed on attempt {attempt + 1}: {e}, retrying in {delay:.1f}s...",
                )
                await asyncio.sleep(delay)

        # All retries failed
        if last_exception:
            raise last_exception
        raise Exception("All retries failed with no exception recorded")
