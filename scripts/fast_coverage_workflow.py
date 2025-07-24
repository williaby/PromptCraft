#!/usr/bin/env python3
"""
Fast Coverage Workflow

Simple integration script that runs tests and generates enhanced coverage reports
using the new path-based analysis approach for maximum speed and detail.

This script:
1. Runs tests with standard coverage (fast)
2. Uses path-based analysis to generate test-type reports (no overhead)
3. Provides same detailed insights as --cov-context approach but much faster

Usage:
    python scripts/fast_coverage_workflow.py                    # Run tests + analysis
    python scripts/fast_coverage_workflow.py --tests-only      # Just run tests
    python scripts/fast_coverage_workflow.py --analysis-only   # Just run analysis
"""

import argparse
import subprocess
import sys


def run_tests_with_coverage() -> bool:
    """Run tests with standard coverage (no --cov-context overhead)."""
    print("🧪 Running tests with standard coverage...")

    try:
        # Run pytest with standard coverage (fast)
        cmd = [
            "poetry",
            "run",
            "pytest",
            "-v",
            "--cov=src",
            "--cov-branch",
            "--cov-report=html:reports/coverage/standard",
            "--cov-report=xml:reports/coverage/coverage.xml",
            "--cov-report=term-missing:skip-covered",
            "-m",
            "not slow and not performance and not stress",
            "--tb=short",
            "--maxfail=5",
        ]

        result = subprocess.run(cmd, check=False, capture_output=False, text=True)

        if result.returncode == 0:
            print("✅ Tests completed successfully")
            return True
        print(f"⚠️  Tests completed with issues (exit code: {result.returncode})")
        return True  # Continue with analysis even if some tests failed

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_path_based_analysis() -> bool:
    """Run the path-based coverage analysis."""
    print("\n🔍 Running path-based coverage analysis...")

    try:
        # Run the path-based analyzer
        cmd = [
            "python",
            "scripts/path_based_coverage_analyzer.py",
            "--source-dir",
            "reports/coverage/standard",
            "--output-dir",
            "reports/coverage",
        ]

        result = subprocess.run(cmd, check=False, capture_output=False, text=True)

        if result.returncode == 0:
            print("✅ Path-based analysis completed successfully")
            return True
        print(f"❌ Path-based analysis failed (exit code: {result.returncode})")
        return False

    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False


def main():
    """Main workflow orchestrator."""
    parser = argparse.ArgumentParser(
        description="Fast coverage workflow with path-based analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/fast_coverage_workflow.py                    # Full workflow
  python scripts/fast_coverage_workflow.py --tests-only      # Tests only
  python scripts/fast_coverage_workflow.py --analysis-only   # Analysis only
        """,
    )

    parser.add_argument("--tests-only", action="store_true", help="Run tests only, skip analysis")

    parser.add_argument("--analysis-only", action="store_true", help="Run analysis only, skip tests")

    args = parser.parse_args()

    print("🚀 Fast Coverage Workflow")
    print("=" * 50)

    success = True

    # Run tests unless analysis-only
    if not args.analysis_only:
        success = run_tests_with_coverage()
        if not success:
            print("❌ Test execution failed")
            return 1

    # Run analysis unless tests-only
    if not args.tests_only:
        success = run_path_based_analysis()
        if not success:
            print("❌ Analysis failed")
            return 1

    if not args.tests_only and not args.analysis_only:
        print("\n🎉 Complete fast coverage workflow finished!")
        print("\n🌐 View Results:")
        print("  • Main Dashboard: reports/coverage/index.html")
        print("  • Test Type Analysis: reports/coverage/by-type/index.html")
        print("  • Standard Report: reports/coverage/standard/index.html")
        print("\n💡 Benefits Achieved:")
        print("  • Fast test execution (no --cov-context overhead)")
        print("  • Detailed test-type specific analysis")
        print("  • Same insights as previous approach")
        print("  • Compatible with VS Code workflow")

    return 0


if __name__ == "__main__":
    sys.exit(main())
