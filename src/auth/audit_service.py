"""Audit service for comprehensive security event tracking and compliance."""

import asyncio
import contextlib
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.utils.datetime_compat import UTC

from .models import SecurityEventResponse

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of audit actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"


class AuditEntry:
    """Audit log entry."""

    def __init__(
        self,
        action: AuditAction,
        resource: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        result: str = "success",
    ) -> None:
        """Initialize audit entry.

        Args:
            action: Type of action performed
            resource: Resource affected
            user_id: User who performed action
            ip_address: IP address of user
            details: Additional details
            result: Result of action (success/failure)
        """
        self.timestamp = datetime.now(UTC)
        self.action = action
        self.resource = resource
        self.user_id = user_id
        self.ip_address = ip_address
        self.details = details or {}
        self.result = result
        self.id = f"{self.timestamp.timestamp()}_{action.value}_{resource}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "resource": self.resource,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "result": self.result,
        }


class AuditService:
    """Comprehensive audit service for security and compliance."""

    def __init__(
        self,
        audit_dir: Path | None = None,
        retention_days: int = 90,
        max_entries_memory: int = 10000,
    ) -> None:
        """Initialize audit service.

        Args:
            audit_dir: Directory for audit logs
            retention_days: Days to retain audit logs
            max_entries_memory: Maximum entries to keep in memory
        """
        self.audit_dir = audit_dir or Path("audit_logs")
        self.retention_days = retention_days
        self.max_entries_memory = max_entries_memory

        # Audit storage
        self._audit_log: list[AuditEntry] = []
        self._audit_index: dict[str, list[AuditEntry]] = {}  # By user
        self._resource_index: dict[str, list[AuditEntry]] = {}  # By resource

        # Compliance tracking
        self._compliance_rules: dict[str, Any] = self._init_compliance_rules()
        self._compliance_violations: list[dict[str, Any]] = []

        # Background tasks
        self._persistence_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None
        self._is_initialized = False

    def _init_compliance_rules(self) -> dict[str, Any]:
        """Initialize compliance rules."""
        return {
            "max_failed_logins": 5,
            "session_timeout": 3600,  # 1 hour
            "password_expiry": 90,  # days
            "require_mfa": True,
            "data_retention": 365,  # days
            "audit_all_admin_actions": True,
            "gdpr_compliant": True,
            "sox_compliant": False,
        }

    async def initialize(self) -> None:
        """Initialize the audit service."""
        if self._is_initialized:
            return

        # Create audit directory
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Load recent audit logs
        await self._load_recent_logs()

        # Start background tasks
        self._persistence_task = asyncio.create_task(self._persist_logs())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_logs())

        self._is_initialized = True
        logger.info("AuditService initialized with retention=%d days", self.retention_days)

    async def log_action(
        self,
        action: AuditAction,
        resource: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        result: str = "success",
    ) -> AuditEntry:
        """Log an audit action.

        Args:
            action: Type of action
            resource: Resource affected
            user_id: User performing action
            ip_address: User's IP address
            details: Additional details
            result: Action result

        Returns:
            Created audit entry
        """
        if not self._is_initialized:
            await self.initialize()

        # Create entry
        entry = AuditEntry(
            action=action,
            resource=resource,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            result=result,
        )

        # Store in memory
        self._audit_log.append(entry)

        # Update indexes
        if user_id:
            if user_id not in self._audit_index:
                self._audit_index[user_id] = []
            self._audit_index[user_id].append(entry)

        if resource not in self._resource_index:
            self._resource_index[resource] = []
        self._resource_index[resource].append(entry)

        # Check compliance
        await self._check_compliance(entry)

        # Trim if too many entries
        if len(self._audit_log) > self.max_entries_memory:
            self._audit_log = self._audit_log[-self.max_entries_memory :]

        return entry

    async def log_security_event(self, event: SecurityEventResponse) -> AuditEntry:
        """Log a security event to audit trail.

        Args:
            event: Security event to log

        Returns:
            Created audit entry
        """
        details = {
            "event_id": str(event.id),
            "event_type": event.event_type,
            "severity": event.severity,
            "risk_score": event.risk_score,
            **event.details,
        }

        return await self.log_action(
            action=AuditAction.SECURITY_EVENT,
            resource=f"security/{event.event_type}",
            user_id=event.user_id,
            ip_address=event.ip_address,
            details=details,
            result="logged",
        )

    async def _check_compliance(self, entry: AuditEntry) -> None:
        """Check entry against compliance rules.

        Args:
            entry: Audit entry to check
        """
        violations = []

        # Check failed login attempts
        if entry.action == AuditAction.LOGIN and entry.result == "failure":
            if entry.user_id:
                recent_failures = [
                    e
                    for e in self._audit_index.get(entry.user_id, [])
                    if e.action == AuditAction.LOGIN
                    and e.result == "failure"
                    and e.timestamp > datetime.now(UTC) - timedelta(hours=1)
                ]

                if len(recent_failures) > self._compliance_rules["max_failed_logins"]:
                    violations.append(
                        {
                            "rule": "max_failed_logins",
                            "user_id": entry.user_id,
                            "count": len(recent_failures),
                            "timestamp": entry.timestamp,
                        },
                    )

        # Check admin actions
        if self._compliance_rules["audit_all_admin_actions"]:
            if entry.details.get("is_admin") and entry.result == "failure":
                violations.append(
                    {
                        "rule": "admin_action_failure",
                        "action": entry.action.value,
                        "resource": entry.resource,
                        "timestamp": entry.timestamp,
                    },
                )

        # Store violations
        self._compliance_violations.extend(violations)

    async def get_user_audit_trail(
        self,
        user_id: str,
        limit: int = 100,
        action: AuditAction | None = None,
    ) -> list[AuditEntry]:
        """Get audit trail for a user.

        Args:
            user_id: User identifier
            limit: Maximum entries to return
            action: Filter by action type

        Returns:
            List of audit entries
        """
        entries = self._audit_index.get(user_id, [])

        if action:
            entries = [e for e in entries if e.action == action]

        # Sort by timestamp desc and limit
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    async def get_resource_audit_trail(
        self,
        resource: str,
        limit: int = 100,
        action: AuditAction | None = None,
    ) -> list[AuditEntry]:
        """Get audit trail for a resource.

        Args:
            resource: Resource identifier
            limit: Maximum entries to return
            action: Filter by action type

        Returns:
            List of audit entries
        """
        entries = self._resource_index.get(resource, [])

        if action:
            entries = [e for e in entries if e.action == action]

        # Sort by timestamp desc and limit
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    async def search_audit_log(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: str | None = None,
        action: AuditAction | None = None,
        resource: str | None = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Search audit log with filters.

        Args:
            start_date: Start of date range
            end_date: End of date range
            user_id: Filter by user
            action: Filter by action
            resource: Filter by resource
            limit: Maximum results

        Returns:
            List of matching audit entries
        """
        results = self._audit_log

        # Apply filters
        if start_date:
            results = [e for e in results if e.timestamp >= start_date]

        if end_date:
            results = [e for e in results if e.timestamp <= end_date]

        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if action:
            results = [e for e in results if e.action == action]

        if resource:
            results = [e for e in results if e.resource == resource]

        # Sort and limit
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    async def get_compliance_report(self) -> dict[str, Any]:
        """Generate compliance report.

        Returns:
            Compliance report dictionary
        """
        return {
            "rules": self._compliance_rules,
            "violations": len(self._compliance_violations),
            "recent_violations": self._compliance_violations[-10:],
            "audit_entries": len(self._audit_log),
            "users_tracked": len(self._audit_index),
            "resources_tracked": len(self._resource_index),
            "retention_days": self.retention_days,
            "gdpr_compliant": self._compliance_rules["gdpr_compliant"],
            "sox_compliant": self._compliance_rules["sox_compliant"],
        }

    async def _persist_logs(self) -> None:
        """Background task to persist audit logs to disk."""
        while True:
            try:
                await asyncio.sleep(60)  # Persist every minute

                # Get current date for file name
                now = datetime.now(UTC)
                filename = self.audit_dir / f"audit_{now.strftime('%Y%m%d')}.jsonl"

                # Write new entries
                entries_to_write = self._audit_log[-100:]  # Last 100 entries

                with filename.open("a") as f:
                    for entry in entries_to_write:
                        f.write(json.dumps(entry.to_dict()) + "\n")

                logger.debug("Persisted %d audit entries to %s", len(entries_to_write), filename)

            except asyncio.CancelledError:
                # Final persist before shutdown
                try:
                    filename = self.audit_dir / f"audit_{datetime.now(UTC).strftime('%Y%m%d')}.jsonl"
                    with filename.open("a") as f:
                        for entry in self._audit_log:
                            f.write(json.dumps(entry.to_dict()) + "\n")
                except Exception as e:
                    logger.error("Final persist error: %s", e)
                break
            except Exception as e:
                logger.error("Audit persistence error: %s", e)

    async def _cleanup_old_logs(self) -> None:
        """Background task to clean up old audit logs."""
        while True:
            try:
                await asyncio.sleep(3600)  # Check hourly

                # Calculate cutoff date
                cutoff = datetime.now(UTC) - timedelta(days=self.retention_days)

                # Remove old files
                for file in self.audit_dir.glob("audit_*.jsonl"):
                    try:
                        # Parse date from filename
                        date_str = file.stem.replace("audit_", "")
                        file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=UTC)

                        if file_date < cutoff:
                            file.unlink()
                            logger.info("Removed old audit file: %s", file)
                    except Exception as e:
                        logger.error("Error processing file %s: %s", file, e)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Audit cleanup error: %s", e)

    async def _load_recent_logs(self) -> None:
        """Load recent audit logs from disk."""
        try:
            # Load today's logs
            today = datetime.now(UTC)
            filename = self.audit_dir / f"audit_{today.strftime('%Y%m%d')}.jsonl"

            if filename.exists():
                with filename.open() as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            # Reconstruct audit entry (simplified)
                            # In production, would properly deserialize
                            logger.debug("Loaded audit entry: %s", data["id"])
                        except Exception as e:
                            logger.error("Error loading audit entry: %s", e)
        except Exception as e:
            logger.error("Error loading recent logs: %s", e)

    async def get_security_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[SecurityEventResponse]:
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
            # Search audit log for security events in date range
            audit_entries = await self.search_audit_log(
                start_date=start_date,
                end_date=end_date,
                action=AuditAction.SECURITY_EVENT,
                user_id=user_id,
            )

            # Convert audit entries to SecurityEventResponse objects
            security_events = []
            for entry in audit_entries:
                # Extract security event details from audit entry
                event_id = entry.details.get("event_id", entry.id)
                event_type = entry.details.get("event_type", "unknown")
                severity = entry.details.get("severity", "info")
                risk_score = entry.details.get("risk_score", 0)

                # Filter by event types if specified
                if event_types and event_type not in event_types:
                    continue

                # Create SecurityEventResponse object
                security_event = SecurityEventResponse(
                    id=event_id,
                    event_type=event_type,
                    severity=severity,
                    user_id=entry.user_id,
                    ip_address=entry.ip_address,
                    risk_score=risk_score,
                    timestamp=entry.timestamp,
                    details=entry.details,
                )
                security_events.append(security_event)

            return security_events

        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            raise

    async def close(self) -> None:
        """Close the audit service."""
        if self._persistence_task:
            self._persistence_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._persistence_task

        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        self._is_initialized = False
