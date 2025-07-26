#!/usr/bin/env python3
"""
Coverage File Watcher for Automatic Report Updates

This script monitors coverage.xml and junit.xml files for changes and automatically
regenerates coverage reports when VS Code runs tests with coverage.

Features:
- Watches coverage.xml and junit.xml for modifications
- Debounces rapid changes to avoid multiple regenerations
- Runs in background with minimal resource usage
- Automatically triggers generate_test_coverage_fast.py

Usage:
    # Start monitoring in background
    python scripts/coverage_file_watcher.py --daemon

    # Run once and exit
    python scripts/coverage_file_watcher.py --once

    # Stop monitoring
    python scripts/coverage_file_watcher.py --stop
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class CoverageFileWatcher:
    """File watcher for automatic coverage report regeneration."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.coverage_xml = self.project_root / "coverage.xml"
        self.junit_xml = self.project_root / "reports" / "junit.xml"
        self.generator_script = self.project_root / "scripts" / "auto_coverage_report.py"

        # Debouncing
        self.last_update_time = 0
        self.debounce_seconds = 2.0

        # Process management
        self.pid_file = self.project_root / "scripts" / ".coverage_watcher.pid"
        self.running = True

    def get_file_timestamps(self) -> set[float]:
        """Get modification timestamps of watched files."""
        timestamps = set()

        for filepath in [self.coverage_xml, self.junit_xml]:
            if filepath.exists():
                timestamps.add(filepath.stat().st_mtime)

        return timestamps

    def should_regenerate(self, current_timestamps: set[float]) -> bool:
        """Check if reports should be regenerated based on file changes."""
        if not current_timestamps:
            return False

        # Check if any file was modified recently
        latest_modification = max(current_timestamps)

        # Debounce: only regenerate if enough time has passed since last update
        if time.time() - self.last_update_time < self.debounce_seconds:
            return False

        # Check if files were modified after last update
        return latest_modification > self.last_update_time

    def regenerate_reports(self) -> bool:
        """Trigger coverage report regeneration."""
        try:
            print("🔄 Detected coverage data changes - regenerating reports...")

            # Run the generator script quietly
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.generator_script),
                    "--quiet",
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                print("✅ Coverage reports updated automatically")
                self.last_update_time = time.time()
                return True
            print(f"⚠️  Report generation failed: {result.stderr}")
            return False

        except Exception as e:
            print(f"❌ Error regenerating reports: {e}")
            return False

    def create_pid_file(self) -> None:
        """Create PID file for process management."""
        self.pid_file.write_text(str(os.getpid()))

    def remove_pid_file(self) -> None:
        """Remove PID file on exit."""
        if self.pid_file.exists():
            self.pid_file.unlink()

    def signal_handler(self, signum, frame):  # noqa: ARG002
        """Handle shutdown signals gracefully."""
        print(f"\n📴 Received signal {signum} - shutting down coverage watcher...")
        self.running = False
        self.remove_pid_file()
        sys.exit(0)

    def is_already_running(self) -> bool:
        """Check if another watcher instance is already running."""
        if not self.pid_file.exists():
            return False

        try:
            pid = int(self.pid_file.read_text().strip())
            # Check if process is still running
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # Process is dead or PID file is corrupt
            self.pid_file.unlink()
            return False

    def stop_existing_watcher(self) -> bool:
        """Stop any existing watcher process."""
        if not self.pid_file.exists():
            print("📴 No watcher process found to stop")
            return False

        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)  # noqa: S110 - Process shutdown coordination delay

            # Force kill if still running
            import contextlib

            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)  # Process already dead

            self.remove_pid_file()
            print("✅ Stopped existing coverage watcher")
            return True

        except (OSError, ValueError) as e:
            print(f"⚠️  Error stopping watcher: {e}")
            self.remove_pid_file()
            return False

    def watch_once(self) -> bool:
        """Check once for changes and regenerate if needed."""
        current_timestamps = self.get_file_timestamps()

        if self.should_regenerate(current_timestamps):
            return self.regenerate_reports()
        print("ℹ️  No coverage data changes detected")  # noqa: RUF001
        return False

    def watch_continuously(self) -> None:
        """Watch files continuously for changes."""
        if self.is_already_running():
            print("⚠️  Coverage watcher is already running")
            return

        print("👀 Starting coverage file watcher...")
        print(f"📁 Watching: {self.coverage_xml}")
        print(f"📁 Watching: {self.junit_xml}")
        print("🔄 Will auto-regenerate reports when VS Code runs tests with coverage")
        print("📴 Press Ctrl+C to stop")

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Create PID file
        self.create_pid_file()

        # Initialize with current timestamps
        last_timestamps = self.get_file_timestamps()

        try:
            while self.running:
                current_timestamps = self.get_file_timestamps()

                if current_timestamps != last_timestamps:
                    if self.should_regenerate(current_timestamps):
                        self.regenerate_reports()
                    last_timestamps = current_timestamps

                time.sleep(1)  # noqa: S110 - File monitoring polling interval (1 second)

        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        finally:
            self.remove_pid_file()


def main():
    """Main entry point with command line options."""
    parser = argparse.ArgumentParser(
        description="Watch coverage files and auto-regenerate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/coverage_file_watcher.py --daemon     # Start background monitoring
    python scripts/coverage_file_watcher.py --once      # Check once and exit
    python scripts/coverage_file_watcher.py --stop      # Stop existing watcher
        """,
    )

    parser.add_argument(
        "--daemon",
        "-d",
        action="store_true",
        help="Run as daemon process (continuous monitoring)",
    )

    parser.add_argument(
        "--once",
        "-o",
        action="store_true",
        help="Check once for changes and exit",
    )

    parser.add_argument(
        "--stop",
        "-s",
        action="store_true",
        help="Stop any existing watcher process",
    )

    args = parser.parse_args()

    watcher = CoverageFileWatcher()

    if args.stop:
        watcher.stop_existing_watcher()
        return

    if args.once:
        watcher.watch_once()
        return

    # Default to daemon mode
    watcher.watch_continuously()


if __name__ == "__main__":
    main()
