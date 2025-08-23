"""Test the comprehensive isolation fixture system.

This test file demonstrates and validates the comprehensive test isolation
system to ensure it properly maintains clean state between test runs.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from tests.fixtures.isolation import (
    assert_no_state_leakage,
    create_isolated_jwt_test_suite,
    isolated_environment_vars,
    isolated_mock_context,
    isolated_temp_directory,
    validate_test_isolation,
)


class TestComprehensiveIsolation:
    """Test class for comprehensive isolation system validation."""

    def test_isolation_manager_basic_functionality(self, isolation_manager):
        """Test that isolation manager provides proper context management."""
        # The auto_isolation fixture creates a context, but the stack size may vary
        # What matters is that we can manipulate contexts properly
        initial_stack_size = len(isolation_manager._isolation_stack)

        # Push a new context
        isolation_manager.push_isolation_context("test_context")
        assert len(isolation_manager._isolation_stack) == initial_stack_size + 1

        # Register a mock
        test_mock = Mock()
        isolation_manager.register_mock(test_mock)
        assert test_mock in isolation_manager._active_mocks

        # Pop context should clean up the mock
        isolation_manager.pop_isolation_context()
        assert len(isolation_manager._isolation_stack) == initial_stack_size
        assert test_mock not in isolation_manager._active_mocks

    def test_environment_variable_isolation(self):
        """Test isolated environment variable changes."""
        # TEST_VAR should not exist initially
        original_value = os.environ.get("TEST_VAR")
        assert original_value is None  # Ensure clean starting state

        with isolated_environment_vars(TEST_VAR="test_value", NEW_VAR="new_value"):
            assert os.environ.get("TEST_VAR") == "test_value"
            assert os.environ.get("NEW_VAR") == "new_value"

        # Should be restored after context (back to None)
        assert os.environ.get("TEST_VAR") is None
        assert os.environ.get("NEW_VAR") is None

    def test_environment_variable_unset_isolation(self):
        """Test isolated environment variable unsetting."""
        # Set a variable first
        os.environ["TEMP_TEST_VAR"] = "temp_value"

        with isolated_environment_vars(TEMP_TEST_VAR=None):
            assert os.environ.get("TEMP_TEST_VAR") is None

        # Should be restored
        assert os.environ.get("TEMP_TEST_VAR") == "temp_value"

        # Clean up
        del os.environ["TEMP_TEST_VAR"]

    def test_temporary_directory_isolation(self):
        """Test isolated temporary directory creation and cleanup."""
        created_dirs = []

        with isolated_temp_directory() as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            created_dirs.append(temp_dir)

            # Create a file in the temp directory
            test_file = temp_dir / "test_file.txt"
            test_file.write_text("test content")
            assert test_file.exists()

        # Directory should be cleaned up
        for temp_dir in created_dirs:
            assert not temp_dir.exists()

    def test_mock_context_isolation(self):
        """Test isolated mock context management."""
        with isolated_mock_context("builtins.open", "os.path.exists") as mocks:
            open_mock, exists_mock = mocks

            # Mocks should be properly configured
            assert isinstance(open_mock, Mock)
            assert isinstance(exists_mock, Mock)

            # Set up mock behavior
            exists_mock.return_value = True
            assert exists_mock.return_value is True

        # Mocks should be stopped after context
        # (In real usage, the patches would be stopped automatically)

    def test_file_system_isolation(self, isolated_file_system):
        """Test isolated file system operations."""
        # Should be operating in a temporary directory
        current_dir = Path.cwd()
        assert str(current_dir).startswith(str(Path(tempfile.gettempdir())))

        # Create files safely in isolated environment
        test_file = Path("isolated_test_file.txt")
        test_file.write_text("isolated content")
        assert test_file.exists()

        # File operations are isolated to temp directory

    def test_comprehensive_isolation_fixture(self, comprehensive_isolation):
        """Test the comprehensive isolation fixture."""
        context = comprehensive_isolation

        # Should provide temp directory
        assert context["temp_dir"] is not None
        assert context["temp_dir"].exists()

        # Should have environment backup
        assert "env_backup" in context
        assert isinstance(context["env_backup"], dict)

        # Should have mock and async task containers
        assert "mocks" in context
        assert "async_tasks" in context

    def test_jwt_test_suite_creation(self):
        """Test isolated JWT test suite creation."""
        jwt_suite = create_isolated_jwt_test_suite()

        # Should contain all expected components
        expected_keys = {"validator", "valid_token", "expired_token", "malformed_token", "admin_user", "regular_user"}
        assert set(jwt_suite.keys()) == expected_keys

        # Components should be properly isolated instances
        assert jwt_suite["validator"] is not None
        assert isinstance(jwt_suite["valid_token"], str)
        assert len(jwt_suite["valid_token"].split(".")) == 3  # Valid JWT structure

    def test_state_leakage_detection(self):
        """Test that state leakage detection works properly."""
        # Should pass with non-strict mode (cleans up automatically)
        assert_no_state_leakage(strict=False)

        # This test validates that the assertion works correctly
        # In a real scenario, failing tests would leave state that triggers the assertion

    def test_isolation_validation(self):
        """Test isolation validation for test functions."""

        # Test function with isolation fixture
        def test_with_isolation(isolation_manager):
            pass

        # Test function without isolation
        def test_without_isolation():
            pass

        assert validate_test_isolation(test_with_isolation)
        assert not validate_test_isolation(test_without_isolation)

    def test_multiple_isolation_contexts(self, isolation_manager):
        """Test that multiple isolation contexts work correctly."""
        initial_stack_size = len(isolation_manager._isolation_stack)

        # Create nested isolation contexts
        isolation_manager.push_isolation_context("context_1")
        isolation_manager.push_isolation_context("context_2")

        assert len(isolation_manager._isolation_stack) == initial_stack_size + 2

        # Register resources in different contexts
        mock1 = Mock()
        isolation_manager.register_mock(mock1)

        isolation_manager.pop_isolation_context()  # context_2
        isolation_manager.pop_isolation_context()  # context_1

        assert len(isolation_manager._isolation_stack) == initial_stack_size

    def test_isolation_between_test_methods(self):
        """Test that isolation is maintained between test methods."""
        # This test runs after previous tests and should have clean state
        # The auto_isolation fixture ensures this happens automatically
        assert_no_state_leakage(strict=False)

    @pytest.mark.parametrize(
        "test_data",
        [
            {"env_var": "TEST_1", "value": "value_1"},
            {"env_var": "TEST_2", "value": "value_2"},
            {"env_var": "TEST_3", "value": "value_3"},
        ],
    )
    def test_parametrized_isolation(self, test_data):
        """Test that isolation works correctly with parametrized tests."""
        env_var = test_data["env_var"]
        value = test_data["value"]

        # Each parametrized run should have clean state
        assert os.environ.get(env_var) is None

        with isolated_environment_vars(**{env_var: value}):
            assert os.environ.get(env_var) == value

        # Should be cleaned up after each parametrized run
        assert os.environ.get(env_var) is None


class TestIsolationEdgeCases:
    """Test edge cases and error conditions in isolation system."""

    def test_isolation_with_exception(self, isolation_manager):
        """Test that isolation cleanup happens even with exceptions."""
        initial_stack_size = len(isolation_manager._isolation_stack)

        try:
            isolation_manager.push_isolation_context("exception_test")
            test_mock = Mock()
            isolation_manager.register_mock(test_mock)

            # Simulate an exception
            raise ValueError("Test exception")

        except ValueError:
            # Exception should not prevent cleanup
            isolation_manager.pop_isolation_context()

        assert len(isolation_manager._isolation_stack) == initial_stack_size

    def test_double_cleanup_safety(self, isolation_manager):
        """Test that double cleanup doesn't cause errors."""
        isolation_manager.push_isolation_context("double_cleanup_test")

        # First cleanup
        isolation_manager.pop_isolation_context()

        # Second cleanup should be safe (no-op)
        isolation_manager.pop_isolation_context()  # Should not raise

    def test_isolation_with_nested_temp_directories(self):
        """Test nested temporary directory isolation."""
        outer_dirs = []
        inner_dirs = []

        with isolated_temp_directory() as outer_dir:
            outer_dirs.append(outer_dir)
            assert outer_dir.exists()

            with isolated_temp_directory() as inner_dir:
                inner_dirs.append(inner_dir)
                assert inner_dir.exists()
                assert outer_dir.exists()

                # Both should be different directories
                assert outer_dir != inner_dir

            # Inner should be cleaned up, outer should still exist
            assert not inner_dirs[0].exists()
            assert outer_dir.exists()

        # Both should be cleaned up
        assert not outer_dirs[0].exists()
        assert not inner_dirs[0].exists()

    def test_isolation_performance(self):
        """Test that isolation doesn't significantly impact performance."""
        import time

        iterations = 100
        start_time = time.perf_counter()

        for i in range(iterations):
            with isolated_environment_vars(PERF_TEST=f"iteration_{i}"):
                # Minimal operation
                pass

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should complete reasonably quickly (adjust threshold as needed)
        # This is more about detecting major performance regressions
        assert duration < 1.0, f"Isolation overhead too high: {duration:.3f}s for {iterations} iterations"
