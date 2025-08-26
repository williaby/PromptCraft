"""Authentication services package.

This package contains services for authentication, security monitoring, and event logging.
All services support async operations and are designed for high performance.
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
    # Core services
    "SecurityLogger",
    "SecurityMonitor",
    # Alert engine
    "AlertEngine",
    "SecurityAlert",
    "AlertSeverity",
    "AlertType",
    # Notification handlers
    "WebhookHandler",
    "EmailHandler",
    "SlackHandler",
    "WebhookConfig",
    "EmailConfig",
    "SlackConfig",
    "create_notification_handlers",
    # Suspicious activity detection
    "SuspiciousActivityDetector",
    "SuspiciousActivityType",
    "ActivityAnalysisResult",
    "SuspiciousActivityConfig",
    # Security integration
    "SecurityIntegrationService",
    "SecurityIntegrationConfig",
    "SecurityIntegrationMetrics",
    # Audit service
    "AuditService",
    "ExportFormat",
    "RetentionPolicy",
    "AuditReportRequest",
    "AuditStatistics",
    "ComplianceReport",
]
