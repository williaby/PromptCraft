"""Shared fixtures for authentication tests - compatible with simplified auth system."""

import base64
import json
from datetime import timedelta
from typing import Any
from unittest.mock import Mock

import pytest

from src.auth import ServiceTokenManager
from src.auth.models import AuthenticatedUser, UserRole
from src.utils.datetime_compat import utc_now


@pytest.fixture
def mock_service_token_manager():
    """Create mock service token manager."""
    manager = Mock(spec=ServiceTokenManager)
    manager.create_token.return_value = {
        "token_id": "test-token-123",
        "token_secret": "secret-key",
        "token_name": "test-service",
        "metadata": {"permissions": ["read", "write"]},
    }
    manager.validate_token.return_value = True
    return manager


@pytest.fixture
def authenticated_user():
    """Create authenticated user for testing."""
    return AuthenticatedUser(
        email="test@example.com",
        role=UserRole.USER,
        user_id="test-user-123",
        token_id="session-token-123",  # noqa: S106
    )


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return AuthenticatedUser(
        email="admin@example.com",
        role=UserRole.ADMIN,
        user_id="admin-user-123",
        token_id="admin-session-123",  # noqa: S106
    )


@pytest.fixture
def valid_jwt_payload():
    """Valid JWT payload for testing."""
    return {
        "iss": "https://test.cloudflareaccess.com",
        "aud": "https://test-app.com",
        "sub": "user123",
        "email": "test@example.com",
        "exp": int((utc_now() + timedelta(hours=1)).timestamp()),
        "iat": int(utc_now().timestamp()),
        "nbf": int(utc_now().timestamp()),
    }


def create_jwt_token(payload: dict[str, Any], header: dict[str, Any] | None = None) -> str:
    """Create a properly formatted JWT token for testing.

    Args:
        payload: JWT payload claims
        header: JWT header (defaults to standard RS256 header)

    Returns:
        Formatted JWT token string
    """
    if header is None:
        header = {"alg": "RS256", "typ": "JWT", "kid": "test-key-id"}

    # Encode header and payload
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")).decode("utf-8").rstrip("=")
    )

    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("utf-8").rstrip("=")
    )

    # Create fake signature
    signature = base64.urlsafe_b64encode(b"fake-signature").decode("utf-8").rstrip("=")

    return f"{header_encoded}.{payload_encoded}.{signature}"


@pytest.fixture
def create_test_jwt():
    """Factory fixture for creating test JWT tokens."""
    return create_jwt_token


@pytest.fixture
def valid_jwt_token(valid_jwt_payload, create_test_jwt):
    """Create a valid JWT token for testing."""
    return create_test_jwt(valid_jwt_payload)


@pytest.fixture
def jwt_token_without_kid(valid_jwt_payload, create_test_jwt):
    """Create JWT token without 'kid' in header."""
    header = {"alg": "RS256", "typ": "JWT"}  # Missing 'kid'
    return create_test_jwt(valid_jwt_payload, header)


@pytest.fixture
def jwt_token_missing_email(valid_jwt_payload, create_test_jwt):
    """Create JWT token without email claim."""
    payload = valid_jwt_payload.copy()
    del payload["email"]
    return create_test_jwt(payload)


@pytest.fixture
def jwt_token_empty_email(valid_jwt_payload, create_test_jwt):
    """Create JWT token with empty email claim."""
    payload = valid_jwt_payload.copy()
    payload["email"] = ""
    return create_test_jwt(payload)


@pytest.fixture
def jwt_token_none_email(valid_jwt_payload, create_test_jwt):
    """Create JWT token with None email claim."""
    payload = valid_jwt_payload.copy()
    payload["email"] = None
    return create_test_jwt(payload)


# Cloudflare Access fixtures for auth_simple compatibility
@pytest.fixture
def cloudflare_headers():
    """Mock Cloudflare headers for authenticated user."""
    return {
        "cf-access-authenticated-user-email": "test@example.com",
        "cf-access-username": "test@example.com",
        "cf-access-user": "test-user-id",
        "cf-access-organization": "test-org",
        "cf-ray": "test-ray-id",
        "x-forwarded-for": "192.168.1.100",
    }


@pytest.fixture
def admin_cloudflare_headers():
    """Mock Cloudflare headers for admin user."""
    return {
        "cf-access-authenticated-user-email": "admin@example.com",
        "cf-access-username": "admin@example.com",
        "cf-access-user": "admin-user-id",
        "cf-access-organization": "test-org",
        "cf-ray": "admin-ray-id",
        "x-forwarded-for": "192.168.1.101",
    }


@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state = MagicMock()
    request.url.path = "/test"
    request.method = "GET"
    request.client.host = "192.168.1.100"
    return request
