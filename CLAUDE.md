# CLAUDE.md

Project-scoped guidance for Claude Code in PromptCraft. This file layers on top of the global standards at
`~/.claude/CLAUDE.md`; where a rule here conflicts with global, project wins.

## Project Overview

PromptCraft refines a user's rough prompt into a standard, robust prompt that returns higher quality results than the
unrefined prompt. The design is recorded in `docs/architecture/adr-001-portable-prompt-refiner.md`:

- **Spec**: versioned plain-file data (C.R.E.A.T.E. checklist plus role and inputs slots, depth tiers, refiner
  prompts, examples, target profiles, golden set). Single source of truth.
- **Claude skill**: hand-written from the spec; Claude does the refining itself.
- **Python library**: `refine(prompt, *, mode, target, engine)` with visible and invisible modes, an
  OpenAI-compatible engine for llama.cpp, and an enforced on-prem data boundary.
- **Scope rule**: build a component only when a named caller exists.

The legacy four-journey workbench (Gradio, FastAPI, Qdrant, Zen MCP) is archived on branch `archive/legacy-hybrid-v0`.
Do not reintroduce its subsystems.

**Current phase:** Phase 0 (archive, tooling, CI alignment). See `docs/architecture/phase-0-migration-plan.md`.

## Repository Layout

```text
src/promptcraft/   # Library package (minimal until Phase 2)
tests/             # pytest suite, selected by markers
knowledge/         # Legacy C.R.E.A.T.E. source material; converted to the spec in Phase 1
docs/              # MkDocs site: ADRs, plans, standards, known vulnerabilities
.claude/rules/     # Project-scoped rules (python, testing, git, pre-commit, writing)
```

## Commands

```bash
make setup        # uv sync --frozen and install git hooks
make check        # lint, typecheck, test, security
make test         # pytest with coverage (80% minimum)
make lint         # ruff format --check and ruff check
make typecheck    # basedpyright strict
make security     # bandit and pip-audit
make docs         # mkdocs build --strict
make pre-commit   # all hooks on all files
uv run nox        # the same gates through nox sessions
```

Use `uv add` for dependencies and commit `uv.lock` with the change.

## Model Selection

Follow the model selection table in the global `~/.claude/CLAUDE.md`. This project adds no overrides. In short: the
most capable model for architecture, ADRs, and refiner prompt design; the default model for standard development; the
fastest model for read-only exploration.

## Agent and Skill Orchestration

Use the **Agent** tool for specialized work and the **Skill** tool for named workflows (`brainstorming`,
`writing-plans`, `test-driven-development`, `systematic-debugging`, `ci-fix`, `pr-review`, `repo-compliance`,
`verification-before-completion`). Prefer a skill over improvisation when one applies.

Use `TodoWrite` for tasks with three or more steps. Tracked plans and decision records go in `docs/architecture/`.

## Development Standards

- **Python**: ruff format and lint, line length 120; basedpyright strict. See `.claude/rules/python.md`.
- **Markdown**: `.markdownlint.json`, 120-character lines. **YAML**: `.yamllint.yml`.
- **Naming**: `snake_case` modules and functions, `PascalCase` classes, `kebab-case` branch names with a prefix.
- **Philosophy**: reuse first, configure rather than build, build only what is PromptCraft-specific.

## Response-Aware Development (RAD)

Tag assumptions that could cause production failures with `#CRITICAL`, `#ASSUME`, or `#EDGE`, each paired with a
`#VERIFY` instruction. Mandatory categories: timing, external resources, data integrity, concurrency, security. For
this project that includes engine latency budgets, llama.cpp schema-constrained output, and the on-prem data boundary.

Reference: `~/.claude/docs/response-aware-development.md`.

## Security

- On-prem prompts never leave the local network; see the on-prem guarantee in ADR-001.
- Commits must be signed.
- No unfixed CVE ages past 60 days; record suppressions in `docs/known-vulnerabilities.md`.

## CI

CI calls the `ByronWilliamsCPA/.github` reusable workflows, pinned by commit SHA with a version comment and advanced
by Renovate. The ruleset requires the bare checks `CI Gate` and `Dependency & Standards Validation`. Qlty and
SonarCloud are required quality services.

## Git

- Conventional commit prefixes: `feat`, `fix`, `docs`, `test`, `chore`, `style`, `refactor`, `security`, `build`,
  `ci`.
- Branch prefixes: `feature/`, `fix/`, `hotfix/`, `release/`, `docs/`, `refactor/`.
- Worktrees live at `.worktrees/<branch-slug>`.

See `.claude/rules/git-workflow.md` and `docs/standards/git-workflow.md`.

## Writing Style

- **No em-dashes** anywhere; a pre-commit hook enforces this.
- Favor imperatives over narrative prose in standards files.

See `.claude/rules/writing.md`.
