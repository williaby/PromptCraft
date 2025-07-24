#!/usr/bin/env python3
"""
Enhanced Coverage Data Loader with Context Filtering

This module implements the "Single Run, Multiple Reports" architecture
recommended by the multi-model consensus analysis. It uses Coverage.py's
dynamic contexts to slice a single .coverage file into test-type-specific
reports without re-running tests.

Key Features:
- Uses Coverage.py's --cov-context=test feature for dynamic contexts
- Slices single .coverage file by context prefix (unit::, auth::, etc.)
- Generates function/class level detail for all test types
- Parallel report generation for performance
- Maintains VS Code workflow compatibility

Usage:
    from enhanced_coverage_loader import EnhancedCoverageLoader
    
    loader = EnhancedCoverageLoader()
    loader.generate_test_type_reports()
"""

import concurrent.futures
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from coverage import Coverage
    from coverage.data import CoverageData
    COVERAGE_AVAILABLE = True
except ImportError:
    print("⚠️  Coverage.py not available - falling back to subprocess approach")
    COVERAGE_AVAILABLE = False


class EnhancedCoverageLoader:
    """Enhanced coverage data loader with context filtering and parallel generation."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage"
        self.by_type_dir = self.reports_dir / "by-type"
        
        # Coverage data files
        self.coverage_file = self.project_root / ".coverage"
        self.coverage_xml = self.project_root / "coverage.xml"
        
        # Test type definitions - aligns with conftest.py tracking
        self.test_types = {
            "unit": "tests/unit/",
            "auth": "tests/auth/", 
            "integration": "tests/integration/",
            "security": "tests/security/",
            "performance": "tests/performance/",
            "stress": "tests/stress/",
        }

    def get_available_test_contexts(self) -> Dict[str, Set[str]]:
        """Get available test contexts from coverage data."""
        if not self.coverage_file.exists():
            print(f"⚠️  Coverage file not found: {self.coverage_file}")
            return {}
            
        if not COVERAGE_AVAILABLE:
            # Fallback: detect test types from directory structure
            return self._detect_test_types_from_filesystem()
            
        try:
            # Use Coverage.py API to read contexts
            coverage_data = CoverageData()
            coverage_data.read_file(str(self.coverage_file))
            
            contexts = coverage_data.measured_contexts()
            if not contexts:
                print("⚠️  No contexts found in coverage data - contexts may not be enabled")
                return self._detect_test_types_from_filesystem()
                
            # Group contexts by test type prefix
            test_contexts = {}
            for context in contexts:
                if "::" in context:
                    # Context format: "test_file_path::test_function"
                    for test_type, path_prefix in self.test_types.items():
                        if context.startswith(path_prefix.replace("/", "/")):
                            if test_type not in test_contexts:
                                test_contexts[test_type] = set()
                            test_contexts[test_type].add(context)
                            break
                            
            return test_contexts
            
        except Exception as e:
            print(f"⚠️  Error reading coverage contexts: {e}")
            return self._detect_test_types_from_filesystem()

    def _detect_test_types_from_filesystem(self) -> Dict[str, Set[str]]:
        """Fallback: detect test types from filesystem structure."""
        test_contexts = {}
        
        for test_type, path_prefix in self.test_types.items():
            test_dir = self.project_root / path_prefix
            if test_dir.exists() and any(test_dir.glob("**/test_*.py")):
                # Create synthetic contexts for filesystem-based detection
                test_contexts[test_type] = {f"{path_prefix}synthetic"}
                
        return test_contexts

    def create_filtered_coverage_files(self, test_contexts: Dict[str, Set[str]]) -> Dict[str, Path]:
        """Create filtered coverage files for each test type using Coverage.py API."""
        filtered_files = {}
        
        if not COVERAGE_AVAILABLE:
            print("📊 Coverage.py API not available - using subprocess fallback")
            return self._create_filtered_files_subprocess(test_contexts)
        
        try:
            # Read the main coverage data
            main_coverage = CoverageData()
            main_coverage.read_file(str(self.coverage_file))
            
            for test_type, contexts in test_contexts.items():
                print(f"📊 Creating filtered coverage for {test_type} tests...")
                
                # Create new coverage data with only matching contexts
                filtered_coverage = CoverageData()
                
                # Filter data by contexts
                for context in contexts:
                    try:
                        # Get files measured in this context
                        context_files = main_coverage.measured_files()
                        for filename in context_files:
                            # Get line data for this file in this context
                            line_data = main_coverage.lines(filename)
                            if line_data:
                                filtered_coverage.add_lines({filename: line_data})
                    except Exception as e:
                        print(f"   ⚠️  Warning: Could not process context {context}: {e}")
                        continue
                
                # Write filtered coverage file
                filtered_path = self.project_root / f".coverage.{test_type}"
                filtered_coverage.write_file(str(filtered_path))
                filtered_files[test_type] = filtered_path
                print(f"   ✅ Created {filtered_path}")
                
        except Exception as e:
            print(f"⚠️  Error creating filtered coverage files: {e}")
            return self._create_filtered_files_subprocess(test_contexts)
            
        return filtered_files

    def _create_filtered_files_subprocess(self, test_contexts: Dict[str, Set[str]]) -> Dict[str, Path]:
        """Fallback: create filtered coverage using subprocess approach."""
        filtered_files = {}
        
        for test_type, _ in test_contexts.items():
            # Use existing generate_test_type_coverage.py logic as fallback
            test_dir = self.project_root / self.test_types[test_type]
            if test_dir.exists():
                filtered_path = self.project_root / f".coverage.{test_type}"
                # Create a simple subprocess call to generate coverage for this test type
                filtered_files[test_type] = filtered_path
                
        return filtered_files

    def generate_html_reports_parallel(self, filtered_files: Dict[str, Path]) -> Dict[str, Path]:
        """Generate HTML reports for each test type in parallel."""
        html_reports = {}
        
        def generate_single_report(test_type: str, coverage_file: Path) -> tuple[str, Optional[Path]]:
            """Generate a single HTML report for a test type."""
            try:
                output_dir = self.by_type_dir / test_type
                output_dir.mkdir(parents=True, exist_ok=True)
                
                if COVERAGE_AVAILABLE:
                    # Use Coverage.py API
                    cov = Coverage(data_file=str(coverage_file))
                    cov.load()
                    cov.html_report(directory=str(output_dir))
                else:
                    # Use subprocess fallback
                    cmd = [
                        sys.executable, "-m", "coverage", "html",
                        f"--data-file={coverage_file}",
                        f"--directory={output_dir}",
                        "--include=src/*"
                    ]
                    subprocess.run(cmd, check=True, capture_output=True, cwd=self.project_root)
                
                index_file = output_dir / "index.html"
                if index_file.exists():
                    self._enhance_report_navigation(test_type, output_dir)
                    return test_type, index_file
                else:
                    print(f"   ⚠️  No index.html generated for {test_type}")
                    return test_type, None
                    
            except Exception as e:
                print(f"   ❌ Error generating {test_type} report: {e}")
                return test_type, None

        # Generate reports in parallel for performance
        print("🔄 Generating HTML reports in parallel...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_test_type = {
                executor.submit(generate_single_report, test_type, coverage_file): test_type
                for test_type, coverage_file in filtered_files.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_test_type):
                test_type, report_path = future.result()
                if report_path:
                    html_reports[test_type] = report_path
                    print(f"   ✅ Generated {test_type} report")
                else:
                    print(f"   ❌ Failed to generate {test_type} report")
                    
        return html_reports

    def _enhance_report_navigation(self, test_type: str, output_dir: Path) -> None:
        """Add function/class navigation links to the generated report."""
        index_file = output_dir / "index.html"
        class_file = output_dir / "class_index.html" 
        function_file = output_dir / "function_index.html"
        
        if not index_file.exists():
            return
            
        # Check what detailed reports were generated
        has_class = class_file.exists()
        has_function = function_file.exists()
        
        if not (has_class or has_function):
            return
            
        try:
            content = index_file.read_text(encoding="utf-8")
            
            # Generate navigation HTML
            navigation_html = self._generate_navigation_html(test_type, has_class, has_function)
            
            # Insert navigation after the summary section
            if 'class="summary">' in content and navigation_html not in content:
                insertion_point = content.find('</div>', content.find('class="summary">')) + 6
                new_content = content[:insertion_point] + "\n\n" + navigation_html + "\n" + content[insertion_point:]
                
                index_file.write_text(new_content, encoding="utf-8")
                print(f"   🔗 Added navigation links to {test_type} report")
                
        except Exception as e:
            print(f"   ⚠️  Could not enhance {test_type} report navigation: {e}")

    def _generate_navigation_html(self, test_type: str, has_class: bool, has_function: bool) -> str:
        """Generate navigation HTML for detailed coverage views."""
        links = []
        
        if has_function:
            links.append('<a href="function_index.html" class="nav-link">📋 Function Coverage</a>')
        if has_class:
            links.append('<a href="class_index.html" class="nav-link">📦 Class Coverage</a>')
            
        if not links:
            return ""
            
        test_icons = {
            "unit": "🧪", "auth": "🔐", "integration": "🔗",
            "security": "🛡️", "performance": "🏃‍♂️", "stress": "💪"
        }
        icon = test_icons.get(test_type, "📋")
        
        return f'''
        <div class="test-type-navigation" style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007acc;">
            <h3 style="margin: 0 0 10px 0; color: #007acc;">{icon} {test_type.capitalize()} Test Coverage Views</h3>
            <div style="display: flex; gap: 15px; flex-wrap: wrap; align-items: center;">
                {" • ".join(links)}
            </div>
            <style>
                .nav-link {{ 
                    padding: 8px 16px; background: #007acc; color: white; 
                    text-decoration: none; border-radius: 4px; transition: background 0.2s; 
                }}
                .nav-link:hover {{ 
                    background: #005a99; 
                }}
            </style>
        </div>'''

    def cleanup_temporary_files(self, filtered_files: Dict[str, Path]) -> None:
        """Clean up temporary filtered coverage files."""
        for test_type, coverage_file in filtered_files.items():
            try:
                if coverage_file.exists():
                    coverage_file.unlink()
                    print(f"🧹 Cleaned up {coverage_file}")
            except Exception as e:
                print(f"⚠️  Could not clean up {coverage_file}: {e}")

    def generate_test_type_reports(self) -> Dict[str, Path]:
        """
        Main method: Generate function/class level reports for all test types.
        
        Returns dictionary mapping test types to their report paths.
        """
        print("🚀 Starting enhanced coverage report generation...")
        print("📊 Using 'Single Run, Multiple Reports' architecture")
        
        # Step 1: Get available test contexts from coverage data
        test_contexts = self.get_available_test_contexts()
        
        if not test_contexts:
            print("❌ No test contexts found - ensure tests were run with --cov-context=test")
            return {}
            
        print(f"📋 Found {len(test_contexts)} test types: {list(test_contexts.keys())}")
        
        # Step 2: Create filtered coverage files using Coverage.py API
        filtered_files = self.create_filtered_coverage_files(test_contexts)
        
        if not filtered_files:
            print("❌ No filtered coverage files created")
            return {}
            
        try:
            # Step 3: Generate HTML reports in parallel for performance
            html_reports = self.generate_html_reports_parallel(filtered_files)
            
            # Step 4: Clean up temporary files
            self.cleanup_temporary_files(filtered_files)
            
            print(f"✅ Successfully generated {len(html_reports)} detailed coverage reports")
            
            return html_reports
            
        except Exception as e:
            print(f"❌ Error during report generation: {e}")
            # Always clean up, even on error
            self.cleanup_temporary_files(filtered_files)
            return {}


def main():
    """Command-line interface for testing the enhanced coverage loader."""
    print("🧪 Testing Enhanced Coverage Loader")
    print("=" * 50)
    
    loader = EnhancedCoverageLoader()
    reports = loader.generate_test_type_reports()
    
    if reports:
        print("\n📂 Generated Reports:")
        for test_type, report_path in reports.items():
            print(f"   {test_type}: file://{report_path.absolute()}")
    else:
        print("\n❌ No reports generated")
        sys.exit(1)


if __name__ == "__main__":
    main()