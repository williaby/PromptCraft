"""
Tests for MCP Tool Router
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_integration.message_router import MCPMessageRouter, MCPServerInfo
from src.mcp_integration.protocol_handler import MCPProtocolError, MCPStandardErrors
from src.mcp_integration.tool_router import (
    MCPToolRouter,
    PromptCraftToolExecutor,
    ToolDefinition,
    ToolExecutionResult,
)


class TestToolDefinition:
    """Test ToolDefinition dataclass."""

    def test_tool_definition_creation(self):
        """Test creating ToolDefinition."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test tool description",
            server_name="test_server",
            input_schema={"type": "object"},
        )

        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.server_name == "test_server"
        assert tool.input_schema == {"type": "object"}
        assert tool.output_schema is None

    def test_tool_definition_with_output_schema(self):
        """Test ToolDefinition with output schema."""
        output_schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        tool = ToolDefinition(
            name="test_tool",
            description="Test tool",
            server_name="test_server",
            input_schema={"type": "object"},
            output_schema=output_schema,
        )

        assert tool.output_schema == output_schema


class TestToolExecutionResult:
    """Test ToolExecutionResult dataclass."""

    def test_execution_result_default_values(self):
        """Test ToolExecutionResult with default values."""
        result = ToolExecutionResult(success=True)

        assert result.success is True
        assert result.result is None
        assert result.error is None
        assert result.execution_time == 0.0
        assert result.server_name is None

    def test_execution_result_with_values(self):
        """Test ToolExecutionResult with custom values."""
        result = ToolExecutionResult(
            success=False,
            result={"data": "test"},
            error="Test error",
            execution_time=1.5,
            server_name="test_server",
        )

        assert result.success is False
        assert result.result == {"data": "test"}
        assert result.error == "Test error"
        assert result.execution_time == 1.5
        assert result.server_name == "test_server"


class TestPromptCraftToolExecutor:
    """Test PromptCraftToolExecutor."""

    @pytest.fixture
    def executor(self):
        """Create executor fixture."""
        return PromptCraftToolExecutor()

    def test_executor_initialization(self, executor):
        """Test executor initialization."""
        assert hasattr(executor, "logger")

    @pytest.mark.asyncio
    async def test_execute_read_success(self, executor, tmp_path):
        """Test successful file read."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "line 1\nline 2\nline 3\nline 4"
        test_file.write_text(test_content)

        result = await executor.execute_read(str(test_file))

        assert "content" in result
        assert len(result["content"]) == 1
        assert "isError" not in result

        content_text = result["content"][0]["text"]
        assert "1→line 1" in content_text
        assert "2→line 2" in content_text
        assert "3→line 3" in content_text
        assert "4→line 4" in content_text

    @pytest.mark.asyncio
    async def test_execute_read_with_offset_and_limit(self, executor, tmp_path):
        """Test file read with offset and limit."""
        test_file = tmp_path / "test.txt"
        test_content = "\n".join([f"line {i}" for i in range(1, 11)])
        test_file.write_text(test_content)

        result = await executor.execute_read(str(test_file), offset=2, limit=3)

        content_text = result["content"][0]["text"]
        assert "3→line 3" in content_text
        assert "4→line 4" in content_text
        assert "5→line 5" in content_text
        assert "line 1" not in content_text
        assert "line 6" not in content_text

    @pytest.mark.asyncio
    async def test_execute_read_file_not_found(self, executor):
        """Test reading non-existent file."""
        result = await executor.execute_read("/path/that/does/not/exist.txt")

        assert "isError" in result
        assert result["isError"] is True
        assert "File not found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_read_path_is_directory(self, executor, tmp_path):
        """Test reading a directory instead of file."""
        result = await executor.execute_read(str(tmp_path))

        assert "isError" in result
        assert result["isError"] is True
        assert "Path is not a file" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_read_long_lines(self, executor, tmp_path):
        """Test reading file with long lines."""
        test_file = tmp_path / "test.txt"
        long_line = "x" * 2500  # Longer than 2000 char limit
        test_file.write_text(f"short line\n{long_line}\nshort line")

        result = await executor.execute_read(str(test_file))

        content_text = result["content"][0]["text"]
        assert "short line" in content_text
        assert "..." in content_text  # Long line should be truncated

    @pytest.mark.asyncio
    async def test_execute_write_success(self, executor, tmp_path):
        """Test successful file write."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"

        result = await executor.execute_write(str(test_file), content)

        assert "content" in result
        assert "isError" not in result
        assert "Successfully wrote 13 characters" in result["content"][0]["text"]
        assert test_file.read_text() == content

    @pytest.mark.asyncio
    async def test_execute_write_create_directories(self, executor, tmp_path):
        """Test write creates parent directories."""
        test_file = tmp_path / "subdir" / "test.txt"
        content = "test content"

        result = await executor.execute_write(str(test_file), content)

        assert "isError" not in result
        assert test_file.exists()
        assert test_file.read_text() == content

    @pytest.mark.asyncio
    async def test_execute_bash_success(self, executor):
        """Test successful bash execution."""
        # Mock subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = ("Hello World\n", "")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            result = await executor.execute_bash("echo 'Hello World'")

        assert "content" in result
        assert "isError" not in result
        assert "exitCode" in result
        assert result["exitCode"] == 0
        assert "Hello World" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_bash_with_stderr(self, executor):
        """Test bash execution with stderr output."""
        # Mock subprocess execution with stderr
        mock_process = AsyncMock()
        mock_process.communicate.return_value = ("", "error\n")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            result = await executor.execute_bash("echo 'error' >&2")

        assert "STDERR:" in result["content"][0]["text"]
        assert "error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_bash_dangerous_command(self, executor):
        """Test blocking dangerous commands."""
        result = await executor.execute_bash("rm -rf /")

        assert "isError" in result
        assert result["isError"] is True
        assert "Command blocked for security reasons" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_bash_timeout(self, executor):
        """Test bash command timeout."""
        # Mock subprocess that will timeout
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=("", ""))
        mock_process.kill = MagicMock()

        # Patch wait_for in the tool_router module specifically to raise TimeoutError
        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            with patch("src.mcp_integration.tool_router.asyncio.wait_for", side_effect=TimeoutError()):
                result = await executor.execute_bash("sleep 60", timeout=0.1)

        assert "isError" in result
        assert result["isError"] is True
        assert "Command timed out" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_search_success(self, executor, tmp_path):
        """Test successful document search."""
        # Create test files
        (tmp_path / "test1.md").write_text("This is a test document\nwith some content")
        (tmp_path / "test2.md").write_text("Another document\nwith different content")
        (tmp_path / "test3.txt").write_text("This should not be found")  # .txt files not included

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [tmp_path / "test1.md", tmp_path / "test2.md"]
            result = await executor.execute_search("test")

        assert "content" in result
        assert "resultCount" in result
        content_text = result["content"][0]["text"]
        assert "Found" in content_text
        assert "test1.md" in content_text

    @pytest.mark.asyncio
    async def test_execute_search_no_results(self, executor):
        """Test search with no results."""
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = []
            result = await executor.execute_search("nonexistent")

        assert "content" in result
        assert "No results found" in result["content"][0]["text"]
        assert result["resultCount"] == 0

    @pytest.mark.asyncio
    async def test_execute_search_limit(self, executor, tmp_path):
        """Test search result limit."""
        # Create multiple test files
        for i in range(5):
            (tmp_path / f"test{i}.md").write_text(f"This is test document {i}")

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = [tmp_path / f"test{i}.md" for i in range(5)]
            result = await executor.execute_search("test", limit=3)

        assert result["resultCount"] <= 3


class TestMCPToolRouter:
    """Test MCPToolRouter."""

    @pytest.fixture
    def mock_message_router(self):
        """Create mock message router."""
        router = MagicMock(spec=MCPMessageRouter)
        router.list_connected_servers.return_value = []
        return router

    @pytest.fixture
    def tool_router(self, mock_message_router):
        """Create tool router fixture."""
        return MCPToolRouter(mock_message_router)

    def test_router_initialization(self, tool_router, mock_message_router):
        """Test router initialization."""
        assert tool_router.message_router == mock_message_router
        assert hasattr(tool_router, "promptcraft_executor")
        assert hasattr(tool_router, "available_tools")
        assert hasattr(tool_router, "logger")

        # Check that PromptCraft tools are registered
        assert "read_file" in tool_router.available_tools
        assert "write_file" in tool_router.available_tools
        assert "execute_bash" in tool_router.available_tools
        assert "search_documents" in tool_router.available_tools

    def test_register_promptcraft_tools(self, tool_router):
        """Test PromptCraft tools registration."""
        tools = tool_router.available_tools

        # Check read_file tool
        read_tool = tools["read_file"]
        assert read_tool.name == "read_file"
        assert read_tool.server_name == "promptcraft"
        assert "file_path" in read_tool.input_schema["properties"]

        # Check write_file tool
        write_tool = tools["write_file"]
        assert write_tool.name == "write_file"
        assert write_tool.server_name == "promptcraft"
        assert "file_path" in write_tool.input_schema["properties"]
        assert "content" in write_tool.input_schema["properties"]

    def test_refresh_server_tools_no_servers(self, tool_router, mock_message_router):
        """Test refreshing tools with no connected servers."""
        mock_message_router.list_connected_servers.return_value = []

        initial_count = len(tool_router.available_tools)
        tool_router.refresh_server_tools()

        # Should only have PromptCraft tools
        assert len(tool_router.available_tools) == initial_count
        assert all(tool.server_name == "promptcraft" for tool in tool_router.available_tools.values())

    def test_refresh_server_tools_with_servers(self, tool_router, mock_message_router):
        """Test refreshing tools with connected servers."""
        # Mock server info - need to match actual MCPServerInfo signature
        from src.mcp_integration.connection_bridge import ActiveConnection

        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={},
            tools=[
                {
                    "name": "test_tool",
                    "description": "Test tool from server",
                    "inputSchema": {"type": "object"},
                },
            ],
            resources=[],
            prompts=[],
        )

        mock_message_router.list_connected_servers.return_value = ["test_server"]
        mock_message_router.get_server_info.return_value = server_info

        tool_router.refresh_server_tools()

        # Should have PromptCraft tools plus server tool
        assert "test_server:test_tool" in tool_router.available_tools
        server_tool = tool_router.available_tools["test_server:test_tool"]
        assert server_tool.name == "test_tool"
        assert server_tool.server_name == "test_server"

    @pytest.mark.asyncio
    async def test_execute_tool_promptcraft_read(self, tool_router, tmp_path):
        """Test executing PromptCraft read tool."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = await tool_router.execute_tool("read_file", {"file_path": str(test_file)})

        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert result.server_name == "promptcraft"
        assert result.execution_time > 0
        assert "test content" in result.result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_tool_promptcraft_write(self, tool_router, tmp_path):
        """Test executing PromptCraft write tool."""
        test_file = tmp_path / "test.txt"

        result = await tool_router.execute_tool(
            "write_file",
            {
                "file_path": str(test_file),
                "content": "test content",
            },
        )

        assert result.success is True
        assert result.server_name == "promptcraft"
        assert test_file.read_text() == "test content"

    @pytest.mark.asyncio
    async def test_execute_tool_promptcraft_bash(self, tool_router):
        """Test executing PromptCraft bash tool."""
        # Mock subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = ("hello\n", "")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            result = await tool_router.execute_tool("execute_bash", {"command": "echo hello"})

        assert result.success is True
        assert result.server_name == "promptcraft"
        assert "hello" in result.result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_tool_promptcraft_search(self, tool_router):
        """Test executing PromptCraft search tool."""
        with patch.object(tool_router.promptcraft_executor, "execute_search") as mock_search:
            mock_search.return_value = {
                "content": [{"type": "text", "text": "Search results"}],
                "resultCount": 1,
            }

            result = await tool_router.execute_tool("search_documents", {"query": "test"})

        assert result.success is True
        assert result.server_name == "promptcraft"
        mock_search.assert_called_once_with("test", 10)

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, tool_router):
        """Test executing non-existent tool."""
        result = await tool_router.execute_tool("nonexistent_tool", {})

        assert result.success is False
        assert "Tool not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_with_server_prefix(self, tool_router, mock_message_router):
        """Test executing tool with server prefix."""
        # Add a server tool - match actual MCPServerInfo signature
        from src.mcp_integration.connection_bridge import ActiveConnection

        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={},
            tools=[{"name": "test_tool", "description": "Test"}],
            resources=[],
            prompts=[],
        )

        mock_message_router.list_connected_servers.return_value = ["test_server"]
        mock_message_router.get_server_info.return_value = server_info
        mock_message_router.call_server_tool = AsyncMock(return_value={"result": "success"})

        tool_router.refresh_server_tools()

        result = await tool_router.execute_tool("test_tool", {})

        assert result.success is True
        assert result.server_name == "test_server"

    @pytest.mark.asyncio
    async def test_execute_server_tool_success(self, tool_router, mock_message_router):
        """Test successful server tool execution."""
        mock_message_router.call_server_tool = AsyncMock(return_value={"result": "success"})

        result = await tool_router._execute_server_tool("test_server", "test_tool", {})

        assert "result" in result
        assert result["result"] == "success"
        mock_message_router.call_server_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_server_tool_no_result(self, tool_router, mock_message_router):
        """Test server tool execution with no result."""
        mock_message_router.call_server_tool = AsyncMock(return_value=None)

        result = await tool_router._execute_server_tool("test_server", "test_tool", {})

        assert "content" in result
        assert "Tool executed successfully" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_server_tool_error(self, tool_router, mock_message_router):
        """Test server tool execution error."""
        mock_message_router.call_server_tool = AsyncMock(side_effect=Exception("Server error"))

        result = await tool_router._execute_server_tool("test_server", "test_tool", {})

        assert "isError" in result
        assert result["isError"] is True
        assert "Error executing tool" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_promptcraft_tool_unknown(self, tool_router):
        """Test executing unknown PromptCraft tool."""
        with pytest.raises(MCPProtocolError) as exc_info:
            await tool_router._execute_promptcraft_tool("unknown_tool", {})

        assert exc_info.value.code == MCPStandardErrors.METHOD_NOT_FOUND
        assert "PromptCraft tool not implemented" in exc_info.value.message

    def test_get_available_tools(self, tool_router):
        """Test getting available tools."""
        tools = tool_router.get_available_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 4  # At least the PromptCraft tools

        tool_names = [tool["name"] for tool in tools]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "execute_bash" in tool_names
        assert "search_documents" in tool_names

        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "server_name" in tool
            assert "input_schema" in tool

    def test_get_tools_by_server(self, tool_router):
        """Test getting tools by server."""
        tools = tool_router.get_tools_by_server("promptcraft")

        assert len(tools) == 4
        tool_names = [tool["name"] for tool in tools]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "execute_bash" in tool_names
        assert "search_documents" in tool_names

    def test_get_tools_by_nonexistent_server(self, tool_router):
        """Test getting tools from non-existent server."""
        tools = tool_router.get_tools_by_server("nonexistent")

        assert tools == []

    def test_get_status(self, tool_router, mock_message_router):
        """Test getting router status."""
        mock_message_router.list_connected_servers.return_value = ["server1", "server2"]

        status = tool_router.get_status()

        assert "total_tools" in status
        assert "tools_by_server" in status
        assert "connected_servers" in status
        assert "promptcraft_tools" in status

        assert status["total_tools"] >= 4
        assert status["connected_servers"] == 2
        assert status["promptcraft_tools"] == 4
        assert "promptcraft" in status["tools_by_server"]
        assert status["tools_by_server"]["promptcraft"] == 4


class TestToolExecutionEdgeCases:
    """Test edge cases in tool execution."""

    @pytest.fixture
    def tool_router(self):
        """Create tool router with mock message router."""
        mock_router = MagicMock(spec=MCPMessageRouter)
        mock_router.list_connected_servers.return_value = []
        return MCPToolRouter(mock_router)

    @pytest.mark.asyncio
    async def test_execute_tool_exception_handling(self, tool_router):
        """Test exception handling during tool execution."""
        # Mock the executor to raise an exception
        with patch.object(tool_router.promptcraft_executor, "execute_read", side_effect=Exception("Test error")):
            result = await tool_router.execute_tool("read_file", {"file_path": "/test"})

        assert result.success is False
        assert "Test error" in result.error
        assert result.server_name == "promptcraft"
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_tool_execution_timing(self, tool_router, tmp_path):
        """Test that execution time is recorded."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = await tool_router.execute_tool("read_file", {"file_path": str(test_file)})

        assert result.execution_time > 0
        assert result.execution_time < 1.0  # Should be very fast

    def test_tool_definition_equality(self):
        """Test ToolDefinition equality and hashing."""
        tool1 = ToolDefinition("test", "desc", "server", {"type": "object"})
        tool2 = ToolDefinition("test", "desc", "server", {"type": "object"})

        # They should be equal (dataclass implements __eq__)
        assert tool1 == tool2
