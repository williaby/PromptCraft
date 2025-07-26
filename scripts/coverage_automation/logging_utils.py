"""
Structured logging utilities for coverage automation.
Provides context-aware logging with proper error handling.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class ContextAwareLogger:
    """Logger with context information for better debugging."""

    def __init__(self, name: str, log_level: str = "INFO"):
        """Initialize logger with structured formatting."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **context: Any) -> None:
        """Log info message with optional context."""
        self._log_with_context(logging.INFO, message, context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning message with optional context."""
        self._log_with_context(logging.WARNING, message, context)

    def error(self, message: str, **context: Any) -> None:
        """Log error message with optional context."""
        self._log_with_context(logging.ERROR, message, context)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug message with optional context."""
        self._log_with_context(logging.DEBUG, message, context)

    def _log_with_context(self, level: int, message: str, context: dict[str, Any]) -> None:
        """Log message with structured context information."""
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            formatted_message = f"{message} | {context_str}"
        else:
            formatted_message = message

        self.logger.log(level, formatted_message)


class SecurityLogger:
    """Specialized logger for security-related events."""

    def __init__(self):
        self.logger = ContextAwareLogger("coverage_automation.security", "WARNING")

    def log_path_validation_failure(self, file_path: Path, reason: str) -> None:
        """Log path validation security failure."""
        self.logger.error(
            "Security: Path validation failed",
            file_path=str(file_path),
            reason=reason,
            timestamp=datetime.now().isoformat(),
        )

    def log_file_size_violation(self, file_path: Path, size_bytes: int, limit_bytes: int) -> None:
        """Log file size security violation."""
        self.logger.error(
            "Security: File size limit exceeded",
            file_path=str(file_path),
            size_bytes=size_bytes,
            limit_bytes=limit_bytes,
            timestamp=datetime.now().isoformat(),
        )

    def log_import_path_rejection(self, import_path: str, reason: str) -> None:
        """Log import path security rejection."""
        self.logger.error(
            "Security: Import path rejected",
            import_path=import_path,
            reason=reason,
            timestamp=datetime.now().isoformat(),
        )


class PerformanceLogger:
    """Logger for performance metrics and timing."""

    def __init__(self):
        self.logger = ContextAwareLogger("coverage_automation.performance", "INFO")

    def log_operation_timing(self, operation: str, duration_seconds: float, **context: Any) -> None:
        """Log operation timing with context."""
        self.logger.info(f"Performance: {operation} completed", duration_seconds=round(duration_seconds, 3), **context)

    def log_cache_stats(self, cache_name: str, hits: int, misses: int, size: int) -> None:
        """Log cache performance statistics."""
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        self.logger.info(
            f"Performance: Cache stats for {cache_name}",
            hits=hits,
            misses=misses,
            size=size,
            hit_rate=round(hit_rate * 100, 2),
        )


def get_logger(component: str) -> ContextAwareLogger:
    """Get a context-aware logger for a component."""
    return ContextAwareLogger(f"coverage_automation.{component}")


def get_security_logger() -> SecurityLogger:
    """Get the security logger instance."""
    return SecurityLogger()


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger instance."""
    return PerformanceLogger()
