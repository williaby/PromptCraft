#!/usr/bin/env python3
"""
Test script for zen MCP stdio integration.

Tests the integrated zen MCP client to verify Phase 1 implementation is working correctly.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_integration.zen_stdio_client import ZenStdioMCPClient, create_zen_stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_connection():
    """Test basic connection to zen-mcp-server via stdio."""
    logger.info("Testing basic MCP stdio connection...")
    
    try:
        client = ZenStdioMCPClient()
        success = await client.connect()
        
        if success:
            logger.info("✅ Successfully connected to zen-mcp-server via MCP stdio")
            await client.disconnect()
            return True
        else:
            logger.error("❌ Failed to connect to zen-mcp-server")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection test failed with exception: {e}")
        return False


async def test_health_check():
    """Test health check functionality."""
    logger.info("Testing MCP stdio health check...")
    
    try:
        client = ZenStdioMCPClient()
        await client.connect()
        
        health = await client.health_check()
        logger.info(f"✅ Health check response: {health}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False


async def test_model_recommendations():
    """Test model recommendations via MCP stdio."""
    logger.info("Testing model recommendations via MCP stdio...")
    
    try:
        client = ZenStdioMCPClient()
        await client.connect()
        
        # Test with a coding prompt
        prompt = "Write a Python function to sort a list using quicksort algorithm"
        result = await client.get_model_recommendations(prompt)
        
        if result:
            logger.info(f"✅ Model recommendations received:")
            logger.info(f"  Task type: {result.task_type}")
            logger.info(f"  Complexity level: {result.complexity_level}")
            logger.info(f"  Primary model: {result.primary_recommendation.model_name}")
            logger.info(f"  Reasoning: {result.reasoning}")
            await client.disconnect()
            return True
        else:
            logger.error("❌ No model recommendations returned")
            await client.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"❌ Model recommendations test failed: {e}")
        return False


async def test_smart_execution():
    """Test smart execution via MCP stdio."""
    logger.info("Testing smart execution via MCP stdio...")
    
    try:
        client = ZenStdioMCPClient()
        await client.connect()
        
        # Test with simple prompt
        prompt = "What is 2+2? Respond with just the number."
        result = await client.execute_with_routing(prompt)
        
        if result["success"]:
            logger.info(f"✅ Smart execution successful:")
            logger.info(f"  Model used: {result['result']['model_used']}")
            logger.info(f"  Response: {result['result']['content'][:100]}...")
            logger.info(f"  Response time: {result['result']['response_time']:.2f}s")
            await client.disconnect()
            return True
        else:
            logger.error(f"❌ Smart execution failed: {result['error']}")
            await client.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"❌ Smart execution test failed: {e}")
        return False


async def test_convenience_function():
    """Test convenience function for creating client."""
    logger.info("Testing convenience function...")
    
    try:
        client = await create_zen_stdio_client()
        
        # Quick health check
        health = await client.health_check()
        logger.info(f"✅ Convenience function works, health: {health.connection_state}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Convenience function test failed: {e}")
        return False


async def test_fallback_behavior():
    """Test HTTP fallback behavior when MCP fails."""
    logger.info("Testing HTTP fallback behavior...")
    
    try:
        # Create client with invalid server path to force fallback
        client = ZenStdioMCPClient(server_path="/invalid/path/server.py")
        await client.connect()  # This should fail and trigger fallback
        
        # Try to get model recommendations (should use HTTP fallback)
        prompt = "Simple test prompt"
        result = await client.get_model_recommendations(prompt)
        
        if result:
            logger.info("✅ HTTP fallback appears to work")
            await client.disconnect()
            return True
        else:
            logger.warning("⚠️  Neither MCP nor HTTP fallback worked")
            await client.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"❌ Fallback test failed: {e}")
        return False


async def run_integration_tests():
    """Run all integration tests."""
    logger.info("🚀 Starting MCP stdio integration tests...")
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Health Check", test_health_check),
        ("Model Recommendations", test_model_recommendations),
        ("Smart Execution", test_smart_execution),
        ("Convenience Function", test_convenience_function),
        ("Fallback Behavior", test_fallback_behavior),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        
        # Brief pause between tests
        await asyncio.sleep(1)
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 All MCP stdio integration tests passed!")
        return True
    else:
        logger.error("🚫 Some MCP stdio integration tests failed")
        return False


if __name__ == "__main__":
    logger.info("MCP Stdio Integration Test Suite")
    logger.info("Verifying Phase 1 implementation from zen team")
    
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)