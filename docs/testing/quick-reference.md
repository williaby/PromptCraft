# Testing Quick Reference

## Essential Commands

### Setup

```bash
uv sync
uv run pre-commit install
```

### Basic Testing

```bash
# Run all tests
uv run nox

# Unit tests only
uv run nox -s tests_unit

# With coverage
uv run pytest tests/unit/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Linting and formatting
uv run nox -s lint

# Type checking
uv run nox -s type_check

# Pre-commit hooks
uv run nox -s pre_commit
```

### Security

```bash
# Security scans
uv run nox -s security

# Individual tools
uv run bandit -r src
uv run safety check
```

### Performance

```bash
# Start app and run performance tests
uv run python -m src.main &
uv run nox -s performance_testing
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
uv run pytest -m "not slow"    # Skip slow tests
uv run pytest -m integration   # Integration tests only
uv run pytest -m unit         # Unit tests only
uv run pytest -m security     # Security tests only
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
