from src.utils.datetime_compat import utc_now


"""
MCP Message Router and Dispatcher

Routes MCP protocol messages between clients and servers, handles method dispatch,
and manages bi-directional communication for the Model Context Protocol.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any

from src.utils.logging_mixin import LoggerMixin

from .connection_bridge import ActiveConnection
from .protocol_handler import (
    MCPError,
    MCPMethodRegistry,
    MCPNotification,
    MCPProtocolError,
    MCPProtocolHandler,
    MCPRequest,
    MCPResponse,
    MCPStandardErrors,
)


logger = logging.getLogger(__name__)


@dataclass
class MCPServerInfo:
    """Information about a connected MCP server."""

    name: str
    connection: ActiveConnection
    capabilities: dict[str, Any]
    tools: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    prompts: list[dict[str, Any]]
    last_ping: datetime | None = None


class MCPMessageRouter(LoggerMixin):
    """Routes MCP messages between clients and servers."""

    def __init__(self) -> None:
        super().__init__()
        self.protocol_handler = MCPProtocolHandler()
        self.method_registry = MCPMethodRegistry()
        self.servers: dict[str, MCPServerInfo] = {}
        self.server_streams: dict[str, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}

        # Register standard MCP methods
        self._register_standard_methods()

    def _register_standard_methods(self) -> None:
        """Register standard MCP protocol methods."""
        self.method_registry.register_handler("initialize", self._handle_initialize)
        self.method_registry.register_handler("ping", self._handle_ping)
        self.method_registry.register_handler("tools/list", self._handle_tools_list)
        self.method_registry.register_handler("tools/call", self._handle_tools_call)
        self.method_registry.register_handler("resources/list", self._handle_resources_list)
        self.method_registry.register_handler("resources/read", self._handle_resources_read)
        self.method_registry.register_handler("prompts/list", self._handle_prompts_list)
        self.method_registry.register_handler("prompts/get", self._handle_prompts_get)

    async def connect_server(self, server_name: str, connection: ActiveConnection) -> bool:
        """Connect to an MCP server and establish protocol communication.

        Args:
            server_name: Name of the server to connect
            connection: Active connection to the server

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if connection.connection.type == "npx" and connection.process:
                # For NPX servers, use stdio streams
                reader = asyncio.StreamReader()
                writer_transport, writer_protocol = await asyncio.open_connection(
                    sock=connection.process.stdout,
                )
                writer = writer_protocol.transport

                # Store streams for later use (cast WriteTransport to StreamWriter for compatibility)
                self.server_streams[server_name] = (reader, writer)  # type: ignore[assignment]

                # Initialize the server (cast WriteTransport to StreamWriter for compatibility)
                success = await self._initialize_server(server_name, reader, writer)  # type: ignore[arg-type]
                if success:
                    self.logger.info(f"Successfully connected to MCP server: {server_name}")
                    return True
                self.logger.error(f"Failed to initialize MCP server: {server_name}")
                return False

            if connection.connection.type in ["embedded", "external", "docker"]:
                # For HTTP-based servers, we'll need HTTP-to-MCP bridging
                self.logger.info(f"HTTP-based MCP server connection not yet implemented: {server_name}")
                return False
            self.logger.error(f"Unsupported connection type: {connection.connection.type}")
            return False

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            return False

    async def _initialize_server(
        self, server_name: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bool:
        """Initialize communication with an MCP server.

        Args:
            server_name: Name of the server
            reader: Stream reader for receiving messages
            writer: Stream writer for sending messages

        Returns:
            True if initialization successful
        """
        try:
            # Send initialize request
            initialize_request = self.protocol_handler.create_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {},
                    },
                    "clientInfo": {
                        "name": "PromptCraft-Hybrid",
                        "version": "0.1.0",
                    },
                },
            )

            # Send the request and wait for response
            response = await self._send_request_and_wait(writer, reader, initialize_request)

            if response:
                # Parse server capabilities
                server_capabilities = response.get("capabilities", {})
                server_info = response.get("serverInfo", {})

                # Create server info record
                server_info_obj = MCPServerInfo(
                    name=server_name,
                    connection=None,  # type: ignore[arg-type] # We'll update this later if needed
                    capabilities=server_capabilities,
                    tools=[],  # Will be populated by tools/list
                    resources=[],  # Will be populated by resources/list
                    prompts=[],  # Will be populated by prompts/list
                    last_ping=utc_now(),
                )

                self.servers[server_name] = server_info_obj

                # Start background message handler for this server
                asyncio.create_task(self._handle_server_messages(server_name, reader, writer))

                # Query server capabilities
                await self._query_server_capabilities(server_name, writer, reader)

                self.logger.info(f"Initialized MCP server {server_name}: {server_info}")
                return True
            self.logger.error(f"No response to initialize request from {server_name}")
            return False

        except Exception as e:
            self.logger.error(f"Failed to initialize server {server_name}: {e}")
            return False

    async def _send_request_and_wait(
        self, writer: asyncio.StreamWriter, reader: asyncio.StreamReader, request: MCPRequest, timeout: float = 10.0
    ) -> Any | None:
        """Send a request and wait for response.

        Args:
            writer: Stream writer
            reader: Stream reader
            request: Request to send
            timeout: Request timeout in seconds

        Returns:
            Response result or None if failed
        """
        try:
            # Send request
            message_str = self.protocol_handler.serialize_message(request)
            writer.write((message_str + "\n").encode())
            await writer.drain()

            # Wait for response
            start_time = asyncio.get_event_loop().time()
            while True:
                try:
                    line = await asyncio.wait_for(reader.readline(), timeout=1.0)
                    if not line:
                        break

                    message_str = line.decode().strip()
                    if not message_str:
                        continue

                    message = self.protocol_handler.deserialize_message(message_str)

                    # Check if this is the response we're waiting for
                    if isinstance(message, MCPResponse) and message.id == request.id:
                        return message.result
                    if isinstance(message, MCPError) and message.id == request.id:
                        self.logger.error(f"Request {request.id} failed: {message.error}")
                        return None

                except TimeoutError:
                    # Check overall timeout
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        self.logger.error(f"Request {request.id} timed out")
                        return None
                    continue

        except Exception as e:
            self.logger.error(f"Failed to send request {request.id}: {e}")
            return None

        # Fallback return if no response was received
        return None

    async def _query_server_capabilities(
        self, server_name: str, writer: asyncio.StreamWriter, reader: asyncio.StreamReader
    ) -> None:
        """Query server for available tools, resources, and prompts.

        Args:
            server_name: Name of the server
            writer: Stream writer
            reader: Stream reader
        """
        server_info = self.servers.get(server_name)
        if not server_info:
            return

        try:
            # Query tools
            if server_info.capabilities.get("tools"):
                tools_request = self.protocol_handler.create_request("tools/list", {})
                tools_response = await self._send_request_and_wait(writer, reader, tools_request)
                if tools_response and "tools" in tools_response:
                    server_info.tools = tools_response["tools"]
                    self.logger.info(f"Server {server_name} has {len(server_info.tools)} tools")

            # Query resources
            if server_info.capabilities.get("resources"):
                resources_request = self.protocol_handler.create_request("resources/list", {})
                resources_response = await self._send_request_and_wait(writer, reader, resources_request)
                if resources_response and "resources" in resources_response:
                    server_info.resources = resources_response["resources"]
                    self.logger.info(f"Server {server_name} has {len(server_info.resources)} resources")

            # Query prompts
            if server_info.capabilities.get("prompts"):
                prompts_request = self.protocol_handler.create_request("prompts/list", {})
                prompts_response = await self._send_request_and_wait(writer, reader, prompts_request)
                if prompts_response and "prompts" in prompts_response:
                    server_info.prompts = prompts_response["prompts"]
                    self.logger.info(f"Server {server_name} has {len(server_info.prompts)} prompts")

        except Exception as e:
            self.logger.error(f"Failed to query capabilities for {server_name}: {e}")

    async def _handle_server_messages(
        self, server_name: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming messages from an MCP server.

        Args:
            server_name: Name of the server
            reader: Stream reader
            writer: Stream writer
        """
        self.logger.info(f"Starting message handler for server: {server_name}")

        try:
            while True:
                line = await reader.readline()
                if not line:
                    self.logger.warning(f"Connection to {server_name} closed")
                    break

                message_str = line.decode().strip()
                if not message_str:
                    continue

                try:
                    message = self.protocol_handler.deserialize_message(message_str)

                    if isinstance(message, MCPRequest):
                        # Handle incoming request from server
                        response = await self.method_registry.handle_request(message)
                        self.protocol_handler.send_response(writer, response)
                        await writer.drain()

                    elif isinstance(message, MCPNotification):
                        # Handle notification from server
                        self.logger.debug(f"Received notification from {server_name}: {message.method}")

                    else:
                        self.logger.debug(f"Received message from {server_name}: {type(message)}")

                except Exception as e:
                    self.logger.error(f"Failed to process message from {server_name}: {e}")

        except Exception as e:
            self.logger.error(f"Message handler for {server_name} failed: {e}")
        finally:
            # Cleanup
            self.servers.pop(server_name, None)
            self.server_streams.pop(server_name, None)
            self.logger.info(f"Message handler for {server_name} terminated")

    # Standard MCP method handlers

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP initialize method."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
            "serverInfo": {
                "name": "PromptCraft-Hybrid-Client",
                "version": "0.1.0",
            },
        }

    async def _handle_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP ping method."""
        return {}

    async def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/list method."""
        # Return PromptCraft tools that can be called by MCP servers
        return {
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read content from a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to read"},
                        },
                        "required": ["file_path"],
                    },
                },
                {
                    "name": "search_documents",
                    "description": "Search through documents using semantic search",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum number of results", "default": 10},
                        },
                        "required": ["query"],
                    },
                },
            ],
        }

    async def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call method."""
        tool_name = params.get("name")
        tool_arguments = params.get("arguments", {})

        if tool_name == "read_file":
            return await self._execute_read_file(tool_arguments)
        if tool_name == "search_documents":
            return await self._execute_search_documents(tool_arguments)
        raise MCPProtocolError(
            MCPStandardErrors.METHOD_NOT_FOUND,
            f"Tool not found: {tool_name}",
        )

    async def _handle_resources_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/list method."""
        return {
            "resources": [
                {
                    "uri": "promptcraft://documents",
                    "name": "Document Collection",
                    "description": "Access to PromptCraft document collection",
                    "mimeType": "application/json",
                },
            ],
        }

    async def _handle_resources_read(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/read method."""
        uri = params.get("uri")

        if uri == "promptcraft://documents":
            # Return document collection metadata
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(
                            {
                                "collection": "PromptCraft Documents",
                                "count": "dynamic",
                                "access_methods": ["search_documents", "read_file"],
                            }
                        ),
                    },
                ],
            }
        raise MCPProtocolError(
            MCPStandardErrors.INVALID_PARAMS,
            f"Unknown resource URI: {uri}",
        )

    async def _handle_prompts_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/list method."""
        return {
            "prompts": [
                {
                    "name": "document_search",
                    "description": "Search and analyze documents",
                    "arguments": [
                        {
                            "name": "query",
                            "description": "Search query",
                            "required": True,
                        },
                    ],
                },
            ],
        }

    async def _handle_prompts_get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/get method."""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if prompt_name == "document_search":
            query = arguments.get("query", "")
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Search for documents related to: {query}",
                        },
                    },
                ],
            }
        raise MCPProtocolError(
            MCPStandardErrors.METHOD_NOT_FOUND,
            f"Prompt not found: {prompt_name}",
        )

    # Tool execution methods (to be connected to PromptCraft tools)

    async def _execute_read_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute read_file tool."""
        file_path = arguments.get("file_path")
        if not file_path:
            raise MCPProtocolError(
                MCPStandardErrors.INVALID_PARAMS,
                "file_path parameter required",
            )

        try:
            # This would connect to PromptCraft's Read tool
            from pathlib import Path

            path = Path(file_path)

            if not path.exists():
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"File not found: {file_path}",
                        },
                    ],
                    "isError": True,
                }

            content = path.read_text(encoding="utf-8")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    },
                ],
            }

        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error reading file: {e!s}",
                    },
                ],
                "isError": True,
            }

    async def _execute_search_documents(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute search_documents tool."""
        query = arguments.get("query")
        arguments.get("limit", 10)

        if not query:
            raise MCPProtocolError(
                MCPStandardErrors.INVALID_PARAMS,
                "query parameter required",
            )

        try:
            # This would connect to PromptCraft's vector search system
            # For now, return a mock response
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Search results for '{query}' (mock implementation):\n\n1. Document about {query} concepts\n2. Related technical documentation\n3. Best practices guide",
                    },
                ],
            }

        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error searching documents: {e!s}",
                    },
                ],
                "isError": True,
            }

    # Public API methods

    async def call_server_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on a connected MCP server.

        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if server_name not in self.servers:
            raise MCPProtocolError(
                MCPStandardErrors.INVALID_PARAMS,
                f"Server not connected: {server_name}",
            )

        if server_name not in self.server_streams:
            raise MCPProtocolError(
                MCPStandardErrors.INTERNAL_ERROR,
                f"No stream available for server: {server_name}",
            )

        reader, writer = self.server_streams[server_name]

        # Create and send tool call request
        request = self.protocol_handler.create_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

        return await self._send_request_and_wait(writer, reader, request)

    def get_server_info(self, server_name: str) -> MCPServerInfo | None:
        """Get information about a connected server.

        Args:
            server_name: Name of the server

        Returns:
            Server information or None if not connected
        """
        return self.servers.get(server_name)

    def list_connected_servers(self) -> list[str]:
        """Get list of connected server names.

        Returns:
            List of server names
        """
        return list(self.servers.keys())

    def get_status(self) -> dict[str, Any]:
        """Get router status information.

        Returns:
            Status dictionary
        """
        return {
            "connected_servers": len(self.servers),
            "servers": {
                name: {
                    "capabilities": info.capabilities,
                    "tools_count": len(info.tools),
                    "resources_count": len(info.resources),
                    "prompts_count": len(info.prompts),
                    "last_ping": info.last_ping.isoformat() if info.last_ping else None,
                }
                for name, info in self.servers.items()
            },
        }
