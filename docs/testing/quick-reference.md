# Testing Quick Reference

## Essential Commands

### Setup
```bash
poetry install --with dev
poetry run pre-commit install
```

### Basic Testing
```bash
# Run all tests
poetry run nox

# Unit tests only
poetry run nox -s tests_unit

# With coverage
poetry run pytest tests/unit/ --cov=src --cov-report=html
```

### Code Quality
```bash
# Linting and formatting
poetry run nox -s lint

# Type checking
poetry run nox -s type_check

# Pre-commit hooks
poetry run nox -s pre_commit
```

### Security
```bash
# Security scans
poetry run nox -s security

# Individual tools
poetry run bandit -r src
poetry run safety check
```

### Performance
```bash
# Start app and run performance tests
poetry run python -m src.main &
poetry run nox -s performance_testing
```

### Quality Gates
```bash
# Comprehensive validation
python scripts/quality-gates.py

# With custom config
python scripts/quality-gates.py --config quality-gate-config.json
```

## Test Markers

```bash
poetry run pytest -m "not slow"    # Skip slow tests
poetry run pytest -m integration   # Integration tests only
poetry run pytest -m unit         # Unit tests only
poetry run pytest -m security     # Security tests only
```

## Coverage Thresholds

- **Total**: 80% minimum
- **Unit**: 85% minimum
- **Integration**: 70% minimum

## File Locations

- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Performance**: `tests/performance/`
- **Configuration**: `noxfile.py`, `pyproject.toml`
- **Quality Gates**: `scripts/quality-gates.py`
