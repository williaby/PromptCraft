# PromptCraft Documentation

Welcome to PromptCraft - AI-powered workbench for prompt orchestration.

## Getting Started

- [Project Overview](planning/project_hub.md)
- [Four Journeys](planning/four-journeys.md)
- [Architecture Decision Records](planning/ADR.md)
- [Development Guidelines](planning/development.md)
- [Phase 1 Issues](planning/phase-1-issues.md)

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
