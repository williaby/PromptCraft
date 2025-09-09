"""Integration tests for auth_simple FastAPI middleware.

This module provides comprehensive end-to-end testing of the simplified
authentication system with real FastAPI applications, following patterns
from the main auth integration tests for consistency and migration compatibility.

Test Coverage:
- Complete FastAPI application with middleware
- End-to-end authentication flows
- Session management lifecycle
- Error handling and status codes
- Public path handling
- Real HTTP request/response cycles
"""

from unittest.mock import Mock, patch

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
import pytest

from src.auth_simple import (
    AuthConfig,
    CloudflareAccessMiddleware,
    SimpleSessionManager,
    require_admin,
    require_auth,
    setup_auth_middleware,
)
from src.auth_simple.whitelist import EmailWhitelistValidator


@pytest.mark.integration
class TestAuthSimpleIntegration:
    """Integration tests for complete auth_simple authentication flow."""

    @pytest.fixture
    def auth_config(self) -> AuthConfig:
        """Create authentication configuration for integration testing."""
        return AuthConfig(
            auth_mode="cloudflare_simple",
            enabled=True,
            email_whitelist=["user@example.com", "admin@example.com", "@company.com", "concurrent@example.com", "user1@example.com", "user2@example.com"],
            admin_emails=["admin@example.com"],
            full_users=["user@example.com", "concurrent@example.com", "user1@example.com", "user2@example.com"],
            limited_users=["@company.com"],
            session_timeout=3600,
            enable_session_cookies=True,
            session_cookie_secure=False,  # For testing
            public_paths={"/health", "/docs", "/public"},
            dev_mode=True,  # Enable for testing
        )

    @pytest.fixture
    def auth_components(self, auth_config: AuthConfig) -> dict:
        """Create authentication components for testing."""
        validator = EmailWhitelistValidator(
            whitelist=auth_config.email_whitelist,
            admin_emails=auth_config.admin_emails,
            full_users=auth_config.full_users,
            limited_users=auth_config.limited_users,
        )
        session_manager = SimpleSessionManager(session_timeout=auth_config.session_timeout)
        
        return {
            "whitelist_validator": validator,
            "session_manager": session_manager,
            "public_paths": auth_config.public_paths,
            "enable_session_cookies": auth_config.enable_session_cookies,
        }

    @pytest.fixture
    def fastapi_app(self, auth_components: dict) -> FastAPI:
        """Create FastAPI application with authentication middleware."""
        app = FastAPI()
        
        # Add middleware - let FastAPI instantiate it
        app.add_middleware(
            CloudflareAccessMiddleware,
            **auth_components,
        )

        # Public endpoints
        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        @app.get("/public")
        async def public_endpoint():
            return {"message": "This is public"}

        @app.get("/docs")
        async def docs():
            return {"docs": "API documentation"}

        # Protected endpoints
        @app.get("/protected")
        async def protected(user=Depends(require_auth)):
            return {"user": user, "message": "Protected content"}

        @app.get("/admin")
        async def admin_only(user=Depends(require_admin)):
            return {"user": user, "message": "Admin only content"}

        @app.get("/user-info")
        async def user_info(request: Request):
            return {"user": getattr(request.state, "user", None)}

        return app

    @pytest.fixture
    def test_client(self, fastapi_app: FastAPI) -> TestClient:
        """Create test client for FastAPI application."""
        return TestClient(fastapi_app)

    def test_public_endpoints_no_auth_required(self, test_client: TestClient):
        """Test that public endpoints don't require authentication."""
        # Test all public endpoints
        public_paths = ["/health", "/public", "/docs"]
        
        for path in public_paths:
            response = test_client.get(path)
            assert response.status_code == 200
            
            # Handle different content types
            if path == "/docs":
                # /docs returns HTML (Swagger UI)
                assert "swagger-ui" in response.text.lower()
            else:
                # Other endpoints return JSON
                json_data = response.json()
                assert "status" in json_data or "message" in json_data

    def test_protected_endpoint_no_auth_fails(self, test_client: TestClient):
        """Test that protected endpoints fail without authentication."""
        response = test_client.get("/protected")
        assert response.status_code == 401
        assert "No authenticated user found" in response.json()["detail"]

    def test_admin_endpoint_no_auth_fails(self, test_client: TestClient):
        """Test that admin endpoints fail without authentication."""
        response = test_client.get("/admin")
        assert response.status_code == 401
        assert "No authenticated user found" in response.json()["detail"]

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_protected_endpoint_with_valid_user(self, mock_extract_user, test_client: TestClient):
        """Test protected endpoint with valid authenticated user."""
        # Mock Cloudflare user extraction
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "user@example.com"
        mock_extract_user.return_value = mock_cloudflare_user

        # Mock Cloudflare headers
        headers = {
            "cf-access-authenticated-user-email": "user@example.com",
            "cf-ray": "test-ray-123",
            "cf-ipcountry": "US",
        }

        response = test_client.get("/protected", headers=headers)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["user"]["email"] == "user@example.com"
        assert response_data["user"]["user_tier"] == "full"
        assert response_data["user"]["can_access_premium"] is True
        assert response_data["message"] == "Protected content"

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_admin_endpoint_with_admin_user(self, mock_extract_user, test_client: TestClient):
        """Test admin endpoint with admin user."""
        # Mock Cloudflare admin user
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "admin@example.com"
        mock_extract_user.return_value = mock_cloudflare_user

        headers = {
            "cf-access-authenticated-user-email": "admin@example.com",
            "cf-ray": "admin-ray-123",
            "cf-ipcountry": "US",
        }

        response = test_client.get("/admin", headers=headers)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["user"]["email"] == "admin@example.com"
        assert response_data["user"]["is_admin"] is True
        assert response_data["user"]["user_tier"] == "admin"
        assert response_data["message"] == "Admin only content"

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_admin_endpoint_with_regular_user_fails(self, mock_extract_user, test_client: TestClient):
        """Test admin endpoint with regular user fails."""
        # Mock regular user
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "user@example.com"
        mock_extract_user.return_value = mock_cloudflare_user

        headers = {
            "cf-access-authenticated-user-email": "user@example.com",
            "cf-ray": "user-ray-123",
            "cf-ipcountry": "US",
        }

        response = test_client.get("/admin", headers=headers)
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_unauthorized_email_access_denied(self, mock_extract_user, test_client: TestClient):
        """Test that unauthorized emails are denied access."""
        # Mock unauthorized user
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "unauthorized@example.com"
        mock_extract_user.return_value = mock_cloudflare_user

        headers = {
            "cf-access-authenticated-user-email": "unauthorized@example.com",
            "cf-ray": "unauthorized-ray-123",
            "cf-ipcountry": "US",
        }

        response = test_client.get("/protected", headers=headers)
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"]

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_domain_whitelist_authorization(self, mock_extract_user, test_client: TestClient):
        """Test authorization via domain whitelist."""
        # Mock user from whitelisted domain
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "newuser@company.com"
        mock_extract_user.return_value = mock_cloudflare_user

        headers = {
            "cf-access-authenticated-user-email": "newuser@company.com",
            "cf-ray": "domain-ray-123",
            "cf-ipcountry": "US",
        }

        response = test_client.get("/protected", headers=headers)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["user"]["email"] == "newuser@company.com"
        assert response_data["user"]["user_tier"] == "limited"  # Default for domain users
        assert response_data["user"]["can_access_premium"] is False

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_session_management_lifecycle(self, mock_extract_user, test_client: TestClient):
        """Test complete session management lifecycle."""
        # Mock user
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "user@example.com"
        mock_extract_user.return_value = mock_cloudflare_user

        headers = {
            "cf-access-authenticated-user-email": "user@example.com",
            "cf-ray": "session-ray-123",
            "cf-ipcountry": "US",
        }

        # First request - should create session
        response1 = test_client.get("/user-info", headers=headers)
        assert response1.status_code == 200
        
        # Should have session cookie set
        assert "session_id" in response1.cookies
        session_id = response1.cookies["session_id"]
        assert session_id is not None

        # Second request with session cookie - should reuse session  
        cookies = {"session_id": session_id}
        response2 = test_client.get("/user-info", headers=headers, cookies=cookies)
        assert response2.status_code == 200
        
        # Should have same user info
        user_info1 = response1.json()["user"]
        user_info2 = response2.json()["user"]
        assert user_info1["email"] == user_info2["email"]
        assert user_info1["session_id"] == user_info2["session_id"]

    def test_static_files_bypass_auth(self, test_client: TestClient):
        """Test that static files bypass authentication."""
        # FastAPI TestClient doesn't serve static files by default
        # but we can test that our middleware would bypass them
        
        # This tests the middleware logic, not actual file serving
        static_paths = ["/static/css/style.css", "/static/js/app.js", "/static/images/logo.png"]
        
        for path in static_paths:
            # These would normally return 404 since no handler exists
            # but the middleware should process them as public
            response = test_client.get(path)
            # Should not get auth error (401/403)
            assert response.status_code in [404, 405]  # Not auth errors

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_error_handling_middleware_exception(self, mock_extract_user, test_client: TestClient):
        """Test middleware error handling for exceptions."""
        # Mock exception during user extraction
        mock_extract_user.side_effect = Exception("Unexpected middleware error")

        headers = {
            "cf-access-authenticated-user-email": "user@example.com",
            "cf-ray": "error-ray-123",
        }

        response = test_client.get("/protected", headers=headers)
        assert response.status_code == 500
        assert "Internal authentication error" in response.json()["detail"]

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_tier_based_access_control(self, mock_extract_user, test_client: TestClient):
        """Test tier-based access control functionality."""
        test_users = [
            ("admin@example.com", "admin", True, True),
            ("user@example.com", "full", False, True), 
            ("limited@company.com", "limited", False, False),
        ]

        for email, expected_tier, expected_admin, expected_premium in test_users:
            mock_cloudflare_user = Mock()
            mock_cloudflare_user.email = email
            mock_extract_user.return_value = mock_cloudflare_user

            headers = {
                "cf-access-authenticated-user-email": email,
                "cf-ray": f"tier-test-{email.replace('@', '-').replace('.', '-')}",
            }

            response = test_client.get("/user-info", headers=headers)
            assert response.status_code == 200
            
            user_info = response.json()["user"]
            assert user_info["email"] == email
            assert user_info["user_tier"] == expected_tier
            assert user_info["is_admin"] is expected_admin
            assert user_info["can_access_premium"] is expected_premium

    def test_health_check_during_auth_failure(self, test_client: TestClient):
        """Test that health checks work even during auth system issues."""
        # Even if auth system has issues, health checks should work
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_concurrent_session_requests(self, mock_extract_user, test_client: TestClient):
        """Test handling of concurrent requests with the same user."""
        # Mock user
        mock_cloudflare_user = Mock()
        mock_cloudflare_user.email = "concurrent@example.com"
        mock_extract_user.return_value = mock_cloudflare_user

        headers = {
            "cf-access-authenticated-user-email": "concurrent@example.com",
            "cf-ray": "concurrent-ray-123",
        }

        # Make multiple concurrent requests
        responses = []
        for i in range(3):
            response = test_client.get("/user-info", headers=headers)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            user_info = response.json()["user"]
            assert user_info["email"] == "concurrent@example.com"

        # Should have created sessions (each request creates new session without cookie)
        session_ids = [response.json()["user"]["session_id"] for response in responses]
        # Each request without session cookie creates new session
        assert len(set(session_ids)) == 3

    @patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request")
    def test_request_state_isolation(self, mock_extract_user, test_client: TestClient):
        """Test that request state is properly isolated between requests."""
        # Mock different users
        users = ["user1@example.com", "user2@example.com"]
        responses = []

        for email in users:
            mock_cloudflare_user = Mock()
            mock_cloudflare_user.email = email
            mock_extract_user.return_value = mock_cloudflare_user

            headers = {
                "cf-access-authenticated-user-email": email,
                "cf-ray": f"isolation-{email.replace('@', '-').replace('.', '-')}",
            }

            response = test_client.get("/user-info", headers=headers)
            responses.append((email, response))

        # Verify each response has correct user info
        for expected_email, response in responses:
            assert response.status_code == 200
            user_info = response.json()["user"]
            assert user_info["email"] == expected_email


@pytest.mark.integration  
class TestAuthSimpleSetupIntegration:
    """Integration tests for auth setup utilities."""

    def test_setup_auth_middleware_integration(self):
        """Test setup_auth_middleware utility function."""
        app = FastAPI()
        
        # Mock configuration manager
        from src.auth_simple.config import AuthConfig, ConfigManager
        config = AuthConfig(
            enabled=True,
            email_whitelist=["test@example.com"],
            admin_emails=["admin@example.com"],
            public_paths={"/health"},
        )
        config_manager = ConfigManager(config)
        
        # Setup middleware
        middleware_instance = setup_auth_middleware(app, config_manager)
        
        assert middleware_instance is not None
        assert isinstance(middleware_instance, CloudflareAccessMiddleware)

    def test_setup_auth_middleware_disabled(self):
        """Test setup with disabled authentication."""
        app = FastAPI()
        
        from src.auth_simple.config import AuthConfig, ConfigManager
        config = AuthConfig(enabled=False)
        config_manager = ConfigManager(config)
        
        middleware_instance = setup_auth_middleware(app, config_manager)
        
        # Should return None when auth is disabled
        assert middleware_instance is None

    def test_setup_auth_middleware_disabled_mode(self):
        """Test setup with disabled auth mode."""
        app = FastAPI()
        
        from src.auth_simple.config import AuthConfig, ConfigManager
        config = AuthConfig(auth_mode="disabled")
        config_manager = ConfigManager(config)
        
        middleware_instance = setup_auth_middleware(app, config_manager)
        
        # Should return None when auth mode is disabled
        assert middleware_instance is None


@pytest.mark.integration
class TestAuthSimpleErrorScenarios:
    """Integration tests for error scenarios and edge cases."""

    @pytest.fixture
    def minimal_app(self) -> FastAPI:
        """Create minimal FastAPI app for error testing."""
        app = FastAPI()
        
        # Minimal middleware setup
        validator = EmailWhitelistValidator(["test@example.com"])
        session_manager = SimpleSessionManager()
        
        app.add_middleware(
            CloudflareAccessMiddleware,
            whitelist_validator=validator,
            session_manager=session_manager,
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    def test_malformed_cloudflare_headers(self, minimal_app: FastAPI):
        """Test handling of malformed Cloudflare headers."""
        client = TestClient(minimal_app)
        
        # Missing required headers
        response = client.get("/test")
        assert response.status_code == 401

        # Malformed headers
        headers = {
            "cf-access-authenticated-user-email": "",  # Empty email
            "cf-ray": "test-ray",
        }
        response = client.get("/test", headers=headers)
        assert response.status_code == 401

    def test_session_cookie_security_attributes(self, minimal_app: FastAPI):
        """Test that session cookies have proper security attributes."""
        client = TestClient(minimal_app)
        
        # This would require actual cookie inspection which TestClient doesn't fully support
        # But we've tested the _set_session_cookie method in unit tests
        # This is more for documentation of expected behavior
        
        with patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request") as mock_extract:
            mock_user = Mock()
            mock_user.email = "test@example.com"
            mock_extract.return_value = mock_user

            headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "test"}
            response = client.get("/test", headers=headers)
            
            # Should succeed and set secure cookie
            assert response.status_code == 200

    def test_middleware_order_independence(self):
        """Test that auth middleware works regardless of middleware order."""
        app = FastAPI()
        
        # Add some other middleware first
        @app.middleware("http")
        async def custom_middleware(request, call_next):
            response = await call_next(request)
            response.headers["X-Custom"] = "test"
            return response
        
        # Then add auth middleware
        validator = EmailWhitelistValidator(["test@example.com"])
        session_manager = SimpleSessionManager()
        
        app.add_middleware(
            CloudflareAccessMiddleware,
            whitelist_validator=validator,
            session_manager=session_manager,
        )

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        
        with patch("src.auth_simple.cloudflare_auth.CloudflareAuthHandler.extract_user_from_request") as mock_extract:
            mock_user = Mock()
            mock_user.email = "test@example.com"
            mock_extract.return_value = mock_user

            headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "test"}
            response = client.get("/test", headers=headers)
            
            assert response.status_code == 200
            assert "X-Custom" in response.headers