#!/usr/bin/env python3
"""
VS Code Python Test Integration Verification Script

This script verifies that VS Code can properly discover and run tests
using the configured pytest environment.
"""

# Security: subprocess used for controlled VS Code integration testing - no user input processed
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return its result."""
    print(f"\n🔍 {description}")  # noqa: T201
    print(f"Command: {' '.join(command)}")  # noqa: T201

    try:
        result = subprocess.run(  # noqa: S603
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )  # nosec B603

        print(f"Exit code: {result.returncode}")  # noqa: T201
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")  # noqa: T201
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")  # noqa: T201

        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")  # noqa: T201
        return False


def main() -> bool:
    """Main verification function."""
    print("🧪 VS Code Python Test Integration Verification")  # noqa: T201
    print("=" * 50)  # noqa: T201

    # Get project root
    project_root = Path.cwd()
    venv_path = "/home/byron/.cache/pypoetry/virtualenvs/promptcraft-hybrid-ww18U7e4-py3.11"
    pytest_path = f"{venv_path}/bin/pytest"
    python_path = f"{venv_path}/bin/python"

    # Check paths exist
    print(f"📁 Project root: {project_root}")  # noqa: T201
    print(f"🐍 Python path: {python_path}")  # noqa: T201
    print(f"🧪 Pytest path: {pytest_path}")  # noqa: T201

    if not Path(python_path).exists():
        print("❌ Python executable not found!")  # noqa: T201
        return False

    if not Path(pytest_path).exists():
        print("❌ Pytest executable not found!")  # noqa: T201
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
    print("\n📊 Summary")  # noqa: T201
    print("=" * 20)  # noqa: T201
    results = [
        ("Python version check", success1),
        ("Pytest version check", success2),
        ("Test discovery", success3),
        ("Single test execution", success4),
    ]

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")  # noqa: T201
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! VS Code should be able to discover and run tests.")  # noqa: T201
        print("\nNext steps:")  # noqa: T201
        print("1. Reload VS Code window (Ctrl+Shift+P -> 'Developer: Reload Window')")  # noqa: T201
        print("2. Open Test Explorer (Ctrl+Shift+P -> 'Test: Focus on Test Explorer View')")  # noqa: T201
        print("3. Tests should appear in the Test Explorer")  # noqa: T201
        print("4. You can run individual tests by clicking the play button")  # noqa: T201
        return True
    print("\n❌ Some tests failed. Check the error messages above.")  # noqa: T201
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
