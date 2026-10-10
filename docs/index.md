# PromptCraft

PromptCraft refines a rough prompt into a standard, robust prompt that gets better results from the model you send it
to. It is being rebuilt from a legacy multi-agent workbench into a small, portable library.

## Status

The project is in **Phase 0**: the legacy code is archived on branch `archive/legacy-hybrid-v0`, tooling is moving to
uv and nox, and CI is moving to the `ByronWilliamsCPA/.github` reusable workflows. No refiner code has shipped yet.

## Design

- [ADR-001: Portable Prompt Refiner](architecture/adr-001-portable-prompt-refiner.md) records the design: a shared
  spec, a hand-written Claude skill, and a Python `refine()` library with visible and invisible modes for the on-prem
  family office portal.
- [Phase 0 Migration Plan](architecture/phase-0-migration-plan.md) lists the archive, tooling, and CI alignment steps.

## Development

```bash
make setup      # uv sync and install git hooks
make check      # lint, typecheck, tests, security
make docs       # build this site in strict mode
```
