"""Comprehensive error handling integration tests.

This module tests error handling, recovery, and fault tolerance across all major
components of the PromptCraft system, including MCP integration, vector stores,
query processing, and configuration management.
"""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.config.settings import ApplicationSettings
from src.core.query_counselor import QueryCounselor
from src.core.vector_store import (
    DEFAULT_VECTOR_DIMENSIONS,
    ConnectionStatus,
    EnhancedMockVectorStore,
    QdrantVectorStore,
    SearchParameters,
)
from src.core.zen_mcp_error_handling import (
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    RecoveryStrategy,
    ZenMCPCircuitBreaker,
    ZenMCPErrorHandler,
    ZenMCPRetryPolicy,
)
from src.mcp_integration.config_manager import MCPConfigurationManager
from src.mcp_integration.mcp_client import (
    MCPAuthenticationError,
    MCPConnectionError,
    MCPConnectionState,
    MCPServiceUnavailableError,
    MCPTimeoutError,
    MCPValidationError,
    ZenMCPClient,
)
from src.mcp_integration.parallel_executor import ParallelSubagentExecutor


class TestComprehensiveErrorHandling:
    """Comprehensive error handling integration tests."""

    @pytest.fixture
    def error_prone_settings(self):
        """Create settings that might cause errors."""
        return ApplicationSettings(
            mcp_enabled=True,
            mcp_server_url="http://unreachable.server:3000",
            mcp_timeout=1.0,  # Short timeout for testing
            mcp_max_retries=2,
            qdrant_enabled=True,
            qdrant_host="unreachable.qdrant.server",
            qdrant_port=6333,
            qdrant_timeout=1.0,
            vector_store_type="qdrant",
        )

    @pytest.fixture
    def mock_error_settings(self):
        """Create mock settings for controlled error testing."""
        return ApplicationSettings(
            mcp_enabled=True,
            mcp_server_url="http://localhost:3000",
            mcp_timeout=10.0,
            mcp_max_retries=3,
            qdrant_enabled=False,
            vector_store_type="mock",
        )

    @pytest.fixture
    def error_handler(self):
        """Create error handler instance."""
        return ZenMCPErrorHandler()

    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker instance."""
        return ZenMCPCircuitBreaker(failure_threshold=3, recovery_timeout=5.0, half_open_max_calls=2)

    @pytest.fixture
    def retry_policy(self):
        """Create retry policy instance."""
        return ZenMCPRetryPolicy(max_retries=3, base_delay=0.1, max_delay=2.0, backoff_factor=2.0)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_connection_error_handling(self, error_prone_settings, error_handler):
        """Test MCP connection error handling with various failure scenarios."""

        # Test connection timeout
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Connection timeout")

            client = ZenMCPClient(
                server_url=error_prone_settings.mcp_server_url,
                timeout=error_prone_settings.mcp_timeout,
                max_retries=error_prone_settings.mcp_max_retries,
            )

            # Test connection failure
            with pytest.raises(MCPConnectionError) as exc_info:
                await client.connect()

            assert "Connection failed" in str(exc_info.value)
            assert client.connection_state == MCPConnectionState.FAILED

            # Test error context creation
            error_context = ErrorContext(
                operation="connect",
                component="ZenMCPClient",
                error_type="ConnectionError",
                details={"server_url": error_prone_settings.mcp_server_url},
            )

            # Test error handling
            handled_error = await error_handler.handle_error(
                exc_info.value, error_context, RecoveryStrategy.CIRCUIT_BREAKER,
            )

            assert handled_error.severity == ErrorSeverity.HIGH
            assert handled_error.category == ErrorCategory.NETWORK
            assert handled_error.recoverable is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_service_unavailable_error_handling(self, mock_error_settings):
        """Test MCP service unavailable error handling."""

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful connection
            mock_connect_response = MagicMock()
            mock_connect_response.status_code = 200
            mock_connect_response.json.return_value = {"status": "healthy"}
            mock_client.get.return_value = mock_connect_response

            client = ZenMCPClient(
                server_url=mock_error_settings.mcp_server_url,
                timeout=mock_error_settings.mcp_timeout,
                max_retries=mock_error_settings.mcp_max_retries,
            )

            await client.connect()

            # Test 503 Service Unavailable
            mock_error_response = MagicMock()
            mock_error_response.status_code = 503
            mock_error_response.headers = {"Retry-After": "30"}
            http_error = httpx.HTTPStatusError("Service unavailable", request=MagicMock(), response=mock_error_response)
            mock_client.post.side_effect = http_error

            with pytest.raises(MCPServiceUnavailableError) as exc_info:
                await client.orchestrate_agents([])

            assert "Service unavailable" in str(exc_info.value)
            assert exc_info.value.retry_after == 30

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_rate_limit_error_handling(self, mock_error_settings):
        """Test MCP rate limit error handling."""

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful connection
            mock_connect_response = MagicMock()
            mock_connect_response.status_code = 200
            mock_connect_response.json.return_value = {"status": "healthy"}
            mock_client.get.return_value = mock_connect_response

            client = ZenMCPClient(
                server_url=mock_error_settings.mcp_server_url,
                timeout=mock_error_settings.mcp_timeout,
                max_retries=mock_error_settings.mcp_max_retries,
            )

            await client.connect()

            # Test 429 Rate Limit
            mock_error_response = MagicMock()
            mock_error_response.status_code = 429
            mock_error_response.headers = {"Retry-After": "60", "X-RateLimit-Limit": "100"}
            http_error = httpx.HTTPStatusError("Rate limit exceeded", request=MagicMock(), response=mock_error_response)
            mock_client.post.side_effect = http_error

            with pytest.raises(MCPServiceUnavailableError) as exc_info:
                await client.orchestrate_agents([])

            assert "Rate limit exceeded" in str(exc_info.value)
            assert exc_info.value.retry_after == 60

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_authentication_error_handling(self, mock_error_settings):
        """Test MCP authentication error handling."""

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock authentication failure
            mock_error_response = MagicMock()
            mock_error_response.status_code = 401
            mock_error_response.json.return_value = {"error": "Invalid API key"}
            http_error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_error_response)
            mock_client.get.side_effect = http_error

            client = ZenMCPClient(
                server_url=mock_error_settings.mcp_server_url,
                timeout=mock_error_settings.mcp_timeout,
                max_retries=mock_error_settings.mcp_max_retries,
                api_key="invalid_key",
            )

            with pytest.raises(MCPAuthenticationError) as exc_info:
                await client.connect()

            assert "Authentication failed" in str(exc_info.value)
            assert exc_info.value.error_code == "INVALID_API_KEY"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_validation_error_handling(self, mock_error_settings):
        """Test MCP validation error handling."""

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful connection
            mock_connect_response = MagicMock()
            mock_connect_response.status_code = 200
            mock_connect_response.json.return_value = {"status": "healthy"}
            mock_client.get.return_value = mock_connect_response

            client = ZenMCPClient(
                server_url=mock_error_settings.mcp_server_url,
                timeout=mock_error_settings.mcp_timeout,
                max_retries=mock_error_settings.mcp_max_retries,
            )

            await client.connect()

            # Test validation error
            mock_error_response = MagicMock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "error": "Validation failed",
                "details": {"field": "query", "message": "Query is too long"},
            }
            http_error = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_error_response)
            mock_client.post.side_effect = http_error

            with pytest.raises(MCPValidationError) as exc_info:
                await client.validate_query("x" * 10000)  # Very long query

            assert "Validation failed" in str(exc_info.value)
            assert exc_info.value.validation_errors == {"field": "query", "message": "Query is too long"}

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vector_store_error_handling(self, mock_error_settings):
        """Test vector store error handling scenarios."""

        # Test with high error rate mock store
        error_config = {
            "type": "mock",
            "simulate_latency": True,
            "error_rate": 0.8,  # 80% error rate
            "base_latency": 0.01,
        }

        store = EnhancedMockVectorStore(error_config)
        await store.connect()

        # Test search error handling
        search_params = SearchParameters(embeddings=[[0.1] * DEFAULT_VECTOR_DIMENSIONS], limit=5, collection="default")

        error_count = 0
        success_count = 0

        # Attempt multiple searches
        for i in range(20):
            try:
                results = await store.search(search_params)
                success_count += 1
            except Exception as e:
                error_count += 1
                # Verify error is properly handled
                assert isinstance(e, RuntimeError)
                assert "Simulated error" in str(e)

        # Should have significant error rate
        assert error_count > 10
        assert success_count > 0  # Some should still succeed

        # Test circuit breaker activation
        assert store._circuit_breaker_failures > 0
        if store._circuit_breaker_failures >= 5:
            assert store._circuit_breaker_open is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_qdrant_connection_error_handling(self, error_prone_settings):
        """Test Qdrant connection error handling."""

        config = {
            "type": "qdrant",
            "host": error_prone_settings.qdrant_host,
            "port": error_prone_settings.qdrant_port,
            "timeout": error_prone_settings.qdrant_timeout,
        }

        # Test connection failure
        with patch("src.core.vector_store.QdrantClient") as mock_client_class:
            mock_client_class.side_effect = ConnectionError("Connection refused")

            store = QdrantVectorStore(config)

            with pytest.raises(RuntimeError) as exc_info:
                await store.connect()

            assert "Qdrant client not available" in str(exc_info.value)
            assert store.get_connection_status() == ConnectionStatus.UNHEALTHY

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_counselor_error_handling(self, mock_error_settings):
        """Test QueryCounselor error handling with component failures."""

        with patch("src.config.settings.get_settings", return_value=mock_error_settings):
            # Mock failing MCP client
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connect.side_effect = MCPConnectionError("Connection failed")

            # Mock failing HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.process_query.side_effect = RuntimeError("Vector store unavailable")

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                # Test QueryCounselor initialization with failing components
                counselor = QueryCounselor()

                # Test graceful degradation
                query = "Test query with failing components"

                # Should handle MCP client failure gracefully
                try:
                    intent = await counselor.analyze_intent(query)
                    # Should still return some intent even with failures
                    assert intent is not None
                except Exception as e:
                    # If it fails, should be a controlled failure
                    assert "Connection failed" in str(e) or "Vector store unavailable" in str(e)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, circuit_breaker):
        """Test circuit breaker functionality with error scenarios."""

        # Test circuit breaker states
        assert circuit_breaker.state == "CLOSED"

        # Simulate failures to trigger circuit breaker
        for i in range(3):
            circuit_breaker.record_failure()

        # Should transition to OPEN state
        assert circuit_breaker.state == "OPEN"

        # Test call blocking in OPEN state
        with pytest.raises(Exception) as exc_info:
            circuit_breaker.call(lambda: "test")

        assert "Circuit breaker is OPEN" in str(exc_info.value)

        # Test transition to HALF_OPEN after timeout
        await asyncio.sleep(0.1)  # Simulate time passing
        circuit_breaker._last_failure_time = time.time() - 10  # Force timeout

        # Should allow limited calls in HALF_OPEN state
        circuit_breaker.state = "HALF_OPEN"
        result = circuit_breaker.call(lambda: "success")
        assert result == "success"

        # Record success should close circuit
        circuit_breaker.record_success()
        assert circuit_breaker.state == "CLOSED"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_retry_policy_functionality(self, retry_policy):
        """Test retry policy functionality with various error scenarios."""

        # Test successful retry after transient failure
        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Transient failure")
            return "success"

        result = await retry_policy.execute(failing_function)
        assert result == "success"
        assert call_count == 3

        # Test retry exhaustion
        call_count = 0

        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("Permanent failure")

        with pytest.raises(httpx.ConnectError):
            await retry_policy.execute(always_failing_function)

        assert call_count == 4  # Original + 3 retries

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_context_and_categorization(self, error_handler):
        """Test error context creation and categorization."""

        # Test network error categorization
        network_error = httpx.ConnectError("Connection refused")
        network_context = ErrorContext(
            operation="connect",
            component="ZenMCPClient",
            error_type="ConnectError",
            details={"server_url": "http://localhost:3000"},
        )

        handled_network = await error_handler.handle_error(network_error, network_context, RecoveryStrategy.RETRY)

        assert handled_network.category == ErrorCategory.NETWORK
        assert handled_network.severity == ErrorSeverity.HIGH
        assert handled_network.recoverable is True

        # Test validation error categorization
        validation_error = ValueError("Invalid input parameters")
        validation_context = ErrorContext(
            operation="validate_query",
            component="QueryValidator",
            error_type="ValueError",
            details={"parameter": "query", "value": ""},
        )

        handled_validation = await error_handler.handle_error(
            validation_error, validation_context, RecoveryStrategy.IMMEDIATE_FAIL,
        )

        assert handled_validation.category == ErrorCategory.VALIDATION
        assert handled_validation.severity == ErrorSeverity.MEDIUM
        assert handled_validation.recoverable is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_parallel_executor_error_handling(self, mock_error_settings):
        """Test parallel executor error handling with agent failures."""

        with patch("src.config.settings.get_settings", return_value=mock_error_settings):
            # Mock configuration manager
            config_manager = MagicMock()
            config_manager.get_parallel_execution_config.return_value = {"max_concurrent": 3, "timeout_seconds": 5}

            # Mock MCP client with mixed success/failure
            mock_mcp_client = AsyncMock()

            # Mock executor
            executor = ParallelSubagentExecutor(config_manager, mock_mcp_client)

            # Mock agent execution with some failures
            async def mock_execute_agent(agent_id, input_data):
                if agent_id == "failing_agent":
                    raise RuntimeError("Agent execution failed")
                return {"agent_id": agent_id, "success": True, "result": f"Success from {agent_id}"}

            mock_mcp_client.execute_agent = mock_execute_agent

            # Test parallel execution with mixed results
            agent_tasks = [
                ("success_agent_1", {"query": "test"}),
                ("failing_agent", {"query": "test"}),
                ("success_agent_2", {"query": "test"}),
            ]

            results = await executor.execute_agents_parallel(agent_tasks)

            # Should handle partial failures gracefully
            assert len(results) == 3
            successful_results = [r for r in results if r.get("success")]
            failed_results = [r for r in results if not r.get("success")]

            assert len(successful_results) == 2
            assert len(failed_results) == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_configuration_error_handling(self):
        """Test configuration error handling scenarios."""

        # Test invalid configuration
        with pytest.raises(ValueError):
            ApplicationSettings(
                mcp_timeout=-1,  # Invalid timeout
                mcp_max_retries=-1,  # Invalid retries
                qdrant_port=70000,  # Invalid port
            )

        # Test missing required configuration
        incomplete_settings = ApplicationSettings(mcp_enabled=True, mcp_server_url="", mcp_timeout=10.0)  # Empty URL

        # Should handle empty URL gracefully
        assert incomplete_settings.mcp_server_url == ""

        # Test configuration validation
        config_manager = MCPConfigurationManager()
        with patch("src.config.settings.get_settings", return_value=incomplete_settings):
            is_valid = config_manager.validate_configuration()
            assert is_valid is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_strategies(self, error_handler):
        """Test different error recovery strategies."""

        # Test immediate fail strategy
        critical_error = RuntimeError("Critical system failure")
        critical_context = ErrorContext(
            operation="system_operation", component="CoreSystem", error_type="RuntimeError", details={"critical": True},
        )

        handled_critical = await error_handler.handle_error(
            critical_error, critical_context, RecoveryStrategy.IMMEDIATE_FAIL,
        )

        assert handled_critical.recovery_strategy == RecoveryStrategy.IMMEDIATE_FAIL
        assert handled_critical.recoverable is False

        # Test retry strategy
        transient_error = httpx.TimeoutException("Request timeout")
        transient_context = ErrorContext(
            operation="http_request", component="HTTPClient", error_type="TimeoutException", details={"timeout": 5.0},
        )

        handled_transient = await error_handler.handle_error(transient_error, transient_context, RecoveryStrategy.RETRY)

        assert handled_transient.recovery_strategy == RecoveryStrategy.RETRY
        assert handled_transient.recoverable is True

        # Test circuit breaker strategy
        network_error = httpx.ConnectError("Connection refused")
        network_context = ErrorContext(
            operation="connect",
            component="NetworkClient",
            error_type="ConnectError",
            details={"host": "localhost", "port": 3000},
        )

        handled_network = await error_handler.handle_error(
            network_error, network_context, RecoveryStrategy.CIRCUIT_BREAKER,
        )

        assert handled_network.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER
        assert handled_network.recoverable is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_error_resilience(self, mock_error_settings):
        """Test end-to-end error resilience across all components."""

        with patch("src.config.settings.get_settings", return_value=mock_error_settings):
            # Mock components with various failure modes
            mock_mcp_client = AsyncMock()
            mock_hyde_processor = AsyncMock()

            # Simulate intermittent failures
            call_count = 0

            async def intermittent_mcp_failure(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Fail every 3rd call
                    raise MCPTimeoutError("Intermittent timeout")
                return [MagicMock(success=True, content="Success")]

            mock_mcp_client.orchestrate_agents.side_effect = intermittent_mcp_failure

            # Configure mock vector store with error rate
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "error_rate": 0.2, "base_latency": 0.01},  # 20% error rate
            )
            await mock_vector_store.connect()

            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query.return_value = {
                "enhanced_query": "Enhanced query",
                "original_query": "Original query",
                "enhancement_score": 0.8,
            }

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test multiple queries with error resilience
                successful_queries = 0
                failed_queries = 0

                for i in range(10):
                    try:
                        query = f"Test query {i}"
                        intent = await counselor.analyze_intent(query)

                        # Try to process with HyDE (may fail due to vector store errors)
                        try:
                            hyde_result = await counselor.hyde_processor.process_query(query)
                        except:
                            # Use original query if HyDE fails
                            hyde_result = {"enhanced_query": query}

                        # Try to orchestrate agents (may fail due to MCP errors)
                        try:
                            agents = await counselor.select_agents(intent)
                            responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])
                            successful_queries += 1
                        except Exception as e:
                            failed_queries += 1
                            # Verify error is handled gracefully
                            assert isinstance(e, (MCPTimeoutError, RuntimeError))

                    except Exception as e:
                        failed_queries += 1
                        # Should be controlled failures
                        assert isinstance(e, (MCPTimeoutError, RuntimeError, ConnectionError))

                # Should have some successful queries despite errors
                assert successful_queries > 0
                assert failed_queries > 0

                # System should remain stable
                assert counselor.mcp_client is not None
                assert counselor.hyde_processor is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_logging_and_monitoring(self, error_handler):
        """Test error logging and monitoring capabilities."""

        # Test error logging
        test_error = RuntimeError("Test error for logging")
        test_context = ErrorContext(
            operation="test_operation", component="TestComponent", error_type="RuntimeError", details={"test": True},
        )

        handled_error = await error_handler.handle_error(test_error, test_context, RecoveryStrategy.RETRY)

        # Verify error is properly logged
        assert handled_error.timestamp > 0
        assert handled_error.error_id is not None
        assert handled_error.context == test_context

        # Test error metrics
        error_metrics = error_handler.get_error_metrics()
        assert error_metrics["total_errors"] >= 1
        assert error_metrics["errors_by_category"]["SYSTEM"] >= 1
        assert error_metrics["errors_by_severity"]["MEDIUM"] >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graceful_degradation_scenarios(self, mock_error_settings):
        """Test graceful degradation in various failure scenarios."""

        # Test with all components working
        with patch("src.config.settings.get_settings", return_value=mock_error_settings):
            mock_mcp_client = AsyncMock()
            mock_mcp_client.orchestrate_agents.return_value = [MagicMock(success=True, content="Full functionality")]

            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.process_query.return_value = {
                "enhanced_query": "Enhanced query",
                "enhancement_score": 0.9,
            }

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test full functionality
                query = "Test query"
                intent = await counselor.analyze_intent(query)
                hyde_result = await counselor.hyde_processor.process_query(query)
                agents = await counselor.select_agents(intent)
                responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                assert len(responses) == 1
                assert responses[0].success is True
                assert responses[0].content == "Full functionality"

        # Test with HyDE processor failing (should degrade gracefully)
        with patch("src.config.settings.get_settings", return_value=mock_error_settings):
            mock_mcp_client = AsyncMock()
            mock_mcp_client.orchestrate_agents.return_value = [
                MagicMock(success=True, content="Degraded functionality"),
            ]

            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.process_query.side_effect = RuntimeError("HyDE processor failed")

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test degraded functionality
                query = "Test query"
                intent = await counselor.analyze_intent(query)

                # HyDE should fail, but system should continue
                try:
                    hyde_result = await counselor.hyde_processor.process_query(query)
                except RuntimeError:
                    # Use original query as fallback
                    hyde_result = {"enhanced_query": query}

                agents = await counselor.select_agents(intent)
                responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                assert len(responses) == 1
                assert responses[0].success is True
                assert responses[0].content == "Degraded functionality"
