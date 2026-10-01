"""
MCP Tool Router

Routes tool execution between MCP servers and PromptCraft tools, providing
a unified interface for tool invocation across the hybrid infrastructure.
"""

import asyncio
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shlex
import tempfile
import time
from typing import Any

from src.utils.logging_mixin import LoggerMixin

from .message_router import MCPMessageRouter
from .protocol_handler import MCPProtocolError, MCPStandardErrors


logger = logging.getLogger(__name__)

# LLM08: Excessive Agency hardening. Tool inputs from an LLM are never trusted.
# Bash execution is gated behind an explicit opt-in env flag; file paths must
# resolve under one of the allowed roots; writes must use an allowed extension.
_BASH_EXEC_ENV = "PROMPTCRAFT_MCP_ENABLE_BASH"
_FILE_ALLOWLIST_ENV = "PROMPTCRAFT_MCP_ALLOWED_PATHS"
_WRITE_EXTENSIONS_ENV = "PROMPTCRAFT_MCP_WRITE_EXTENSIONS"

# Hard caps protect against resource exhaustion when an LLM picks pathological
# offset/limit values.
_MAX_READ_LIMIT = 50000
_MAX_OFFSET = 10_000_000
_MAX_PATH_LEN = 4096
_MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MiB
_MAX_BASH_TIMEOUT = 300.0
_MAX_SEARCH_LIMIT = 100

# Always-denied prefixes regardless of the configured allowlist. Resolving to
# any of these (or descendants) blocks the operation. Matched against the
# resolved absolute path with a trailing separator to avoid prefix-only
# collisions (e.g. /etc-foo not matching /etc).
_DENY_PATH_PREFIXES = (
    "/etc/",
    "/root/",
    "/proc/",
    "/sys/",
    "/var/log/",
    "/var/run/",
    "/boot/",
    "/dev/",
)

_DENY_PATH_SUFFIXES = (
    "/.ssh",
    "/.aws",
    "/.gnupg",
    "/.env",
    "/.netrc",
    "/id_rsa",
    "/id_ed25519",
    "/credentials",
    "/authorized_keys",
)

# Default write extension allowlist. Override via env.
_DEFAULT_WRITE_EXTENSIONS = frozenset(
    {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".log", ".html", ".py"},
)

# Shell metacharacters that allow chaining, substitution, or redirection. If
# any appear in a bash command we refuse to run it under shell=True semantics.
_SHELL_METACHARS = re.compile(r"[;&|`$><(){}\[\]\\\n\r]")

# Known-dangerous tokens. Substring match is intentional: even partial appearance
# (e.g. "sudo " inside a pipeline) is grounds for rejection.
_DANGEROUS_BASH_TOKENS = (
    "rm -rf",
    "sudo ",
    " su ",
    "chmod 777",
    "mkfs",
    "fdisk",
    "dd if=",
    "curl ",
    "wget ",
    "nc ",
    ":(){",  # fork bomb
    "/etc/passwd",
    "/etc/shadow",
)


def _allowed_roots() -> list[Path]:
    """Return the set of resolved directories under which file ops are allowed.

    Defaults cover the project working directory and the system temp dir so
    pytest fixtures (tmp_path) continue to work. Override with a colon-separated
    list in PROMPTCRAFT_MCP_ALLOWED_PATHS.
    """
    env_value = os.environ.get(_FILE_ALLOWLIST_ENV)
    if env_value:
        roots = [Path(p).expanduser().resolve() for p in env_value.split(os.pathsep) if p.strip()]
    else:
        roots = [Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve()]
    return roots


def _allowed_write_extensions() -> frozenset[str]:
    env_value = os.environ.get(_WRITE_EXTENSIONS_ENV)
    if env_value:
        return frozenset(ext.strip().lower() for ext in env_value.split(",") if ext.strip())
    return _DEFAULT_WRITE_EXTENSIONS


def _validate_file_path(raw_path: str, *, for_write: bool) -> Path:
    """Resolve ``raw_path`` and ensure it lives under an allowed root.

    Raises ``ValueError`` for any path that fails the safety checks. Callers
    surface the error as an isError tool result so the LLM cannot retry into
    sensitive locations.
    """
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("file_path must be a non-empty string")
    if len(raw_path) > _MAX_PATH_LEN:
        raise ValueError("file_path exceeds maximum length")
    if "\x00" in raw_path:
        raise ValueError("file_path contains a null byte")

    candidate = Path(raw_path).expanduser()
    # Resolve to absolute even when the file does not yet exist (for writes).
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"file_path cannot be resolved: {exc}") from exc

    resolved_str = str(resolved)
    deny_prefix_match = any((resolved_str + "/").startswith(prefix) for prefix in _DENY_PATH_PREFIXES)
    if deny_prefix_match or any(resolved_str.endswith(suffix) for suffix in _DENY_PATH_SUFFIXES):
        raise ValueError("file_path is in a denied location")

    allowed = _allowed_roots()
    if not any(resolved == root or root in resolved.parents for root in allowed):
        raise ValueError("file_path is outside the configured allowlist")

    # Reject symlinks that point outside the allowlist. Existing entries only.
    if candidate.is_symlink() or (candidate.exists() and candidate.is_symlink()):
        target = candidate.resolve(strict=False)
        if not any(target == root or root in target.parents for root in allowed):
            raise ValueError("symlink target is outside the allowlist")

    if for_write:
        suffix = resolved.suffix.lower()
        allowed_exts = _allowed_write_extensions()
        if suffix and suffix not in allowed_exts:
            raise ValueError(f"write extension '{suffix}' is not allowed")

    return resolved


def _bash_exec_enabled() -> bool:
    return os.environ.get(_BASH_EXEC_ENV, "").lower() in {"1", "true", "yes", "on"}


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

    async def execute_read(  # noqa: PLR0911 - security guard clauses; combining hurts readability
        self,
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Execute PromptCraft Read tool functionality.

        Args:
            file_path: Path to file to read
            offset: Line offset to start reading from
            limit: Maximum number of lines to read

        Returns:
            Tool execution result
        """
        try:
            try:
                path = _validate_file_path(file_path, for_write=False)
            except ValueError as exc:
                return {
                    "content": [{"type": "text", "text": f"Access denied: {exc}"}],
                    "isError": True,
                }

            if offset is not None:
                if not isinstance(offset, int) or offset < 0 or offset > _MAX_OFFSET:
                    return {
                        "content": [{"type": "text", "text": "offset out of range"}],
                        "isError": True,
                    }
            if limit is not None:
                if not isinstance(limit, int) or limit < 1 or limit > _MAX_READ_LIMIT:
                    return {
                        "content": [
                            {"type": "text", "text": f"limit must be between 1 and {_MAX_READ_LIMIT}"},
                        ],
                        "isError": True,
                    }

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

            if path.stat().st_size > _MAX_FILE_BYTES:
                return {
                    "content": [{"type": "text", "text": "File exceeds maximum readable size"}],
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
                display_line = line[:2000] + "..." if len(line) > 2000 else line
                formatted_lines.append(f"{line_num:4d}→{display_line}")

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
            try:
                path = _validate_file_path(file_path, for_write=True)
            except ValueError as exc:
                return {
                    "content": [{"type": "text", "text": f"Write denied: {exc}"}],
                    "isError": True,
                }

            if len(content.encode("utf-8")) > _MAX_FILE_BYTES:
                return {
                    "content": [{"type": "text", "text": "content exceeds maximum allowed size"}],
                    "isError": True,
                }

            self.logger.info("MCP tool write: %s (%d bytes)", path, len(content))

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

    async def execute_bash(  # noqa: PLR0911 - security guard clauses; combining hurts readability
        self,
        command: str,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute PromptCraft Bash tool functionality.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Tool execution result
        """
        try:
            if not _bash_exec_enabled():
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Bash execution is disabled. Set "
                                f"{_BASH_EXEC_ENV}=1 to opt in, and review the command before enabling."
                            ),
                        },
                    ],
                    "isError": True,
                }

            if not isinstance(command, str) or not command.strip():
                return {
                    "content": [{"type": "text", "text": "command must be a non-empty string"}],
                    "isError": True,
                }
            if len(command) > 2000:
                return {
                    "content": [{"type": "text", "text": "command exceeds maximum length"}],
                    "isError": True,
                }
            try:
                bounded_timeout = float(timeout)
            except (TypeError, ValueError):
                bounded_timeout = 30.0
            bounded_timeout = max(0.1, min(bounded_timeout, _MAX_BASH_TIMEOUT))

            lowered = command.lower()
            if any(token in lowered for token in _DANGEROUS_BASH_TOKENS):
                return {
                    "content": [{"type": "text", "text": "Command blocked: contains a dangerous token"}],
                    "isError": True,
                }
            if _SHELL_METACHARS.search(command):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Command blocked: shell metacharacters (pipes, redirects, substitution) are not allowed",
                        },
                    ],
                    "isError": True,
                }

            # Parse safely instead of relying on the shell. This rejects unparseable
            # input and avoids shell=True command injection.
            try:
                argv = shlex.split(command, posix=True)
            except ValueError as exc:
                return {
                    "content": [{"type": "text", "text": f"Command not parseable: {exc}"}],
                    "isError": True,
                }
            if not argv:
                return {
                    "content": [{"type": "text", "text": "command is empty after parsing"}],
                    "isError": True,
                }

            self.logger.info("MCP bash exec (opt-in): %s", argv[0])

            # Execute command without invoking a shell.
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            timeout = bounded_timeout

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
            if not isinstance(query, str) or not query.strip():
                return {
                    "content": [{"type": "text", "text": "query must be a non-empty string"}],
                    "isError": True,
                }
            if len(query) > 1000:
                return {
                    "content": [{"type": "text", "text": "query exceeds maximum length"}],
                    "isError": True,
                }
            if not isinstance(limit, int) or limit < 1:
                limit = 10
            limit = min(limit, _MAX_SEARCH_LIMIT)

            # This would integrate with PromptCraft's vector search system
            # For now, implement a basic file search as a placeholder. Only
            # search within explicitly allowed roots, never the whole tree.
            search_results = []
            search_paths = _allowed_roots()

            for search_path in search_paths:
                if not search_path.exists() or not search_path.is_dir():
                    continue
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
                    except Exception as e:
                        logger.debug("Skipping file %s during search: %s", file_path, e)
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
            offset = arguments.get("offset")
            limit = arguments.get("limit")
            if not isinstance(file_path, str):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "file_path must be a string",
                )
            if offset is not None and not isinstance(offset, int):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "offset must be an integer",
                )
            if limit is not None and not isinstance(limit, int):
                raise MCPProtocolError(
                    MCPStandardErrors.INVALID_PARAMS,
                    "limit must be an integer",
                )
            return await self.promptcraft_executor.execute_read(
                file_path,
                offset,
                limit,
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
