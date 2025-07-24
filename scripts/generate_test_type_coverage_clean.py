#!/usr/bin/env python3
"""
Generate separate HTML coverage reports for different test types with proper file organization.
This version addresses file organization issues by putting all generated files in appropriate directories.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import shutil


def run_command(cmd, description, cwd=None):
    """Run a command and handle output."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            cmd, 
            check=False, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        if result.returncode != 0:
            print(f"⚠️  {description} completed with warnings")
            if result.stderr:
                print(f"   stderr: {result.stderr[:200]}...")
        else:
            print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def setup_output_directories():
    """Create organized output directories."""
    directories = {
        'reports': Path('reports'),
        'coverage': Path('reports/coverage'),
        'coverage_by_type': Path('reports/coverage/by-type'),
        'temp': Path('reports/temp'),
    }
    
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {path}")
    
    return directories


def cleanup_root_files():
    """Clean up any files that might be created at root level."""
    cleanup_patterns = [
        'coverage-*.xml',
        'junit-*.xml', 
        'bandit-*.json',
        '.coverage.*'
    ]
    
    root = Path('.')
    cleaned_files = []
    
    for pattern in cleanup_patterns:
        for file in root.glob(pattern):
            if file.is_file():
                # Move to temp directory
                temp_dir = Path('reports/temp')
                temp_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file), temp_dir / file.name)
                cleaned_files.append(file.name)
    
    if cleaned_files:
        print(f"🧹 Moved {len(cleaned_files)} files to reports/temp/")
    
    return cleaned_files


def generate_test_type_coverage(test_type, path, marker, description, directories):
    """Generate coverage for a specific test type with organized output."""
    print(f"\n📊 Generating {description} coverage...")
    
    # Use organized paths - consistent with conftest.py structure
    html_output = directories['coverage_by_type'] / test_type
    xml_output = directories['coverage'] / f"coverage-{test_type}.xml"
    junit_output = directories['temp'] / f"junit-{test_type}.xml"
    
    # Build command with organized output paths
    cmd = f"""poetry run pytest \
        --cov=src \
        --cov-report=html:{html_output} \
        --cov-report=xml:{xml_output} \
        --cov-report=term-missing \
        --junitxml={junit_output} \
        --tb=short \
        --quiet \
        -m "{marker}" \
        {path}"""
    
    success = run_command(cmd, f"{description} coverage generation")
    
    if success and (html_output / "index.html").exists():
        # Add custom header to HTML report
        customize_html_report(html_output / "index.html", description, marker, path)
        print(f"✅ {description} HTML report: {html_output}/index.html")
        
        # Extract coverage data
        coverage_data = extract_coverage_data(xml_output)
        return coverage_data
    else:
        print(f"❌ Failed to generate {description} HTML report")
        return None


def customize_html_report(html_file, description, marker, path):
    """Add custom header with test type information to HTML report."""
    try:
        content = html_file.read_text()
        
        custom_header = f"""
        <div style="background: #e6f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #007acc;">
            <h3 style="margin: 0 0 10px 0; color: #333;">📊 {description} Coverage Report</h3>
            <p style="margin: 0; color: #666;">
                <strong>Test Type:</strong> {description} |
                <strong>Marker:</strong> {marker} |
                <strong>Path:</strong> {path}
            </p>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">
                <strong>Generated:</strong> {Path.cwd()}/reports/coverage/by-type/{html_file.parent.name}/
            </p>
        </div>
        """
        
        content = content.replace(
            "<h1>Coverage report</h1>",
            f"<h1>Coverage report: {description}</h1>{custom_header}"
        )
        
        html_file.write_text(content)
        
    except Exception as e:
        print(f"⚠️  Could not customize {description} report: {e}")


def extract_coverage_data(xml_file):
    """Extract coverage percentage from XML report."""
    try:
        import xml.etree.ElementTree as ET
        
        if not xml_file.exists():
            return None
            
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        return {
            "percentage": float(root.attrib["line-rate"]) * 100,
            "covered": int(root.attrib["lines-covered"]),
            "total": int(root.attrib["lines-valid"]),
        }
    except Exception as e:
        print(f"⚠️  Could not extract coverage data from {xml_file}: {e}")
        return None


def create_navigation_index(directories, coverage_summary):
    """Create organized navigation index with proper file organization info."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PromptCraft Coverage Reports by Test Type</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }}
            .report-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }}
            .report-card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; transition: transform 0.2s; }}
            .report-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
            .report-card h3 {{ margin: 0 0 10px 0; color: #007acc; }}
            .report-card p {{ color: #666; margin: 0 0 15px 0; }}
            .report-card a {{ display: inline-block; background: #007acc; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }}
            .report-card a:hover {{ background: #005a9e; }}
            .stats {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .file-organization {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .coverage-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .coverage-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007acc; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 PromptCraft Coverage Reports (Organized)</h1>

            <div class="file-organization">
                <h3>📁 File Organization</h3>
                <p><strong>All generated files are now properly organized:</strong></p>
                <ul>
                    <li><strong>HTML Reports:</strong> <code>reports/coverage/by-type/</code></li>
                    <li><strong>XML Coverage:</strong> <code>reports/coverage/</code></li>
                    <li><strong>JUnit Files:</strong> <code>reports/temp/</code></li>
                    <li><strong>Root Level:</strong> Clean! No more clutter</li>
                </ul>
            </div>

            <div class="coverage-stats">
                {generate_coverage_cards(coverage_summary)}
            </div>

            <div class="report-grid">
                <div class="report-card">
                    <h3>🧪 Unit Tests</h3>
                    <p>Isolated testing of individual components and functions.</p>
                    <a href="by-type/unit/">View Unit Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>🔗 Integration Tests</h3>
                    <p>Testing interactions between components and external services.</p>
                    <a href="by-type/integration/">View Integration Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>🔐 Authentication Tests</h3>
                    <p>Security-focused testing of authentication systems.</p>
                    <a href="by-type/auth/">View Auth Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>🏃‍♂️ Performance Tests</h3>
                    <p>Performance benchmarking and load testing scenarios.</p>
                    <a href="by-type/performance/">View Performance Coverage →</a>
                </div>

                <div class="report-card">
                    <h3>💪 Stress Tests</h3>
                    <p>High-load testing to identify breaking points.</p>
                    <a href="by-type/stress/">View Stress Coverage →</a>
                </div>
            </div>

            <div class="stats">
                <h3>📋 How to Use These Reports:</h3>
                <ul>
                    <li><strong>Red lines:</strong> Not covered by tests of this type</li>
                    <li><strong>Green lines:</strong> Covered by tests of this type</li>
                    <li><strong>Yellow lines:</strong> Partially covered (branches)</li>
                    <li><strong>File organization:</strong> All artifacts properly organized in reports/ directory</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    index_file = directories['coverage_by_type'] / ".." / "index.html"
    index_file.write_text(html_content)
    print(f"✅ Navigation index created: {index_file}")


def generate_coverage_cards(coverage_summary):
    """Generate HTML for coverage summary cards."""
    if not coverage_summary:
        return "<p>No coverage data available</p>"
    
    cards = []
    for test_type, data in coverage_summary.items():
        if data:
            cards.append(f"""
                <div class="coverage-item">
                    <h4>{test_type.capitalize()}</h4>
                    <p><strong>{data['percentage']:.1f}%</strong></p>
                    <small>{data['covered']}/{data['total']} lines</small>
                </div>
            """)
    
    return "".join(cards)


def main():
    """Generate organized coverage reports for each test type."""
    print("🔍 Generating organized HTML coverage reports by test type")
    print("=" * 60)
    
    # Ensure we're in project root
    os.chdir(Path(__file__).parent.parent)
    
    # Set up organized directory structure  
    directories = setup_output_directories()
    
    # Clean up any existing root-level files
    cleanup_root_files()
    
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
        coverage_data = generate_test_type_coverage(name, path, marker, description, directories)
        if coverage_data:
            coverage_summary[name] = coverage_data
    
    # Create organized navigation index
    create_navigation_index(directories, coverage_summary)
    
    # Final cleanup of any stray files
    final_cleanup = cleanup_root_files()
    
    # Print summary
    print("\n📈 Coverage Summary by Test Type")
    print("=" * 40)
    
    for name, data in coverage_summary.items():
        if data:
            print(f"{name.capitalize():15} {data['percentage']:6.2f}% ({data['covered']}/{data['total']} lines)")
    
    print("\n🎉 Organized coverage reports generated successfully!")
    print("📁 Reports structure:")
    print("  • HTML Reports: reports/coverage/by-type/")
    print("  • XML Coverage: reports/coverage/")
    print("  • Temp Files: reports/temp/")
    print("  • Navigation: reports/coverage/index.html")
    
    print(f"\n🧹 Organization improvements:")
    print(f"  • All artifacts properly organized in reports/ directory")
    print(f"  • Root level cleaned of coverage/junit/bandit files")
    print(f"  • Consistent file naming and structure")
    print(f"  • Easy cleanup with 'rm -rf reports/' if needed")


if __name__ == "__main__":
    main()