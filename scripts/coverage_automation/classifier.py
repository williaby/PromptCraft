"""
Test type classification and target mapping.
Analyzes test files to determine their target source files and test types.
"""

import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import TestPatternConfig
from .logging_utils import get_logger, get_performance_logger, get_security_logger
from .security import SecurityValidator


class TestTypeClassifier:
    """Classifies test files and maps them to their target source files."""

    def __init__(self, project_root: Path, config: TestPatternConfig):
        """Initialize the test type classifier."""
        self.project_root = project_root
        self.config = config
        self.logger = get_logger("classifier")
        self.security_logger = get_security_logger()
        self.perf_logger = get_performance_logger()

        # Initialize security validator
        self.security = SecurityValidator(project_root)

        # Compiled regex patterns for security and performance
        self.compiled_patterns = {
            # Hardened patterns with negative lookbehind to prevent conflicts
            "src_from_import": re.compile(r"from\s+src\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+"),
            "src_direct_import": re.compile(r"import\s+src\.([a-zA-Z_][a-zA-Z0-9_.]*?)(?:\s|$|,)"),
            # Test file patterns with specificity ordering
            "unit_test": re.compile(r"(?<!integration)(?<!auth)(?<!security)test\.py$", re.IGNORECASE),
            "integration_test": re.compile(r"integration.*test\.py$", re.IGNORECASE),
            "auth_test": re.compile(r"auth.*test\.py$", re.IGNORECASE),
            "security_test": re.compile(r"security.*test\.py$", re.IGNORECASE),
        }

        self.logger.info(
            "Test type classifier initialized",
            project_root=str(project_root),
            pattern_count=len(self.compiled_patterns),
        )

    def estimate_test_type_coverage(
        self, coverage_data: dict[str, Any], contexts: set[str],
    ) -> dict[str, dict[str, float]]:
        """
        Estimate coverage and branch coverage by test type based on file patterns.

        Args:
            coverage_data: Coverage data from coverage.py
            contexts: Set of test contexts that were executed

        Returns:
            Dictionary mapping test types to their coverage metrics
        """
        start_time = time.time()

        try:
            # Type validation for critical inputs
            if not isinstance(coverage_data, dict):
                raise TypeError(f"coverage_data must be dict, got {type(coverage_data).__name__}")
            if not isinstance(contexts, (set, frozenset)):
                raise TypeError(f"contexts must be set or frozenset, got {type(contexts).__name__}")

            coverage_by_type = {}
            files = coverage_data.get("files", {})

            # Get Codecov-aligned file patterns
            file_patterns = self._get_codecov_aligned_patterns()

            for test_type in contexts:
                if test_type not in file_patterns:
                    self.logger.warning("Test type not found in patterns", test_type=test_type)
                    continue

                patterns = file_patterns[test_type]
                matching_files = self._find_matching_files(files, patterns)

                if matching_files:
                    metrics = self._calculate_coverage_metrics(matching_files)
                    coverage_by_type[test_type] = metrics

                    self.logger.debug(
                        "Coverage calculated for test type",
                        test_type=test_type,
                        file_count=len(matching_files),
                        statement_coverage=round(metrics["statement"], 2),
                    )
                else:
                    coverage_by_type[test_type] = {"statement": 0.0, "branch": 0.0, "total_branches": 0}

                    self.logger.debug("No matching files found for test type", test_type=test_type)

            return coverage_by_type

        except (TypeError, ValueError):
            # Re-raise validation errors - these should propagate
            raise
        except Exception as e:
            self.logger.error("Error estimating test type coverage", error=str(e), contexts=list(contexts))
            # Return empty coverage for all contexts to avoid breaking the system
            return {test_type: {"statement": 0.0, "branch": 0.0, "total_branches": 0} for test_type in contexts}

        finally:
            self.perf_logger.log_operation_timing(
                "estimate_test_type_coverage", time.time() - start_time, context_count=len(contexts),
            )

    def _get_codecov_aligned_patterns(self) -> dict[str, list[str]]:
        """Get file patterns aligned with Codecov flags."""
        # Get patterns from Codecov configuration
        codecov_mapping = self.config.get_codecov_flag_mapping()

        # If we have Codecov patterns, use them; otherwise fall back to defaults
        if codecov_mapping:
            self.logger.debug("Using Codecov-aligned patterns")
            return codecov_mapping

        # Default patterns if no Codecov alignment
        return {
            "auth": ["auth/"],
            "unit": ["agents/", "core/", "utils/", "api/", "config/"],
            "integration": ["ui/", "mcp_integration/"],
            "security": ["security/"],
            "performance": ["performance/", "core/"],
            "examples": ["examples/"],
            "contract": ["contract/", "mcp_integration/"],
            "stress": ["performance/", "stress/", "core/"],
        }

    def _find_matching_files(self, files: dict, patterns: list[str]) -> list[dict]:
        """Find files matching the given patterns."""
        matching_files = []

        for file_path, file_data in files.items():
            if any(pattern in file_path for pattern in patterns):
                matching_files.append(file_data)

        return matching_files

    def _calculate_coverage_metrics(self, matching_files: list[dict]) -> dict[str, float]:
        """Calculate coverage metrics for a list of files."""
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

        return {"statement": statement_coverage, "branch": branch_coverage, "total_branches": total_branches}

    @lru_cache(maxsize=32)
    def get_test_target_mapping(self, test_type: str) -> frozenset[str]:
        """
        Get the set of source files that are actually tested by the given test type.
        This analyzes test files to determine which source files they target.

        Args:
            test_type: The test type to analyze

        Returns:
            Frozen set of source file paths that are targeted by this test type
        """
        start_time = time.time()

        try:
            # Type validation
            if not isinstance(test_type, str):
                raise TypeError(f"test_type must be str, got {type(test_type).__name__}: {test_type}")

            # Get test configuration from external YAML config
            test_config = self.config.get_test_type_config(test_type)
            patterns = test_config.get("patterns", [])
            test_targets = set()

            # Analyze test files to find their targets
            tests_dir = self.project_root / "tests"
            if tests_dir.exists():
                for pattern in patterns:
                    targets = self._analyze_pattern_targets(pattern, tests_dir)
                    test_targets.update(targets)

            result = frozenset(test_targets)

            self.logger.debug("Test target mapping completed", test_type=test_type, target_count=len(result))

            return result

        except Exception as e:
            self.logger.error("Error getting test target mapping", test_type=test_type, error=str(e))
            return frozenset()

        finally:
            self.perf_logger.log_operation_timing(
                "get_test_target_mapping", time.time() - start_time, test_type=test_type,
            )

    def _analyze_pattern_targets(self, pattern: str, tests_dir: Path) -> set[str]:
        """Analyze targets for a specific pattern."""
        targets = set()

        if pattern.endswith("/"):
            # Directory pattern - find all test files in this directory
            test_path = self.project_root / pattern.rstrip("/")
            if test_path.exists():
                for test_file in test_path.rglob("test_*.py"):
                    file_targets = self.analyze_test_file_targets(str(test_file))
                    targets.update(file_targets)
        else:
            # File pattern - use glob to find matching files
            for test_file in tests_dir.rglob(pattern.split("/")[-1]):
                if len(pattern.split("/")) > 1 and pattern.split("/")[-2] in str(test_file.parent):
                    file_targets = self.analyze_test_file_targets(str(test_file))
                    targets.update(file_targets)

        return targets

    @lru_cache(maxsize=256)
    def analyze_test_file_targets(self, test_file_path_str: str) -> frozenset[str]:
        """
        Analyze a test file to determine which source files it targets.
        This looks at import statements and test structure to infer targets.

        Args:
            test_file_path_str: String path to the test file

        Returns:
            Frozen set of target source file paths
        """
        test_file_path = Path(test_file_path_str)
        targets = set()

        try:
            # Security validations
            if not self.security.validate_path(test_file_path):
                return frozenset()

            if not self.security.validate_file_size(test_file_path):
                return frozenset()

            # Read and analyze file content
            with open(test_file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Security: Sanitize content before regex processing
            content = self.security.sanitize_content(content)

            # Extract import statements using compiled, hardened regex patterns
            targets.update(self._extract_src_imports(content))

            # Infer targets based on test file name and location
            targets.update(self._infer_targets_from_location(test_file_path))

        except Exception as e:
            self.logger.warning("Could not analyze test file", test_file=str(test_file_path), error=str(e))

        return frozenset(targets)

    def _extract_src_imports(self, content: str) -> set[str]:
        """Extract source file targets from import statements."""
        targets = set()

        # Look for imports from src/ with security validation
        src_imports = self.compiled_patterns["src_from_import"].findall(content)
        for imp in src_imports:
            if self.security.validate_import_path(imp):
                # Convert module path to file path
                module_path = imp.replace(".", "/") + ".py"
                source_path = f"src/{module_path}"
                targets.add(source_path)

        # Look for direct imports of src modules
        direct_imports = self.compiled_patterns["src_direct_import"].findall(content)
        for imp in direct_imports:
            if self.security.validate_import_path(imp):
                module_path = imp.replace(".", "/") + ".py"
                source_path = f"src/{module_path}"
                targets.add(source_path)

        return targets

    def _infer_targets_from_location(self, test_file_path: Path) -> set[str]:
        """Infer target files based on test file name and location."""
        targets = set()

        test_name = test_file_path.stem
        if not test_name.startswith("test_"):
            return targets

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
            potential_targets = self._infer_unit_test_targets(test_relative, module_name)
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

        return targets

    def _infer_unit_test_targets(self, test_relative: Path, module_name: str) -> list[str]:
        """Infer unit test targets from directory structure."""
        parts = test_relative.parts

        if len(parts) >= 3 and parts[1] == "unit":
            # Get the directory under unit/
            subdir = parts[2] if len(parts) > 3 else ""
            if subdir and subdir != test_relative.stem:
                return [f"src/{subdir}/{module_name}.py"]
            # Try common directories
            return [
                f"src/core/{module_name}.py",
                f"src/agents/{module_name}.py",
                f"src/utils/{module_name}.py",
                f"src/api/{module_name}.py",
                f"src/{module_name}.py",
            ]
        return [f"src/{module_name}.py"]
