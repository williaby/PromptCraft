# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PromptCraft-Hybrid is a Zen-powered AI workbench that transforms queries into accurate, context-aware outputs through
intelligent orchestration and multi-agent collaboration. It implements a hybrid architecture with on-premise compute,
external Qdrant vector database on Unraid, and Ubuntu VM deployment.

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

## Development Commands

### Setup and Installation

```bash
# Complete development setup
make setup

# REQUIRED: Setup Assured-OSS authentication (first time only)
# Place your service account JSON at .gcp/service-account.json first
./scripts/setup-assured-oss-local.sh

# Install dependencies only
poetry install --sync

# Install pre-commit hooks
poetry run pre-commit install

# REQUIRED: Validate GPG and SSH keys are present
gpg --list-secret-keys  # Must show GPG key for .env encryption
ssh-add -l              # Must show SSH key for signed commits
git config --get user.signingkey  # Must be configured for signed commits
```

### Testing

The project uses a tiered testing approach to optimize development speed while maintaining comprehensive coverage.

#### Test Performance Tiers

**Fast Development Loop (< 1 minute)**
```bash
# Core unit tests only - fastest feedback
make test-fast
# or
poetry run pytest tests/unit/ tests/auth/ -m "not slow and not performance and not stress" --maxfail=3 --tb=short
```

**Pre-commit Validation (< 2 minutes)**
```bash
# Unit + auth + essential integration tests
make test-pre-commit
# or
poetry run pytest tests/unit/ tests/auth/ tests/integration/ -m "not performance and not stress and not contract" --maxfail=5
```

**PR Validation (< 5 minutes)**
```bash
# All tests except performance/stress (CI default for PRs)
make test-pr
# or
poetry run pytest -m "not performance and not stress" --maxfail=10
```

**Full Test Suite**
```bash
# Complete test suite including performance tests (main branch/scheduled)
make test
# or
poetry run pytest -v --cov=src --cov-report=html --cov-report=term-missing
```

**Performance Tests Only**
```bash
# Run only performance and stress tests
make test-performance
# or
poetry run pytest tests/performance/ -m "performance or stress" --tb=line
```

**Additional Test Commands**
```bash
# Smoke tests for basic functionality
make test-smoke

# Tests with detailed timing analysis
make test-with-timing

# Run specific test file
poetry run pytest tests/unit/test_query_counselor.py -v

# Run with different Python version using nox
nox -s tests -p 3.12

# Run integration tests only
pytest tests/integration/ -v

# Run unit tests only
pytest tests/unit/ -v
```

#### Test Markers

The project uses pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (moderate speed)
- `@pytest.mark.performance` - Performance tests (slow, comprehensive)
- `@pytest.mark.stress` - Stress tests (very slow)
- `@pytest.mark.contract` - Contract tests (require external services)
- `@pytest.mark.slow` - Any slow-running test
- `@pytest.mark.fast` - Fast tests for development cycles
- `@pytest.mark.smoke` - Basic functionality validation tests

**Usage Examples:**
```bash
# Run only fast tests
pytest -m "fast"

# Exclude slow tests
pytest -m "not slow"

# Run only unit and integration tests
pytest -m "unit or integration"

# Exclude performance and stress tests
pytest -m "not performance and not stress"
```

### Code Quality and Formatting

```bash
# Format code
make format
# or
poetry run black .
poetry run ruff check --fix .

# Run linting checks
make lint
# or
poetry run black --check .
poetry run ruff check .
poetry run mypy src

# Markdown linting (MANDATORY for all .md files)
markdownlint **/*.md
markdownlint --config .markdownlint.json **/*.md --ignore-path .markdownlintignore

# YAML linting (MANDATORY for all .yml/.yaml files)
yamllint .
yamllint -c .yamllint.yml **/*.{yml,yaml}

# Run all pre-commit hooks manually
make pre-commit
# or
poetry run pre-commit run --all-files
```

### Security Checks

```bash
# Run security scans
make security
# or
poetry run safety check
poetry run bandit -r src

# Using nox for comprehensive security checks
nox -s security
```

### Development with Nox

```bash
# Run tests across Python versions (3.11, 3.12)
nox -s tests

# Run tests with specific Python version
nox -s tests -p 3.12

# Type checking with MyPy
nox -s type_check

# Comprehensive linting (Black, Ruff, markdownlint, yamllint)
nox -s lint

# Security analysis (Safety, Bandit, detect-secrets)
nox -s security

# Format code
nox -s format

# Clean up build artifacts
nox -s clean
```

### CI/CD Optimization

The CI pipeline uses tiered testing for optimal performance:

**Pull Request Workflow (15 minutes timeout)**
- Runs `pytest -m "not performance and not stress"` for faster feedback
- Excludes 24 performance tests and stress tests
- Focuses on 1,936 core tests for validation

**Main Branch/Scheduled Workflow (25 minutes timeout)**
- Runs full test suite including performance tests
- Generates detailed timing reports with `--durations=20`
- Separate performance testing job for comprehensive validation

**Test Distribution:**
- Unit tests: 1,603 (fast, < 5 minutes)
- Integration tests: 161 (moderate, < 3 minutes)
- Performance tests: 24 (slow, excluded from PRs)
- Auth/Security tests: 35 (fast, always included)

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
# - Cloudflared tunnel provides unified access at single domain
```

### Cloudflared Tunnel Integration

The system uses cloudflared tunnel for unified access to all journeys:

```yaml
# Example cloudflared config.yml for unified access
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

**Benefits of Cloudflared Tunnel Approach:**
- Single domain access for all four journeys
- No nginx or OAuth2 proxy needed
- Built-in Google OAuth authentication
- Automatic SSL termination
- Native WebSocket support for Code-Server
- Simplified infrastructure (40% reduction in complexity)

### Context7 MCP Server Integration

When using Context7 for package documentation, use the integration script to ensure correct package names:

```bash
# Check if package is ready for Context7 use
python scripts/claude-context7-integration.py validate-package fastapi

# Generate properly formatted Context7 call
python scripts/claude-context7-integration.py get-context7-call fastapi "getting started" 3000

# Get Claude-friendly help for any package
python scripts/claude-context7-integration.py claude-help numpy

# Check all project dependencies against Context7 mappings
python scripts/claude-context7-integration.py check-all-deps
```

**Context7 Usage Pattern:**

1. Always check package status first: `validate-package <name>`
2. For verified packages, use `get-context7-call` to generate the proper call
3. For unverified packages, follow the recommendations to resolve Context7 ID first
4. Update `/docs/context7-quick-reference.json` when new packages are verified

**Reference Documentation:**

- **Package Mappings**: `/docs/context7-quick-reference.json` - JSON lookup table for verified Context7 IDs
- **Comprehensive Guide**: `/docs/context7-package-reference.md` - Detailed documentation with examples and best practices
- **Integration Helper**: `/scripts/claude-context7-integration.py` - Validation and call generation script

### Additional Commands

```bash
# Clean build artifacts and caches
make clean

# Run specific test files
poetry run pytest tests/unit/test_query_counselor.py -v

# Run only integration tests
poetry run pytest tests/integration/ -v -m integration

# Run only unit tests
poetry run pytest tests/unit/ -v -m unit

# Skip slow tests
poetry run pytest -m "not slow"

# Generate requirements with hash verification for Docker
./scripts/generate_requirements.sh

# Build Docker image
docker build -t promptcraft-hybrid .

# Run with Docker Compose (development)
docker-compose up -d

# Validate environment and encryption keys
poetry run python src/utils/encryption.py

# Check for outdated dependencies
poetry show --outdated

# Update dependencies with hash verification
nox -s deps
```

## Project Architecture

### Project Documentation Hub

The `docs/planning/project_hub.md` serves as the central index for all project documentation. Key resources:

- **Strategic Vision**: Executive summary, four journeys, MVP definition
- **Standards**: Knowledge file style guide, development guidelines
- **Technical Architecture**: ADR, technical specifications, functional area deep dives
- **Operations**: Server setup, runbook, deployment automation

### Directory Structure

```text
src/
├── agents/          # Multi-agent system framework
│   ├── base_agent.py      # Base agent interface (currently empty - placeholder)
│   ├── create_agent.py    # Agent factory/creation logic
│   └── registry.py        # Agent registry and discovery
├── core/            # Core business logic
│   ├── query_counselor.py # Query processing and routing (currently empty)
│   ├── hyde_processor.py  # HyDE-enhanced retrieval (currently empty)
│   └── vector_store.py    # Vector database interface (currently empty)
├── ui/              # Gradio interface components
├── ingestion/       # Knowledge processing pipeline
├── mcp_integration/ # MCP server integration
├── config/          # Configuration management
└── utils/           # Shared utilities

knowledge/           # Knowledge base with C.R.E.A.T.E. framework
├── create/          # Structured knowledge files
└── domain_specific/ # Specialized domain knowledge

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── fixtures/        # Test fixtures
```

### Key Components

**Multi-Agent System:**

- Base agent framework in `src/agents/base_agent.py` (currently placeholder)
- Agent registry for discovery and coordination in `src/agents/registry.py`
- Specialized agents coordinated through Zen MCP Server

**Query Processing:**

- HyDE-enhanced retrieval for improved semantic search (three-tier analysis)
- Tiered search strategy in `src/core/hyde_processor.py` (currently placeholder)
- Query routing and counseling in `src/core/query_counselor.py` (currently placeholder)

**Knowledge Management:**

- External Qdrant vector database (192.168.1.16:6333) for semantic storage and retrieval
- Knowledge files follow C.R.E.A.T.E. Framework with YAML frontmatter
- Strict markdown formatting per `docs/style_guide.md`
- Ingestion pipeline processes various document types

**Development Status:**

- Project is in early development phase with many core files as placeholders
- Architecture is well-defined but implementation is pending
- Focus on configuration over custom development (reuse existing tools)
- Main application entry point: `src/main:app` (FastAPI/Uvicorn)
- Gradio UI accessible at <http://192.168.1.205:7860>
- External Qdrant vector database at 192.168.1.16:6333 (hosted on Unraid)
- Cloudflare tunnel provides secure remote access to development environment

### Configuration Files

**Python Configuration:**

- `pyproject.toml` - Primary configuration for Poetry, tools (black, ruff, mypy, pytest), and project metadata
- `noxfile.py` - Automation for testing across Python versions and running quality checks
- `.pre-commit-config.yaml` - Git hooks for code quality enforcement

**Development Tools:**

- Black (line length 120) for code formatting
- Ruff for comprehensive linting with extensive rule set (E, W, F, I, C, B, UP, N, YTT, ANN, S, etc.)
- MyPy for type checking with strict configuration
- Pytest with coverage reporting (80% minimum, HTML and XML reports)
- Bandit for security scanning (excludes B101, B601)
- Safety for dependency vulnerability checking
- Pre-commit hooks with Poetry integration

**File-Specific Linting (MANDATORY COMPLIANCE):**

- **Python**: `pyproject.toml` (PRIMARY - Black 120 chars, Ruff, MyPy, Bandit B101/B601 excluded)
- **Markdown**: `.markdownlint.json` (120 char line length, consistent list style, 2-space indent)
- **YAML**: `.yamllint.yml` (aligned with pyproject.toml excludes, 120 chars, 2-space indent)
- **JSON**: Built-in formatting validation via pre-commit hooks
- **EditorConfig**: `.editorconfig` (consistent with pyproject.toml Python settings)

## Progressive User Journeys

The system implements four levels of AI assistance:

1. **Journey 1: Quick Enhancement** - Basic prompt improvement
2. **Journey 2: Power Templates** - Template-based prompt generation
3. **Journey 3: Light IDE Integration** - Local development integration
4. **Journey 4: Full Automation** - Complete execution automation

## Knowledge Base and Development Philosophy

### C.R.E.A.T.E. Framework

Knowledge files in `knowledge/` follow the C.R.E.A.T.E. Framework:

- **C - Context**: Role, persona, background, goals
- **R - Request**: Core task, deliverable specifications
- **E - Examples**: Few-shot examples and demonstrations
- **A - Augmentations**: Frameworks, evidence, reasoning prompts
- **T - Tone & Format**: Voice, style, structural formatting
- **E - Evaluation**: Quality checks and verification

Each knowledge file includes YAML frontmatter with metadata for RAG filtering and follows strict markdown formatting
guidelines defined in `docs/style_guide.md`.

### Development Philosophy (MANDATORY)

1. **Reuse First**: Check ledgerbase, FISProject, and .github repositories for existing solutions
   - CI/CD & DevOps: Copy from ledgerbase
   - Documentation Templates: Reuse from FISProject
   - GitHub Actions: Use workflows from .github
   - UI Components: Leverage existing promptcraft_app.py
2. **Configure, Don't Build**: Use Zen MCP Server, Heimdall MCP Server, and AssuredOSS packages
   - Orchestration: Use Zen MCP Server instead of custom orchestration
   - Analysis: Integrate Heimdall MCP Server rather than building analysis tools
   - Security: Use AssuredOSS packages when available
3. **Focus on Unique Value**: Build only what's truly unique to PromptCraft
   - Claude.md generation logic
   - Prompt composition intelligence
   - User preference learning
   - C.R.E.A.T.E. framework implementation

### Naming Conventions (MANDATORY COMPLIANCE)

**ALL components must follow these strict naming conventions:**

#### Core Components

- **Agent ID**: snake_case (e.g., `security_agent`, `create_agent`, `irs_8867`)
- **Agent Classes**: PascalCase + "Agent" suffix (e.g., `SecurityAgent`, `CreateAgent`)
- **Knowledge Folders**: snake_case matching agent_id (e.g., `/knowledge/security_agent/`)
- **Knowledge Files**: kebab-case.md (e.g., `auth-best-practices.md`)

#### Code & Files

- **Python Files**: snake_case.py (e.g., `src/agents/security_agent.py`)
- **Python Classes**: PascalCase (e.g., `class BaseAgent:`)
- **Python Functions**: snake_case() (e.g., `def get_relevant_knowledge():`)
- **Python Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES = 3`)
- **Test Files**: test_snake_case.py (e.g., `test_security_agent.py`)

#### Git & Development

- **Git Branches**: kebab-case with prefixes (e.g., `feature/add-claude-md-generator`)
- **PR Titles**: Conventional Commits (e.g., `feat(security): add SQL injection detection`)
- **Commit Messages**: Follow Conventional Commits format

### Knowledge Base Standards (MANDATORY)

**ALL knowledge files MUST follow these rules:**

#### File Structure Requirements

```text
/knowledge/{agent_id}/{kebab-case-filename}.md
```

#### YAML Front Matter (MANDATORY)

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

#### Heading Structure (STRICTLY ENFORCED)

- **H1 (#)**: Document title only (MUST match title in front matter)
- **H2 (##)**: Major sections
- **H3 (###)**: Atomic knowledge chunks (self-contained units)
- **H4 and below**: STRICTLY PROHIBITED (breaks RAG chunking)

#### Content Rules

- Each H3 section MUST be completely self-contained
- Complex content (tables, diagrams, code) MUST be preceded by descriptive prose
- Use agent directives: `> **AGENT-DIRECTIVE:** instruction here`
- Only `status: published` files are ingested by RAG pipeline

### Content Standards

- **Machine-readability**: Documents must be flawlessly parsed by remark/TOC tools and RAG pipeline
- **Human clarity**: Raw Markdown should be as legible as rendered HTML
- **Maintainability**: Predictable structure lowers error rates
- **Atomicity**: Each H3 section must be retrievable in isolation

## Security and Docker

### Security Implementation

- Defense-in-depth security with multi-stage Docker builds
- Dependency security with cryptographic hashes in requirements files
- Automated vulnerability scanning with Safety and Bandit
- Container security with non-root user execution (user promptcraft:1000)
- Local encrypted .env files (no secrets in code or commits)
- Pre-commit hooks prevent common security issues
- Health checks and security headers in containers

### Local Encryption Setup (MANDATORY)

**Environment must have both GPG and SSH keys configured:**

#### Required Keys

1. **GPG Key**: For .env file encryption/decryption
   - Used to encrypt sensitive environment variables
   - Must be accessible to the application
   - Separate from commit signing to avoid conflicts

2. **SSH Key**: For signed commits to GitHub
   - Used for commit verification and authentication
   - Must be configured in Git for signed commits
   - Separate from GPG encryption key

#### Assured-OSS Service Account Setup (MANDATORY)

**Local development requires service account for assured-oss package access:**

1. **Service Account File**: Place your Google Cloud service account JSON at:
   - `.gcp/service-account.json` (preferred, git-ignored)
   - `secrets/service-account.json` (alternative, git-ignored)
   - `~/.config/promptcraft/service-account.json` (user-global)

2. **Setup Process**:

   ```bash
   # Create secure directory
   mkdir -p .gcp

   # Copy your service account file (replace with actual path)
   cp /path/to/your/service-account.json .gcp/service-account.json

   # Run setup script
   ./scripts/setup-assured-oss-local.sh
   ```

3. **Security Requirements**:
   - Service account file MUST be git-ignored
   - Never commit service account credentials
   - Re-run setup script if access tokens expire (1 hour lifetime)

#### Key Validation Requirements

- Environment MUST validate both keys are present during startup
- Applications MUST fail fast if required keys are missing
- Follow ledgerbase encryption.py pattern for implementation
- Use Fernet symmetric encryption for .env files

#### Implementation Pattern

```python
# Follow ledgerbase encryption.py pattern
from cryptography.fernet import Fernet
import gnupg  # For GPG operations

def validate_environment_keys():
    """Validate required GPG and SSH keys are present."""
    # Check GPG key availability
    # Check SSH key configuration
    # Fail fast if either is missing
    pass

def encrypt_env_file(content: str) -> str:
    """Encrypt .env content using GPG key."""
    # Follow ledgerbase pattern
    pass
```

### Docker Architecture

- Multi-stage builds for minimal final image size
- Non-root user execution for enhanced security (user promptcraft:1000)
- Health checks on port 7860 (/health endpoint)
- Security environment variables (PYTHONDONTWRITEBYTECODE, PYTHONHASHSEED=random)
- Only essential runtime dependencies in final image
- Application runs via uvicorn with single worker for development
- Requirements pinned with cryptographic hashes in requirements-docker.txt

## Branch Strategy

- Main branch: `main`
- Current development branch: `knowledgebase_edits`
- Create feature branches from `main`

## Strict Linting Compliance (MANDATORY)

### Configuration Hierarchy and Consistency

**IMPORTANT**: All linting configurations must align with existing `pyproject.toml` settings:

- **Python line length**: 120 characters (Black/Ruff in pyproject.toml)
- **Python target versions**: 3.11, 3.12 (pyproject.toml)
- **Exclude patterns**: Must match Black's extend-exclude in pyproject.toml
- **Bandit exclusions**: B101, B601 (as configured in pyproject.toml)

### File-Type Specific Linting Requirements

**ALL modifications to files MUST comply with the following linting standards:**

#### Markdown Files (.md)

- **Configuration**: `.markdownlint.json`
- **Command**: `markdownlint **/*.md`
- **Requirements**: 120 character line length, consistent list styles, proper heading hierarchy
- **MUST RUN** before committing any markdown changes

#### YAML Files (.yml, .yaml)

- **Configuration**: `.yamllint.yml` (aligned with pyproject.toml exclude patterns)
- **Command**: `yamllint **/*.{yml,yaml}`
- **Requirements**:
  - 2-space indentation (consistent with .editorconfig)
  - 120 character line length
  - Exclude patterns match pyproject.toml Black configuration
- **MUST RUN** before committing any YAML changes

#### Python Files (.py)

- **Configuration**: `pyproject.toml` (PRIMARY configuration - DO NOT OVERRIDE)
- **Commands**: `black --check .`, `ruff check .`, `mypy src`
- **Requirements**:
  - 120 character line length (Black/Ruff)
  - Target Python 3.11, 3.12
  - Comprehensive Ruff rule compliance (E, W, F, I, C, B, UP, N, YTT, ANN, S, etc.)
  - Bandit security scanning (excludes B101, B601)
- **MUST RUN** before committing any Python changes

#### JSON Files (.json)

- **Validation**: Automatic via pre-commit hooks
- **Requirements**: Valid JSON syntax, proper formatting
- **MUST PASS** pre-commit validation

### Linting Enforcement Strategy

1. **Pre-commit hooks**: Automatically run linters on staged files
2. **Manual verification**: Run specific linters before major changes
3. **CI/CD integration**: All linting checks must pass in automated pipelines
4. **Editor integration**: Use `.editorconfig` for consistent formatting
5. **Configuration consistency**: All linting configs must align with `pyproject.toml` settings

### Critical Configuration Alignment Rules

- **NEVER override** Python settings from `pyproject.toml`
- **Ensure exclude patterns** in new linting configs match Black's extend-exclude
- **Maintain consistency** between `.editorconfig`, `.yamllint.yml`, and `pyproject.toml`
- **Respect existing** line length, indentation, and target version settings

## Important Development Notes

### Mandatory Practices

- **ALWAYS** run file-specific linters before committing changes
- **VERIFY** linting compliance for the specific file type being modified
- **FOLLOW** all naming conventions exactly as specified
- **USE** Poetry for dependency management - avoid pip directly
- **ENSURE** pre-commit hooks are mandatory and will run automatically
- **FOLLOW** the development philosophy: Reuse First, Configure Don't Build, Focus on Unique Value

### Development Standards (MANDATORY)

#### Security Requirements

- **Secrets**: Use local encrypted .env files (following ledgerbase encryption.py pattern)
- **GPG Key**: MUST be present for .env encryption/decryption
- **SSH Key**: MUST be present for signed commits to GitHub
- **Key Validation**: Environment MUST validate both GPG and SSH keys are available
- **Dependencies**: Use AssuredOSS packages when available
- **Authentication**: Copy auth patterns from ledgerbase
- **Scanning**: All PRs must pass GitGuardian and Semgrep checks

#### Code Standards

- **Zen MCP Integration**: Use Zen MCP Server for ALL orchestration
- **Heimdall Integration**: Use Heimdall MCP Server for analysis
- **API Response Time**: p95 < 2s for Claude.md generation
- **Memory Usage**: < 2GB per container
- **Test Coverage**: Minimum 80% for all Python code

#### Git Workflow

- **Branches**: feature/<issue-number>-<short-name>
- **Commits**: Follow Conventional Commits format
- **PRs**: Must link to GitHub issue (e.g., "Closes #21")
- **Size**: Keep PRs under 400 lines when possible

#### Code Review Checklist

- [ ] **Reuse Check**: Could this use existing code from ledgerbase/FISProject?
- [ ] **Zen/Heimdall Usage**: Is orchestration done through MCP servers?
- [ ] **Security**: Are secrets in encrypted .env? GPG/SSH keys validated?
- [ ] **Focus**: Does this contribute to unique value (Claude.md generation)?
- [ ] **Naming**: Do all components follow naming conventions?
- [ ] **Knowledge Files**: Do they follow the style guide?

### Current State Awareness

- Most source files are currently placeholder/empty as the project is in early development
- Architecture is well-defined in documentation but implementation is pending
- Focus on reading `docs/planning/project_hub.md` for comprehensive project understanding
- Use `docs/planning/repomix-output.xml` to understand repository structure

### Quality Standards

- **80% minimum test coverage** required for all Python code
- **ALL code must pass** Black, Ruff, MyPy, and Bandit checks
- **ALL markdown files must pass** markdownlint validation
- **ALL YAML files must pass** yamllint validation
- **Docker multi-stage builds** for security and efficiency
- **Reproducible builds** with hash verification for dependencies
- **Knowledge files must follow** C.R.E.A.T.E. Framework and style guide
- **EditorConfig compliance** for all file types

### Creating Knowledge Files (MANDATORY PROCESS)

When creating or modifying files in `/knowledge/` directory:

1. **Location**: Files MUST be in `/knowledge/{agent_id}/` matching exact agent_id
2. **Naming**: Use kebab-case for filenames (e.g., `auth-best-practices.md`)
3. **Structure**: Follow the knowledge base template exactly:

   ```yaml
   ---
   title: [Must match H1 heading]
   version: 1.0
   status: draft  # Start as draft, then in-review, finally published
   agent_id: [snake_case matching folder]
   tags: ['lowercase', 'underscore_separated']
   purpose: [Single sentence ending with period]
   ---

   # [Title matching front matter]

   ## [Major Section]

   ### [Atomic Knowledge Chunk]

   Self-contained content that makes sense in isolation...
   ```

4. **Content Rules**:
   - Each H3 section must be self-contained (retrievable independently)
   - No H4 or deeper headings (breaks RAG chunking)
   - Complex content requires descriptive prose before tables/code
   - Use agent directives: `> **AGENT-DIRECTIVE:** instruction`

5. **Lifecycle**:
   - Start with `status: draft`
   - Move to `status: in-review` for PR
   - Only `status: published` files are ingested by RAG pipeline

6. **Validation**: All knowledge files are automatically validated for:
   - Correct YAML front matter
   - Proper heading hierarchy
   - File location matches agent_id
   - Naming conventions compliance

### Claude Code Slash Commands (COMPREHENSIVE WORKFLOW AUTOMATION)

**Project-specific slash commands for complete development workflow automation:**

#### Core Workflow Commands (Multi-Agent Orchestration)

```bash
# Complete implementation and validation cycle with multi-agent review
/project:workflow-review-cycle phase X issue Y        # Full review with O3/Gemini
/project:workflow-review-cycle quick phase X issue Y  # Essential testing only
/project:workflow-review-cycle consensus phase X issue Y  # Multi-model consensus

# Comprehensive planning and scope analysis
/project:workflow-plan-validation        # Validate project plans
/project:workflow-scope-analysis        # Analyze implementation scope
/project:workflow-implementation        # Guided implementation workflow

# Issue resolution with multi-agent coordination
/project:workflow-resolve-issue         # Complete issue resolution workflow
```

#### Validation & Quality Commands

```bash
# Pre-commit validation with comprehensive quality gates
/project:validation-precommit                              # Full pre-commit validation
/project:validation-frontmatter knowledge/agent/file.md    # YAML front matter validation
/project:validation-lint-doc docs/planning/file.md         # Document compliance checking
/project:validation-naming-conventions                     # Naming standards compliance
/project:validation-agent-structure                        # Agent architecture validation
/project:validation-knowledge-chunk                        # Knowledge file validation
/project:validation-standardize-planning-doc               # Planning document standards
```

#### Creation & Migration Commands

```bash
# Generate properly structured files following project standards
/project:creation-knowledge-file security authentication best practices  # Knowledge files
/project:creation-planning-doc                                          # Planning documents
/project:creation-agent-skeleton                                        # Agent scaffolding

# Migration and modernization utilities
/project:migration-legacy-knowledge      # Migrate old knowledge files
/project:migration-knowledge-file       # Update knowledge file format
/project:migration-qdrant-schema        # Update vector database schema
```

#### Meta & Documentation Commands

```bash
# Command system utilities
/project:meta-list-commands             # List all available commands
/project:meta-command-help              # Get help for specific commands
/project:meta-fix-links docs/file.md    # Fix broken internal links
```

**Key Workflow Features:**

- **Multi-Agent Collaboration**: O3 for testing, Gemini for code review through Zen MCP Server
- **Comprehensive Quality Gates**: 80% test coverage, security scanning, linting compliance
- **Automated Validation**: Pre-commit hooks, naming conventions, file structure validation
- **Complete Workflow Automation**: From planning to deployment with validation checkpoints
- **Consensus Building**: Multi-model agreement on implementation decisions
- **Security-First**: Integrated security scanning and best practices validation

**How It Works:**

- Commands are **intelligent prompt templates** stored as `.md` files in `.claude/commands/`
- Available when typing `/` in Claude Code interface
- Use `$ARGUMENTS` placeholder for dynamic input and context
- Invoked as `/project:command-name arguments`
- **Integrate with Zen MCP Server** for multi-agent orchestration
- **Enforce quality standards** automatically through validation workflows

**Development Philosophy Integration:**

These commands embody the project's core principles:

- **Reuse First**: Standardized workflows prevent rebuilding common patterns
- **Configure Don't Build**: Use proven templates rather than custom solutions
- **Focus on Unique Value**: Automate routine tasks to focus on PromptCraft innovation

**Example Workflow:**

```bash
# 1. Plan and validate scope
/project:workflow-scope-analysis phase 2 issue 5

# 2. Create structured implementation
/project:workflow-implementation phase 2 issue 5

# 3. Comprehensive review with multi-agent validation
/project:workflow-review-cycle phase 2 issue 5

# 4. Generate documentation
/project:creation-planning-doc implementation-summary
```

**Advanced Features:**

- **Quality Gate Enforcement**: Automatic failure on coverage < 80%, security issues, or linting violations
- **Multi-Agent Consensus**: O3 develops additional tests, Gemini performs code review, consensus validates decisions
- **Complete Validation Reports**: Pass/fail status for all acceptance criteria with actionable recommendations
- **Integration Testing**: Validates Qdrant, Azure AI, and multi-agent coordination
- **Security Integration**: Bandit scanning, dependency checks, and best practices validation

**Development**: See `docs/planning/slash-command-spec.md` for complete standards and catalog

### Environment Validation (MANDATORY)

Before starting development, ensure:

```bash
# Validate encryption keys are present
poetry run python src/utils/encryption.py

# Manual validation commands
gpg --list-secret-keys                # Must show GPG keys
ssh-add -l                           # Must show SSH keys
git config --get user.signingkey     # Must show signing key
```

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
