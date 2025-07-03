.PHONY: help install setup test lint format security clean

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

lint: ## Run linting checks
	$(POETRY) run black --check .
	$(POETRY) run ruff check .
	$(POETRY) run mypy src
	markdownlint **/*.md
	yamllint .

format: ## Format code
	$(POETRY) run black .
	$(POETRY) run ruff check --fix .

security: ## Run security checks
	$(POETRY) run safety check
	$(POETRY) run bandit -r src

dev: ## Start development environment with all services
	docker-compose -f docker-compose.zen-vm.yaml up -d
	@echo "Development environment started!"
	@echo "- Gradio UI: http://192.168.1.205:7860"
	@echo "- Zen MCP Server: http://192.168.1.205:3000"
	@echo "- External Qdrant Dashboard: http://192.168.1.16:6333/dashboard"

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
