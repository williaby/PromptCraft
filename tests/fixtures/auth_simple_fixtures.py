"""Test fixtures for the simplified authentication system.

This module provides fixtures for testing the auth_simple module,
including Cloudflare header mocks, test users, and middleware setup.
"""

from unittest.mock import MagicMock

import pytest

from src.auth_simple import (
    CloudflareUser,
    ConfigManager,
    EmailWhitelistConfig,
    EmailWhitelistValidator,
    create_test_config,
)


@pytest.fixture
def cloudflare_headers_authenticated():
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
def cloudflare_headers_admin():
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
def cloudflare_headers_unauthorized():
    """Mock Cloudflare headers for unauthorized user."""
    return {
        "cf-access-authenticated-user-email": "unauthorized@badomain.com",
        "cf-access-username": "unauthorized@badomain.com",
        "cf-access-user": "unauthorized-user-id",
        "cf-access-organization": "test-org",
        "cf-ray": "unauthorized-ray-id",
        "x-forwarded-for": "192.168.1.102",
    }


@pytest.fixture
def cloudflare_headers_missing():
    """Mock request with missing Cloudflare headers."""
    return {"x-forwarded-for": "192.168.1.103", "user-agent": "Test Agent"}


@pytest.fixture
def test_user_authenticated():
    """Test user object for authenticated user."""
    return {
        "email": "test@example.com",
        "user_id": "test-user-id",
        "is_admin": False,
        "authenticated": True,
        "session_id": "test-session-123",
        "groups": ["users"],
        "organization": "test-org",
    }


@pytest.fixture
def test_user_admin():
    """Test user object for admin user."""
    return {
        "email": "admin@example.com",
        "user_id": "admin-user-id",
        "is_admin": True,
        "authenticated": True,
        "session_id": "admin-session-123",
        "groups": ["users", "admins"],
        "organization": "test-org",
    }


@pytest.fixture
def test_auth_config():
    """Test authentication configuration."""
    return create_test_config(
        dev_mode=True,
        email_whitelist=["test@example.com", "@testdomain.com", "admin@example.com"],
        admin_emails=["admin@example.com"],
        session_timeout=300,  # 5 minutes for testing
        log_level="DEBUG",
    )


@pytest.fixture
def test_config_manager(test_auth_config):
    """Test configuration manager."""
    return ConfigManager(test_auth_config)


@pytest.fixture
def test_middleware(test_config_manager):
    """Test authentication middleware."""
    return test_config_manager.create_middleware()


@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    request = MagicMock()
    request.state = MagicMock()
    request.url.path = "/test"
    request.method = "GET"
    request.client.host = "192.168.1.100"
    return request


@pytest.fixture
def mock_request_with_auth(mock_request, test_user_authenticated):
    """Mock FastAPI request object with authenticated user."""
    mock_request.state.user = test_user_authenticated
    return mock_request


@pytest.fixture
def mock_request_with_admin(mock_request, test_user_admin):
    """Mock FastAPI request object with admin user."""
    mock_request.state.user = test_user_admin
    return mock_request


@pytest.fixture
def mock_request_with_headers(mock_request, cloudflare_headers_authenticated):
    """Mock FastAPI request with Cloudflare headers."""
    mock_request.headers = cloudflare_headers_authenticated
    return mock_request


@pytest.fixture
def email_whitelist_config():
    """Test email whitelist configuration."""
    return EmailWhitelistConfig(
        allowed_emails=["test@example.com", "admin@example.com"],
        allowed_domains=["@testdomain.com", "@company.com"],
        admin_emails=["admin@example.com"],
        case_sensitive=False,
        normalize_domains=True,
    )


@pytest.fixture
def email_validator(email_whitelist_config):
    """Test email validator."""
    return EmailWhitelistValidator(email_whitelist_config)


@pytest.fixture
def cloudflare_user():
    """Test CloudflareUser object."""
    return CloudflareUser(
        email="test@example.com",
        user_id="test-user-id",
        username="test@example.com",
        organization="test-org",
        ray_id="test-ray-id",
    )


@pytest.fixture
def cloudflare_admin_user():
    """Test CloudflareUser object for admin."""
    return CloudflareUser(
        email="admin@example.com",
        user_id="admin-user-id",
        username="admin@example.com",
        organization="test-org",
        ray_id="admin-ray-id",
    )


# Service Token fixtures for compatibility with existing tests
@pytest.fixture
def mock_service_token_user():
    """Mock service token user for compatibility."""
    from src.auth import ServiceTokenUser

    return ServiceTokenUser(
        token_id="test-token-123",
        token_name="Test Service Token",
        metadata={"permissions": ["read", "write"], "service_name": "test-service"},
        usage_count=5,
    )


@pytest.fixture
def mock_authenticated_user():
    """Mock authenticated user for compatibility with existing tests."""
    from src.auth.models import AuthenticatedUser, UserRole

    return AuthenticatedUser(
        email="test@example.com",
        role=UserRole.USER,
        user_id="test-user-123",
        token_id="session-token-123",
    )


@pytest.fixture
def mock_admin_user():
    """Mock admin user for compatibility."""
    from src.auth.models import AuthenticatedUser, UserRole

    return AuthenticatedUser(
        email="admin@example.com",
        role=UserRole.ADMIN,
        user_id="admin-user-123",
        token_id="admin-session-123",
    )


# App fixtures for integration testing
@pytest.fixture
def test_app():
    """Test FastAPI application with simplified auth."""
    from fastapi import FastAPI

    app = FastAPI(title="Test App")

    # Use test configuration for auth
    test_config = create_test_config()
    config_manager = ConfigManager(test_config)

    # Setup auth middleware
    middleware = config_manager.create_middleware()
    app.add_middleware(
        type(middleware),
        whitelist_validator=middleware.whitelist_validator,
        session_manager=middleware.session_manager,
        public_paths=middleware.public_paths,
        health_check_paths=middleware.health_check_paths,
        enable_session_cookies=middleware.enable_session_cookies,
    )

    return app


@pytest.fixture
def test_client(test_app):
    """Test client for integration testing."""
    from fastapi.testclient import TestClient

    return TestClient(test_app)


# Environment setup fixtures
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("PROMPTCRAFT_AUTH_MODE", "cloudflare_simple")
    monkeypatch.setenv("PROMPTCRAFT_EMAIL_WHITELIST", "test@example.com,@testdomain.com")
    monkeypatch.setenv("PROMPTCRAFT_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.setenv("PROMPTCRAFT_SESSION_TIMEOUT", "300")
    monkeypatch.setenv("PROMPTCRAFT_DEV_MODE", "True")


# Utility fixtures for complex test scenarios
@pytest.fixture
def auth_test_scenarios():
    """Common authentication test scenarios."""
    return {
        "valid_user": {
            "headers": {"cf-access-authenticated-user-email": "test@example.com"},
            "expected_authenticated": True,
            "expected_admin": False,
        },
        "valid_admin": {
            "headers": {"cf-access-authenticated-user-email": "admin@example.com"},
            "expected_authenticated": True,
            "expected_admin": True,
        },
        "invalid_user": {
            "headers": {"cf-access-authenticated-user-email": "unauthorized@baddomain.com"},
            "expected_authenticated": False,
            "expected_admin": False,
        },
        "missing_headers": {"headers": {}, "expected_authenticated": False, "expected_admin": False},
    }


@pytest.fixture
def integration_test_paths():
    """Common paths for integration testing."""
    return {
        "public": ["/health", "/ping", "/docs", "/openapi.json"],
        "authenticated": ["/api/v1/protected", "/dashboard"],
        "admin": ["/admin", "/api/v1/admin", "/metrics"],
    }


# Helper functions for authenticated test requests
@pytest.fixture
def authenticated_headers():
    """Standard authenticated user headers for test requests."""
    return {
        "Cf-Access-Authenticated-User-Email": "test@example.com",
        "Cf-Access-Username": "test@example.com",
        "Cf-Access-User": "test-user-id",
        "Cf-Ray": "test-ray-id",
    }


@pytest.fixture
def admin_headers():
    """Admin user headers for test requests."""
    return {
        "Cf-Access-Authenticated-User-Email": "admin@example.com",
        "Cf-Access-Username": "admin@example.com",
        "Cf-Access-User": "admin-user-id",
        "Cf-Ray": "admin-ray-id",
    }


@pytest.fixture
def service_token_headers():
    """Service token headers for test requests."""
    return {"Authorization": "Bearer sk_test_service_token_123", "X-Service-Token": "test-service-token"}


@pytest.fixture
def authenticated_client(test_client, authenticated_headers):
    """Test client pre-configured with authenticated user headers."""

    def make_request(method, url, **kwargs):
        """Make request with authenticated headers."""
        headers = kwargs.get("headers", {})
        headers.update(authenticated_headers)
        kwargs["headers"] = headers
        return getattr(test_client, method.lower())(url, **kwargs)

    # Add helper methods to client
    test_client.get_authenticated = lambda url, **kw: make_request("GET", url, **kw)
    test_client.post_authenticated = lambda url, **kw: make_request("POST", url, **kw)
    test_client.put_authenticated = lambda url, **kw: make_request("PUT", url, **kw)
    test_client.delete_authenticated = lambda url, **kw: make_request("DELETE", url, **kw)

    return test_client


@pytest.fixture
def admin_client(test_client, admin_headers):
    """Test client pre-configured with admin user headers."""

    def make_request(method, url, **kwargs):
        """Make request with admin headers."""
        headers = kwargs.get("headers", {})
        headers.update(admin_headers)
        kwargs["headers"] = headers
        return getattr(test_client, method.lower())(url, **kwargs)

    # Add helper methods to client
    test_client.get_admin = lambda url, **kw: make_request("GET", url, **kw)
    test_client.post_admin = lambda url, **kw: make_request("POST", url, **kw)
    test_client.put_admin = lambda url, **kw: make_request("PUT", url, **kw)
    test_client.delete_admin = lambda url, **kw: make_request("DELETE", url, **kw)

    return test_client


# Dependency override helpers for unit tests
class AuthTestHelper:
    """Helper class for managing authentication in tests."""

    @staticmethod
    def override_auth_dependency(app, user_mock):
        """Override authentication dependency with a mock user."""
        from src.auth.middleware import require_authentication

        app.dependency_overrides[require_authentication] = lambda: user_mock
        return app

    @staticmethod
    def override_admin_dependency(app, admin_mock):
        """Override admin requirement dependency with a mock admin."""
        from src.api.auth_endpoints import require_admin_role

        app.dependency_overrides[require_admin_role] = lambda: admin_mock
        return app

    @staticmethod
    def clear_overrides(app):
        """Clear all dependency overrides."""
        app.dependency_overrides.clear()

    @staticmethod
    def create_mock_authenticated_user(email="test@example.com", is_admin=False):
        """Create a properly structured mock authenticated user."""
        from unittest.mock import Mock

        from src.auth.middleware import AuthenticatedUser
        from src.auth.models import UserRole

        user = Mock(spec=AuthenticatedUser)
        user.email = email
        user.role = UserRole.ADMIN if is_admin else UserRole.USER
        user.user_id = f"{email.split('@')[0]}-user-id"
        user.token_id = f"{email.split('@')[0]}-token-id"

        # Make sure isinstance() works correctly
        user.__class__ = AuthenticatedUser
        return user

    @staticmethod
    def create_mock_service_token_user(token_name="test-token", permissions=None):
        """Create a properly structured mock service token user."""
        from unittest.mock import Mock

        from src.auth.middleware import ServiceTokenUser

        user = Mock(spec=ServiceTokenUser)
        user.token_name = token_name
        user.token_id = f"{token_name}-id"
        user.metadata = {"permissions": permissions or ["read"]}
        user.usage_count = 0
        user.has_permission = Mock(return_value=True)

        # Make sure isinstance() works correctly
        user.__class__ = ServiceTokenUser
        return user


@pytest.fixture
def auth_test_helper():
    """Provide the authentication test helper."""
    return AuthTestHelper


# FastAPI app with authentication for integration testing
@pytest.fixture
def authenticated_test_app():
    """FastAPI app with authentication middleware configured for testing."""
    from fastapi import FastAPI

    app = FastAPI(title="Authenticated Test App")

    # Configure authentication with test settings
    test_config = create_test_config(
        dev_mode=True,
        email_whitelist=["test@example.com", "@testdomain.com", "admin@example.com"],
        admin_emails=["admin@example.com"],
    )
    config_manager = ConfigManager(test_config)

    # Setup middleware
    middleware = config_manager.create_middleware()
    app.add_middleware(
        type(middleware),
        whitelist_validator=middleware.whitelist_validator,
        session_manager=middleware.session_manager,
        public_paths=middleware.public_paths,
        health_check_paths=middleware.health_check_paths,
        enable_session_cookies=middleware.enable_session_cookies,
    )

    return app


# Test route helpers
@pytest.fixture
def test_routes():
    """Helper function to add test routes to FastAPI apps."""

    def add_test_routes(app):
        from src.api.auth_endpoints import require_admin_role
        from src.auth.middleware import require_authentication

        @app.get("/test/public")
        async def public_endpoint():
            return {"message": "public"}

        @app.get("/test/authenticated")
        async def authenticated_endpoint(user=require_authentication):
            return {"message": "authenticated", "user": user.email if hasattr(user, "email") else str(user)}

        @app.get("/test/admin")
        async def admin_endpoint(user=require_admin_role):
            return {"message": "admin", "user": user.email if hasattr(user, "email") else str(user)}

        return app

    return add_test_routes
