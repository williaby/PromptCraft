#!/usr/bin/env python3
"""
VS Code Coverage Integration v2

This script provides seamless integration with VS Code's "Run Tests with Coverage" workflow.
It monitors for coverage file changes and automatically generates enhanced reports.

Key Features:
- Monitors .coverage file changes (VS Code always generates this)
- Triggers XML generation if VS Code doesn't create it
- Runs both old and new automation systems
- Provides real-time feedback

Usage:
  python scripts/vscode_coverage_integration_v2.py --watch    # Run in background
  python scripts/vscode_coverage_integration_v2.py --manual  # Manual trigger
"""

import argparse

# Security: subprocess used for controlled VS Code coverage integration - no user input processed
import subprocess
import sys
import time
from pathlib import Path


class VSCodeCoverageIntegration:
    """Handles VS Code coverage workflow integration."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.coverage_file = self.project_root / ".coverage"
        self.coverage_xml = self.project_root / "coverage.xml"
        self.junit_xml = self.project_root / "reports" / "junit.xml"
        self.htmlcov_dir = self.project_root / "htmlcov"

    def is_fresh_coverage_data(self, max_age_seconds: int = 300) -> tuple[bool, str]:
        """Check if we have fresh coverage data."""
        if not self.coverage_file.exists():
            return False, "No .coverage file found"

        age = time.time() - self.coverage_file.stat().st_mtime
        if age > max_age_seconds:
            return False, f"Coverage data is {age/60:.1f} minutes old"

        return True, f"Fresh coverage data ({age:.0f}s old)"

    def ensure_xml_reports(self) -> bool:
        """Ensure XML reports are generated from .coverage data."""
        try:
            print("📊 Ensuring XML reports are generated...")

            # Generate XML if it doesn't exist or is older than .coverage
            need_xml = (
                not self.coverage_xml.exists() or self.coverage_xml.stat().st_mtime < self.coverage_file.stat().st_mtime
            )

            if need_xml:
                print("🔄 Generating coverage.xml from .coverage data...")
                result = subprocess.run(
                    ["poetry", "run", "coverage", "xml", "-o", "coverage.xml"],
                    check=False,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"⚠️ Warning: Failed to generate coverage.xml: {result.stderr}")
                    return False
                print("✅ Generated coverage.xml")

            # Create HTML if it doesn't exist or is older than .coverage
            need_html = (
                not self.htmlcov_dir.exists()
                or not (self.htmlcov_dir / "index.html").exists()
                or (self.htmlcov_dir / "index.html").stat().st_mtime < self.coverage_file.stat().st_mtime
            )

            if need_html:
                print("🔄 Generating HTML coverage reports...")
                result = subprocess.run(
                    ["poetry", "run", "coverage", "html", "-d", "htmlcov"],
                    check=False,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"⚠️ Warning: Failed to generate HTML: {result.stderr}")
                else:
                    print("✅ Generated HTML coverage reports")

            return True

        except Exception as e:
            print(f"❌ Error ensuring XML reports: {e}")
            return False

    def run_automation_scripts(self) -> bool:
        """Run the enhanced automation scripts."""
        success = True

        # Try new v2 system first
        try:
            print("🚀 Running new automation system (v2)...")
            result = subprocess.run(
                [sys.executable, "scripts/simplified_coverage_automation_v2.py", "--force"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=45,
            )

            if result.returncode == 0:
                print("✅ New automation system completed")
            else:
                print(f"⚠️ New automation system had issues: {result.stderr}")
                success = False
        except Exception as e:
            print(f"⚠️ New automation system failed: {e}")
            success = False

        # Always run the original system for simplified_report.html
        try:
            print("🔄 Running original automation system...")
            result = subprocess.run(
                [sys.executable, "scripts/simplified_coverage_automation.py", "--force"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("✅ Original automation system completed")
            else:
                print(f"⚠️ Original automation system had issues: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Original automation system failed: {e}")

        return success

    def update_reports(self) -> bool:
        """Complete workflow to update all coverage reports."""
        print("📊 VS Code Coverage Integration")
        print("=" * 50)

        # Check for fresh data
        fresh, message = self.is_fresh_coverage_data()
        print(f"📊 Coverage status: {message}")

        if not fresh:
            print("ℹ️ No fresh coverage data found")  # noqa: RUF001
            return False

        # Ensure all needed files exist
        if not self.ensure_xml_reports():
            print("⚠️ Could not generate XML reports, continuing anyway...")

        # Run automation scripts
        success = self.run_automation_scripts()

        if success:
            print("\n🎉 Coverage reports updated successfully!")
            print(f"📂 Simplified Report: file://{self.project_root}/reports/coverage/simplified_report.html")
            print(f"📂 Detailed Report: file://{self.project_root}/htmlcov/index.html")
            print(f"📂 Gap Analysis: file://{self.project_root}/reports/coverage/test_gap_analysis.html")
        else:
            print("\n⚠️ Some issues occurred during report generation")

        return success

    def watch_mode(self):
        """Watch for coverage file changes and auto-update."""
        print("👀 Watching for VS Code coverage changes...")
        print("   Press Ctrl+C to stop")

        last_mtime = 0
        if self.coverage_file.exists():
            last_mtime = self.coverage_file.stat().st_mtime

        try:
            while True:
                if self.coverage_file.exists():
                    current_mtime = self.coverage_file.stat().st_mtime
                    if current_mtime > last_mtime:
                        print("\n🔄 Coverage file updated, processing...")
                        self.update_reports()
                        last_mtime = current_mtime
                        print("\n👀 Resuming watch mode...")

                time.sleep(2)  # noqa: S110 - Coverage file change monitoring interval

        except KeyboardInterrupt:
            print("\n👋 Stopping coverage watcher")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="VS Code Coverage Integration")
    parser.add_argument("--watch", action="store_true", help="Watch for coverage changes")
    parser.add_argument("--manual", action="store_true", help="Manual trigger")
    parser.add_argument("--force", action="store_true", help="Force update regardless of age")

    args = parser.parse_args()

    integration = VSCodeCoverageIntegration()

    if args.watch:
        integration.watch_mode()
    elif args.manual or args.force:
        # Override age check if forced
        if args.force:
            integration.is_fresh_coverage_data = lambda max_age=300: (True, "Forced update")  # noqa: ARG005
        integration.update_reports()
    else:
        integration.update_reports()


if __name__ == "__main__":
    main()
