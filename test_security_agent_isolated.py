#!/usr/bin/env python3
"""
Test SecurityAuditorAgent in isolation to verify zen agent functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test minimal imports
try:
    # Import base classes first
    from agents.base_agent import BaseAgent
    from agents.models import AgentInput, AgentOutput
    print("✅ Base classes imported")
    
    # Import zen base 
    from agents.zen_agent_base import ZenAgentBase, ZEN_AGENT_REGISTRY
    print("✅ ZenAgentBase imported")
    
    # Import registry separately
    from agents.registry import agent_registry
    print("✅ Agent registry imported")
    print("Current registry:", list(agent_registry._registry.keys()))
    
    # Now import security agent
    from agents.security_auditor_agent import SecurityAuditorAgent
    print("✅ SecurityAuditorAgent imported")
    print("Updated registry:", list(agent_registry._registry.keys()))
    
    # Test agent instantiation
    config = {"agent_id": "test_security_agent"}
    agent = SecurityAuditorAgent(config)
    print("✅ Agent instantiated")
    print(f"Agent tools: {agent.zen_tools}")
    print(f"Agent class: {agent.__class__.__name__}")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    traceback.print_exc()

print("\n" + "="*50)
print("Zen Agent Registry Contents:")
for agent_id, info in ZEN_AGENT_REGISTRY.items():
    print(f"  {agent_id}: {info['zen_tools']}")