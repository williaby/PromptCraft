"""Core application settings using Pydantic BaseSettings.

This module defines the core configuration schema for the PromptCraft-Hybrid application.
It provides type-safe configuration with validation and environment-specific loading.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..utils.encryption import (
    EncryptionError,
    GPGError,
    load_encrypted_env,
    validate_environment_keys,
)


def _get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path object pointing to the project root directory.
    """
    current_file = Path(__file__).resolve()
    # Navigate up from src/config/settings.py to project root
    return current_file.parent.parent.parent


def _detect_environment() -> str:
    """Detect the current environment from environment variables or .env files.

    Returns:
        The detected environment string (dev, staging, or prod).
        Defaults to 'dev' if no environment is detected.
    """
    # First check environment variable
    env_from_var = os.getenv("PROMPTCRAFT_ENVIRONMENT")
    if env_from_var and env_from_var in ("dev", "staging", "prod"):
        return env_from_var

    # Then check .env file if it exists
    project_root = _get_project_root()
    env_file = project_root / ".env"

    if env_file.exists():
        try:
            with env_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("PROMPTCRAFT_ENVIRONMENT="):
                        env_value = line.split("=", 1)[1].strip().strip("\"'")
                        if env_value in ("dev", "staging", "prod"):
                            return env_value
        except (OSError, UnicodeDecodeError):
            # If we can't read the file, fall back to default
            pass

    # Default to development environment
    return "dev"


def _load_env_file(file_path: Path) -> dict[str, Any]:
    """Load environment variables from a .env file.

    Args:
        file_path: Path to the .env file to load.

    Returns:
        Dictionary of environment variables from the file.
    """
    env_vars: dict[str, Any] = {}

    if not file_path.exists():
        return env_vars

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE format
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")  # Remove quotes

                    # Only load variables with PROMPTCRAFT_ prefix
                    if key.startswith("PROMPTCRAFT_"):
                        # Remove prefix for Pydantic
                        pydantic_key = key[len("PROMPTCRAFT_") :].lower()
                        env_vars[pydantic_key] = value

    except (OSError, UnicodeDecodeError) as e:
        # Log warning but don't fail - graceful degradation
        print(f"Warning: Could not read {file_path}: {e}")

    return env_vars


def _load_encrypted_env_file(file_path: Path) -> dict[str, Any]:
    """Load environment variables from an encrypted .env file.

    Args:
        file_path: Path to the encrypted .env file to load.

    Returns:
        Dictionary of environment variables from the encrypted file.
    """
    env_vars: dict[str, Any] = {}

    if not file_path.exists():
        return env_vars

    try:
        # Use the encryption utility to load encrypted env file
        raw_env_vars = load_encrypted_env(str(file_path))

        # Process variables with PROMPTCRAFT_ prefix
        for key, value in raw_env_vars.items():
            if key.startswith("PROMPTCRAFT_"):
                # Remove prefix for Pydantic
                pydantic_key = key[len("PROMPTCRAFT_") :].lower()
                env_vars[pydantic_key] = value

    except (FileNotFoundError, GPGError) as e:
        # Log warning but don't fail - graceful degradation
        print(f"Warning: Could not load encrypted file {file_path}: {e}")

    return env_vars


def _env_file_settings() -> dict[str, Any]:
    """Custom settings source for environment-specific .env file loading.

    This function implements the secure file loading hierarchy:
    1. .env.{environment}.gpg file (encrypted, highest priority)
    2. .env.{environment} file (fallback for development)
    3. .env.gpg file (encrypted base file)
    4. .env file (fallback base file)

    Returns:
        Dictionary of configuration values from .env files.
    """
    project_root = _get_project_root()
    env_vars: dict[str, Any] = {}

    # Detect current environment
    current_env = _detect_environment()

    # Load base .env file first (lowest priority)
    base_env_file = project_root / ".env"
    env_vars.update(_load_env_file(base_env_file))

    # Try to load encrypted base .env file (higher priority)
    base_encrypted_file = project_root / ".env.gpg"
    env_vars.update(_load_encrypted_env_file(base_encrypted_file))

    # Load environment-specific .env file (higher priority)
    env_specific_file = project_root / f".env.{current_env}"
    env_vars.update(_load_env_file(env_specific_file))

    # Try to load encrypted environment-specific file (highest priority)
    env_encrypted_file = project_root / f".env.{current_env}.gpg"
    env_vars.update(_load_encrypted_env_file(env_encrypted_file))

    return env_vars


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails with detailed error information."""

    def __init__(
        self,
        message: str,
        field_errors: list[str] | None = None,
        suggestions: list[str] | None = None,
    ):
        """Initialize configuration validation error.

        Args:
            message: The main error message
            field_errors: List of specific field validation errors
            suggestions: List of suggested fixes or valid values
        """
        super().__init__(message)
        self.field_errors = field_errors or []
        self.suggestions = suggestions or []

    def __str__(self) -> str:
        """Return formatted error message with all details."""
        parts = [super().__str__()]

        if self.field_errors:
            parts.append("\nField Validation Errors:")
            for error in self.field_errors:
                parts.append(f"  • {error}")

        if self.suggestions:
            parts.append("\nSuggestions:")
            for suggestion in self.suggestions:
                parts.append(f"  • {suggestion}")

        return "\n".join(parts)


class ApplicationSettings(BaseSettings):
    """Core application configuration settings.

    This class defines the base configuration schema for the PromptCraft-Hybrid
    application. It uses Pydantic BaseSettings for environment variable loading
    and validation with environment-specific .env file support.

    Attributes:
        app_name: The application name for logging and identification.
        version: The application version string.
        environment: The deployment environment (dev, staging, prod).
        debug: Whether debug mode is enabled.
        api_host: The host address for the API server.
        api_port: The port number for the API server.
    """

    app_name: str = Field(
        default="PromptCraft-Hybrid",
        description="Application name for logging and identification",
    )

    version: str = Field(
        default="0.1.0",
        description="Application version string",
    )

    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        description="Deployment environment (dev, staging, prod)",
    )

    debug: bool = Field(
        default=True,
        description="Whether debug mode is enabled",
    )

    api_host: str = Field(
        default="0.0.0.0",  # noqa: S104
        description="Host address for the API server",
    )

    api_port: int = Field(
        default=8000,
        description="Port number for the API server",
    )

    # Database Configuration (sensitive values)
    database_password: SecretStr | None = Field(
        default=None,
        description="Database password (sensitive - never logged)",
    )

    database_url: SecretStr | None = Field(
        default=None,
        description="Complete database connection URL (sensitive - never logged)",
    )

    # API Keys and Secrets (sensitive values)
    api_key: SecretStr | None = Field(
        default=None,
        description="Primary API key for external services (sensitive - never logged)",
    )

    secret_key: SecretStr | None = Field(
        default=None,
        description="Application secret key for encryption/signing (sensitive - never logged)",
    )

    azure_openai_api_key: SecretStr | None = Field(
        default=None,
        description="Azure OpenAI API key (sensitive - never logged)",
    )

    # JWT and Authentication Secrets
    jwt_secret_key: SecretStr | None = Field(
        default=None,
        description="JWT signing secret key (sensitive - never logged)",
    )

    # External Service Configuration
    qdrant_api_key: SecretStr | None = Field(
        default=None,
        description="Qdrant vector database API key (sensitive - never logged)",
    )

    encryption_key: SecretStr | None = Field(
        default=None,
        description="Encryption key for data at rest (sensitive - never logged)",
    )

    model_config = SettingsConfigDict(
        extra="forbid",  # Prevent unknown settings
        case_sensitive=False,
        env_prefix="PROMPTCRAFT_",
    )

    @field_validator("api_host")
    @classmethod
    def validate_api_host(cls, v: str) -> str:
        """Validate the API host address with detailed error messages.

        Args:
            v: The host address to validate.

        Returns:
            The validated host address.

        Raises:
            ValueError: If the host address is invalid with detailed guidance.
        """
        if not v.strip():
            raise ValueError(
                "API host cannot be empty. "
                "Common values: '0.0.0.0' (all interfaces), 'localhost' (local only), "
                "'127.0.0.1' (loopback), or a valid IP address/hostname.",
            )

        v = v.strip()

        # Check for valid IP address format
        ip_pattern = re.compile(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        )

        # Check for valid hostname format
        hostname_pattern = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)$",
        )

        # Allow common special cases
        if v in ("0.0.0.0", "localhost", "127.0.0.1"):  # noqa: S104
            return v

        # Validate IP address format
        if ip_pattern.match(v):
            return v

        # Validate hostname format
        if hostname_pattern.match(v) and len(v) <= 253:
            return v

        # If none match, provide detailed error
        raise ValueError(
            f"Invalid API host format: '{v}'. "
            "Host must be a valid IP address (e.g., '192.168.1.100'), "
            "hostname (e.g., 'api.example.com'), or special value "
            "('0.0.0.0', 'localhost', '127.0.0.1').",
        )

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string with semantic version checking.

        Args:
            v: The version string to validate.

        Returns:
            The validated version string.

        Raises:
            ValueError: If the version string is invalid with guidance.
        """
        if not v.strip():
            raise ValueError(
                "Version cannot be empty. "
                "Use semantic versioning format: 'MAJOR.MINOR.PATCH' (e.g., '1.0.0', '0.1.0').",
            )

        v = v.strip()

        # Check for semantic version format (flexible)
        semver_pattern = re.compile(
            r"^\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$",
        )

        if not semver_pattern.match(v):
            raise ValueError(
                f"Invalid version format: '{v}'. "
                "Use semantic versioning: 'MAJOR.MINOR.PATCH' (e.g., '1.0.0'), "
                "'MAJOR.MINOR' (e.g., '1.0'), or include pre-release/build metadata "
                "(e.g., '1.0.0-alpha', '1.0.0+build.1').",
            )

        return v

    @field_validator("app_name")
    @classmethod
    def validate_app_name(cls, v: str) -> str:
        """Validate the application name with format requirements.

        Args:
            v: The application name to validate.

        Returns:
            The validated application name.

        Raises:
            ValueError: If the application name is invalid with guidance.
        """
        if not v.strip():
            raise ValueError(
                "Application name cannot be empty. "
                "Use a descriptive name like 'PromptCraft-Hybrid', 'MyApp', or 'API-Service'.",
            )

        v = v.strip()

        # Check length constraints
        if len(v) > 100:
            raise ValueError(
                f"Application name too long ({len(v)} characters). "
                "Maximum length is 100 characters for logging and identification purposes.",
            )

        # Check for reasonable characters (allow spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9._\s-]+$", v):
            raise ValueError(
                f"Invalid application name: '{v}'. "
                "Name should contain only letters, numbers, spaces, hyphens, "
                "underscores, and periods.",
            )

        return v

    @field_validator("api_port")
    @classmethod
    def validate_api_port_detailed(cls, v: int) -> int:
        """Enhanced port validation with detailed error messages.

        Args:
            v: The port number to validate.

        Returns:
            The validated port number.

        Raises:
            ValueError: If the port is invalid with suggested alternatives.
        """
        if not (1 <= v <= 65535):
            raise ValueError(
                f"Port {v} is outside valid range. "
                "Ports must be between 1-65535. "
                "Common choices: 8000 (development), 80 (HTTP), 443 (HTTPS), "
                "3000 (Node.js), 5000 (Flask), 8080 (alternative HTTP).",
            )

        # Warn about privileged ports in development
        if v < 1024:
            # This is just informational, not an error
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Using privileged port {v} (< 1024). "
                "This may require root privileges. "
                "Consider using ports 8000+ for development.",
            )

        return v

    @field_validator("environment")
    @classmethod
    def validate_environment_requirements(cls, v: str) -> str:
        """Validate environment with specific requirements per environment.

        Args:
            v: The environment value to validate.

        Returns:
            The validated environment value.

        Raises:
            ValueError: If environment-specific requirements are not met.
        """
        if v not in ("dev", "staging", "prod"):
            raise ValueError(
                f"Invalid environment: '{v}'. "
                "Valid environments: 'dev' (development), 'staging' (pre-production), "
                "'prod' (production).",
            )

        # Note: Cross-field validation (like checking debug mode based on environment)
        # will be handled in the startup validation function instead of here
        # since Pydantic v2 changed how cross-field validation works

        return v

    @field_validator(
        "database_password",
        "database_url",
        "api_key",
        "secret_key",
        "azure_openai_api_key",
        "jwt_secret_key",
        "qdrant_api_key",
        "encryption_key",
    )
    @classmethod
    def validate_secret_not_empty(cls, v: SecretStr | None) -> SecretStr | None:
        """Validate that secret values are not empty strings.

        Args:
            v: The secret value to validate.

        Returns:
            The validated secret value.

        Raises:
            ValueError: If the secret is an empty string.
        """
        if v is not None and not v.get_secret_value().strip():
            raise ValueError(
                "Secret values cannot be empty strings. "
                "Provide a valid secret value or leave unset for optional secrets.",
            )

        return v


# Global settings instance for singleton pattern
_settings: ApplicationSettings | None = None

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def validate_encryption_available() -> bool:
    """Check if encryption is available and properly configured.

    Returns:
        True if encryption is available, False otherwise.
    """
    try:
        validate_environment_keys()
        return True
    except EncryptionError:
        return False


def _mask_secret_value(value: str, show_chars: int = 4) -> str:
    """Mask a secret value for safe logging.

    Args:
        value: The secret value to mask
        show_chars: Number of characters to show at the end

    Returns:
        Masked value safe for logging
    """
    if len(value) <= show_chars:
        return "*" * len(value)
    return "*" * (len(value) - show_chars) + value[-show_chars:]


def _log_configuration_status(settings: ApplicationSettings) -> None:
    """Log configuration loading status without exposing sensitive data.

    Args:
        settings: The loaded settings instance to log
    """
    logger = logging.getLogger(__name__)

    # Log basic configuration
    logger.info(f"Configuration loaded for environment: {settings.environment}")
    logger.info(f"Application: {settings.app_name} v{settings.version}")
    logger.info(f"API server: {settings.api_host}:{settings.api_port}")
    logger.info(f"Debug mode: {settings.debug}")

    # Log secret field status (without values)
    secret_fields = {
        "database_password": settings.database_password,
        "database_url": settings.database_url,
        "api_key": settings.api_key,
        "secret_key": settings.secret_key,
        "azure_openai_api_key": settings.azure_openai_api_key,
        "jwt_secret_key": settings.jwt_secret_key,
        "qdrant_api_key": settings.qdrant_api_key,
        "encryption_key": settings.encryption_key,
    }

    configured_secrets = []
    missing_secrets = []

    for field_name, value in secret_fields.items():
        if value is not None and value.get_secret_value().strip():
            configured_secrets.append(field_name)
        else:
            missing_secrets.append(field_name)

    if configured_secrets:
        logger.info(f"Configured secrets: {', '.join(configured_secrets)}")

    if missing_secrets:
        if settings.environment == "prod":
            logger.warning(
                f"Missing secrets in production: {', '.join(missing_secrets)}",
            )
        else:
            logger.debug(
                f"Optional secrets not configured: {', '.join(missing_secrets)}",
            )


def validate_configuration_on_startup(settings: ApplicationSettings) -> None:
    """Perform comprehensive configuration validation on application startup.

    This function validates the entire configuration and provides detailed
    error reporting with actionable suggestions for fixing issues.

    Args:
        settings: The settings instance to validate

    Raises:
        ConfigurationValidationError: If validation fails with detailed errors
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting configuration validation...")

    validation_errors = []
    suggestions = []

    # Environment-specific validation
    if settings.environment == "prod":
        # Production-specific requirements
        if settings.debug:
            validation_errors.append("Debug mode should be disabled in production")
            suggestions.append("Set PROMPTCRAFT_DEBUG=false for production deployment")

        # Check for required secrets in production
        required_secrets_prod = ["secret_key", "jwt_secret_key"]
        for secret_name in required_secrets_prod:
            secret_value = getattr(settings, secret_name, None)
            if not secret_value or not secret_value.get_secret_value().strip():
                validation_errors.append(
                    f"Required secret '{secret_name}' is missing in production",
                )
                suggestions.append(
                    f"Set PROMPTCRAFT_{secret_name.upper()} environment variable",
                )

        # Validate production-appropriate host binding
        if settings.api_host in ("127.0.0.1", "localhost"):
            validation_errors.append(
                "Production API host should not be localhost/127.0.0.1",
            )
            suggestions.append(
                "Use '0.0.0.0' to bind to all interfaces or specify production host",
            )

    elif settings.environment == "staging":
        # Staging-specific validation
        if (
            not settings.secret_key
            or not settings.secret_key.get_secret_value().strip()
        ):
            validation_errors.append(
                "Secret key should be configured in staging environment",
            )
            suggestions.append("Set PROMPTCRAFT_SECRET_KEY for staging testing")

    # General security validation
    if settings.api_port == 80 or settings.api_port == 443:
        if settings.environment != "prod":
            validation_errors.append(
                f"Using standard web port {settings.api_port} in {settings.environment} environment",
            )
            suggestions.append(
                "Consider using development ports like 8000, 3000, or 5000",
            )

    # Validate host/port combination makes sense
    if (
        settings.api_host == "0.0.0.0"
        and settings.environment == "dev"
        and settings.api_port < 1024
    ):
        validation_errors.append(
            "Binding to all interfaces with privileged port in development",
        )
        suggestions.append("Use 'localhost' host or port >= 1024 for development")

    # Cross-field validation
    if settings.database_url and settings.database_password:
        logger.warning(
            "Both database_url and database_password are set. URL typically includes password.",
        )

    # Encryption availability check
    encryption_available = validate_encryption_available()
    if settings.environment == "prod" and not encryption_available:
        validation_errors.append("Encryption not available in production environment")
        suggestions.extend(
            [
                "Ensure GPG keys are properly configured",
                "Verify SSH keys are loaded for signed commits",
                "Run: poetry run python src/utils/encryption.py",
            ],
        )

    # Log validation results
    if validation_errors:
        logger.error(
            f"Configuration validation failed with {len(validation_errors)} error(s)",
        )
        raise ConfigurationValidationError(
            f"Configuration validation failed for {settings.environment} environment",
            field_errors=validation_errors,
            suggestions=suggestions,
        )
    else:
        logger.info("Configuration validation completed successfully")

    # Log configuration status for operational awareness
    _log_configuration_status(settings)


def validate_field_requirements_by_environment(environment: str) -> set[str]:
    """Get required fields for a specific environment.

    Args:
        environment: The environment to get requirements for

    Returns:
        Set of field names that are required for the environment
    """
    base_required = {"app_name", "version", "environment", "api_host", "api_port"}

    if environment == "prod":
        return base_required | {"secret_key", "jwt_secret_key"}
    elif environment == "staging":
        return base_required | {"secret_key"}
    else:  # dev
        return base_required


def get_settings(validate_on_startup: bool = True) -> ApplicationSettings:
    """Get settings instance based on current environment with comprehensive validation.

    This factory function provides a singleton pattern for application settings.
    It detects the current environment and loads configuration with the proper
    precedence hierarchy:

    1. Environment variables (highest priority)
    2. .env.{environment}.gpg file (encrypted environment-specific)
    3. .env.{environment} file (plain environment-specific)
    4. .env.gpg file (encrypted base)
    5. .env file (plain base)
    6. Pydantic field defaults (lowest priority)

    The function ensures that settings are loaded only once per application
    lifecycle and provides graceful fallback when encryption is unavailable
    during development. It also performs comprehensive validation and logging.

    Args:
        validate_on_startup: Whether to perform full startup validation (default: True)

    Returns:
        ApplicationSettings instance configured for the current environment.

    Raises:
        ConfigurationValidationError: If configuration validation fails
        ValidationError: If Pydantic field validation fails

    Example:
        >>> settings = get_settings()
        >>> print(f"Running in {settings.environment} mode on {settings.api_host}:{settings.api_port}")
        >>> # Secret values are protected
        >>> if settings.database_password:
        ...     print("Database password is configured (value hidden)")
    """
    global _settings
    logger = logging.getLogger(__name__)

    if _settings is None:
        logger.info("Initializing application configuration...")

        # Check encryption availability
        encryption_available = validate_encryption_available()
        current_env = _detect_environment()

        logger.info(f"Detected environment: {current_env}")
        logger.info(f"Encryption available: {encryption_available}")

        # Log encryption status with appropriate levels
        if current_env == "prod" and not encryption_available:
            logger.warning(
                "Production environment detected but encryption not available. "
                "Some features may be limited. Ensure GPG and SSH keys are properly configured.",
            )
        elif current_env == "dev" and not encryption_available:
            logger.info(
                "Development environment - encryption not required but recommended "
                "for testing production features.",
            )
        elif encryption_available:
            logger.info("Encryption system is properly configured and available.")

        try:
            # Load settings with enhanced error handling
            logger.debug("Loading configuration from environment and files...")
            _settings = ApplicationSettings()

            # Perform startup validation if requested
            if validate_on_startup:
                validate_configuration_on_startup(_settings)
            else:
                # Still log basic configuration info
                _log_configuration_status(_settings)

        except ValidationError as e:
            # Convert Pydantic validation errors to our enhanced format
            field_errors = []
            suggestions = []

            for error in e.errors():
                field_name = ".".join(str(loc) for loc in error["loc"])
                error_msg = error["msg"]
                field_errors.append(f"{field_name}: {error_msg}")

                # Add field-specific suggestions
                if field_name == "api_port":
                    suggestions.append(
                        "Use a port between 1-65535, common choices: 8000, 3000, 5000",
                    )
                elif field_name == "environment":
                    suggestions.append(
                        "Set PROMPTCRAFT_ENVIRONMENT to 'dev', 'staging', or 'prod'",
                    )
                elif field_name == "api_host":
                    suggestions.append(
                        "Use '0.0.0.0', 'localhost', '127.0.0.1', or a valid IP/hostname",
                    )

            raise ConfigurationValidationError(
                f"Configuration field validation failed in {current_env} environment",
                field_errors=field_errors,
                suggestions=suggestions,
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error during configuration loading: {e}")
            raise ConfigurationValidationError(
                "Unexpected configuration loading error",
                field_errors=[str(e)],
                suggestions=[
                    "Check environment variables and .env files for syntax errors",
                ],
            ) from e

        logger.info("Configuration initialization completed successfully")

    return _settings


def reload_settings(validate_on_startup: bool = True) -> ApplicationSettings:
    """Reload settings from environment and files with validation.

    This function forces a reload of settings, useful for testing or when
    environment configuration has changed during runtime.

    Args:
        validate_on_startup: Whether to perform full startup validation (default: True)

    Returns:
        Fresh ApplicationSettings instance with current configuration.

    Raises:
        ConfigurationValidationError: If configuration validation fails
    """
    global _settings
    logger = logging.getLogger(__name__)
    logger.info("Reloading configuration...")
    _settings = None
    return get_settings(validate_on_startup=validate_on_startup)
