---
title: Test Engineering Agent Knowledge Base
agent_id: test_engineering
version: 1.0
status: published
tags: ["testing", "test-engineering", "pytest", "coverage", "debugging"]
source: "PromptCraft-Hybrid Project"
purpose: To provide comprehensive knowledge for the TestEngineeringAgent to assist with test creation, execution, and troubleshooting.
---

# Test Engineering Agent Knowledge Base

This document serves as the knowledge base for the TestEngineeringAgent, providing it with detailed information about testing practices, tools, and workflows in the PromptCraft-Hybrid project.

## Agent Overview

The TestEngineeringAgent is a specialized AI agent designed to assist developers with all aspects of software testing in the PromptCraft codebase. It provides capabilities for:

- Test generation and scaffolding
- Test execution and debugging
- Coverage analysis and improvement
- Performance optimization
- Error diagnosis and resolution

## Core Testing Framework

PromptCraft uses a comprehensive testing framework built on industry-standard tools:

### Pytest
The primary testing framework with the following key features:
- Marker-based test categorization (unit, integration, component, etc.)
- Fixture system for test setup and teardown
- Parametrized testing for multiple test cases
- Rich plugin ecosystem

### Nox
Task automation tool that provides:
- Consistent test execution across Python versions
- Session-based organization (unit, integration, lint, etc.)
- Environment isolation for different test types

### Coverage.py
Code coverage analysis tool with:
- Branch coverage tracking
- HTML and JSON reporting
- Coverage threshold enforcement

## Test Categories and Markers

Understanding test types is crucial for proper test organization and execution:

### Unit Tests (`unit`)
- Fast, isolated tests for individual functions and classes
- No external dependencies (databases, APIs, file systems)
- Use mocking for external dependencies
- Run frequently during development
- Target: 85%+ coverage

### Integration Tests (`integration`)
- Tests that verify interaction between components
- May use real external services or databases
- Slower than unit tests but faster than E2E
- Run in CI/CD pipeline
- Target: 70%+ coverage

### Component Tests (`component`)
- Tests for bounded contexts with mocked dependencies
- Validate behavior of larger components
- Use test containers for services when needed

### Contract Tests (`contract`)
- Consumer-driven contract testing with Pact
- Verify API contracts between services
- Run as part of integration testing

### End-to-End Tests (`e2e`)
- Full user journey testing through the application
- Slowest test type, run less frequently
- Use UI automation or API testing

### Performance Tests (`perf`)
- Load, stress, and performance testing
- Use Locust for load testing
- Benchmark critical operations

### Security Tests (`security`)
- Security-focused tests and scans
- Bandit for static analysis
- Safety for dependency vulnerability checks

### Fast Tests (`fast`)
- Subset of tests for quick feedback
- Excludes slow tests by default
- Used for development workflow

## Test Execution Commands

### Basic Test Execution
```bash
# Run all tests (excluding slow ones by default)
poetry run pytest

# Run specific test file
poetry run pytest tests/unit/test_example.py

# Run specific test function
poetry run pytest tests/unit/test_example.py::test_function_name

# Run tests with a specific marker
poetry run pytest -m unit
poetry run pytest -m integration
```

### Advanced Test Execution
```bash
# Run tests in parallel
poetry run pytest -n auto

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run last failed tests
poetry run pytest --lf

# Run with detailed output
poetry run pytest -vv --tb=long

# Drop into debugger on failure
poetry run pytest --pdb

# Show local variables on failure
poetry run pytest --showlocals
```

### Nox Sessions
```bash
# Run unit tests
poetry run nox -s unit

# Run integration tests
poetry run nox -s integration

# Run linting
poetry run nox -s lint

# Run type checking
poetry run nox -s type_check

# Run security checks
poetry run nox -s security
```

## Coverage Analysis

### Coverage Commands
```bash
# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html

# Generate terminal coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Generate JSON coverage report
poetry run pytest --cov=src --cov-report=json

# Run with branch coverage
poetry run pytest --cov=src --cov-branch
```

### Coverage Configuration
Coverage is configured in `pyproject.toml`:
- Source: `src` directory
- Omit: Tests, scripts, and __init__.py files
- Branch coverage enabled
- Minimum threshold: 80%

## Test Structure Guidelines

### File Organization
```
tests/
├── unit/              # Unit tests
│   ├── core/          # Tests for src/core/
│   ├── agents/        # Tests for src/agents/
│   └── utils/         # Tests for src/utils/
├── integration/       # Integration tests
├── contract/          # Contract tests
├── e2e/               # End-to-end tests
├── performance/       # Performance tests
└── security/          # Security tests
```

### Test File Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Test Class Structure
```python
class TestModuleName:
    """Test cases for module_name."""

    def test_descriptive_test_name(self):
        """Test description.

        Arrange: Set up preconditions
        Act: Execute the function
        Assert: Verify the result
        """
        # Arrange
        # ...

        # Act
        # ...

        # Assert
        # ...
```

## Common Testing Patterns

### Fixtures
```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["key"] == "value"
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("valid", True),
    ("invalid", False),
    ("", False),
])
def test_validation(input, expected):
    """Test validation with multiple inputs."""
    assert validate_input(input) == expected
```

### Mocking
```python
from unittest.mock import Mock, patch

@patch("src.module.external_service")
def test_with_mock(mock_service):
    """Test with mocked external service."""
    mock_service.return_value = "mocked_result"
    result = function_using_service()
    assert result == "expected_based_on_mock"
```

## Debugging Strategies

### Verbose Output
```bash
# Maximum verbosity
poetry run pytest -vvv

# Show all output including prints
poetry run pytest -s

# Show local variables on failure
poetry run pytest --showlocals

# Full traceback
poetry run pytest --tb=long
```

### Debugger Integration
```bash
# Drop into debugger on first failure
poetry run pytest --pdb

# Drop into debugger on setup failure
poetry run pytest --pdb-trace

# Set breakpoint in code
import pytest; pytest.set_trace()
```

## Performance Optimization

### Test Speed Strategies
1. Use appropriate fixture scopes (function, class, module, session)
2. Mock external dependencies
3. Use tmp_path fixtures for temporary files
4. Avoid expensive setup in test functions
5. Group related tests in classes

### Parallel Execution
```bash
# Install pytest-xdist
poetry add --group dev pytest-xdist

# Run tests in parallel
poetry run pytest -n auto

# Run with specific number of workers
poetry run pytest -n 4
```

## Error Diagnosis

### Common Error Patterns

#### Import Errors
- Verify all dependencies are in pyproject.toml
- Run `poetry install` after adding dependencies
- Check import paths are correct
- Ensure __init__.py files exist

#### Fixture Errors
- Check fixture name spelling
- Verify fixture location (conftest.py or same file)
- Check fixture dependencies
- Validate fixture scope

#### Assertion Errors
- Add debug prints to see actual values
- Use pytest.set_trace() for interactive debugging
- Check floating point comparisons with pytest.approx()
- Verify test data setup

## Quality Gates

### Coverage Thresholds
- Total project: 80% minimum
- Unit tests: 85% minimum
- Integration tests: 70% minimum

### Code Quality
- All tests must pass
- No high-severity security issues
- Type checking must pass
- Linting must pass

## Best Practices

### Test Design
1. Follow AAA pattern (Arrange, Act, Assert)
2. Write descriptive test names
3. Keep tests focused and isolated
4. Use meaningful assertion messages
5. Test both positive and negative cases

### Coverage
1. Focus on critical business logic first
2. Test error handling paths
3. Include edge cases and boundary conditions
4. Document coverage gaps with reasoning
5. Regularly review and improve coverage

### Performance
1. Keep unit tests under 1 second each
2. Use mocking for external dependencies
3. Optimize test data creation
4. Profile slow tests
5. Separate slow tests with markers

## Integration with Development Workflow

### Local Development
1. Run fast unit tests during development
2. Use TDD approach when possible
3. Run full test suite before commits
4. Use pre-commit hooks for automated checks

### CI/CD Pipeline
1. Run unit tests on every push
2. Run integration tests on pull requests
3. Enforce coverage thresholds
4. Run security scans regularly

## Troubleshooting Guide

### Test Discovery Issues
- Verify test file naming (test_*.py)
- Check that __init__.py exists in test directories
- Ensure pytest is configured correctly in pyproject.toml
- Run with verbose output to see discovery process

### Coverage Issues
- Run with branch coverage enabled
- Check that source paths are correct
- Verify omitted files are appropriate
- Use term-missing to see uncovered lines

### Performance Issues
- Profile test execution with --durations
- Check for unnecessary setup/teardown
- Optimize fixture scopes
- Use parallel execution when possible

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Nox Documentation](https://nox.thea.codes/)
- PromptCraft Testing Documentation
- pyproject.toml test configuration
