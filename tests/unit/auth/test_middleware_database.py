"""Unit tests for authentication middleware database integration.

Tests the new database integration features added to AuthenticationMiddleware
for Phase 1 Issue AUTH-1 implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.auth.config import AuthenticationConfig
from src.auth.middleware import AuthenticationMiddleware
from src.auth.models import AuthenticatedUser, AuthenticationError, UserRole
from src.database import DatabaseError


@pytest.mark.auth
@pytest.mark.unit
@pytest.mark.fast
class TestAuthenticationMiddlewareDatabaseIntegration:
    """Test authentication middleware database integration features."""

    @pytest.fixture
    def auth_config(self):
        """Authentication configuration for testing."""
        return AuthenticationConfig(
            cloudflare_access_enabled=True,
            cloudflare_team_domain="test",
            cloudflare_jwks_url="https://test.com/jwks",
            auth_logging_enabled=True,
        )

    @pytest.fixture
    def mock_jwt_validator(self):
        """Mock JWT validator for testing."""
        validator = MagicMock()
        validator.validate_token.return_value = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )
        return validator

    @pytest.fixture
    def mock_request(self):
        """Mock request for testing."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {
            "CF-Access-Jwt-Assertion": "test-jwt-token",
            "CF-Connecting-IP": "192.168.1.100",
            "User-Agent": "Mozilla/5.0 Test Browser",
            "CF-Ray": "test-ray-12345",
        }
        request.state = MagicMock()
        return request

    @pytest.fixture
    def mock_database_manager(self):
        """Mock database manager for testing."""
        manager = AsyncMock()
        session = AsyncMock()

        # Mock session context manager
        manager.get_session.return_value.__aenter__ = AsyncMock(return_value=session)
        manager.get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock session operations
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = AsyncMock()

        return manager, session

    def test_middleware_initialization_database_enabled(self, auth_config, mock_jwt_validator):
        """Test middleware initialization with database enabled."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        assert middleware.database_enabled is True

    def test_middleware_initialization_database_disabled(self, auth_config, mock_jwt_validator):
        """Test middleware initialization with database disabled."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=False,
        )

        assert middleware.database_enabled is False

    async def test_update_user_session_success(self, auth_config, mock_jwt_validator, mock_request):
        """Test successful user session update."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub-123", "email": "test@example.com"},
        )

        mock_manager, mock_session = self.mock_database_manager()

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            await middleware._update_user_session(authenticated_user, mock_request)

            # Verify database operations were called
            mock_manager.get_session.assert_called_once()
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

    async def test_update_user_session_database_disabled(self, auth_config, mock_jwt_validator, mock_request):
        """Test user session update when database is disabled."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=False,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        # Should not raise exception and should not call database
        with patch("src.auth.middleware.get_database_manager") as mock_get_db:
            await middleware._update_user_session(authenticated_user, mock_request)
            mock_get_db.assert_not_called()

    async def test_update_user_session_database_error_graceful_degradation(
        self,
        auth_config,
        mock_jwt_validator,
        mock_request,
    ):
        """Test graceful degradation when database session update fails."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        # Mock database manager to raise DatabaseError
        mock_manager = AsyncMock()
        mock_manager.get_session.side_effect = DatabaseError("Database unavailable")

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            # Should not raise exception (graceful degradation)
            await middleware._update_user_session(authenticated_user, mock_request)

    async def test_update_user_session_unexpected_error_graceful_degradation(
        self,
        auth_config,
        mock_jwt_validator,
        mock_request,
    ):
        """Test graceful degradation when unexpected error occurs."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        # Mock database manager to raise unexpected error
        mock_manager = AsyncMock()
        mock_manager.get_session.side_effect = Exception("Unexpected error")

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            # Should not raise exception (graceful degradation)
            await middleware._update_user_session(authenticated_user, mock_request)

    async def test_log_authentication_event_success(self, auth_config, mock_jwt_validator, mock_request):
        """Test successful authentication event logging."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        mock_manager, mock_session = self.mock_database_manager()

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            await middleware._log_authentication_event(
                authenticated_user=authenticated_user,
                request=mock_request,
                success=True,
                jwt_time_ms=12.5,
                db_time_ms=8.3,
                total_time_ms=45.7,
            )

            # Verify database operations were called
            mock_manager.get_session.assert_called_once()
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    async def test_log_authentication_event_failure(self, auth_config, mock_jwt_validator, mock_request):
        """Test authentication event logging for failures."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        mock_manager, mock_session = self.mock_database_manager()

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            await middleware._log_authentication_event(
                authenticated_user=None,
                request=mock_request,
                success=False,
                jwt_time_ms=0,
                db_time_ms=0,
                total_time_ms=25.3,
                error_message="JWT token invalid",
            )

            # Verify database operations were called
            mock_manager.get_session.assert_called_once()
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    async def test_log_authentication_event_database_disabled(self, auth_config, mock_jwt_validator, mock_request):
        """Test authentication event logging when database is disabled."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=False,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        # Should not call database
        with patch("src.auth.middleware.get_database_manager") as mock_get_db:
            await middleware._log_authentication_event(
                authenticated_user=authenticated_user,
                request=mock_request,
                success=True,
                jwt_time_ms=10.0,
                db_time_ms=5.0,
                total_time_ms=30.0,
            )
            mock_get_db.assert_not_called()

    async def test_log_authentication_event_database_error_graceful_degradation(
        self,
        auth_config,
        mock_jwt_validator,
        mock_request,
    ):
        """Test graceful degradation when event logging fails."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        # Mock database manager to raise DatabaseError
        mock_manager = AsyncMock()
        mock_manager.get_session.side_effect = DatabaseError("Database unavailable")

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            # Should not raise exception (graceful degradation)
            await middleware._log_authentication_event(
                authenticated_user=authenticated_user,
                request=mock_request,
                success=True,
                jwt_time_ms=10.0,
                db_time_ms=5.0,
                total_time_ms=30.0,
            )

    def test_get_client_ip_cloudflare_header(self, auth_config, mock_jwt_validator):
        """Test client IP extraction from Cloudflare headers."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
        )

        request = MagicMock(spec=Request)
        request.headers = {"CF-Connecting-IP": "203.0.113.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_x_forwarded_for(self, auth_config, mock_jwt_validator):
        """Test client IP extraction from X-Forwarded-For header."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
        )

        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"  # Should get first IP in chain

    def test_get_client_ip_x_real_ip(self, auth_config, mock_jwt_validator):
        """Test client IP extraction from X-Real-IP header."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
        )

        request = MagicMock(spec=Request)
        request.headers = {"X-Real-IP": "203.0.113.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_fallback_to_client_host(self, auth_config, mock_jwt_validator):
        """Test client IP fallback to request.client.host."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
        )

        request = MagicMock(spec=Request)
        request.headers = {}
        request.client.host = "192.168.1.100"

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_no_ip_available(self, auth_config, mock_jwt_validator):
        """Test client IP extraction when no IP is available."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
        )

        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip is None

    async def test_dispatch_with_database_integration_success(self, auth_config, mock_jwt_validator, mock_request):
        """Test complete dispatch flow with database integration."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})

        mock_manager, mock_session = self.mock_database_manager()

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            response = await middleware.dispatch(mock_request, mock_call_next)

            assert response.status_code == 200

            # Verify user context was set
            assert hasattr(mock_request.state, "authenticated_user")
            assert hasattr(mock_request.state, "user_email")
            assert hasattr(mock_request.state, "user_role")

            # Verify database operations were called (session update + event logging)
            assert mock_manager.get_session.call_count >= 2
            assert mock_session.commit.call_count >= 2

    async def test_dispatch_with_database_integration_auth_failure(self, auth_config, mock_request):
        """Test dispatch flow with authentication failure and database logging."""
        app = FastAPI()

        # Mock JWT validator to raise authentication error
        mock_jwt_validator = MagicMock()
        mock_jwt_validator.validate_token.side_effect = AuthenticationError("Invalid token", 401)

        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})

        mock_manager, mock_session = self.mock_database_manager()

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            response = await middleware.dispatch(mock_request, mock_call_next)

            assert response.status_code == 401

            # Verify failure event was logged
            mock_manager.get_session.assert_called_once()
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    async def test_dispatch_performance_metrics_collection(self, auth_config, mock_jwt_validator, mock_request):
        """Test that performance metrics are collected during dispatch."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})

        mock_manager, mock_session = self.mock_database_manager()

        # Mock time.time to control timing
        start_time = 1000.0
        times = [start_time, start_time + 0.010, start_time + 0.015, start_time + 0.050]

        with (
            patch("src.auth.middleware.get_database_manager", return_value=mock_manager),
            patch("time.time", side_effect=times),
        ):

            response = await middleware.dispatch(mock_request, mock_call_next)

            assert response.status_code == 200

            # Verify event logging was called with performance metrics
            mock_session.add.assert_called()

            # Get the authentication event that was added
            add_call_args = mock_session.add.call_args[0][0]
            assert hasattr(add_call_args, "performance_metrics")
            assert add_call_args.performance_metrics is not None

    async def test_dispatch_database_completely_unavailable(self, auth_config, mock_jwt_validator, mock_request):
        """Test dispatch when database is completely unavailable."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        async def mock_call_next(request):
            return JSONResponse(content={"status": "success"})

        # Mock get_database_manager to raise exception
        with patch("src.auth.middleware.get_database_manager", side_effect=Exception("DB unavailable")):
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Authentication should still succeed (graceful degradation)
            assert response.status_code == 200

            # Verify user context was still set
            assert hasattr(mock_request.state, "authenticated_user")
            assert mock_request.state.user_email == "test@example.com"
