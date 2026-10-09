# PromptCraft

PromptCraft refines a rough prompt into a standard, robust prompt that gets higher quality results from the model you
send it to. It targets Claude (through a skill) and local models such as Qwen on llama.cpp (through a small Python
library), with prompts for on-prem use never leaving the local network.

> **Status: Phase 0.** The legacy multi-agent workbench was archived to branch `archive/legacy-hybrid-v0`. The repo is
> being realigned to org tooling (uv, nox, `ByronWilliamsCPA/.github` reusable workflows) before new code lands.

## Design

- [ADR-001: Portable Prompt Refiner](docs/architecture/adr-001-portable-prompt-refiner.md): the design and phased plan.
- [Phase 0 Migration Plan](docs/architecture/phase-0-migration-plan.md): archive, tooling, and CI alignment.

## Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.

```bash
make setup      # uv sync --frozen, install pre-commit and commit-msg hooks
make check      # ruff, basedpyright, pytest with coverage, bandit, pip-audit
make docs       # mkdocs build --strict
uv run nox      # the same gates through nox sessions
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch, commit, and review rules.

## License

[MIT](LICENSE)
