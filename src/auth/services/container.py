"""Service container for dependency injection in AUTH-4 Enhanced Security Event Logging.

This module provides a comprehensive dependency injection container for managing
service lifecycles, dependencies, and configuration in the AUTH-4 system.

Features:
- Service registration with singleton and transient lifetimes
- Automatic dependency resolution and injection
- Configuration-based service initialization
- Environment-specific service setups (dev, test, production)
- Circular dependency detection and prevention
- Service health monitoring and lifecycle management

Performance target: < 1ms service resolution time
Architecture: Container-based dependency injection with lazy initialization
"""

import asyncio
import contextlib
import inspect
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar, Union
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceLifetime(str, Enum):
    """Service lifetime management options."""

    SINGLETON = "singleton"      # Single instance shared across requests
    TRANSIENT = "transient"      # New instance created each time
    SCOPED = "scoped"           # Single instance per request scope


class ServiceStatus(str, Enum):
    """Service status for health monitoring."""

    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISPOSED = "disposed"


@dataclass
class ServiceRegistration:
    """Service registration metadata."""

    service_type: type[T]
    implementation: type[T] | Callable[..., T] | T
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: list[type] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    factory_func: Callable[..., T] | None = None
    initialization_required: bool = True
    health_check: Callable[[T], bool] | None = None

    # Runtime metadata
    registration_id: str = field(default_factory=lambda: str(uuid4()))
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ServiceInstance:
    """Service instance metadata."""

    service: Any
    registration: ServiceRegistration
    status: ServiceStatus = ServiceStatus.REGISTERED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_health_check: datetime | None = None
    error_count: int = 0
    last_error: str | None = None


class ServiceResolutionError(Exception):
    """Exception raised when service resolution fails."""


class CircularDependencyError(ServiceResolutionError):
    """Exception raised when circular dependency is detected."""


class ServiceConfigurationError(Exception):
    """Exception raised when service configuration is invalid."""


class ServiceHealthError(Exception):
    """Exception raised when service health check fails."""


class IServiceContainer(ABC):
    """Abstract base class for service containers."""

    @abstractmethod
    def register_singleton(self, service_type: type[T], implementation: type[T] | Callable[..., T] | T) -> None:
        """Register a singleton service."""

    @abstractmethod
    def register_transient(self, service_type: type[T], implementation: type[T] | Callable[..., T] | T) -> None:
        """Register a transient service."""

    @abstractmethod
    def resolve(self, service_type: type[T]) -> T:
        """Resolve a service instance."""

    @abstractmethod
    async def initialize_services(self) -> None:
        """Initialize all registered services."""


class ServiceContainerConfiguration(BaseModel):
    """Configuration for the service container."""

    environment: str = Field(default="development", description="Environment name (dev, test, prod)")
    enable_health_checks: bool = Field(default=True, description="Enable service health monitoring")
    health_check_interval_seconds: int = Field(default=60, description="Health check interval")
    max_initialization_retries: int = Field(default=3, description="Maximum initialization retries")
    initialization_timeout_seconds: float = Field(default=30.0, description="Service initialization timeout")
    enable_circular_dependency_detection: bool = Field(default=True, description="Enable circular dependency detection")
    log_service_resolutions: bool = Field(default=False, description="Log all service resolutions for debugging")


class ServiceContainer(IServiceContainer):
    """Comprehensive dependency injection container for AUTH-4 services."""

    def __init__(self, config: ServiceContainerConfiguration | None = None) -> None:
        """Initialize the service container.

        Args:
            config: Container configuration (uses defaults if None)
        """
        self.config = config or ServiceContainerConfiguration()

        # Service registry
        self._registrations: dict[type, ServiceRegistration] = {}
        self._instances: dict[type, ServiceInstance] = {}
        self._factory_cache: dict[str, Any] = {}

        # Dependency tracking
        self._resolution_stack: list[type] = []
        self._dependency_graph: dict[type, list[type]] = defaultdict(list)

        # Health monitoring
        self._health_check_task: asyncio.Task | None = None
        self._initialization_lock = asyncio.Lock()

        # Performance metrics
        self._resolution_times: list[float] = []
        self._initialization_times: dict[type, float] = {}

        logger.info(f"Service container initialized for environment: {self.config.environment}")

    def register_singleton(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | T,
        dependencies: list[type] | None = None,
        configuration: dict[str, Any] | None = None,
        factory_func: Callable[..., T] | None = None,
        health_check: Callable[[T], bool] | None = None,
    ) -> "ServiceContainer":
        """Register a singleton service.

        Args:
            service_type: Service interface or base type
            implementation: Service implementation, factory function, or instance
            dependencies: List of dependency types to inject
            configuration: Service-specific configuration
            factory_func: Custom factory function for service creation
            health_check: Health check function for monitoring

        Returns:
            Self for method chaining
        """
        return self._register_service(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SINGLETON,
            dependencies=dependencies or [],
            configuration=configuration or {},
            factory_func=factory_func,
            health_check=health_check,
        )

    def register_transient(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | T,
        dependencies: list[type] | None = None,
        configuration: dict[str, Any] | None = None,
        factory_func: Callable[..., T] | None = None,
    ) -> "ServiceContainer":
        """Register a transient service.

        Args:
            service_type: Service interface or base type
            implementation: Service implementation or factory function
            dependencies: List of dependency types to inject
            configuration: Service-specific configuration
            factory_func: Custom factory function for service creation

        Returns:
            Self for method chaining
        """
        return self._register_service(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=dependencies or [],
            configuration=configuration or {},
            factory_func=factory_func,
        )

    def _register_service(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | T,
        lifetime: ServiceLifetime,
        dependencies: list[type],
        configuration: dict[str, Any],
        factory_func: Callable[..., T] | None = None,
        health_check: Callable[[T], bool] | None = None,
    ) -> "ServiceContainer":
        """Internal method to register a service."""
        try:
            # Validate registration
            self._validate_service_registration(service_type, implementation, dependencies)

            # Auto-detect dependencies if None (not if empty list)
            if dependencies is None and inspect.isclass(implementation):
                dependencies = self._analyze_constructor_dependencies(implementation)
            elif dependencies is None:
                dependencies = []

            # Create registration
            registration = ServiceRegistration(
                service_type=service_type,
                implementation=implementation,
                lifetime=lifetime,
                dependencies=dependencies,
                configuration=configuration,
                factory_func=factory_func,
                health_check=health_check,
            )

            # Store registration
            self._registrations[service_type] = registration

            # Update dependency graph for circular dependency detection
            self._dependency_graph[service_type] = dependencies

            # Validate no circular dependencies
            if self.config.enable_circular_dependency_detection:
                self._detect_circular_dependencies(service_type)

            logger.debug(f"Registered {lifetime.value} service: {service_type.__name__}")

            return self

        except Exception as e:
            logger.error(f"Failed to register service {service_type.__name__}: {e}")
            raise ServiceConfigurationError(f"Service registration failed: {e}") from e

    def resolve(self, service_type: type[T]) -> T:
        """Resolve a service instance with dependency injection.

        Args:
            service_type: Type of service to resolve

        Returns:
            Service instance with all dependencies injected

        Raises:
            ServiceResolutionError: If service cannot be resolved
        """
        import time
        start_time = time.time()

        try:
            # Check if service is registered
            if service_type not in self._registrations:
                raise ServiceResolutionError(f"Service {service_type.__name__} is not registered")

            registration = self._registrations[service_type]

            # For singleton lifetime, return existing instance if available
            if registration.lifetime == ServiceLifetime.SINGLETON:
                if service_type in self._instances:
                    instance = self._instances[service_type]
                    if instance.status == ServiceStatus.READY:
                        return instance.service
                    if instance.status == ServiceStatus.ERROR:
                        raise ServiceResolutionError(f"Service {service_type.__name__} is in error state: {instance.last_error}")

            # Check for circular dependencies
            if service_type in self._resolution_stack:
                cycle = " -> ".join([t.__name__ for t in self._resolution_stack] + [service_type.__name__])
                raise CircularDependencyError(f"Circular dependency detected: {cycle}")

            # Add to resolution stack
            self._resolution_stack.append(service_type)

            try:
                # Resolve dependencies first
                resolved_dependencies = []
                for dependency_type in registration.dependencies:
                    dependency_instance = self.resolve(dependency_type)
                    resolved_dependencies.append(dependency_instance)

                # Create service instance
                service_instance = self._create_service_instance(registration, resolved_dependencies)

                # Store instance for singleton lifetime
                if registration.lifetime == ServiceLifetime.SINGLETON:
                    instance_metadata = ServiceInstance(
                        service=service_instance,
                        registration=registration,
                        status=ServiceStatus.READY,
                    )
                    self._instances[service_type] = instance_metadata

                # Log resolution if enabled
                if self.config.log_service_resolutions:
                    resolution_time_ms = (time.time() - start_time) * 1000
                    logger.debug(f"Resolved {service_type.__name__} in {resolution_time_ms:.2f}ms")
                    self._resolution_times.append(resolution_time_ms)

                return service_instance

            finally:
                # Remove from resolution stack
                if service_type in self._resolution_stack:
                    self._resolution_stack.remove(service_type)

        except Exception as e:
            logger.error(f"Failed to resolve service {service_type.__name__}: {e}")

            # Mark singleton as error state if applicable
            if service_type in self._registrations and self._registrations[service_type].lifetime == ServiceLifetime.SINGLETON:
                error_instance = ServiceInstance(
                    service=None,
                    registration=self._registrations[service_type],
                    status=ServiceStatus.ERROR,
                    last_error=str(e),
                )
                self._instances[service_type] = error_instance

            if isinstance(e, (ServiceResolutionError, CircularDependencyError)):
                raise
            raise ServiceResolutionError(f"Failed to resolve {service_type.__name__}: {e}") from e

    async def initialize_services(self, service_types: list[type] | None = None) -> dict[type, bool]:
        """Initialize registered services asynchronously.

        Args:
            service_types: Specific services to initialize (all if None)

        Returns:
            Dictionary of service types and their initialization success status
        """
        async with self._initialization_lock:
            services_to_initialize = service_types or list(self._registrations.keys())
            results = {}

            logger.info(f"Initializing {len(services_to_initialize)} services...")

            # Initialize services in dependency order
            initialization_order = self._calculate_initialization_order(services_to_initialize)

            for service_type in initialization_order:
                try:
                    start_time = datetime.now()

                    # Resolve the service (this will create it)
                    service_instance = self.resolve(service_type)

                    # Call initialize method if it exists
                    if hasattr(service_instance, "initialize") and callable(service_instance.initialize):
                        if asyncio.iscoroutinefunction(service_instance.initialize):
                            await asyncio.wait_for(
                                service_instance.initialize(),
                                timeout=self.config.initialization_timeout_seconds,
                            )
                        else:
                            service_instance.initialize()

                    # Update instance status
                    if service_type in self._instances:
                        self._instances[service_type].status = ServiceStatus.READY

                    # Record initialization time
                    init_time = (datetime.now() - start_time).total_seconds()
                    self._initialization_times[service_type] = init_time

                    results[service_type] = True
                    logger.debug(f"Initialized {service_type.__name__} in {init_time:.2f}s")

                except Exception as e:
                    logger.error(f"Failed to initialize {service_type.__name__}: {e}")

                    # Mark as error state
                    if service_type in self._instances:
                        self._instances[service_type].status = ServiceStatus.ERROR
                        self._instances[service_type].last_error = str(e)
                        self._instances[service_type].error_count += 1

                    results[service_type] = False

            # Start health monitoring if enabled
            if self.config.enable_health_checks and not self._health_check_task:
                self._start_health_monitoring()

            successful_count = sum(results.values())
            logger.info(f"Service initialization completed: {successful_count}/{len(services_to_initialize)} services ready")

            return results

    def _create_service_instance(self, registration: ServiceRegistration, dependencies: list[Any]) -> Any:
        """Create a service instance with resolved dependencies."""
        try:
            # Use custom factory if provided
            if registration.factory_func:
                return registration.factory_func(*dependencies, **registration.configuration)

            # If implementation is already an instance, return it
            if not inspect.isclass(registration.implementation) and not callable(registration.implementation):
                return registration.implementation

            # If implementation is a callable/class, call it with dependencies
            if inspect.isclass(registration.implementation):
                # Analyze constructor to match dependencies to parameters
                constructor_params = self._get_constructor_parameters(registration.implementation)

                # Build keyword arguments from configuration
                kwargs = registration.configuration.copy()

                # Add positional dependencies based on parameter analysis
                if dependencies:
                    # Map dependencies to constructor parameters (skip 'self')
                    param_names = [name for name in constructor_params if name not in ["self", "cls"]]
                    for i, dependency in enumerate(dependencies):
                        if i < len(param_names):
                            param_name = param_names[i]
                            if param_name not in kwargs:
                                kwargs[param_name] = dependency

                return registration.implementation(**kwargs)

            if callable(registration.implementation):
                return registration.implementation(*dependencies, **registration.configuration)

            raise ServiceConfigurationError(f"Invalid implementation type: {type(registration.implementation)}")

        except Exception as e:
            logger.error(f"Failed to create service instance: {e}")
            raise ServiceResolutionError(f"Service instance creation failed: {e}") from e

    def _validate_service_registration(self, service_type: type, implementation: Any, dependencies: list[type]) -> None:
        """Validate service registration parameters."""
        if not service_type:
            raise ServiceConfigurationError("Service type cannot be None")

        if not implementation:
            raise ServiceConfigurationError("Service implementation cannot be None")

        # Validate dependencies are types
        for dep in dependencies:
            if not isinstance(dep, type):
                raise ServiceConfigurationError(f"Dependency {dep} must be a type")

    def _analyze_constructor_dependencies(self, implementation: type) -> list[type]:
        """Analyze constructor parameters to auto-detect dependencies."""
        dependencies = []

        try:
            constructor_params = self._get_constructor_parameters(implementation)

            for param_name, param in constructor_params.items():
                if param_name in ["self", "cls"]:
                    continue

                # Try to extract type annotation
                if param.annotation != inspect.Parameter.empty:
                    annotation = param.annotation

                    # Handle Optional[Type] annotations
                    if hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
                        args = annotation.__args__
                        if len(args) == 2 and type(None) in args:
                            # This is Optional[Type]
                            non_none_type = next(arg for arg in args if arg != type(None))
                            if isinstance(non_none_type, type):
                                dependencies.append(non_none_type)
                    elif isinstance(annotation, type):
                        dependencies.append(annotation)

        except Exception as e:
            logger.warning(f"Failed to analyze constructor dependencies for {implementation.__name__}: {e}")

        return dependencies

    def _get_constructor_parameters(self, cls: type) -> dict[str, inspect.Parameter]:
        """Get constructor parameters for a class."""
        try:
            signature = inspect.signature(cls.__init__)
            return signature.parameters
        except Exception:
            return {}

    def _detect_circular_dependencies(self, service_type: type) -> None:
        """Detect circular dependencies in the dependency graph."""
        visited = set()
        rec_stack = set()

        def has_cycle(node: type) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._dependency_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        if has_cycle(service_type):
            raise CircularDependencyError(f"Circular dependency detected involving {service_type.__name__}")

    def _calculate_initialization_order(self, service_types: list[type]) -> list[type]:
        """Calculate service initialization order based on dependencies."""
        # Topological sort of dependency graph
        visited = set()
        temp_visited = set()
        result = []

        def visit(service_type: type) -> None:
            if service_type in temp_visited:
                # Circular dependency detected - handle gracefully
                return
            if service_type in visited:
                return

            temp_visited.add(service_type)

            # Visit dependencies first
            for dependency in self._dependency_graph.get(service_type, []):
                if dependency in service_types:
                    visit(dependency)

            temp_visited.remove(service_type)
            visited.add(service_type)
            result.append(service_type)

        for service_type in service_types:
            if service_type not in visited:
                visit(service_type)

        return result

    def _start_health_monitoring(self) -> None:
        """Start background health monitoring task."""
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._health_monitor())
            logger.info("Started service health monitoring")

    async def _health_monitor(self) -> None:
        """Background task for monitoring service health."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all services."""
        for service_type, instance in self._instances.items():
            registration = instance.registration

            if instance.status != ServiceStatus.READY or not registration.health_check:
                continue

            try:
                is_healthy = registration.health_check(instance.service)
                instance.last_health_check = datetime.now(UTC)

                if not is_healthy:
                    instance.status = ServiceStatus.ERROR
                    instance.error_count += 1
                    instance.last_error = "Health check failed"
                    logger.warning(f"Service {service_type.__name__} failed health check")

            except Exception as e:
                instance.status = ServiceStatus.ERROR
                instance.error_count += 1
                instance.last_error = str(e)
                logger.error(f"Health check error for {service_type.__name__}: {e}")

    def get_service_status(self, service_type: type) -> ServiceStatus:
        """Get current status of a service."""
        if service_type not in self._registrations:
            return ServiceStatus.NOT_REGISTERED

        if service_type in self._instances:
            return self._instances[service_type].status

        return ServiceStatus.REGISTERED

    def get_container_metrics(self) -> dict[str, Any]:
        """Get container performance and health metrics."""
        return {
            "services": {
                "total_registered": len(self._registrations),
                "total_instances": len(self._instances),
                "ready_services": sum(1 for i in self._instances.values() if i.status == ServiceStatus.READY),
                "error_services": sum(1 for i in self._instances.values() if i.status == ServiceStatus.ERROR),
            },
            "performance": {
                "average_resolution_time_ms": (
                    sum(self._resolution_times) / len(self._resolution_times)
                    if self._resolution_times else 0.0
                ),
                "total_resolutions": len(self._resolution_times),
                "initialization_times": {
                    service_type.__name__: time_seconds
                    for service_type, time_seconds in self._initialization_times.items()
                },
            },
            "health": {
                "health_checks_enabled": self.config.enable_health_checks,
                "last_health_check": max(
                    (i.last_health_check for i in self._instances.values() if i.last_health_check),
                    default=None,
                ),
            },
            "configuration": {
                "environment": self.config.environment,
                "circular_dependency_detection": self.config.enable_circular_dependency_detection,
            },
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the container and all services."""
        logger.info("Shutting down service container...")

        # Cancel health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_check_task

        # Dispose services in reverse dependency order
        shutdown_order = list(reversed(self._calculate_initialization_order(list(self._instances.keys()))))

        for service_type in shutdown_order:
            if service_type in self._instances:
                instance = self._instances[service_type]
                try:
                    # Call dispose/shutdown method if it exists
                    service = instance.service
                    if hasattr(service, "shutdown") and callable(service.shutdown):
                        if asyncio.iscoroutinefunction(service.shutdown):
                            await service.shutdown()
                        else:
                            service.shutdown()

                    instance.status = ServiceStatus.DISPOSED

                except Exception as e:
                    logger.error(f"Error shutting down service {service_type.__name__}: {e}")

        logger.info("Service container shutdown completed")


# Global container instance for easy access
_global_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def configure_container(config: ServiceContainerConfiguration) -> ServiceContainer:
    """Configure the global service container."""
    global _global_container
    _global_container = ServiceContainer(config)
    return _global_container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _global_container
    if _global_container:
        try:
            # Try to shutdown gracefully if there's a running event loop
            asyncio.get_running_loop()
            asyncio.create_task(_global_container.shutdown())
        except RuntimeError:
            # No running event loop, just reset without shutdown
            pass
    _global_container = None
