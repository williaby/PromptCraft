"""Unit tests for UserTierManager module."""

import json
from unittest.mock import Mock, patch

import pytest

from src.admin.user_tier_manager import UserTierManager, UserTierManagerError
from src.auth_simple.config import AuthConfig, ConfigManager
from src.auth_simple.whitelist import EmailWhitelistValidator, UserTier


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return AuthConfig(
        admin_emails=["admin@example.com"],
        full_users=["full@example.com"],
        limited_users=["limited@example.com"],
        email_whitelist=["admin@example.com", "full@example.com", "limited@example.com", "unassigned@example.com"],
    )


@pytest.fixture
def mock_config_manager(mock_config):
    """Create a mock config manager."""
    manager = Mock(spec=ConfigManager)
    manager.config = mock_config
    manager.create_whitelist_validator.return_value = Mock(spec=EmailWhitelistValidator)
    return manager


@pytest.fixture
def tier_manager(mock_config_manager):
    """Create a UserTierManager instance with mocked dependencies."""
    with patch("src.admin.user_tier_manager.get_config_manager", return_value=mock_config_manager):
        manager = UserTierManager()
        # Mock the validator
        manager.validator = Mock(spec=EmailWhitelistValidator)
        manager.validator.is_authorized.return_value = True
        manager.validator.get_user_tier.return_value = UserTier.FULL
        manager.validator.validate_whitelist_config.return_value = []
        manager.validator.get_whitelist_stats.return_value = {
            "individual_emails": 4,
            "domains": [],
            "admin_emails": 1,
            "full_users": 1,
            "limited_users": 1,
        }
        return manager


class TestUserTierManager:
    """Test cases for UserTierManager class."""

    def test_init_with_config_manager(self, mock_config_manager):
        """Test initialization with provided config manager."""
        manager = UserTierManager(mock_config_manager)
        assert manager.config_manager == mock_config_manager
        assert manager.changes_log == []

    def test_init_without_config_manager(self):
        """Test initialization without provided config manager."""
        with patch("src.admin.user_tier_manager.get_config_manager") as mock_get_config:
            mock_config_manager = Mock(spec=ConfigManager)
            mock_get_config.return_value = mock_config_manager

            manager = UserTierManager()
            assert manager.config_manager == mock_config_manager
            mock_get_config.assert_called_once()

    def test_validate_email_valid_emails(self, tier_manager):
        """Test email validation with valid email addresses."""
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "user+tag@example.org"]

        for email in valid_emails:
            assert tier_manager._validate_email(email) is True

    def test_validate_email_valid_domain_patterns(self, tier_manager):
        """Test email validation with valid domain patterns."""
        valid_domains = ["@example.com", "@subdomain.example.org", "@test-domain.co.uk"]

        for domain in valid_domains:
            assert tier_manager._validate_email(domain) is True

    def test_validate_email_invalid_emails(self, tier_manager):
        """Test email validation with invalid email addresses."""
        invalid_emails = [
            "",
            None,
            "invalid",
            "@",
            "user@",
            "user@domain.",
            123,  # Non-string type
        ]

        for email in invalid_emails:
            assert tier_manager._validate_email(email) is False

        # Test that domain patterns ARE valid (they start with @)
        assert tier_manager._validate_email("@domain") is True
        assert tier_manager._validate_email("@example.com") is True

    def test_get_all_users(self, tier_manager):
        """Test getting all users organized by tier."""
        result = tier_manager.get_all_users()

        assert "admin" in result
        assert "full" in result
        assert "limited" in result
        assert "unassigned" in result

        # Check admin user
        admin_users = result["admin"]
        assert len(admin_users) == 1
        assert admin_users[0]["email"] == "admin@example.com"
        assert admin_users[0]["is_admin"] is True
        assert admin_users[0]["can_access_premium"] is True

    def test_get_all_users_with_unassigned(self, tier_manager):
        """Test getting all users includes unassigned users."""
        result = tier_manager.get_all_users()

        unassigned_users = result["unassigned"]
        assert len(unassigned_users) == 1
        assert unassigned_users[0]["email"] == "unassigned@example.com"
        assert unassigned_users[0]["assigned_at"] == "unassigned"

    def test_assign_user_tier_success(self, tier_manager):
        """Test successful user tier assignment."""
        success, message = tier_manager.assign_user_tier("test@example.com", "full", "admin@example.com")

        assert success is True
        assert "Successfully assigned" in message
        assert len(tier_manager.changes_log) == 1

        # Check change log
        change = tier_manager.changes_log[0]
        assert change["action"] == "assign_tier"
        assert change["email"] == "test@example.com"
        assert change["tier"] == "full"
        assert change["admin"] == "admin@example.com"

    def test_assign_user_tier_invalid_email(self, tier_manager):
        """Test tier assignment with invalid email."""
        success, message = tier_manager.assign_user_tier("invalid-email", "full", "admin@example.com")

        assert success is False
        assert "Invalid email format" in message

    def test_assign_user_tier_invalid_tier(self, tier_manager):
        """Test tier assignment with invalid tier."""
        success, message = tier_manager.assign_user_tier("test@example.com", "invalid", "admin@example.com")

        assert success is False
        assert "Invalid tier" in message

    def test_assign_user_tier_not_authorized(self, tier_manager):
        """Test tier assignment for unauthorized email."""
        tier_manager.validator.is_authorized.return_value = False

        success, message = tier_manager.assign_user_tier("unauthorized@example.com", "full", "admin@example.com")

        assert success is False
        assert "not in the whitelist" in message

    def test_remove_user_tier_success(self, tier_manager):
        """Test successful user tier removal."""
        # First add user to a tier
        tier_manager.config_manager.config.full_users.append("test@example.com")

        success, message = tier_manager.remove_user_tier("test@example.com", "admin@example.com")

        assert success is True
        assert len(tier_manager.changes_log) == 1

        # Check change log
        change = tier_manager.changes_log[0]
        assert change["action"] == "remove_tier"
        assert change["email"] == "test@example.com"
        assert change["admin"] == "admin@example.com"

    def test_remove_from_all_tiers(self, tier_manager):
        """Test removing user from all tiers."""
        # Add user to multiple tiers
        tier_manager.config_manager.config.admin_emails.append("test@example.com")
        tier_manager.config_manager.config.full_users.append("test@example.com")

        success, message = tier_manager._remove_from_all_tiers("test@example.com")

        assert success is True
        assert "admin, full" in message
        assert "test@example.com" not in tier_manager.config_manager.config.admin_emails
        assert "test@example.com" not in tier_manager.config_manager.config.full_users

    def test_remove_from_all_tiers_not_assigned(self, tier_manager):
        """Test removing user not assigned to any tier."""
        success, message = tier_manager._remove_from_all_tiers("nonexistent@example.com")

        assert success is True
        assert "was not assigned to any tier" in message

    def test_get_user_tier_info_success(self, tier_manager):
        """Test getting user tier information."""
        result = tier_manager.get_user_tier_info("test@example.com")

        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["tier"] == "full"
        assert result["is_authorized"] is True

    def test_get_user_tier_info_unauthorized(self, tier_manager):
        """Test getting tier info for unauthorized user."""
        tier_manager.validator.is_authorized.return_value = False

        result = tier_manager.get_user_tier_info("unauthorized@example.com")
        assert result is None

    def test_validate_tier_configuration(self, tier_manager):
        """Test tier configuration validation."""
        warnings = tier_manager.validate_tier_configuration()
        assert isinstance(warnings, list)

    def test_get_tier_statistics(self, tier_manager):
        """Test getting tier statistics."""
        stats = tier_manager.get_tier_statistics()

        assert "individual_emails" in stats
        assert "total_authorized_users" in stats
        assert "changes_made" in stats
        assert "last_modified" in stats

    def test_bulk_assign_tier_success(self, tier_manager):
        """Test bulk tier assignment."""
        emails = ["user1@example.com", "user2@example.com"]

        result = tier_manager.bulk_assign_tier(emails, "full", "admin@example.com")

        assert result["total"] == 2
        assert len(result["successful"]) == 2
        assert len(result["failed"]) == 0

    def test_bulk_assign_tier_mixed_results(self, tier_manager):
        """Test bulk tier assignment with mixed results."""
        emails = ["valid@example.com", "invalid-email"]

        result = tier_manager.bulk_assign_tier(emails, "full", "admin@example.com")

        assert result["total"] == 2
        assert len(result["successful"]) == 1
        assert len(result["failed"]) == 1

    def test_export_tier_configuration(self, tier_manager):
        """Test exporting tier configuration."""
        export_json = tier_manager.export_tier_configuration()

        config_data = json.loads(export_json)
        assert "exported_at" in config_data
        assert "admin_emails" in config_data
        assert "full_users" in config_data
        assert "limited_users" in config_data
        assert "email_whitelist" in config_data
        assert "statistics" in config_data
        assert "changes_log" in config_data

    def test_search_users(self, tier_manager):
        """Test searching users by email pattern."""
        results = tier_manager.search_users("admin")

        assert len(results) == 1
        assert results[0]["email"] == "admin@example.com"
        assert results[0]["current_tier"] == "admin"

    def test_search_users_case_insensitive(self, tier_manager):
        """Test case-insensitive user search."""
        results = tier_manager.search_users("ADMIN")

        assert len(results) == 1
        assert results[0]["email"] == "admin@example.com"

    def test_get_changes_log(self, tier_manager):
        """Test getting changes log."""
        # Add some changes
        tier_manager.changes_log = [
            {"action": "test1", "timestamp": "2023-01-01"},
            {"action": "test2", "timestamp": "2023-01-02"},
        ]

        recent_changes = tier_manager.get_changes_log(limit=1)
        assert len(recent_changes) == 1
        assert recent_changes[0]["action"] == "test2"

    def test_persist_changes(self, tier_manager):
        """Test persisting configuration changes."""
        success, message = tier_manager.persist_changes()

        assert success is True
        assert "Configuration changes applied" in message
        assert len(tier_manager.changes_log) == 1

        # Check change log entry
        change = tier_manager.changes_log[0]
        assert change["action"] == "persist_config"

    def test_reload_configuration(self, tier_manager):
        """Test reloading configuration."""
        with patch("src.admin.user_tier_manager.ConfigLoader") as mock_loader:
            # Create a real AuthConfig object instead of a Mock
            from src.auth_simple.config import AuthConfig
            mock_config = AuthConfig(
                email_whitelist=["test@example.com"],
                admin_emails=["admin@example.com"],
                enabled=True,
            )
            mock_loader.load_from_env.return_value = mock_config

            success, message = tier_manager.reload_configuration()

            assert success is True
            assert "Configuration successfully reloaded" in message
            # Compare specific attributes instead of the whole object
            assert tier_manager.config_manager.config.email_whitelist == mock_config.email_whitelist
            assert tier_manager.config_manager.config.admin_emails == mock_config.admin_emails
            assert tier_manager.changes_log == []

    def test_generate_env_file_updates(self, tier_manager):
        """Test generating environment file updates."""
        env_content = tier_manager.generate_env_file_updates()

        assert "PROMPTCRAFT_ADMIN_EMAILS" in env_content
        assert "PROMPTCRAFT_FULL_USERS" in env_content
        assert "PROMPTCRAFT_LIMITED_USERS" in env_content
        assert "admin@example.com" in env_content
        assert "full@example.com" in env_content
        assert "limited@example.com" in env_content

    def test_error_handling_in_get_all_users(self, tier_manager):
        """Test error handling in get_all_users method."""
        tier_manager.config_manager.config = None

        with pytest.raises(UserTierManagerError):
            tier_manager.get_all_users()

    def test_error_handling_in_assign_user_tier(self, tier_manager):
        """Test error handling in assign_user_tier method."""
        # Mock an exception during tier assignment
        tier_manager._remove_from_all_tiers = Mock(side_effect=Exception("Test error"))

        success, message = tier_manager.assign_user_tier("test@example.com", "full", "admin@example.com")

        assert success is False
        assert "Failed to assign tier" in message

    def test_error_handling_in_get_user_tier_info(self, tier_manager):
        """Test error handling in get_user_tier_info method."""
        tier_manager.validator.is_authorized.side_effect = Exception("Test error")

        result = tier_manager.get_user_tier_info("test@example.com")
        assert result is None

    def test_error_handling_in_validate_tier_configuration(self, tier_manager):
        """Test error handling in validate_tier_configuration method."""
        tier_manager.validator.validate_whitelist_config.side_effect = Exception("Test error")

        warnings = tier_manager.validate_tier_configuration()
        assert len(warnings) == 1
        assert "Configuration validation failed" in warnings[0]

    def test_error_handling_in_get_tier_statistics(self, tier_manager):
        """Test error handling in get_tier_statistics method."""
        tier_manager.validator.get_whitelist_stats.side_effect = Exception("Test error")

        stats = tier_manager.get_tier_statistics()
        assert "error" in stats
        assert "Failed to get statistics" in stats["error"]

    def test_error_handling_in_search_users(self, tier_manager):
        """Test error handling in search_users method."""
        tier_manager.get_all_users = Mock(side_effect=Exception("Test error"))

        results = tier_manager.search_users("test")
        assert results == []

    def test_error_handling_in_export_tier_configuration(self, tier_manager):
        """Test error handling in export_tier_configuration method."""
        tier_manager.get_tier_statistics = Mock(side_effect=Exception("Test error"))

        export_json = tier_manager.export_tier_configuration()
        config_data = json.loads(export_json)
        assert "error" in config_data
        assert "Export failed" in config_data["error"]

    def test_error_handling_in_persist_changes(self, tier_manager):
        """Test error handling in persist_changes method."""
        tier_manager.config_manager._validate_config = Mock(side_effect=Exception("Test error"))

        success, message = tier_manager.persist_changes()
        assert success is False
        assert "Failed to persist changes" in message

    def test_error_handling_in_reload_configuration(self, tier_manager):
        """Test error handling in reload_configuration method."""
        with patch("src.admin.user_tier_manager.ConfigLoader") as mock_loader:
            mock_loader.load_from_env.side_effect = Exception("Test error")

            success, message = tier_manager.reload_configuration()
            assert success is False
            assert "Failed to reload configuration" in message

    def test_error_handling_in_generate_env_file_updates(self, tier_manager):
        """Test error handling in generate_env_file_updates method."""
        tier_manager.config_manager.config = None

        env_content = tier_manager.generate_env_file_updates()
        assert "Error generating environment updates" in env_content
