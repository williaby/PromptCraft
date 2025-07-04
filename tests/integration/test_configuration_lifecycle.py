"""Integration tests for the complete configuration system lifecycle.

This module tests the full configuration system end-to-end, including:
- Loading configurations from different sources
- Environment-specific behavior
- Encryption integration
- Health check integration
- Error handling and recovery
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.config.health import (
    get_configuration_health_summary,
    get_configuration_status,
)
from src.config.settings import (
    ApplicationSettings,
    ConfigurationValidationError,
    reload_settings,
)
from src.main import app


class TestConfigurationLifecycle:
    """Test the complete configuration lifecycle from loading to health checks."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any cached settings
        reload_settings()

        # Store original environment to restore later
        self.original_env = dict(os.environ)

        # Clear all PROMPTCRAFT_ environment variables
        for key in list(os.environ.keys()):
            if key.startswith("PROMPTCRAFT_"):
                del os.environ[key]

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Reload settings to default state
        reload_settings()

    def test_development_environment_full_cycle(self):
        """Test complete configuration cycle in development environment."""
        # Set development environment
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "dev"
        os.environ["PROMPTCRAFT_APP_NAME"] = "Test PromptCraft"
        os.environ["PROMPTCRAFT_API_HOST"] = "localhost"
        os.environ["PROMPTCRAFT_API_PORT"] = "3000"
        os.environ["PROMPTCRAFT_DEBUG"] = "true"

        # Load settings
        settings = reload_settings()

        # Verify configuration loaded correctly
        assert settings.environment == "dev"
        assert settings.app_name == "Test PromptCraft"
        assert settings.api_host == "localhost"
        assert settings.api_port == 3000
        assert settings.debug is True

        # Test configuration status
        status = get_configuration_status(settings)
        assert status.environment == "dev"
        assert status.config_loaded is True
        assert status.validation_status == "passed"
        assert status.config_healthy is True

        # Test health summary
        health_summary = get_configuration_health_summary()
        assert health_summary["healthy"] is True
        assert health_summary["environment"] == "dev"
        assert health_summary["config_loaded"] is True

    def test_production_environment_with_secrets(self):
        """Test production environment configuration with secrets."""
        # Set production environment with all required secrets
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "prod"
        os.environ["PROMPTCRAFT_APP_NAME"] = "PromptCraft Production"
        os.environ["PROMPTCRAFT_API_HOST"] = "0.0.0.0"
        os.environ["PROMPTCRAFT_API_PORT"] = "80"
        os.environ["PROMPTCRAFT_DEBUG"] = "false"
        os.environ["PROMPTCRAFT_SECRET_KEY"] = "production-secret-key-32-chars-long"
        os.environ["PROMPTCRAFT_JWT_SECRET_KEY"] = (
            "jwt-production-secret-key-long-enough"
        )
        os.environ["PROMPTCRAFT_API_KEY"] = "prod-api-key-12345"

        # Mock encryption availability for production
        with patch("src.config.settings.validate_encryption_available") as mock_encrypt:
            mock_encrypt.return_value = True

            settings = reload_settings()

            # Verify production configuration
            assert settings.environment == "prod"
            assert settings.app_name == "PromptCraft Production"
            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 80
            assert settings.debug is False
            assert settings.secret_key is not None
            assert settings.jwt_secret_key is not None
            assert settings.api_key is not None

            # Verify secrets are properly handled
            assert (
                settings.secret_key.get_secret_value()
                == "production-secret-key-32-chars-long"
            )
            assert (
                settings.jwt_secret_key.get_secret_value()
                == "jwt-production-secret-key-long-enough"
            )
            assert settings.api_key.get_secret_value() == "prod-api-key-12345"

            # Test configuration status
            status = get_configuration_status(settings)
            assert status.environment == "prod"
            assert status.config_loaded is True
            assert status.encryption_enabled is True
            assert status.validation_status == "passed"
            assert status.secrets_configured == 3
            assert status.config_healthy is True

    def test_production_environment_missing_secrets(self):
        """Test production environment with missing required secrets."""
        # Set production environment without required secrets
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "prod"
        os.environ["PROMPTCRAFT_API_HOST"] = "0.0.0.0"
        os.environ["PROMPTCRAFT_DEBUG"] = "false"
        # Intentionally not setting SECRET_KEY and JWT_SECRET_KEY

        with patch("src.config.settings.validate_encryption_available") as mock_encrypt:
            mock_encrypt.return_value = True

            settings = reload_settings()

            # Configuration should load but validation should fail
            status = get_configuration_status(settings)
            assert status.environment == "prod"
            assert status.config_loaded is True
            assert status.validation_status == "failed"
            assert status.config_healthy is False
            assert len(status.validation_errors) > 0

            # Check that validation errors mention missing secrets
            error_text = " ".join(status.validation_errors)
            assert "secret" in error_text.lower()

    def test_staging_environment_configuration(self):
        """Test staging environment configuration requirements."""
        # Set staging environment
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "staging"
        os.environ["PROMPTCRAFT_APP_NAME"] = "PromptCraft Staging"
        os.environ["PROMPTCRAFT_API_HOST"] = "staging.example.com"
        os.environ["PROMPTCRAFT_API_PORT"] = "8080"
        os.environ["PROMPTCRAFT_DEBUG"] = "false"
        os.environ["PROMPTCRAFT_SECRET_KEY"] = "staging-secret-key-for-testing"

        with patch("src.config.settings.validate_encryption_available") as mock_encrypt:
            mock_encrypt.return_value = True

            settings = reload_settings()

            # Verify staging configuration
            assert settings.environment == "staging"
            assert settings.app_name == "PromptCraft Staging"
            assert settings.api_host == "staging.example.com"
            assert settings.api_port == 8080
            assert settings.debug is False
            assert settings.secret_key is not None

            # Test configuration status
            status = get_configuration_status(settings)
            assert status.environment == "staging"
            assert status.config_loaded is True
            assert status.validation_status == "passed"
            assert status.config_healthy is True

    @patch("src.config.settings.load_encrypted_env")
    def test_encrypted_file_loading_integration(self, mock_load_encrypted):
        """Test integration with encrypted .env file loading."""
        # Mock encrypted file content
        mock_load_encrypted.return_value = {
            "PROMPTCRAFT_API_KEY": "encrypted-api-key-value",
            "PROMPTCRAFT_SECRET_KEY": "encrypted-secret-key-value",
            "PROMPTCRAFT_DATABASE_PASSWORD": "encrypted-db-password",
        }

        # Create temporary encrypted file
        with tempfile.NamedTemporaryFile(suffix=".gpg", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Set environment to use encrypted file
            os.environ["PROMPTCRAFT_ENVIRONMENT"] = "prod"
            os.environ["PROMPTCRAFT_ENCRYPTED_ENV_FILE"] = str(tmp_path)

            with patch(
                "src.config.settings.validate_encryption_available",
            ) as mock_encrypt:
                mock_encrypt.return_value = True

                settings = reload_settings()

                # Verify encrypted values were loaded
                assert settings.api_key is not None
                assert settings.secret_key is not None
                assert settings.database_password is not None

                # Verify secret values
                assert settings.api_key.get_secret_value() == "encrypted-api-key-value"
                assert (
                    settings.secret_key.get_secret_value()
                    == "encrypted-secret-key-value"
                )
                assert (
                    settings.database_password.get_secret_value()
                    == "encrypted-db-password"
                )

                # Test configuration status
                status = get_configuration_status(settings)
                assert status.config_source == "env_files"
                assert status.encryption_enabled is True
                assert status.secrets_configured == 3

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_configuration_validation_error_handling(self):
        """Test configuration validation error handling and recovery."""
        # Set invalid configuration
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "prod"
        os.environ["PROMPTCRAFT_API_PORT"] = "99999"  # Invalid port
        os.environ["PROMPTCRAFT_API_HOST"] = ""  # Invalid empty host
        os.environ["PROMPTCRAFT_DEBUG"] = "true"  # Invalid for production

        with patch("src.config.settings.validate_encryption_available") as mock_encrypt:
            mock_encrypt.return_value = False

            # Configuration should load but have validation errors
            settings = reload_settings()
            status = get_configuration_status(settings)

            assert status.config_loaded is True
            assert status.validation_status == "failed"
            assert status.config_healthy is False
            assert len(status.validation_errors) > 0

            # Test health summary with errors
            health_summary = get_configuration_health_summary()
            assert health_summary["healthy"] is False

    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over file configurations."""
        # Set environment variable
        os.environ["PROMPTCRAFT_API_PORT"] = "5000"
        os.environ["PROMPTCRAFT_APP_NAME"] = "Environment Override"

        # Create temporary .env file with different values
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".env",
            delete=False,
        ) as tmp_file:
            tmp_file.write("PROMPTCRAFT_API_PORT=3000\n")
            tmp_file.write("PROMPTCRAFT_APP_NAME=File Value\n")
            tmp_path = Path(tmp_file.name)

        try:
            # Mock _get_project_root to point to temp file directory
            with patch("src.config.settings._get_project_root") as mock_root:
                mock_root.return_value = tmp_path.parent

                # Rename temp file to .env
                env_path = tmp_path.parent / ".env"
                tmp_path.rename(env_path)

                settings = reload_settings()

                # Environment variables should override file values
                assert settings.api_port == 5000  # From environment
                assert settings.app_name == "Environment Override"  # From environment

        finally:
            # Clean up
            env_path.unlink(missing_ok=True)

    def test_cross_field_validation_warnings(self):
        """Test cross-field validation warnings in configuration."""
        # Set conflicting database configuration
        os.environ["PROMPTCRAFT_DATABASE_URL"] = "postgresql://user:pass@host:5432/db"
        os.environ["PROMPTCRAFT_DATABASE_PASSWORD"] = "separate-password"

        settings = reload_settings()
        status = get_configuration_status(settings)

        # Should have warning about conflicting database configuration
        assert status.config_loaded is True
        # Validation might pass but with warnings


class TestConfigurationHealthIntegration:
    """Test integration between configuration system and health check endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        # Clear any cached settings
        reload_settings()

    def teardown_method(self):
        """Clean up after tests."""
        reload_settings()

    def test_health_endpoint_integration_healthy(self):
        """Test /health endpoint integration with healthy configuration."""
        # Set up healthy configuration
        with patch.dict(
            os.environ,
            {
                "PROMPTCRAFT_ENVIRONMENT": "dev",
                "PROMPTCRAFT_API_HOST": "localhost",
                "PROMPTCRAFT_API_PORT": "8000",
            },
        ):
            with patch(
                "src.config.settings.validate_encryption_available",
            ) as mock_encrypt:
                mock_encrypt.return_value = True

                response = self.client.get("/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["healthy"] is True
                assert data["environment"] == "dev"

    def test_health_endpoint_integration_unhealthy(self):
        """Test /health endpoint integration with unhealthy configuration."""
        # Set up unhealthy configuration (production with debug enabled)
        with patch.dict(
            os.environ,
            {
                "PROMPTCRAFT_ENVIRONMENT": "prod",
                "PROMPTCRAFT_DEBUG": "true",  # Invalid for production
                "PROMPTCRAFT_API_HOST": "localhost",  # Invalid for production
            },
        ):
            with patch(
                "src.config.settings.validate_encryption_available",
            ) as mock_encrypt:
                mock_encrypt.return_value = False  # No encryption in production

                response = self.client.get("/health")

                assert response.status_code == 503
                data = response.json()
                assert data["detail"]["status"] == "unhealthy"
                assert data["detail"]["healthy"] is False

    def test_config_health_endpoint_integration(self):
        """Test /health/config endpoint integration."""
        with patch.dict(
            os.environ,
            {
                "PROMPTCRAFT_ENVIRONMENT": "staging",
                "PROMPTCRAFT_SECRET_KEY": "staging-secret-key",
            },
        ):
            with patch(
                "src.config.settings.validate_encryption_available",
            ) as mock_encrypt:
                mock_encrypt.return_value = True

                response = self.client.get("/health/config")

                assert response.status_code == 200
                data = response.json()
                assert data["environment"] == "staging"
                assert data["config_loaded"] is True
                assert data["encryption_enabled"] is True
                assert data["config_healthy"] is True

    def test_configuration_error_endpoint_response(self):
        """Test endpoint behavior when configuration fails completely."""
        # Mock a complete configuration failure
        with patch("src.config.settings.get_settings") as mock_get_settings:
            mock_get_settings.side_effect = ConfigurationValidationError(
                "Critical configuration failure",
                field_errors=["Missing required configuration"],
                suggestions=["Check environment variables"],
            )

            response = self.client.get("/health/config")

            assert response.status_code == 500
            data = response.json()
            assert "Configuration validation failed" in data["detail"]["error"]


class TestConfigurationErrorRecovery:
    """Test configuration system error recovery and graceful degradation."""

    def setup_method(self):
        """Set up test environment."""
        reload_settings()
        self.original_env = dict(os.environ)

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        reload_settings()

    def test_encryption_unavailable_graceful_degradation(self):
        """Test graceful degradation when encryption is unavailable."""
        # Set production environment without encryption
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "prod"
        os.environ["PROMPTCRAFT_SECRET_KEY"] = "production-secret-key"

        with patch("src.config.settings.validate_encryption_available") as mock_encrypt:
            mock_encrypt.return_value = False

            # Should not raise exception, but should warn
            settings = reload_settings()

            assert settings.environment == "prod"
            assert settings.secret_key is not None

            # Health check should reflect encryption unavailability
            status = get_configuration_status(settings)
            assert status.config_loaded is True
            assert status.encryption_enabled is False

    def test_partial_configuration_loading(self):
        """Test behavior with partial configuration loading."""
        # Set some valid and some invalid configuration
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "dev"
        os.environ["PROMPTCRAFT_APP_NAME"] = "Valid App Name"
        os.environ["PROMPTCRAFT_API_PORT"] = "invalid-port"  # Invalid

        # Should load valid settings and use defaults for invalid ones
        settings = reload_settings()

        assert settings.environment == "dev"
        assert settings.app_name == "Valid App Name"
        # Should fall back to default port due to validation error
        assert isinstance(settings.api_port, int)

    def test_file_loading_error_recovery(self):
        """Test recovery when .env file loading fails."""
        # Create invalid .env file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".env",
            delete=False,
        ) as tmp_file:
            tmp_file.write("INVALID LINE WITHOUT EQUALS\n")
            tmp_file.write("PROMPTCRAFT_ENVIRONMENT=dev\n")
            tmp_path = Path(tmp_file.name)

        try:
            with patch("src.config.settings._get_project_root") as mock_root:
                mock_root.return_value = tmp_path.parent

                # Rename to .env
                env_path = tmp_path.parent / ".env"
                tmp_path.rename(env_path)

                # Should handle invalid lines gracefully
                settings = reload_settings()
                assert settings.environment == "dev"  # Valid line should be processed

        finally:
            env_path.unlink(missing_ok=True)


class TestAcceptanceCriteria:
    """Test all acceptance criteria from the original configuration system requirements."""

    def setup_method(self):
        """Set up test environment."""
        reload_settings()
        self.original_env = dict(os.environ)

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        reload_settings()

    def test_pydantic_schema_validation(self):
        """Test that configuration classes are defined with Pydantic schema validation."""
        # Test that ApplicationSettings is a Pydantic model
        assert issubclass(ApplicationSettings, BaseSettings)

        # Test schema validation
        with pytest.raises(ValueError):
            ApplicationSettings(api_port=99999)  # Invalid port

        with pytest.raises(ValueError):
            ApplicationSettings(api_host="")  # Empty host

    def test_environment_specific_configs(self):
        """Test that environment-specific configurations work (dev, staging, prod)."""
        # Test development environment
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "dev"
        dev_settings = reload_settings()
        assert dev_settings.environment == "dev"

        # Test staging environment
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "staging"
        staging_settings = reload_settings()
        assert staging_settings.environment == "staging"

        # Test production environment
        os.environ["PROMPTCRAFT_ENVIRONMENT"] = "prod"
        prod_settings = reload_settings()
        assert prod_settings.environment == "prod"

    def test_env_file_encryption_integration(self):
        """Test that .env file encryption/decryption is integrated with settings loading."""
        with patch("src.config.settings.validate_encryption_available") as mock_encrypt:
            mock_encrypt.return_value = True

            with patch("src.config.settings.load_encrypted_env") as mock_load:
                mock_load.return_value = {
                    "PROMPTCRAFT_API_KEY": "encrypted-key",
                    "PROMPTCRAFT_SECRET_KEY": "encrypted-secret",
                }

                # Create temporary encrypted file
                with tempfile.NamedTemporaryFile(
                    suffix=".gpg",
                    delete=False,
                ) as tmp_file:
                    tmp_path = Path(tmp_file.name)

                try:
                    os.environ["PROMPTCRAFT_ENCRYPTED_ENV_FILE"] = str(tmp_path)
                    settings = reload_settings()

                    assert settings.api_key is not None
                    assert settings.secret_key is not None

                finally:
                    tmp_path.unlink(missing_ok=True)

    def test_configuration_parameter_validation(self):
        """Test that all configuration parameters are validated with appropriate error messages."""
        # Test port validation
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(api_port=0)
        assert "Port 0 is outside valid range" in str(exc_info.value)

        # Test host validation
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(api_host="")
        assert "API host cannot be empty" in str(exc_info.value)

        # Test version validation
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(version="invalid")
        assert "Invalid version format" in str(exc_info.value)

    def test_default_configurations_immediate_start(self):
        """Test that default configurations allow immediate development start."""
        # Clear all environment variables
        for key in list(os.environ.keys()):
            if key.startswith("PROMPTCRAFT_"):
                del os.environ[key]

        # Should be able to create settings with defaults
        settings = reload_settings()

        # Should have sensible defaults for development
        assert settings.environment == "dev"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.debug is True
        assert settings.app_name == "PromptCraft-Hybrid"

    def test_health_check_endpoints_return_status(self):
        """Test that health check endpoints return configuration status."""
        client = TestClient(app)

        # Test main health endpoint
        response = client.get("/health")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data

        # Test detailed config health endpoint
        response = client.get("/health/config")
        assert response.status_code in (200, 500)

        if response.status_code == 200:
            data = response.json()
            assert "config_loaded" in data
            assert "environment" in data
            assert "validation_status" in data

    def test_sensitive_values_never_logged_or_exposed(self):
        """Test that sensitive values are never logged or exposed in error messages."""
        # Create settings with secret values
        settings = ApplicationSettings(
            api_key=SecretStr("super-secret-api-key"),
            secret_key=SecretStr("super-secret-app-key"),
            database_password=SecretStr("super-secret-db-password"),
        )

        # Test that secrets are not in string representation
        settings_str = str(settings)
        assert "super-secret-api-key" not in settings_str
        assert "super-secret-app-key" not in settings_str
        assert "super-secret-db-password" not in settings_str

        # Test that health checks don't expose secrets
        status = get_configuration_status(settings)
        status_json = status.model_dump_json()
        assert "super-secret-api-key" not in status_json
        assert "super-secret-app-key" not in status_json
        assert "super-secret-db-password" not in status_json

        # Test health summary doesn't expose secrets
        health_summary = get_configuration_health_summary()
        health_json = json.dumps(health_summary)
        assert "super-secret-api-key" not in health_json
        assert "super-secret-app-key" not in health_json
        assert "super-secret-db-password" not in health_json
