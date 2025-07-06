# Configuration System Migration Guide

This guide helps you migrate from the previous configuration approach to the new Phase 1-5 Configuration System.

## Overview

The new configuration system provides:
- Type-safe settings with Pydantic validation
- Environment-specific configuration loading
- Encrypted secrets management
- Health check monitoring
- Better error messages and validation

## Migration Steps

### 1. Update Dependencies

Add the required dependencies to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
cryptography = "^41.0.0"  # For encryption support
```

Run `poetry install` to install dependencies.

### 2. Replace Old Configuration

#### Before (Old Approach)
```python
# config.py
import os

API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")
```

#### After (New Approach)
```python
# Use the centralized configuration
from src.config import get_settings

settings = get_settings()

# Access configuration
api_host = settings.api_host
api_port = settings.api_port
debug = settings.debug
secret_key = settings.secret_key.get_secret_value() if settings.secret_key else None
```

### 3. Update Environment Variables

Add the `PROMPTCRAFT_` prefix to all environment variables:

#### Before
```bash
export API_HOST=0.0.0.0
export API_PORT=8080
export DEBUG=false
export SECRET_KEY=my-secret-key
```

#### After
```bash
export PROMPTCRAFT_API_HOST=0.0.0.0
export PROMPTCRAFT_API_PORT=8080
export PROMPTCRAFT_DEBUG=false
export PROMPTCRAFT_SECRET_KEY=my-secret-key
```

### 4. Create Environment Files

Instead of managing individual environment variables, create `.env` files:

```bash
# .env.dev
PROMPTCRAFT_ENVIRONMENT=dev
PROMPTCRAFT_DEBUG=true
PROMPTCRAFT_API_HOST=localhost
PROMPTCRAFT_API_PORT=7860

# .env.prod
PROMPTCRAFT_ENVIRONMENT=prod
PROMPTCRAFT_DEBUG=false
PROMPTCRAFT_API_HOST=0.0.0.0
PROMPTCRAFT_API_PORT=80
PROMPTCRAFT_SECRET_KEY=production-secret-key
```

### 5. Update Application Startup

#### Before
```python
# main.py
import os
from fastapi import FastAPI

app = FastAPI(debug=os.getenv("DEBUG", "true") == "true")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000"))
    )
```

#### After
```python
# main.py
from fastapi import FastAPI
from src.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port
    )
```

### 6. Handle Validation Errors

The new system provides better error handling:

```python
from src.config import get_settings, ConfigurationValidationError

try:
    settings = get_settings()
except ConfigurationValidationError as e:
    print(f"Configuration error: {e}")
    for error in e.field_errors:
        print(f"  - {error}")
    for suggestion in e.suggestions:
        print(f"  💡 {suggestion}")
    exit(1)
```

### 7. Add Health Checks

Add health check endpoints to monitor configuration:

```python
from src.config import get_configuration_health_summary

@app.get("/health")
async def health_check():
    return get_configuration_health_summary()
```

## Common Migration Issues

### Issue 1: Missing Environment Prefix

**Error**: Settings not loading from environment variables

**Solution**: Ensure all environment variables use the `PROMPTCRAFT_` prefix

### Issue 2: Type Conversion Errors

**Before**: Manual type conversion
```python
port = int(os.getenv("PORT", "8000"))
```

**After**: Automatic type conversion with validation
```python
api_port: int = Field(default=8000, ge=1, le=65535)
```

### Issue 3: Secret Handling

**Before**: Plain text secrets
```python
secret = os.getenv("SECRET_KEY")
```

**After**: Protected secrets with SecretStr
```python
secret_key: SecretStr = Field(default=None)
# Access with: settings.secret_key.get_secret_value()
```

## Testing Your Migration

1. **Verify Configuration Loading**
```bash
poetry run python examples/config_demo.py
```

2. **Check Health Endpoints**
```bash
# Start the application
poetry run python src/main.py

# Test health endpoint
curl http://localhost:8000/health
```

3. **Validate Environment Detection**
```bash
# Test different environments
PROMPTCRAFT_ENVIRONMENT=staging poetry run python examples/config_demo.py
```

## Rollback Plan

If you need to rollback:

1. Keep your old configuration files
2. Use feature flags to switch between old and new config:

```python
USE_NEW_CONFIG = os.getenv("USE_NEW_CONFIG", "false") == "true"

if USE_NEW_CONFIG:
    from src.config import get_settings
    settings = get_settings()
else:
    # Use old configuration approach
    import old_config as settings
```

## Benefits After Migration

- **Type Safety**: Catch configuration errors at startup
- **Better Validation**: Clear error messages with suggestions
- **Security**: Automatic secret protection
- **Monitoring**: Health check endpoints for operations
- **Environment Management**: Easy switching between dev/staging/prod
- **Documentation**: Auto-generated config documentation from types

## Next Steps

1. Review the [Usage Guide](./usage-guide.md) for detailed information
2. Explore [Security Best Practices](./security-best-practices.md)
3. Set up encrypted configuration files for production
4. Integrate health checks with your monitoring system
