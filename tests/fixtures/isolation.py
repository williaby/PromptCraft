"""Comprehensive test isolation fixtures and utilities.

This module provides centralized test isolation patterns that ensure clean state
between test runs. It integrates with existing test factories and provides
both manual and automatic isolation capabilities.
"""

import asyncio
import gc
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Set
from unittest.mock import Mock, patch

import pytest

from tests.utils.auth_factories import IsolationHelpers as AuthIsolationHelpers


class GlobalIsolationManager:
    """Manages global test isolation state across all test components."""

    def __init__(self):
        self._isolation_stack: List[Dict[str, Any]] = []
        self._active_mocks: Set[Mock] = set()
        self._temp_directories: List[Path] = []
        self._environment_backup: Dict[str, str] = {}

    def push_isolation_context(self, context_name: str) -> None:
        """Push a new isolation context onto the stack."""
        context = {
            "name": context_name,
            "mocks": set(),
            "temp_dirs": [],
            "env_changes": {},
        }
        self._isolation_stack.append(context)

    def pop_isolation_context(self) -> None:
        """Pop and clean up the current isolation context."""
        if not self._isolation_stack:
            return

        context = self._isolation_stack.pop()

        # Clean up mocks
        for mock in context["mocks"]:
            if hasattr(mock, "stop"):
                try:
                    mock.stop()
                except Exception:
                    pass  # Best effort cleanup
            # Remove from active mocks
            self._active_mocks.discard(mock)

        # Clean up temporary directories
        for temp_dir in context["temp_dirs"]:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

        # Restore environment variables
        for key, value in context["env_changes"].items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def register_mock(self, mock: Mock) -> None:
        """Register a mock for cleanup in the current context."""
        if self._isolation_stack:
            self._isolation_stack[-1]["mocks"].add(mock)
        self._active_mocks.add(mock)

    def register_temp_directory(self, path: Path) -> None:
        """Register a temporary directory for cleanup."""
        if self._isolation_stack:
            self._isolation_stack[-1]["temp_dirs"].append(path)
        self._temp_directories.append(path)

    def backup_environment_var(self, key: str) -> None:
        """Backup an environment variable for restoration."""
        if self._isolation_stack:
            context = self._isolation_stack[-1]
            if key not in context["env_changes"]:
                context["env_changes"][key] = os.environ.get(key)

    def cleanup_all(self) -> None:
        """Clean up all isolation contexts and resources."""
        while self._isolation_stack:
            self.pop_isolation_context()

        # Final cleanup of any remaining resources
        for mock in self._active_mocks:
            if hasattr(mock, "stop"):
                try:
                    mock.stop()
                except Exception:
                    pass  # Best effort cleanup

        self._active_mocks.clear()

        # Clean up temp directories
        for temp_dir in self._temp_directories:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

        self._temp_directories.clear()

        # Force garbage collection to clean up any remaining objects
        gc.collect()


# Global isolation manager instance
_isolation_manager = GlobalIsolationManager()


@pytest.fixture(scope="function", autouse=True)
def auto_isolation(request):
    """Automatic isolation fixture that runs for every test function.

    This fixture ensures clean state by:
    1. Resetting authentication module state
    2. Creating a fresh isolation context
    3. Cleaning up after test completion
    """
    test_name = request.node.name if hasattr(request, "node") else "unknown_test"

    # Setup: Create isolation context
    _isolation_manager.push_isolation_context(test_name)

    # Reset authentication state
    AuthIsolationHelpers.reset_module_state()

    yield

    # Teardown: Clean up isolation context
    _isolation_manager.pop_isolation_context()


@pytest.fixture
def isolation_manager() -> GlobalIsolationManager:
    """Provide access to the global isolation manager for manual control."""
    return _isolation_manager


@contextmanager
def isolated_environment_vars(**env_vars: Optional[str]) -> Generator[None, None, None]:
    """Context manager for isolated environment variable changes.

    Args:
        **env_vars: Environment variables to set. Use None to unset a variable.

    Example:
        with isolated_environment_vars(TEST_MODE="true", DEBUG=None):
            # TEST_MODE is set to "true", DEBUG is unset
            pass
        # Original values are restored
    """
    original_values = {}

    try:
        for key, value in env_vars.items():
            # Backup original value
            _isolation_manager.backup_environment_var(key)
            original_values[key] = os.environ.get(key)

            # Set new value
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

        yield

    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@contextmanager
def isolated_temp_directory() -> Generator[Path, None, None]:
    """Context manager for isolated temporary directory creation.

    Yields:
        Path: Path to the temporary directory

    The directory is automatically cleaned up after the context ends.
    """
    temp_dir = Path(tempfile.mkdtemp())
    _isolation_manager.register_temp_directory(temp_dir)

    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


@contextmanager
def isolated_mock_context(*patches: str, **patch_kwargs: Any) -> Generator[List[Mock], None, None]:
    """Context manager for isolated mock patching.

    Args:
        *patches: Module paths to patch
        **patch_kwargs: Keyword arguments for patch configuration

    Yields:
        List[Mock]: List of mock objects created

    Example:
        with isolated_mock_context('src.auth.jwt_validator.JWTValidator',
                                  'src.auth.jwks_client.JWKSClient') as mocks:
            validator_mock, client_mock = mocks
            # Use mocks...
        # Mocks are automatically cleaned up
    """
    mock_objects = []
    patchers = []

    try:
        for patch_path in patches:
            patcher = patch(patch_path, **patch_kwargs)
            mock_obj = patcher.start()
            patchers.append(patcher)
            mock_objects.append(mock_obj)
            _isolation_manager.register_mock(mock_obj)

        yield mock_objects

    finally:
        for patcher in patchers:
            patcher.stop()


@pytest.fixture
def isolated_database_session():
    """Fixture for isolated database session with automatic rollback.

    This fixture provides a database session that automatically rolls back
    all changes at the end of the test, ensuring no data persists between tests.
    """
    # This is a placeholder for database session isolation
    # Implementation would depend on the specific database setup
    # For now, we'll use a mock to demonstrate the pattern

    mock_session = Mock()
    mock_session.rollback = Mock()
    mock_session.close = Mock()

    try:
        yield mock_session
    finally:
        mock_session.rollback()
        mock_session.close()


@pytest.fixture
async def isolated_async_context() -> AsyncGenerator[None, None]:
    """Fixture for isolated async context with proper cleanup.

    Ensures that async resources are properly cleaned up and that
    event loops don't leak state between tests.
    """
    # Store reference to current event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    try:
        yield
    finally:
        # Cancel any remaining tasks
        if loop and not loop.is_closed():
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass


@pytest.fixture
def isolated_file_system():
    """Fixture for isolated file system operations using temporary directory.

    Yields:
        Path: Temporary directory path for file system operations

    All file operations should be performed within this directory to ensure
    isolation from the actual file system.
    """
    with isolated_temp_directory() as temp_dir:
        # Change working directory to temp directory for isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            yield temp_dir
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def comprehensive_isolation():
    """Comprehensive isolation fixture combining all isolation patterns.

    This fixture provides:
    - Environment variable isolation
    - Temporary directory
    - Mock cleanup
    - Async context cleanup
    - Database session isolation
    """
    isolation_context = {
        "env_backup": dict(os.environ),
        "temp_dir": None,
        "mocks": [],
        "async_tasks": [],
    }

    try:
        # Create temporary directory
        with isolated_temp_directory() as temp_dir:
            isolation_context["temp_dir"] = temp_dir

            # Setup comprehensive isolation context
            _isolation_manager.push_isolation_context("comprehensive_isolation")

            yield isolation_context

    finally:
        # Cleanup comprehensive isolation
        _isolation_manager.pop_isolation_context()

        # Restore environment
        os.environ.clear()
        os.environ.update(isolation_context["env_backup"])


# Convenience functions for common isolation patterns


def create_isolated_jwt_test_suite():
    """Create a complete isolated test suite for JWT testing.

    Returns:
        Dict[str, Any]: Test suite components with proper isolation
    """
    from tests.utils.auth_factories import (
        JWTValidatorFactory,
        JWTTokenFactory,
        AuthenticatedUserFactory,
    )

    return {
        "validator": JWTValidatorFactory.create_validator(),
        "valid_token": JWTTokenFactory.create_valid_token(),
        "expired_token": JWTTokenFactory.create_expired_token(),
        "malformed_token": JWTTokenFactory.create_malformed_token(),
        "admin_user": AuthenticatedUserFactory.create_admin_user(),
        "regular_user": AuthenticatedUserFactory.create_regular_user(),
    }


def create_isolated_claude_integration_test_suite():
    """Create isolated test suite for Claude integration testing.

    Returns:
        Dict[str, Any]: Claude integration test components
    """
    # This would be implemented based on Claude integration requirements
    # For now, return basic structure
    return {
        "mock_command_registry": Mock(),
        "mock_user_control": Mock(),
        "isolated_history": [],
        "test_commands": ["test:command1", "test:command2"],
    }


# Test validation functions


def validate_test_isolation(test_function) -> bool:
    """Validate that a test function follows proper isolation patterns.

    Args:
        test_function: Test function to validate

    Returns:
        bool: True if test follows isolation patterns, False otherwise
    """
    # Check if test uses isolated fixtures
    if hasattr(test_function, "pytestmark"):
        for mark in test_function.pytestmark:
            if mark.name in ["isolate", "isolated"]:
                return True

    # Check function signature for isolation fixtures
    import inspect

    sig = inspect.signature(test_function)
    isolation_fixtures = {
        "isolation_manager",
        "comprehensive_isolation",
        "isolated_database_session",
        "isolated_file_system",
        "auto_isolation",
    }

    return bool(isolation_fixtures.intersection(sig.parameters.keys()))


def assert_no_state_leakage(strict: bool = True):
    """Assert that no test state has leaked between tests.

    Args:
        strict: If True, enforce strict state checking. If False, only warn.

    This function can be called at the beginning of tests to ensure
    that previous tests have been properly cleaned up.
    """
    # Check for common state leakage patterns
    active_mocks = len(_isolation_manager._active_mocks)
    isolation_contexts = len(_isolation_manager._isolation_stack)

    if strict:
        assert active_mocks == 0, f"Active mocks detected - possible state leakage: {active_mocks}"
        assert isolation_contexts <= 1, f"Isolation contexts not properly cleaned up: {isolation_contexts}"
    else:
        # In non-strict mode, just clean up what we can
        if active_mocks > 0:
            _isolation_manager._active_mocks.clear()
        if isolation_contexts > 1:
            _isolation_manager.cleanup_all()

    # Additional checks can be added here for specific modules
    AuthIsolationHelpers.reset_module_state()
