"""
MCP Protocol Handler implementation.

This module provides the MCP (Message Control Protocol) handler for
managing communication with MCP servers.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPStandardErrors(Enum):
    """Standard MCP error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000


@dataclass
class MCPError:
    """MCP error response message."""

    jsonrpc: str = "2.0"
    error: dict[str, Any] = field(default_factory=dict)
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {"jsonrpc": self.jsonrpc, "error": self.error}
        if self.id is not None:
            data["id"] = self.id
        return data


class MCPProtocolError(Exception):
    """MCP protocol-specific error exception."""

    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


@dataclass
class MCPRequest:
    """MCP request message."""

    jsonrpc: str = "2.0"
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"req_{id(object())}")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id, "method": self.method}
        if self.params is not None:
            data["params"] = self.params
        return data


@dataclass
class MCPResponse:
    """MCP response message."""

    jsonrpc: str = "2.0"
    id: str = ""
    result: Any | None = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            data["error"] = self.error
        else:
            data["result"] = self.result
        return data


@dataclass
class MCPNotification:
    """MCP notification message."""

    jsonrpc: str = "2.0"
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.params is not None:
            data["params"] = self.params
        return data


class MCPMethodRegistry:
    """Registry for MCP method handlers."""

    def __init__(self) -> None:
        self.handlers: dict[str, Any] = {}
        self.logger = logger

    def register(self, method: str, handler: Any) -> None:
        """Register a method handler."""
        self.handlers[method] = handler

    def register_handler(self, method: str, handler: Any) -> None:
        """Register a method handler (alias for compatibility)."""
        self.handlers[method] = handler

    def get_handler(self, method: str) -> Any:
        """Get handler for a method."""
        return self.handlers.get(method)

    def list_methods(self) -> list[str]:
        """List all registered methods."""
        return list(self.handlers.keys())

    async def handle_request(self, request: MCPRequest) -> MCPResponse | MCPError:
        """Handle an MCP request."""
        method = request.method
        handler = self.get_handler(method)

        if handler is None:
            return MCPError(
                error={"code": MCPStandardErrors.METHOD_NOT_FOUND.value, "message": f"Method not found: {method}"},
                id=request.id,
            )

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(request.params)
            else:
                result = handler(request.params)

            return MCPResponse(id=request.id, result=result)
        except Exception as e:
            logger.error("Handler error for method %s: %s", method, e)
            return MCPError(
                error={"code": MCPStandardErrors.INTERNAL_ERROR.value, "message": f"Handler error: {e!s}"},
                id=request.id,
            )


class MCPProtocolHandler:
    """MCP protocol message handler."""

    def __init__(self) -> None:
        self.registry = MCPMethodRegistry()
        self.running = False
        self.pending_requests: dict[str, Any] = {}
        self.request_timeout = 30.0
        self.logger = logger

    async def start(self) -> None:
        """Start the protocol handler."""
        self.running = True
        logger.info("MCP protocol handler started")

    async def stop(self) -> None:
        """Stop the protocol handler."""
        self.running = False
        logger.info("MCP protocol handler stopped")

    async def handle_message(self, message: str | dict[str, Any]) -> dict[str, Any] | None:
        """Handle an incoming MCP message."""
        try:
            data = json.loads(message) if isinstance(message, str) else message

            # Determine message type and handle accordingly
            if "id" in data and "method" in data:
                # Request
                return await self._handle_request(data)
            if "id" in data and ("result" in data or "error" in data):
                # Response
                await self._handle_response(data)
                return None
            if "method" in data:
                # Notification
                await self._handle_notification(data)
                return None
            raise MCPProtocolError(MCPStandardErrors.INVALID_REQUEST.value, "Invalid message format")

        except json.JSONDecodeError as e:
            raise MCPProtocolError(MCPStandardErrors.PARSE_ERROR.value, "Failed to parse JSON") from e
        except Exception as e:
            logger.error("Error handling MCP message: %s", e)
            if "id" in locals() and "data" in locals() and "id" in data:
                return self.create_error(data["id"], MCPStandardErrors.INTERNAL_ERROR.value, str(e)).to_dict()
            raise

    async def _handle_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """Handle a request message."""
        method = data.get("method")
        if method is None:
            return self.create_error(
                data.get("id", "unknown"),
                MCPStandardErrors.INVALID_REQUEST.value,
                "Missing method",
            ).to_dict()
        handler = self.registry.get_handler(method)

        if handler is None:
            return self.create_error(
                data["id"],
                MCPStandardErrors.METHOD_NOT_FOUND.value,
                f"Method {method} not found",
            ).to_dict()

        try:
            params = data.get("params", {})
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)

            return MCPResponse(id=data["id"], result=result).to_dict()

        except Exception as e:
            logger.error("Error executing method %s: %s", method, e)
            return self.create_error(data["id"], MCPStandardErrors.INTERNAL_ERROR.value, str(e)).to_dict()

    async def _handle_response(self, data: dict[str, Any]) -> None:
        """Handle a response message."""
        # In a full implementation, this would match responses to pending requests
        logger.debug("Received response: %s", data)

    async def _handle_notification(self, data: dict[str, Any]) -> None:
        """Handle a notification message."""
        method = data.get("method")
        if method is None:
            logger.warning("Notification missing method field")
            return
        params = data.get("params", {})
        handler = self.registry.get_handler(method)

        if handler is not None:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(params)
                else:
                    handler(params)
            except Exception as e:
                logger.error("Error handling notification %s: %s", method, e)
        else:
            logger.warning("No handler for notification method: %s", method)

    def register_method(self, method: str, handler: Any) -> None:
        """Register a method handler."""
        self.registry.register_handler(method, handler)

    def create_request(self, method: str, params: dict[str, Any] | None = None) -> MCPRequest:
        """Create an MCP request."""
        return MCPRequest(method=method, params=params or {})

    def create_response(self, request_id: str, result: Any = None) -> MCPResponse:
        """Create an MCP response."""
        return MCPResponse(id=request_id, result=result)

    def create_error(self, request_id: str, code: int, message: str, data: Any | None = None) -> MCPError:
        """Create an MCP error response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        else:
            error["data"] = None
        return MCPError(error=error, id=request_id)

    def create_notification(self, method: str, params: dict[str, Any] | None = None) -> MCPNotification:
        """Create an MCP notification."""
        return MCPNotification(method=method, params=params or {})

    def serialize_message(self, message: MCPRequest | MCPResponse | MCPError | MCPNotification) -> str:
        """Serialize an MCP message to JSON string."""
        try:
            if hasattr(message, "to_dict"):
                return json.dumps(message.to_dict(), separators=(",", ":"))
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR.value,
                "Message serialization failed: Unknown message type",
            )
        except MCPProtocolError:
            raise
        except Exception as e:
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR.value,
                f"Message serialization failed: {e!s}",
            ) from e

    def deserialize_message(self, message_str: str) -> MCPRequest | MCPResponse | MCPError | MCPNotification:
        """Deserialize JSON string to MCP message."""
        try:
            data = json.loads(message_str)
        except json.JSONDecodeError as e:
            raise MCPProtocolError(MCPStandardErrors.PARSE_ERROR.value, f"JSON parsing failed: {e!s}") from e
        except Exception as e:
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR.value,
                f"Message deserialization failed: {e!s}",
            ) from e

        # Validate JSON-RPC version
        if data.get("jsonrpc") != "2.0":
            raise MCPProtocolError(MCPStandardErrors.INVALID_REQUEST.value, "Invalid JSON-RPC 2.0 format")

        # Determine message type and create appropriate object
        if "method" in data and "id" in data:
            # Request
            return MCPRequest(method=data["method"], params=data.get("params", {}), id=data["id"])
        if "method" in data:
            # Notification
            return MCPNotification(method=data["method"], params=data.get("params", {}))
        if "id" in data and "error" in data:
            # Error response
            return MCPError(error=data["error"], id=data["id"])
        if "id" in data:
            # Success response
            return MCPResponse(result=data.get("result"), id=data["id"])
        raise MCPProtocolError(MCPStandardErrors.INVALID_REQUEST.value, "Message does not contain required fields")

    async def send_request(self, writer: Any, request: MCPRequest) -> Any:
        """Send request and wait for response."""
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request.id] = future

        try:
            # Send request
            message = self.serialize_message(request)
            writer.write(message.encode() + b"\n")
            await writer.drain()

            # Wait for response with timeout
            return await asyncio.wait_for(future, timeout=self.request_timeout)
        except TimeoutError as e:
            raise MCPProtocolError(MCPStandardErrors.INTERNAL_ERROR.value, "Request timeout") from e
        finally:
            # Clean up pending request
            if request.id in self.pending_requests:
                del self.pending_requests[request.id]

    def send_notification(self, writer: Any, notification: MCPNotification) -> None:
        """Send notification (fire and forget)."""
        message = self.serialize_message(notification)
        writer.write(message.encode() + b"\n")

    def send_response(self, writer: Any, response: MCPResponse | MCPError) -> None:
        """Send response or error."""
        message = self.serialize_message(response)
        writer.write(message.encode() + b"\n")

    def handle_response(self, response: MCPResponse | MCPError) -> None:
        """Handle incoming response."""
        request_id = response.id
        if request_id not in self.pending_requests:
            logger.warning("Received response for unknown request ID: %s", request_id)
            return

        future = self.pending_requests[request_id]
        if isinstance(response, MCPError):
            # Set exception for error response
            error = MCPProtocolError(response.error["code"], response.error["message"], response.error.get("data"))
            future.set_exception(error)
        else:
            # Set result for success response
            future.set_result(response.result)

    def get_message_type(self, message: Any) -> MCPMessageType:
        """Get the type of an MCP message."""
        if isinstance(message, MCPRequest):
            return MCPMessageType.REQUEST
        if isinstance(message, MCPResponse):
            return MCPMessageType.RESPONSE
        if isinstance(message, MCPError):
            return MCPMessageType.ERROR
        if isinstance(message, MCPNotification):
            return MCPMessageType.NOTIFICATION
        raise ValueError(f"Unknown message type: {type(message)}")
