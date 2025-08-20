---
title: Qwen Test Engineer Agent Knowledge Base
agent_id: qwen_test_engineer
version: 1.0
status: published
tags: ["testing", "test-engineering", "qwen", "pytest", "coverage"]
source: "PromptCraft-Hybrid Project"
purpose: To provide comprehensive knowledge for the QwenTestEngineerAgent to assist Qwen Code with test-related tasks.
---

# Qwen Test Engineer Agent Knowledge Base

This document serves as the knowledge base for the QwenTestEngineerAgent, providing it with detailed information about testing practices, tools, and workflows in the PromptCraft-Hybrid project, specifically tailored for assisting Qwen Code.

## Agent Purpose

The QwenTestEngineerAgent is a specialized AI agent designed to assist Qwen Code with all aspects of software testing in the PromptCraft codebase. It focuses on providing clear, actionable guidance formatted specifically for an AI assistant working with developers.

## Core Testing Framework

PromptCraft uses a comprehensive testing framework built on industry-standard tools, optimized for Qwen's assistance:

### Pytest (Primary Framework)
Key features for Qwen to understand:
- Marker-based test categorization (unit, integration, component, etc.)
- Fixture system for test setup and teardown
- Parametrized testing for multiple test cases
- Rich plugin ecosystem

### Nox (Task Automation)
- Session-based organization (unit, integration, lint, etc.)
- Environment isolation for different test types
- Consistent execution across Python versions

### Coverage.py (Coverage Analysis)
- Branch coverage tracking
- HTML and JSON reporting
- Coverage threshold enforcement

## Test Categories and Markers (Important for Qwen)

Understanding these is crucial for proper test organization:

### Unit Tests (`unit`)
- Fast, isolated tests for individual functions/classes
- No external dependencies (mock everything)
- Run frequently during development
- Target: 85%+ coverage

### Integration Tests (`integration`)
- Tests interaction between components
- May use real services with containers
- Slower than unit tests
- Target: 70%+ coverage

### Component Tests (`component`)
- Tests for bounded contexts with mocks
- Validate behavior of larger components

### Fast Tests (`fast`)
- Subset for quick feedback
- Excludes slow tests by default

## Key Commands for Qwen to Reference

### Basic Test Execution
```bash
# Run all tests (excluding slow ones by default)
poetry run pytest

# Run specific test file
poetry run pytest tests/unit/test_example.py

# Run tests with a specific marker
poetry run pytest -m unit
```

### Coverage Analysis
```bash
# Generate terminal coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html
```

### Debugging
```bash
# Run with detailed output
poetry run pytest -vv --tb=long

# Drop into debugger on failure
poetry run pytest --pdb

# Show local variables on failure
poetry run pytest --showlocals
```

## File Organization Patterns

Qwen should understand these patterns:

```
tests/
├── unit/              # Unit tests (fast)
│   ├── core/          # Tests for src/core/
│   ├── agents/        # Tests for src/agents/
│   └── utils/         # Tests for src/utils/
├── integration/       # Integration tests
├── contract/          # Contract tests
├── e2e/               # End-to-end tests
└── security/          # Security tests
```

## Test Structure Guidelines

### File Naming
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

## Common Error Patterns and Solutions

### Import Errors
- Verify dependencies in pyproject.toml
- Run `poetry install` after adding dependencies
- Check import paths are correct

### Fixture Errors
- Check fixture name spelling
- Verify fixture location (conftest.py or same file)
- Check fixture dependencies

### Assertion Errors
- Add debug prints to see actual values
- Use pytest.set_trace() for debugging
- Check floating point comparisons with pytest.approx()

## Performance Optimization Tips

### Test Speed Strategies
1. Use appropriate fixture scopes
2. Mock external dependencies
3. Use tmp_path fixtures for temporary files
4. Avoid expensive setup in test functions

### Parallel Execution
```bash
# Run tests in parallel
poetry run pytest -n auto
```

## Coverage Improvement Strategies

### Focus Areas
1. Core business logic first
2. Error handling paths
3. Edge cases and boundary conditions
4. Document coverage gaps with reasoning

### Coverage Commands
```bash
# See exactly which lines are missing
poetry run pytest --cov=src --cov-report=term-missing
```

## Best Practices for Qwen to Recommend

### Test Design
1. Follow AAA pattern (Arrange, Act, Assert)
2. Write descriptive test names
3. Keep tests focused and isolated
4. Test both positive and negative cases

### Code Quality
1. All tests must pass before committing
2. Maintain coverage thresholds
3. Keep tests readable and maintainable
4. Avoid test interdependencies

## Integration with Development Workflow

### Local Development
1. Run fast unit tests during development
2. Use TDD approach when possible
3. Run full test suite before commits

### CI/CD Pipeline
1. Run unit tests on every push
2. Run integration tests on pull requests
3. Enforce coverage thresholds

## Troubleshooting Guide

### Test Discovery Issues
- Verify test file naming (test_*.py)
- Check that __init__.py exists in test directories
- Ensure pytest is configured correctly

### Coverage Issues
- Run with branch coverage enabled
- Check that source paths are correct
- Verify omitted files are appropriate

### Performance Issues
- Profile test execution with --durations
- Check for unnecessary setup/teardown
- Optimize fixture scopes

## References for Qwen

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- PromptCraft Testing Documentation
- pyproject.toml test configuration
