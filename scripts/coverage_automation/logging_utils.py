"""
Logging utilities for coverage automation.
"""

import logging
from pathlib import Path
from typing import Any


class ContextAwareLogger:
    """Logger with structured context information."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        context_str = ' '.join(f'{k}={v}' for k, v in kwargs.items())
        full_message = f"{message} {context_str}".strip()
        self.logger.info(full_message)
        
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        context_str = ' '.join(f'{k}={v}' for k, v in kwargs.items())
        full_message = f"{message} {context_str}".strip()
        self.logger.warning(full_message)
        
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        context_str = ' '.join(f'{k}={v}' for k, v in kwargs.items())
        full_message = f"{message} {context_str}".strip()
        self.logger.error(full_message)


class SecurityLogger:
    """Specialized logger for security events."""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        
    def log_path_validation_failure(self, path: Path, reason: str):
        """Log path validation failure."""
        self.logger.warning(f"Security: Path validation failed - {reason} path={path}")
        
    def log_file_size_violation(self, path: Path, size_mb: float):
        """Log file size violation.""" 
        self.logger.warning(f"Security: File size violation path={path} size_mb={size_mb}")


class PerformanceLogger:
    """Specialized logger for performance events."""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        
    def log_operation_timing(self, operation: str, duration_seconds: float, context: str = ""):
        """Log operation timing."""
        context_info = f" context={context}" if context else ""
        self.logger.info(f"Performance: {operation} completed duration_seconds={duration_seconds}{context_info}")


def get_logger(name: str) -> ContextAwareLogger:
    """Get a context-aware logger."""
    return ContextAwareLogger(name)


def get_security_logger() -> SecurityLogger:
    """Get security logger."""
    return SecurityLogger()


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger."""
    return PerformanceLogger()