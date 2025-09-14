# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Code Supervisor Role (CRITICAL)

**Claude Code acts as the SUPERVISOR for all development tasks and MUST:**

1. **Always Use TodoWrite Tool**: Create and maintain TODO lists for ALL tasks to track progress
2. **Assign Tasks to Agents**: Each TODO item should be assigned to a specialized agent via Zen MCP Server
3. **Review Agent Work**: Validate all agent outputs before proceeding to next steps
4. **Use Temporary Reference Files**: Create `.tmp-` prefixed files in `tmp_cleanup/` folder to store detailed context that might be lost during compaction
5. **Maintain Continuity**: Use reference files to preserve TODO details across conversation compactions

### Agent Assignment Patterns

```bash
# Always assign TODO items to appropriate agents:
- Security tasks → Security Agent (via mcp__zen__secaudit)
- Code reviews → Code Review Agent (via mcp__zen__codereview)
- Testing → Test Engineer Agent (via mcp__zen__testgen)
- Documentation → Documentation Agent (via mcp__zen__docgen)
- Debugging → Debug Agent (via mcp__zen__debug)
- Analysis → Analysis Agent (via mcp__zen__analyze)
- Refactoring → Refactor Agent (via mcp__zen__refactor)
```

### Temporary Reference Files (Anti-Compaction Strategy)

**ALWAYS create temporary reference files when:**
- TODO list contains >5 items
- Complex implementation details need preservation
- Multi-step workflows span multiple conversation turns
- Agent assignments and progress need tracking

**Naming Convention**: `tmp_cleanup/.tmp-{task-type}-{timestamp}.md` (e.g., `tmp_cleanup/.tmp-auth4-implementation-20250125.md`)

## Project Overview

PromptCraft-Hybrid is a Zen-powered AI workbench that transforms queries into accurate, context-aware outputs through intelligent orchestration and multi-agent collaboration. It implements a hybrid architecture with on-premise compute, external Qdrant vector database on Unraid, and Ubuntu VM deployment.

**Key Architecture Concepts:**

- **Dual-Orchestration Model**: Zen MCP Server for real-time user interactions, Prefect for background workflows
- **Four Progressive Journeys**: From simple prompt enhancement to full multi-agent automation
- **HyDE Query Enhancement**: Three-tier query analysis system for improved retrieval accuracy
- **Agent-First Design**: Specialized AI agents with dedicated knowledge bases
- **C.R.E.A.T.E. Framework**: Core prompt engineering methodology (Context, Request, Examples, Augmentations, Tone & Format, Evaluation)

**Tech Stack:**

- Python 3.11+ (Poetry dependency management)
- Gradio UI + FastAPI backend
- External Qdrant vector database (192.168.1.16:6333) for semantic search
- Azure AI integration for LLM services
- Docker containerization with multi-stage builds
- Zen MCP Server for agent orchestration
- Prefect for background orchestration

## Essential Development Commands

### Quick Setup
```bash
# Complete development setup
make setup

# Install dependencies and validate keys
poetry install --sync
poetry run pre-commit install

# REQUIRED: Validate GPG and SSH keys are present
gpg --list-secret-keys  # Must show GPG key for .env encryption
ssh-add -l              # Must show SSH key for signed commits
git config --get user.signingkey  # Must be configured for signed commits
```

### Testing (Tiered Approach)
```bash
# Fast Development Loop (< 1 minute)
make test-fast

# Pre-commit Validation (< 2 minutes)
make test-pre-commit

# PR Validation (< 5 minutes)
make test-pr

# Full Test Suite
make test
```

### Code Quality
```bash
# Format code
make format

# Run linting checks
make lint

# Run all pre-commit hooks manually
make pre-commit
```

### Security & Environment
```bash
# Run security scans
make security

# Validate environment and encryption keys
poetry run python src/utils/encryption.py
```

> **Detailed Commands**: See `docs/standards/development-commands.md` for comprehensive command reference

## Core Development Standards

> **Complete Standards**: See `/docs/standards/` directory for detailed specifications

### File-Specific Linting (MANDATORY COMPLIANCE)

- **Python**: `pyproject.toml` (Black 120 chars, Ruff, MyPy, Bandit B101/B601 excluded)
- **Markdown**: `.markdownlint.json` (120 char line length, consistent list style)
- **YAML**: `.yamllint.yml` (aligned with pyproject.toml excludes, 120 chars)
- **MUST RUN** file-specific linters before committing changes

### Naming Conventions (MANDATORY COMPLIANCE)

**Core Components:**
- **Agent ID**: snake_case (e.g., `security_agent`, `create_agent`)
- **Agent Classes**: PascalCase + "Agent" suffix (e.g., `SecurityAgent`)
- **Knowledge Files**: kebab-case.md (e.g., `auth-best-practices.md`)

**Code & Files:**
- **Python Files**: snake_case.py
- **Python Classes**: PascalCase
- **Python Functions**: snake_case()
- **Git Branches**: kebab-case with prefixes (e.g., `feature/add-claude-md-generator`)

### Knowledge Base Standards (MANDATORY)

**File Structure**: `/knowledge/{agent_id}/{kebab-case-filename}.md`

**YAML Front Matter**:
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

**Content Rules:**
- Each H3 section MUST be completely self-contained
- No H4 or deeper headings (breaks RAG chunking)
- Only `status: published` files are ingested by RAG pipeline

> **Complete Knowledge Standards**: See `docs/standards/knowledge-base-standards.md`

## Development Philosophy (MANDATORY)

1. **Reuse First**: Check ledgerbase, FISProject, and .github repositories for existing solutions
2. **Configure, Don't Build**: Use Zen MCP Server, Heimdall MCP Server, and AssuredOSS packages
3. **Focus on Unique Value**: Build only what's truly unique to PromptCraft

### Security Requirements (MANDATORY)

- **GPG Key**: MUST be present for .env encryption/decryption
- **SSH Key**: MUST be present for signed commits to GitHub
- **Key Validation**: Environment MUST validate both keys are available
- **AssuredOSS**: Service account at `.gcp/service-account.json`

> **Complete Security Standards**: See `docs/standards/security-requirements.md`

## Supervisor Workflow Patterns (MANDATORY)

### Task Decomposition and Agent Assignment

**Every development task MUST follow this pattern:**

1. **Create TODO List**: Use TodoWrite tool to break down the task into specific, actionable items
2. **Agent Assignment**: Assign each TODO item to the most appropriate specialized agent
3. **Progress Tracking**: Mark items as in_progress when assigned, completed when validated
4. **Reference File Creation**: For complex tasks, create `.tmp-` reference files in `tmp_cleanup/` folder immediately
5. **Agent Output Validation**: Review all agent work before marking items complete

### Multi-Agent Coordination

**For complex tasks requiring multiple agents:**

1. **Sequential Dependencies**: Use TodoWrite to show dependencies between tasks
2. **Parallel Execution**: Assign independent tasks to multiple agents simultaneously
3. **Integration Points**: Create specific TODO items for integrating agent outputs
4. **Quality Gates**: Assign review tasks to appropriate agents after implementation

> **Complete Workflow Patterns**: See `docs/standards/supervisor-workflows.md`

## Claude Code Slash Commands

**Project-specific slash commands for complete development workflow automation:**

### Core Workflow Commands
```bash
# Complete implementation and validation cycle with multi-agent review
/project:workflow-review-cycle phase X issue Y        # Full review with O3/Gemini
/project:workflow-review-cycle consensus phase X issue Y  # Multi-model consensus

# Comprehensive planning and scope analysis
/project:workflow-plan-validation        # Validate project plans
/project:workflow-implementation        # Guided implementation workflow
```

### Validation & Quality Commands
```bash
# Pre-commit validation with comprehensive quality gates
/project:validation-precommit                              # Full pre-commit validation
/project:validation-naming-conventions                     # Naming standards compliance
/project:validation-knowledge-chunk                        # Knowledge file validation
```

### Creation Commands
```bash
# Generate properly structured files following project standards
/project:creation-knowledge-file security authentication best practices  # Knowledge files
/project:creation-agent-skeleton                                        # Agent scaffolding
```

> **Complete Command Reference**: See `docs/standards/slash-commands.md`

## Important Development Notes

### Mandatory Practices

- **ALWAYS** use TodoWrite tool for task tracking and agent coordination
- **ASSIGN** each TODO item to appropriate specialized agents via Zen MCP Server
- **CREATE** temporary reference files in `tmp_cleanup/` folder for complex multi-step tasks
- **VALIDATE** all agent outputs before marking TODO items as completed
- **ALWAYS** run file-specific linters before committing changes
- **FOLLOW** all naming conventions exactly as specified
- **USE** Poetry for dependency management - avoid pip directly

### Code Review Checklist

- [ ] **TODO Management**: Was TodoWrite used for task tracking?
- [ ] **Agent Assignment**: Were tasks assigned to appropriate specialized agents?
- [ ] **Reference Files**: Were temporary reference files created for complex tasks?
- [ ] **Agent Validation**: Was all agent work reviewed and validated?
- [ ] **Reuse Check**: Could this use existing code from ledgerbase/FISProject?
- [ ] **Security**: Are secrets in encrypted .env? GPG/SSH keys validated?
- [ ] **Naming**: Do all components follow naming conventions?
- [ ] **Knowledge Files**: Do they follow the style guide?

### Pre-Commit Linting Checklist

Before committing ANY changes, ensure:

- [ ] Environment validation passes (GPG and SSH keys present)
- [ ] File-specific linter has been run and passes
- [ ] Pre-commit hooks execute successfully
- [ ] No linting warnings or errors remain
- [ ] Code formatting is consistent with project standards
- [ ] Commits are signed (Git signing key configured)
- [ ] Test coverage remains at or above 80%
- [ ] All security scans pass (Safety, Bandit)
- [ ] **S105/S106 Rule**: Do NOT manually add `# noqa: S105/S106` in test files (globally ignored)
- [ ] **RUF100 Rule**: Run `ruff check --select=RUF100 --fix` to remove unused noqa annotations

## Troubleshooting References

### S105/S106 Noqa Auto-Fix Issues

> **CRITICAL REFERENCE**: `docs/planning/s105-s106-noqa-troubleshooting.md`

**✅ RESOLVED**: S105/S106 hardcoded password detection is now properly configured:
- S105/S106 rules are globally ignored in all test files (`tests/**/*.py`)
- Legitimate constants in `src/auth/constants.py` and `src/security/audit_logging.py` are also ignored
- Manual noqa annotations for S105/S106 in test files are no longer needed
- If S105/S106 errors appear in test files, this indicates a configuration regression

### Import Sequence & Order Conflicts

> **CRITICAL REFERENCE**: `docs/planning/import-sequence-troubleshooting.md`

If encountering import-related lint errors (PLC0415, F403, F401) that create tool conflicts:
- PLC0415 errors often indicate legitimate circular import prevention patterns
- Auto-fix tools may create circular import runtime errors when moving imports
- See the troubleshooting guide for per-file ignore configurations and architectural solutions
- Do NOT manually move function-level imports without checking for circular dependencies

---

*This streamlined configuration focuses on essential guidance. Detailed specifications available in `/docs/standards/` directory.*
