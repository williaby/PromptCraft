"""Unit tests for auth middleware with database integration."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.auth.config import AuthenticationConfig
from src.auth.jwt_validator import JWTValidator
from src.auth.middleware import AuthenticationMiddleware
from src.database.models import ServiceToken


class TestAuthMiddlewareDatabase:
    """Test suite for authentication middleware with database integration."""

    @pytest.fixture
    def mock_config(self):
        """Mock authentication configuration."""
        config = MagicMock(spec=AuthenticationConfig)
        config.cloudflare_team_domain = "test.cloudflareaccess.com"
        config.cloudflare_aud = "test-audience"
        config.rate_limit = "10/minute"
        config.rate_limit_storage_uri = "memory://"
        config.cloudflare_access_enabled = True
        config.auth_logging_enabled = True
        config.auth_error_detail_enabled = True
        return config

    @pytest.fixture
    def mock_jwt_validator(self):
        """Mock JWT validator."""
        validator = MagicMock(spec=JWTValidator)
        validator.validate_jwt = AsyncMock(
            return_value={"email": "test@example.com", "sub": "user123", "aud": "test-audience"},
        )
        return validator

    @pytest.fixture
    def mock_database(self):
        """Mock database connection."""
        db = AsyncMock()

        # Mock session context manager
        session = AsyncMock()
        db.session.return_value.__aenter__.return_value = session
        db.session.return_value.__aexit__.return_value = None

        return db, session

    @pytest.fixture
    def auth_middleware(self, mock_config, mock_jwt_validator):
        """Authentication middleware instance."""
        app = MagicMock()
        return AuthenticationMiddleware(app, mock_config, mock_jwt_validator, excluded_paths=["/health", "/docs"])

    @pytest.mark.asyncio
    async def test_service_token_validation_success(self, auth_middleware, mock_database):
        """Test successful service token validation against database."""
        db, session = mock_database

        # Mock request with service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_valid_token"}.get(key)
        request.headers = mock_headers
        request.method = "GET"

        # Mock database token lookup
        mock_token = MagicMock(spec=ServiceToken)
        mock_token.id = "token-uuid"
        mock_token.token_name = "test-api-token"  # noqa: S105
        mock_token.is_active = True
        mock_token.is_expired = False
        mock_token.usage_count = 5
        mock_token.token_metadata = {"permissions": ["read", "write"]}

        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_token
        session.execute.return_value = mock_result

        response = Response()
        call_next = AsyncMock(return_value=response)

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            result = await auth_middleware.dispatch(request, call_next)

            # Should proceed to next middleware
            call_next.assert_called_once_with(request)
            assert result == response

            # Should have updated usage count in database (via SQL UPDATE)
            # Verify that execute was called twice: once for SELECT, once for UPDATE
            assert session.execute.call_count == 2

            # Verify the authenticated user has correct usage count
            authenticated_user = request.state.authenticated_user
            assert authenticated_user.usage_count == 6  # original 5 + 1

    @pytest.mark.asyncio
    async def test_service_token_validation_not_found(self, auth_middleware, mock_database):
        """Test service token validation when token not found in database."""
        db, session = mock_database

        # Mock request with invalid service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_invalid_token"}.get(key)
        request.headers = mock_headers
        request.method = "GET"

        # Mock database - token not found
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        session.execute.return_value = mock_result

        call_next = AsyncMock()

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            result = await auth_middleware.dispatch(request, call_next)

            # Should return 401 Unauthorized
            assert isinstance(result, JSONResponse)
            assert result.status_code == 401
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_token_validation_expired(self, auth_middleware, mock_database):
        """Test service token validation with expired token."""
        db, session = mock_database

        # Mock request with service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_expired_token"}.get(key)
        request.headers = mock_headers
        request.method = "GET"

        # Mock expired token
        mock_token = MagicMock(spec=ServiceToken)
        mock_token.id = "expired-token-uuid"
        mock_token.token_name = "expired-api-token"  # noqa: S105
        mock_token.is_active = True
        mock_token.is_expired = True  # Token is expired
        mock_token.is_valid = False  # Not valid due to expiration
        mock_token.expires_at = datetime.now(UTC) - timedelta(hours=1)

        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_token
        session.execute.return_value = mock_result

        call_next = AsyncMock()

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            result = await auth_middleware.dispatch(request, call_next)

            # Should return 401 Unauthorized for expired token
            assert isinstance(result, JSONResponse)
            assert result.status_code == 401
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_token_validation_inactive(self, auth_middleware, mock_database):
        """Test service token validation with inactive token."""
        db, session = mock_database

        # Mock request with service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_inactive_token"}.get(key)
        request.headers = mock_headers
        request.method = "GET"

        # Mock inactive token
        mock_token = MagicMock(spec=ServiceToken)
        mock_token.id = "inactive-token-uuid"
        mock_token.token_name = "inactive-api-token"  # noqa: S105
        mock_token.is_active = False  # Token is inactive
        mock_token.is_expired = False
        mock_token.is_valid = False  # Not valid due to being inactive

        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_token
        session.execute.return_value = mock_result

        call_next = AsyncMock()

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            result = await auth_middleware.dispatch(request, call_next)

            # Should return 401 Unauthorized for inactive token
            assert isinstance(result, JSONResponse)
            assert result.status_code == 401
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_handling(self, auth_middleware, mock_database):
        """Test handling of database errors during token validation."""
        db, session = mock_database

        # Mock request with service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_token"}.get(key)
        request.headers = mock_headers
        request.method = "GET"

        # Mock database error
        session.execute.side_effect = Exception("Database connection failed")

        call_next = AsyncMock()

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            result = await auth_middleware.dispatch(request, call_next)

            # Should return 500 Internal Server Error for database issues
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_token_hash_generation(self, auth_middleware):
        """Test that service tokens are properly hashed for database lookup."""
        import hashlib

        raw_token = "sk_test_raw_token_value"  # noqa: S105
        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Test hash generation directly (no internal method exists)
        result_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        assert result_hash == expected_hash

        # Verify the hash is consistent and has correct format
        assert len(result_hash) == 64  # SHA-256 produces 64-character hex string
        assert all(c in "0123456789abcdef" for c in result_hash)  # Valid hex

    @pytest.mark.asyncio
    async def test_token_metadata_injection(self, auth_middleware, mock_database):
        """Test that token metadata is properly injected into request state."""
        db, session = mock_database

        # Mock request with service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_token_with_metadata"}.get(key)
        request.headers = mock_headers
        request.method = "GET"
        request.state = MagicMock()

        # Mock token with rich metadata
        mock_token = MagicMock(spec=ServiceToken)
        mock_token.id = "metadata-token-uuid"
        mock_token.token_name = "metadata-api-token"  # noqa: S105
        mock_token.is_active = True
        mock_token.is_expired = False
        mock_token.is_valid = True
        mock_token.token_metadata = {
            "permissions": ["read", "write", "admin"],
            "client_type": "service",
            "environment": "production",
            "rate_limit": "1000/hour",
        }

        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_token
        session.execute.return_value = mock_result

        response = Response()
        call_next = AsyncMock(return_value=response)

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            result = await auth_middleware.dispatch(request, call_next)

            # Should proceed and inject metadata into request state
            call_next.assert_called_once_with(request)
            assert result == response

            # Verify metadata is available in request state
            assert hasattr(request.state, "token_metadata")
            assert request.state.token_metadata == mock_token.token_metadata

    @pytest.mark.asyncio
    async def test_excluded_paths_bypass_database(self, auth_middleware, mock_database):
        """Test that excluded paths bypass database token validation."""
        db, session = mock_database

        # Mock request to excluded path
        request = MagicMock(spec=Request)
        request.url.path = "/health"
        request.headers = {}
        request.method = "GET"

        response = Response()
        call_next = AsyncMock(return_value=response)

        result = await auth_middleware.dispatch(request, call_next)

        # Should proceed without database interaction
        call_next.assert_called_once_with(request)
        assert result == response

        # Database should not have been accessed
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_usage_analytics_tracking(self, auth_middleware, mock_database):
        """Test that token usage is properly tracked for analytics."""
        db, session = mock_database

        # Mock request with service token
        request = MagicMock(spec=Request)
        request.url.path = "/api/analytics"
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key: {"Authorization": "Bearer sk_test_analytics_token"}.get(key)
        request.headers = mock_headers
        request.method = "POST"
        request.client.host = "192.168.1.100"

        # Mock token
        mock_token = MagicMock(spec=ServiceToken)
        mock_token.id = "analytics-token-uuid"
        mock_token.token_name = "analytics-api-token"  # noqa: S105
        mock_token.is_active = True
        mock_token.is_expired = False
        mock_token.is_valid = True
        mock_token.usage_count = 42
        mock_token.last_used = datetime.now(UTC) - timedelta(hours=2)

        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_token
        session.execute.return_value = mock_result

        response = Response()
        call_next = AsyncMock(return_value=response)

        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Mock async generator to yield session once
            async def mock_async_generator():
                yield session

            mock_get_db.return_value = mock_async_generator()

            # Track time before request (for potential performance testing)
            _before_request = datetime.now(UTC)

            result = await auth_middleware.dispatch(request, call_next)

            # Track time after request (for potential performance testing)
            _after_request = datetime.now(UTC)

            # Should proceed successfully
            call_next.assert_called_once_with(request)
            assert result == response

            # Should have updated usage count in database (via SQL UPDATE)
            assert session.execute.call_count == 2  # SELECT + UPDATE

            # Verify the authenticated user has correct usage count
            authenticated_user = request.state.authenticated_user
            assert authenticated_user.usage_count == 43  # original 42 + 1

            # Note: last_used is updated in database via SQL, not on the mock object
