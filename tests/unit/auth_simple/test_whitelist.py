"""Comprehensive unit tests for auth_simple whitelist management.

This module provides extensive test coverage for the email whitelist validation
system including WhitelistManager, create_validator_from_env function, and
comprehensive EmailWhitelistValidator functionality.

Test Coverage:
- EmailWhitelistValidator complete functionality
- WhitelistManager runtime operations
- create_validator_from_env parsing
- UserTier integration and validation
- Edge cases and error handling
"""

from unittest.mock import patch

import pytest

from src.auth_simple.whitelist import (
    EmailWhitelistConfig,
    EmailWhitelistValidator,
    UserTier,
    WhitelistEntry,
    WhitelistManager,
    create_validator_from_env,
)


@pytest.mark.unit
class TestUserTier:
    """Test UserTier enum functionality."""

    def test_user_tier_values(self):
        """Test UserTier enum values."""
        assert UserTier.ADMIN == "admin"
        assert UserTier.FULL == "full"
        assert UserTier.LIMITED == "limited"

    def test_from_string_valid(self):
        """Test UserTier.from_string with valid values."""
        assert UserTier.from_string("admin") == UserTier.ADMIN
        assert UserTier.from_string("ADMIN") == UserTier.ADMIN
        assert UserTier.from_string("  full  ") == UserTier.FULL
        assert UserTier.from_string("LIMITED") == UserTier.LIMITED

    def test_from_string_invalid(self):
        """Test UserTier.from_string with invalid values."""
        with pytest.raises(ValueError, match="Invalid user tier: invalid"):
            UserTier.from_string("invalid")

        with pytest.raises(ValueError, match="Invalid user tier: "):
            UserTier.from_string("")

    def test_can_access_premium_models(self):
        """Test premium model access permissions."""
        assert UserTier.ADMIN.can_access_premium_models is True
        assert UserTier.FULL.can_access_premium_models is True
        assert UserTier.LIMITED.can_access_premium_models is False

    def test_has_admin_privileges(self):
        """Test admin privileges."""
        assert UserTier.ADMIN.has_admin_privileges is True
        assert UserTier.FULL.has_admin_privileges is False
        assert UserTier.LIMITED.has_admin_privileges is False


@pytest.mark.unit
class TestWhitelistEntry:
    """Test WhitelistEntry dataclass."""

    def test_whitelist_entry_creation(self):
        """Test WhitelistEntry creation."""
        entry = WhitelistEntry(
            value="test@example.com",
            is_domain=False,
            added_at="2023-01-01T00:00:00Z",
            description="Test user",
        )

        assert entry.value == "test@example.com"
        assert entry.is_domain is False
        assert entry.added_at == "2023-01-01T00:00:00Z"
        assert entry.description == "Test user"

    def test_whitelist_entry_minimal(self):
        """Test WhitelistEntry with minimal data."""
        entry = WhitelistEntry(
            value="@company.com",
            is_domain=True,
            added_at="2023-01-01T00:00:00Z",
        )

        assert entry.value == "@company.com"
        assert entry.is_domain is True
        assert entry.description is None


@pytest.mark.unit
class TestEmailWhitelistConfig:
    """Test EmailWhitelistConfig validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EmailWhitelistConfig()

        assert config.whitelist == []
        assert config.admin_emails == []
        assert config.full_users == []
        assert config.limited_users == []
        assert config.case_sensitive is False

    def test_normalize_emails_from_string(self):
        """Test email normalization from comma-separated string."""
        config = EmailWhitelistConfig(
            whitelist="test@example.com, admin@company.com,  @domain.com",
            admin_emails="admin1@example.com,admin2@example.com",
            full_users="full@example.com",
            limited_users="limited@example.com",
        )

        assert config.whitelist == ["test@example.com", "admin@company.com", "@domain.com"]
        assert config.admin_emails == ["admin1@example.com", "admin2@example.com"]
        assert config.full_users == ["full@example.com"]
        assert config.limited_users == ["limited@example.com"]

    def test_normalize_emails_from_list(self):
        """Test email normalization from list."""
        config = EmailWhitelistConfig(
            whitelist=["test@example.com", "admin@company.com"],
            admin_emails=["admin@example.com"],
        )

        assert config.whitelist == ["test@example.com", "admin@company.com"]
        assert config.admin_emails == ["admin@example.com"]

    def test_normalize_empty_values(self):
        """Test normalization with empty values."""
        config = EmailWhitelistConfig(
            whitelist="",
            admin_emails=None,
            full_users=[],
        )

        assert config.whitelist == []
        assert config.admin_emails == []
        assert config.full_users == []


@pytest.mark.unit
class TestEmailWhitelistValidatorInit:
    """Test EmailWhitelistValidator initialization."""

    def test_init_empty_lists(self):
        """Test initialization with empty lists."""
        validator = EmailWhitelistValidator([])

        assert validator.individual_emails == set()
        assert validator.domain_patterns == set()
        assert validator.admin_emails == []
        assert validator.full_users == []
        assert validator.limited_users == []
        assert validator.case_sensitive is False

    def test_init_mixed_emails_domains(self):
        """Test initialization with mixed emails and domains."""
        validator = EmailWhitelistValidator(
            whitelist=["test@example.com", "@company.com", "admin@test.org"],
            admin_emails=["admin@test.org"],
            full_users=["test@example.com"],
            limited_users=["@company.com"],
        )

        assert validator.individual_emails == {"test@example.com", "admin@test.org"}
        assert validator.domain_patterns == {"@company.com"}
        assert validator.admin_emails == ["admin@test.org"]
        assert validator.full_users == ["test@example.com"]
        assert validator.limited_users == ["@company.com"]

    def test_init_case_sensitive(self):
        """Test initialization with case-sensitive emails."""
        validator = EmailWhitelistValidator(
            whitelist=["Test@Example.com", "@Company.Com"],
            case_sensitive=True,
        )

        assert validator.individual_emails == {"Test@Example.com"}
        assert validator.domain_patterns == {"@Company.Com"}
        assert validator.case_sensitive is True

    def test_init_case_insensitive(self):
        """Test initialization with case-insensitive emails."""
        validator = EmailWhitelistValidator(
            whitelist=["Test@Example.com", "@Company.Com"],
            case_sensitive=False,
        )

        assert validator.individual_emails == {"test@example.com"}
        assert validator.domain_patterns == {"@company.com"}
        assert validator.case_sensitive is False

    @patch("src.auth_simple.whitelist.logger")
    def test_init_logging(self, mock_logger):
        """Test initialization logging."""
        EmailWhitelistValidator(
            whitelist=["test@example.com", "@company.com"],
            admin_emails=["admin@example.com"],
            full_users=["full@example.com"],
            limited_users=["limited@example.com"],
        )

        mock_logger.info.assert_called_once()
        # Check that the log call was made with the expected format string and arguments
        call_args, call_kwargs = mock_logger.info.call_args
        log_format = call_args[0]
        log_args = call_args[1:]

        assert "Initialized email whitelist" in log_format
        assert log_args == (1, 1, 1, 1, 1)  # individual, domain, admin, full, limited counts


@pytest.mark.unit
class TestEmailWhitelistValidatorNormalization:
    """Test email normalization methods."""

    def test_normalize_emails_case_sensitive(self):
        """Test _normalize_emails with case sensitivity."""
        validator = EmailWhitelistValidator([], case_sensitive=True)

        emails = ["Test@Example.com", "ADMIN@Company.COM"]
        normalized = validator._normalize_emails(emails)

        assert normalized == ["Test@Example.com", "ADMIN@Company.COM"]

    def test_normalize_emails_case_insensitive(self):
        """Test _normalize_emails with case insensitivity."""
        validator = EmailWhitelistValidator([], case_sensitive=False)

        emails = ["Test@Example.com", "ADMIN@Company.COM"]
        normalized = validator._normalize_emails(emails)

        assert normalized == ["test@example.com", "admin@company.com"]

    def test_normalize_emails_with_whitespace(self):
        """Test _normalize_emails with whitespace."""
        validator = EmailWhitelistValidator([])

        emails = ["  test@example.com  ", "", "   ", "admin@company.com"]
        normalized = validator._normalize_emails(emails)

        assert normalized == ["test@example.com", "admin@company.com"]

    def test_normalize_emails_empty_list(self):
        """Test _normalize_emails with empty list."""
        validator = EmailWhitelistValidator([])

        assert validator._normalize_emails([]) == []
        assert validator._normalize_emails(None) == []

    def test_normalize_email_single(self):
        """Test _normalize_email with single email."""
        validator_sensitive = EmailWhitelistValidator([], case_sensitive=True)
        validator_insensitive = EmailWhitelistValidator([], case_sensitive=False)

        email = "  Test@Example.COM  "

        assert validator_sensitive._normalize_email(email) == "Test@Example.COM"
        assert validator_insensitive._normalize_email(email) == "test@example.com"


@pytest.mark.unit
class TestEmailWhitelistValidatorAuthorization:
    """Test email authorization methods."""

    def test_is_authorized_individual_email(self):
        """Test authorization with individual emails."""
        validator = EmailWhitelistValidator(["test@example.com", "admin@company.com"])

        assert validator.is_authorized("test@example.com") is True
        assert validator.is_authorized("admin@company.com") is True
        assert validator.is_authorized("unauthorized@example.com") is False

    def test_is_authorized_domain_pattern(self):
        """Test authorization with domain patterns."""
        validator = EmailWhitelistValidator(["@company.com", "@trusted.org"])

        assert validator.is_authorized("anyone@company.com") is True
        assert validator.is_authorized("user@trusted.org") is True
        assert validator.is_authorized("user@untrusted.com") is False

    def test_is_authorized_mixed(self):
        """Test authorization with mixed emails and domains."""
        validator = EmailWhitelistValidator(
            [
                "specific@example.com",
                "@company.com",
                "admin@test.org",
            ],
        )

        assert validator.is_authorized("specific@example.com") is True
        assert validator.is_authorized("anyone@company.com") is True
        assert validator.is_authorized("admin@test.org") is True
        assert validator.is_authorized("other@example.com") is False

    def test_is_authorized_empty_email(self):
        """Test authorization with empty email."""
        validator = EmailWhitelistValidator(["test@example.com"])

        assert validator.is_authorized("") is False
        assert validator.is_authorized(None) is False

    def test_is_authorized_case_sensitivity(self):
        """Test authorization with case sensitivity."""
        validator_sensitive = EmailWhitelistValidator(
            ["Test@Example.com"],
            case_sensitive=True,
        )
        validator_insensitive = EmailWhitelistValidator(
            ["Test@Example.com"],
            case_sensitive=False,
        )

        # Case sensitive - exact match required
        assert validator_sensitive.is_authorized("Test@Example.com") is True
        assert validator_sensitive.is_authorized("test@example.com") is False

        # Case insensitive - any case works
        assert validator_insensitive.is_authorized("Test@Example.com") is True
        assert validator_insensitive.is_authorized("test@example.com") is True

    @patch("src.auth_simple.whitelist.logger")
    def test_is_authorized_logging(self, mock_logger):
        """Test authorization logging."""
        validator = EmailWhitelistValidator(["test@example.com", "@company.com"])

        # Authorized individual email
        validator.is_authorized("test@example.com")
        mock_logger.debug.assert_called_with("Email %s authorized via individual whitelist", "test@example.com")

        # Authorized domain
        validator.is_authorized("user@company.com")
        mock_logger.debug.assert_called_with(
            "Email %s authorized via domain pattern %s",
            "user@company.com",
            "@company.com",
        )

        # Unauthorized
        validator.is_authorized("unauthorized@example.com")
        mock_logger.debug.assert_called_with("Email %s not authorized", "unauthorized@example.com")


@pytest.mark.unit
class TestEmailWhitelistValidatorAdmin:
    """Test admin privilege methods."""

    def test_is_admin_valid(self):
        """Test is_admin with valid admin emails."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@company.com", "@company.com"],
            admin_emails=["admin@company.com", "super@company.com"],
        )

        assert validator.is_admin("admin@company.com") is True
        assert validator.is_admin("super@company.com") is True
        assert validator.is_admin("user@company.com") is False

    def test_is_admin_empty_email(self):
        """Test is_admin with empty email."""
        validator = EmailWhitelistValidator([], admin_emails=["admin@company.com"])

        assert validator.is_admin("") is False
        assert validator.is_admin(None) is False

    def test_is_admin_case_sensitivity(self):
        """Test is_admin with case sensitivity."""
        validator_sensitive = EmailWhitelistValidator(
            [],
            admin_emails=["Admin@Company.com"],
            case_sensitive=True,
        )
        validator_insensitive = EmailWhitelistValidator(
            [],
            admin_emails=["Admin@Company.com"],
            case_sensitive=False,
        )

        assert validator_sensitive.is_admin("Admin@Company.com") is True
        assert validator_sensitive.is_admin("admin@company.com") is False

        assert validator_insensitive.is_admin("Admin@Company.com") is True
        assert validator_insensitive.is_admin("admin@company.com") is True

    @patch("src.auth_simple.whitelist.logger")
    def test_is_admin_logging(self, mock_logger):
        """Test admin privilege logging."""
        validator = EmailWhitelistValidator([], admin_emails=["admin@company.com"])

        validator.is_admin("admin@company.com")
        mock_logger.debug.assert_called_with("Email %s has admin privileges", "admin@company.com")


@pytest.mark.unit
class TestEmailWhitelistValidatorRoles:
    """Test user role determination methods."""

    def test_get_user_role_unauthorized(self):
        """Test get_user_role for unauthorized user."""
        validator = EmailWhitelistValidator(["test@example.com"])

        assert validator.get_user_role("unauthorized@example.com") == "unauthorized"

    def test_get_user_role_admin(self):
        """Test get_user_role for admin user."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com"],
            admin_emails=["admin@example.com"],
        )

        assert validator.get_user_role("admin@example.com") == "admin"

    def test_get_user_role_user(self):
        """Test get_user_role for regular user."""
        validator = EmailWhitelistValidator(["user@example.com"])

        assert validator.get_user_role("user@example.com") == "user"


@pytest.mark.unit
class TestEmailWhitelistValidatorTiers:
    """Test user tier determination methods."""

    def test_get_user_tier_empty_email(self):
        """Test get_user_tier with empty email."""
        validator = EmailWhitelistValidator(["test@example.com"])

        with pytest.raises(ValueError, match="Email cannot be empty"):
            validator.get_user_tier("")

        with pytest.raises(ValueError, match="Email cannot be empty"):
            validator.get_user_tier(None)

    def test_get_user_tier_unauthorized(self):
        """Test get_user_tier for unauthorized email."""
        validator = EmailWhitelistValidator(["test@example.com"])

        with pytest.raises(ValueError, match="Email .* is not authorized"):
            validator.get_user_tier("unauthorized@example.com")

    def test_get_user_tier_exact_matches(self):
        """Test get_user_tier with exact email matches."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com", "full@example.com", "limited@example.com"],
            admin_emails=["admin@example.com"],
            full_users=["full@example.com"],
            limited_users=["limited@example.com"],
        )

        assert validator.get_user_tier("admin@example.com") == UserTier.ADMIN
        assert validator.get_user_tier("full@example.com") == UserTier.FULL
        assert validator.get_user_tier("limited@example.com") == UserTier.LIMITED

    def test_get_user_tier_domain_matches(self):
        """Test get_user_tier with domain pattern matches."""
        validator = EmailWhitelistValidator(
            whitelist=["@company.com"],
            admin_emails=["@admin.company.com"],
            full_users=["@full.company.com"],
            limited_users=["@limited.company.com"],
        )

        # These should fail because users aren't in whitelist
        with pytest.raises(ValueError):
            validator.get_user_tier("user@admin.company.com")

        # Add domains to whitelist
        validator = EmailWhitelistValidator(
            whitelist=["@admin.company.com", "@full.company.com", "@limited.company.com"],
            admin_emails=["@admin.company.com"],
            full_users=["@full.company.com"],
            limited_users=["@limited.company.com"],
        )

        assert validator.get_user_tier("user@admin.company.com") == UserTier.ADMIN
        assert validator.get_user_tier("user@full.company.com") == UserTier.FULL
        assert validator.get_user_tier("user@limited.company.com") == UserTier.LIMITED

    def test_get_user_tier_priority_order(self):
        """Test get_user_tier tier priority (admin > full > limited)."""
        # Email in multiple tiers - should return highest priority (admin)
        validator = EmailWhitelistValidator(
            whitelist=["test@example.com"],
            admin_emails=["test@example.com"],
            full_users=["test@example.com"],
            limited_users=["test@example.com"],
        )

        assert validator.get_user_tier("test@example.com") == UserTier.ADMIN

        # Email in full and limited - should return full
        validator = EmailWhitelistValidator(
            whitelist=["test@example.com"],
            full_users=["test@example.com"],
            limited_users=["test@example.com"],
        )

        assert validator.get_user_tier("test@example.com") == UserTier.FULL

    def test_get_user_tier_default_limited(self):
        """Test get_user_tier defaults to LIMITED for authorized users."""
        validator = EmailWhitelistValidator(["test@example.com"])

        assert validator.get_user_tier("test@example.com") == UserTier.LIMITED

    @patch("src.auth_simple.whitelist.logger")
    def test_get_user_tier_logging(self, mock_logger):
        """Test get_user_tier logging."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com", "user@example.com"],
            admin_emails=["admin@example.com"],
        )

        # Exact match logging
        validator.get_user_tier("admin@example.com")
        mock_logger.debug.assert_called_with("Email %s has %s tier (exact match)", "admin@example.com", "admin")

        # Default tier logging
        validator.get_user_tier("user@example.com")
        mock_logger.debug.assert_called_with("Email %s defaulted to limited tier", "user@example.com")


@pytest.mark.unit
class TestEmailWhitelistValidatorAccessMethods:
    """Test access permission methods."""

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


@pytest.mark.unit
class TestEmailWhitelistValidatorStats:
    """Test whitelist statistics methods."""

    def test_get_whitelist_stats(self):
        """Test get_whitelist_stats method."""
        validator = EmailWhitelistValidator(
            whitelist=["test@example.com", "admin@company.com", "@company.com", "@trusted.org"],
            admin_emails=["admin@company.com"],
            full_users=["test@example.com"],
            limited_users=["@company.com"],
        )

        stats = validator.get_whitelist_stats()

        assert stats["individual_emails"] == 2
        assert stats["domain_patterns"] == 2
        assert stats["admin_emails"] == 1
        assert stats["full_users"] == 1
        assert stats["limited_users"] == 1
        assert stats["total_entries"] == 4
        assert stats["case_sensitive"] is False
        assert set(stats["domains"]) == {"@company.com", "@trusted.org"}
        assert stats["tier_distribution"] == {
            "admin": 1,
            "full": 1,
            "limited": 1,
        }


@pytest.mark.unit
class TestEmailWhitelistValidatorValidation:
    """Test whitelist configuration validation."""

    def test_validate_whitelist_config_empty(self):
        """Test validation with empty whitelist."""
        validator = EmailWhitelistValidator([])
        warnings = validator.validate_whitelist_config()

        assert any("Whitelist is empty" in w for w in warnings)

    def test_validate_whitelist_config_admin_not_in_whitelist(self):
        """Test validation with admin not in whitelist."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            admin_emails=["admin@example.com"],
        )
        warnings = validator.validate_whitelist_config()

        assert any("Admin email admin@example.com is not in whitelist" in w for w in warnings)

    def test_validate_whitelist_config_full_user_not_in_whitelist(self):
        """Test validation with full user not in whitelist."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            full_users=["full@example.com"],
        )
        warnings = validator.validate_whitelist_config()

        assert any("Full user email full@example.com is not in whitelist" in w for w in warnings)

    def test_validate_whitelist_config_limited_user_not_in_whitelist(self):
        """Test validation with limited user not in whitelist."""
        validator = EmailWhitelistValidator(
            whitelist=["user@example.com"],
            limited_users=["limited@example.com"],
        )
        warnings = validator.validate_whitelist_config()

        assert any("Limited user email limited@example.com is not in whitelist" in w for w in warnings)

    def test_validate_whitelist_config_tier_conflicts(self):
        """Test validation with tier conflicts."""
        validator = EmailWhitelistValidator(
            whitelist=["conflict@example.com"],
            admin_emails=["conflict@example.com"],
            full_users=["conflict@example.com"],
            limited_users=["conflict@example.com"],
        )
        warnings = validator.validate_whitelist_config()

        assert any("conflict@example.com is assigned to multiple tiers" in w for w in warnings)

    def test_validate_whitelist_config_public_domains(self):
        """Test validation with public email domains."""
        validator = EmailWhitelistValidator(["@gmail.com", "@outlook.com"])
        warnings = validator.validate_whitelist_config()

        assert any("Public email domains" in w for w in warnings)

    def test_validate_whitelist_config_clean(self):
        """Test validation with clean configuration."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@company.com", "user@company.com", "@company.com"],
            admin_emails=["admin@company.com"],
            full_users=["user@company.com"],
        )
        warnings = validator.validate_whitelist_config()

        # Should have no warnings for clean config
        assert len(warnings) == 0


@pytest.mark.unit
class TestWhitelistManager:
    """Test WhitelistManager runtime operations."""

    def test_init(self):
        """Test WhitelistManager initialization."""
        validator = EmailWhitelistValidator(["test@example.com"])
        manager = WhitelistManager(validator)

        assert manager.validator is validator

    @patch("src.auth_simple.whitelist.logger")
    def test_add_email_individual(self, mock_logger):
        """Test adding individual email."""
        validator = EmailWhitelistValidator([])
        manager = WhitelistManager(validator)

        result = manager.add_email("test@example.com")

        assert result is True
        assert "test@example.com" in validator.individual_emails
        assert "test@example.com" not in validator.admin_emails
        mock_logger.info.assert_called_with("Added email %s to whitelist (admin: %s)", "test@example.com", False)

    @patch("src.auth_simple.whitelist.logger")
    def test_add_email_admin(self, mock_logger):
        """Test adding admin email."""
        validator = EmailWhitelistValidator([])
        manager = WhitelistManager(validator)

        result = manager.add_email("admin@example.com", is_admin=True)

        assert result is True
        assert "admin@example.com" in validator.individual_emails
        assert "admin@example.com" in validator.admin_emails
        mock_logger.info.assert_called_with("Added email %s to whitelist (admin: %s)", "admin@example.com", True)

    @patch("src.auth_simple.whitelist.logger")
    def test_add_email_domain(self, mock_logger):
        """Test adding domain pattern."""
        validator = EmailWhitelistValidator([])
        manager = WhitelistManager(validator)

        result = manager.add_email("@company.com")

        assert result is True
        assert "@company.com" in validator.domain_patterns
        mock_logger.info.assert_called_with("Added email %s to whitelist (admin: %s)", "@company.com", False)

    @patch("src.auth_simple.whitelist.logger")
    def test_add_email_error(self, mock_logger):
        """Test add_email error handling."""
        validator = EmailWhitelistValidator([])
        manager = WhitelistManager(validator)

        # Mock _normalize_email to raise exception
        with patch.object(validator, "_normalize_email", side_effect=Exception("Test error")):
            result = manager.add_email("test@example.com")

        assert result is False
        mock_logger.error.assert_called_with(
            "Failed to add email %s to whitelist: %s",
            "test@example.com",
            mock_logger.error.call_args[0][2],
        )

    @patch("src.auth_simple.whitelist.logger")
    def test_remove_email_individual(self, mock_logger):
        """Test removing individual email."""
        validator = EmailWhitelistValidator(["test@example.com"])
        manager = WhitelistManager(validator)

        result = manager.remove_email("test@example.com")

        assert result is True
        assert "test@example.com" not in validator.individual_emails
        mock_logger.info.assert_called_with("Removed email %s from whitelist", "test@example.com")

    @patch("src.auth_simple.whitelist.logger")
    def test_remove_email_domain(self, mock_logger):
        """Test removing domain pattern."""
        validator = EmailWhitelistValidator(["@company.com"])
        manager = WhitelistManager(validator)

        result = manager.remove_email("@company.com")

        assert result is True
        assert "@company.com" not in validator.domain_patterns
        mock_logger.info.assert_called_with("Removed email %s from whitelist", "@company.com")

    @patch("src.auth_simple.whitelist.logger")
    def test_remove_email_admin(self, mock_logger):
        """Test removing admin email."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com"],
            admin_emails=["admin@example.com"],
        )
        manager = WhitelistManager(validator)

        result = manager.remove_email("admin@example.com")

        assert result is True
        assert "admin@example.com" not in validator.individual_emails
        assert "admin@example.com" not in validator.admin_emails

    @patch("src.auth_simple.whitelist.logger")
    def test_remove_email_not_found(self, mock_logger):
        """Test removing email not in whitelist."""
        validator = EmailWhitelistValidator([])
        manager = WhitelistManager(validator)

        result = manager.remove_email("notfound@example.com")

        assert result is False
        mock_logger.warning.assert_called_with("Email %s not found in whitelist", "notfound@example.com")

    @patch("src.auth_simple.whitelist.logger")
    def test_remove_email_error(self, mock_logger):
        """Test remove_email error handling."""
        validator = EmailWhitelistValidator([])
        manager = WhitelistManager(validator)

        # Mock _normalize_email to raise exception
        with patch.object(validator, "_normalize_email", side_effect=Exception("Test error")):
            result = manager.remove_email("test@example.com")

        assert result is False
        mock_logger.error.assert_called_with(
            "Failed to remove email %s from whitelist: %s",
            "test@example.com",
            mock_logger.error.call_args[0][2],
        )

    def test_check_email(self):
        """Test check_email method."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@example.com"],
            admin_emails=["admin@example.com"],
        )
        manager = WhitelistManager(validator)

        result = manager.check_email("admin@example.com")

        expected = {
            "email": "admin@example.com",
            "is_authorized": True,
            "is_admin": True,
            "role": "admin",
            "normalized_email": "admin@example.com",
        }

        assert result == expected

    def test_check_email_unauthorized(self):
        """Test check_email with unauthorized email."""
        validator = EmailWhitelistValidator(["authorized@example.com"])
        manager = WhitelistManager(validator)

        result = manager.check_email("unauthorized@example.com")

        expected = {
            "email": "unauthorized@example.com",
            "is_authorized": False,
            "is_admin": False,
            "role": "unauthorized",
            "normalized_email": "unauthorized@example.com",
        }

        assert result == expected


@pytest.mark.unit
class TestCreateValidatorFromEnv:
    """Test create_validator_from_env function."""

    def test_create_validator_all_parameters(self):
        """Test creating validator with all parameters."""
        validator = create_validator_from_env(
            whitelist_str="test@example.com,@company.com",
            admin_emails_str="admin@example.com,super@company.com",
            full_users_str="full@example.com",
            limited_users_str="limited@example.com",
        )

        assert validator.individual_emails == {"test@example.com"}
        assert validator.domain_patterns == {"@company.com"}
        assert validator.admin_emails == ["admin@example.com", "super@company.com"]
        assert validator.full_users == ["full@example.com"]
        assert validator.limited_users == ["limited@example.com"]

    def test_create_validator_whitelist_only(self):
        """Test creating validator with whitelist only."""
        validator = create_validator_from_env("test@example.com,@company.com")

        assert validator.individual_emails == {"test@example.com"}
        assert validator.domain_patterns == {"@company.com"}
        assert validator.admin_emails == []
        assert validator.full_users == []
        assert validator.limited_users == []

    def test_create_validator_empty_strings(self):
        """Test creating validator with empty strings."""
        validator = create_validator_from_env("", "", "", "")

        assert validator.individual_emails == set()
        assert validator.domain_patterns == set()
        assert validator.admin_emails == []
        assert validator.full_users == []
        assert validator.limited_users == []

    def test_create_validator_whitespace_handling(self):
        """Test creating validator with whitespace in strings."""
        validator = create_validator_from_env(
            whitelist_str="  test@example.com  , , @company.com  ",
            admin_emails_str=" admin@example.com , ",
        )

        assert validator.individual_emails == {"test@example.com"}
        assert validator.domain_patterns == {"@company.com"}
        assert validator.admin_emails == ["admin@example.com"]

    def test_create_validator_none_strings(self):
        """Test creating validator with None strings (defaults to empty)."""
        # Since the function uses default parameters, None won't be passed
        # but empty strings will result in empty lists
        validator = create_validator_from_env(
            whitelist_str=None or "",
            admin_emails_str=None or "",
        )

        assert validator.individual_emails == set()
        assert validator.domain_patterns == set()
        assert validator.admin_emails == []
