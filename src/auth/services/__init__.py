"""Authentication services package with dependency injection support.

This package contains services for authentication, security monitoring, and event logging.
All services support async operations and are designed for high performance.

Dependency Injection:
- ServiceContainer: Main DI container for service lifecycle management
- ServiceBootstrap: Environment-specific service configuration and initialization
- Service registration with automatic dependency resolution
- Environment-aware configurations (development, test, production)
"""

from .alert_engine import AlertEngine, AlertSeverity, AlertType, SecurityAlert
from .audit_service import (
    AuditReportRequest,
    AuditService,
    AuditStatistics,
    ComplianceReport,
    ExportFormat,
    RetentionPolicy,
)
from .bootstrap import (
    ServiceBootstrapError,
    bootstrap_services_async,
    create_development_container,
    create_production_container,
    create_test_container,
    get_container_for_environment,
    initialize_container_async,
    validate_container_configuration,
)
from .container import (
    CircularDependencyError,
    IServiceContainer,
    ServiceContainer,
    ServiceContainerConfiguration,
    ServiceLifetime,
    ServiceResolutionError,
    ServiceStatus,
    configure_container,
    get_container,
    reset_container,
)
from .notification_handlers import (
    EmailConfig,
    EmailHandler,
    SlackConfig,
    SlackHandler,
    WebhookConfig,
    WebhookHandler,
    create_notification_handlers,
)
from .security_integration import SecurityIntegrationConfig, SecurityIntegrationMetrics, SecurityIntegrationService
from .security_logger import SecurityLogger
from .security_monitor import SecurityMonitor
from .suspicious_activity_detector import (
    ActivityAnalysisResult,
    SuspiciousActivityConfig,
    SuspiciousActivityDetector,
    SuspiciousActivityType,
)

__all__ = [
    "ActivityAnalysisResult",
    # Alert engine
    "AlertEngine",
    "AlertSeverity",
    "AlertType",
    "AuditReportRequest",
    # Audit service
    "AuditService",
    "AuditStatistics",
    # Service bootstrap and initialization
    "bootstrap_services_async",
    # Dependency injection container
    "CircularDependencyError",
    "ComplianceReport",
    "configure_container",
    "create_development_container",
    "create_production_container",
    "create_test_container",
    "EmailConfig",
    "EmailHandler",
    "ExportFormat",
    "get_container",
    "get_container_for_environment",
    "IServiceContainer",
    "initialize_container_async",
    "RetentionPolicy",
    "reset_container",
    "SecurityAlert",
    "SecurityIntegrationConfig",
    "SecurityIntegrationMetrics",
    # Security integration
    "SecurityIntegrationService",
    # Core services
    "SecurityLogger",
    "SecurityMonitor",
    "ServiceBootstrapError",
    "ServiceContainer",
    "ServiceContainerConfiguration",
    "ServiceLifetime",
    "ServiceResolutionError",
    "ServiceStatus",
    "SlackConfig",
    "SlackHandler",
    "SuspiciousActivityConfig",
    # Suspicious activity detection
    "SuspiciousActivityDetector",
    "SuspiciousActivityType",
    "validate_container_configuration",
    "WebhookConfig",
    # Notification handlers
    "WebhookHandler",
    "create_notification_handlers",
]
