"""
Secure Logging Utilities

Provides utilities for safe logging that prevent log injection attacks
by sanitizing user-provided input before inclusion in log messages.
"""

import re
from typing import Any


def sanitize_for_logging(value: Any) -> str:
    """
    Sanitize a value for safe inclusion in log messages.

    Removes control characters that could be used for log injection attacks,
    including CRLF sequences and other control characters.

    Args:
        value: The value to sanitize (will be converted to string)

    Returns:
        Sanitized string safe for logging
    """
    if value is None:
        return "None"

    # Convert to string and remove control characters
    # This removes CR (\r), LF (\n), and other control characters
    # that could be used for log injection
    sanitized = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", "", str(value))

    # Limit length to prevent log flooding
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + "..."

    return sanitized


def validate_identifier(value: str, name: str = "identifier") -> str:
    """
    Validate that a value is a safe identifier for logging.

    Ensures the value contains only alphanumeric characters, underscores,
    hyphens, and periods, which are safe for logging.

    Args:
        value: The identifier to validate
        name: Name of the identifier for error messages

    Returns:
        The validated identifier

    Raises:
        ValueError: If the identifier contains unsafe characters
    """
    if not value:
        raise ValueError(f"{name} cannot be empty")

    # Allow alphanumeric, underscore, hyphen, and period
    if not re.match(r"^[a-zA-Z0-9_.-]+$", value):
        raise ValueError(f"{name} contains invalid characters")

    # Prevent extremely long identifiers
    if len(value) > 100:
        raise ValueError(f"{name} is too long (max 100 characters)")

    return value


def safe_log_params(**kwargs: Any) -> dict[str, str]:
    """
    Sanitize multiple parameters for logging.

    Args:
        **kwargs: Key-value pairs to sanitize

    Returns:
        Dictionary with sanitized values
    """
    return {key: sanitize_for_logging(value) for key, value in kwargs.items()}
