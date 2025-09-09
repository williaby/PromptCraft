"""Integration tests for the complete user tier system."""

from unittest.mock import Mock, patch

from fastapi import Request
import pytest
from starlette.datastructures import Headers

from src.auth_simple.cloudflare_auth import CloudflareAuthHandler
from src.auth_simple.middleware import CloudflareAccessMiddleware, SimpleSessionManager
from src.auth_simple.whitelist import EmailWhitelistValidator, UserTier
from src.mcp_integration.model_registry import UserTierFilter


class TestUserTierIntegration:
    """Integration tests for complete user tier system."""

    @pytest.fixture
    def mock_cloudflare_headers(self):
        """Mock Cloudflare Access headers."""
        return {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "test-ray-id", "cf-ipcountry": "US"}

    @pytest.fixture
    def limited_user_validator(self):
        """Create validator with limited user configuration."""
        return EmailWhitelistValidator(
            whitelist=["limited@example.com"],
            admin_emails=[],
            full_users=[],
            limited_users=["limited@example.com"],
        )

    @pytest.fixture
    def full_user_validator(self):
        """Create validator with full user configuration."""
        return EmailWhitelistValidator(
            whitelist=["full@example.com"],
            admin_emails=[],
            full_users=["full@example.com"],
            limited_users=[],
        )

    @pytest.fixture
    def admin_user_validator(self):
        """Create validator with admin user configuration."""
        return EmailWhitelistValidator(
            whitelist=["admin@example.com"],
            admin_emails=["admin@example.com"],
            full_users=[],
            limited_users=[],
        )

    @pytest.fixture
    def mock_request(self, mock_cloudflare_headers):
        """Create mock FastAPI request with Cloudflare headers."""
        request = Mock(spec=Request)
        request.headers = Headers(mock_cloudflare_headers)
        request.state = Mock()
        # Configure state to support both attribute and dict-like access
        request.state.user = {}
        return request

    def test_limited_user_tier_detection(self, limited_user_validator, mock_request):
        """Test that limited users are correctly identified."""
        # Update headers for limited user
        mock_request.headers = Headers(
            {
                "cf-access-authenticated-user-email": "limited@example.com",
                "cf-ray": "test-ray-id",
                "cf-ipcountry": "US",
            },
        )

        # Test tier detection
        tier = limited_user_validator.get_user_tier("limited@example.com")
        assert tier == UserTier.LIMITED
        assert tier.can_access_premium_models is False
        assert tier.has_admin_privileges is False

    def test_full_user_tier_detection(self, full_user_validator, mock_request):
        """Test that full users are correctly identified."""
        # Update headers for full user
        mock_request.headers = Headers(
            {"cf-access-authenticated-user-email": "full@example.com", "cf-ray": "test-ray-id", "cf-ipcountry": "US"},
        )

        # Test tier detection
        tier = full_user_validator.get_user_tier("full@example.com")
        assert tier == UserTier.FULL
        assert tier.can_access_premium_models is True
        assert tier.has_admin_privileges is False

    def test_admin_user_tier_detection(self, admin_user_validator, mock_request):
        """Test that admin users are correctly identified."""
        # Update headers for admin user
        mock_request.headers = Headers(
            {"cf-access-authenticated-user-email": "admin@example.com", "cf-ray": "test-ray-id", "cf-ipcountry": "US"},
        )

        # Test tier detection
        tier = admin_user_validator.get_user_tier("admin@example.com")
        assert tier == UserTier.ADMIN
        assert tier.can_access_premium_models is True
        assert tier.has_admin_privileges is True

    async def test_middleware_injects_tier_information(self, full_user_validator, mock_request):
        """Test that middleware correctly injects tier information into request state."""
        # Update headers to match the full_user_validator
        from starlette.datastructures import Headers

        mock_request.headers = Headers(
            {"cf-access-authenticated-user-email": "full@example.com", "cf-ray": "test-ray-id", "cf-ipcountry": "US"},
        )

        # Create middleware components
        cloudflare_auth = CloudflareAuthHandler()
        session_manager = SimpleSessionManager()

        # Mock the Cloudflare user extraction - use email that matches validator
        mock_user = Mock()
        mock_user.email = "full@example.com"  # Match the full_user_validator fixture
        mock_user.authenticated_at = "2023-01-01T00:00:00Z"

        with patch.object(cloudflare_auth, "extract_user_from_request", return_value=mock_user):
            with patch.object(cloudflare_auth, "create_user_context", return_value={}):
                middleware = CloudflareAccessMiddleware(
                    app=None,
                    whitelist_validator=full_user_validator,
                    session_manager=session_manager,
                )

                # Simulate the authentication process
                await middleware._authenticate_request(mock_request)

                # Check that tier information is injected
                assert hasattr(mock_request.state, "user")
                assert mock_request.state.user["user_tier"] == "full"
                assert mock_request.state.user["can_access_premium"] is True
                assert mock_request.state.user["is_admin"] is False

    @patch("src.mcp_integration.model_registry.ModelRegistry.get_model_capabilities")
    def test_model_registry_tier_filtering(self, mock_get_capabilities):
        """Test that model registry correctly filters models by tier."""
        from src.mcp_integration.model_registry import ModelCapabilities

        # Mock model capabilities
        free_model = ModelCapabilities(
            model_id="free-model",
            display_name="Free Model",
            provider="test",
            category="free_general",
            context_window=4096,
            max_tokens_per_request=2048,
            rate_limit_requests_per_minute=20,
            rate_limit_tokens_per_minute=None,
            cost_per_input_token=None,
            cost_per_output_token=None,
            timeout_seconds=30,
            supports_streaming=True,
            supports_function_calling=False,
            supports_vision=False,
            supports_reasoning=False,
            available_regions=["us"],
            enabled=True,
        )

        premium_model = ModelCapabilities(
            model_id="premium-model",
            display_name="Premium Model",
            provider="test",
            category="premium_reasoning",
            context_window=8192,
            max_tokens_per_request=4096,
            rate_limit_requests_per_minute=10,
            rate_limit_tokens_per_minute=None,
            cost_per_input_token=0.001,
            cost_per_output_token=0.002,
            timeout_seconds=30,
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False,
            supports_reasoning=True,
            available_regions=["us"],
            enabled=True,
        )

        def mock_capabilities(model_id):
            return {"free-model": free_model, "premium-model": premium_model}.get(model_id)

        mock_get_capabilities.side_effect = mock_capabilities

        registry = Mock()
        registry.get_model_capabilities = mock_capabilities

        # Test filtering for different tiers
        models = ["free-model", "premium-model"]

        # Limited user should only get free models
        limited_models = UserTierFilter.filter_models_by_tier(models, "limited", registry)
        assert "free-model" in limited_models
        assert "premium-model" not in limited_models

        # Full user should get all models
        full_models = UserTierFilter.filter_models_by_tier(models, "full", registry)
        assert "free-model" in full_models
        assert "premium-model" in full_models

        # Admin user should get all models
        admin_models = UserTierFilter.filter_models_by_tier(models, "admin", registry)
        assert "free-model" in admin_models
        assert "premium-model" in admin_models

    def test_end_to_end_tier_workflow(self):
        """Test complete workflow from authentication to model access."""
        # Create test users with different tiers
        validator = EmailWhitelistValidator(
            whitelist=["admin@test.com", "full@test.com", "limited@test.com"],
            admin_emails=["admin@test.com"],
            full_users=["full@test.com"],
            limited_users=["limited@test.com"],
        )

        # Test admin workflow
        admin_tier = validator.get_user_tier("admin@test.com")
        assert admin_tier == UserTier.ADMIN
        assert validator.can_access_premium_models("admin@test.com") is True
        assert validator.has_admin_privileges("admin@test.com") is True

        # Test full user workflow
        full_tier = validator.get_user_tier("full@test.com")
        assert full_tier == UserTier.FULL
        assert validator.can_access_premium_models("full@test.com") is True
        assert validator.has_admin_privileges("full@test.com") is False

        # Test limited user workflow
        limited_tier = validator.get_user_tier("limited@test.com")
        assert limited_tier == UserTier.LIMITED
        assert validator.can_access_premium_models("limited@test.com") is False
        assert validator.has_admin_privileges("limited@test.com") is False

    def test_configuration_validation_integration(self):
        """Test that configuration validation catches common issues."""
        # Test user in multiple tiers
        validator = EmailWhitelistValidator(
            whitelist=["user@test.com"],
            admin_emails=["user@test.com"],
            full_users=["user@test.com"],  # Same user in both admin and full
            limited_users=[],
        )

        warnings = validator.validate_whitelist_config()
        tier_warnings = [w for w in warnings if "multiple tiers" in w]
        assert len(tier_warnings) > 0

        # Test tier user not in whitelist
        validator2 = EmailWhitelistValidator(
            whitelist=["authorized@test.com"],
            admin_emails=["not-whitelisted@test.com"],  # Admin not in whitelist
            full_users=[],
            limited_users=[],
        )

        warnings2 = validator2.validate_whitelist_config()
        whitelist_warnings = [w for w in warnings2 if "not in whitelist" in w]
        assert len(whitelist_warnings) > 0

    def test_session_management_with_tiers(self):
        """Test that session management correctly handles tier information."""
        session_manager = SimpleSessionManager()

        # Create session for each tier
        admin_session_id = session_manager.create_session(email="admin@test.com", is_admin=True, user_tier="admin")

        full_session_id = session_manager.create_session(email="full@test.com", is_admin=False, user_tier="full")

        limited_session_id = session_manager.create_session(
            email="limited@test.com",
            is_admin=False,
            user_tier="limited",
        )

        # Verify sessions contain tier information
        admin_session = session_manager.get_session(admin_session_id)
        full_session = session_manager.get_session(full_session_id)
        limited_session = session_manager.get_session(limited_session_id)

        assert admin_session["user_tier"] == "admin"
        assert admin_session["is_admin"] is True

        assert full_session["user_tier"] == "full"
        assert full_session["is_admin"] is False

        assert limited_session["user_tier"] == "limited"
        assert limited_session["is_admin"] is False

    def test_domain_wildcards_with_tiers(self):
        """Test that domain wildcards work correctly with tiers."""
        validator = EmailWhitelistValidator(
            whitelist=["@company.com", "@partner.org"],
            admin_emails=["admin@company.com"],
            full_users=["@partner.org"],  # All partner.org users are full
            limited_users=["@company.com"],  # All company.com users are limited (except admin)
        )

        # Test admin user from company domain
        assert validator.get_user_tier("admin@company.com") == UserTier.ADMIN

        # Test regular company user (should be limited despite domain rule)
        assert validator.get_user_tier("user@company.com") == UserTier.LIMITED

        # Test partner org user (should be full due to domain rule)
        assert validator.get_user_tier("anyone@partner.org") == UserTier.FULL

    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback behaviors."""
        validator = EmailWhitelistValidator(
            whitelist=["user@test.com"],
            admin_emails=[],
            full_users=[],
            limited_users=[],
        )

        # Authorized user not in any tier should default to limited
        tier = validator.get_user_tier("user@test.com")
        assert tier == UserTier.LIMITED

        # Unauthorized user should raise error
        with pytest.raises(ValueError, match="not authorized"):
            validator.get_user_tier("unauthorized@test.com")

        # Empty email should raise error
        with pytest.raises(ValueError, match="Email cannot be empty"):
            validator.get_user_tier("")

        # None email should raise error
        with pytest.raises(ValueError, match="Email cannot be empty"):
            validator.get_user_tier(None)
