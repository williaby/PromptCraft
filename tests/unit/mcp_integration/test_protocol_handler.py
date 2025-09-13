"""
Tests for MCP Protocol Handler
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_integration.protocol_handler import (
    MCPError,
    MCPMessageType,
    MCPMethodRegistry,
    MCPNotification,
    MCPProtocolError,
    MCPProtocolHandler,
    MCPRequest,
    MCPResponse,
    MCPStandardErrors,
)


class TestMCPDataClasses:
    """Test MCP data classes."""

    def test_mcp_request_default_values(self):
        """Test MCPRequest with default values."""
        request = MCPRequest()

        assert request.jsonrpc == "2.0"
        assert request.method == ""
        assert request.params == {}
        assert isinstance(request.id, str)
        assert len(request.id) > 0

    def test_mcp_request_custom_values(self):
        """Test MCPRequest with custom values."""
        params = {"key": "value"}
        request = MCPRequest(method="test_method", params=params, id="test_id")

        assert request.jsonrpc == "2.0"
        assert request.method == "test_method"
        assert request.params == params
        assert request.id == "test_id"

    def test_mcp_response_default_values(self):
        """Test MCPResponse with default values."""
        response = MCPResponse()

        assert response.jsonrpc == "2.0"
        assert response.result is None
        assert response.id == ""

    def test_mcp_response_to_dict(self):
        """Test MCPResponse to_dict method."""
        response = MCPResponse(result={"data": "test"}, id="test_id")
        result = response.to_dict()

        expected = {
            "jsonrpc": "2.0",
            "result": {"data": "test"},
            "id": "test_id",
        }
        assert result == expected

    def test_mcp_error_default_values(self):
        """Test MCPError with default values."""
        error = MCPError()

        assert error.jsonrpc == "2.0"
        assert error.error == {}
        assert error.id is None

    def test_mcp_error_to_dict_with_id(self):
        """Test MCPError to_dict method with ID."""
        error_data = {"code": -32600, "message": "Invalid Request"}
        error = MCPError(error=error_data, id="test_id")
        result = error.to_dict()

        expected = {
            "jsonrpc": "2.0",
            "error": error_data,
            "id": "test_id",
        }
        assert result == expected

    def test_mcp_error_to_dict_without_id(self):
        """Test MCPError to_dict method without ID."""
        error_data = {"code": -32600, "message": "Invalid Request"}
        error = MCPError(error=error_data)
        result = error.to_dict()

        expected = {
            "jsonrpc": "2.0",
            "error": error_data,
        }
        assert result == expected

    def test_mcp_notification_default_values(self):
        """Test MCPNotification with default values."""
        notification = MCPNotification()

        assert notification.jsonrpc == "2.0"
        assert notification.method == ""
        assert notification.params == {}


class TestMCPProtocolError:
    """Test MCP protocol error class."""

    def test_protocol_error_creation(self):
        """Test MCPProtocolError creation."""
        error = MCPProtocolError(code=-32600, message="Invalid Request", data="test_data")

        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data == "test_data"
        assert str(error) == "MCP Error -32600: Invalid Request"

    def test_protocol_error_without_data(self):
        """Test MCPProtocolError without data."""
        error = MCPProtocolError(code=-32700, message="Parse error")

        assert error.code == -32700
        assert error.message == "Parse error"
        assert error.data is None


class TestMCPStandardErrors:
    """Test MCP standard error codes."""

    def test_standard_error_codes(self):
        """Test standard error code values."""
        assert MCPStandardErrors.PARSE_ERROR == -32700
        assert MCPStandardErrors.INVALID_REQUEST == -32600
        assert MCPStandardErrors.METHOD_NOT_FOUND == -32601
        assert MCPStandardErrors.INVALID_PARAMS == -32602
        assert MCPStandardErrors.INTERNAL_ERROR == -32603
        assert MCPStandardErrors.SERVER_ERROR_START == -32099
        assert MCPStandardErrors.SERVER_ERROR_END == -32000


class TestMCPProtocolHandler:
    """Test MCP protocol handler."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler()

    def test_handler_initialization(self, handler):
        """Test protocol handler initialization."""
        assert isinstance(handler.pending_requests, dict)
        assert len(handler.pending_requests) == 0
        assert handler.request_timeout == 30.0
        assert hasattr(handler, "logger")

    def test_create_request(self, handler):
        """Test creating MCP request."""
        method = "test_method"
        params = {"key": "value"}

        request = handler.create_request(method, params)

        assert isinstance(request, MCPRequest)
        assert request.method == method
        assert request.params == params
        assert request.jsonrpc == "2.0"
        assert isinstance(request.id, str)
        assert len(request.id) > 0

    def test_create_request_without_params(self, handler):
        """Test creating MCP request without parameters."""
        request = handler.create_request("test_method")

        assert request.method == "test_method"
        assert request.params == {}

    def test_create_response(self, handler):
        """Test creating MCP response."""
        request_id = "test_id"
        result = {"data": "test"}

        response = handler.create_response(request_id, result)

        assert isinstance(response, MCPResponse)
        assert response.id == request_id
        assert response.result == result
        assert response.jsonrpc == "2.0"

    def test_create_error(self, handler):
        """Test creating MCP error."""
        request_id = "test_id"
        code = -32600
        message = "Invalid Request"
        data = "test_data"

        error = handler.create_error(request_id, code, message, data)

        assert isinstance(error, MCPError)
        assert error.id == request_id
        assert error.error["code"] == code
        assert error.error["message"] == message
        assert error.error["data"] == data

    def test_create_error_without_data(self, handler):
        """Test creating MCP error without data."""
        error = handler.create_error("test_id", -32700, "Parse error")

        assert error.error["code"] == -32700
        assert error.error["message"] == "Parse error"
        assert error.error["data"] is None

    def test_create_notification(self, handler):
        """Test creating MCP notification."""
        method = "test_notification"
        params = {"key": "value"}

        notification = handler.create_notification(method, params)

        assert isinstance(notification, MCPNotification)
        assert notification.method == method
        assert notification.params == params
        assert notification.jsonrpc == "2.0"

    def test_create_notification_without_params(self, handler):
        """Test creating MCP notification without parameters."""
        notification = handler.create_notification("test_method")

        assert notification.method == "test_method"
        assert notification.params == {}


class TestMessageSerialization:
    """Test message serialization."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler()

    def test_serialize_request(self, handler):
        """Test serializing MCP request."""
        request = MCPRequest(method="test", params={"key": "value"}, id="123")

        result = handler.serialize_message(request)
        data = json.loads(result)

        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "test"
        assert data["params"] == {"key": "value"}
        assert data["id"] == "123"

    def test_serialize_response(self, handler):
        """Test serializing MCP response."""
        response = MCPResponse(result={"data": "test"}, id="123")

        result = handler.serialize_message(response)
        data = json.loads(result)

        assert data["jsonrpc"] == "2.0"
        assert data["result"] == {"data": "test"}
        assert data["id"] == "123"

    def test_serialize_error(self, handler):
        """Test serializing MCP error."""
        error = MCPError(
            error={"code": -32600, "message": "Invalid Request"},
            id="123",
        )

        result = handler.serialize_message(error)
        data = json.loads(result)

        assert data["jsonrpc"] == "2.0"
        assert data["error"]["code"] == -32600
        assert data["error"]["message"] == "Invalid Request"
        assert data["id"] == "123"

    def test_serialize_notification(self, handler):
        """Test serializing MCP notification."""
        notification = MCPNotification(method="test", params={"key": "value"})

        result = handler.serialize_message(notification)
        data = json.loads(result)

        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "test"
        assert data["params"] == {"key": "value"}
        assert "id" not in data

    def test_serialize_unknown_message_type(self, handler):
        """Test serializing unknown message type."""
        with pytest.raises(MCPProtocolError) as exc_info:
            handler.serialize_message("invalid")

        assert exc_info.value.code == MCPStandardErrors.INTERNAL_ERROR
        assert "Message serialization failed" in exc_info.value.message


class TestMessageDeserialization:
    """Test message deserialization."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler()

    def test_deserialize_request(self, handler):
        """Test deserializing MCP request."""
        data = {
            "jsonrpc": "2.0",
            "method": "test",
            "params": {"key": "value"},
            "id": "123",
        }
        message_str = json.dumps(data)

        result = handler.deserialize_message(message_str)

        assert isinstance(result, MCPRequest)
        assert result.method == "test"
        assert result.params == {"key": "value"}
        assert result.id == "123"

    def test_deserialize_notification(self, handler):
        """Test deserializing MCP notification."""
        data = {
            "jsonrpc": "2.0",
            "method": "test",
            "params": {"key": "value"},
        }
        message_str = json.dumps(data)

        result = handler.deserialize_message(message_str)

        assert isinstance(result, MCPNotification)
        assert result.method == "test"
        assert result.params == {"key": "value"}

    def test_deserialize_response(self, handler):
        """Test deserializing MCP response."""
        data = {
            "jsonrpc": "2.0",
            "result": {"data": "test"},
            "id": "123",
        }
        message_str = json.dumps(data)

        result = handler.deserialize_message(message_str)

        assert isinstance(result, MCPResponse)
        assert result.result == {"data": "test"}
        assert result.id == "123"

    def test_deserialize_error(self, handler):
        """Test deserializing MCP error."""
        data = {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": "123",
        }
        message_str = json.dumps(data)

        result = handler.deserialize_message(message_str)

        assert isinstance(result, MCPError)
        assert result.error["code"] == -32600
        assert result.error["message"] == "Invalid Request"
        assert result.id == "123"

    def test_deserialize_invalid_json(self, handler):
        """Test deserializing invalid JSON."""
        with pytest.raises(MCPProtocolError) as exc_info:
            handler.deserialize_message("invalid json")

        assert exc_info.value.code == MCPStandardErrors.PARSE_ERROR
        assert "JSON parsing failed" in exc_info.value.message

    def test_deserialize_invalid_jsonrpc(self, handler):
        """Test deserializing invalid JSON-RPC format."""
        data = {"jsonrpc": "1.0", "method": "test"}
        message_str = json.dumps(data)

        with pytest.raises(MCPProtocolError) as exc_info:
            handler.deserialize_message(message_str)

        assert exc_info.value.code == MCPStandardErrors.INVALID_REQUEST
        assert "Invalid JSON-RPC 2.0 format" in exc_info.value.message

    def test_deserialize_missing_required_fields(self, handler):
        """Test deserializing message with missing required fields."""
        data = {"jsonrpc": "2.0"}
        message_str = json.dumps(data)

        with pytest.raises(MCPProtocolError) as exc_info:
            handler.deserialize_message(message_str)

        assert exc_info.value.code == MCPStandardErrors.INVALID_REQUEST
        assert "Message does not contain required fields" in exc_info.value.message


class TestAsyncCommunication:
    """Test async communication methods."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler()

    @pytest.mark.asyncio
    async def test_send_request_success(self, handler):
        """Test sending request successfully."""
        # Mock writer
        writer = AsyncMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        # Create request
        request = MCPRequest(method="test", id="123")

        # Mock future resolution
        async def mock_wait_for(future, timeout):
            future.set_result({"result": "success"})
            return {"result": "success"}

        with patch("asyncio.wait_for", side_effect=mock_wait_for):
            result = await handler.send_request(writer, request)

        assert result == {"result": "success"}
        assert writer.write.called
        assert writer.drain.called
        assert request.id not in handler.pending_requests

    @pytest.mark.asyncio
    async def test_send_request_timeout(self, handler):
        """Test request timeout."""
        writer = AsyncMock()
        request = MCPRequest(method="test", id="123")

        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(MCPProtocolError) as exc_info:
                await handler.send_request(writer, request)

        assert exc_info.value.code == MCPStandardErrors.INTERNAL_ERROR
        assert "Request timeout" in exc_info.value.message
        assert request.id not in handler.pending_requests

    def test_send_notification(self, handler):
        """Test sending notification."""
        writer = MagicMock()
        notification = MCPNotification(method="test_notification")

        handler.send_notification(writer, notification)

        assert writer.write.called
        call_args = writer.write.call_args[0][0]
        assert b"test_notification" in call_args

    def test_send_response(self, handler):
        """Test sending response."""
        writer = MagicMock()
        response = MCPResponse(result={"data": "test"}, id="123")

        handler.send_response(writer, response)

        assert writer.write.called
        call_args = writer.write.call_args[0][0]
        assert b'"result":{"data":"test"}' in call_args

    def test_send_error_response(self, handler):
        """Test sending error response."""
        writer = MagicMock()
        error = MCPError(
            error={"code": -32600, "message": "Invalid Request"},
            id="123",
        )

        handler.send_response(writer, error)

        assert writer.write.called
        call_args = writer.write.call_args[0][0]
        assert b'"error":{"code":-32600' in call_args


class TestResponseHandling:
    """Test response handling."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler()

    def test_handle_response_success(self, handler):
        """Test handling successful response."""
        # Create pending request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            future = asyncio.Future()
            handler.pending_requests["123"] = future

            # Handle response
            response = MCPResponse(result={"data": "test"}, id="123")
            handler.handle_response(response)

            assert future.done()
            assert future.result() == {"data": "test"}
            # Note: handle_response doesn't remove from pending_requests - that's done in send_request
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_handle_error_response(self, handler):
        """Test handling error response."""
        # Create pending request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            future = asyncio.Future()
            handler.pending_requests["123"] = future

            # Handle error
            error = MCPError(
                error={"code": -32600, "message": "Invalid Request"},
                id="123",
            )
            handler.handle_response(error)

            assert future.done()
            assert future.exception() is not None
            assert isinstance(future.exception(), MCPProtocolError)
            assert future.exception().code == -32600
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_handle_response_unknown_id(self, handler, caplog):
        """Test handling response with unknown ID."""
        response = MCPResponse(result={"data": "test"}, id="unknown")

        handler.handle_response(response)

        assert "unknown request ID" in caplog.text


class TestMessageTypeDetection:
    """Test message type detection."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler()

    def test_get_message_type_request(self, handler):
        """Test getting request message type."""
        request = MCPRequest(method="test")
        result = handler.get_message_type(request)
        assert result == MCPMessageType.REQUEST

    def test_get_message_type_response(self, handler):
        """Test getting response message type."""
        response = MCPResponse(result={})
        result = handler.get_message_type(response)
        assert result == MCPMessageType.RESPONSE

    def test_get_message_type_error(self, handler):
        """Test getting error message type."""
        error = MCPError(error={})
        result = handler.get_message_type(error)
        assert result == MCPMessageType.ERROR

    def test_get_message_type_notification(self, handler):
        """Test getting notification message type."""
        notification = MCPNotification(method="test")
        result = handler.get_message_type(notification)
        assert result == MCPMessageType.NOTIFICATION

    def test_get_message_type_unknown(self, handler):
        """Test getting unknown message type."""
        with pytest.raises(ValueError, match="Unknown message type"):
            handler.get_message_type("invalid")


class TestMCPMethodRegistry:
    """Test MCP method registry."""

    @pytest.fixture
    def registry(self):
        """Create method registry fixture."""
        return MCPMethodRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert isinstance(registry.handlers, dict)
        assert len(registry.handlers) == 0
        assert hasattr(registry, "logger")

    def test_register_handler(self, registry):
        """Test registering method handler."""

        async def test_handler(params):
            return {"result": "test"}

        registry.register_handler("test_method", test_handler)

        assert "test_method" in registry.handlers
        assert registry.handlers["test_method"] == test_handler

    def test_get_handler_exists(self, registry):
        """Test getting existing handler."""

        async def test_handler(params):
            return {"result": "test"}

        registry.register_handler("test_method", test_handler)
        handler = registry.get_handler("test_method")

        assert handler == test_handler

    def test_get_handler_not_exists(self, registry):
        """Test getting non-existent handler."""
        handler = registry.get_handler("nonexistent")
        assert handler is None

    def test_list_methods(self, registry):
        """Test listing registered methods."""

        async def handler1(params):
            pass

        async def handler2(params):
            pass

        registry.register_handler("method1", handler1)
        registry.register_handler("method2", handler2)

        methods = registry.list_methods()
        assert set(methods) == {"method1", "method2"}

    @pytest.mark.asyncio
    async def test_handle_request_success(self, registry):
        """Test handling request successfully."""

        async def test_handler(params):
            return {"result": params.get("input", "default")}

        registry.register_handler("test_method", test_handler)
        request = MCPRequest(
            method="test_method",
            params={"input": "test_data"},
            id="123",
        )

        response = await registry.handle_request(request)

        assert isinstance(response, MCPResponse)
        assert response.id == "123"
        assert response.result == {"result": "test_data"}

    @pytest.mark.asyncio
    async def test_handle_request_method_not_found(self, registry):
        """Test handling request for non-existent method."""
        request = MCPRequest(method="nonexistent", id="123")

        response = await registry.handle_request(request)

        assert isinstance(response, MCPError)
        assert response.id == "123"
        assert response.error["code"] == MCPStandardErrors.METHOD_NOT_FOUND
        assert "Method not found" in response.error["message"]

    @pytest.mark.asyncio
    async def test_handle_request_handler_error(self, registry):
        """Test handling request when handler raises exception."""

        async def failing_handler(params):
            raise ValueError("Test error")

        registry.register_handler("failing_method", failing_handler)
        request = MCPRequest(method="failing_method", id="123")

        response = await registry.handle_request(request)

        assert isinstance(response, MCPError)
        assert response.id == "123"
        assert response.error["code"] == MCPStandardErrors.INTERNAL_ERROR
        assert "Handler error" in response.error["message"]
