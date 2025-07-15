# MCP Client Interface Usage Guide

This document provides guidance on using the new abstract MCP client interface implemented for PromptCraft-Hybrid.

## Overview

The MCP client interface provides a unified abstraction for integrating with MCP (Model Context Protocol) servers, with support for both development mock clients and production Zen MCP Server integration.

## Key Components

### Abstract Interface

```python
from src.mcp_integration.mcp_client import MCPClientInterface

# All MCP clients implement this interface
class MCPClientInterface(ABC):
    async def connect(self) -> bool
    async def disconnect(self) -> bool
    async def health_check(self) -> MCPHealthStatus
    async def validate_query(self, query: str) -> Dict[str, Any]
    async def orchestrate_agents(self, workflow_steps: List[WorkflowStep]) -> List[Response]
    async def get_capabilities(self) -> List[str]
```

### Factory Pattern

```python
from src.mcp_integration.mcp_client import MCPClientFactory

# Create mock client for development
mock_client = MCPClientFactory.create_client("mock")

# Create Zen MCP client for production
zen_client = MCPClientFactory.create_client(
    "zen",
    server_url="http://zen-mcp-server:3000",
    api_key="your-api-key"
)
```

### Error Handling

```python
from src.mcp_integration.mcp_client import (
    MCPError,
    MCPConnectionError,
    MCPTimeoutError,
    MCPServiceUnavailableError
)

try:
    responses = await client.orchestrate_agents(workflow_steps)
except MCPConnectionError as e:
    logger.error(f"Connection failed: {e}")
    # Handle connection issues
except MCPTimeoutError as e:
    logger.error(f"Operation timed out: {e.timeout_seconds}s")
    # Handle timeout scenarios
except MCPServiceUnavailableError as e:
    logger.error(f"Service unavailable, retry in {e.retry_after}s")
    # Handle service unavailability
```

## Mock Client Usage

The mock client simulates MCP server behavior for development and testing:

```python
from src.mcp_integration.mcp_client import MockMCPClient

# Create with failure simulation for testing error handling
client = MockMCPClient(
    simulate_failures=True,
    failure_rate=0.1,  # 10% failure rate
    response_delay=0.1  # 100ms simulated delay
)

await client.connect()
health = await client.health_check()
responses = await client.orchestrate_agents(workflow_steps)
await client.disconnect()
```

## Zen MCP Client Usage

The Zen MCP client integrates with the real Zen MCP Server:

```python
from src.mcp_integration.mcp_client import ZenMCPClient

client = ZenMCPClient(
    server_url="http://zen-mcp-server:3000",
    api_key="your-api-key",
    timeout=30.0,
    max_retries=3
)

# Note: Real implementation will be completed in Week 2
await client.connect()
responses = await client.orchestrate_agents(workflow_steps)
await client.disconnect()
```

## Connection Manager

For production use, the connection manager provides automatic health monitoring and circuit breaker functionality:

```python
from src.mcp_integration.mcp_client import MCPConnectionManager

client = MCPClientFactory.create_client("zen", server_url="...")
manager = MCPConnectionManager(
    client=client,
    health_check_interval=30.0,
    max_consecutive_failures=5,
    circuit_breaker_timeout=60.0
)

await manager.start()

# Execute operations with automatic fallback
result = await manager.execute_with_fallback(
    "orchestrate_agents",
    workflow_steps
)

await manager.stop()
```

## Integration with QueryCounselor

The QueryCounselor now uses the MCP client interface:

```python
from src.core.query_counselor import QueryCounselor
from src.mcp_integration.mcp_client import MCPClientFactory

# Use mock client for development
mock_client = MCPClientFactory.create_client("mock")
counselor = QueryCounselor(mcp_client=mock_client)

# Use Zen client for production
zen_client = MCPClientFactory.create_client("zen", server_url="...")
counselor = QueryCounselor(mcp_client=zen_client)

# QueryCounselor automatically handles MCP errors gracefully
intent = await counselor.analyze_intent("Create a prompt template")
agents = await counselor.select_agents(intent)
responses = await counselor.orchestrate_workflow(agents, "query")
final_response = await counselor.synthesize_response(responses)
```

## Health Monitoring

The health status provides comprehensive monitoring information:

```python
health = await client.health_check()

print(f"Connection State: {health.connection_state}")
print(f"Response Time: {health.response_time_ms}ms")
print(f"Error Count: {health.error_count}")
print(f"Capabilities: {health.capabilities}")
print(f"Server Version: {health.server_version}")
```

## Best Practices

### Development Phase

1. Use `MockMCPClient` for initial development and unit testing
2. Enable failure simulation to test error handling paths
3. Use factory pattern for easy switching between implementations

### Production Phase

1. Use `ZenMCPClient` with `MCPConnectionManager` for robust operation
2. Configure appropriate timeouts and retry parameters
3. Monitor health status and handle degraded states
4. Implement proper logging and alerting for MCP errors

### Error Handling

1. Always catch specific MCP error types for appropriate handling
2. Implement graceful fallback for service unavailability
3. Use circuit breaker pattern to prevent cascading failures
4. Provide user-friendly error messages with actionable guidance

## Implementation Status

- ✅ Abstract interface and base classes
- ✅ Mock client implementation with error simulation
- ✅ Comprehensive error handling and typing
- ✅ Connection manager with circuit breaker
- ✅ Integration with QueryCounselor
- 🔄 Zen MCP client (placeholder - Week 2 implementation)
- 🔄 Real MCP protocol integration (Week 2)
- 🔄 Production health monitoring (Week 2)

## Next Steps

Week 2 implementation will include:

1. Complete Zen MCP Server integration with real protocol
2. HTTP client session management and connection pooling
3. Authentication and security implementation
4. Production health monitoring and metrics
5. Performance optimization for <2s response time requirement
6. Integration testing with real Zen MCP Server
