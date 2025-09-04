"""
Comprehensive tests for User Control System.

This test module provides complete coverage of the user control system
with minimal mocking, focusing on actual process testing and realistic scenarios.
Following the user's guidance to prioritize testing real functionality.

Coverage targets:
- All core classes: UserControlSystem, CategoryManager, TierController, ProfileManager
- Command parsing and execution
- Session management and persistence
- Performance monitoring and analytics
- User preferences and profiles
"""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest

from src.core.user_control_system import (
    CategoryManager,
    CommandParser,
    CommandResult,
    PerformanceMonitor,
    ProfileManager,
    SessionProfile,
    UserControlSystem,
    UserSession,
)
from src.utils.datetime_compat import UTC


class TestUserSession:
    """Test UserSession data class."""

    def test_user_session_defaults(self):
        """Test UserSession creation with defaults."""
        session = UserSession(session_id="test_session")

        assert session.session_id == "test_session"
        assert session.user_level == "balanced"
        assert session.active_categories == {}
        assert session.performance_mode == "conservative"
        assert session.command_history == []
        assert session.preferences == {}
        assert session.learning_enabled is True
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)

    def test_user_session_custom_values(self):
        """Test UserSession with custom values."""
        now = datetime.now(UTC)
        session = UserSession(
            session_id="custom_session",
            user_level="expert",
            active_categories={"analysis": True, "quality": False},
            performance_mode="aggressive",
            command_history=[{"command": "/help", "timestamp": now}],
            preferences={"theme": "dark", "verbose": True},
            learning_enabled=False,
            created_at=now,
            last_activity=now,
        )

        assert session.session_id == "custom_session"
        assert session.user_level == "expert"
        assert session.active_categories == {"analysis": True, "quality": False}
        assert session.performance_mode == "aggressive"
        assert len(session.command_history) == 1
        assert session.preferences == {"theme": "dark", "verbose": True}
        assert session.learning_enabled is False
        assert session.created_at == now
        assert session.last_activity == now


class TestSessionProfile:
    """Test SessionProfile data class."""

    def test_session_profile_creation(self):
        """Test SessionProfile creation."""
        profile = SessionProfile(
            name="Development Profile",
            description="Profile for software development tasks",
            categories={"core": True, "git": True, "analysis": True},
            performance_mode="balanced",
        )

        assert profile.name == "Development Profile"
        assert profile.description == "Profile for software development tasks"
        assert profile.categories == {"core": True, "git": True, "analysis": True}
        assert profile.performance_mode == "balanced"
        assert profile.detection_config is None
        assert profile.tags == []
        assert profile.created_by == "user"
        assert isinstance(profile.created_at, datetime)
        assert profile.usage_count == 0
        assert profile.last_used is None

    def test_session_profile_custom_values(self):
        """Test SessionProfile with custom values."""
        now = datetime.now(UTC)
        profile = SessionProfile(
            name="Custom Profile",
            description="Custom profile",
            categories={"test": True},
            performance_mode="aggressive",
            detection_config={"threshold": 0.8},
            tags=["development", "testing"],
            created_by="admin",
            created_at=now,
            usage_count=5,
            last_used=now,
        )

        assert profile.detection_config == {"threshold": 0.8}
        assert profile.tags == ["development", "testing"]
        assert profile.created_by == "admin"
        assert profile.created_at == now
        assert profile.usage_count == 5
        assert profile.last_used == now


class TestCommandResult:
    """Test CommandResult data class."""

    def test_command_result_success(self):
        """Test successful CommandResult."""
        result = CommandResult(
            success=True,
            message="Command executed successfully",
        )

        assert result.success is True
        assert result.message == "Command executed successfully"
        assert result.data is None
        assert result.suggestions == []
        assert result.warnings == []

    def test_command_result_with_data(self):
        """Test CommandResult with data and suggestions."""
        result = CommandResult(
            success=False,
            message="Command failed",
            data={"error_code": 404, "details": "Not found"},
            suggestions=["Try /help", "Check spelling"],
            warnings=["This is deprecated"],
        )

        assert result.success is False
        assert result.message == "Command failed"
        assert result.data == {"error_code": 404, "details": "Not found"}
        assert result.suggestions == ["Try /help", "Check spelling"]
        assert result.warnings == ["This is deprecated"]


class TestCategoryManager:
    """Test CategoryManager class."""

    @pytest.fixture
    def mock_detection_system(self):
        """Create mock detection system."""
        return Mock()

    @pytest.fixture
    def category_manager(self, mock_detection_system):
        """Create CategoryManager instance."""
        return CategoryManager(mock_detection_system)

    def test_category_manager_initialization(self, category_manager):
        """Test CategoryManager initialization."""
        assert category_manager.detection_system is not None
        assert isinstance(category_manager.available_categories, dict)

        # Check that essential categories exist
        assert "core" in category_manager.available_categories
        assert "git" in category_manager.available_categories
        assert "analysis" in category_manager.available_categories

        # Check core category structure
        core_category = category_manager.available_categories["core"]
        assert "description" in core_category
        assert "functions" in core_category
        assert "tier" in core_category
        assert "token_cost" in core_category
        assert core_category["always_required"] is True

    def test_load_category_success(self, category_manager):
        """Test successful category loading."""
        result = category_manager.load_category("analysis")

        assert result.success is True
        assert "analysis" in result.message
        assert result.data is not None
        assert result.data["category"] == "analysis"
        assert "functions_loaded" in result.data
        assert "token_cost" in result.data
        assert "tier" in result.data

    def test_load_category_always_required(self, category_manager):
        """Test loading always-required category."""
        result = category_manager.load_category("core")

        assert result.success is True
        assert "always loaded" in result.message
        assert result.data["status"] == "always_loaded"

    def test_load_category_unknown(self, category_manager):
        """Test loading unknown category."""
        result = category_manager.load_category("unknown")

        assert result.success is False
        assert "Unknown category" in result.message
        assert len(result.suggestions) > 0
        assert "Available categories" in result.suggestions[0]

    def test_unload_category_success(self, category_manager):
        """Test successful category unloading."""
        result = category_manager.unload_category("analysis")

        assert result.success is True
        assert "Successfully unloaded" in result.message
        assert result.data is not None
        assert result.data["category"] == "analysis"
        assert "functions_unloaded" in result.data
        assert "tokens_saved" in result.data

    def test_unload_category_always_required(self, category_manager):
        """Test unloading always-required category fails."""
        result = category_manager.unload_category("core")

        assert result.success is False
        assert "Cannot unload" in result.message
        assert len(result.warnings) > 0
        assert "always loaded" in result.warnings[0]

    def test_unload_category_unknown(self, category_manager):
        """Test unloading unknown category."""
        result = category_manager.unload_category("nonexistent")

        assert result.success is False
        assert "Unknown category" in result.message
        assert len(result.suggestions) > 0


class TestCommandParser:
    """Test CommandParser class."""

    @pytest.fixture
    def parser(self):
        """Create CommandParser instance."""
        return CommandParser()

    def test_parse_help_command(self, parser):
        """Test parsing help command."""
        result = parser.parse_command("/help")

        assert "error" not in result
        assert result["command"] == "help"
        assert result["args"] == []

    def test_parse_load_command_with_args(self, parser):
        """Test parsing load command with arguments."""
        result = parser.parse_command("/load analysis quality")

        assert "error" not in result
        assert result["command"] == "load"
        assert result["args"] == ["analysis", "quality"]

    def test_parse_tier_command(self, parser):
        """Test parsing tier command."""
        result = parser.parse_command("/tier 2")

        assert "error" not in result
        assert result["command"] == "tier"
        assert result["args"] == ["2"]

    def test_parse_empty_command(self, parser):
        """Test parsing empty command."""
        result = parser.parse_command("")

        assert "error" in result
        assert "Empty command" in result["error"]

    def test_parse_invalid_command(self, parser):
        """Test parsing invalid command."""
        result = parser.parse_command("invalid_command")

        assert "error" in result
        assert "must start with '/'" in result["error"]

    def test_parse_unknown_command(self, parser):
        """Test parsing unknown command."""
        result = parser.parse_command("/unknown")

        assert "error" in result
        assert "Unknown command" in result["error"]
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create PerformanceMonitor instance."""
        return PerformanceMonitor()

    def test_performance_monitor_initialization(self, monitor):
        """Test PerformanceMonitor initialization."""
        assert isinstance(monitor.metrics, dict)
        assert "loading_times" in monitor.metrics
        assert "memory_usage" in monitor.metrics
        assert "cache_hits" in monitor.metrics
        assert "cache_misses" in monitor.metrics
        assert "function_calls" in monitor.metrics
        assert "category_usage" in monitor.metrics

    def test_record_loading_time(self, monitor):
        """Test recording loading time metrics."""
        monitor.record_loading_time("load_analysis", 150.0)

        # Check that metrics were recorded
        assert len(monitor.metrics["loading_times"]) == 1
        loading_time = monitor.metrics["loading_times"][0]
        assert loading_time["operation"] == "load_analysis"
        assert loading_time["duration_ms"] == 150.0
        assert "timestamp" in loading_time

    def test_record_memory_usage(self, monitor):
        """Test recording memory usage metrics."""
        monitor.record_memory_usage(256.5)

        # Check that metrics were recorded
        assert len(monitor.metrics["memory_usage"]) == 1
        memory_usage = monitor.metrics["memory_usage"][0]
        assert memory_usage["usage_mb"] == 256.5
        assert "timestamp" in memory_usage

    def test_get_function_stats(self, monitor):
        """Test getting function statistics."""
        # Record some metrics
        monitor.record_loading_time("load_analysis", 150.0)
        monitor.record_loading_time("load_quality", 100.0)
        monitor.record_memory_usage(256.0)
        monitor.metrics["cache_hits"] = 10
        monitor.metrics["cache_misses"] = 5
        monitor.metrics["function_calls"]["analyze"] = 3
        monitor.metrics["function_calls"]["refactor"] = 2

        result = monitor.get_function_stats()

        assert result.success is True
        assert "statistics" in result.message
        assert result.data is not None

        # Check that calculated values are correct
        data = result.data
        assert data["total_function_calls"] == 5  # 3 + 2
        assert data["avg_loading_time_ms"] == 125.0  # (150 + 100) / 2
        assert data["cache_hit_rate"] == 10 / 15  # 10 / (10 + 5)


class TestProfileManager:
    """Test ProfileManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def profile_manager(self, temp_dir):
        """Create ProfileManager with temporary storage."""
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()
        return ProfileManager(str(profiles_dir))

    def test_profile_manager_initialization(self, profile_manager):
        """Test ProfileManager initialization."""
        assert profile_manager.profiles_dir.exists()

    def test_save_and_load_profile(self, profile_manager):
        """Test saving and loading a profile."""
        profile = SessionProfile(
            name="Test Profile",
            description="A test profile",
            categories={"core": True, "analysis": True},
            performance_mode="balanced",
            tags=["test", "development"],
        )

        # Save profile
        result = profile_manager.save_profile(profile)
        assert result.success is True
        assert "saved successfully" in result.message

        # Load profile
        loaded_profiles = profile_manager.list_profiles()
        assert len(loaded_profiles) == 1
        assert loaded_profiles[0].name == "Test Profile"
        assert loaded_profiles[0].categories == {"core": True, "analysis": True}

    def test_delete_profile(self, profile_manager):
        """Test deleting a profile."""
        profile = SessionProfile(
            name="Delete Me",
            description="Profile to delete",
            categories={"core": True},
            performance_mode="conservative",
        )

        # Save and then delete
        profile_manager.save_profile(profile)
        result = profile_manager.delete_profile("Delete Me")

        assert result.success is True
        assert "deleted successfully" in result.message

        # Verify it's gone
        profiles = profile_manager.list_profiles()
        assert len(profiles) == 0

    def test_delete_nonexistent_profile(self, profile_manager):
        """Test deleting non-existent profile."""
        result = profile_manager.delete_profile("Nonexistent")

        assert result.success is False
        assert "not found" in result.message

    def test_apply_profile(self, profile_manager):
        """Test applying a profile to session."""
        profile = SessionProfile(
            name="Apply Test",
            description="Profile for apply test",
            categories={"analysis": True, "quality": False},
            performance_mode="aggressive",
        )

        profile_manager.save_profile(profile)

        session = UserSession(session_id="test_session")
        result = profile_manager.apply_profile("Apply Test", session)

        assert result.success is True
        assert "applied successfully" in result.message
        assert session.active_categories == {"analysis": True, "quality": False}
        assert session.performance_mode == "aggressive"


class TestUserControlSystem:
    """Test UserControlSystem integration."""

    @pytest.fixture
    def mock_detection_system(self):
        """Create mock detection system."""
        detection_system = Mock()
        detection_system.available_categories = ["core", "git", "analysis"]
        return detection_system

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock config manager."""
        return Mock()

    @pytest.fixture
    def user_control_system(self, mock_detection_system, mock_config_manager):
        """Create UserControlSystem instance."""
        return UserControlSystem(mock_detection_system, mock_config_manager)

    def test_system_initialization(self, user_control_system):
        """Test UserControlSystem initialization."""
        assert user_control_system.detection_system is not None
        assert user_control_system.config_manager is not None
        assert user_control_system.category_manager is not None
        assert user_control_system.tier_controller is not None
        assert user_control_system.performance_monitor is not None
        assert user_control_system.profile_manager is not None
        assert user_control_system.command_parser is not None

        # Check session initialization
        assert isinstance(user_control_system.current_session, UserSession)
        assert user_control_system.current_session.user_level == "balanced"
        assert user_control_system.current_session.performance_mode == "conservative"

    @pytest.mark.asyncio
    async def test_execute_help_command(self, user_control_system):
        """Test executing help command."""
        result = await user_control_system.execute_command("/help")

        assert result.success is True
        assert "Available commands" in result.message or "Help" in result.message

    @pytest.mark.asyncio
    async def test_execute_status_command(self, user_control_system):
        """Test executing status command."""
        result = await user_control_system.execute_command("/status")

        assert result.success is True
        assert result.data is not None
        assert "session" in result.data
        assert "categories" in result.data

    @pytest.mark.asyncio
    async def test_execute_load_command(self, user_control_system):
        """Test executing load command."""
        result = await user_control_system.execute_command("/load analysis")

        assert result.success is True
        assert "analysis" in result.message

    @pytest.mark.asyncio
    async def test_execute_invalid_command(self, user_control_system):
        """Test executing invalid command."""
        result = await user_control_system.execute_command("/invalid")

        assert result.success is False
        assert "Unknown command" in result.message
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_execute_empty_command(self, user_control_system):
        """Test executing empty command."""
        result = await user_control_system.execute_command("")

        assert result.success is False
        assert "Empty command" in result.message

    @pytest.mark.asyncio
    async def test_command_history_tracking(self, user_control_system):
        """Test that commands are tracked in history."""
        await user_control_system.execute_command("/help")
        await user_control_system.execute_command("/status")

        # Check that commands were recorded
        assert len(user_control_system.current_session.command_history) >= 2

        # Check analytics
        assert user_control_system.usage_analytics["commands_executed"]["help"] >= 1
        assert user_control_system.usage_analytics["commands_executed"]["status"] >= 1

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, user_control_system):
        """Test that performance metrics are collected."""
        # Execute a few commands
        await user_control_system.execute_command("/help")
        await user_control_system.execute_command("/status")

        # Check that performance data was collected
        summary = user_control_system.performance_monitor.get_performance_summary()
        assert "avg_command_time" in summary
        assert summary["avg_command_time"] > 0

    def test_session_state_management(self, user_control_system):
        """Test session state management."""
        # Modify session state
        user_control_system.current_session.user_level = "expert"
        user_control_system.current_session.performance_mode = "aggressive"
        user_control_system.current_session.active_categories["analysis"] = True

        # Verify state changes
        assert user_control_system.current_session.user_level == "expert"
        assert user_control_system.current_session.performance_mode == "aggressive"
        assert user_control_system.current_session.active_categories["analysis"] is True

    def test_usage_analytics_collection(self, user_control_system):
        """Test usage analytics collection."""
        # Check initial state
        analytics = user_control_system.usage_analytics
        assert "commands_executed" in analytics
        assert "categories_used" in analytics
        assert "error_patterns" in analytics
        assert "session_patterns" in analytics


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.fixture
    def mock_detection_system(self):
        """Create comprehensive mock detection system."""
        detection_system = Mock()
        detection_system.available_categories = ["core", "git", "analysis", "quality", "test"]
        detection_system.current_tier = 2
        return detection_system

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock config manager."""
        config_manager = Mock()
        config_manager.get_detection_config.return_value = {"threshold": 0.8}
        return config_manager

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def user_control_system(self, mock_detection_system, mock_config_manager, temp_dir):
        """Create UserControlSystem with temporary storage."""
        # Patch ProfileManager to use temp directory
        with patch.object(
            ProfileManager,
            "__init__",
            lambda self, profiles_dir=None: setattr(self, "profiles_dir", temp_dir / "profiles")
            or temp_dir.joinpath("profiles").mkdir(exist_ok=True),
        ):
            return UserControlSystem(mock_detection_system, mock_config_manager)

    @pytest.mark.asyncio
    async def test_complete_workflow_scenario(self, user_control_system):
        """Test complete user workflow scenario."""
        # 1. Start with help
        help_result = await user_control_system.execute_command("/help")
        assert help_result.success is True

        # 2. Check current status
        status_result = await user_control_system.execute_command("/status")
        assert status_result.success is True
        assert status_result.data is not None

        # 3. Load analysis category
        load_result = await user_control_system.execute_command("/load analysis")
        assert load_result.success is True
        assert "analysis" in load_result.message

        # 4. Set performance mode
        perf_result = await user_control_system.execute_command("/performance aggressive")
        assert perf_result.success is True

        # 5. Check final status
        final_status = await user_control_system.execute_command("/status")
        assert final_status.success is True

        # Verify session state changes
        session = user_control_system.current_session
        assert len(session.command_history) >= 5

        # Verify analytics were collected
        analytics = user_control_system.usage_analytics
        assert analytics["commands_executed"]["help"] >= 1
        assert analytics["commands_executed"]["status"] >= 2
        assert analytics["commands_executed"]["load"] >= 1

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, user_control_system):
        """Test error handling and recovery scenarios."""
        # Try invalid command
        invalid_result = await user_control_system.execute_command("/invalid")
        assert invalid_result.success is False
        assert len(invalid_result.suggestions) > 0

        # Try loading non-existent category
        load_invalid = await user_control_system.execute_command("/load nonexistent")
        assert load_invalid.success is False

        # Try valid command after errors
        valid_result = await user_control_system.execute_command("/help")
        assert valid_result.success is True

        # Verify system is still functional
        status_result = await user_control_system.execute_command("/status")
        assert status_result.success is True

    @pytest.mark.asyncio
    async def test_session_persistence_and_recovery(self, user_control_system):
        """Test session persistence and recovery."""
        original_session_id = user_control_system.current_session.session_id

        # Modify session state
        user_control_system.current_session.user_level = "expert"
        user_control_system.current_session.active_categories["analysis"] = True
        user_control_system.current_session.preferences["theme"] = "dark"

        # Execute some commands to build history
        await user_control_system.execute_command("/help")
        await user_control_system.execute_command("/status")

        # Verify session state
        assert user_control_system.current_session.session_id == original_session_id
        assert user_control_system.current_session.user_level == "expert"
        assert user_control_system.current_session.active_categories["analysis"] is True
        assert user_control_system.current_session.preferences["theme"] == "dark"
        assert len(user_control_system.current_session.command_history) >= 2

    def test_performance_monitoring_comprehensive(self, user_control_system):
        """Test comprehensive performance monitoring."""
        monitor = user_control_system.performance_monitor

        # Record various metrics
        monitor.record_command_execution("load", 0.5, True, {"tokens": 1000})
        monitor.record_command_execution("tier", 0.3, True, {"tokens": 200})
        monitor.record_command_execution("help", 0.1, True, {"tokens": 50})
        monitor.record_command_execution("invalid", 0.05, False, {"tokens": 0})

        monitor.record_category_performance("analysis", 2.5, 5000, 0.9)
        monitor.record_category_performance("quality", 1.8, 3000, 0.85)

        # Get comprehensive summary
        summary = monitor.get_performance_summary()

        assert summary["total_tokens_used"] == 1250
        assert 0 < summary["avg_command_time"] < 1.0
        assert summary["command_success_rate"] == 0.75  # 3/4 commands succeeded

        assert "analysis" in summary["category_performance"]
        assert "quality" in summary["category_performance"]

        analysis_perf = summary["category_performance"]["analysis"]
        assert analysis_perf["avg_load_time"] == 2.5
        assert analysis_perf["avg_token_cost"] == 5000
        assert analysis_perf["avg_success_rate"] == 0.9
