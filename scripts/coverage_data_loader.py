#!/usr/bin/env python3
"""
Coverage Data Loader Module

Part of the modular coverage reporting system. Handles parsing of VS Code generated
coverage.xml and junit.xml files into structured data for report generation.

This module implements the consensus plan from Zen Consensus analysis to restore
sophisticated coverage reporting functionality while eliminating the 5x test
execution inefficiency.
"""

from pathlib import Path
import time
from typing import Any

from defusedxml import ElementTree as ET  # noqa: N817


class CoverageDataLoader:
    """Loads and parses coverage data from VS Code test runs."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage"

        # Single canonical locations for test result files
        self.canonical_coverage_xml = self.project_root / "coverage.xml"
        self.canonical_junit_xml = self.project_root / "reports" / "junit.xml"

    def find_coverage_files(self) -> dict[str, Path | None]:
        """Find the canonical coverage files."""
        files = {"coverage_xml": None, "junit_xml": None}

        # Use canonical locations only
        if self.canonical_coverage_xml.exists():
            files["coverage_xml"] = self.canonical_coverage_xml
        if self.canonical_junit_xml.exists():
            files["junit_xml"] = self.canonical_junit_xml

        return files

    def load_coverage_data(self) -> dict[str, Any] | None:
        """Load coverage data from coverage.xml file."""
        files = self.find_coverage_files()
        coverage_xml = files["coverage_xml"]

        if not coverage_xml or not coverage_xml.exists():
            # Check if we have .coverage binary file but no XML - VS Code integration issue
            if (self.project_root / ".coverage").exists():
                print("📊 VS Code generated .coverage but no XML - generating XML automatically...")
                try:
                    # Security: subprocess used for controlled coverage commands - no user input processed
                    import subprocess

                    # Security: Using hardcoded command with controlled arguments
                    # No user input in command args, cwd restricted to project_root
                    subprocess.run(  # noqa: S603
                        ["poetry", "run", "coverage", "xml"],
                        cwd=self.project_root,
                        check=True,
                        capture_output=True,
                        timeout=30,
                    )
                    if self.canonical_coverage_xml.exists():
                        print("✅ Generated coverage.xml from VS Code .coverage data")
                        # Recursive call now that XML exists
                        return self.load_coverage_data()
                    print("⚠️  coverage xml command succeeded but no XML file found")
                except Exception as e:
                    print(f"⚠️  Could not generate coverage.xml: {e}")
            return None

        try:
            tree = ET.parse(coverage_xml)
            root = tree.getroot()

            # Extract overall coverage that matches VS Code display
            overall = {
                "line_rate": float(root.attrib["line-rate"]),
                "lines_covered": int(root.attrib["lines-covered"]),
                "lines_valid": int(root.attrib["lines-valid"]),
                "branch_rate": float(root.attrib.get("branch-rate", 0)),
                "percentage": float(root.attrib["line-rate"]) * 100,
            }

            # Extract file-level coverage that matches VS Code
            files_coverage = {}
            for package in root.findall(".//package"):
                for cls in package.findall(".//class"):
                    filename = cls.get("filename", "unknown")
                    file_coverage = {
                        "line_rate": float(cls.attrib["line-rate"]),
                        "lines_covered": 0,
                        "lines_valid": 0,
                        "percentage": float(cls.attrib["line-rate"]) * 100,
                        "lines": {},  # Store line-by-line coverage
                    }

                    # Count actual lines and store line coverage
                    for line in cls.findall(".//line"):
                        line_number = int(line.get("number", 0))
                        hits = int(line.get("hits", 0))
                        file_coverage["lines_valid"] += 1
                        file_coverage["lines"][line_number] = hits
                        if hits > 0:
                            file_coverage["lines_covered"] += 1

                    files_coverage[filename] = file_coverage

            return {"overall": overall, "files": files_coverage, "timestamp": coverage_xml.stat().st_mtime}

        except Exception as e:
            print(f"⚠️  Error parsing coverage data: {e}")
            return None

    def load_test_execution_data(self) -> dict[str, list[dict[str, Any]]]:
        """Load test execution data from junit.xml file."""
        files = self.find_coverage_files()
        junit_xml = files["junit_xml"]

        if not junit_xml or not junit_xml.exists():
            return {}

        try:
            tree = ET.parse(junit_xml)
            root = tree.getroot()

            test_executions = []

            for testcase in root.findall(".//testcase"):
                test_info = {
                    "classname": testcase.get("classname", ""),
                    "name": testcase.get("name", ""),
                    "time": float(testcase.get("time", 0)),
                    "file": testcase.get("file", ""),
                    "line": testcase.get("line", ""),
                    "status": "passed",  # Default status
                }

                # Check for failures or errors
                if testcase.find("failure") is not None:
                    test_info["status"] = "failed"
                elif testcase.find("error") is not None:
                    test_info["status"] = "error"
                elif testcase.find("skipped") is not None:
                    test_info["status"] = "skipped"

                test_executions.append(test_info)

            return {
                "test_executions": test_executions,
                "total_tests": len(test_executions),
                "timestamp": junit_xml.stat().st_mtime,
            }

        except Exception as e:
            print(f"⚠️  Error parsing test execution data: {e}")
            return {}

    def get_combined_data(self) -> dict[str, Any] | None:
        """Load and combine both coverage and test execution data."""
        coverage_data = self.load_coverage_data()
        test_data = self.load_test_execution_data()

        if not coverage_data:
            return None

        return {"coverage": coverage_data, "tests": test_data, "loaded_at": time.time()}


if __name__ == "__main__":
    # Test the loader
    loader = CoverageDataLoader()
    data = loader.get_combined_data()

    if data:
        coverage = data["coverage"]
        tests = data["tests"]
        print(f"✅ Loaded coverage data: {coverage['overall']['percentage']:.1f}% overall")
        if tests:
            print(f"🧪 Found {tests['total_tests']} test executions")
    else:
        print("❌ No coverage data found")
