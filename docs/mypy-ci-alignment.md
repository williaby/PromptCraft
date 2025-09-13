# MyPy CI Alignment Tool

This document describes the MyPy CI alignment tool that helps ensure local MyPy results match CI expectations.

## Purpose

The `scripts/mypy_ci_match.py` script runs MyPy with CI-identical settings to help developers
identify and fix type checking issues before pushing to CI.

## Usage

```bash
# Run MyPy with CI-matching settings
python scripts/mypy_ci_match.py

# Clear local cache first (recommended for accurate results)
python scripts/mypy_ci_match.py --clear-cache
```

## Features

- Uses fresh cache directory (like CI)
- Sets CI-identical environment variables
- Provides clear success/failure feedback
- Matches CI type checking behavior exactly

## Environment Variables

The tool sets these variables to match CI:

- `CI_ENVIRONMENT=true`
- `MYPY_CACHE_DIR=<temp_directory>`

This ensures local results match CI exactly, reducing surprises in pull requests.
