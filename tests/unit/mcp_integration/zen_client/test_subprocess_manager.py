"""Comprehensive tests for subprocess management components."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.mcp_integration.zen_client.models import MCPConnectionStatus
from src.mcp_integration.zen_client.subprocess_manager import ProcessPool, ZenMCPProcess


class TestZenMCPProcess:
    """Test ZenMCPProcess functionality."""

    def test_initialization(self, connection_config):
        """Test ZenMCPProcess initialization."""
        process = ZenMCPProcess(connection_config)

        assert process.config == connection_config
        assert process.process is None
        assert process.start_time is None
        assert process.last_health_check is None
        assert process.error_count == 0

    @pytest.mark.asyncio
    async def test_start_server_success(self, connection_config, mock_subprocess, temp_server_file):
        """Test successful server startup."""
        # Update config to use temp file
        connection_config.server_path = str(temp_server_file)
        process = ZenMCPProcess(connection_config)

        # Mock successful process start
        mock_subprocess.poll.return_value = None  # Process running

        result = await process.start_server()

        assert result is True
        assert process.process is not None
        assert process.start_time is not None
        assert process.error_count == 0

    @pytest.mark.asyncio
    async def test_start_server_already_running(self, connection_config, mock_subprocess):
        """Test start server when already running."""
        process = ZenMCPProcess(connection_config)

        # Set up running process
        process.process = mock_subprocess

        with patch.object(process, "is_running", return_value=True):
            result = await process.start_server()

        assert result is True

    @pytest.mark.asyncio
    async def test_start_server_file_not_found(self, connection_config):
        """Test start server with non-existent server file."""
        connection_config.server_path = "/non/existent/server.py"
        process = ZenMCPProcess(connection_config)

        result = await process.start_server()

        assert result is False

    @pytest.mark.asyncio
    async def test_start_server_immediate_termination(self, connection_config, temp_server_file):
        """Test start server when process terminates immediately."""
        connection_config.server_path = str(temp_server_file)
        process = ZenMCPProcess(connection_config)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = 1  # Process terminated
            mock_process.stderr.read.return_value = "Server failed to start"
            mock_popen.return_value = mock_process

            result = await process.start_server()

        assert result is False
        assert process.process is None

    @pytest.mark.asyncio
    async def test_start_server_exception(self, connection_config, temp_server_file):
        """Test start server exception handling."""
        connection_config.server_path = str(temp_server_file)
        process = ZenMCPProcess(connection_config)

        with patch("subprocess.Popen", side_effect=Exception("Subprocess error")):
            result = await process.start_server()

        assert result is False

    @pytest.mark.asyncio
    async def test_start_server_with_env_vars(self, connection_config, temp_server_file):
        """Test start server with environment variables."""
        connection_config.server_path = str(temp_server_file)
        connection_config.env_vars = {"TEST_VAR": "test_value"}
        process = ZenMCPProcess(connection_config)

        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            result = await process.start_server()

            # Verify environment variables were passed
            call_args = mock_popen.call_args
            env_arg = call_args[1]["env"]
            assert env_arg["TEST_VAR"] == "test_value"

        assert result is True

    @pytest.mark.asyncio
    async def test_stop_server_graceful(self, connection_config, mock_subprocess):
        """Test graceful server shutdown."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        # Mock graceful shutdown
        mock_subprocess.stdin.closed = False
        process._wait_for_process_termination = AsyncMock()

        result = await process.stop_server()

        assert result is True
        assert process.process is None
        assert process.start_time is None

    @pytest.mark.asyncio
    async def test_stop_server_not_running(self, connection_config):
        """Test stop server when not running."""
        process = ZenMCPProcess(connection_config)

        result = await process.stop_server()

        assert result is True

    @pytest.mark.asyncio
    async def test_stop_server_force_termination(self, connection_config, mock_subprocess):
        """Test forced server termination."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        # Mock timeout on graceful shutdown
        async def mock_wait_timeout(*args, **kwargs):
            raise TimeoutError()

        mock_subprocess.stdin.closed = False
        mock_subprocess.poll.return_value = None  # Still running

        with patch("asyncio.wait_for", side_effect=mock_wait_timeout):
            with patch.object(process, "_wait_for_process_termination", new_callable=AsyncMock):
                result = await process.stop_server()

        mock_subprocess.terminate.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_stop_server_force_kill(self, connection_config, mock_subprocess):
        """Test forced server kill."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        # Mock timeout on both graceful and terminate
        async def mock_wait_timeout(*args, **kwargs):
            raise TimeoutError()

        mock_subprocess.stdin.closed = False
        mock_subprocess.poll.return_value = None  # Still running

        with patch("asyncio.wait_for", side_effect=mock_wait_timeout):
            with patch.object(process, "_wait_for_process_termination", new_callable=AsyncMock):
                result = await process.stop_server()

        mock_subprocess.terminate.assert_called_once()
        mock_subprocess.kill.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_stop_server_exception(self, connection_config, mock_subprocess):
        """Test stop server exception handling."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        mock_subprocess.stdin.close.side_effect = Exception("Close error")
        process._wait_for_process_termination = AsyncMock()

        result = await process.stop_server()

        assert result is True  # Should still succeed despite exception

    def test_is_running_true(self, connection_config, mock_subprocess):
        """Test is_running when process is running."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        mock_subprocess.poll.return_value = None  # Running

        assert process.is_running() is True

    def test_is_running_false_no_process(self, connection_config):
        """Test is_running when no process."""
        process = ZenMCPProcess(connection_config)

        assert process.is_running() is False

    def test_is_running_false_terminated(self, connection_config, mock_subprocess):
        """Test is_running when process terminated."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        mock_subprocess.poll.return_value = 1  # Terminated

        assert process.is_running() is False

    def test_get_process_id(self, connection_config, mock_subprocess):
        """Test getting process ID."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        assert process.get_process_id() == 12345

    def test_get_process_id_no_process(self, connection_config):
        """Test getting process ID when no process."""
        process = ZenMCPProcess(connection_config)

        assert process.get_process_id() is None

    def test_get_uptime(self, connection_config, mock_time):
        """Test getting process uptime."""
        process = ZenMCPProcess(connection_config)
        process.start_time = 1641547700.0  # 100 seconds ago

        uptime = process.get_uptime()

        assert uptime == 100.0

    def test_get_uptime_no_start_time(self, connection_config):
        """Test getting uptime when no start time."""
        process = ZenMCPProcess(connection_config)

        assert process.get_uptime() is None

    def test_get_status(self, connection_config, mock_subprocess, mock_time):
        """Test getting process status."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess
        process.start_time = 1641547700.0
        process.error_count = 2

        mock_subprocess.poll.return_value = None  # Running

        status = process.get_status()

        assert isinstance(status, MCPConnectionStatus)
        assert status.connected is True
        assert status.process_id == 12345
        assert status.uptime == 100.0
        assert status.error_count == 2

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, connection_config, mock_subprocess, mock_time):
        """Test health check when process is healthy."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        mock_subprocess.poll.return_value = None  # Running
        mock_subprocess.stderr.readable.return_value = False

        is_healthy, error_msg = await process.health_check()

        assert is_healthy is True
        assert error_msg is None
        assert process.last_health_check is not None

    @pytest.mark.asyncio
    async def test_health_check_not_running(self, connection_config):
        """Test health check when process not running."""
        process = ZenMCPProcess(connection_config)

        is_healthy, error_msg = await process.health_check()

        assert is_healthy is False
        assert "Process is not running" in error_msg

    @pytest.mark.asyncio
    async def test_health_check_terminated(self, connection_config, mock_subprocess):
        """Test health check when process terminated."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        mock_subprocess.poll.return_value = 1  # Terminated

        is_healthy, error_msg = await process.health_check()

        assert is_healthy is False
        assert "Process terminated with code 1" in error_msg

    @pytest.mark.asyncio
    async def test_health_check_stderr_output(self, connection_config, mock_subprocess):
        """Test health check with stderr output."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        mock_subprocess.poll.return_value = None
        mock_subprocess.stderr.readable.return_value = True
        mock_subprocess.stderr.read.return_value = "Warning: high memory usage"

        with patch("select.select", return_value=([mock_subprocess.stderr], [], [])):
            is_healthy, error_msg = await process.health_check()

        assert is_healthy is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_health_check_exception(self, connection_config):
        """Test health check exception handling."""
        process = ZenMCPProcess(connection_config)

        # Force exception during health check
        with patch.object(process, "is_running", side_effect=Exception("Health check error")):
            is_healthy, error_msg = await process.health_check()

        assert is_healthy is False
        assert "Health check failed" in error_msg
        assert process.error_count == 1

    @pytest.mark.asyncio
    async def test_restart_server(self, connection_config, mock_subprocess, temp_server_file):
        """Test server restart."""
        connection_config.server_path = str(temp_server_file)
        process = ZenMCPProcess(connection_config)

        # Mock successful restart
        process.stop_server = AsyncMock(return_value=True)
        process.start_server = AsyncMock(return_value=True)

        result = await process.restart_server()

        assert result is True
        process.stop_server.assert_called_once()
        process.start_server.assert_called_once()

    def test_resolve_server_path_absolute(self, connection_config):
        """Test resolving absolute server path."""
        connection_config.server_path = "/absolute/path/server.py"
        process = ZenMCPProcess(connection_config)

        resolved = process._resolve_server_path()

        assert resolved == Path("/absolute/path/server.py")

    def test_resolve_server_path_relative_cwd(self, connection_config, temp_server_file):
        """Test resolving relative server path from CWD."""
        # Create relative path from temp file
        relative_path = temp_server_file.name
        connection_config.server_path = relative_path
        process = ZenMCPProcess(connection_config)

        with patch("pathlib.Path.cwd", return_value=temp_server_file.parent):
            resolved = process._resolve_server_path()

        assert resolved.name == relative_path

    def test_resolve_server_path_relative_module(self, connection_config):
        """Test resolving relative server path from module directory."""
        connection_config.server_path = "non_existent.py"
        process = ZenMCPProcess(connection_config)

        resolved = process._resolve_server_path()

        # Should return original path when not found
        assert resolved.name == "non_existent.py"

    def test_get_python_executable_current(self, connection_config):
        """Test getting current Python executable."""
        process = ZenMCPProcess(connection_config)

        executable = process._get_python_executable()

        assert executable == Path(sys.executable)

    def test_get_python_executable_venv(self, connection_config):
        """Test getting Python executable in virtual environment."""
        process = ZenMCPProcess(connection_config)

        with (
            patch("sys.prefix", "/venv/path"),
            patch("sys.base_prefix", "/system/python"),
            patch("hasattr", return_value=True),
        ):
            executable = process._get_python_executable()

        assert executable == Path(sys.executable)

    def test_get_python_executable_zen_venv(self, connection_config, tmp_path):
        """Test getting Python executable from .zen_venv."""
        process = ZenMCPProcess(connection_config)

        # Create mock .zen_venv structure
        zen_venv = tmp_path / ".zen_venv" / "bin" / "python"
        zen_venv.parent.mkdir(parents=True)
        zen_venv.touch()

        with patch("pathlib.Path.__file__", str(tmp_path / "module.py")):
            with patch.object(Path, "parent", tmp_path):
                executable = process._get_python_executable()

        # Should find zen_venv python (mocked logic)
        assert isinstance(executable, Path)

    @pytest.mark.asyncio
    async def test_wait_for_process_termination(self, connection_config, mock_subprocess):
        """Test waiting for process termination."""
        process = ZenMCPProcess(connection_config)
        process.process = mock_subprocess

        # Mock process termination after some polls
        poll_count = 0

        def mock_poll():
            nonlocal poll_count
            poll_count += 1
            return None if poll_count < 3 else 0

        mock_subprocess.poll.side_effect = mock_poll

        await process._wait_for_process_termination()

        assert poll_count == 3


class TestProcessPool:
    """Test ProcessPool functionality."""

    def test_initialization(self, connection_config):
        """Test ProcessPool initialization."""
        pool = ProcessPool(connection_config, pool_size=3)

        assert pool.config == connection_config
        assert pool.pool_size == 3
        assert pool.current_process_id == "main"
        assert len(pool.processes) == 0

    def test_initialization_default_pool_size(self, connection_config):
        """Test ProcessPool initialization with default pool size."""
        pool = ProcessPool(connection_config)

        assert pool.pool_size == 1

    @pytest.mark.asyncio
    async def test_get_process_new(self, connection_config, temp_server_file):
        """Test getting new process from pool."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config)

        with patch.object(ZenMCPProcess, "start_server", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = True

            process = await pool.get_process()

        assert process is not None
        assert isinstance(process, ZenMCPProcess)
        assert "main" in pool.processes
        mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_process_existing_running(self, connection_config):
        """Test getting existing running process from pool."""
        pool = ProcessPool(connection_config)

        # Create mock running process
        mock_process = Mock(spec=ZenMCPProcess)
        mock_process.is_running.return_value = True
        pool.processes["main"] = mock_process

        process = await pool.get_process()

        assert process is mock_process
        mock_process.start_server.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_process_existing_not_running(self, connection_config, temp_server_file):
        """Test getting existing non-running process from pool."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config)

        # Create mock non-running process
        mock_process = Mock(spec=ZenMCPProcess)
        mock_process.is_running.return_value = False
        mock_process.start_server = AsyncMock(return_value=True)
        pool.processes["main"] = mock_process

        process = await pool.get_process()

        assert process is mock_process
        mock_process.start_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_process_start_failure(self, connection_config, temp_server_file):
        """Test getting process when start fails."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config)

        with patch.object(ZenMCPProcess, "start_server", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = False

            process = await pool.get_process()

        assert process is None

    @pytest.mark.asyncio
    async def test_get_process_custom_id(self, connection_config, temp_server_file):
        """Test getting process with custom process ID."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config)

        with patch.object(ZenMCPProcess, "start_server", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = True

            process = await pool.get_process("custom")

        assert process is not None
        assert "custom" in pool.processes
        assert "main" not in pool.processes

    @pytest.mark.asyncio
    async def test_shutdown_all(self, connection_config):
        """Test shutting down all processes in pool."""
        pool = ProcessPool(connection_config)

        # Create mock processes
        mock_process1 = Mock(spec=ZenMCPProcess)
        mock_process1.is_running.return_value = True
        mock_process1.stop_server = AsyncMock()

        mock_process2 = Mock(spec=ZenMCPProcess)
        mock_process2.is_running.return_value = False
        mock_process2.stop_server = AsyncMock()

        pool.processes["proc1"] = mock_process1
        pool.processes["proc2"] = mock_process2

        await pool.shutdown_all()

        mock_process1.stop_server.assert_called_once()
        mock_process2.stop_server.assert_called_once()
        assert len(pool.processes) == 0

    def test_get_pool_status(self, connection_config):
        """Test getting pool status."""
        pool = ProcessPool(connection_config)

        # Create mock processes
        mock_status1 = MCPConnectionStatus(connected=True, process_id=123)
        mock_status2 = MCPConnectionStatus(connected=False, process_id=None)

        mock_process1 = Mock(spec=ZenMCPProcess)
        mock_process1.get_status.return_value = mock_status1

        mock_process2 = Mock(spec=ZenMCPProcess)
        mock_process2.get_status.return_value = mock_status2

        pool.processes["proc1"] = mock_process1
        pool.processes["proc2"] = mock_process2

        status = pool.get_pool_status()

        assert len(status) == 2
        assert status["proc1"] == mock_status1
        assert status["proc2"] == mock_status2


class TestSubprocessManagerIntegration:
    """Test integration between subprocess management components."""

    @pytest.mark.asyncio
    async def test_pool_process_lifecycle(self, connection_config, temp_server_file):
        """Test complete process lifecycle through pool."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config, pool_size=2)

        with (
            patch.object(ZenMCPProcess, "start_server", new_callable=AsyncMock) as mock_start,
            patch.object(ZenMCPProcess, "stop_server", new_callable=AsyncMock) as mock_stop,
        ):

            mock_start.return_value = True
            mock_stop.return_value = True

            # Get processes
            process1 = await pool.get_process("worker1")
            process2 = await pool.get_process("worker2")

            assert process1 is not None
            assert process2 is not None
            assert len(pool.processes) == 2

            # Shutdown all
            await pool.shutdown_all()

            assert mock_stop.call_count == 2
            assert len(pool.processes) == 0

    @pytest.mark.asyncio
    async def test_process_restart_through_pool(self, connection_config, temp_server_file):
        """Test process restart through pool management."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config)

        with (
            patch.object(ZenMCPProcess, "start_server", new_callable=AsyncMock) as mock_start,
            patch.object(ZenMCPProcess, "restart_server", new_callable=AsyncMock) as mock_restart,
        ):

            mock_start.return_value = True
            mock_restart.return_value = True

            # Get initial process
            process = await pool.get_process()
            assert process is not None

            # Restart process
            await process.restart_server()

            mock_restart.assert_called_once()

    def test_subprocess_scenarios_healthy(self, subprocess_scenarios, connection_config):
        """Test subprocess scenarios for healthy process."""
        scenario = subprocess_scenarios["healthy"]
        process = ZenMCPProcess(connection_config)

        mock_process = Mock()
        mock_process.poll.return_value = scenario["poll_result"]
        process.process = mock_process

        assert process.is_running() is True

    def test_subprocess_scenarios_crashed(self, subprocess_scenarios, connection_config):
        """Test subprocess scenarios for crashed process."""
        scenario = subprocess_scenarios["crashed"]
        process = ZenMCPProcess(connection_config)

        mock_process = Mock()
        mock_process.poll.return_value = scenario["poll_result"]
        process.process = mock_process

        assert process.is_running() is False

    @pytest.mark.asyncio
    async def test_multiple_pool_instances(self, connection_config, temp_server_file):
        """Test multiple pool instances with different configurations."""
        connection_config.server_path = str(temp_server_file)

        pool1 = ProcessPool(connection_config, pool_size=1)
        pool2 = ProcessPool(connection_config, pool_size=3)

        assert pool1.pool_size == 1
        assert pool2.pool_size == 3

        # Pools should be independent
        with patch.object(ZenMCPProcess, "start_server", new_callable=AsyncMock, return_value=True):
            process1 = await pool1.get_process("test")
            process2 = await pool2.get_process("test")

        assert len(pool1.processes) == 1
        assert len(pool2.processes) == 1
        assert pool1.processes["test"] is not pool2.processes["test"]

    @pytest.mark.asyncio
    async def test_concurrent_process_access(self, connection_config, temp_server_file):
        """Test concurrent access to the same process in pool."""
        connection_config.server_path = str(temp_server_file)
        pool = ProcessPool(connection_config)

        start_call_count = 0

        async def mock_start_server(self):
            nonlocal start_call_count
            start_call_count += 1
            await asyncio.sleep(0.1)  # Simulate startup time
            return True

        with patch.object(ZenMCPProcess, "start_server", mock_start_server):
            # Multiple concurrent requests for same process
            tasks = [pool.get_process("main") for _ in range(3)]
            results = await asyncio.gather(*tasks)

        # All should get the same process instance
        assert all(result is not None for result in results)
        assert all(result is results[0] for result in results[1:])
        # But start should only be called once
        assert start_call_count == 1
