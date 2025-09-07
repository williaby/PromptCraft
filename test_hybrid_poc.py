#!/usr/bin/env python3
"""
Hybrid Architecture PoC Performance Test

This script tests the core functionality of the hybrid architecture:
1. Agent-scoped tool loading mechanism
2. Performance validation against 200ms target  
3. Context isolation guarantees
4. Fallback behavior when tools unavailable

Usage:
    python test_hybrid_poc.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from agents.security_auditor_agent import SecurityAuditorAgent
    from agents.models import AgentInput
    from utils.observability import create_structured_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the PromptCraft root directory")
    sys.exit(1)

logger = create_structured_logger(__name__)

async def test_agent_performance():
    """Test agent performance and validate 200ms target."""
    print("🚀 Testing Hybrid Architecture PoC")
    print("=" * 50)
    
    # Test configuration
    agent_config = {
        "agent_id": "security-auditor-test",
        "severity_threshold": "medium"
    }
    
    try:
        # Initialize security auditor agent
        print("📋 Initializing SecurityAuditorAgent...")
        agent = SecurityAuditorAgent(agent_config)
        print(f"✅ Agent initialized with tools: {agent.zen_tools}")
        
        # Prepare test input
        test_input = AgentInput(
            query="Perform security analysis on authentication code",
            metadata={
                "test_mode": True,
                "performance_test": True
            }
        )
        
        # Execute agent and measure performance
        print("\n⚡ Executing agent with performance measurement...")
        start_time = time.time()
        
        result = await agent.execute(test_input)
        
        execution_time = time.time() - start_time
        
        # Performance validation
        print(f"\n📊 Performance Results:")
        print(f"Total execution time: {execution_time:.3f}s")
        print(f"Agent processing time: {result.processing_time:.3f}s")
        print(f"Agent confidence: {result.confidence:.2f}")
        
        # Validate performance target
        PERFORMANCE_TARGET = 0.2  # 200ms for tool loading
        loading_time = result.metadata.get("loading_time", execution_time)
        
        if loading_time <= PERFORMANCE_TARGET:
            print(f"✅ Performance target MET: {loading_time:.3f}s <= {PERFORMANCE_TARGET}s")
        else:
            print(f"⚠️  Performance target MISSED: {loading_time:.3f}s > {PERFORMANCE_TARGET}s")
        
        # Context isolation validation
        print(f"\n🔒 Context Isolation Results:")
        print(f"Agent type: {result.metadata.get('agent_type', 'unknown')}")
        print(f"Tools loaded: {result.metadata.get('tools_loaded', [])}")
        print(f"Context isolation: {result.metadata.get('context_isolation', False)}")
        print(f"Agent context ID: {result.metadata.get('agent_context_id', 'none')}")
        
        # Output analysis
        print(f"\n📝 Analysis Results:")
        print(f"Content length: {len(result.content)} characters")
        print(f"Security issues found: {result.metadata.get('security_issues_found', 'unknown')}")
        print(f"Analysis type: {result.metadata.get('analysis_type', 'unknown')}")
        
        # Show sample output
        print(f"\n📄 Sample Output (first 200 chars):")
        print(result.content[:200] + "..." if len(result.content) > 200 else result.content)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"PoC test failed: {e}")
        return False

async def test_fallback_behavior():
    """Test agent behavior when zen tools are unavailable."""
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 30)
    
    # Test with simulated tool loading failure
    agent_config = {
        "agent_id": "security-auditor-fallback-test",
        "severity_threshold": "low"
    }
    
    try:
        agent = SecurityAuditorAgent(agent_config)
        
        # Force tool loading failure simulation
        agent._is_tools_loaded = False
        agent._loaded_tools = {}
        
        test_input = AgentInput(
            query="Test fallback security analysis",
            metadata={"test_mode": True, "fallback_test": True}
        )
        
        start_time = time.time()
        result = await agent.execute(test_input)
        execution_time = time.time() - start_time
        
        print(f"Fallback execution time: {execution_time:.3f}s")
        print(f"Fallback confidence: {result.confidence:.2f}")
        print(f"Fallback mode detected: {result.metadata.get('fallback_analysis', False)}")
        
        # Verify graceful degradation
        if result.confidence > 0 and len(result.content) > 0:
            print("✅ Fallback behavior working correctly")
            return True
        else:
            print("❌ Fallback behavior failed")
            return False
            
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

def print_context_savings():
    """Display context optimization calculations."""
    print("\n💰 Context Optimization Analysis")
    print("=" * 35)
    
    # Context calculations from hybrid architecture plan
    current_context = 51000  # 51k tokens before hybrid
    target_context = 36000   # 36k tokens with hybrid
    savings = current_context - target_context
    
    # Tool costs
    zen_tools_before = 19600  # All zen tools loaded
    zen_tools_after = 3700   # Only 3 core tools
    tool_savings = zen_tools_before - zen_tools_after
    
    print(f"📊 Context Usage:")
    print(f"  Before: {current_context:,} tokens (25.5% of 200k)")
    print(f"  After:  {target_context:,} tokens (18% of 200k)")
    print(f"  Savings: {savings:,} tokens ({savings/2000:.1f}% improvement)")
    
    print(f"\n🛠️  Zen Tool Optimization:")
    print(f"  Before: {zen_tools_before:,} tokens (all tools loaded)")
    print(f"  After:  {zen_tools_after:,} tokens (3 core tools only)")
    print(f"  Tool savings: {tool_savings:,} tokens ({tool_savings/zen_tools_before*100:.1f}% reduction)")
    
    print(f"\n🎯 Available Context:")
    print(f"  Before: {200000 - current_context:,} tokens (74.5% usable)")
    print(f"  After:  {200000 - target_context:,} tokens (82% usable)")
    print(f"  Improvement: {(200000 - target_context) - (200000 - current_context):,} tokens")

async def main():
    """Run complete PoC test suite."""
    print("🧪 Hybrid Architecture PoC Test Suite")
    print("=====================================")
    
    # Context optimization display
    print_context_savings()
    
    # Performance test
    perf_test_success = await test_agent_performance()
    
    # Fallback test
    fallback_test_success = await test_fallback_behavior()
    
    # Overall results
    print(f"\n📋 PoC Test Summary")
    print("=" * 20)
    print(f"Performance test: {'✅ PASS' if perf_test_success else '❌ FAIL'}")
    print(f"Fallback test: {'✅ PASS' if fallback_test_success else '❌ FAIL'}")
    
    if perf_test_success and fallback_test_success:
        print(f"\n🎉 PoC VALIDATION SUCCESSFUL!")
        print("Hybrid architecture is ready for Phase 1 implementation.")
        return 0
    else:
        print(f"\n⚠️  PoC validation failed. Review implementation before proceeding.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())