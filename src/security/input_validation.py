"""Enhanced input validation and sanitization for FastAPI.

This module provides comprehensive input validation and sanitization
to prevent XSS, injection attacks, and other malicious input.
"""

import html
import re
import urllib.parse
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SecureStringField(str):
    """String field with automatic HTML escaping and validation."""

    @classmethod
    def __get_validators__(cls) -> Any:
        """Pydantic v1 compatibility for custom validation."""
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> str:
        """Validate and sanitize string input.

        Args:
            value: Input value to validate

        Returns:
            Sanitized string value

        Raises:
            ValueError: If input contains dangerous content
        """
        if not isinstance(value, str):
            value = str(value)

        # Basic length check
        max_input_length = 10000  # 10KB limit
        if len(value) > max_input_length:
            raise ValueError(f"Input too long (maximum {max_input_length} characters)")

        # Check for null bytes
        if "\x00" in value:
            raise ValueError("Null bytes not allowed in input")

        # HTML escape to prevent XSS
        sanitized = html.escape(value, quote=True)

        # Additional checks for suspicious patterns
        suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript protocol
            r"vbscript:",  # VBScript protocol
            r"onload\s*=",  # Event handlers
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                raise ValueError("Potentially dangerous content detected")

        return sanitized


class SecurePathField(str):
    """Path field with directory traversal protection."""

    @classmethod
    def __get_validators__(cls) -> Any:
        """Pydantic v1 compatibility for custom validation."""
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> str:
        """Validate path input to prevent directory traversal.

        Args:
            value: Path value to validate

        Returns:
            Sanitized path value

        Raises:
            ValueError: If path contains dangerous patterns
        """
        if not isinstance(value, str):
            value = str(value)

        # Check for directory traversal attempts
        if ".." in value:
            raise ValueError("Directory traversal not allowed")

        # Check for absolute paths
        if value.startswith("/") or (len(value) > 1 and value[1] == ":"):
            raise ValueError("Absolute paths not allowed")

        # Normalize and validate
        normalized = urllib.parse.unquote(value)
        if normalized != value:
            raise ValueError("URL-encoded paths not allowed")

        # Check for suspicious characters
        dangerous_chars = ["\x00", "\r", "\n", "|", "&", ";", "$", "`"]
        for char in dangerous_chars:
            if char in value:
                raise ValueError(f"Dangerous character '{char}' not allowed")

        return value


class SecureEmailField(str):
    """Email field with enhanced validation."""

    @classmethod
    def __get_validators__(cls) -> Any:
        """Pydantic v1 compatibility for custom validation."""
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> str:
        """Validate email input.

        Args:
            value: Email value to validate

        Returns:
            Validated email value

        Raises:
            ValueError: If email format is invalid
        """
        if not isinstance(value, str):
            value = str(value)

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            raise ValueError("Invalid email format")

        # Length checks
        max_email_length = 320  # RFC 5321 limit
        max_local_length = 64  # RFC 5321 limit
        if len(value) > max_email_length:
            raise ValueError("Email too long")

        local, domain = value.rsplit("@", 1)
        if len(local) > max_local_length:
            raise ValueError("Email local part too long")

        return value.lower()  # Normalize to lowercase


class BaseSecureModel(BaseModel):
    """Base model with security enhancements."""

    class Config:
        """Pydantic configuration for security."""

        # Prevent unknown fields
        extra = "forbid"
        # Validate assignments
        validate_assignment = True
        # Use enum values
        use_enum_values = True
        # Strict validation
        str_strip_whitespace = True
        anystr_strip_whitespace = True


class SecureTextInput(BaseSecureModel):
    """Secure text input validation model."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text content with XSS protection",
    )

    @field_validator("text")
    @classmethod
    def validate_text_content(cls, value: str) -> str:
        """Validate and sanitize text content.

        Args:
            value: Text value to validate

        Returns:
            Sanitized text value
        """
        return SecureStringField.validate(value)


class SecureFileUpload(BaseSecureModel):
    """Secure file upload validation model."""

    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Filename with path traversal protection",
    )
    content_type: str = Field(
        ...,
        description="MIME content type",
    )

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        """Validate filename for security.

        Args:
            value: Filename to validate

        Returns:
            Validated filename
        """
        # Use path validation
        validated = SecurePathField.validate(value)

        # Additional filename checks
        if not re.match(r"^[a-zA-Z0-9._-]+$", validated):
            raise ValueError("Filename contains invalid characters")

        # Check for executable extensions
        dangerous_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".scr",
            ".js",
            ".vbs",
            ".php",
            ".asp",
            ".jsp",
            ".sh",
            ".py",
            ".pl",
        ]

        for ext in dangerous_extensions:
            if validated.lower().endswith(ext):
                raise ValueError(f"File type '{ext}' not allowed")

        return validated

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        """Validate MIME content type.

        Args:
            value: Content type to validate

        Returns:
            Validated content type
        """
        # Basic MIME type validation
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^]*$", value):
            raise ValueError("Invalid content type format")

        # Whitelist safe content types
        safe_types = [
            "text/plain",
            "text/csv",
            "text/markdown",
            "application/json",
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]

        if value not in safe_types:
            raise ValueError(f"Content type '{value}' not allowed")

        return value


class SecureQueryParams(BaseSecureModel):
    """Secure query parameter validation."""

    search: str | None = Field(
        None,
        max_length=1000,
        description="Search query with XSS protection",
    )
    page: int = Field(
        1,
        ge=1,
        le=10000,
        description="Page number",
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Items per page",
    )
    sort: str | None = Field(
        None,
        max_length=50,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*(:asc|:desc)?$",
        description="Sort field and direction",
    )

    @field_validator("search")
    @classmethod
    def validate_search(cls, value: str | None) -> str | None:
        """Validate search query.

        Args:
            value: Search query to validate

        Returns:
            Sanitized search query
        """
        if value is None:
            return None

        return SecureStringField.validate(value)


def create_input_sanitizer() -> dict[str, Any]:
    """Create input sanitization configuration.

    Returns:
        Dictionary of sanitization functions
    """
    return {
        "string": SecureStringField.validate,
        "path": SecurePathField.validate,
        "email": SecureEmailField.validate,
    }


def sanitize_dict_values(data: dict[str, Any], sanitizer_type: str = "string") -> dict[str, Any]:
    """Sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize
        sanitizer_type: Type of sanitization to apply

    Returns:
        Dictionary with sanitized values
    """
    sanitizers = create_input_sanitizer()
    sanitizer = sanitizers.get(sanitizer_type, sanitizers["string"])

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitizer(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_values(value, sanitizer_type)
        elif isinstance(value, list):
            sanitized[key] = [sanitizer(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value

    return sanitized
