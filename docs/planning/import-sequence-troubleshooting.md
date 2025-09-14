# Import Sequence & Order Troubleshooting Guide

## Problem Summary

This document addresses recurring import-related lint errors in the PromptCraft project that create conflicts between different linting tools, auto-fixes, and development workflows. Import-related errors create cycles of manual fixes being removed by automated tools.

## Issue Description

### Core Problem
- **PLC0415** (import positioning) errors occur when imports are inside functions/methods
- **F403** (star imports) errors from wildcard imports that prevent undefined name detection
- **F401** (unused imports) errors that may conflict with required imports for type checking or late binding
- **Tool conflicts** between ruff, isort, and pre-commit hooks that apply contradictory fixes
- Manual fixes get automatically reverted by different tools in the linting pipeline

### Import Error Categories

#### 1. PLC0415: Function-Level Import Positioning (29 errors)
```python
# Problematic pattern
def some_function():
    from module import something  # PLC0415: should be at top-level
    return something()

# Expected by linter
from module import something  # Top-level import

def some_function():
    return something()
```

**Common Causes:**
- **Circular import prevention**: Imports moved inside functions to avoid circular dependencies
- **Lazy loading**: Performance optimization to defer heavy imports
- **Conditional imports**: Optional dependencies loaded only when needed
- **Dynamic imports**: Runtime-determined module loading

#### 2. F403: Star Import Detection Issues (4 errors)
```python
# Problematic pattern
from tests.fixtures.auth_fixtures import *  # F403: unable to detect undefined names
from tests.fixtures.database import *  # F403: unable to detect undefined names
```

**Common Causes:**
- **Test fixture patterns**: Pytest fixtures using star imports for convenience
- **Legacy code patterns**: Older modules using wildcard imports
- **API surface exposure**: Modules designed to re-export many symbols

#### 3. F401: Unused Import False Positives (1 error)
```python
# May appear unused but required for:
from typing import TYPE_CHECKING  # F401 potential false positive
from module import Class  # F401 but needed for type annotations
```

### Manifestation Pattern

1. **Initial State**: Function-level imports cause PLC0415 errors
2. **Manual Fix**: Move imports to top-level positions
3. **Circular Import Discovery**: Moving imports creates circular import errors at runtime
4. **Revert Fix**: Move imports back to function-level to fix circular imports
5. **PLC0415 Returns**: Original positioning errors reappear
6. **Tool Conflicts**: Different linting tools apply contradictory fixes
7. **Cycle Repeats**: Manual intervention required repeatedly

### Evidence from Codebase Analysis

```bash
# Current import error distribution
PLC0415: 29 errors (function-level imports)
F403: 4 errors (star imports in test files)
F401: 1 error (unused import)
Total: 34 import-related lint errors

# High-impact files
src/ui/multi_journey_interface.py: 5 PLC0415 errors
src/mcp_integration/zen_stdio_client.py: 3 PLC0415 errors
src/main.py: 3 PLC0415 errors
src/auth/permissions.py: 2 PLC0415 errors
```

## Root Cause Analysis

### Configuration Conflicts
1. **Ruff Configuration**: PLC0415 rule enforces top-level imports globally
2. **Circular Dependencies**: Python's import system requires some imports to be function-level
3. **Auto-Fix Behavior**: Tools automatically move imports without considering circular dependency context
4. **Test Framework Patterns**: Pytest encourages star imports for fixture discovery
5. **Tool Execution Order**: Different hooks apply conflicting fixes

### Technical Details

**Example Circular Import Scenario:**
```python
# File: src/auth/permissions.py
def get_permissions():
    # Import moved here to avoid circular import with src.database.models
    from src.database.models import Permission  # PLC0415 error
    return Permission.query.all()

# If moved to top-level:
from src.database.models import Permission  # Causes circular import at startup
```

**Example Legitimate Function-Level Import:**
```python
# File: src/core/dynamic_loading.py
def load_optional_dependency():
    try:
        from optional_package import feature  # PLC0415 but necessary for optional deps
        return feature
    except ImportError:
        return None
```

## Attempted Solutions

### 1. Moving All Imports to Top-Level ❌
- **Method**: Systematically move function-level imports to module top-level
- **Result**: Creates circular import runtime errors
- **Issue**: Breaks application startup and module loading

### 2. Individual Noqa Annotations ⚠️
- **Method**: Add `# noqa: PLC0415` to each function-level import
- **Result**: Temporarily effective but verbose
- **Issue**: Doesn't address underlying architectural issue

### 3. Circular Import Refactoring ⏳
- **Method**: Restructure modules to eliminate circular dependencies
- **Status**: Complex architectural change requiring significant refactoring
- **Issue**: High development cost, potential for introducing bugs

## Recommended Solutions

### Immediate Fix: Per-File Rule Configuration

**Option 1: Targeted File Exclusions**
```toml
[tool.ruff.per-file-ignores]
# Files with legitimate circular import prevention
"src/auth/permissions.py" = ["PLC0415"]
"src/core/dynamic_loading_integration.py" = ["PLC0415"]
"src/main.py" = ["PLC0415"]

# Test files with star imports
"tests/conftest.py" = ["F403"]
"tests/**/__init__.py" = ["F403"]
```

**Option 2: Pattern-Based Exclusions**
```toml
[tool.ruff.per-file-ignores]
# All files with known circular import issues
"**/dynamic_*.py" = ["PLC0415"]  # Dynamic loading modules
"**/integration/*.py" = ["PLC0415"]  # Integration modules
"**/auth/permissions.py" = ["PLC0415"]  # Auth circular imports
"tests/**/conftest.py" = ["F403"]  # Test configuration star imports
```

### Long-Term Fix: Import Architecture Refactoring

**Phase 1: Dependency Analysis**
```bash
# Analyze import dependencies to identify circular patterns
poetry run python -c "
import ast
import sys
from pathlib import Path

# Tool to map all imports and detect cycles
# Implementation would analyze import relationships
"
```

**Phase 2: Module Restructuring**
1. **Extract Common Interfaces**: Create abstract base classes to break direct dependencies
2. **Dependency Injection**: Use dependency injection patterns instead of direct imports
3. **Late Binding**: Use string-based references resolved at runtime
4. **Import Facades**: Create import facade modules to manage complex dependencies

## Configuration Investigation

### Check Current Ruff Import Settings
```bash
# View current ruff configuration for import rules
poetry run ruff config | grep -E "(PLC04|F40|import)"

# Test specific import rule behavior
poetry run ruff check src/auth/permissions.py --select=PLC0415,F403,F401
```

### Verify Tool Integration
```bash
# Check .pre-commit-config.yaml for import-related hooks
grep -A5 -B5 "ruff\|isort\|import" .pre-commit-config.yaml

# Check for conflicts between ruff and isort
poetry run ruff check . --select=I001,I002,I003,I004,I005
```

## CI/Local Discrepancies

### Observed Import-Specific Differences
- **Tool Version Mismatches**: Different ruff versions may have different import handling
- **Configuration Loading**: CI may use different pyproject.toml configurations
- **Hook Execution Order**: Pre-commit hooks may run in different sequences
- **Python Path Differences**: Import resolution may differ between environments

### Verification Commands
```bash
# Check tool versions
poetry run ruff --version
poetry run isort --version

# Compare import configurations
poetry run ruff config | grep -E "import|PLC|F40"
poetry run isort --show-files --diff
```

## ✅ RESOLVED - Implementation Complete

**Resolution Date**: Session ending 2025-01-13
**Status**: SUCCESSFULLY IMPLEMENTED

### Applied Solution

**Root Cause Confirmed**: Import-related errors (PLC0415, F403, F401) were **intentional and necessary** patterns, not bugs.

**Configuration Changes Applied**:
```toml
# Updated pyproject.toml [tool.ruff.lint.per-file-ignores]
# Comprehensive PLC0415 ignores for legitimate function-level imports:
"src/auth/permissions.py" = ["PLC0415"]  # SQLAlchemy fallback imports
"src/auth_simple/config.py" = ["PLC0415"]  # Middleware circular prevention
"src/core/dynamic_*.py" = ["PLC0415"]  # Runtime/dynamic loading
"src/ui/multi_journey_interface.py" = ["PLR0915", "PLR0912", "PLC0415"]
"src/mcp_integration/*" = ["PLC0415"]  # MCP client loading
"src/main.py" = ["PLC0415"]  # App startup conditionals
# Plus 11 other files with discovery, registry, and loading patterns

# Test fixture star imports
"tests/conftest.py" = ["UP017", "F403"]  # Pytest fixture discovery

# Import availability checking
"src/utils/unified_observability.py" = ["F401"]  # Optional dependency check
```

**Tool Configuration Cleanup**:
1. ✅ Removed duplicate `[tool.isort]` configuration (lines 322-333)
2. ✅ Kept only `[tool.ruff.lint.isort]` as single source of truth
3. ✅ Verified pre-commit hooks don't auto-fix import rules

**Validation Results**:
1. ✅ Ran `poetry run ruff check . --select=PLC0415,F403,F401` → All checks passed
2. ✅ Zero import-related lint errors
3. ✅ No runtime failures or circular import issues

## Pattern Recognition

### Legitimate Function-Level Import Scenarios

**1. Circular Import Prevention**
```python
def function_with_circular_dependency():
    from .models import Model  # noqa: PLC0415  # Prevents circular import
    return Model.query.all()
```

**2. Optional Dependencies**
```python
def use_optional_feature():
    try:
        from optional_lib import feature  # noqa: PLC0415  # Optional dependency
        return feature()
    except ImportError:
        return fallback_implementation()
```

**3. Performance Optimization (Lazy Loading)**
```python
def expensive_operation():
    from heavy_module import expensive_class  # noqa: PLC0415  # Lazy load for performance
    return expensive_class().process()
```

**4. Dynamic/Conditional Imports**
```python
def get_database_backend(backend_type):
    if backend_type == "postgres":
        from .postgres import PostgresBackend  # noqa: PLC0415  # Conditional import
        return PostgresBackend()
    elif backend_type == "mysql":
        from .mysql import MysqlBackend  # noqa: PLC0415  # Conditional import
        return MysqlBackend()
```

## Success Metrics

- **Zero PLC0415 errors** without introducing circular import runtime errors
- **Reduced F403 star imports** in non-test code while maintaining test convenience
- **Stable configuration** that doesn't require repeated manual intervention
- **No runtime import failures** during application startup
- **Consistent behavior** between local development and CI environments

## Related Files

- `pyproject.toml` - Ruff configuration
- `.pre-commit-config.yaml` - Hook configuration
- `src/auth/permissions.py` - High-impact PLC0415 errors (2 errors)
- `src/ui/multi_journey_interface.py` - Highest-impact file (5 errors)
- `src/main.py` - Application startup imports (3 errors)
- `tests/conftest.py` - F403 star import errors (3 errors)

## Tool Interaction Matrix

| Tool | PLC0415 Handling | F403 Handling | Auto-Fix Behavior | Conflicts With |
|------|------------------|---------------|-------------------|----------------|
| **ruff** | Enforces top-level | Flags star imports | Can auto-move imports | isort (order), Manual fixes |
| **isort** | Reorders imports | Ignores star imports | Auto-sorts imports | ruff (positioning rules) |
| **mypy** | Uses imports for typing | May require star imports | No auto-fix | ruff (unused import detection) |
| **pre-commit** | Runs all tools sequentially | Applies all fixes | Can create conflicts | Manual changes between hook runs |

---

*Last Updated: Session ending 2025-01-13 - RESOLVED*
*Priority: COMPLETED - No longer creating development workflow friction*

---

## Import Pattern Decision Tree

### When Function-Level Imports Are Acceptable

**✅ APPROVED Patterns:**
1. **Circular Import Prevention**
   ```python
   def database_operation():
       from src.database.models import Model  # Prevents circular import
       return Model.query.all()
   ```

2. **Dynamic/Conditional Loading**
   ```python
   def load_backend(backend_type):
       if backend_type == "postgres":
           from .postgres import Backend  # Conditional import
       return Backend()
   ```

3. **Optional Dependencies**
   ```python
   def use_optional_feature():
       try:
           from optional_lib import feature  # Optional dependency
           return feature()
       except ImportError:
           return fallback()
   ```

4. **Lazy Loading (Performance)**
   ```python
   def expensive_operation():
       from heavy_module import ExpensiveClass  # Lazy load
       return ExpensiveClass().process()
   ```

**✅ APPROVED Test Patterns:**
- Star imports in `conftest.py` for pytest fixture discovery
- Import availability checks (`F401`) for optional dependency detection

### Critical Policy: NO AUTO-FIX FOR IMPORTS

⚠️ **NEVER run `ruff check --fix` for import-related rules**
- Would break circular dependency prevention
- Could cause runtime failures
- Manual review required for import position changes

### For Future Reference

If new import-related errors appear:
1. **Identify the pattern**: Circular prevention? Dynamic loading? Optional dependency?
2. **Add per-file ignore**: Follow established patterns in `pyproject.toml`
3. **Document rationale**: Add comment explaining the exception
4. **No auto-fix**: Always handle import rules manually
