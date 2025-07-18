#!/usr/bin/env python3
"""Debug the routing logic to understand the gradual rollout issue."""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp_integration.hybrid_router import HybridRouter, RoutingStrategy
from src.mcp_integration.mcp_client import MCPConnectionState

# Create mock clients
mock_openrouter_client = Mock()
mock_openrouter_client.connection_state = MCPConnectionState.CONNECTED

mock_mcp_client = Mock()
mock_mcp_client.connection_state = MCPConnectionState.CONNECTED

# Create router with gradual rollout
router = HybridRouter(
    openrouter_client=mock_openrouter_client,
    mcp_client=mock_mcp_client,
    strategy=RoutingStrategy.OPENROUTER_PRIMARY,
    enable_gradual_rollout=True,
)

print(f"Initial traffic percentage: {router.openrouter_traffic_percentage}")
print(f"Gradual rollout enabled: {router.enable_gradual_rollout}")

# Set traffic percentage
router.set_traffic_percentage(50)

print(f"After setting traffic percentage: {router.openrouter_traffic_percentage}")

# Test a few routing decisions
openrouter_count = 0
mcp_count = 0

for i in range(10):
    decision = router._make_routing_decision(f"request_{i}", "orchestration")
    print(f"Request {i}: {decision.service} - {decision.reason}")
    
    if decision.service == "openrouter":
        openrouter_count += 1
    else:
        mcp_count += 1

print(f"OpenRouter count: {openrouter_count}")
print(f"MCP count: {mcp_count}")