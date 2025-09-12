"""
Comprehensive tests for authentication middleware.

This test suite provides thorough coverage of the AuthenticationMiddleware class,
ServiceTokenUser, security logging components, and all helper functions to achieve
>90% code coverage.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

from fastapi import Response
from fastapi.responses import JSONResponse
import pytest

from src.auth.middleware import (
    AuthenticationMiddleware,
    SecurityLogger,
    SecurityMonitor,
    ServiceTokenUser,
    create_rate_limiter,
    get_current_user,
    require_authentication,
    require_role,
    setup_authentication,
)
from src.auth.models import AuthenticationError, JWTValidationError, SecurityEventSeverity, SecurityEventType, UserRole
from src.database.models import AuthenticationEvent


class TestServiceTokenUser:
    """Test cases for ServiceTokenUser class."""

    def test_service_token_user_init(self):
        """Test ServiceTokenUser initialization with all parameters."""
        user = ServiceTokenUser(
            token_id="service-123",
            token_name="test_service_token",
            metadata={"permissions": ["read", "write"]},
            usage_count=5,
        )

        assert user.token_id == "service-123"
        assert user.token_name == "test_service_token"
        assert user.metadata == {"permissions": ["read", "write"]}
        assert user.usage_count == 5
        assert user.email == "test_service_token@service.local"
        assert user.user_type == "service_token"

    def test_service_token_user_has_permission(self):
        """Test ServiceTokenUser has_permission method."""
        user = ServiceTokenUser(
            token_id="service-456",
            token_name="admin_token",
            metadata={"permissions": ["read", "write", "admin"]},
            usage_count=0,
        )

        assert user.has_permission("read") is True
        assert user.has_permission("write") is True
        assert user.has_permission("admin") is True
        assert user.has_permission("delete") is True  # admin has all permissions
        assert user.has_permission("nonexistent") is True  # admin has all permissions

    def test_service_token_user_has_permission_limited(self):
        """Test ServiceTokenUser has_permission with limited permissions."""
        user = ServiceTokenUser(
            token_id="service-789",
            token_name="read_only_token",
            metadata={"permissions": ["read"]},
            usage_count=0,
        )

        assert user.has_permission("read") is True
        assert user.has_permission("write") is False
        assert user.has_permission("admin") is False

    def test_service_token_user_no_permissions(self):
        """Test ServiceTokenUser with no permissions."""
        user = ServiceTokenUser(token_id="service-000", token_name="no_perms_token", metadata={}, usage_count=0)

        assert user.has_permission("read") is False
        assert user.has_permission("write") is False


class TestSecurityLogger:
    """Test cases for SecurityLogger compatibility class."""

    def test_security_logger_init(self):
        """Test SecurityLogger initialization."""
        logger = SecurityLogger()
        assert logger.logger.name == "security"

    def test_security_logger_log_security_event(self):
        """Test SecurityLogger log_security_event method."""
        with patch.object(logging.getLogger("security"), "info") as mock_info:
            logger = SecurityLogger()
            logger.log_security_event("AUTH_SUCCESS", "User authenticated", "INFO", user="test@example.com")

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "[AUTH_SUCCESS]" in call_args
            assert "User authenticated" in call_args
            assert "user" in call_args

    def test_security_logger_log_security_event_critical(self):
        """Test SecurityLogger with critical severity."""
        with patch.object(logging.getLogger("security"), "critical") as mock_critical:
            logger = SecurityLogger()
            logger.log_security_event("BREACH", "Security breach detected", "CRITICAL")

            mock_critical.assert_called_once()

    def test_security_logger_log_security_event_high(self):
        """Test SecurityLogger with high severity."""
        with patch.object(logging.getLogger("security"), "error") as mock_error:
            logger = SecurityLogger()
            logger.log_security_event("FAILURE", "Auth failure", "HIGH")

            mock_error.assert_called_once()

    def test_security_logger_log_security_event_medium(self):
        """Test SecurityLogger with medium severity."""
        with patch.object(logging.getLogger("security"), "warning") as mock_warning:
            logger = SecurityLogger()
            logger.log_security_event("WARNING", "Rate limit approached", "MEDIUM")

            mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_security_logger_log_event_enum_types(self):
        """Test SecurityLogger log_event method with enum types."""
        with patch.object(logging.getLogger("security"), "info") as mock_info:
            logger = SecurityLogger()

            await logger.log_event(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                severity=SecurityEventSeverity.INFO,
                user_id="test@example.com",
                ip_address="127.0.0.1",
            )

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "[LOGIN_SUCCESS]" in call_args
            assert "test@example.com" in call_args

    @pytest.mark.asyncio
    async def test_security_logger_log_event_string_types(self):
        """Test SecurityLogger log_event method with string types."""
        with patch.object(logging.getLogger("security"), "warning") as mock_warning:
            logger = SecurityLogger()

            await logger.log_event(
                event_type="LOGIN_FAILURE",
                severity="WARNING",
                user_id="test@example.com",
                details={"error": "Invalid token"},
            )

            mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_security_logger_log_event_critical_severity(self):
        """Test SecurityLogger log_event with critical severity."""
        with patch.object(logging.getLogger("security"), "critical") as mock_critical:
            logger = SecurityLogger()

            await logger.log_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                severity=SecurityEventSeverity.CRITICAL,
                details={"error": "System failure"},
            )

            mock_critical.assert_called_once()

    @pytest.mark.asyncio
    async def test_security_logger_log_event_minimal_data(self):
        """Test SecurityLogger log_event with minimal data."""
        with patch.object(logging.getLogger("security"), "info") as mock_info:
            logger = SecurityLogger()

            await logger.log_event(event_type="SIMPLE_EVENT", severity=None, user_id=None, ip_address=None)

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "[SIMPLE_EVENT]" in call_args


class TestSecurityMonitor:
    """Test cases for SecurityMonitor compatibility class."""

    def test_security_monitor_init(self):
        """Test SecurityMonitor initialization."""
        monitor = SecurityMonitor()
        assert monitor.logger.name == "security.monitor"
        assert isinstance(monitor.failed_attempts, dict)

    def test_security_monitor_record_failed_attempt(self):
        """Test SecurityMonitor record_failed_attempt method."""
        with patch.object(logging.getLogger("security.monitor"), "warning") as mock_warning:
            monitor = SecurityMonitor()
            monitor.record_failed_attempt("user@example.com")

            assert monitor.failed_attempts["user@example.com"] == 1
            mock_warning.assert_called_once()

            # Record another attempt
            monitor.record_failed_attempt("user@example.com")
            assert monitor.failed_attempts["user@example.com"] == 2

    def test_security_monitor_record_failed_attempt_with_info(self):
        """Test SecurityMonitor record_failed_attempt with request info."""
        with patch.object(logging.getLogger("security.monitor"), "warning"):
            monitor = SecurityMonitor()
            request_info = {"ip": "127.0.0.1", "user_agent": "TestClient"}
            monitor.record_failed_attempt("user@example.com", request_info)

            assert monitor.failed_attempts["user@example.com"] == 1

    def test_security_monitor_is_blocked(self):
        """Test SecurityMonitor is_blocked method."""
        monitor = SecurityMonitor()

        assert monitor.is_blocked("user@example.com") is False

        # Simulate 11 failed attempts
        monitor.failed_attempts["user@example.com"] = 11
        assert monitor.is_blocked("user@example.com") is True

    def test_security_monitor_reset_failed_attempts(self):
        """Test SecurityMonitor reset_failed_attempts method."""
        monitor = SecurityMonitor()
        monitor.failed_attempts["user@example.com"] = 5

        monitor.reset_failed_attempts("user@example.com")
        assert "user@example.com" not in monitor.failed_attempts

    def test_security_monitor_reset_nonexistent_user(self):
        """Test SecurityMonitor reset for nonexistent user."""
        monitor = SecurityMonitor()
        # Should not raise an error
        monitor.reset_failed_attempts("nonexistent@example.com")

    @pytest.mark.asyncio
    async def test_security_monitor_track_failed_authentication(self):
        """Test SecurityMonitor track_failed_authentication method."""
        with patch.object(logging.getLogger("security.monitor"), "warning"):
            monitor = SecurityMonitor()

            alerts = await monitor.track_failed_authentication(
                user_id="user@example.com",
                ip_address="127.0.0.1",
                user_agent="TestClient",
                endpoint="/api/auth",
                error_type="invalid_token",
            )

            assert alerts == []  # Simplified monitoring returns empty alerts
            assert monitor.failed_attempts["user@example.com"] == 1

    @pytest.mark.asyncio
    async def test_security_monitor_track_failed_auth_no_user_id(self):
        """Test SecurityMonitor track_failed_authentication without user_id."""
        with patch.object(logging.getLogger("security.monitor"), "warning"):
            monitor = SecurityMonitor()

            await monitor.track_failed_authentication(
                user_id=None,
                ip_address="192.168.1.1",
                details={"reason": "no_token"},
            )

            assert monitor.failed_attempts["192.168.1.1"] == 1

    @pytest.mark.asyncio
    async def test_security_monitor_track_failed_auth_no_identifiers(self):
        """Test SecurityMonitor track_failed_authentication without identifiers."""
        with patch.object(logging.getLogger("security.monitor"), "warning"):
            monitor = SecurityMonitor()

            await monitor.track_failed_authentication(
                user_id=None,
                ip_address=None,
                details={"reason": "malformed_request"},
            )

            assert monitor.failed_attempts["unknown"] == 1


class TestAuthenticationMiddleware:
    """Comprehensive test cases for AuthenticationMiddleware class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock authentication configuration."""
        config = Mock()
        config.cloudflare_access_enabled = True
        config.auth_logging_enabled = True
        config.auth_error_detail_enabled = True
        config.email_whitelist_enabled = False
        config.email_whitelist = []
        return config

    @pytest.fixture
    def mock_jwt_validator(self):
        """Create mock JWT validator."""
        validator = Mock()
        validator.validate_token = Mock()
        return validator

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app."""
        return Mock()

    @pytest.fixture
    def middleware(self, mock_app, mock_config, mock_jwt_validator):
        """Create AuthenticationMiddleware instance."""
        return AuthenticationMiddleware(
            app=mock_app,
            config=mock_config,
            jwt_validator=mock_jwt_validator,
            excluded_paths=["/health", "/metrics"],
            database_enabled=True,
        )

    def test_middleware_init(self, mock_app, mock_config, mock_jwt_validator):
        """Test middleware initialization with all parameters."""
        middleware = AuthenticationMiddleware(
            app=mock_app,
            config=mock_config,
            jwt_validator=mock_jwt_validator,
            excluded_paths=["/custom", "/health"],
            database_enabled=False,
        )

        assert middleware.config == mock_config
        assert middleware.jwt_validator == mock_jwt_validator
        assert middleware.database_enabled is False
        assert "/custom" in middleware.excluded_paths
        assert "/health" in middleware.excluded_paths

    def test_middleware_init_defaults(self, mock_app):
        """Test middleware initialization with defaults."""
        middleware = AuthenticationMiddleware(app=mock_app)

        assert middleware.config is None
        assert middleware.jwt_validator is None
        assert middleware.database_enabled is True
        assert "/health" in middleware.excluded_paths
        assert "/metrics" in middleware.excluded_paths

    def test_is_excluded_path(self, middleware):
        """Test _is_excluded_path method."""
        assert middleware._is_excluded_path("/health") is True
        assert middleware._is_excluded_path("/metrics") is True
        assert middleware._is_excluded_path("/health/detailed") is True
        assert middleware._is_excluded_path("/api/protected") is False
        assert middleware._is_excluded_path("/") is False

    def test_is_excluded_path_exact_match(self):
        """Test _is_excluded_path with exact match only."""
        middleware = AuthenticationMiddleware(app=Mock(), excluded_paths=["/api/public"])

        assert middleware._is_excluded_path("/api/public") is True
        assert middleware._is_excluded_path("/api/public/sub") is True
        assert middleware._is_excluded_path("/api/private") is False

    @pytest.mark.asyncio
    async def test_dispatch_excluded_path(self, middleware):
        """Test dispatch method with excluded path."""
        request = Mock()
        request.url.path = "/health"

        call_next = AsyncMock()
        call_next.return_value = Response(content="OK", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_auth_disabled(self, mock_app, mock_jwt_validator):
        """Test dispatch when authentication is disabled."""
        mock_config = Mock()
        mock_config.cloudflare_access_enabled = False

        middleware = AuthenticationMiddleware(app=mock_app, config=mock_config, jwt_validator=mock_jwt_validator)

        request = Mock()
        request.url.path = "/api/protected"

        call_next = AsyncMock()
        call_next.return_value = Response(content="Success", status_code=200)

        with patch.object(middleware, "_is_excluded_path", return_value=False):
            with patch("src.auth.middleware.logger.debug") as mock_debug:
                response = await middleware.dispatch(request, call_next)

                assert response.status_code == 200
                call_next.assert_called_once_with(request)
                mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_auth_token_cf_access_jwt(self):
        """Test _extract_auth_token with Cloudflare Access JWT header."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {"CF-Access-Jwt-Assertion": "cf-jwt-token-123"}

        with patch("src.auth.middleware.logger.debug") as mock_debug:
            token = middleware._extract_auth_token(request)
            assert token == "cf-jwt-token-123"
            mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_auth_token_authorization_bearer(self):
        """Test _extract_auth_token with Authorization Bearer header."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {"Authorization": "Bearer auth-bearer-token"}

        token = middleware._extract_auth_token(request)
        assert token == "auth-bearer-token"

    @pytest.mark.asyncio
    async def test_extract_auth_token_service_token_bearer(self):
        """Test _extract_auth_token with service token in Bearer header."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {"Authorization": "Bearer sk_service_token_123"}

        with patch("src.auth.middleware.logger.debug") as mock_debug:
            token = middleware._extract_auth_token(request)
            assert token == "sk_service_token_123"
            mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_auth_token_custom_jwt_header(self):
        """Test _extract_auth_token with custom JWT header."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {"X-JWT-Token": "custom-jwt-token"}

        token = middleware._extract_auth_token(request)
        assert token == "custom-jwt-token"

    @pytest.mark.asyncio
    async def test_extract_auth_token_service_token_header(self):
        """Test _extract_auth_token with service token header."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {"X-Service-Token": "direct-service-token"}

        token = middleware._extract_auth_token(request)
        assert token == "direct-service-token"

    @pytest.mark.asyncio
    async def test_extract_auth_token_none(self):
        """Test _extract_auth_token when no token is present."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {}

        with patch("src.auth.middleware.logger.debug") as mock_debug:
            token = middleware._extract_auth_token(request)
            assert token is None
            mock_debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_auth_token_priority_order(self):
        """Test _extract_auth_token priority order."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {
            "CF-Access-Jwt-Assertion": "cf-token",
            "Authorization": "Bearer auth-token",
            "X-JWT-Token": "custom-token",
            "X-Service-Token": "service-token",
        }

        # CF-Access-Jwt-Assertion should have highest priority
        token = middleware._extract_auth_token(request)
        assert token == "cf-token"

    def test_extract_jwt_token_legacy_method(self):
        """Test _extract_jwt_token legacy method."""
        middleware = AuthenticationMiddleware(app=Mock())

        request = Mock()
        request.headers = {"CF-Access-Jwt-Assertion": "legacy-jwt-token"}

        with patch.object(middleware, "_extract_auth_token", return_value="legacy-jwt-token") as mock_extract:
            token = middleware._extract_jwt_token(request)
            assert token == "legacy-jwt-token"
            mock_extract.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_validate_jwt_token_success(self, middleware):
        """Test _validate_jwt_token success scenario."""
        request = Mock()
        token = "valid-jwt-token"

        # Mock authenticated user
        mock_user = Mock()
        mock_user.email = "test@example.com"
        middleware.jwt_validator.validate_token.return_value = mock_user

        with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
            user = await middleware._validate_jwt_token(request, token)

            assert user == mock_user
            middleware.jwt_validator.validate_token.assert_called_once_with(token, email_whitelist=None)
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_jwt_token_with_whitelist(self, middleware):
        """Test _validate_jwt_token with email whitelist."""
        request = Mock()
        token = "valid-jwt-token"

        # Enable email whitelist
        middleware.config.email_whitelist_enabled = True
        middleware.config.email_whitelist = ["allowed@example.com"]

        mock_user = Mock()
        mock_user.email = "allowed@example.com"
        middleware.jwt_validator.validate_token.return_value = mock_user

        with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock):
            user = await middleware._validate_jwt_token(request, token)

            assert user == mock_user
            middleware.jwt_validator.validate_token.assert_called_once_with(
                token,
                email_whitelist=["allowed@example.com"],
            )

    @pytest.mark.asyncio
    async def test_validate_jwt_token_validation_error(self, middleware):
        """Test _validate_jwt_token with validation error."""
        request = Mock()
        token = "invalid-jwt-token"

        # Mock JWT validation error
        jwt_error = JWTValidationError("Invalid token format")
        middleware.jwt_validator.validate_token.side_effect = jwt_error

        with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
            with pytest.raises(AuthenticationError) as exc_info:
                await middleware._validate_jwt_token(request, token)

            assert "Token validation failed" in str(exc_info.value)
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_service_token_success(self, middleware):
        """Test _validate_service_token success scenario."""
        request = Mock()
        token = "sk_valid_service_token"

        # Mock database session and token record
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_token_record = Mock()
        mock_token_record.id = 123
        mock_token_record.token_name = "test_service_token"
        mock_token_record.token_metadata = {"permissions": ["read", "write"]}
        mock_token_record.usage_count = 5
        mock_token_record.is_active = True
        mock_token_record.is_expired = False

        mock_result.fetchone.return_value = mock_token_record
        mock_session.execute.return_value = mock_result

        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
                user = await middleware._validate_service_token(request, token)

                assert isinstance(user, ServiceTokenUser)
                assert user.token_name == "test_service_token"
                assert user.metadata == {"permissions": ["read", "write"]}
                assert user.usage_count == 6  # Incremented
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_service_token_not_found(self, middleware):
        """Test _validate_service_token when token not found."""
        request = Mock()
        token = "sk_nonexistent_token"

        # Mock database session with no token found
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
                with pytest.raises(AuthenticationError) as exc_info:
                    await middleware._validate_service_token(request, token)

                assert "Invalid service token" in str(exc_info.value)
                assert exc_info.value.status_code == 401
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_service_token_inactive(self, middleware):
        """Test _validate_service_token with inactive token."""
        request = Mock()
        token = "sk_inactive_token"

        # Mock inactive token record
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_token_record = Mock()
        mock_token_record.token_name = "inactive_token"
        mock_token_record.is_active = False
        mock_token_record.is_expired = False

        mock_result.fetchone.return_value = mock_token_record
        mock_session.execute.return_value = mock_result

        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock):
                with pytest.raises(AuthenticationError) as exc_info:
                    await middleware._validate_service_token(request, token)

                assert "Service token is inactive" in str(exc_info.value)
                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_service_token_expired(self, middleware):
        """Test _validate_service_token with expired token."""
        request = Mock()
        token = "sk_expired_token"

        # Mock expired token record
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_token_record = Mock()
        mock_token_record.token_name = "expired_token"
        mock_token_record.is_active = True
        mock_token_record.is_expired = True

        mock_result.fetchone.return_value = mock_token_record
        mock_session.execute.return_value = mock_result

        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock):
                with pytest.raises(AuthenticationError) as exc_info:
                    await middleware._validate_service_token(request, token)

                assert "Service token has expired" in str(exc_info.value)
                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_service_token_database_error(self, middleware):
        """Test _validate_service_token with database error."""
        request = Mock()
        token = "sk_db_error_token"

        # Mock database error
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection failed")

        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock):
                with pytest.raises(AuthenticationError) as exc_info:
                    await middleware._validate_service_token(request, token)

                assert "Service token validation failed" in str(exc_info.value)
                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_authenticate_request_no_token(self, middleware):
        """Test _authenticate_request when no token is provided."""
        request = Mock()
        request.headers = {}

        with patch.object(middleware, "_extract_auth_token", return_value=None):
            with pytest.raises(AuthenticationError) as exc_info:
                await middleware._authenticate_request(request)

            assert "Missing authentication token" in str(exc_info.value)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_request_service_token(self, middleware):
        """Test _authenticate_request with service token."""
        request = Mock()
        token = "sk_service_token_123"

        mock_service_user = ServiceTokenUser(token_id="123", token_name="test_service", metadata={}, usage_count=0)

        with patch.object(middleware, "_extract_auth_token", return_value=token):
            with patch.object(middleware, "_validate_service_token", return_value=mock_service_user):
                user = await middleware._authenticate_request(request)

                assert user == mock_service_user

    @pytest.mark.asyncio
    async def test_authenticate_request_jwt_token(self, middleware):
        """Test _authenticate_request with JWT token."""
        request = Mock()
        token = "jwt_token_456"

        mock_jwt_user = Mock()
        mock_jwt_user.email = "test@example.com"

        with patch.object(middleware, "_extract_auth_token", return_value=token):
            with patch.object(middleware, "_validate_jwt_token", return_value=mock_jwt_user):
                user = await middleware._authenticate_request(request)

                assert user == mock_jwt_user

    @pytest.mark.asyncio
    async def test_log_authentication_event_success(self, middleware):
        """Test _log_authentication_event success case."""
        request = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "TestClient/1.0", "cf-ray": "ray123"}

        # Mock database session
        mock_session = AsyncMock()
        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            await middleware._log_authentication_event(
                request,
                user_email="test@example.com",
                event_type="auth_success",
                success=True,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

            # Verify the authentication event was created correctly
            call_args = mock_session.add.call_args[0][0]
            assert isinstance(call_args, AuthenticationEvent)
            assert call_args.user_email == "test@example.com"
            assert call_args.event_type == "auth_success"
            assert call_args.success is True

    @pytest.mark.asyncio
    async def test_log_authentication_event_with_service_token(self, middleware):
        """Test _log_authentication_event with service token info."""
        request = Mock()
        request.client.host = "10.0.0.1"
        request.headers = {}

        mock_session = AsyncMock()
        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            await middleware._log_authentication_event(
                request,
                service_token_name="test_service_token",
                event_type="service_token_auth",
                success=True,
            )

            # Should use service_token_name as user_email
            call_args = mock_session.add.call_args[0][0]
            assert call_args.user_email == "test_service_token"
            assert call_args.error_details["service_token_name"] == "test_service_token"

    @pytest.mark.asyncio
    async def test_log_authentication_event_error_handling(self, middleware):
        """Test _log_authentication_event error handling."""
        request = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {}

        # Mock database error - need to make the async generator itself fail
        async def failing_get_db():
            raise Exception("Database error")
            yield  # unreachable but needed for generator syntax

        with patch("src.auth.middleware.get_db", return_value=failing_get_db()):
            with patch("src.auth.middleware.logger.warning") as mock_warning:
                # Should not raise exception
                await middleware._log_authentication_event(
                    request,
                    user_email="test@example.com",
                    event_type="auth_test",
                    success=True,
                )

                mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_authentication_event_no_client(self, middleware):
        """Test _log_authentication_event when request has no client."""
        request = Mock()
        request.client = None
        request.headers = {}

        mock_session = AsyncMock()
        with patch("src.auth.middleware.get_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_session]

            await middleware._log_authentication_event(
                request,
                user_email="test@example.com",
                event_type="auth_no_client",
                success=True,
            )

            call_args = mock_session.add.call_args[0][0]
            assert call_args.ip_address is None

    def test_create_auth_error_response(self, middleware):
        """Test _create_auth_error_response method."""
        error = AuthenticationError("Test authentication error", 401)

        response = middleware._create_auth_error_response(error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

        # Check response content
        response_content = response.body.decode()
        response_json = eval(response_content)
        assert response_json["error"] == "Authentication failed"
        assert response_json["message"] == "Test authentication error"

    def test_create_auth_error_response_detail_disabled(self, middleware):
        """Test _create_auth_error_response with error details disabled."""
        middleware.config.auth_error_detail_enabled = False
        error = AuthenticationError("Sensitive error details", 401)

        response = middleware._create_auth_error_response(error)

        response_content = response.body.decode()
        response_json = eval(response_content)
        assert response_json["message"] == "Authentication required"

    @pytest.mark.asyncio
    async def test_update_user_session_success(self, middleware):
        """Test _update_user_session success case."""
        authenticated_user = Mock()
        authenticated_user.email = "test@example.com"
        authenticated_user.jwt_claims = {"sub": "cloudflare-sub-123"}

        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "TestClient/1.0"}

        # Mock database operations for new get_db() implementation
        mock_session = AsyncMock()

        # Mock existing session query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # No existing session
        mock_session.execute.return_value = mock_result

        # Mock the async generator get_db() function
        async def mock_get_db():
            yield mock_session

        with patch("src.auth.middleware.get_db", return_value=mock_get_db()):
            await middleware._update_user_session(authenticated_user, request)

            # Should execute queries and commit
            assert mock_session.execute.call_count >= 1
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_session_existing_session(self, middleware):
        """Test _update_user_session with existing session."""
        authenticated_user = Mock()
        authenticated_user.email = "existing@example.com"
        authenticated_user.jwt_claims = {"sub": "existing-sub"}

        request = Mock()

        # Mock existing session
        mock_existing_session = Mock()
        mock_existing_session.email = "existing@example.com"

        mock_session = AsyncMock()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing_session
        mock_session.execute.return_value = mock_result

        # Mock the async generator get_db() function
        async def mock_get_db():
            yield mock_session

        with patch("src.auth.middleware.get_db", return_value=mock_get_db()):
            await middleware._update_user_session(authenticated_user, request)

            # Should update existing session instead of adding new one
            mock_session.add.assert_not_called()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_session_database_disabled(self):
        """Test _update_user_session when database is disabled."""
        middleware = AuthenticationMiddleware(app=Mock(), database_enabled=False)

        authenticated_user = Mock()
        request = Mock()

        # Should return early without database operations
        await middleware._update_user_session(authenticated_user, request)
        # No assertions needed - should just return without error

    @pytest.mark.asyncio
    async def test_update_user_session_database_error(self, middleware):
        """Test _update_user_session with database error."""
        authenticated_user = Mock()
        authenticated_user.email = "db_error@example.com"
        authenticated_user.jwt_claims = {"sub": "sub123"}

        request = Mock()

        # Mock database error for get_db() implementation
        async def mock_get_db():
            raise Exception("Database connection failed")

        with patch("src.auth.middleware.get_db", return_value=mock_get_db()):
            with patch("src.auth.middleware.logger.warning") as mock_warning:
                # Should not raise exception
                await middleware._update_user_session(authenticated_user, request)

                mock_warning.assert_called_once()

    def test_get_client_ip_cloudflare_header(self, middleware):
        """Test _get_client_ip with Cloudflare header."""
        request = Mock()
        request.headers = {"CF-Connecting-IP": "203.0.113.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_x_forwarded_for(self, middleware):
        """Test _get_client_ip with X-Forwarded-For header."""
        request = Mock()
        request.headers = {"X-Forwarded-For": "203.0.113.2, 198.51.100.1, 192.0.2.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.2"

    def test_get_client_ip_x_real_ip(self, middleware):
        """Test _get_client_ip with X-Real-IP header."""
        request = Mock()
        request.headers = {"X-Real-IP": "203.0.113.3"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.3"

    def test_get_client_ip_request_client(self, middleware):
        """Test _get_client_ip from request.client.host."""
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "203.0.113.4"

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.4"

    def test_get_client_ip_no_client(self, middleware):
        """Test _get_client_ip when no client info available."""
        request = Mock()
        request.headers = {}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip is None

    def test_get_client_ip_invalid_host(self, middleware):
        """Test _get_client_ip with invalid host string."""
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "x" * 50  # Too long for IP address

        ip = middleware._get_client_ip(request)
        assert ip is None

    def test_get_client_ip_host_conversion_error(self, middleware):
        """Test _get_client_ip when host conversion raises exception."""
        request = Mock()
        request.headers = {}
        request.client = Mock()
        # Mock host that raises exception when converted to string
        request.client.host = Mock()
        request.client.host.__str__ = Mock(side_effect=Exception("Conversion error"))

        ip = middleware._get_client_ip(request)
        assert ip is None

    def test_get_client_ip_priority_order(self, middleware):
        """Test _get_client_ip priority order."""
        request = Mock()
        request.headers = {
            "CF-Connecting-IP": "cloudflare-ip",
            "X-Forwarded-For": "forwarded-ip",
            "X-Real-IP": "real-ip",
        }
        request.client = Mock()
        request.client.host = "client-ip"

        # Cloudflare header should have highest priority
        ip = middleware._get_client_ip(request)
        assert ip == "cloudflare-ip"

    @pytest.mark.asyncio
    async def test_dispatch_full_success_flow_jwt(self, middleware):
        """Test complete dispatch flow with successful JWT authentication."""
        # Setup mocks
        request = Mock()
        request.url.path = "/api/protected"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "TestClient", "cf-ray": "ray123"}

        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.role = UserRole.USER
        mock_user.session_id = "session123"

        call_next = AsyncMock()
        call_next.return_value = Response(content="Success", status_code=200)

        with patch.object(middleware, "_authenticate_request", return_value=mock_user):
            with patch.object(middleware, "_update_user_session", new_callable=AsyncMock) as mock_update:
                with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
                    response = await middleware.dispatch(request, call_next)

                    assert response.status_code == 200
                    assert request.state.authenticated_user == mock_user
                    assert request.state.user_email == "test@example.com"
                    assert request.state.user_role == UserRole.USER

                    mock_update.assert_called_once_with(mock_user, request)
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_full_success_flow_service_token(self, middleware):
        """Test complete dispatch flow with successful service token authentication."""
        request = Mock()
        request.url.path = "/api/service"
        request.client.host = "10.0.0.1"
        request.headers = {"user-agent": "ServiceClient"}

        mock_service_user = ServiceTokenUser(
            token_id="service123",
            token_name="test_service",
            metadata={"permissions": ["read"]},
            usage_count=5,
        )

        call_next = AsyncMock()
        call_next.return_value = Response(content="Service Success", status_code=200)

        with patch.object(middleware, "_authenticate_request", return_value=mock_service_user):
            with patch.object(middleware, "_update_user_session", new_callable=AsyncMock):
                with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock):
                    response = await middleware.dispatch(request, call_next)

                    assert response.status_code == 200
                    assert request.state.authenticated_user == mock_service_user
                    assert request.state.user_email is None  # Service tokens don't have email
                    assert request.state.user_role is None  # Service tokens don't have roles
                    assert request.state.token_metadata == {"permissions": ["read"]}

    @pytest.mark.asyncio
    async def test_dispatch_authentication_error(self, middleware):
        """Test dispatch with authentication error."""
        request = Mock()
        request.url.path = "/api/protected"
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "TestClient"}

        auth_error = AuthenticationError("Invalid token", 401)

        call_next = AsyncMock()

        with patch.object(middleware, "_authenticate_request", side_effect=auth_error):
            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
                response = await middleware.dispatch(request, call_next)

                assert response.status_code == 401
                call_next.assert_not_called()
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_unexpected_exception(self, middleware):
        """Test dispatch with unexpected exception."""
        request = Mock()
        request.url.path = "/api/test"
        request.client.host = "172.16.0.1"
        request.headers = {}

        call_next = AsyncMock()

        with patch.object(middleware, "_authenticate_request", side_effect=Exception("Unexpected error")):
            with patch.object(middleware, "_log_authentication_event", new_callable=AsyncMock) as mock_log:
                with patch("src.auth.middleware.logger.error") as mock_error:
                    response = await middleware.dispatch(request, call_next)

                    assert response.status_code == 500
                    assert isinstance(response, JSONResponse)
                    mock_error.assert_called_once()
                    mock_log.assert_called_once()


class TestRateLimiterFunctions:
    """Test cases for rate limiter functions."""

    @patch("src.auth.middleware.Limiter")
    @patch("src.auth.middleware.get_remote_address")
    def test_create_rate_limiter_ip_based(self, mock_get_remote_address, mock_limiter_class):
        """Test create_rate_limiter with IP-based rate limiting."""
        mock_config = Mock()
        mock_config.rate_limit_key_func = "ip"
        mock_config.rate_limit_requests = 100
        mock_config.rate_limit_window = 60

        mock_limiter = Mock()
        mock_limiter_class.return_value = mock_limiter

        limiter = create_rate_limiter(mock_config)

        assert limiter == mock_limiter
        mock_limiter_class.assert_called_once()

        # Check that key_func was set correctly
        call_args = mock_limiter_class.call_args
        key_func = call_args[1]["key_func"]
        default_limits = call_args[1]["default_limits"]

        # Test key function with mock request
        mock_request = Mock()
        key_func(mock_request)
        mock_get_remote_address.assert_called_with(mock_request)

        assert default_limits == ["100/60seconds"]

    @patch("src.auth.middleware.Limiter")
    @patch("src.auth.middleware.get_remote_address")
    def test_create_rate_limiter_email_based(self, mock_get_remote_address, mock_limiter_class):
        """Test create_rate_limiter with email-based rate limiting."""
        mock_config = Mock()
        mock_config.rate_limit_key_func = "email"
        mock_config.rate_limit_requests = 50
        mock_config.rate_limit_window = 30

        mock_limiter = Mock()
        mock_limiter_class.return_value = mock_limiter

        create_rate_limiter(mock_config)

        # Test key function with authenticated user
        call_args = mock_limiter_class.call_args
        key_func = call_args[1]["key_func"]

        mock_request = Mock()
        mock_request.state.user_email = "test@example.com"

        result = key_func(mock_request)
        assert result == "test@example.com"

    @patch("src.auth.middleware.Limiter")
    @patch("src.auth.middleware.get_remote_address")
    def test_create_rate_limiter_user_based(self, mock_get_remote_address, mock_limiter_class):
        """Test create_rate_limiter with user-based rate limiting."""
        mock_config = Mock()
        mock_config.rate_limit_key_func = "user"
        mock_config.rate_limit_requests = 75
        mock_config.rate_limit_window = 45

        create_rate_limiter(mock_config)

        # Test key function with authenticated user object
        call_args = mock_limiter_class.call_args
        key_func = call_args[1]["key_func"]

        mock_request = Mock()
        mock_user = Mock()
        mock_user.email = "user@example.com"
        mock_request.state.authenticated_user = mock_user

        result = key_func(mock_request)
        assert result == "user@example.com"

    @patch("src.auth.middleware.Limiter")
    @patch("src.auth.middleware.get_remote_address")
    def test_create_rate_limiter_fallback_to_ip(self, mock_get_remote_address, mock_limiter_class):
        """Test create_rate_limiter fallback to IP when user info not available."""
        mock_config = Mock()
        mock_config.rate_limit_key_func = "email"
        mock_config.rate_limit_requests = 60
        mock_config.rate_limit_window = 60

        create_rate_limiter(mock_config)

        call_args = mock_limiter_class.call_args
        key_func = call_args[1]["key_func"]

        # Mock request without user_email
        mock_request = Mock()
        mock_request.state = Mock(spec=[])  # Empty state

        key_func(mock_request)
        mock_get_remote_address.assert_called_with(mock_request)

    @patch("src.auth.middleware.Limiter")
    @patch("src.auth.middleware.get_remote_address")
    def test_create_rate_limiter_default_key_func(self, mock_get_remote_address, mock_limiter_class):
        """Test create_rate_limiter with unrecognized key_func defaults to IP."""
        mock_config = Mock()
        mock_config.rate_limit_key_func = "unknown"
        mock_config.rate_limit_requests = 100
        mock_config.rate_limit_window = 60

        create_rate_limiter(mock_config)

        call_args = mock_limiter_class.call_args
        key_func = call_args[1]["key_func"]

        mock_request = Mock()
        key_func(mock_request)
        mock_get_remote_address.assert_called_with(mock_request)

    @patch("src.auth.middleware.AuthenticationMiddleware")
    @patch("src.auth.middleware.create_rate_limiter")
    @patch("src.auth.middleware.SlowAPIMiddleware")
    @patch("src.auth.middleware._rate_limit_exceeded_handler")
    def test_setup_authentication_with_rate_limiting(
        self,
        mock_handler,
        mock_slow_api_middleware,
        mock_create_limiter,
        mock_auth_middleware_class,
    ):
        """Test setup_authentication with rate limiting enabled."""
        mock_app = Mock()
        mock_config = Mock()
        mock_config.rate_limiting_enabled = True
        mock_config.cloudflare_audience = "test-audience"
        mock_config.cloudflare_issuer = "test-issuer"
        mock_config.jwt_algorithm = "HS256"

        mock_limiter = Mock()
        mock_create_limiter.return_value = mock_limiter

        limiter = setup_authentication(mock_app, mock_config)

        # Verify middleware was added
        mock_app.add_middleware.assert_called()

        # Verify rate limiting was configured
        assert mock_app.state.limiter == mock_limiter
        mock_app.add_exception_handler.assert_called()

        assert limiter == mock_limiter

    @patch("src.auth.middleware.AuthenticationMiddleware")
    @patch("src.auth.middleware.create_rate_limiter")
    def test_setup_authentication_without_rate_limiting(self, mock_create_limiter, mock_auth_middleware_class):
        """Test setup_authentication with rate limiting disabled."""
        mock_app = Mock()
        mock_config = Mock()
        mock_config.rate_limiting_enabled = False
        mock_config.cloudflare_audience = "test-audience"
        mock_config.cloudflare_issuer = "test-issuer"
        mock_config.jwt_algorithm = "HS256"

        mock_limiter = Mock()
        mock_create_limiter.return_value = mock_limiter

        limiter = setup_authentication(mock_app, mock_config, database_enabled=False)

        # Verify middleware was added with correct parameters
        mock_app.add_middleware.assert_called()
        call_args = mock_app.add_middleware.call_args
        assert call_args[1]["database_enabled"] is False

        # Verify rate limiting was not configured (limiter should not be set on app.state)
        # Check that SlowAPIMiddleware was not added when rate limiting is disabled
        middleware_calls = mock_app.add_middleware.call_args_list
        assert not any("SlowAPIMiddleware" in str(call) for call in middleware_calls)

        assert limiter == mock_limiter


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_get_current_user_success(self):
        """Test get_current_user with authenticated user."""
        request = Mock()
        mock_user = Mock()
        request.state.authenticated_user = mock_user

        user = get_current_user(request)
        assert user == mock_user

    def test_get_current_user_no_state(self):
        """Test get_current_user when request has no state."""
        request = Mock(spec=[])  # Request without state attribute

        user = get_current_user(request)
        assert user is None

    def test_get_current_user_no_user(self):
        """Test get_current_user when state has no user."""
        request = Mock()
        request.state = Mock(spec=[])  # State without authenticated_user

        user = get_current_user(request)
        assert user is None

    def test_require_authentication_success(self):
        """Test require_authentication with authenticated user."""
        request = Mock()
        mock_user = Mock()
        request.state.authenticated_user = mock_user

        user = require_authentication(request)
        assert user == mock_user

    def test_require_authentication_no_user(self):
        """Test require_authentication without authenticated user."""
        request = Mock()
        request.state = Mock(spec=[])

        with pytest.raises(Exception) as exc_info:
            require_authentication(request)

        assert "Authentication required" in str(exc_info.value)

    def test_require_role_success(self):
        """Test require_role with correct role."""
        request = Mock()
        mock_user = Mock()
        mock_user.role.value = "admin"
        request.state.authenticated_user = mock_user

        user = require_role(request, "admin")
        assert user == mock_user

    def test_require_role_wrong_role(self):
        """Test require_role with incorrect role."""
        request = Mock()
        mock_user = Mock()
        mock_user.role.value = "user"
        request.state.authenticated_user = mock_user

        with pytest.raises(Exception) as exc_info:
            require_role(request, "admin")

        assert "Role 'admin' required" in str(exc_info.value)

    def test_require_role_no_user(self):
        """Test require_role without authenticated user."""
        request = Mock()
        request.state = Mock(spec=[])

        with pytest.raises(Exception) as exc_info:
            require_role(request, "admin")

        assert "Authentication required" in str(exc_info.value)


class TestAuthenticationIntegration:
    """Integration tests for complete authentication workflows."""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow_with_logging(self):
        """Test complete authentication flow including all logging components."""
        # Setup comprehensive middleware
        mock_config = Mock()
        mock_config.cloudflare_access_enabled = True
        mock_config.auth_logging_enabled = True
        mock_config.auth_error_detail_enabled = True
        mock_config.email_whitelist_enabled = False

        mock_jwt_validator = Mock()
        mock_user = Mock()
        mock_user.email = "integration@example.com"
        mock_user.role = UserRole.USER
        mock_user.jwt_claims = {"sub": "integration-sub"}
        mock_jwt_validator.validate_token.return_value = mock_user

        middleware = AuthenticationMiddleware(
            app=Mock(),
            config=mock_config,
            jwt_validator=mock_jwt_validator,
            excluded_paths=[],
            database_enabled=True,
        )

        # Setup request
        request = Mock()
        request.url.path = "/api/integration"
        request.client.host = "203.0.113.100"
        request.headers = {
            "Authorization": "Bearer integration-jwt-token",
            "user-agent": "IntegrationClient/1.0",
            "cf-ray": "integration-ray-123",
        }

        call_next = AsyncMock()
        call_next.return_value = Response(content="Integration Success", status_code=200)

        # Mock database operations (now using get_db() only)
        with patch("src.auth.middleware.get_db") as mock_get_db:
            # Setup database session mocks
            mock_session = AsyncMock()

            # Mock both authentication event logging and session updates
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None  # No existing session
            mock_session.execute.return_value = mock_result

            # Mock the async generator get_db() function
            async def mock_get_db_gen():
                yield mock_session

            mock_get_db.return_value = mock_get_db_gen()

            # Execute the complete flow
            response = await middleware.dispatch(request, call_next)

            # Verify successful authentication
            assert response.status_code == 200
            assert request.state.authenticated_user == mock_user
            assert request.state.user_email == "integration@example.com"
            assert request.state.user_role == UserRole.USER

            # Verify all database operations were called
            mock_session.add.assert_called()  # Auth event logging
            mock_session.commit.assert_called()
            # Session update is done within the same session context (using get_db())
            assert mock_session.add.call_count >= 1  # At least auth event was logged
