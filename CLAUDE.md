# CLAUDE.md

Project-scoped guidance for Claude Code working in PromptCraft-Hybrid. This file
layers on top of the global standards at `~/.claude/CLAUDE.md` (v1.4.0); where a
rule here conflicts with global, project wins per the scoped-context rule.

## Project Overview

PromptCraft-Hybrid is an AI workbench that transforms queries into accurate,
context-aware outputs through intelligent orchestration and multi-agent
collaboration. Hybrid architecture: on-premise compute plus an external Qdrant
vector database on Unraid, deployed to an Ubuntu VM.

**Key architecture concepts:**

- **Dual orchestration**: real-time agent flows for user interaction; Prefect
  for background workflows.
- **Four progressive journeys**: prompt enhancement through full multi-agent
  automation.
- **HyDE query enhancement**: three-tier query analysis for retrieval accuracy.
- **Agent-first design**: specialized agents with dedicated knowledge bases
  under `knowledge/{agent_id}/`.
- **C.R.E.A.T.E. framework**: prompt engineering methodology (Context, Request,
  Examples, Augmentations, Tone and Format, Evaluation).

**Tech stack:**

- Python 3.11+ with Poetry
- Gradio UI, FastAPI backend
- External Qdrant at 192.168.1.16:6333 for semantic search
- Azure AI for LLM services
- Docker multi-stage builds
- Prefect for background orchestration

## Repository Layout

```text
src/                     # Application code (see module map below)
tests/                   # Pytest suite; subdirs by type (unit/integration/e2e/...)
knowledge/{agent_id}/    # Agent-scoped knowledge files (RAG-ingested)
docs/                    # Product docs, standards, architecture records
docs/standards/          # Detailed specs referenced by this file
.claude/                 # Project-level commands, settings, standards
config/                  # Application configuration
database/                # Schema and migrations
temp_cleanup/            # Holding area for in-flight files; not shipped
```

`src/` module purpose (one-liner each):

| Module | Purpose |
| --- | --- |
| `agents/` | Agent registry, base classes, discovery |
| `api/` | FastAPI endpoints (dynamic loading, A/B testing, core API) |
| `auth/`, `auth_simple/` | Auth and authorization frameworks |
| `config/` | Pydantic-validated settings per environment |
| `core/` | Query counseling, HyDE processor, user control system |
| `database/` | Models and connection management |
| `mcp_integration/` | Model Context Protocol bridging |
| `ui/` | Gradio journey interface |
| `utils/` | Encryption, logging, circuit breakers, resilience |
| `monitoring/`, `metrics/` | Observability |
| `security/`, `standards/` | Security utilities and validation standards |

## Quick Start

```bash
# Complete development setup
make setup

# Dependencies and pre-commit install
poetry install --sync
poetry run pre-commit install

# Validate GPG and SSH keys are present (required)
gpg --list-secret-keys              # GPG key for .env encryption
ssh-add -l                          # SSH key for signed commits
git config --get user.signingkey    # Signing key for git
```

## Commands

### Testing (tiered)

```bash
make test-fast          # < 1 min, inner dev loop
make test-pre-commit    # < 2 min, pre-commit gate
make test-pr            # < 5 min, PR gate
make test               # full suite
```

### Quality and security

```bash
make format             # Ruff format (project uses 120 char line length)
make lint               # Ruff + pre-commit-equivalent linters
make pre-commit         # Run all pre-commit hooks manually
make security           # Bandit, pip-audit, Semgrep
poetry run python src/utils/encryption.py   # Validate env + keys
```

> **Reference:** `docs/standards/development-commands.md`

## Agent and Skill Orchestration

Use the built-in **Agent** tool for specialized work and the **Skill** tool for
the shared skill catalog. Do not route tasks through retired `mcp__zen__*` tool
names; those are superseded by subagents and skills.

**When to delegate via `Agent`:**

| Task type | Subagent |
| --- | --- |
| Broad codebase exploration (read-only) | `Explore` |
| Implementation planning | `Plan` |
| Security review | `security-auditor` or relevant `owasp-*` agent |
| Code review | `code-reviewer` |
| Test authoring | `test-engineer` or `test-writer` |
| Documentation | `documentation-writer` |
| Database work | `database-operations-agent` |
| Debugging | start with the `systematic-debugging` skill |

**When to use `Skill`:**

For named workflows: `brainstorming`, `test-driven-development`,
`writing-plans`, `executing-plans`, `verification-before-completion`,
`requesting-code-review`, `systematic-debugging`, `ci-fix`, `pr-review`,
`handoff`. Prefer the skill over ad-hoc improvisation when one applies.

**Model selection** (per global guidance; project overrides none):

| Task type | Model |
| --- | --- |
| Complex reasoning, architecture, ADRs | Opus 4.7 |
| Standard development | Sonnet 4.6 (default) |
| Read-only exploration | Haiku 4.5 |

### Task tracking

Use `TodoWrite` for any task with three or more steps or spanning multiple
turns. Mark each item `completed` immediately on finish; do not batch. For
plans that must survive compaction, see the `writing-plans` skill. Note:
`docs/planning/` is **gitignored** (local scratch only); use
`docs/architecture/` for tracked plans and ADR-style decision records.

## Development Standards

### Linting and formatting (MANDATORY)

- **Python**: `pyproject.toml` with Ruff format + lint; line length **120**
  (project override of global 88). Type checking currently uses MyPy; migration
  to BasedPyright strict is a tracked improvement.
- **Markdown**: `.markdownlint.json`, 120-char lines.
- **YAML**: `.yamllint.yml`, aligned with Python excludes.
- File-specific linters must pass before commit.

> **Reference:** `docs/standards/linting.md`, `docs/standards/python.md` (if present)

### Naming conventions (MANDATORY)

- **Agent ID**: `snake_case` (e.g. `security_agent`)
- **Agent class**: `PascalCase` + `Agent` suffix (e.g. `SecurityAgent`)
- **Knowledge files**: `kebab-case.md` under `knowledge/{agent_id}/`
- **Python**: `snake_case` files and functions, `PascalCase` classes
- **Git branches**: `kebab-case` with prefix, e.g. `feature/add-hyde-variants`

### Knowledge base (MANDATORY)

Files at `knowledge/{agent_id}/{kebab-case-file}.md` with YAML front matter:

```yaml
---
title: [Human-readable title]
version: [X.Y or X.Y.Z]
status: [draft|in-review|published]
agent_id: [snake_case, must match folder]
tags: ['lowercase', 'underscore_separated']
purpose: [Single sentence ending with period.]
---
```

Each H3 section must be self-contained. No H4 or deeper (breaks RAG chunking).
Only `status: published` files are ingested.

> **Reference:** `docs/standards/knowledge-base-standards.md`

### Development philosophy

1. **Reuse first**: search existing modules before building new ones.
2. **Configure, do not build**: prefer MCP-driven integrations and established
   packages over custom scaffolding.
3. **Focus on unique value**: build only what is truly PromptCraft-specific.

## Security

- GPG key required for `.env` encryption and decryption.
- SSH key required for signed commits; `git config user.signingkey` must be set.
- Environment validation runs via `poetry run python src/utils/encryption.py`.
- No unfixed CVEs age past 60 days. Document any suppressions in
  `docs/known-vulnerabilities.md` (OpenSSF release gate).

> **Reference:** `docs/standards/security-requirements.md`

### Response-Aware Development (RAD)

Tag assumptions that could cause production failures using `#CRITICAL`,
`#ASSUME`, `#EDGE` markers paired with `#VERIFY` instructions. Mandatory
categories: timing, external resources, data integrity, concurrency, security,
payment or financial. Current tag count in `src/` is low; expand coverage as
you touch those code paths.

> **Reference (global):** `~/.claude/docs/response-aware-development.md`

## Slash Commands and Skills

Prefer global skills from `~/.claude/` for generic development tasks; fall
back to project-specific commands under `.claude/commands/` only for
PromptCraft-specific workflows.

**Common global skills (partial list):**

- `pr-review`, `ci-fix`, `testing`, `test-coverage`, `quality`, `security`
- `rad` (Response-Aware Development)
- `writing-plans`, `executing-plans`, `phase-gate`, `project-planning`
- `git`, `finishing-a-development-branch`, `using-git-worktrees`
- `brainstorming`, `systematic-debugging`, `debug-tests`
- `verification-before-completion`, `requesting-code-review`,
  `receiving-code-review`
- `doc-audit`, `handoff`, `claude-md-improver`, `skill-creator`

**Project-specific commands (PromptCraft-only functionality):**

```bash
/creation-agent-skeleton           # Scaffold a PromptCraft runtime agent
/creation-knowledge-file           # Scaffold a knowledge base file
/validation-agent-structure        # Validate agent registry structure
/validation-knowledge-chunk        # Validate RAG chunking
/validation-naming-conventions     # Enforce project naming rules
/validation-frontmatter            # Validate YAML frontmatter
/validation-standardize-planning-doc
/quality-frontmatter-validate
/quality-naming-conventions
/migration-knowledge-file          # KB file migrations
/migration-legacy-knowledge
/migration-qdrant-schema           # Qdrant schema migration
/function-loading-control          # Dynamic function loader
/tools-ai-validate                 # AI tools config validation
/workflow-resolve-issue            # Project-specific issue orchestrator
/workflow-review-cycle             # Project-specific review orchestrator
/notification                      # PushCut notifications
/meta-list-commands                # List available commands
/meta-command-help                 # Per-command help
```

> **Migration note:** Several former generic-purpose commands were deleted
> in favor of global skills. Many of the remaining project-specific
> commands should eventually be converted to skills for better discovery
> and auto-activation. Use the `skill-creator` skill when converting.

## Git and Worktrees

- Always run `pre-commit run --all-files` before committing.
- Commits must be signed.
- Conventional commit prefixes: `feat`, `fix`, `docs`, `test`, `chore`,
  `style`, `refactor`, `security`, `build`, `ci`.
- Worktrees live at `.worktrees/<branch-slug>` inside the project; never at
  `~/.config/...` or global paths.

> **Reference:** `docs/standards/git-workflow.md`

## OpenSSF Baseline

Required root files: `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`,
`CHANGELOG.md`, `README.md`. Release gate blocks any vulnerability aged 60+
days; document each in `docs/known-vulnerabilities.md`.

## Scope and Folder-Level CLAUDE.md

This repo has distinct subdomains (`src/api/`, `src/agents/`, `src/auth/`,
`src/mcp_integration/`, `src/ui/`). When a subfolder accrues conventions that
differ from this file, add a focused `src/<area>/CLAUDE.md` with one or two
overrides rather than restating global rules.

## Writing Style

- **No em-dashes** anywhere (docs, commits, ADRs, comments). Use a comma,
  semicolon, colon, or restructured sentence.
- Favor imperatives over narrative prose in standards files.

> **Reference (global):** `~/.claude/.claude/rules/writing.md`

---

*Detailed specifications live in `docs/standards/` and in the global standards
under `~/.claude/`. This file is the entry point; follow the links for depth.*
