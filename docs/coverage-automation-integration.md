# Coverage Automation Integration

This document describes the complete coverage automation system that automatically updates coverage reports when
VS Code runs tests.

## System Overview

The coverage automation system provides three integration approaches:

1. **VS Code Tasks** (Recommended for manual control)
2. **VS Code Coverage Hook** (Enhanced automation)
3. **File Watcher Daemon** (Background monitoring)

## Implementation Summary

### ✅ Coverage Contexts Enabled

**Real per-test coverage is now available:**

```toml
# pyproject.toml
[tool.coverage.run]
dynamic_context = "test_function"
```

This eliminates the >100% simulation artifacts and provides actual per-test-type coverage data.

### ✅ Enhanced VS Code Hook

**Location:** `scripts/vscode_coverage_hook.py`

**Features:**

- Detects if coverage contexts are enabled
- Waits for fresh coverage data from VS Code
- Automatically generates all coverage reports
- Provides context-aware feedback

**Usage:**

```bash
# Manual execution
python scripts/vscode_coverage_hook.py

# VS Code Task integration (Ctrl+Shift+P → Tasks: Run Task → Update Coverage Reports)
```

### ✅ VS Code Tasks Integration

**Location:** `.vscode/tasks.json`

**Available Tasks:**

1. **Update Coverage Reports** - Run enhanced coverage hook
2. **Start Coverage File Watcher** - Begin background monitoring
3. **Stop Coverage File Watcher** - End background monitoring

**Access:** `Ctrl+Shift+P` → "Tasks: Run Task" → Select task

### ✅ File Watcher Daemon

**Location:** `scripts/coverage_file_watcher.py`

**Features:**

- Background monitoring of `coverage.xml` and `reports/junit.xml`
- Debounced updates (2-second delay to avoid rapid regeneration)
- Process management with PID files
- Graceful shutdown handling

**Usage:**

```bash
# Start background monitoring
python scripts/coverage_file_watcher.py --daemon

# Check once and exit
python scripts/coverage_file_watcher.py --once

# Stop existing watcher
python scripts/coverage_file_watcher.py --stop
```

## Integration Workflow

### When VS Code Runs "Run Tests with Coverage"

1. **VS Code generates** `coverage.xml` and `reports/junit.xml`
2. **Coverage contexts** capture real per-test coverage data
3. **Hook/Watcher detects** file changes automatically
4. **Reports regenerate** with:
   - Main overview (`reports/coverage/index.html`)
   - By-type analysis (`reports/coverage/by-type/index.html`)
   - Individual test type reports (`reports/coverage/by-type/{type}/index.html`)
   - Standard coverage report integration

### Real Coverage Data vs Simulation

**Before (Simulation):**

- Unit tests: 102.0% (1.2x multiplier)
- Auth tests: 33.9% (0.4x multiplier)
- Results were artificially adjusted

**After (Real Coverage Contexts):**

- Auth tests: 1.8% (actual coverage from 351 tests)
- Unit tests: Real coverage when run
- Data directly from coverage.py contexts

## Usage Recommendations

### Option 1: Manual Control (Recommended)

Use VS Code Tasks for controlled updates:

1. Run tests with coverage in VS Code
2. `Ctrl+Shift+P` → "Tasks: Run Task" → "Update Coverage Reports"
3. Reports update with real coverage data

### Option 2: Background Automation

Use file watcher for continuous updates:

1. `python scripts/coverage_file_watcher.py --daemon`
2. Reports update automatically after any VS Code test run
3. `python scripts/coverage_file_watcher.py --stop` when done

### Option 3: Direct Hook Execution

Run the hook script directly:

```bash
python scripts/vscode_coverage_hook.py
```

## Configuration Files Updated

### pyproject.toml

- ✅ Added `dynamic_context = "test_function"` for real coverage contexts
- ✅ Updated `--junitxml=reports/junit.xml` path

### .vscode/settings.json

- ✅ Updated `--junitxml=reports/junit.xml` for VS Code consistency

### .vscode/tasks.json

- ✅ Added three coverage automation tasks
- ✅ Proper presentation and execution settings

## Current System Status

### Coverage Data (Auth Tests Only)

- **Overall Coverage:** 4.5% (386 / 8,586 lines)
- **Auth Test Coverage:** 1.8% (153 / 8,586 lines, 351 tests)
- **Real Data Source:** Coverage contexts with `test_function` tracking
- **No More >100% Coverage:** Simulation multipliers eliminated

### Automation Features

- ✅ **VS Code Integration:** Works with "Run Tests with Coverage" button
- ✅ **Real Coverage Contexts:** Actual per-test coverage measurement
- ✅ **Background Monitoring:** Optional file watcher daemon
- ✅ **Manual Control:** VS Code tasks for controlled updates
- ✅ **Enhanced Reporting:** Sortable tables, interactive features
- ✅ **File-Explorer Compatible:** No server required, works offline

## Next Steps

1. **Run full test suite** with coverage to get comprehensive data:

   ```bash
   poetry run pytest -v --cov=src --cov-report=html --cov-report=xml --junitxml=reports/junit.xml
   ```

2. **Choose automation approach:**
   - Manual: Use VS Code tasks as needed
   - Automatic: Start file watcher daemon
   - Hybrid: Hook execution after test runs

3. **Monitor coverage contexts** effectiveness with real per-test data

The system now provides both automatic coverage updates and real per-test coverage measurement, eliminating the
>100% simulation artifacts while maintaining the sophisticated reporting capabilities.
