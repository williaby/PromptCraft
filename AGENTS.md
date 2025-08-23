# Repository Guidelines

For a deeper, process-oriented guide (branching, workflow, dependency policy), see [docs/planning/development.md](docs/planning/development.md).

## Project Structure & Module Organization
- `src/`: Application code by domain (`agents/`, `api/`, `auth/`, `core/`, `database/`, `ui/`, `utils/`, `config/`) — entrypoint: [src/main.py](src/main.py).
- `tests/`: Layered suites (`unit/`, `integration/`, `contract/`, `performance/`, `security/`) — layout: [tests/](tests/).
- `docs/`: MkDocs site content; keep user-facing docs in sync with code.
- `scripts/`: Utility scripts run via `poetry` or `make`.
- `examples/` and `config/`: Sample flows and environment settings.
- Key files: [src/agents/registry.py](src/agents/registry.py), [src/agents/base_agent.py](src/agents/base_agent.py), [Makefile](Makefile), [pyproject.toml](pyproject.toml), [noxfile.py](noxfile.py), [mkdocs.yml](mkdocs.yml).

## Build, Test, and Development Commands
- `make setup`: Install deps, install pre-commit, prime local tooling. See targets in [Makefile](Makefile).
- `make test`: Run full pytest with coverage (HTML in `htmlcov/`).
- `make test-fast`: Quick unit/auth subset for local loops.
- `make lint` / `make format`: Check/auto-fix with Black, Ruff; run mypy, markdownlint, yamllint.
- `make dev`: Start Dockerized dev stack (FastAPI, Gradio, MCP, Qdrant). 
- Run API locally: `poetry run uvicorn src.main:app --reload`.

## Coding Style & Naming Conventions
- Python 3.11; format with Black (120 cols); lint with Ruff; type-check `mypy` (strict where applicable). Tooling in [pyproject.toml](pyproject.toml).
- Imports follow isort (Black profile). Prefer `pathlib` and f-strings.
- Names: modules `snake_case`, classes `PascalCase`, constants `UPPER_CASE`.
- Agents: register with `@agent_registry.register("my_agent")` and implement `execute()`; place code in [src/agents/](src/agents/) and tests in [tests/unit/agents/](tests/unit/agents/). See [src/agents/registry.py](src/agents/registry.py) and [src/agents/base_agent.py](src/agents/base_agent.py).

## Testing Guidelines
- Framework: `pytest` (+ `pytest-cov`). Default markers exclude slow; notable markers: `unit`, `integration`, `contract`, `perf`, `security`, `smoke` (configured in [pyproject.toml](pyproject.toml)).
- Naming: files `test_*.py`, functions `test_*`. Put narrow tests near their domain (e.g., [tests/unit/api/](tests/unit/api/)).
- Coverage: target ≥ 80% on full runs. Commands: `make test`, quick: `make test-fast`.

## Commit & Pull Request Guidelines
- Conventional Commits: `feat(scope): summary`, `fix(scope): summary`. Example: `feat(testing): add coverage analyzer`.
- Before PR: run `make test-pr` and `make lint`; update docs, add tests; include linked issues and screenshots for UI changes.
- Keep PRs focused and describe rationale, risk, and rollout notes.

## Security & Configuration Tips
- Copy [.env.template](.env.template) → `.env`; never commit secrets. Use environment-specific files (`.env.dev`, `.env.staging`, `.env.prod`). See [SECURITY.md](SECURITY.md) for guidance.
- Validate security: `make security` (Safety, Bandit). Pre-commit hooks (see [.pre-commit-config.yaml](.pre-commit-config.yaml)) enforce lint/format.
