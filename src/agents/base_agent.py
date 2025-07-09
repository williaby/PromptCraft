"""
Base Agent Framework for PromptCraft-Hybrid.

This module provides the foundational abstract base class and data models for all agents
in the PromptCraft system. It defines the standardized interface contracts that ensure
consistent behavior across all agent implementations.

The module implements:
- BaseAgent: Abstract base class defining the core agent contract
- AgentInput: Standardized input data model for agent execution
- AgentOutput: Standardized output data model for agent responses

Architecture:
    All agents must inherit from BaseAgent and implement the execute() method.
    The system uses dependency injection for configuration and supports
    runtime configuration overrides through AgentInput.

Example:
    ```python
    from src.agents.base_agent import BaseAgent, AgentInput, AgentOutput
    from src.agents.registry import agent_registry

    @agent_registry.register("my_agent")
    class MyAgent(BaseAgent):
        def __init__(self, config: Dict[str, Any]):
            super().__init__(config)

        async def execute(self, agent_input: AgentInput) -> AgentOutput:
            return AgentOutput(content="Hello World")
    ```

Dependencies:
    - abc: For abstract base class functionality
    - typing: For type annotations
    - pydantic: For data validation and serialization

Called by:
    - src/agents/registry.py: Agent registration and management
    - src/agents/create_agent.py: CreateAgent implementation
    - src/main.py: FastAPI integration and dependency injection
    - All agent implementations throughout the system

Complexity: O(1) - Abstract interface with no algorithmic complexity
"""

# TODO: Implement the BaseAgent abstract class and data models
# as specified in /docs/zen/02-agent-system.md
