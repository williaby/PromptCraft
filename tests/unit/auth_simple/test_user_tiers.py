"""Tests for user tier functionality in the authentication system."""

import pytest

from src.auth_simple.whitelist import EmailWhitelistValidator, UserTier


class TestUserTier:
    """Test UserTier enum functionality."""

    def test_user_tier_values(self):
        """Test that UserTier enum has expected values."""
        assert UserTier.ADMIN == "admin"
        assert UserTier.FULL == "full"
        assert UserTier.LIMITED == "limited"

    def test_from_string_valid(self):
        """Test UserTier.from_string with valid values."""
        assert UserTier.from_string("admin") == UserTier.ADMIN
        assert UserTier.from_string("full") == UserTier.FULL
        assert UserTier.from_string("limited") == UserTier.LIMITED

        # Test case insensitive
        assert UserTier.from_string("ADMIN") == UserTier.ADMIN
        assert UserTier.from_string("Full") == UserTier.FULL
        assert UserTier.from_string(" LIMITED ") == UserTier.LIMITED

    def test_from_string_invalid(self):
        """Test UserTier.from_string with invalid values."""
        with pytest.raises(ValueError, match="Invalid user tier"):
            UserTier.from_string("invalid")

        with pytest.raises(ValueError, match="Invalid user tier"):
            UserTier.from_string("")

    def test_can_access_premium_models(self):
        """Test premium model access property."""
        assert UserTier.ADMIN.can_access_premium_models is True
        assert UserTier.FULL.can_access_premium_models is True
        assert UserTier.LIMITED.can_access_premium_models is False

    def test_has_admin_privileges(self):
        """Test admin privileges property."""
        assert UserTier.ADMIN.has_admin_privileges is True
        assert UserTier.FULL.has_admin_privileges is False
        assert UserTier.LIMITED.has_admin_privileges is False


class TestEmailWhitelistValidatorTiers:
    """Test EmailWhitelistValidator with tier functionality."""

    def test_basic_tier_initialization(self):
        """Test validator initialization with tier information."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com", "@company.com"],
            admin_emails=["admin@example.com"],
            full_users=["full@example.com"],
            limited_users=["limited@example.com"],
        )

        assert len(validator.admin_emails) == 1
        assert len(validator.full_users) == 1
        assert len(validator.limited_users) == 1
        assert "admin@example.com" in validator.admin_emails
        assert "full@example.com" in validator.full_users
        assert "limited@example.com" in validator.limited_users

    def test_get_user_tier_admin(self):
        """Test get_user_tier for admin users."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com"],
            admin_emails=["admin@example.com"],
            full_users=[],
            limited_users=[],
        )

        tier = validator.get_user_tier("admin@example.com")
        assert tier == UserTier.ADMIN

    def test_get_user_tier_full(self):
        """Test get_user_tier for full users."""
        validator = EmailWhitelistValidator(
            whitelist=["full@example.com"],
            admin_emails=[],
            full_users=["full@example.com"],
            limited_users=[],
        )

        tier = validator.get_user_tier("full@example.com")
        assert tier == UserTier.FULL

    def test_get_user_tier_limited(self):
        """Test get_user_tier for limited users."""
        validator = EmailWhitelistValidator(
            whitelist=["limited@example.com"],
            admin_emails=[],
            full_users=[],
            limited_users=["limited@example.com"],
        )

        tier = validator.get_user_tier("limited@example.com")
        assert tier == UserTier.LIMITED

    def test_get_user_tier_default_limited(self):
        """Test that authorized users not in tier lists default to limited."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            admin_emails=[],
            full_users=[],
            limited_users=[],
        )

        tier = validator.get_user_tier("user@example.com")
        assert tier == UserTier.LIMITED

    def test_get_user_tier_priority_order(self):
        """Test that admin tier takes priority over other tiers."""
        # User in both admin and full lists should be admin
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            admin_emails=["user@example.com"],
            full_users=["user@example.com"],
            limited_users=["user@example.com"],
        )

        tier = validator.get_user_tier("user@example.com")
        assert tier == UserTier.ADMIN

    def test_get_user_tier_unauthorized(self):
        """Test get_user_tier for unauthorized users."""
        validator = EmailWhitelistValidator(
            whitelist=["authorized@example.com"],
            admin_emails=[],
            full_users=[],
            limited_users=[],
        )

        with pytest.raises(ValueError, match="not authorized"):
            validator.get_user_tier("unauthorized@example.com")

    def test_get_user_tier_empty_email(self):
        """Test get_user_tier with empty email."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            admin_emails=[],
            full_users=[],
            limited_users=[],
        )

        with pytest.raises(ValueError, match="Email cannot be empty"):
            validator.get_user_tier("")

    def test_can_access_premium_models(self):
        """Test can_access_premium_models method."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com", "full@example.com", "limited@example.com"],
            admin_emails=["admin@example.com"],
            full_users=["full@example.com"],
            limited_users=["limited@example.com"],
        )

        assert validator.can_access_premium_models("admin@example.com") is True
        assert validator.can_access_premium_models("full@example.com") is True
        assert validator.can_access_premium_models("limited@example.com") is False
        assert validator.can_access_premium_models("unauthorized@example.com") is False

    def test_has_admin_privileges(self):
        """Test has_admin_privileges method."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com", "full@example.com", "limited@example.com"],
            admin_emails=["admin@example.com"],
            full_users=["full@example.com"],
            limited_users=["limited@example.com"],
        )

        assert validator.has_admin_privileges("admin@example.com") is True
        assert validator.has_admin_privileges("full@example.com") is False
        assert validator.has_admin_privileges("limited@example.com") is False
        assert validator.has_admin_privileges("unauthorized@example.com") is False

    def test_whitelist_stats_with_tiers(self):
        """Test get_whitelist_stats includes tier information."""
        validator = EmailWhitelistValidator(
            whitelist=["user1@example.com", "user2@example.com", "@company.com"],
            admin_emails=["admin@example.com"],
            full_users=["full1@example.com", "full2@example.com"],
            limited_users=["limited@example.com"],
        )

        stats = validator.get_whitelist_stats()

        assert stats["admin_emails"] == 1
        assert stats["full_users"] == 2
        assert stats["limited_users"] == 1
        assert "tier_distribution" in stats
        assert stats["tier_distribution"]["admin"] == 1
        assert stats["tier_distribution"]["full"] == 2
        assert stats["tier_distribution"]["limited"] == 1

    def test_validate_whitelist_config_tier_conflicts(self):
        """Test validation catches tier conflicts."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            admin_emails=["user@example.com"],  # Same user in multiple tiers
            full_users=["user@example.com"],
            limited_users=[],
        )

        warnings = validator.validate_whitelist_config()

        # Should warn about user being in multiple tiers
        tier_conflict_warnings = [w for w in warnings if "multiple tiers" in w]
        assert len(tier_conflict_warnings) > 0
        assert "user@example.com" in tier_conflict_warnings[0]

    def test_validate_whitelist_config_tier_users_not_in_whitelist(self):
        """Test validation catches tier users not in main whitelist."""
        validator = EmailWhitelistValidator(
            whitelist=["authorized@example.com"],
            admin_emails=["admin-not-in-whitelist@example.com"],
            full_users=["full-not-in-whitelist@example.com"],
            limited_users=["limited-not-in-whitelist@example.com"],
        )

        warnings = validator.validate_whitelist_config()

        # Should warn about each tier user not being in whitelist
        admin_warnings = [w for w in warnings if "Admin email" in w and "not in whitelist" in w]
        full_warnings = [w for w in warnings if "Full user email" in w and "not in whitelist" in w]
        limited_warnings = [w for w in warnings if "Limited user email" in w and "not in whitelist" in w]

        assert len(admin_warnings) == 1
        assert len(full_warnings) == 1
        assert len(limited_warnings) == 1

    def test_case_sensitivity_with_tiers(self):
        """Test case sensitivity handling with tier emails."""
        # Case sensitive mode
        validator_sensitive = EmailWhitelistValidator(
            whitelist=["User@Example.com", "Admin@Example.com", "Full@Example.com", "Limited@Example.com"],
            admin_emails=["Admin@Example.com"],
            full_users=["Full@Example.com"],
            limited_users=["Limited@Example.com"],
            case_sensitive=True,
        )

        # Should not match different cases
        with pytest.raises(ValueError, match="not authorized"):
            validator_sensitive.get_user_tier("user@example.com")

        # Case insensitive mode (default)
        validator_insensitive = EmailWhitelistValidator(
            whitelist=["User@Example.com", "Admin@Example.com", "Full@Example.com", "Limited@Example.com"],
            admin_emails=["Admin@Example.com"],
            full_users=["Full@Example.com"],
            limited_users=["Limited@Example.com"],
            case_sensitive=False,
        )

        # Should match different cases
        assert validator_insensitive.get_user_tier("admin@example.com") == UserTier.ADMIN
        assert validator_insensitive.get_user_tier("full@example.com") == UserTier.FULL
        assert validator_insensitive.get_user_tier("limited@example.com") == UserTier.LIMITED
