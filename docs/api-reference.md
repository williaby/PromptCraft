# Configuration System API Reference

## Core Functions

### `get_settings(validate_on_startup: bool = True) -> ApplicationSettings`

Get the application settings using a singleton pattern.

**Parameters:**

- `validate_on_startup` (bool): Whether to validate configuration on load. Default: True

**Returns:**

- `ApplicationSettings`: The application configuration instance

**Raises:**

- `ConfigurationValidationError`: If validation fails

**Example:**

```python
from src.config import get_settings

settings = get_settings()
print(f"Environment: {settings.environment}")
```

### `reload_settings(validate_on_startup: bool = True) -> ApplicationSettings`

Force reload settings from environment and files.

**Parameters:**

- `validate_on_startup` (bool): Whether to validate configuration on load. Default: True

**Returns:**

- `ApplicationSettings`: New application configuration instance

**Example:**

```python
from src.config import reload_settings

# Change environment
os.environ["PROMPTCRAFT_ENVIRONMENT"] = "staging"

# Reload settings
settings = reload_settings()
```

## Health Check Functions

### `get_configuration_status(settings: ApplicationSettings) -> ConfigurationStatusModel`

Generate comprehensive configuration status for health monitoring.

**Parameters:**

- `settings` (ApplicationSettings): The settings instance to analyze

**Returns:**

- `ConfigurationStatusModel`: Detailed configuration status

**Example:**

```python
from src.config import get_settings, get_configuration_status

settings = get_settings()
status = get_configuration_status(settings)

print(f"Config healthy: {status.config_healthy}")
print(f"Secrets configured: {status.secrets_configured}")
```

### `get_configuration_health_summary() -> dict[str, Any]`

Get a simplified health summary for quick checks.

**Returns:**

- `dict`: Basic health information

**Example:**

```python
from src.config import get_configuration_health_summary

summary = get_configuration_health_summary()
if summary["healthy"]:
    print("Configuration is healthy")
```

## Models

### `ApplicationSettings`

Main application configuration model.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_name` | str | "PromptCraft-Hybrid" | Application name |
| `version` | str | "0.1.0" | Application version |
| `environment` | Literal["dev", "staging", "prod"] | "dev" | Deployment environment |
| `debug` | bool | True | Debug mode flag |
| `api_host` | str | "0.0.0.0" | API server host |
| `api_port` | int | 8000 | API server port |
| `database_url` | SecretStr | None | Database connection URL |
| `database_password` | SecretStr | None | Database password |
| `secret_key` | SecretStr | None | Application secret key |
| `api_key` | SecretStr | None | API authentication key |
| `jwt_secret_key` | SecretStr | None | JWT signing key |
| `encryption_key` | SecretStr | None | Data encryption key |

**Configuration:**

- Environment prefix: `PROMPTCRAFT_`
- Case sensitive: No
- Extra fields: Forbidden

### `ConfigurationStatusModel`

Configuration status for health checks.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `environment` | str | Current deployment environment |
| `version` | str | Application version string |
| `debug` | bool | Whether debug mode is enabled |
| `config_loaded` | bool | Configuration loaded successfully |
| `encryption_enabled` | bool | Encryption system availability |
| `config_source` | str | Primary configuration source |
| `validation_status` | str | Validation result (passed/failed/warning) |
| `validation_errors` | list[str] | Sanitized validation errors |
| `secrets_configured` | int | Number of configured secrets |
| `api_host` | str | API host address |
| `api_port` | int | API port number |
| `timestamp` | datetime | Status generation time (UTC) |
| `config_healthy` | bool | Overall health (computed) |

## Exceptions

### `ConfigurationValidationError`

Raised when configuration validation fails.

**Attributes:**

- `message` (str): Error description
- `field_errors` (list[str]): Specific field validation errors
- `suggestions` (list[str]): Helpful suggestions for fixing

**Example:**

```python
from src.config import ConfigurationValidationError

try:
    settings = get_settings()
except ConfigurationValidationError as e:
    print(f"Error: {e}")
    for error in e.field_errors:
        print(f"  - {error}")
```

## HTTP Endpoints

### `GET /health`

Simple health check endpoint for monitoring.

**Response:**

```json
{
  "status": "healthy",
  "service": "promptcraft-hybrid",
  "healthy": true,
  "environment": "dev",
  "version": "0.1.0",
  "config_loaded": true,
  "encryption_available": false,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Status Codes:**

- `200`: Service is healthy
- `503`: Service is unhealthy
- `500`: Health check failed

### `GET /health/config`

Detailed configuration status endpoint.

**Response:**

```json
{
  "environment": "prod",
  "version": "0.1.0",
  "debug": false,
  "config_loaded": true,
  "encryption_enabled": true,
  "config_source": "env_files",
  "validation_status": "passed",
  "validation_errors": [],
  "secrets_configured": 5,
  "api_host": "0.0.0.0",
  "api_port": 80,
  "timestamp": "2024-01-01T12:00:00Z",
  "config_healthy": true
}
```

**Status Codes:**

- `200`: Configuration status retrieved
- `500`: Configuration check failed

### `GET /ping`

Simple ping endpoint for load balancers.

**Response:**

```json
{
  "message": "pong"
}
```

### `GET /`

Root endpoint with application information.

**Response:**

```json
{
  "service": "PromptCraft-Hybrid",
  "version": "0.1.0",
  "environment": "dev",
  "status": "running",
  "docs_url": "/docs"
}
```

## Environment Variables

All configuration can be set via environment variables with the `PROMPTCRAFT_` prefix.

### Format

```bash
PROMPTCRAFT_<SETTING_NAME>=value
```

### Examples

```bash
# Basic settings
PROMPTCRAFT_ENVIRONMENT=prod
PROMPTCRAFT_DEBUG=false
PROMPTCRAFT_API_PORT=8080

# Secret values
PROMPTCRAFT_SECRET_KEY=your-secret-key
PROMPTCRAFT_DATABASE_PASSWORD=secure-password
PROMPTCRAFT_API_KEY=api-key-value

# Complex types (JSON)
PROMPTCRAFT_ALLOWED_ORIGINS='["https://app.com", "https://api.com"]'
```

## Configuration Files

### File Loading Order

1. `.env.{environment}.gpg` (encrypted, if exists)
2. `.env.{environment}` (plaintext)
3. `.env.gpg` (encrypted base config)
4. `.env` (plaintext base config)

### File Format

```bash
# .env file example
PROMPTCRAFT_APP_NAME=MyApp
PROMPTCRAFT_VERSION=1.0.0
PROMPTCRAFT_ENVIRONMENT=dev
PROMPTCRAFT_DEBUG=true
```

## Validation Rules

### Built-in Validations

1. **Environment validation**: Must be one of: dev, staging, prod
2. **Port validation**: Must be between 1-65535
3. **URL validation**: Database URLs must be valid connection strings
4. **Production rules**:
   - Debug must be false in production
   - Required secrets must be configured
   - Security headers must be set

### Custom Validations

Add custom validation in settings:

```python
from pydantic import field_validator

class ApplicationSettings(BaseSettings):
    api_port: int = Field(default=8000)

    @field_validator("api_port")
    @classmethod
    def validate_api_port(cls, v: int) -> int:
        if v < 1024 and v != 80 and v != 443:
            raise ValueError("Ports below 1024 require root privileges")
        return v
```

## Security Considerations

### Secret Protection

All sensitive values use `SecretStr`:

- Values are not displayed in logs
- String representation shows `**********`
- Access with `.get_secret_value()`

### Health Check Safety

Health endpoints never expose:

- Actual secret values
- File system paths
- Internal error details
- Stack traces

### Encryption Support

When GPG encryption is available:

- `.env.{environment}.gpg` files are automatically decrypted
- Encryption status shown in health checks
- No plaintext secrets on disk

## Examples

### Basic Configuration Access

```python
from src.config import get_settings

settings = get_settings()

# Basic settings
print(f"App: {settings.app_name}")
print(f"Version: {settings.version}")
print(f"Environment: {settings.environment}")

# Conditional logic
if settings.debug:
    enable_debug_features()

# Safe secret access
if settings.api_key:
    api_key_value = settings.api_key.get_secret_value()
    configure_api_auth(api_key_value)
```

### Health Check Integration

```python
from fastapi import FastAPI, HTTPException
from src.config import get_configuration_health_summary

app = FastAPI()

@app.get("/health")
async def health():
    summary = get_configuration_health_summary()
    if not summary["healthy"]:
        raise HTTPException(status_code=503, detail=summary)
    return summary
```

### Environment-Specific Behavior

```python
from src.config import get_settings

settings = get_settings()

match settings.environment:
    case "dev":
        configure_development()
    case "staging":
        configure_staging()
    case "prod":
        configure_production()
```
