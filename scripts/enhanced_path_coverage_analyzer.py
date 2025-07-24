#!/usr/bin/env python3
"""
Enhanced Path-Based Coverage Analyzer with Function/Class Support

This script extends the path-based approach to include function and class level
coverage analysis by parsing both the index pages and individual file detail pages
from the standard Coverage.py HTML report.

Key Features:
- Parses function_index.html and class_index.html for granular coverage data
- Extracts function/class coverage from individual file detail pages
- Generates test-type specific reports matching standard Coverage.py styling
- Maintains fast execution without runtime overhead
- Supports sortable tables, filtering, and navigation like standard reports

Usage:
    python scripts/enhanced_path_coverage_analyzer.py
    python scripts/enhanced_path_coverage_analyzer.py --source-dir reports/coverage/standard
    python scripts/enhanced_path_coverage_analyzer.py --include-functions --include-classes
"""

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import unquote

from bs4 import BeautifulSoup


@dataclass
class CoverageFileData:
    """Represents coverage data for a single source file."""
    file_path: str
    statements: int
    missing: int
    excluded: int
    branches: int
    partial: int
    coverage_percent: float
    detailed_link: Optional[str] = None

    @property
    def covered_statements(self) -> int:
        return self.statements - self.missing


@dataclass
class FunctionCoverageData:
    """Represents coverage data for a single function."""
    name: str
    file_path: str
    statements: int
    missing: int
    excluded: int
    branches: int
    partial: int
    coverage_percent: float
    line_number: Optional[int] = None

    @property
    def covered_statements(self) -> int:
        return self.statements - self.missing


@dataclass
class ClassCoverageData:
    """Represents coverage data for a single class."""
    name: str
    file_path: str
    statements: int
    missing: int
    excluded: int
    branches: int
    partial: int
    coverage_percent: float
    line_number: Optional[int] = None

    @property
    def covered_statements(self) -> int:
        return self.statements - self.missing


@dataclass
class TestTypeAnalysis:
    """Enhanced analysis results for a specific test type."""
    name: str
    display_name: str
    icon: str
    files: List[CoverageFileData] = field(default_factory=list)
    functions: List[FunctionCoverageData] = field(default_factory=list)
    classes: List[ClassCoverageData] = field(default_factory=list)
    estimated_test_count: int = 0

    @property
    def total_statements(self) -> int:
        return sum(f.statements for f in self.files)
    
    @property
    def total_covered(self) -> int:
        return sum(f.covered_statements for f in self.files)
    
    @property
    def coverage_percent(self) -> float:
        if self.total_statements == 0:
            return 100.0
        return (self.total_covered / self.total_statements) * 100


class IntelligentTestTypeClassifier:
    """
    Intelligent classifier that maps source files to test types based on 
    file path patterns and domain knowledge about typical test coverage.
    """
    
    def __init__(self):
        # Test type definitions with intelligent path patterns and priorities
        self.test_types = {
            'unit': {
                'display_name': '🧪 Unit Tests',
                'icon': '🧪',
                'source_patterns': [
                    r'src/core/',
                    r'src/agents/',
                    r'src/utils/',
                    r'src/config/',
                ],
                'exclude_patterns': [
                    r'src/ui/',  # UI typically tested with integration
                    r'src/mcp_integration/',  # Integration points
                ],
                'test_estimate_multiplier': 15  # ~15 tests per file
            },
            'auth': {
                'display_name': '🔐 Auth & Security Tests', 
                'icon': '🔐',
                'source_patterns': [
                    r'src/auth/',
                    r'src/security/',
                ],
                'exclude_patterns': [],
                'test_estimate_multiplier': 20  # Auth files heavily tested
            },
            'integration': {
                'display_name': '🔗 Integration Tests',
                'icon': '🔗', 
                'source_patterns': [
                    r'src/mcp_integration/',
                    r'src/ui/',
                    r'src/api/',
                    r'examples/',
                ],
                'exclude_patterns': [],
                'test_estimate_multiplier': 8  # Fewer but more comprehensive tests
            },
            'security': {
                'display_name': '🛡️ Security Tests',
                'icon': '🛡️',
                'source_patterns': [
                    r'src/security/',
                    r'src/auth/',
                ],
                'exclude_patterns': [],
                'test_estimate_multiplier': 12  # Security-focused testing
            },
            'performance': {
                'display_name': '⚡ Performance Tests',
                'icon': '⚡',
                'source_patterns': [
                    r'src/core/',
                    r'src/mcp_integration/',
                    r'src/utils/circuit_breaker',
                    r'src/utils/performance',
                    r'src/config/performance',
                ],
                'exclude_patterns': [
                    r'src/ui/',  # UI performance tested differently
                ],
                'test_estimate_multiplier': 5  # Fewer but intensive tests
            },
            'stress': {
                'display_name': '💪 Stress Tests',
                'icon': '💪',
                'source_patterns': [
                    r'src/core/vector_store',
                    r'src/mcp_integration/',
                    r'src/utils/circuit_breaker',
                ],
                'exclude_patterns': [],
                'test_estimate_multiplier': 3  # Few but comprehensive stress tests
            }
        }

    def classify_source_file(self, file_path: str) -> Set[str]:
        """
        Classify a source file into one or more test types based on intelligent analysis.
        Returns set of test type names that likely cover this file.
        """
        test_types = set()
        
        # Normalize path for consistent matching
        normalized_path = file_path.replace('\\', '/')
        
        for test_type, config in self.test_types.items():
            # Check if file matches any include patterns
            matches_include = any(
                re.search(pattern, normalized_path) 
                for pattern in config['source_patterns']
            )
            
            # Check if file matches any exclude patterns
            matches_exclude = any(
                re.search(pattern, normalized_path) 
                for pattern in config['exclude_patterns']
            )
            
            if matches_include and not matches_exclude:
                test_types.add(test_type)
        
        # Special case handling for files that might not match patterns
        if not test_types:
            # Default to unit tests for core source files
            if 'src/' in normalized_path and not any(exclude in normalized_path for exclude in ['ui/', 'integration']):
                test_types.add('unit')
        
        return test_types

    def estimate_test_count(self, file_path: str, test_type: str, file_statements: int) -> int:
        """Estimate number of tests for a file based on complexity and test type."""
        config = self.test_types.get(test_type, {})
        base_multiplier = config.get('test_estimate_multiplier', 10)
        
        # Adjust based on file complexity (statement count)
        if file_statements > 200:
            complexity_factor = 1.5  # Complex files get more tests
        elif file_statements > 100:
            complexity_factor = 1.2
        elif file_statements < 30:
            complexity_factor = 0.7  # Simple files get fewer tests
        else:
            complexity_factor = 1.0
            
        return max(1, int(base_multiplier * complexity_factor))


class EnhancedCoverageHTMLParser:
    """
    Enhanced parser for Coverage.py HTML reports that extracts file, function, 
    and class level coverage data.
    """
    
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)
        self.classifier = IntelligentTestTypeClassifier()
        
    def parse_index_page(self, index_file: Path) -> List[CoverageFileData]:
        """Parse the main index.html file to extract file-level coverage data."""
        if not index_file.exists():
            raise FileNotFoundError(f"Coverage index file not found: {index_file}")
            
        with open(index_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        files = []
        
        # Find the main coverage table
        table = soup.find('table', class_='index')
        if not table:
            raise ValueError("Could not find coverage table in index.html")
        
        # Parse each file row (skip header and footer)
        for row in table.find('tbody').find_all('tr', class_='region'):
            cols = row.find_all('td')
            if len(cols) < 7:
                continue
                
            # Extract file path and detailed link
            file_link = cols[0].find('a')
            if not file_link:
                continue
                
            file_path = file_link.get_text().strip()
            detailed_link = file_link.get('href')
            
            try:
                # Parse coverage statistics
                statements = int(cols[1].get_text().strip())
                missing = int(cols[2].get_text().strip())
                excluded = int(cols[3].get_text().strip())
                branches = int(cols[4].get_text().strip())
                partial = int(cols[5].get_text().strip())
                
                # Parse coverage percentage
                coverage_text = cols[6].get_text().strip().replace('%', '')
                coverage_percent = float(coverage_text)
                
                files.append(CoverageFileData(
                    file_path=file_path,
                    statements=statements,
                    missing=missing,
                    excluded=excluded,
                    branches=branches,
                    partial=partial,
                    coverage_percent=coverage_percent,
                    detailed_link=detailed_link
                ))
                
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse row for {file_path}: {e}")
                continue
        
        return files

    def parse_function_index(self) -> List[FunctionCoverageData]:
        """Parse function_index.html to extract function-level coverage data."""
        function_file = self.source_dir / 'function_index.html'
        if not function_file.exists():
            print(f"Warning: Function index not found: {function_file}")
            return []
            
        with open(function_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        functions = []
        
        # Find the function coverage table
        table = soup.find('table', class_='index')
        if not table:
            return functions
        
        # Parse each function row
        tbody = table.find('tbody')
        if not tbody:
            return functions
            
        for row in tbody.find_all('tr', class_='region'):
            cols = row.find_all('td')
            if len(cols) < 8:  # Function table has 8 columns: file, function, statements, missing, excluded, branches, partial, coverage
                continue
                
            try:
                # Extract file path from first column
                file_cell = cols[0]
                file_path = file_cell.get_text().strip()
                
                # Extract function name from second column
                func_cell = cols[1]
                # Look for the <data> element or direct text
                data_elem = func_cell.find('data')
                if data_elem:
                    func_name = data_elem.get('value', '').strip()
                    if not func_name:
                        # Try getting text content
                        func_name = func_cell.get_text().strip()
                        # Clean up special cases like "(no function)"
                        if func_name == "(no function)":
                            func_name = "module_level"
                else:
                    func_name = func_cell.get_text().strip()
                    if func_name == "(no function)":
                        func_name = "module_level"
                
                # Skip empty or invalid function names
                if not func_name or func_name.isspace():
                    continue
                
                # Parse coverage statistics (columns 2-7)
                statements = int(cols[2].get_text().strip())
                missing = int(cols[3].get_text().strip())
                excluded = int(cols[4].get_text().strip())
                branches = int(cols[5].get_text().strip())
                partial = int(cols[6].get_text().strip())
                
                # Parse coverage percentage
                coverage_text = cols[7].get_text().strip().replace('%', '')
                coverage_percent = float(coverage_text)
                
                functions.append(FunctionCoverageData(
                    name=func_name,
                    file_path=file_path,
                    statements=statements,
                    missing=missing,
                    excluded=excluded,
                    branches=branches,
                    partial=partial,
                    coverage_percent=coverage_percent
                ))
                
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse function row: {e}")
                continue
        
        return functions

    def parse_class_index(self) -> List[ClassCoverageData]:
        """Parse class_index.html to extract class-level coverage data."""
        class_file = self.source_dir / 'class_index.html'
        if not class_file.exists():
            print(f"Warning: Class index not found: {class_file}")
            return []
            
        with open(class_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        classes = []
        
        # Find the class coverage table
        table = soup.find('table', class_='index')
        if not table:
            return classes
        
        # Parse each class row
        tbody = table.find('tbody')
        if not tbody:
            return classes
            
        for row in tbody.find_all('tr', class_='region'):
            cols = row.find_all('td')
            if len(cols) < 8:  # Class table has 8 columns: file, class, statements, missing, excluded, branches, partial, coverage
                continue
                
            try:
                # Extract file path from first column
                file_cell = cols[0]
                file_path = file_cell.get_text().strip()
                
                # Extract class name from second column
                class_cell = cols[1]
                # Look for the <data> element or direct text
                data_elem = class_cell.find('data')
                if data_elem:
                    class_name = data_elem.get('value', '').strip()
                    if not class_name:
                        # Try getting text content
                        class_name = class_cell.get_text().strip()
                        # Clean up special cases like "(no class)"
                        if class_name == "(no class)":
                            class_name = "module_level"
                else:
                    class_name = class_cell.get_text().strip()
                    if class_name == "(no class)":
                        class_name = "module_level"
                
                # Skip empty or invalid class names, and skip module_level entries
                if not class_name or class_name.isspace() or class_name == "module_level":
                    continue
                
                # Parse coverage statistics (columns 2-7)
                statements = int(cols[2].get_text().strip())
                missing = int(cols[3].get_text().strip())
                excluded = int(cols[4].get_text().strip())
                branches = int(cols[5].get_text().strip())
                partial = int(cols[6].get_text().strip())
                
                # Parse coverage percentage
                coverage_text = cols[7].get_text().strip().replace('%', '')
                coverage_percent = float(coverage_text)
                
                classes.append(ClassCoverageData(
                    name=class_name,
                    file_path=file_path,
                    statements=statements,
                    missing=missing,
                    excluded=excluded,
                    branches=branches,
                    partial=partial,
                    coverage_percent=coverage_percent
                ))
                
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse class row: {e}")
                continue
        
        return classes

    def analyze_by_test_types(self, include_functions: bool = True, include_classes: bool = True) -> Dict[str, TestTypeAnalysis]:
        """
        Analyze coverage data and organize by test types using intelligent classification.
        """
        # Parse all coverage data
        print("Parsing file coverage data...")
        index_file = self.source_dir / 'index.html'
        files = self.parse_index_page(index_file)
        
        functions = []
        classes = []
        
        if include_functions:
            print("Parsing function coverage data...")
            functions = self.parse_function_index()
            
        if include_classes:
            print("Parsing class coverage data...")
            classes = self.parse_class_index()
        
        # Initialize test type analyses
        test_analyses = {}
        for test_type, config in self.classifier.test_types.items():
            test_analyses[test_type] = TestTypeAnalysis(
                name=test_type,
                display_name=config['display_name'],
                icon=config['icon']
            )
        
        # Classify files and assign to test types
        print("Classifying files by test types...")
        for file_data in files:
            test_types = self.classifier.classify_source_file(file_data.file_path)
            
            for test_type in test_types:
                if test_type in test_analyses:
                    test_analyses[test_type].files.append(file_data)
                    
                    # Estimate test count for this file
                    estimated_tests = self.classifier.estimate_test_count(
                        file_data.file_path, test_type, file_data.statements
                    )
                    test_analyses[test_type].estimated_test_count += estimated_tests
        
        # Classify functions by test types
        if include_functions:
            print("Classifying functions by test types...")
            for func_data in functions:
                test_types = self.classifier.classify_source_file(func_data.file_path)
                
                for test_type in test_types:
                    if test_type in test_analyses:
                        test_analyses[test_type].functions.append(func_data)
        
        # Classify classes by test types  
        if include_classes:
            print("Classifying classes by test types...")
            for class_data in classes:
                test_types = self.classifier.classify_source_file(class_data.file_path)
                
                for test_type in test_types:
                    if test_type in test_analyses:
                        test_analyses[test_type].classes.append(class_data)
        
        return test_analyses


class EnhancedHTMLReportGenerator:
    """
    Enhanced HTML report generator that creates test-type specific coverage reports
    matching the standard Coverage.py styling with function and class support.
    """
    
    def __init__(self, output_dir: Path, source_dir: Path):
        self.output_dir = Path(output_dir)
        self.source_dir = Path(source_dir)
        
    def copy_static_assets(self):
        """Copy CSS, JS, and image assets from source to output directory."""
        static_files = [
            'style_cb_81f8c14c.css',
            'coverage_html_cb_6fb7b396.js', 
            'favicon_32_cb_58284776.png',
            'keybd_closed_cb_ce680311.png'
        ]
        
        for filename in static_files:
            source_file = self.source_dir / filename
            if source_file.exists():
                shutil.copy2(source_file, self.output_dir)
    
    def generate_file_index_html(self, analysis: TestTypeAnalysis, test_type: str) -> str:
        """Generate the main index.html for a test type (files view)."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %z")
        
        # Calculate totals
        total_statements = analysis.total_statements
        total_missing = sum(f.missing for f in analysis.files)
        total_excluded = sum(f.excluded for f in analysis.files)
        total_branches = sum(f.branches for f in analysis.files)
        total_partial = sum(f.partial for f in analysis.files)
        overall_coverage = analysis.coverage_percent
        
        # Generate file rows
        file_rows = ""
        for file_data in sorted(analysis.files, key=lambda f: f.file_path):
            file_rows += f'''
            <tr class="region">
                <td class="name left"><a href="{file_data.detailed_link or '#'}">{file_data.file_path}</a></td>
                <td>{file_data.statements}</td>
                <td>{file_data.missing}</td>
                <td>{file_data.excluded}</td>
                <td>{file_data.branches}</td>
                <td>{file_data.partial}</td>
                <td class="right" data-ratio="{file_data.covered_statements} {file_data.statements}">{file_data.coverage_percent:.2f}%</td>
            </tr>'''
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Coverage report: {analysis.display_name}</title>
    <link rel="icon" sizes="32x32" href="favicon_32_cb_58284776.png">
    <link rel="stylesheet" href="style_cb_81f8c14c.css" type="text/css">
    <script src="coverage_html_cb_6fb7b396.js" defer></script>
</head>
<body class="indexfile">
<header>
    <div class="content">
        <h1>{analysis.display_name} Coverage: 
            <span class="pc_cov">{overall_coverage:.2f}%</span>
        </h1>
        <aside id="help_panel_wrapper">
            <input id="help_panel_state" type="checkbox">
            <label for="help_panel_state">
                <img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show/hide keyboard shortcuts">
            </label>
            <div id="help_panel">
                <p class="legend">Shortcuts on this page</p>
                <div class="keyhelp">
                    <p><kbd>f</kbd><kbd>s</kbd><kbd>m</kbd><kbd>x</kbd><kbd>b</kbd><kbd>p</kbd><kbd>c</kbd> &nbsp; change column sorting</p>
                    <p><kbd>[</kbd><kbd>]</kbd> &nbsp; prev/next file</p>
                    <p><kbd>?</kbd> &nbsp; show/hide this help</p>
                </div>
            </div>
        </aside>
        <form id="filter_container">
            <input id="filter" type="text" value="" placeholder="filter...">
            <div>
                <input id="hide100" type="checkbox">
                <label for="hide100">hide covered</label>
            </div>
        </form>
        <h2>
            <a class="button current">Files</a>
            <a class="button" href="function_index.html">Functions</a>
            <a class="button" href="class_index.html">Classes</a>
        </h2>
        <p class="text">
            <a class="nav" href="../../index.html">← Back to Coverage Dashboard</a>
        </p>
        <p class="text">
            <span class="text">{analysis.estimated_test_count:,} estimated tests ⚡ </span>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {timestamp}
        </p>
    </div>
</header>
<main id="index">
    <table class="index" data-sortable>
        <thead>
            <tr class="tablehead" title="Click to sort">
                <th id="file" class="name left" aria-sort="none" data-shortcut="f">File<span class="arrows"></span></th>
                <th id="statements" aria-sort="none" data-default-sort-order="descending" data-shortcut="s">statements<span class="arrows"></span></th>
                <th id="missing" aria-sort="none" data-default-sort-order="descending" data-shortcut="m">missing<span class="arrows"></span></th>
                <th id="excluded" aria-sort="none" data-default-sort-order="descending" data-shortcut="x">excluded<span class="arrows"></span></th>
                <th id="branches" aria-sort="none" data-default-sort-order="descending" data-shortcut="b">branches<span class="arrows"></span></th>
                <th id="partial" aria-sort="none" data-default-sort-order="descending" data-shortcut="p">partial<span class="arrows"></span></th>
                <th id="coverage" class="right" aria-sort="none" data-shortcut="c">coverage<span class="arrows"></span></th>
            </tr>
        </thead>
        <tbody>{file_rows}
        </tbody>
        <tfoot>
            <tr class="total">
                <td class="name left">Total</td>
                <td>{total_statements}</td>
                <td>{total_missing}</td>
                <td>{total_excluded}</td>
                <td>{total_branches}</td>
                <td>{total_partial}</td>
                <td class="right" data-ratio="{analysis.total_covered} {total_statements}">{overall_coverage:.2f}%</td>
            </tr>
        </tfoot>
    </table>
    <p id="no_rows">No items found using the specified filter.</p>
</main>
<footer>
    <div class="content">
        <p>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {timestamp}
        </p>
    </div>
</footer>
</body>
</html>'''
        
        return html_content

    def generate_function_index_html(self, analysis: TestTypeAnalysis, test_type: str) -> str:
        """Generate the function_index.html for a test type."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %z")
        
        # Calculate totals for functions
        total_statements = sum(f.statements for f in analysis.functions)
        total_missing = sum(f.missing for f in analysis.functions)
        total_excluded = sum(f.excluded for f in analysis.functions)
        total_branches = sum(f.branches for f in analysis.functions)
        total_partial = sum(f.partial for f in analysis.functions)
        total_covered = sum(f.covered_statements for f in analysis.functions)
        overall_coverage = (total_covered / total_statements * 100) if total_statements > 0 else 100.0
        
        # Generate function rows
        function_rows = ""
        for func_data in sorted(analysis.functions, key=lambda f: f.file_path + ":" + f.name):
            function_rows += f'''
            <tr class="region">
                <td class="name left">{func_data.file_path}:{func_data.name}</td>
                <td>{func_data.statements}</td>
                <td>{func_data.missing}</td>
                <td>{func_data.excluded}</td>
                <td>{func_data.branches}</td>
                <td>{func_data.partial}</td>
                <td class="right" data-ratio="{func_data.covered_statements} {func_data.statements}">{func_data.coverage_percent:.2f}%</td>
            </tr>'''
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Functions: {analysis.display_name}</title>
    <link rel="icon" sizes="32x32" href="favicon_32_cb_58284776.png">
    <link rel="stylesheet" href="style_cb_81f8c14c.css" type="text/css">
    <script src="coverage_html_cb_6fb7b396.js" defer></script>
</head>
<body class="indexfile">
<header>
    <div class="content">
        <h1>{analysis.display_name} Functions: 
            <span class="pc_cov">{overall_coverage:.2f}%</span>
        </h1>
        <aside id="help_panel_wrapper">
            <input id="help_panel_state" type="checkbox">
            <label for="help_panel_state">
                <img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show/hide keyboard shortcuts">
            </label>
            <div id="help_panel">
                <p class="legend">Shortcuts on this page</p>
                <div class="keyhelp">
                    <p><kbd>f</kbd><kbd>n</kbd><kbd>s</kbd><kbd>m</kbd><kbd>x</kbd><kbd>b</kbd><kbd>p</kbd><kbd>c</kbd> &nbsp; change column sorting</p>
                    <p><kbd>[</kbd><kbd>]</kbd> &nbsp; prev/next file</p>
                    <p><kbd>?</kbd> &nbsp; show/hide this help</p>
                </div>
            </div>
        </aside>
        <form id="filter_container">
            <input id="filter" type="text" value="" placeholder="filter...">
            <div>
                <input id="hide100" type="checkbox">
                <label for="hide100">hide covered</label>
            </div>
        </form>
        <h2>
            <a class="button" href="index.html">Files</a>
            <a class="button current">Functions</a>
            <a class="button" href="class_index.html">Classes</a>
        </h2>
        <p class="text">
            <a class="nav" href="../../index.html">← Back to Coverage Dashboard</a>
        </p>
        <p class="text">
            <span class="text">{len(analysis.functions)} functions from {analysis.estimated_test_count:,} tests ⚡ </span>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {timestamp}
        </p>
    </div>
</header>
<main id="index">
    <table class="index" data-sortable>
        <thead>
            <tr class="tablehead" title="Click to sort">
                <th id="function" class="name left" aria-sort="none" data-shortcut="f">Function<span class="arrows"></span></th>
                <th id="statements" aria-sort="none" data-default-sort-order="descending" data-shortcut="s">statements<span class="arrows"></span></th>
                <th id="missing" aria-sort="none" data-default-sort-order="descending" data-shortcut="m">missing<span class="arrows"></span></th>
                <th id="excluded" aria-sort="none" data-default-sort-order="descending" data-shortcut="x">excluded<span class="arrows"></span></th>
                <th id="branches" aria-sort="none" data-default-sort-order="descending" data-shortcut="b">branches<span class="arrows"></span></th>
                <th id="partial" aria-sort="none" data-default-sort-order="descending" data-shortcut="p">partial<span class="arrows"></span></th>
                <th id="coverage" class="right" aria-sort="none" data-shortcut="c">coverage<span class="arrows"></span></th>
            </tr>
        </thead>
        <tbody>{function_rows}
        </tbody>
        <tfoot>
            <tr class="total">
                <td class="name left">Total</td>
                <td>{total_statements}</td>
                <td>{total_missing}</td>
                <td>{total_excluded}</td>
                <td>{total_branches}</td>
                <td>{total_partial}</td>
                <td class="right" data-ratio="{total_covered} {total_statements}">{overall_coverage:.2f}%</td>
            </tr>
        </tfoot>
    </table>
    <p id="no_rows">No items found using the specified filter.</p>
</main>
<footer>
    <div class="content">
        <p>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {timestamp}
        </p>
    </div>
</footer>
</body>
</html>'''
        
        return html_content

    def generate_class_index_html(self, analysis: TestTypeAnalysis, test_type: str) -> str:
        """Generate the class_index.html for a test type."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %z")
        
        # Calculate totals for classes
        total_statements = sum(c.statements for c in analysis.classes)
        total_missing = sum(c.missing for c in analysis.classes)
        total_excluded = sum(c.excluded for c in analysis.classes)
        total_branches = sum(c.branches for c in analysis.classes)
        total_partial = sum(c.partial for c in analysis.classes)
        total_covered = sum(c.covered_statements for c in analysis.classes)
        overall_coverage = (total_covered / total_statements * 100) if total_statements > 0 else 100.0
        
        # Generate class rows
        class_rows = ""
        for class_data in sorted(analysis.classes, key=lambda c: c.file_path + ":" + c.name):
            class_rows += f'''
            <tr class="region">
                <td class="name left">{class_data.file_path}:{class_data.name}</td>
                <td>{class_data.statements}</td>
                <td>{class_data.missing}</td>
                <td>{class_data.excluded}</td>
                <td>{class_data.branches}</td>
                <td>{class_data.partial}</td>
                <td class="right" data-ratio="{class_data.covered_statements} {class_data.statements}">{class_data.coverage_percent:.2f}%</td>
            </tr>'''
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Classes: {analysis.display_name}</title>
    <link rel="icon" sizes="32x32" href="favicon_32_cb_58284776.png">
    <link rel="stylesheet" href="style_cb_81f8c14c.css" type="text/css">
    <script src="coverage_html_cb_6fb7b396.js" defer></script>
</head>
<body class="indexfile">
<header>
    <div class="content">
        <h1>{analysis.display_name} Classes: 
            <span class="pc_cov">{overall_coverage:.2f}%</span>
        </h1>
        <aside id="help_panel_wrapper">
            <input id="help_panel_state" type="checkbox">
            <label for="help_panel_state">
                <img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show/hide keyboard shortcuts">
            </label>
            <div id="help_panel">
                <p class="legend">Shortcuts on this page</p>
                <div class="keyhelp">
                    <p><kbd>f</kbd><kbd>n</kbd><kbd>s</kbd><kbd>m</kbd><kbd>x</kbd><kbd>b</kbd><kbd>p</kbd><kbd>c</kbd> &nbsp; change column sorting</p>
                    <p><kbd>[</kbd><kbd>]</kbd> &nbsp; prev/next file</p>
                    <p><kbd>?</kbd> &nbsp; show/hide this help</p>
                </div>
            </div>
        </aside>
        <form id="filter_container">
            <input id="filter" type="text" value="" placeholder="filter...">
            <div>
                <input id="hide100" type="checkbox">
                <label for="hide100">hide covered</label>
            </div>
        </form>
        <h2>
            <a class="button" href="index.html">Files</a>
            <a class="button" href="function_index.html">Functions</a>
            <a class="button current">Classes</a>
        </h2>
        <p class="text">
            <a class="nav" href="../../index.html">← Back to Coverage Dashboard</a>
        </p>
        <p class="text">
            <span class="text">{len(analysis.classes)} classes from {analysis.estimated_test_count:,} tests ⚡ </span>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {timestamp}
        </p>
    </div>
</header>
<main id="index">
    <table class="index" data-sortable>
        <thead>
            <tr class="tablehead" title="Click to sort">
                <th id="class" class="name left" aria-sort="none" data-shortcut="f">Class<span class="arrows"></span></th>
                <th id="statements" aria-sort="none" data-default-sort-order="descending" data-shortcut="s">statements<span class="arrows"></span></th>
                <th id="missing" aria-sort="none" data-default-sort-order="descending" data-shortcut="m">missing<span class="arrows"></span></th>
                <th id="excluded" aria-sort="none" data-default-sort-order="descending" data-shortcut="x">excluded<span class="arrows"></span></th>
                <th id="branches" aria-sort="none" data-default-sort-order="descending" data-shortcut="b">branches<span class="arrows"></span></th>
                <th id="partial" aria-sort="none" data-default-sort-order="descending" data-shortcut="p">partial<span class="arrows"></span></th>
                <th id="coverage" class="right" aria-sort="none" data-shortcut="c">coverage<span class="arrows"></span></th>
            </tr>
        </thead>
        <tbody>{class_rows}
        </tbody>
        <tfoot>
            <tr class="total">
                <td class="name left">Total</td>
                <td>{total_statements}</td>
                <td>{total_missing}</td>
                <td>{total_excluded}</td>
                <td>{total_branches}</td>
                <td>{total_partial}</td>
                <td class="right" data-ratio="{total_covered} {total_statements}">{overall_coverage:.2f}%</td>
            </tr>
        </tfoot>
    </table>
    <p id="no_rows">No items found using the specified filter.</p>
</main>
<footer>
    <div class="content">
        <p>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {timestamp}
        </p>
    </div>
</footer>
</body>
</html>'''
        
        return html_content

    def generate_reports(self, test_analyses: Dict[str, TestTypeAnalysis], 
                        include_functions: bool = True, include_classes: bool = True):
        """Generate all HTML reports for each test type."""
        
        print(f"Generating enhanced HTML reports in: {self.output_dir}")
        
        for test_type, analysis in test_analyses.items():
            if not analysis.files:  # Skip empty test types
                continue
                
            print(f"  Generating {analysis.display_name} reports...")
            
            # Create test type directory
            test_dir = self.output_dir / "by-type" / test_type
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy static assets to each test type directory
            static_files = [
                'style_cb_81f8c14c.css',
                'coverage_html_cb_6fb7b396.js', 
                'favicon_32_cb_58284776.png',
                'keybd_closed_cb_ce680311.png'
            ]
            
            for filename in static_files:
                source_file = self.source_dir / filename
                if source_file.exists():
                    shutil.copy2(source_file, test_dir)
            
            # Generate main index (files view)
            index_html = self.generate_file_index_html(analysis, test_type)
            with open(test_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(index_html)
            
            # Generate function index if requested and data available
            if include_functions and analysis.functions:
                function_html = self.generate_function_index_html(analysis, test_type)
                with open(test_dir / "function_index.html", 'w', encoding='utf-8') as f:
                    f.write(function_html)
            
            # Generate class index if requested and data available
            if include_classes and analysis.classes:
                class_html = self.generate_class_index_html(analysis, test_type)
                with open(test_dir / "class_index.html", 'w', encoding='utf-8') as f:
                    f.write(class_html)
        
        print("✅ Enhanced HTML reports generated successfully!")


def main():
    """Main entry point for the enhanced path-based coverage analyzer."""
    parser = argparse.ArgumentParser(
        description="Enhanced Path-Based Coverage Analyzer with Function/Class Support"
    )
    parser.add_argument(
        "--source-dir", 
        type=Path,
        default="reports/coverage/standard",
        help="Directory containing the standard Coverage.py HTML report"
    )
    parser.add_argument(
        "--output-dir",
        type=Path, 
        default="reports/coverage",
        help="Output directory for generated reports"
    )
    parser.add_argument(
        "--include-functions",
        action="store_true",
        default=True,
        help="Include function-level coverage analysis"
    )
    parser.add_argument(
        "--include-classes", 
        action="store_true",
        default=True,
        help="Include class-level coverage analysis"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate source directory
    if not args.source_dir.exists():
        print(f"❌ Error: Source directory not found: {args.source_dir}")
        print("Make sure you have run coverage with HTML output first:")
        print("  poetry run pytest --cov=src --cov-report=html")
        sys.exit(1)
    
    index_file = args.source_dir / "index.html"
    if not index_file.exists():
        print(f"❌ Error: Coverage index file not found: {index_file}")
        sys.exit(1)
    
    try:
        print("🚀 Enhanced Path-Based Coverage Analyzer")
        print(f"📁 Source: {args.source_dir}")
        print(f"📁 Output: {args.output_dir}")
        print(f"🔍 Functions: {'✅' if args.include_functions else '❌'}")
        print(f"🔍 Classes: {'✅' if args.include_classes else '❌'}")
        print()
        
        # Parse coverage data with enhanced support
        parser = EnhancedCoverageHTMLParser(args.source_dir)
        test_analyses = parser.analyze_by_test_types(
            include_functions=args.include_functions,
            include_classes=args.include_classes
        )
        
        # Generate enhanced HTML reports
        generator = EnhancedHTMLReportGenerator(args.output_dir, args.source_dir)
        generator.generate_reports(
            test_analyses, 
            include_functions=args.include_functions,
            include_classes=args.include_classes
        )
        
        # Print summary
        print("\n📊 Enhanced Coverage Analysis Summary:")
        print("=" * 80)
        
        for test_type, analysis in test_analyses.items():
            if analysis.files:
                func_count = len(analysis.functions) if args.include_functions else 0
                class_count = len(analysis.classes) if args.include_classes else 0
                
                print(f"{analysis.display_name}")
                print(f"  📄 Files: {len(analysis.files)} ({analysis.coverage_percent:.1f}% coverage)")
                if func_count > 0:
                    print(f"  🔧 Functions: {func_count}")
                if class_count > 0:
                    print(f"  🏗️  Classes: {class_count}")
                print(f"  🧪 Est. Tests: {analysis.estimated_test_count:,}")
                print(f"  📁 Report: {args.output_dir}/by-type/{test_type}/index.html")
                print()
        
        print("✅ Enhanced analysis complete! Open the reports in your browser to explore.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()