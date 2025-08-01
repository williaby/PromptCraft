# Test Configuration Documentation

## Single Canonical junit.xml Location

**Issue**: Previously, multiple junit.xml files were being created in different locations, causing confusion and data inconsistency.

**Solution**: All test configurations now use a single canonical location for junit.xml:

```
PROJECT_ROOT/reports/junit.xml
```

## Configuration Files Updated

### 1. pyproject.toml (Primary pytest configuration)

```toml
[tool.pytest.ini_options]
addopts = "--junitxml=reports/junit.xml ..."
```

### 2. VS Code settings.json (IDE test integration)

```json
"python.testing.coverageArgs": [
    "--junitxml=reports/junit.xml",
    ...
]
```

### 3. Coverage System Scripts

- `scripts/coverage_data_loader.py`
- `scripts/vscode_coverage_integration.py`

All updated to use `self.canonical_junit_xml = self.project_root / "reports" / "junit.xml"`

## What Was Fixed

**Before:**

- `./junit.xml` (pytest default)
- `./reports/junit/junit.xml` (VS Code setting)
- `./reports/coverage/junit.xml` (legacy location)

**After:**

- `./reports/junit.xml` (single canonical location)

## Important Notes

1. **Never create junit.xml in subdirectories** - always use the project root
2. **All test commands should output to the same location**
3. **Coverage system expects canonical location only**
4. **VS Code integration uses canonical location**

## Verification

To verify single junit.xml location:

```bash
find . -name "junit.xml" -type f
# Should only show: ./reports/junit.xml
```

To test coverage system with canonical paths:

```bash
python scripts/generate_test_coverage_fast.py
# Should load data from ./reports/junit.xml successfully
```
