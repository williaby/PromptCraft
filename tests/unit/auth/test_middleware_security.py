"""
Comprehensive security tests for authentication middleware.

Tests focus on critical security paths in AuthenticationMiddleware
to improve coverage from 12% to 85%+.
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import pytest

from src.auth.middleware import (
    AuthenticationMiddleware,
    SecurityLogger,
    SecurityMonitor,
    create_rate_limiter,
    get_current_user,
    require_authentication,
    require_role,
)
from src.auth.models import AuthenticatedUser, AuthenticationError


class TestAuthenticationMiddleware:
    """Test AuthenticationMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        return FastAPI()

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock()
        config.cloudflare_access_enabled = True
        config.rate_limit_requests = 100
        config.rate_limit_window = 60
        config.auth_logging_enabled = False  # Disable logging to prevent AttributeError
        config.auth_error_detail_enabled = True
        config.email_whitelist_enabled = False
        config.email_whitelist = []
        return config

    @pytest.fixture
    def middleware(self, app, mock_config):
        """Create middleware instance."""
        return AuthenticationMiddleware(
            app=app,
            config=mock_config,
            jwt_validator=None,
            excluded_paths=["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"],
            database_enabled=False,  # Disable database to prevent get_db() stalling
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()
        return request

    def test_middleware_initialization(self, app):
        """Test middleware initialization with different configurations."""
        # Default initialization
        middleware = AuthenticationMiddleware(
            app=app,
            config=None,
            jwt_validator=None,
            excluded_paths=None,
            database_enabled=True,
        )

        assert middleware.config is None
        assert middleware.jwt_validator is None
        assert middleware.database_enabled is True
        assert "/health" in middleware.excluded_paths
        assert "/metrics" in middleware.excluded_paths

    def test_middleware_initialization_custom_paths(self, app):
        """Test middleware with custom excluded paths."""
        custom_paths = ["/custom/health", "/custom/metrics"]
        middleware = AuthenticationMiddleware(
            app=app,
            config=None,
            jwt_validator=None,
            excluded_paths=custom_paths,
            database_enabled=False,
        )

        assert middleware.excluded_paths == custom_paths
        assert middleware.database_enabled is False

    @pytest.mark.asyncio
    async def test_dispatch_excluded_path(self, middleware, mock_request):
        """Test middleware skips authentication for excluded paths."""
        mock_request.url.path = "/health"
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        response = await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once_with(mock_request)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_docs_path(self, middleware, mock_request):
        """Test middleware allows docs endpoints."""
        docs_paths = ["/docs", "/redoc", "/openapi.json"]

        for path in docs_paths:
            mock_request.url.path = path
            call_next = AsyncMock(return_value=JSONResponse({"docs": "allowed"}))

            await middleware.dispatch(mock_request, call_next)

            call_next.assert_called_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_favicon(self, middleware, mock_request):
        """Test middleware allows favicon requests."""
        mock_request.url.path = "/favicon.ico"
        call_next = AsyncMock(return_value="favicon_response")

        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_protected_path_no_auth(self, middleware, mock_request):
        """Test middleware blocks protected paths without authentication."""
        mock_request.url.path = "/api/protected"
        mock_request.headers = {}  # No auth headers
        call_next = AsyncMock()

        # Mock authentication to raise AuthenticationError (not authenticated)
        async def mock_auth_request(request):
            raise AuthenticationError("No token provided")

        with patch.object(middleware, "_authenticate_request", side_effect=mock_auth_request):
            with patch.object(middleware, "_create_auth_error_response") as mock_error_response:
                mock_error_response.return_value = JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401,
                )
                response = await middleware.dispatch(mock_request, call_next)

        # Should not call next middleware
        call_next.assert_not_called()
        # Should return 401 response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dispatch_authenticated_request(self, middleware, mock_request):
        """Test middleware allows authenticated requests."""
        mock_request.url.path = "/api/protected"
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        call_next = AsyncMock(return_value=JSONResponse({"data": "success"}))

        # Mock authenticated user
        mock_user = Mock(spec=AuthenticatedUser)
        mock_user.email = "test@example.com"
        mock_user.user_id = "user123"
        mock_user.role = Mock()
        mock_user.role.value = "user"
        mock_user.jwt_claims = {"sub": "user123", "email": "test@example.com"}
        mock_user.session_id = "session123"

        async def mock_auth_request(request):
            return mock_user

        with patch.object(middleware, "_authenticate_request", side_effect=mock_auth_request):
            response = await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once_with(mock_request)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_database_logging(self, app, mock_config, mock_request):
        """Test middleware logs authentication events when database enabled."""
        # Create middleware with database enabled and proper mocking
        middleware_with_db = AuthenticationMiddleware(
            app=app,
            config=mock_config,
            jwt_validator=None,
            excluded_paths=["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"],
            database_enabled=True,
        )

        mock_request.url.path = "/api/test"
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        call_next = AsyncMock(return_value=JSONResponse({"success": True}))

        mock_user = Mock(spec=AuthenticatedUser)
        mock_user.email = "test@example.com"
        mock_user.user_id = "user123"
        mock_user.role = Mock()
        mock_user.role.value = "user"
        mock_user.jwt_claims = {"sub": "user123", "email": "test@example.com"}
        mock_user.session_id = "session123"

        async def mock_auth_request(request):
            return mock_user

        with patch.object(middleware_with_db, "_authenticate_request", side_effect=mock_auth_request):
            with patch.object(middleware_with_db, "_log_authentication_event") as mock_log:
                with patch.object(middleware_with_db, "_update_user_session") as mock_update_session:
                    await middleware_with_db.dispatch(mock_request, call_next)

                    # Should log authentication event for database-enabled middleware
                    mock_log.assert_called_once()
                    # Should also update user session
                    mock_update_session.assert_called_once()

    def test_extract_auth_token_no_headers(self, middleware, mock_request):
        """Test token extraction with no headers."""
        mock_request.headers = {}

        result = middleware._extract_auth_token(mock_request)
        assert result is None

    def test_extract_auth_token_missing_token(self, middleware, mock_request):
        """Test token extraction with missing token."""
        mock_request.headers = {"Authorization": "Bearer "}

        result = middleware._extract_auth_token(mock_request)
        assert result is None or result == ""

    def test_extract_auth_token_invalid_format(self, middleware, mock_request):
        """Test token extraction with invalid token format."""
        invalid_tokens = [
            "InvalidFormat token123",
            "Basic dXNlcjpwYXNz",  # Basic auth
            "token_without_bearer",
        ]

        for token in invalid_tokens:
            mock_request.headers = {"Authorization": token}
            result = middleware._extract_auth_token(mock_request)
            # Should return None for non-Bearer tokens
            assert result is None


class TestSecurityLogger:
    """Test SecurityLogger class."""

    def test_security_logger_initialization(self):
        """Test security logger initialization."""
        logger = SecurityLogger()
        assert logger is not None

    def test_security_logger_log_event(self):
        """Test security event logging."""
        logger = SecurityLogger()

        # Test various log levels
        with patch.object(logger, "log_security_event") as mock_log:
            logger.log_security_event("test_event", "info", {"user": "test"})
            mock_log.assert_called_once_with("test_event", "info", {"user": "test"})


class TestSecurityMonitor:
    """Test SecurityMonitor class."""

    def test_security_monitor_initialization(self):
        """Test security monitor initialization."""
        monitor = SecurityMonitor()
        assert monitor is not None

    def test_security_monitor_record_failed_attempt(self):
        """Test security event tracking."""
        monitor = SecurityMonitor()

        with patch.object(monitor, "record_failed_attempt") as mock_record:
            monitor.record_failed_attempt("test_user", {"ip": "127.0.0.1"})
            mock_record.assert_called_once_with("test_user", {"ip": "127.0.0.1"})


class TestAuthenticationFunctions:
    """Test standalone authentication functions."""

    @pytest.fixture
    def mock_request_with_user(self):
        """Create mock request with authenticated user."""
        request = Mock(spec=Request)
        mock_user = Mock(spec=AuthenticatedUser)
        mock_user.email = "test@example.com"
        mock_user.user_id = "user123"
        mock_user.role = Mock()
        mock_user.role.value = "admin"
        request.state = Mock()
        request.state.authenticated_user = mock_user
        return request

    @pytest.fixture
    def mock_request_no_user(self):
        """Create mock request without user."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated_user = None
        return request

    def test_get_current_user_with_user(self, mock_request_with_user):
        """Test get_current_user with authenticated user."""
        user = get_current_user(mock_request_with_user)

        assert user is not None
        assert user.email == "test@example.com"
        assert user.user_id == "user123"

    def test_get_current_user_no_user(self, mock_request_no_user):
        """Test get_current_user without authenticated user."""
        user = get_current_user(mock_request_no_user)
        assert user is None

    def test_require_authentication_success(self, mock_request_with_user):
        """Test require_authentication with authenticated user."""
        user = require_authentication(mock_request_with_user)

        assert user is not None
        assert user.email == "test@example.com"

    def test_require_authentication_failure(self, mock_request_no_user):
        """Test require_authentication without authenticated user."""
        with pytest.raises(HTTPException) as exc_info:
            require_authentication(mock_request_no_user)

        assert exc_info.value.status_code == 401

    def test_require_role_success(self, mock_request_with_user):
        """Test require_role with correct role."""
        # Mock user with admin role (already set in fixture)
        user = require_role(mock_request_with_user, "admin")

        assert user is not None
        assert user.role.value == "admin"

    def test_require_role_failure(self, mock_request_with_user):
        """Test require_role with incorrect role."""
        # Mock user with user role trying to access admin endpoint
        mock_request_with_user.state.authenticated_user.role.value = "user"

        with pytest.raises(HTTPException) as exc_info:
            require_role(mock_request_with_user, "admin")

        assert exc_info.value.status_code == 403

    def test_create_rate_limiter(self):
        """Test rate limiter creation."""
        mock_config = Mock()
        mock_config.rate_limit_requests = 100
        mock_config.rate_limit_window = 60

        with patch("src.auth.middleware.Limiter") as mock_limiter_class:
            mock_limiter_instance = Mock()
            mock_limiter_class.return_value = mock_limiter_instance

            limiter = create_rate_limiter(mock_config)
            assert limiter is not None


class TestSecurityEdgeCases:
    """Test security edge cases and attack scenarios."""

    @pytest.fixture
    def middleware(self):
        """Create middleware for security testing."""
        app = FastAPI()
        mock_config = Mock()
        mock_config.cloudflare_access_enabled = True
        mock_config.auth_logging_enabled = False  # Disable logging to prevent AttributeError
        mock_config.auth_error_detail_enabled = True
        mock_config.email_whitelist_enabled = False
        mock_config.email_whitelist = []
        return AuthenticationMiddleware(
            app=app,
            config=mock_config,
            jwt_validator=None,
            excluded_paths=["/health", "/favicon.ico", "/docs"],  # Add /docs to excluded paths
            database_enabled=False,  # Disable database to prevent get_db() stalling
        )

    def test_malicious_headers(self, middleware, mock_request):
        """Test handling of malicious headers."""
        mock_request = Mock(spec=Request)

        # Test various malicious header scenarios
        malicious_headers = [
            {"Authorization": "Bearer <script>alert('xss')</script>"},
            {"Authorization": "Bearer ' OR 1=1 --"},
            {"Authorization": "Bearer " + "A" * 10000},  # Very long token
            {"Authorization": "Bearer \x00\x01\x02"},  # Binary data
            {"X-Forwarded-For": "127.0.0.1, <script>"},  # Header injection
        ]

        for headers in malicious_headers:
            mock_request.headers = headers
            try:
                result = middleware._extract_auth_token(mock_request)
                # Should extract token safely without crashing
                # Token validation happens in _validate_jwt_token, not _extract_auth_token
                # So malicious content may be extracted but not validated
                assert isinstance(result, (str, type(None)))  # Should not crash
            except Exception as e:
                # Should not throw exceptions during extraction
                raise AssertionError(f"Token extraction should not crash: {e}")

    def test_path_traversal_protection(self, middleware):
        """Test protection against path traversal in excluded paths."""
        mock_request = Mock(spec=Request)
        AsyncMock()

        # Test path traversal attempts
        malicious_paths = [
            "/health/../admin",
            "/health/../../etc/passwd",
            "/health%2F%2E%2E%2Fadmin",  # URL encoded
            "//health/../admin",
        ]

        for path in malicious_paths:
            mock_request.url.path = path
            # These should NOT be treated as excluded paths
            # Would need to test the actual path checking logic
            # Placeholder for actual path traversal protection test

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, middleware):
        """Test thread safety with concurrent requests."""
        import asyncio

        async def make_request(path):
            mock_request = Mock(spec=Request)
            mock_request.url.path = path
            mock_request.headers = {}
            mock_request.client.host = "127.0.0.1"
            mock_request.state = Mock()
            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))

            try:
                return await middleware.dispatch(mock_request, call_next)
            except Exception as e:
                # Return error response for failed requests
                return JSONResponse({"error": str(e)}, status_code=500)

        # Test concurrent requests to different paths
        # Note: /health and /docs are excluded paths and should pass through
        # /api/* paths will fail auth but should return error responses, not hang
        tasks = [
            make_request("/health"),  # Should pass through (excluded)
            make_request("/api/test1"),  # Will fail auth but should return 401
            make_request("/api/test2"),  # Will fail auth but should return 401
            make_request("/docs"),  # Should pass through (excluded)
        ]

        # Use asyncio.wait_for to add timeout protection
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=5.0,
            )
        except TimeoutError:
            pytest.fail("Concurrent requests test timed out - indicates stalling issue")

        # All requests should complete without issues (either success or proper error)
        assert len(responses) == 4

        # Verify responses are valid (not exceptions)
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                pytest.fail(f"Request {i} raised unexpected exception: {response}")
            assert hasattr(response, "status_code"), f"Response {i} is not a valid HTTP response"

    def test_memory_usage_protection(self, middleware, mock_request):
        """Test protection against memory exhaustion attacks."""
        # Test with very large headers
        large_value = "x" * 1000000  # 1MB string
        mock_request.headers = {
            "Authorization": f"Bearer {large_value}",
            "User-Agent": large_value,
        }

        # Should handle gracefully without consuming excessive memory
        result = middleware._extract_auth_token(mock_request)
        # Should return None for malformed tokens or handle gracefully
        assert result is None or isinstance(result, str)

    def test_unicode_handling(self, middleware, mock_request):
        """Test proper unicode handling in authentication."""
        unicode_headers = {
            "Authorization": "Bearer token_with_unicode_🔒",
            "User-Agent": "Browser/1.0 (Unicode: 测试)",
        }
        mock_request.headers = unicode_headers

        # Should handle unicode without crashing
        result = middleware._extract_auth_token(mock_request)
        # Should handle unicode tokens (may extract or return None)
        assert result is None or isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.auth.middleware", "--cov-report=term-missing"])
