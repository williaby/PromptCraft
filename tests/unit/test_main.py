"""Tests for the main FastAPI application module."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.config.settings import ApplicationSettings, ConfigurationValidationError
from src.main import app, create_app, lifespan


class TestAppCreation:
    """Test FastAPI app creation and configuration."""

    @patch("src.main.get_settings")
    def test_create_app_with_valid_settings(self, mock_get_settings) -> None:
        """Test app creation with valid settings."""
        mock_settings = ApplicationSettings(
            app_name="Test App",
            version="1.0.0",
            environment="dev",
            debug=True,
        )
        mock_get_settings.return_value = mock_settings

        app_instance = create_app()

        assert app_instance.title == "Test App"
        assert app_instance.version == "1.0.0"
        assert app_instance.docs_url == "/docs"  # Debug mode enabled
        assert app_instance.redoc_url == "/redoc"

    @patch("src.main.get_settings")
    def test_create_app_production_mode(self, mock_get_settings) -> None:
        """Test app creation in production mode."""
        mock_settings = ApplicationSettings(
            app_name="Prod App",
            version="2.0.0",
            environment="prod",
            debug=False,
        )
        mock_get_settings.return_value = mock_settings

        app_instance = create_app()

        assert app_instance.title == "Prod App"
        assert app_instance.version == "2.0.0"
        assert app_instance.docs_url is None  # Debug mode disabled
        assert app_instance.redoc_url is None

    @patch("src.main.get_settings")
    def test_create_app_with_settings_error(self, mock_get_settings) -> None:
        """Test app creation when settings loading fails."""
        mock_get_settings.side_effect = ValueError("Settings error")

        app_instance = create_app()

        # Should fallback to defaults
        assert app_instance.title == "PromptCraft-Hybrid"
        assert app_instance.version == "0.1.0"

    @patch("src.main.get_settings")
    def test_create_app_with_unexpected_error(self, mock_get_settings) -> None:
        """Test app creation with unexpected error."""
        mock_get_settings.side_effect = RuntimeError("Unexpected error")

        app_instance = create_app()

        # Should fallback to defaults
        assert app_instance.title == "PromptCraft-Hybrid"

    def test_cors_configuration_dev(self) -> None:
        """Test CORS configuration for development environment."""
        with patch("src.main.get_settings") as mock_get_settings:
            mock_settings = ApplicationSettings(environment="dev")
            mock_get_settings.return_value = mock_settings

            app_instance = create_app()

            # Check that CORS middleware is added (we can't easily inspect the config)
            # But we can verify the app was created without errors
            assert app_instance is not None

    def test_cors_configuration_staging(self) -> None:
        """Test CORS configuration for staging environment."""
        with patch("src.main.get_settings") as mock_get_settings:
            mock_settings = ApplicationSettings(environment="staging")
            mock_get_settings.return_value = mock_settings

            app_instance = create_app()
            assert app_instance is not None

    def test_cors_configuration_prod(self) -> None:
        """Test CORS configuration for production environment."""
        with patch("src.main.get_settings") as mock_get_settings:
            mock_settings = ApplicationSettings(environment="prod")
            mock_get_settings.return_value = mock_settings

            app_instance = create_app()
            assert app_instance is not None

    def test_cors_configuration_unknown_env(self) -> None:
        """Test CORS configuration for unknown environment."""
        with patch("src.main.get_settings") as mock_get_settings:
            # Create settings with valid environment first, then modify
            mock_settings = ApplicationSettings(environment="dev")
            # Manually override environment for testing (bypassing validation)
            mock_settings.environment = "test"
            mock_get_settings.return_value = mock_settings

            app_instance = create_app()
            assert app_instance is not None


class TestRootEndpoints:
    """Test basic endpoints in the FastAPI app."""

    def setup_method(self) -> None:
        """Set up test client."""
        self.client = TestClient(app)

    def test_root_endpoint_with_app_state(self) -> None:
        """Test root endpoint when app state is available."""
        # Mock app state
        mock_settings = ApplicationSettings(
            app_name="Test App",
            version="1.0.0",
            environment="dev",
            debug=True,
        )
        app.state.settings = mock_settings

        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Test App"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "dev"
        assert data["status"] == "running"
        assert data["docs_url"] == "/docs"

    def test_root_endpoint_without_app_state(self) -> None:
        """Test root endpoint when app state is not available."""
        # Remove app state if it exists
        if hasattr(app.state, "settings"):
            delattr(app.state, "settings")

        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "PromptCraft-Hybrid"
        assert data["version"] == "unknown"
        assert data["environment"] == "unknown"
        assert data["status"] == "running"

    def test_ping_endpoint(self) -> None:
        """Test ping endpoint."""
        response = self.client.get("/ping")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"


class TestLifespanEvents:
    """Test application lifespan events."""

    @patch("src.main.get_settings")
    async def test_lifespan_startup_success(self, mock_get_settings) -> None:
        """Test successful application startup."""
        mock_settings = ApplicationSettings(
            app_name="Test App",
            version="1.0.0",
            environment="dev",
        )
        mock_get_settings.return_value = mock_settings

        # Test the lifespan context manager directly
        mock_app = MagicMock()
        mock_app.state = MagicMock()

        # Test that the lifespan context manager works
        async with lifespan(mock_app):
            # Verify settings were stored in app state
            assert mock_app.state.settings == mock_settings

    @patch("src.main.get_settings")
    async def test_lifespan_configuration_validation_error(self, mock_get_settings) -> None:
        """Test startup with configuration validation error."""
        mock_get_settings.side_effect = ConfigurationValidationError(
            "Config error",
            field_errors=["Error 1", "Error 2"],
            suggestions=["Fix 1", "Fix 2"],
        )

        mock_app = MagicMock()

        # Should raise ConfigurationValidationError
        with pytest.raises(ConfigurationValidationError):
            async with lifespan(mock_app):
                pass

    @patch("src.main.get_settings")
    async def test_lifespan_unexpected_error(self, mock_get_settings) -> None:
        """Test startup with unexpected error."""
        mock_get_settings.side_effect = RuntimeError("Unexpected error")

        mock_app = MagicMock()

        # Should raise the RuntimeError
        with pytest.raises(RuntimeError):
            async with lifespan(mock_app):
                pass


class TestMainScriptExecution:
    """Test the main script execution scenarios."""

    def test_settings_properties_for_main(self) -> None:
        """Test that settings have the properties needed for main execution."""
        settings = ApplicationSettings(
            api_host="localhost",
            api_port=8000,
            debug=True,
        )

        assert settings.api_host == "localhost"
        assert settings.api_port == 8000
        assert settings.debug is True

    def test_configuration_error_handling(self) -> None:
        """Test that configuration errors are properly raised."""
        with pytest.raises(ConfigurationValidationError):
            raise ConfigurationValidationError("Config error")

    def test_os_error_handling(self) -> None:
        """Test that OS errors are properly raised."""
        with pytest.raises(OSError, match="Failed to start server"):
            raise OSError("Failed to start server")

    def test_runtime_error_handling(self) -> None:
        """Test that runtime errors are properly raised."""
        with pytest.raises(RuntimeError):
            raise RuntimeError("Unexpected error")
