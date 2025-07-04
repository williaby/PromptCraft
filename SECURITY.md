# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches
depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to **<security@promptcraft.io>**. You will receive a response
from us within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on
complexity but historically within a few days.

Please include the following in your report:

1. Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
2. Full paths of source file(s) related to the manifestation of the issue
3. The location of the affected source code (tag/branch/commit or direct URL)
4. Any special configuration required to reproduce the issue
5. Step-by-step instructions to reproduce the issue
6. Proof-of-concept or exploit code (if possible)
7. Impact of the issue, including how an attacker might exploit the issue

## Security Best Practices

### Dependencies

- All dependencies are locked with specific versions in `poetry.lock`
- Requirements are exported with cryptographic hashes for pip verification
- Automated dependency updates via Renovate bot
- Daily security scanning in CI/CD pipeline

### Code Security

- All code is scanned with Bandit for common security issues
- Secrets detection prevents accidental credential commits
- Type checking with mypy reduces runtime errors
- Comprehensive test coverage (>80%) for all critical paths

### Infrastructure

- All containers run as non-root users
- Minimal base images to reduce attack surface
- Network isolation between services
- Secrets managed via environment variables (never in code)

## Security Checklist for Contributors

Before submitting a PR:

- [ ] Run `nox -s security` to check for vulnerabilities
- [ ] Ensure no secrets are exposed in code or configuration
- [ ] Verify all user inputs are validated and sanitized
- [ ] Check that error messages don't leak sensitive information
- [ ] Confirm logging doesn't include PII or credentials
- [ ] Test with `pip install --require-hashes` to verify dependency integrity
