# Configuration Security Best Practices

## Overview

This guide outlines security best practices for the PromptCraft configuration system, focusing on protecting
sensitive data, preventing leaks, and maintaining security across different environments.

## Secret Management

### 1. Never Commit Secrets to Version Control

**❌ DON'T:**

```bash
# .env file committed to git
PROMPTCRAFT_SECRET_KEY=super-secret-production-key
PROMPTCRAFT_API_KEY=sk-1234567890abcdef
```

**✅ DO:**

```bash
# .env.example file (safe to commit)
PROMPTCRAFT_SECRET_KEY=your-secret-key-here
PROMPTCRAFT_API_KEY=your-api-key-here

# .gitignore
.env
.env.local
.env.prod
*.gpg
```

### 2. Use Encrypted Files for Production Secrets

**✅ RECOMMENDED:**

```bash
# Create encrypted environment file
echo "PROMPTCRAFT_SECRET_KEY=prod-secret" | gpg --encrypt --armor -r your@email.com > .env.prod.gpg

# Load in production
export PROMPTCRAFT_ENCRYPTED_ENV_FILE=/path/to/.env.prod.gpg
```

### 3. Environment-Specific Secret Management

**Development:**

- Use dummy/development secrets
- Store in local `.env` files (git-ignored)
- No encryption required

**Staging:**

- Use staging-specific secrets
- Encrypted files recommended
- Minimal production-like secrets

**Production:**

- Always use encrypted storage
- Rotate secrets regularly
- Never use development secrets

## Encryption Setup

### 1. GPG Key Management

```bash
# Generate GPG key for encryption
gpg --full-generate-key

# Choose RSA and RSA (default)
# Key size: 4096 bits
# Key expires: 2y (2 years)
# Provide real name and email

# Verify key creation
gpg --list-secret-keys

# Export public key for team sharing
gpg --export --armor your@email.com > public-key.asc
```

### 2. SSH Key for Git Signing

```bash
# Generate SSH key for commit signing
ssh-keygen -t ed25519 -C "your@email.com"

# Add to SSH agent
ssh-add ~/.ssh/id_ed25519

# Configure Git to use SSH signing
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global gpg.format ssh
```

### 3. Key Security

- **Protect private keys with strong passphrases**
- **Store keys securely (encrypted disk, secure key manager)**
- **Never share private keys**
- **Use separate keys for different purposes**
- **Rotate keys annually**

## Environment Configuration

### 1. Environment Detection

```python
from src.config.settings import get_settings

settings = get_settings()

# Environment-specific security checks
if settings.environment == "prod":
    assert not settings.debug, "Debug mode disabled in production"
    assert settings.secret_key, "Secret key required in production"
    assert settings.api_host != "localhost", "Use proper host in production"
```

### 2. Production Security Checklist

- [ ] **Debug mode disabled** (`PROMPTCRAFT_DEBUG=false`)
- [ ] **Strong secret keys** (32+ characters, random)
- [ ] **Proper API hosts** (not localhost/127.0.0.1)
- [ ] **Secure ports** (443 for HTTPS, avoid privileged ports)
- [ ] **All required secrets present**
- [ ] **Encryption keys available**
- [ ] **No development/test data**

### 3. Staging Security Checklist

- [ ] **Debug mode disabled** (recommended)
- [ ] **Staging-specific secrets** (not production secrets)
- [ ] **Isolated from production** (separate databases, APIs)
- [ ] **Production-like security** (encryption, validation)
- [ ] **No real customer data**

## Secret Validation

### 1. Secret Strength Requirements

```python
import secrets
import string

def generate_strong_secret(length=32):
    """Generate cryptographically strong secret."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Generate secrets
secret_key = generate_strong_secret(32)
jwt_secret = generate_strong_secret(64)
api_key = generate_strong_secret(40)
```

### 2. Secret Validation Rules

- **Minimum length**: 16 characters
- **Recommended length**: 32+ characters for keys, 64+ for JWT secrets
- **Character set**: Mix of letters, numbers, symbols
- **Randomness**: Use cryptographically secure random generation
- **Uniqueness**: Different secrets for different purposes

### 3. Custom Secret Validators

```python
from pydantic import field_validator
import re

class ApplicationSettings(BaseSettings):
    secret_key: Optional[SecretStr] = None

    @field_validator("secret_key")
    @classmethod
    def validate_secret_strength(cls, v: Optional[SecretStr]) -> Optional[SecretStr]:
        if v is None:
            return v

        value = v.get_secret_value()

        if len(value) < 16:
            raise ValueError("Secret key must be at least 16 characters")

        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', value):
            raise ValueError("Secret key must contain letters and numbers")

        return v
```

## Logging and Monitoring Security

### 1. Prevent Secret Leakage

```python
import logging
from pydantic import SecretStr

# Configure logging to mask secrets
class SecretFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        # Mask potential secrets (simplified example)
        return re.sub(r'\b[A-Za-z0-9]{20,}\b', '[REDACTED]', message)

# Use SecretStr for all sensitive data
secret_key = SecretStr("sensitive-value")

# This will NOT log the actual value
logging.info(f"Secret configured: {secret_key}")  # Logs: SecretStr('**********')

# Only access when needed
if secret_key:
    actual_value = secret_key.get_secret_value()  # Use with caution
```

### 2. Secure Health Checks

```python
from src.config.health import get_configuration_status

# Health checks never expose secret values
status = get_configuration_status(settings)

# Safe to expose:
print(f"Secrets configured: {status.secrets_configured}")  # Count only
print(f"Config source: {status.config_source}")           # Source type
print(f"Encryption enabled: {status.encryption_enabled}") # Boolean status

# Never exposed:
# - Actual secret values
# - Secret keys
# - API tokens
# - Database passwords
```

### 3. Error Message Security

```python
from src.config.settings import ConfigurationValidationError

# Sanitize error messages
def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages."""
    patterns = [
        (r'password\s*[\'"][^\'\"]+[\'"]', 'password [REDACTED]'),
        (r'key\s*[\'"][^\'\"]+[\'"]', 'key [REDACTED]'),
        (r'secret\s*[\'"][^\'\"]+[\'"]', 'secret [REDACTED]'),
        (r'/[^/\s]+/[^/\s]+\.env', '/[PATH]/[FILE].env'),
    ]

    result = message
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result

# Use in error handling
try:
    validate_configuration()
except Exception as e:
    safe_message = sanitize_error_message(str(e))
    logging.error(f"Configuration error: {safe_message}")
```

## Access Control

### 1. File Permissions

```bash
# Secure file permissions for sensitive files
chmod 600 .env.prod.gpg          # Owner read/write only
chmod 600 ~/.gnupg/*             # GPG keyring protection
chmod 700 ~/.gnupg               # GPG directory protection
chmod 600 ~/.ssh/id_*            # SSH key protection
```

### 2. Environment Variable Security

```python
import os
from typing import Dict, Set

def audit_environment_variables() -> Dict[str, str]:
    """Audit environment variables for sensitive data."""
    sensitive_patterns = {
        'password', 'secret', 'key', 'token', 'auth', 'credential'
    }

    findings = {}
    for key, value in os.environ.items():
        key_lower = key.lower()
        if any(pattern in key_lower for pattern in sensitive_patterns):
            findings[key] = "[PRESENT]" if value else "[EMPTY]"

    return findings

# Regular security audit
audit_results = audit_environment_variables()
for key, status in audit_results.items():
    print(f"Sensitive env var {key}: {status}")
```

### 3. Process Security

```python
import psutil
import os

def check_process_security():
    """Check if sensitive environment variables are visible in process list."""
    current_process = psutil.Process(os.getpid())

    # Check environment variables visible to other processes
    try:
        env_vars = current_process.environ()
        sensitive_vars = [k for k in env_vars.keys()
                         if any(word in k.lower() for word in ['secret', 'key', 'password'])]

        if sensitive_vars:
            print(f"WARNING: Sensitive env vars visible: {sensitive_vars}")
            print("Consider using encrypted files instead of environment variables")
    except psutil.AccessDenied:
        print("Process environment protected (good)")
```

## Network Security

### 1. API Security Configuration

```python
# Secure API configuration
class SecuritySettings:
    def __init__(self, settings):
        self.settings = settings

    def validate_network_security(self):
        """Validate network security configuration."""
        errors = []

        # Check for insecure configurations
        if self.settings.environment == "prod":
            if self.settings.api_host == "0.0.0.0" and self.settings.api_port < 1024:
                errors.append("Production should not bind to privileged ports")

            if not self.settings.debug:
                # Production should not expose debug endpoints
                pass

        # Check SSL/TLS configuration (if applicable)
        if hasattr(self.settings, 'ssl_enabled'):
            if self.settings.environment in ('prod', 'staging') and not self.settings.ssl_enabled:
                errors.append("SSL/TLS should be enabled in production/staging")

        return errors
```

### 2. Database Security

```python
from urllib.parse import urlparse

def validate_database_security(database_url: str, environment: str) -> list:
    """Validate database connection security."""
    errors = []

    if not database_url:
        return errors

    parsed = urlparse(database_url)

    # Check for secure connections
    if environment in ('prod', 'staging'):
        if parsed.scheme not in ('postgresql+ssl', 'mysql+ssl'):
            errors.append("Database should use SSL/TLS in production")

    # Check for default credentials
    if parsed.username in ('root', 'admin', 'postgres') and environment == 'prod':
        errors.append("Production should not use default database usernames")

    # Check for localhost in production
    if environment == 'prod' and parsed.hostname in ('localhost', '127.0.0.1'):
        errors.append("Production should not use localhost database")

    return errors
```

## Deployment Security

### 1. CI/CD Security

```yaml
# .github/workflows/deploy.yml
name: Secure Deployment

on:
  push:
    branches: [main]

jobs:
  security-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Security scanning
      - name: Run Bandit Security Scan
        run: |
          pip install bandit
          bandit -r src/ -f json -o security-report.json

      # Secret scanning
      - name: Run Secret Scan
        run: |
          pip install detect-secrets
          detect-secrets scan --all-files

      # Dependency security
      - name: Check Dependencies
        run: |
          pip install safety
          safety check

  deploy:
    needs: security-checks
    runs-on: ubuntu-latest
    environment: production
    steps:
      # Use encrypted secrets from GitHub Secrets
      - name: Deploy
        env:
          PROMPTCRAFT_SECRET_KEY: ${{ secrets.PROMPTCRAFT_SECRET_KEY }}
          PROMPTCRAFT_API_KEY: ${{ secrets.PROMPTCRAFT_API_KEY }}
        run: |
          # Deployment commands
          echo "Deploying with secure configuration..."
```

### 2. Container Security

```dockerfile
# Multi-stage build for security
FROM python:3.11-slim as base

# Create non-root user
RUN groupadd --gid 1000 promptcraft && \
    useradd --uid 1000 --gid promptcraft --shell /bin/bash --create-home promptcraft

# Security: Remove unnecessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# Security: Set secure environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

# Switch to non-root user
USER promptcraft
WORKDIR /app

# Copy application code
COPY --chown=promptcraft:promptcraft . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Runtime Security Monitoring

```python
import logging
import time
from typing import Dict, Any

class SecurityMonitor:
    def __init__(self):
        self.logger = logging.getLogger("security")
        self.failed_attempts = {}

    def log_configuration_access(self, operation: str, success: bool, details: Dict[str, Any]):
        """Log configuration access for security monitoring."""
        log_data = {
            "timestamp": time.time(),
            "operation": operation,
            "success": success,
            "user": details.get("user", "system"),
            "source_ip": details.get("source_ip", "unknown")
        }

        if success:
            self.logger.info(f"Configuration {operation} successful", extra=log_data)
        else:
            self.logger.warning(f"Configuration {operation} failed", extra=log_data)
            self._track_failed_attempt(details.get("source_ip", "unknown"))

    def _track_failed_attempt(self, source_ip: str):
        """Track failed attempts for rate limiting."""
        if source_ip not in self.failed_attempts:
            self.failed_attempts[source_ip] = []

        self.failed_attempts[source_ip].append(time.time())

        # Clean old attempts (older than 1 hour)
        cutoff = time.time() - 3600
        self.failed_attempts[source_ip] = [
            attempt for attempt in self.failed_attempts[source_ip]
            if attempt > cutoff
        ]

        # Alert on too many failures
        if len(self.failed_attempts[source_ip]) > 10:
            self.logger.critical(f"Too many failed attempts from {source_ip}")

# Usage
monitor = SecurityMonitor()
monitor.log_configuration_access("secret_access", True, {"user": "api"})
```

## Incident Response

### 1. Secret Compromise Response

**Immediate Actions:**

1. **Rotate compromised secrets immediately**
2. **Revoke access tokens/API keys**
3. **Update encrypted files with new secrets**
4. **Deploy new configuration**
5. **Monitor for unauthorized access**

```bash
# Emergency secret rotation script
#!/bin/bash

echo "Emergency secret rotation initiated..."

# Generate new secrets
NEW_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
NEW_JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# Update environment
export PROMPTCRAFT_SECRET_KEY="$NEW_SECRET_KEY"
export PROMPTCRAFT_JWT_SECRET_KEY="$NEW_JWT_SECRET"

# Restart services
docker-compose restart
kubectl rollout restart deployment/promptcraft

echo "Secret rotation completed. Monitor logs for issues."
```

### 2. Security Audit Log Analysis

```python
import json
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_security_logs(log_file: str) -> Dict[str, Any]:
    """Analyze security logs for suspicious activity."""

    suspicious_patterns = []
    failed_attempts = defaultdict(int)

    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)

                # Track failed configuration access
                if not log_entry.get('success', True):
                    source_ip = log_entry.get('source_ip', 'unknown')
                    failed_attempts[source_ip] += 1

                # Check for suspicious patterns
                if log_entry.get('operation') == 'secret_access':
                    if log_entry.get('user') == 'anonymous':
                        suspicious_patterns.append(log_entry)

            except json.JSONDecodeError:
                continue

    # Generate report
    report = {
        'total_failed_attempts': sum(failed_attempts.values()),
        'suspicious_ips': {ip: count for ip, count in failed_attempts.items() if count > 5},
        'suspicious_patterns': suspicious_patterns,
        'analysis_time': datetime.utcnow().isoformat()
    }

    return report
```

### 3. Configuration Backup and Recovery

```python
import json
import shutil
from datetime import datetime
from pathlib import Path

class ConfigurationBackup:
    def __init__(self, backup_dir: str = "/secure/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_configuration(self, settings) -> str:
        """Create secure backup of configuration."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name

        # Create backup data (without secrets)
        backup_data = {
            'environment': settings.environment,
            'version': settings.version,
            'api_host': settings.api_host,
            'api_port': settings.api_port,
            'debug': settings.debug,
            'backup_timestamp': timestamp,
            'secrets_configured': sum(1 for field in settings.__fields__
                                    if getattr(settings, field) is not None and 'secret' in field.lower())
        }

        # Write backup
        with open(backup_path.with_suffix('.json'), 'w') as f:
            json.dump(backup_data, f, indent=2)

        # Backup encrypted files if they exist
        for env_file in ['prod', 'staging']:
            env_path = Path(f".env.{env_file}.gpg")
            if env_path.exists():
                shutil.copy(env_path, backup_path.with_suffix(f'.{env_file}.gpg'))

        return str(backup_path)

    def restore_configuration(self, backup_name: str):
        """Restore configuration from backup."""
        backup_path = self.backup_dir / backup_name

        if not backup_path.with_suffix('.json').exists():
            raise ValueError(f"Backup {backup_name} not found")

        # Implementation would restore configuration
        # This is a placeholder for the actual restore logic
        print(f"Restoring configuration from {backup_path}")
```

## Security Testing

### 1. Security Test Suite

```python
import pytest
from unittest.mock import patch
import os

class TestConfigurationSecurity:
    def test_secrets_not_in_logs(self, caplog):
        """Test that secrets are not exposed in logs."""
        from src.config.settings import ApplicationSettings
        import logging

        settings = ApplicationSettings(
            secret_key="super-secret-value",
            api_key="secret-api-key"
        )

        with caplog.at_level(logging.DEBUG):
            logging.info(f"Settings loaded: {settings}")

        log_text = caplog.text
        assert "super-secret-value" not in log_text
        assert "secret-api-key" not in log_text

    def test_production_security_validation(self):
        """Test production security requirements."""
        from src.config.settings import ApplicationSettings, validate_configuration_on_startup

        # Should fail with insecure production config
        settings = ApplicationSettings(
            environment="prod",
            debug=True,  # Insecure
            api_host="localhost",  # Insecure
        )

        with pytest.raises(Exception):
            validate_configuration_on_startup(settings)

    def test_secret_strength_validation(self):
        """Test secret strength requirements."""
        from src.config.settings import ApplicationSettings

        # Weak secret should fail
        with pytest.raises(ValueError):
            ApplicationSettings(secret_key="weak")

        # Strong secret should pass
        settings = ApplicationSettings(secret_key="strong-secret-key-32-characters-long")
        assert settings.secret_key is not None

    @patch.dict(os.environ, {}, clear=True)
    def test_no_secrets_in_environment_default(self):
        """Test that no secrets are exposed in default environment."""
        from src.config.settings import ApplicationSettings

        settings = ApplicationSettings()

        # Default settings should not have secrets
        assert settings.secret_key is None
        assert settings.api_key is None
        assert settings.database_password is None
```

### 2. Penetration Testing Checklist

- [ ] **Configuration injection attacks**
- [ ] **Environment variable enumeration**
- [ ] **File path traversal in config loading**
- [ ] **Secret extraction from memory dumps**
- [ ] **Log file analysis for secret leakage**
- [ ] **Health endpoint information disclosure**
- [ ] **Configuration tampering**
- [ ] **Privilege escalation through config**

### 3. Automated Security Scanning

```bash
#!/bin/bash
# security-scan.sh

echo "Running automated security scans..."

# Static analysis
bandit -r src/ -ll

# Secret detection
detect-secrets scan --all-files

# Dependency vulnerabilities
safety check

# Configuration security
python scripts/security-audit.py

# Docker security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/root/.cache/ aquasec/trivy image promptcraft:latest

echo "Security scan completed. Review results above."
```

## Compliance and Governance

### 1. Security Documentation Requirements

- **Security architecture documentation**
- **Secret management procedures**
- **Incident response playbooks**
- **Access control policies**
- **Audit logging requirements**
- **Compliance mapping (SOC2, PCI, etc.)**

### 2. Regular Security Reviews

```python
from datetime import datetime, timedelta

class SecurityReviewSchedule:
    def __init__(self):
        self.last_review = None
        self.review_interval = timedelta(days=90)  # Quarterly

    def is_review_due(self) -> bool:
        """Check if security review is due."""
        if not self.last_review:
            return True

        return datetime.utcnow() - self.last_review > self.review_interval

    def security_review_checklist(self) -> list:
        """Return security review checklist."""
        return [
            "Review and rotate all secrets",
            "Audit access permissions",
            "Update security documentation",
            "Test incident response procedures",
            "Review dependency vulnerabilities",
            "Validate encryption key strength",
            "Check compliance requirements",
            "Update security training"
        ]
```

Remember: Security is an ongoing process, not a one-time setup. Regularly review and update these practices as your
application and threat landscape evolve.
