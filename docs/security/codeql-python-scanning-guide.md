---
title: "CodeQL Python Security Scanning Guide"
version: "1.0"
status: "published"
component: "Security"
tags: ["security", "codeql", "python", "scanning", "ci-cd"]
purpose: "Complete guide for CodeQL Python security scanning configuration and procedures."
---

# CodeQL Python Security Scanning Guide

**Related Issue**: [#119 - CodeQL Security Scanning Configuration Fix](https://github.com/williaby/PromptCraft/issues/119)
**Last Updated**: January 10, 2025
**Status**: Active Configuration

## Overview

CodeQL is GitHub's semantic code analysis engine that finds security vulnerabilities in Python code. This guide covers the
complete setup, configuration, and operational procedures for Python security scanning in the PromptCraft project.

## Configuration

### Workflow Configuration

**File**: `.github/workflows/codeql.yml`

```yaml
name: "CodeQL Analysis"

on:
  push:
    branches: [ "main" ]
    paths:
      - '**/*.py'
      - '.github/workflows/codeql.yml'
  pull_request:
    branches: [ "main" ]
    paths:
      - '**/*.py'
      - '.github/workflows/codeql.yml'
  schedule:
    - cron: '39 16 * * 1' # Runs every Monday at 16:39 UTC

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read

    strategy:
      fail-fast: false
      matrix:
        # Python configuration for PromptCraft project
        language: [ 'python' ]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install --only main

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{matrix.language}}"
```

### Key Configuration Elements

#### 1. Language Configuration

```yaml
language: [ 'python' ]  # Scans Python files only
```

#### 2. Python Environment Setup

```yaml
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'  # Match project Python version

- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install poetry
    poetry install --only main  # Install main dependencies for analysis
```

#### 3. Security Query Configuration

```yaml
queries: security-extended  # Built-in Python security patterns
```

#### 4. Path-Based Triggers

```yaml
paths:
  - '**/*.py'  # Trigger on Python file changes
  - '.github/workflows/codeql.yml'  # Trigger on workflow changes
```

## Security Patterns Detected

### Built-in Security-Extended Queries

CodeQL's `security-extended` query suite detects the following Python security vulnerabilities:

#### 1. SQL Injection

```python
# VULNERABLE - CodeQL will detect this
def get_user(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)  # SQL injection vulnerability

# SECURE - CodeQL will not flag this
def get_user_safe(user_input):
    query = "SELECT * FROM users WHERE name = %s"
    cursor.execute(query, (user_input,))  # Parameterized query
```

#### 2. Command Injection

```python
# VULNERABLE - CodeQL will detect this
def run_command(user_input):
    command = f"ls {user_input}"
    subprocess.run(command, shell=True)  # Command injection vulnerability

# SECURE - CodeQL will not flag this
def run_command_safe(user_input):
    subprocess.run(["ls", user_input])  # Safe argument passing
```

#### 3. Path Traversal

```python
# VULNERABLE - CodeQL will detect this
def read_file(filename):
    path = f"/uploads/{filename}"
    with open(path, 'r') as f:  # Path traversal vulnerability
        return f.read()

# SECURE - CodeQL will not flag this
def read_file_safe(filename):
    safe_path = os.path.join("/uploads", os.path.basename(filename))
    with open(safe_path, 'r') as f:  # Path validation
        return f.read()
```

#### 4. Hardcoded Secrets

```python
# VULNERABLE - CodeQL will detect these
API_KEY = "sk-1234567890abcdef"  # Hardcoded API key
PASSWORD = "admin123"  # Hardcoded password
TOKEN = "ghp_abcdef123456"  # Hardcoded GitHub token

# SECURE - CodeQL will not flag these
API_KEY = os.getenv("API_KEY")  # Environment variable
PASSWORD = config.get("password")  # Configuration system
```

#### 5. Insecure Deserialization

```python
# VULNERABLE - CodeQL will detect this
def load_data(data):
    return pickle.loads(data)  # Insecure deserialization

# SECURE - CodeQL will not flag this
def load_data_safe(data):
    return json.loads(data)  # Safe serialization format
```

#### 6. Weak Cryptography

```python
# VULNERABLE - CodeQL will detect this
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # Weak hash

# SECURE - CodeQL will not flag this
def hash_password_safe(password):
    return hashlib.sha256(password.encode()).hexdigest()  # Strong hash
```

#### 7. Code Injection

```python
# VULNERABLE - CodeQL will detect this
def execute_code(user_code):
    return eval(user_code)  # Code injection vulnerability

# SECURE - CodeQL will not flag this
def execute_code_safe(user_code):
    allowed_ops = {"add": lambda x, y: x + y}
    return allowed_ops.get(user_code, lambda: "Invalid")()
```

## Operational Procedures

### 1. Monitoring Security Alerts

#### Accessing CodeQL Results

```bash
# View security alerts via GitHub CLI
gh api repos/{owner}/{repo}/code-scanning/alerts

# View alerts in GitHub web interface
# Navigate to: Security > Code scanning alerts
```

#### Alert Severity Levels

- **Critical**: Immediate security risk requiring urgent attention
- **High**: Significant security vulnerability
- **Medium**: Moderate security concern
- **Low**: Minor security issue or potential improvement

### 2. Alert Triage Process

#### Step 1: Alert Review

1. **Assess Severity**: Review the vulnerability type and impact
2. **Verify Finding**: Confirm the vulnerability is real (not false positive)
3. **Check Exploitability**: Determine if the vulnerability is exploitable
4. **Assess Business Impact**: Evaluate potential impact on PromptCraft

#### Step 2: Response Actions

```python
# Example alert response workflow
class SecurityAlertResponse:
    def __init__(self, alert_id, severity, vulnerability_type):
        self.alert_id = alert_id
        self.severity = severity
        self.vulnerability_type = vulnerability_type

    def get_response_time(self):
        """Get required response time based on severity."""
        response_times = {
            "critical": "4 hours",
            "high": "24 hours",
            "medium": "7 days",
            "low": "30 days"
        }
        return response_times.get(self.severity, "30 days")

    def get_required_actions(self):
        """Get required actions based on vulnerability type."""
        actions = {
            "sql-injection": ["Fix parameterized queries", "Test with SQL injection payloads"],
            "command-injection": ["Sanitize inputs", "Use safe subprocess calls"],
            "hardcoded-secrets": ["Move to environment variables", "Rotate compromised secrets"],
            "path-traversal": ["Validate file paths", "Use safe path joining"],
            "insecure-deserialization": ["Replace with safe formats", "Validate input sources"],
            "weak-cryptography": ["Update to strong algorithms", "Review existing hashes"]
        }
        return actions.get(self.vulnerability_type, ["Review and fix"])
```

### 3. False Positive Management

#### Common False Positives

1. **Test Files**: Security test files with intentional vulnerabilities
2. **Configuration Examples**: Example code in documentation
3. **Development Tools**: Scripts for development/testing only

#### Suppression Methods

##### Method 1: Code Comments

```python
# Suppress false positive with nosec comment
password = "test123"  # nosec - test password for unit tests only
```

##### Method 2: Configuration File

```yaml
# .codeql/config.yml
queries:
  - uses: security-extended

query-filters:
  - exclude:
      id: py/hardcoded-credentials
      where:
        - file: "**/tests/**"
        - file: "**/examples/**"
```

##### Method 3: GitHub Alert Dismissal

```bash
# Dismiss false positive via GitHub CLI
gh api repos/{owner}/{repo}/code-scanning/alerts/{alert_id} \
  --method PATCH \
  --field state=dismissed \
  --field dismissed_reason=false_positive
```

### 4. Custom Query Development

#### Creating Custom Queries (Advanced)

```ql
/**
 * @name PromptCraft specific security pattern
 * @description Detect insecure prompt processing
 * @kind problem
 * @problem.severity warning
 * @security-severity 6.0
 * @id py/promptcraft-insecure-prompt
 */

import python

from Call call
where call.getFunc().getName() = "eval" and
      call.getArg(0).toString().matches("%prompt%")
select call, "Potential code injection in prompt processing"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Scan Failures

**Issue**: CodeQL analysis fails to complete

```text
Error: CodeQL database creation failed
```

**Solutions**:

```yaml
# Add debugging to workflow
- name: Debug Python Environment
  run: |
    python --version
    pip --version
    poetry --version
    poetry check

# Increase timeout
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: python
    queries: security-extended
  timeout-minutes: 30  # Increase timeout
```

#### 2. Dependency Resolution Issues

**Issue**: Poetry installation fails during analysis

```text
Error: Could not install dependencies
```

**Solutions**:

```yaml
# Use specific Poetry version
- name: Install Poetry
  run: |
    pip install poetry==1.7.1
    poetry config virtualenvs.create false

# Cache dependencies
- name: Cache Poetry dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pypoetry
    key: poetry-${{ hashFiles('**/poetry.lock') }}
```

#### 3. Database Rebuild Issues

**Issue**: CodeQL database takes too long to rebuild

```text
Warning: CodeQL database creation exceeded time limit
```

**Solutions**:

```yaml
# Optimize for faster builds
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: python
    queries: security-extended
    ram: 4096  # Increase RAM allocation
    threads: 2  # Use multiple threads
```

#### 4. Path Trigger Issues

**Issue**: Scans not triggering on Python file changes

**Solutions**:

```yaml
# Debug path matching
on:
  push:
    paths:
      - '**/*.py'      # All Python files
      - 'src/**'       # Source directory
      - 'tests/**'     # Test directory
      - '!docs/**'     # Exclude docs
```

### Performance Optimization

#### 1. Scan Duration Optimization

```yaml
# Optimize scan performance
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: python
    queries: security-extended
    config: |
      paths-ignore:
        - docs/**
        - examples/**
        - .venv/**
        - __pycache__/**
```

#### 2. Resource Usage

- **Average scan time**: 5-10 minutes for PromptCraft codebase
- **RAM usage**: 2-4 GB during analysis
- **Storage**: ~500 MB for CodeQL database

#### 3. Scheduling Optimization

```yaml
# Optimize scheduling for resource usage
schedule:
  - cron: '0 2 * * 1'  # Run at 2 AM Monday (low traffic)
```

## Integration with Security Workflow

### 1. Security Gates (Issue #120)

Once Issue #120 is implemented, CodeQL will be a blocking requirement:

```yaml
# Branch protection rule (future)
required_status_checks:
  strict: true
  contexts:
    - "CodeQL Analysis"
```

### 2. Security Dashboard Integration

```python
# Integration with security monitoring
class CodeQLMonitoring:
    def __init__(self, github_token):
        self.github = Github(github_token)

    def get_security_alerts(self, repo_name):
        """Get current CodeQL security alerts."""
        repo = self.github.get_repo(repo_name)
        alerts = repo.get_code_scanning_alerts()

        return [{
            "id": alert.id,
            "severity": alert.severity,
            "state": alert.state,
            "created_at": alert.created_at,
            "rule": alert.rule.name
        } for alert in alerts]

    def get_security_metrics(self, repo_name):
        """Get security scanning metrics."""
        alerts = self.get_security_alerts(repo_name)

        return {
            "total_alerts": len(alerts),
            "open_alerts": len([a for a in alerts if a["state"] == "open"]),
            "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
            "scan_coverage": "100%"  # Python files covered
        }
```

### 3. Compliance Reporting

```python
# Generate compliance reports
def generate_security_compliance_report(repo_name, period_days=30):
    """Generate security compliance report for audit purposes."""

    report = {
        "report_period": f"Last {period_days} days",
        "scanning_enabled": True,
        "scan_frequency": "On every push + weekly scheduled",
        "languages_covered": ["Python"],
        "query_suites": ["security-extended"],
        "alerts_addressed": "Within SLA timeframes",
        "false_positive_rate": "<5%",
        "compliance_status": "COMPLIANT"
    }

    return report
```

## Maintenance and Updates

### Regular Maintenance Tasks

#### Monthly Tasks

- [ ] Review and address open security alerts
- [ ] Update CodeQL queries to latest version
- [ ] Verify scan performance and duration
- [ ] Review false positive suppressions

#### Quarterly Tasks

- [ ] Audit CodeQL configuration for optimization
- [ ] Review and update custom queries
- [ ] Validate integration with security workflow
- [ ] Update documentation and procedures

#### Annual Tasks

- [ ] Complete security review of CodeQL setup
- [ ] Evaluate new CodeQL features and queries
- [ ] Update team training on security scanning
- [ ] Review compliance requirements

### Version Updates

#### CodeQL Action Updates

```yaml
# Keep CodeQL actions updated
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3  # Update to latest version

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3  # Update to latest version
```

#### Python Version Updates

```yaml
# Update Python version as needed
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'  # Update when project upgrades Python
```

## Emergency Procedures

### Critical Vulnerability Response

#### Immediate Actions (0-4 hours)

1. **Assess Impact**: Determine if vulnerability is exploitable
2. **Temporary Mitigation**: Implement quick fixes if possible
3. **Alert Team**: Notify security team and stakeholders
4. **Block Deployment**: Prevent vulnerable code from reaching production

#### Short-term Actions (4-24 hours)

1. **Develop Fix**: Create proper fix for vulnerability
2. **Test Fix**: Validate fix doesn't break functionality
3. **Emergency Deployment**: Deploy fix to production if critical
4. **Monitor**: Watch for exploitation attempts

#### Medium-term Actions (1-7 days)

1. **Root Cause Analysis**: Understand how vulnerability was introduced
2. **Process Improvement**: Update development practices
3. **Additional Testing**: Comprehensive security testing
4. **Documentation**: Update procedures and lessons learned

## Related Documentation

- [Security Best Practices Guide](security-best-practices.md)
- [CodeQL Historical Gap Analysis](codeql-historical-gap-analysis.md)
- [Issue #119: CodeQL Configuration Fix](https://github.com/williaby/PromptCraft/issues/119)
- [Issue #120: Security Gates Enforcement](https://github.com/williaby/PromptCraft/issues/120)
- [Phase 1 Security Infrastructure Issues](../planning/phase-1-security-ai.md)

---

**Document Status**: Active
**Review Schedule**: Quarterly
**Last Security Review**: January 10, 2025
**Next Review**: April 10, 2025
