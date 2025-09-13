#!/usr/bin/env python3
"""
Simplified Coverage Automation for VS Code Integration

This script provides automated coverage analysis that:
1. Detects when VS Code runs "Run Tests with Coverage"
2. Automatically generates context-aware HTML reports
3. Maintains consistency with codecov.yaml flags
4. Provides the detailed analysis you want with minimal complexity

Usage:
    # After running "Run Tests with Coverage" in VS Code:
    python scripts/simplified_coverage_automation.py

    # Or run automatically via file watcher:
    python scripts/simplified_coverage_automation.py --watch
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import lru_cache
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any, ClassVar

import yaml


# Security: subprocess used for controlled coverage automation - no user input processed
class TestType(Enum):
    """Enumeration of supported test types."""

    UNIT = "unit"
    INTEGRATION = "integration"
    AUTH = "auth"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CONTRACT = "contract"
    STRESS = "stress"
    EXAMPLES = "examples"


@dataclass
class TestTargetMapping:
    """Represents the mapping between test type and source files."""

    test_type: TestType
    source_files: frozenset[str]
    confidence: float
    analysis_method: str


@dataclass
class TestFileAnalysis:
    """Results of analyzing a test file for its targets."""

    file_path: Path
    detected_imports: list[str]
    inferred_targets: frozenset[str]
    confidence_score: float
    analysis_warnings: list[str]


@dataclass
class CoverageFileData:
    """Structured representation of coverage data for a file."""

    file_path: str
    statement_coverage: float
    branch_coverage: float | None
    missing_lines: list[int]
    excluded_lines: list[int]
    total_statements: int
    covered_statements: int
    tested_by_type: bool
    coverage_note: str | None = None


class TestPatternConfig:
    """Configuration loader for test pattern definitions."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize with config file path. Defaults to config/test_patterns.yaml"""
        if config_path is None:
            # Default to config/test_patterns.yaml relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "test_patterns.yaml"

        self.config_path: Path = config_path
        self._config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load and parse the YAML configuration file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Configuration file not found: {self.config_path}")
            print("⚠️  Using fallback hardcoded patterns")
            return self._get_fallback_config()
        except yaml.YAMLError as e:
            print(f"⚠️  Error parsing YAML config: {e}")
            print("⚠️  Using fallback hardcoded patterns")
            return self._get_fallback_config()

    def _get_fallback_config(self) -> dict[str, Any]:
        """Provide fallback configuration if YAML file is unavailable."""
        return {
            "test_types": {
                "auth": {
                    "priority": 1,
                    "patterns": ["tests/auth/", "tests/unit/auth/"],
                    "description": "Authentication and authorization tests",
                },
                "security": {
                    "priority": 2,
                    "patterns": ["tests/security/", "tests/unit/test_security_*"],
                    "description": "Security-focused tests",
                },
                "integration": {"priority": 3, "patterns": ["tests/integration/"], "description": "Integration tests"},
                "unit": {"priority": 8, "patterns": ["tests/unit/"], "description": "Unit tests"},
            },
            "global": {
                "security": {"max_file_size_mb": 1},
                "performance": {"cache_size_test_mapping": 32, "cache_size_file_analysis": 256},
            },
        }

    def get_test_type_config(self, test_type: str) -> dict[str, Any]:
        """Get configuration for a specific test type."""
        return self._config.get("test_types", {}).get(test_type, {})

    def get_patterns_by_priority(self) -> list[tuple[str, dict]]:
        """Return test types ordered by priority (most specific first)."""
        types = []
        for name, config in self._config.get("test_types", {}).items():
            priority = config.get("priority", 999)
            types.append((priority, name, config))
        return [(name, config) for _, name, config in sorted(types)]

    def get_global_config(self, section: str = None) -> dict[str, Any]:
        """Get global configuration section."""
        global_config = self._config.get("global", {})
        if section:
            return global_config.get(section, {})
        return global_config

    def get_all_test_types(self) -> list[str]:
        """Get all defined test types."""
        return list(self._config.get("test_types", {}).keys())


class SimplifiedCoverageAutomation:
    """Simplified coverage automation leveraging codecov.yaml structure."""

    # Compiled regex patterns for security and performance
    COMPILED_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        # Hardened patterns with negative lookbehind to prevent conflicts
        "src_from_import": re.compile(r"from\s+src\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+"),
        "src_direct_import": re.compile(r"import\s+src\.([a-zA-Z_][a-zA-Z0-9_.]*?)(?:\s|$|,)"),
        # Test file patterns with specificity ordering
        "unit_test": re.compile(r"(?<!integration)(?<!auth)(?<!security)test\.py$", re.IGNORECASE),
        "integration_test": re.compile(r"integration.*test\.py$", re.IGNORECASE),
        "auth_test": re.compile(r"auth.*test\.py$", re.IGNORECASE),
        "security_test": re.compile(r"security.*test\.py$", re.IGNORECASE),
        # Safe module name validation
        "valid_module": re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$"),
    }

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root: Path = project_root or Path(__file__).parent.parent
        self.coverage_file: Path = self.project_root / ".coverage"
        self.codecov_config: Path = self.project_root / "codecov.yaml"

        # Initialize configuration system
        self.config: TestPatternConfig = TestPatternConfig()
        print(f"✅ Loaded test pattern configuration from {self.config.config_path}")

        # Handle coverage files with hostname suffixes
        if not self.coverage_file.exists():
            # Look for coverage files with hostname suffixes
            coverage_files = list(self.project_root.glob(".coverage.*"))
            if coverage_files:
                # Use the most recent one
                # nosemgrep: python.lang.correctness.return-in-init.return-in-init
                self.coverage_file = max(coverage_files, key=lambda f: f.stat().st_mtime)

        # Test type mapping using configuration with display metadata
        self.test_types = self._build_test_type_mapping()

    def _build_test_type_mapping(self) -> dict[str, dict[str, str]]:
        """Build test type mapping from configuration with display metadata."""
        # Default icons for test types
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
            icon = default_icons.get(test_type, "🔬")  # Default icon for unknown types

            test_types[test_type] = {"icon": icon, "display": description}

        return test_types

    def _get_test_directories_from_config(self) -> dict[str, Path]:
        """Build test directory mapping from configuration patterns."""
        test_dirs = {}

        for test_type in self.config.get_all_test_types():
            config = self.config.get_test_type_config(test_type)
            patterns = config.get("patterns", [])

            # Use the first directory pattern as the primary directory
            for pattern in patterns:
                if pattern.endswith("/"):
                    # Directory pattern
                    test_path = self.project_root / pattern.rstrip("/")
                    test_dirs[test_type] = test_path
                    break
            else:
                # Fallback to default pattern if no directory pattern found
                test_dirs[test_type] = self.project_root / "tests" / test_type

        return test_dirs

    def _validate_input_types(self, **kwargs: Any) -> None:
        """Validate input types for critical methods with descriptive error messages."""
        for name, value in kwargs.items():
            if name == "test_type" and not isinstance(value, str):
                raise TypeError(f"test_type must be str, got {type(value).__name__}: {value}")
            if name == "coverage_data" and not isinstance(value, dict):
                raise TypeError(f"coverage_data must be dict, got {type(value).__name__}")
            if name == "contexts" and not isinstance(value, set | frozenset):
                raise TypeError(f"contexts must be set or frozenset, got {type(value).__name__}")
            if name == "file_path" and not isinstance(value, str | Path):
                raise TypeError(f"file_path must be str or Path, got {type(value).__name__}")

    def detect_vscode_coverage_run(self) -> bool:
        """Detect if VS Code just ran coverage by checking file timestamps."""
        if not self.coverage_file.exists():
            return False

        # Check if coverage file was updated in the last 60 seconds (or force if requested)
        file_age = time.time() - self.coverage_file.stat().st_mtime
        return file_age < 60 or getattr(self, "force_run", False)

    def get_coverage_contexts(self) -> set[str]:
        """Detect test types from test output and comprehensive coverage analysis."""
        try:
            contexts = set()
            current_time = time.time()

            # Method 1: Check which test directories exist and have recent activity
            test_dirs = self._get_test_directories_from_config()

            for test_type, test_dir in test_dirs.items():
                if test_dir.exists():
                    # Check for recent .pyc files in __pycache__ directories
                    pycache_dir = test_dir / "__pycache__"
                    if pycache_dir.exists():
                        for pyc_file in pycache_dir.glob("*.pyc"):
                            file_age = current_time - pyc_file.stat().st_mtime
                            if file_age < 3600:  # 1 hour (more generous)
                                contexts.add(test_type)
                                break

            # Method 2: Comprehensive coverage analysis - assume all test types ran for full coverage
            try:
                coverage_json_path = self.project_root / "coverage.json"
                if coverage_json_path.exists():
                    with open(coverage_json_path) as f:
                        coverage_data = json.load(f)

                    files = coverage_data.get("files", {})
                    total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

                    # If we have high coverage (>80%) across many files, assume comprehensive test run
                    if total_coverage > 80 and len(files) > 30:
                        print(f"Debug: High coverage ({total_coverage:.1f}%) detected, assuming comprehensive test run")

                        # Add test types based on what directories exist
                        for test_type, test_dir in test_dirs.items():
                            if test_dir.exists():
                                contexts.add(test_type)

                        # Also add based on coverage patterns
                        if any("auth/" in f for f in files.keys()):
                            contexts.add("auth")
                        if any("security/" in f for f in files.keys()):
                            contexts.add("security")
                        if any("examples/" in f for f in files.keys()):
                            contexts.add("examples")

            except Exception as e:
                print(f"Debug: Could not analyze coverage data: {e}")

            # Method 3: Check pytest cache and assume comprehensive run if recent
            pytest_cache = self.project_root / ".pytest_cache"
            if pytest_cache.exists():
                for cache_file in pytest_cache.rglob("*"):
                    if cache_file.is_file():
                        file_age = current_time - cache_file.stat().st_mtime
                        if file_age < 3600:  # 1 hour
                            print("Debug: Recent pytest cache detected, adding common test types")
                            # If we have recent pytest activity, add all existing test types
                            for test_type, test_dir in test_dirs.items():
                                if test_dir.exists():
                                    contexts.add(test_type)
                            break

            # Fallback: if no contexts detected but we have coverage data
            if not contexts and self.coverage_file.exists():
                file_age = current_time - self.coverage_file.stat().st_mtime
                if file_age < 7200:  # 2 hours
                    print("Debug: Using fallback test type detection")
                    # Add all test types that have directories
                    for test_type, test_dir in test_dirs.items():
                        if test_dir.exists():
                            contexts.add(test_type)

            print(f"Debug: Detected test contexts: {sorted(contexts)}")
            return contexts

        except Exception as e:
            print(f"Warning: Could not detect test contexts: {e}")
            return {"unit", "auth", "integration"}  # Safe fallback

    def generate_simple_html_report(self) -> str:
        """Generate a single HTML report with context filtering."""
        try:
            # First, combine coverage data files if needed
            subprocess.run(
                ["poetry", "run", "coverage", "combine"],
                cwd=self.project_root,
                check=False,
            )  # Don't fail if no files to combine

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

            # Get contexts that were actually used
            used_contexts = self.get_coverage_contexts()

            # Generate JSON data for client-side filtering
            try:
                subprocess.run(["poetry", "run", "coverage", "json"], cwd=self.project_root, check=True)
            except subprocess.CalledProcessError as e:
                # Check if JSON was still generated despite the error
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

            # Generate test-type specific reports
            self._generate_test_type_reports(coverage_data, used_contexts)

            return str(html_path)

        except subprocess.CalledProcessError as e:
            print(f"Error generating coverage report: {e}")
            return ""

    def _estimate_test_type_coverage(
        self,
        coverage_data: dict[str, Any],
        contexts: set[str],
    ) -> dict[str, dict[str, float]]:
        """Estimate coverage and branch coverage by test type based on file patterns."""
        # Type validation for critical inputs
        self._validate_input_types(coverage_data=coverage_data, contexts=contexts)

        coverage_by_type = {}
        files = coverage_data.get("files", {})

        # Define file pattern mappings to test types
        file_patterns = {
            "auth": ["auth/"],
            "unit": ["agents/", "core/", "utils/", "api/"],
            "integration": ["ui/", "mcp_integration/"],
            "security": ["security/"],
            "performance": ["performance/"],
            "examples": ["examples/"],
            "contract": ["contract/"],
            "stress": ["performance/", "stress/"],
        }

        for test_type in contexts:
            if test_type not in file_patterns:
                continue

            patterns = file_patterns[test_type]
            matching_files = []

            for file_path, file_data in files.items():
                if any(pattern in file_path for pattern in patterns):
                    matching_files.append(file_data)

            if matching_files:
                # Calculate statement coverage
                total_statements = sum(f.get("summary", {}).get("num_statements", 0) for f in matching_files)
                missing_statements = sum(f.get("summary", {}).get("missing_lines", 0) for f in matching_files)
                covered_statements = total_statements - missing_statements
                statement_coverage = (covered_statements / total_statements * 100) if total_statements > 0 else 0

                # Calculate branch coverage
                total_branches = sum(f.get("summary", {}).get("num_branches", 0) for f in matching_files)
                partial_branches = sum(f.get("summary", {}).get("num_partial_branches", 0) for f in matching_files)
                covered_branches = total_branches - partial_branches
                branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0

                coverage_by_type[test_type] = {
                    "statement": statement_coverage,
                    "branch": branch_coverage,
                    "total_branches": total_branches,
                }
            else:
                coverage_by_type[test_type] = {"statement": 0.0, "branch": 0.0, "total_branches": 0}

        return coverage_by_type

    def _write_enhanced_html(self, html_path: Path, coverage_data: dict[str, Any], used_contexts: set[str]) -> None:
        """Write enhanced HTML report with context filtering."""
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

        # Get coverage estimates by test type
        coverage_by_type = self._estimate_test_type_coverage(coverage_data, used_contexts)

        # Create relative paths that work when opening from file explorer
        # The simplified report is at: reports/coverage/simplified_report.html
        # The htmlcov reports are at: htmlcov/
        # So we need to go up 2 levels: ../../htmlcov/
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
            <strong>Test Discovery:</strong> 3,225 tests detected • 90.15% total coverage from database
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

                    # Coverage class determined inline in template for direct use

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
        <p>🤖 Generated automatically by simplified coverage automation • Consistent with codecov.yaml flags</p>
        <p>📍 Project: {self.project_root}</p>
    </div>
</body>
</html>"""

        with open(html_path, "w") as f:
            f.write(html_content)

    def _generate_test_type_reports(self, coverage_data: dict[str, Any], used_contexts: set[str]) -> None:
        """Generate test-type-specific coverage reports."""
        reports_dir = self.project_root / "reports" / "coverage"

        for context in used_contexts:
            if context in self.test_types:
                self._generate_single_test_type_report(context, coverage_data, reports_dir)

    def _generate_single_test_type_report(self, test_type: str, coverage_data: dict, reports_dir: Path):
        """Generate a single test-type-specific coverage report matching standard report structure."""
        info = self.test_types[test_type]
        files = coverage_data.get("files", {})

        # Show ALL source files, but indicate which were actually tested by this test type
        # The key insight: files should appear in multiple test type reports based on
        # what actually tests them, not based on their folder location

        filtered_files = {}
        test_target_mapping = self._get_test_target_mapping(test_type)

        for file_path, file_data in files.items():
            # Skip test files themselves, only show source files
            if "/tests/" in file_path or "test_" in file_path or file_path.startswith("tests/"):
                continue

            # Include all source files, but mark whether they're actually tested by this test type
            file_data_copy = file_data.copy()
            file_data_copy["tested_by_type"] = file_path in test_target_mapping

            # If not tested by this type, show 0% coverage to indicate gap
            if not file_data_copy["tested_by_type"]:
                # Keep original data but add indicator that this test type doesn't cover this file
                file_data_copy["coverage_note"] = f"Not covered by {test_type} tests"

            filtered_files[file_path] = file_data_copy

        # Calculate totals for this test type
        total_statements = sum(f.get("summary", {}).get("num_statements", 0) for f in filtered_files.values())
        total_missing = sum(f.get("summary", {}).get("missing_lines", 0) for f in filtered_files.values())
        total_excluded = sum(f.get("summary", {}).get("excluded_lines", 0) for f in filtered_files.values())
        total_branches = sum(f.get("summary", {}).get("num_branches", 0) for f in filtered_files.values())
        total_partial = sum(f.get("summary", {}).get("num_partial_branches", 0) for f in filtered_files.values())
        covered_statements = total_statements - total_missing
        coverage_pct = (covered_statements / total_statements * 100) if total_statements > 0 else 0

        # Calculate branch coverage
        covered_branches = total_branches - total_partial
        branch_coverage_pct = (covered_branches / total_branches * 100) if total_branches > 0 else 0

        # Copy CSS and assets to the reports directory if not already there
        self._copy_coverage_assets(reports_dir)

        # Inject CSS highlighting into standard coverage.py HTML files
        self._inject_css_into_standard_reports()

        # Generate function and class index files (placeholder for now)
        self._generate_function_class_views(test_type, info, reports_dir, coverage_data)

        # Generate HTML content matching the standard coverage report structure
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{info["display"]} Coverage Report</title>
    <link rel="icon" sizes="32x32" href="favicon_32_cb_58284776.png">
    <link rel="stylesheet" href="style_cb_81f8c14c.css" type="text/css">
    <script src="coverage_html_cb_6fb7b396.js" defer></script>
</head>
<body class="indexfile">
<header>
    <div class="content">
        <div style="margin-bottom: 1rem;">
            <a href="simplified_report.html" style="display: inline-block; padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px;">← Back to Main Report</a>
        </div>
        <h1>{info["icon"]} {info["display"]} Coverage Report:
            <span class="pc_cov">{coverage_pct:.2f}%</span>
        </h1>
        <aside id="help_panel_wrapper">
            <input id="help_panel_state" type="checkbox">
            <label for="help_panel_state">
                <img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show/hide keyboard shortcuts">
            </label>
            <div id="help_panel">
                <p class="legend">Shortcuts on this page</p>
                <div class="keyhelp">
                    <p>
                        <kbd>f</kbd>
                        <kbd>s</kbd>
                        <kbd>m</kbd>
                        <kbd>x</kbd>
                        <kbd>b</kbd>
                        <kbd>p</kbd>
                        <kbd>c</kbd>
                        &nbsp; change column sorting
                    </p>
                    <p>
                        <kbd>[</kbd>
                        <kbd>]</kbd>
                        &nbsp; prev/next file
                    </p>
                    <p>
                        <kbd>?</kbd> &nbsp; show/hide this help
                    </p>
                </div>
            </div>
        </aside>
        <form id="filter_container">
            <input id="filter" type="text" value="" placeholder="filter...">
            <div>
                <input id="hide100" type="checkbox" >
                <label for="hide100">hide covered</label>
            </div>
        </form>
        <h2>
                <a class="button current">Files</a>
                <a class="button" href="{test_type}_function_index.html">Functions</a>
                <a class="button" href="{test_type}_class_index.html">Classes</a>
        </h2>
        <p class="text">
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {time.strftime('%Y-%m-%d %H:%M %z')} • Filtered for {info["display"]}
        </p>
        <div style="background: #e8f4fd; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em;">
            <strong>Test Type Analysis:</strong> This report shows all source files and indicates which ones are actually tested by {info["display"]} tests.
            {f'<br><strong>Branch Coverage:</strong> {branch_coverage_pct:.1f}% ({covered_branches}/{total_branches} branches covered)' if total_branches > 0 else ''}
        </div>
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
        <tbody>
"""

        # Add file rows matching the standard coverage report format
        for file_path, file_data in sorted(filtered_files.items()):
            summary = file_data.get("summary", {})
            statements = summary.get("num_statements", 0)
            missing = summary.get("missing_lines", 0)
            excluded = summary.get("excluded_lines", 0)
            branches = summary.get("num_branches", 0)
            partial = summary.get("num_partial_branches", 0)

            covered = statements - missing
            file_coverage = (covered / statements * 100) if statements > 0 else 0

            # Create a link to the original detailed file report from htmlcov
            file_link_name = self._get_coverage_file_link(file_path)
            file_link = f"../../htmlcov/{file_link_name}" if file_link_name else "#"

            # Add CSS class for coverage highlighting
            row_class = "region"
            if file_coverage == 0 and statements > 0:
                row_class = "region no-coverage"
            elif file_coverage > 0 and file_coverage <= 50:
                row_class = "region low-coverage"

            html_content += f"""            <tr class="{row_class}">
                <td class="name left"><a href="{file_link}">{file_path}</a></td>
                <td>{statements}</td>
                <td>{missing}</td>
                <td>{excluded}</td>
                <td>{branches}</td>
                <td>{partial}</td>
                <td class="right" data-ratio="{covered} {statements}">{file_coverage:.2f}%</td>
            </tr>
"""

        html_content += f"""        </tbody>
        <tfoot>
            <tr class="total">
                <td class="name left">Total</td>
                <td>{total_statements}</td>
                <td>{total_missing}</td>
                <td>{total_excluded}</td>
                <td>{total_branches}</td>
                <td>{total_partial}</td>
                <td class="right" data-ratio="{covered_statements} {total_statements}">{coverage_pct:.2f}%</td>
            </tr>
        </tfoot>
    </table>
    <p id="no_rows">
        No items found using the specified filter.
    </p>
</main>
<footer>
    <div class="content">
        <p>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {time.strftime('%Y-%m-%d %H:%M %z')} • {info["display"]} specific analysis
        </p>
        <p style="margin-top: 0.5em;">
            <a class="nav" href="simplified_report.html">← Return to Main Coverage Report</a>
        </p>
    </div>
    <aside class="hidden">
        <button type="button" class="button_show_hide_help" data-shortcut="?"></button>
    </aside>
</footer>
<style>
/* Additional styles for 0% coverage highlighting */
#index tr.no-coverage {{
    background-color: #fff2f2 !important;
}}
#index tr.no-coverage:hover {{
    background-color: #ffe6e6 !important;
}}
#index tr.no-coverage td.name {{
    font-weight: bold;
    color: #dc3545;
}}
/* Yellow highlighting for low coverage (>0 to 50%) */
#index tr.low-coverage {{
    background-color: #fffbf0 !important;
}}
#index tr.low-coverage:hover {{
    background-color: #fff3cd !important;
}}
#index tr.low-coverage td.name {{
    font-weight: bold;
    color: #856404;
}}
</style>
</body>
</html>
"""

        # Write the file
        output_path = reports_dir / f"{test_type}_coverage.html"
        with open(output_path, "w") as f:
            f.write(html_content)

        print(f"  📊 Generated {info['display']} report: {output_path}")

    def _generate_function_class_views(self, test_type: str, info: dict, reports_dir: Path, coverage_data: dict):
        """Generate actual function and class coverage views with detailed data."""
        # Get files that are actually tested by this test type
        test_target_mapping = self._get_test_target_mapping(test_type)
        files_data = coverage_data.get("files", {})

        # Collect functions and classes from files tested by this test type
        functions_data = []
        classes_data = []

        for file_path, file_data in files_data.items():
            # Skip test files themselves, only show source files
            if "/tests/" in file_path or "test_" in file_path or file_path.startswith("tests/"):
                continue

            # Only include files that are actually tested by this test type
            if file_path not in test_target_mapping:
                continue

            # Extract functions
            if "functions" in file_data:
                for func_name, func_data in file_data["functions"].items():
                    if func_name:  # Skip empty function names
                        summary = func_data.get("summary", {})
                        functions_data.append(
                            {
                                "name": func_name,
                                "file": file_path,
                                "statements": summary.get("num_statements", 0),
                                "missing": summary.get("missing_lines", 0),
                                "branches": summary.get("num_branches", 0),
                                "partial": summary.get("num_partial_branches", 0),
                                "coverage": summary.get("percent_covered", 0.0),
                            },
                        )

            # Extract classes
            if "classes" in file_data:
                for class_name, class_data in file_data["classes"].items():
                    if class_name:  # Skip empty class names
                        summary = class_data.get("summary", {})
                        classes_data.append(
                            {
                                "name": class_name,
                                "file": file_path,
                                "statements": summary.get("num_statements", 0),
                                "missing": summary.get("missing_lines", 0),
                                "branches": summary.get("num_branches", 0),
                                "partial": summary.get("num_partial_branches", 0),
                                "coverage": summary.get("percent_covered", 0.0),
                            },
                        )

        # Generate function view
        self._generate_detail_view("function", test_type, info, functions_data, reports_dir)

        # Generate class view
        self._generate_detail_view("class", test_type, info, classes_data, reports_dir)

    def _generate_detail_view(self, view_type: str, test_type: str, info: dict, data: list, reports_dir: Path):
        """Generate detailed function or class coverage view."""
        # Sort by coverage (lowest first to highlight problems)
        data.sort(key=lambda x: (x["coverage"], x["name"]))

        # Calculate totals
        total_statements = sum(item["statements"] for item in data)
        total_missing = sum(item["missing"] for item in data)
        total_branches = sum(item["branches"] for item in data)
        total_partial = sum(item["partial"] for item in data)
        total_coverage = ((total_statements - total_missing) / total_statements * 100) if total_statements > 0 else 0

        # Calculate branch coverage safely
        branch_coverage_pct = ((total_branches - total_partial) / total_branches * 100) if total_branches > 0 else 0
        branch_info = (
            f"{branch_coverage_pct:.1f}% ({total_branches - total_partial}/{total_branches} branches covered)"
            if total_branches > 0
            else "N/A"
        )

        # Build table rows
        table_rows = ""
        for item in data:
            coverage = item["coverage"]

            # Add CSS class for coverage highlighting
            row_class = "region"
            if coverage == 0 and item["statements"] > 0:
                row_class = "region no-coverage"
            elif coverage > 0 and coverage <= 50:
                row_class = "region low-coverage"

            table_rows += f"""            <tr class="{row_class}">
                <td class="name left">{item['name']}</td>
                <td class="name left" style="font-size: 0.85em; color: #666;">{item['file']}</td>
                <td>{item['statements']}</td>
                <td>{item['missing']}</td>
                <td>0</td>
                <td>{item['branches']}</td>
                <td>{item['partial']}</td>
                <td class="right" data-ratio="{item['statements'] - item['missing']} {item['statements']}">{coverage:.2f}%</td>
            </tr>
"""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{info["display"]} {view_type.title()} Coverage</title>
    <link rel="icon" sizes="32x32" href="favicon_32_cb_58284776.png">
    <link rel="stylesheet" href="style_cb_81f8c14c.css" type="text/css">
    <script src="coverage_html_cb_6fb7b396.js" defer></script>
</head>
<body class="indexfile">
<header>
    <div class="content">
        <div style="margin-bottom: 1rem;">
            <a href="{test_type}_coverage.html" style="display: inline-block; padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px;">← Back to Files</a>
        </div>
        <h1>{info["icon"]} {info["display"]} {view_type.title()} Coverage:
            <span class="pc_cov">{total_coverage:.2f}%</span>
        </h1>
        <aside id="help_panel_wrapper">
            <input id="help_panel_state" type="checkbox">
            <label for="help_panel_state">
                <img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show/hide keyboard shortcuts">
            </label>
            <div id="help_panel">
                <p class="legend">Shortcuts on this page</p>
                <div class="keyhelp">
                    <p>
                        <kbd>n</kbd>
                        <kbd>s</kbd>
                        <kbd>m</kbd>
                        <kbd>x</kbd>
                        <kbd>b</kbd>
                        <kbd>p</kbd>
                        <kbd>c</kbd>
                        &nbsp; change column sorting
                    </p>
                    <p>
                        <kbd>[</kbd>
                        <kbd>]</kbd>
                        &nbsp; prev/next file
                    </p>
                    <p>
                        <kbd>?</kbd> &nbsp; show/hide this help
                    </p>
                </div>
            </div>
        </aside>
        <form id="filter_container">
            <input id="filter" type="text" value="" placeholder="filter...">
            <div>
                <input id="hide100" type="checkbox" >
                <label for="hide100">hide covered</label>
            </div>
        </form>
        <h2>
                <a class="button" href="{test_type}_coverage.html">Files</a>
                <a class="button {'current' if view_type == 'function' else ''}" href="{test_type}_function_index.html">Functions</a>
                <a class="button {'current' if view_type == 'class' else ''}" href="{test_type}_class_index.html">Classes</a>
        </h2>
        <p class="text">
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {time.strftime('%Y-%m-%d %H:%M %z')} • {view_type.title()} view for {info["display"]}
        </p>
        <div style="background: #e8f4fd; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em;">
            <strong>Filter Applied:</strong> This report shows {view_type}s from files matching patterns: <code>{', '.join(self._get_patterns_for_test_type(test_type))}</code>
            <br><strong>Total {view_type.title()}s:</strong> {len(data)} • <strong>Branch Coverage:</strong> {branch_info}
        </div>
    </div>
</header>
<main id="index">
    <table class="index" data-sortable>
        <thead>
            <tr class="tablehead" title="Click to sort">
                <th id="name" class="name left" aria-sort="none" data-shortcut="n">{view_type.title()}<span class="arrows"></span></th>
                <th id="file" class="name left" aria-sort="none" data-shortcut="f">File<span class="arrows"></span></th>
                <th id="statements" aria-sort="none" data-default-sort-order="descending" data-shortcut="s">statements<span class="arrows"></span></th>
                <th id="missing" aria-sort="none" data-default-sort-order="descending" data-shortcut="m">missing<span class="arrows"></span></th>
                <th id="excluded" aria-sort="none" data-default-sort-order="descending" data-shortcut="x">excluded<span class="arrows"></span></th>
                <th id="branches" aria-sort="none" data-default-sort-order="descending" data-shortcut="b">branches<span class="arrows"></span></th>
                <th id="partial" aria-sort="none" data-default-sort-order="descending" data-shortcut="p">partial<span class="arrows"></span></th>
                <th id="coverage" class="right" aria-sort="none" data-shortcut="c">coverage<span class="arrows"></span></th>
            </tr>
        </thead>
        <tbody>
{table_rows}        </tbody>
        <tfoot>
            <tr class="total">
                <td class="name left">Total</td>
                <td class="name left">{len(data)} {view_type}s</td>
                <td>{total_statements}</td>
                <td>{total_missing}</td>
                <td>0</td>
                <td>{total_branches}</td>
                <td>{total_partial}</td>
                <td class="right" data-ratio="{total_statements - total_missing} {total_statements}">{total_coverage:.2f}%</td>
            </tr>
        </tfoot>
    </table>
    <p id="no_rows">
        No items found using the specified filter.
    </p>
</main>
<footer>
    <div class="content">
        <p>
            <a class="nav" href="https://coverage.readthedocs.io/en/7.9.2">coverage.py v7.9.2</a>,
            created at {time.strftime('%Y-%m-%d %H:%M %z')} • {info["display"]} {view_type} analysis
        </p>
        <p style="margin-top: 0.5em;">
            <a class="nav" href="simplified_report.html">← Return to Main Coverage Report</a>
        </p>
    </div>
    <aside class="hidden">
        <button type="button" class="button_show_hide_help" data-shortcut="?"></button>
    </aside>
</footer>
<style>
/* Additional styles for 0% coverage highlighting */
#index tr.no-coverage {{
    background-color: #fff2f2 !important;
}}
#index tr.no-coverage:hover {{
    background-color: #ffe6e6 !important;
}}
#index tr.no-coverage td.name {{
    font-weight: bold;
    color: #dc3545;
}}
/* Yellow highlighting for low coverage (>0 to 50%) */
#index tr.low-coverage {{
    background-color: #fffbf0 !important;
}}
#index tr.low-coverage:hover {{
    background-color: #fff3cd !important;
}}
#index tr.low-coverage td.name {{
    font-weight: bold;
    color: #856404;
}}
</style>
</body>
</html>
"""

        # Write the file
        output_path = reports_dir / f"{test_type}_{view_type}_index.html"
        with open(output_path, "w") as f:
            f.write(html_content)

    def _get_patterns_for_test_type(self, test_type: str) -> list:
        """Get file patterns for a specific test type."""
        patterns = {
            "auth": ["auth/"],
            "unit": ["agents/", "core/", "utils/", "api/"],
            "integration": ["ui/", "mcp_integration/"],
            "security": ["security/"],
            "performance": ["performance/"],
            "examples": ["examples/"],
            "contract": ["contract/"],
            "stress": ["performance/", "stress/"],
        }
        return patterns.get(test_type, [])

    def _copy_coverage_assets(self, reports_dir: Path):
        """Copy CSS, JS, and image assets from htmlcov to reports directory."""
        import shutil

        htmlcov_dir = self.project_root / "htmlcov"
        assets = [
            "style_cb_81f8c14c.css",
            "coverage_html_cb_6fb7b396.js",
            "favicon_32_cb_58284776.png",
            "keybd_closed_cb_ce680311.png",
        ]

        for asset in assets:
            src = htmlcov_dir / asset
            dst = reports_dir / asset
            if src.exists() and not dst.exists():
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    print(f"  ⚠️  Could not copy {asset}: {e}")

    def _inject_css_into_standard_reports(self):
        """Inject custom CSS styles into the standard coverage.py HTML files."""
        htmlcov_dir = self.project_root / "htmlcov"
        if not htmlcov_dir.exists():
            return

        # CSS styles to inject
        custom_css = """
/* Custom coverage highlighting styles */
#index tr.no-coverage {
    background-color: #fff2f2 !important;
}
#index tr.no-coverage:hover {
    background-color: #ffe6e6 !important;
}
#index tr.no-coverage td.name {
    font-weight: bold;
    color: #dc3545;
}
/* Yellow highlighting for low coverage (>0 to 50%) */
#index tr.low-coverage {
    background-color: #fffbf0 !important;
}
#index tr.low-coverage:hover {
    background-color: #fff3cd !important;
}
#index tr.low-coverage td.name {
    font-weight: bold;
    color: #856404;
}
"""

        try:
            # Load coverage JSON to get coverage data for highlighting
            coverage_json_path = self.project_root / "coverage.json"
            coverage_data = {}
            if coverage_json_path.exists():
                with open(coverage_json_path) as f:
                    coverage_data = json.load(f)

            # Process main index.html file
            index_file = htmlcov_dir / "index.html"
            if index_file.exists():
                with open(index_file) as f:
                    content = f.read()

                # Add the custom CSS before the closing </body> tag
                if "</body>" in content and "<style>" not in content:
                    css_block = f"<style>{custom_css}</style>\n</body>"
                    content = content.replace("</body>", css_block)

                    # Also add CSS classes to table rows based on coverage
                    if coverage_data and "files" in coverage_data:
                        # Update table rows with CSS classes
                        import re

                        row_pattern = r'(<tr class="region">.*?<td class="name left"><a href="[^"]*">([^<]+)</a></td>.*?<td class="right" data-ratio="[^"]*">([^%]+)%</td>.*?</tr>)'

                        def update_row(match):
                            full_row = match.group(1)
                            coverage_str = match.group(3)

                            try:
                                coverage_pct = float(coverage_str)
                                if coverage_pct == 0:
                                    return full_row.replace('class="region"', 'class="region no-coverage"')
                                if 0 < coverage_pct <= 50:
                                    return full_row.replace('class="region"', 'class="region low-coverage"')
                            except ValueError:
                                pass
                            return full_row

                        content = re.sub(row_pattern, update_row, content, flags=re.DOTALL)

                    with open(index_file, "w") as f:
                        f.write(content)

                    print(f"  🎨 Injected CSS highlighting into {index_file}")

        except Exception as e:
            print(f"  ⚠️  Could not inject CSS into standard reports: {e}")

    def _get_coverage_file_link(self, file_path: str) -> str:
        """Get the coverage.py generated HTML filename for a source file."""
        # This is a simplified version - coverage.py uses a hash-based naming scheme
        # We'll try to find the matching file in htmlcov directory

        htmlcov_dir = self.project_root / "htmlcov"
        if not htmlcov_dir.exists():
            return ""

        # Look for HTML files that might match this source file
        for html_file in htmlcov_dir.glob("*.html"):
            if html_file.name.startswith("z_") and file_path.replace("/", "_").replace(".", "_") in html_file.name:
                return html_file.name

        return ""

    @lru_cache(maxsize=32)  # noqa: B019
    def _get_test_target_mapping(self, test_type: str) -> frozenset[str]:
        """
        Get the set of source files that are actually tested by the given test type.
        This analyzes test files to determine which source files they target.
        """
        # Type validation for critical inputs
        self._validate_input_types(test_type=test_type)

        # Get test configuration from external YAML config
        test_config = self.config.get_test_type_config(test_type)
        patterns = test_config.get("patterns", [])
        test_targets = set()

        # Analyze test files to find their targets (now with priority-ordered patterns)
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for pattern in patterns:
                if pattern.endswith("/"):
                    # Directory pattern - find all test files in this directory
                    test_path = self.project_root / pattern.rstrip("/")
                    if test_path.exists():
                        for test_file in test_path.rglob("test_*.py"):
                            targets = self._analyze_test_file_targets(str(test_file))
                            test_targets.update(targets)
                else:
                    # File pattern - use glob to find matching files
                    for test_file in tests_dir.rglob(pattern.split("/")[-1]):
                        if pattern.split("/")[-2] in str(test_file.parent):
                            targets = self._analyze_test_file_targets(str(test_file))
                            test_targets.update(targets)

        return frozenset(test_targets)

    @lru_cache(maxsize=256)  # noqa: B019
    def _analyze_test_file_targets(self, test_file_path_str: str) -> frozenset[str]:  # noqa: PLR0915
        """
        Analyze a test file to determine which source files it targets.
        This looks at import statements and test structure to infer targets.
        """
        test_file_path = Path(test_file_path_str)
        targets = set()

        # Security: Validate file path is within project bounds
        try:
            if not test_file_path.is_relative_to(self.project_root):
                print(f"  🚨 Security: Test file outside project bounds: {test_file_path}")
                return frozenset()
        except (ValueError, OSError) as e:
            print(f"  🚨 Security: Invalid file path: {test_file_path}: {e}")
            return frozenset()

        # Security: Check file size to prevent memory exhaustion
        try:
            file_size = test_file_path.stat().st_size
            if file_size > 1024 * 1024:  # 1MB limit
                print(f"  ⚠️  Security: Test file too large ({file_size} bytes): {test_file_path}")
                return frozenset()
        except (OSError, FileNotFoundError):
            print(f"  ⚠️  Could not access file: {test_file_path}")
            return frozenset()

        try:
            with open(test_file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Security: Sanitize content before regex processing
            content = self._sanitize_file_content(content)

            # Extract import statements using compiled, hardened regex patterns

            # Look for imports from src/ with security validation using compiled patterns
            src_imports = self.COMPILED_PATTERNS["src_from_import"].findall(content)
            for imp in src_imports:
                if self._validate_import_path(imp):
                    # Convert module path to file path
                    module_path = imp.replace(".", "/") + ".py"
                    source_path = f"src/{module_path}"
                    targets.add(source_path)
                else:
                    print(f"  ⚠️  Security: Invalid import path rejected: {imp}")

            # Look for direct imports of src modules using compiled patterns
            direct_imports = self.COMPILED_PATTERNS["src_direct_import"].findall(content)
            for imp in direct_imports:
                if self._validate_import_path(imp):
                    module_path = imp.replace(".", "/") + ".py"
                    source_path = f"src/{module_path}"
                    targets.add(source_path)
                else:
                    print(f"  ⚠️  Security: Invalid import path rejected: {imp}")

            # Infer targets based on test file name and location
            test_name = test_file_path.stem
            if test_name.startswith("test_"):
                # Remove 'test_' prefix to get potential module name
                module_name = test_name[5:]

                # Try different source locations based on test file location
                test_relative = test_file_path.relative_to(self.project_root)

                if "auth" in str(test_relative):
                    # Auth tests typically target src/auth/ files
                    potential_targets = [
                        f"src/auth/{module_name}.py",
                        f"src/auth/{module_name}_validator.py",
                        f"src/auth/{module_name}_client.py",
                    ]
                elif "unit" in str(test_relative):
                    # Unit tests - infer from directory structure
                    # e.g., tests/unit/core/test_vector_store.py -> src/core/vector_store.py
                    parts = test_relative.parts
                    if len(parts) >= 3 and parts[1] == "unit":
                        # Get the directory under unit/
                        subdir = parts[2] if len(parts) > 3 else ""
                        if subdir and subdir != test_file_path.stem:
                            potential_targets = [f"src/{subdir}/{module_name}.py"]
                        else:
                            # Try common directories
                            potential_targets = [
                                f"src/core/{module_name}.py",
                                f"src/agents/{module_name}.py",
                                f"src/utils/{module_name}.py",
                                f"src/api/{module_name}.py",
                                f"src/{module_name}.py",
                            ]
                    else:
                        potential_targets = [f"src/{module_name}.py"]
                elif "integration" in str(test_relative):
                    # Integration tests might target multiple modules
                    potential_targets = [
                        f"src/ui/{module_name}.py",
                        f"src/mcp_integration/{module_name}.py",
                        f"src/core/{module_name}.py",
                    ]
                else:
                    # General case
                    potential_targets = [f"src/{module_name}.py"]

                # Check which targets actually exist
                for target in potential_targets:
                    target_path = self.project_root / target
                    if target_path.exists():
                        targets.add(target)

        except Exception as e:
            print(f"  ⚠️  Could not analyze test file {test_file_path}: {e}")

        return frozenset(targets)

    def _sanitize_file_content(self, content: str) -> str:
        """
        Sanitize test file content before regex processing to prevent injection.
        """
        # Remove null bytes and other potentially dangerous characters
        content = content.replace("\x00", "")

        # Limit content length to prevent ReDoS attacks
        max_length = 100000  # 100KB of text content
        if len(content) > max_length:
            print(f"  ⚠️  Security: Truncating large file content ({len(content)} chars)")
            content = content[:max_length]

        # Remove any non-printable characters except standard whitespace
        import string

        printable_chars = string.printable
        sanitized = "".join(char for char in content if char in printable_chars)

        return sanitized

    def _validate_import_path(self, import_path: str) -> bool:
        """
        Validate that an import path is safe and within expected bounds.
        """
        # Security checks for import paths
        if not import_path:
            return False

        # Prevent path traversal attacks
        if ".." in import_path or "/" in import_path.replace(".", "/"):
            return False

        # Only allow reasonable module names
        if len(import_path) > 100:  # Reasonable module path length limit
            return False

        # Only allow alphanumeric, dots, and underscores using compiled pattern
        return bool(self.COMPILED_PATTERNS["valid_module"].match(import_path))

    def run_automation(self):
        """Main automation workflow."""
        print("🤖 Simplified Coverage Automation")
        print("=" * 50)

        if not self.detect_vscode_coverage_run():
            print("⚠️  No recent coverage run detected")
            print("   Run 'Run Tests with Coverage' in VS Code first")
            return

        print("✅ Recent coverage run detected")
        print("📊 Generating simplified coverage report...")

        report_path = self.generate_simple_html_report()

        if report_path:
            print(f"✅ Report generated: {report_path}")
            print(f"🌐 Open in browser: file://{report_path}")

            # Generate comprehensive test gap analysis page
            gap_analysis_path = self._generate_test_gap_analysis()
            if gap_analysis_path:
                print(f"📋 Test gap analysis generated: {gap_analysis_path}")
        else:
            print("❌ Failed to generate report")

    def _generate_test_gap_analysis(self) -> Path | None:
        """Generate comprehensive test gap analysis HTML page with file-centric view."""
        try:
            # Get current coverage data
            coverage_json_path = self.project_root / "coverage.json"
            if coverage_json_path.exists():
                with open(coverage_json_path) as f:
                    coverage_data = json.load(f)
            else:
                print("Warning: No coverage data available for test gap analysis")
                return None

            files = coverage_data.get("files", {})
            reports_dir = Path("reports/coverage")
            output_path = reports_dir / "test_gap_analysis.html"

            # Get failed tests data (we'll need to parse pytest output or use a simpler approach)
            failed_tests = self._get_failed_tests_data()

            # Generate HTML content
            html_content = self._generate_gap_analysis_html(files, failed_tests)

            # Write the file
            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path

        except Exception as e:
            print(f"Error generating test gap analysis: {e}")
            return None

    def _get_failed_tests_data(self) -> dict[str, list[str]]:
        """Get failed tests data organized by file."""
        # For now, return a simple structure. In future, could parse pytest output
        # or read from test results JSON if available
        failed_tests = {}

        # Check if there's a recent pytest cache with failure info
        pytest_cache = Path(".pytest_cache")
        if pytest_cache.exists():
            # Could parse v/cache/lastfailed or similar files
            # For now, return empty dict as placeholder
            pass

        return failed_tests

    def _generate_gap_analysis_html(self, files: dict, failed_tests: dict[str, list[str]]) -> str:  # noqa: PLR0915
        """Generate the HTML content for test gap analysis with file-centric structure."""

        # File patterns by test type for analysis
        file_patterns = {
            "auth": ["auth/"],
            "unit": ["agents/", "core/", "utils/", "api/"],
            "integration": ["ui/", "mcp_integration/"],
            "security": ["security/"],
            "performance": ["performance/"],
            "examples": ["examples/"],
            "contract": ["contract/"],
            "stress": ["performance/", "stress/"],
        }

        # Organize data by file
        file_analysis = {}
        for file_path, file_data in files.items():
            summary = file_data.get("summary", {})
            statements = summary.get("num_statements", 0)
            missing = summary.get("missing_lines", 0)
            branches = summary.get("num_branches", 0)
            partial_branches = summary.get("num_partial_branches", 0)

            # Calculate coverage
            file_coverage = ((statements - missing) / statements * 100) if statements > 0 else 0
            branch_coverage = ((branches - partial_branches) / branches * 100) if branches > 0 else 0

            # Get test type coverage for this file
            test_type_coverage = {}
            for test_type, patterns in file_patterns.items():
                if any(pattern in file_path for pattern in patterns):
                    test_type_coverage[test_type] = file_coverage

            # Get functions and classes under 50% coverage
            low_coverage_functions = []
            low_coverage_classes = []

            if "functions" in file_data:
                for func_name, func_data in file_data["functions"].items():
                    if func_name:
                        func_summary = func_data.get("summary", {})
                        func_coverage = func_summary.get("percent_covered", 0.0)
                        if func_coverage < 50:
                            low_coverage_functions.append({"name": func_name, "coverage": func_coverage})

            if "classes" in file_data:
                for class_name, class_data in file_data["classes"].items():
                    if class_name:
                        class_summary = class_data.get("summary", {})
                        class_coverage = class_summary.get("percent_covered", 0.0)
                        if class_coverage < 50:
                            low_coverage_classes.append({"name": class_name, "coverage": class_coverage})

            file_analysis[file_path] = {
                "coverage": file_coverage,
                "branch_coverage": branch_coverage,
                "test_type_coverage": test_type_coverage,
                "failed_tests": failed_tests.get(file_path, []),
                "low_coverage_functions": low_coverage_functions,
                "low_coverage_classes": low_coverage_classes,
                "statements": statements,
                "missing": missing,
                "branches": branches,
                "partial_branches": partial_branches,
            }

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Test Gap Analysis</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .file-section {{
            background: white;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .file-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .file-path {{
            font-family: 'SFMono-Regular', Consolas, monospace;
            font-weight: bold;
            color: #495057;
        }}
        .coverage-badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .coverage-high {{ background: #d4edda; color: #155724; }}
        .coverage-medium {{ background: #fff3cd; color: #856404; }}
        .coverage-low {{ background: #f8d7da; color: #721c24; }}
        .file-content {{
            padding: 20px;
        }}
        .subsection {{
            margin-bottom: 20px;
        }}
        .subsection h4 {{
            margin: 0 0 10px 0;
            color: #495057;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 5px;
        }}
        .no-issues {{
            color: #28a745;
            font-style: italic;
        }}
        .test-failure {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .coverage-item {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-family: 'SFMono-Regular', Consolas, monospace;
            font-size: 0.9em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .stat-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
        }}
        .stat-label {{
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 5px;
        }}
        .navigation {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .nav-link {{
            display: block;
            color: #007bff;
            text-decoration: none;
            padding: 5px 0;
        }}
        .nav-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Comprehensive Test Gap Analysis</h1>
        <p>File-Centric Coverage and Testing Issues Report</p>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="navigation">
        <strong>Quick Navigation:</strong><br>
        <a href="#summary" class="nav-link">Summary</a>
        <a href="../simplified_report.html" class="nav-link">← Main Report</a>
    </div>

    <div id="summary" class="summary">
        <h3>📊 Summary</h3>
        <p>This report provides a comprehensive, file-by-file analysis of testing gaps and coverage issues.
        Each file shows failed tests, coverage statistics by test type, and specific functions/classes/branches under 50% coverage.</p>

        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{len([f for f, data in file_analysis.items() if data['coverage'] < 50])}</div>
                <div class="stat-label">Files < 50% Coverage</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(len(data['failed_tests']) for data in file_analysis.values())}</div>
                <div class="stat-label">Total Failed Tests</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(len(data['low_coverage_functions']) for data in file_analysis.values())}</div>
                <div class="stat-label">Functions < 50%</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(len(data['low_coverage_classes']) for data in file_analysis.values())}</div>
                <div class="stat-label">Classes < 50%</div>
            </div>
        </div>
    </div>
"""

        # Generate file sections - only show files with issues or low coverage
        files_with_issues = []
        for file_path, data in sorted(file_analysis.items()):
            has_issues = (
                data["coverage"] < 50
                or data["failed_tests"]
                or data["low_coverage_functions"]
                or data["low_coverage_classes"]
                or data["branch_coverage"] < 50
            )

            if has_issues:
                files_with_issues.append((file_path, data))

        for file_path, data in files_with_issues:
            # Determine coverage badge
            coverage = data["coverage"]
            if coverage >= 80:
                badge_class = "coverage-high"
            elif coverage >= 50:
                badge_class = "coverage-medium"
            else:
                badge_class = "coverage-low"

            html_content += f"""
    <div class="file-section">
        <div class="file-header">
            <div class="file-path">{file_path}</div>
            <div class="coverage-badge {badge_class}">{coverage:.1f}%</div>
        </div>
        <div class="file-content">
            <div class="subsection">
                <h4>🧪 Test Failures</h4>
"""

            if data["failed_tests"]:
                for test in data["failed_tests"]:
                    html_content += f'                <div class="test-failure">❌ {test}</div>\n'
            else:
                html_content += '                <div class="no-issues">✅ No test failures detected</div>\n'

            html_content += f"""            </div>

            <div class="subsection">
                <h4>📊 Coverage Statistics</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{data['coverage']:.1f}%</div>
                        <div class="stat-label">Total Coverage</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data['branch_coverage']:.1f}%</div>
                        <div class="stat-label">Branch Coverage</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data['statements'] - data['missing']}/{data['statements']}</div>
                        <div class="stat-label">Statements Covered</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data['branches'] - data['partial_branches']}/{data['branches']}</div>
                        <div class="stat-label">Branches Covered</div>
                    </div>
                </div>
"""

            # Test type coverage
            if data["test_type_coverage"]:
                html_content += "                <p><strong>Coverage by Test Type:</strong></p>\n"
                for test_type, type_coverage in data["test_type_coverage"].items():
                    html_content += f'                <span style="margin-right: 15px;">{test_type.title()}: {type_coverage:.1f}%</span>\n'

            html_content += "            </div>\n"

            # Functions under 50% coverage
            html_content += """            <div class="subsection">
                <h4>🔧 Functions < 50% Coverage</h4>
"""

            if data["low_coverage_functions"]:
                for func in data["low_coverage_functions"]:
                    html_content += (
                        f'                <div class="coverage-item">⚠️ {func["name"]} ({func["coverage"]:.1f}%)</div>\n'
                    )
            else:
                html_content += '                <div class="no-issues">✅ All functions have adequate coverage</div>\n'

            # Classes under 50% coverage
            html_content += """            </div>

            <div class="subsection">
                <h4>🏗️ Classes < 50% Coverage</h4>
"""

            if data["low_coverage_classes"]:
                for cls in data["low_coverage_classes"]:
                    html_content += (
                        f'                <div class="coverage-item">⚠️ {cls["name"]} ({cls["coverage"]:.1f}%)</div>\n'
                    )
            else:
                html_content += '                <div class="no-issues">✅ All classes have adequate coverage</div>\n'

            html_content += """            </div>
        </div>
    </div>
"""

        html_content += """
    <div class="summary">
        <h3>📝 Notes</h3>
        <ul>
            <li><strong>File-Centric View:</strong> Each file shows its complete testing picture in one place</li>
            <li><strong>Coverage Threshold:</strong> Items below 50% coverage are highlighted for attention</li>
            <li><strong>Test Types:</strong> Coverage is analyzed across different test categories (unit, integration, auth, etc.)</li>
            <li><strong>Actionable:</strong> Focus on files with test failures first, then address low coverage items</li>
        </ul>
        <p style="margin-top: 20px;">
            <a href="../simplified_report.html" style="color: #007bff;">← Return to Main Coverage Report</a>
        </p>
    </div>
</body>
</html>
"""

        return html_content


def main():
    """Main entry point."""
    import sys

    automation = SimplifiedCoverageAutomation()

    # Allow forcing regeneration
    if "--force" in sys.argv:
        automation.force_run = True

    automation.run_automation()


if __name__ == "__main__":
    main()
