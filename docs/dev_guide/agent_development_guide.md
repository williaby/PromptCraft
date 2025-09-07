# Agent Development Guide

This guide provides a step-by-step process for developing new agents for the PromptCraft Hybrid System.

## 1. Agent Structure

Each agent should be a self-contained Python module that inherits from the `Agent` base class. The agent should implement the following methods:

* `__init__(self, name, description)`: The constructor for the agent.
* `process(self, query)`: The main method for processing a query.

## 2. Creating a New Agent

To create a new agent, create a new Python file in the `src/agents` directory. The file should contain a class that inherits from the `Agent` base class.

Here is an example of a simple agent:

```python
from src.core.agent import Agent

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            description="A simple agent that echoes the query."
        )

    def process(self, query):
        return f"You said: {query}"
```

## 3. Testing Your Agent

To test your agent, create a new test file in the `tests/agents` directory. The test file should contain unit tests for your agent's `process` method.

Here is an example of a simple test for `MyAgent`:

```python
from src.agents.my_agent import MyAgent

def test_my_agent():
    agent = MyAgent()
    assert agent.process("hello") == "You said: hello"
```

## 4. Registering Your Agent

To register your agent, add it to the `AGENT_REGISTRY` in the `src/core/agent_registry.py` file.

```python
from src.agents.my_agent import MyAgent

AGENT_REGISTRY = {
    "my_agent": MyAgent,
    # ... other agents
}
```

Once your agent is registered, it will be available to the Zen MCP Server and can be used in workflows.
