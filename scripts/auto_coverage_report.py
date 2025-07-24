#!/usr/bin/env python3
"""
Automated Coverage Report Generator for VS Code Integration

This script provides a simple interface to generate detailed coverage reports
after running tests in VS Code. It handles the timing and file detection
automatically.

Usage:
    python scripts/auto_coverage_report.py

Integration with VS Code:
    1. Run "Run Tests with Coverage" in VS Code
    2. Run this script to get detailed reports
    3. Open the generated HTML reports for analysis
"""

import importlib.util
import sys
import time
from pathlib import Path

# Add project root to path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

spec = importlib.util.spec_from_file_location(
    "vscode_coverage_integration",
    project_root / "scripts" / "vscode_coverage_integration.py",
)
vscode_integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vscode_integration)

VSCodeCoverageIntegrator = vscode_integration.VSCodeCoverageIntegrator


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
            time.sleep(1)
            print(f"✅ Coverage data detected after {i+1} seconds")
            return True

        print(f"   Checking... ({i+1}/{max_wait})")
        time.sleep(1)

    print(f"⚠️  Timeout after {max_wait} seconds - proceeding with available data")
    return False


def main():
    """Main automation workflow."""
    print("🤖 Automated Coverage Report Generator")
    print("=" * 50)

    # Give VS Code time to finish if it's still running
    wait_for_vscode_completion()

    # Generate the reports
    integrator = VSCodeCoverageIntegrator()
    success = integrator.run_integration()

    if success:
        print("\n🎉 Coverage reports successfully generated!")
        print("\n📂 Quick Access:")

        # Provide easy file paths for opening
        enhanced_report = project_root / "reports" / "coverage" / "vscode_integrated_report.html"
        if enhanced_report.exists():
            print(f"   Enhanced: file://{enhanced_report.absolute()}")

        standard_locations = [
            project_root / "reports" / "coverage" / "standard" / "index.html",
            project_root / "reports" / "coverage" / "index.html",
            project_root / "reports" / "coverage" / "htmlcov" / "index.html",
        ]

        for location in standard_locations:
            if location.exists():
                print(f"   Standard: file://{location.absolute()}")
                break

        print("\n💡 Next Steps:")
        print("   • Click the file:// links above to open reports in your browser")
        print("   • Focus on files with red/yellow coverage for improvement")
        print("   • Re-run this script after making test changes")

    else:
        print("\n❌ Failed to generate coverage reports")
        print("💡 Try running 'Run Tests with Coverage' in VS Code first")
        sys.exit(1)


if __name__ == "__main__":
    main()
