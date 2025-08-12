"""
MCP Integration Module for PromptCraft-Hybrid.

This module provides integration capabilities with Model Context Protocol (MCP) servers,
enabling PromptCraft to communicate with external services and orchestration systems.
The primary integration is with the Zen MCP Server for agent coordination and management.

Key Integrations:
    - Zen MCP Server: Agent orchestration and multi-agent coordination
    - Docker MCP Toolkit: Universal IDE access with ≤2GB memory servers
    - External MCP services: Additional protocol-compliant services
    - Protocol handling: MCP message serialization and deserialization
    - Connection management: Persistent connections and reconnection logic
    - Smart routing: Automatic fallback between Docker and self-hosted deployments

Architecture:
    The MCP integration layer acts as a bridge between PromptCraft's internal
    agent system and external MCP-compliant services. It provides:

    - Protocol abstraction for MCP communication
    - Connection pooling and management
    - Error handling and resilience patterns
    - Message routing and transformation
    - Authentication and security for external connections
    - Smart routing between Docker MCP Toolkit and self-hosted deployments
    - Capability mapping and feature detection for optimal client selection
    - Graceful fallback mechanisms for enhanced reliability

Zen MCP Server Integration:
    The Zen MCP Server provides sophisticated agent orchestration capabilities:
    - Multi-agent coordination and consensus building
    - Advanced reasoning workflows (O3, Gemini models)
    - Quality gate enforcement and validation
    - Comprehensive analysis and review cycles
    - Integration testing and security scanning

Usage:
    This module is typically imported by core business logic components
    that need to communicate with external MCP services:

    **RECOMMENDED USAGE:**
    >>> from src.mcp_integration import HybridRouter  # Primary entry point for most use cases
    >>> from src.mcp_integration import MCPClientFactory  # For configuration-driven client creation
    >>> from src.mcp_integration import ZenMCPClient  # Direct Zen MCP Server integration

    **COMPONENT OVERVIEW:**
    - HybridRouter: Primary entry point - intelligent routing between OpenRouter and MCP services
    - MCPClientFactory: Configuration-driven client creation with automatic fallbacks
    - ZenMCPClient: Direct integration with Zen MCP Server (now integrated via Docker)
    - DockerMCPClient: Docker-based MCP integration for containerized environments
    - MCPClient: DEPRECATED - Legacy placeholder implementation, use HybridRouter instead

Dependencies:
    - src.config: For MCP server configuration and connection settings
    - src.utils.resilience: For connection resilience and retry patterns
    - src.utils.logging_mixin: For standardized logging across MCP operations
    - External MCP servers: Zen MCP Server and other protocol-compliant services

Called by:
    - src/core: For agent orchestration and enhanced processing
    - src/agents: For external agent coordination and management
    - src/main.py: For MCP service initialization and health checks

Time Complexity: O(1) for connection management, O(n) for message processing
Space Complexity: O(k) where k is the number of active MCP connections
"""

from .client import MCPClient
from .config_manager import MCPConfigurationManager
from .docker_mcp_client import DockerMCPClient
from .hybrid_router import (
    HybridRouter,
    RoutingDecision,
    RoutingMetrics,
    RoutingStrategy,
)
from .mcp_client import (
    MCPClientFactory,
    MCPClientInterface,
    MCPConnectionError,
    MCPConnectionManager,
    MCPConnectionState,
    MCPError,
    MCPErrorType,
    MCPHealthStatus,
    MCPRateLimitError,
    MCPServiceUnavailableError,
    MCPTimeoutError,
    MockMCPClient,
    ZenMCPClient,
)
from .openrouter_client import OpenRouterClient
from .parallel_executor import ParallelSubagentExecutor

__all__ = [
    "DockerMCPClient",
    "HybridRouter",
    "MCPClient",
    "MCPClientFactory",
    "MCPClientInterface",
    "MCPConfigurationManager",
    "MCPConnectionError",
    "MCPConnectionManager",
    "MCPConnectionState",
    "MCPError",
    "MCPErrorType",
    "MCPHealthStatus",
    "MCPRateLimitError",
    "MCPServiceUnavailableError",
    "MCPTimeoutError",
    "MockMCPClient",
    "ModelCapabilities",
    "ModelRegistry",
    "OpenRouterClient",
    "ParallelSubagentExecutor",
    "RoutingDecision",
    "RoutingMetrics",
    "RoutingStrategy",
    "ZenMCPClient",
]
