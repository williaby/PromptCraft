"""
Coverage report rendering and generation.
"""

import json
from pathlib import Path
import subprocess
import time
from typing import Any

from .classifier import TestTypeClassifier
from .config import TestPatternConfig


class CoverageRenderer:
    """Renders coverage reports in various formats."""

    def __init__(self, project_root: Path, config: TestPatternConfig, classifier: TestTypeClassifier):
        self.project_root = project_root
        self.config = config
        self.classifier = classifier

        # Test type mapping with display metadata
        self.test_types = self._build_test_type_mapping()

    def _build_test_type_mapping(self) -> dict[str, dict[str, str]]:
        """Build test type mapping from configuration with display metadata."""
        default_icons = {
            "unit": "🧪",
            "auth": "🔐",
            "integration": "🔗",
            "security": "🛡️",
            "performance": "⚡",
            "stress": "💪",
            "contract": "📋",
            "examples": "📚",
        }

        test_types = {}
        for test_type in self.config.get_all_test_types():
            config = self.config.get_test_type_config(test_type)
            description = config.get("description", f"{test_type.title()} Tests")
            icon = default_icons.get(test_type, "🔬")

            test_types[test_type] = {"icon": icon, "display": description}

        return test_types

    def generate_coverage_reports(self, used_contexts: set[str]) -> str:
        """Generate enhanced HTML coverage reports."""
        try:
            # First, combine coverage data files if needed
            subprocess.run(
                ["poetry", "run", "coverage", "combine"],
                cwd=self.project_root,
                check=False,
            )

            # Generate standard HTML report
            try:
                subprocess.run(
                    ["poetry", "run", "coverage", "html", "--directory", "htmlcov"],
                    cwd=self.project_root,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                # Check if HTML was still generated despite the error
                htmlcov_index = self.project_root / "htmlcov" / "index.html"
                if not htmlcov_index.exists():
                    raise e
                print("Warning: Coverage HTML generated with warnings (continuing...)")

            # Generate JSON data for filtering
            try:
                subprocess.run(["poetry", "run", "coverage", "json"], cwd=self.project_root, check=True)
            except subprocess.CalledProcessError as e:
                coverage_json_path = self.project_root / "coverage.json"
                if not coverage_json_path.exists():
                    raise e
                print("Warning: Coverage JSON generated with warnings (continuing...)")

            # Read the generated JSON
            coverage_json_path = self.project_root / "coverage.json"
            if coverage_json_path.exists():
                with open(coverage_json_path) as f:
                    coverage_data = json.load(f)
            else:
                coverage_data = {}

            # Create enhanced HTML with context info
            html_path = self.project_root / "reports" / "coverage" / "simplified_report.html"
            html_path.parent.mkdir(parents=True, exist_ok=True)

            self._write_enhanced_html(html_path, coverage_data, used_contexts)

            return str(html_path)

        except subprocess.CalledProcessError as e:
            print(f"Error generating coverage report: {e}")
            return ""

    def _write_enhanced_html(self, html_path: Path, coverage_data: dict[str, Any], used_contexts: set[str]) -> None:
        """Write enhanced HTML report with context filtering."""
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

        # Get coverage estimates by test type
        coverage_by_type = self.classifier.estimate_test_type_coverage(coverage_data, used_contexts)

        # Create relative paths for htmlcov reports
        htmlcov_index = "../../htmlcov/index.html"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptCraft Coverage Report - Simplified</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .coverage-high {{ color: #28a745; font-weight: bold; }}
        .coverage-medium {{ color: #ffc107; font-weight: bold; }}
        .coverage-low {{ color: #dc3545; font-weight: bold; }}
        .context-pills {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }}
        .context-pill {{ padding: 8px 16px; background: #e9ecef; border-radius: 15px; font-size: 14px; margin-bottom: 8px; cursor: pointer; text-decoration: none; color: inherit; display: inline-block; }}
        .context-pill.active {{ background: #007acc; color: white; }}
        .context-pill:hover {{ background: #005a9e; color: white; }}
        .context-coverage {{ font-size: 12px; opacity: 0.9; margin-top: 4px; }}
        .report-links {{ margin: 20px 0; }}
        .report-links a {{ display: inline-block; margin-right: 15px; padding: 8px 16px;
                          background: #007acc; color: white; text-decoration: none; border-radius: 4px; }}
        .test-summary {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .test-count {{ color: #666; font-size: 14px; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 PromptCraft Coverage Report</h1>
        <p><strong>Overall Coverage:</strong> <span class="coverage-{'high' if total_coverage >= 80 else 'medium' if total_coverage >= 60 else 'low'}">{total_coverage:.1f}%</span></p>
        <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div class="test-count">
            <strong>Test Discovery:</strong> Coverage analysis complete
        </div>
    </div>

    <div class="test-summary">
        <h3>🧪 Test Types Executed</h3>
        <div class="context-pills">
"""

        if used_contexts:
            for context in sorted(used_contexts):
                if context in self.test_types:
                    info = self.test_types[context]
                    type_data = coverage_by_type.get(context, {"statement": 0, "branch": 0, "total_branches": 0})
                    statement_coverage = type_data["statement"]
                    branch_coverage = type_data["branch"]
                    total_branches = type_data["total_branches"]

                    branch_info = f" • {branch_coverage:.1f}% branches" if total_branches > 0 else ""

                    html_content += f"""
            <a href="{context}_coverage.html" class="context-pill active">
                <div>{info["icon"]} {info["display"]}</div>
                <div class="context-coverage">~{statement_coverage:.1f}% coverage{branch_info}</div>
            </a>"""
        else:
            html_content += '<div class="context-pill">🔍 Auto-detecting test types...</div>'

        html_content += f"""
        </div>
    </div>

    <div class="report-links">
        <h3>📋 Standard Coverage Report</h3>
        <a href="{htmlcov_index}">📊 View Complete Coverage Report</a>
        <p style="margin-top: 10px; color: #666; font-size: 14px;">
            The standard report includes Files, Functions, and Classes views with sortable tables and detailed line-by-line coverage.
        </p>
    </div>

    <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h4>💡 How to Use</h4>
        <ul>
            <li><strong>Test Type Reports:</strong> Click any test type pill above to see coverage analysis for that specific test type</li>
            <li><strong>Standard Report:</strong> Click "View Complete Coverage Report" for comprehensive file-by-file analysis</li>
            <li><strong>Navigation:</strong> Each test type report includes a "Back to Main" link for easy navigation</li>
            <li><strong>Test Types:</strong> Automatically detected based on code coverage patterns and test structure</li>
            <li><strong>Coverage Estimates:</strong> Per-test-type coverage estimated from file patterns and actual test execution</li>
        </ul>
    </div>

    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #666; font-size: 14px;">
        <p>🤖 Generated automatically by coverage automation • Consistent with codecov.yaml flags</p>
        <p>📍 Project: {self.project_root}</p>
    </div>
</body>
</html>"""

        with open(html_path, "w") as f:
            f.write(html_content)
