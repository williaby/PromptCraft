#!/usr/bin/env python3
"""
VS Code Coverage Analyzer - Single Source Coverage Analysis

Processes VS Code "Run Tests with Coverage" output to generate enhanced coverage reports
with file/function/class level views, aggregated and by test type classification.

Usage:
    python scripts/vscode_coverage_analyzer.py
    python scripts/vscode_coverage_analyzer.py --source-dir htmlcov --output-dir reports/coverage
    python scripts/vscode_coverage_analyzer.py --verbose
"""

import argparse
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: beautifulsoup4 not available. Install with: pip install beautifulsoup4")


class TestTypeClassifier:
    """Classifies source files into test types based on file paths and patterns."""
    
    def __init__(self):
        self.test_types = {
            'unit': {
                'source_patterns': [
                    r'src/core/',
                    r'src/agents/',
                    r'src/utils/',
                    r'src/config/',
                ],
                'exclude_patterns': [
                    r'.*integration.*',
                    r'.*main\.py$',
                    r'.*__main__\.py$',
                ],
                'description': 'Core business logic and utilities'
            },
            'auth': {
                'source_patterns': [
                    r'src/auth/',
                    r'.*jwt.*',
                    r'.*token.*',
                    r'.*authentication.*',
                    r'.*middleware.*',
                ],
                'exclude_patterns': [],
                'description': 'Authentication and authorization'
            },
            'security': {
                'source_patterns': [
                    r'src/security/',
                    r'.*crypto.*',
                    r'.*audit.*',
                    r'.*hash.*',
                    r'.*encrypt.*',
                ],
                'exclude_patterns': [],
                'description': 'Security modules and cryptography'
            },
            'integration': {
                'source_patterns': [
                    r'src/api/',
                    r'src/mcp_integration/',
                    r'.*client.*',
                    r'.*router.*',
                    r'.*integration.*',
                    r'.*endpoint.*',
                ],
                'exclude_patterns': [],
                'description': 'API integration and external services'
            },
            'ui': {
                'source_patterns': [
                    r'src/ui/',
                    r'.*gradio.*',
                    r'.*interface.*',
                    r'.*component.*',
                ],
                'exclude_patterns': [],
                'description': 'User interface components'
            },
            'performance': {
                'source_patterns': [
                    r'.*performance.*',
                    r'.*optimization.*',
                    r'.*cache.*',
                    r'.*monitor.*',
                ],
                'exclude_patterns': [],
                'description': 'Performance and optimization'
            },
            'ingestion': {
                'source_patterns': [
                    r'src/ingestion/',
                    r'.*pipeline.*',
                    r'.*processor.*',
                    r'.*vector.*',
                ],
                'exclude_patterns': [],
                'description': 'Knowledge ingestion pipeline'
            }
        }
    
    def classify_file(self, file_path: str) -> List[str]:
        """Classify a file into one or more test types based on path patterns."""
        matching_types = []
        
        for test_type, config in self.test_types.items():
            # Check if file matches any source patterns
            matches_source = any(
                re.search(pattern, file_path, re.IGNORECASE)
                for pattern in config['source_patterns']
            )
            
            # Check if file matches any exclude patterns
            matches_exclude = any(
                re.search(pattern, file_path, re.IGNORECASE)
                for pattern in config['exclude_patterns']
            )
            
            if matches_source and not matches_exclude:
                matching_types.append(test_type)
        
        # Default to 'unit' if no specific classification
        return matching_types if matching_types else ['unit']


class CoverageParser:
    """Parses VS Code coverage output from multiple sources."""
    
    def __init__(self, source_dir: Path, verbose: bool = False):
        self.source_dir = source_dir
        self.verbose = verbose
        self.classifier = TestTypeClassifier()
    
    def parse_coverage_xml(self) -> Dict:
        """Parse coverage.xml file for detailed coverage data."""
        coverage_xml = Path("coverage.xml")
        if not coverage_xml.exists():
            raise FileNotFoundError(f"coverage.xml not found. Run VS Code 'Tests with Coverage' first.")
        
        if self.verbose:
            print(f"📊 Parsing {coverage_xml}")
        
        tree = ET.parse(coverage_xml)
        root = tree.getroot()
        
        coverage_data = {
            'summary': {},
            'files': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Parse summary data from cobertura XML format
        line_rate = float(root.get('line-rate', 0))
        branch_rate = float(root.get('branch-rate', 0))
        lines_valid = int(root.get('lines-valid', 0))
        lines_covered = int(root.get('lines-covered', 0))
        branches_valid = int(root.get('branches-valid', 0))
        branches_covered = int(root.get('branches-covered', 0))
        
        coverage_data['summary']['line'] = {
            'covered': lines_covered,
            'missed': lines_valid - lines_covered,
            'total': lines_valid,
            'percentage': round(line_rate * 100, 2)
        }
        
        coverage_data['summary']['branch'] = {
            'covered': branches_covered,
            'missed': branches_valid - branches_covered,
            'total': branches_valid,
            'percentage': round(branch_rate * 100, 2)
        }
        
        # Parse file-level data
        for package in root.findall('.//package'):
            for class_elem in package.findall('classes/class'):
                filename = class_elem.get('filename', '')
                if not filename:
                    continue
                
                file_data = {
                    'path': filename,
                    'test_types': self.classifier.classify_file(filename),
                    'lines': {},
                    'functions': {},
                    'summary': {}
                }
                
                # Parse line coverage
                for line in class_elem.findall('lines/line'):
                    line_num = int(line.get('number', 0))
                    hits = int(line.get('hits', 0))
                    file_data['lines'][line_num] = hits
                
                # Calculate file summary
                total_lines = len(file_data['lines'])
                covered_lines = sum(1 for hits in file_data['lines'].values() if hits > 0)
                file_data['summary'] = {
                    'total_lines': total_lines,
                    'covered_lines': covered_lines,
                    'percentage': round((covered_lines / total_lines * 100) if total_lines > 0 else 0, 2)
                }
                
                coverage_data['files'][filename] = file_data
        
        return coverage_data
    
    def parse_htmlcov_index(self) -> Dict:
        """Parse htmlcov/index.html for additional insights if available."""
        htmlcov_index = self.source_dir / "index.html"
        
        if not htmlcov_index.exists() or not HAS_BS4:
            if self.verbose:
                print(f"⚠️  Skipping HTML parsing ({'BeautifulSoup not available' if not HAS_BS4 else 'File not found'})")
            return {}
        
        if self.verbose:
            print(f"🔍 Parsing {htmlcov_index}")
        
        with open(htmlcov_index, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Extract file data from HTML table
        html_data = {}
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:
                filename = cells[0].get_text().strip()
                statements = cells[1].get_text().strip()
                missing = cells[2].get_text().strip()
                coverage_text = cells[3].get_text().strip()
                
                # Extract percentage
                coverage_match = re.search(r'(\d+)%', coverage_text)
                if coverage_match:
                    percentage = float(coverage_match.group(1))
                    html_data[filename] = {
                        'statements': statements,
                        'missing': missing,
                        'percentage': percentage
                    }
        
        return html_data


class ReportGenerator:
    """Generates enhanced HTML coverage reports."""
    
    def __init__(self, coverage_data: Dict, output_dir: Path, verbose: bool = False):
        self.coverage_data = coverage_data
        self.output_dir = output_dir
        self.verbose = verbose
        self.classifier = TestTypeClassifier()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all_reports(self):
        """Generate all coverage reports."""
        if self.verbose:
            print(f"📝 Generating reports in {self.output_dir}")
        
        # Generate main dashboard
        self.generate_main_dashboard()
        
        # Generate test type reports
        self.generate_test_type_reports()
        
        # Generate file detail reports
        self.generate_file_detail_reports()
        
        if self.verbose:
            print(f"✅ Reports generated successfully")
    
    def generate_main_dashboard(self):
        """Generate main coverage dashboard."""
        dashboard_html = self._create_dashboard_html()
        dashboard_path = self.output_dir / "index.html"
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        if self.verbose:
            print(f"📊 Main dashboard: {dashboard_path}")
    
    def generate_test_type_reports(self):
        """Generate test type specific reports."""
        test_type_dir = self.output_dir / "by-type"
        test_type_dir.mkdir(exist_ok=True)
        
        # Group files by test type
        files_by_type = defaultdict(list)
        for filename, file_data in self.coverage_data['files'].items():
            for test_type in file_data['test_types']:
                files_by_type[test_type].append((filename, file_data))
        
        # Generate report for each test type
        for test_type, files in files_by_type.items():
            if not files:
                continue
            
            type_html = self._create_test_type_html(test_type, files)
            type_path = test_type_dir / f"{test_type}.html"
            
            with open(type_path, 'w', encoding='utf-8') as f:
                f.write(type_html)
            
            if self.verbose:
                print(f"🏷️  {test_type} report: {type_path}")
        
        # Generate test type index
        index_html = self._create_test_type_index_html(files_by_type)
        index_path = test_type_dir / "index.html"
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    def generate_file_detail_reports(self):
        """Generate detailed file coverage reports."""
        detail_dir = self.output_dir / "files"
        detail_dir.mkdir(exist_ok=True)
        
        for filename, file_data in self.coverage_data['files'].items():
            if not file_data['lines']:
                continue
            
            detail_html = self._create_file_detail_html(filename, file_data)
            safe_filename = filename.replace('/', '_').replace('.', '_') + ".html"
            detail_path = detail_dir / safe_filename
            
            with open(detail_path, 'w', encoding='utf-8') as f:
                f.write(detail_html)
    
    def _create_dashboard_html(self) -> str:
        """Create main dashboard HTML."""
        summary = self.coverage_data.get('summary', {})
        files = self.coverage_data.get('files', {})
        
        # Calculate overall stats
        total_files = len(files)
        line_coverage = summary.get('line', {}).get('percentage', 0)
        branch_coverage = summary.get('branch', {}).get('percentage', 0)
        
        # Group by test type for summary
        type_stats = defaultdict(lambda: {'files': 0, 'lines': 0, 'covered': 0})
        for filename, file_data in files.items():
            for test_type in file_data['test_types']:
                type_stats[test_type]['files'] += 1
                type_stats[test_type]['lines'] += file_data['summary']['total_lines']
                type_stats[test_type]['covered'] += file_data['summary']['covered_lines']
        
        # Calculate percentages
        for test_type, stats in type_stats.items():
            if stats['lines'] > 0:
                stats['percentage'] = round((stats['covered'] / stats['lines']) * 100, 2)
            else:
                stats['percentage'] = 0
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptCraft Coverage Dashboard</title>
    <style>
        {self._get_common_css()}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 PromptCraft Coverage Dashboard</h1>
        
        <div class="nav-controls">
            <div>
                <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} •
                <strong>Source:</strong> VS Code "Run Tests with Coverage"
            </div>
            <div>
                <strong>Files:</strong> {total_files} •
                <strong>Line Coverage:</strong> {line_coverage}% •
                <strong>Branch Coverage:</strong> {branch_coverage}%
            </div>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>📈 Overall Coverage</h3>
                <div class="stat {self._get_coverage_class(line_coverage)}">{line_coverage}%</div>
                <p>{summary.get('line', {}).get('covered', 0):,} / {summary.get('line', {}).get('total', 0):,} lines</p>
                <p>Branch: {branch_coverage}%</p>
            </div>
            
            {self._generate_type_summary_cards(type_stats)}
        </div>

        <div class="nav-controls">
            <h3>📋 Detailed Reports</h3>
            <p>
                <a href="by-type/index.html" class="file-link">📂 By Test Type</a> •
                <a href="files/" class="file-link">📄 File Details</a> •
                <a href="../htmlcov/index.html" class="file-link">🔗 Standard Report</a>
            </p>
        </div>

        <h3>📁 File Coverage Summary</h3>
        <table class="coverage-table">
            <thead>
                <tr>
                    <th class="sortable">File</th>
                    <th class="sortable">Test Types</th>
                    <th class="sortable">Lines</th>
                    <th class="sortable">Covered</th>
                    <th class="sortable">Coverage %</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_file_table_rows(files)}
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by VS Code Coverage Analyzer • Single source analysis • Fast path-based classification</p>
        </div>
    </div>

    <script>
        {self._get_common_js()}
    </script>
</body>
</html>"""
    
    def _create_test_type_html(self, test_type: str, files: List[Tuple[str, Dict]]) -> str:
        """Create test type specific HTML report."""
        # Calculate test type summary
        total_lines = sum(file_data['summary']['total_lines'] for _, file_data in files)
        covered_lines = sum(file_data['summary']['covered_lines'] for _, file_data in files)
        percentage = round((covered_lines / total_lines * 100) if total_lines > 0 else 0, 2)
        
        test_type_config = self.classifier.test_types.get(test_type, {})
        description = test_type_config.get('description', 'No description available')
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{test_type.title()} Test Coverage</title>
    <style>
        {self._get_common_css()}
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Dashboard</a>
        
        <h1>🏷️ {test_type.title()} Test Coverage</h1>
        
        <div class="nav-controls">
            <div>
                <strong>Description:</strong> {description}
            </div>
            <div>
                <strong>Files:</strong> {len(files)} •
                <strong>Coverage:</strong> {percentage}%
            </div>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>📊 {test_type.title()} Coverage</h3>
                <div class="stat {self._get_coverage_class(percentage)}">{percentage}%</div>
                <p>{covered_lines:,} / {total_lines:,} lines</p>
                <p>{len(files)} files</p>
            </div>
        </div>

        <h3>📁 Files in {test_type.title()} Category</h3>
        <table class="coverage-table">
            <thead>
                <tr>
                    <th class="sortable">File</th>
                    <th class="sortable">Lines</th>
                    <th class="sortable">Covered</th>
                    <th class="sortable">Coverage %</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_test_type_file_rows(files)}
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by VS Code Coverage Analyzer • {test_type.title()} test classification</p>
        </div>
    </div>

    <script>
        {self._get_common_js()}
    </script>
</body>
</html>"""
    
    def _create_test_type_index_html(self, files_by_type: Dict) -> str:
        """Create test type index HTML."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage by Test Type</title>
    <style>
        {self._get_common_css()}
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Dashboard</a>
        
        <h1>🏷️ Coverage by Test Type</h1>
        
        <div class="summary-grid">
            {self._generate_test_type_index_cards(files_by_type)}
        </div>

        <div class="footer">
            <p>Generated by VS Code Coverage Analyzer • Path-based test type classification</p>
        </div>
    </div>
</body>
</html>"""
    
    def _create_file_detail_html(self, filename: str, file_data: Dict) -> str:
        """Create detailed file coverage HTML."""
        lines = file_data.get('lines', {})
        summary = file_data.get('summary', {})
        
        # Try to read source file for line-by-line coverage
        source_lines = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
        except (FileNotFoundError, UnicodeDecodeError):
            source_lines = []
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage: {filename}</title>
    <style>
        {self._get_common_css()}
        .line-coverage {{ font-family: monospace; font-size: 14px; }}
        .line-covered {{ background-color: #d4edda; }}
        .line-missed {{ background-color: #f8d7da; }}
        .line-number {{ color: #666; width: 50px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Dashboard</a>
        
        <h1>📄 {filename}</h1>
        
        <div class="nav-controls">
            <div>
                <strong>Test Types:</strong> {', '.join(file_data.get('test_types', []))}
            </div>
            <div>
                <strong>Coverage:</strong> {summary.get('percentage', 0)}% • 
                <strong>Lines:</strong> {summary.get('covered_lines', 0)} / {summary.get('total_lines', 0)}
            </div>
        </div>

        <div class="line-coverage">
            {self._generate_line_coverage_display(source_lines, lines)}
        </div>

        <div class="footer">
            <p>Line-by-line coverage for {filename}</p>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_type_summary_cards(self, type_stats: Dict) -> str:
        """Generate summary cards for each test type."""
        cards = []
        type_icons = {
            'unit': '🧪', 'auth': '🔐', 'security': '🛡️', 'integration': '🔗',
            'ui': '🎨', 'performance': '🏃‍♂️', 'ingestion': '📥'
        }
        
        for test_type, stats in sorted(type_stats.items()):
            icon = type_icons.get(test_type, '📁')
            percentage = stats['percentage']
            cards.append(f"""
            <div class="summary-card">
                <h3>{icon} {test_type.title()}</h3>
                <div class="stat {self._get_coverage_class(percentage)}">{percentage}%</div>
                <p>{stats['files']} files</p>
                <a href="by-type/{test_type}.html" class="file-link">View Details →</a>
            </div>""")
        
        return ''.join(cards)
    
    def _generate_file_table_rows(self, files: Dict) -> str:
        """Generate table rows for file coverage summary."""
        rows = []
        for filename, file_data in sorted(files.items()):
            summary = file_data['summary']
            test_types = ', '.join(file_data['test_types'])
            percentage = summary['percentage']
            
            rows.append(f"""
                <tr>
                    <td><a href="files/{filename.replace('/', '_').replace('.', '_')}.html" class="file-link">{filename}</a></td>
                    <td>{test_types}</td>
                    <td>{summary['total_lines']}</td>
                    <td>{summary['covered_lines']}</td>
                    <td class="{self._get_coverage_class(percentage)}">{percentage}%</td>
                </tr>""")
        
        return ''.join(rows)
    
    def _generate_test_type_file_rows(self, files: List[Tuple[str, Dict]]) -> str:
        """Generate table rows for test type specific files."""
        rows = []
        for filename, file_data in sorted(files):
            summary = file_data['summary']
            percentage = summary['percentage']
            
            rows.append(f"""
                <tr>
                    <td><a href="../files/{filename.replace('/', '_').replace('.', '_')}.html" class="file-link">{filename}</a></td>
                    <td>{summary['total_lines']}</td>
                    <td>{summary['covered_lines']}</td>
                    <td class="{self._get_coverage_class(percentage)}">{percentage}%</td>
                </tr>""")
        
        return ''.join(rows)
    
    def _generate_test_type_index_cards(self, files_by_type: Dict) -> str:
        """Generate cards for test type index."""
        cards = []
        type_icons = {
            'unit': '🧪', 'auth': '🔐', 'security': '🛡️', 'integration': '🔗',
            'ui': '🎨', 'performance': '🏃‍♂️', 'ingestion': '📥'
        }
        
        for test_type, files in sorted(files_by_type.items()):
            if not files:
                continue
            
            icon = type_icons.get(test_type, '📁')
            total_lines = sum(file_data['summary']['total_lines'] for _, file_data in files)
            covered_lines = sum(file_data['summary']['covered_lines'] for _, file_data in files)
            percentage = round((covered_lines / total_lines * 100) if total_lines > 0 else 0, 2)
            
            cards.append(f"""
            <div class="summary-card">
                <h3>{icon} {test_type.title()}</h3>
                <div class="stat {self._get_coverage_class(percentage)}">{percentage}%</div>
                <p>{len(files)} files</p>
                <a href="{test_type}.html" class="file-link">View Details →</a>
            </div>""")
        
        return ''.join(cards)
    
    def _generate_line_coverage_display(self, source_lines: List[str], coverage_lines: Dict) -> str:
        """Generate line-by-line coverage display."""
        if not source_lines:
            return "<p>Source file not available for line-by-line display.</p>"
        
        lines = []
        for i, source_line in enumerate(source_lines, 1):
            hits = coverage_lines.get(i, -1)  # -1 means not executable
            
            if hits == -1:
                css_class = ""
            elif hits > 0:
                css_class = "line-covered"
            else:
                css_class = "line-missed"
            
            lines.append(f"""
                <div class="{css_class}">
                    <span class="line-number">{i:4d}</span>
                    <code>{source_line.rstrip()}</code>
                </div>""")
        
        return ''.join(lines)
    
    def _get_coverage_class(self, percentage: float) -> str:
        """Get CSS class based on coverage percentage."""
        if percentage >= 80:
            return 'coverage-high'
        elif percentage >= 60:
            return 'coverage-medium'
        else:
            return 'coverage-low'
    
    def _get_common_css(self) -> str:
        """Get common CSS styles for all reports."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 20px; background: #f5f5f5; line-height: 1.6;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white;
            padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; margin-bottom: 20px; }
        
        .nav-controls {
            background: #f8f9fa; padding: 15px; border-radius: 5px;
            margin: 20px 0; display: flex; justify-content: space-between;
            align-items: center; flex-wrap: wrap;
        }
        
        .summary-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin: 20px 0;
        }
        .summary-card {
            background: #f8f9fa; border: 1px solid #e9ecef;
            border-radius: 8px; padding: 20px; text-align: center;
        }
        .summary-card h3 { margin: 0 0 10px 0; color: #007acc; }
        .summary-card .stat { font-size: 24px; font-weight: bold; margin: 10px 0; }
        
        .coverage-table {
            width: 100%; border-collapse: collapse; margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .coverage-table th {
            background: #007acc; color: white; padding: 12px 15px;
            text-align: left; font-weight: 600; cursor: pointer;
        }
        .coverage-table td {
            padding: 10px 15px; border-bottom: 1px solid #e9ecef;
        }
        .coverage-table tr:hover { background: #f8f9fa; }
        
        .coverage-high { color: #28a745; font-weight: bold; }
        .coverage-medium { color: #ffc107; font-weight: bold; }
        .coverage-low { color: #dc3545; font-weight: bold; }
        
        .file-link {
            color: #007acc; text-decoration: none;
            border-bottom: 1px dotted #007acc;
        }
        .file-link:hover {
            text-decoration: none; color: #005a99;
            border-bottom: 1px solid #005a99;
        }
        
        .back-link {
            display: inline-block; margin-bottom: 20px; padding: 8px 16px;
            background: #6c757d; color: white; text-decoration: none;
            border-radius: 4px; font-size: 14px;
        }
        .back-link:hover { background: #5a6268; color: white; }
        
        .footer {
            margin-top: 40px; padding-top: 20px; border-top: 1px solid #e9ecef;
            color: #666; font-size: 14px; text-align: center;
        }
        """
    
    def _get_common_js(self) -> str:
        """Get common JavaScript for all reports."""
        return """
        // Simple table sorting
        document.addEventListener('DOMContentLoaded', function() {
            const tables = document.querySelectorAll('.coverage-table');
            tables.forEach(table => {
                const headers = table.querySelectorAll('th.sortable');
                headers.forEach((header, index) => {
                    header.addEventListener('click', () => sortTable(table, index));
                });
            });
        });
        
        function sortTable(table, columnIndex) {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            const isNumeric = rows.some(row => {
                const cell = row.cells[columnIndex];
                return cell && /^[\d.,%]+$/.test(cell.textContent.trim());
            });
            
            rows.sort((a, b) => {
                const aText = a.cells[columnIndex]?.textContent.trim() || '';
                const bText = b.cells[columnIndex]?.textContent.trim() || '';
                
                if (isNumeric) {
                    const aVal = parseFloat(aText.replace(/[%,]/g, ''));
                    const bVal = parseFloat(bText.replace(/[%,]/g, ''));
                    return bVal - aVal; // Descending for numbers
                }
                
                return aText.localeCompare(bText);
            });
            
            rows.forEach(row => tbody.appendChild(row));
        }
        """


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VS Code Coverage Analyzer - Single source coverage analysis"
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("htmlcov"),
        help="Source directory for coverage HTML files (default: htmlcov)"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path,
        default=Path("reports/coverage"),
        help="Output directory for enhanced reports (default: reports/coverage)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        if args.verbose:
            print(f"🚀 VS Code Coverage Analyzer")
            print(f"📂 Source: {args.source_dir}")
            print(f"📁 Output: {args.output_dir}")
        
        # Parse coverage data
        parser = CoverageParser(args.source_dir, args.verbose)
        coverage_data = parser.parse_coverage_xml()
        
        if args.verbose:
            files_count = len(coverage_data['files'])
            overall_coverage = coverage_data.get('summary', {}).get('line', {}).get('percentage', 0)
            print(f"📊 Analyzed {files_count} files with {overall_coverage}% line coverage")
        
        # Generate reports
        generator = ReportGenerator(coverage_data, args.output_dir, args.verbose)
        generator.generate_all_reports()
        
        print(f"✅ Enhanced coverage reports generated in {args.output_dir}")
        print(f"🌐 Open {args.output_dir}/index.html to view the dashboard")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())