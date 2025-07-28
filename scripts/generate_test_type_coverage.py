#!/usr/bin/env python3
"""
Generate Test-Type-Specific Coverage Reports

This script generates pytest-cov HTML reports for each test type
to provide function and class level coverage detail.

Usage:
    python scripts/generate_test_type_coverage.py
    python scripts/generate_test_type_coverage.py --test-type unit
    python scripts/generate_test_type_coverage.py --test-type auth,integration
"""

import argparse

# Security: subprocess used for controlled test type coverage generation - no user input processed
import subprocess
from pathlib import Path


class TestTypeCoverageGenerator:
    """Generates coverage reports for specific test types."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage" / "by-type"

    def generate_for_test_types(self, test_types: list[str] | None = None) -> None:
        """Generate coverage reports for specified test types."""
        if test_types is None:
            test_types = ["unit", "auth", "integration", "security", "performance"]

        for test_type in test_types:
            if self._test_type_has_tests(test_type):
                print(f"📊 Generating {test_type} test coverage report...")
                self._generate_test_type_coverage(test_type)
            else:
                print(f"⚠️  No tests found for {test_type} test type")

    def _test_type_has_tests(self, test_type: str) -> bool:
        """Check if the test type has any test files."""
        test_dir = self.project_root / "tests" / test_type
        if not test_dir.exists():
            return False

        # Check for any Python test files
        test_files = list(test_dir.glob("**/test_*.py"))
        return len(test_files) > 0

    def _generate_test_type_coverage(self, test_type: str) -> None:
        """Generate coverage report for a specific test type."""
        test_dir = self.project_root / "tests" / test_type
        output_dir = self.reports_dir / test_type

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build pytest command
        cmd = [
            "poetry",
            "run",
            "pytest",
            str(test_dir),
            "--cov=src",
            "--cov-branch",
            f"--cov-report=html:{output_dir}",
            "--cov-report=term-missing",
            "-v",
            "--tb=short",
        ]

        try:
            # Run pytest with coverage
            result = subprocess.run(
                cmd,
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                print(f"   ✅ Generated {test_type} coverage report at {output_dir}")
                self._add_navigation_to_report(test_type, output_dir)
            else:
                print(f"   ❌ Failed to generate {test_type} coverage report")
                print(f"   Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"   ⏰ {test_type} coverage generation timed out after 5 minutes")
        except Exception as e:
            print(f"   ❌ Error generating {test_type} coverage: {e}")

    def _add_navigation_to_report(self, test_type: str, output_dir: Path) -> None:
        """Add navigation links to the generated report."""
        index_file = output_dir / "index.html"
        class_file = output_dir / "class_index.html"
        function_file = output_dir / "function_index.html"

        if not index_file.exists():
            return

        # Check what reports were generated
        has_class = class_file.exists()
        has_function = function_file.exists()

        if not (has_class or has_function):
            return

        # Read current content
        try:
            content = index_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"   ⚠️  Could not add navigation to {test_type}: {e}")
            return

        # Add navigation links after the header
        navigation_html = self._generate_navigation_html(test_type, has_class, has_function)

        # Find insertion point (after the first h1)
        h1_end = content.find("</h1>")
        if h1_end != -1:
            insertion_point = h1_end + 5
            new_content = content[:insertion_point] + "\n" + navigation_html + "\n" + content[insertion_point:]

            # Write updated content
            index_file.write_text(new_content, encoding="utf-8")
            print(f"   🔗 Added function/class navigation to {test_type} report")

    def _generate_navigation_html(self, test_type: str, has_class: bool, has_function: bool) -> str:
        """Generate navigation HTML for the report."""
        links = []

        if has_function:
            links.append('<a href="function_index.html" class="nav-link">📋 Function Coverage</a>')
        if has_class:
            links.append('<a href="class_index.html" class="nav-link">📦 Class Coverage</a>')

        if not links:
            return ""

        test_icons = {"unit": "🧪", "auth": "🔐", "integration": "🔗", "security": "🛡️", "performance": "🏃‍♂️"}
        icon = test_icons.get(test_type, "📋")

        return f"""
        <div class="test-type-navigation" style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007acc;">
            <h3 style="margin: 0 0 10px 0; color: #007acc;">{icon} {test_type.capitalize()} Test Coverage Views</h3>
            <div style="display: flex; gap: 15px; flex-wrap: wrap; align-items: center;">
                {" • ".join(links)}
            </div>
            <style>
                .nav-link {{
                    padding: 8px 16px; background: #007acc; color: white;
                    text-decoration: none; border-radius: 4px; transition: background 0.2s;
                }}
                .nav-link:hover {{
                    background: #005a99;
                }}
            </style>
        </div>"""


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate test-type-specific coverage reports")
    parser.add_argument(
        "--test-type",
        help="Comma-separated list of test types to generate (e.g., unit,auth,integration)",
    )

    args = parser.parse_args()

    test_types = None
    if args.test_type:
        test_types = [t.strip() for t in args.test_type.split(",")]

    generator = TestTypeCoverageGenerator()
    generator.generate_for_test_types(test_types)


if __name__ == "__main__":
    main()
