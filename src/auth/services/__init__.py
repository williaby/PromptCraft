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
    "ActivityAnalysisResult",
    # Alert engine
    "AlertEngine",
    "AlertSeverity",
    "AlertType",
    "AuditReportRequest",
    # Audit service
    "AuditService",
    "AuditStatistics",
    "ComplianceReport",
    "EmailConfig",
    "EmailHandler",
    "ExportFormat",
    "RetentionPolicy",
    "SecurityAlert",
    "SecurityIntegrationConfig",
    "SecurityIntegrationMetrics",
    # Security integration
    "SecurityIntegrationService",
    # Core services
    "SecurityLogger",
    "SecurityMonitor",
    "SlackConfig",
    "SlackHandler",
    "SuspiciousActivityConfig",
    # Suspicious activity detection
    "SuspiciousActivityDetector",
    "SuspiciousActivityType",
    "WebhookConfig",
    # Notification handlers
    "WebhookHandler",
    "create_notification_handlers",
]
