# Linting Standards

> **Comprehensive linting configuration and standards for PromptCraft development**

## Configuration Hierarchy and Consistency

### Primary Configuration Source

**IMPORTANT**: `pyproject.toml` is the PRIMARY configuration source. All other linting configurations
must align with these settings:

- **Python line length**: 120 characters (Ruff format and lint)
- **Python target versions**: 3.11, 3.12
- **Exclude patterns**: Must match Ruff's `extend-exclude` patterns
- **Bandit exclusions**: B101, B601 (as configured in pyproject.toml)

### Configuration File Alignment

All linting configurations must maintain consistency:

- `.editorconfig` matches `pyproject.toml` (indentation, line length)
- `.yamllint.yml` matches `pyproject.toml` (exclude patterns, line length)
- `.markdownlint.json` matches project standards (line length, style)

## File-Type Specific Linting

### Python Files (.py)

**Configuration**: `pyproject.toml` (PRIMARY - DO NOT OVERRIDE)

Ruff is the formatter and linter. Black is no longer used; do not reintroduce a
`[tool.black]` block.

```toml
[tool.ruff]
line-length = 120
target-version = "py311"
extend-exclude = [
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "venv",
    "build",
    "dist",
    "node_modules"
]

[tool.ruff.format]
# Ruff format provides the formatting previously delegated to Black.
quote-style = "double"
indent-style = "space"

[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "C", "B", "UP", "N", "YTT",
    "ANN", "S", "BLE", "COM", "DTZ", "EM", "ICN",
    "PIE", "PT", "RSE", "RET", "SIM", "TID", "ARG",
    "PTH", "ERA", "PD", "PGH", "PL", "TRY", "RUF"
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.bandit]
exclude_dirs = ["tests", "test_*.py", "*_test.py"]
skips = ["B101", "B601"]  # Skip assert_used and shell_injection_process
```

**Commands**:

```bash
# MUST RUN before committing Python changes
uv run --frozen ruff format --check .   # Code formatting check
uv run --frozen ruff format .           # Apply formatting
uv run --frozen ruff check .            # Comprehensive linting
uv run --frozen ruff check --fix .      # Auto-fix issues
uv run --frozen mypy src                # Type checking
uv run --frozen bandit -r src           # Security scanning
```

### Markdown Files (.md)

**Configuration**: `.markdownlint.json`

```json
{
  "default": true,
  "MD013": {
    "line_length": 120,
    "heading_line_length": 120,
    "code_block_line_length": 120,
    "tables": false
  },
  "MD007": {
    "indent": 2
  },
  "MD030": {
    "ul_single": 1,
    "ol_single": 1,
    "ul_multi": 1,
    "ol_multi": 1
  },
  "MD033": {
    "allowed_elements": ["br", "sub", "sup", "details", "summary"]
  },
  "MD041": false
}
```

**Commands**:

```bash
# MUST RUN before committing Markdown changes
markdownlint **/*.md                                    # Check all markdown files
markdownlint --config .markdownlint.json **/*.md      # With specific config
markdownlint --fix **/*.md                             # Auto-fix issues
markdownlint **/*.md --ignore-path .markdownlintignore # With ignore file
```

### YAML Files (.yml, .yaml)

**Configuration**: `.yamllint.yml`

```yaml
extends: default

rules:
  line-length:
    max: 120
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
    check-multi-line-strings: false
  comments:
    min-spaces-from-content: 1
  comments-indentation: disable
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no']

ignore: |
  .git/
  .mypy_cache/
  .pytest_cache/
  .venv/
  venv/
  build/
  dist/
  node_modules/
```

**Commands**:

```bash
# MUST RUN before committing YAML changes
yamllint .                           # Check all YAML files
yamllint -c .yamllint.yml **/*.{yml,yaml}  # With specific config
yamllint --format parsable .         # Machine-readable output
```

### JSON Files (.json)

**Validation**: Automatic via pre-commit hooks

```bash
# Validation commands
python -m json.tool file.json       # Validate JSON syntax
jq . file.json                      # Pretty-print and validate
```

## Linting Enforcement Strategy

### Pre-commit Hooks (MANDATORY)

```yaml
# .pre-commit-config.yaml (essential configuration)
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json
      - id: check-toml

  - repo: local
    hooks:
      - id: ruff-format
        name: ruff-format
        entry: uv run --frozen ruff format
        language: system
        types: [python]
        args: [--line-length=120]
      - id: ruff
        name: ruff
        entry: uv run --frozen ruff check
        language: system
        types: [python]
        args: [--fix, --line-length=120]
      - id: mypy
        name: mypy
        entry: uv run --frozen mypy
        language: system
        types: [python]
        args: [--config-file=pyproject.toml]

  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.9.26
    hooks:
      - id: uv-lock
        # Verifies uv.lock is in sync with pyproject.toml.

  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.39.0
    hooks:
      - id: markdownlint
        args: [--config=.markdownlint.json]

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-c=.yamllint.yml]
```

**Setup and Usage**:

```bash
# Install pre-commit hooks (MANDATORY)
uv run --frozen pre-commit install

# Run manually on all files
uv run --frozen pre-commit run --all-files

# Run on staged files only
uv run --frozen pre-commit run

# Update hook versions
uv run --frozen pre-commit autoupdate
```

### Manual Verification Commands

```bash
# Complete linting check (run before major commits)
make lint  # If Makefile exists
# or
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy src
markdownlint **/*.md
yamllint **/*.{yml,yaml}
uv run --frozen bandit -r src
```

### CI/CD Integration

```yaml
# GitHub Actions workflow example
name: Code Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: '0.9.26'
          enable-cache: true
          cache-dependency-glob: 'uv.lock'

      - name: Install dependencies
        run: uv sync --frozen --all-groups

      - name: Run Ruff format check
        run: uv run --frozen ruff format --check .

      - name: Run Ruff lint
        run: uv run --frozen ruff check .

      - name: Run MyPy
        run: uv run --frozen mypy src

      - name: Run Markdownlint
        run: markdownlint **/*.md

      - name: Run yamllint
        run: yamllint **/*.{yml,yaml}

      - name: Run Bandit
        run: uv run --frozen bandit -r src
```

## Common Linting Issues and Solutions

### Python Linting Issues

#### Import Organization (Ruff I001)

```python
# Wrong
import sys
import os
from typing import Dict
import requests

# Correct
import os
import sys

import requests
from typing import Dict
```

#### Line Length (Ruff E501)

```python
# Wrong
really_long_function_name_that_exceeds_line_length(argument1, argument2, argument3, argument4, argument5)

# Correct
really_long_function_name_that_exceeds_line_length(
    argument1, argument2, argument3, argument4, argument5
)
```

#### Type Annotations (MyPy/Ruff ANN)

```python
# Wrong
def process_data(data):
    return data.upper()

# Correct
def process_data(data: str) -> str:
    return data.upper()
```

#### Security Issues (Bandit)

```python
# Wrong
password = "hardcoded_password"
subprocess.run(f"rm -rf {user_input}", shell=True)

# Correct
password = os.getenv("PASSWORD")  # From environment
subprocess.run(["rm", "-rf", validated_path])  # No shell=True
```

### Markdown Linting Issues

#### Line Length (MD013)

```markdown
<!-- Wrong -->
This is a very long line that exceeds the 120 character limit and should be broken into multiple lines for better readability.

<!-- Correct -->
This is a very long line that exceeds the 120 character limit and should be broken into
multiple lines for better readability.
```

#### List Consistency (MD030)

```markdown
<!-- Wrong -->
- Item 1
  - Subitem with inconsistent indentation
- Item 2

<!-- Correct -->
- Item 1
  - Subitem with consistent 2-space indentation
- Item 2
```

### YAML Linting Issues

#### Indentation (yamllint indentation)

```yaml
# Wrong
services:
    app:
        image: python:3.11
        ports:
            - "8000:8000"

# Correct
services:
  app:
    image: python:3.11
    ports:
      - "8000:8000"
```

#### Line Length (yamllint line-length)

```yaml
# Wrong
description: "This is a very long description that exceeds the line length limit and should be broken"

# Correct
description: >
  This is a very long description that exceeds the line length limit
  and should be broken using YAML multiline syntax
```

## Editor Integration

### VS Code Configuration

```json
// .vscode/settings.json
{
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.banditEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "markdownlint.config": {
    "extends": ".markdownlint.json"
  },
  "yaml.format.singleQuote": false,
  "yaml.format.bracketSpacing": true,
  "[yaml]": {
    "editor.insertSpaces": true,
    "editor.tabSize": 2,
    "editor.autoIndent": "advanced"
  }
}
```

### PyCharm Configuration

```xml
<!-- .idea/codeStyles/Python.xml -->
<code_scheme name="PromptCraft">
  <option name="LINE_SEPARATOR" value="&#10;" />
  <option name="RIGHT_MARGIN" value="120" />
  <Python>
    <option name="USE_CONTINUATION_INDENT_FOR_ARGUMENTS" value="true" />
    <option name="FROM_IMPORT_WRAPPING" value="1" />
    <option name="IMPORT_SORTING_TYPE" value="2" />
  </Python>
</code_scheme>
```

## Troubleshooting

### Common Pre-commit Issues

```bash
# Pre-commit hook failures
uv run --frozen pre-commit run --all-files --show-diff-on-failure

# Update outdated hooks
uv run --frozen pre-commit autoupdate

# Skip hooks temporarily (NOT RECOMMENDED)
git commit --no-verify -m "emergency fix"

# Fix specific hook failures
uv run --frozen pre-commit run ruff-format --all-files
uv run --frozen pre-commit run ruff --all-files
```

### Performance Optimization

```bash
# Speed up MyPy
uv run --frozen mypy --install-types --non-interactive
uv run --frozen mypy --cache-fine-grained src

# Parallel linting
uv run --frozen ruff check . --jobs 4
markdownlint **/*.md --parallel

# Cache optimization
export PRE_COMMIT_COLOR=always
export PRE_COMMIT_USE_CACHE=1
```

### Configuration Conflicts

```bash
# Detect configuration inconsistencies
uv run --frozen ruff format --check --diff .
uv run --frozen ruff check --show-source .

# Validate YAML configuration
yamllint -c .yamllint.yml .yamllint.yml

# Test markdownlint config
markdownlint --config .markdownlint.json README.md
```

## Critical Configuration Alignment Rules

1. **NEVER override** Python settings from `pyproject.toml`
2. **Ensure exclude patterns** in all configs match Ruff's `extend-exclude`
3. **Maintain consistency** between `.editorconfig`, `.yamllint.yml`, and `pyproject.toml`
4. **Respect existing** line length (120 chars), indentation (2/4 spaces), and target versions
5. **Test configuration changes** against existing codebase before committing
6. **Document deviations** from standards with clear justification
