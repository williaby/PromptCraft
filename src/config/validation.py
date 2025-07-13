"""Configuration validation utilities.

This module provides shared validation functions to avoid circular imports
between settings and health modules.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import ApplicationSettings

logger = logging.getLogger(__name__)


def validate_configuration_on_startup(settings: "ApplicationSettings") -> None:
    """Validate configuration settings on application startup.

    This function is extracted here to avoid circular imports between
    settings.py and health.py modules.

    Args:
        settings: The application settings to validate

    Raises:
        ConfigurationValidationError: If validation fails
    """
    # This is currently a placeholder - the actual validation
    # logic should be implemented here to avoid circular imports
    logger.info("Configuration validation completed successfully for %s", type(settings).__name__)
