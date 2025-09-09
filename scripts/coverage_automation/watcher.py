"""
File monitoring and coverage detection for automation.
"""

from pathlib import Path
import time

from .config import TestPatternConfig


class CoverageWatcher:
    """Watches for coverage file changes and detects test runs."""

    def __init__(self, project_root: Path, config: TestPatternConfig):
        self.project_root = project_root
        self.config = config
        self.coverage_file = project_root / ".coverage"

        # Handle coverage files with hostname suffixes
        if not self.coverage_file.exists():
            coverage_files = list(self.project_root.glob(".coverage.*"))
            if coverage_files:
                self.coverage_file = max(coverage_files, key=lambda f: f.stat().st_mtime)

    def detect_vscode_coverage_run(self) -> bool:
        """Detect if VS Code just ran coverage by checking file timestamps."""
        if not self.coverage_file.exists():
            return False

        # Check if coverage file was updated in the last 60 seconds
        file_age = time.time() - self.coverage_file.stat().st_mtime
        return file_age < 60

    def get_coverage_contexts(self) -> set[str]:
        """Detect test types from test output and coverage analysis."""
        try:
            contexts = set()
            current_time = time.time()

            # Get test directories from config
            test_dirs = self._get_test_directories_from_config()

            for test_type, test_dir in test_dirs.items():
                if test_dir.exists():
                    # Check for recent .pyc files in __pycache__ directories
                    pycache_dir = test_dir / "__pycache__"
                    if pycache_dir.exists():
                        for pyc_file in pycache_dir.glob("*.pyc"):
                            file_age = current_time - pyc_file.stat().st_mtime
                            if file_age < 3600:  # 1 hour
                                contexts.add(test_type)
                                break

            # Fallback: if no contexts detected but we have coverage data
            if not contexts and self.coverage_file.exists():
                file_age = current_time - self.coverage_file.stat().st_mtime
                if file_age < 7200:  # 2 hours
                    # Add all test types that have directories
                    for test_type, test_dir in test_dirs.items():
                        if test_dir.exists():
                            contexts.add(test_type)

            return contexts

        except Exception as e:
            print(f"Warning: Could not detect test contexts: {e}")
            return {"unit", "auth", "integration"}  # Safe fallback

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
