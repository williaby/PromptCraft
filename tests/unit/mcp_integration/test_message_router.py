"""
Tests for MCP Message Router
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_integration.connection_bridge import ActiveConnection
from src.mcp_integration.message_router import (
    MCPMessageRouter,
    MCPServerInfo,
)
from src.mcp_integration.protocol_handler import (
    MCPError,
    MCPProtocolError,
    MCPRequest,
    MCPResponse,
    MCPStandardErrors,
)
from src.utils.datetime_compat import utc_now


class TestMCPServerInfo:
    """Test MCPServerInfo dataclass."""

    def test_server_info_creation(self):
        """Test creating MCPServerInfo."""
        mock_connection = MagicMock(spec=ActiveConnection)

        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={"tools": {}, "resources": {}},
            tools=[{"name": "test_tool"}],
            resources=[{"uri": "test://resource"}],
            prompts=[{"name": "test_prompt"}],
        )

        assert server_info.name == "test_server"
        assert server_info.connection == mock_connection
        assert server_info.capabilities == {"tools": {}, "resources": {}}
        assert server_info.tools == [{"name": "test_tool"}]
        assert server_info.resources == [{"uri": "test://resource"}]
        assert server_info.prompts == [{"name": "test_prompt"}]
        assert server_info.last_ping is None

    def test_server_info_with_ping(self):
        """Test MCPServerInfo with ping timestamp."""
        mock_connection = MagicMock(spec=ActiveConnection)
        ping_time = utc_now()

        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={},
            tools=[],
            resources=[],
            prompts=[],
            last_ping=ping_time,
        )

        assert server_info.last_ping == ping_time


class TestMCPMessageRouter:
    """Test MCPMessageRouter."""

    @pytest.fixture
    def router(self):
        """Create message router fixture."""
        return MCPMessageRouter()

    def test_router_initialization(self, router):
        """Test router initialization."""
        assert hasattr(router, "protocol_handler")
        assert hasattr(router, "method_registry")
        assert hasattr(router, "servers")
        assert hasattr(router, "server_streams")
        assert hasattr(router, "logger")

        # Check that it starts with empty state
        assert len(router.servers) == 0
        assert len(router.server_streams) == 0

    def test_register_standard_methods(self, router):
        """Test that standard MCP methods are registered."""
        # Check that standard methods are in the registry
        methods = router.method_registry.list_methods()

        expected_methods = [
            "initialize",
            "ping",
            "tools/list",
            "tools/call",
            "resources/list",
            "resources/read",
            "prompts/list",
            "prompts/get",
        ]

        for method in expected_methods:
            assert method in methods

    @pytest.mark.asyncio
    async def test_handle_initialize(self, router):
        """Test initialize method handler."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test", "version": "1.0"},
        }

        result = await router._handle_initialize(params)

        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "PromptCraft-Hybrid-Client"

    @pytest.mark.asyncio
    async def test_handle_ping(self, router):
        """Test ping method handler."""
        result = await router._handle_ping({})
        assert result == {}

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, router):
        """Test tools/list method handler."""
        result = await router._handle_tools_list({})

        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) >= 2  # read_file and search_documents

        tool_names = [tool["name"] for tool in result["tools"]]
        assert "read_file" in tool_names
        assert "search_documents" in tool_names

    @pytest.mark.asyncio
    async def test_handle_tools_call_read_file(self, router, tmp_path):
        """Test tools/call method handler for read_file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        params = {
            "name": "read_file",
            "arguments": {"file_path": str(test_file)},
        }

        result = await router._handle_tools_call(params)

        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == test_content
        assert "isError" not in result

    @pytest.mark.asyncio
    async def test_handle_tools_call_read_file_not_found(self, router):
        """Test tools/call method handler for non-existent file."""
        params = {
            "name": "read_file",
            "arguments": {"file_path": "/nonexistent/file.txt"},
        }

        result = await router._handle_tools_call(params)

        assert "content" in result
        assert result["isError"] is True
        assert "File not found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_handle_tools_call_search_documents(self, router):
        """Test tools/call method handler for search_documents."""
        params = {
            "name": "search_documents",
            "arguments": {"query": "test query", "limit": 5},
        }

        result = await router._handle_tools_call(params)

        assert "content" in result
        assert len(result["content"]) == 1
        assert "test query" in result["content"][0]["text"]
        assert "Search results" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_handle_tools_call_unknown_tool(self, router):
        """Test tools/call method handler for unknown tool."""
        params = {
            "name": "unknown_tool",
            "arguments": {},
        }

        with pytest.raises(MCPProtocolError) as exc_info:
            await router._handle_tools_call(params)

        assert exc_info.value.code == MCPStandardErrors.METHOD_NOT_FOUND
        assert "Tool not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_handle_resources_list(self, router):
        """Test resources/list method handler."""
        result = await router._handle_resources_list({})

        assert "resources" in result
        assert len(result["resources"]) >= 1
        assert result["resources"][0]["uri"] == "promptcraft://documents"

    @pytest.mark.asyncio
    async def test_handle_resources_read_valid_uri(self, router):
        """Test resources/read method handler with valid URI."""
        params = {"uri": "promptcraft://documents"}

        result = await router._handle_resources_read(params)

        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["uri"] == "promptcraft://documents"
        assert result["contents"][0]["mimeType"] == "application/json"

        # Check that text contains valid JSON
        text = result["contents"][0]["text"]
        json_data = json.loads(text)
        assert "collection" in json_data

    @pytest.mark.asyncio
    async def test_handle_resources_read_invalid_uri(self, router):
        """Test resources/read method handler with invalid URI."""
        params = {"uri": "invalid://uri"}

        with pytest.raises(MCPProtocolError) as exc_info:
            await router._handle_resources_read(params)

        assert exc_info.value.code == MCPStandardErrors.INVALID_PARAMS
        assert "Unknown resource URI" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self, router):
        """Test prompts/list method handler."""
        result = await router._handle_prompts_list({})

        assert "prompts" in result
        assert len(result["prompts"]) >= 1
        assert result["prompts"][0]["name"] == "document_search"

    @pytest.mark.asyncio
    async def test_handle_prompts_get_valid(self, router):
        """Test prompts/get method handler with valid prompt."""
        params = {
            "name": "document_search",
            "arguments": {"query": "test query"},
        }

        result = await router._handle_prompts_get(params)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert "test query" in result["messages"][0]["content"]["text"]

    @pytest.mark.asyncio
    async def test_handle_prompts_get_invalid(self, router):
        """Test prompts/get method handler with invalid prompt."""
        params = {"name": "unknown_prompt", "arguments": {}}

        with pytest.raises(MCPProtocolError) as exc_info:
            await router._handle_prompts_get(params)

        assert exc_info.value.code == MCPStandardErrors.METHOD_NOT_FOUND
        assert "Prompt not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_execute_read_file_missing_path(self, router):
        """Test _execute_read_file with missing file_path."""
        with pytest.raises(MCPProtocolError) as exc_info:
            await router._execute_read_file({})

        assert exc_info.value.code == MCPStandardErrors.INVALID_PARAMS
        assert "file_path parameter required" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_execute_read_file_error_handling(self, router):
        """Test _execute_read_file error handling."""
        # Test with path that exists but raises exception during read
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied")):
                result = await router._execute_read_file({"file_path": "/test"})

        assert "isError" in result
        assert result["isError"] is True
        assert "Error reading file" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_search_documents_missing_query(self, router):
        """Test _execute_search_documents with missing query."""
        with pytest.raises(MCPProtocolError) as exc_info:
            await router._execute_search_documents({"limit": 5})

        assert exc_info.value.code == MCPStandardErrors.INVALID_PARAMS
        assert "query parameter required" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_execute_search_documents_with_defaults(self, router):
        """Test _execute_search_documents with default limit."""
        result = await router._execute_search_documents({"query": "test"})

        assert "content" in result
        assert "test" in result["content"][0]["text"]

    def test_get_server_info_exists(self, router):
        """Test getting existing server info."""
        # Add a mock server
        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={},
            tools=[],
            resources=[],
            prompts=[],
        )
        router.servers["test_server"] = server_info

        result = router.get_server_info("test_server")
        assert result == server_info

    def test_get_server_info_not_exists(self, router):
        """Test getting non-existent server info."""
        result = router.get_server_info("nonexistent")
        assert result is None

    def test_list_connected_servers_empty(self, router):
        """Test listing servers when none connected."""
        result = router.list_connected_servers()
        assert result == []

    def test_list_connected_servers_with_servers(self, router):
        """Test listing servers when some connected."""
        # Add mock servers
        mock_connection = MagicMock(spec=ActiveConnection)

        server1 = MCPServerInfo("server1", mock_connection, {}, [], [], [])
        server2 = MCPServerInfo("server2", mock_connection, {}, [], [], [])

        router.servers["server1"] = server1
        router.servers["server2"] = server2

        result = router.list_connected_servers()
        assert set(result) == {"server1", "server2"}

    def test_get_status_empty(self, router):
        """Test getting status with no connected servers."""
        result = router.get_status()

        assert result["connected_servers"] == 0
        assert result["servers"] == {}

    def test_get_status_with_servers(self, router):
        """Test getting status with connected servers."""
        mock_connection = MagicMock(spec=ActiveConnection)
        ping_time = utc_now()

        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={"tools": {}},
            tools=[{"name": "tool1"}, {"name": "tool2"}],
            resources=[{"uri": "resource1"}],
            prompts=[{"name": "prompt1"}],
            last_ping=ping_time,
        )

        router.servers["test_server"] = server_info

        result = router.get_status()

        assert result["connected_servers"] == 1
        assert "test_server" in result["servers"]

        server_status = result["servers"]["test_server"]
        assert server_status["capabilities"] == {"tools": {}}
        assert server_status["tools_count"] == 2
        assert server_status["resources_count"] == 1
        assert server_status["prompts_count"] == 1
        assert server_status["last_ping"] == ping_time.isoformat()


class TestConnectionAndCommunication:
    """Test connection and communication methods."""

    @pytest.fixture
    def router(self):
        """Create message router fixture."""
        return MCPMessageRouter()

    @pytest.mark.asyncio
    async def test_call_server_tool_server_not_connected(self, router):
        """Test calling tool on non-connected server."""
        with pytest.raises(MCPProtocolError) as exc_info:
            await router.call_server_tool("nonexistent", "tool", {})

        assert exc_info.value.code == MCPStandardErrors.INVALID_PARAMS
        assert "Server not connected" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_call_server_tool_no_stream(self, router):
        """Test calling tool when server has no stream."""
        # Add server without stream
        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo("test_server", mock_connection, {}, [], [], [])
        router.servers["test_server"] = server_info

        with pytest.raises(MCPProtocolError) as exc_info:
            await router.call_server_tool("test_server", "tool", {})

        assert exc_info.value.code == MCPStandardErrors.INTERNAL_ERROR
        assert "No stream available" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_call_server_tool_success(self, router):
        """Test successful server tool call."""
        # Add server and stream
        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo("test_server", mock_connection, {}, [], [], [])
        router.servers["test_server"] = server_info

        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        router.server_streams["test_server"] = (mock_reader, mock_writer)

        # Mock the _send_request_and_wait method
        expected_result = {"result": "success"}
        with patch.object(router, "_send_request_and_wait", return_value=expected_result):
            result = await router.call_server_tool("test_server", "test_tool", {"arg": "value"})

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_send_request_and_wait_success(self, router):
        """Test successful request/response cycle."""
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        mock_reader = AsyncMock()

        # Create a test request
        request = MCPRequest(method="test", id="123")

        # Mock the response
        response = MCPResponse(result={"data": "test"}, id="123")
        response_json = json.dumps(response.to_dict())

        # Mock readline to return the response
        mock_reader.readline.return_value = (response_json + "\n").encode()

        with patch.object(router.protocol_handler, "serialize_message") as mock_serialize:
            mock_serialize.return_value = '{"test": "request"}'

            result = await router._send_request_and_wait(mock_writer, mock_reader, request)

        assert result == {"data": "test"}
        assert mock_writer.write.called
        assert mock_writer.drain.called

    @pytest.mark.asyncio
    async def test_send_request_and_wait_error_response(self, router):
        """Test request with error response."""
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        mock_reader = AsyncMock()
        request = MCPRequest(method="test", id="123")

        # Mock error response
        error = MCPError(
            error={"code": -32600, "message": "Invalid Request"},
            id="123",
        )
        error_json = json.dumps(error.to_dict())
        mock_reader.readline.return_value = (error_json + "\n").encode()

        with patch.object(router.protocol_handler, "serialize_message", return_value='{"test": "request"}'):
            result = await router._send_request_and_wait(mock_writer, mock_reader, request)

        assert result is None

    @pytest.mark.asyncio
    async def test_send_request_and_wait_timeout(self, router):
        """Test request timeout."""
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        mock_reader = AsyncMock()
        mock_reader.readline.side_effect = TimeoutError()

        request = MCPRequest(method="test", id="123")

        with patch.object(router.protocol_handler, "serialize_message", return_value='{"test": "request"}'):
            result = await router._send_request_and_wait(mock_writer, mock_reader, request, timeout=0.1)

        assert result is None

    @pytest.mark.asyncio
    async def test_send_request_and_wait_connection_closed(self, router):
        """Test request when connection is closed."""
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        mock_reader = AsyncMock()
        mock_reader.readline.return_value = b""  # Empty bytes indicates closed connection

        request = MCPRequest(method="test", id="123")

        with patch.object(router.protocol_handler, "serialize_message", return_value='{"test": "request"}'):
            result = await router._send_request_and_wait(mock_writer, mock_reader, request)

        assert result is None


class TestMessageHandling:
    """Test message handling methods."""

    @pytest.fixture
    def router(self):
        """Create message router fixture."""
        return MCPMessageRouter()

    @pytest.mark.asyncio
    async def test_handle_server_messages_request(self, router):
        """Test handling incoming request from server."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        # Mock incoming request
        MCPRequest(method="ping", id="123")
        request_json = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": "123",
            },
        )

        # Set up reader to return the request then close
        mock_reader.readline.side_effect = [
            (request_json + "\n").encode(),
            b"",  # End of stream
        ]

        with patch.object(router.protocol_handler, "send_response") as mock_send:
            await router._handle_server_messages("test_server", mock_reader, mock_writer)

        # Verify response was sent
        assert mock_send.called

    @pytest.mark.asyncio
    async def test_handle_server_messages_notification(self, router):
        """Test handling incoming notification from server."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()

        # Mock incoming notification
        notification_json = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "progress",
                "params": {"progress": 50},
            },
        )

        mock_reader.readline.side_effect = [
            (notification_json + "\n").encode(),
            b"",  # End of stream
        ]

        await router._handle_server_messages("test_server", mock_reader, mock_writer)

        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_handle_server_messages_cleanup(self, router):
        """Test that message handler cleans up properly."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()

        # Add server info that should be cleaned up
        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo("test_server", mock_connection, {}, [], [], [])
        router.servers["test_server"] = server_info
        router.server_streams["test_server"] = (mock_reader, mock_writer)

        # Mock reader to immediately close
        mock_reader.readline.return_value = b""

        await router._handle_server_messages("test_server", mock_reader, mock_writer)

        # Check cleanup occurred
        assert "test_server" not in router.servers
        assert "test_server" not in router.server_streams


class TestEdgeCasesAndErrors:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def router(self):
        """Create message router fixture."""
        return MCPMessageRouter()

    @pytest.mark.asyncio
    async def test_query_server_capabilities_no_server(self, router):
        """Test querying capabilities for non-existent server."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()

        # Should not raise exception, just return silently
        await router._query_server_capabilities("nonexistent", mock_writer, mock_reader)

    @pytest.mark.asyncio
    async def test_query_server_capabilities_success(self, router):
        """Test successful capability querying."""
        mock_connection = MagicMock(spec=ActiveConnection)
        server_info = MCPServerInfo(
            name="test_server",
            connection=mock_connection,
            capabilities={"tools": {"enabled": True}, "resources": {"enabled": True}, "prompts": {"enabled": True}},
            tools=[],
            resources=[],
            prompts=[],
        )
        router.servers["test_server"] = server_info

        mock_reader = AsyncMock()
        mock_writer = MagicMock()

        # Mock successful responses
        tools_response = {"tools": [{"name": "tool1"}, {"name": "tool2"}]}
        resources_response = {"resources": [{"uri": "resource1"}]}
        prompts_response = {"prompts": [{"name": "prompt1"}]}

        with patch.object(router, "_send_request_and_wait") as mock_send:
            mock_send.side_effect = [tools_response, resources_response, prompts_response]

            await router._query_server_capabilities("test_server", mock_writer, mock_reader)

        # Check that server info was updated - get fresh reference since it's modified in place
        updated_server_info = router.servers["test_server"]
        assert len(updated_server_info.tools) == 2
        assert len(updated_server_info.resources) == 1
        assert len(updated_server_info.prompts) == 1

    @pytest.mark.asyncio
    async def test_connect_server_unsupported_type(self, router):
        """Test connecting to server with unsupported connection type."""
        mock_connection = MagicMock(spec=ActiveConnection)
        mock_connection.connection = MagicMock()
        mock_connection.connection.type = "unsupported"

        result = await router.connect_server("test_server", mock_connection)

        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_server_no_response(self, router):
        """Test server initialization with no response."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        with patch.object(router, "_send_request_and_wait", return_value=None):
            result = await router._initialize_server("test_server", mock_reader, mock_writer)

        assert result is False

    def test_server_info_with_none_connection(self):
        """Test MCPServerInfo with None connection."""
        server_info = MCPServerInfo(
            name="test",
            connection=None,
            capabilities={},
            tools=[],
            resources=[],
            prompts=[],
        )

        assert server_info.connection is None
        assert server_info.name == "test"
