# Hybrid MCP Architecture - Complete Implementation Plan

## 🎯 Executive Summary

**Problem**: 83.8k tokens (41.9%) consumed by MCP tools before work begins
**Solution**: Hybrid architecture with core tools (3.5k tokens) + agent-scoped specialty tools
**Impact**: 80k tokens (40%+) context liberation = 164k tokens available for work

## ✅ Phase 1: Immediate Context Optimization (COMPLETED)

### Step 1.1: Zen Server Reconfiguration ✅

- **Action**: Reconfigured zen server to load only 3 core tools
- **Before**: 12 tools (~19k tokens)
- **After**: 3 tools (~3.5k tokens)
- **Savings**: 15.5k tokens from zen alone

```bash
# Current optimized configuration
DISABLED_TOOLS=thinkdeep,codereview,debug,secaudit,docgen,analyze,refactor,listmodels,version,planner,precommit,pr_prepare,pr_review,model_evaluator,dynamic_model_selector,routing_status,consensus,testgen,tracer

# Only enabled: chat, layered_consensus, challenge
```

### Step 1.2: Immediate Impact Measurement

- **Expected Context Before**: 83.8k MCP tokens
- **Expected Context After**: ~68k MCP tokens (15.5k savings)
- **Next Test**: Run `/context` to verify reduction

## 🔧 Phase 2: Agent-Scoped Tool Infrastructure (NEXT - 2-3 weeks)

### Step 2.1: Agent Base Framework

- **Create**: `agents/base.py` - SpecialtyAgent base class
- **Implement**: Dynamic MCP tool loading in agent context only
- **Features**: Tool isolation, context management, cleanup

### Step 2.2: Priority Agent Implementation

**Order by impact and feasibility:**

1. **Security-Auditor Agent** (High Impact)
   - Tools: `mcp__zen__secaudit`, `mcp__semgrep__security_check`
   - Context: 2.9k tokens (agent-only)
   - Triggers: Security analysis, vulnerability scanning

2. **Code-Reviewer Agent** (High Usage)
   - Tools: `mcp__zen__codereview`, `mcp__zen__analyze`
   - Context: 4.3k tokens (agent-only)
   - Triggers: Code review requests

3. **Debug-Investigator Agent** (Critical Functionality)
   - Tools: `mcp__zen__debug`, `mcp__zen__analyze`, `mcp__zen__thinkdeep`
   - Context: 6.1k tokens (agent-only)
   - Triggers: Bug investigation, error analysis

### Step 2.3: Tool Loading Mechanism

```python
class ToolLoader:
    @staticmethod
    async def load_agent_tools(agent_type: str) -> List[Tool]:
        """Load tools in agent subprocess/context only"""
        tools = AGENT_TOOL_MAPPING[agent_type]
        # Create temporary MCP connection
        # Load tools in isolation
        # Return tool interfaces

    @staticmethod
    async def cleanup_agent_tools(agent_id: str):
        """Cleanup agent tools after task completion"""
        # Close MCP connections
        # Free context memory
        # Log usage metrics
```

### Step 2.4: Integration with Task System

- **Modify**: Existing `Task` tool to support agent-scoped tool loading
- **Add**: `subagent_tool_loading` parameter
- **Implement**: Automatic tool cleanup after agent execution

## 🚀 Phase 3: Full Agent Ecosystem (3-4 weeks)

### Step 3.1: Remaining Agent Implementation

4. **Documentation-Writer Agent**
   - Tools: `mcp__zen__docgen`
   - Context: 1.3k tokens

5. **Refactor-Specialist Agent**
   - Tools: `mcp__zen__refactor`, `mcp__zen__codereview`
   - Context: 4.5k tokens

6. **Analysis-Agent**
   - Tools: `mcp__zen__analyze`, `mcp__zen__thinkdeep`
   - Context: 4.0k tokens

### Step 3.2: Advanced Features

- **Connection Pooling**: Reuse MCP connections for performance
- **Tool Caching**: Cache frequently used tool metadata
- **Performance Monitoring**: Track context usage and optimization opportunities

### Step 3.3: Other MCP Server Optimization

**Playwright Server** (Currently 22 tools, ~11k tokens):

- **Strategy**: Create browser-automation agent
- **Load On-Demand**: Only when browser tasks needed
- **Potential Savings**: 10k+ tokens

**GitHub Server** (Currently 84 tools, ~47k tokens):

- **Strategy**: Create git-workflow agent
- **Load On-Demand**: Only for repository operations
- **Potential Savings**: 45k+ tokens

## 📊 Expected Results

### Context Usage Projection

```
Current State:
├── MCP Tools: 83.8k tokens (41.9%)
├── System: 3.4k tokens (1.7%)
├── Available: 98.8k tokens (49.4%)
└── Total: 200k tokens

Target State (Phase 2):
├── Core MCP Tools: 3.5k tokens (1.8%)
├── System: 3.4k tokens (1.7%)
├── Available: 193k tokens (96.5%)
└── Total: 200k tokens

Target State (Phase 3):
├── Core MCP Tools: 3.5k tokens (1.8%)
├── System: 3.4k tokens (1.7%)
├── Available: 193k tokens (96.5%)
└── Agent Contexts: Variable (isolated)
```

### Performance Targets

- **Context Overhead**: <4k tokens (2% of 200k)
- **Tool Loading**: <200ms per agent
- **Task Execution**: <700ms total overhead
- **Success Rate**: >95% for agent tool loading

## 🛠️ Implementation Commands

### Phase 1 (Completed)

```bash
# Zen server reconfiguration (DONE)
claude mcp remove zen -s user
claude mcp add --scope user zen /home/byron/dev/zen-mcp-server/.zen_venv/bin/python \
  -e DISABLED_TOOLS=thinkdeep,codereview,debug,secaudit,docgen,analyze,refactor,listmodels,version,planner,precommit,pr_prepare,pr_review,model_evaluator,dynamic_model_selector,routing_status,consensus,testgen,tracer \
  -- /home/byron/dev/zen-mcp-server/server.py
```

### Phase 2 (Next Steps)

```bash
# Create agent infrastructure
mkdir -p /home/byron/dev/PromptCraft/agents/specialty/
touch /home/byron/dev/PromptCraft/agents/base.py
touch /home/byron/dev/PromptCraft/agents/security_auditor.py
touch /home/byron/dev/PromptCraft/agents/tool_loader.py

# Test first agent
python -m agents.security_auditor --test
```

### Emergency Rollback

```bash
# Restore full zen server (if needed)
claude mcp remove zen -s user
claude mcp add --scope user zen /home/byron/dev/zen-mcp-server/.zen_venv/bin/python \
  -e DISABLED_TOOLS=planner,precommit,pr_prepare,pr_review,model_evaluator,dynamic_model_selector,routing_status,consensus,testgen,tracer \
  -- /home/byron/dev/zen-mcp-server/server.py
```

## 🎯 Success Metrics

### Phase 1 Success Criteria (Immediate)

- [ ] Context reduction from 83.8k → ~68k tokens
- [ ] Core tools (chat, layered_consensus, challenge) working
- [ ] No functionality loss for essential features

### Phase 2 Success Criteria (2-3 weeks)

- [ ] Context reduction to <10k MCP tokens
- [ ] 3 priority agents working (security, code-review, debug)
- [ ] Agent tool loading <200ms
- [ ] 100% feature parity for agent-handled tasks

### Phase 3 Success Criteria (3-4 weeks)

- [ ] Context overhead <4k tokens (2%)
- [ ] All specialty tools available via agents
- [ ] >95% tool loading success rate
- [ ] Performance monitoring and optimization complete

## 📋 Next Actions

### Immediate (Today)

1. **Test Phase 1**: Run `/context` to verify 15k token reduction
2. **Validate Core Tools**: Test chat, layered_consensus, challenge functionality
3. **Document Baseline**: Record exact token savings achieved

### Week 1

1. **Design Agent Framework**: Create base classes and interfaces
2. **Implement Tool Loader**: Dynamic MCP connection management
3. **Build Security Agent**: First proof-of-concept agent

### Week 2-3

1. **Deploy Priority Agents**: Security, code-review, debug agents
2. **Integration Testing**: Verify agent tool loading works reliably
3. **Performance Optimization**: Connection pooling, caching

This plan transforms the context crisis into a strategic advantage, providing 80k+ additional tokens while maintaining full functionality through intelligent agent-scoped tool loading.
