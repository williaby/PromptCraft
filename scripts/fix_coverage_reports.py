#!/usr/bin/env python3
"""
Fix Coverage Report Issues

This script addresses two main issues:
1. Missing enhanced-analysis.html file (generates it from existing data)
2. Missing function/class level links in test-type coverage reports

Usage:
    python scripts/fix_coverage_reports.py
"""

import json
import time
from pathlib import Path
from typing import Any


class CoverageReportFixer:
    """Fixes coverage report issues without regenerating everything."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage"

    def fix_all_issues(self) -> None:
        """Fix all identified coverage report issues."""
        print("🔧 Fixing coverage report issues...")

        # Issue 1: Generate missing enhanced analysis report
        self.generate_enhanced_analysis()

        # Issue 2: Add function/class links to test-type reports
        self.add_function_class_links()

        print("✅ All coverage report issues fixed!")

    def generate_enhanced_analysis(self) -> None:
        """Generate the missing enhanced-analysis.html file."""
        print("📊 Generating enhanced analysis report...")

        coverage_json_path = self.reports_dir / "coverage.json"
        if not coverage_json_path.exists():
            print("⚠️  No coverage.json found - skipping enhanced analysis")
            return

        try:
            with coverage_json_path.open() as f:
                coverage_data = json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading coverage.json: {e}")
            return

        # Extract file-level data
        files_data = {}
        if "files" in coverage_data:
            for filepath, file_info in coverage_data["files"].items():
                if "summary" in file_info:
                    summary = file_info["summary"]
                    percentage = (
                        (summary["covered_lines"] / summary["num_statements"] * 100)
                        if summary["num_statements"] > 0
                        else 0
                    )
                    files_data[filepath] = {
                        "percentage": percentage,
                        "lines_covered": summary["covered_lines"],
                        "lines_valid": summary["num_statements"],
                        "missing_lines": summary.get("missing_lines", []),
                    }

        # Generate HTML content
        html_content = self._generate_enhanced_analysis_html(files_data, coverage_data)

        # Write file
        enhanced_file = self.reports_dir / "enhanced-analysis.html"
        enhanced_file.write_text(html_content, encoding="utf-8")
        print(f"✅ Generated enhanced analysis: {enhanced_file}")

    def add_function_class_links(self) -> None:
        """Add function and class level links to test-type coverage reports."""
        print("🔗 Adding function/class links to test-type reports...")

        by_type_dir = self.reports_dir / "by-type"
        if not by_type_dir.exists():
            print("⚠️  No by-type directory found")
            return

        # Process each test type that has pytest-cov HTML reports
        for test_type_dir in by_type_dir.iterdir():
            if test_type_dir.is_dir() and test_type_dir.name != "index.html":
                self._add_links_to_test_type(test_type_dir)

    def _add_links_to_test_type(self, test_type_dir: Path) -> None:
        """Add function/class links to a specific test type report."""
        index_file = test_type_dir / "index.html"
        class_file = test_type_dir / "class_index.html"
        function_file = test_type_dir / "function_index.html"

        if not index_file.exists():
            return

        # Check if this test type has pytest-cov generated reports
        has_class_report = class_file.exists()
        has_function_report = function_file.exists()

        if not (has_class_report or has_function_report):
            print(f"   {test_type_dir.name}: No pytest-cov reports found")
            return

        # Read current content
        try:
            content = index_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️  Error reading {index_file}: {e}")
            return

        # Add navigation links if they don't exist
        navigation_html = self._generate_navigation_links(test_type_dir.name, has_class_report, has_function_report)

        # Insert navigation after the header but before the content
        if 'class="summary">' in content and navigation_html not in content:
            insertion_point = content.find("</div>", content.find('class="summary">')) + 6
            new_content = content[:insertion_point] + "\n\n" + navigation_html + "\n" + content[insertion_point:]

            # Write updated content
            index_file.write_text(new_content, encoding="utf-8")
            print(f"   ✅ {test_type_dir.name}: Added function/class links")
        else:
            print(f"   📋 {test_type_dir.name}: Links already exist or no suitable insertion point")

    def _generate_navigation_links(self, test_type: str, has_class: bool, has_function: bool) -> str:
        """Generate navigation links HTML."""
        links = []

        if has_function:
            links.append('<a href="function_index.html" class="nav-link">📋 Function Coverage</a>')
        if has_class:
            links.append('<a href="class_index.html" class="nav-link">📦 Class Coverage</a>')

        if not links:
            return ""

        return f"""
        <div class="coverage-navigation">
            <h3>📊 Detailed Coverage Views</h3>
            <div class="nav-links">
                {" • ".join(links)}
            </div>
            <style>
                .coverage-navigation {{
                    background: #e8f4fd; padding: 15px; border-radius: 5px;
                    margin: 20px 0; border-left: 4px solid #007acc;
                }}
                .coverage-navigation h3 {{
                    margin: 0 0 10px 0; color: #007acc;
                }}
                .nav-links {{
                    display: flex; gap: 15px; flex-wrap: wrap;
                }}
                .nav-link {{
                    padding: 8px 16px; background: #007acc; color: white;
                    text-decoration: none; border-radius: 4px; transition: background 0.2s;
                }}
                .nav-link:hover {{
                    background: #005a99;
                }}
            </style>
        </div>"""

    def _generate_enhanced_analysis_html(self, files_data: dict[str, Any], coverage_data: dict[str, Any]) -> str:
        """Generate the enhanced analysis HTML content."""

        # Calculate overall stats
        total_lines = sum(f["lines_valid"] for f in files_data.values())
        covered_lines = sum(f["lines_covered"] for f in files_data.values())
        overall_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0

        # Sort files by coverage (lowest first)
        sorted_files = sorted(files_data.items(), key=lambda x: x[1]["percentage"])

        # Generate file table
        files_table = ""
        for filepath, file_data in sorted_files:
            coverage_class = self._get_coverage_class(file_data["percentage"])
            missing_info = ""
            if file_data.get("missing_lines"):
                missing_lines = file_data["missing_lines"]
                if isinstance(missing_lines, list) and len(missing_lines) > 10:
                    missing_info = f"Lines {missing_lines[0]}-{missing_lines[-1]} and others"
                elif isinstance(missing_lines, list):
                    missing_info = f"Lines {', '.join(map(str, missing_lines))}"
                else:
                    missing_info = f"Missing lines: {missing_lines}"

            files_table += f"""
            <tr>
                <td><code>{filepath}</code></td>
                <td class="{coverage_class}">{file_data["percentage"]:.1f}%</td>
                <td>{file_data["lines_covered"]} / {file_data["lines_valid"]}</td>
                <td><small>{missing_info}</small></td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Coverage Analysis - PromptCraft</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f5f5f5; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; margin-bottom: 20px; }}
        .summary {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .files-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .files-table th {{ background: #007acc; color: white; padding: 15px; text-align: left; font-weight: 600; }}
        .files-table td {{ padding: 12px 15px; border-bottom: 1px solid #e9ecef; }}
        .files-table tr:hover {{ background: #f8f9fa; }}
        .coverage-high {{ color: #28a745; font-weight: bold; }}
        .coverage-medium {{ color: #ffc107; font-weight: bold; }}
        .coverage-low {{ color: #dc3545; font-weight: bold; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; }}
        .back-link:hover {{ background: #5a6268; color: white; }}
        .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Coverage Overview</a>

        <h1>📊 Enhanced Coverage Analysis</h1>

        <div class="summary">
            <h3>📈 Overall Coverage Summary</h3>
            <p><strong>Total Coverage:</strong> <span class="{self._get_coverage_class(overall_percentage)}">{overall_percentage:.1f}%</span> ({covered_lines:,} / {total_lines:,} lines)</p>
            <p><strong>Files analyzed:</strong> {len(files_data)} files</p>
            <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <h2>📁 File Coverage Details</h2>
        <p>Files are sorted by coverage percentage (lowest first) to highlight improvement opportunities:</p>

        <table class="files-table">
            <thead>
                <tr>
                    <th>File</th>
                    <th>Coverage</th>
                    <th>Lines</th>
                    <th>Missing Lines</th>
                </tr>
            </thead>
            <tbody>
                {files_table}
            </tbody>
        </table>

        <div class="recommendations">
            <h3>🚀 Improvement Recommendations</h3>
            <ul>
                <li><strong>Focus on red files:</strong> Files below 60% need immediate attention</li>
                <li><strong>Target yellow files:</strong> Files between 60-80% are good candidates for improvement</li>
                <li><strong>Add unit tests:</strong> Cover individual functions and methods</li>
                <li><strong>Test edge cases:</strong> Add tests for error conditions and boundary values</li>
                <li><strong>Integration tests:</strong> Test component interactions</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    def _get_coverage_class(self, percentage: float) -> str:
        """Get CSS class based on coverage percentage."""
        if percentage >= 80:
            return "coverage-high"
        if percentage >= 60:
            return "coverage-medium"
        return "coverage-low"


def main():
    """Main entry point."""
    fixer = CoverageReportFixer()
    fixer.fix_all_issues()


if __name__ == "__main__":
    main()
