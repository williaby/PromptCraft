"""
MCP Tool Router

Routes tool execution between MCP servers and PromptCraft tools, providing
a unified interface for tool invocation across the hybrid infrastructure.
"""

import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from src.utils.logging_mixin import LoggerMixin

from .message_router import MCPMessageRouter
from .protocol_handler import MCPProtocolError, MCPStandardErrors


logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool available through MCP."""

    name: str
    description: str
    server_name: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""

    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    server_name: str | None = None


class PromptCraftToolExecutor:
    """Executes PromptCraft native tools for MCP servers."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.PromptCraftToolExecutor")

    async def execute_read(self, file_path: str, offset: int | None = None, limit: int | None = None) -> dict[str, Any]:
        """Execute PromptCraft Read tool functionality.

        Args:
            file_path: Path to file to read
            offset: Line offset to start reading from
            limit: Maximum number of lines to read

        Returns:
            Tool execution result
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return {
                    "content": [{"type": "text", "text": f"File not found: {file_path}"}],
                    "isError": True,
                }

            if not path.is_file():
                return {
                    "content": [{"type": "text", "text": f"Path is not a file: {file_path}"}],
                    "isError": True,
                }

            # Read file content with line numbers (similar to PromptCraft Read tool)
            lines = path.read_text(encoding="utf-8").splitlines()

            # Apply offset and limit
            if offset is not None:
                lines = lines[offset:]
            if limit is not None:
                lines = lines[:limit]

            # Format with line numbers
            formatted_lines = []
            start_line = (offset or 0) + 1
            for i, line in enumerate(lines):
                line_num = start_line + i
                # Truncate very long lines
                if len(line) > 2000:
                    line = line[:2000] + "..."
                formatted_lines.append(f"{line_num:4d}→{line}")

            content = "\n".join(formatted_lines)

            return {
                "content": [{"type": "text", "text": content}],
            }

        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return {
                "content": [{"type": "text", "text": f"Error reading file: {e!s}"}],
                "isError": True,
            }

    async def execute_write(self, file_path: str, content: str) -> dict[str, Any]:
        """Execute PromptCraft Write tool functionality.

        Args:
            file_path: Path to file to write
            content: Content to write

        Returns:
            Tool execution result
        """
        try:
            path = Path(file_path)

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            path.write_text(content, encoding="utf-8")

            return {
                "content": [{"type": "text", "text": f"Successfully wrote {len(content)} characters to {file_path}"}],
            }

        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            return {
                "content": [{"type": "text", "text": f"Error writing file: {e!s}"}],
                "isError": True,
            }

    async def execute_bash(self, command: str, timeout: float = 30.0) -> dict[str, Any]:
        """Execute PromptCraft Bash tool functionality.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Tool execution result
        """
        try:
            # Security check - limit dangerous commands
            dangerous_commands = ["rm -rf", "sudo", "su", "chmod 777", "mkfs", "fdisk"]
            if any(dangerous in command.lower() for dangerous in dangerous_commands):
                return {
                    "content": [{"type": "text", "text": f"Command blocked for security reasons: {command}"}],
                    "isError": True,
                }

            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except TimeoutError:
                process.kill()
                await process.communicate()
                return {
                    "content": [{"type": "text", "text": f"Command timed out after {timeout}s: {command}"}],
                    "isError": True,
                }

            # Format output
            output_parts = []
            if stdout:
                stdout_text = stdout.decode("utf-8") if isinstance(stdout, bytes) else str(stdout)
                output_parts.append(f"STDOUT:\n{stdout_text}")
            if stderr:
                stderr_text = stderr.decode("utf-8") if isinstance(stderr, bytes) else str(stderr)
                output_parts.append(f"STDERR:\n{stderr_text}")

            output = (
                "\n".join(output_parts)
                if output_parts
                else f"Command completed with no output (exit code: {process.returncode})"
            )

            return {
                "content": [{"type": "text", "text": output}],
                "exitCode": process.returncode,
            }

        except Exception as e:
            self.logger.error(f"Failed to execute bash command '{command}': {e}")
            return {
                "content": [{"type": "text", "text": f"Error executing command: {e!s}"}],
                "isError": True,
            }

    async def execute_search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Execute document search functionality.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Tool execution result
        """
        try:
            # This would integrate with PromptCraft's vector search system
            # For now, implement a basic file search as a placeholder

            search_results = []
            search_paths = [Path()]

            for search_path in search_paths:
                for file_path in search_path.rglob("*.md"):
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if query.lower() in content.lower():
                            # Extract context around the match
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if query.lower() in line.lower():
                                    context_start = max(0, i - 2)
                                    context_end = min(len(lines), i + 3)
                                    context = "\n".join(lines[context_start:context_end])

                                    search_results.append(
                                        {
                                            "file": str(file_path),
                                            "line": i + 1,
                                            "context": context,
                                        },
                                    )
                                    break

                        if len(search_results) >= limit:
                            break
                    except Exception:
                        continue

                if len(search_results) >= limit:
                    break

            if search_results:
                result_text = f"Found {len(search_results)} results for '{query}':\n\n"
                for i, result in enumerate(search_results, 1):
                    result_text += f"{i}. {result['file']}:{result['line']}\n{result['context']}\n\n"
            else:
                result_text = f"No results found for '{query}'"

            return {
                "content": [{"type": "text", "text": result_text}],
                "resultCount": len(search_results),
            }

        except Exception as e:
            self.logger.error(f"Failed to execute search for '{query}': {e}")
            return {
                "content": [{"type": "text", "text": f"Error executing search: {e!s}"}],
                "isError": True,
            }


class MCPToolRouter(LoggerMixin):
    """Routes tool execution between MCP servers and PromptCraft tools."""

    def __init__(self, message_router: MCPMessageRouter) -> None:
        super().__init__()
        self.message_router = message_router
        self.promptcraft_executor = PromptCraftToolExecutor()
        self.available_tools: dict[str, ToolDefinition] = {}
        self._register_promptcraft_tools()

    def _register_promptcraft_tools(self) -> None:
        """Register PromptCraft native tools."""
        self.available_tools.update(
            {
                "read_file": ToolDefinition(
                    name="read_file",
                    description="Read content from a file with optional offset and limit",
                    server_name="promptcraft",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to read"},
                            "offset": {"type": "integer", "description": "Line offset to start reading from"},
                            "limit": {"type": "integer", "description": "Maximum number of lines to read"},
                        },
                        "required": ["file_path"],
                    },
                ),
                "write_file": ToolDefinition(
                    name="write_file",
                    description="Write content to a file",
                    server_name="promptcraft",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to write"},
                            "content": {"type": "string", "description": "Content to write to the file"},
                        },
                        "required": ["file_path", "content"],
                    },
                ),
                "execute_bash": ToolDefinition(
                    name="execute_bash",
                    description="Execute a bash command",
                    server_name="promptcraft",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to execute"},
                            "timeout": {"type": "number", "description": "Command timeout in seconds", "default": 30.0},
                        },
                        "required": ["command"],
                    },
                ),
                "search_documents": ToolDefinition(
                    name="search_documents",
                    description="Search through documents using text matching",
                    server_name="promptcraft",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum number of results", "default": 10},
                        },
                        "required": ["query"],
                    },
                ),
            },
        )

    def refresh_server_tools(self) -> None:
        """Refresh available tools from connected MCP servers."""
        # Clear existing server tools
        server_tools = {name: tool for name, tool in self.available_tools.items() if tool.server_name == "promptcraft"}
        self.available_tools = server_tools

        # Add tools from connected servers
        for server_name in self.message_router.list_connected_servers():
            server_info = self.message_router.get_server_info(server_name)
            if server_info and server_info.tools:
                for tool_info in server_info.tools:
                    tool_name = tool_info.get("name", "")
                    if tool_name:
                        # Create unique tool name with server prefix
                        unique_name = f"{server_name}:{tool_name}"
                        self.available_tools[unique_name] = ToolDefinition(
                            name=tool_name,
                            description=tool_info.get("description", ""),
                            server_name=server_name,
                            input_schema=tool_info.get("inputSchema", {}),
                        )

        self.logger.info(f"Refreshed tools: {len(self.available_tools)} available")

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        import time

        start_time = time.time()

        # Check if tool exists
        if tool_name not in self.available_tools:
            # Try with server prefix
            found = False
            for available_name, tool_def in self.available_tools.items():
                if tool_def.name == tool_name or available_name.endswith(f":{tool_name}"):
                    tool_name = available_name
                    found = True
                    break

            if not found:
                return ToolExecutionResult(
                    success=False,
                    error=f"Tool not found: {tool_name}",
                    execution_time=time.time() - start_time,
                )

        tool_def = self.available_tools[tool_name]

        try:
            # Route to appropriate executor
            if tool_def.server_name == "promptcraft":
                result = await self._execute_promptcraft_tool(tool_def.name, arguments)
            else:
                result = await self._execute_server_tool(tool_def.server_name, tool_def.name, arguments)

            return ToolExecutionResult(
                success=not result.get("isError", False),
                result=result,
                execution_time=time.time() - start_time,
                server_name=tool_def.server_name,
            )

        except Exception as e:
            self.logger.error(f"Failed to execute tool {tool_name}: {e}")
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                server_name=tool_def.server_name,
            )

    async def _execute_promptcraft_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a PromptCraft native tool.

        Args:
            tool_name: Name of the PromptCraft tool
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if tool_name == "read_file":
            file_path = arguments.get("file_path")
            if not isinstance(file_path, str):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "file_path must be a string",
                )
            return await self.promptcraft_executor.execute_read(
                file_path,
                arguments.get("offset"),
                arguments.get("limit"),
            )
        if tool_name == "write_file":
            file_path = arguments.get("file_path")
            content = arguments.get("content")
            if not isinstance(file_path, str):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "file_path must be a string",
                )
            if not isinstance(content, str):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "content must be a string",
                )
            return await self.promptcraft_executor.execute_write(
                file_path,
                content,
            )
        if tool_name == "execute_bash":
            command = arguments.get("command")
            if not isinstance(command, str):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "command must be a string",
                )
            return await self.promptcraft_executor.execute_bash(
                command,
                arguments.get("timeout", 30.0),
            )
        if tool_name == "search_documents":
            query = arguments.get("query")
            if not isinstance(query, str):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "query must be a string",
                )
            return await self.promptcraft_executor.execute_search(
                query,
                arguments.get("limit", 10),
            )
        raise MCPProtocolError(
            MCPStandardErrors.METHOD_NOT_FOUND,
            f"PromptCraft tool not implemented: {tool_name}",
        )

    async def _execute_server_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool on an MCP server.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            result = await self.message_router.call_server_tool(server_name, tool_name, arguments)
            return result or {"content": [{"type": "text", "text": "Tool executed successfully with no output"}]}

        except Exception as e:
            self.logger.error(f"Failed to execute server tool {server_name}:{tool_name}: {e}")
            return {
                "content": [{"type": "text", "text": f"Error executing tool: {e!s}"}],
                "isError": True,
            }

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of all available tools.

        Returns:
            List of tool definitions
        """
        tools = []
        for tool_name, tool_def in self.available_tools.items():
            tools.append(
                {
                    "name": tool_name,
                    "description": tool_def.description,
                    "server_name": tool_def.server_name,
                    "input_schema": tool_def.input_schema,
                },
            )

        return tools

    def get_tools_by_server(self, server_name: str) -> list[dict[str, Any]]:
        """Get tools available from a specific server.

        Args:
            server_name: Name of the server

        Returns:
            List of tools from that server
        """
        tools = []
        for tool_name, tool_def in self.available_tools.items():
            if tool_def.server_name == server_name:
                tools.append(
                    {
                        "name": tool_name,
                        "description": tool_def.description,
                        "input_schema": tool_def.input_schema,
                    },
                )

        return tools

    def get_status(self) -> dict[str, Any]:
        """Get tool router status.

        Returns:
            Status information
        """
        tools_by_server = {}
        for tool_def in self.available_tools.values():
            server_name = tool_def.server_name
            if server_name not in tools_by_server:
                tools_by_server[server_name] = 0
            tools_by_server[server_name] += 1

        return {
            "total_tools": len(self.available_tools),
            "tools_by_server": tools_by_server,
            "connected_servers": len(self.message_router.list_connected_servers()),
            "promptcraft_tools": len([t for t in self.available_tools.values() if t.server_name == "promptcraft"]),
        }
