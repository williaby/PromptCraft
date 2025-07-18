"""
Logging mixin for PromptCraft-Hybrid components.

This module provides a standardized logging interface for all components
in the PromptCraft-Hybrid system, ensuring consistent logging behavior
across all modules.
"""

import logging
from typing import Any, Dict, Optional


class LoggingMixin:
    """
    Mixin class providing standardized logging functionality.

    This mixin provides a consistent logging interface for all components
    in the PromptCraft-Hybrid system. It automatically creates a logger
    based on the class name and module.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance for this component."""
        return self._logger

    def log_debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        self._logger.debug(message, extra=extra)

    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        self._logger.info(message, extra=extra)

    def log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        self._logger.warning(message, extra=extra)

    def log_error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        self._logger.error(message, extra=extra)

    def log_critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a critical message."""
        self._logger.critical(message, extra=extra)

    def log_exception(self, message: str, exc_info: bool = True, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an exception with traceback."""
        self._logger.exception(message, exc_info=exc_info, extra=extra)


class StructuredLoggingMixin(LoggingMixin):
    """Mixin class providing structured logging functionality."""
    
    def log_structured(self, level: str, message: str, data: Dict[str, Any]) -> None:
        """Log a structured message with additional data."""
        getattr(self._logger, level.lower())(message, extra=data)


def get_component_logger(component_name: str) -> logging.Logger:
    """Get a logger for a specific component."""
    return logging.getLogger(f"promptcraft.{component_name}")
