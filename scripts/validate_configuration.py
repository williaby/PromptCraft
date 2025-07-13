#!/usr/bin/env python3
"""
Configuration Validation Script

Validates consistency of line length and tool versions across all configuration files
to ensure development environment alignment.

This script addresses Phase 1 Issue 44: Configuration Standardization and Line Length Alignment
"""

import json
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    # For older Python versions, use the toml library
    from typing import Any, BinaryIO, TextIO

    import toml  # type: ignore[import-untyped]

    # Create a compatible interface
    class TomlLibCompat:
        @staticmethod
        def load(f: BinaryIO | TextIO) -> dict[str, Any]:
            if hasattr(f, "mode") and "b" in f.mode:
                content = f.read().decode("utf-8")  # type: ignore[union-attr]
                return toml.loads(content)  # type: ignore[no-any-return]
            return toml.load(f)  # type: ignore[no-any-return]

    tomllib = TomlLibCompat()  # type: ignore[assignment]


import yaml


class ConfigurationValidator:
    """Validates configuration consistency across development tools."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.target_line_length = 120
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Configuration Validation - Phase 1 Issue 44")
        print("=" * 60)

        # Core validation checks
        self.validate_line_length_consistency()
        self.validate_tool_versions()
        self.validate_claude_md_accuracy()
        self.validate_ci_alignment()

        # Report results
        self.print_results()

        return len(self.errors) == 0

    def validate_line_length_consistency(self) -> None:
        """Validate line length is consistent across all config files."""
        print("📏 Validating line length consistency...")

        configs = self._get_line_length_configs()

        for config_name, line_length in configs.items():
            if line_length != self.target_line_length:
                self.errors.append(f"{config_name}: Line length {line_length} != target {self.target_line_length}")
            else:
                self.info.append(f"{config_name}: ✅ Line length {line_length}")

    def validate_tool_versions(self) -> None:
        """Validate tool versions are aligned between pre-commit and pyproject.toml."""
        print("🔧 Validating tool version alignment...")

        pyproject_versions = self._get_pyproject_tool_versions()
        precommit_versions = self._get_precommit_tool_versions()

        for tool in ["black", "ruff", "mypy"]:
            pyproject_version = pyproject_versions.get(tool)
            precommit_version = precommit_versions.get(tool)

            if pyproject_version and precommit_version:
                # Extract version numbers for comparison
                py_ver = self._extract_version_number(pyproject_version)
                pc_ver = self._extract_version_number(precommit_version)

                if py_ver and pc_ver:
                    if self._is_version_compatible(py_ver, pc_ver):
                        self.info.append(f"{tool}: ✅ Versions compatible ({pyproject_version} / {precommit_version})")
                    else:
                        self.warnings.append(
                            f"{tool}: Version mismatch - pyproject.toml: {pyproject_version}, pre-commit: {precommit_version}",
                        )
                else:
                    self.warnings.append(f"{tool}: Could not parse version numbers")
            else:
                self.warnings.append(f"{tool}: Missing version information")

    def validate_claude_md_accuracy(self) -> None:
        """Validate CLAUDE.md reflects actual configuration."""
        print("📝 Validating CLAUDE.md accuracy...")

        claude_md_path = self.project_root / "CLAUDE.md"
        if not claude_md_path.exists():
            self.errors.append("CLAUDE.md not found")
            return

        content = claude_md_path.read_text()

        # Check for incorrect line length references
        if "88" in content and "character" in content:
            # More specific check to avoid false positives
            if re.search(r"88\s+character", content, re.IGNORECASE):
                self.errors.append("CLAUDE.md contains references to 88 character line length")
            else:
                self.info.append("CLAUDE.md: ✅ No incorrect 88 character references found")
        else:
            self.info.append("CLAUDE.md: ✅ No 88 character references found")

        # Check for correct line length references
        if f"{self.target_line_length}" in content:
            self.info.append(f"CLAUDE.md: ✅ Contains {self.target_line_length} character references")
        else:
            self.warnings.append(f"CLAUDE.md: No {self.target_line_length} character references found")

    def validate_ci_alignment(self) -> None:
        """Validate CI workflows use consistent configuration."""
        print("🚀 Validating CI pipeline alignment...")

        ci_path = self.project_root / ".github" / "workflows" / "ci.yml"
        if not ci_path.exists():
            self.warnings.append("CI workflow file not found")
            return

        content = ci_path.read_text()

        # Check if CI uses explicit line length arguments with more specific regex
        import re

        # Look for explicit line-length arguments in tool commands
        line_length_patterns = [
            r"--line-length[=\s]+\d+",  # black --line-length=120
            r"--line-length[=\s]+\d+",  # ruff --line-length 120
            r"args:\s*\[.*--line-length[=\s]+\d+.*\]",  # pre-commit args
        ]

        has_explicit_config = any(re.search(pattern, content) for pattern in line_length_patterns)

        if has_explicit_config:
            self.info.append("CI: ✅ Uses explicit line length configuration")
        else:
            self.warnings.append("CI: No explicit line length configuration found in tool commands")

        # Check for Black and Ruff usage
        if "black" in content and "ruff" in content:
            self.info.append("CI: ✅ Uses both Black and Ruff")
        else:
            self.warnings.append("CI: Missing Black or Ruff configuration")

    def _get_line_length_configs(self) -> dict[str, int]:
        """Extract line length from all configuration files."""
        configs = {}

        # pyproject.toml
        try:
            pyproject_path = self.project_root / "pyproject.toml"
            with pyproject_path.open("rb") as f:
                pyproject_data = tomllib.load(f)

            if "tool" in pyproject_data:
                if "black" in pyproject_data["tool"]:
                    black_config = pyproject_data["tool"]["black"]
                    if "line-length" not in black_config:
                        self.warnings.append(
                            "pyproject.toml (Black): Using default line-length (88), explicit configuration recommended",
                        )
                    configs["pyproject.toml (Black)"] = black_config.get("line-length", 88)

                if "ruff" in pyproject_data["tool"]:
                    ruff_config = pyproject_data["tool"]["ruff"]
                    if "line-length" not in ruff_config:
                        self.warnings.append(
                            "pyproject.toml (Ruff): Using default line-length (88), explicit configuration recommended",
                        )
                    configs["pyproject.toml (Ruff)"] = ruff_config.get("line-length", 88)
        except Exception as e:
            self.warnings.append(f"Could not read pyproject.toml: {e}")

        # .markdownlint.json
        try:
            markdownlint_path = self.project_root / ".markdownlint.json"
            with markdownlint_path.open() as f:
                markdownlint_data = json.load(f)

            if "MD013" in markdownlint_data:
                md013_config = markdownlint_data["MD013"]
                if "line_length" not in md013_config:
                    self.warnings.append(
                        ".markdownlint.json (MD013): Using default line_length (80), explicit configuration recommended",
                    )
                configs[".markdownlint.json"] = md013_config.get("line_length", 80)
        except Exception as e:
            self.warnings.append(f"Could not read .markdownlint.json: {e}")

        # .yamllint.yml
        try:
            yamllint_path = self.project_root / ".yamllint.yml"
            with yamllint_path.open() as f:
                yamllint_data = yaml.safe_load(f)

            if "rules" in yamllint_data and "line-length" in yamllint_data["rules"]:
                line_length_config = yamllint_data["rules"]["line-length"]
                if "max" not in line_length_config:
                    self.warnings.append(
                        ".yamllint.yml (line-length): Using default max (80), explicit configuration recommended",
                    )
                configs[".yamllint.yml"] = line_length_config.get("max", 80)
        except Exception as e:
            self.warnings.append(f"Could not read .yamllint.yml: {e}")

        return configs

    def _get_pyproject_tool_versions(self) -> dict[str, str]:
        """Extract tool versions from pyproject.toml."""
        try:
            pyproject_path = self.project_root / "pyproject.toml"
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)

            dev_deps = data.get("tool", {}).get("poetry", {}).get("group", {}).get("dev", {}).get("dependencies", {})
            return {
                "black": dev_deps.get("black", ""),
                "ruff": dev_deps.get("ruff", ""),
                "mypy": dev_deps.get("mypy", ""),
            }
        except Exception as e:
            self.warnings.append(f"Could not read pyproject.toml tool versions: {e}")
            return {}

    def _get_precommit_tool_versions(self) -> dict[str, str]:
        """Extract tool versions from .pre-commit-config.yaml."""
        try:
            precommit_path = self.project_root / ".pre-commit-config.yaml"
            with precommit_path.open() as f:
                data = yaml.safe_load(f)

            versions = {}
            for repo in data.get("repos", []):
                if "psf/black" in repo.get("repo", ""):
                    versions["black"] = repo.get("rev", "")
                elif "ruff-pre-commit" in repo.get("repo", ""):
                    versions["ruff"] = repo.get("rev", "")
                elif "mirrors-mypy" in repo.get("repo", ""):
                    versions["mypy"] = repo.get("rev", "")

            return versions
        except Exception as e:
            self.warnings.append(f"Could not read .pre-commit-config.yaml: {e}")
            return {}

    def _extract_version_number(self, version_str: str) -> str:
        """Extract version number from version string."""
        # Remove common prefixes and constraints
        version_str = re.sub(r"^[>=<~^]+", "", version_str)
        version_str = version_str.replace("v", "")

        # Extract version pattern (X.Y.Z or X.Y)
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_str)
        return match.group(1) if match else ""

    def _is_version_compatible(self, version1: str, version2: str) -> bool:
        """Check if two versions are compatible (major.minor match)."""
        try:
            v1_parts = version1.split(".")
            v2_parts = version2.split(".")

            # Compare major.minor
            return v1_parts[0] == v2_parts[0] and v1_parts[1] == v2_parts[1]
        except Exception:
            return False

    def print_results(self) -> None:
        """Print validation results."""
        print("\n" + "=" * 60)
        print("📊 Validation Results")
        print("=" * 60)

        if self.info:
            print("\n✅ SUCCESS:")
            for item in self.info:
                print(f"  {item}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for item in self.warnings:
                print(f"  {item}")

        if self.errors:
            print("\n❌ ERRORS:")
            for item in self.errors:
                print(f"  {item}")

        print("\n" + "=" * 60)
        if self.errors:
            print("❌ VALIDATION FAILED - Please fix errors above")
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
        else:
            print("✅ VALIDATION PASSED - All configurations aligned")
        print("=" * 60)


def main() -> None:
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    validator = ConfigurationValidator(project_root)

    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
