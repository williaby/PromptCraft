# Configuration System Examples

This directory contains example scripts demonstrating the PromptCraft Configuration System features.

## Available Examples

### 1. `config_demo.py` - Basic Configuration Usage
Demonstrates the core configuration system features:
- Loading environment-specific settings
- Accessing configuration values
- Environment detection and behavior

**Run:**
```bash
poetry run python examples/config_demo.py
```

### 2. `encryption_usage.py` - Encryption Integration
Shows how to work with encrypted configuration files:
- Setting up encrypted .env files
- Using SecretStr fields
- Production encryption workflow
- Development setup without encryption

**Run:**
```bash
poetry run python examples/encryption_usage.py
```

### 3. `health_check_demo.py` - Health Monitoring
Demonstrates the health check features:
- Configuration status monitoring
- Health check endpoints
- Security features (no secret exposure)
- JSON serialization for APIs

**Run:**
```bash
poetry run python examples/health_check_demo.py
```

## Running with Different Environments

You can test different environments by setting the `PROMPTCRAFT_ENVIRONMENT` variable:

```bash
# Development environment (default)
poetry run python examples/config_demo.py

# Staging environment
PROMPTCRAFT_ENVIRONMENT=staging poetry run python examples/config_demo.py

# Production environment
PROMPTCRAFT_ENVIRONMENT=prod poetry run python examples/config_demo.py
```

## Testing with Custom Settings

Override specific settings using environment variables:

```bash
# Custom API port
PROMPTCRAFT_API_PORT=9000 poetry run python examples/config_demo.py

# Debug mode off
PROMPTCRAFT_DEBUG=false poetry run python examples/config_demo.py
```

## Live Server Testing

To test health endpoints with a running server:

1. Start the server:
```bash
poetry run python src/main.py
```

2. In another terminal, run the health check demo:
```bash
poetry run python examples/health_check_demo.py
```

The demo will detect the live server and show actual endpoint responses.

## Security Notes

- Never commit real secrets in example files
- Use placeholder values for demonstration
- The examples show security best practices
- Production secrets should always be encrypted

## Prerequisites

Ensure you have the project dependencies installed:

```bash
poetry install
```

For encryption examples, you'll need GPG installed:
```bash
# Ubuntu/Debian
sudo apt-get install gnupg

# macOS
brew install gnupg
```
