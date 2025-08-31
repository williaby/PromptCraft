"""
Unit tests for AUTH-4 service bootstrap configuration.

Tests the service registration, configuration, and dependency injection
bootstrap functionality for the AUTH-4 Enhanced Security Event Logging system.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.auth.services.bootstrap import (
    ServiceBootstrapError,
    bootstrap_services_async,
    create_alert_engine_production,
    create_development_container,
    create_production_container,
    create_security_monitor_dev,
    create_security_monitor_production,
    create_security_monitor_test,
    create_suspicious_activity_detector_dev,
    create_suspicious_activity_detector_production,
    create_suspicious_activity_detector_test,
    create_test_container,
    get_container_for_environment,
    initialize_container_async,
    validate_container_configuration,
)
from src.auth.services.container import ServiceContainer, ServiceContainerConfiguration


@pytest.fixture
def mock_container():
    """Create mock service container for testing."""
    container = Mock(spec=ServiceContainer)
    container._registrations = {}
    container.register_singleton = Mock()
    container.initialize_services = AsyncMock(return_value={})
    container.config = Mock(spec=ServiceContainerConfiguration)
    container.config.enable_circular_dependency_detection = True
    container._detect_circular_dependencies = Mock()
    return container


@pytest.fixture
def mock_database():
    """Create mock database service."""
    db_mock = Mock()
    db_mock._initialized = True
    return db_mock


@pytest.fixture
def mock_security_logger():
    """Create mock security logger service."""
    logger_mock = Mock()
    logger_mock._batch_processor_task = Mock()
    logger_mock._batch_processor_task.done.return_value = False
    return logger_mock


@pytest.fixture
def mock_alert_engine():
    """Create mock alert engine service."""
    engine_mock = Mock()
    engine_mock._processor_task = Mock()
    engine_mock._processor_task.done.return_value = False
    return engine_mock


class TestServiceContainerCreation:
    """Test service container creation for different environments."""

    @patch("src.auth.services.bootstrap.ServiceContainer")
    def test_create_development_container_success(self, mock_service_container):
        """Test successful creation of development container."""
        mock_instance = Mock()
        mock_service_container.return_value = mock_instance
        mock_instance.register_singleton = Mock()

        result = create_development_container()

        assert result is mock_instance
        mock_service_container.assert_called_once()
        # Verify that services were registered
        assert mock_instance.register_singleton.call_count >= 5

    @patch("src.auth.services.bootstrap.ServiceContainer")
    def test_create_test_container_success(self, mock_service_container):
        """Test successful creation of test container."""
        mock_instance = Mock()
        mock_service_container.return_value = mock_instance
        mock_instance.register_singleton = Mock()

        result = create_test_container()

        assert result is mock_instance
        mock_service_container.assert_called_once()
        # Verify that services were registered
        assert mock_instance.register_singleton.call_count >= 5

    @patch("src.auth.services.bootstrap.ServiceContainer")
    def test_create_production_container_success(self, mock_service_container):
        """Test successful creation of production container."""
        mock_instance = Mock()
        mock_service_container.return_value = mock_instance
        mock_instance.register_singleton = Mock()

        result = create_production_container()

        assert result is mock_instance
        mock_service_container.assert_called_once()
        # Verify that services were registered
        assert mock_instance.register_singleton.call_count >= 5


class TestEnvironmentSelection:
    """Test environment-specific container selection."""

    def test_get_container_for_environment_development(self):
        """Test getting container for development environment."""
        with patch("src.auth.services.bootstrap.create_development_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("development")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_get_container_for_environment_dev_alias(self):
        """Test getting container for dev alias."""
        with patch("src.auth.services.bootstrap.create_development_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("dev")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_get_container_for_environment_test(self):
        """Test getting container for test environment."""
        with patch("src.auth.services.bootstrap.create_test_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("test")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_get_container_for_environment_testing_alias(self):
        """Test getting container for testing alias."""
        with patch("src.auth.services.bootstrap.create_test_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("testing")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_get_container_for_environment_production(self):
        """Test getting container for production environment."""
        with patch("src.auth.services.bootstrap.create_production_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("production")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_get_container_for_environment_prod_alias(self):
        """Test getting container for prod alias."""
        with patch("src.auth.services.bootstrap.create_production_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("prod")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_get_container_for_environment_invalid(self):
        """Test error handling for invalid environment."""
        with pytest.raises(ServiceBootstrapError, match="Unsupported environment"):
            get_container_for_environment("invalid_env")

    def test_get_container_for_environment_case_insensitive(self):
        """Test that environment selection is case insensitive."""
        with patch("src.auth.services.bootstrap.create_development_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            result = get_container_for_environment("DEVELOPMENT")

            assert result is mock_container
            mock_create.assert_called_once()


class TestContainerInitialization:
    """Test service container initialization functions."""

    @pytest.mark.asyncio
    async def test_initialize_container_async_success(self, mock_container):
        """Test successful container initialization."""
        from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
        from src.auth.services.alert_engine import AlertEngine
        from src.auth.services.security_logger import SecurityLogger

        # Mock successful initialization results
        mock_container._registrations = {
            SecurityEventsPostgreSQL: Mock(),
            SecurityLogger: Mock(),
            AlertEngine: Mock(),
        }
        mock_container.initialize_services.return_value = {
            SecurityEventsPostgreSQL: True,
            SecurityLogger: True,
            AlertEngine: True,
        }

        result = await initialize_container_async(mock_container)

        assert result == {
            SecurityEventsPostgreSQL: True,
            SecurityLogger: True,
            AlertEngine: True,
        }
        mock_container.initialize_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_container_async_critical_service_failure(self, mock_container):
        """Test handling of critical service initialization failure."""
        from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
        from src.auth.services.security_logger import SecurityLogger

        # Mock critical service failure
        mock_container._registrations = {
            SecurityEventsPostgreSQL: Mock(),
            SecurityLogger: Mock(),
        }
        mock_container.initialize_services.return_value = {
            SecurityEventsPostgreSQL: False,  # Critical service failed
            SecurityLogger: True,
        }

        with pytest.raises(ServiceBootstrapError, match="Critical services failed to initialize"):
            await initialize_container_async(mock_container)

    @pytest.mark.asyncio
    async def test_initialize_container_async_exception_handling(self, mock_container):
        """Test exception handling during initialization."""
        mock_container._registrations = {}
        mock_container.initialize_services.side_effect = Exception("Initialization error")

        with pytest.raises(ServiceBootstrapError, match="Container initialization failed"):
            await initialize_container_async(mock_container)


class TestBootstrapServicesAsync:
    """Test the main bootstrap services async function."""

    @pytest.mark.asyncio
    async def test_bootstrap_services_async_development_success(self):
        """Test successful bootstrap for development environment."""
        mock_container = Mock()

        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get, \
             patch("src.auth.services.bootstrap.initialize_container_async") as mock_init:
            mock_get.return_value = mock_container
            mock_init.return_value = {}

            result = await bootstrap_services_async("development")

            assert result is mock_container
            mock_get.assert_called_once_with("development")
            mock_init.assert_called_once_with(mock_container)

    @pytest.mark.asyncio
    async def test_bootstrap_services_async_test_success(self):
        """Test successful bootstrap for test environment."""
        mock_container = Mock()

        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get, \
             patch("src.auth.services.bootstrap.initialize_container_async") as mock_init:
            mock_get.return_value = mock_container
            mock_init.return_value = {}

            result = await bootstrap_services_async("test")

            assert result is mock_container
            mock_get.assert_called_once_with("test")
            mock_init.assert_called_once_with(mock_container)

    @pytest.mark.asyncio
    async def test_bootstrap_services_async_production_success(self):
        """Test successful bootstrap for production environment."""
        mock_container = Mock()

        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get, \
             patch("src.auth.services.bootstrap.initialize_container_async") as mock_init:
            mock_get.return_value = mock_container
            mock_init.return_value = {}

            result = await bootstrap_services_async("production")

            assert result is mock_container
            mock_get.assert_called_once_with("production")
            mock_init.assert_called_once_with(mock_container)

    @pytest.mark.asyncio
    async def test_bootstrap_services_async_container_creation_failure(self):
        """Test bootstrap failure during container creation."""
        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get:
            mock_get.side_effect = ServiceBootstrapError("Container creation failed")

            with pytest.raises(ServiceBootstrapError, match="Bootstrap failed"):
                await bootstrap_services_async("development")

    @pytest.mark.asyncio
    async def test_bootstrap_services_async_initialization_failure(self):
        """Test bootstrap failure during service initialization."""
        mock_container = Mock()

        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get, \
             patch("src.auth.services.bootstrap.initialize_container_async") as mock_init:
            mock_get.return_value = mock_container
            mock_init.side_effect = ServiceBootstrapError("Initialization failed")

            with pytest.raises(ServiceBootstrapError, match="Bootstrap failed"):
                await bootstrap_services_async("development")


class TestContainerValidation:
    """Test service container validation functions."""

    def test_validate_container_configuration_success(self, mock_container):
        """Test successful container configuration validation."""
        from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
        from src.auth.services.alert_engine import AlertEngine
        from src.auth.services.audit_service import AuditService
        from src.auth.services.security_logger import SecurityLogger
        from src.auth.services.security_monitor import SecurityMonitor
        from src.auth.services.suspicious_activity_detector import SuspiciousActivityDetector

        # Mock all critical services are registered
        mock_container._registrations = {
            SecurityEventsPostgreSQL: Mock(dependencies=[]),
            SecurityLogger: Mock(dependencies=[]),
            AlertEngine: Mock(dependencies=[SecurityEventsPostgreSQL, SecurityLogger]),
            SecurityMonitor: Mock(dependencies=[SecurityEventsPostgreSQL, SecurityLogger, AlertEngine]),
            SuspiciousActivityDetector: Mock(dependencies=[SecurityEventsPostgreSQL, SecurityLogger]),
            AuditService: Mock(dependencies=[SecurityEventsPostgreSQL, SecurityLogger]),
        }

        issues = validate_container_configuration(mock_container)

        assert issues == []

    def test_validate_container_configuration_missing_critical_service(self, mock_container):
        """Test validation with missing critical service."""
        from src.auth.services.security_logger import SecurityLogger

        # Mock missing critical service
        mock_container._registrations = {
            SecurityLogger: Mock(dependencies=[]),
        }

        issues = validate_container_configuration(mock_container)

        assert len(issues) > 0
        assert any("Critical service not registered" in issue for issue in issues)

    def test_validate_container_configuration_missing_dependency(self, mock_container):
        """Test validation with missing dependency."""
        from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
        from src.auth.services.alert_engine import AlertEngine
        from src.auth.services.security_logger import SecurityLogger

        # Create a fake service class that's unregistered
        class UnregisteredService:
            pass

        # Mock service with missing dependency
        mock_container._registrations = {
            SecurityEventsPostgreSQL: Mock(dependencies=[]),
            SecurityLogger: Mock(dependencies=[]),
            AlertEngine: Mock(dependencies=[SecurityEventsPostgreSQL, SecurityLogger, UnregisteredService]),  # UnregisteredService is unregistered
        }

        issues = validate_container_configuration(mock_container)

        assert len(issues) > 0
        assert any("depends on unregistered service" in issue for issue in issues)

    def test_validate_container_configuration_circular_dependency(self, mock_container):
        """Test validation with circular dependency detection."""
        from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
        from src.auth.services.security_logger import SecurityLogger

        # Mock circular dependency detection
        mock_container._registrations = {
            SecurityEventsPostgreSQL: Mock(dependencies=[]),
            SecurityLogger: Mock(dependencies=[]),
        }
        mock_container._detect_circular_dependencies.side_effect = Exception("Circular dependency detected")

        issues = validate_container_configuration(mock_container)

        assert len(issues) > 0
        assert any("Circular dependency detected" in issue for issue in issues)

    def test_validate_container_configuration_exception_handling(self, mock_container):
        """Test validation with general exception."""
        mock_container._registrations = {}
        # Mock exception during validation
        mock_container.config = None  # This will cause an AttributeError

        issues = validate_container_configuration(mock_container)

        assert len(issues) > 0
        assert any("Validation error" in issue for issue in issues)


class TestFactoryFunctions:
    """Test service factory functions."""

    def test_create_security_monitor_dev(self, mock_database, mock_security_logger, mock_alert_engine):
        """Test development SecurityMonitor factory."""
        result = create_security_monitor_dev(mock_database, mock_security_logger, mock_alert_engine)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.failed_attempts_threshold == 3  # Development setting
        assert result.config.account_lockout_duration_minutes == 15  # Shorter for development

    def test_create_security_monitor_test(self, mock_database, mock_security_logger, mock_alert_engine):
        """Test test SecurityMonitor factory."""
        result = create_security_monitor_test(mock_database, mock_security_logger, mock_alert_engine)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.failed_attempts_threshold == 2  # Very low for tests
        assert result.config.account_lockout_enabled is False  # Disabled for tests

    def test_create_security_monitor_production(self, mock_database, mock_security_logger, mock_alert_engine):
        """Test production SecurityMonitor factory."""
        result = create_security_monitor_production(mock_database, mock_security_logger, mock_alert_engine)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.failed_attempts_threshold == 10  # Production threshold
        assert result.config.account_lockout_duration_minutes == 30  # Production setting

    def test_create_suspicious_activity_detector_dev(self, mock_database, mock_security_logger):
        """Test development SuspiciousActivityDetector factory."""
        result = create_suspicious_activity_detector_dev(mock_database, mock_security_logger)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.risk_threshold_suspicious == 30  # Lower for development
        assert result.config.historical_window_days == 7  # Shorter window

    def test_create_suspicious_activity_detector_test(self, mock_database, mock_security_logger):
        """Test test SuspiciousActivityDetector factory."""
        result = create_suspicious_activity_detector_test(mock_database, mock_security_logger)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.risk_threshold_suspicious == 20  # Very low for tests
        assert result.config.enable_geolocation_check is False  # Disabled for tests

    def test_create_suspicious_activity_detector_production(self, mock_database, mock_security_logger):
        """Test production SuspiciousActivityDetector factory."""
        result = create_suspicious_activity_detector_production(mock_database, mock_security_logger)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.risk_threshold_suspicious == 40  # Production threshold
        assert result.config.enable_geolocation_check is True  # Enabled for production
        assert result.config.max_distance_km == 1000.0  # Production setting

    def test_create_alert_engine_production(self, mock_database, mock_security_logger):
        """Test production AlertEngine factory."""
        result = create_alert_engine_production(mock_database, mock_security_logger)

        assert result is not None
        assert hasattr(result, "config")
        assert result.config.processing_batch_size == 20  # Production batch size
        assert result.config.alert_retention_days == 90  # Production retention


class TestBootstrapIntegration:
    """Test bootstrap integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_bootstrap_cycle_development(self):
        """Test complete bootstrap cycle for development environment."""
        with patch("src.auth.services.bootstrap.create_development_container") as mock_create, \
             patch("src.auth.services.bootstrap.initialize_container_async") as mock_init:

            mock_container = Mock()
            mock_create.return_value = mock_container
            mock_init.return_value = {}

            result = await bootstrap_services_async("development")

            assert result is mock_container
            mock_create.assert_called_once()
            mock_init.assert_called_once_with(mock_container)

    def test_environment_specific_configurations(self):
        """Test that different environments get different configurations."""
        # Test that development container is different from production
        with patch("src.auth.services.bootstrap.ServiceContainer") as mock_service_container:
            mock_dev_container = Mock()
            mock_prod_container = Mock()
            mock_service_container.side_effect = [mock_dev_container, mock_prod_container]

            create_development_container()
            create_production_container()

            # Verify different configurations were applied
            assert mock_service_container.call_count == 2

            # Check that different configurations were used
            dev_call_config = mock_service_container.call_args_list[0][0][0]
            prod_call_config = mock_service_container.call_args_list[1][0][0]

            assert dev_call_config.environment == "development"
            assert prod_call_config.environment == "production"
            assert dev_call_config.health_check_interval_seconds == 30  # Dev setting
            assert prod_call_config.health_check_interval_seconds == 60  # Prod setting


class TestErrorHandling:
    """Test comprehensive error handling in bootstrap process."""

    def test_service_bootstrap_error_creation(self):
        """Test ServiceBootstrapError exception creation."""
        error_msg = "Test bootstrap error"
        error = ServiceBootstrapError(error_msg)

        assert str(error) == error_msg
        assert isinstance(error, Exception)

    @pytest.mark.asyncio
    async def test_bootstrap_with_container_creation_failure(self):
        """Test bootstrap behavior when container creation fails."""
        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get:
            mock_get.side_effect = ServiceBootstrapError("Container creation failed")

            with pytest.raises(ServiceBootstrapError, match="Bootstrap failed"):
                await bootstrap_services_async("development")

    @pytest.mark.asyncio
    async def test_bootstrap_with_initialization_failure(self):
        """Test bootstrap behavior when service initialization fails."""
        mock_container = Mock()

        with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get, \
             patch("src.auth.services.bootstrap.initialize_container_async") as mock_init:
            mock_get.return_value = mock_container
            mock_init.side_effect = ServiceBootstrapError("Service initialization failed")

            with pytest.raises(ServiceBootstrapError, match="Bootstrap failed"):
                await bootstrap_services_async("development")

    def test_environment_validation_with_whitespace(self):
        """Test that environment validation handles whitespace correctly."""
        with patch("src.auth.services.bootstrap.create_development_container") as mock_create:
            mock_container = Mock()
            mock_create.return_value = mock_container

            # Test with leading/trailing whitespace
            result = get_container_for_environment("  development  ")

            assert result is mock_container
            mock_create.assert_called_once()

    def test_environment_validation_with_empty_string(self):
        """Test environment validation with empty string."""
        with pytest.raises(ServiceBootstrapError, match="Unsupported environment"):
            get_container_for_environment("")

    def test_environment_validation_with_none(self):
        """Test environment validation with None."""
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'lower'"):
            get_container_for_environment(None)


class TestBootstrapRealExecution:
    """Test bootstrap functions with some real execution to improve coverage."""

    def test_service_bootstrap_error_real_instantiation(self):
        """Test ServiceBootstrapError can be instantiated and used."""
        error = ServiceBootstrapError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_get_container_for_environment_with_real_factory_call(self):
        """Test get_container_for_environment actually calls factory functions."""
        with patch("src.auth.services.bootstrap.create_development_container") as mock_create_dev:
            mock_create_dev.return_value = Mock()

            # Actually call the function - this should execute the real logic
            result = get_container_for_environment("development")

            # Verify the factory was called
            mock_create_dev.assert_called_once()
            assert result is mock_create_dev.return_value

    def test_bootstrap_services_async_real_logic_path(self):
        """Test bootstrap_services_async executes real logic paths."""
        import asyncio

        async def run_test():
            with patch("src.auth.services.bootstrap.get_container_for_environment") as mock_get_container:
                with patch("src.auth.services.bootstrap.initialize_container_async") as mock_initialize:
                    mock_container = Mock()
                    mock_get_container.return_value = mock_container
                    mock_initialize.return_value = None

                    # Actually call the async function
                    result = await bootstrap_services_async("test")

                    # Verify the real function calls were made
                    mock_get_container.assert_called_once_with("test")
                    mock_initialize.assert_called_once_with(mock_container)
                    assert result is mock_container

        asyncio.run(run_test())


class TestContainerConfiguration:
    """Test detailed container configuration validation."""

    def test_development_container_configuration(self):
        """Test development container has correct configuration."""
        with patch("src.auth.services.bootstrap.ServiceContainer") as mock_service_container:
            mock_container = Mock()
            mock_service_container.return_value = mock_container

            create_development_container()

            # Check configuration passed to ServiceContainer
            call_args = mock_service_container.call_args[0][0]
            assert call_args.environment == "development"
            assert call_args.enable_health_checks is True
            assert call_args.health_check_interval_seconds == 30
            assert call_args.log_service_resolutions is True

    def test_test_container_configuration(self):
        """Test test container has correct configuration."""
        with patch("src.auth.services.bootstrap.ServiceContainer") as mock_service_container:
            mock_container = Mock()
            mock_service_container.return_value = mock_container

            create_test_container()

            # Check configuration passed to ServiceContainer
            call_args = mock_service_container.call_args[0][0]
            assert call_args.environment == "test"
            assert call_args.enable_health_checks is False
            assert call_args.log_service_resolutions is False
            assert call_args.max_initialization_retries == 1
            assert call_args.initialization_timeout_seconds == 5.0

    def test_production_container_configuration(self):
        """Test production container has correct configuration."""
        with patch("src.auth.services.bootstrap.ServiceContainer") as mock_service_container:
            mock_container = Mock()
            mock_service_container.return_value = mock_container

            create_production_container()

            # Check configuration passed to ServiceContainer
            call_args = mock_service_container.call_args[0][0]
            assert call_args.environment == "production"
            assert call_args.enable_health_checks is True
            assert call_args.health_check_interval_seconds == 60
            assert call_args.log_service_resolutions is False
            assert call_args.max_initialization_retries == 3
            assert call_args.initialization_timeout_seconds == 30.0
