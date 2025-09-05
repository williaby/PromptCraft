"""Unit tests for TierManagementInterface module."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.admin.user_tier_manager import UserTierManager
from src.ui.admin.tier_management_interface import TierManagementInterface


@pytest.fixture
def mock_tier_manager():
    """Create a mock tier manager."""
    manager = Mock(spec=UserTierManager)

    # Mock default responses
    manager.get_all_users.return_value = {
        "admin": [
            {"email": "admin@example.com", "can_access_premium": True, "is_admin": True, "assigned_at": "existing"},
        ],
        "full": [
            {"email": "full@example.com", "can_access_premium": True, "is_admin": False, "assigned_at": "existing"},
        ],
        "limited": [
            {"email": "limited@example.com", "can_access_premium": False, "is_admin": False, "assigned_at": "existing"},
        ],
        "unassigned": [
            {
                "email": "unassigned@example.com",
                "can_access_premium": False,
                "is_admin": False,
                "assigned_at": "unassigned",
            },
        ],
    }

    manager.get_tier_statistics.return_value = {
        "tier_distribution": {"admin": 1, "full": 1, "limited": 1},
        "total_authorized_users": 4,
        "individual_emails": 4,
        "domains": [],
    }

    manager.assign_user_tier.return_value = (True, "Successfully assigned user to tier")
    manager.remove_user_tier.return_value = (True, "Successfully removed user from tier")
    manager.bulk_assign_tier.return_value = {
        "total": 2,
        "successful": [{"email": "test@example.com", "message": "Success"}],
        "failed": [],
    }
    manager.search_users.return_value = [{"email": "admin@example.com", "current_tier": "admin"}]
    manager.validate_tier_configuration.return_value = []
    manager.export_tier_configuration.return_value = '{"test": "config"}'
    manager.persist_changes.return_value = (True, "Changes applied successfully")
    manager.reload_configuration.return_value = (True, "Configuration reloaded successfully")
    manager.generate_env_file_updates.return_value = "PROMPTCRAFT_ADMIN_EMAILS=admin@example.com"
    manager.get_changes_log.return_value = [
        {
            "timestamp": "2023-01-01T10:00:00",
            "action": "assign_tier",
            "email": "test@example.com",
            "tier": "full",
            "admin": "admin@example.com",
        },
    ]

    return manager


@pytest.fixture
def interface(mock_tier_manager):
    """Create a TierManagementInterface instance with mocked dependencies."""
    with patch("src.ui.admin.tier_management_interface.UserTierManager", return_value=mock_tier_manager):
        interface = TierManagementInterface()
        interface.tier_manager = mock_tier_manager
        return interface


class TestTierManagementInterface:
    """Test cases for TierManagementInterface class."""

    def test_init(self):
        """Test interface initialization."""
        with patch("src.ui.admin.tier_management_interface.UserTierManager") as mock_utm:
            interface = TierManagementInterface()
            mock_utm.assert_called_once()
            assert interface.tier_manager is not None

    def test_create_admin_interface(self, interface):
        """Test admin interface creation."""
        with patch("gradio.Tab") as mock_tab:
            mock_tab.return_value.__enter__ = Mock(return_value=mock_tab.return_value)
            mock_tab.return_value.__exit__ = Mock(return_value=None)

            with (
                patch("gradio.HTML"),
                patch("gradio.Row"),
                patch("gradio.Column"),
                patch("gradio.Group"),
                patch("gradio.Textbox"),
                patch("gradio.Dropdown"),
                patch("gradio.Button"),
                patch("gradio.Dataframe"),
            ):

                admin_tab = interface.create_admin_interface()
                # Tab is called multiple times for main tab and sub-tabs
                assert mock_tab.call_count >= 1
                assert admin_tab is not None

    def test_assign_tier_success(self, interface, mock_tier_manager):
        """Test successful tier assignment."""
        result = interface._assign_tier("test@example.com", "full")

        assert len(result) == 6  # result_html, stats_html, 4 tables
        assert "✅ Success" in result[0]  # result_html
        mock_tier_manager.assign_user_tier.assert_called_once_with("test@example.com", "full", "admin@example.com")

    def test_assign_tier_failure(self, interface, mock_tier_manager):
        """Test failed tier assignment."""
        mock_tier_manager.assign_user_tier.return_value = (False, "Assignment failed")

        result = interface._assign_tier("invalid@example.com", "full")

        assert len(result) == 6
        assert "❌ Error" in result[0]
        assert "Assignment failed" in result[0]

    def test_assign_tier_exception(self, interface, mock_tier_manager):
        """Test tier assignment with exception."""
        mock_tier_manager.assign_user_tier.side_effect = Exception("System error")

        result = interface._assign_tier("test@example.com", "full")

        assert len(result) == 6
        assert "❌ System Error" in result[0]
        assert "System error" in result[0]

    def test_remove_tier_success(self, interface, mock_tier_manager):
        """Test successful tier removal."""
        result = interface._remove_tier("test@example.com")

        assert len(result) == 6
        assert "✅ Success" in result[0]
        mock_tier_manager.remove_user_tier.assert_called_once_with("test@example.com", "admin@example.com")

    def test_remove_tier_failure(self, interface, mock_tier_manager):
        """Test failed tier removal."""
        mock_tier_manager.remove_user_tier.return_value = (False, "Removal failed")

        result = interface._remove_tier("invalid@example.com")

        assert len(result) == 6
        assert "❌ Error" in result[0]
        assert "Removal failed" in result[0]

    def test_remove_tier_exception(self, interface, mock_tier_manager):
        """Test tier removal with exception."""
        mock_tier_manager.remove_user_tier.side_effect = Exception("System error")

        result = interface._remove_tier("test@example.com")

        assert len(result) == 6
        assert "System error" in result[0]

    def test_bulk_assign_success(self, interface, mock_tier_manager):
        """Test successful bulk assignment."""
        emails_text = "user1@example.com\nuser2@example.com"

        result = interface._bulk_assign(emails_text, "full")

        assert len(result) == 6
        assert "Bulk Assignment Results" in result[0]
        mock_tier_manager.bulk_assign_tier.assert_called_once_with(
            ["user1@example.com", "user2@example.com"],
            "full",
            "admin@example.com",
        )

    def test_bulk_assign_empty_input(self, interface, mock_tier_manager):
        """Test bulk assignment with empty input."""
        result = interface._bulk_assign("", "full")

        assert len(result) == 6
        assert "Please enter email addresses" in result[0]
        mock_tier_manager.bulk_assign_tier.assert_not_called()

    def test_bulk_assign_with_failures(self, interface, mock_tier_manager):
        """Test bulk assignment with some failures."""
        mock_tier_manager.bulk_assign_tier.return_value = {
            "total": 2,
            "successful": [{"email": "good@example.com", "message": "Success"}],
            "failed": [{"email": "bad@example.com", "error": "Invalid email"}],
        }

        result = interface._bulk_assign("good@example.com\nbad@example.com", "full")

        assert len(result) == 6
        assert "Failed:" in result[0]
        assert "bad@example.com" in result[0]

    def test_bulk_assign_exception(self, interface, mock_tier_manager):
        """Test bulk assignment with exception."""
        mock_tier_manager.bulk_assign_tier.side_effect = Exception("System error")

        result = interface._bulk_assign("test@example.com", "full")

        assert len(result) == 6
        assert "System error" in result[0]

    def test_search_users_success(self, interface, mock_tier_manager):
        """Test successful user search."""
        result = interface._search_users("admin")

        assert len(result) == 5  # stats_html + 4 tables
        assert "Search Results" in result[0]
        assert "Found 1 users" in result[0]
        mock_tier_manager.search_users.assert_called_once_with("admin")

    def test_search_users_empty_query(self, interface, mock_tier_manager):
        """Test search with empty query returns refresh data."""
        with patch.object(interface, "_refresh_all_data") as mock_refresh:
            mock_refresh.return_value = ("stats", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

            interface._search_users("")

            mock_refresh.assert_called_once()
            mock_tier_manager.search_users.assert_not_called()

    def test_search_users_exception(self, interface, mock_tier_manager):
        """Test search users with exception."""
        mock_tier_manager.search_users.side_effect = Exception("Search error")

        result = interface._search_users("admin")

        assert len(result) == 5
        assert "Search error" in result[0]

    def test_refresh_all_data_success(self, interface):
        """Test successful data refresh."""
        result = interface._refresh_all_data()

        assert len(result) == 5
        assert isinstance(result[0], str)  # stats_html
        assert all(isinstance(table, pd.DataFrame) for table in result[1:])

    def test_refresh_all_data_exception(self, interface, mock_tier_manager):
        """Test data refresh with exception."""
        mock_tier_manager.get_tier_statistics.side_effect = Exception("Stats error")

        result = interface._refresh_all_data()

        assert len(result) == 5
        assert "Error loading statistics: Stats error" in result[0]

    def test_validate_configuration_success(self, interface, mock_tier_manager):
        """Test successful configuration validation."""
        mock_tier_manager.validate_tier_configuration.return_value = []

        result = interface._validate_configuration()

        assert "✅ Configuration Valid" in result
        assert "No configuration issues detected" in result

    def test_validate_configuration_with_warnings(self, interface, mock_tier_manager):
        """Test configuration validation with warnings."""
        mock_tier_manager.validate_tier_configuration.return_value = ["Warning 1", "Warning 2"]

        result = interface._validate_configuration()

        assert "⚠️ Configuration Warnings" in result
        assert "Warning 1" in result
        assert "Warning 2" in result

    def test_validate_configuration_exception(self, interface, mock_tier_manager):
        """Test configuration validation with exception."""
        mock_tier_manager.validate_tier_configuration.side_effect = Exception("Validation error")

        result = interface._validate_configuration()

        assert "❌ Validation Error" in result
        assert "Validation error" in result

    def test_export_configuration_success(self, interface, mock_tier_manager):
        """Test successful configuration export."""
        result = interface._export_configuration()

        assert "✅ Configuration Exported" in result
        assert "View Configuration JSON" in result
        assert '{"test": "config"}' in result

    def test_export_configuration_exception(self, interface, mock_tier_manager):
        """Test configuration export with exception."""
        mock_tier_manager.export_tier_configuration.side_effect = Exception("Export error")

        result = interface._export_configuration()

        assert "❌ Export Error" in result
        assert "Export error" in result

    def test_persist_changes_success(self, interface, mock_tier_manager):
        """Test successful changes persistence."""
        result = interface._persist_changes()

        assert "✅ Changes Applied" in result
        assert "Changes applied successfully" in result

    def test_persist_changes_failure(self, interface, mock_tier_manager):
        """Test failed changes persistence."""
        mock_tier_manager.persist_changes.return_value = (False, "Persistence failed")

        result = interface._persist_changes()

        assert "❌ Persistence Error" in result
        assert "Persistence failed" in result

    def test_persist_changes_exception(self, interface, mock_tier_manager):
        """Test changes persistence with exception."""
        mock_tier_manager.persist_changes.side_effect = Exception("System error")

        result = interface._persist_changes()

        assert "❌ System Error" in result
        assert "System error" in result

    def test_reload_configuration_success(self, interface, mock_tier_manager):
        """Test successful configuration reload."""
        result = interface._reload_configuration()

        assert len(result) == 6
        assert "✅ Configuration Reloaded" in result[0]
        assert "Configuration reloaded successfully" in result[0]

    def test_reload_configuration_failure(self, interface, mock_tier_manager):
        """Test failed configuration reload."""
        mock_tier_manager.reload_configuration.return_value = (False, "Reload failed")

        result = interface._reload_configuration()

        assert len(result) == 6
        assert "❌ Reload Error" in result[0]
        assert "Reload failed" in result[0]

    def test_reload_configuration_exception(self, interface, mock_tier_manager):
        """Test configuration reload with exception."""
        mock_tier_manager.reload_configuration.side_effect = Exception("System error")

        result = interface._reload_configuration()

        assert len(result) == 6
        assert "❌ System Error" in result[0]
        assert "System error" in result[0]

    def test_generate_env_updates_success(self, interface, mock_tier_manager):
        """Test successful environment updates generation."""
        result = interface._generate_env_updates()

        assert "✅ Environment Updates Generated" in result
        assert "View Environment File Updates" in result
        assert "PROMPTCRAFT_ADMIN_EMAILS=admin@example.com" in result

    def test_generate_env_updates_exception(self, interface, mock_tier_manager):
        """Test environment updates generation with exception."""
        mock_tier_manager.generate_env_file_updates.side_effect = Exception("Generation error")

        result = interface._generate_env_updates()

        assert "❌ Generation Error" in result
        assert "Generation error" in result

    def test_refresh_changes_log_success(self, interface, mock_tier_manager):
        """Test successful changes log refresh."""
        result = interface._refresh_changes_log()

        assert "[2023-01-01 10:00:00]" in result
        assert "ASSIGN_TIER" in result
        assert "test@example.com" in result

    def test_refresh_changes_log_empty(self, interface, mock_tier_manager):
        """Test changes log refresh with no changes."""
        mock_tier_manager.get_changes_log.return_value = []

        result = interface._refresh_changes_log()

        assert result == "No recent changes recorded."

    def test_refresh_changes_log_exception(self, interface, mock_tier_manager):
        """Test changes log refresh with exception."""
        mock_tier_manager.get_changes_log.side_effect = Exception("Log error")

        result = interface._refresh_changes_log()

        assert "Error loading changes log" in result
        assert "Log error" in result

    def test_generate_stats_html_success(self, interface, mock_tier_manager):
        """Test successful stats HTML generation."""
        result = interface._generate_stats_html()

        assert "📊 User Statistics" in result
        assert "👑 Admin Users:" in result
        assert "⭐ Full Users:" in result
        assert "🔒 Limited Users:" in result

    def test_generate_stats_html_exception(self, interface, mock_tier_manager):
        """Test stats HTML generation with exception."""
        mock_tier_manager.get_tier_statistics.side_effect = Exception("Stats error")

        result = interface._generate_stats_html()

        assert "Error loading statistics" in result
        assert "Stats error" in result

    def test_generate_user_tables_success(self, interface, mock_tier_manager):
        """Test successful user tables generation."""
        result = interface._generate_user_tables()

        assert len(result) == 4  # admin, full, limited, unassigned tables
        assert all(isinstance(table, pd.DataFrame) for table in result)

    def test_generate_user_tables_exception(self, interface, mock_tier_manager):
        """Test user tables generation with exception."""
        mock_tier_manager.get_all_users.side_effect = Exception("Tables error")

        result = interface._generate_user_tables()

        assert len(result) == 4
        assert all(isinstance(table, pd.DataFrame) for table in result)
        assert all(table.empty for table in result)

    def test_generate_tables_from_data(self, interface):
        """Test table generation from user data."""
        users_data = {
            "admin": [{"email": "admin@example.com"}],
            "full": [{"email": "full@example.com"}],
            "limited": [{"email": "limited@example.com"}],
            "unassigned": [{"email": "unassigned@example.com"}],
        }

        result = interface._generate_tables_from_data(users_data)

        assert len(result) == 4
        admin_df, full_df, limited_df, unassigned_df = result

        assert len(admin_df) == 1
        assert admin_df.iloc[0]["Email"] == "admin@example.com"
        assert "Full Access + Admin" in admin_df.iloc[0]["Access Level"]

        assert len(full_df) == 1
        assert full_df.iloc[0]["Email"] == "full@example.com"
        assert "All Models" in full_df.iloc[0]["Access Level"]

        assert len(limited_df) == 1
        assert limited_df.iloc[0]["Email"] == "limited@example.com"
        assert "Free Models Only" in limited_df.iloc[0]["Access Level"]

        assert len(unassigned_df) == 1
        assert unassigned_df.iloc[0]["Email"] == "unassigned@example.com"
        assert "No Tier Assigned" in unassigned_df.iloc[0]["Status"]

    def test_get_table_outputs(self, interface):
        """Test getting table outputs helper method."""
        components = {
            "admin_users_df": "admin_table",
            "full_users_df": "full_table",
            "limited_users_df": "limited_table",
            "unassigned_df": "unassigned_table",
        }

        result = interface._get_table_outputs(components)

        assert len(result) == 4
        assert result == ["admin_table", "full_table", "limited_table", "unassigned_table"]
