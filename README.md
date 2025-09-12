---
title: PromptCraft-Hybrid
version: 1.0
status: published
component: Documentation
tags: ["readme", "overview", "getting-started", "hybrid-ai", "development"]
source: "PromptCraft-Hybrid Project"
purpose: To provide comprehensive overview and quick start guide for the PromptCraft-Hybrid AI development platform.
---

# PromptCraft-Hybrid

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/williaby/PromptCraft/badge)](https://api.securityscorecards.dev/projects/github.com/williaby/PromptCraft)
[![CodeQL](https://github.com/williaby/PromptCraft/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/williaby/PromptCraft/actions/workflows/codeql.yml)
[![Dependency Review](https://github.com/williaby/PromptCraft/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/williaby/PromptCraft/actions/workflows/dependency-review.yml)
[![CI (Safety & Bandit)](https://github.com/williaby/PromptCraft/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/williaby/PromptCraft/actions/workflows/ci.yml)

An advanced, hybrid AI platform designed to transform user queries into highly accurate, context-aware, and
structured outputs. It integrates on-premise hardware with specialized cloud services to deliver a powerful,
cost-effective, and extensible AI development workbench.

## Welcome to the Project

This repository contains all the code and documentation for PromptCraft-Hybrid. Our core philosophy is to
**configure what is common, build what is unique, and enhance what is ambiguous.**

### Your Guide to Our Documentation

This README provides a high-level overview. For detailed information, our documentation is centralized in the
**Project Hub**. It is the single source of truth for this project.

**To get started, please visit the [>> PROJECT HUB <<](docs/planning/project-hub.md) to find the document relevant
to your role.**

---

## At a Glance: Core Features & Architecture

This project is built on several key concepts and a unique hybrid architecture.

### Core Features

* **Four Progressive Journeys**: A unique user model that guides users from simple prompt enhancement to full,
  multi-agent workflow automation.
* **Dual-Orchestration Model**: We use the best tool for the job. **Zen MCP Server** handles real-time,
  user-facing agent orchestration, while **Prefect** manages background, scheduled data workflows like knowledge
  ingestion and quality assurance.
* **HyDE Query Enhancement**: A sophisticated pipeline that analyzes user queries for intent and ambiguity,
  generating hypothetical documents to improve retrieval accuracy.
* **Agent-First Design**: The system's expertise comes from specialized, independent AI agents with their own
  dedicated knowledge bases, allowing for scalable, domain-specific intelligence.
* **Hybrid Infrastructure**: A cost-effective model that leverages external Qdrant on Unraid (192.168.1.16) for
  vector search and Ubuntu VM deployment (192.168.1.205) for application services with minimal cloud dependencies.
* **Cost Control with Free Mode**: New toggle to use only free models (1000 requests/day) in Journey 4, perfect
  for development, testing, and cost-conscious usage.
* **Transparent Pricing**: See exactly which model is being used and its cost in real-time.
* **Smart Routing**: Automatically selects the best available free model when in Free Mode.

### Technology Stack Overview

| Component                    | Technology          | Purpose                                             |
| ---------------------------- | ------------------- | --------------------------------------------------- |
| **Real-Time Orchestration**  | Zen MCP Server      | Coordinates AI agents and tools for user queries.   |
| **Background Orchestration** | Prefect             | Manages scheduled data & maintenance workflows.     |
| **Query Intelligence**       | HyDE Engine         | Enhances ambiguous user queries.                    |
| **RAG Framework**            | LlamaIndex          | Manages data ingestion and retrieval pipelines.     |
| **Vector Database**          | Qdrant (External)   | High-speed semantic search on Unraid (192.168.1.16) |
| **UI Framework**             | Gradio + Code-Server| Journeys 1-4 web interface + IDE integration       |
| **Application Host**         | Ubuntu VM           | Hosts MCP stack on VM (192.168.1.205)               |
| **Unified Access**           | Cloudflared Tunnel  | Single domain access for all journeys              |

### 🚀 Hybrid Infrastructure Discovery

PromptCraft features an intelligent **Hybrid Infrastructure Discovery System** that seamlessly migrates user-level configurations to project-level deployment while preventing resource conflicts and duplication.

**Key Capabilities:**

* **Smart Service Detection**: Automatically discovers existing MCP servers from multiple sources (user-level ~/.claude, Docker containers, NPX services, environment variables)
* **Anti-Duplication**: File locks and resource monitoring prevent duplicate service deployment
* **Cascade Loading**: Intelligent fallback strategy (External → User → Project → Docker → NPX)
* **Agent Discovery**: 24+ YAML-defined AI agents automatically detected and available for dynamic loading
* **Resource Management**: CPU/memory constraints and performance monitoring prevent system degradation

**Discovery API Endpoints:**

* `/api/discovery/agents` - List available agents (24+ detected)
* `/api/discovery/status` - Infrastructure health monitoring
* `/api/discovery/mcp-servers` - MCP server discovery status
* `/api/agents/{id}/load` - Dynamic agent loading
* `/api/agents/{id}/unload` - Resource cleanup

**Benefits:**

* ✅ **Zero Configuration**: Automatically detects and reuses existing services
* ✅ **Resource Efficient**: Eliminates duplicate deployments and optimizes memory usage
* ✅ **Production Ready**: Team deployment without manual service setup
* ✅ **Development Friendly**: Works seamlessly with local development environments

**Usage Examples:**

```python
# Discover and connect to MCP servers
from mcp_integration.smart_discovery import SmartMCPDiscovery

discovery = SmartMCPDiscovery()

# Auto-discover context7 MCP server (NPX-based)
context7 = await discovery.discover_server("context7")
# Returns: ServerConnection(url="npx://@upstash/context7-mcp", type="npx", ...)

# Auto-discover zen-mcp server (local deployment)  
zen_mcp = await discovery.discover_server("zen-mcp")
# Returns: ServerConnection(url="http://localhost:8000", type="embedded", ...)
```

```bash
# Test NPX MCP integration
npm install  # Installs @upstash/context7-mcp, @jschuller/perplexity-mcp, etc.
python validate_npx_integration.py  # Validates complete NPX setup

# Discovery API endpoints
curl http://localhost:7862/api/discovery/status          # Infrastructure status
curl http://localhost:7862/api/discovery/mcp-servers     # Available MCP servers
curl http://localhost:7862/api/discovery/agents          # Available agents
```

> _For detailed technical implementation, see [ADR-014: Hybrid Infrastructure Discovery](./docs/planning/ADR.md#17-adr-014-hybrid-infrastructure-discovery-and-integration)._

> _For a complete breakdown of the architecture and the rationale behind these choices, please see our
[**Architecture Decision Record (ADR)**](./docs/planning/ADR.md)._

---

## Quick Start for Developers

This section provides the essential steps to get the project running on your local machine. For detailed
explanations, standards, and troubleshooting, please refer to the **Developer Guide & Coding Standards**
linked in our Project Hub.

### Claude Code Slash Commands

This project includes custom Claude Code slash commands to automate documentation workflows:

```bash
# List all available commands
/project:list-commands

# Validate document compliance
/project:lint-doc docs/planning/exec.md

# Create new knowledge base files
/project:create-knowledge-file security oauth2 implementation

# Fix broken internal links
/project:fix-links docs/planning/project-hub.md
```

**Commands are stored in** `.claude/commands/` and available when using Claude Code. Type `/` to see all
available commands.

### Prerequisites

* Docker & Docker Compose
* Poetry for Python dependency management
* Nox for task automation
* External Qdrant instance running on Unraid at 192.168.1.16:6333
* Ubuntu VM at 192.168.1.205 for application deployment

### Installation and Setup

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/williaby/PromptCraft.git
   cd PromptCraft-Hybrid
   ```

2. **Configure Environment**:
   * Copy the `.env.example` file to `.env`.
   * Populate the `.env` file with your Azure, Cloudflare, and other necessary API keys.
   * Configure external Qdrant connection (192.168.1.16:6333) and Ubuntu VM deployment target (192.168.1.205).

3. **Install Dependencies**:
   * Use Poetry to install all required Python packages from the `pyproject.toml` file.

   ```bash
   poetry install
   ```

4. **Deploy to Ubuntu VM**:
   * Deploy application services to Ubuntu VM (excludes Qdrant which runs externally on Unraid).

   ```bash
   # On Ubuntu VM (192.168.1.205)
   make dev
   # This starts all services except Qdrant (external dependency)
   ```

5. **Configure Cloudflared Tunnel** (Optional for remote access):
   * Set up cloudflared tunnel for unified web access to all journeys.
   * All services bind to localhost (127.0.0.1) for tunnel routing.

   ```yaml
   # Example cloudflared config.yml
   ingress:
     - hostname: promptcraft.yourdomain.com
       path: /ide/*
       service: http://localhost:8080      # Journey 3 (Code-Server)
     - hostname: promptcraft.yourdomain.com
       path: /api/*
       service: http://localhost:8000      # API endpoints
     - hostname: promptcraft.yourdomain.com
       path: /
       service: http://localhost:7860      # Journey 1, 2, 4 (Gradio)
     - service: http_status:404
   ```

6. **Run Tests**:
   * Use Nox to run the test suite and ensure your environment is set up correctly.

   ```bash
   nox -s tests
   ```

You are now ready to start development!

## Hardware Requirements

### Minimum (Phase 1)

* **RAM**: 36GB minimum
* **Storage**: 500GB NVMe SSD
* **CPU**: 8+ cores recommended
* **Network**: Gigabit LAN

### Recommended (Full Stack)

* **RAM**: 64GB
* **Storage**: 1TB NVMe SSD
* **CPU**: 16+ cores
* **GPU**: Optional for local LLM inference

## Contributing

We welcome contributions! Whether it's a bug report, a new feature, or improvements to our documentation, we
value your input. Please read our **[Developer Guide & Coding Standards (CONTRIBUTING.md)](./CONTRIBUTING.md)**
to get started. For a quick reference to project structure, commands, style, and testing conventions, see the
**[Repository Guidelines](./AGENTS.md)**.

## License

This project is licensed under the MIT License - see the **[LICENSE](./LICENSE)** file for details.
# CI Fix: Updated requirements script defaults
