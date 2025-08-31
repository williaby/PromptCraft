"""Service bootstrap configuration for AUTH-4 Enhanced Security Event Logging.

This module provides service registration and configuration for the AUTH-4 dependency
injection system. It handles environment-specific setups and service lifecycle management.

Features:
- Environment-specific service configurations (dev, test, production)
- Service dependency mapping and registration
- Configuration validation and health checks
- Service factory functions for complex initialization
- Graceful fallback configurations for missing dependencies

Performance target: < 100ms full service container initialization
Architecture: Configuration-driven service bootstrapping with validation
"""

import logging

from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
from src.auth.services.alert_engine import AlertEngine, AlertEngineConfig
from src.auth.services.audit_service import AuditService
from src.auth.services.container import ServiceContainer, ServiceContainerConfiguration
from src.auth.services.security_logger import LoggingConfig, SecurityLogger
from src.auth.services.security_monitor import MonitoringConfig, SecurityMonitor
from src.auth.services.suspicious_activity_detector import (
    SuspiciousActivityConfig,
    SuspiciousActivityDetector,
)

logger = logging.getLogger(__name__)


class ServiceBootstrapError(Exception):
    """Exception raised when service bootstrap fails."""


def create_development_container() -> ServiceContainer:
    """Create service container configured for development environment.

    Development configuration features:
    - Relaxed security thresholds for easier testing
    - Verbose logging and debug information
    - Local database connections
    - Disabled external integrations (email, Slack)

    Returns:
        Configured service container for development
    """
    config = ServiceContainerConfiguration(
        environment="development",
        enable_health_checks=True,
        health_check_interval_seconds=30,
        log_service_resolutions=True,
    )

    container = ServiceContainer(config)

    # Register core database service
    container.register_singleton(
        SecurityEventsPostgreSQL,
        SecurityEventsPostgreSQL,
        configuration={},
        health_check=lambda db: hasattr(db, "_initialized") and getattr(db, "_initialized", False),
    )

    # Register security logger with development settings
    container.register_singleton(
        SecurityLogger,
        SecurityLogger,
        dependencies=[],  # SecurityLogger doesn't take database as constructor param
        configuration={
            "config": LoggingConfig(
                batch_size=5,  # Smaller batches for development
                batch_timeout_seconds=1.0,  # Faster processing for development
                queue_max_size=100,  # Smaller queue for development
                rate_limit_max_events=1000,  # Higher rate limit for testing
            ),
        },
    )

    # Register alert engine with development settings
    container.register_singleton(
        AlertEngine,
        AlertEngine,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
        configuration={
            "config": AlertEngineConfig(
                processing_batch_size=5,
                alert_rate_limit_max_alerts=200,  # Higher limits for development
                alert_retention_days=30,
            ),
            "notification_handlers": [],  # No external notifications in development
        },
    )

    # Register security monitor with development settings
    container.register_singleton(
        SecurityMonitor,
        SecurityMonitor,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger, AlertEngine],
        factory_func=create_security_monitor_dev,
    )

    # Register suspicious activity detector with development settings
    container.register_singleton(
        SuspiciousActivityDetector,
        SuspiciousActivityDetector,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
        factory_func=create_suspicious_activity_detector_dev,
    )

    # Register audit service
    container.register_singleton(
        AuditService,
        AuditService,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
    )

    logger.info("Development service container configured successfully")
    return container


def create_test_container() -> ServiceContainer:
    """Create service container configured for testing environment.

    Test configuration features:
    - Fast service initialization for quick test startup
    - In-memory or mock services where possible
    - Disabled background tasks and health checks
    - Minimal logging to reduce test noise

    Returns:
        Configured service container for testing
    """
    config = ServiceContainerConfiguration(
        environment="test",
        enable_health_checks=False,  # Disable for faster tests
        log_service_resolutions=False,  # Reduce test noise
        max_initialization_retries=1,  # Fail fast in tests
        initialization_timeout_seconds=5.0,  # Quick timeout for tests
    )

    container = ServiceContainer(config)

    # Register database service (will use test database)
    container.register_singleton(
        SecurityEventsPostgreSQL,
        SecurityEventsPostgreSQL,
    )

    # Register security logger with test settings
    container.register_singleton(
        SecurityLogger,
        SecurityLogger,
        configuration={
            "config": LoggingConfig(
                batch_size=1,  # Process immediately in tests
                batch_timeout_seconds=0.1,  # Very fast processing
                queue_max_size=50,  # Small queue for tests
                rate_limit_max_events=10000,  # Very high limit for tests
            ),
        },
    )

    # Register alert engine with test settings
    container.register_singleton(
        AlertEngine,
        AlertEngine,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
        configuration={
            "config": AlertEngineConfig(
                processing_batch_size=1,
                processing_timeout_seconds=0.1,
                alert_rate_limit_max_alerts=1000,
            ),
            "notification_handlers": [],  # No notifications in tests
        },
    )

    # Register security monitor with test settings
    container.register_singleton(
        SecurityMonitor,
        SecurityMonitor,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger, AlertEngine],
        factory_func=create_security_monitor_test,
    )

    # Register suspicious activity detector with test settings
    container.register_singleton(
        SuspiciousActivityDetector,
        SuspiciousActivityDetector,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
        factory_func=create_suspicious_activity_detector_test,
    )

    # Register audit service
    container.register_singleton(
        AuditService,
        AuditService,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
    )

    logger.info("Test service container configured successfully")
    return container


def create_production_container() -> ServiceContainer:
    """Create service container configured for production environment.

    Production configuration features:
    - Strict security thresholds and monitoring
    - Full external integrations (email, Slack, webhooks)
    - Comprehensive health checks and alerting
    - Optimized performance settings
    - Full logging and audit trails

    Returns:
        Configured service container for production
    """
    config = ServiceContainerConfiguration(
        environment="production",
        enable_health_checks=True,
        health_check_interval_seconds=60,
        log_service_resolutions=False,  # Performance optimization
        max_initialization_retries=3,
        initialization_timeout_seconds=30.0,
    )

    container = ServiceContainer(config)

    # Register database service with production settings
    container.register_singleton(
        SecurityEventsPostgreSQL,
        SecurityEventsPostgreSQL,
        configuration={
            "connection_pool_size": 20,  # Larger pool for production
            "max_overflow": 30,
        },
        health_check=lambda db: hasattr(db, "_initialized") and getattr(db, "_initialized", False),
    )

    # Register security logger with production settings
    container.register_singleton(
        SecurityLogger,
        SecurityLogger,
        configuration={
            "config": LoggingConfig(
                batch_size=50,  # Optimized batch size
                batch_timeout_seconds=2.0,
                queue_max_size=1000,
                rate_limit_max_events=500,
                retention_days_info=14,
                retention_days_warning=90,
                retention_days_critical=365,
            ),
        },
        health_check=lambda logger: (
            hasattr(logger, "_batch_processor_task")
            and logger._batch_processor_task
            and not logger._batch_processor_task.done()
        ),
    )

    # Register alert engine with production notification handlers
    container.register_singleton(
        AlertEngine,
        AlertEngine,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
        factory_func=create_alert_engine_production,
        health_check=lambda engine: (
            hasattr(engine, "_processor_task") and engine._processor_task and not engine._processor_task.done()
        ),
    )

    # Register security monitor with production settings
    container.register_singleton(
        SecurityMonitor,
        SecurityMonitor,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger, AlertEngine],
        factory_func=create_security_monitor_production,
    )

    # Register suspicious activity detector with production settings
    container.register_singleton(
        SuspiciousActivityDetector,
        SuspiciousActivityDetector,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
        factory_func=create_suspicious_activity_detector_production,
    )

    # Register audit service
    container.register_singleton(
        AuditService,
        AuditService,
        dependencies=[SecurityEventsPostgreSQL, SecurityLogger],
    )

    logger.info("Production service container configured successfully")
    return container


def create_security_monitor_dev(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
    alert_engine: AlertEngine,
) -> SecurityMonitor:
    """Factory function for creating SecurityMonitor in development environment."""
    config = MonitoringConfig(
        failed_attempts_threshold=3,  # Lower threshold for testing
        failed_attempts_window_minutes=5,
        brute_force_threshold=5,
        brute_force_window_minutes=10,
        account_lockout_enabled=True,
        account_lockout_duration_minutes=15,  # Shorter lockout for development
        suspicious_ip_threshold=20,  # Lower threshold for testing
    )

    return SecurityMonitor(
        db=db,
        security_logger=security_logger,
        alert_engine=alert_engine,
        config=config,
    )


def create_security_monitor_test(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
    alert_engine: AlertEngine,
) -> SecurityMonitor:
    """Factory function for creating SecurityMonitor in test environment."""
    config = MonitoringConfig(
        failed_attempts_threshold=2,  # Very low threshold for fast tests
        failed_attempts_window_minutes=1,
        brute_force_threshold=3,
        brute_force_window_minutes=1,
        account_lockout_enabled=False,  # Disable lockout in tests unless explicitly testing it
        cleanup_interval_minutes=1,  # Fast cleanup for tests
    )

    return SecurityMonitor(
        db=db,
        security_logger=security_logger,
        alert_engine=alert_engine,
        config=config,
    )


def create_security_monitor_production(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
    alert_engine: AlertEngine,
) -> SecurityMonitor:
    """Factory function for creating SecurityMonitor in production environment."""
    config = MonitoringConfig(
        failed_attempts_threshold=10,  # Production threshold
        failed_attempts_window_minutes=5,
        brute_force_threshold=25,
        brute_force_window_minutes=10,
        account_lockout_enabled=True,
        account_lockout_duration_minutes=30,
        suspicious_ip_threshold=50,
        suspicious_ip_window_minutes=15,
        monitoring_rate_limit=1000,
        max_tracking_entries=10000,
        cleanup_interval_minutes=60,
    )

    return SecurityMonitor(
        db=db,
        security_logger=security_logger,
        alert_engine=alert_engine,
        config=config,
    )


def create_suspicious_activity_detector_dev(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
) -> SuspiciousActivityDetector:
    """Factory function for creating SuspiciousActivityDetector in development environment."""
    config = SuspiciousActivityConfig(
        risk_threshold_suspicious=30,  # Lower threshold for development
        risk_threshold_critical=60,
        historical_window_days=7,  # Shorter window for development
        minimum_baseline_events=5,
    )

    return SuspiciousActivityDetector(
        config=config,
        db=db,
        security_logger=security_logger,
    )


def create_suspicious_activity_detector_test(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
) -> SuspiciousActivityDetector:
    """Factory function for creating SuspiciousActivityDetector in test environment."""
    config = SuspiciousActivityConfig(
        risk_threshold_suspicious=20,  # Very low threshold for tests
        risk_threshold_critical=40,
        historical_window_days=1,  # Minimal window for fast tests
        minimum_baseline_events=2,
        enable_geolocation_check=False,  # Disable complex features in tests
    )

    return SuspiciousActivityDetector(
        config=config,
        db=db,
        security_logger=security_logger,
    )


def create_suspicious_activity_detector_production(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
) -> SuspiciousActivityDetector:
    """Factory function for creating SuspiciousActivityDetector in production environment."""
    config = SuspiciousActivityConfig(
        risk_threshold_suspicious=40,  # Production threshold
        risk_threshold_critical=70,
        historical_window_days=30,
        minimum_baseline_events=10,
        enable_geolocation_check=True,
        enable_time_analysis=True,
        enable_user_agent_analysis=True,
        enable_behavioral_analysis=True,
        max_distance_km=1000.0,
        impossible_travel_speed_kmh=900.0,
    )

    return SuspiciousActivityDetector(
        config=config,
        db=db,
        security_logger=security_logger,
    )


def create_alert_engine_production(
    db: SecurityEventsPostgreSQL,
    security_logger: SecurityLogger,
) -> AlertEngine:
    """Factory function for creating AlertEngine with production notification handlers."""
    # Create notification handlers for production
    notification_handlers = []

    # TODO: Configure actual email/Slack/webhook handlers based on environment variables
    # For now, create placeholder handlers that can be configured later

    config = AlertEngineConfig(
        processing_batch_size=20,
        processing_timeout_seconds=1.0,
        alert_rate_limit_window_minutes=60,
        alert_rate_limit_max_alerts=100,
        webhook_timeout_seconds=5.0,
        webhook_retry_attempts=3,
        alert_retention_days=90,
        event_correlation_window_minutes=30,
    )

    return AlertEngine(
        config=config,
        notification_handlers=notification_handlers,
        db=db,
        security_logger=security_logger,
    )


async def initialize_container_async(container: ServiceContainer) -> dict[type, bool]:
    """Initialize all services in the container asynchronously.

    Args:
        container: Service container to initialize

    Returns:
        Dictionary of service types and their initialization success status

    Raises:
        ServiceBootstrapError: If critical services fail to initialize
    """
    try:
        # Get all registered services
        service_types = list(container._registrations.keys())

        logger.info(f"Initializing {len(service_types)} services...")

        # Initialize services
        results = await container.initialize_services(service_types)

        # Check for critical service failures
        critical_services = [SecurityEventsPostgreSQL, SecurityLogger]
        failed_critical = [
            service_type for service_type in critical_services if service_type in results and not results[service_type]
        ]

        if failed_critical:
            failed_names = [s.__name__ for s in failed_critical]
            raise ServiceBootstrapError(f"Critical services failed to initialize: {failed_names}")

        successful_count = sum(results.values())
        total_count = len(results)

        logger.info(f"Service initialization completed: {successful_count}/{total_count} services ready")

        return results

    except Exception as e:
        logger.error(f"Service container initialization failed: {e}")
        raise ServiceBootstrapError(f"Container initialization failed: {e}") from e


def get_container_for_environment(environment: str = "development") -> ServiceContainer:
    """Get a pre-configured service container for the specified environment.

    Args:
        environment: Environment name (development, test, production)

    Returns:
        Configured service container

    Raises:
        ServiceBootstrapError: If environment is not supported
    """
    environment = environment.lower().strip()

    container_factories = {
        "development": create_development_container,
        "dev": create_development_container,
        "test": create_test_container,
        "testing": create_test_container,
        "production": create_production_container,
        "prod": create_production_container,
    }

    if environment not in container_factories:
        supported = list(container_factories.keys())
        raise ServiceBootstrapError(f"Unsupported environment '{environment}'. Supported: {supported}")

    factory = container_factories[environment]
    container = factory()

    logger.info(f"Service container created for environment: {environment}")
    return container


async def bootstrap_services_async(environment: str = "development") -> ServiceContainer:
    """Bootstrap all AUTH-4 services for the specified environment.

    This is the main entry point for setting up the complete AUTH-4 service stack
    with dependency injection.

    Args:
        environment: Environment name (development, test, production)

    Returns:
        Fully initialized service container

    Raises:
        ServiceBootstrapError: If bootstrap fails
    """
    try:
        # Create container for environment
        container = get_container_for_environment(environment)

        # Initialize all services
        await initialize_container_async(container)

        logger.info(f"AUTH-4 services successfully bootstrapped for {environment} environment")
        return container

    except Exception as e:
        logger.error(f"Service bootstrap failed: {e}")
        raise ServiceBootstrapError(f"Bootstrap failed: {e}") from e


def validate_container_configuration(container: ServiceContainer) -> list[str]:
    """Validate service container configuration and return any issues found.

    Args:
        container: Service container to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    issues = []

    try:
        # Check that all critical services are registered
        critical_services = [
            SecurityEventsPostgreSQL,
            SecurityLogger,
            AlertEngine,
            SecurityMonitor,
            SuspiciousActivityDetector,
            AuditService,
        ]

        for service_type in critical_services:
            if service_type not in container._registrations:
                issues.append(f"Critical service not registered: {service_type.__name__}")

        # Check dependency resolution
        for service_type, registration in container._registrations.items():
            for dependency in registration.dependencies:
                if dependency not in container._registrations:
                    issues.append(
                        f"Service {service_type.__name__} depends on unregistered service: {dependency.__name__}",
                    )

        # Check for circular dependencies
        if container.config.enable_circular_dependency_detection:
            try:
                for service_type in container._registrations:
                    container._detect_circular_dependencies(service_type)
            except Exception as e:
                issues.append(f"Circular dependency detected: {e}")

    except Exception as e:
        issues.append(f"Validation error: {e}")

    return issues
