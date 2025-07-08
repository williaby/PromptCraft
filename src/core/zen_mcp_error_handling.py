"""Zen MCP error handling and resilience system for C.R.E.A.T.E. framework.

This module provides comprehensive error handling for Zen MCP integration,
including circuit breaker pattern, exponential backoff, and graceful degradation.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZenMCPError(Exception):
    """Base exception for Zen MCP errors."""


class ZenMCPConnectionError(ZenMCPError):
    """Exception raised for connection errors."""


class ZenMCPTimeoutError(ZenMCPError):
    """Exception raised for timeout errors."""


class ZenMCPRateLimitError(ZenMCPError):
    """Exception raised for rate limit errors."""


class CircuitBreakerState(Enum):
    """Circuit breaker states for Zen MCP failure handling."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests due to failures
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open


class CircuitBreaker:
    """Circuit breaker implementation for Zen MCP failure handling."""

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration.
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.logger = logger

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute.
            *args: Function arguments.
            **kwargs: Function keyword arguments.

        Returns:
            Function result.

        Raises:
            ZenMCPError: If circuit breaker is open or function fails.
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise ZenMCPError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise ZenMCPError(f"Function call failed: {e}") from e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset.

        Returns:
            True if should attempt reset, False otherwise.
        """
        return (
            time.time() - self.last_failure_time
        ) > self.config.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful function execution."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.info("Circuit breaker entering CLOSED state")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed function execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning("Circuit breaker entering OPEN state from HALF_OPEN")
        elif (
            self.state == CircuitBreakerState.CLOSED
            and self.failure_count >= self.config.failure_threshold
        ):
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(
                "Circuit breaker entering OPEN state after %d failures",
                self.failure_count,
            )


@dataclass
class RetryConfig:
    """Configuration for retry policy."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryPolicy:
    """Exponential backoff retry policy for Zen MCP operations."""

    def __init__(self, config: RetryConfig | None = None):
        """Initialize retry policy.

        Args:
            config: Retry configuration.
        """
        self.config = config or RetryConfig()
        self.logger = logger

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry policy.

        Args:
            func: Function to execute.
            *args: Function arguments.
            **kwargs: Function keyword arguments.

        Returns:
            Function result.

        Raises:
            ZenMCPError: If all retries fail.
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.config.max_retries:
                    break

                delay = self._calculate_delay(attempt)
                self.logger.warning(
                    "Retry attempt %d failed, retrying in %.2f seconds: %s",
                    attempt + 1,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)

        raise ZenMCPError(f"All retry attempts failed: {last_exception}") from last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt.

        Args:
            attempt: Retry attempt number (0-based).

        Returns:
            Delay in seconds.
        """
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            import random
            delay *= random.uniform(0.5, 1.5)

        return delay


class ZenMCPErrorHandler:
    """Comprehensive error handler for Zen MCP integration."""

    def __init__(
        self,
        circuit_breaker: CircuitBreaker | None = None,
        retry_policy: RetryPolicy | None = None,
    ):
        """Initialize error handler.

        Args:
            circuit_breaker: Circuit breaker instance.
            retry_policy: Retry policy instance.
        """
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.retry_policy = retry_policy or RetryPolicy()
        self.logger = logger

    async def execute_with_protection(
        self,
        func: Callable,
        fallback_func: Callable | None = None,
        *args,
        **kwargs,
    ) -> Any:
        """Execute function with comprehensive error protection.

        Args:
            func: Primary function to execute.
            fallback_func: Fallback function if primary fails.
            *args: Function arguments.
            **kwargs: Function keyword arguments.

        Returns:
            Function result.

        Raises:
            ZenMCPError: If both primary and fallback fail.
        """
        try:
            # Try primary function with circuit breaker and retry
            return await self.circuit_breaker.call(
                self.retry_policy.execute, func, *args, **kwargs
            )
        except ZenMCPError as e:
            self.logger.error("Primary function failed: %s", e)

            if fallback_func:
                try:
                    self.logger.info("Attempting fallback function")
                    return await fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    self.logger.error("Fallback function failed: %s", fallback_error)
                    raise ZenMCPError(
                        f"Both primary and fallback functions failed: {e}"
                    ) from fallback_error

            raise


# Mock Zen MCP client for testing and development
class MockZenMCPClient:
    """Mock Zen MCP client for testing error handling."""

    def __init__(self, failure_rate: float = 0.0):
        """Initialize mock client.

        Args:
            failure_rate: Probability of failure (0.0 to 1.0).
        """
        self.failure_rate = failure_rate
        self.call_count = 0

    async def process_prompt(self, prompt: str) -> dict[str, Any]:
        """Mock prompt processing.

        Args:
            prompt: Input prompt.

        Returns:
            Mock response.

        Raises:
            ZenMCPConnectionError: If simulated failure occurs.
        """
        self.call_count += 1
        
        import random
        if random.random() < self.failure_rate:
            raise ZenMCPConnectionError(f"Simulated failure on call {self.call_count}")

        return {
            "enhanced_prompt": f"Enhanced: {prompt}",
            "metadata": {"call_count": self.call_count},
        }


class ZenMCPIntegration:
    """Integration layer for Zen MCP with error handling."""

    def __init__(
        self,
        client: Any | None = None,
        error_handler: ZenMCPErrorHandler | None = None,
    ):
        """Initialize Zen MCP integration.

        Args:
            client: Zen MCP client instance.
            error_handler: Error handler instance.
        """
        self.client = client or MockZenMCPClient()
        self.error_handler = error_handler or ZenMCPErrorHandler()
        self.logger = logger

    async def enhance_prompt(self, prompt: str) -> dict[str, Any]:
        """Enhance prompt using Zen MCP with error handling.

        Args:
            prompt: Input prompt to enhance.

        Returns:
            Enhanced prompt response.

        Raises:
            ZenMCPError: If enhancement fails.
        """
        async def primary_func() -> dict[str, Any]:
            return await self.client.process_prompt(prompt)

        async def fallback_func() -> dict[str, Any]:
            self.logger.info("Using fallback prompt enhancement")
            return {
                "enhanced_prompt": f"[FALLBACK] {prompt}",
                "metadata": {"fallback": True},
            }

        return await self.error_handler.execute_with_protection(
            primary_func, fallback_func
        )

    def get_circuit_breaker_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state.

        Returns:
            Circuit breaker state.
        """
        return self.error_handler.circuit_breaker.state

    def get_failure_count(self) -> int:
        """Get current failure count.

        Returns:
            Number of failures.
        """
        return self.error_handler.circuit_breaker.failure_count