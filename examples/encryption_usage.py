#!/usr/bin/env python3
"""Example usage of the encryption integration in PromptCraft-Hybrid.

This example demonstrates how to use the encryption features in practice,
including setting up encrypted environment files and using SecretStr fields.
"""



# Example of how to set up environment variables with secrets
def setup_example_environment():
    """Example of setting up environment variables with secrets."""

    # Example environment variables (these would normally be in .env files)
    example_env_vars = {
        # Basic application config (non-sensitive)
        "PROMPTCRAFT_APP_NAME": "PromptCraft-Production",
        "PROMPTCRAFT_ENVIRONMENT": "prod",
        "PROMPTCRAFT_DEBUG": "false",
        "PROMPTCRAFT_API_HOST": "0.0.0.0",
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

    return example_env_vars


def create_example_env_files():
    """Create example .env files showing the structure."""

    # Base .env file (non-sensitive settings)
    base_env_content = """# Base Environment Configuration
# ==============================
# This file contains non-sensitive base settings.

# Application Configuration
PROMPTCRAFT_APP_NAME=PromptCraft-Hybrid
PROMPTCRAFT_VERSION=0.1.0
PROMPTCRAFT_DEBUG=false

# API Server Configuration
PROMPTCRAFT_API_HOST=0.0.0.0
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

    print("Example .env file structure:")
    print("=" * 50)
    print()
    print("📁 .env (base, non-sensitive)")
    print("-" * 30)
    print(base_env_content)

    print("📁 .env.prod.gpg (production, encrypted)")
    print("-" * 40)
    print("# This would be encrypted content:")
    print(prod_env_content)


def demonstrate_settings_usage():
    """Demonstrate how to use the settings in application code."""

    print("💻 Application Usage Examples")
    print("=" * 50)

    # This would normally import from the actual module
    example_code = """
from src.config.settings import get_settings

# Get application settings
settings = get_settings()

# Basic configuration (safe to log)
print(f"Running {settings.app_name} v{settings.version}")
print(f"Environment: {settings.environment}")
print(f"Debug mode: {settings.debug}")
print(f"API server: {settings.api_host}:{settings.api_port}")

# Using secret values (never logged directly)
if settings.database_password:
    # Use the secret value for database connection
    db_password = settings.database_password.get_secret_value()
    # Connect to database using db_password
    print("Database password available (value hidden)")

if settings.api_key:
    # Use API key for external service calls
    api_key = settings.api_key.get_secret_value()
    # Make API calls using api_key
    print("API key available (value hidden)")

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

    print("✓ All required production secrets are configured")
"""

    print("Example application code:")
    print(example_code)


def demonstrate_encryption_workflow():
    """Demonstrate the encryption workflow for production deployment."""

    print("🔐 Encryption Workflow for Production")
    print("=" * 50)

    workflow_steps = [
        "1. Create .env.prod file with sensitive values",
        "2. Encrypt the file: gpg --encrypt --recipient <key-id> .env.prod",
        "3. Save as .env.prod.gpg",
        "4. Delete the plain .env.prod file",
        "5. Deploy .env.prod.gpg to production server",
        "6. Ensure GPG keys are available on production server",
        "7. Application automatically decrypts and loads secrets",
    ]

    print("Production deployment workflow:")
    for step in workflow_steps:
        print(f"  {step}")

    print()
    print("Security benefits:")
    print("  ✓ Secrets are encrypted at rest")
    print("  ✓ Only authorized users can decrypt")
    print("  ✓ Safe to store in version control (encrypted)")
    print("  ✓ Audit trail of who can access secrets")
    print("  ✓ Development works without encryption setup")


def demonstrate_development_setup():
    """Demonstrate development environment setup."""

    print("🛠️  Development Environment Setup")
    print("=" * 50)

    dev_steps = [
        "1. Create .env.dev file with development values",
        "2. Use non-sensitive default values for development",
        "3. Optionally set up encryption for testing production features",
        "4. Override specific values with environment variables as needed",
    ]

    print("Development setup steps:")
    for step in dev_steps:
        print(f"  {step}")

    print()
    print("Development benefits:")
    print("  ✓ No encryption setup required for basic development")
    print("  ✓ Easy to override values for testing")
    print("  ✓ Clear separation of dev/staging/prod configurations")
    print("  ✓ Can test encryption features when needed")


if __name__ == "__main__":
    print("🎯 PromptCraft Encryption Integration Usage Examples")
    print("=" * 60)
    print()

    try:
        create_example_env_files()
        print()
        demonstrate_settings_usage()
        print()
        demonstrate_encryption_workflow()
        print()
        demonstrate_development_setup()

        print()
        print("🎉 Encryption integration is ready for use!")
        print()
        print("Next steps:")
        print("  1. Set up GPG keys for encryption (production)")
        print("  2. Create environment-specific .env files")
        print("  3. Encrypt sensitive .env files with GPG")
        print("  4. Update application code to use get_settings()")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback

        traceback.print_exc()
