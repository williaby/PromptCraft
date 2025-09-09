#!/usr/bin/env python3
"""
VS Code Python Test Integration Verification Script

This script verifies that VS Code can properly discover and run tests
using the configured pytest environment.
"""

# Security: subprocess used for controlled VS Code integration testing - no user input processed
from pathlib import Path
import subprocess
import sys


def run_command(command: list[str], _description: str) -> bool:
    """Run a command and return its result."""

    try:
        result = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )  # nosec B603

        if result.stdout:
            pass
        if result.stderr:
            pass

        return result.returncode == 0
    except Exception:
        return False


def main() -> bool:
    """Main verification function."""

    # Get project root
    Path.cwd()
    venv_path = "/home/byron/.cache/pypoetry/virtualenvs/promptcraft-hybrid-ww18U7e4-py3.11"
    pytest_path = f"{venv_path}/bin/pytest"
    python_path = f"{venv_path}/bin/python"

    # Check paths exist

    if not Path(python_path).exists():
        return False

    if not Path(pytest_path).exists():
        return False

    # Test 1: Python version
    success1 = run_command([python_path, "--version"], "Checking Python version")

    # Test 2: Pytest version
    success2 = run_command([pytest_path, "--version"], "Checking pytest version")

    # Test 3: Test discovery (dry run)
    success3 = run_command(
        [
            pytest_path,
            "--collect-only",
            "-q",
            "tests/unit/test_health_check.py::TestConfigurationStatusModel::test_model_creation_with_valid_data",
        ],
        "Test discovery for specific test",
    )

    # Test 4: Run single test
    success4 = run_command(
        [
            pytest_path,
            "tests/unit/test_health_check.py::TestConfigurationStatusModel::test_model_creation_with_valid_data",
            "-v",
            "--no-cov",  # Skip coverage for this verification
        ],
        "Running single test without coverage",
    )

    # Summary
    results = [
        ("Python version check", success1),
        ("Pytest version check", success2),
        ("Test discovery", success3),
        ("Single test execution", success4),
    ]

    all_passed = True
    for _test_name, passed in results:
        if not passed:
            all_passed = False

    return bool(all_passed)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
