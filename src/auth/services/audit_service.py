"""Enhanced security audit service for compliance reporting and data retention.

This module provides comprehensive audit trail functionality with compliance-ready
reporting, event archival, and automated retention policy enforcement.
"""

import csv
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from io import StringIO
from typing import Any

from pydantic import BaseModel, Field

from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
from src.auth.models import SecurityEvent, SecurityEventType

from .security_logger import SecurityLogger

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats for audit reports."""

    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class RetentionPolicy(BaseModel):
    """Data retention policy configuration."""

    event_types: list[SecurityEventType] = Field(description="Event types covered by this policy")
    retention_days: int = Field(description="Number of days to retain events")
    description: str = Field(description="Human-readable description of the policy")


class AuditReportRequest(BaseModel):
    """Request model for generating audit reports."""

    start_date: datetime = Field(description="Start date for report period")
    end_date: datetime = Field(description="End date for report period")
    user_id: str | None = Field(None, description="Filter by specific user ID")
    event_types: list[SecurityEventType] | None = Field(None, description="Filter by event types")
    severity_levels: list[str] | None = Field(None, description="Filter by severity levels")
    format: ExportFormat = Field(ExportFormat.CSV, description="Export format")
    include_metadata: bool = Field(True, description="Include full metadata in export")


class AuditStatistics(BaseModel):
    """Audit report statistics summary."""

    total_events: int = Field(description="Total events in report period")
    events_by_type: dict[str, int] = Field(description="Event count by type")
    events_by_severity: dict[str, int] = Field(description="Event count by severity")
    unique_users: int = Field(description="Number of unique users")
    unique_ip_addresses: int = Field(description="Number of unique IP addresses")
    report_period: str = Field(description="Human-readable report period")


class ComplianceReport(BaseModel):
    """Complete compliance audit report."""

    report_id: str = Field(description="Unique report identifier")
    generated_at: datetime = Field(description="Report generation timestamp")
    report_request: AuditReportRequest = Field(description="Original report request")
    statistics: AuditStatistics = Field(description="Report statistics summary")
    events: list[SecurityEvent] = Field(description="Security events data")


class AuditService:
    """Compliance reporting and data retention service.

    This service provides comprehensive audit trail functionality including:
    - Compliance-ready report generation in CSV and JSON formats
    - Automated data retention policy enforcement
    - Forensic analysis capabilities
    - Performance optimized for large datasets
    """

    def __init__(
        self, db: SecurityEventsPostgreSQL | None = None, security_logger: SecurityLogger | None = None,
    ) -> None:
        """Initialize audit service.

        Args:
            db: Security events database instance
            security_logger: Security logger for audit events
        """
        self.db = db or SecurityEventsPostgreSQL()
        self.security_logger = security_logger or SecurityLogger()

        # Default retention policies based on plan requirements
        self.retention_policies = [
            RetentionPolicy(
                event_types=[
                    SecurityEventType.LOGIN_FAILURE,
                    SecurityEventType.LOGIN_SUCCESS,
                    SecurityEventType.LOGOUT,
                    SecurityEventType.PASSWORD_CHANGED,
                    SecurityEventType.SESSION_EXPIRED,
                ],
                retention_days=90,
                description="Standard security events - 90 days retention",
            ),
            RetentionPolicy(
                event_types=[
                    SecurityEventType.ACCOUNT_LOCKOUT,
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    SecurityEventType.BRUTE_FORCE_ATTEMPT,
                    SecurityEventType.SECURITY_ALERT,
                    SecurityEventType.RATE_LIMIT_EXCEEDED,
                ],
                retention_days=365,
                description="Critical security events - 1 year retention",
            ),
        ]

        # Performance tracking
        self._report_generation_times: list[float] = []

    async def initialize(self) -> None:
        """Initialize the audit service and dependencies.

        This method ensures all dependencies are initialized and performance tracking is ready.
        It's idempotent and can be called multiple times safely.
        """
        # Initialize database
        if hasattr(self.db, "initialize"):
            await self.db.initialize()

        # Initialize security logger
        if hasattr(self.security_logger, "initialize"):
            await self.security_logger.initialize()

    async def generate_compliance_report(self, request: AuditReportRequest) -> ComplianceReport:
        """Generate comprehensive compliance audit report.

        Args:
            request: Audit report request parameters

        Returns:
            Complete compliance report with events and statistics

        Raises:
            ValueError: If request parameters are invalid
        """
        start_time = datetime.now()

        try:
            # Validate request
            if request.end_date <= request.start_date:
                raise ValueError("End date must be after start date")

            if (request.end_date - request.start_date).days > 365:
                logger.warning("Report period exceeds 1 year, may impact performance")

            # Generate unique report ID with microseconds to ensure uniqueness
            now = datetime.now()
            report_id = f"audit_{int(now.timestamp())}_{now.microsecond}_{hash(str(request))}"

            # Fetch events from database with filters
            events = await self._fetch_filtered_events(request)

            # Generate statistics
            statistics = self._generate_statistics(events, request)

            # Create compliance report
            report = ComplianceReport(
                report_id=report_id,
                generated_at=datetime.now(),
                report_request=request,
                statistics=statistics,
                events=events,
            )

            # Track performance
            generation_time = (datetime.now() - start_time).total_seconds()
            self._report_generation_times.append(generation_time)

            # Log audit report generation
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.AUDIT_LOG_GENERATED,
                user_id=request.user_id or "system",
                metadata={
                    "report_id": report_id,
                    "events_count": len(events),
                    "generation_time_seconds": generation_time,
                    "report_period_days": (request.end_date - request.start_date).days,
                },
            )

            logger.info(f"Generated compliance report {report_id} with {len(events)} events in {generation_time:.2f}s")

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                metadata={"error": str(e), "operation": "generate_compliance_report"},
            )
            raise

    async def export_report_csv(self, report: ComplianceReport) -> str:
        """Export compliance report as CSV format.

        Args:
            report: Compliance report to export

        Returns:
            CSV-formatted string
        """
        output = StringIO()
        fieldnames = [
            "timestamp",
            "event_type",
            "user_id",
            "ip_address",
            "user_agent",
            "severity",
            "session_id",
            "risk_score",
        ]

        if report.report_request.include_metadata:
            fieldnames.append("details")

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for event in report.events:
            row = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value if hasattr(event.event_type, "value") else event.event_type,
                "user_id": event.user_id or "",
                "ip_address": event.ip_address or "",
                "user_agent": event.user_agent or "",
                "severity": event.severity.value if hasattr(event.severity, "value") else event.severity,
                "session_id": event.session_id or "",
                "risk_score": event.risk_score,
            }

            if report.report_request.include_metadata:
                row["details"] = json.dumps(event.details) if event.details else ""

            writer.writerow(row)

        return output.getvalue()

    async def export_report_json(self, report: ComplianceReport) -> str:
        """Export compliance report as JSON format.

        Args:
            report: Compliance report to export

        Returns:
            JSON-formatted string
        """
        # Create serializable report data
        report_data = {
            "report_metadata": {
                "report_id": report.report_id,
                "generated_at": report.generated_at.isoformat(),
                "statistics": report.statistics.model_dump(),
                "request_parameters": {
                    "start_date": report.report_request.start_date.isoformat(),
                    "end_date": report.report_request.end_date.isoformat(),
                    "user_id": report.report_request.user_id,
                    "event_types": (
                        [et.value for et in report.report_request.event_types]
                        if report.report_request.event_types
                        else None
                    ),
                    "severity_levels": report.report_request.severity_levels,
                    "include_metadata": report.report_request.include_metadata,
                },
            },
            "events": [],
        }

        # Convert events to serializable format
        for event in report.events:
            event_data = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value if hasattr(event.event_type, "value") else event.event_type,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "severity": event.severity.value if hasattr(event.severity, "value") else event.severity,
                "session_id": event.session_id,
                "risk_score": event.risk_score,
            }

            if report.report_request.include_metadata:
                event_data["details"] = event.details

            report_data["events"].append(event_data)

        return json.dumps(report_data, indent=2, ensure_ascii=False)

    async def enforce_retention_policies(self) -> dict[str, int]:
        """Enforce data retention policies by cleaning up expired events.

        Returns:
            Dictionary with cleanup statistics by policy

        Raises:
            Exception: If cleanup operation fails
        """
        start_time = datetime.now()
        cleanup_stats = {}
        total_deleted = 0

        try:
            for policy in self.retention_policies:
                # Calculate cutoff date for this policy
                cutoff_date = datetime.now() - timedelta(days=policy.retention_days)

                # Delete expired events for this policy's event types
                deleted_count = await self.db.cleanup_expired_events(
                    cutoff_date=cutoff_date,
                    event_types=policy.event_types,
                )

                cleanup_stats[policy.description] = deleted_count
                total_deleted += deleted_count

                logger.info(f"Retention policy '{policy.description}': deleted {deleted_count} expired events")

            # Vacuum database for performance
            if total_deleted > 0:
                await self.db.vacuum_database()

            cleanup_time = (datetime.now() - start_time).total_seconds()

            # Log retention enforcement
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_MAINTENANCE,
                metadata={
                    "operation": "retention_policy_enforcement",
                    "total_events_deleted": total_deleted,
                    "cleanup_time_seconds": cleanup_time,
                    "policies_applied": len(self.retention_policies),
                },
            )

            logger.info(
                f"Retention policy enforcement completed: {total_deleted} events deleted in {cleanup_time:.2f}s",
            )

            return cleanup_stats

        except Exception as e:
            logger.error(f"Failed to enforce retention policies: {e}")
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                metadata={"error": str(e), "operation": "enforce_retention_policies"},
            )
            raise

    async def get_audit_statistics(self, start_date: datetime, end_date: datetime) -> AuditStatistics:
        """Get audit statistics for specified time period.

        Args:
            start_date: Start of statistics period
            end_date: End of statistics period

        Returns:
            Audit statistics summary
        """
        try:
            events = await self.db.get_events_by_date_range(start_date, end_date)

            return self._generate_statistics(events, AuditReportRequest(start_date=start_date, end_date=end_date))

        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            raise

    async def get_security_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: list[SecurityEventType] | None = None,
        user_id: str | None = None,
    ) -> list[SecurityEvent]:
        """Get security events for specified time period.

        Args:
            start_date: Start of events period
            end_date: End of events period
            event_types: Filter by specific event types
            user_id: Filter by specific user ID

        Returns:
            List of security events
        """
        try:
            # Use existing database functionality
            events = await self.db.get_events_by_date_range(start_date, end_date)

            # Apply additional filters if provided
            if user_id:
                events = [e for e in events if e.user_id == user_id]

            if event_types:
                event_type_values = [et.value for et in event_types]
                events = [
                    e
                    for e in events
                    if (e.event_type.value if hasattr(e.event_type, "value") else e.event_type) in event_type_values
                ]

            return events

        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            raise

    async def schedule_retention_cleanup(self) -> None:
        """Schedule automated retention policy cleanup.

        This method should be called periodically (e.g., daily) to enforce
        retention policies automatically.
        """
        try:
            await self.enforce_retention_policies()

            # Schedule next cleanup (this would typically be handled by a job scheduler)
            logger.info("Retention cleanup completed successfully")

        except Exception as e:
            logger.error(f"Scheduled retention cleanup failed: {e}")
            # In a real implementation, this would trigger alerts
            raise

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get audit service performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        if not self._report_generation_times:
            return {
                "reports_generated": 0,
                "average_generation_time": 0.0,
                "max_generation_time": 0.0,
                "min_generation_time": 0.0,
                "total_retention_policies": len(self.retention_policies),
            }

        return {
            "reports_generated": len(self._report_generation_times),
            "average_generation_time": sum(self._report_generation_times) / len(self._report_generation_times),
            "max_generation_time": max(self._report_generation_times),
            "min_generation_time": min(self._report_generation_times),
            "total_retention_policies": len(self.retention_policies),
        }

    async def _fetch_filtered_events(self, request: AuditReportRequest) -> list[SecurityEvent]:
        """Fetch events from database applying request filters.

        Args:
            request: Audit report request with filters

        Returns:
            Filtered list of security events
        """
        # Start with date range filter
        events = await self.db.get_events_by_date_range(request.start_date, request.end_date)

        # Apply additional filters
        if request.user_id:
            events = [e for e in events if e.user_id == request.user_id]

        if request.event_types:
            event_type_values = [et.value for et in request.event_types]
            # Handle both enum objects and string values (due to use_enum_values=True)
            events = [
                e
                for e in events
                if (e.event_type.value if hasattr(e.event_type, "value") else e.event_type) in event_type_values
            ]

        if request.severity_levels:
            events = [e for e in events if e.severity in request.severity_levels]

        return events

    def _generate_statistics(self, events: list[SecurityEvent], request: AuditReportRequest) -> AuditStatistics:
        """Generate statistics summary for events.

        Args:
            events: List of security events
            request: Original audit request

        Returns:
            Statistics summary
        """
        # Count events by type
        events_by_type = {}
        for event in events:
            # Handle both enum objects and string values
            event_type = event.event_type.value if hasattr(event.event_type, "value") else event.event_type
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

        # Count events by severity
        events_by_severity = {}
        for event in events:
            severity = event.severity
            events_by_severity[severity] = events_by_severity.get(severity, 0) + 1

        # Count unique users and IPs
        unique_users = len({e.user_id for e in events if e.user_id})
        unique_ips = len({e.ip_address for e in events if e.ip_address})

        # Generate human-readable period
        period_days = (request.end_date - request.start_date).days
        report_period = (
            f"{request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')} ({period_days} days)"
        )

        return AuditStatistics(
            total_events=len(events),
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            unique_users=unique_users,
            unique_ip_addresses=unique_ips,
            report_period=report_period,
        )
