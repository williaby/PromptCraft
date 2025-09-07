# Agent-Scoped Tool Loading Architecture

## Overview

This document defines the architecture for loading MCP tools on-demand through specialized agents, dramatically reducing context overhead while maintaining full functionality.

## Core Architecture Principles

### 1. **Separation of Concerns**

- **Core Tools**: Always available in main Claude context (chat, layered_consensus, challenge)
- **Specialty Tools**: Loaded only in agent contexts when needed
- **Isolation**: Agent tools don't pollute main context

### 2. **Agent Tool Mapping**

Each specialized agent has a predefined set of tools it can load:

```yaml
agents:
  security-auditor:
    primary_tools: [mcp__zen__secaudit]
    secondary_tools: [mcp__semgrep__security_check]
    context_cost: 2.3k + 570 = 2.87k tokens

  code-reviewer:
    primary_tools: [mcp__zen__codereview]
    secondary_tools: [mcp__zen__analyze]
    context_cost: 2.2k + 2.1k = 4.3k tokens

  debug-investigator:
    primary_tools: [mcp__zen__debug]
    secondary_tools: [mcp__zen__analyze, mcp__zen__thinkdeep]
    context_cost: 2.1k + 2.1k + 1.9k = 6.1k tokens
```

### 3. **Loading Strategy**

#### Current State (Broken)

```
Claude Context: [83.8k MCP tools] + [work]
Available: 98.8k tokens (49.4%)
```

#### Target State (Hybrid)

```
Claude Context: [3.5k core tools] + [work]
Agent Context: [specific tools] + [task]
Available: ~164k tokens (82%)
```

## Implementation Components

### 1. **Agent Base Class**

```python
class SpecialtyAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.available_tools = AGENT_TOOL_MAPPING[agent_type]

    async def load_tools(self) -> List[Tool]:
        """Load agent-specific tools into agent context only"""
        pass

    async def execute_task(self, task: str) -> str:
        """Execute task with agent-specific tool context"""
        pass
```

### 2. **Tool Loading Mechanism**

- **Dynamic MCP Server Creation**: Agents create temporary MCP connections
- **Context Isolation**: Tools loaded in agent subprocess/context
- **Cleanup**: Automatic tool unloading after task completion
- **Caching**: Connection pooling for frequently used tool combinations

### 3. **Agent Registry**

```python
AGENT_TOOL_MAPPING = {
    "security-auditor": {
        "primary": ["mcp__zen__secaudit"],
        "secondary": ["mcp__semgrep__security_check", "mcp__semgrep__semgrep_scan"],
        "max_context": 4000  # tokens
    },
    "code-reviewer": {
        "primary": ["mcp__zen__codereview"],
        "secondary": ["mcp__zen__analyze"],
        "max_context": 4500
    },
    "debug-investigator": {
        "primary": ["mcp__zen__debug"],
        "secondary": ["mcp__zen__analyze", "mcp__zen__thinkdeep"],
        "max_context": 6500
    }
}
```

## Tool Access Patterns

### 1. **Core Tool Usage (Always Available)**

```python
# Direct access in main context
result = await mcp__zen__chat(
    prompt="Help me understand this code",
    model="anthropic/claude-opus-4.1"
)
```

### 2. **Specialty Tool Usage (Agent-Scoped)**

```python
# Via Task agent system
result = await Task(
    description="Security audit of authentication module",
    prompt="Review auth.py for security vulnerabilities",
    subagent_type="security-auditor"  # This loads secaudit tools
)
```

### 3. **Fallback Strategy**

If agent tool loading fails:

1. **Graceful Degradation**: Use core tools only
2. **Error Reporting**: Clear feedback about missing capabilities
3. **Manual Override**: Allow direct tool loading if needed

## Performance Optimization

### 1. **Connection Pooling**

- Reuse MCP connections for frequently accessed tools
- Cache tool metadata and schemas
- Lazy loading of rarely used tools

### 2. **Context Management**

- **Pre-warming**: Common agent contexts kept warm
- **Cleanup**: Aggressive cleanup of unused tool contexts
- **Monitoring**: Track context usage and optimize

### 3. **Tool Batching**

- Load related tools together (e.g., analyze + thinkdeep)
- Minimize context switches
- Optimize tool execution order

## Security Considerations

### 1. **Tool Isolation**

- Agent tools can't access main context
- Separate execution environments
- Limited cross-agent communication

### 2. **Access Control**

- Agents can only load their assigned tools
- No privilege escalation
- Audit trail for tool usage

### 3. **Resource Limits**

- Maximum context per agent
- Timeout for tool loading
- Memory usage monitoring

## Rollback Strategy

If the hybrid architecture fails:

1. **Emergency Revert**: Single command to restore full MCP loading
2. **Gradual Rollback**: Disable agent loading, keep core tools
3. **Tool-by-Tool**: Re-enable specific tools as needed

```bash
# Emergency full revert
claude mcp remove zen -s user
claude mcp add --scope user zen /home/byron/dev/zen-mcp-server/.zen_venv/bin/python \
  -e DISABLED_TOOLS=planner,precommit,pr_prepare,pr_review,model_evaluator,dynamic_model_selector,routing_status,consensus,testgen,tracer \
  -- /home/byron/dev/zen-mcp-server/server.py
```

## Success Metrics

### Context Efficiency

- **Current**: 83.8k MCP tokens (41.9%)
- **Target**: 3.5k MCP tokens (1.8%)
- **Savings**: 80k tokens (40%+ context liberation)

### Performance

- **Tool Loading**: <200ms per agent
- **Task Execution**: <700ms total overhead
- **Success Rate**: >95% for agent tool loading

### Functionality

- **Feature Parity**: 100% capability preservation
- **User Experience**: Transparent tool access
- **Reliability**: Fallback mechanisms working
