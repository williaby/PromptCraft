#!/usr/bin/env python3
"""
VS Code Coverage Integration Hook

This script is called automatically by VS Code after running tests with coverage.
It triggers the fast coverage report generation to update all HTML reports.

Usage:
- Configured as VS Code task in .vscode/tasks.json
- Can be integrated with pytest plugins
- Supports both automatic and manual execution
- Enhanced with coverage contexts support

Integration Options:
1. VS Code Task: Bound to keyboard shortcut or run manually
2. Pytest Plugin: Automatic execution after test runs
3. File Watcher: Continuous monitoring for changes
"""

from pathlib import Path
import sys
import time


# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

import subprocess  # noqa: E402

from generate_test_coverage_fast import FastCoverageReportGenerator  # noqa: E402


def check_coverage_contexts_enabled():
    """Check if coverage contexts are properly configured."""
    try:
        import tomli

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                config = tomli.load(f)

            coverage_config = config.get("tool", {}).get("coverage", {}).get("run", {})
            dynamic_context = coverage_config.get("dynamic_context")

            if dynamic_context == "test_function":
                print("✅ Coverage contexts enabled - real per-test coverage available")
                return True
            print("ℹ️  Coverage contexts not enabled - using simulation approach")  # noqa: RUF001
            return False
    except Exception as e:
        print(f"⚠️  Could not check coverage context configuration: {e}")
        return False


def wait_for_coverage_files(max_wait_seconds=5):
    """Wait for coverage files to be written after VS Code test run."""
    project_root = Path(__file__).parent.parent
    coverage_xml = project_root / "coverage.xml"
    junit_xml = project_root / "reports" / "junit.xml"

    start_time = time.time()

    # Wait for both files to exist and be recent
    while time.time() - start_time < max_wait_seconds:
        if coverage_xml.exists() and junit_xml.exists():
            # Check if files are recent (within last 30 seconds)
            coverage_age = time.time() - coverage_xml.stat().st_mtime
            junit_age = time.time() - junit_xml.stat().st_mtime

            if coverage_age < 30 and junit_age < 30:
                print(f"✅ Found fresh coverage data (coverage: {coverage_age:.1f}s, junit: {junit_age:.1f}s old)")
                return True

        time.sleep(0.5)  # noqa: S110 - Coverage file availability polling interval

    print("⚠️  Coverage files not found or not recent - continuing anyway")
    return False


def main():
    """Enhanced hook entry point with context checking and file waiting."""
    print("🔄 VS Code Coverage Integration Hook")

    # Check if coverage contexts are enabled
    contexts_enabled = check_coverage_contexts_enabled()

    # Wait for coverage files to be written
    wait_for_coverage_files()

    # Generate fast reports
    generator = FastCoverageReportGenerator(quiet=False)
    fast_success = generator.run(force=False)

    # Generate simplified reports (including simplified_report.html)
    print("🔄 Generating simplified coverage reports...")
    project_root = Path(__file__).parent.parent
    simplified_script = project_root / "scripts" / "simplified_coverage_automation.py"

    try:
        # Security: subprocess used for controlled coverage automation - no user input processed  # noqa: S603
        result = subprocess.run(
            [sys.executable, str(simplified_script)],
            check=False,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        simplified_success = result.returncode == 0
        if not simplified_success:
            print(f"⚠️  Simplified reports failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Error running simplified coverage automation: {e}")
        simplified_success = False

    if fast_success and simplified_success:
        print("✅ All coverage reports updated automatically")
        print("📊 Updated: Fast reports + simplified_report.html")
        if contexts_enabled:
            print("💡 Real per-test coverage data used (contexts enabled)")
        else:
            print("💡 Simulated per-test coverage used (enable contexts for real data)")
    elif fast_success:
        print("✅ Fast coverage reports updated")
        print("⚠️  Simplified reports had issues - check logs")
    else:
        print("⚠️  Coverage reports not updated - run tests with coverage first")
        sys.exit(1)


if __name__ == "__main__":
    main()
