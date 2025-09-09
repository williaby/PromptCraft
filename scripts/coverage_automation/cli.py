"""
Command-line interface for coverage automation.
"""

from pathlib import Path
import subprocess

from .classifier import TestTypeClassifier
from .config import TestPatternConfig
from .renderer import CoverageRenderer
from .watcher import CoverageWatcher


class CoverageAutomationCLI:
    """Command-line interface for coverage automation."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

        # Initialize components
        self.config = TestPatternConfig()
        self.watcher = CoverageWatcher(self.project_root, self.config)
        self.classifier = TestTypeClassifier(self.project_root, self.config)
        self.renderer = CoverageRenderer(self.project_root, self.config, self.classifier)

    def validate_environment(self) -> bool:
        """Validate that the environment is properly configured."""
        try:
            # Check if we're in a Poetry project
            pyproject_file = self.project_root / "pyproject.toml"
            if not pyproject_file.exists():
                print("⚠️  No pyproject.toml found - Poetry may not be configured")
                return False

            # Check if Poetry is available
            result = subprocess.run(
                ["poetry", "--version"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                print("⚠️  Poetry not found - please install Poetry")
                return False

            print("✅ Environment validation passed")
            return True

        except Exception as e:
            print(f"⚠️  Environment validation failed: {e}")
            return False

    def run_automation(self, force_run: bool = False) -> bool:
        """Run the main automation workflow."""
        try:
            print("🤖 Coverage Automation")
            print("=" * 50)

            # Set force run flag if requested
            if force_run:
                self.watcher.force_run = True

            if not self.watcher.detect_vscode_coverage_run():
                print("⚠️  No recent coverage run detected")
                if not force_run:
                    print("   Run 'Run Tests with Coverage' in VS Code first")
                    return False

            print("✅ Recent coverage run detected")
            print("📊 Generating coverage report...")

            # Get contexts and generate reports
            used_contexts = self.watcher.get_coverage_contexts()
            report_path = self.renderer.generate_coverage_reports(used_contexts)

            if report_path:
                print(f"✅ Report generated: {report_path}")
                print(f"🌐 Open in browser: file://{report_path}")
                return True
            print("❌ Failed to generate report")
            return False

        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False
