"""
PromptCraft MCP Stdio Client Library

Python library for integrating PromptCraft applications with zen-mcp-server
via native MCP stdio protocol. Provides high-level interface with automatic
fallback, error handling, and performance optimization.

Features:
- Native MCP stdio communication
- Automatic HTTP fallback on failures
- Subprocess management and connection pooling
- Circuit breaker pattern for reliability
- Comprehensive error handling and retry logic
- Performance metrics and health monitoring

Usage:
    Basic usage with context manager:
    
    ```python
    from promptcraft_mcp_client import ZenMCPStdioClient
    from promptcraft_mcp_client.models import RouteAnalysisRequest
    
    async with ZenMCPStdioClient("/path/to/server.py") as client:
        request = RouteAnalysisRequest(
            prompt="Write Python code to sort a list",
            user_tier="full"
        )
        result = await client.analyze_route(request)
        print(result.analysis)
    ```
    
    Or create client directly:
    
    ```python
    from promptcraft_mcp_client import create_client
    
    client = await create_client(
        server_path="/path/to/zen-mcp-server/server.py",
        env_vars={"LOG_LEVEL": "INFO"},
        http_fallback_url="http://localhost:8000"
    )
    
    # Use client...
    await client.disconnect()
    ```
"""

from .client import ZenMCPStdioClient, create_client
from .error_handler import CircuitBreakerState, MCPConnectionManager, RetryHandler
from .models import (
    # Result models
    AnalysisResult,
    BridgeMetrics,
    ExecutionResult,
    FallbackConfig,
    # Configuration models
    MCPConnectionConfig,
    # Status and monitoring models
    MCPConnectionStatus,
    MCPHealthCheck,
    # MCP protocol models
    MCPToolCall,
    MCPToolResult,
    ModelListRequest,
    ModelListResult,
    # Request models
    RouteAnalysisRequest,
    SmartExecutionRequest,
)
from .protocol_bridge import MCPProtocolBridge
from .subprocess_manager import ProcessPool, ZenMCPProcess


__version__ = "1.0.0"
__author__ = "zen-mcp-server development team"

# Public API exports
__all__ = [
    # Result models
    "AnalysisResult",
    "BridgeMetrics",
    "CircuitBreakerState",
    "ExecutionResult",
    "FallbackConfig",
    # Configuration
    "MCPConnectionConfig",
    "MCPConnectionManager",
    # Status and monitoring
    "MCPConnectionStatus",
    "MCPHealthCheck",
    "MCPProtocolBridge",
    # MCP protocol types
    "MCPToolCall",
    "MCPToolResult",
    "ModelListRequest",
    "ModelListResult",
    "ProcessPool",
    "RetryHandler",
    # Request models for PromptCraft operations
    "RouteAnalysisRequest",
    "SmartExecutionRequest",
    # Advanced usage (for custom integrations)
    "ZenMCPProcess",
    # Main client classes
    "ZenMCPStdioClient",
    "create_client",
]

# Library metadata
LIBRARY_INFO = {
    "name": "promptcraft_mcp_client",
    "version": __version__,
    "description": "MCP stdio client library for PromptCraft integration with zen-mcp-server",
    "features": [
        "Native MCP stdio communication",
        "Automatic HTTP fallback",
        "Process lifecycle management",
        "Circuit breaker reliability patterns",
        "Performance monitoring",
        "Comprehensive error handling",
    ],
    "compatibility": {
        "zen_mcp_server": ">=1.0.0",
        "python": ">=3.9",
        "mcp_protocol": ">=1.0.0",
    },
}


def get_library_info() -> dict:
    """Get library information and metadata."""
    return LIBRARY_INFO.copy()


def get_version() -> str:
    """Get library version string."""
    return __version__
