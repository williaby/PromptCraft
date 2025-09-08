"""Comprehensive tests for auth_simple middleware to achieve 90%+ security coverage."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request, Response
from starlette.datastructures import Headers

from src.auth_simple.cloudflare_auth import CloudflareAuthError
from src.auth_simple.middleware import (
    AuthenticationDependency,
    CloudflareAccessMiddleware,
    SimpleSessionManager,
    create_auth_middleware,
    require_admin,
    require_auth,
)
from src.auth_simple.whitelist import EmailWhitelistValidator, UserTier
from src.utils.datetime_compat import UTC


class TestSimpleSessionManager:
    """Comprehensive tests for SimpleSessionManager."""

    def test_initialization(self):
        """Test session manager initialization."""
        session_manager = SimpleSessionManager(session_timeout=1800)
        assert session_manager.sessions == {}
        assert session_manager.session_timeout == 1800

    def test_initialization_default_timeout(self):
        """Test session manager with default timeout."""
        session_manager = SimpleSessionManager()
        assert session_manager.session_timeout == 3600

    def test_create_session_basic(self):
        """Test basic session creation."""
        session_manager = SimpleSessionManager()

        with (
            patch("src.auth_simple.middleware.secrets.token_urlsafe") as mock_token,
            patch("src.auth_simple.middleware.datetime") as mock_datetime,
        ):

            mock_token.return_value = "test_session_id"
            mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            session_id = session_manager.create_session(email="test@example.com", is_admin=False, user_tier="full")

            assert session_id == "test_session_id"
            assert "test_session_id" in session_manager.sessions

            session = session_manager.sessions["test_session_id"]
            assert session["email"] == "test@example.com"
            assert session["is_admin"] is False
            assert session["user_tier"] == "full"
            assert session["created_at"] == mock_now
            assert session["last_accessed"] == mock_now
            assert session["cf_context"] == {}

    def test_create_session_with_context(self):
        """Test session creation with Cloudflare context."""
        session_manager = SimpleSessionManager()
        cf_context = {"cf_ray": "test-ray", "ip_country": "US"}

        session_id = session_manager.create_session(
            email="admin@example.com", is_admin=True, user_tier="admin", cf_context=cf_context,
        )

        session = session_manager.sessions[session_id]
        assert session["cf_context"] == cf_context
        assert session["is_admin"] is True
        assert session["user_tier"] == "admin"

    def test_get_session_valid(self):
        """Test retrieving a valid session."""
        session_manager = SimpleSessionManager()

        with patch("src.auth_simple.middleware.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            # Create session
            session_id = session_manager.create_session(email="test@example.com", is_admin=False, user_tier="full")

            # Get session should update last_accessed
            mock_later = datetime(2023, 1, 1, 12, 30, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_later

            session = session_manager.get_session(session_id)

            assert session is not None
            assert session["email"] == "test@example.com"
            assert session["last_accessed"] == mock_later

    def test_get_session_empty_session_id(self):
        """Test get_session with empty session ID."""
        session_manager = SimpleSessionManager()
        assert session_manager.get_session("") is None
        assert session_manager.get_session(None) is None

    def test_get_session_nonexistent(self):
        """Test retrieving a nonexistent session."""
        session_manager = SimpleSessionManager()
        assert session_manager.get_session("nonexistent") is None

    def test_get_session_expired(self):
        """Test retrieving an expired session."""
        session_manager = SimpleSessionManager(session_timeout=60)  # 1 minute

        with patch("src.auth_simple.middleware.datetime") as mock_datetime:
            # Create session
            mock_create = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_create

            session_id = session_manager.create_session(email="test@example.com", is_admin=False, user_tier="full")

            # Try to get session 2 minutes later (expired)
            mock_expired = datetime(2023, 1, 1, 12, 2, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_expired

            session = session_manager.get_session(session_id)

            assert session is None
            assert session_id not in session_manager.sessions  # Should be removed

    def test_invalidate_session_existing(self):
        """Test invalidating an existing session."""
        session_manager = SimpleSessionManager()
        session_id = session_manager.create_session(email="test@example.com", is_admin=False, user_tier="full")

        result = session_manager.invalidate_session(session_id)

        assert result is True
        assert session_id not in session_manager.sessions

    def test_invalidate_session_nonexistent(self):
        """Test invalidating a nonexistent session."""
        session_manager = SimpleSessionManager()
        result = session_manager.invalidate_session("nonexistent")
        assert result is False

    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        session_manager = SimpleSessionManager(session_timeout=60)

        with patch("src.auth_simple.middleware.datetime") as mock_datetime:
            # Create two sessions
            mock_create = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_create

            session_id1 = session_manager.create_session("user1@example.com", False, "full")
            session_id2 = session_manager.create_session("user2@example.com", False, "limited")

            # Move time forward - first session expires, second doesn't
            mock_check = datetime(2023, 1, 1, 12, 1, 30, tzinfo=UTC)  # 1.5 minutes later
            mock_datetime.now.return_value = mock_check

            session_manager.cleanup_expired_sessions()

            # Both sessions should be removed as they're both expired
            assert session_id1 not in session_manager.sessions
            assert session_id2 not in session_manager.sessions

    def test_is_session_expired_true(self):
        """Test session expiration check - expired."""
        session_manager = SimpleSessionManager(session_timeout=60)

        with patch("src.auth_simple.middleware.datetime") as mock_datetime:
            mock_old = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            session = {"last_accessed": mock_old}

            mock_now = datetime(2023, 1, 1, 12, 2, 0, tzinfo=UTC)  # 2 minutes later
            mock_datetime.now.return_value = mock_now

            assert session_manager._is_session_expired(session) is True

    def test_is_session_expired_false(self):
        """Test session expiration check - not expired."""
        session_manager = SimpleSessionManager(session_timeout=3600)  # 1 hour

        with patch("src.auth_simple.middleware.datetime") as mock_datetime:
            mock_recent = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            session = {"last_accessed": mock_recent}

            mock_now = datetime(2023, 1, 1, 12, 30, 0, tzinfo=UTC)  # 30 minutes later
            mock_datetime.now.return_value = mock_now

            assert session_manager._is_session_expired(session) is False


class TestCloudflareAccessMiddleware:
    """Comprehensive tests for CloudflareAccessMiddleware."""

    @pytest.fixture
    def mock_validator(self):
        """Create mock email whitelist validator."""
        validator = Mock(spec=EmailWhitelistValidator)
        validator.is_authorized.return_value = True
        validator.get_user_tier.return_value = UserTier.FULL
        return validator

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager."""
        manager = Mock(spec=SimpleSessionManager)
        manager.get_session.return_value = None
        manager.create_session.return_value = "test_session_id"
        return manager

    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request."""
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.headers = Headers({"cf-access-authenticated-user-email": "test@example.com"})
        request.state = Mock()
        request.cookies = {}
        return request

    def test_initialization_basic(self, mock_validator):
        """Test basic middleware initialization."""
        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        assert middleware.whitelist_validator == mock_validator
        assert middleware.session_manager is not None
        assert middleware.enable_session_cookies is True
        assert len(middleware.all_public_paths) > 0

    def test_initialization_with_custom_session_manager(self, mock_validator, mock_session_manager):
        """Test initialization with custom session manager."""
        middleware = CloudflareAccessMiddleware(
            app=None, whitelist_validator=mock_validator, session_manager=mock_session_manager,
        )

        assert middleware.session_manager == mock_session_manager

    def test_initialization_with_custom_paths(self, mock_validator):
        """Test initialization with custom public paths."""
        custom_paths = {"/custom", "/special"}

        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator, public_paths=custom_paths)

        assert custom_paths.issubset(middleware.all_public_paths)

    def test_initialization_disable_cookies(self, mock_validator):
        """Test initialization with disabled session cookies."""
        middleware = CloudflareAccessMiddleware(
            app=None, whitelist_validator=mock_validator, enable_session_cookies=False,
        )

        assert middleware.enable_session_cookies is False

    def test_is_public_path_true(self, mock_validator):
        """Test public path checking - true cases."""
        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        assert middleware._is_public_path("/") is True
        assert middleware._is_public_path("/health") is True
        assert middleware._is_public_path("/docs") is True
        assert middleware._is_public_path("/static/css/style.css") is True

    def test_is_public_path_false(self, mock_validator):
        """Test public path checking - false cases."""
        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        assert middleware._is_public_path("/private") is False
        assert middleware._is_public_path("/api/user/profile") is False
        assert middleware._is_public_path("/admin") is False

    @pytest.mark.asyncio
    async def test_dispatch_public_path(self, mock_validator, mock_request):
        """Test dispatch for public paths - should skip auth."""
        mock_request.url.path = "/health"
        call_next = AsyncMock(return_value=Response())

        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        response = await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once_with(mock_request)
        # Validator should not be called for public paths
        mock_validator.is_authorized.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_authenticated_request(self, mock_validator, mock_session_manager, mock_request):
        """Test dispatch for authenticated request."""
        call_next = AsyncMock(return_value=Response())

        # Mock successful authentication flow
        with patch.object(CloudflareAccessMiddleware, "_authenticate_request", new_callable=AsyncMock):
            middleware = CloudflareAccessMiddleware(
                app=None, whitelist_validator=mock_validator, session_manager=mock_session_manager,
            )

            response = await middleware.dispatch(mock_request, call_next)

            call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_authentication_error(self, mock_validator, mock_request):
        """Test dispatch when authentication fails."""
        call_next = AsyncMock()

        # Mock authentication failure
        with patch.object(
            CloudflareAccessMiddleware,
            "_authenticate_request",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=401),
        ):
            middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(mock_request, call_next)

            assert exc_info.value.status_code == 401
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_unexpected_error(self, mock_validator, mock_request):
        """Test dispatch handling unexpected errors."""
        call_next = AsyncMock()

        # Mock unexpected error
        with patch.object(
            CloudflareAccessMiddleware,
            "_authenticate_request",
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error"),
        ):
            middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

            response = await middleware.dispatch(mock_request, call_next)

            assert response.status_code == 500
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_authenticate_request_cloudflare_error(self, mock_validator, mock_request):
        """Test authentication when Cloudflare extraction fails."""
        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        with patch.object(
            middleware.cloudflare_auth, "extract_user_from_request", side_effect=CloudflareAuthError("No user found"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await middleware._authenticate_request(mock_request)

            assert exc_info.value.status_code == 401
            assert "No authenticated user found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_request_unauthorized_email(self, mock_validator, mock_request):
        """Test authentication with unauthorized email."""
        mock_user = Mock()
        mock_user.email = "unauthorized@example.com"

        mock_validator.is_authorized.return_value = False

        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        with patch.object(middleware.cloudflare_auth, "extract_user_from_request", return_value=mock_user):
            with pytest.raises(HTTPException) as exc_info:
                await middleware._authenticate_request(mock_request)

            assert exc_info.value.status_code == 403
            assert "not authorized" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_request_new_session(self, mock_validator, mock_session_manager, mock_request):
        """Test authentication creating new session."""
        mock_user = Mock()
        mock_user.email = "test@example.com"

        mock_validator.is_authorized.return_value = True
        mock_validator.get_user_tier.return_value = UserTier.ADMIN
        mock_validator.has_admin_privileges.return_value = True
        mock_validator.can_access_premium_models.return_value = True
        mock_session_manager.get_session.return_value = None  # No existing session
        mock_session_manager.create_session.return_value = "new_session_id"

        # Mock the session retrieval after creation
        new_session_data = {
            "email": "test@example.com",
            "is_admin": True,
            "user_tier": "admin",
            "created_at": datetime.now(UTC),
            "cf_context": {},
        }

        def mock_get_session(session_id):
            if session_id == "new_session_id":
                return new_session_data
            return None

        mock_session_manager.get_session.side_effect = mock_get_session

        middleware = CloudflareAccessMiddleware(
            app=None, whitelist_validator=mock_validator, session_manager=mock_session_manager,
        )

        with (
            patch.object(middleware.cloudflare_auth, "extract_user_from_request", return_value=mock_user),
            patch.object(middleware.cloudflare_auth, "create_user_context", return_value={}),
        ):

            await middleware._authenticate_request(mock_request)

            # Verify session creation
            mock_session_manager.create_session.assert_called_once_with("test@example.com", True, "admin", {})

            # Verify user context injection
            assert hasattr(mock_request.state, "user")
            assert mock_request.state.user["email"] == "test@example.com"
            assert mock_request.state.user["is_admin"] is True
            assert mock_request.state.user["user_tier"] == "admin"

    @pytest.mark.asyncio
    async def test_authenticate_request_existing_session(self, mock_validator, mock_session_manager, mock_request):
        """Test authentication with existing valid session."""
        mock_user = Mock()
        mock_user.email = "test@example.com"

        # Mock existing session
        existing_session = {
            "email": "test@example.com",
            "is_admin": False,
            "user_tier": "limited",
            "created_at": datetime.now(UTC),
            "cf_context": {},
        }

        mock_request.cookies = {"session_id": "existing_session"}
        mock_validator.is_authorized.return_value = True
        mock_validator.get_user_tier.return_value = UserTier.FULL  # Tier changed
        mock_session_manager.get_session.return_value = existing_session

        middleware = CloudflareAccessMiddleware(
            app=None, whitelist_validator=mock_validator, session_manager=mock_session_manager,
        )

        with patch.object(middleware.cloudflare_auth, "extract_user_from_request", return_value=mock_user):
            await middleware._authenticate_request(mock_request)

            # Should update session with new tier info
            assert existing_session["user_tier"] == "full"
            assert existing_session["is_admin"] is False  # Updated based on new tier
            assert existing_session["can_access_premium"] is True

    @pytest.mark.asyncio
    async def test_authenticate_request_session_creation_failure(
        self, mock_validator, mock_session_manager, mock_request,
    ):
        """Test authentication when session creation fails."""
        mock_user = Mock()
        mock_user.email = "test@example.com"

        mock_validator.is_authorized.return_value = True
        mock_validator.get_user_tier.return_value = UserTier.FULL
        mock_session_manager.get_session.return_value = None  # No existing session
        mock_session_manager.create_session.return_value = "new_session_id"

        # Mock session retrieval failure after creation
        mock_session_manager.get_session.side_effect = [None, None]  # Creation fails

        middleware = CloudflareAccessMiddleware(
            app=None, whitelist_validator=mock_validator, session_manager=mock_session_manager,
        )

        with (
            patch.object(middleware.cloudflare_auth, "extract_user_from_request", return_value=mock_user),
            patch.object(middleware.cloudflare_auth, "create_user_context", return_value={}),
        ):

            with pytest.raises(HTTPException) as exc_info:
                await middleware._authenticate_request(mock_request)

            assert exc_info.value.status_code == 500
            assert "Session creation failed" in exc_info.value.detail

    def test_set_session_cookie(self, mock_validator):
        """Test setting session cookie."""
        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)
        response = Mock(spec=Response)

        middleware._set_session_cookie(response, "test_session_id")

        response.set_cookie.assert_called_once_with(
            key="session_id",
            value="test_session_id",
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=middleware.session_manager.session_timeout,
        )

    @pytest.mark.asyncio
    async def test_dispatch_with_session_cookie_setting(self, mock_validator, mock_request):
        """Test dispatch that sets session cookie."""
        call_next = AsyncMock(return_value=Response())
        mock_request.state.new_session_id = "new_session"

        middleware = CloudflareAccessMiddleware(app=None, whitelist_validator=mock_validator)

        with (
            patch.object(middleware, "_authenticate_request", new_callable=AsyncMock),
            patch.object(middleware, "_set_session_cookie") as mock_set_cookie,
        ):

            response = await middleware.dispatch(mock_request, call_next)

            mock_set_cookie.assert_called_once_with(response, "new_session")


class TestAuthenticationDependency:
    """Tests for AuthenticationDependency."""

    @pytest.fixture
    def mock_request_with_user(self):
        """Create mock request with user state."""
        request = Mock(spec=Request)
        request.state.user = {"email": "test@example.com", "is_admin": False, "user_tier": "full"}
        return request

    @pytest.fixture
    def mock_request_with_admin(self):
        """Create mock request with admin user state."""
        request = Mock(spec=Request)
        request.state.user = {"email": "admin@example.com", "is_admin": True, "user_tier": "admin"}
        return request

    @pytest.fixture
    def mock_request_no_user(self):
        """Create mock request without user state."""
        request = Mock(spec=Request)
        request.state = Mock()
        # Explicitly make sure user attribute doesn't exist
        delattr(request.state, "user") if hasattr(request.state, "user") else None
        return request

    def test_initialization_default(self):
        """Test dependency initialization with defaults."""
        dep = AuthenticationDependency()
        assert dep.require_admin is False

    def test_initialization_require_admin(self):
        """Test dependency initialization requiring admin."""
        dep = AuthenticationDependency(require_admin=True)
        assert dep.require_admin is True

    def test_call_success_regular_user(self, mock_request_with_user):
        """Test successful authentication for regular user."""
        dep = AuthenticationDependency()
        result = dep(mock_request_with_user)

        assert result == mock_request_with_user.state.user

    def test_call_success_admin_user(self, mock_request_with_admin):
        """Test successful authentication for admin user."""
        dep = AuthenticationDependency()
        result = dep(mock_request_with_admin)

        assert result == mock_request_with_admin.state.user

    def test_call_success_admin_required_admin_user(self, mock_request_with_admin):
        """Test successful authentication when admin required and user is admin."""
        dep = AuthenticationDependency(require_admin=True)
        result = dep(mock_request_with_admin)

        assert result == mock_request_with_admin.state.user

    def test_call_no_user_state(self, mock_request_no_user):
        """Test authentication failure when no user state."""
        dep = AuthenticationDependency()

        with pytest.raises(HTTPException) as exc_info:
            dep(mock_request_no_user)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    def test_call_admin_required_regular_user(self, mock_request_with_user):
        """Test authentication failure when admin required but user is not admin."""
        dep = AuthenticationDependency(require_admin=True)

        with pytest.raises(HTTPException) as exc_info:
            dep(mock_request_with_user)

        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail

    def test_convenience_instances(self):
        """Test convenience dependency instances."""
        assert require_auth.require_admin is False
        assert require_admin.require_admin is True


class TestCreateAuthMiddleware:
    """Tests for create_auth_middleware factory function."""

    def test_create_basic_middleware(self):
        """Test creating basic middleware."""
        with patch("src.auth_simple.whitelist.create_validator_from_env") as mock_create_validator:
            mock_validator = Mock(spec=EmailWhitelistValidator)
            mock_create_validator.return_value = mock_validator

            middleware = create_auth_middleware("test@example.com")

            assert isinstance(middleware, CloudflareAccessMiddleware)
            assert middleware.whitelist_validator == mock_validator
            mock_create_validator.assert_called_once_with("test@example.com", "", "", "")

    def test_create_middleware_with_all_params(self):
        """Test creating middleware with all parameters."""
        with patch("src.auth_simple.whitelist.create_validator_from_env") as mock_create_validator:
            mock_validator = Mock(spec=EmailWhitelistValidator)
            mock_create_validator.return_value = mock_validator

            public_paths = {"/custom"}

            middleware = create_auth_middleware(
                whitelist_str="test@example.com",
                admin_emails_str="admin@example.com",
                full_users_str="full@example.com",
                limited_users_str="limited@example.com",
                session_timeout=1800,
                public_paths=public_paths,
            )

            assert isinstance(middleware, CloudflareAccessMiddleware)
            assert middleware.session_manager.session_timeout == 1800
            assert public_paths.issubset(middleware.all_public_paths)

            mock_create_validator.assert_called_once_with(
                "test@example.com", "admin@example.com", "full@example.com", "limited@example.com",
            )
