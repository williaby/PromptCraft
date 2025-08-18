"""
Test type classification and coverage analysis.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar

from .config import TestPatternConfig
from .security import SecurityValidator


class TestTypeClassifier:
    """Classifies tests by type and estimates coverage."""

    # Compiled regex patterns for security and performance
    COMPILED_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "src_from_import": re.compile(r"from\s+src\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+"),
        "src_direct_import": re.compile(r"import\s+src\.([a-zA-Z_][a-zA-Z0-9_.]*?)(?:\s|$|,)"),
        "valid_module": re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$"),
    }

    def __init__(self, project_root: Path, config: TestPatternConfig):
        self.project_root = project_root
        self.config = config
        self.security = SecurityValidator(project_root)

    def estimate_test_type_coverage(
        self,
        coverage_data: dict[str, Any],
        contexts: set[str],
    ) -> dict[str, dict[str, float]]:
        """Estimate coverage and branch coverage by test type based on file patterns."""
        # Type validation for critical inputs
        if not isinstance(coverage_data, dict):
            raise TypeError(f"coverage_data must be dict, got {type(coverage_data).__name__}")
        if not isinstance(contexts, (set, frozenset)):
            raise TypeError(f"contexts must be set or frozenset, got {type(contexts).__name__}")

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

    @lru_cache(maxsize=32)
    def get_test_target_mapping(self, test_type: str) -> frozenset[str]:
        """
        Get the set of source files that are actually tested by the given test type.
        This analyzes test files to determine which source files they target.
        """
        # Type validation for critical inputs
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

    @lru_cache(maxsize=256)
    def _analyze_test_file_targets(self, test_file_path_str: str) -> frozenset[str]:
        """
        Analyze a test file to determine which source files it targets.
        This looks at import statements and test structure to infer targets.
        """
        test_file_path = Path(test_file_path_str)
        targets = set()

        # Security: Validate file path is within project bounds
        if not self.security.validate_path(test_file_path):
            print(f"  🚨 Security: Test file outside project bounds: {test_file_path}")
            return frozenset()

        # Security: Check file size to prevent memory exhaustion
        if not self.security.validate_file_size(test_file_path):
            print(f"  ⚠️  Security: Test file too large: {test_file_path}")
            return frozenset()

        try:
            with open(test_file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Security: Sanitize content before regex processing
            content = self._sanitize_file_content(content)

            # Extract import statements using compiled patterns
            src_imports = self.COMPILED_PATTERNS["src_from_import"].findall(content)
            for imp in src_imports:
                if self.security.validate_import_path(imp):
                    # Convert module path to file path
                    module_path = imp.replace(".", "/") + ".py"
                    source_path = f"src/{module_path}"
                    targets.add(source_path)

            # Look for direct imports of src modules
            direct_imports = self.COMPILED_PATTERNS["src_direct_import"].findall(content)
            for imp in direct_imports:
                if self.security.validate_import_path(imp):
                    module_path = imp.replace(".", "/") + ".py"
                    source_path = f"src/{module_path}"
                    targets.add(source_path)

            # Infer targets based on test file name and location
            test_name = test_file_path.stem
            if test_name.startswith("test_"):
                module_name = test_name[5:]
                test_relative = test_file_path.relative_to(self.project_root)

                # Try different source locations based on test file location
                potential_targets = self._get_potential_targets(test_relative, module_name)

                # Check which targets actually exist
                for target in potential_targets:
                    target_path = self.project_root / target
                    if target_path.exists():
                        targets.add(target)

        except Exception as e:
            print(f"  ⚠️  Could not analyze test file {test_file_path}: {e}")

        return frozenset(targets)

    def _get_potential_targets(self, test_relative: Path, module_name: str) -> list[str]:
        """Get potential target files based on test location."""
        if "auth" in str(test_relative):
            return [
                f"src/auth/{module_name}.py",
                f"src/auth/{module_name}_validator.py",
                f"src/auth/{module_name}_client.py",
            ]
        if "unit" in str(test_relative):
            # Unit tests - infer from directory structure
            parts = test_relative.parts
            if len(parts) >= 3 and parts[1] == "unit":
                subdir = parts[2] if len(parts) > 3 else ""
                if subdir and subdir != test_relative.stem:
                    return [f"src/{subdir}/{module_name}.py"]
                return [
                    f"src/core/{module_name}.py",
                    f"src/agents/{module_name}.py",
                    f"src/utils/{module_name}.py",
                    f"src/api/{module_name}.py",
                    f"src/{module_name}.py",
                ]
            return [f"src/{module_name}.py"]
        if "integration" in str(test_relative):
            return [
                f"src/ui/{module_name}.py",
                f"src/mcp_integration/{module_name}.py",
                f"src/core/{module_name}.py",
            ]
        return [f"src/{module_name}.py"]

    def _sanitize_file_content(self, content: str) -> str:
        """Sanitize test file content before regex processing."""
        return self.security.sanitize_content(content)
