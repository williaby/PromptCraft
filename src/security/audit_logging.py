"""Audit logging system for security events.

This module provides comprehensive audit logging capabilities for tracking
security-relevant events throughout the application lifecycle.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog
from fastapi import Request, status

from src.config.settings import get_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Get structured logger for audit events
audit_logger = structlog.get_logger("audit")


class AuditEventType(str, Enum):
    """Types of audit events to track."""

    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_CREATED = "auth.token.created"  # nosec B105  # Not a password - audit event type
    AUTH_TOKEN_REVOKED = "auth.token.revoked"  # nosec B105  # Not a password - audit event type

    # Authorization events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"
    AUTHZ_PERMISSION_ESCALATION = "authz.permission.escalation"

    # Data access events
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Security events
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious.activity"
    SECURITY_ERROR_HANDLER_TRIGGERED = "security.error_handler.triggered"
    SECURITY_VALIDATION_FAILURE = "security.validation.failure"

    # Administrative events
    ADMIN_CONFIG_CHANGE = "admin.config.change"
    ADMIN_USER_CREATE = "admin.user.create"
    ADMIN_USER_DELETE = "admin.user.delete"
    ADMIN_SYSTEM_SHUTDOWN = "admin.system.shutdown"
    ADMIN_SYSTEM_STARTUP = "admin.system.startup"

    # API events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"


class AuditEventSeverity(str, Enum):
    """Severity levels for audit events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent:
    """Structured audit event for security logging."""

    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditEventSeverity,
        message: str,
        request: Request | None = None,
        user_id: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        outcome: str | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize audit event.

        Args:
            event_type: Type of audit event
            severity: Event severity level
            message: Human-readable event description
            request: FastAPI request object (if applicable)
            user_id: User identifier (if authenticated)
            resource: Resource being accessed/modified
            action: Action being performed
            outcome: Outcome of the action (success/failure/etc.)
            additional_data: Additional context data
        """
        self.event_type = event_type
        self.severity = severity
        self.message = message
        self.timestamp = datetime.now(UTC).isoformat()
        self.request = request
        self.user_id = user_id
        self.resource = resource
        self.action = action
        self.outcome = outcome
        self.additional_data = additional_data or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert audit event to dictionary for logging.

        Returns:
            Dictionary representation of the audit event
        """
        event_data = {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "outcome": self.outcome,
        }

        # Add request information if available
        if self.request:
            event_data.update(
                {
                    "request": {
                        "method": self.request.method,
                        "path": self.request.url.path,
                        "query_params": dict(self.request.query_params),
                        "client_ip": self._get_client_ip(self.request),
                        "user_agent": self.request.headers.get("user-agent", "unknown"),
                        "referer": self.request.headers.get("referer"),
                    },
                },
            )

        # Add user information
        if self.user_id:
            event_data["user_id"] = self.user_id

        # Add resource and action
        if self.resource:
            event_data["resource"] = self.resource

        if self.action:
            event_data["action"] = self.action

        # Add additional context data
        if self.additional_data:
            event_data["additional_data"] = self.additional_data

        return event_data

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        return request.client.host if request.client else "unknown"


class AuditLogger:
    """Centralized audit logging system."""

    def __init__(self) -> None:
        """Initialize audit logger."""
        self.settings = get_settings(validate_on_startup=False)
        self.logger = audit_logger

    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: The audit event to log
        """
        event_data = event.to_dict()

        # Log based on severity
        if event.severity == AuditEventSeverity.CRITICAL:
            self.logger.critical(event.message, **event_data)
        elif event.severity == AuditEventSeverity.HIGH:
            self.logger.error(event.message, **event_data)
        elif event.severity == AuditEventSeverity.MEDIUM:
            self.logger.warning(event.message, **event_data)
        else:
            self.logger.info(event.message, **event_data)

    def log_authentication_event(
        self,
        event_type: AuditEventType,
        request: Request,
        user_id: str | None = None,
        outcome: str = "success",
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Log authentication-related events.

        Args:
            event_type: Authentication event type
            request: FastAPI request object
            user_id: User identifier
            outcome: Authentication outcome
            additional_data: Additional context data
        """
        severity = AuditEventSeverity.HIGH if outcome == "failure" else AuditEventSeverity.MEDIUM
        message = f"Authentication event: {event_type.value} - {outcome}"

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            request=request,
            user_id=user_id,
            action="authenticate",
            outcome=outcome,
            additional_data=additional_data,
        )

        self.log_event(event)

    def log_security_event(
        self,
        event_type: AuditEventType,
        message: str,
        request: Request | None = None,
        severity: AuditEventSeverity = AuditEventSeverity.HIGH,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Log security-related events.

        Args:
            event_type: Security event type
            message: Event description
            request: FastAPI request object (if applicable)
            severity: Event severity
            additional_data: Additional context data
        """
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            request=request,
            action="security_check",
            outcome="detected",
            additional_data=additional_data,
        )

        self.log_event(event)

    def log_api_event(
        self,
        request: Request,
        response_status: int,
        processing_time: float,
        user_id: str | None = None,
    ) -> None:
        """Log API request/response events.

        Args:
            request: FastAPI request object
            response_status: HTTP response status code
            processing_time: Request processing time in seconds
            user_id: User identifier (if authenticated)
        """
        # HTTP status code thresholds
        server_error_threshold = status.HTTP_500_INTERNAL_SERVER_ERROR
        client_error_threshold = status.HTTP_400_BAD_REQUEST

        # Determine severity based on status code
        if response_status >= server_error_threshold:
            severity = AuditEventSeverity.HIGH
            outcome = "server_error"
        elif response_status >= client_error_threshold:
            severity = AuditEventSeverity.MEDIUM
            outcome = "client_error"
        else:
            severity = AuditEventSeverity.LOW
            outcome = "success"

        message = f"API request: {request.method} {request.url.path} -> {response_status}"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=severity,
            message=message,
            request=request,
            user_id=user_id,
            resource=request.url.path,
            action=request.method.lower(),
            outcome=outcome,
            additional_data={
                "response_status": response_status,
                "processing_time": processing_time,
            },
        )

        self.log_event(event)


# Global audit logger instance
audit_logger_instance = AuditLogger()


# Convenience functions for common audit events
def log_authentication_success(request: Request, user_id: str) -> None:
    """Log successful authentication."""
    audit_logger_instance.log_authentication_event(
        AuditEventType.AUTH_LOGIN_SUCCESS,
        request,
        user_id,
        "success",
    )


def log_authentication_failure(request: Request, reason: str = "invalid_credentials") -> None:
    """Log failed authentication."""
    audit_logger_instance.log_authentication_event(
        AuditEventType.AUTH_LOGIN_FAILURE,
        request,
        None,
        "failure",
        {"failure_reason": reason},
    )


def log_rate_limit_exceeded(request: Request, limit: str) -> None:
    """Log rate limit exceeded event."""
    audit_logger_instance.log_security_event(
        AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED,
        "Rate limit exceeded",
        request,
        AuditEventSeverity.MEDIUM,
        {"rate_limit": limit},
    )


def log_validation_failure(request: Request, validation_errors: list) -> None:
    """Log validation failure event."""
    audit_logger_instance.log_security_event(
        AuditEventType.SECURITY_VALIDATION_FAILURE,
        "Request validation failed",
        request,
        AuditEventSeverity.MEDIUM,
        {"validation_errors": validation_errors},
    )


def log_error_handler_triggered(request: Request, error_type: str, error_message: str) -> None:
    """Log error handler activation."""
    audit_logger_instance.log_security_event(
        AuditEventType.SECURITY_ERROR_HANDLER_TRIGGERED,
        f"Error handler triggered: {error_type}",
        request,
        AuditEventSeverity.HIGH,
        {"error_type": error_type, "error_message": error_message},
    )


def log_api_request(request: Request, response_status: int, processing_time: float) -> None:
    """Log API request/response."""
    audit_logger_instance.log_api_event(request, response_status, processing_time)
