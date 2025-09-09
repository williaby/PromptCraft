#!/usr/bin/env python3
"""
Pytest Coverage Hook Plugin

This pytest plugin automatically detects when tests are run with coverage
and triggers the enhanced coverage report generation. It integrates seamlessly
with VS Code's "Run Tests with Coverage" workflow.

Features:
- Automatically detects coverage runs via pytest hooks
- Triggers enhanced report generation after test completion
- Works with both CLI and VS Code test execution
- No manual intervention required
- Handles errors gracefully

Usage:
This plugin is automatically loaded when pytest runs if the pytest_plugins
directory is in the Python path and the plugin is installed.

Integration with VS Code:
- VS Code runs: pytest --cov=src --cov-report=html --cov-report=xml
- Plugin detects coverage arguments
- After tests complete, plugin triggers report generation
- Enhanced reports appear in reports/coverage/ directory
"""

import contextlib
import os
from pathlib import Path
import subprocess  # nosec B404  # Required for coverage hook integration
import sys


def pytest_configure(config: object) -> None:
    """
    Called after command line options have been parsed.
    Register custom markers and check if coverage is enabled.
    """
    # Register our custom marker
    config.addinivalue_line("markers", "coverage_hook: Mark tests that should trigger coverage report generation")

    # Store coverage detection for later use
    cov_enabled = False
    try:
        cov_enabled = (
            config.getoption("--cov") is not None
            or config.getoption("--cov-report") is not None
            or any("--cov" in str(arg) for arg in config.invocation_params.args)
        )
    except ValueError:
        # pytest-cov not installed or --cov option not available
        # Check command line args directly
        cov_enabled = any("--cov" in str(arg) for arg in config.invocation_params.args)

    config._coverage_enabled = cov_enabled

    if cov_enabled:
        pass


def pytest_sessionfinish(session: object, exitstatus: int) -> None:  # noqa: ARG001  # Pytest hook signature
    """
    Called after whole test run finished, right before returning the exit status.
    This is the perfect place to trigger coverage report generation.
    """
    # Only run if coverage was enabled and tests actually ran
    if not getattr(session.config, "_coverage_enabled", False):
        return

    # Skip if session had collection errors or no tests ran
    if hasattr(session, "testscollected") and session.testscollected == 0:
        return

    with contextlib.suppress(subprocess.TimeoutExpired, Exception):
        # Find the project root directory
        project_root = Path.cwd()
        while project_root.parent != project_root:
            if (project_root / "pyproject.toml").exists():
                break
            project_root = project_root.parent
        else:
            # Fallback to current directory
            project_root = Path.cwd()

        # Path to the coverage hook script
        hook_script = project_root / "scripts" / "vscode_coverage_hook.py"

        if not hook_script.exists():
            return

        # Execute the coverage hook script
        result = subprocess.run(  # noqa: S603  # nosec B603  # Controlled Python script execution with timeout
            [sys.executable, str(hook_script)],
            check=False,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
        )

        if result.returncode == 0:
            # Print any output from the hook (but suppress verbose output)
            if result.stdout and "✅ Coverage reports updated" in result.stdout:
                pass
        elif result.stderr:
            pass


def pytest_runtest_makereport(item: object, call: object) -> None:
    """
    Called to create a test report for each phase of a test (setup, call, teardown).
    We can use this to track test execution context.
    """
    # Set coverage context based on test path for better tracking
    if call.when == "call" and hasattr(item.config, "_coverage_enabled") and item.config._coverage_enabled:
        # Extract test type from test path for coverage context
        test_path = str(item.fspath)

        if "/tests/unit/" in test_path:
            context = "unit"
        elif "/tests/auth/" in test_path:
            context = "auth"
        elif "/tests/integration/" in test_path:
            context = "integration"
        elif "/tests/security/" in test_path:
            context = "security"
        elif "/tests/performance/" in test_path:
            context = "performance"
        elif "/tests/stress/" in test_path:
            context = "stress"
        elif "/tests/contract/" in test_path:
            context = "contract"
        elif "/tests/examples/" in test_path:
            context = "examples"
        else:
            context = "other"

        # Set environment variable for coverage context (matches conftest.py)
        os.environ["COVERAGE_CONTEXT"] = context


# Plugin registration for pytest
# This is handled via conftest.py instead


# For direct execution testing
if __name__ == "__main__":
    pass
