# Local Testing Execution Guide

This guide provides comprehensive instructions for running the PromptCraft testing infrastructure locally.

## Prerequisites

### System Requirements

- Python 3.11 or 3.12
- Poetry 1.7.1 or higher
- Node.js (for markdownlint)
- Git (for version control)
- Docker (optional, for container testing)

### Environment Setup

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install Node.js dependencies for linting
npm install -g markdownlint-cli

# Clone the repository and install dependencies
git clone <repository-url>
cd PromptCraft
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

### Encryption Key Validation

Before running tests, ensure encryption keys are properly configured:

```bash
# Validate GPG and SSH keys are present
gpg --list-secret-keys  # Must show GPG key for .env encryption
ssh-add -l              # Must show SSH key for signed commits
git config --get user.signingkey  # Must be configured for signed commits

# Run environment validation
poetry run python src/utils/encryption.py
```

## Testing Framework Overview

The testing infrastructure uses Nox for session management and supports multiple testing levels:

- **Quick**: Essential unit tests only
- **Standard**: Unit + integration + edge cases
- **Comprehensive**: All tests including mutation and security
- **Focused**: Specific test types (security, performance, etc.)

## Basic Test Execution

### Using Nox (Recommended)

```bash
# Run all test sessions
poetry run nox

# Run specific test types
poetry run nox -s tests_unit
poetry run nox -s tests_integration
poetry run nox -s tests_edge_cases

# Run with specific Python version
poetry run nox -s tests_unit -p 3.12

# Run linting and type checking
poetry run nox -s lint
poetry run nox -s type_check

# Run security scans
poetry run nox -s security

# Run pre-commit hooks
poetry run nox -s pre_commit
```

### Using Pytest Directly

```bash
# Basic unit tests
poetry run pytest tests/unit/ -v

# Integration tests
poetry run pytest tests/integration/ -v

# Contract tests
poetry run pytest tests/contract/ -v

# Edge case tests
poetry run pytest tests/unit/test_edge_cases_parametrized.py -v

# With coverage reporting
poetry run pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
poetry run pytest tests/unit/test_query_counselor.py -v

# Run tests matching pattern
poetry run pytest -k "test_security" -v

# Run with markers
poetry run pytest -m "not slow" -v
```

## Advanced Testing

### Contract Testing

```bash
# Run contract tests (with Pact when available)
poetry run nox -s contract_testing

# Run with mock fallback
poetry run pytest tests/contract/ -v
```

### Performance Testing

```bash
# Start application in background
poetry run python -m src.main &

# Run performance tests with Locust
poetry run nox -s performance_testing

# Or run Locust directly
poetry run locust -f tests/performance/locustfile.py --host=http://localhost:7860
```

### Mutation Testing

```bash
# Run mutation testing (comprehensive)
poetry run nox -s mutation_testing

# Run mutmut directly
poetry run mutmut run
poetry run mutmut show
poetry run mutmut html
```

### Security Testing

```bash
# Run comprehensive security scans
poetry run nox -s security

# Individual security tools
poetry run bandit -r src
poetry run safety check
poetry run detect-secrets scan --all-files
```

### DAST Security Scanning

```bash
# Start application
poetry run python -m src.main &

# Wait for startup
sleep 15

# Run DAST scanning
poetry run nox -s dast_scanning

# Or run OWASP ZAP directly
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:7860
```

## Quality Gate Validation

### Comprehensive Quality Gates

```bash
# Run all quality gates
python scripts/quality-gates.py

# Run with custom thresholds
python scripts/quality-gates.py --config quality-gate-config.json

# Skip specific validations
python scripts/quality-gates.py --skip-performance --skip-documentation
```

### Custom Configuration

Create `quality-gate-config.json`:

```json
{
  "min_coverage_total": 85.0,
  "min_coverage_unit": 90.0,
  "max_complexity_average": 5.0,
  "max_high_security_issues": 0,
  "max_medium_security_issues": 3,
  "min_docstring_coverage": 85.0
}
```

## Test Coverage Analysis

### Generate Coverage Reports

```bash
# HTML coverage report
poetry run pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html

# Terminal coverage report
poetry run pytest tests/unit/ --cov=src --cov-report=term-missing

# XML coverage for CI/CD
poetry run pytest tests/unit/ --cov=src --cov-report=xml

# Combined coverage from multiple test types
poetry run pytest tests/unit/ tests/integration/ --cov=src --cov-report=html
```

### Coverage Thresholds

The project enforces minimum coverage thresholds:

- **Total Coverage**: 80% minimum
- **Unit Tests**: 85% minimum
- **Integration Tests**: 70% minimum

## Debugging Test Failures

### Verbose Output

```bash
# Maximum verbosity
poetry run pytest -vvv

# Show all output (including print statements)
poetry run pytest -s

# Stop on first failure
poetry run pytest -x

# Drop into debugger on failure
poetry run pytest --pdb
```

### Log Analysis

```bash
# Show full traceback
poetry run pytest --tb=long

# Show only short traceback
poetry run pytest --tb=short

# Show no traceback
poetry run pytest --tb=no
```

### Test Markers

```bash
# Run only fast tests
poetry run pytest -m "not slow"

# Run only integration tests
poetry run pytest -m integration

# Run only unit tests
poetry run pytest -m unit

# Run security-related tests
poetry run pytest -m security
```

## Performance Optimization

### Parallel Test Execution

```bash
# Install pytest-xdist
poetry add --group dev pytest-xdist

# Run tests in parallel
poetry run pytest -n auto

# Run with specific number of workers
poetry run pytest -n 4
```

### Test Selection

```bash
# Run only changed tests (requires pytest-testmon)
poetry run pytest --testmon

# Run based on Git changes
poetry run pytest --lf  # Last failed
poetry run pytest --ff  # Failed first
```

## Environment-Specific Testing

### Docker Testing

```bash
# Build test image
docker build -t promptcraft-test .

# Run tests in container
docker run --rm promptcraft-test poetry run nox

# Run with volume mount for development
docker run --rm -v $(pwd):/app promptcraft-test poetry run pytest tests/unit/
```

### External Dependencies

For tests requiring external services:

```bash
# Start Qdrant vector database (if needed)
docker run -p 6333:6333 qdrant/qdrant

# Start Redis (for caching tests)
docker run -p 6379:6379 redis:alpine

# Run tests with external dependencies
QDRANT_HOST=localhost REDIS_HOST=localhost poetry run pytest tests/integration/
```

## Continuous Integration Locally

### Simulate CI Pipeline

```bash
# Run the same checks as CI
poetry run nox -s lint type_check tests_unit tests_integration security

# Generate artifacts like CI
mkdir -p artifacts
poetry run pytest tests/unit/ --cov=src --cov-report=xml:artifacts/coverage.xml
poetry run bandit -r src -f json -o artifacts/bandit-report.json
```

### Pre-commit Validation

```bash
# Run all pre-commit hooks
poetry run pre-commit run --all-files

# Run specific hooks
poetry run pre-commit run black
poetry run pre-commit run ruff
poetry run pre-commit run mypy
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `poetry install --with dev` has been run
2. **Permission Errors**: Check file permissions and encryption keys
3. **Coverage Issues**: Verify all source files are included in coverage configuration
4. **Performance Test Failures**: Ensure application is running and accessible

### Environment Reset

```bash
# Clean Poetry cache
poetry cache clear --all pypi

# Reset virtual environment
poetry env remove python
poetry install --with dev

# Clean test artifacts
rm -rf .coverage htmlcov/ .pytest_cache/ .nox/
```

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH="${PWD}/src"
export LOG_LEVEL=DEBUG

# Run tests with debug output
poetry run pytest tests/unit/ -s --log-cli-level=DEBUG
```

## Integration with IDEs

### VS Code Configuration

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/unit"],
  "python.testing.unittestEnabled": false,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "python.formatting.provider": "black"
}
```

### PyCharm Configuration

1. Set interpreter to Poetry virtual environment
2. Configure test runner to use pytest
3. Set working directory to project root
4. Enable coverage analysis

## Best Practices

### Test Organization

- Keep unit tests fast (< 1 second each)
- Use fixtures for common setup
- Mock external dependencies
- Write descriptive test names
- Group related tests in classes

### Coverage Guidelines

- Aim for 85%+ unit test coverage
- Focus on critical business logic
- Test error handling paths
- Include edge cases and boundary conditions
- Document why coverage gaps exist

### Performance Testing Best Practices

- Establish baseline performance metrics
- Test under realistic load conditions
- Monitor memory usage and response times
- Use consistent test environments
- Document performance requirements

---

For additional help or questions about the testing infrastructure, please refer to the project documentation or
contact the development team.
