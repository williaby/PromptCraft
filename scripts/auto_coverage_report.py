#!/usr/bin/env python3
"""
Automated Coverage Report Generator for VS Code Integration

This script provides a comprehensive interface to generate detailed coverage reports
after running tests in VS Code. It now includes parallel test-type report generation
using the enhanced coverage loader with Coverage.py dynamic contexts.

Features:
- VS Code integration for seamless workflow
- Parallel test-type report generation (unit, auth, integration, etc.)
- Function/class level detail for all test types
- Enhanced dashboard with navigation links

Usage:
    python scripts/auto_coverage_report.py

Integration with VS Code:
    1. Run "Run Tests with Coverage" in VS Code
    2. Run this script to get comprehensive reports
    3. Open the generated HTML reports for analysis
"""

import importlib.util
import sys
import time
from pathlib import Path

# Add project root to path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import VS Code integration
spec = importlib.util.spec_from_file_location(
    "vscode_coverage_integration",
    project_root / "scripts" / "vscode_coverage_integration.py",
)
vscode_integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vscode_integration)

# Import enhanced coverage loader
spec = importlib.util.spec_from_file_location(
    "enhanced_coverage_loader",
    project_root / "scripts" / "enhanced_coverage_loader.py",
)
enhanced_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enhanced_loader)

VSCodeCoverageIntegrator = vscode_integration.VSCodeCoverageIntegrator
EnhancedCoverageLoader = enhanced_loader.EnhancedCoverageLoader


def wait_for_vscode_completion(max_wait=10):
    """
    Wait for VS Code to complete its coverage generation and file movement.
    VS Code typically takes a few seconds to generate and move files.
    """
    print("⏳ Waiting for VS Code to complete coverage generation...")

    integrator = VSCodeCoverageIntegrator()

    for i in range(max_wait):
        files = integrator.find_coverage_files()

        # Check if we have the basic files VS Code should generate
        if files["coverage_xml"] and files["junit_xml"]:
            # Wait an additional second for file movement to complete
            time.sleep(1)  # noqa: S110 - Required for VS Code file synchronization
            print(f"✅ Coverage data detected after {i+1} seconds")
            return True

        print(f"   Checking... ({i+1}/{max_wait})")
        time.sleep(1)  # noqa: S110 - Polling interval for VS Code coverage generation

    print(f"⚠️  Timeout after {max_wait} seconds - proceeding with available data")
    return False


def main():
    """Main automation workflow with enhanced parallel test-type report generation."""
    print("🤖 Automated Coverage Report Generator")
    print("=" * 50)
    print("📊 Using 'Single Run, Multiple Reports' architecture")
    print("🔄 Enhanced with parallel test-type report generation")

    # Give VS Code time to finish if it's still running
    wait_for_vscode_completion()

    # Step 1: Generate standard VS Code integration reports
    print("\n📋 Step 1: Generating VS Code integration reports...")
    integrator = VSCodeCoverageIntegrator()
    vscode_success = integrator.run_integration()

    if not vscode_success:
        print("❌ VS Code integration failed - proceeding with enhanced reports anyway")

    # Step 2: Generate enhanced test-type reports using parallel processing
    print("\n📋 Step 2: Generating parallel test-type reports...")
    enhanced_loader = EnhancedCoverageLoader()
    enhanced_reports = enhanced_loader.generate_test_type_reports()

    # Step 3: Report results
    print("\n🎉 Coverage report generation complete!")

    if vscode_success or enhanced_reports:
        print("\n📂 Generated Reports:")

        # Main overview report
        main_report = project_root / "reports" / "coverage" / "index.html"
        if main_report.exists():
            print(f"   📊 Main Overview: file://{main_report.absolute()}")

        # Enhanced analysis report
        enhanced_report = project_root / "reports" / "coverage" / "vscode_integrated_report.html"
        if enhanced_report.exists():
            print(f"   📈 Enhanced Analysis: file://{enhanced_report.absolute()}")

        # Test-type specific reports
        if enhanced_reports:
            print(f"\n🧪 Test-Type Specific Reports ({len(enhanced_reports)} types):")
            for test_type, report_path in enhanced_reports.items():
                if report_path.exists():
                    print(
                        f"   {_get_test_type_icon(test_type)} {test_type.capitalize()}: file://{report_path.absolute()}",
                    )

        # Standard coverage report
        standard_locations = [
            project_root / "reports" / "coverage" / "standard" / "index.html",
            project_root / "reports" / "coverage" / "htmlcov" / "index.html",
        ]

        for location in standard_locations:
            if location.exists():
                print(f"   📋 Standard Coverage: file://{location.absolute()}")
                break

        print("\n💡 New Features:")
        print("   • Function/class level detail for ALL test types")
        print("   • Parallel report generation for improved performance")
        print("   • Enhanced navigation between test type reports")
        print("   • Coverage.py dynamic contexts for precise test type filtering")

        print("\n💡 Next Steps:")
        print("   • Open the Main Overview report for a complete dashboard")
        print("   • Use test-type specific reports for focused analysis")
        print("   • Focus on files with red/yellow coverage for improvement")
        print("   • Re-run this script after making test changes")

    else:
        print("\n❌ Failed to generate coverage reports")
        print("💡 Try running 'Run Tests with Coverage' in VS Code first")
        print("💡 Ensure tests were run with --cov-context=test for enhanced features")
        sys.exit(1)


def _get_test_type_icon(test_type: str) -> str:
    """Get emoji icon for test type."""
    icons = {"unit": "🧪", "auth": "🔐", "integration": "🔗", "security": "🛡️", "performance": "🏃‍♂️", "stress": "💪"}
    return icons.get(test_type, "📋")


if __name__ == "__main__":
    main()
