---
title: PromptCraft-Hybrid MCP Server Reference
version: 1.5
status: published
component: Architecture
tags: ["mcp-servers", "orchestration", "zen-mcp", "architecture", "phase-deployment"]
source: "PromptCraft-Hybrid Project"
purpose: To provide comprehensive reference for all MCP servers integrated within the PromptCraft-Hybrid ecosystem.
planning_horizon: "medium-term"
stakeholders: ["Architects", "Developers", "AI Engineers"]
---

# PromptCraft-Hybrid MCP Server Reference

## Table of Contents

### Core MCP Servers List

- [Zen MCP Server](#zen-mcp-server) - Central orchestration brain (Phase 1)
- [Serena MCP](#serena-mcp-moved-to-phase-1) - Advanced NLP capabilities (Phase 1)
- [GitHub MCP](#github-mcp-moved-to-phase-1) - Repository interface (Phase 1)
- [FileSystem MCP](#filesystem-mcp-moved-to-phase-1) - File operations (Phase 1)
- [Sequential Thinking MCP](#sequential-thinking-mcp-moved-to-phase-1) - Structured reasoning (Phase 1)
- [Memory MCP (Qdrant)](#memory-mcp-qdrant-enhanced-in-phase-1) - Vector search and retrieval (Phase 1)
- [Heimdall MCP](#heimdall-mcp-remains-phase-2) - Security and code analysis (Phase 2)
- [Code Interpreter MCP](#code-interpreter-mcp-remains-phase-3) - Sandboxed execution (Phase 3)
- [Human-in-the-Loop (HITL) MCP](#human-in-the-loop-hitl-mcp-remains-phase-3) - Human approval workflows (Phase 3)
- [Perplexity MCP](#perplexity-mcp-remains-phase-2) - Conversational search (Phase 2)
- [Tavily MCP](#tavily-mcp-remains-phase-2) - LLM-optimized search (Phase 2)
- [Context7 MCP](#context7-mcp-remains-phase-2) - Serverless RAG backend (Phase 2)
- [Sentry MCP](#sentry-mcp-remains-phase-4) - Error tracking and monitoring (Phase 4)

### Phase 1 Public Search MCPs

- [Google Search MCP](#google-search-mcp) - Standard web search
- [DuckDuckGo Search MCP](#duckduckgo-search-mcp) - Privacy-focused search
- [URL Reader MCP](#url-reader-mcp) - Content extraction

### Integration Patterns

- [Standard Integration Pattern](#standard-integration-pattern)
- [Phase-Based Activation](#phase-based-activation)
- [Enhanced Phase 1 Integration](#enhanced-phase-1-integration)

### Guidelines and Planning

- [MCP Selection Guidelines](#mcp-selection-guidelines)
- [Future MCP Expansion (Phase 4)](#future-mcp-expansion-phase-4)

## Introduction

This document serves as the central reference for all Master Control Program (MCP) servers integrated within the
PromptCraft-Hybrid ecosystem. MCPs are specialized, tool-bearing servers that provide discrete capabilities to the
central **Zen MCP Server**, which orchestrates them to fulfill complex user requests in Journeys 2, 3, and 4.

Each MCP is a standalone, addressable service, allowing for a modular, scalable, and maintainable architecture.
The Zen MCP Server intelligently routes tasks to the appropriate MCP based on the user's intent, conversational
context, and the specific requirements of the active agents.

### MCP Availability by Phase

MCPs are introduced progressively across our four-phase rollout:

| Phase       | Focus                           | MCPs Available                                                       |
| :---------- | :------------------------------ | :------------------------------------------------------------------- |
| **Phase 1** | Foundation + Enhanced Journey 3 | Zen (local), Public Search MCPs, Serena, GitHub, Sequential Thinking, FileSystem, Qdrant |
| **Phase 2** | Multi-Agent Orchestration       | + Heimdall, Advanced Search MCPs (Tavily, Perplexity, Context7)     |
| **Phase 3** | Advanced Workflows              | + Code Interpreter, Human-in-the-Loop                               |
| **Phase 4** | Continuous Enhancement          | + Sentry, Custom/Specialized MCPs                                   |

## Core MCP Servers

The following are the foundational MCPs that provide core capabilities to the orchestration layer.

### Zen MCP Server

The Zen MCP Server is the central brain of the orchestration layer, responsible for all real-time, user-facing
coordination.

- **Official Repo:**
  [https://github.com/BeehiveInnovations/zen-mcp-server](https://github.com/BeehiveInnovations/zen-mcp-server)
- **Hosting Model:** Self-Hosted (Core on-premise component).
- **Phase Availability:** `Phase 1` (Journey 3 Light local setup)
- **Priority:** `Critical` - Required for all orchestration
- **Dependencies:** Node.js v18+, Anthropic API Key
- **Role in Architecture:** Acts as the primary real-time orchestrator for Journeys 2-4. It receives user queries,
  selects the appropriate agents and MCPs, and coordinates their execution to produce a final, coherent response.
- **Core Features:**
  - **Multi-Model Coordination:** Intelligently selects the best LLM (e.g., Gemini Pro, Flash, O3) for a given
    sub-task.
  - **Cross-Tool Continuation:** Maintains conversational state as a task moves between different MCPs.
  - **Agent-to-Agent Communication:** Facilitates dialogue between specialized agents.
  - **Intelligent Routing:** Analyzes user intent to route requests to downstream MCPs.
  - **Error Recovery & State Management:** Manages the overall state of a multi-step task.
- **Related ADRs:**
  - ADR-002: MCP Server Orchestration
  - ADR-008: Journey 3 Light Strategy

### Serena MCP (Moved to Phase 1)

The Serena MCP provides advanced natural language processing and conversational AI capabilities.

- **Official Repo:** [https://github.com/serena-ai/serena-mcp-server](https://github.com/serena-ai/serena-mcp-server)
- **Hosting Model:** Self-Hosted (Part of Phase 1 6-container stack)
- **Phase Availability:** `Phase 1` - Enhanced Journey 3 capabilities
- **Priority:** `High` - Core conversational enhancement
- **Dependencies:** Docker, Python 3.9+
- **Resource Requirements:** 4GB RAM
- **Role in Architecture:** Enhances natural language understanding and generation, providing sophisticated
  conversation management for Journey 3.
- **Core Features:**
  - Advanced context tracking
  - Multi-turn conversation management
  - Intent recognition and disambiguation
  - Natural language generation optimization
- **Integration Notes:** Works closely with Sequential Thinking MCP for complex queries
- **Related ADRs:**
  - ADR-009: Phase 1 Stack Expansion

### GitHub MCP (Moved to Phase 1)

The GitHub MCP provides a direct interface to the GitHub API, enabling the system to understand and interact with
code repositories.

- **Official Repo:** [https://github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)
- **Hosting Model:** Self-Hosted (The service is hosted internally, but it interacts with the externally-hosted
  GitHub.com API).
- **Phase Availability:** `Phase 1` - Enhanced developer workflows
- **Priority:** `High` - Essential for developer workflows
- **Dependencies:** GitHub API Token
- **Resource Requirements:** 2GB RAM
- **Role in Architecture:** Fetches repository context, analyzes project structure, and performs actions on behalf of
  the user. Critical for Journey 3 (IDE Integration).
- **Core Features:**
  - Repository analysis and file-level retrieval.
  - Version control awareness (branches, commits, PRs).
  - Automated project scaffolding.
- **Rate Limits:** Subject to GitHub API limits (5000 req/hour authenticated)
- **Related ADRs:**
  - ADR-003: Developer-First Features
  - ADR-009: Phase 1 Stack Expansion

### FileSystem MCP (Moved to Phase 1)

The FileSystem MCP provides the ability to read, write, and manipulate files and directories.

- **Official Repo:**
  [https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- **Hosting Model:** Self-Hosted (Provides direct access to the on-premise file system).
- **Phase Availability:** `Phase 1` - Core file operations
- **Priority:** `High` - Required for agent file operations
- **Dependencies:** Proper file system permissions
- **Resource Requirements:** 1GB RAM
- **Security Considerations:** Sandboxed to specific directories only
- **Role in Architecture:** Enables agents to work with local files, create project structures, and manage artifacts.
- **Core Features:**
  - File I/O (Create, Read, Update, Delete).
  - Project Scaffolding from templates.
  - Artifact Management in a designated workspace.
- **Related ADRs:**
  - ADR-004: Security-First Architecture (sandboxing)
  - ADR-009: Phase 1 Stack Expansion

### Sequential Thinking MCP (Moved to Phase 1)

Provides a structured reasoning framework to improve the quality of LLM responses for complex tasks.

- **Official Repo:**
  [https://github.com/modelcontextprotocol/servers/tree/HEAD/src/sequentialthinking](https://github.com/modelcontextprotocol/servers/tree/HEAD/src/sequentialthinking)
- **Registry ID:** <https://mcp.so/server/sequentialthinking/modelcontextprotocol>
- **Hosting Model:** Self-Hosted (The logic wraps and structures calls to an LLM).
- **Phase Availability:** `Phase 1` - Enhanced reasoning
- **Priority:** `High` - Core reasoning enhancement
- **Dependencies:** Access to LLM endpoints
- **Resource Requirements:** 2GB RAM
- **Role in Architecture:** Invoked by the Zen MCP server when a task requires complex reasoning. It forces the LLM
  to "think step-by-step," breaking down a problem into a logical sequence before generating a final answer. This
  improves accuracy and transparency.
- **Core Features:**
  - Implements Chain-of-Thought (CoT) or similar step-by-step reasoning patterns.
  - Decomposes complex user requests into a series of smaller, manageable sub-tasks.
  - Generates a structured plan or thought process that can guide other agents or subsequent LLM calls.
- **Performance Impact:** Adds 200-500ms latency but improves accuracy by 30%
- **Related ADRs:**
  - ADR-006: Sequential Thinking Integration
  - ADR-009: Phase 1 Stack Expansion

### Memory MCP (Qdrant) Enhanced in Phase 1

The Memory MCP provides the core vector search and retrieval capabilities from the on-premise knowledge base.

- **Official Repo (Implementation):**
  [https://github.com/qdrant/mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant)
- **Hosting Model:** Self-Hosted (Containerized instance of Qdrant).
- **Phase Availability:** `Phase 1` (Journey 1 knowledge base + enhanced)
- **Priority:** `Critical` - Core knowledge retrieval
- **Dependencies:** Docker, NVMe storage
- **Resource Requirements:** 8GB RAM minimum (increased for Phase 1), NVMe required
- **Role in Architecture:** Serves as the long-term memory for all agents. It is responsible for the "Retrieval" step
  in the RAG pipeline, finding the most relevant knowledge chunks to answer a query.
- **Core Features:**
  - High-speed semantic search using vector embeddings.
  - Hybrid search combining vector (dense) and keyword (sparse) methods.
  - Manages multiple knowledge collections for different agents.
  - Scales to handle millions of document chunks.
  - Enhanced with multi-collection support for Phase 1 MCPs
- **Performance Metrics:**
  - Query latency: <50ms p95
  - Ingestion rate: 1000 docs/minute
  - Collections: Up to 10 separate collections
- **Related ADRs:**
  - ADR-001: RAG Over Fine-Tuning
  - ADR-005: HyDE for Query Enhancement
  - ADR-009: Phase 1 Stack Expansion

### Heimdall MCP (Remains Phase 2)

The Heimdall MCP is the system's dedicated security and code analysis engine.

- **Official Repo:** [https://github.com/lcbcFoo/heimdall-mcp-server](https://github.com/lcbcFoo/heimdall-mcp-server)
- **Hosting Model:** Self-Hosted (Ensures code analysis remains within the private infrastructure).
- **Phase Availability:** `Phase 2`
- **Priority:** `High` - Security analysis for multi-agent workflows
- **Dependencies:** Docker, Python 3.9+
- **Role in Architecture:** Provides on-demand security analysis, vulnerability scanning, and compliance checking.
- **Core Features:**
  - Static & Dynamic Code Analysis.
  - Compliance Verification (e.g., SOC 2, HIPAA).
  - Dependency Scanning for known vulnerabilities.
  - Infrastructure as Code (IaC) Analysis.
- **Integration Notes:** Primary security validation for Journey 2-4 agent outputs
- **Related ADRs:**
  - ADR-004: Security-First Architecture

### Code Interpreter MCP (Remains Phase 3)

The Code Interpreter MCP provides a sandboxed environment for executing code and validating its output.

- **Official Repo:**
  [https://github.com/executeautomation/mcp-code-runner](https://github.com/executeautomation/mcp-code-runner)
- **Hosting Model:** Self-Hosted (Required for a secure, sandboxed execution environment).
- **Phase Availability:** `Phase 3`
- **Priority:** `Medium` - Enables Journey 4 execution
- **Dependencies:** Docker, Sandbox environment
- **Security Considerations:** Strict resource limits, network isolation
- **Role in Architecture:** Acts as a verification layer to ensure generated code is functional, enabling the "Direct
  Execution" workflow (Journey 4).
- **Core Features:**
  - Secure, sandboxed code execution (Python, JS).
  - Unit Test Execution.
  - REPL (Read-Eval-Print Loop) for interactive development.
- **Related ADRs:**
  - ADR-010: Direct Execution Safety

### Human-in-the-Loop (HITL) MCP (Remains Phase 3)

The HITL MCP manages workflows that require human intervention, approval, or feedback.

- **Official Repo:**
  [https://github.com/gotohuman/gotohuman-mcp-server](https://github.com/gotohuman/gotohuman-mcp-server)
- **Hosting Model:** Self-Hosted (Integrates with the core application UI/API).
- **Phase Availability:** `Phase 3`
- **Priority:** `Medium` - Enhanced workflows
- **Dependencies:** Notification system (email/Slack)
- **Role in Architecture:** Pauses an automated workflow to wait for explicit user input, which is critical for
  sign-offs or decision-making.
- **Core Features:**
  - Approval Workflows.
  - Feedback Collection.
  - Interactive Disambiguation.
- **Integration Notes:** Can integrate with Slack, email, or web UI for notifications

### Perplexity MCP (Remains Phase 2)

Provides access to the Perplexity online search API, optimized for conversational and direct answers.

- **Official Repo:**
  [https://github.com/ppl-ai/modelcontextprotocol/tree/main](https://github.com/ppl-ai/modelcontextprotocol/tree/main)
- **Hosting Model:** Externally Hosted (Access via Remote API).
- **Phase Availability:** `Phase 2`
- **Priority:** `Low` - Premium search tier
- **Cost:** $0.30 per query (use sparingly)
- **API Requirements:** Perplexity API Key
- **Role in Architecture:** Used for quick, factual lookups where a concise answer is preferred over a list of links.
  Part of the tiered search strategy.
- **Core Features:**
  - Conversational search capabilities.
  - Provides direct, synthesized answers to queries.
  - Includes sources used for generating the answer.
- **Related ADRs:**
  - ADR-002: Tiered Search Strategy

### Tavily MCP (Remains Phase 2)

Provides access to the Tavily Search API, which is a search engine built specifically for LLMs and RAG, focusing on
comprehensive and reliable results.

- **Official Repo:** [https://github.com/tavily-ai/tavily-mcp](https://github.com/tavily-ai/tavily-mcp)
- **Hosting Model:** Externally Hosted (Access via Remote API).
- **Phase Availability:** `Phase 2`
- **Priority:** `Medium` - Standard search tier
- **Cost:** $0.0006 per query
- **API Requirements:** Tavily API Key
- **Role in Architecture:** Serves as a high-quality search source for research-intensive tasks. Used when agents need
  in-depth, well-vetted information on a topic.
- **Core Features:**
  - Optimized for accuracy and relevance for AI agents.
  - Returns organized and structured search results.
  - Can include raw page content for deep analysis.
- **Related ADRs:**
  - ADR-002: Tiered Search Strategy

### Context7 MCP (Remains Phase 2)

Provides a serverless, low-latency RAG and search context backend, powered by Upstash.

- **Official Repo:** [https://github.com/upstash/context7](https://github.com/upstash/context7)
- **Hosting Model:** Externally Hosted (Access via Remote API).
- **Phase Availability:** `Phase 2`
- **Priority:** `High` - Free/low-cost search tier
- **Cost:** Free tier available
- **API Requirements:** Upstash API Key
- **Role in Architecture:** Used as a high-performance search and context retrieval layer, particularly when speed is
  critical. A key component of the tiered search strategy.
- **Core Features:**
  - Low-latency vector search.
  - Managed RAG context provider.
  - Serverless architecture for scalability.
- **Related ADRs:**
  - ADR-002: Tiered Search Strategy

### Sentry MCP (Remains Phase 4)

The Sentry MCP provides an interface for real-time error tracking and performance monitoring.

- **Official Repo:** [https://mcp.sentry.dev/mcp](https://mcp.sentry.dev/mcp)
- **Hosting Model:** Externally Hosted (Access via Remote API).
- **Phase Availability:** `Phase 4`
- **Priority:** `Low` - Production monitoring
- **API Requirements:** Sentry API Key
- **Cost:** Based on event volume
- **Role in Architecture:** Allows agents to report errors or performance metrics during execution, and can potentially
  be used to query for error patterns.
- **Core Features:**
  - Event and Error Reporting.
  - Performance Monitoring.
  - Querying for issue details.
- **Integration Notes:** Optional for production monitoring

## Public Search MCPs for Immediate Use

These MCPs are available immediately in Phase 1 through Journey 3 Light, providing instant value without any setup
requirements.

### Google Search MCP

- **Access Method:** Public endpoint via Zen MCP
- **Phase Availability:** `Phase 1`
- **Priority:** `High` - Immediate developer value
- **Cost:** Free (rate limited)
- **Example Usage:** `claude /tool:google "latest React best practices"`
- **Rate Limits:** 100 searches/day/user

### DuckDuckGo Search MCP

- **Access Method:** Public endpoint via Zen MCP
- **Phase Availability:** `Phase 1`
- **Priority:** `High` - Privacy-focused alternative
- **Cost:** Free
- **Example Usage:** `claude /tool:ddg "Model Context Protocol documentation"`
- **Features:** No tracking, no personalization

### URL Reader MCP

- **Access Method:** Public endpoint via Zen MCP
- **Phase Availability:** `Phase 1`
- **Priority:** `High` - Content extraction
- **Cost:** Free
- **Example Usage:** `claude /tool:url "https://example.com/article"`
- **Limitations:** Cannot access authenticated content

## MCP Integration Patterns

### Standard Integration Pattern

All MCPs follow a consistent integration pattern through Zen:

```python
# Consistent pattern for all integrations
result = await zen_client.call_tool(
    server="mcp_name",      # Which MCP server
    tool="tool_name",       # Which capability
    params={...},           # Parameters
    timeout=30,             # Consistent timeout
    retry=3                 # Automatic retry
)
```

### Phase-Based Activation

MCPs are activated based on the current deployment phase:

```yaml
# zen_config.yaml
mcp_servers:
  phase_1:
    # Public search MCPs
    - google_search
    - duckduckgo_search
    - url_reader
    # Core infrastructure MCPs (expanded)
    - qdrant_memory
    - serena           # NEW in Phase 1
    - github           # NEW in Phase 1
    - filesystem       # NEW in Phase 1
    - sequential_thinking  # NEW in Phase 1
  phase_2:
    - heimdall
    - context7
    - tavily
    - perplexity
  phase_3:
    - code_interpreter
    - human_in_loop
  phase_4:
    - sentry
    - custom_mcps
```

### Enhanced Phase 1 Integration

The expanded Phase 1 stack enables richer Journey 3 capabilities:

```python
# Example: Enhanced Journey 3 workflow with Phase 1 MCPs
async def enhanced_journey_3_workflow(query: str):
    # 1. Use Sequential Thinking for complex reasoning
    thought_process = await zen_client.call_tool(
        server="sequential_thinking",
        tool="analyze",
        params={"query": query}
    )

    # 2. Search GitHub for relevant code
    if "code" in query.lower():
        github_context = await zen_client.call_tool(
            server="github",
            tool="search_code",
            params={"query": extract_code_intent(query)}
        )

    # 3. Use Serena for natural language enhancement
    enhanced_response = await zen_client.call_tool(
        server="serena",
        tool="enhance",
        params={
            "thought_process": thought_process,
            "context": github_context
        }
    )

    # 4. Save to FileSystem if needed
    if needs_file_output(enhanced_response):
        await zen_client.call_tool(
            server="filesystem",
            tool="write",
            params={"path": "output.md", "content": enhanced_response}
        )

    return enhanced_response
```

## MCP Selection Guidelines

### Search Tier Selection

Based on ADR-002 (Tiered Search Strategy):

1. **Phase 1 Free Search**: Google, DuckDuckGo, URL Reader
2. **Phase 2 Enhanced Search**:
   - Documentation/FAQ: Use Context7 (free tier)
   - General Search: Use Tavily ($0.0006/query)
   - Premium/Complex: Use Perplexity ($0.30/query)

### Security Considerations

- **Self-Hosted Required**: Heimdall, FileSystem, Code Interpreter, Serena, GitHub MCP, Sequential Thinking
- **External OK**: Search MCPs, Sentry
- **Sandboxing Required**: Code Interpreter, FileSystem

### Performance Considerations

| MCP Type            | Expected Latency | Caching Strategy | Phase 1 Resource Impact |
| :------------------ | :--------------- | :--------------- | :---------------------- |
| Local (Qdrant)      | <50ms            | Built-in         | 8GB RAM                 |
| Serena              | <100ms           | Redis cache      | 4GB RAM                 |
| GitHub MCP          | <200ms           | Response cache   | 2GB RAM                 |
| FileSystem          | <50ms            | None needed      | 1GB RAM                 |
| Sequential Thinking | <500ms           | Result cache     | 2GB RAM                 |
| External API        | <1000ms          | Response cache   | Minimal                 |

### Phase 1 Resource Allocation

Total Phase 1 MCP resource requirements:

- **Qdrant Memory**: 8GB RAM
- **Serena**: 4GB RAM
- **GitHub MCP**: 2GB RAM
- **Sequential Thinking**: 2GB RAM
- **FileSystem**: 1GB RAM
- **Zen Orchestrator**: 4GB RAM
- **System overhead**: 15GB RAM
- **Total**: 36GB RAM minimum

## Future MCP Expansion (Phase 4)

Potential MCPs for future phases:

- **Slack MCP**: Team communication integration
- **Jira MCP**: Project management integration
- **AWS MCP**: Cloud resource management
- **Stripe MCP**: Payment processing for SaaS
- **Custom Domain MCPs**: Industry-specific tools

Each new MCP should be evaluated against:

- Clear business value
- Maintenance burden
- Security implications
- Cost per operation

## Related Documentation

- [Four User Journeys](./four-journeys.md) - User journey progression and MCP integration
- [Architecture Decision Record](./ADR.md) - Technical decisions including Phase 1 expansion
- [Development Guidelines](./development.md) - MCP development standards and conventions
