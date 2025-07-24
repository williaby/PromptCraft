"""
Pytest configuration and custom hooks for PromptCraft testing.
Automatically generates test-type-specific coverage reports.
"""

import subprocess
import sys
from pathlib import Path

# Global variable to track which test types were executed
executed_test_types: set[str] = set()


def pytest_runtest_protocol(item, nextitem):
    """Hook called for each test to track test types by markers."""
    global executed_test_types

    # Extract markers from the test item
    markers = [marker.name for marker in item.iter_markers()]

    # Map markers to test types
    test_type_markers = {
        "unit": "unit",
        "integration": "integration",
        "auth": "auth",
        "performance": "performance",
        "stress": "stress",
    }

    for marker, test_type in test_type_markers.items():
        if marker in markers:
            executed_test_types.add(test_type)
            break

    # Call the default implementation


def pytest_sessionfinish(session, exitstatus):
    """Hook called after all tests are completed."""
    global executed_test_types

    # Only generate reports if coverage was enabled and tests were run
    if not executed_test_types:
        return

    # Check if this is a coverage run (look for --cov in sys.argv)
    if not any("--cov" in arg for arg in sys.argv):
        return

    # Check if VS Code coverage is enabled (lightweight generation)
    vscode_coverage = any("--cov-report=html" in arg for arg in sys.argv)

    if vscode_coverage and len(executed_test_types) > 0:
        print("\n🔍 Generating organized coverage reports (VS Code integration)...")
        generate_lightweight_reports(executed_test_types)
    else:
        print("\n💡 Use scripts/generate_test_type_coverage_clean.py for detailed reports")


def generate_lightweight_reports(test_types: set[str]):
    """Generate lightweight organized reports without recursive pytest calls."""
    try:
        # Create organized structure
        reports_dir = Path("reports/coverage/by-type")
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Move standard htmlcov to organized location
        if Path("htmlcov").exists():
            standard_dir = Path("reports/coverage/standard")
            if standard_dir.exists():
                import shutil

                shutil.rmtree(standard_dir)
            Path("htmlcov").rename(standard_dir)
            print("  📋 Organized standard coverage: reports/coverage/standard/")

        # Also move any htmlcov-by-type content to organized location
        if Path("htmlcov-by-type").exists():
            by_type_dir = Path("reports/coverage/by-type")
            if by_type_dir.exists():
                import shutil

                shutil.rmtree(by_type_dir)
            Path("htmlcov-by-type").rename(by_type_dir)
            print("  📋 Organized detailed coverage: reports/coverage/by-type/")

        # Create navigation index for VS Code integration
        create_vscode_navigation_index(test_types)

        print("  ✅ Organized coverage reports available at: reports/coverage/")
        print("  🔗 Navigation: reports/coverage/index.html")

    except Exception as e:
        print(f"  ⚠️  Could not organize reports: {e}")


def create_vscode_navigation_index(test_types: set[str]):
    """Create lightweight navigation index for VS Code integration."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PromptCraft Coverage Reports (VS Code Integration)</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }}
            .report-card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 15px 0; }}
            .report-card h3 {{ margin: 0 0 10px 0; color: #007acc; }}
            .report-card a {{ display: inline-block; background: #007acc; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }}
            .report-card a:hover {{ background: #005a9e; }}
            .info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .test-types {{ background: #f0f8e6; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Coverage Reports (Auto-Generated)</h1>

            <div class="info">
                <p><strong>Generated automatically by VS Code "Run Tests with Coverage"</strong></p>
                <p>This navigation page is created each time you run coverage in VS Code, organizing your reports for easy access.</p>
            </div>

            <div class="test-types">
                <h3>🧪 Test Types Executed:</h3>
                <p>This run included: <strong>{', '.join(sorted(test_types)) if test_types else 'Various test types'}</strong></p>
            </div>

            <div class="report-card">
                <h3>📈 Standard Coverage Report</h3>
                <p>Complete project coverage analysis from your VS Code test run.</p>
                <a href="standard/index.html">View Standard Coverage →</a>
            </div>

            <div class="report-card">
                <h3>🔧 Detailed Test-Type Reports</h3>
                <p>Test-type-specific coverage breakdowns (unit, integration, auth, etc.).</p>
                <a href="by-type/index.html">View Detailed Reports →</a>
            </div>

            <div class="info">
                <h3>📋 Quick Actions:</h3>
                <ul>
                    <li><strong>VS Code Integration:</strong> This page auto-updates with each coverage run</li>
                    <li><strong>Detailed Analysis:</strong> Use <code>python scripts/generate_test_type_coverage_clean.py</code></li>
                    <li><strong>File Organization:</strong> All reports organized in <code>reports/coverage/</code></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    index_file = Path("reports/coverage/index.html")
    index_file.write_text(html_content)


def generate_test_type_reports(test_types: set[str]):
    """Generate HTML coverage reports for each executed test type."""

    # Create output directory
    output_dir = Path("htmlcov-by-type")
    output_dir.mkdir(exist_ok=True)

    # Test type configurations
    test_configs = {
        "unit": ("tests/unit/", "Unit Tests"),
        "integration": ("tests/integration/", "Integration Tests"),
        "auth": ("tests/auth/", "Authentication Tests"),
        "performance": ("tests/performance/", "Performance Tests"),
        "stress": ("tests/performance/", "Stress Tests"),
    }

    coverage_summary = {}
    reports_generated = []

    for test_type in test_types:
        if test_type not in test_configs:
            continue

        test_path, description = test_configs[test_type]
        print(f"  📊 Generating {description} coverage...")

        try:
            # Ensure reports directory exists
            reports_dir = Path("reports/coverage")
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Generate coverage report for this specific test type with organized output
            cmd = [
                "poetry",
                "run",
                "pytest",
                "--cov=src",
                f"--cov-report=html:{output_dir}/{test_type}",
                f"--cov-report=xml:reports/coverage/coverage-{test_type}.xml",
                f"--junitxml=reports/temp/junit-{test_type}.xml",
                "--tb=no",  # Suppress traceback output
                "--quiet",  # Minimize output
                "-m",
                test_type,
                test_path,
            ]

            # Create temp directory for junit files
            Path("reports/temp").mkdir(parents=True, exist_ok=True)

            result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=Path.cwd())

            # Add custom header to the HTML report
            html_file = output_dir / test_type / "index.html"
            if html_file.exists():
                add_custom_header(html_file, description, test_type, test_path)
                reports_generated.append((test_type, description))

                # Extract coverage percentage from organized location
                xml_file = Path(f"reports/coverage/coverage-{test_type}.xml")
                if xml_file.exists():
                    coverage_summary[test_type] = extract_coverage_percentage(xml_file)

        except Exception as e:
            print(f"  ❌ Failed to generate {description} report: {e}")

    if reports_generated:
        # Generate navigation index
        generate_navigation_index(output_dir, reports_generated, coverage_summary)

        print("  ✅ Test-type-specific coverage reports generated!")
        print(f"  📁 Reports location: {output_dir}")
        print("  🔗 Available reports:")
        for test_type, description in reports_generated:
            print(f"    • {description}: {output_dir}/{test_type}/index.html")


def add_custom_header(html_file: Path, description: str, test_type: str, test_path: str):
    """Add custom header with test type information to HTML report."""
    try:
        content = html_file.read_text()

        custom_header = f"""
        <div style="background: #e6f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #007acc;">
            <h3 style="margin: 0 0 10px 0; color: #333;">📊 {description} Coverage Report</h3>
            <p style="margin: 0; color: #666;">
                <strong>Test Type:</strong> {description} |
                <strong>Marker:</strong> {test_type} |
                <strong>Path:</strong> {test_path}
            </p>
        </div>
        """

        content = content.replace("<h1>Coverage report</h1>", f"<h1>Coverage report: {description}</h1>{custom_header}")

        html_file.write_text(content)

    except Exception as e:
        print(f"  ⚠️  Could not customize {description} report: {e}")


def extract_coverage_percentage(xml_file: Path) -> dict[str, float]:
    """Extract coverage percentage from XML report."""
    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse(xml_file)
        root = tree.getroot()

        return {
            "percentage": float(root.attrib["line-rate"]) * 100,
            "covered": int(root.attrib["lines-covered"]),
            "total": int(root.attrib["lines-valid"]),
        }
    except Exception:
        return {"percentage": 0, "covered": 0, "total": 0}


def generate_navigation_index(output_dir: Path, reports: list, coverage_summary: dict):
    """Generate navigation index page."""

    report_cards = []
    for test_type, description in reports:
        coverage_info = coverage_summary.get(test_type, {"percentage": 0})
        coverage_pct = coverage_info["percentage"]

        icon_map = {"unit": "🧪", "integration": "🔗", "auth": "🔐", "performance": "🏃‍♂️", "stress": "💪"}

        icon = icon_map.get(test_type, "📊")

        report_cards.append(
            f"""
            <div class="report-card">
                <h3>{icon} {description}</h3>
                <p><strong>Coverage: {coverage_pct:.2f}%</strong><br>
                Auto-generated from VS Code test execution.</p>
                <a href="{test_type}/index.html">View {description} →</a>
            </div>
        """,
        )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PromptCraft Coverage Reports by Test Type</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }}
            .report-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }}
            .report-card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; transition: transform 0.2s; }}
            .report-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
            .report-card h3 {{ margin: 0 0 10px 0; color: #007acc; }}
            .report-card p {{ color: #666; margin: 0 0 15px 0; }}
            .report-card a {{ display: inline-block; background: #007acc; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }}
            .report-card a:hover {{ background: #005a9e; }}
            .stats {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 PromptCraft Coverage Reports (Auto-Generated)</h1>

            <div class="stats">
                <p><strong>Generated from VS Code test execution</strong> - These reports were automatically created based on the test types that were executed in VS Code.</p>
            </div>

            <div class="report-grid">
                {''.join(report_cards)}
            </div>

            <div class="stats">
                <h3>📋 How to Use These Reports:</h3>
                <ul>
                    <li><strong>Red lines:</strong> Not covered by this test type</li>
                    <li><strong>Green lines:</strong> Covered by this test type</li>
                    <li><strong>Auto-refresh:</strong> Reports update each time you run tests in VS Code</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    index_file = output_dir / "index.html"
    index_file.write_text(html_content)


# Reset test types at the start of each session
def pytest_sessionstart(session):
    """Reset tracking at the start of each test session."""
    global executed_test_types
    executed_test_types.clear()
