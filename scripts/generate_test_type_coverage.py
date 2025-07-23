#!/usr/bin/env python3
"""
Generate separate HTML coverage reports for different test types.
This allows detailed analysis of coverage by unit, integration, performance, etc.
"""

import os
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle output."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  {description} completed with warnings (coverage generated)")
        else:
            print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Generate coverage reports for each test type."""
    print("🔍 Generating HTML coverage reports by test type")
    print("=" * 50)

    # Ensure we're in project root
    os.chdir(Path(__file__).parent.parent)

    # Create output directory
    Path("htmlcov-by-type").mkdir(exist_ok=True)

    # Test configurations: (name, path, marker, description)
    test_configs = [
        ("unit", "tests/unit/", "unit", "Unit Tests"),
        ("integration", "tests/integration/", "integration", "Integration Tests"),
        ("auth", "tests/auth/", "auth", "Authentication Tests"),
        ("performance", "tests/performance/", "performance", "Performance Tests"),
        ("stress", "tests/performance/", "stress", "Stress Tests"),
    ]

    coverage_summary = {}

    # Generate coverage for each test type
    for name, path, marker, description in test_configs:
        print(f"\n📊 Generating {description} coverage...")

        cmd = f"""poetry run pytest \
            --cov=src \
            --cov-report=html:htmlcov-by-type/{name} \
            --cov-report=xml:coverage-{name}.xml \
            --cov-report=term-missing \
            --tb=short \
            -m "{marker}" \
            {path}"""

        run_command(cmd, f"{description} coverage generation")

        # Check if HTML report was generated and add custom info
        index_file = Path(f"htmlcov-by-type/{name}/index.html")
        if index_file.exists():
            # Read the file and add test type information
            content = index_file.read_text()

            # Add custom header with test type info
            custom_header = f"""
            <div style="background: #e6f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #007acc;">
                <h3 style="margin: 0 0 10px 0; color: #333;">📊 {description} Coverage Report</h3>
                <p style="margin: 0; color: #666;">
                    <strong>Test Type:</strong> {description} |
                    <strong>Marker:</strong> {marker} |
                    <strong>Path:</strong> {path}
                </p>
            </div>
            """

            # Insert after the <h1> tag
            content = content.replace(
                "<h1>Coverage report</h1>", f"<h1>Coverage report: {description}</h1>{custom_header}",
            )

            index_file.write_text(content)
            print(f"✅ {description} HTML report: htmlcov-by-type/{name}/index.html")

            # Extract coverage percentage from XML if it exists
            xml_file = Path(f"coverage-{name}.xml")
            if xml_file.exists():
                try:
                    import xml.etree.ElementTree as ET

                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    line_rate = float(root.attrib["line-rate"])
                    lines_covered = int(root.attrib["lines-covered"])
                    lines_valid = int(root.attrib["lines-valid"])
                    coverage_summary[name] = {
                        "percentage": line_rate * 100,
                        "covered": lines_covered,
                        "total": lines_valid,
                    }
                except Exception:
                    pass
        else:
            print(f"❌ Failed to generate {description} HTML report")

    # Generate combined coverage for comparison
    print("\n📊 Generating combined coverage report...")
    cmd = """poetry run pytest \
        --cov=src \
        --cov-report=html:htmlcov-by-type/combined \
        --cov-report=xml:coverage-combined.xml \
        --cov-report=term-missing \
        --tb=short \
        tests/"""

    run_command(cmd, "Combined coverage generation")

    # Add info to combined report
    combined_index = Path("htmlcov-by-type/combined/index.html")
    if combined_index.exists():
        content = combined_index.read_text()
        custom_header = """
        <div style="background: #f0f8e6; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #4caf50;">
            <h3 style="margin: 0 0 10px 0; color: #333;">📈 Combined Coverage Report</h3>
            <p style="margin: 0; color: #666;">
                <strong>Includes:</strong> Unit, Integration, Auth, Performance, and Stress Tests
            </p>
        </div>
        """
        content = content.replace(
            "<h1>Coverage report</h1>", f"<h1>Coverage report: All Tests Combined</h1>{custom_header}",
        )
        combined_index.write_text(content)
        print("✅ Combined HTML report: htmlcov-by-type/combined/index.html")

    # Print coverage summary
    print("\n📈 Coverage Summary by Test Type")
    print("=" * 40)

    for name, data in coverage_summary.items():
        print(f"{name.capitalize():15} {data['percentage']:6.2f}% ({data['covered']}/{data['total']} lines)")

    # Create index page for easy navigation
    create_index_page()

    print("\n🎉 Coverage reports generated successfully!")
    print("📁 Reports location: htmlcov-by-type/")
    print("🌐 Start server: cd htmlcov-by-type && python -m http.server 8081")

    # Start HTTP server
    print("\n🚀 Starting HTTP server for coverage reports...")
    os.chdir("htmlcov-by-type")
    try:
        subprocess.Popen(["python", "-m", "http.server", "8081"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("📡 Coverage reports server started at http://localhost:8081")
        print("\n🔗 Available reports:")
        print("  • Navigation Index: http://localhost:8081/")
        print("  • Unit Tests: http://localhost:8081/unit/")
        print("  • Integration Tests: http://localhost:8081/integration/")
        print("  • Auth Tests: http://localhost:8081/auth/")
        print("  • Performance Tests: http://localhost:8081/performance/")
        print("  • Stress Tests: http://localhost:8081/stress/")
        print("  • Combined: http://localhost:8081/combined/")
        print("\n💡 Use VS Code Simple Browser (Ctrl+Shift+P) to view these URLs")
    except Exception as e:
        print(f"⚠️  Could not start HTTP server: {e}")


def create_index_page():
    """Create a navigation index page for all coverage reports."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PromptCraft Coverage Reports by Test Type</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }
            .report-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }
            .report-card { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; transition: transform 0.2s; }
            .report-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
            .report-card h3 { margin: 0 0 10px 0; color: #007acc; }
            .report-card p { color: #666; margin: 0 0 15px 0; }
            .report-card a { display: inline-block; background: #007acc; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
            .report-card a:hover { background: #005a9e; }
            .stats { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 PromptCraft Coverage Reports by Test Type</h1>

            <div class="stats">
                <p><strong>Purpose:</strong> Analyze test coverage breakdown by test type to identify gaps and improve testing strategy.</p>
                <p><strong>Generated:</strong> Each report shows line-by-line coverage for specific test categories.</p>
            </div>

            <div class="report-grid">
                <div class="report-card">
                    <h3>🧪 Unit Tests</h3>
                    <p>Isolated testing of individual components and functions. Fast execution, focused scope.</p>
                    <a href="unit/">View Unit Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>🔗 Integration Tests</h3>
                    <p>Testing interactions between components and external services.</p>
                    <a href="integration/">View Integration Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>🔐 Authentication Tests</h3>
                    <p>Security-focused testing of authentication and authorization systems.</p>
                    <a href="auth/">View Auth Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>🏃‍♂️ Performance Tests</h3>
                    <p>Performance benchmarking and load testing scenarios.</p>
                    <a href="performance/">View Performance Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>💪 Stress Tests</h3>
                    <p>High-load testing to identify breaking points and resource limits.</p>
                    <a href="stress/">View Stress Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>📈 Combined Report</h3>
                    <p>Comprehensive coverage across all test types for overall project health.</p>
                    <a href="combined/">View Combined Coverage →</a>
                </div>
            </div>

            <div class="stats">
                <h3>📋 How to Use These Reports:</h3>
                <ul>
                    <li><strong>Red lines:</strong> Not covered by tests of this type</li>
                    <li><strong>Green lines:</strong> Covered by tests of this type</li>
                    <li><strong>Yellow lines:</strong> Partially covered (branches)</li>
                    <li><strong>Function/Class views:</strong> Use the navigation to drill down</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    Path("htmlcov-by-type/index.html").write_text(html_content)
    print("✅ Navigation index created: htmlcov-by-type/index.html")


if __name__ == "__main__":
    main()
