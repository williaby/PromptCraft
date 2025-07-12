#!/usr/bin/env python3
"""Example usage of the encryption integration in PromptCraft-Hybrid.

This example demonstrates how to use the encryption features in practice,
including setting up encrypted environment files and using SecretStr fields.
"""

import logging


# Example of how to set up environment variables with secrets
def setup_example_environment() -> dict[str, str]:
    """Example of setting up environment variables with secrets."""
    # Example environment variables (these would normally be in .env files)
    return {
        # Basic application config (non-sensitive)
        "PROMPTCRAFT_APP_NAME": "PromptCraft-Production",
        "PROMPTCRAFT_ENVIRONMENT": "prod",
        "PROMPTCRAFT_DEBUG": "false",
        "PROMPTCRAFT_API_HOST": "127.0.0.1",  # Use localhost instead of 0.0.0.0
        "PROMPTCRAFT_API_PORT": "8000",
        # Sensitive configuration (should be in encrypted files)
        "PROMPTCRAFT_DATABASE_PASSWORD": "super-secret-db-password-123",
        "PROMPTCRAFT_DATABASE_URL": "postgresql://user:pass@localhost:5432/promptcraft",
        "PROMPTCRAFT_API_KEY": "sk-1234567890abcdef1234567890abcdef",
        "PROMPTCRAFT_SECRET_KEY": "your-secret-signing-key-here",
        "PROMPTCRAFT_AZURE_OPENAI_API_KEY": "abcd1234567890efgh1234567890ijkl",
        "PROMPTCRAFT_JWT_SECRET_KEY": "jwt-signing-secret-key-here",
        "PROMPTCRAFT_QDRANT_API_KEY": "qdrant-vector-db-api-key",
        "PROMPTCRAFT_ENCRYPTION_KEY": "encryption-key-for-data-at-rest",
    }


def create_example_env_files() -> None:
    """Create example .env files showing the structure."""
    logger = logging.getLogger(__name__)

    # Base .env file (non-sensitive settings)
    base_env_content = """# Base Environment Configuration
# ==============================
# This file contains non-sensitive base settings.

# Application Configuration
PROMPTCRAFT_APP_NAME=PromptCraft-Hybrid
PROMPTCRAFT_VERSION=0.1.0
PROMPTCRAFT_DEBUG=false

# API Server Configuration
PROMPTCRAFT_API_HOST=127.0.0.1
PROMPTCRAFT_API_PORT=8000
"""

    # Production .env file (would be encrypted as .env.prod.gpg)
    prod_env_content = """# Production Environment Configuration (ENCRYPTED)
# =================================================
# This file should be encrypted as .env.prod.gpg

# Application Configuration
PROMPTCRAFT_APP_NAME=PromptCraft-Production
PROMPTCRAFT_ENVIRONMENT=prod
PROMPTCRAFT_DEBUG=false

# Sensitive Database Configuration
PROMPTCRAFT_DATABASE_PASSWORD=super-secret-db-password-123
PROMPTCRAFT_DATABASE_URL=postgresql://user:pass@prod-server:5432/promptcraft

# API Keys and Secrets
PROMPTCRAFT_API_KEY=sk-1234567890abcdef1234567890abcdef
PROMPTCRAFT_SECRET_KEY=your-secret-signing-key-here
PROMPTCRAFT_AZURE_OPENAI_API_KEY=abcd1234567890efgh1234567890ijkl
PROMPTCRAFT_JWT_SECRET_KEY=jwt-signing-secret-key-here
PROMPTCRAFT_QDRANT_API_KEY=qdrant-vector-db-api-key
PROMPTCRAFT_ENCRYPTION_KEY=encryption-key-for-data-at-rest
"""

    logger.info("Example .env file structure:")
    logger.info("=" * 50)
    logger.info("")
    logger.info("📁 .env (base, non-sensitive)")
    logger.info("-" * 30)
    logger.info(base_env_content)

    logger.info("📁 .env.prod.gpg (production, encrypted)")
    logger.info("-" * 40)
    logger.info("# This would be encrypted content:")
    logger.info(prod_env_content)


def demonstrate_settings_usage() -> None:
    """Demonstrate how to use the settings in application code."""
    logger = logging.getLogger(__name__)

    logger.info("💻 Application Usage Examples")
    logger.info("=" * 50)

    # This would normally import from the actual module
    example_code = """
from src.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

# Basic configuration (safe to log)
logger.info("Running %s v%s", settings.app_name, settings.version)
logger.info("Environment: %s", settings.environment)
logger.info("Debug mode: %s", settings.debug)
logger.info("API server: %s:%s", settings.api_host, settings.api_port)

# Using secret values (never logged directly)
if settings.database_password:
    # Use the secret value for database connection
    db_password = settings.database_password.get_secret_value()
    # Connect to database using db_password
    logger.info("Database password available (value hidden)")

if settings.api_key:
    # Use API key for external service calls
    api_key = settings.api_key.get_secret_value()
    # Make API calls using api_key
    logger.info("API key available (value hidden)")

# Configuration validation
if settings.environment == "prod":
    # Ensure all required secrets are present in production
    required_secrets = [
        settings.database_password,
        settings.api_key,
        settings.secret_key,
    ]

    if not all(required_secrets):
        raise ValueError("Missing required secrets in production environment")

    logger.info("✓ All required production secrets are configured")
"""

    logger.info("Example application code:")
    logger.info(example_code)


def demonstrate_encryption_workflow() -> None:
    """Demonstrate the encryption workflow for production deployment."""
    logger = logging.getLogger(__name__)

    logger.info("🔐 Encryption Workflow for Production")
    logger.info("=" * 50)

    workflow_steps = [
        "1. Create .env.prod file with sensitive values",
        "2. Encrypt the file: gpg --encrypt --recipient <key-id> .env.prod",
        "3. Save as .env.prod.gpg",
        "4. Delete the plain .env.prod file",
        "5. Deploy .env.prod.gpg to production server",
        "6. Ensure GPG keys are available on production server",
        "7. Application automatically decrypts and loads secrets",
    ]

    logger.info("Production deployment workflow:")
    for step in workflow_steps:
        logger.info("  %s", step)

    logger.info("")
    logger.info("Security benefits:")
    logger.info("  ✓ Secrets are encrypted at rest")
    logger.info("  ✓ Only authorized users can decrypt")
    logger.info("  ✓ Safe to store in version control (encrypted)")
    logger.info("  ✓ Audit trail of who can access secrets")
    logger.info("  ✓ Development works without encryption setup")


def demonstrate_development_setup() -> None:
    """Demonstrate development environment setup."""
    logger = logging.getLogger(__name__)

    logger.info("🛠️  Development Environment Setup")
    logger.info("=" * 50)

    dev_steps = [
        "1. Create .env.dev file with development values",
        "2. Use non-sensitive default values for development",
        "3. Optionally set up encryption for testing production features",
        "4. Override specific values with environment variables as needed",
    ]

    logger.info("Development setup steps:")
    for step in dev_steps:
        logger.info("  %s", step)

    logger.info("")
    logger.info("Development benefits:")
    logger.info("  ✓ No encryption setup required for basic development")
    logger.info("  ✓ Easy to override values for testing")
    logger.info("  ✓ Clear separation of dev/staging/prod configurations")
    logger.info("  ✓ Can test encryption features when needed")


if __name__ == "__main__":
    # Set up logging for the example
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("🎯 PromptCraft Encryption Integration Usage Examples")
    logger.info("=" * 60)
    logger.info("")

    try:
        create_example_env_files()
        logger.info("")
        demonstrate_settings_usage()
        logger.info("")
        demonstrate_encryption_workflow()
        logger.info("")
        demonstrate_development_setup()

        logger.info("")
        logger.info("🎉 Encryption integration is ready for use!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Set up GPG keys for encryption (production)")
        logger.info("  2. Create environment-specific .env files")
        logger.info("  3. Encrypt sensitive .env files with GPG")
        logger.info("  4. Update application code to use get_settings()")

    except Exception as e:
        logger.error("❌ Example failed: %s", e)
        import traceback

        traceback.print_exc()
