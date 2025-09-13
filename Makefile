.PHONY: help install setup test test-fast test-pre-commit test-pr test-performance test-smoke test-with-timing lint mypy-ci mypy-ci-clear format security clean

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3.11
POETRY := poetry

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
	$(POETRY) install --sync

setup: install ## Complete development setup
	$(POETRY) run pre-commit install
	./scripts/generate_requirements.sh
	$(POETRY) run python src/utils/encryption.py
	@echo "Development environment ready!"

test: ## Run tests with coverage
	$(POETRY) run pytest -v --cov=src --cov-report=html --cov-report=term-missing

test-fast: ## Run fast tests for development (< 1 minute)
	$(POETRY) run pytest tests/unit/ tests/auth/ -m "not slow and not performance and not stress" --maxfail=3 --tb=short

test-pre-commit: ## Run pre-commit validation tests (< 2 minutes)
	$(POETRY) run pytest tests/unit/ tests/auth/ tests/integration/ -m "not performance and not stress and not contract" --maxfail=5

test-pr: ## Run PR validation tests (< 5 minutes)
	$(POETRY) run pytest -m "not performance and not stress" --maxfail=10

test-performance: ## Run performance tests only
	$(POETRY) run pytest tests/performance/ -m "performance or stress" --tb=line

test-smoke: ## Run smoke tests for basic functionality
	$(POETRY) run pytest tests/unit/ -m "smoke or fast" --maxfail=1 -x

test-with-timing: ## Run tests with detailed timing analysis
	$(POETRY) run pytest --durations=20 --tb=short

lint: ## Run linting checks (matches CI exactly)
	@echo "🔍 Running linting checks (CI-matching configuration)"
	$(POETRY) run black --check --config=pyproject.toml .
	$(POETRY) run ruff check --config=pyproject.toml --no-cache .
	$(POETRY) run mypy src --config-file=pyproject.toml --cache-dir=.mypy_cache
	markdownlint **/*.md
	yamllint .

lint-local: ## Run linting checks for local development (with fixes)
	@echo "🛠️  Running linting checks with auto-fixes for local development"
	$(POETRY) run black --config=pyproject.toml .
	$(POETRY) run ruff check --fix --config=pyproject.toml .
	$(POETRY) run mypy src --config-file=pyproject.toml

mypy-ci: ## Run MyPy with CI-matching settings (fresh cache)
	$(PYTHON) scripts/mypy_ci_match.py

mypy-ci-clear: ## Run MyPy with CI-matching settings (clear cache first)
	$(PYTHON) scripts/mypy_ci_match.py --clear-cache

format: ## Format code (alias for lint-local for backwards compatibility)
	@echo "⚠️  Note: 'make format' now runs 'make lint-local' for consistency"
	$(MAKE) lint-local

security: ## Run security checks
	$(POETRY) run safety check
	$(POETRY) run bandit -r src

dev: ## Start development environment with all services (including integrated Zen MCP Server)
	docker-compose -f docker-compose.zen-vm.yaml up -d
	@echo "Development environment started!"
	@echo "- Gradio UI: http://127.0.0.1:7860 (Journeys 1, 2, 4)"
	@echo "- FastAPI Backend: http://127.0.0.1:8000 (API endpoints)"
	@echo "- Zen MCP Server: http://127.0.0.1:3000 (AI Agent Orchestration)"
	@echo "- Code-Server IDE: http://127.0.0.1:8080 (Journey 3)"
	@echo "- External Qdrant Dashboard: http://192.168.1.16:6333/dashboard"
	@echo ""
	@echo "✅ Zen MCP Server is now integrated and managed by Docker Compose!"
	@echo "⚡ All services start with a single 'make dev' command"

pre-commit: ## Run all pre-commit hooks manually
	$(POETRY) run pre-commit run --all-files

lint-docs: ## Lint documentation files with Claude Code commands
	@echo "Use Claude Code slash commands for document linting:"
	@echo "  /project:lint-doc docs/planning/exec.md"
	@echo "  /project:fix-links docs/planning/exec.md"
	@echo "  /project:validate-frontmatter docs/planning/exec.md"

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .coverage htmlcov coverage.xml
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf dist build *.egg-info
