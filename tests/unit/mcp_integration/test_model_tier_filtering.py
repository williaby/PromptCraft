"""Tests for model registry tier filtering functionality."""

from unittest.mock import Mock

from src.mcp_integration.model_registry import ModelCapabilities, UserTierFilter


class TestUserTierFilter:
    """Test UserTierFilter functionality."""

    def test_tier_category_access_definitions(self):
        """Test that tier access categories are properly defined."""
        assert "free_general" in UserTierFilter.TIER_CATEGORY_ACCESS["limited"]
        assert len(UserTierFilter.TIER_CATEGORY_ACCESS["limited"]) == 1  # Only free models

        assert "free_general" in UserTierFilter.TIER_CATEGORY_ACCESS["full"]
        assert "premium_reasoning" in UserTierFilter.TIER_CATEGORY_ACCESS["full"]
        assert len(UserTierFilter.TIER_CATEGORY_ACCESS["full"]) >= 2  # Free + premium models

        assert UserTierFilter.TIER_CATEGORY_ACCESS["admin"] == UserTierFilter.TIER_CATEGORY_ACCESS["full"]

    def test_filter_models_by_tier_limited(self):
        """Test filtering models for limited tier users."""
        # Mock model registry
        mock_registry = Mock()

        # Define model capabilities
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
            available_regions=["us", "eu"],
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

        mock_registry.get_model_capabilities.side_effect = lambda model_id: {
            "free-model": free_model,
            "premium-model": premium_model,
        }.get(model_id)

        models = ["free-model", "premium-model"]
        filtered = UserTierFilter.filter_models_by_tier(models, "limited", mock_registry)

        assert "free-model" in filtered
        assert "premium-model" not in filtered
        assert len(filtered) == 1

    def test_filter_models_by_tier_full(self):
        """Test filtering models for full tier users."""
        # Mock model registry
        mock_registry = Mock()

        # Define model capabilities (same as above)
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
            available_regions=["us", "eu"],
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

        mock_registry.get_model_capabilities.side_effect = lambda model_id: {
            "free-model": free_model,
            "premium-model": premium_model,
        }.get(model_id)

        models = ["free-model", "premium-model"]
        filtered = UserTierFilter.filter_models_by_tier(models, "full", mock_registry)

        assert "free-model" in filtered
        assert "premium-model" in filtered
        assert len(filtered) == 2

    def test_filter_models_by_tier_unknown_tier(self):
        """Test filtering with unknown tier defaults to limited."""
        mock_registry = Mock()

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
            available_regions=["us", "eu"],
            enabled=True,
        )

        mock_registry.get_model_capabilities.return_value = free_model

        models = ["free-model"]
        filtered = UserTierFilter.filter_models_by_tier(models, "unknown_tier", mock_registry)

        assert len(filtered) == 1  # Should default to limited access

    def test_can_access_model_true(self):
        """Test can_access_model returns True for accessible models."""
        mock_registry = Mock()

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
            available_regions=["us", "eu"],
            enabled=True,
        )

        mock_registry.get_model_capabilities.return_value = free_model

        assert UserTierFilter.can_access_model("free-model", "limited", mock_registry) is True
        assert UserTierFilter.can_access_model("free-model", "full", mock_registry) is True
        assert UserTierFilter.can_access_model("free-model", "admin", mock_registry) is True

    def test_can_access_model_false(self):
        """Test can_access_model returns False for inaccessible models."""
        mock_registry = Mock()

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

        mock_registry.get_model_capabilities.return_value = premium_model

        assert UserTierFilter.can_access_model("premium-model", "limited", mock_registry) is False
        assert UserTierFilter.can_access_model("premium-model", "full", mock_registry) is True
        assert UserTierFilter.can_access_model("premium-model", "admin", mock_registry) is True

    def test_filter_models_missing_capabilities(self):
        """Test filtering handles models without capabilities gracefully."""
        mock_registry = Mock()
        mock_registry.get_model_capabilities.return_value = None  # Model not found

        models = ["nonexistent-model"]
        filtered = UserTierFilter.filter_models_by_tier(models, "limited", mock_registry)

        assert len(filtered) == 0  # Model without capabilities should be filtered out

    def test_filter_models_empty_list(self):
        """Test filtering empty model list."""
        mock_registry = Mock()

        filtered = UserTierFilter.filter_models_by_tier([], "limited", mock_registry)

        assert filtered == []

    def test_admin_tier_access_equivalence(self):
        """Test that admin tier has same access as full tier."""
        assert UserTierFilter.TIER_CATEGORY_ACCESS["admin"] == UserTierFilter.TIER_CATEGORY_ACCESS["full"]

    def test_tier_hierarchy_consistency(self):
        """Test that tier access follows expected hierarchy."""
        limited_categories = set(UserTierFilter.TIER_CATEGORY_ACCESS["limited"])
        full_categories = set(UserTierFilter.TIER_CATEGORY_ACCESS["full"])
        admin_categories = set(UserTierFilter.TIER_CATEGORY_ACCESS["admin"])

        # Limited should be a subset of full
        assert limited_categories.issubset(full_categories)

        # Admin should have same access as full
        assert admin_categories == full_categories

        # Full should have more categories than limited
        assert len(full_categories) > len(limited_categories)
