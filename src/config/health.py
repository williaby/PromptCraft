"""Health check models and utilities for configuration status monitoring.

This module implements Phase 5 of the Core Configuration System: Health Check Integration.
It provides configuration status models and utilities for exposing operational
information through health check endpoints without revealing sensitive data.
"""

import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, computed_field

from .constants import FILE_PATH_PATTERNS, SECRET_FIELD_NAMES, SENSITIVE_ERROR_PATTERNS
from .settings import (
    ApplicationSettings,
    ConfigurationValidationError,
    get_settings,
    validate_encryption_available,
)
from .validation import validate_configuration_on_startup

# Compile regex patterns once for better performance
_COMPILED_SENSITIVE_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), replacement) for pattern, replacement in SENSITIVE_ERROR_PATTERNS
]

_COMPILED_FILE_PATH_PATTERNS = [re.compile(pattern) for pattern in FILE_PATH_PATTERNS]

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
        default_factory=lambda: datetime.now(UTC),
        description="When this status was generated (UTC)",
    )

    @computed_field
    def config_healthy(self) -> bool:
        """Computed field indicating overall configuration health.

        Returns:
            True if configuration is healthy (loaded and validated successfully)
        """
        return self.config_loaded and self.validation_status in ("passed", "warning")

    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat() + "Z"}}


def _count_configured_secrets(settings: ApplicationSettings) -> int:
    """Count the number of configured secret fields without exposing values.

    Args:
        settings: The settings instance to analyze

    Returns:
        Number of secret fields that have non-empty values
    """
    configured_count = 0
    for field_name in SECRET_FIELD_NAMES:
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
    # Check if key environment variables are set
    env_vars_set = any(
        os.getenv(f"PROMPTCRAFT_{key.upper()}") for key in ["ENVIRONMENT", "API_HOST", "API_PORT", "DEBUG"]
    )

    if env_vars_set:
        return "env_vars"

    # Check if environment-specific .env files likely exist
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

    Uses pre-compiled regex patterns for optimal performance.

    Args:
        errors: List of validation error messages

    Returns:
        Sanitized error messages safe for health check exposure
    """
    sanitized = []

    for error in errors:
        sanitized_error = error

        # Check for sensitive patterns using pre-compiled regex patterns
        for compiled_pattern, replacement in _COMPILED_SENSITIVE_PATTERNS:
            if compiled_pattern.search(error):
                sanitized_error = replacement
                break
        else:
            # Check for file path patterns using pre-compiled patterns
            for compiled_path_pattern in _COMPILED_FILE_PATH_PATTERNS:
                if compiled_path_pattern.search(error):
                    sanitized_error = "Configuration file path issue (path hidden)"
                    break
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
        validate_configuration_on_startup(settings)
        logger.debug("Configuration validation passed")
    except ConfigurationValidationError as e:
        validation_status = "failed"
        validation_errors = _sanitize_validation_errors(e.field_errors)
        logger.warning(
            "Configuration validation failed: %d errors",
            len(validation_errors),
        )
    except (ValueError, TypeError, AttributeError) as e:
        validation_status = "failed"
        validation_errors = ["Configuration format error"]
        logger.error("Configuration format error: %s", type(e).__name__)
    except Exception:
        logger.exception("Unexpected validation error")
        raise

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
        "Configuration status generated: healthy=%s, secrets=%d, source=%s",
        status.config_healthy,
        secrets_count,
        config_source,
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
        settings = get_settings(validate_on_startup=False)
        status = get_configuration_status(settings)

        return {
            "healthy": status.config_healthy,
            "environment": status.environment,
            "version": status.version,
            "config_loaded": status.config_loaded,
            "encryption_available": status.encryption_enabled,
            "timestamp": status.timestamp.isoformat(),
        }
    except (ValueError, TypeError, AttributeError) as e:
        logger.error("Configuration health summary format error: %s", type(e).__name__)
        return {
            "healthy": False,
            "error": "Configuration health check failed",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception:
        logger.exception("Failed to generate configuration health summary")
        return {
            "healthy": False,
            "error": "Configuration health check failed",
            "timestamp": datetime.now(UTC).isoformat(),
        }
