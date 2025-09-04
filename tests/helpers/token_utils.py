"""Test helper utilities for JWT token generation.

This module provides deterministic token generation functions using the standard library
to ensure test isolation and avoid dependencies on PyJWT internal implementation details.
"""

import base64
import json
from typing import Any


def b64_encode_part(data: dict[str, Any] | bytes) -> str:
    """Encode a dictionary or bytes for a JWT part using standard library.

    This function uses the standard library to avoid test pollution from PyJWT internals
    and ensure consistent behavior across different test execution contexts.

    Args:
        data: Dictionary to encode as JSON or raw bytes to encode

    Returns:
        Base64url encoded string without padding
    """
    json_data = json.dumps(data, separators=(",", ":")).encode("utf-8") if isinstance(data, dict) else data

    # Use standard library for deterministic encoding
    encoded_part = base64.urlsafe_b64encode(json_data).rstrip(b"=")
    return encoded_part.decode("utf-8")


def create_malformed_jwt_token(
    header: dict[str, Any] | bytes | None = None,
    payload: dict[str, Any] | bytes | None = None,
    signature: str | None = None,
) -> str:
    """Create a JWT token for testing, including malformed variants.

    This function creates JWT tokens without using PyJWT utilities to ensure
    test isolation and deterministic behavior.

    Args:
        header: JWT header dict or raw bytes (defaults to standard RS256 header)
        payload: JWT payload dict or raw bytes (defaults to minimal payload)
        signature: Signature string (defaults to "fake-signature")

    Returns:
        Formatted JWT token string
    """
    # Default header if not provided
    if header is None:
        header = {"alg": "RS256", "typ": "JWT", "kid": "test-key-id"}

    # Default payload if not provided
    if payload is None:
        payload = {"email": "test@example.com", "sub": "user123"}

    # Default signature if not provided
    if signature is None:
        signature = b64_encode_part(b"fake-signature")

    # Encode parts
    header_encoded = b64_encode_part(header)
    payload_encoded = b64_encode_part(payload)

    return f"{header_encoded}.{payload_encoded}.{signature}"


def create_invalid_structure_tokens() -> list[str]:
    """Generate a list of structurally invalid JWT tokens for testing.

    Returns:
        List of invalid token strings
    """
    return [
        "",  # Empty string
        "invalid.token",  # Missing parts
        "header.payload",  # Missing signature
        "too.many.parts.here.invalid",  # Too many parts
        "header.payload.signature.extra",  # Extra parts
        "not-base64.payload.signature",  # Invalid base64
    ]
