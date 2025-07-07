#!/usr/bin/env python3
"""
Demonstration script for Phase 4 Enhanced Validation & Error Handling.

This script demonstrates the comprehensive validation features implemented
in the Core Configuration System Phase 4.
"""

import logging

from src.config.settings import (
    ApplicationSettings,
    ConfigurationValidationError,
    validate_configuration_on_startup,
)
from src.utils.setup_validator import validate_startup_configuration


def demo_enhanced_field_validation():
    """Demonstrate enhanced field validation with detailed error messages."""
    print("=" * 60)
    print("DEMO: Enhanced Field Validation")
    print("=" * 60)

    # 1. Port validation
    print("\n1. Testing port validation...")
    try:
        ApplicationSettings(api_port=70000)
    except Exception as e:
        print("✓ Invalid port rejected with detailed message:")
        print(f"  {e}")

    # 2. Host validation
    print("\n2. Testing host validation...")
    try:
        ApplicationSettings(api_host="invalid@host!")
    except Exception as e:
        print("✓ Invalid host rejected with detailed message:")
        print(f"  {e}")

    # 3. Version validation
    print("\n3. Testing version validation...")
    try:
        ApplicationSettings(version="not-a-version")
    except Exception as e:
        print("✓ Invalid version rejected with semantic versioning guidance:")
        print(f"  {e}")

    # 4. App name validation
    print("\n4. Testing app name validation...")
    try:
        ApplicationSettings(app_name="x" * 101)  # Too long
    except Exception as e:
        print("✓ Long app name rejected with length guidance:")
        print(f"  {e}")

    # 5. Secret validation
    print("\n5. Testing secret validation...")
    try:
        ApplicationSettings(api_key="")  # Empty secret
    except Exception as e:
        print("✓ Empty secret rejected with guidance:")
        print(f"  {e}")


def demo_environment_specific_validation():
    """Demonstrate environment-specific validation requirements."""
    print("\n" + "=" * 60)
    print("DEMO: Environment-Specific Validation")
    print("=" * 60)

    # Production environment validation
    print("\n1. Testing production environment validation...")
    try:
        settings = ApplicationSettings(
            environment="prod",
            debug=True,  # Should be False in prod
            api_host="localhost",  # Should not be localhost in prod
        )
        validate_configuration_on_startup(settings)
    except ConfigurationValidationError as e:
        print("✓ Production issues caught:")
        print(f"  {e}")

    # Development environment (should be more lenient)
    print("\n2. Testing development environment validation...")
    try:
        settings = ApplicationSettings(
            environment="dev",
            debug=True,
            api_host="localhost",
        )
        validate_configuration_on_startup(settings)
        print("✓ Development configuration accepted")
    except Exception as e:
        print(f"✗ Development validation failed: {e}")


def demo_startup_validation():
    """Demonstrate comprehensive startup validation."""
    print("\n" + "=" * 60)
    print("DEMO: Comprehensive Startup Validation")
    print("=" * 60)

    # Configure logging to see validation process
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    print("\n1. Testing system requirements validation...")
    print("   (Note: May show Python version warning if not 3.11+)")

    print("\n2. Running comprehensive startup validation...")
    try:
        # This will validate system, environment, and configuration
        success = validate_startup_configuration()
        if success:
            print("✓ All startup validation checks passed!")
        else:
            print("✗ Some startup validation checks failed (see logs above)")
    except Exception as e:
        print(f"✗ Startup validation error: {e}")


def demo_custom_error_formatting():
    """Demonstrate custom error class with detailed formatting."""
    print("\n" + "=" * 60)
    print("DEMO: Custom Error Formatting")
    print("=" * 60)

    # Create a custom error with all components
    field_errors = [
        "Port 70000 is outside valid range (1-65535)",
        "Host 'invalid@host' contains illegal characters",
        "Secret 'api_key' cannot be empty",
    ]

    suggestions = [
        "Use port 8000 for development or 80/443 for production",
        "Use a valid hostname like 'localhost' or IP address like '127.0.0.1'",
        "Set PROMPTCRAFT_API_KEY environment variable with a valid API key",
    ]

    error = ConfigurationValidationError(
        "Configuration validation failed with multiple issues",
        field_errors=field_errors,
        suggestions=suggestions,
    )

    print("✓ Custom error with detailed formatting:")
    print(error)


def demo_logging_integration():
    """Demonstrate logging integration and secret masking."""
    print("\n" + "=" * 60)
    print("DEMO: Logging Integration & Secret Masking")
    print("=" * 60)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        force=True,
    )

    print("\n1. Testing configuration loading with logging...")

    # Create settings with some secrets
    settings = ApplicationSettings(
        api_key="secret-api-key-12345",
        secret_key="super-secret-jwt-key",
        environment="dev",
    )

    print("\n2. Validating configuration (watch for secret masking)...")
    validate_configuration_on_startup(settings)

    print("\n✓ Notice that secret values are never exposed in logs!")


if __name__ == "__main__":
    print("Phase 4 Enhanced Validation & Error Handling Demonstration")
    print("This demo shows the comprehensive validation features implemented.")

    try:
        demo_enhanced_field_validation()
        demo_environment_specific_validation()
        demo_custom_error_formatting()
        demo_logging_integration()
        demo_startup_validation()

        print("\n" + "=" * 60)
        print("DEMO COMPLETE: All validation features demonstrated successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
