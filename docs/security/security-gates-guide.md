# Security Gates Guide for Developers

## Overview

All pull requests to the main branch now require passing security scans before merging. This guide helps you
understand and work with the security gates effectively.

## What Are Security Gates?

Security gates are automated checks that run on every pull request to ensure code meets security standards.
These checks are now **blocking**, meaning your PR cannot be merged until all security scans pass.

## Required Security Checks

The following security checks must pass before your PR can be merged:

### 1. CodeQL Analysis

- **What it does**: Scans for security vulnerabilities in Python code
- **Common issues**: SQL injection, command injection, XSS vulnerabilities
- **Run time**: 2-5 minutes

### 2. Dependency Review

- **What it does**: Checks for known vulnerabilities in dependencies
- **Common issues**: Outdated packages with CVEs
- **Run time**: 1-2 minutes

### 3. PR Validation

- **What it does**: Validates PR requirements and code standards
- **Common issues**: Missing tests, incorrect formatting
- **Run time**: 1-3 minutes

## Understanding Security Gate Notifications

### Email Notifications

When a security scan fails, you'll receive:

1. **GitHub's standard workflow failure email** - Shows which workflow failed
2. **PR comment** - Detailed information about the failure and next steps
3. **PR label** - `security-gate-blocked` label added automatically

### PR Interface

- Red X marks next to failing checks
- "Merge" button disabled until all checks pass
- Detailed logs available by clicking on the failed check

## Common Issues and Solutions

### CodeQL Failures

#### SQL Injection Warnings

```python
# ❌ Bad - Direct string interpolation
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# ✅ Good - Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

# ✅ Good - Using SQLAlchemy ORM
user = session.query(User).filter(User.id == user_id).first()
```

#### Command Injection

```python
# ❌ Bad - Direct command execution
os.system(f"git clone {repo_url}")

# ✅ Good - Using subprocess with list
subprocess.run(["git", "clone", repo_url], check=True)
```

#### Path Traversal

```python
# ❌ Bad - Unvalidated file path
file_path = request.args.get('file')
with open(f"/data/{file_path}", 'r') as f:
    content = f.read()

# ✅ Good - Validate and sanitize
import os
file_name = os.path.basename(request.args.get('file'))
safe_path = os.path.join("/data", file_name)
if os.path.commonpath([safe_path, "/data"]) == "/data":
    with open(safe_path, 'r') as f:
        content = f.read()
```

### Dependency Vulnerabilities

#### Check for Updates

```bash
# Check which packages have updates
poetry show --outdated

# Update a specific package
poetry add package-name@latest

# Update all dependencies
poetry update
```

#### Lock File Sync

```bash
# Regenerate lock file
poetry lock --no-update

# Sync requirements files
./scripts/generate_requirements.sh
```

### PR Validation Failures

#### Missing Tests

- Ensure test coverage remains above 80%
- Add tests for new functionality
- Run tests locally: `poetry run pytest`

#### Code Formatting

```bash
# Format Python code
poetry run black .
poetry run ruff check --fix .

# Check formatting
poetry run black --check .
poetry run ruff check .
```

## Handling False Positives

If you believe a security finding is a false positive:

### 1. Verify It's Actually a False Positive

- Review the security finding carefully
- Consult with team members
- Check if there's a secure alternative

### 2. Document the Exception

Create a PR to add the exception:

```yaml
# Edit .github/security-exceptions.yml
exceptions:
  - id: "EX-001"  # Increment the number
    type: "false-positive"
    tool: "codeql"
    rule: "py/sql-injection"
    file: "src/core/database.py"
    line: 156
    justification: "Using SQLAlchemy ORM with parameterized queries, CodeQL incorrectly flags the query builder"
    risk_accepted: false
    expires: "2024-04-01"  # 3 months maximum
    approved_by: "@security-team"
    approved_date: "2024-01-10"
    pr_reference: "#123"
```

### 3. Get Approval

- Request review from security team
- Link to documentation proving it's safe
- Wait for approval before proceeding

## Emergency Override Process

For critical hotfixes only:

1. **Contact security team lead immediately**
2. **Document in PR description**:

   ```text
   SECURITY_OVERRIDE: Critical production fix

   Justification: [Detailed reason]
   Risk: [What security risk exists]
   Mitigation: [How it will be fixed]
   Deadline: [When it will be fixed]
   ```

3. **Create follow-up issue** for fixing the security issue

See [Security Override Process](override-process.md) for detailed instructions.

## Best Practices

### 1. Run Security Checks Locally

```bash
# Install CodeQL CLI (one-time setup)
# See: https://github.com/github/codeql-cli-binaries

# Run CodeQL analysis locally
codeql database create my-db --language=python
codeql database analyze my-db --format=sarif-latest --output=results.sarif
```

### 2. Fix Issues Early

- Address security warnings in development
- Don't wait for CI to catch issues
- Use IDE security plugins

### 3. Keep Dependencies Updated

```bash
# Weekly dependency check
poetry show --outdated
poetry update --dry-run
```

### 4. Write Secure Code by Default

- Always validate user input
- Use parameterized queries
- Avoid shell command execution
- Sanitize file paths
- Use secure random generators

## Troubleshooting

### Security Check Not Running

- Ensure your PR targets the main branch
- Check if workflows are enabled for your fork
- Verify branch protection is active

### Check Stuck in Pending

- GitHub Actions may be experiencing delays
- Re-run the workflow from the PR page
- Contact DevOps if persistent

### Can't Find Security Scan Results

1. Go to your PR page
2. Click "Checks" tab
3. Select the failing check
4. View detailed logs

## Getting Help

### Resources

- [Security Override Process](override-process.md)
- [Security Exceptions Registry](.github/security-exceptions.yml)
- [GitHub Security Documentation](https://docs.github.com/en/code-security)

### Support Channels

- **Security Team**: <security@company.com>
- **Slack**: #security-help
- **Office Hours**: Thursdays 2-3 PM

### Quick Questions

- For false positives: Contact @security-team
- For tool issues: Contact @devops-team
- For process questions: Check this guide first

## Security Gate Metrics

Weekly reports are generated showing:

- Security scan pass/fail rates
- Common failure reasons
- Exception usage
- Override frequency

Access reports: `security-metrics/`

## Appendix: Security Tools Reference

### CodeQL Rules

- [Python Security Queries](https://codeql.github.com/codeql-query-help/python/)
- Most common: injection, path traversal, XSS

### Dependency Scanning

- Checks against: GitHub Advisory Database, NVD, OSV
- Severity levels: Critical, High, Medium, Low
- Updates daily

### Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Secure Coding Guidelines](https://wiki.sei.cmu.edu/confluence/display/seccode)

---

*Remember: Security gates protect our code and users. When in doubt, ask for help rather than bypassing security checks.*
