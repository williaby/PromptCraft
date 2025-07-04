"""Health check models and utilities for configuration status monitoring.

This module implements Phase 5 of the Core Configuration System: Health Check Integration.
It provides configuration status models and utilities for exposing operational
information through health check endpoints without revealing sensitive data.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field

from .settings import (
    ApplicationSettings,
    ConfigurationValidationError,
    validate_encryption_available,
)

logger = logging.getLogger(__name__)


class ConfigurationStatusModel(BaseModel):
    """Configuration status model for health check responses.

    This model represents the current state of the application configuration
    for operational monitoring purposes. It exposes only non-sensitive
    information that is useful for debugging and system health monitoring.

    Attributes:
        environment: Current deployment environment (dev/staging/prod)
        version: Application version string
        debug: Whether debug mode is enabled
        config_loaded: Whether configuration loaded successfully
        encryption_enabled: Whether encryption is available and working
        config_source: Primary source of configuration (env_vars, files, defaults)
        validation_status: Whether configuration validation passed
        validation_errors: Non-sensitive validation error summaries
        secrets_configured: Count of configured secret fields (not values)
        timestamp: When this status was generated
    """

    environment: str = Field(
        description="Current deployment environment (dev/staging/prod)",
    )

    version: str = Field(description="Application version string")

    debug: bool = Field(description="Whether debug mode is enabled")

    config_loaded: bool = Field(description="Whether configuration loaded successfully")

    encryption_enabled: bool = Field(
        description="Whether encryption is available and working",
    )

    config_source: str = Field(
        description="Primary source of configuration (env_vars, files, defaults)",
    )

    validation_status: str = Field(
        description="Configuration validation status (passed, failed, warning)",
    )

    validation_errors: list[str] = Field(
        default_factory=list,
        description="Non-sensitive validation error summaries",
    )

    secrets_configured: int = Field(
        description="Count of configured secret fields (not values)",
    )

    api_host: str = Field(
        description="API host address (safe to expose for operational monitoring)",
    )

    api_port: int = Field(description="API port number")

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this status was generated (UTC)",
    )

    @computed_field
    @property
    def config_healthy(self) -> bool:
        """Computed field indicating overall configuration health.

        Returns:
            True if configuration is healthy (loaded and validated successfully)
        """
        return self.config_loaded and self.validation_status in ("passed", "warning")

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda dt: dt.isoformat() + "Z"}


def _count_configured_secrets(settings: ApplicationSettings) -> int:
    """Count the number of configured secret fields without exposing values.

    Args:
        settings: The settings instance to analyze

    Returns:
        Number of secret fields that have non-empty values
    """
    secret_fields = [
        "database_password",
        "database_url",
        "api_key",
        "secret_key",
        "azure_openai_api_key",
        "jwt_secret_key",
        "qdrant_api_key",
        "encryption_key",
    ]

    configured_count = 0
    for field_name in secret_fields:
        field_value = getattr(settings, field_name, None)
        if field_value is not None and field_value.get_secret_value().strip():
            configured_count += 1

    return configured_count


def _determine_config_source(settings: ApplicationSettings) -> str:
    """Determine the primary source of configuration.

    This is a best-effort determination based on typical patterns.
    Since Pydantic doesn't track sources directly, we use heuristics.

    Args:
        settings: The settings instance to analyze

    Returns:
        Primary configuration source identifier
    """
    import os

    # Check if key environment variables are set
    env_vars_set = any(
        os.getenv(f"PROMPTCRAFT_{key.upper()}")
        for key in ["ENVIRONMENT", "API_HOST", "API_PORT", "DEBUG"]
    )

    if env_vars_set:
        return "env_vars"

    # Check if environment-specific .env files likely exist
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    env_files = [
        project_root / f".env.{settings.environment}",
        project_root / f".env.{settings.environment}.gpg",
        project_root / ".env",
        project_root / ".env.gpg",
    ]

    if any(env_file.exists() for env_file in env_files):
        return "env_files"

    return "defaults"


def _sanitize_validation_errors(errors: list[str]) -> list[str]:
    """Sanitize validation errors to remove sensitive information.

    Args:
        errors: List of validation error messages

    Returns:
        Sanitized error messages safe for health check exposure
    """
    import re

    sanitized = []

    for error in errors:
        sanitized_error = error

        # Replace common sensitive patterns first (before regex substitution)
        if "password" in error.lower():
            sanitized_error = "Password configuration issue (details hidden)"
        elif "api key" in error.lower() or "api_key" in error.lower():
            sanitized_error = "API key configuration issue (details hidden)"
        elif "key" in error.lower() and "secret" in error.lower():
            sanitized_error = "Secret key configuration issue (details hidden)"
        elif "jwt" in error.lower() and "secret" in error.lower():
            sanitized_error = "JWT secret configuration issue (details hidden)"
        elif "/home/" in error or "C:\\" in error or "/Users/" in error:
            # Remove file paths
            sanitized_error = "Configuration file path issue (path hidden)"
        else:
            # If no pattern match, sanitize quoted values
            sanitized_error = re.sub(r"'[^']*'", "'***'", sanitized_error)
            sanitized_error = re.sub(r'"[^"]*"', '"***"', sanitized_error)

        sanitized.append(sanitized_error)

    return sanitized


def get_configuration_status(settings: ApplicationSettings) -> ConfigurationStatusModel:
    """Generate current configuration status for health check endpoints.

    This function creates a comprehensive status model showing the current
    state of application configuration. It's designed to be safe for exposure
    in health check endpoints, containing only operational information and
    no sensitive data.

    Args:
        settings: The application settings instance to analyze

    Returns:
        ConfigurationStatusModel with current status information

    Example:
        >>> settings = get_settings()
        >>> status = get_configuration_status(settings)
        >>> print(f"Config healthy: {status.config_healthy}")
        >>> print(f"Secrets configured: {status.secrets_configured}")
    """
    logger.debug("Generating configuration status for health check")

    # Test encryption availability
    encryption_available = validate_encryption_available()

    # Count configured secrets
    secrets_count = _count_configured_secrets(settings)

    # Determine configuration source
    config_source = _determine_config_source(settings)

    # Test configuration validation
    validation_status = "passed"
    validation_errors: list[str] = []

    try:
        # Import here to avoid circular imports
        from .settings import validate_configuration_on_startup

        validate_configuration_on_startup(settings)
        logger.debug("Configuration validation passed")
    except ConfigurationValidationError as e:
        validation_status = "failed"
        validation_errors = _sanitize_validation_errors(e.field_errors)
        logger.warning(
            f"Configuration validation failed: {len(validation_errors)} errors",
        )
    except Exception as e:
        validation_status = "failed"
        validation_errors = ["Unexpected validation error (details hidden)"]
        logger.error(f"Unexpected validation error: {e}")

    # Create status model
    status = ConfigurationStatusModel(
        environment=settings.environment,
        version=settings.version,
        debug=settings.debug,
        config_loaded=True,  # If we got here, config loaded successfully
        encryption_enabled=encryption_available,
        config_source=config_source,
        validation_status=validation_status,
        validation_errors=validation_errors,
        secrets_configured=secrets_count,
        api_host=settings.api_host,
        api_port=settings.api_port,
    )

    logger.debug(
        f"Configuration status generated: healthy={status.config_healthy}, "
        f"secrets={secrets_count}, source={config_source}",
    )

    return status


def get_configuration_health_summary() -> dict[str, Any]:
    """Get a simplified configuration health summary for quick checks.

    This function provides a minimal health check response for use in
    simple monitoring systems that just need to know if configuration
    is working properly.

    Returns:
        Dictionary with basic health information

    Example:
        >>> summary = get_configuration_health_summary()
        >>> if summary["healthy"]:
        ...     print("Configuration is healthy")
    """
    try:
        from .settings import get_settings

        settings = get_settings(validate_on_startup=False)
        status = get_configuration_status(settings)

        return {
            "healthy": status.config_healthy,
            "environment": status.environment,
            "version": status.version,
            "config_loaded": status.config_loaded,
            "encryption_available": status.encryption_enabled,
            "timestamp": status.timestamp.isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Failed to generate configuration health summary: {e}")
        return {
            "healthy": False,
            "error": "Configuration health check failed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
