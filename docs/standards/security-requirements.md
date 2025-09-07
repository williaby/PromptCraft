# Security Requirements

> **Comprehensive security standards and requirements for PromptCraft development**

## Encryption and Key Management

### Required Keys (MANDATORY)

**Environment must have both GPG and SSH keys configured:**

#### GPG Key Requirements

- **Purpose**: For .env file encryption/decryption
- **Usage**: Encrypts sensitive environment variables locally
- **Validation**: Must be accessible to the application
- **Separation**: Separate from commit signing to avoid conflicts

#### SSH Key Requirements

- **Purpose**: For signed commits to GitHub
- **Usage**: Commit verification and authentication
- **Configuration**: Must be configured in Git for signed commits
- **Separation**: Separate from GPG encryption key

### Key Validation Process

```bash
# MANDATORY validation commands
gpg --list-secret-keys                # Must show GPG keys
ssh-add -l                           # Must show SSH keys
git config --get user.signingkey     # Must show signing key

# Environment validation
poetry run python src/utils/encryption.py
```

### Implementation Pattern

```python
# Follow ledgerbase encryption.py pattern
from cryptography.fernet import Fernet
import gnupg  # For GPG operations

def validate_environment_keys():
    """Validate required GPG and SSH keys are present."""
    # Check GPG key availability
    # Check SSH key configuration
    # Fail fast if either is missing
    pass

def encrypt_env_file(content: str) -> str:
    """Encrypt .env content using GPG key."""
    # Follow ledgerbase pattern
    pass
```

## Service Account Management

### Assured-OSS Service Account Setup (MANDATORY)

**Local development requires service account for assured-oss package access:**

#### File Location Priority

1. `.gcp/service-account.json` (preferred, git-ignored)
2. `secrets/service-account.json` (alternative, git-ignored)
3. `~/.config/promptcraft/service-account.json` (user-global)

#### Setup Process

```bash
# Create secure directory
mkdir -p .gcp

# Copy your service account file (replace with actual path)
cp /path/to/your/service-account.json .gcp/service-account.json

# Run setup script
./scripts/setup-assured-oss-local.sh
```

#### Security Requirements

- Service account file MUST be git-ignored
- Never commit service account credentials
- Re-run setup script if access tokens expire (1 hour lifetime)
- Use least-privilege principle for service account permissions

## Secrets Management

### Local Environment Files

```bash
# Encrypted .env files only
.env.encrypted     # Production secrets (encrypted with GPG)
.env.dev          # Development secrets (encrypted with GPG)
.env.example      # Template with placeholder values (safe to commit)
```

### Encryption Standards

- **Algorithm**: Fernet symmetric encryption (cryptography library)
- **Key Derivation**: GPG-based key management
- **Storage**: No plaintext secrets in version control
- **Access**: Application-level decryption only

### Environment Variable Patterns

```bash
# Database connections
DATABASE_URL="postgresql://user:pass@host:port/db"
QDRANT_URL="http://192.168.1.16:6333"

# API keys (encrypted)
AZURE_AI_API_KEY="encrypted_value"
OPENAI_API_KEY="encrypted_value"

# Authentication secrets
JWT_SECRET_KEY="encrypted_value"
SESSION_SECRET="encrypted_value"

# Service accounts (file paths only)
GOOGLE_APPLICATION_CREDENTIALS=".gcp/service-account.json"
```

## Dependency Security

### Vulnerability Scanning (MANDATORY)

```bash
# Required security scans before commits
poetry run safety check              # Dependency vulnerabilities
poetry run bandit -r src            # Python security issues
poetry run pip-audit                # Additional dependency scanning

# Automated CI/CD scanning
# - GitGuardian (secrets detection)
# - Semgrep (code security analysis)
# - Snyk (dependency vulnerabilities)
```

### Dependency Management

```bash
# Secure dependency installation
poetry install --sync               # Use lock file exclusively
poetry update --lock               # Update with lock file regeneration

# Hash verification (Docker builds)
./scripts/generate_requirements.sh  # Generate requirements-docker.txt with hashes

# Audit dependencies
poetry show --outdated             # Check for updates
nox -s security                    # Comprehensive security analysis
```

### Exclusion Patterns

**Bandit Security Exclusions** (configured in pyproject.toml):

- `B101`: Skip assert statements in tests
- `B601`: Skip shell=True in controlled contexts

## Container Security

### Docker Security Standards

```dockerfile
# Multi-stage builds for minimal attack surface
FROM python:3.11-slim as builder
# Build dependencies and application

FROM python:3.11-slim as runtime
# Minimal runtime environment only

# Non-root user execution
USER promptcraft:1000

# Security environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
```

### Security Controls

- **Non-root execution**: All containers run as user `promptcraft:1000`
- **Minimal base images**: Use slim variants only
- **No secrets in images**: All secrets mounted at runtime
- **Health checks**: Monitor container security posture
- **Security headers**: Implement in application layer

### Network Security

```yaml
# Docker Compose security
services:
  app:
    networks:
      - app-network
    ports:
      - "127.0.0.1:7860:7860"  # Bind to localhost only

networks:
  app-network:
    driver: bridge
    internal: true  # No external access
```

## Authentication and Authorization

### JWT Token Security

```python
# JWT configuration standards
JWT_ALGORITHM = "RS256"  # Asymmetric signing
JWT_EXPIRY = 3600       # 1 hour maximum
JWT_ISSUER = "promptcraft"
JWT_AUDIENCE = "api.promptcraft.local"

# Token validation requirements
- Signature verification
- Expiry validation
- Issuer verification
- Audience validation
- Algorithm allowlist
```

### Session Management

```python
# Session security requirements
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
SESSION_COOKIE_SAMESITE = "Strict" # CSRF protection
SESSION_LIFETIME = 1800           # 30 minutes maximum
```

### Password Security

```python
# Password hashing standards
from werkzeug.security import generate_password_hash, check_password_hash

# Requirements
- Minimum 12 characters
- Mixed case, numbers, symbols
- bcrypt or argon2 hashing
- Salt rounds: minimum 12
- No password storage in logs
```

## Code Security Standards

### Input Validation

```python
# Input validation patterns
from pydantic import BaseModel, validator
from typing import Optional

class SecureInput(BaseModel):
    user_input: str

    @validator('user_input')
    def validate_input(cls, v):
        # Sanitize and validate all inputs
        # Prevent injection attacks
        # Enforce length limits
        return sanitized_input
```

### Output Sanitization

```python
# Output sanitization requirements
- HTML escaping for web output
- SQL parameterization for database queries
- Shell command sanitization
- Log sanitization to prevent injection
- Error message sanitization (no sensitive data exposure)
```

### Secure Coding Practices

- **Principle of Least Privilege**: Minimal permissions for all operations
- **Defense in Depth**: Multiple security layers
- **Fail Secure**: Secure defaults on error conditions
- **Input Validation**: Validate all inputs at boundaries
- **Output Encoding**: Encode outputs for destination context

## API Security

### FastAPI Security Configuration

```python
# Security middleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://promptcraft.yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Minimal required methods
    allow_headers=["Authorization", "Content-Type"],
)

# Authentication middleware
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Token validation logic
    pass
```

### Rate Limiting

```python
# Rate limiting configuration
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/endpoint")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def protected_endpoint():
    pass
```

## Incident Response

### Security Event Logging

```python
# Security logging standards
import logging
import json

security_logger = logging.getLogger('security')

def log_security_event(event_type: str, details: dict):
    """Log security events for monitoring and incident response."""
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'severity': determine_severity(event_type),
    }
    security_logger.warning(json.dumps(event))
```

### Monitoring Requirements

- **Failed authentication attempts**: Log and alert after 5 failures
- **Privilege escalation attempts**: Immediate alerting
- **Suspicious API usage**: Rate limiting and monitoring
- **Data access patterns**: Unusual access monitoring
- **Configuration changes**: Audit logging required

### Response Procedures

1. **Detection**: Automated monitoring and alerting
2. **Assessment**: Classify incident severity and impact
3. **Containment**: Immediate response to limit damage
4. **Investigation**: Forensic analysis and root cause
5. **Recovery**: System restoration and hardening
6. **Lessons Learned**: Process improvement and documentation

## Compliance and Auditing

### Security Audit Requirements

```bash
# Regular security audits
poetry run bandit -r src --format json > security-report.json
poetry run safety check --json > vulnerability-report.json
poetry run semgrep --config=auto src --json > semgrep-report.json
```

### Documentation Requirements

- **Security Architecture**: Document all security controls
- **Threat Model**: Identify and assess security threats
- **Incident Response Plan**: Documented response procedures
- **Security Training**: Developer security awareness
- **Audit Logs**: Comprehensive logging and retention

### Compliance Checklist

- [ ] All secrets encrypted and properly managed
- [ ] Dependency vulnerabilities addressed
- [ ] Input validation implemented
- [ ] Authentication and authorization configured
- [ ] Security logging and monitoring active
- [ ] Container security hardening applied
- [ ] Regular security audits performed
- [ ] Incident response procedures documented
- [ ] Security training completed
- [ ] Code review includes security assessment
