#!/usr/bin/env python3
"""
Scheduled Testing Manager for PromptCraft

This script manages scheduled testing execution, both locally and in CI/CD.
It provides configuration management, test execution, and reporting capabilities.
"""

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ScheduleManager:
    """Main class for managing scheduled testing."""

    def __init__(self, config_path: Path | None = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "testing-schedule.json"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load testing schedule configuration."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def list_schedules(self) -> None:
        """List all available testing schedules."""
        print("Available Testing Schedules:")
        print("=" * 50)

        for schedule_name, schedule_config in self.config["schedules"].items():
            enabled = "✅" if schedule_config.get("enabled", False) else "❌"
            print(f"{enabled} {schedule_name}")
            print(f"   Description: {schedule_config.get('description', 'No description')}")
            print(f"   Cron: {schedule_config.get('cron', 'Not scheduled')}")
            print(f"   Components: {len(schedule_config.get('components', []))}")
            print()

    def list_components(self) -> None:
        """List all available test components."""
        print("Available Test Components:")
        print("=" * 50)

        for component_name, component_config in self.config["test_components"].items():
            critical = "🔴" if component_config.get("critical", False) else "🟡"
            requires_app = " (requires app)" if component_config.get("requires_app", False) else ""

            print(f"{critical} {component_name}{requires_app}")
            print(f"   Command: {component_config.get('command', 'No command')}")
            print(f"   Timeout: {component_config.get('timeout_minutes', 'No timeout')} minutes")
            print(f"   Retries: {component_config.get('retry_count', 0)}")
            print()

    def validate_config(self) -> bool:
        """Validate the configuration file."""
        logger.info("Validating configuration...")

        errors = []

        # Check required top-level keys
        required_keys = ["schedules", "test_components", "notification_channels", "thresholds", "global_settings"]
        for key in required_keys:
            if key not in self.config:
                errors.append(f"Missing required key: {key}")

        # Validate schedules
        for schedule_name, schedule_config in self.config.get("schedules", {}).items():
            # Check components exist
            for component in schedule_config.get("components", []):
                if component not in self.config.get("test_components", {}):
                    errors.append(f"Schedule '{schedule_name}' references unknown component: {component}")

        # Validate test components
        for component_name, component_config in self.config.get("test_components", {}).items():
            if "command" not in component_config:
                errors.append(f"Component '{component_name}' missing required 'command' field")

        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        logger.info("Configuration validation passed ✅")
        return True

    def run_schedule(self, schedule_name: str, dry_run: bool = False) -> bool:
        """Run a specific testing schedule."""
        if schedule_name not in self.config["schedules"]:
            logger.error(f"Schedule '{schedule_name}' not found")
            return False

        schedule_config = self.config["schedules"][schedule_name]

        if not schedule_config.get("enabled", False):
            logger.warning(f"Schedule '{schedule_name}' is disabled")
            return False

        logger.info(f"Running schedule: {schedule_name}")
        logger.info(f"Description: {schedule_config.get('description', 'No description')}")

        components = schedule_config.get("components", [])
        results = {}

        # Check if we need to start the application
        requires_app = any(
            self.config["test_components"].get(comp, {}).get("requires_app", False) for comp in components
        )

        app_process = None
        if requires_app and not dry_run:
            logger.info("Starting application for tests that require it...")
            app_process = self._start_application()
            if app_process:
                time.sleep(15)  # Wait for application to start
            else:
                logger.error("Failed to start application")
                return False

        try:
            # Execute components
            for component_name in components:
                if component_name not in self.config["test_components"]:
                    logger.error(f"Component '{component_name}' not found")
                    results[component_name] = {"success": False, "error": "Component not found"}
                    continue

                component_config = self.config["test_components"][component_name]
                result = self._run_component(component_name, component_config, dry_run)
                results[component_name] = result

                # If critical component fails, stop execution
                if component_config.get("critical", False) and not result["success"]:
                    logger.error(f"Critical component '{component_name}' failed, stopping execution")
                    break

            # Generate report
            self._generate_report(schedule_name, results)

            # Check if schedule passed
            critical_failures = [
                name
                for name, result in results.items()
                if not result["success"] and self.config["test_components"].get(name, {}).get("critical", False)
            ]

            success = len(critical_failures) == 0

            if success:
                logger.info(f"Schedule '{schedule_name}' completed successfully ✅")
            else:
                logger.error(
                    f"Schedule '{schedule_name}' failed due to critical component failures: {critical_failures}",
                )

            return success

        finally:
            # Clean up application process
            if app_process:
                logger.info("Stopping application...")
                app_process.terminate()
                try:
                    app_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    app_process.kill()

    def _start_application(self) -> subprocess.Popen | None:
        """Start the application in the background."""
        try:
            process = subprocess.Popen(
                ["poetry", "run", "python", "-m", "src.main"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return process
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return None

    def _run_component(self, component_name: str, component_config: dict[str, Any], dry_run: bool) -> dict[str, Any]:
        """Run a single test component."""
        command = component_config["command"]
        timeout_minutes = component_config.get("timeout_minutes", 60)
        retry_count = component_config.get("retry_count", 0)

        logger.info(f"Running component: {component_name}")
        logger.info(f"Command: {command}")

        if dry_run:
            logger.info("(DRY RUN - not actually executing)")
            return {"success": True, "output": "Dry run - not executed", "duration": 0}

        start_time = time.time()

        for attempt in range(retry_count + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{retry_count}")

            try:
                result = subprocess.run(
                    command.split(),
                    check=False,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=timeout_minutes * 60,
                )

                duration = time.time() - start_time

                if result.returncode == 0:
                    logger.info(f"Component '{component_name}' completed successfully ✅")
                    return {
                        "success": True,
                        "output": result.stdout,
                        "error": result.stderr,
                        "duration": duration,
                        "attempts": attempt + 1,
                    }
                logger.warning(f"Component '{component_name}' failed with return code {result.returncode}")
                if attempt == retry_count:  # Last attempt
                    return {
                        "success": False,
                        "output": result.stdout,
                        "error": result.stderr,
                        "duration": duration,
                        "attempts": attempt + 1,
                        "return_code": result.returncode,
                    }

            except subprocess.TimeoutExpired:
                logger.error(f"Component '{component_name}' timed out after {timeout_minutes} minutes")
                if attempt == retry_count:  # Last attempt
                    return {
                        "success": False,
                        "error": f"Timeout after {timeout_minutes} minutes",
                        "duration": timeout_minutes * 60,
                        "attempts": attempt + 1,
                    }
            except Exception as e:
                logger.error(f"Component '{component_name}' failed with exception: {e}")
                if attempt == retry_count:  # Last attempt
                    return {
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - start_time,
                        "attempts": attempt + 1,
                    }

        # Should not reach here
        return {"success": False, "error": "Unknown error", "duration": 0, "attempts": retry_count + 1}

    def _generate_report(self, schedule_name: str, results: dict[str, dict[str, Any]]) -> None:
        """Generate a test execution report."""
        report_file = (
            self.project_root / f'schedule-report-{schedule_name}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.md'
        )

        total_components = len(results)
        successful_components = sum(1 for result in results.values() if result["success"])
        failed_components = total_components - successful_components
        total_duration = sum(result.get("duration", 0) for result in results.values())

        with open(report_file, "w") as f:
            f.write(f"# Schedule Execution Report: {schedule_name}\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n")
            f.write(f"**Schedule**: {schedule_name}\n")
            f.write(f"**Total Duration**: {total_duration:.1f} seconds\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total Components**: {total_components}\n")
            f.write(f"- **Successful**: {successful_components} ✅\n")
            f.write(f"- **Failed**: {failed_components} ❌\n")
            f.write(f"- **Success Rate**: {(successful_components/total_components*100):.1f}%\n\n")

            f.write("## Component Results\n\n")
            for component_name, result in results.items():
                status = "✅" if result["success"] else "❌"
                duration = result.get("duration", 0)
                attempts = result.get("attempts", 1)

                f.write(f"### {status} {component_name}\n")
                f.write(f"- **Duration**: {duration:.1f}s\n")
                f.write(f"- **Attempts**: {attempts}\n")

                if not result["success"]:
                    f.write(f"- **Error**: {result.get('error', 'Unknown error')}\n")
                    if "return_code" in result:
                        f.write(f"- **Return Code**: {result['return_code']}\n")

                f.write("\n")

        logger.info(f"Report generated: {report_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PromptCraft Scheduled Testing Manager")
    parser.add_argument("--config", type=Path, help="Path to configuration file")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List schedules command
    subparsers.add_parser("list-schedules", help="List available testing schedules")

    # List components command
    subparsers.add_parser("list-components", help="List available test components")

    # Validate config command
    subparsers.add_parser("validate", help="Validate configuration file")

    # Run schedule command
    run_parser = subparsers.add_parser("run", help="Run a testing schedule")
    run_parser.add_argument("schedule", help="Schedule name to run")
    run_parser.add_argument("--dry-run", action="store_true", help="Show what would be executed without running")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = ScheduleManager(args.config)

    if args.command == "list-schedules":
        manager.list_schedules()
    elif args.command == "list-components":
        manager.list_components()
    elif args.command == "validate":
        success = manager.validate_config()
        sys.exit(0 if success else 1)
    elif args.command == "run":
        success = manager.run_schedule(args.schedule, args.dry_run)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
