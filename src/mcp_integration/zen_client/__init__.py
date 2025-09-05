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
from .models import (
    # Request models
    RouteAnalysisRequest,
    SmartExecutionRequest,
    ModelListRequest,
    
    # Result models  
    AnalysisResult,
    ExecutionResult,
    ModelListResult,
    
    # Configuration models
    MCPConnectionConfig,
    FallbackConfig,
    
    # Status and monitoring models
    MCPConnectionStatus,
    MCPHealthCheck,
    BridgeMetrics,
    
    # MCP protocol models
    MCPToolCall,
    MCPToolResult,
)

from .subprocess_manager import ZenMCPProcess, ProcessPool
from .protocol_bridge import MCPProtocolBridge
from .error_handler import MCPConnectionManager, RetryHandler, CircuitBreakerState

__version__ = "1.0.0"
__author__ = "zen-mcp-server development team"

# Public API exports
__all__ = [
    # Main client classes
    "ZenMCPStdioClient",
    "create_client",
    
    # Request models for PromptCraft operations
    "RouteAnalysisRequest", 
    "SmartExecutionRequest",
    "ModelListRequest",
    
    # Result models
    "AnalysisResult",
    "ExecutionResult", 
    "ModelListResult",
    
    # Configuration
    "MCPConnectionConfig",
    "FallbackConfig",
    
    # Status and monitoring
    "MCPConnectionStatus",
    "MCPHealthCheck", 
    "BridgeMetrics",
    
    # Advanced usage (for custom integrations)
    "ZenMCPProcess",
    "ProcessPool",
    "MCPProtocolBridge",
    "MCPConnectionManager",
    "RetryHandler",
    "CircuitBreakerState",
    
    # MCP protocol types
    "MCPToolCall",
    "MCPToolResult",
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