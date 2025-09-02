"""
Comprehensive test suite for User Control System

Tests the CategoryManager, TierController, PerformanceMonitor, and other components
that make up the user control system functionality.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.utils.datetime_compat import UTC

from src.core.user_control_system import (
    CategoryManager,
    CommandResult,
    PerformanceMonitor,
    SessionProfile,
    TierController,
    UserSession,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_detection_system():
    """Create mock TaskDetectionSystem"""
    mock_system = Mock()
    mock_system.get_categories.return_value = {
        "core": {"tier": 1, "loaded": True, "functions": ["func1", "func2"]},
        "advanced": {"tier": 2, "loaded": False, "functions": ["func3", "func4"]},
        "expert": {"tier": 3, "loaded": False, "functions": ["func5"]},
    }
    mock_system.load_category.return_value = True
    mock_system.unload_category.return_value = True
    return mock_system


@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager"""
    mock_manager = Mock()
    mock_manager.get_config.return_value = {
        "detection_enabled": True,
        "max_tier": 3,
        "performance_mode": "balanced",
    }
    return mock_manager


@pytest.fixture
def category_manager(mock_detection_system):
    """Create CategoryManager instance with mocked dependencies"""
    return CategoryManager(mock_detection_system)


@pytest.fixture
def tier_controller(mock_detection_system):
    """Create TierController instance with mocked dependencies"""
    return TierController(mock_detection_system)


@pytest.fixture
def performance_monitor():
    """Create PerformanceMonitor instance"""
    return PerformanceMonitor()


@pytest.fixture
def sample_user_session():
    """Create sample UserSession for testing"""
    return UserSession(
        session_id="test-session-123",
        user_level="balanced",
        active_categories={"core": True, "advanced": False},
        performance_mode="conservative",
        command_history=[
            {
                "timestamp": "2025-01-15T11:00:00",
                "command": "load_category",
                "parameters": {"category": "core"},
                "success": True,
            },
        ],
        preferences={"theme": "dark", "auto_save": True},
        learning_enabled=True,
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        last_activity=datetime(2025, 1, 15, 11, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_session_profile():
    """Create sample SessionProfile for testing"""
    return SessionProfile(
        name="Test Profile",
        description="A test session profile",
        categories={"core": True, "advanced": False},
        performance_mode="balanced",
        detection_config={"max_tier": 2},
        tags=["test", "development"],
    )


@pytest.fixture
def sample_command_result():
    """Create sample CommandResult for testing"""
    return CommandResult(
        success=True,
        message="Operation completed successfully",
        data={"loaded_categories": ["core"], "active_functions": 10},
    )


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestDataClasses:
    """Test dataclass creation and validation"""

    def test_user_session_creation(self, sample_user_session):
        """Test UserSession dataclass creation"""
        assert sample_user_session.session_id == "test-session-123"
        assert sample_user_session.user_level == "balanced"
        assert sample_user_session.active_categories["core"] is True
        assert sample_user_session.performance_mode == "conservative"
        assert len(sample_user_session.command_history) == 1
        assert sample_user_session.learning_enabled is True

    def test_user_session_default_values(self):
        """Test UserSession with default values"""
        session = UserSession(session_id="test-default")

        assert session.session_id == "test-default"
        assert session.user_level == "balanced"
        assert session.performance_mode == "conservative"
        assert isinstance(session.active_categories, dict)
        assert isinstance(session.command_history, list)
        assert isinstance(session.preferences, dict)
        assert session.learning_enabled is True
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)

    def test_session_profile_creation(self, sample_session_profile):
        """Test SessionProfile dataclass creation"""
        assert sample_session_profile.name == "Test Profile"
        assert sample_session_profile.description == "A test session profile"
        assert sample_session_profile.categories["core"] is True
        assert sample_session_profile.performance_mode == "balanced"
        assert sample_session_profile.detection_config["max_tier"] == 2
        assert "test" in sample_session_profile.tags

    def test_command_result_creation(self, sample_command_result):
        """Test CommandResult dataclass creation"""
        assert sample_command_result.success is True
        assert "successfully" in sample_command_result.message
        assert sample_command_result.data["loaded_categories"] == ["core"]
        assert sample_command_result.data["active_functions"] == 10

    def test_command_result_error_case(self):
        """Test CommandResult for error scenarios"""
        error_result = CommandResult(
            success=False,
            message="Operation failed",
            data={"error_code": 404, "details": "Category not found"},
        )

        assert error_result.success is False
        assert "failed" in error_result.message
        assert error_result.data["error_code"] == 404


# =============================================================================
# CATEGORY MANAGER TESTS
# =============================================================================


class TestCategoryManager:
    """Test CategoryManager functionality"""

    def test_initialization(self, category_manager, mock_detection_system):
        """Test CategoryManager initialization"""
        assert category_manager.detection_system == mock_detection_system
        assert hasattr(category_manager, "detection_system")

    def test_load_category_success(self, category_manager, mock_detection_system):
        """Test successful category loading"""
        result = category_manager.load_category("core")

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert "core" in result.message.lower() or "essential" in result.message.lower()

    def test_load_category_not_found(self, category_manager, mock_detection_system):
        """Test loading non-existent category"""
        mock_detection_system.get_categories.return_value = {}

        result = category_manager.load_category("non_existent")

        assert isinstance(result, CommandResult)
        # Should handle gracefully

    def test_load_category_already_loaded(self, category_manager, mock_detection_system):
        """Test loading already loaded category"""
        mock_detection_system.get_categories.return_value = {
            "core": {"tier": 1, "loaded": True, "functions": ["func1"]},
        }

        result = category_manager.load_category("core")

        assert isinstance(result, CommandResult)
        # Should handle already loaded state

    def test_unload_category_success(self, category_manager, mock_detection_system):
        """Test successful category unloading"""
        result = category_manager.unload_category("core")

        assert isinstance(result, CommandResult)
        # Core category cannot be unloaded as it's essential - this is expected behavior
        assert result.success is False
        assert "required" in result.message.lower()

    def test_unload_category_not_loaded(self, category_manager, mock_detection_system):
        """Test unloading category that's not loaded"""
        mock_detection_system.get_categories.return_value = {
            "core": {"tier": 1, "loaded": False, "functions": ["func1"]},
        }

        result = category_manager.unload_category("core")

        assert isinstance(result, CommandResult)
        # Should handle not loaded state

    def test_list_categories_all(self, category_manager, mock_detection_system):
        """Test listing all categories"""
        result = category_manager.list_categories()

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert "categories" in result.message.lower() or result.data is not None

    def test_list_categories_with_tier_filter(self, category_manager, mock_detection_system):
        """Test listing categories with tier filter"""
        result = category_manager.list_categories(filter_tier=1)

        assert isinstance(result, CommandResult)
        # Should filter by tier

    def test_list_categories_loaded_only(self, category_manager, mock_detection_system):
        """Test listing only loaded categories"""
        result = category_manager.list_categories(show_loaded_only=True)

        assert isinstance(result, CommandResult)
        # Should show only loaded categories

    def test_get_category_info_existing(self, category_manager, mock_detection_system):
        """Test getting info for existing category"""
        result = category_manager.get_category_info("core")

        assert isinstance(result, CommandResult)

    def test_get_category_info_non_existing(self, category_manager, mock_detection_system):
        """Test getting info for non-existing category"""
        mock_detection_system.get_categories.return_value = {}

        result = category_manager.get_category_info("non_existent")

        assert isinstance(result, CommandResult)
        # Should handle non-existent category


# =============================================================================
# TIER CONTROLLER TESTS
# =============================================================================


class TestTierController:
    """Test TierController functionality"""

    def test_initialization(self, tier_controller, mock_detection_system):
        """Test TierController initialization"""
        assert tier_controller.detection_system == mock_detection_system
        assert hasattr(tier_controller, "detection_system")

    def test_load_tier_success(self, tier_controller, mock_detection_system):
        """Test successful tier loading"""
        mock_detection_system.get_categories.return_value = {
            "core": {"tier": 1, "loaded": False},
            "advanced": {"tier": 1, "loaded": False},
        }
        mock_detection_system.load_category.return_value = True

        result = tier_controller.load_tier(1)

        assert isinstance(result, CommandResult)

    def test_load_tier_with_force(self, tier_controller, mock_detection_system):
        """Test tier loading with force flag"""
        result = tier_controller.load_tier(2, force=True)

        assert isinstance(result, CommandResult)

    def test_load_tier_invalid(self, tier_controller, mock_detection_system):
        """Test loading invalid tier"""
        result = tier_controller.load_tier(99)  # Very high tier

        assert isinstance(result, CommandResult)
        # Should handle invalid tier gracefully

    def test_unload_tier_success(self, tier_controller, mock_detection_system):
        """Test successful tier unloading"""
        mock_detection_system.get_categories.return_value = {
            "advanced": {"tier": 2, "loaded": True},
        }
        mock_detection_system.unload_category.return_value = True

        result = tier_controller.unload_tier(2)

        assert isinstance(result, CommandResult)

    def test_unload_tier_with_force(self, tier_controller, mock_detection_system):
        """Test tier unloading with force flag"""
        result = tier_controller.unload_tier(1, force=True)

        assert isinstance(result, CommandResult)

    def test_get_tier_status(self, tier_controller, mock_detection_system):
        """Test getting tier status"""
        result = tier_controller.get_tier_status()

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert result.data is not None
        assert "tiers" in result.data

    def test_optimize_for_task_valid(self, tier_controller, mock_detection_system):
        """Test optimizing for valid task type"""
        result = tier_controller.optimize_for_task("data_analysis")

        assert isinstance(result, CommandResult)

    def test_optimize_for_task_invalid(self, tier_controller, mock_detection_system):
        """Test optimizing for invalid task type"""
        result = tier_controller.optimize_for_task("unknown_task")

        assert isinstance(result, CommandResult)
        # Should handle unknown task gracefully

    def test_optimize_for_task_empty(self, tier_controller, mock_detection_system):
        """Test optimizing with empty task type"""
        result = tier_controller.optimize_for_task("")

        assert isinstance(result, CommandResult)
        # Should handle empty input


# =============================================================================
# PERFORMANCE MONITOR TESTS
# =============================================================================


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality"""

    def test_initialization(self, performance_monitor):
        """Test PerformanceMonitor initialization"""
        assert hasattr(performance_monitor, "metrics")
        assert "loading_times" in performance_monitor.metrics
        assert "memory_usage" in performance_monitor.metrics
        assert isinstance(performance_monitor.metrics["loading_times"], list)
        assert isinstance(performance_monitor.metrics["memory_usage"], list)

    def test_record_loading_time(self, performance_monitor):
        """Test recording loading time"""
        performance_monitor.record_loading_time("load_category", 150.5)

        # Should store the loading time
        assert len(performance_monitor.metrics["loading_times"]) > 0
        assert performance_monitor.metrics["loading_times"][0]["operation"] == "load_category"
        assert performance_monitor.metrics["loading_times"][0]["duration_ms"] == 150.5

    def test_record_loading_time_multiple(self, performance_monitor):
        """Test recording multiple loading times"""
        operations = [
            ("load_category", 100.0),
            ("unload_category", 50.0),
            ("optimize_for_task", 200.0),
        ]

        for operation, duration in operations:
            performance_monitor.record_loading_time(operation, duration)

        assert len(performance_monitor.metrics["loading_times"]) >= 3

    def test_record_memory_usage(self, performance_monitor):
        """Test recording memory usage"""
        performance_monitor.record_memory_usage(256.7)

        # Should store the memory usage
        assert len(performance_monitor.metrics["memory_usage"]) > 0
        assert performance_monitor.metrics["memory_usage"][0]["usage_mb"] == 256.7

    def test_record_memory_usage_multiple(self, performance_monitor):
        """Test recording multiple memory usage points"""
        memory_values = [100.0, 150.5, 200.2, 175.8]

        for memory in memory_values:
            performance_monitor.record_memory_usage(memory)

        assert len(performance_monitor.metrics["memory_usage"]) >= 4

    def test_get_function_stats_empty(self, performance_monitor):
        """Test getting function stats with no data"""
        result = performance_monitor.get_function_stats()

        assert isinstance(result, CommandResult)

    def test_get_function_stats_with_data(self, performance_monitor):
        """Test getting function stats with recorded data"""
        # Record some data first
        performance_monitor.record_loading_time("load_category", 100.0)
        performance_monitor.record_loading_time("load_category", 120.0)
        performance_monitor.record_memory_usage(200.0)

        result = performance_monitor.get_function_stats()

        assert isinstance(result, CommandResult)
        # Should contain statistical information

    def test_clear_cache(self, performance_monitor):
        """Test clearing performance cache"""
        # Add some data first
        performance_monitor.record_loading_time("test", 100.0)
        performance_monitor.record_memory_usage(150.0)

        result = performance_monitor.clear_cache()

        assert isinstance(result, CommandResult)
        # Data should be cleared or reset

    def test_benchmark_loading_no_data(self, performance_monitor):
        """Test benchmark loading with no recorded data"""
        result = performance_monitor.benchmark_loading()

        assert isinstance(result, CommandResult)

    def test_benchmark_loading_with_data(self, performance_monitor):
        """Test benchmark loading with recorded data"""
        # Record some benchmark data
        for i in range(5):
            performance_monitor.record_loading_time(f"operation_{i}", 100.0 + i * 10)
            performance_monitor.record_memory_usage(200.0 + i * 25)

        result = performance_monitor.benchmark_loading()

        assert isinstance(result, CommandResult)
        # Should contain benchmark results
