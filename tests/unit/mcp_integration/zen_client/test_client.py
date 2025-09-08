"""Comprehensive tests for ZenMCPStdioClient."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.mcp_integration.zen_client.client import ZenMCPStdioClient, create_client
from src.mcp_integration.zen_client.models import (
    AnalysisResult,
    ExecutionResult,
    ModelListResult,
    RouteAnalysisRequest,
)


class TestZenMCPStdioClient:
    """Test ZenMCPStdioClient functionality."""

    def test_client_initialization(self, connection_config, fallback_config):
        """Test client initialization with configuration."""
        client = ZenMCPStdioClient(
            server_path="./test_server.py",
            env_vars={"TEST": "value"},
            fallback_config=fallback_config,
            connection_timeout=30.0,
        )

        assert client.connection_config.server_path == "./test_server.py"
        assert client.connection_config.env_vars["TEST"] == "value"
        assert client.connection_config.timeout == 30.0
        assert not client.connected
        assert client.current_process is None
        assert client.process_pool is not None
        assert client.protocol_bridge is not None
        assert client.connection_manager is not None
        assert client.retry_handler is not None

    def test_client_initialization_with_defaults(self):
        """Test client initialization with minimal configuration."""
        client = ZenMCPStdioClient(server_path="./server.py")

        assert client.connection_config.server_path == "./server.py"
        assert client.connection_config.env_vars == {}
        assert client.connection_config.timeout == 30.0
        assert not client.connected

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_subprocess):
        """Test successful connection to server."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock process pool and test connection
        mock_process = Mock()
        mock_process.is_running.return_value = True
        client.process_pool.get_process = AsyncMock(return_value=mock_process)
        client._test_connection = AsyncMock(return_value=True)

        result = await client.connect()

        assert result is True
        assert client.connected is True
        assert client.current_process is mock_process

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Test connection when already connected."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Set up already connected state
        mock_process = Mock()
        mock_process.is_running.return_value = True
        client.connected = True
        client.current_process = mock_process

        result = await client.connect()

        assert result is True
        assert client.connected is True

    @pytest.mark.asyncio
    async def test_connect_process_start_failure(self):
        """Test connection failure when process won't start."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock process pool failure
        client.process_pool.get_process = AsyncMock(return_value=None)

        result = await client.connect()

        assert result is False
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_connect_test_failure(self):
        """Test connection failure when test connection fails."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.is_running.return_value = True
        client.process_pool.get_process = AsyncMock(return_value=mock_process)
        client._test_connection = AsyncMock(return_value=False)

        result = await client.connect()

        assert result is False
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_connect_exception_handling(self):
        """Test connection exception handling."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.process_pool.get_process = AsyncMock(side_effect=Exception("Process error"))

        result = await client.connect()

        assert result is False
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection and cleanup."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Set up connected state
        client.connected = True
        client.current_process = Mock()
        client.process_pool.shutdown_all = AsyncMock()
        client.connection_manager.close = AsyncMock()

        await client.disconnect()

        assert client.connected is False
        assert client.current_process is None
        client.process_pool.shutdown_all.assert_called_once()
        client.connection_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_exception_handling(self):
        """Test disconnect exception handling."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connected = True
        client.process_pool.shutdown_all = AsyncMock(side_effect=Exception("Shutdown error"))
        client.connection_manager.close = AsyncMock()

        # Should not raise exception
        await client.disconnect()

        assert client.connected is False

    @pytest.mark.asyncio
    async def test_analyze_route_success(self, sample_route_analysis_request):
        """Test successful route analysis."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock successful operation
        expected_result = {
            "success": True,
            "analysis": {"complexity_score": 0.7},
            "recommendations": {"primary_model": "claude-3-5-sonnet"},
            "processing_time": 1.2,
        }
        client.connection_manager.with_fallback_to_http = AsyncMock(return_value=(expected_result, True))

        result = await client.analyze_route(sample_route_analysis_request)

        assert isinstance(result, AnalysisResult)
        assert result.success is True
        assert result.analysis == {"complexity_score": 0.7}
        assert result.processing_time == 1.2

    @pytest.mark.asyncio
    async def test_analyze_route_failure(self, sample_route_analysis_request):
        """Test route analysis failure handling."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connection_manager.with_fallback_to_http = AsyncMock(side_effect=Exception("Analysis failed"))

        result = await client.analyze_route(sample_route_analysis_request)

        assert isinstance(result, AnalysisResult)
        assert result.success is False
        assert result.error == "Analysis failed"

    @pytest.mark.asyncio
    async def test_smart_execute_success(self, sample_smart_execution_request):
        """Test successful smart execution."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        expected_result = {
            "success": True,
            "result": {"content": "Generated content", "model_used": "claude-3-5-sonnet"},
            "execution_metadata": {"cost": 0.05},
            "processing_time": 2.1,
        }
        client.connection_manager.with_fallback_to_http = AsyncMock(return_value=(expected_result, True))

        result = await client.smart_execute(sample_smart_execution_request)

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.response["content"] == "Generated content"
        assert result.processing_time == 2.1

    @pytest.mark.asyncio
    async def test_smart_execute_failure(self, sample_smart_execution_request):
        """Test smart execution failure handling."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connection_manager.with_fallback_to_http = AsyncMock(side_effect=Exception("Execution failed"))

        result = await client.smart_execute(sample_smart_execution_request)

        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert result.error == "Execution failed"

    @pytest.mark.asyncio
    async def test_list_models_success(self, sample_model_list_request):
        """Test successful model listing."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        expected_result = {
            "success": True,
            "models": ["claude-3-5-sonnet", "gpt-4-turbo"],
            "metadata": {"user_tier": "premium"},
            "processing_time": 0.3,
        }
        client.connection_manager.with_fallback_to_http = AsyncMock(return_value=(expected_result, True))

        result = await client.list_models(sample_model_list_request)

        assert isinstance(result, ModelListResult)
        assert result.success is True
        assert any(model["name"] == "claude-3-5-sonnet" for model in result.models)
        assert any(model["name"] == "gpt-4-turbo" for model in result.models)
        assert result.processing_time == 0.3

    @pytest.mark.asyncio
    async def test_list_models_failure(self, sample_model_list_request):
        """Test model listing failure handling."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connection_manager.with_fallback_to_http = AsyncMock(side_effect=Exception("Listing failed"))

        result = await client.list_models(sample_model_list_request)

        assert isinstance(result, ModelListResult)
        assert result.success is False
        assert result.error == "Listing failed"

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Set up connected state
        client.connected = True
        client.current_process = Mock()
        client.retry_handler.with_retry = AsyncMock(return_value={"content": "Tool response"})

        result = await client.call_tool("test_tool", {"arg": "value"})

        assert result == {"content": "Tool response"}

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        """Test tool call when not connected."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        with pytest.raises(Exception, match="Not connected"):
            await client.call_tool("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_send_mcp_request_success(self, mock_uuid):
        """Test successful MCP request sending."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock process
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.flush = Mock()

        mock_zen_process = Mock()
        mock_zen_process.process = mock_process
        client.current_process = mock_zen_process

        # Mock response reading
        client._read_response = AsyncMock(
            return_value='{"jsonrpc": "2.0", "id": "test-request-id", "result": {"content": "test"}}',
        )

        result = await client._send_mcp_request("test_tool", {"arg": "value"})

        assert result == {"content": "test"}

    @pytest.mark.asyncio
    async def test_send_mcp_request_no_process(self):
        """Test MCP request with no active process."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.current_process = None

        with pytest.raises(Exception, match="No active server process"):
            await client._send_mcp_request("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_send_mcp_request_timeout(self, mock_uuid):
        """Test MCP request timeout handling."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_zen_process = Mock()
        mock_zen_process.process = mock_process
        client.current_process = mock_zen_process

        # Mock timeout
        client._read_response = AsyncMock(side_effect=TimeoutError())

        with pytest.raises(Exception, match="MCP request timeout"):
            await client._send_mcp_request("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_send_mcp_request_json_error(self, mock_uuid):
        """Test MCP request JSON parsing error."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_zen_process = Mock()
        mock_zen_process.process = mock_process
        client.current_process = mock_zen_process

        # Mock invalid JSON response
        client._read_response = AsyncMock(return_value="invalid json")

        with pytest.raises(Exception, match="Invalid JSON"):
            await client._send_mcp_request("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_send_mcp_request_mcp_error(self, mock_uuid):
        """Test MCP request with server error response."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_zen_process = Mock()
        mock_zen_process.process = mock_process
        client.current_process = mock_zen_process

        # Mock error response
        client._read_response = AsyncMock(
            return_value='{"jsonrpc": "2.0", "id": "test-request-id", "error": {"code": 500, "message": "Server error"}}',
        )

        with pytest.raises(Exception, match="MCP error 500: Server error"):
            await client._send_mcp_request("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_read_response_success(self, mock_event_loop):
        """Test successful response reading."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.stdout = Mock()

        response = await client._read_response(mock_process, "test-id")

        assert "test response" in response

    @pytest.mark.asyncio
    async def test_read_response_no_stdout(self):
        """Test response reading with no stdout."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.stdout = None

        with pytest.raises(Exception, match="Process stdout not available"):
            await client._read_response(mock_process, "test-id")

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.call_tool = AsyncMock(return_value={"models": ["flash"]})

        result = await client._test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection test failure."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.call_tool = AsyncMock(side_effect=Exception("Connection test failed"))

        result = await client._test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check(self, health_check_result):
        """Test health check delegation."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connection_manager.health_check = AsyncMock(return_value=health_check_result)

        result = await client.health_check()

        assert result == health_check_result
        client.connection_manager.health_check.assert_called_once_with(client)

    def test_get_connection_status_with_process(self, connection_status):
        """Test connection status with active process."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.get_status.return_value = connection_status
        client.current_process = mock_process
        client.connected = True

        result = client.get_connection_status()

        assert result.connected is True

    def test_get_connection_status_no_process(self):
        """Test connection status without active process."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.current_process = None

        result = client.get_connection_status()

        assert result.connected is False

    def test_get_metrics(self, bridge_metrics):
        """Test metrics retrieval."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connection_manager.get_metrics = Mock(return_value=bridge_metrics)

        result = client.get_metrics()

        assert result == bridge_metrics

    def test_is_connected_true(self):
        """Test is_connected when connected."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.is_running.return_value = True
        client.connected = True
        client.current_process = mock_process

        assert client.is_connected() is True

    def test_is_connected_false(self):
        """Test is_connected when not connected."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        client.connected = False
        client.current_process = None

        assert client.is_connected() is False

    def test_is_connected_process_not_running(self):
        """Test is_connected when process stopped."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        mock_process = Mock()
        mock_process.is_running.return_value = False
        client.connected = True
        client.current_process = mock_process

        assert client.is_connected() is False

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_subprocess):
        """Test async context manager functionality."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock successful connection and disconnection
        client.connect = AsyncMock(return_value=True)
        client.disconnect = AsyncMock()

        async with client as ctx_client:
            assert ctx_client is client
            client.connect.assert_called_once()

        client.disconnect.assert_called_once()


class TestCreateClientFunction:
    """Test the create_client convenience function."""

    @pytest.mark.asyncio
    async def test_create_client_default_parameters(self):
        """Test create_client with default parameters."""
        with patch.object(ZenMCPStdioClient, "connect") as mock_connect:
            mock_connect.return_value = AsyncMock()

            client = await create_client()

            assert isinstance(client, ZenMCPStdioClient)
            assert client.connection_config.server_path == "./server.py"
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_client_custom_parameters(self):
        """Test create_client with custom parameters."""
        with patch.object(ZenMCPStdioClient, "connect") as mock_connect:
            mock_connect.return_value = AsyncMock()

            client = await create_client(
                server_path="./custom_server.py",
                env_vars={"CUSTOM": "value"},
                http_fallback_url="http://custom:9000",
            )

            assert isinstance(client, ZenMCPStdioClient)
            assert client.connection_config.server_path == "./custom_server.py"
            assert client.connection_config.env_vars["CUSTOM"] == "value"
            mock_connect.assert_called_once()


class TestClientEdgeCases:
    """Test edge cases and error conditions."""

    def test_client_initialization_none_fallback_config(self):
        """Test client initialization with None fallback config."""
        client = ZenMCPStdioClient(
            server_path="./test_server.py",
            fallback_config=None,
        )

        # Should create default fallback config
        assert client.connection_manager is not None

    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections(self):
        """Test handling of multiple concurrent connection attempts."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock process pool
        mock_process = Mock()
        mock_process.is_running.return_value = True
        client.process_pool.get_process = AsyncMock(return_value=mock_process)
        client._test_connection = AsyncMock(return_value=True)

        # Run multiple connections concurrently
        tasks = [client.connect() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All should succeed, but only one actual connection
        assert all(results)
        assert client.connected is True

    @pytest.mark.asyncio
    async def test_disconnect_while_not_connected(self):
        """Test disconnect when not connected."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Should not raise error
        await client.disconnect()

        assert client.connected is False

    @pytest.mark.asyncio
    async def test_operations_with_various_request_types(self):
        """Test operations with different request parameter types."""
        client = ZenMCPStdioClient(server_path="./test_server.py")

        # Mock the fallback mechanism
        client.connection_manager.with_fallback_to_http = AsyncMock(return_value=({"success": True}, True))

        # Test with minimal request
        minimal_request = RouteAnalysisRequest(prompt="test", user_tier="free")
        result = await client.analyze_route(minimal_request)
        assert result.success is True

        # Test with dict conversion
        request_dict = minimal_request.dict()
        assert "prompt" in request_dict
