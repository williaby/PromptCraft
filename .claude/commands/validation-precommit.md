# Validate Pre-commit Compliance

Perform comprehensive pre-commit validation and compliance checking with automatic corrections for all file types in PromptCraft-Hybrid project: $ARGUMENTS

## Analysis Required

1. **File Type Detection**: Determine applicable pre-commit hooks based on file extension and location
2. **Hook-by-Hook Validation**: Check compliance with each applicable pre-commit hook
3. **Safe Auto-Corrections**: Apply formatting and safe fixes automatically
4. **Security & Type Issue Detection**: Flag critical issues requiring manual review
5. **Poetry & Dependency Validation**: Check Poetry configuration and lock file consistency
6. **Cross-File Impact Analysis**: Identify changes that might affect other files
7. **Test Coverage Validation**: Ensure 80% minimum coverage for Python files
8. **Git Environment Validation**: Verify GPG/SSH keys for signed commits and encryption
9. **Knowledge Base Compliance**: Validate C.R.E.A.T.E. framework and atomic structure
10. **Commit Message Readiness**: Suggest proper conventional commit format
11. **CI/CD Impact Assessment**: Check workflow triggers and deployment readiness
12. **Compliance Scoring**: Provide comprehensive before/after assessment

## Pre-commit Hook Coverage

### Universal Hooks (All Files)

**Auto-Corrections Applied**:

- **trailing-whitespace**: Remove trailing whitespace from all lines
- **end-of-file-fixer**: Ensure files end with newline
- **check-case-conflict**: Flag case conflicts (manual review)
- **check-merge-conflict**: Detect merge conflict markers
- **fix-byte-order-marker**: Remove byte order markers
- **mixed-line-ending**: Standardize line endings to LF

**Manual Review Flagged**:

- **check-added-large-files**: Files over 1000KB (suggest alternatives)
- **detect-private-key**: Private key detection (security critical)

### File-Type Specific Hooks

#### Python Files (.py)

**Auto-Corrections Applied**:

- **black**: Code formatting (88 character line length)
- **ruff --fix**: Auto-fixable linting violations
- **debug-statements**: Remove debug imports and statements

**Manual Review Flagged**:

- **mypy**: Type checking errors (exclude tests/)
- **bandit**: Security vulnerabilities (following pyproject.toml config)
- **ruff --exit-non-zero-on-fix**: Non-auto-fixable linting issues

#### Structured Data Files

**Auto-Corrections Applied**:

- **check-yaml**: Fix YAML syntax (with --allow-multiple-documents)
- **check-json**: Fix JSON syntax and formatting
- **check-toml**: Fix TOML syntax and formatting
- **check-xml**: Fix XML syntax and formatting

**Manual Review Flagged**:

- Complex structural issues requiring content understanding

#### Markdown Files (.md)

**Auto-Corrections Applied**:

- **markdownlint**: Apply --config .markdownlint.json auto-fixes
- Line length, heading spacing, list formatting

**Manual Review Flagged**:

- Content structure violations requiring human judgment

#### YAML Files (.yml, .yaml)

**Auto-Corrections Applied**:

- **yamllint**: Apply -c .yamllint.yml auto-fixes
- Indentation, line length, syntax corrections

**Manual Review Flagged**:

- Complex configuration issues

#### Poetry & Dependencies

**Auto-Corrections Applied**:

- **poetry-check**: Basic pyproject.toml validation

**Manual Review Flagged**:

- **poetry-lock**: Lock file inconsistencies (requires --no-update)
- Dependency version conflicts
- Virtual environment issues

## Commit Readiness Implementation

### 1. Test Coverage Validation

```python
def validate_test_coverage(file_path: str) -> dict:
    """Validate test coverage meets 80% minimum requirement."""
    if not file_path.endswith('.py') or 'tests/' in file_path:
        return {"skipped": "Not applicable for non-Python or test files"}

    # Run coverage for specific file
    coverage_result = run_pytest_coverage(file_path)

    results = {
        "current_coverage": coverage_result.percentage,
        "meets_minimum": coverage_result.percentage >= 80,
        "missing_lines": coverage_result.missing_lines,
        "actions_required": []
    }

    if not results["meets_minimum"]:
        test_file = get_corresponding_test_file(file_path)
        results["actions_required"] = [
            f"Add unit tests for uncovered functions in {test_file}",
            f"Run: poetry run pytest {test_file} --cov={file_path}",
            f"Target coverage: {80 - results['current_coverage']:.1f}% increase needed"
        ]

    return results

def get_corresponding_test_file(file_path: str) -> str:
    """Get the expected test file path for a source file."""
    # src/core/query_counselor.py -> tests/unit/test_query_counselor.py
    rel_path = file_path.replace('src/', '').replace('.py', '')
    return f"tests/unit/test_{os.path.basename(rel_path)}.py"
```

### 2. Git Environment Validation

```python
def validate_git_environment() -> dict:
    """Validate GPG and SSH keys for CLAUDE.md compliance."""
    results = {
        "gpg_key": check_gpg_keys(),
        "ssh_key": check_ssh_keys(),
        "git_signing": check_git_signing_config(),
        "ready_for_commit": True,
        "actions_required": []
    }

    # GPG key validation (for .env encryption)
    if not results["gpg_key"]["available"]:
        results["ready_for_commit"] = False
        results["actions_required"].append(
            "Generate GPG key for .env encryption: gpg --gen-key"
        )

    # SSH key validation (for signed commits)
    if not results["ssh_key"]["in_agent"]:
        results["ready_for_commit"] = False
        results["actions_required"].append(
            "Add SSH key to agent: ssh-add ~/.ssh/id_rsa"
        )

    # Git signing configuration
    if not results["git_signing"]["configured"]:
        results["ready_for_commit"] = False
        results["actions_required"].append(
            "Configure Git signing key: git config user.signingkey <GPG-KEY-ID>"
        )

    return results

def check_gpg_keys() -> dict:
    """Check GPG key availability for encryption."""
    result = subprocess.run(['gpg', '--list-secret-keys'],
                          capture_output=True, text=True)
    return {
        "available": result.returncode == 0 and 'sec' in result.stdout,
        "count": result.stdout.count('sec ') if result.returncode == 0 else 0
    }

def check_ssh_keys() -> dict:
    """Check SSH key availability."""
    result = subprocess.run(['ssh-add', '-l'],
                          capture_output=True, text=True)
    return {
        "in_agent": result.returncode == 0 and 'SHA256:' in result.stdout,
        "count": len(result.stdout.splitlines()) if result.returncode == 0 else 0
    }
```

### 3. Knowledge Base Validation

```python
def validate_knowledge_base_compliance(file_path: str, content: str) -> dict:
    """Validate C.R.E.A.T.E. framework and atomic structure."""
    if not file_path.startswith('knowledge/'):
        return {"skipped": "Not a knowledge base file"}

    results = {
        "create_framework": validate_create_framework(content),
        "h3_atomicity": validate_h3_atomicity(content),
        "agent_id_consistency": validate_agent_id_consistency(file_path, content),
        "yaml_frontmatter": validate_yaml_frontmatter(content),
        "actions_required": []
    }

    # Check C.R.E.A.T.E. framework completeness
    missing_sections = results["create_framework"]["missing"]
    if missing_sections:
        results["actions_required"].append(
            f"Add missing C.R.E.A.T.E. sections: {', '.join(missing_sections)}"
        )

    # Check H3 atomicity
    non_atomic = results["h3_atomicity"]["non_atomic_sections"]
    if non_atomic:
        for section in non_atomic:
            results["actions_required"].append(
                f"Make H3 section '{section}' self-contained with complete context"
            )

    return results

def validate_create_framework(content: str) -> dict:
    """Validate C.R.E.A.T.E. framework presence."""
    framework_elements = {
        "Context": ["context", "background", "role", "persona"],
        "Request": ["request", "task", "objective", "goal"],
        "Examples": ["example", "demonstration", "sample"],
        "Augmentations": ["framework", "methodology", "reasoning"],
        "Tone": ["tone", "style", "voice", "format"],
        "Evaluation": ["evaluation", "quality", "validation", "check"]
    }

    found = {}
    missing = []

    content_lower = content.lower()
    for element, keywords in framework_elements.items():
        found[element] = any(keyword in content_lower for keyword in keywords)
        if not found[element]:
            missing.append(element)

    return {"found": found, "missing": missing, "completeness": len(found) - len(missing)}
```

### 4. Commit Message Generation

```python
def generate_commit_message(file_path: str, changes_summary: dict) -> str:
    """Generate conventional commit message based on file changes."""

    # Determine commit type and scope
    commit_type = determine_commit_type(file_path, changes_summary)
    scope = determine_scope(file_path)

    # Generate description
    description = generate_description(changes_summary)

    # Build conventional commit message
    message = f"{commit_type}"
    if scope:
        message += f"({scope})"
    message += f": {description}\n\n"

    # Add bullet points for major changes
    if changes_summary.get("major_changes"):
        for change in changes_summary["major_changes"]:
            message += f"- {change}\n"
        message += "\n"

    # Add Claude attribution per CLAUDE.md
    message += "🤖 Generated with [Claude Code](https://claude.ai/code)\n\n"
    message += "Co-Authored-By: Claude <noreply@anthropic.com>"

    return message

def determine_commit_type(file_path: str, changes: dict) -> str:
    """Determine conventional commit type."""
    if changes.get("new_file"):
        return "feat"
    elif changes.get("security_fixes"):
        return "fix"
    elif changes.get("only_formatting"):
        return "style"
    elif changes.get("test_changes"):
        return "test"
    elif file_path.endswith('.md'):
        return "docs"
    elif changes.get("breaking_changes"):
        return "feat!"
    else:
        return "feat"

def determine_scope(file_path: str) -> str:
    """Determine commit scope from file path."""
    if file_path.startswith('src/core/'):
        return "core"
    elif file_path.startswith('src/agents/'):
        return "agents"
    elif file_path.startswith('knowledge/'):
        return "knowledge"
    elif file_path.startswith('docs/'):
        return "docs"
    elif file_path.startswith('tests/'):
        return "test"
    elif file_path.startswith('.github/'):
        return "ci"
    else:
        return None
```

### 5. CI/CD Impact Analysis

```python
def analyze_cicd_impact(file_path: str) -> dict:
    """Analyze CI/CD pipeline impact of file changes."""
    workflows_triggered = []
    estimated_time = 0

    # Check workflow triggers
    if file_path.endswith(('.py', '.toml', 'Dockerfile')):
        workflows_triggered.extend(['ci.yml', 'codeql.yml'])
        estimated_time += 8  # Base CI time

    if file_path.startswith('deployment/'):
        workflows_triggered.append('azure-deploy.yml')
        estimated_time += 15  # Deployment time

    if 'Dockerfile' in file_path or file_path.startswith('src/'):
        docker_build_required = True
        estimated_time += 5  # Docker build time
    else:
        docker_build_required = False

    return {
        "workflows_triggered": workflows_triggered,
        "docker_build_required": docker_build_required,
        "estimated_ci_time": f"{estimated_time}-{estimated_time + 4} minutes",
        "deployment_impact": "deployment/" in file_path,
        "breaking_change_risk": check_breaking_change_risk(file_path)
    }

def check_breaking_change_risk(file_path: str) -> str:
    """Assess risk of breaking changes."""
    if file_path.startswith('src/core/'):
        return "HIGH - Core functionality changes"
    elif file_path.endswith('pyproject.toml'):
        return "MEDIUM - Dependency changes"
    elif file_path.startswith('src/'):
        return "MEDIUM - Source code changes"
    else:
        return "LOW - Documentation or configuration"
```

## Auto-Correction Implementation

### 1. Hook Detection and Filtering

```python
def get_applicable_hooks(file_path: str) -> list:
    """Determine which pre-commit hooks apply to the given file."""
    hooks = []

    # Universal hooks
    hooks.extend([
        "trailing-whitespace", "end-of-file-fixer", "check-case-conflict",
        "check-merge-conflict", "fix-byte-order-marker", "mixed-line-ending",
        "check-added-large-files", "detect-private-key"
    ])

    # File-type specific
    if file_path.endswith('.py'):
        hooks.extend(["black", "ruff", "mypy", "bandit", "debug-statements"])
    elif file_path.endswith(('.yml', '.yaml')):
        hooks.extend(["check-yaml", "yamllint"])
    elif file_path.endswith('.json'):
        hooks.extend(["check-json"])
    elif file_path.endswith('.toml'):
        hooks.extend(["check-toml"])
    elif file_path.endswith('.xml'):
        hooks.extend(["check-xml"])
    elif file_path.endswith('.md'):
        hooks.extend(["markdownlint"])

    # Poetry specific (for pyproject.toml)
    if file_path.endswith('pyproject.toml'):
        hooks.extend(["poetry-check", "poetry-lock"])

    return hooks
```

### 2. Safe Auto-Correction Categories

```python
SAFE_AUTO_FIXES = {
    # Formatting (no logic impact)
    "formatting": ["black", "trailing-whitespace", "end-of-file-fixer",
                   "fix-byte-order-marker", "mixed-line-ending"],

    # Syntax fixes (structure only)
    "syntax": ["check-yaml", "check-json", "check-toml", "check-xml"],

    # Linting auto-fixes (safe violations only)
    "linting": ["ruff --fix", "markdownlint auto-fixes", "yamllint auto-fixes"],

    # Cleanup (remove unwanted elements)
    "cleanup": ["debug-statements"]
}

MANUAL_REVIEW_REQUIRED = {
    # Type and logic issues
    "type_checking": ["mypy"],

    # Security issues
    "security": ["bandit", "detect-private-key"],

    # Complex linting
    "complex_linting": ["ruff non-auto-fixable"],

    # Dependency management
    "dependencies": ["poetry-lock", "check-added-large-files"],

    # Structural issues
    "structure": ["check-case-conflict", "check-merge-conflict"]
}
```

### 3. Hook-Specific Validation Logic

```python
def validate_python_file(content: str, file_path: str) -> dict:
    """Comprehensive Python file validation."""
    results = {
        "auto_fixes": {},
        "manual_issues": {},
        "corrected_content": content
    }

    # Black formatting
    formatted_content = apply_black_formatting(content)
    if formatted_content != content:
        results["auto_fixes"]["black"] = "Applied code formatting"
        results["corrected_content"] = formatted_content

    # Ruff auto-fixes
    ruff_fixes, remaining_issues = apply_ruff_fixes(formatted_content)
    if ruff_fixes:
        results["auto_fixes"]["ruff"] = f"Fixed {len(ruff_fixes)} auto-fixable issues"
        results["corrected_content"] = apply_fixes(results["corrected_content"], ruff_fixes)

    if remaining_issues:
        results["manual_issues"]["ruff"] = remaining_issues

    # MyPy type checking (manual review)
    if not file_path.startswith('tests/'):
        type_errors = run_mypy_check(file_path)
        if type_errors:
            results["manual_issues"]["mypy"] = type_errors

    # Bandit security scan (manual review)
    security_issues = run_bandit_scan(results["corrected_content"])
    if security_issues:
        results["manual_issues"]["bandit"] = security_issues

    return results

def validate_yaml_file(content: str, file_path: str) -> dict:
    """YAML file validation with yamllint."""
    results = {
        "auto_fixes": {},
        "manual_issues": {},
        "corrected_content": content
    }

    # YAML syntax validation
    try:
        yaml.safe_load_all(content)  # Support multiple documents
    except yaml.YAMLError as e:
        results["manual_issues"]["yaml_syntax"] = str(e)
        return results

    # yamllint auto-fixes
    yamllint_fixes = apply_yamllint_fixes(content)
    if yamllint_fixes:
        results["auto_fixes"]["yamllint"] = "Applied YAML formatting fixes"
        results["corrected_content"] = yamllint_fixes

    return results
```

### 4. Universal File Fixes

```python
def apply_universal_fixes(content: str) -> tuple[str, list]:
    """Apply universal pre-commit fixes to any file."""
    fixes_applied = []

    # Remove trailing whitespace
    lines = content.splitlines()
    original_line_count = len(lines)
    lines = [line.rstrip() for line in lines]
    if any(line != orig for line, orig in zip(lines, content.splitlines())):
        fixes_applied.append("Removed trailing whitespace")

    # Ensure file ends with newline
    corrected_content = '\n'.join(lines)
    if content and not content.endswith('\n'):
        corrected_content += '\n'
        fixes_applied.append("Added final newline")

    return corrected_content, fixes_applied
```

## Security and Critical Issue Detection

### Security Hook Analysis

```python
def analyze_security_issues(file_path: str, content: str) -> dict:
    """Comprehensive security analysis using bandit and private key detection."""
    issues = {
        "critical": [],  # Must fix before commit
        "high": [],      # Should fix before commit
        "medium": [],    # Consider fixing
        "info": []       # Informational
    }

    # Private key detection (critical)
    if detect_private_key_patterns(content):
        issues["critical"].append({
            "hook": "detect-private-key",
            "issue": "Private key or sensitive credential detected",
            "action": "Remove sensitive data immediately",
            "guidance": "Use encrypted .env files following CLAUDE.md guidelines"
        })

    # Bandit security scan (severity-based)
    bandit_results = run_bandit_with_config(content, "pyproject.toml")
    for result in bandit_results:
        severity = result.get("severity", "medium").lower()
        if severity in issues:
            issues[severity].append({
                "hook": "bandit",
                "issue": result["issue"],
                "line": result.get("line_number"),
                "action": result["recommendation"],
                "test_id": result.get("test_id")
            })

    return issues
```

### Type Checking Analysis

```python
def analyze_type_issues(file_path: str) -> dict:
    """MyPy type checking with actionable suggestions."""
    if file_path.startswith('tests/'):
        return {"skipped": "Tests directory excluded from type checking"}

    type_errors = run_mypy_with_config(file_path, "pyproject.toml")
    categorized_errors = {
        "missing_imports": [],
        "type_annotations": [],
        "incompatible_types": [],
        "other": []
    }

    for error in type_errors:
        if "import" in error.message.lower():
            categorized_errors["missing_imports"].append(error)
        elif "annotation" in error.message.lower():
            categorized_errors["type_annotations"].append(error)
        elif "incompatible" in error.message.lower():
            categorized_errors["incompatible_types"].append(error)
        else:
            categorized_errors["other"].append(error)

    return categorized_errors
```

## Required Output Format

### 1. Auto-Corrected File Content

```markdown
[Only provide corrected content if auto-fixes were applied]

---
# AUTO-CORRECTED CONTENT
# The following content has been automatically corrected for pre-commit compliance:
---

[Corrected file content with all safe auto-fixes applied]
```

### 2. Pre-commit Compliance Report

```markdown
# Pre-commit Validation Report

## File: [file_path]

### ✅ AUTO-CORRECTIONS APPLIED

#### Universal Fixes
- ✓ Removed trailing whitespace from 3 lines
- ✓ Added final newline
- ✓ Standardized line endings to LF

#### File-Type Specific Fixes
- ✓ **black**: Applied Python code formatting (88 char line length)
- ✓ **ruff --fix**: Resolved 5 auto-fixable linting issues
  - F401: Removed unused imports
  - E501: Fixed line length violations
  - W291: Removed trailing whitespace
- ✓ **yamllint**: Fixed indentation and spacing
- ✓ **markdownlint**: Corrected heading structure and list formatting

### 🔍 MANUAL REVIEW REQUIRED

#### 🛡️ Security Issues (CRITICAL)
- **bandit B105**: Line 23 - Hardcoded password string
  - **Severity**: High
  - **Action**: Move to encrypted .env file following CLAUDE.md encryption patterns
  - **File**: `src/config/settings.py:23`

#### 🎯 Type Checking Issues
- **mypy**: 3 type errors found
  - **Line 45**: `Argument 1 to "process_data" has incompatible type "str"; expected "Dict[str, Any]"`
    - **Fix**: Add type annotation or cast: `process_data(json.loads(data))`
  - **Line 67**: `Function is missing a return type annotation`
    - **Fix**: Add `-> Optional[str]:` to function signature
  - **Line 89**: `Cannot determine type of 'config_data'`
    - **Fix**: Add explicit type hint: `config_data: Dict[str, Any] = {}`

#### 🧹 Complex Linting Issues
- **ruff E711**: Line 156 - `comparison to None should be 'if cond is None:'`
- **ruff F841**: Line 203 - Local variable 'temp_file' is assigned to but never used
- **ruff C901**: Line 234 - `'validate_config'` is too complex (12 > 10)
  - **Suggestion**: Break function into smaller helper functions

#### 📦 Dependency Issues
- **poetry-lock**: Poetry lock file is out of sync with pyproject.toml
  - **Action**: Run `poetry lock --no-update` to sync lock file
  - **Impact**: CI/CD builds may fail with current lock file
- **check-added-large-files**: File size 1.2MB exceeds 1000KB limit
  - **Suggestion**: Move large assets to separate storage or compress

### 📊 PRE-COMMIT HOOK COMPLIANCE

#### Hooks Passed (8/12)
✅ trailing-whitespace
✅ end-of-file-fixer
✅ black
✅ ruff (auto-fixable rules)
✅ check-yaml
✅ markdownlint
✅ yamllint
✅ debug-statements

#### Hooks Failed (4/12)
❌ bandit (1 security issue)
❌ mypy (3 type errors)
❌ ruff (3 complex issues)
❌ poetry-lock (out of sync)

### 🧪 COMMIT READINESS VALIDATION

#### Test Coverage Assessment
- **Current Coverage**: 78% (below 80% minimum)
- **Missing Coverage**: `src/core/query_counselor.py` (45% coverage)
- **Action Required**: Add unit tests for uncovered functions
- **Command**: `poetry run pytest tests/unit/test_query_counselor.py --cov=src/core/query_counselor.py`

#### Git Environment Status
✅ **GPG Key**: Found and configured for .env encryption
❌ **SSH Key**: Not found in ssh-agent
✅ **Git Signing**: user.signingkey configured
- **Action Required**: Run `ssh-add ~/.ssh/id_rsa` before committing

#### Knowledge Base Compliance (knowledge/ files only)
✅ **YAML Front Matter**: Complete and valid
❌ **H3 Atomicity**: 2 sections need better self-containment
✅ **Agent ID Consistency**: Matches directory structure
❌ **C.R.E.A.T.E. Framework**: Missing Examples section
- **Action Required**: Add self-contained context to H3 sections

#### Commit Message Suggestion
```

feat(core): implement query processing validation

- Add pre-commit validation for query_counselor.py
- Fix type annotations and security issues
- Improve test coverage to 85%

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>

```

#### CI/CD Impact Analysis
- **Workflows Triggered**: `ci.yml` (tests), `codeql.yml` (security)
- **Docker Build**: Required (Dockerfile changes detected)
- **Azure Deployment**: Not triggered (no deployment/ changes)
- **Estimated CI Time**: 8-12 minutes

### 📋 TODO CHECKLIST

#### Critical (Must Fix Before Commit)
- [ ] **SECURITY**: Remove hardcoded password from `settings.py:23`
- [ ] **SECURITY**: Implement .env encryption following CLAUDE.md patterns
- [ ] **GIT-ENV**: Add SSH key to ssh-agent (`ssh-add ~/.ssh/id_rsa`)
- [ ] **COVERAGE**: Add unit tests to reach 80% minimum coverage
- [ ] **TYPE**: Fix incompatible type argument at `process_data.py:45`
- [ ] **TYPE**: Add return type annotation to `helper_function:67`

#### High Priority (Should Fix Before Commit)
- [ ] **DEPS**: Run `poetry lock --no-update` to sync dependencies
- [ ] **KNOWLEDGE**: Add self-contained context to H3 sections (atomicity)
- [ ] **KNOWLEDGE**: Complete C.R.E.A.T.E. framework Examples section
- [ ] **TYPE**: Add type hint for `config_data` variable at line 89
- [ ] **LINT**: Fix None comparison style at line 156
- [ ] **LINT**: Remove unused variable `temp_file` at line 203

#### Medium Priority (Consider for Future PR)
- [ ] **COMPLEXITY**: Refactor `validate_config` function (lines 234-280)
- [ ] **PERFORMANCE**: Consider file size optimization for large asset
- [ ] **CI-OPT**: Optimize Docker build for faster CI pipeline
- [ ] **DOCS**: Add type hints to improve code maintainability

### 🎯 COMPLIANCE SUMMARY
- **Before**: 67% compliance (8/12 hooks passing)
- **After Auto-fixes**: 75% compliance (9/12 hooks passing)
- **Target**: 100% compliance (all hooks passing)
- **Estimated Fix Time**: 15-20 minutes for critical issues

### 📚 REFERENCE DOCUMENTATION
- **Security Patterns**: See CLAUDE.md encryption guidelines
- **Type Checking**: Follow mypy configuration in pyproject.toml
- **Code Style**: All formatting follows pyproject.toml Black/Ruff settings
- **Poetry Management**: See CLAUDE.md dependency management section
```

## Validation Scope and Limitations

### Auto-Correction Scope

- **Safe formatting changes**: Always applied automatically
- **Syntax fixes**: Applied when no logic impact
- **Import cleanup**: Remove unused imports only
- **Whitespace/newlines**: Universal fixes applied

### Manual Review Required

- **Security vulnerabilities**: Never auto-fix (require human review)
- **Type errors**: Complex logic requires developer understanding
- **Dependency conflicts**: May require version strategy decisions
- **Large file issues**: May require architectural decisions
- **Complex refactoring**: Function complexity, naming, structure

### Hook Configuration Respect

- All validations follow exact configurations from:
  - `pyproject.toml` (Black, Ruff, MyPy, Bandit settings)
  - `.markdownlint.json` (Markdown rules)
  - `.yamllint.yml` (YAML formatting rules)
- No configuration overrides applied

## Important Notes

- **Configuration Consistency**: All checks use exact same settings as actual pre-commit hooks
- **Security First**: Critical security issues flagged prominently with immediate action required
- **Incremental Progress**: Shows compliance improvement from auto-fixes
- **Actionable TODOs**: Every issue includes specific fix instructions
- **Cross-Hook Awareness**: Considers interactions between different hook results
- **Performance Considerations**: Validates large file handling and dependency impacts
- **Repository Context**: Suggestions consider project structure and conventions from CLAUDE.md
- **CI/CD Impact**: Flags issues that would cause build failures
