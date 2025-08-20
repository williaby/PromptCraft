"""
Agent Module Initialization for PromptCraft-Hybrid.

This module serves as the entry point for the agent system, ensuring all agent
implementations are properly registered with the global registry during application
startup. It follows the explicit import pattern to guarantee agent discovery.

The module exports:
- agent_registry: Global registry instance for agent management
- BaseAgent: Abstract base class for all agent implementations
- AgentInput: Standardized input data model
- AgentOutput: Standardized output data model

Architecture:
    Agent discovery relies on explicit imports to trigger the @agent_registry.register
    decorator execution. This ensures all agents are available before the application
    processes requests.

Import Pattern:
    Each agent module must be imported here to ensure registration occurs at
    application startup, not at first use.

Dependencies:
    - .registry: For agent_registry instance
    - .base_agent: For BaseAgent interface and data models
    - .create_agent: For CreateAgent implementation
    - Future agent implementations will be added here

Called by:
    - src/main.py: During application initialization
    - FastAPI dependency injection system
    - Agent orchestration and management systems

Complexity: O(n) where n is the number of agent modules to import
"""

# Import the registry module for agent_registry instance
# Import base agent for BaseAgent interface and data models
from .base_agent import BaseAgent

# Import agent implementations to trigger registration
from .create_agent import CreateAgent
from .examples.text_processor_agent import TextProcessorAgent
from .models import AgentInput, AgentOutput
from .qwen_test_engineer_agent import QwenTestEngineerAgent
from .registry import agent_registry
from .test_engineering_agent import TestEngineeringAgent

# Export required components
__all__ = [
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    "CreateAgent",
    "QwenTestEngineerAgent",
    "TestEngineeringAgent",
    "TextProcessorAgent",
    "agent_registry",
]
