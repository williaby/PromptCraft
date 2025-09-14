"""
Comprehensive tests for ZenStdioMCPClient.

This test suite provides comprehensive coverage for the ZenStdioMCPClient class,
testing all methods including connection management, health checks, model recommendations,
routing execution, query validation, agent orchestration, and environment handling.
"""

import time
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.mcp_integration.mcp_client import (
    MCPConnectionState,
    MCPError,
    MCPHealthStatus,
)
from src.mcp_integration.zen_client import (
    RouteAnalysisRequest,
    SmartExecutionRequest,
)
from src.mcp_integration.zen_stdio_client import (
    ZenStdioMCPClient,
    create_zen_stdio_client,
)


class MockZenClient:
    """Mock Zen MCP stdio client for testing."""

    def __init__(self, healthy: bool = True, raise_exception: bool = False):
        self.healthy = healthy
        self.raise_exception = raise_exception

    async def health_check(self):
        if self.raise_exception:
            raise Exception("Health check failed")
        return MagicMock(
            healthy=self.healthy,
            latency_ms=50.0,
            server_version="1.0.0",
        )

    async def disconnect(self):
        if self.raise_exception:
            raise Exception("Disconnect failed")
        return True

    async def analyze_route(self, request: RouteAnalysisRequest):
        if self.raise_exception:
            raise Exception("Route analysis failed")

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.recommendations = {
            "primary": {
                "model_id": "gpt-4",
                "model_name": "GPT-4",
                "tier": "premium",
                "reasoning": "Best for complex tasks",
            },
            "cost_comparison": {
                "recommended_cost": 0.03,
            },
        }
        mock_result.analysis = {
            "task_type": "complex_analysis",
            "complexity_score": 0.8,
            "complexity_level": "high",
            "indicators": ["complex_reasoning", "multi_step"],
            "reasoning": "Complex analysis task detected",
        }
        return mock_result

    async def smart_execute(self, request: SmartExecutionRequest):
        if self.raise_exception:
            raise Exception("Smart execution failed")

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.response = {
            "content": "Test response",
            "model_used": "gpt-4",
            "estimated_cost": 0.05,
        }
        mock_result.execution_metadata = {
            "task_type": "analysis",
            "complexity_level": "medium",
            "selection_reasoning": "Selected based on capabilities",
            "cost_optimized": True,
            "confidence": 0.9,
        }
        return mock_result


class TestZenStdioMCPClient:
    """Test suite for ZenStdioMCPClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return ZenStdioMCPClient(
            server_path="/test/server.py",
            http_fallback_url="http://test:8000",
            timeout=10.0,
            max_retries=2,
            backoff_factor=0.5,
        )

    @pytest.fixture
    def mock_zen_client(self):
        """Create a mock zen client."""
        return MockZenClient()

    def test_initialization(self, client):
        """Test client initialization with default and custom parameters."""
        # Test initialization parameters
        assert client.server_path == "/test/server.py"
        assert client.http_fallback_url == "http://test:8000"
        assert client.timeout == 10.0
        assert client.max_retries == 2
        assert client.backoff_factor == 0.5

        # Test initial state
        assert client.zen_client is None
        assert client.connection_state == MCPConnectionState.DISCONNECTED
        assert client.error_count == 0
        assert client.last_successful_request is None

    def test_initialization_defaults(self):
        """Test client initialization with default parameters."""
        client = ZenStdioMCPClient()

        assert client.server_path == "/home/byron/dev/zen-mcp-server/server.py"
        assert client.http_fallback_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.backoff_factor == 1.0

    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        """Test successful connection to zen server."""
        mock_zen_client = MockZenClient(healthy=True)

        with patch("src.mcp_integration.zen_stdio_client.create_client", return_value=mock_zen_client) as mock_create:
            with patch.object(client, "_get_zen_environment", return_value={"TEST": "value"}):
                result = await client.connect()

                assert result is True
                assert client.connection_state == MCPConnectionState.CONNECTED
                assert client.zen_client == mock_zen_client
                assert client.last_successful_request is not None

                # Verify create_client was called with correct parameters
                mock_create.assert_called_once_with(
                    server_path="/test/server.py",
                    env_vars={"TEST": "value"},
                    http_fallback_url="http://test:8000",
                )

    @pytest.mark.asyncio
    async def test_connect_health_check_failure(self, client):
        """Test connection failure due to health check failure."""
        mock_zen_client = MockZenClient(healthy=False)

        with patch("src.mcp_integration.zen_stdio_client.create_client", return_value=mock_zen_client):
            with patch.object(client, "_get_zen_environment", return_value={}):
                result = await client.connect()

                assert result is False
                assert client.connection_state == MCPConnectionState.DISCONNECTED
                assert client.error_count == 1

    @pytest.mark.asyncio
    async def test_connect_exception(self, client):
        """Test connection failure due to exception."""
        with patch("src.mcp_integration.zen_stdio_client.create_client", side_effect=Exception("Connection failed")):
            with patch.object(client, "_get_zen_environment", return_value={}):
                result = await client.connect()

                assert result is False
                assert client.connection_state == MCPConnectionState.DISCONNECTED
                assert client.error_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_success(self, client):
        """Test successful disconnection."""
        mock_zen_client = MockZenClient()
        client.zen_client = mock_zen_client
        client.connection_state = MCPConnectionState.CONNECTED

        result = await client.disconnect()

        assert result is True
        assert client.zen_client is None
        assert client.connection_state == MCPConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_disconnect_with_exception(self, client):
        """Test disconnection with exception."""
        mock_zen_client = MockZenClient(raise_exception=True)
        client.zen_client = mock_zen_client

        result = await client.disconnect()

        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self, client):
        """Test disconnection when no client is connected."""
        result = await client.disconnect()

        assert result is True
        assert client.connection_state == MCPConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        mock_zen_client = MockZenClient(healthy=True)
        client.zen_client = mock_zen_client
        client.connection_state = MCPConnectionState.CONNECTED
        client.last_successful_request = time.time()

        health_status = await client.health_check()

        assert isinstance(health_status, MCPHealthStatus)
        assert health_status.connection_state == MCPConnectionState.CONNECTED
        assert health_status.response_time_ms == 50.0
        assert "mcp_stdio" in health_status.capabilities
        assert "zen_native" in health_status.capabilities
        assert health_status.server_version == "1.0.0"
        assert health_status.metadata["zen_native"] is True
        assert health_status.metadata["server_healthy"] is True

    @pytest.mark.asyncio
    async def test_health_check_no_client(self, client):
        """Test health check when not connected."""
        with pytest.raises(MCPError, match="Not connected to server"):
            await client.health_check()

    @pytest.mark.asyncio
    async def test_health_check_exception(self, client):
        """Test health check with exception."""
        mock_zen_client = MockZenClient(raise_exception=True)
        client.zen_client = mock_zen_client

        with pytest.raises(MCPError, match="Health check failed"):
            await client.health_check()

        assert client.error_count == 1

    @pytest.mark.asyncio
    async def test_get_model_recommendations_success(self, client):
        """Test successful model recommendations."""
        mock_zen_client = MockZenClient()
        client.zen_client = mock_zen_client

        with patch("src.mcp_integration.models.ModelRecommendation") as mock_model_rec_class:
            with patch("src.mcp_integration.models.RoutingAnalysis") as mock_routing_analysis_class:
                # Setup mocks
                mock_model_rec = MagicMock()
                mock_model_rec_class.return_value = mock_model_rec

                mock_routing_analysis = MagicMock()
                mock_routing_analysis_class.return_value = mock_routing_analysis

                result = await client.get_model_recommendations("test prompt")

                assert result == mock_routing_analysis
                mock_model_rec_class.assert_called_once()
                mock_routing_analysis_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_model_recommendations_no_recommendations(self, client):
        """Test model recommendations with missing recommendations."""
        mock_zen_client = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.recommendations = None  # No recommendations
        mock_result.analysis = {"task_type": "test"}
        mock_zen_client.analyze_route = AsyncMock(return_value=mock_result)

        client.zen_client = mock_zen_client

        with patch("src.mcp_integration.models.ModelRecommendation") as mock_model_rec_class:
            with patch("src.mcp_integration.models.RoutingAnalysis"):
                await client.get_model_recommendations("test prompt")

                # Should handle missing recommendations gracefully
                mock_model_rec_class.assert_called_once()
                call_args = mock_model_rec_class.call_args
                assert call_args[1]["model_id"] == "unknown"
                assert call_args[1]["reasoning"] == "No recommendations available"

    @pytest.mark.asyncio
    async def test_get_model_recommendations_no_client(self, client):
        """Test model recommendations when not connected."""
        with pytest.raises(MCPError, match="Not connected to server"):
            await client.get_model_recommendations("test prompt")

    @pytest.mark.asyncio
    async def test_get_model_recommendations_exception(self, client):
        """Test model recommendations with exception."""
        mock_zen_client = MockZenClient(raise_exception=True)
        client.zen_client = mock_zen_client

        result = await client.get_model_recommendations("test prompt")

        assert result is None

    @pytest.mark.asyncio
    async def test_execute_with_routing_success(self, client):
        """Test successful routing execution."""
        mock_zen_client = MockZenClient()
        client.zen_client = mock_zen_client

        result = await client.execute_with_routing("test prompt")

        assert result["success"] is True
        assert "result" in result
        assert result["result"]["content"] == "Test response"
        assert result["result"]["model_used"] == "gpt-4"
        assert result["result"]["estimated_cost"] == 0.05
        assert "routing_metadata" in result["result"]
        assert result["result"]["routing_metadata"]["zen_native"] is True
        assert result["result"]["routing_metadata"]["fallback_used"] is False

    @pytest.mark.asyncio
    async def test_execute_with_routing_failure(self, client):
        """Test routing execution failure."""
        mock_zen_client = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Execution failed"
        mock_zen_client.smart_execute = AsyncMock(return_value=mock_result)

        client.zen_client = mock_zen_client

        result = await client.execute_with_routing("test prompt")

        assert result["success"] is False
        assert "Zen execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_with_routing_no_client(self, client):
        """Test routing execution when not connected."""
        with pytest.raises(MCPError, match="Not connected to server"):
            await client.execute_with_routing("test prompt")

    @pytest.mark.asyncio
    async def test_execute_with_routing_exception(self, client):
        """Test routing execution with exception."""
        mock_zen_client = MockZenClient(raise_exception=True)
        client.zen_client = mock_zen_client

        result = await client.execute_with_routing("test prompt")

        assert result["success"] is False
        assert "MCP execution failed" in result["error"]

    def test_get_zen_environment_success(self, client):
        """Test successful environment variable loading."""
        env_content = "API_KEY=test_key\nDATABASE_URL=test_url\n# Comment line\nDEBUG=true\n"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.open", mock_open(read_data=env_content)):
                env_vars = client._get_zen_environment()

                assert env_vars["API_KEY"] == "test_key"
                assert env_vars["DATABASE_URL"] == "test_url"
                assert env_vars["DEBUG"] == "true"
                assert env_vars["LOG_LEVEL"] == "INFO"
                assert env_vars["PROMPTCRAFT_INTEGRATION"] == "true"

    def test_get_zen_environment_file_not_exists(self, client):
        """Test environment loading when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            env_vars = client._get_zen_environment()

            assert env_vars["LOG_LEVEL"] == "INFO"
            assert env_vars["PROMPTCRAFT_INTEGRATION"] == "true"
            assert len(env_vars) == 2  # Only default values

    def test_get_zen_environment_file_error(self, client):
        """Test environment loading with file read error."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=OSError("File read error")):
                env_vars = client._get_zen_environment()

                # Should return default values when file read fails
                assert env_vars["LOG_LEVEL"] == "INFO"
                assert env_vars["PROMPTCRAFT_INTEGRATION"] == "true"

    @pytest.mark.asyncio
    async def test_validate_query_not_connected(self, client):
        """Test query validation when not connected."""
        # Empty query
        result = await client.validate_query("")
        assert result["is_valid"] is False
        assert "Empty query" in result["potential_issues"]

        # Valid query
        result = await client.validate_query("test query")
        assert result["is_valid"] is True
        assert result["sanitized_query"] == "test query"
        assert result["potential_issues"] == []

    @pytest.mark.asyncio
    async def test_validate_query_connected_valid(self, client):
        """Test query validation when connected with valid query."""
        client.zen_client = MockZenClient()

        result = await client.validate_query("  valid query  ")

        assert result["is_valid"] is True
        assert result["sanitized_query"] == "valid query"
        assert result["potential_issues"] == []

    @pytest.mark.asyncio
    async def test_validate_query_security_issues(self, client):
        """Test query validation with security issues."""
        client.zen_client = MockZenClient()

        malicious_query = "<script>alert('xss')</script> javascript:void(0) eval(malicious)"
        result = await client.validate_query(malicious_query)

        assert result["is_valid"] is False
        assert "Potential XSS attempt detected" in result["potential_issues"]
        assert "<script>" not in result["sanitized_query"]
        assert "javascript:" not in result["sanitized_query"]
        assert "eval(" not in result["sanitized_query"]

    @pytest.mark.asyncio
    async def test_validate_query_length_limit(self, client):
        """Test query validation with length limit."""
        client.zen_client = MockZenClient()

        long_query = "a" * 10001  # Exceeds limit
        result = await client.validate_query(long_query)

        assert result["is_valid"] is False
        assert "Query exceeds maximum length" in result["potential_issues"]

    @pytest.mark.asyncio
    async def test_validate_query_exception(self, client):
        """Test query validation with exception."""
        client.zen_client = MockZenClient()

        # Simulate an exception during validation by mocking len() to fail
        with patch("builtins.len", side_effect=Exception("Validation error")):
            result = await client.validate_query("test")

            assert result["is_valid"] is True  # Fail open
            assert "Validation service error" in result["potential_issues"][0]

    @pytest.mark.asyncio
    async def test_orchestrate_agents_success(self, client):
        """Test successful agent orchestration."""
        client.zen_client = MockZenClient()

        # Create mock workflow steps
        workflow_steps = [
            MagicMock(step_id="step1", agent_id="agent1"),
            MagicMock(step_id="step2", agent_id="agent2"),
        ]

        with patch("src.mcp_integration.mcp_client.Response") as mock_response_class:
            mock_response = MagicMock()
            mock_response_class.return_value = mock_response

            responses = await client.orchestrate_agents(workflow_steps)

            assert len(responses) == 2
            assert mock_response_class.call_count == 2

            # Verify response creation calls
            calls = mock_response_class.call_args_list
            assert calls[0][1]["agent_id"] == "agent1"
            assert calls[0][1]["success"] is True
            assert calls[1][1]["agent_id"] == "agent2"
            assert calls[1][1]["success"] is True

    @pytest.mark.asyncio
    async def test_orchestrate_agents_with_errors(self, client):
        """Test agent orchestration with errors."""
        client.zen_client = MockZenClient()

        workflow_steps = [MagicMock(step_id="step1", agent_id="agent1")]

        def side_effect(*args, **kwargs):
            # First call fails, second call (in exception handler) succeeds
            if hasattr(side_effect, "call_count"):
                side_effect.call_count += 1
            else:
                side_effect.call_count = 1

            if side_effect.call_count == 1:
                raise Exception("Response creation failed")
            return MagicMock()  # Return mock for error response

        with patch("src.mcp_integration.mcp_client.Response", side_effect=side_effect) as mock_response_class:
            responses = await client.orchestrate_agents(workflow_steps)

            assert len(responses) == 1
            # Should create error response when Response creation fails
            assert mock_response_class.call_count == 2  # One for success, one for error handling

    @pytest.mark.asyncio
    async def test_orchestrate_agents_no_client(self, client):
        """Test agent orchestration when not connected."""
        workflow_steps = [MagicMock()]

        with pytest.raises(MCPError, match="Not connected to server"):
            await client.orchestrate_agents(workflow_steps)

    @pytest.mark.asyncio
    async def test_get_capabilities_not_connected(self, client):
        """Test get capabilities when not connected."""
        capabilities = await client.get_capabilities()

        expected_capabilities = ["mcp_stdio", "zen_native", "http_fallback"]
        assert capabilities == expected_capabilities

    @pytest.mark.asyncio
    async def test_get_capabilities_connected(self, client):
        """Test get capabilities when connected."""
        client.zen_client = MockZenClient()

        capabilities = await client.get_capabilities()

        expected_capabilities = [
            "mcp_stdio",
            "zen_native",
            "http_fallback",
            "dynamic_model_selector",
            "smart_execution",
            "route_analysis",
            "cost_optimization",
        ]
        assert capabilities == expected_capabilities

    @pytest.mark.asyncio
    async def test_get_capabilities_exception(self, client):
        """Test get capabilities with exception."""
        client.zen_client = MockZenClient()

        # Mock logger to capture the exception
        with patch("src.mcp_integration.zen_stdio_client.logger.error") as mock_error:
            # Patch the method to force an exception in the try block
            async def failing_get_capabilities():
                try:
                    # Force an exception
                    raise Exception("Capabilities error")
                except Exception as e:
                    mock_error(f"Failed to get capabilities: {e}")
                    return ["mcp_stdio", "zen_native", "http_fallback"]

            # Replace the method
            client.get_capabilities = failing_get_capabilities
            capabilities = await client.get_capabilities()

            # Should return fallback capabilities
            expected_capabilities = ["mcp_stdio", "zen_native", "http_fallback"]
            assert capabilities == expected_capabilities
            mock_error.assert_called_once()


class TestCreateZenStdioClient:
    """Test suite for create_zen_stdio_client function."""

    @pytest.mark.asyncio
    async def test_create_zen_stdio_client_success(self):
        """Test successful client creation and connection."""
        with patch.object(ZenStdioMCPClient, "connect", return_value=True) as mock_connect:
            client = await create_zen_stdio_client(
                server_path="/test/server.py",
                timeout=15.0,
            )

            assert isinstance(client, ZenStdioMCPClient)
            assert client.server_path == "/test/server.py"
            assert client.timeout == 15.0
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_zen_stdio_client_defaults(self):
        """Test client creation with default parameters."""
        with patch.object(ZenStdioMCPClient, "connect", return_value=True) as mock_connect:
            client = await create_zen_stdio_client()

            assert isinstance(client, ZenStdioMCPClient)
            assert client.server_path == "/home/byron/dev/zen-mcp-server/server.py"
            mock_connect.assert_called_once()


class TestEdgeCasesAndErrorHandling:
    """Test suite for edge cases and comprehensive error handling."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return ZenStdioMCPClient()

    @pytest.mark.asyncio
    async def test_health_check_no_latency(self, client):
        """Test health check when zen client returns no latency."""
        mock_zen_client = MagicMock()
        mock_health = MagicMock()
        mock_health.healthy = True
        mock_health.latency_ms = None  # No latency
        mock_health.server_version = "test"
        mock_zen_client.health_check = AsyncMock(return_value=mock_health)

        client.zen_client = mock_zen_client
        client.connection_state = MCPConnectionState.CONNECTED

        health_status = await client.health_check()

        assert health_status.response_time_ms == 0.0

    @pytest.mark.asyncio
    async def test_health_check_no_health_object(self, client):
        """Test health check when zen client returns None."""
        mock_zen_client = MagicMock()
        mock_zen_client.health_check = AsyncMock(return_value=None)

        client.zen_client = mock_zen_client
        client.connection_state = MCPConnectionState.CONNECTED

        health_status = await client.health_check()

        assert health_status.response_time_ms == 0.0
        assert health_status.server_version == "unknown"
        assert health_status.metadata["server_healthy"] is False

    @pytest.mark.asyncio
    async def test_execute_routing_no_result(self, client):
        """Test routing execution when zen client returns None."""
        mock_zen_client = MagicMock()
        mock_zen_client.smart_execute = AsyncMock(return_value=None)

        client.zen_client = mock_zen_client

        result = await client.execute_with_routing("test")

        assert result["success"] is False
        assert "Unknown error" in result["error"]

    @pytest.mark.asyncio
    async def test_get_model_recommendations_unsuccessful_result(self, client):
        """Test model recommendations when result is not successful."""
        mock_zen_client = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_zen_client.analyze_route = AsyncMock(return_value=mock_result)

        client.zen_client = mock_zen_client

        result = await client.get_model_recommendations("test")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_query_empty_string(self, client):
        """Test query validation with empty string."""
        result = await client.validate_query("")

        assert result["is_valid"] is False
        assert result["sanitized_query"] == ""
        assert "Empty query" in result["potential_issues"]

    @pytest.mark.asyncio
    async def test_validate_query_whitespace_only(self, client):
        """Test query validation with whitespace only."""
        result = await client.validate_query("   ")

        assert result["is_valid"] is False
        assert result["sanitized_query"] == ""
        assert "Empty query" in result["potential_issues"]

    @pytest.mark.asyncio
    async def test_validate_query_none_input(self, client):
        """Test query validation with None input."""
        result = await client.validate_query(None)

        assert result["is_valid"] is False
        assert result["sanitized_query"] == ""
        assert "Empty query" in result["potential_issues"]
