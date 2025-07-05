# PromptCraft Configuration System Usage Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Configuration Options](#configuration-options)
4. [Environment Management](#environment-management)
5. [Security Best Practices](#security-best-practices)
6. [Health Monitoring](#health-monitoring)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

## Introduction

The PromptCraft Configuration System provides a comprehensive, secure, and flexible approach to managing application configuration across different environments. Built on top of Pydantic for type safety and validation, it includes features for encrypted secrets, health monitoring, and environment-specific settings.

### Key Features
- **Type-safe configuration** with Pydantic models
- **Environment-specific settings** (dev, staging, prod)
- **Encrypted secrets management** with GPG
- **Health check endpoints** for operational monitoring
- **Validation with helpful error messages**
- **Hierarchical configuration loading**

## Quick Start

### Installation

The configuration system is included with PromptCraft. Ensure you have the dependencies installed:

```bash
poetry install
```

### Basic Usage

```python
from src.config import get_settings

# Get the application settings
settings = get_settings()

# Access configuration values
print(f"App: {settings.app_name} v{settings.version}")
print(f"Environment: {settings.environment}")
print(f"API: http://{settings.api_host}:{settings.api_port}")
```

### Running the Application

```bash
# Development mode
poetry run python src/main.py

# Production mode with environment variables
PROMPTCRAFT_ENVIRONMENT=prod PROMPTCRAFT_DEBUG=false poetry run python src/main.py
```

## Configuration Options

### Core Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `app_name` | str | "PromptCraft-Hybrid" | Application name |
| `version` | str | "0.1.0" | Application version |
| `environment` | Literal["dev", "staging", "prod"] | "dev" | Deployment environment |
| `debug` | bool | True | Debug mode flag |
| `api_host` | str | "0.0.0.0" | API server host |
| `api_port` | int | 8000 | API server port |

### Database Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `database_url` | SecretStr | None | PostgreSQL connection URL |
| `database_password` | SecretStr | None | Database password |
| `db_pool_size` | int | 10 | Connection pool size |
| `db_max_overflow` | int | 20 | Maximum overflow connections |
| `db_echo` | bool | False | Echo SQL statements |

### Security Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `secret_key` | SecretStr | None | Application secret key |
| `api_key` | SecretStr | None | API authentication key |
| `jwt_secret_key` | SecretStr | None | JWT signing key |
| `encryption_key` | SecretStr | None | Data encryption key |
| `allowed_origins` | list[str] | ["*"] (dev only) | CORS allowed origins |

### External Service Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `azure_openai_api_key` | SecretStr | None | Azure OpenAI API key |
| `azure_openai_endpoint` | HttpUrl | None | Azure OpenAI endpoint |
| `qdrant_host` | str | "192.168.1.16" | Qdrant vector DB host |
| `qdrant_port` | int | 6333 | Qdrant vector DB port |
| `qdrant_api_key` | SecretStr | None | Qdrant API key |

## Environment Management

### Configuration Hierarchy

Configuration is loaded with the following precedence (highest to lowest):

1. **Environment Variables** - `PROMPTCRAFT_` prefix
2. **Environment-specific .env file** - `.env.{environment}`
3. **Base .env file** - `.env`
4. **Pydantic field defaults**

### Environment Files

Create environment-specific configuration files:

#### `.env.dev`
```bash
PROMPTCRAFT_ENVIRONMENT=dev
PROMPTCRAFT_DEBUG=true
PROMPTCRAFT_API_HOST=localhost
PROMPTCRAFT_API_PORT=7860
PROMPTCRAFT_DB_ECHO=true
```

#### `.env.staging`
```bash
PROMPTCRAFT_ENVIRONMENT=staging
PROMPTCRAFT_DEBUG=false
PROMPTCRAFT_API_HOST=0.0.0.0
PROMPTCRAFT_API_PORT=8000
PROMPTCRAFT_ALLOWED_ORIGINS=["https://staging.promptcraft.io"]
```

#### `.env.prod`
```bash
PROMPTCRAFT_ENVIRONMENT=prod
PROMPTCRAFT_DEBUG=false
PROMPTCRAFT_API_HOST=0.0.0.0
PROMPTCRAFT_API_PORT=80
PROMPTCRAFT_ALLOWED_ORIGINS=["https://promptcraft.io"]
```

### Using Encrypted Files

For production environments, use encrypted configuration files:

```bash
# Encrypt a configuration file
gpg --encrypt --recipient your-key-id .env.prod
# Creates .env.prod.gpg

# The system automatically decrypts when loading
PROMPTCRAFT_ENVIRONMENT=prod poetry run python src/main.py
```

## Security Best Practices

### 1. Never Commit Secrets

Use `.gitignore` to exclude sensitive files:
```
.env
.env.*
!.env.*.gpg
```

### 2. Use SecretStr for Sensitive Values

All sensitive configuration values use Pydantic's `SecretStr`:
```python
# Correct - value is protected
api_key: SecretStr = Field(default=None)

# Accessing the value
if settings.api_key:
    actual_value = settings.api_key.get_secret_value()
```

### 3. Validate Production Configuration

```python
# The system automatically validates:
# - Debug mode is off in production
# - Required secrets are configured
# - Security settings are appropriate
```

### 4. Use Health Checks

Monitor configuration status without exposing secrets:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/config
```

## Health Monitoring

### Available Endpoints

#### `/health` - Simple Health Check
```json
{
  "status": "healthy",
  "service": "promptcraft-hybrid",
  "healthy": true,
  "environment": "dev",
  "version": "0.1.0"
}
```

#### `/health/config` - Detailed Configuration Status
```json
{
  "environment": "prod",
  "version": "0.1.0",
  "debug": false,
  "config_loaded": true,
  "encryption_enabled": true,
  "config_source": "env_files",
  "validation_status": "passed",
  "secrets_configured": 5,
  "config_healthy": true
}
```

### Integration with Monitoring

```python
# Example: Prometheus health check
@app.get("/metrics")
async def metrics():
    status = get_configuration_status(settings)
    return {
        "config_healthy": int(status.config_healthy),
        "secrets_configured": status.secrets_configured,
        "encryption_enabled": int(status.encryption_enabled)
    }
```

## Common Patterns

### Conditional Configuration

```python
settings = get_settings()

if settings.environment == "dev":
    # Development-specific behavior
    logging.getLogger().setLevel(logging.DEBUG)
elif settings.environment == "prod":
    # Production-specific behavior
    configure_monitoring()
```

### Feature Flags

```python
# In settings
enable_new_feature: bool = Field(default=False)

# In application
if settings.enable_new_feature:
    activate_new_feature()
```

### Dynamic Reload

```python
# For testing or runtime updates
from src.config import reload_settings

# Change environment variable
os.environ["PROMPTCRAFT_DEBUG"] = "false"

# Reload configuration
settings = reload_settings()
```

## Troubleshooting

### Common Issues

#### 1. Configuration Validation Errors
```
ConfigurationValidationError: Debug mode should be disabled in production
```
**Solution**: Set `PROMPTCRAFT_DEBUG=false` for production

#### 2. Missing Required Secrets
```
ConfigurationValidationError: Database URL is required in production
```
**Solution**: Configure required secrets in environment or .env file

#### 3. Encryption Not Available
```
Warning: Encryption system not available
```
**Solution**: Install cryptography package: `pip install cryptography`

### Debug Configuration Loading

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Load settings with verbose output
settings = get_settings()
```

### Verify Configuration

```python
# Check configuration status
from src.config import get_configuration_status

status = get_configuration_status(settings)
print(f"Config healthy: {status.config_healthy}")
print(f"Validation: {status.validation_status}")
print(f"Source: {status.config_source}")
```

## Next Steps

- Review [Security Best Practices](./security-best-practices.md)
- Explore [Configuration System Guide](./configuration-system-guide.md)
- Run examples: `poetry run python examples/config_demo.py`
- Test health checks: `poetry run python examples/health_check_demo.py`
