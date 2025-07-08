"""Unit tests for Zen MCP error handling system.

This module contains comprehensive tests for the Zen MCP error handling
components including circuit breaker, retry policy, and error handler.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.core.zen_mcp_error_handling import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    MockZenMCPClient,
    RetryConfig,
    RetryPolicy,
    ZenMCPConnectionError,
    ZenMCPError,
    ZenMCPErrorHandler,
    ZenMCPIntegration,
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=1, success_threshold=2
        )
        self.circuit_breaker = CircuitBreaker(self.config)

    @pytest.mark.asyncio()
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        async def success_func():
            return "success"

        result = await self.circuit_breaker.call(success_func)
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio()
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        async def failure_func():
            raise Exception("Test failure")

        # Trigger failures to open circuit breaker
        for _ in range(self.config.failure_threshold):
            with pytest.raises(ZenMCPError):
                await self.circuit_breaker.call(failure_func)

        assert self.circuit_breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio()
    async def test_circuit_breaker_open_state_blocks_calls(self):
        """Test circuit breaker blocks calls when open."""
        # Force circuit breaker to open state
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.last_failure_time = 0  # Force no reset

        async def success_func():
            return "success"

        with pytest.raises(ZenMCPError, match="Circuit breaker is OPEN"):
            await self.circuit_breaker.call(success_func)

    @pytest.mark.asyncio()
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker half-open recovery."""
        # Force circuit breaker to half-open state
        self.circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        self.circuit_breaker.success_count = 0

        async def success_func():
            return "success"

        # Execute successful calls to close circuit breaker
        for _ in range(self.config.success_threshold):
            result = await self.circuit_breaker.call(success_func)
            assert result == "success"

        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio()
    async def test_circuit_breaker_half_open_failure_reopens(self):
        """Test circuit breaker reopens on failure in half-open state."""
        self.circuit_breaker.state = CircuitBreakerState.HALF_OPEN

        async def failure_func():
            raise Exception("Test failure")

        with pytest.raises(ZenMCPError):
            await self.circuit_breaker.call(failure_func)

        assert self.circuit_breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_should_attempt_reset(self):
        """Test circuit breaker reset timing."""
        import time

        self.circuit_breaker.last_failure_time = time.time() - 2
        assert self.circuit_breaker._should_attempt_reset() is True

        self.circuit_breaker.last_failure_time = time.time()
        assert self.circuit_breaker._should_attempt_reset() is False


class TestRetryPolicy:
    """Test cases for RetryPolicy class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)
        self.retry_policy = RetryPolicy(self.config)

    @pytest.mark.asyncio()
    async def test_retry_policy_success_on_first_try(self):
        """Test retry policy with immediate success."""
        async def success_func():
            return "success"

        result = await self.retry_policy.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio()
    async def test_retry_policy_success_after_retries(self):
        """Test retry policy with success after retries."""
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await self.retry_policy.execute(flaky_func)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio()
    async def test_retry_policy_all_retries_fail(self):
        """Test retry policy when all retries fail."""
        async def failure_func():
            raise Exception("Persistent failure")

        with pytest.raises(ZenMCPError, match="All retry attempts failed"):
            await self.retry_policy.execute(failure_func)

    def test_retry_policy_calculate_delay(self):
        """Test retry delay calculation."""
        delays = [
            self.retry_policy._calculate_delay(i) for i in range(3)
        ]
        
        # Should be exponentially increasing
        assert delays[0] < delays[1] < delays[2]

    def test_retry_policy_max_delay(self):
        """Test retry policy respects max delay."""
        config = RetryConfig(max_delay=1.0, base_delay=0.1, jitter=False)
        retry_policy = RetryPolicy(config)
        
        # Large attempt should still respect max delay
        delay = retry_policy._calculate_delay(10)
        assert delay <= config.max_delay


class TestZenMCPErrorHandler:
    """Test cases for ZenMCPErrorHandler class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.error_handler = ZenMCPErrorHandler()

    @pytest.mark.asyncio()
    async def test_error_handler_primary_success(self):
        """Test error handler with primary function success."""
        async def success_func():
            return "success"

        result = await self.error_handler.execute_with_protection(success_func)
        assert result == "success"

    @pytest.mark.asyncio()
    async def test_error_handler_fallback_success(self):
        """Test error handler with fallback function success."""
        async def failure_func():
            raise Exception("Primary failure")

        async def fallback_func():
            return "fallback_success"

        result = await self.error_handler.execute_with_protection(
            failure_func, fallback_func
        )
        assert result == "fallback_success"

    @pytest.mark.asyncio()
    async def test_error_handler_fallback_failure(self):
        """Test error handler when both primary and fallback fail."""
        async def failure_func():
            raise Exception("Primary failure")

        async def fallback_failure():
            raise Exception("Fallback failure")

        with pytest.raises(ZenMCPError, match="Both primary and fallback functions failed"):
            await self.error_handler.execute_with_protection(
                failure_func, fallback_failure
            )

    @pytest.mark.asyncio()
    async def test_error_handler_no_fallback(self):
        """Test error handler without fallback function."""
        async def failure_func():
            raise Exception("Primary failure")

        with pytest.raises(ZenMCPError):
            await self.error_handler.execute_with_protection(failure_func)


class TestMockZenMCPClient:
    """Test cases for MockZenMCPClient class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = MockZenMCPClient(failure_rate=0.0)

    @pytest.mark.asyncio()
    async def test_mock_client_success(self):
        """Test mock client successful operation."""
        result = await self.client.process_prompt("test prompt")
        assert result["enhanced_prompt"] == "Enhanced: test prompt"
        assert result["metadata"]["call_count"] == 1

    @pytest.mark.asyncio()
    async def test_mock_client_failure(self):
        """Test mock client failure simulation."""
        client = MockZenMCPClient(failure_rate=1.0)
        
        with pytest.raises(ZenMCPConnectionError):
            await client.process_prompt("test prompt")

    @pytest.mark.asyncio()
    async def test_mock_client_call_count(self):
        """Test mock client call counting."""
        await self.client.process_prompt("test 1")
        await self.client.process_prompt("test 2")
        
        assert self.client.call_count == 2


class TestZenMCPIntegration:
    """Test cases for ZenMCPIntegration class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = MockZenMCPClient(failure_rate=0.0)
        self.integration = ZenMCPIntegration(self.client)

    @pytest.mark.asyncio()
    async def test_integration_enhance_prompt_success(self):
        """Test integration prompt enhancement success."""
        result = await self.integration.enhance_prompt("test prompt")
        assert result["enhanced_prompt"] == "Enhanced: test prompt"
        assert "metadata" in result

    @pytest.mark.asyncio()
    async def test_integration_enhance_prompt_fallback(self):
        """Test integration prompt enhancement with fallback."""
        # Use client with 100% failure rate to trigger fallback
        client = MockZenMCPClient(failure_rate=1.0)
        integration = ZenMCPIntegration(client)
        
        result = await integration.enhance_prompt("test prompt")
        assert result["enhanced_prompt"] == "[FALLBACK] test prompt"
        assert result["metadata"]["fallback"] is True

    def test_integration_get_circuit_breaker_state(self):
        """Test getting circuit breaker state."""
        state = self.integration.get_circuit_breaker_state()
        assert state == CircuitBreakerState.CLOSED

    def test_integration_get_failure_count(self):
        """Test getting failure count."""
        count = self.integration.get_failure_count()
        assert count == 0

    @pytest.mark.asyncio()
    async def test_integration_circuit_breaker_opens(self):
        """Test integration circuit breaker opens on failures."""
        # Use client with 100% failure rate
        client = MockZenMCPClient(failure_rate=1.0)
        
        # Configure circuit breaker to open quickly
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        circuit_breaker = CircuitBreaker(config)
        error_handler = ZenMCPErrorHandler(circuit_breaker=circuit_breaker)
        integration = ZenMCPIntegration(client, error_handler)
        
        # Trigger failures to open circuit breaker
        for _ in range(3):
            await integration.enhance_prompt("test prompt")
        
        # Should still work due to fallback, but circuit breaker should be open
        assert integration.get_circuit_breaker_state() == CircuitBreakerState.OPEN


class TestConfiguration:
    """Test cases for configuration classes."""

    def test_circuit_breaker_config_defaults(self):
        """Test CircuitBreakerConfig default values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.success_threshold == 3

    def test_circuit_breaker_config_custom(self):
        """Test CircuitBreakerConfig custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=10, recovery_timeout=30, success_threshold=5
        )
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 30
        assert config.success_threshold == 5

    def test_retry_config_defaults(self):
        """Test RetryConfig default values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_retry_config_custom(self):
        """Test RetryConfig custom values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
        )
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False