"""
Configuration settings for PromptCraft-Hybrid.

This module provides centralized configuration management for the
PromptCraft-Hybrid system, including model settings, API keys,
and application configuration.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigurationValidationError(Exception):
    """Exception raised for configuration validation errors."""

    pass


class Settings:
    """
    Configuration settings for PromptCraft-Hybrid.

    This class manages all configuration settings for the application,
    including model configurations, API keys, and system settings.
    """

    def __init__(self):
        # Application settings
        self.app_name = "PromptCraft-Hybrid"
        self.version = "0.1.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "dev")

        # Server settings
        self.server_host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.server_port = int(os.getenv("SERVER_PORT", "7860"))

        # Model settings
        self.default_model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

        # File upload settings
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.max_files = int(os.getenv("MAX_FILES", "5"))
        self.supported_file_types = [".txt", ".md", ".pdf", ".docx", ".csv", ".json"]

        # API settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        # Database settings
        self.qdrant_host = os.getenv("QDRANT_HOST", "192.168.1.16")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")

        # Session settings
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        self.cost_tracking_enabled = os.getenv("COST_TRACKING_ENABLED", "true").lower() == "true"

        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "promptcraft.log")

        # Feature flags
        self.feature_journey_1 = os.getenv("FEATURE_JOURNEY_1", "true").lower() == "true"
        self.feature_journey_2 = os.getenv("FEATURE_JOURNEY_2", "false").lower() == "true"
        self.feature_journey_3 = os.getenv("FEATURE_JOURNEY_3", "false").lower() == "true"
        self.feature_journey_4 = os.getenv("FEATURE_JOURNEY_4", "false").lower() == "true"

        # Paths
        self.project_root = Path(__file__).parent.parent.parent
        self.knowledge_base_path = self.project_root / "knowledge"
        self.templates_path = self.project_root / "templates"
        self.uploads_path = self.project_root / "uploads"

        # Ensure directories exist
        self.uploads_path.mkdir(parents=True, exist_ok=True)

    def get_model_costs(self) -> Dict[str, float]:
        """Get model cost information."""
        return {
            # Free models
            "llama-4-maverick:free": 0.0,
            "mistral-small-3.1:free": 0.0,
            "deepseek-chat:free": 0.0,
            "optimus-alpha:free": 0.0,
            # Standard models (cost per 1K tokens)
            "gpt-4o-mini": 0.0015,
            "gpt-3.5-turbo": 0.0005,
            "claude-3-haiku": 0.00025,
            "gemini-1.5-flash": 0.00035,
            # Premium models
            "gpt-4o": 0.015,
            "claude-3.5-sonnet": 0.003,
            "gemini-1.5-pro": 0.00125,
            "o1-preview": 0.015,
        }

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        provider_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "openrouter": self.openrouter_api_key,
        }
        return provider_map.get(provider.lower())

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature_map = {
            "journey_1": self.feature_journey_1,
            "journey_2": self.feature_journey_2,
            "journey_3": self.feature_journey_3,
            "journey_4": self.feature_journey_4,
        }
        return feature_map.get(feature.lower(), False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "default_model": self.default_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "max_file_size": self.max_file_size,
            "max_files": self.max_files,
            "supported_file_types": self.supported_file_types,
            "qdrant_host": self.qdrant_host,
            "qdrant_port": self.qdrant_port,
            "session_timeout": self.session_timeout,
            "cost_tracking_enabled": self.cost_tracking_enabled,
            "log_level": self.log_level,
            "features": {
                "journey_1": self.feature_journey_1,
                "journey_2": self.feature_journey_2,
                "journey_3": self.feature_journey_3,
                "journey_4": self.feature_journey_4,
            },
        }


# Alias for backward compatibility
ApplicationSettings = Settings

# Global settings instance
_settings_instance = None


def get_settings(validate_on_startup: bool = True) -> Settings:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """Reload the global settings instance."""
    global _settings_instance
    _settings_instance = None
    return get_settings()


def _load_encrypted_env_file(file_path: str) -> Dict[str, str]:
    """Load encrypted environment file (placeholder implementation)."""
    # This is a placeholder - in a real implementation, this would
    # decrypt and load environment variables from an encrypted file
    return {}


def validate_encryption_available() -> bool:
    """Validate that encryption capabilities are available."""
    # This is a placeholder - in a real implementation, this would
    # check for GPG keys and encryption capabilities
    return True


def _detect_environment() -> str:
    """Detect the current environment."""
    return os.getenv("ENVIRONMENT", "dev")


def _env_file_settings() -> Dict[str, str]:
    """Get environment file settings."""
    # This is a placeholder - in a real implementation, this would
    # load settings from environment files
    return {}


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _load_env_file(file_path: str) -> Dict[str, str]:
    """Load environment file."""
    # Placeholder implementation
    return {}


def _log_configuration_status(status: str) -> None:
    """Log configuration status."""
    # Placeholder implementation
    pass


def _log_encryption_status(status: str) -> None:
    """Log encryption status."""
    # Placeholder implementation
    pass


def _mask_secret_value(value: str) -> str:
    """Mask secret values for logging."""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def _process_validation_errors(errors: list) -> None:
    """Process validation errors."""
    # Placeholder implementation
    pass


def _validate_general_security() -> bool:
    """Validate general security requirements."""
    # Placeholder implementation
    return True


def _validate_production_requirements() -> bool:
    """Validate production requirements."""
    # Placeholder implementation
    return True


def _validate_staging_requirements() -> bool:
    """Validate staging requirements."""
    # Placeholder implementation
    return True


def validate_configuration_on_startup() -> bool:
    """Validate configuration on startup."""
    # Placeholder implementation
    return True


def validate_field_requirements_by_environment(env: str) -> bool:
    """Validate field requirements by environment."""
    # Placeholder implementation
    return True
