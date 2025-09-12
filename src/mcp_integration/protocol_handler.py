"""
MCP Protocol Handler

Implementation of JSON-RPC 2.0 message handling for the Model Context Protocol (MCP).
Provides message serialization, deserialization, and protocol-level communication
for MCP server interactions.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from typing import Any
import uuid

from src.utils.logging_mixin import LoggerMixin


logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types based on JSON-RPC 2.0 specification."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPRequest:
    """MCP JSON-RPC 2.0 request message."""

    jsonrpc: str = "2.0"
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class MCPResponse:
    """MCP JSON-RPC 2.0 response message."""

    jsonrpc: str = "2.0"
    result: Any = None
    id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "jsonrpc": self.jsonrpc,
            "result": self.result,
            "id": self.id,
        }


@dataclass
class MCPError:
    """MCP JSON-RPC 2.0 error message."""

    jsonrpc: str = "2.0"
    error: dict[str, Any] = field(default_factory=dict)
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "error": self.error,
        }
        if self.id is not None:
            result["id"] = self.id
        return result


@dataclass
class MCPNotification:
    """MCP JSON-RPC 2.0 notification message."""

    jsonrpc: str = "2.0"
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)


class MCPProtocolError(Exception):
    """Base exception for MCP protocol errors."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


class MCPStandardErrors:
    """Standard JSON-RPC 2.0 error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000


class MCPProtocolHandler(LoggerMixin):
    """Handles MCP protocol messages and communication."""

    def __init__(self) -> None:
        super().__init__()
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.request_timeout = 30.0  # seconds

    def create_request(self, method: str, params: dict[str, Any] | None = None) -> MCPRequest:
        """Create a new MCP request message.

        Args:
            method: MCP method name
            params: Request parameters

        Returns:
            MCPRequest object with unique ID
        """
        return MCPRequest(
            method=method,
            params=params or {},
            id=str(uuid.uuid4()),
        )

    def create_response(self, request_id: str, result: Any) -> MCPResponse:
        """Create a response to an MCP request.

        Args:
            request_id: ID of the original request
            result: Response data

        Returns:
            MCPResponse object
        """
        return MCPResponse(id=request_id, result=result)

    def create_error(self, request_id: str | None, code: int, message: str, data: Any = None) -> MCPError:
        """Create an MCP error response.

        Args:
            request_id: ID of the original request (None for notifications)
            code: Error code
            message: Error message
            data: Additional error data

        Returns:
            MCPError object
        """
        return MCPError(
            id=request_id,
            error={
                "code": code,
                "message": message,
                "data": data,
            },
        )

    def create_notification(self, method: str, params: dict[str, Any] | None = None) -> MCPNotification:
        """Create an MCP notification message.

        Args:
            method: Notification method name
            params: Notification parameters

        Returns:
            MCPNotification object
        """
        return MCPNotification(method=method, params=params or {})

    def serialize_message(self, message: MCPRequest | MCPResponse | MCPError | MCPNotification) -> str:
        """Serialize an MCP message to JSON string.

        Args:
            message: Message object to serialize

        Returns:
            JSON string representation
        """
        try:
            if isinstance(message, MCPRequest):
                data = {
                    "jsonrpc": message.jsonrpc,
                    "method": message.method,
                    "params": message.params,
                    "id": message.id,
                }
            elif isinstance(message, (MCPResponse, MCPError)):
                data = message.to_dict()
            elif isinstance(message, MCPNotification):
                data = {
                    "jsonrpc": message.jsonrpc,
                    "method": message.method,
                    "params": message.params,
                }
            else:
                raise ValueError(f"Unknown message type: {type(message)}")

            return json.dumps(data, separators=(",", ":"))

        except Exception as e:
            self.logger.error(f"Failed to serialize message: {e}")
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR,
                f"Message serialization failed: {e!s}",
            )

    def deserialize_message(self, message_str: str) -> MCPRequest | MCPResponse | MCPError | MCPNotification:
        """Deserialize JSON string to MCP message object.

        Args:
            message_str: JSON string to deserialize

        Returns:
            Appropriate message object
        """
        try:
            data = json.loads(message_str)

            # Validate JSON-RPC 2.0 format
            if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_REQUEST,
                    "Invalid JSON-RPC 2.0 format",
                )

            # Determine message type and create appropriate object
            if "method" in data:
                if "id" in data:
                    # Request
                    return MCPRequest(
                        method=data["method"],
                        params=data.get("params", {}),
                        id=data["id"],
                    )
                # Notification
                return MCPNotification(
                    method=data["method"],
                    params=data.get("params", {}),
                )
            if "result" in data:
                # Response
                return MCPResponse(
                    result=data["result"],
                    id=data.get("id", ""),
                )
            if "error" in data:
                # Error
                return MCPError(
                    error=data["error"],
                    id=data.get("id"),
                )
            raise MCPProtocolError(
                MCPStandardErrors.INVALID_REQUEST,
                "Message does not contain required fields",
            )

        except json.JSONDecodeError as e:
            raise MCPProtocolError(
                MCPStandardErrors.PARSE_ERROR,
                f"JSON parsing failed: {e!s}",
            )
        except Exception as e:
            if isinstance(e, MCPProtocolError):
                raise
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR,
                f"Message deserialization failed: {e!s}",
            )

    async def send_request(self, writer: asyncio.StreamWriter, request: MCPRequest) -> Any:
        """Send an MCP request and wait for response.

        Args:
            writer: AsyncIO stream writer
            request: MCP request to send

        Returns:
            Response result data
        """
        # Create future for response
        future: asyncio.Future[Any] = asyncio.Future()
        self.pending_requests[request.id] = future

        try:
            # Serialize and send request
            message_str = self.serialize_message(request)
            self.logger.debug(f"Sending MCP request: {request.method} (ID: {request.id})")

            writer.write((message_str + "\n").encode())
            await writer.drain()

            # Wait for response with timeout
            return await asyncio.wait_for(future, timeout=self.request_timeout)

        except TimeoutError:
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR,
                f"Request timeout after {self.request_timeout}s",
            )
        except Exception as e:
            self.logger.error(f"Failed to send request {request.id}: {e}")
            raise
        finally:
            # Clean up pending request
            self.pending_requests.pop(request.id, None)

    def send_notification(self, writer: asyncio.StreamWriter, notification: MCPNotification) -> None:
        """Send an MCP notification (no response expected).

        Args:
            writer: AsyncIO stream writer
            notification: MCP notification to send
        """
        try:
            message_str = self.serialize_message(notification)
            self.logger.debug(f"Sending MCP notification: {notification.method}")

            writer.write((message_str + "\n").encode())
            # Note: We don't await drain() for notifications to avoid blocking

        except Exception as e:
            self.logger.error(f"Failed to send notification {notification.method}: {e}")
            raise

    def send_response(self, writer: asyncio.StreamWriter, response: MCPResponse | MCPError) -> None:
        """Send an MCP response or error.

        Args:
            writer: AsyncIO stream writer
            response: MCP response or error to send
        """
        try:
            message_str = self.serialize_message(response)
            response_type = "response" if isinstance(response, MCPResponse) else "error"
            self.logger.debug(f"Sending MCP {response_type} (ID: {response.id})")

            writer.write((message_str + "\n").encode())
            # Note: We don't await drain() for responses to avoid blocking

        except Exception as e:
            self.logger.error(f"Failed to send {response_type}: {e}")
            raise

    def handle_response(self, response: MCPResponse | MCPError) -> None:
        """Handle incoming response or error message.

        Args:
            response: Response or error message
        """
        request_id = response.id
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]

            if isinstance(response, MCPResponse):
                self.logger.debug(f"Received response for request {request_id}")
                future.set_result(response.result)
            elif isinstance(response, MCPError):
                self.logger.warning(f"Received error for request {request_id}: {response.error}")
                error = MCPProtocolError(
                    response.error.get("code", MCPStandardErrors.INTERNAL_ERROR),
                    response.error.get("message", "Unknown error"),
                    response.error.get("data"),
                )
                future.set_exception(error)
        else:
            self.logger.warning(f"Received response for unknown request ID: {request_id}")

    def get_message_type(self, message: MCPRequest | MCPResponse | MCPError | MCPNotification) -> MCPMessageType:
        """Get the type of an MCP message.

        Args:
            message: Message to classify

        Returns:
            Message type enum
        """
        if isinstance(message, MCPRequest):
            return MCPMessageType.REQUEST
        if isinstance(message, MCPResponse):
            return MCPMessageType.RESPONSE
        if isinstance(message, MCPError):
            return MCPMessageType.ERROR
        if isinstance(message, MCPNotification):
            return MCPMessageType.NOTIFICATION
        raise ValueError(f"Unknown message type: {type(message)}")


class MCPMethodRegistry:
    """Registry for MCP method handlers."""

    def __init__(self) -> None:
        self.handlers: dict[str, Callable] = {}
        self.logger = logging.getLogger(f"{__name__}.MCPMethodRegistry")

    def register_handler(self, method: str, handler: Callable) -> None:
        """Register a handler for an MCP method.

        Args:
            method: MCP method name
            handler: Async callable to handle the method
        """
        self.handlers[method] = handler
        self.logger.debug(f"Registered handler for method: {method}")

    def get_handler(self, method: str) -> Callable | None:
        """Get handler for an MCP method.

        Args:
            method: MCP method name

        Returns:
            Handler function or None if not found
        """
        return self.handlers.get(method)

    def list_methods(self) -> list[str]:
        """Get list of registered method names.

        Returns:
            List of method names
        """
        return list(self.handlers.keys())

    async def handle_request(self, request: MCPRequest) -> MCPResponse | MCPError:
        """Handle an MCP request using registered handlers.

        Args:
            request: MCP request to handle

        Returns:
            Response or error message
        """
        handler = self.get_handler(request.method)

        if not handler:
            return MCPError(
                id=request.id,
                error={
                    "code": MCPStandardErrors.METHOD_NOT_FOUND,
                    "message": f"Method not found: {request.method}",
                },
            )

        try:
            result = await handler(request.params)
            return MCPResponse(id=request.id, result=result)

        except Exception as e:
            self.logger.error(f"Handler error for {request.method}: {e}")
            return MCPError(
                id=request.id,
                error={
                    "code": MCPStandardErrors.INTERNAL_ERROR,
                    "message": f"Handler error: {e!s}",
                },
            )
