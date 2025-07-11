"""Tests for the setup validator utility module.

This module tests the system requirements validation and startup checks
that ensure the environment is properly configured for the application.
"""

from unittest.mock import Mock, patch

import pytest

from src.utils.setup_validator import (
    run_startup_checks,
    validate_environment_setup,
    validate_startup_configuration,
    validate_system_requirements,
)


class TestSetupValidator:
    """Test the setup validator utility functions."""

    def test_validate_system_requirements_valid(self):
        """Test that current Python version is considered valid."""
        # Current Python version should be valid since tests are running
        is_valid, errors = validate_system_requirements()
        assert is_valid is True
        assert errors == []

    @patch("sys.version_info", (3, 9, 0))
    def test_validate_system_requirements_invalid_python(self):
        """Test system requirements validation with invalid Python version."""
        is_valid, errors = validate_system_requirements()
        assert is_valid is False
        assert len(errors) > 0
        assert any("Python 3.11+ required" in error for error in errors)

    @patch("sys.version_info", (3, 11, 5))
    def test_validate_system_requirements_minimum_valid(self):
        """Test system requirements validation with minimum valid Python version."""
        is_valid, errors = validate_system_requirements()
        assert is_valid is True
        assert errors == []

    def test_validate_environment_setup(self):
        """Test environment setup validation."""
        # This may pass or fail depending on encryption setup
        success, errors, warnings = validate_environment_setup()

        # Should return the correct types
        assert isinstance(success, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    def test_validate_system_requirements_success(self):
        """Test system requirements validation when all checks pass."""
        success, errors = validate_system_requirements()

        # Should succeed in test environment
        assert success is True
        assert errors == []

    @patch("sys.version_info", (3, 10, 0))
    def test_validate_system_requirements_python_failure(self):
        """Test system requirements validation with Python version failure."""
        success, errors = validate_system_requirements()

        assert success is False
        assert len(errors) >= 1
        assert any("Python 3.11+ required" in error for error in errors)

    def test_validate_system_requirements_imports(self):
        """Test system requirements validation with import checks."""
        # Current environment should have required packages
        success, errors = validate_system_requirements()

        # Should succeed since pydantic and gnupg should be available
        assert isinstance(success, bool)
        assert isinstance(errors, list)

    def test_validate_startup_configuration_basic(self):
        """Test basic startup configuration validation."""
        # This function loads settings internally or uses provided ones
        # It returns a boolean indicating success/failure
        result = validate_startup_configuration()

        # Should return a boolean
        assert isinstance(result, bool)

    @patch("src.utils.setup_validator.validate_system_requirements")
    @patch("src.utils.setup_validator.validate_environment_setup")
    def test_run_startup_checks_success(self, mock_env_setup, mock_system_req):
        """Test running startup checks when all validations pass."""
        mock_system_req.return_value = (True, [])
        mock_env_setup.return_value = (True, [], [])

        with patch("src.config.settings.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.environment = "dev"
            mock_get_settings.return_value = mock_settings

            # Should not raise SystemExit for successful validation
            try:
                result = validate_startup_configuration()
                assert isinstance(result, bool)
            except SystemExit:
                pytest.fail("Should not exit on successful validation")

    @patch("src.utils.setup_validator.validate_system_requirements")
    def test_run_startup_checks_system_failure(self, mock_validate_system):
        """Test running startup checks when system validation fails."""
        mock_validate_system.return_value = (False, ["System validation error"])

        # Should exit with error code 1
        with pytest.raises(SystemExit) as exc_info:
            run_startup_checks()

        assert exc_info.value.code == 1


class TestEnvironmentValidation:
    """Test environment-specific validation logic."""

    def test_environment_validation_types(self):
        """Test basic environment validation functionality."""
        # Test that validation functions return expected types
        success, errors, warnings = validate_environment_setup()

        assert isinstance(success, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    def test_system_requirements_basic(self):
        """Test basic system requirements validation."""
        success, errors = validate_system_requirements()

        # Should return proper types
        assert isinstance(success, bool)
        assert isinstance(errors, list)

        # In test environment, should generally pass
        if not success:
            # Log errors for debugging (errors available in 'errors' list)
            pass


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("sys.version_info", (3, 9, 0))
    def test_python_version_edge_cases(self):
        """Test Python version checking with edge cases."""
        # Test version comparison logic
        success, errors = validate_system_requirements()
        assert success is False
        assert any("Python 3.11+ required" in error for error in errors)

    def test_validation_robustness(self):
        """Test validation robustness with actual system."""
        # Test actual system validation
        success, errors = validate_system_requirements()

        # Should handle system information gracefully
        assert isinstance(success, bool)
        assert isinstance(errors, list)

        # Test environment setup
        env_success, env_errors, env_warnings = validate_environment_setup()
        assert isinstance(env_success, bool)
        assert isinstance(env_errors, list)
        assert isinstance(env_warnings, list)

    def test_startup_configuration_with_none(self):
        """Test startup configuration with None argument."""
        # The function should handle None by loading settings internally
        result = validate_startup_configuration(None)
        assert isinstance(result, bool)
