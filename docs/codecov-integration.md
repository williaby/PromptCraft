# Codecov Integration Guide

## Overview

The `codecov.yaml` configuration file provides comprehensive coverage reporting for PromptCraft-Hybrid with
support for multiple test types, component-based analysis, and quality gates.

## Key Features

### Flags and Components

- **unit**: Unit tests with 85% target coverage
- **integration**: Integration tests with 75% target coverage
- **performance**: Performance test coverage (optional)
- **contract**: Contract test coverage for MCP integrations
- **mutation**: Mutation test coverage validation

### Component Management

- **core**: Core business logic (`src/core/`)
- **agents**: Agent system (`src/agents/`)
- **config**: Configuration management (`src/config/`)
- **utils**: Utility modules (`src/utils/`)
- **ui**: User interface (`src/ui/`)
- **mcp_integration**: MCP integration layer (`src/mcp_integration/`)
- **ingestion**: Knowledge ingestion pipeline (`src/ingestion/`)

## Coverage Targets

| Test Type | Target Coverage | Threshold |
|-----------|----------------|-----------|
| Overall   | 80%            | ±5%       |
| Unit      | 85%            | ±5%       |
| Integration | 75%          | ±5%       |
| Patch     | 80%            | ±5%       |

## Usage with Nox

The configuration automatically works with existing Nox sessions:

```bash
# Run unit tests with coverage upload
nox -s tests_unit

# Run integration tests with coverage upload
nox -s tests_integration
```

Coverage reports are automatically uploaded to Codecov when `CODECOV_TOKEN` environment variable is set.

## Validation

The configuration has been validated against the Codecov API:

```bash
curl --data-binary @codecov.yaml https://codecov.io/validate
```

Status: ✅ Valid

## Configuration Details

- **Branch**: `main` (default)
- **Report Age**: Maximum 12 hours
- **Precision**: 2 decimal places
- **Coverage Range**: 70-95%
- **Carryforward**: Enabled for unit and integration flags

## Pull Request Integration

- Automatically comments on PRs with coverage changes
- Requires head commit coverage data
- Shows coverage diff and flag-specific results
- Annotations enabled for GitHub checks

## Exclusions

The following paths are excluded from coverage reporting:

- Test directories (`tests/`)
- Documentation (`docs/`)
- Configuration files (`*.yaml`, `*.toml`)
- Build artifacts (`htmlcov/`, `__pycache__/`)
- Scripts and utilities (`scripts/`, `noxfile.py`)
