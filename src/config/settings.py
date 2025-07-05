"""Simplified configuration settings for health check integration.

This is a minimal version to support the health check integration PR.
The full configuration system is in a separate PR (#149).
"""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        message: str,
        field_errors: list[str] | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.field_errors = field_errors or []
        self.suggestions = suggestions or []


class ApplicationSettings(BaseSettings):
    """Basic application settings for health check integration."""

    app_name: str = Field(default="PromptCraft-Hybrid")
    version: str = Field(default="0.1.0")
    environment: Literal["dev", "staging", "prod"] = Field(default="dev")
    debug: bool = Field(default=True)
    api_host: str = Field(default="0.0.0.0")  # noqa: S104
    api_port: int = Field(default=8000)

    # Basic secret fields for testing health checks
    api_key: SecretStr | None = Field(default=None)
    secret_key: SecretStr | None = Field(default=None)

    model_config = {"env_prefix": "PROMPTCRAFT_"}


def validate_encryption_available() -> bool:
    """Check if encryption is available (simplified version)."""
    try:
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False


def validate_configuration_on_startup(settings: ApplicationSettings) -> None:
    """Validate configuration (simplified version)."""
    if settings.environment == "prod" and settings.debug:
        raise ConfigurationValidationError(
            "Debug mode should be disabled in production",
            field_errors=["Debug mode enabled in production"],
            suggestions=["Set PROMPTCRAFT_DEBUG=false"],
        )


def get_settings(validate_on_startup: bool = True) -> ApplicationSettings:
    """Get application settings."""
    settings = ApplicationSettings()
    if validate_on_startup:
        validate_configuration_on_startup(settings)
    return settings


def reload_settings(validate_on_startup: bool = True) -> ApplicationSettings:
    """Reload settings (simplified version)."""
    return get_settings(validate_on_startup)
