"""
Agent Registry System for PromptCraft-Hybrid.

This module provides the centralized registry for discovering and managing agent classes
throughout the PromptCraft system. It implements a decorator-based registration pattern
that enables automatic agent discovery and type-safe agent instantiation.

The registry system supports:
- Decorator-based agent registration
- Type-safe agent class retrieval
- Agent discovery and listing
- Validation of agent interface compliance

Architecture:
    The registry uses a singleton pattern with a global registry instance that
    is populated at import time through decorator usage. All agents must use
    the @agent_registry.register("agent_id") decorator to be discoverable.

Example:
    ```python
    from src.agents.registry import agent_registry
    from src.agents.base_agent import BaseAgent

    @agent_registry.register("my_agent")
    class MyAgent(BaseAgent):
        def __init__(self, config):
            super().__init__(config)

    # Later, retrieve the agent class
    agent_class = agent_registry.get_agent_class("my_agent")
    ```

Dependencies:
    - logging: For registration event logging
    - typing: For type annotations and generic types
    - src.agents.base_agent: For BaseAgent interface validation

Called by:
    - src/agents/__init__.py: During module initialization
    - src/main.py: For agent instantiation and dependency injection
    - Agent implementations: Through decorator registration
    - FastAPI endpoints: For agent discovery and execution

Complexity: O(1) for registration and retrieval operations
"""

# TODO: Implement the AgentRegistry class as specified in /docs/zen/02-agent-system.md
# TODO: Implement the global agent_registry instance
# TODO: Add validation for BaseAgent interface compliance
# TODO: Add comprehensive error handling for duplicate registrations
