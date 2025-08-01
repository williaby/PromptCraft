# CI Workflow Backups

This directory contains backup versions of CI workflows for reference and potential restoration.

## Files

### `ci-original.yml`

- **Original CI workflow** from the repository
- **Execution Pattern**: Sequential test execution within jobs
- **Test Types**: Unit → Integration → Auth → Performance → Stress (sequential)
- **Coverage**: Uses `dynamic_context = "test_function"` for accurate function-level coverage
- **Codecov Flags**: unit, integration, auth, performance, stress
- **Typical Runtime**: 15-20 minutes
- **Features**:
  - Multiple Python version testing (3.11, 3.12, 3.13-dev)
  - Comprehensive test matrix with separate coverage uploads
  - Performance and mutation testing on main branch
  - Docker builds after successful tests

### `ci-optimized.yml`

- **Experimental parallel workflow** using pytest-xdist
- **Execution Pattern**: Parallel test execution within jobs using pytest-xdist
- **Coverage Limitation**: **Incompatible with `dynamic_context = "test_function"`**
- **Performance Gain**: 35-60% time reduction (when coverage config allows)
- **Status**: Not viable due to coverage configuration conflict
- **Issue**: Causes `pytest_cov.DistCovError: Detected dynamic_context=test_function` errors
- **Features**:
  - Pre-cached MyPy stubs for faster type checking
  - Enhanced Poetry installation and caching
  - Parallel test execution with `--numprocesses=2`

## Current Active Workflow

The current `/.github/workflows/ci.yml` implements **job-level parallelization**:

- **Preserves** all codecov flags and function-level coverage
- **Compatible** with `dynamic_context = "test_function"`
- **Performance**: 40-60% time reduction through parallel job execution
- **Approach**: Runs test types concurrently across separate GitHub Actions jobs

## Restoration Instructions

To restore any backup workflow:

```bash
# Restore original workflow
cp docs/planning/backups/ci-workflows/ci-original.yml .github/workflows/ci.yml

# Restore optimized workflow (requires coverage config changes)
cp docs/planning/backups/ci-workflows/ci-optimized.yml .github/workflows/ci.yml
```

## Coverage Configuration Notes

The `ci-optimized.yml` workflow requires changes to `pyproject.toml` coverage configuration:

```toml
[tool.coverage.run]
# Remove or comment out this line for pytest-xdist compatibility:
# dynamic_context = "test_function"

# Alternative approach for parallel coverage:
parallel = true
# source remains the same
```

**Trade-off**: Removing `dynamic_context` will lose function-level coverage granularity and may return to
the 120% coverage estimation issue that originally led to implementing `dynamic_context`.

## Performance Comparison

| Workflow | Runtime | Coverage Accuracy | Codecov Flags | pytest-xdist Compatible |
|----------|---------|-------------------|---------------|------------------------|
| ci-original.yml | 15-20 min | Function-level | ✅ All flags | ❌ Blocked by dynamic_context |
| ci-optimized.yml | 8-12 min | Line-level only | ⚠️ Modified | ✅ Required for parallel tests |
| Current ci.yml | 10-12 min | Function-level | ✅ All flags | ✅ Job-level parallel |

The current active workflow provides the best balance of performance improvement while maintaining coverage accuracy requirements.
