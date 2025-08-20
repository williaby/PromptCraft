#!/usr/bin/env python3
"""
Minimal HTML Renderer for Coverage Reports

This provides the essential HTMLRenderer class to fix the import error
in vscode_coverage_hook.py while maintaining the existing interface.
"""

import time
from pathlib import Path
from typing import Any


class HTMLRenderer:
    """Minimal HTML renderer for coverage reports."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def generate_main_index(
        self,
        coverage_data: dict[str, Any],
        test_distribution: dict[str, Any],
        test_type_coverage: dict[str, Any],
    ) -> str:
        """Generate main coverage index HTML."""
        total_files = len(coverage_data.get("files", {}))
        overall_coverage = coverage_data.get("summary", {}).get("percent_covered", 0)

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Coverage Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
        .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .coverage-high {{ color: #28a745; font-weight: bold; }}
        .coverage-medium {{ color: #ffc107; font-weight: bold; }}
        .coverage-low {{ color: #dc3545; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Coverage Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Total Files:</strong> {total_files}</p>
            <p><strong>Overall Coverage:</strong> <span class="{'coverage-high' if overall_coverage >= 80 else 'coverage-medium' if overall_coverage >= 60 else 'coverage-low'}">{overall_coverage:.1f}%</span></p>
            <p><strong>Generated:</strong> {self.timestamp}</p>
        </div>
    </div>
</body>
</html>"""

    def generate_by_type_index(self, test_distribution: dict[str, Any], test_type_coverage: dict[str, Any]) -> str:
        """Generate by-type index HTML."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Coverage by Test Type</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Coverage by Test Type</h1>
        <p>Test distribution and coverage by type</p>
        <p><strong>Generated:</strong> {self.timestamp}</p>
    </div>
</body>
</html>"""

    def generate_test_type_detail(self, test_type: str, type_coverage: dict[str, Any], count: int) -> str:
        """Generate detailed view for a specific test type."""
        coverage_percent = type_coverage.get("percent_covered", 0)

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{test_type.title()} Test Coverage</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
        .coverage-high {{ color: #28a745; font-weight: bold; }}
        .coverage-medium {{ color: #ffc107; font-weight: bold; }}
        .coverage-low {{ color: #dc3545; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{test_type.title()} Test Coverage</h1>
        <p><strong>Test Count:</strong> {count}</p>
        <p><strong>Coverage:</strong> <span class="{'coverage-high' if coverage_percent >= 80 else 'coverage-medium' if coverage_percent >= 60 else 'coverage-low'}">{coverage_percent:.1f}%</span></p>
        <p><strong>Generated:</strong> {self.timestamp}</p>
    </div>
</body>
</html>"""

    def save_html_file(self, html_content: str, file_path: Path) -> None:
        """Save HTML content to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(html_content, encoding="utf-8")
