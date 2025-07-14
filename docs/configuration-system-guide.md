# PromptCraft Configuration System Guide

## Overview

The PromptCraft configuration system provides a robust, secure, and environment-aware approach to application configuration. Built on Pydantic for type safety and validation, it supports encrypted secrets, environment-specific settings, and comprehensive health monitoring.

## Quick Start

### Basic Usage

```python
from src.config.settings import get_settings

# Get application settings
settings = get_settings()

# Access configuration values
print(f"Running on {settings.api_host}:{settings.api_port}")
print(f"Environment: {settings.environment}")
print(f"Debug mode: {settings.debug}")
```

### Environment Variables

Set configuration via environment variables with `PROMPTCRAFT_` prefix:

```bash
export PROMPTCRAFT_ENVIRONMENT=prod
export PROMPTCRAFT_API_HOST=0.0.0.0
export PROMPTCRAFT_API_PORT=80
export PROMPTCRAFT_DEBUG=false
export PROMPTCRAFT_SECRET_KEY=your-secret-key-here
```

### Environment Files

Create `.env` files for each environment:

```bash
# .env.dev
PROMPTCRAFT_ENVIRONMENT=dev
PROMPTCRAFT_DEBUG=true
PROMPTCRAFT_API_HOST=localhost
PROMPTCRAFT_API_PORT=8000

# .env.prod
PROMPTCRAFT_ENVIRONMENT=prod
PROMPTCRAFT_DEBUG=false
PROMPTCRAFT_API_HOST=0.0.0.0
PROMPTCRAFT_API_PORT=80
PROMPTCRAFT_SECRET_KEY=production-secret-key
```

## Configuration Schema

### Core Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `app_name` | `str` | "PromptCraft-Hybrid" | Application name |
| `version` | `str` | "0.1.0" | Application version |
| `environment` | `str` | "dev" | Environment (dev/staging/prod) |
| `debug` | `bool` | `True` | Debug mode flag |
| `api_host` | `str` | "0.0.0.0" | API server host |
| `api_port` | `int` | 8000 | API server port |

### Secret Settings

All secret settings use `SecretStr` for secure handling:

| Setting | Type | Required | Description |
|---------|------|----------|-------------|
| `database_password` | `SecretStr` | Optional | Database password |
| `database_url` | `SecretStr` | Optional | Complete database URL |
| `api_key` | `SecretStr` | Optional | External API key |
| `secret_key` | `SecretStr` | Prod/Staging | Application secret key |
| `azure_openai_api_key` | `SecretStr` | Optional | Azure OpenAI API key |
| `jwt_secret_key` | `SecretStr` | Production | JWT signing key |
| `qdrant_api_key` | `SecretStr` | Optional | Qdrant vector DB API key |
| `encryption_key` | `SecretStr` | Optional | Encryption key |

### External Service Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `qdrant_host` | `str` | `${QDRANT_HOST:-localhost}` | Qdrant vector database host (use QDRANT_HOST env var) |
| `qdrant_port` | `int` | 6333 | Qdrant vector database port |
| `zen_mcp_host` | `str` | "localhost" | Zen MCP server host |
| `zen_mcp_port` | `int` | 3000 | Zen MCP server port |

## Environment-Specific Configuration

### Development Environment

- **Validation**: Lenient, allows debug mode and localhost
- **Required Secrets**: None
- **Default Values**: Optimized for local development

```python
# Development configuration example
settings = ApplicationSettings(
    environment="dev",
    debug=True,
    api_host="localhost",
    api_port=8000
)
```

### Staging Environment

- **Validation**: Moderate, requires some secrets
- **Required Secrets**: `secret_key`
- **Security**: Encryption recommended but not required

```python
# Staging configuration example
settings = ApplicationSettings(
    environment="staging",
    debug=False,
    api_host="staging.example.com",
    api_port=443,
    secret_key="staging-secret-key"
)
```

### Production Environment

- **Validation**: Strict, enforces security best practices
- **Required Secrets**: `secret_key`, `jwt_secret_key`
- **Security**: Encryption required, no debug mode, proper hosts

```python
# Production configuration example
settings = ApplicationSettings(
    environment="prod",
    debug=False,
    api_host="0.0.0.0",
    api_port=80,
    secret_key="production-secret-key-32-chars",
    jwt_secret_key="jwt-production-secret-key"
)
```

## Encrypted Configuration

### Setup Encryption

1. **Generate GPG Key**:
   ```bash
   gpg --full-generate-key
   # Follow prompts to create key
   ```

2. **Configure SSH Key**:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ssh-add ~/.ssh/id_ed25519
   ```

3. **Validate Keys**:
   ```python
   from src.config.settings import validate_encryption_available

   if validate_encryption_available():
       print("Encryption is ready!")
   else:
       print("Encryption setup required")
   ```

### Create Encrypted Environment File

```python
from src.utils.encryption import encrypt_env_file

# Prepare environment content
env_content = """
PROMPTCRAFT_SECRET_KEY=super-secret-production-key
PROMPTCRAFT_JWT_SECRET_KEY=jwt-secret-for-production
PROMPTCRAFT_API_KEY=external-api-key-value
PROMPTCRAFT_DATABASE_PASSWORD=secure-database-password
"""

# Encrypt for production use
encrypted_content = encrypt_env_file(
    content=env_content,
    recipient="your-email@example.com"
)

# Save to encrypted file
with open(".env.prod.gpg", "w") as f:
    f.write(encrypted_content)
```

### Load Encrypted Configuration

```python
from src.config.settings import get_settings
import os

# Point to encrypted file
os.environ["PROMPTCRAFT_ENCRYPTED_ENV_FILE"] = "/path/to/.env.prod.gpg"

# Load settings (automatically decrypts)
settings = get_settings()
```

## Validation and Error Handling

### Field Validation

The configuration system provides detailed validation with helpful error messages:

```python
from src.config.settings import ApplicationSettings
from pydantic import ValidationError

try:
    settings = ApplicationSettings(
        api_port=99999,  # Invalid port
        api_host="",     # Empty host
        version="invalid" # Invalid version format
    )
except ValidationError as e:
    for error in e.errors():
        print(f"Field: {error['loc'][0]}")
        print(f"Error: {error['msg']}")
        print(f"Value: {error['input']}")
```

### Environment-Specific Validation

```python
from src.config.settings import validate_configuration_on_startup, ConfigurationValidationError

try:
    settings = ApplicationSettings(environment="prod", debug=True)
    validate_configuration_on_startup(settings)
except ConfigurationValidationError as e:
    print(f"Configuration Error: {e}")
    print("Field Errors:")
    for error in e.field_errors:
        print(f"  • {error}")
    print("Suggestions:")
    for suggestion in e.suggestions:
        print(f"  • {suggestion}")
```

### Custom Validation Errors

```python
from src.config.settings import ConfigurationValidationError

# Create detailed error with suggestions
error = ConfigurationValidationError(
    "Configuration validation failed",
    field_errors=[
        "API port must be between 1-65535",
        "Secret key is required in production"
    ],
    suggestions=[
        "Set PROMPTCRAFT_API_PORT=8000",
        "Set PROMPTCRAFT_SECRET_KEY environment variable"
    ]
)
raise error
```

## Health Monitoring

### Health Check Endpoints

The configuration system provides health check endpoints for monitoring:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed configuration health
curl http://localhost:8000/health/config
```

### Health Check Response Format

```json
{
  "status": "healthy",
  "service": "promptcraft-hybrid",
  "environment": "prod",
  "version": "1.0.0",
  "healthy": true,
  "config_loaded": true,
  "encryption_available": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Configuration Status Details

```json
{
  "environment": "prod",
  "version": "1.0.0",
  "debug": false,
  "config_loaded": true,
  "encryption_enabled": true,
  "config_source": "env_vars",
  "validation_status": "passed",
  "secrets_configured": 5,
  "api_host": "0.0.0.0",
  "api_port": 80,
  "config_healthy": true,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Programmatic Health Checks

```python
from src.config.health import get_configuration_status, get_configuration_health_summary

# Get detailed status
settings = get_settings()
status = get_configuration_status(settings)

print(f"Config Health: {status.config_healthy}")
print(f"Secrets Configured: {status.secrets_configured}")
print(f"Validation Status: {status.validation_status}")

# Get health summary
summary = get_configuration_health_summary()
if summary["healthy"]:
    print("All systems operational")
else:
    print(f"Health issue: {summary.get('error', 'Unknown')}")
```

## Security Best Practices

### Secret Management

1. **Never commit secrets to version control**
2. **Use encrypted .env files for production**
3. **Rotate secrets regularly**
4. **Use environment variables in CI/CD**
5. **Validate encryption keys are available**

### Environment Security

```python
# Validate security configuration
def validate_production_security(settings):
    errors = []

    if settings.environment == "prod":
        if settings.debug:
            errors.append("Debug mode must be disabled in production")

        if not settings.secret_key:
            errors.append("Secret key is required in production")

        if settings.api_host in ("localhost", "127.0.0.1"):
            errors.append("Production should not use localhost")

    if errors:
        raise ConfigurationValidationError(
            "Security validation failed",
            field_errors=errors
        )
```

### Logging Security

The configuration system ensures sensitive values are never logged:

```python
# Secrets are automatically masked in logs and string representations
settings = ApplicationSettings(secret_key="super-secret-value")

# This will NOT expose the secret value
print(str(settings))  # Shows SecretStr('**********')

# Access secret value only when needed
secret_value = settings.secret_key.get_secret_value()
```

## Migration Guide

### From Environment Variables Only

If you're currently using basic environment variables:

```python
# Before
import os
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))

# After
from src.config.settings import get_settings
settings = get_settings()
API_HOST = settings.api_host
API_PORT = settings.api_port
```

### From Config Files

If you're using YAML/JSON config files:

```python
# Before
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# After - Convert to environment variables or .env file
# Create .env file with PROMPTCRAFT_ prefixes
# Use the new configuration system
```

### Adding New Configuration Fields

1. **Add field to ApplicationSettings**:
   ```python
   class ApplicationSettings(BaseSettings):
       # Existing fields...
       new_feature_enabled: bool = Field(default=False, description="Enable new feature")
   ```

2. **Add validation if needed**:
   ```python
   @field_validator("new_feature_enabled")
   @classmethod
   def validate_new_feature(cls, v: bool) -> bool:
       # Add custom validation logic
       return v
   ```

3. **Update environment variables**:
   ```bash
   export PROMPTCRAFT_NEW_FEATURE_ENABLED=true
   ```

4. **Update documentation and tests**

## Troubleshooting

### Common Issues

#### 1. Encryption Not Available

**Error**: "Production environment detected but encryption not available"

**Solutions**:
- Install GPG: `sudo apt install gnupg` (Linux) or `brew install gnupg` (macOS)
- Generate GPG key: `gpg --full-generate-key`
- Verify key: `gpg --list-secret-keys`

#### 2. Configuration Validation Failed

**Error**: "Configuration validation failed for prod environment"

**Solutions**:
- Check required secrets are set
- Verify environment-specific requirements
- Review validation error messages for specific issues

#### 3. File Not Found Errors

**Error**: "Encrypted file not found"

**Solutions**:
- Verify file path is correct
- Check file permissions
- Ensure file exists and is readable

#### 4. Port Already in Use

**Error**: "Port 8000 is already in use"

**Solutions**:
- Change port: `export PROMPTCRAFT_API_PORT=8001`
- Find process using port: `lsof -i :8000`
- Kill process or use different port

### Debug Configuration Issues

```python
from src.config.settings import get_settings, validate_configuration_on_startup
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

try:
    settings = get_settings()
    validate_configuration_on_startup(settings)
    print("Configuration is valid!")
except Exception as e:
    print(f"Configuration error: {e}")

    # Check specific areas
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"API endpoint: {settings.api_host}:{settings.api_port}")
```

### Environment-Specific Debugging

```python
from src.config.health import get_configuration_status

settings = get_settings()
status = get_configuration_status(settings)

print(f"Config source: {status.config_source}")
print(f"Encryption enabled: {status.encryption_enabled}")
print(f"Secrets configured: {status.secrets_configured}")

if not status.config_healthy:
    print("Validation errors:")
    for error in status.validation_errors:
        print(f"  • {error}")
```

## Next Steps

- Review [Security Best Practices](./security-best-practices.md)
- Explore [Configuration System Guide](./configuration-system-guide.md)
- Run examples: `poetry run python examples/config_demo.py`
- Test health checks: `poetry run python examples/health_check_demo.py`
