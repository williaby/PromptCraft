# PromptCraft Documentation

Welcome to PromptCraft - AI-powered workbench for prompt orchestration.

## Getting Started

- [Usage Guide](usage-guide.md) - Learn the four journeys and core features
- [Configuration System](configuration-system-guide.md) - Environment setup and configuration
- [API Reference](api-reference.md) - Core functions and programmatic usage

## Development & Security

- [Security Best Practices](security-best-practices.md) - Security guidelines and best practices
- [Testing Guide](testing/quick-reference.md) - Testing frameworks and execution
- [Local Execution Guide](testing/local-execution-guide.md) - Local development setup

## Integration & Tools

- [Context7 Package Reference](context7-package-reference.md) - MCP server integration
- [CodeCov Integration](codecov-integration.md) - Code coverage reporting
- [Migration Guide](migration-guide.md) - Migration procedures and updates

## Security Documentation

- [Security Gates Guide](security/security-gates-guide.md) - Security validation pipeline
- [CodeQL Python Scanning](security/codeql-python-scanning-guide.md) - Static analysis setup
- [Deployment Strategy](deployment-strategy.md) - Secure deployment practices

## Project Overview

PromptCraft-Hybrid is a Zen-powered AI workbench that transforms queries into accurate, context-aware outputs
through intelligent orchestration and multi-agent collaboration.

### Key Features

- **Dual-Orchestration Model**: Zen MCP Server for real-time user interactions, Prefect for background workflows
- **Four Progressive Journeys**: From simple prompt enhancement to full multi-agent automation
- **HyDE Query Enhancement**: Three-tier query analysis system for improved retrieval accuracy
- **Agent-First Design**: Specialized AI agents with dedicated knowledge bases
- **C.R.E.A.T.E. Framework**: Core prompt engineering methodology

### Tech Stack

- Python 3.11+ (Poetry dependency management)
- Gradio UI + FastAPI backend
- External Qdrant vector database for semantic search
- Azure AI integration for LLM services
- Docker containerization with multi-stage builds
- Zen MCP Server for agent orchestration
- Prefect for background orchestration
