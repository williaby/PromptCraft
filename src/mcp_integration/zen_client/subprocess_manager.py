"""
Subprocess Management for PromptCraft MCP Client

Handles the lifecycle of zen-mcp-server subprocess for stdio communication.
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from .models import MCPConnectionConfig, MCPConnectionStatus

logger = logging.getLogger(__name__)


class ZenMCPProcess:
    """
    Manages zen-mcp-server subprocess for MCP stdio communication.
    
    Features:
    - Process lifecycle management (start/stop/restart)
    - Environment variable handling
    - Health monitoring and auto-recovery
    - Graceful shutdown with cleanup
    """
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None
        self.last_health_check: Optional[float] = None
        self.error_count = 0
        
    async def start_server(self) -> bool:
        """
        Start the zen-mcp-server subprocess.
        
        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self.is_running():
            logger.info("Server is already running")
            return True
            
        try:
            # Prepare environment variables
            env = os.environ.copy()
            env.update(self.config.env_vars)
            
            # Determine server path
            server_path = self._resolve_server_path()
            if not server_path.exists():
                logger.error(f"Server executable not found: {server_path}")
                return False
            
            # Determine Python executable
            python_path = self._get_python_executable()
            
            logger.info(f"Starting zen-mcp-server: {python_path} {server_path}")
            
            # Start the subprocess
            self.process = subprocess.Popen(
                [str(python_path), str(server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,  # Line buffered
                cwd=server_path.parent,
            )
            
            # Give the process a moment to start
            await asyncio.sleep(0.5)
            
            # Check if process started successfully
            if self.process.poll() is not None:
                # Process already terminated
                stderr_output = self.process.stderr.read() if self.process.stderr else "No error output"
                logger.error(f"Server process terminated immediately: {stderr_output}")
                self.process = None
                return False
            
            self.start_time = time.time()
            self.error_count = 0
            logger.info(f"✅ zen-mcp-server started successfully (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start zen-mcp-server: {e}")
            if self.process:
                self.process.terminate()
                self.process = None
            return False

    async def stop_server(self) -> bool:
        """
        Stop the zen-mcp-server subprocess gracefully.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running():
            logger.info("Server is not running")
            return True
            
        try:
            logger.info(f"Stopping zen-mcp-server (PID: {self.process.pid})")
            
            # Try graceful shutdown first
            if self.process.stdin and not self.process.stdin.closed:
                try:
                    self.process.stdin.close()
                except Exception as e:
                    logger.warning(f"Error closing stdin: {e}")
            
            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_process_termination()),
                    timeout=5.0
                )
                logger.info("✅ Server stopped gracefully")
                return True
            except asyncio.TimeoutError:
                logger.warning("Graceful shutdown timeout, forcing termination")
                
            # Force termination if graceful shutdown failed
            if self.process.poll() is None:
                self.process.terminate()
                
                # Wait a bit more for terminate
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process_termination()),
                        timeout=3.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Terminate timeout, killing process")
                    self.process.kill()
                    await asyncio.create_task(self._wait_for_process_termination())
            
            self.process = None
            self.start_time = None
            logger.info("✅ Server stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the server process is running."""
        return self.process is not None and self.process.poll() is None

    def get_process_id(self) -> Optional[int]:
        """Get the process ID of the server."""
        return self.process.pid if self.process else None

    def get_uptime(self) -> Optional[float]:
        """Get server uptime in seconds."""
        return time.time() - self.start_time if self.start_time else None

    def get_status(self) -> MCPConnectionStatus:
        """Get current connection status."""
        return MCPConnectionStatus(
            connected=self.is_running(),
            process_id=self.get_process_id(),
            uptime=self.get_uptime(),
            last_activity=None,  # Will be updated by connection manager
            error_count=self.error_count,
        )

    async def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Perform health check on the server process.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_healthy, error_message)
        """
        try:
            if not self.is_running():
                return False, "Process is not running"
            
            # Check if process is responsive (basic check)
            if self.process.poll() is not None:
                return False, f"Process terminated with code {self.process.poll()}"
            
            # Check stderr for errors
            if self.process.stderr and self.process.stderr.readable():
                # Non-blocking read of stderr
                try:
                    import select
                    if select.select([self.process.stderr], [], [], 0)[0]:
                        error_output = self.process.stderr.read()
                        if error_output:
                            logger.warning(f"Server stderr output: {error_output}")
                except Exception:
                    pass  # Ignore select errors on Windows
            
            self.last_health_check = time.time()
            return True, None
            
        except Exception as e:
            error_msg = f"Health check failed: {e}"
            logger.error(error_msg)
            self.error_count += 1
            return False, error_msg

    async def restart_server(self) -> bool:
        """
        Restart the server process.
        
        Returns:
            bool: True if restart was successful, False otherwise
        """
        logger.info("Restarting zen-mcp-server...")
        await self.stop_server()
        await asyncio.sleep(1.0)  # Brief pause between stop and start
        return await self.start_server()

    def _resolve_server_path(self) -> Path:
        """Resolve the path to the zen-mcp-server executable."""
        server_path = Path(self.config.server_path)
        
        if server_path.is_absolute():
            return server_path
            
        # Try relative to current working directory
        cwd_path = Path.cwd() / server_path
        if cwd_path.exists():
            return cwd_path
            
        # Try relative to this module's directory
        module_dir = Path(__file__).parent.parent.parent.parent
        module_path = module_dir / server_path
        if module_path.exists():
            return module_path
            
        # Return original path (will fail later with clear error)
        return server_path

    def _get_python_executable(self) -> Path:
        """Get the appropriate Python executable for running the server."""
        # First, try to use the same Python executable as the current process
        current_python = Path(sys.executable)
        
        # Check if we're in a virtual environment
        if hasattr(sys, 'prefix') and hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix:
            # We're in a virtual environment, use current Python
            return current_python
        
        # Try to find .zen_venv Python
        project_root = Path(__file__).parent.parent.parent.parent
        zen_venv_python = project_root / ".zen_venv" / "bin" / "python"
        if zen_venv_python.exists():
            return zen_venv_python
            
        # Try to find .venv Python
        venv_python = project_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            return venv_python
        
        # Fallback to current Python executable
        return current_python

    async def _wait_for_process_termination(self):
        """Wait for the process to terminate."""
        if self.process:
            while self.process.poll() is None:
                await asyncio.sleep(0.1)


class ProcessPool:
    """
    Pool of MCP server processes for connection reuse and load balancing.
    
    Currently implements a simple single-process pool, but can be extended
    for multiple processes if needed.
    """
    
    def __init__(self, config: MCPConnectionConfig, pool_size: int = 1):
        self.config = config
        self.pool_size = pool_size
        self.processes: Dict[str, ZenMCPProcess] = {}
        self.current_process_id = "main"
        
    async def get_process(self, process_id: Optional[str] = None) -> Optional[ZenMCPProcess]:
        """
        Get a process from the pool, starting one if necessary.
        
        Args:
            process_id: Optional specific process ID, defaults to main process
            
        Returns:
            ZenMCPProcess instance or None if failed to start
        """
        process_id = process_id or self.current_process_id
        
        # Get existing process or create new one
        if process_id not in self.processes:
            self.processes[process_id] = ZenMCPProcess(self.config)
        
        process = self.processes[process_id]
        
        # Start process if not running
        if not process.is_running():
            if not await process.start_server():
                return None
                
        return process

    async def shutdown_all(self):
        """Shutdown all processes in the pool."""
        logger.info("Shutting down all processes in pool...")
        for process_id, process in self.processes.items():
            if process.is_running():
                await process.stop_server()
        self.processes.clear()
        logger.info("✅ All processes shut down")

    def get_pool_status(self) -> Dict[str, MCPConnectionStatus]:
        """Get status of all processes in the pool."""
        return {
            process_id: process.get_status() 
            for process_id, process in self.processes.items()
        }