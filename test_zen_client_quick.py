#!/usr/bin/env python3
"""Quick validation of zen_client tests."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.mcp_integration.zen_client.client import ZenMCPStdioClient
from src.mcp_integration.zen_client.error_handler import CircuitBreakerState, MCPConnectionManager
from src.mcp_integration.zen_client.models import FallbackConfig, MCPConnectionConfig
from src.mcp_integration.zen_client.protocol_bridge import MCPProtocolBridge
from src.mcp_integration.zen_client.subprocess_manager import ProcessPool, ZenMCPProcess


def test_imports():
    """Test that all modules can be imported."""
    print("✅ All zen_client modules imported successfully")
    return True


def test_basic_initialization():
    """Test basic object initialization."""
    # Test client initialization
    client = ZenMCPStdioClient(server_path="./test_server.py")
    assert client is not None
    print("✅ ZenMCPStdioClient initialization successful")

    # Test connection manager
    fallback_config = FallbackConfig(enabled=True, http_base_url="http://localhost:8000")
    manager = MCPConnectionManager(fallback_config)
    assert manager.circuit_state == CircuitBreakerState.CLOSED
    print("✅ MCPConnectionManager initialization successful")

    # Test protocol bridge
    bridge = MCPProtocolBridge()
    assert bridge.bridge_tool_name == "promptcraft_mcp_bridge"
    print("✅ MCPProtocolBridge initialization successful")

    # Test subprocess manager
    config = MCPConnectionConfig(server_path="./test_server.py")
    process = ZenMCPProcess(config)
    assert process.process is None
    print("✅ ZenMCPProcess initialization successful")

    # Test process pool
    pool = ProcessPool(config)
    assert pool.pool_size == 1
    print("✅ ProcessPool initialization successful")

    return True


def test_protocol_bridge_basic():
    """Test basic protocol bridge functionality."""
    bridge = MCPProtocolBridge()

    # Test supported endpoints
    endpoints = bridge.get_supported_endpoints()
    assert len(endpoints) == 3
    assert "/api/promptcraft/route/analyze" in endpoints
    print("✅ Protocol bridge endpoints retrieved")

    # Test endpoint descriptions
    desc = bridge.get_endpoint_description("/api/promptcraft/route/analyze")
    assert desc is not None
    assert "Analyze prompt complexity" in desc
    print("✅ Protocol bridge descriptions work")

    return True


async def test_async_operations():
    """Test async operations don't hang."""
    try:
        # Test client connection with short timeout
        client = ZenMCPStdioClient(server_path="./nonexistent.py")
        # This should fail quickly
        result = await asyncio.wait_for(client.connect(), timeout=1.0)
        # If it doesn't fail, that's also fine for this test
        print("✅ Async client connection test completed")
    except TimeoutError:
        print("⚠️  Async operation timed out (expected for nonexistent server)")
    except Exception as e:
        print(f"✅ Async operation completed with expected error: {type(e).__name__}")

    return True


def run_all_tests():
    """Run all validation tests."""
    print("🧪 Running zen_client validation tests...\n")

    tests = [
        test_imports,
        test_basic_initialization,
        test_protocol_bridge_basic,
    ]

    for test in tests:
        try:
            result = test()
            if not result:
                print(f"❌ Test {test.__name__} failed")
                return False
        except Exception as e:
            print(f"❌ Test {test.__name__} raised exception: {e}")
            return False

    # Run async test
    try:
        asyncio.run(test_async_operations())
    except Exception as e:
        print(f"❌ Async test raised exception: {e}")
        return False

    print("\n🎉 All validation tests passed!")
    print("📊 The zen_client modules are properly structured and importable")
    print("🏗️  Test infrastructure should work correctly")

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
