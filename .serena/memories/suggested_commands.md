# Essential Development Commands

## Setup and Installation
```bash
# Complete development setup
make setup

# Install dependencies only
poetry install --sync

# Install pre-commit hooks
poetry run pre-commit install
```

## Testing
```bash
# Run all tests with coverage
make test
# or with poetry
poetry run pytest -v --cov=src --cov-report=html --cov-report=term-missing

# Run with nox across Python versions
nox -s tests

# Run specific test types
poetry run pytest tests/unit/ -v -m unit
poetry run pytest tests/integration/ -v -m integration
```

## Code Quality and Formatting
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
markdownlint **/*.md
yamllint .

# Run all pre-commit hooks manually
make pre-commit
```

## Security Checks
```bash
# Run security scans
make security
# or
poetry run safety check
poetry run bandit -r src

# Using nox
nox -s security
```

## Development Environment
```bash
# Start development environment
make dev
# This starts:
# - Gradio UI: http://192.168.1.205:7860
# - Zen MCP Server: http://192.168.1.205:3000
# - External Qdrant: http://192.168.1.16:6333/dashboard

# Build Docker image
docker build -t promptcraft-hybrid .
```

## Utility Commands
```bash
# Clean build artifacts
make clean

# Check for outdated dependencies
poetry show --outdated

# Generate requirements for Docker
./scripts/generate_requirements.sh

# Validate encryption environment
poetry run python src/utils/encryption.py
```

## Claude Code Slash Commands
```bash
# List available commands
/project:list-commands

# Document validation
/project:lint-doc docs/planning/exec.md

# Create knowledge files
/project:create-knowledge-file security oauth2 implementation

# Fix broken links
/project:fix-links docs/planning/project-hub.md
```