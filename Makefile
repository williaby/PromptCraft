# Thin wrappers over uv and nox. CI uses the ByronWilliamsCPA/.github
# reusable workflows; these targets mirror them locally.

.PHONY: help setup sync test lint format typecheck security docs pre-commit check clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup:  ## Install dependencies and git hooks
	uv sync --frozen
	uv run --frozen pre-commit install --hook-type pre-commit --hook-type commit-msg

sync:  ## Sync the environment from uv.lock
	uv sync --frozen

test:  ## Run tests with coverage
	uv run --frozen pytest --cov --cov-report=term-missing

lint:  ## Check formatting and lint rules
	uv run --frozen ruff format --check .
	uv run --frozen ruff check .

format:  ## Apply formatting and autofixes
	uv run --frozen ruff format .
	uv run --frozen ruff check --fix .

typecheck:  ## Run basedpyright (strict)
	uv run --frozen basedpyright

security:  ## Run bandit and pip-audit
	uv run --frozen bandit -c pyproject.toml -lll -r src
	uv run --frozen pip-audit --skip-editable

docs:  ## Build the docs site in strict mode
	uv run --frozen mkdocs build --strict

pre-commit:  ## Run all pre-commit hooks on all files
	uv run --frozen pre-commit run --all-files

check: lint typecheck test security  ## Run every local gate

clean:  ## Remove build and cache artifacts
	rm -rf .nox .pytest_cache .ruff_cache build dist site coverage.xml .coverage
