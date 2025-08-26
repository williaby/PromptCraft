# Development Commands Reference

> **Complete command reference for PromptCraft development workflow**

## Code Quality & Formatting

### Essential Commands
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

## Testing Commands

### Test Performance Tiers

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

### Test Markers Reference

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

## Security Commands

```bash
# Run security scans
make security
# or
poetry run safety check
poetry run bandit -r src

# Using nox for comprehensive security checks
nox -s security

# Key validation
gpg --list-secret-keys  # Must show GPG key for .env encryption
ssh-add -l              # Must show SSH key for signed commits
git config --get user.signingkey  # Must be configured for signed commits
```

## Docker Commands

```bash
# Development environment with all services on Ubuntu VM
make dev
# or directly with docker-compose
docker-compose -f docker-compose.zen-vm.yaml up -d

# Build Docker image
docker build -t promptcraft-hybrid .

# Run with Docker Compose (development)
docker-compose up -d

# Generate requirements with hash verification for Docker
./scripts/generate_requirements.sh
```

## Development with Nox

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

## Setup Commands

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
```

## Additional Utilities

```bash
# Clean build artifacts and caches
make clean

# Validate environment and encryption keys
poetry run python src/utils/encryption.py

# Check for outdated dependencies
poetry show --outdated

# Update dependencies with hash verification
nox -s deps

# Context7 MCP Server Integration
python scripts/claude-context7-integration.py validate-package fastapi
python scripts/claude-context7-integration.py get-context7-call fastapi "getting started" 3000
python scripts/claude-context7-integration.py claude-help numpy
python scripts/claude-context7-integration.py check-all-deps
```

## Emergency Recovery

```bash
# If pre-commit hooks fail
poetry run pre-commit run --all-files --show-diff-on-failure

# If dependencies are corrupted
poetry install --sync --no-cache

# If Docker build fails
docker system prune -f
docker build --no-cache -t promptcraft-hybrid .

# If tests hang
pkill -f pytest
poetry run pytest --lf  # Run only last failed tests
```
