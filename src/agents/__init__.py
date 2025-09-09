"""
Agent Module Initialization for PromptCraft-Hybrid.

This module serves as the entry point for the agent system, providing:
- Core agent infrastructure (BaseAgent, models, exceptions, registry)
- CreateAgent implementation for C.R.E.A.T.E. framework prompt generation

Other specialized agents have been moved to the .claude folder for user-level
implementation as per the corrected architecture.

The module exports:
- BaseAgent: Abstract base class for all agent implementations
- AgentInput: Standardized input data model
- AgentOutput: Standardized output data model
- AgentError: Base exception class for agent errors
- agent_registry: Global registry instance for agent management
- CreateAgent: C.R.E.A.T.E. framework prompt generation agent

Dependencies:
    - .base_agent: For BaseAgent interface
    - .models: For AgentInput and AgentOutput data models
    - .exceptions: For agent exception handling
    - .registry: For agent registry management
    - .create_agent: For CreateAgent implementation

Called by:
    - src/main.py: During application initialization
    - Journey1SmartTemplates: For C.R.E.A.T.E. prompt generation
    - Future agent implementations requiring the infrastructure
"""

# Import core infrastructure components
from .base_agent import BaseAgent

# Import the CreateAgent implementation
from .create_agent import CreateAgent
from .exceptions import AgentError
from .models import AgentInput, AgentOutput
from .registry import agent_registry


# Export required components
__all__ = [
    "AgentError",
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    "CreateAgent",
    "agent_registry",
]
