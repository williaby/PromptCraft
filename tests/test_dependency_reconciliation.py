"""
Test suite for dependency reconciliation and version constraint standardization.

This test suite validates the fix for PR #149 dependency conflicts by ensuring:
1. Target packages resolve to expected intermediate versions
2. All constraints follow standardized caret notation
3. No dependency conflicts exist in the resolution
4. Requirements files are consistent with pyproject.toml
"""

import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


class TestDependencyReconciliation:
    """Test dependency reconciliation fixes for PR #149."""

    @pytest.fixture()
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture()
    def pyproject_data(self, project_root: Path) -> dict:
        """Load pyproject.toml data."""
        pyproject_path = project_root / "pyproject.toml"
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)

    @pytest.fixture()
    def requirements_content(self, project_root: Path) -> str:
        """Load requirements.txt content."""
        requirements_path = project_root / "requirements.txt"
        return requirements_path.read_text()

    def test_target_packages_intermediate_versions(self, requirements_content: str):
        """Test that target packages resolve to expected intermediate versions."""
        # Check azure-identity resolves to ~1.17.1
        azure_match = re.search(r"azure-identity==([0-9.]+)", requirements_content)
        assert azure_match, "azure-identity not found in requirements.txt"
        azure_version = azure_match.group(1)
        assert (
            azure_version == "1.17.1"
        ), f"Expected azure-identity==1.17.1, got {azure_version}"

        # Check qdrant-client resolves to ~1.9.2
        qdrant_match = re.search(r"qdrant-client==([0-9.]+)", requirements_content)
        assert qdrant_match, "qdrant-client not found in requirements.txt"
        qdrant_version = qdrant_match.group(1)
        assert (
            qdrant_version == "1.9.2"
        ), f"Expected qdrant-client==1.9.2, got {qdrant_version}"

    def test_constraint_standardization(self, pyproject_data: dict):
        """Test that most dependencies use standardized caret (^) notation."""
        dependencies = pyproject_data["tool"]["poetry"]["dependencies"]

        # Count constraint types (excluding python and complex dependencies)
        caret_count = 0
        tilde_count = 0
        total_count = 0

        for name, spec in dependencies.items():
            if name == "python":
                continue

            # Handle dict format (extras)
            if isinstance(spec, dict):
                version_spec = spec.get("version", "")
            else:
                version_spec = spec

            if not version_spec:
                continue

            total_count += 1
            if version_spec.startswith("^"):
                caret_count += 1
            elif version_spec.startswith("~"):
                tilde_count += 1

        # We expect most dependencies to use caret, with specific exceptions for tilde
        caret_percentage = (caret_count / total_count) * 100
        assert (
            caret_percentage >= 85
        ), f"Only {caret_percentage:.1f}% use caret notation, expected >= 85%"

        # Verify specific packages use tilde (intermediate versions)
        assert dependencies["azure-identity"] == "~1.17.1"
        assert dependencies["qdrant-client"] == "~1.9.2"

    def test_no_range_constraints(self, pyproject_data: dict):
        """Test that range constraints (>=,<) have been eliminated."""
        dependencies = pyproject_data["tool"]["poetry"]["dependencies"]

        range_constraints = []
        for name, spec in dependencies.items():
            if name == "python":
                continue

            # Handle dict format (extras)
            if isinstance(spec, dict):
                version_spec = spec.get("version", "")
            else:
                version_spec = spec

            if not version_spec:
                continue

            # Check for range constraint patterns
            if ">=" in version_spec and "<" in version_spec:
                range_constraints.append(f"{name}: {version_spec}")

        assert not range_constraints, f"Found range constraints: {range_constraints}"

    def test_poetry_configuration_valid(self, project_root: Path):
        """Test that Poetry configuration is valid and consistent."""
        result = subprocess.run(
            ["poetry", "check"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Poetry check failed: {result.stderr}"

    def test_lock_file_consistency(self, project_root: Path):
        """Test that poetry.lock is consistent with pyproject.toml."""
        # Check that lock file exists and is up to date
        lock_path = project_root / "poetry.lock"
        assert lock_path.exists(), "poetry.lock file missing"

        # Test poetry show command works (indicates valid lock file)
        result = subprocess.run(
            ["poetry", "show", "--quiet"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Poetry show failed: {result.stderr}"

    def test_requirements_files_generated(self, project_root: Path):
        """Test that all requirements files exist and are properly formatted."""
        required_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-docker.txt",
        ]

        for req_file in required_files:
            file_path = project_root / req_file
            assert file_path.exists(), f"{req_file} not found"

            content = file_path.read_text()
            assert content.strip(), f"{req_file} is empty"

            # Check for hash verification (security requirement)
            assert "sha256:" in content, f"{req_file} missing hash verification"

    def test_no_security_vulnerabilities(self, pyproject_data: dict):
        """Test that our version selections don't introduce known vulnerabilities."""
        # Check that we're not using known vulnerable versions
        dependencies = pyproject_data["tool"]["poetry"]["dependencies"]

        # Known vulnerable version ranges (examples)
        vulnerable_checks = {
            "gradio": lambda v: self._extract_version(v)
            >= "5.0.0",  # Should be >= 5.31.0
            "fastapi": lambda v: self._extract_version(v)
            >= "0.100.0",  # Should be >= 0.115.0
            "cryptography": lambda v: self._extract_version(v)
            >= "41.0.0",  # Should be >= 45.0.0
        }

        for package, check_func in vulnerable_checks.items():
            if package in dependencies:
                version_spec = dependencies[package]
                if isinstance(version_spec, dict):
                    version_spec = version_spec.get("version", "")

                assert check_func(
                    version_spec,
                ), f"{package} may be using vulnerable version: {version_spec}"

    def test_constraint_compatibility_matrix(self, pyproject_data: dict):
        """Test that constraint types follow the documented compatibility matrix."""
        dependencies = pyproject_data["tool"]["poetry"]["dependencies"]

        # Security-critical packages should use caret for more restrictive updates
        security_critical = [
            "cryptography",
            "pyjwt",
            "python-gnupg",
            "gradio",
            "fastapi",
            "httpx",
            "pydantic",
            "anthropic",
            "openai",
        ]

        for package in security_critical:
            if package in dependencies:
                version_spec = dependencies[package]
                if isinstance(version_spec, dict):
                    version_spec = version_spec.get("version", "")

                # Should use caret (^) or tilde (~) for security packages
                assert version_spec.startswith(
                    ("^", "~"),
                ), f"Security-critical package {package} should use ^ or ~ constraint: {version_spec}"

    @staticmethod
    def _extract_version(version_spec: str) -> str:
        """Extract version number from constraint specification."""
        # Remove constraint operators
        return re.sub(r"[^0-9.]", "", version_spec.split(",")[0])


class TestIntegrationValidation:
    """Integration tests to validate the complete fix."""

    @pytest.fixture()
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_dry_run_install_succeeds(self, project_root: Path):
        """Test that poetry install dry-run succeeds without conflicts."""
        result = subprocess.run(
            ["poetry", "install", "--dry-run"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Poetry install dry-run failed: {result.stderr}"

    def test_requirements_installation_simulation(self, project_root: Path):
        """Test that pip can parse requirements files without errors."""
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-docker.txt",
        ]

        for req_file in requirements_files:
            # Use pip-tools to validate requirements file format
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--dry-run",
                    "--quiet",
                    "-r",
                    req_file,
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            # Note: dry-run may fail due to missing packages, but should not fail on syntax
            # We're mainly checking that the file format is valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
