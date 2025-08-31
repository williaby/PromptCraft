"""
Comprehensive unit tests for auth services container module.

This test suite covers all classes and functions in src/auth/services/container.py
with extensive mocking and edge case testing to achieve >90% coverage.
"""


import pytest

from src.auth.services.container import (
    ServiceContainer,
    ServiceContainerConfiguration,
    ServiceLifetime,
    ServiceResolutionError,
    ServiceStatus,
    configure_container,
    get_container,
    reset_container,
)


class TestServiceLifetime:
    """Test ServiceLifetime enum."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert ServiceLifetime.SINGLETON == "singleton"
        assert ServiceLifetime.TRANSIENT == "transient"

    def test_enum_iteration(self):
        """Test enum can be iterated."""
        values = [item.value for item in ServiceLifetime]
        assert "singleton" in values
        assert "transient" in values


class TestServiceStatus:
    """Test ServiceStatus enum."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert ServiceStatus.NOT_REGISTERED == "not_registered"
        assert ServiceStatus.REGISTERED == "registered"
        assert ServiceStatus.INITIALIZING == "initializing"
        assert ServiceStatus.READY == "ready"
        assert ServiceStatus.ERROR == "error"
        assert ServiceStatus.DISPOSED == "disposed"


class TestServiceContainer:
    """Test ServiceContainer implementation."""

    @pytest.fixture
    def container(self):
        """Create a fresh container for testing."""
        config = ServiceContainerConfiguration()
        return ServiceContainer(config)

    @pytest.fixture
    def mock_service_class(self):
        """Create a mock service class."""
        class MockService:
            def __init__(self, value="default"):
                self.value = value

        return MockService

    def test_init(self):
        """Test container initialization."""
        config = ServiceContainerConfiguration()
        container = ServiceContainer(config)

        assert container.config == config
        assert container._registrations == {}
        assert container._instances == {}

    def test_register_singleton_service(self, container, mock_service_class):
        """Test registering a singleton service."""
        result = container.register_singleton(mock_service_class, mock_service_class)

        assert result is container  # Should return self for chaining
        assert mock_service_class in container._registrations
        registration = container._registrations[mock_service_class]
        assert registration.lifetime == ServiceLifetime.SINGLETON

    def test_resolve_singleton_service(self, container, mock_service_class):
        """Test resolving singleton service."""
        container.register_singleton(mock_service_class, mock_service_class)

        service1 = container.resolve(mock_service_class)
        service2 = container.resolve(mock_service_class)

        assert isinstance(service1, mock_service_class)
        assert service1 is service2  # Same instance for singleton

    def test_resolve_unregistered_service_error(self, container):
        """Test error when resolving unregistered service."""
        class UnregisteredService:
            pass

        with pytest.raises(ServiceResolutionError):
            container.resolve(UnregisteredService)

    def test_resolve_with_dependencies(self, container, mock_service_class):
        """Test resolving service with dependencies."""
        class DependentService:
            def __init__(self, dependency):
                self.dependency = dependency

        container.register_singleton(mock_service_class, mock_service_class)
        container.register_singleton(
            DependentService,
            DependentService,
            dependencies=[mock_service_class],
        )

        service = container.resolve(DependentService)
        assert isinstance(service, DependentService)
        assert isinstance(service.dependency, mock_service_class)

    def test_get_service_status(self, container, mock_service_class):
        """Test getting service status."""
        # Not registered
        status = container.get_service_status(mock_service_class)
        assert status == ServiceStatus.NOT_REGISTERED

        # Registered but not resolved
        container.register_singleton(mock_service_class, mock_service_class)
        status = container.get_service_status(mock_service_class)
        assert status == ServiceStatus.REGISTERED

        # Resolved
        container.resolve(mock_service_class)
        status = container.get_service_status(mock_service_class)
        assert status == ServiceStatus.READY

    def test_get_container_metrics(self, container, mock_service_class):
        """Test getting container metrics."""
        container.register_singleton(mock_service_class, mock_service_class)
        container.resolve(mock_service_class)

        metrics = container.get_container_metrics()

        assert "services" in metrics
        assert "performance" in metrics
        assert "health" in metrics
        assert "configuration" in metrics
        assert metrics["services"]["total_registered"] >= 1


class TestGlobalContainerFunctions:
    """Test global container management functions."""

    def test_get_container_default(self):
        """Test getting default container."""
        # Reset first to ensure clean state
        reset_container()

        container = get_container()
        assert isinstance(container, ServiceContainer)

        # Should return same instance
        container2 = get_container()
        assert container is container2

    def test_configure_container(self):
        """Test configuring global container."""
        # Reset first to ensure clean state
        reset_container()

        config = ServiceContainerConfiguration(
            enable_health_checks=False,
            health_check_interval_seconds=600,
        )

        result = configure_container(config)
        assert isinstance(result, ServiceContainer)

        container = get_container()
        assert container.config.enable_health_checks is False

        # Clean up
        reset_container()

    def test_reset_container(self):
        """Test resetting global container."""
        container1 = get_container()
        reset_container()
        container2 = get_container()

        assert container1 is not container2
