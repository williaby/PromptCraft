"""Authentication fixtures for integration testing.

Provides real authentication services and tokens for testing without mocking.
"""

from datetime import datetime
import secrets
import uuid

from fastapi import Request
import pytest
import pytest_asyncio

from src.auth.middleware import AuthenticatedUser, ServiceTokenUser
from src.auth.models import UserRole
from src.auth.service_token_manager import ServiceTokenManager
from src.database.models import ServiceToken
from src.utils.datetime_compat import UTC, timedelta


@pytest_asyncio.fixture
async def real_service_token_manager(test_db_with_override):
    """Provide real ServiceTokenManager with test database connection."""
    from unittest.mock import AsyncMock, MagicMock, patch
    
    # Unpack the tuple from test_db_with_override fixture
    test_db_session, override_get_db = test_db_with_override

    # Create mock database manager that returns test database session
    mock_db_manager = MagicMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=test_db_session)  # Return session, not tuple
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_db_manager.get_session.return_value = mock_context_manager

    # Patch get_database_manager to return our mock
    with patch("src.auth.service_token_manager.get_database_manager", return_value=mock_db_manager):
        manager = ServiceTokenManager()
        yield manager


@pytest_asyncio.fixture
async def test_service_token(test_db_with_override):
    """Create a real service token in test database."""
    # Unpack the tuple from test_db_with_override fixture
    test_db_session, override_get_db = test_db_with_override
    
    # Create token directly in database
    token_id = uuid.uuid4()
    token_value = f"sk_{secrets.token_urlsafe(32)}"
    token_hash = ServiceTokenManager().hash_token(token_value)
    
    # Generate unique token name for each test to avoid UNIQUE constraint failures
    unique_token_name = f"test_service_token_{secrets.token_hex(8)}"

    # nosec: B106 - test token name is not a password
    service_token = ServiceToken(
        id=token_id,
        token_name=unique_token_name,
        token_hash=token_hash,
        is_active=True,
        usage_count=0,
        token_metadata={"permissions": ["read", "write", "system_status", "audit_log"], "test": True},
        created_at=datetime.now(UTC),
        last_used=None,
    )

    test_db_session.add(service_token)
    await test_db_session.flush()  # Use flush instead of commit to avoid transaction issues

    return {
        "token_value": token_value,
        "token_id": str(token_id),  # Convert UUID to string
        "token_name": unique_token_name,
        "metadata": {"permissions": ["read", "write", "system_status", "audit_log"], "test": True},
    }


@pytest.fixture
def test_authenticated_user() -> AuthenticatedUser:
    """Create a test authenticated user (JWT user)."""
    jwt_claims = {
        "sub": "test_user_123",  # This becomes user_id via property
        "email": "test@example.com",
        "role": "admin",
        "iat": 1640995200,  # Issued at timestamp
        "exp": 1641081600,  # Expiration timestamp
        "iss": "test-issuer",
        "aud": "promptcraft",
    }
    return AuthenticatedUser(
        email="test@example.com",
        role=UserRole.ADMIN,
        jwt_claims=jwt_claims,
    )


@pytest_asyncio.fixture
async def test_service_user(test_service_token) -> ServiceTokenUser:
    """Create a test service token user."""
    return ServiceTokenUser(
        token_name=test_service_token["token_name"],
        token_id=test_service_token["token_id"],
        usage_count=0,
        metadata=test_service_token["metadata"],
    )


@pytest.fixture
def admin_user() -> AuthenticatedUser:
    """Create an admin user for testing admin endpoints."""
    return AuthenticatedUser(
        email="admin@example.com",
        role=UserRole.ADMIN,
        jwt_claims={"sub": "admin_user_456", "email": "admin@example.com", "role": "admin"},
    )


@pytest.fixture
def regular_user() -> AuthenticatedUser:
    """Create a regular user for testing non-admin endpoints."""
    return AuthenticatedUser(
        email="user@example.com",
        role=UserRole.USER,
        jwt_claims={"sub": "regular_user_789", "email": "user@example.com", "role": "user"},
    )


@pytest.fixture
def mock_request():
    """Create a mock Request object for dependency injection."""

    class MockRequest:
        def __init__(self):
            self.headers = {}
            self.state = type("State", (), {})()

        def header(self, key: str) -> str | None:
            return self.headers.get(key.lower())

    return MockRequest()


@pytest_asyncio.fixture
async def authenticated_request(mock_request, test_authenticated_user):
    """Create a request with authenticated user attached."""
    mock_request.state.user = test_authenticated_user
    return mock_request


@pytest_asyncio.fixture
async def service_token_request(mock_request, test_service_user):
    """Create a request with service token user attached."""
    mock_request.state.user = test_service_user
    return mock_request


class TestAuthMiddleware:
    """Test authentication middleware that uses real auth logic but with test users."""

    def __init__(self, test_user: AuthenticatedUser | None = None):
        self.test_user = test_user

    async def __call__(self, request: Request) -> AuthenticatedUser:
        if hasattr(request.state, "user") and request.state.user:
            return request.state.user

        if self.test_user:
            return self.test_user

        # Default to admin user if none provided
        return AuthenticatedUser(
            email="default@example.com",
            role=UserRole.ADMIN,
            jwt_claims={"sub": "default_user", "email": "default@example.com", "role": "admin"},
        )


@pytest.fixture
def auth_middleware_admin(admin_user):
    """Authentication middleware that returns admin user."""
    return TestAuthMiddleware(admin_user)


@pytest.fixture
def auth_middleware_user(regular_user):
    """Authentication middleware that returns regular user."""
    return TestAuthMiddleware(regular_user)


@pytest_asyncio.fixture
async def multiple_service_tokens(test_db_with_override):
    """Create multiple service tokens for testing list operations."""
    # Unpack the tuple from test_db_with_override fixture
    test_db_session, override_get_db = test_db_with_override
    
    tokens = []

    for i in range(3):
        token_id = secrets.token_urlsafe(16)
        token_value = f"sk_{secrets.token_urlsafe(32)}"
        token_hash = ServiceTokenManager().hash_token(token_value)

        service_token = ServiceToken(
            id=token_id,
            token_name=f"test_token_{i+1}",
            token_hash=token_hash,
            is_active=True,
            usage_count=i * 10,
            metadata={"permissions": ["read"], "test": True},
            created_at=datetime.now(UTC) - timedelta(days=i),
            last_used=datetime.now(UTC) - timedelta(hours=i),
        )

        test_db_session.add(service_token)
        tokens.append(
            {
                "token_value": token_value,
                "token_id": token_id,
                "name": f"test_token_{i+1}",
                "usage_count": i * 10,
            },
        )

    await test_db_session.flush()  # Use flush instead of commit to avoid transaction issues
    return tokens
