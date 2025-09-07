# MCP Server Inventory & Tool Matrix

## Overview

This document provides a comprehensive inventory of all MCP servers configured for PromptCraft-Hybrid, detailing available tools, context usage, specialty agent assignments, and implementation status under the new hybrid architecture.

## Current Context Crisis Summary

- **Problem**: 51k/200k tokens (25.5%) consumed before work begins
- **Solution**: Hybrid architecture reducing to 36k tokens (18% overhead)
- **Savings**: 15k tokens (7.5% context liberation)
- **Approach**: Core zen tools always loaded, specialty agents load tools on-demand

## Core MCP Servers (Always Loaded)

### Zen MCP Server

- **Location**: `~/dev/zen-mcp-server` (forked)
- **Status**: Active - Core orchestration
- **Context Usage**: 3.7k tokens (reduced from 19.6k)

#### Core Tools (Always Available)

| Tool | Context Cost | Purpose | Notes |
|------|-------------|---------|--------|
| `mcp__zen__chat` | 1.5k tokens | General collaboration | High-value, frequent use |
| `mcp__zen__layered_consensus` | 1.7k tokens | Multi-model analysis | Critical for complex decisions |
| `mcp__zen__challenge` | 0.5k tokens | Critical validation | Lightweight, essential |

#### Specialty Agent Tools (On-Demand Loading)

| Tool | Context Cost | Assigned Agent | Load Method |
|------|-------------|----------------|-------------|
| `mcp__zen__secaudit` | 2.3k tokens | security-auditor | Agent context only |
| `mcp__zen__codereview` | 2.3k tokens | code-reviewer | Agent context only |
| `mcp__zen__debug` | 2.1k tokens | debug-investigator | Agent context only |
| `mcp__zen__analyze` | 2.2k tokens | analysis-agent | Agent context only |
| `mcp__zen__refactor` | 2.4k tokens | refactor-specialist | Agent context only |
| `mcp__zen__thinkdeep` | 2.0k tokens | deep-thinking-agent | Agent context only |
| `mcp__zen__docgen` | 1.3k tokens | documentation-writer | Agent context only |

## Specialty Agent Tool Mappings

### Security-Auditor Agent

- **Primary Tools**: `mcp__zen__secaudit`, `heimdall-mcp`
- **Context Loading**: 4.1k tokens (in agent context only)
- **Capabilities**: OWASP analysis, vulnerability scanning, compliance checking
- **Triggers**: Security analysis requests, code vulnerability scanning

### Code-Reviewer Agent

- **Primary Tools**: `mcp__zen__codereview`
- **Secondary Tools**: `mcp__zen__analyze` (for complex reviews)
- **Context Loading**: 4.5k tokens (in agent context only)
- **Capabilities**: Code quality assessment, best practices validation
- **Triggers**: Code review requests, quality analysis

### Debug-Investigator Agent

- **Primary Tools**: `mcp__zen__debug`, `mcp__zen__analyze`
- **Context Loading**: 4.3k tokens (in agent context only)
- **Capabilities**: Root cause analysis, systematic debugging, hypothesis testing
- **Triggers**: Bug investigation, error analysis

### Analysis-Agent

- **Primary Tools**: `mcp__zen__analyze`
- **Secondary Tools**: `mcp__zen__thinkdeep` (for complex analysis)
- **Context Loading**: 4.2k tokens (in agent context only)
- **Capabilities**: Architecture analysis, performance assessment, pattern recognition
- **Triggers**: Code analysis, architectural review requests

### Refactor-Specialist Agent

- **Primary Tools**: `mcp__zen__refactor`
- **Secondary Tools**: `mcp__zen__codereview` (for validation)
- **Context Loading**: 4.7k tokens (in agent context only)
- **Capabilities**: Code smell detection, refactoring recommendations
- **Triggers**: Code improvement requests, technical debt analysis

### Documentation-Writer Agent

- **Primary Tools**: `mcp__zen__docgen`
- **Context Loading**: 1.3k tokens (in agent context only)
- **Capabilities**: API documentation, code documentation generation
- **Triggers**: Documentation requests, code comment generation

### Deep-Thinking Agent

- **Primary Tools**: `mcp__zen__thinkdeep`
- **Context Loading**: 2.0k tokens (in agent context only)
- **Capabilities**: Complex problem analysis, multi-step reasoning
- **Triggers**: Complex analysis requests, strategic thinking needs

## Additional MCP Servers (Phase Deployment)

### Phase 1 MCPs (Enhanced Journey 3)

#### GitHub MCP

- **Location**: External service integration
- **Status**: Phase 1 target
- **Resource Requirements**: 2GB RAM
- **Assigned Agent**: developer-workflow
- **Tools**: Repository analysis, code search, PR management
- **Context Cost**: ~2k tokens (agent context only)

#### FileSystem MCP

- **Location**: Local file system integration
- **Status**: Phase 1 target
- **Resource Requirements**: 1GB RAM
- **Assigned Agent**: developer-workflow
- **Tools**: File I/O, project scaffolding, artifact management
- **Context Cost**: ~1.5k tokens (agent context only)

#### Sequential Thinking MCP

- **Location**: External reasoning service
- **Status**: Phase 1 target
- **Resource Requirements**: 2GB RAM
- **Assigned Agent**: research-assistant
- **Tools**: Chain-of-thought reasoning, structured analysis
- **Context Cost**: ~2k tokens (agent context only)

#### Qdrant Memory MCP

- **Location**: `192.168.1.16:6333` (external Unraid)
- **Status**: Active (enhanced for Phase 1)
- **Resource Requirements**: 8GB RAM minimum
- **Assigned Agent**: knowledge-retrieval
- **Tools**: Vector search, knowledge retrieval, multi-collection support
- **Context Cost**: ~1.8k tokens (agent context only)

### Phase 2 MCPs (Multi-Agent Orchestration)

#### Heimdall MCP

- **Location**: Security analysis service
- **Status**: Phase 2 target
- **Resource Requirements**: TBD
- **Assigned Agent**: security-auditor
- **Tools**: Security scanning, compliance validation
- **Context Cost**: ~1.8k tokens (agent context only)

#### Context7 MCP

- **Location**: External serverless RAG
- **Status**: Phase 2 target
- **Assigned Agent**: research-assistant
- **Tools**: Serverless RAG, library documentation access
- **Context Cost**: ~2.1k tokens (agent context only)

#### Tavily MCP

- **Location**: External search API
- **Status**: Phase 2 target
- **Cost**: $0.0006/query
- **Assigned Agent**: research-assistant
- **Tools**: LLM-optimized search
- **Context Cost**: ~1.2k tokens (agent context only)

#### Perplexity MCP

- **Location**: External search API
- **Status**: Phase 2 target
- **Cost**: $0.30/query (premium tier)
- **Assigned Agent**: research-assistant
- **Tools**: Conversational search, direct answers
- **Context Cost**: ~1.4k tokens (agent context only)

## Specialty Agents Summary

| Agent | Primary Tools | Context Cost | Phase | Status |
|-------|--------------|-------------|-------|--------|
| security-auditor | secaudit, heimdall | 4.1k tokens | 1/2 | Implementation ready |
| code-reviewer | codereview, analyze | 4.5k tokens | 1 | Implementation ready |
| debug-investigator | debug, analyze | 4.3k tokens | 1 | Implementation ready |
| analysis-agent | analyze, thinkdeep | 4.2k tokens | 1 | Implementation ready |
| refactor-specialist | refactor, codereview | 4.7k tokens | 1 | Implementation ready |
| documentation-writer | docgen | 1.3k tokens | 1 | Implementation ready |
| deep-thinking-agent | thinkdeep | 2.0k tokens | 1 | Implementation ready |
| developer-workflow | github, filesystem | 3.5k tokens | 1 | Requires MCP setup |
| research-assistant | sequential-thinking, context7, tavily | 5.3k tokens | 1/2 | Mixed phases |
| knowledge-retrieval | qdrant-memory | 1.8k tokens | 1 | Requires enhancement |

## Context Optimization Summary

### Before Hybrid Architecture

- **Total Context**: 51k tokens (25.5% of 200k)
- **Zen Tools**: 19.6k tokens (all loaded)
- **Available for Work**: 149k tokens (74.5%)

### After Hybrid Architecture

- **Total Context**: 36k tokens (18% of 200k)
- **Zen Core Tools**: 3.7k tokens (3 tools only)
- **Available for Work**: 164k tokens (82%)
- **Context Liberation**: 15k tokens (7.5% improvement)

### Tool Loading Strategy

- **Core Tools**: Loaded in Claude Code context (immediate access)
- **Specialty Tools**: Loaded in agent contexts (no Claude Code overhead)
- **Loading Method**: On-demand via Task subagent system
- **Cleanup**: Automatic after agent execution completes

## Implementation Phases

### Phase 0: Proof of Concept (1-2 weeks)

- [ ] Validate agent-scoped tool loading mechanism
- [ ] Measure performance overhead (<200ms acceptable)
- [ ] Test tool isolation and cleanup
- [ ] Define success metrics and benchmarks

### Phase 1: Core Agent Framework (2-3 weeks)

- [ ] Modify zen-mcp-server to load only 3 core tools
- [ ] Implement base agent class with MCP loading capability
- [ ] Deploy security-auditor agent as proof of concept
- [ ] Create agent registry and selection logic

### Phase 2: Agent Ecosystem Expansion (3-4 weeks)

- [ ] Deploy remaining Phase 1 agents
- [ ] Add developer-workflow agent with GitHub/FileSystem integration
- [ ] Implement research-assistant agent
- [ ] Performance optimization and caching

### Phase 3: Production Deployment (2 weeks)

- [ ] Full agent ecosystem testing
- [ ] Monitoring and metrics implementation
- [ ] User documentation and training
- [ ] Performance benchmarking

## Risk Mitigation

### Technical Risks

1. **Agent Tool Loading Failures**: Robust fallback to basic zen tools
2. **Performance Degradation**: Tool caching, connection pooling, lazy loading
3. **Configuration Drift**: Selective cherry-picking, configuration-first approach
4. **Cross-Agent Conflicts**: Tool isolation, separate execution contexts

### Operational Risks

1. **Developer Experience**: Templates, CLI tools, comprehensive documentation
2. **Debugging Complexity**: Centralized logging, OpenTelemetry tracing, dashboard
3. **Maintenance Overhead**: Automated testing, clear ownership model
4. **User Adaptation**: Migration guide, examples, gradual rollout

## Success Metrics

### Context Efficiency

- **Target**: 36k/200k tokens (18% overhead)
- **Success Criteria**: ≥15k token savings sustained
- **Measurement**: Real-time context usage monitoring

### Functionality Restoration

- **Target**: 100% feature parity with previous MCP setup
- **Success Criteria**: All lost capabilities restored via agents
- **Measurement**: Feature availability testing, user acceptance

### Performance

- **Core Tools**: <500ms response time (baseline)
- **Agent Tools**: <700ms response time (including 100-200ms overhead)
- **Agent Success Rate**: >95% (tool loading and execution)
- **Context Utilization**: >82% usable context

## Next Steps

1. **Immediate**: Begin Phase 0 PoC with senior engineer assignment
2. **Short-term**: Define concrete success metrics and benchmarks
3. **Medium-term**: Implement core agent framework
4. **Long-term**: Full agent ecosystem deployment

---

*Document Status: Implementation Planning*
*Created: 2025-01-06*
*Next Review: After PoC completion*
