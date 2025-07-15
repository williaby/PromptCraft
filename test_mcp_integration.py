#!/usr/bin/env python3
"""
Quick test script to validate MCP integration imports and basic functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.query_counselor import QueryCounselor
from src.mcp_integration.mcp_client import (
    MCPClientFactory,
    WorkflowStep,
)


async def test_mock_mcp_client():
    """Test basic MockMCPClient functionality."""
    print("Testing MockMCPClient...")

    # Create mock client
    client = MCPClientFactory.create_client("mock")

    # Test connection
    connected = await client.connect()
    print(f"Connection successful: {connected}")

    # Test health check
    health = await client.health_check()
    print(f"Health status: {health.connection_state}")
    print(f"Capabilities: {health.capabilities}")

    # Test query validation
    validation = await client.validate_query("Test query")
    print(f"Query validation: {validation}")

    # Test workflow orchestration
    steps = [
        WorkflowStep(
            step_id="test_step_1",
            agent_id="test_agent",
            input_data={"query": "test", "agent_type": "general"},
        ),
    ]

    responses = await client.orchestrate_agents(steps)
    print(f"Orchestration responses: {len(responses)}")

    # Test disconnection
    disconnected = await client.disconnect()
    print(f"Disconnection successful: {disconnected}")

    print("MockMCPClient test completed successfully!")


async def test_query_counselor_integration():
    """Test QueryCounselor with new MCP client integration."""
    print("\nTesting QueryCounselor integration...")

    # Create query counselor with default mock client
    counselor = QueryCounselor()

    # Test intent analysis
    intent = await counselor.analyze_intent("Create a prompt template for code analysis")
    print(f"Intent analysis: {intent.query_type}, confidence: {intent.confidence}")

    # Test agent selection
    agents = await counselor.select_agents(intent)
    print(f"Selected agents: {[a.agent_id for a in agents]}")

    # Test workflow orchestration
    responses = await counselor.orchestrate_workflow(agents, "Test query")
    print(f"Workflow responses: {len(responses)}")

    # Test response synthesis
    final_response = await counselor.synthesize_response(responses)
    print(f"Final response confidence: {final_response.confidence}")
    print(f"Final response agents: {final_response.agents_used}")

    print("QueryCounselor integration test completed successfully!")


async def main():
    """Run all tests."""
    try:
        await test_mock_mcp_client()
        await test_query_counselor_integration()
        print("\n✅ All tests passed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
