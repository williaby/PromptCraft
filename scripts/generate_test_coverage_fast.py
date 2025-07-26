#!/usr/bin/env python3
"""
Fast Test Coverage Report Generator

Main orchestration script that integrates the modular coverage reporting components
to generate sophisticated HTML reports from VS Code test runs. This replaces the
monolithic vscode_coverage_integration.py with a clean, modular architecture.

Implements the Zen Consensus plan to restore previous sophisticated functionality
while eliminating the 5x test execution inefficiency by using data from a single
VS Code test run.

Features:
- Modular architecture (loader/slicer/renderer components)
- Automatic VS Code integration with "Run Tests with Coverage" workflow
- Sophisticated sortable HTML reports with embedded assets
- File-explorer compatibility (no server required)
- Test type classification without multiple test runs
- Performance optimized for development workflow

Usage:
  # Automatic mode (run after VS Code test execution)
  python scripts/generate_test_coverage_fast.py

  # Force regeneration
  python scripts/generate_test_coverage_fast.py --force

  # Quiet mode (minimal output)
  python scripts/generate_test_coverage_fast.py --quiet
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any

# Import our modular components
from coverage_data_loader import CoverageDataLoader
from html_renderer import HTMLRenderer
from test_type_slicer import TestTypeSlicer


class FastCoverageReportGenerator:
    """Main orchestrator for fast coverage report generation."""

    def __init__(self, project_root: Path | None = None, quiet: bool = False):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage"
        self.quiet = quiet

        # Initialize modular components
        self.loader = CoverageDataLoader(project_root)
        self.slicer = TestTypeSlicer(project_root)
        self.renderer = HTMLRenderer(project_root)

        # Performance tracking
        self.start_time = time.time()

    def log(self, message: str, force: bool = False) -> None:
        """Log message unless in quiet mode."""
        if not self.quiet or force:
            print(message)

    def check_data_freshness(self) -> bool:
        """Check if coverage data exists and is recent."""
        files = self.loader.find_coverage_files()
        coverage_xml = files["coverage_xml"]

        if not coverage_xml or not coverage_xml.exists():
            return False

        # Check if data is recent (within last hour)
        coverage_age = time.time() - coverage_xml.stat().st_mtime
        if coverage_age > 3600:  # 1 hour
            self.log(f"⚠️  Coverage data is {coverage_age/60:.0f} minutes old")

        return True

    def load_and_validate_data(self) -> dict[str, Any] | None:
        """Load and validate coverage and test data."""
        self.log("📊 Loading coverage data from VS Code test run...")

        combined_data = self.loader.get_combined_data()
        if not combined_data:
            self.log("❌ No coverage data found from VS Code test run", force=True)
            self.log("   Please run tests with coverage in VS Code first:", force=True)
            self.log("   • Use 'Run Tests with Coverage' button", force=True)
            self.log("   • Or Command Palette: 'Python: Run Tests With Coverage'", force=True)
            return None

        coverage_data = combined_data["coverage"]
        test_data = combined_data["tests"]

        # Validate data quality
        if coverage_data["overall"]["percentage"] == 0:
            self.log("⚠️  Coverage shows 0% - this may indicate a test execution issue")

        if not test_data or test_data.get("total_tests", 0) == 0:
            self.log("⚠️  No test execution data found - test type analysis will be limited")

        self.log(f"✅ Loaded coverage: {coverage_data['overall']['percentage']:.1f}% overall")
        if test_data:
            self.log(f"🧪 Found {test_data['total_tests']} test executions")

        return combined_data

    def generate_reports(self, combined_data: dict[str, Any]) -> bool:
        """Generate all coverage reports using modular components."""
        try:
            coverage_data = combined_data["coverage"]
            test_data = combined_data["tests"]

            self.log("🔍 Classifying tests by type...")

            # Use slicer to classify tests and get distribution
            test_distribution = self.slicer.get_test_type_distribution(test_data)
            self.log(f"📋 Test distribution: {dict(test_distribution)}")

            # Generate coverage data for each test type
            self.log("📈 Generating test type coverage analysis...")
            test_type_coverage = self.slicer.get_all_test_type_coverage(coverage_data, test_data)

            # Use renderer to generate all HTML reports
            self.log("🎨 Generating HTML reports...")

            # Generate main index page
            main_html = self.renderer.generate_main_index(coverage_data, test_distribution, test_type_coverage)
            main_file = self.reports_dir / "index.html"
            self.renderer.save_html_file(main_html, main_file)

            # Generate by-type index page
            by_type_html = self.renderer.generate_by_type_index(test_distribution, test_type_coverage)
            by_type_dir = self.reports_dir / "by-type"
            by_type_file = by_type_dir / "index.html"
            self.renderer.save_html_file(by_type_html, by_type_file)

            # Generate detailed reports for each test type
            # Include all test types that have coverage, not just those with junit.xml entries
            all_test_types = set(test_distribution.keys()) | set(test_type_coverage.keys())
            
            for test_type in all_test_types:
                count = test_distribution.get(test_type, 0)
                type_coverage = test_type_coverage.get(test_type, {})
                
                # Generate report if there's either test execution data OR coverage data
                if count > 0 or (type_coverage and type_coverage.get("overall", {}).get("lines_covered", 0) > 0):
                    detail_html = self.renderer.generate_test_type_detail(test_type, type_coverage, count)
                    detail_file = by_type_dir / test_type / "index.html"
                    self.renderer.save_html_file(detail_html, detail_file)
                    self.log(f"📊 Generated {test_type} detailed report")

            # Generate coverage gaps analysis report (bonus feature)
            self.log("🔎 Generating coverage analysis...")
            analysis = self.slicer.get_coverage_gaps_analysis(coverage_data, test_data)
            if analysis["recommendations"]:
                self.log("💡 Coverage recommendations:")
                for rec in analysis["recommendations"][:3]:  # Show top 3
                    self.log(f"   • {rec}")

            return True

        except Exception as e:
            self.log(f"❌ Error generating reports: {e}", force=True)
            return False

    def integrate_with_vscode_htmlcov(self) -> None:
        """Handle VS Code's standard htmlcov integration."""
        # Check for VS Code's standard coverage HTML output
        htmlcov_locations = [
            self.project_root / "htmlcov",  # VS Code default location
            self.reports_dir / "htmlcov",  # VS Code moved location
        ]

        for htmlcov_dir in htmlcov_locations:
            if htmlcov_dir.exists():
                target_dir = self.reports_dir / "standard"
                if target_dir.exists():
                    import shutil

                    shutil.rmtree(target_dir)
                import shutil

                shutil.copytree(htmlcov_dir, target_dir)
                self.log(f"✅ Integrated standard coverage report from {htmlcov_dir.name}")
                return

        self.log("ℹ️  No standard htmlcov found - reports will work without it")

    def run(self, force: bool = False) -> bool:
        """Run the complete coverage report generation workflow."""
        self.log("🚀 Fast Coverage Report Generator")
        self.log("=" * 50)

        # Check if we need to run (unless forced)
        if not force and not self.check_data_freshness():
            self.log("❌ No recent coverage data found", force=True)
            return False

        # Load and validate data
        combined_data = self.load_and_validate_data()
        if not combined_data:
            return False

        # Generate all reports
        success = self.generate_reports(combined_data)
        if not success:
            return False

        # Integrate with VS Code standard reports
        self.integrate_with_vscode_htmlcov()

        # Performance summary
        elapsed = time.time() - self.start_time
        self.log("")
        self.log(f"✅ Report generation completed in {elapsed:.2f}s")
        self.log("")
        self.log("🌐 Coverage Reports Available:")
        self.log(f"  • Main Overview: {self.reports_dir / 'index.html'}")
        self.log(f"  • By Test Type: {self.reports_dir / 'by-type' / 'index.html'}")
        self.log(f"  • Standard Report: {self.reports_dir / 'standard' / 'index.html'}")
        self.log("")
        self.log("💡 Integration Features:")
        self.log("  • Sortable tables with keyboard shortcuts")
        self.log("  • File-explorer compatible (no server required)")
        self.log("  • Matches VS Code coverage display exactly")
        self.log("  • Single test run efficiency (no 5x performance penalty)")
        self.log("  • Automatic updates from VS Code workflow")

        return True


def create_vscode_integration_hook() -> None:
    """Create VS Code integration hook for automatic report generation."""
    hook_script = Path(__file__).parent / "vscode_coverage_hook.py"

    hook_content = '''#!/usr/bin/env python3
"""
VS Code Coverage Integration Hook

This script is called automatically by VS Code after running tests with coverage.
It triggers the fast coverage report generation to update all HTML reports.

This file can be configured as a VS Code task or integrated with pytest plugins.
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from generate_test_coverage_fast import FastCoverageReportGenerator

def main():
    """Main hook entry point."""
    generator = FastCoverageReportGenerator(quiet=True)
    success = generator.run(force=False)

    if success:
        print("✅ Coverage reports updated")
    else:
        print("⚠️  Coverage reports not updated - run tests with coverage first")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    hook_script.write_text(hook_content)
    hook_script.chmod(0o755)  # Make executable
    print(f"✅ Created VS Code integration hook: {hook_script}")


def main():
    """Main entry point with command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate fast coverage reports from VS Code test runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_test_coverage_fast.py                # Normal mode
  python scripts/generate_test_coverage_fast.py --force        # Force regeneration
  python scripts/generate_test_coverage_fast.py --quiet        # Minimal output
  python scripts/generate_test_coverage_fast.py --create-hook  # Create VS Code hook
        """,
    )

    parser.add_argument("--force", "-f", action="store_true", help="Force report generation even if data seems stale")

    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode - minimal output")

    parser.add_argument("--create-hook", action="store_true", help="Create VS Code integration hook script")

    args = parser.parse_args()

    # Handle hook creation
    if args.create_hook:
        create_vscode_integration_hook()
        return

    # Run the main workflow
    generator = FastCoverageReportGenerator(quiet=args.quiet)
    success = generator.run(force=args.force)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
