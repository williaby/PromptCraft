# PromptCraft-Hybrid Development Guide

> This project extends the global CLAUDE.md standards. Only project-specific configurations and deviations are 
> documented below.

## Project Overview

PromptCraft-Hybrid is a Zen-powered AI workbench that transforms queries into accurate, context-aware outputs 
through intelligent orchestration and multi-agent collaboration. It implements a hybrid architecture with on-premise 
compute, external Qdrant vector database on Unraid, and Ubuntu VM deployment.

**Key Architecture Concepts:**

- **Dual-Orchestration Model**: Zen MCP Server for real-time user interactions, Prefect for background workflows
- **Four Progressive Journeys**: From simple prompt enhancement to full multi-agent automation
- **HyDE Query Enhancement**: Three-tier query analysis system for improved retrieval accuracy
- **Agent-First Design**: Specialized AI agents with dedicated knowledge bases
- **C.R.E.A.T.E. Framework**: Core prompt engineering methodology (Context, Request, Examples, Augmentations, 
  Tone & Format, Evaluation)

**Tech Stack:**

- Python 3.11+ (Poetry dependency management)
- Gradio UI + FastAPI backend
- External Qdrant vector database (192.168.1.16:6333) for semantic search
- Azure AI integration for LLM services
- Docker containerization with multi-stage builds
- Zen MCP Server for agent orchestration
- Prefect for background orchestration

## Project-Specific Development Commands

> This project inherits all universal development commands from the global CLAUDE.md. Commands below are PromptCraft-specific or override global behavior.

### Setup and Installation

```bash
# Complete PromptCraft setup
make setup

# REQUIRED: Setup Assured-OSS authentication (first time only)
# Place your service account JSON at .gcp/service-account.json first
./scripts/setup-assured-oss-local.sh

# REQUIRED: Validate GPG and SSH keys are present
gpg --list-secret-keys  # Must show GPG key for .env encryption
ssh-add -l              # Must show SSH key for signed commits
git config --get user.signingkey  # Must be configured for signed commits
```

### Testing Performance Tiers

The project uses a tiered testing approach to optimize development speed while maintaining comprehensive coverage.

```bash
# Fast Development Loop (< 1 minute)
make test-fast

# Pre-commit Validation (< 2 minutes)
make test-pre-commit

# PR Validation (< 5 minutes)
make test-pr

# Full Test Suite
make test

# Performance Tests Only
make test-performance

# Run specific tests without coverage threshold (for focused testing)
poetry run pytest path/to/test.py --cov-fail-under=0
# or without coverage at all
poetry run pytest path/to/test.py
```

### Docker Development

```bash
# Development environment with all services on Ubuntu VM
make dev
# or directly with docker-compose
docker-compose -f docker-compose.zen-vm.yaml up -d

# This starts:
# - Gradio UI: http://127.0.0.1:7860 (Journey 1, 2, 4)
# - FastAPI Backend: http://127.0.0.1:8000 (API endpoints)
# - Code-Server IDE: http://127.0.0.1:8080 (Journey 3)
# - External Qdrant Dashboard: http://192.168.1.16:6333/dashboard (external dependency)
```

### Context7 MCP Server Integration

```bash
# Check if package is ready for Context7 use
python scripts/claude-context7-integration.py validate-package fastapi

# Generate properly formatted Context7 call
python scripts/claude-context7-integration.py get-context7-call fastapi "getting started" 3000
```

## Project-Specific Standards

> All development follows universal quality and security standards. PromptCraft-specific requirements below.

### Performance Requirements
- **API Response Time**: p95 < 2s for Claude.md generation
- **Memory Usage**: < 2GB per container
- **Test Coverage**: Minimum 80% for all Python code

### Security Implementation
- **Secrets Management**: Use local encrypted .env files (following ledgerbase encryption.py pattern)
- **Assured-OSS Service Account**: Place service account JSON at `.gcp/service-account.json`
- **Key Validation**: Environment MUST validate both GPG and SSH keys are available

### Architecture Requirements
- **Zen MCP Integration**: Use Zen MCP Server for ALL orchestration
- **Heimdall Integration**: Use Heimdall MCP Server for analysis
- **External Dependencies**: External Qdrant vector database at 192.168.1.16:6333

## Project Architecture

### Directory Structure

```text
src/
├── agents/          # Multi-agent system framework
├── core/            # Core business logic (query_counselor, hyde_processor, vector_store)
├── ui/              # Gradio interface components
├── ingestion/       # Knowledge processing pipeline
├── mcp_integration/ # MCP server integration
├── config/          # Configuration management
└── utils/           # Shared utilities

knowledge/           # Knowledge base with C.R.E.A.T.E. framework
├── create/          # Structured knowledge files
└── domain_specific/ # Specialized domain knowledge
```

## Progressive User Journeys

The system implements four levels of AI assistance:

1. **Journey 1: Quick Enhancement** - Basic prompt improvement
2. **Journey 2: Power Templates** - Template-based prompt generation
3. **Journey 3: Light IDE Integration** - Local development integration
4. **Journey 4: Full Automation** - Complete execution automation

## Naming Conventions (MANDATORY COMPLIANCE)

**Core Components**
- **Agent ID**: snake_case (e.g., `security_agent`, `create_agent`)
- **Agent Classes**: PascalCase + "Agent" suffix (e.g., `SecurityAgent`)
- **Knowledge Folders**: snake_case matching agent_id (e.g., `/knowledge/security_agent/`)
- **Knowledge Files**: kebab-case.md (e.g., `auth-best-practices.md`)

**Code & Files**
- **Python Files**: snake_case.py (e.g., `src/agents/security_agent.py`)
- **Python Classes**: PascalCase (e.g., `class BaseAgent:`)
- **Python Functions**: snake_case() (e.g., `def get_relevant_knowledge():`)

**Git & Development**
- **Git Branches**: kebab-case with prefixes (e.g., `feature/add-claude-md-generator`)
- **PR Titles**: Conventional Commits (e.g., `feat(security): add SQL injection detection`)

## Knowledge Base Standards (MANDATORY)

### File Structure Requirements

```text
/knowledge/{agent_id}/{kebab-case-filename}.md
```

### YAML Front Matter (MANDATORY)

```yaml
---
title: [Human-readable title]
version: [X.Y or X.Y.Z]
status: [draft|in-review|published]
agent_id: [snake_case - MUST match folder name]
tags: ['lowercase', 'underscore_separated']
purpose: [Single sentence ending with period]
---
```

### Content Rules

- **H1 (#)**: Document title only (MUST match title in front matter)
- **H2 (##)**: Major sections
- **H3 (###)**: Atomic knowledge chunks (self-contained units)
- **H4 and below**: STRICTLY PROHIBITED (breaks RAG chunking)
- Each H3 section MUST be completely self-contained
- Only `status: published` files are ingested by RAG pipeline

## Development Philosophy (MANDATORY)

1. **Reuse First**: Check ledgerbase, FISProject, and .github repositories for existing solutions
2. **Configure, Don't Build**: Use Zen MCP Server, Heimdall MCP Server, and AssuredOSS packages
3. **Focus on Unique Value**: Build only what's truly unique to PromptCraft

## Claude Code Slash Commands

**Project-specific slash commands for complete development workflow automation:**

### Core Workflow Commands
```bash
/project:workflow-review-cycle phase X issue Y        # Full review with O3/Gemini
/project:workflow-plan-validation                     # Validate project plans
/project:workflow-implementation                      # Guided implementation workflow
```

### Validation & Quality Commands
```bash
/project:validation-precommit                         # Full pre-commit validation
/project:validation-frontmatter knowledge/agent/file.md  # YAML validation
/project:validation-naming-conventions               # Naming standards compliance
```

### Creation & Migration Commands
```bash
/project:creation-knowledge-file security authentication  # Knowledge files
/project:creation-planning-doc                           # Planning documents
/project:migration-legacy-knowledge                     # Migrate old knowledge files
```

## Environment Validation (MANDATORY)

Before starting development, ensure:

```bash
# Validate encryption keys are present
poetry run python src/utils/encryption.py

# Manual validation commands
gpg --list-secret-keys                # Must show GPG keys
ssh-add -l                           # Must show SSH keys
git config --get user.signingkey     # Must show signing key
```

## Branch Strategy

- Main branch: `main`
- Create feature branches from `main`
- Follow universal Git workflow with PromptCraft-specific naming: `<type>/<ticket-id>/<short-description>`

## Current Development Status

- Project is in early development phase with many core files as placeholders
- Architecture is well-defined but implementation is pending
- Focus on configuration over custom development (reuse existing tools)
- Main application entry point: `src/main:app` (FastAPI/Uvicorn)
- External Qdrant vector database at 192.168.1.16:6333 (hosted on Unraid)
