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
        data = {"jsonrpc": "2.0", "id": self.id, "method": self.method}
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
        data = {"jsonrpc": "2.0", "id": self.id}
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
        data = {"jsonrpc": "2.0", "method": self.method}
        if self.params is not None:
            data["params"] = self.params
        return data


class MCPMethodRegistry:
    """Registry for MCP method handlers."""

    def __init__(self) -> None:
        self.methods: dict[str, Any] = {}

    def register(self, method: str, handler: Any) -> None:
        """Register a method handler."""
        self.methods[method] = handler

    def get_handler(self, method: str) -> Any:
        """Get handler for a method."""
        return self.methods.get(method)

    def list_methods(self) -> list[str]:
        """List all registered methods."""
        return list(self.methods.keys())


class MCPProtocolHandler:
    """MCP protocol message handler."""

    def __init__(self) -> None:
        self.registry = MCPMethodRegistry()
        self.running = False

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
                return MCPResponse(
                    id=data["id"],
                    error={"code": MCPStandardErrors.INTERNAL_ERROR.value, "message": str(e)},
                ).to_dict()
            raise

    async def _handle_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """Handle a request message."""
        method = data.get("method")
        if method is None:
            return MCPResponse(
                id=data.get("id", "unknown"),
                error={"code": MCPStandardErrors.INVALID_REQUEST.value, "message": "Missing method"},
            ).to_dict()
        handler = self.registry.get_handler(method)

        if handler is None:
            return MCPResponse(
                id=data["id"],
                error={"code": MCPStandardErrors.METHOD_NOT_FOUND.value, "message": f"Method {method} not found"},
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
            return MCPResponse(
                id=data["id"],
                error={"code": MCPStandardErrors.INTERNAL_ERROR.value, "message": str(e)},
            ).to_dict()

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
        self.registry.register(method, handler)
