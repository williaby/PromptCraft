"""Comprehensive unit tests for auth_simple configuration management.

This module provides extensive test coverage for the simplified authentication
configuration system, following patterns from src/auth tests for consistency
and easy migration path.

Test Coverage:
- AuthConfig model validation and defaults
- ConfigLoader environment variable parsing
- ConfigManager initialization and methods
- Field validators and edge cases
- Configuration warnings and validation
"""

import os
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from src.auth_simple.config import (
    AuthConfig,
    AuthMode,
    CloudflareConfig,
    ConfigLoader,
    ConfigManager,
    LogLevel,
    get_auth_config,
    get_config_manager,
    reset_config,
)


@pytest.mark.unit
class TestAuthMode:
    """Test AuthMode enum."""

    def test_auth_mode_values(self):
        """Test AuthMode enum values."""
        assert AuthMode.CLOUDFLARE_SIMPLE == "cloudflare_simple"
        assert AuthMode.DISABLED == "disabled"

    def test_auth_mode_string_conversion(self):
        """Test AuthMode string conversion."""
        assert AuthMode.CLOUDFLARE_SIMPLE.value == "cloudflare_simple"
        assert AuthMode.DISABLED.value == "disabled"


@pytest.mark.unit
class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_level_values(self):
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"


@pytest.mark.unit
class TestCloudflareConfig:
    """Test CloudflareConfig dataclass."""

    def test_default_values(self):
        """Test CloudflareConfig default values."""
        config = CloudflareConfig()

        assert config.validate_headers is True
        assert config.required_headers == ["cf-ray"]
        assert config.log_events is True
        assert config.trust_cf_headers is True

    def test_custom_values(self):
        """Test CloudflareConfig with custom values."""
        config = CloudflareConfig(
            validate_headers=False,
            required_headers=["cf-ray", "cf-ipcountry"],
            log_events=False,
            trust_cf_headers=False,
        )

        assert config.validate_headers is False
        assert config.required_headers == ["cf-ray", "cf-ipcountry"]
        assert config.log_events is False
        assert config.trust_cf_headers is False


@pytest.mark.unit
class TestAuthConfigDefaults:
    """Test AuthConfig default values and basic initialization."""

    def test_init_default_values(self):
        """Test AuthConfig initialization with default values."""
        config = AuthConfig()

        # Core authentication
        assert config.auth_mode == AuthMode.CLOUDFLARE_SIMPLE
        assert config.enabled is True

        # Email whitelist
        assert config.email_whitelist == []
        assert config.admin_emails == []
        assert config.full_users == []
        assert config.limited_users == []
        assert config.case_sensitive_emails is False

        # Session management
        assert config.session_timeout == 3600
        assert config.enable_session_cookies is True
        assert config.session_cookie_secure is True
        assert config.session_cookie_httponly is True

        # Public paths
        expected_paths = {
            "/",
            "/ping",
            "/health",
            "/api/health",
            "/api/v1/health",
            "/health/config",
            "/health/mcp",
            "/health/circuit-breakers",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/validate",
            "/api/v1/search",
        }
        assert config.public_paths == expected_paths

        # Cloudflare config
        assert isinstance(config.cloudflare, CloudflareConfig)
        assert config.cloudflare.validate_headers is True

        # Logging
        assert config.log_level == LogLevel.INFO
        assert config.log_auth_events is True
        assert config.log_failed_attempts is True

        # Development
        assert config.dev_mode is False
        assert config.mock_cf_headers == {}

    def test_init_custom_values(self):
        """Test AuthConfig initialization with custom values."""
        config = AuthConfig(
            auth_mode=AuthMode.DISABLED,
            enabled=False,
            email_whitelist=["test@example.com", "@company.com"],
            admin_emails=["admin@example.com"],
            full_users=["full@example.com"],
            limited_users=["limited@example.com"],
            case_sensitive_emails=True,
            session_timeout=7200,
            enable_session_cookies=False,
            session_cookie_secure=False,
            session_cookie_httponly=False,
            public_paths={"/custom", "/api/public"},
            log_level=LogLevel.DEBUG,
            log_auth_events=False,
            log_failed_attempts=False,
            dev_mode=True,
            mock_cf_headers={"cf-ray": "test-123"},
        )

        assert config.auth_mode == AuthMode.DISABLED
        assert config.enabled is False
        assert config.email_whitelist == ["test@example.com", "@company.com"]
        assert config.admin_emails == ["admin@example.com"]
        assert config.full_users == ["full@example.com"]
        assert config.limited_users == ["limited@example.com"]
        assert config.case_sensitive_emails is True
        assert config.session_timeout == 7200
        assert config.enable_session_cookies is False
        assert config.session_cookie_secure is False
        assert config.session_cookie_httponly is False
        assert config.public_paths == {"/custom", "/api/public"}
        assert config.log_level == LogLevel.DEBUG
        assert config.log_auth_events is False
        assert config.log_failed_attempts is False
        assert config.dev_mode is True
        assert config.mock_cf_headers == {"cf-ray": "test-123"}


@pytest.mark.unit
class TestAuthConfigValidators:
    """Test AuthConfig field validators."""

    def test_parse_email_whitelist_from_string(self):
        """Test parsing email whitelist from comma-separated string."""
        config = AuthConfig(email_whitelist="test@example.com, admin@company.com,  @domain.com")
        assert config.email_whitelist == ["test@example.com", "admin@company.com", "@domain.com"]

    def test_parse_email_whitelist_from_list(self):
        """Test parsing email whitelist from list."""
        config = AuthConfig(email_whitelist=["test@example.com", "admin@company.com"])
        assert config.email_whitelist == ["test@example.com", "admin@company.com"]

    def test_parse_email_whitelist_empty_string(self):
        """Test parsing empty email whitelist string."""
        config = AuthConfig(email_whitelist="")
        assert config.email_whitelist == []

    def test_parse_email_whitelist_none(self):
        """Test parsing None email whitelist."""
        config = AuthConfig(email_whitelist=None)
        assert config.email_whitelist == []

    def test_parse_admin_emails_from_string(self):
        """Test parsing admin emails from comma-separated string."""
        config = AuthConfig(admin_emails="admin1@example.com, admin2@example.com")
        assert config.admin_emails == ["admin1@example.com", "admin2@example.com"]

    def test_parse_admin_emails_from_list(self):
        """Test parsing admin emails from list."""
        config = AuthConfig(admin_emails=["admin1@example.com", "admin2@example.com"])
        assert config.admin_emails == ["admin1@example.com", "admin2@example.com"]

    def test_parse_admin_emails_empty(self):
        """Test parsing empty admin emails."""
        config = AuthConfig(admin_emails="")
        assert config.admin_emails == []

    def test_parse_public_paths_from_string(self):
        """Test parsing public paths from comma-separated string."""
        config = AuthConfig(public_paths="/api/health, /docs,  /custom")
        assert config.public_paths == {"/api/health", "/docs", "/custom"}

    def test_parse_public_paths_from_list(self):
        """Test parsing public paths from list."""
        config = AuthConfig(public_paths=["/api/health", "/docs", "/custom"])
        assert config.public_paths == {"/api/health", "/docs", "/custom"}

    def test_parse_public_paths_from_set(self):
        """Test parsing public paths from set."""
        paths_set = {"/api/health", "/docs", "/custom"}
        config = AuthConfig(public_paths=paths_set)
        assert config.public_paths == paths_set

    def test_parse_public_paths_empty(self):
        """Test parsing empty public paths."""
        config = AuthConfig(public_paths="")
        assert config.public_paths == set()

    def test_validate_session_timeout_valid(self):
        """Test valid session timeout values."""
        config = AuthConfig(session_timeout=3600)  # 1 hour
        assert config.session_timeout == 3600

        config = AuthConfig(session_timeout=86400)  # 24 hours
        assert config.session_timeout == 86400

        config = AuthConfig(session_timeout=60)  # 1 minute
        assert config.session_timeout == 60

    def test_validate_session_timeout_too_low(self):
        """Test session timeout validation with value too low."""
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(session_timeout=30)  # Less than 60 seconds

        assert "Session timeout must be at least 60 seconds" in str(exc_info.value)

    def test_validate_session_timeout_too_high(self):
        """Test session timeout validation with value too high."""
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(session_timeout=86401)  # More than 24 hours

        assert "Session timeout must be less than 24 hours" in str(exc_info.value)


@pytest.mark.unit
class TestAuthConfigValidation:
    """Test AuthConfig validation methods."""

    def test_validate_configuration_dev_mode(self):
        """Test configuration validation in dev mode."""
        config = AuthConfig(dev_mode=True, email_whitelist=[])
        warnings = config.validate_configuration()

        # Should not warn about empty whitelist in dev mode
        assert not any("Email whitelist is empty" in w for w in warnings)

    def test_validate_configuration_production_empty_whitelist(self):
        """Test configuration validation with empty whitelist in production."""
        config = AuthConfig(dev_mode=False, email_whitelist=[])
        warnings = config.validate_configuration()

        assert any("Email whitelist is empty in production mode" in w for w in warnings)

    def test_validate_configuration_insecure_cookies(self):
        """Test configuration validation with insecure cookies in production."""
        config = AuthConfig(
            dev_mode=False,
            session_cookie_secure=False,
            email_whitelist=["test@example.com"],
        )
        warnings = config.validate_configuration()

        assert any("Session cookies should be secure in production" in w for w in warnings)

    def test_validate_configuration_public_domains(self):
        """Test configuration validation with public email domains."""
        config = AuthConfig(
            email_whitelist=["test@example.com", "@gmail.com", "@yahoo.com"],
            dev_mode=False,
        )
        warnings = config.validate_configuration()

        assert any("Public email domain @gmail.com in whitelist" in w for w in warnings)
        assert any("Public email domain @yahoo.com in whitelist" in w for w in warnings)

    def test_validate_configuration_secure_production(self):
        """Test configuration validation with secure production config."""
        config = AuthConfig(
            dev_mode=False,
            email_whitelist=["test@company.com", "@company.com"],
            admin_emails=["admin@company.com"],
            session_cookie_secure=True,
        )
        warnings = config.validate_configuration()

        # Should have minimal warnings for secure config
        public_domain_warnings = [w for w in warnings if "Public email domain" in w]
        assert len(public_domain_warnings) == 0


@pytest.mark.unit
class TestConfigLoader:
    """Test ConfigLoader environment variable parsing."""

    def test_env_prefix_default(self):
        """Test default environment prefix."""
        assert ConfigLoader.ENV_PREFIX == "PROMPTCRAFT_"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_from_env_defaults(self):
        """Test loading config with no environment variables."""
        config = ConfigLoader.load_from_env()

        assert config.auth_mode == AuthMode.CLOUDFLARE_SIMPLE
        assert config.enabled is True
        assert config.email_whitelist == []
        assert config.session_timeout == 3600
        assert config.dev_mode is False
        assert config.log_level == LogLevel.INFO

    @patch.dict(
        os.environ,
        {
            "PROMPTCRAFT_AUTH_MODE": "disabled",
            "PROMPTCRAFT_AUTH_ENABLED": "false",
            "PROMPTCRAFT_EMAIL_WHITELIST": "test@example.com,@company.com",
            "PROMPTCRAFT_ADMIN_EMAILS": "admin@example.com",
            "PROMPTCRAFT_FULL_USERS": "full@example.com",
            "PROMPTCRAFT_LIMITED_USERS": "limited@example.com",
            "PROMPTCRAFT_CASE_SENSITIVE_EMAILS": "true",
            "PROMPTCRAFT_SESSION_TIMEOUT": "7200",
            "PROMPTCRAFT_ENABLE_SESSION_COOKIES": "false",
            "PROMPTCRAFT_SESSION_COOKIE_SECURE": "false",
            "PROMPTCRAFT_PUBLIC_PATHS": "/custom,/api/test",
            "PROMPTCRAFT_LOG_LEVEL": "DEBUG",
            "PROMPTCRAFT_LOG_AUTH_EVENTS": "false",
            "PROMPTCRAFT_LOG_FAILED_ATTEMPTS": "false",
            "PROMPTCRAFT_DEV_MODE": "true",
            "PROMPTCRAFT_CF_VALIDATE_HEADERS": "false",
            "PROMPTCRAFT_CF_REQUIRED_HEADERS": "cf-ray,cf-ipcountry",
            "PROMPTCRAFT_CF_LOG_EVENTS": "false",
            "PROMPTCRAFT_CF_TRUST_HEADERS": "false",
        },
    )
    def test_load_from_env_custom_values(self):
        """Test loading config with custom environment values."""
        config = ConfigLoader.load_from_env()

        assert config.auth_mode == AuthMode.DISABLED
        assert config.enabled is False
        assert config.email_whitelist == ["test@example.com", "@company.com"]
        assert config.admin_emails == ["admin@example.com"]
        assert config.full_users == ["full@example.com"]
        assert config.limited_users == ["limited@example.com"]
        assert config.case_sensitive_emails is True
        assert config.session_timeout == 7200
        assert config.enable_session_cookies is False
        assert config.session_cookie_secure is False
        assert config.public_paths == {"/custom", "/api/test"}
        assert config.log_level == LogLevel.DEBUG
        assert config.log_auth_events is False
        assert config.log_failed_attempts is False
        assert config.dev_mode is True
        assert config.cloudflare.validate_headers is False
        assert config.cloudflare.required_headers == ["cf-ray", "cf-ipcountry"]
        assert config.cloudflare.log_events is False
        assert config.cloudflare.trust_cf_headers is False

    @patch.dict(
        os.environ,
        {
            "PROMPTCRAFT_DEV_MODE": "true",
            "PROMPTCRAFT_DEV_USER_EMAIL": "dev@company.com",
            "PROMPTCRAFT_DEV_CF_RAY": "dev-ray-456",
            "PROMPTCRAFT_DEV_IP_COUNTRY": "CA",
        },
    )
    def test_load_from_env_dev_mode_headers(self):
        """Test loading dev mode mock headers."""
        config = ConfigLoader.load_from_env()

        assert config.dev_mode is True
        assert config.mock_cf_headers == {
            "cf-access-authenticated-user-email": "dev@company.com",
            "cf-ray": "dev-ray-456",
            "cf-ipcountry": "CA",
        }

    @patch.dict(os.environ, {"CUSTOM_AUTH_MODE": "disabled"})
    def test_load_from_env_custom_prefix(self):
        """Test loading config with custom prefix."""
        config = ConfigLoader.load_from_env(prefix="CUSTOM_")

        assert config.auth_mode == AuthMode.DISABLED

    def test_get_bool_env_true_values(self):
        """Test _get_bool_env with true values."""
        true_values = ["true", "1", "yes", "on", "True", "YES", "ON"]

        for value in true_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert ConfigLoader._get_bool_env("TEST_BOOL") is True

    def test_get_bool_env_false_values(self):
        """Test _get_bool_env with false values."""
        false_values = ["false", "0", "no", "off", "False", "NO", "OFF"]

        for value in false_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert ConfigLoader._get_bool_env("TEST_BOOL") is False

    def test_get_bool_env_default(self):
        """Test _get_bool_env with default values."""
        with patch.dict(os.environ, {}, clear=True):
            assert ConfigLoader._get_bool_env("MISSING_BOOL", True) is True
            assert ConfigLoader._get_bool_env("MISSING_BOOL", False) is False

        with patch.dict(os.environ, {"INVALID_BOOL": "maybe"}):
            assert ConfigLoader._get_bool_env("INVALID_BOOL", True) is True
            assert ConfigLoader._get_bool_env("INVALID_BOOL", False) is False

    def test_get_int_env_valid(self):
        """Test _get_int_env with valid values."""
        with patch.dict(os.environ, {"TEST_INT": "123"}):
            assert ConfigLoader._get_int_env("TEST_INT", 0) == 123

        with patch.dict(os.environ, {"TEST_INT": "-456"}):
            assert ConfigLoader._get_int_env("TEST_INT", 0) == -456

    def test_get_int_env_invalid(self):
        """Test _get_int_env with invalid values."""
        with patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            assert ConfigLoader._get_int_env("TEST_INT", 42) == 42

        with patch.dict(os.environ, {}, clear=True):
            assert ConfigLoader._get_int_env("MISSING_INT", 999) == 999


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager initialization and methods."""

    def setup_method(self):
        """Reset config manager before each test."""
        reset_config()

    def test_init_with_config(self):
        """Test ConfigManager initialization with provided config."""
        config = AuthConfig(dev_mode=True, log_level=LogLevel.DEBUG)
        manager = ConfigManager(config)

        assert manager.config == config
        assert manager.config.dev_mode is True
        assert manager.config.log_level == LogLevel.DEBUG

    def test_init_without_config(self):
        """Test ConfigManager initialization without config (loads from env)."""
        with patch.object(ConfigLoader, "load_from_env") as mock_load:
            mock_config = AuthConfig(dev_mode=False)
            mock_load.return_value = mock_config

            manager = ConfigManager()

            assert manager.config == mock_config
            mock_load.assert_called_once()

    def test_is_dev_mode(self):
        """Test is_dev_mode method."""
        dev_config = AuthConfig(dev_mode=True)
        prod_config = AuthConfig(dev_mode=False)

        dev_manager = ConfigManager(dev_config)
        prod_manager = ConfigManager(prod_config)

        assert dev_manager.is_dev_mode() is True
        assert prod_manager.is_dev_mode() is False

    def test_get_mock_headers_dev_mode(self):
        """Test get_mock_headers in dev mode."""
        config = AuthConfig(
            dev_mode=True,
            mock_cf_headers={"cf-ray": "test-123", "cf-access-authenticated-user-email": "test@example.com"},
        )
        manager = ConfigManager(config)

        headers = manager.get_mock_headers()
        assert headers == {"cf-ray": "test-123", "cf-access-authenticated-user-email": "test@example.com"}

    def test_get_mock_headers_production(self):
        """Test get_mock_headers in production mode."""
        config = AuthConfig(dev_mode=False, mock_cf_headers={"cf-ray": "test-123"})
        manager = ConfigManager(config)

        headers = manager.get_mock_headers()
        assert headers == {}

    def test_create_whitelist_validator(self):
        """Test create_whitelist_validator method."""
        config = AuthConfig(
            email_whitelist=["test@example.com", "@company.com"],
            admin_emails=["admin@company.com"],
            full_users=["full@company.com"],
            limited_users=["limited@company.com"],
            case_sensitive_emails=True,
        )
        manager = ConfigManager(config)

        validator = manager.create_whitelist_validator()

        # Test that validator is created with correct parameters
        assert validator.individual_emails == {"test@example.com"}
        assert validator.domain_patterns == {"@company.com"}
        assert validator.admin_emails == ["admin@company.com"]
        assert validator.full_users == ["full@company.com"]
        assert validator.limited_users == ["limited@company.com"]
        assert validator.case_sensitive is True

    def test_create_middleware(self):
        """Test create_middleware method."""
        config = AuthConfig(
            session_timeout=7200,
            public_paths={"/api/health", "/docs"},
            enable_session_cookies=False,
        )
        manager = ConfigManager(config)

        middleware = manager.create_middleware()

        # Test middleware is created with correct configuration
        assert middleware.session_manager.session_timeout == 7200
        assert middleware.public_paths == {"/api/health", "/docs"}
        assert middleware.enable_session_cookies is False

    def test_get_config_summary(self):
        """Test get_config_summary method."""
        config = AuthConfig(
            auth_mode=AuthMode.CLOUDFLARE_SIMPLE,
            enabled=True,
            email_whitelist=["test@example.com", "@company.com"],
            admin_emails=["admin@company.com"],
            session_timeout=3600,
            public_paths={"/health", "/docs", "/api/test"},
            dev_mode=False,
            log_level=LogLevel.INFO,
        )
        manager = ConfigManager(config)

        summary = manager.get_config_summary()

        expected_summary = {
            "auth_mode": "cloudflare_simple",
            "enabled": True,
            "whitelist_count": 2,
            "admin_count": 1,
            "session_timeout": 3600,
            "public_paths_count": 3,
            "dev_mode": False,
            "log_level": "INFO",
        }

        assert summary == expected_summary


@pytest.mark.unit
class TestGlobalConfigFunctions:
    """Test global configuration functions."""

    def setup_method(self):
        """Reset config manager before each test."""
        reset_config()

    def test_get_config_manager_singleton(self):
        """Test get_config_manager returns singleton instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2

    def test_get_auth_config(self):
        """Test get_auth_config function."""
        config = get_auth_config()

        assert isinstance(config, AuthConfig)
        assert config.auth_mode in [AuthMode.CLOUDFLARE_SIMPLE, AuthMode.DISABLED]

    def test_reset_config(self):
        """Test reset_config function."""
        # Get initial manager
        manager1 = get_config_manager()

        # Reset config
        reset_config()

        # Get new manager
        manager2 = get_config_manager()

        # Should be different instances
        assert manager1 is not manager2


@pytest.mark.unit
class TestConfigLoaderErrors:
    """Test ConfigLoader error handling."""

    def test_load_from_env_invalid_config(self):
        """Test loading config with invalid values that cause validation errors."""
        with patch.dict(
            os.environ,
            {
                "PROMPTCRAFT_SESSION_TIMEOUT": "30",  # Too low, should fail validation
            },
        ):
            with pytest.raises(Exception):  # Should raise validation error
                ConfigLoader.load_from_env()

    @patch("src.auth_simple.config.logger")
    def test_load_from_env_logs_success(self, mock_logger):
        """Test that successful config loading is logged."""
        config = ConfigLoader.load_from_env()

        mock_logger.info.assert_called_with(
            "Loaded authentication configuration with mode: %s",
            config.auth_mode,
        )

    @patch("src.auth_simple.config.AuthConfig")
    @patch("src.auth_simple.config.logger")
    def test_load_from_env_logs_error(self, mock_logger, mock_auth_config):
        """Test that config loading errors are logged."""
        mock_auth_config.side_effect = ValueError("Invalid config")

        with pytest.raises(ValueError):
            ConfigLoader.load_from_env()

        mock_logger.error.assert_called_with(
            "Failed to load authentication configuration: %s",
            mock_auth_config.side_effect,
        )


@pytest.mark.unit
class TestConfigManagerValidation:
    """Test ConfigManager validation and logging."""

    def setup_method(self):
        """Reset config manager before each test."""
        reset_config()

    @patch("src.auth_simple.config.logger")
    def test_config_validation_warnings(self, mock_logger):
        """Test that configuration warnings are logged."""
        config = AuthConfig(
            dev_mode=False,
            email_whitelist=[],  # Empty whitelist in production
            session_cookie_secure=False,  # Insecure cookies
        )

        ConfigManager(config)

        # Check that warnings were logged
        warning_calls = [call for call in mock_logger.warning.call_args_list if "Configuration warning" in str(call)]
        assert len(warning_calls) >= 2  # At least empty whitelist and insecure cookies warnings

    @patch("logging.getLogger")
    def test_setup_logging(self, mock_get_logger):
        """Test that logging is set up correctly."""
        config = AuthConfig(log_level=LogLevel.DEBUG)
        mock_auth_logger = mock_get_logger.return_value

        ConfigManager(config)

        mock_get_logger.assert_called_with("src.auth_simple")
        mock_auth_logger.setLevel.assert_called_with("DEBUG")
