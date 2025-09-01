"""Test fixtures for AUTH-4 dependency injection container testing.

This module provides fixtures for testing the service container and dependency
injection system, including mock service implementations and container setup.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
from src.auth.services.alert_engine import AlertEngine
from src.auth.services.audit_service import AuditService
from src.auth.services.bootstrap import (
    create_test_container,
    get_container_for_environment,
    initialize_container_async,
)
from src.auth.services.container import ServiceContainer, ServiceContainerConfiguration, reset_container
from src.auth.services.security_logger import SecurityLogger
from src.auth.services.security_monitor import SecurityMonitor
from src.auth.services.suspicious_activity_detector import SuspiciousActivityDetector
from tests.fixtures.security_service_mocks import (
    MockAlertEngine,
    MockAuditService,
    MockSecurityLogger,
    MockSecurityMonitor,
    MockSuspiciousActivityDetector,
)


@pytest.fixture
def clean_container():
    """Ensure a clean service container state for each test."""
    # Reset global container before test
    reset_container()
    yield
    # Reset global container after test
    reset_container()


@pytest.fixture
def container_config():
    """Provide test-optimized container configuration."""
    return ServiceContainerConfiguration(
        environment="test",
        enable_health_checks=False,  # Disable for faster tests
        log_service_resolutions=False,  # Reduce test noise
        max_initialization_retries=1,  # Fail fast in tests
        initialization_timeout_seconds=1.0,  # Quick timeout for tests
        enable_circular_dependency_detection=True,  # Enable for test safety
    )


@pytest.fixture
def empty_container(clean_container, container_config):
    """Provide an empty service container for testing."""
    return ServiceContainer(container_config)


@pytest.fixture
def mock_service_container(clean_container, container_config):
    """Provide a service container with mock services registered."""
    container = ServiceContainer(container_config)

    # Register mock services for testing
    container.register_singleton(
        SecurityLogger,
        MockSecurityLogger,
        configuration={},
    )

    container.register_singleton(
        AlertEngine,
        MockAlertEngine,
        dependencies=[SecurityLogger],  # AlertEngine depends on SecurityLogger
        configuration={},
    )

    container.register_singleton(
        SecurityMonitor,
        MockSecurityMonitor,
        dependencies=[SecurityLogger, AlertEngine],
        configuration={},
    )

    container.register_singleton(
        SuspiciousActivityDetector,
        MockSuspiciousActivityDetector,
        dependencies=[SecurityLogger, AlertEngine],
        configuration={},
    )

    container.register_singleton(
        AuditService,
        MockAuditService,
        dependencies=[SecurityLogger],
        configuration={},
    )

    return container


@pytest.fixture
async def initialized_mock_container(mock_service_container):
    """Provide a fully initialized service container with mock services."""
    results = await initialize_container_async(mock_service_container)

    # Verify all services initialized successfully
    for service_type, success in results.items():
        assert success, f"Failed to initialize {service_type.__name__}"

    return mock_service_container


@pytest.fixture
def test_environment_container(clean_container):
    """Provide a test-environment container using the bootstrap system."""
    return create_test_container()


@pytest.fixture
async def initialized_test_container(test_environment_container):
    """Provide a fully initialized test environment container."""
    results = await initialize_container_async(test_environment_container)

    # Check that critical services initialized
    critical_services = [SecurityLogger, AlertEngine]
    for service_type in critical_services:
        if service_type in results:
            assert results[service_type], f"Critical service {service_type.__name__} failed to initialize"

    return test_environment_container


class MockServiceFactory:
    """Factory for creating mock services with proper dependency injection."""

    @staticmethod
    def create_mock_database() -> MagicMock:
        """Create a mock database with async methods."""
        mock_db = MagicMock(spec=SecurityEventsPostgreSQL)
        mock_db.initialize = AsyncMock()
        mock_db.close = AsyncMock()
        mock_db.log_security_event = AsyncMock()
        mock_db.get_events_by_user = AsyncMock(return_value=[])
        mock_db.get_events_by_date_range = AsyncMock(return_value=[])
        return mock_db

    @staticmethod
    def create_mock_logger(**kwargs) -> MockSecurityLogger:
        """Create a mock security logger with specified configuration."""
        return MockSecurityLogger(**kwargs)

    @staticmethod
    def create_mock_monitor(**kwargs) -> MockSecurityMonitor:
        """Create a mock security monitor with specified dependencies."""
        return MockSecurityMonitor(**kwargs)

    @staticmethod
    def create_mock_alert_engine(**kwargs) -> MockAlertEngine:
        """Create a mock alert engine with specified dependencies."""
        return MockAlertEngine(**kwargs)

    @staticmethod
    def create_mock_detector(**kwargs) -> MockSuspiciousActivityDetector:
        """Create a mock suspicious activity detector with specified dependencies."""
        return MockSuspiciousActivityDetector(**kwargs)

    @staticmethod
    def create_mock_audit_service(**kwargs) -> MockAuditService:
        """Create a mock audit service with specified dependencies."""
        return MockAuditService(**kwargs)


@pytest.fixture
def mock_service_factory():
    """Provide the mock service factory for test use."""
    return MockServiceFactory()


@pytest.fixture
def service_dependency_chain(mock_service_factory):
    """Provide a complete chain of mock services with proper dependencies."""
    # Create services in dependency order
    mock_db = mock_service_factory.create_mock_database()
    mock_logger = mock_service_factory.create_mock_logger()
    mock_alert_engine = mock_service_factory.create_mock_alert_engine()
    mock_monitor = mock_service_factory.create_mock_monitor(
        security_logger=mock_logger,
        alert_engine=mock_alert_engine,
    )
    mock_detector = mock_service_factory.create_mock_detector(
        security_logger=mock_logger,
        alert_engine=mock_alert_engine,
    )
    mock_audit = mock_service_factory.create_mock_audit_service()

    return {
        "database": mock_db,
        "logger": mock_logger,
        "alert_engine": mock_alert_engine,
        "monitor": mock_monitor,
        "detector": mock_detector,
        "audit": mock_audit,
    }


@pytest.fixture
def custom_container_with_mocks(clean_container, container_config, service_dependency_chain):
    """Provide a container with custom mock service instances."""
    container = ServiceContainer(container_config)

    # Register the pre-created mock instances
    container.register_singleton(SecurityEventsPostgreSQL, service_dependency_chain["database"])
    container.register_singleton(SecurityLogger, service_dependency_chain["logger"])
    container.register_singleton(AlertEngine, service_dependency_chain["alert_engine"])
    container.register_singleton(SecurityMonitor, service_dependency_chain["monitor"])
    container.register_singleton(SuspiciousActivityDetector, service_dependency_chain["detector"])
    container.register_singleton(AuditService, service_dependency_chain["audit"])

    return container


class ContainerTestHelper:
    """Helper class for container testing operations."""

    @staticmethod
    def verify_service_registration(container: ServiceContainer, service_type: type[Any]) -> bool:
        """Verify that a service is properly registered."""
        return service_type in container._registrations

    @staticmethod
    def verify_service_resolution(container: ServiceContainer, service_type: type[Any]) -> bool:
        """Verify that a service can be resolved."""
        try:
            service = container.resolve(service_type)
            return service is not None
        except Exception:
            return False

    @staticmethod
    def verify_dependency_chain(container: ServiceContainer, service_type: type[Any]) -> bool:
        """Verify that a service's dependencies can be resolved."""
        try:
            registration = container._registrations.get(service_type)
            if not registration:
                return False

            # Try to resolve all dependencies
            for dependency_type in registration.dependencies:
                dependency = container.resolve(dependency_type)
                if dependency is None:
                    return False

            return True
        except Exception:
            return False

    @staticmethod
    async def verify_service_initialization(container: ServiceContainer, service_type: type[Any]) -> bool:
        """Verify that a service initializes correctly."""
        try:
            service = container.resolve(service_type)
            if hasattr(service, "initialize") and callable(service.initialize):
                if asyncio.iscoroutinefunction(service.initialize):
                    await service.initialize()
                else:
                    service.initialize()
            return True
        except Exception:
            return False


@pytest.fixture
def container_test_helper():
    """Provide the container test helper."""
    return ContainerTestHelper()


# Container lifecycle fixtures
@pytest.fixture
async def container_lifecycle_context():
    """Provide a context for managing container lifecycle in tests."""
    containers = []

    def create_container(config: ServiceContainerConfiguration | None = None):
        container = ServiceContainer(config or ServiceContainerConfiguration(environment="test"))
        containers.append(container)
        return container

    yield create_container

    # Cleanup all created containers
    for container in containers:
        with contextlib.suppress(Exception):
            await container.shutdown()


# Performance testing fixtures
@pytest.fixture
def performance_container(clean_container):
    """Provide a container configured for performance testing."""
    config = ServiceContainerConfiguration(
        environment="test",
        enable_health_checks=True,
        log_service_resolutions=True,  # Enable for performance measurement
        max_initialization_retries=1,
        initialization_timeout_seconds=0.1,  # Very fast timeout for perf tests
    )
    return ServiceContainer(config)


# Integration test fixtures
@pytest.fixture
async def integration_test_container(clean_container):
    """Provide a container for integration testing with real service implementations."""
    # Create container using test environment settings but with real services
    container = get_container_for_environment("test")

    # Initialize services
    try:
        await initialize_container_async(container)
    except Exception as e:
        pytest.skip(f"Integration test skipped - service initialization failed: {e}")

    return container


# Error simulation fixtures
class ErrorSimulatingContainer(ServiceContainer):
    """Service container that can simulate various error conditions."""

    def __init__(self, config, error_on_resolve=None, error_on_initialize=None):
        super().__init__(config)
        self.error_on_resolve = error_on_resolve or []
        self.error_on_initialize = error_on_initialize or []

    def resolve(self, service_type):
        if service_type in self.error_on_resolve:
            raise Exception(f"Simulated resolution error for {service_type.__name__}")
        return super().resolve(service_type)

    async def initialize_services(self, service_types=None):
        if self.error_on_initialize:
            # Simulate initialization failure
            results = {}
            for service_type in service_types or self._registrations.keys():
                if service_type in self.error_on_initialize:
                    results[service_type] = False
                else:
                    results[service_type] = True
            return results

        return await super().initialize_services(service_types)


@pytest.fixture
def error_simulating_container_factory(clean_container, container_config):
    """Provide a factory for creating containers that simulate errors."""

    def create_error_container(error_on_resolve=None, error_on_initialize=None):
        return ErrorSimulatingContainer(
            container_config,
            error_on_resolve=error_on_resolve,
            error_on_initialize=error_on_initialize,
        )

    return create_error_container


# Scoped service testing (for future enhancement)
@pytest.fixture
def request_scoped_container(clean_container, container_config):
    """Provide a container for testing request-scoped services (future feature)."""
    # This fixture prepares for future request-scoped service support
    container = ServiceContainer(container_config)

    # Add request context simulation capability
    container._request_context = {}

    return container


# Configuration validation fixtures
@pytest.fixture
def invalid_container_configs():
    """Provide various invalid container configurations for testing."""
    return {
        "negative_timeout": ServiceContainerConfiguration(initialization_timeout_seconds=-1.0),
        "zero_retries": ServiceContainerConfiguration(max_initialization_retries=0),
        "invalid_environment": ServiceContainerConfiguration(environment=""),
    }


@pytest.fixture
def container_metrics_validator():
    """Provide a validator for container metrics."""

    def validate_metrics(metrics: dict[str, Any]) -> bool:
        required_keys = ["services", "performance", "health", "configuration"]
        return all(key in metrics for key in required_keys)

    return validate_metrics
