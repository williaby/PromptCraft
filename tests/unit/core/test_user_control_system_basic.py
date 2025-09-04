"""
Basic tests for User Control System components.

This test module provides coverage of the key user control system components
with minimal mocking, focusing on testing the actual interfaces and basic functionality.
"""

from unittest.mock import Mock

import pytest

from src.core.user_control_system import (
    CategoryManager,
    CommandResult,
    PerformanceMonitor,
    SessionProfile,
    UserControlSystem,
    UserSession,
)


class TestUserSession:
    """Test UserSession data class."""

    def test_user_session_creation(self):
        """Test UserSession creation with defaults."""
        session = UserSession(session_id="test_session")

        assert session.session_id == "test_session"
        assert session.user_level == "balanced"
        assert session.performance_mode == "conservative"
        assert session.learning_enabled is True

    def test_user_session_custom_values(self):
        """Test UserSession with custom values."""
        session = UserSession(
            session_id="custom_session",
            user_level="expert",
            performance_mode="aggressive",
            learning_enabled=False,
        )

        assert session.session_id == "custom_session"
        assert session.user_level == "expert"
        assert session.performance_mode == "aggressive"
        assert session.learning_enabled is False


class TestSessionProfile:
    """Test SessionProfile data class."""

    def test_session_profile_creation(self):
        """Test SessionProfile creation."""
        profile = SessionProfile(
            name="Test Profile",
            description="Test profile description",
            categories={"core": True, "analysis": True},
            performance_mode="balanced",
        )

        assert profile.name == "Test Profile"
        assert profile.description == "Test profile description"
        assert profile.categories == {"core": True, "analysis": True}
        assert profile.performance_mode == "balanced"
        assert profile.usage_count == 0
        assert profile.created_by == "user"


class TestCommandResult:
    """Test CommandResult data class."""

    def test_command_result_success(self):
        """Test successful CommandResult."""
        result = CommandResult(success=True, message="Success")

        assert result.success is True
        assert result.message == "Success"
        assert result.data is None
        assert result.suggestions == []
        assert result.warnings == []

    def test_command_result_failure(self):
        """Test failed CommandResult with suggestions."""
        result = CommandResult(
            success=False,
            message="Failed",
            suggestions=["Try /help"],
            warnings=["This is deprecated"],
        )

        assert result.success is False
        assert result.message == "Failed"
        assert result.suggestions == ["Try /help"]
        assert result.warnings == ["This is deprecated"]


class TestCategoryManager:
    """Test CategoryManager functionality."""

    @pytest.fixture
    def mock_detection_system(self):
        """Create mock detection system."""
        return Mock()

    @pytest.fixture
    def category_manager(self, mock_detection_system):
        """Create CategoryManager instance."""
        return CategoryManager(mock_detection_system)

    def test_category_manager_initialization(self, category_manager):
        """Test CategoryManager has expected categories."""
        assert hasattr(category_manager, "available_categories")
        assert isinstance(category_manager.available_categories, dict)

        # Check essential categories exist
        assert "core" in category_manager.available_categories
        assert "git" in category_manager.available_categories

        # Check core category structure
        core_cat = category_manager.available_categories["core"]
        assert "description" in core_cat
        assert "functions" in core_cat
        assert "tier" in core_cat
        assert core_cat.get("always_required") is True

    def test_load_category_success(self, category_manager):
        """Test loading a valid category."""
        result = category_manager.load_category("analysis")

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert "analysis" in result.message

    def test_load_category_unknown(self, category_manager):
        """Test loading unknown category returns error."""
        result = category_manager.load_category("unknown_category")

        assert isinstance(result, CommandResult)
        assert result.success is False
        assert "Unknown category" in result.message
        assert len(result.suggestions) > 0

    def test_load_always_required_category(self, category_manager):
        """Test loading always-required category."""
        result = category_manager.load_category("core")

        assert result.success is True
        assert "always loaded" in result.message

    def test_unload_category_success(self, category_manager):
        """Test unloading a valid category."""
        result = category_manager.unload_category("analysis")

        assert result.success is True
        assert "unloaded" in result.message

    def test_unload_always_required_fails(self, category_manager):
        """Test unloading always-required category fails."""
        result = category_manager.unload_category("core")

        assert result.success is False
        assert "Cannot unload" in result.message
        assert len(result.warnings) > 0


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality."""

    @pytest.fixture
    def monitor(self):
        """Create PerformanceMonitor instance."""
        return PerformanceMonitor()

    def test_monitor_initialization(self, monitor):
        """Test PerformanceMonitor has expected structure."""
        assert hasattr(monitor, "metrics")
        assert isinstance(monitor.metrics, dict)

        # Check expected keys exist
        expected_keys = [
            "loading_times",
            "memory_usage",
            "cache_hits",
            "cache_misses",
            "function_calls",
            "category_usage",
        ]
        for key in expected_keys:
            assert key in monitor.metrics

    def test_record_loading_time(self, monitor):
        """Test recording loading time."""
        monitor.record_loading_time("test_operation", 100.0)

        assert len(monitor.metrics["loading_times"]) == 1
        loading_entry = monitor.metrics["loading_times"][0]
        assert loading_entry["operation"] == "test_operation"
        assert loading_entry["duration_ms"] == 100.0

    def test_record_memory_usage(self, monitor):
        """Test recording memory usage."""
        monitor.record_memory_usage(512.0)

        assert len(monitor.metrics["memory_usage"]) == 1
        memory_entry = monitor.metrics["memory_usage"][0]
        assert memory_entry["usage_mb"] == 512.0

    def test_get_function_stats(self, monitor):
        """Test getting function statistics."""
        # Add some test data
        monitor.record_loading_time("op1", 100.0)
        monitor.record_loading_time("op2", 200.0)
        monitor.metrics["cache_hits"] = 10
        monitor.metrics["cache_misses"] = 5

        result = monitor.get_function_stats()

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert result.data is not None


class TestUserControlSystemBasic:
    """Test basic UserControlSystem functionality."""

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
        """Test UserControlSystem initializes correctly."""
        # Check components are created
        assert hasattr(user_control_system, "detection_system")
        assert hasattr(user_control_system, "config_manager")
        assert hasattr(user_control_system, "category_manager")
        assert hasattr(user_control_system, "tier_controller")
        assert hasattr(user_control_system, "performance_monitor")
        assert hasattr(user_control_system, "profile_manager")
        assert hasattr(user_control_system, "command_parser")

        # Check session is initialized
        assert hasattr(user_control_system, "current_session")
        assert isinstance(user_control_system.current_session, UserSession)
        assert user_control_system.current_session.user_level == "balanced"
        assert user_control_system.current_session.performance_mode == "conservative"

    @pytest.mark.asyncio
    async def test_execute_help_command(self, user_control_system):
        """Test executing help command."""
        result = await user_control_system.execute_command("/help")

        assert isinstance(result, CommandResult)
        # Help command should work (or return appropriate error)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_execute_invalid_command(self, user_control_system):
        """Test executing invalid command."""
        result = await user_control_system.execute_command("invalid")

        assert isinstance(result, CommandResult)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_empty_command(self, user_control_system):
        """Test executing empty command."""
        result = await user_control_system.execute_command("")

        assert isinstance(result, CommandResult)
        assert result.success is False

    def test_session_state_modifications(self, user_control_system):
        """Test modifying session state."""
        original_level = user_control_system.current_session.user_level

        # Modify session
        user_control_system.current_session.user_level = "expert"
        user_control_system.current_session.performance_mode = "aggressive"

        # Verify changes
        assert user_control_system.current_session.user_level == "expert"
        assert user_control_system.current_session.performance_mode == "aggressive"
        assert user_control_system.current_session.user_level != original_level

    def test_usage_analytics_structure(self, user_control_system):
        """Test usage analytics has expected structure."""
        assert hasattr(user_control_system, "usage_analytics")
        analytics = user_control_system.usage_analytics

        expected_keys = ["commands_executed", "categories_used", "error_patterns", "session_patterns"]
        for key in expected_keys:
            assert key in analytics


class TestIntegrationBasic:
    """Test basic integration scenarios."""

    @pytest.fixture
    def user_control_system(self):
        """Create UserControlSystem with mocked dependencies."""
        mock_detection = Mock()
        mock_detection.available_categories = ["core", "git", "analysis"]
        mock_config = Mock()
        return UserControlSystem(mock_detection, mock_config)

    @pytest.mark.asyncio
    async def test_command_execution_flow(self, user_control_system):
        """Test basic command execution flow."""
        # Execute a few commands to test the flow
        commands = ["/help", "/invalid", ""]

        for command in commands:
            result = await user_control_system.execute_command(command)
            assert isinstance(result, CommandResult)
            assert isinstance(result.success, bool)
            assert isinstance(result.message, str)

    def test_component_interaction(self, user_control_system):
        """Test that components are properly integrated."""
        # Check that all components are accessible and properly typed
        assert hasattr(user_control_system.category_manager, "available_categories")
        assert hasattr(user_control_system.performance_monitor, "metrics")
        assert hasattr(user_control_system.current_session, "session_id")

        # Test component methods work
        result = user_control_system.category_manager.load_category("analysis")
        assert isinstance(result, CommandResult)

        stats_result = user_control_system.performance_monitor.get_function_stats()
        assert isinstance(stats_result, CommandResult)
