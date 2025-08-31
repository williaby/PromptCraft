"""Security logger implementation for AUTH-4 Enhanced Security Event Logging."""

import asyncio
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from .audit_service import AuditService

from sqlalchemy import desc, select, text

from src.database.connection import get_database_manager
from src.database.models import SecurityEventLogger

from .models import (
    EventSeverity,
    EventType,
    SecurityEventCreate,
    SecurityEventResponse,
)

logger = logging.getLogger(__name__)


def sanitize_event_details(details: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize security event details to prevent injection attacks.

    Args:
        details: Raw event details dictionary

    Returns:
        Sanitized details dictionary safe for database storage
    """
    if not details:
        return {}

    sanitized = {}

    for key, value in details.items():
        # Sanitize key - only allow alphanumeric and underscores
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "", str(key)[:50])
        if not clean_key:
            continue

        # Sanitize value based on type
        if isinstance(value, str):
            # Remove potential SQL injection characters and limit length
            clean_value = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value[:1000])
            # Remove potential script tags for XSS prevention
            clean_value = re.sub(r"<[^>]*>", "", clean_value)
            sanitized[clean_key] = clean_value
        elif isinstance(value, (int, float, bool)):
            sanitized[clean_key] = value
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries (max depth 3)
            try:
                json_str = json.dumps(value)[:2000]  # Limit JSON size
                sanitized[clean_key] = json.loads(json_str)
            except (TypeError, ValueError, json.JSONDecodeError):
                sanitized[clean_key] = str(value)[:500]
        elif isinstance(value, list):
            # Sanitize lists (max 10 items)
            clean_list = []
            for item in value[:10]:
                if isinstance(item, str):
                    clean_item = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", str(item)[:200])
                    clean_list.append(clean_item)
                elif isinstance(item, (int, float, bool)):
                    clean_list.append(item)
                else:
                    clean_list.append(str(item)[:200])
            sanitized[clean_key] = clean_list
        else:
            # Convert unknown types to string with length limit
            sanitized[clean_key] = str(value)[:500]

    # Limit total number of keys
    if len(sanitized) > 20:
        logger.warning("Security event details truncated - too many keys")
        sanitized = dict(list(sanitized.items())[:20])

    return sanitized


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded for security logging."""

    def __init__(self, message: str, retry_after: int) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message)
        self.retry_after = retry_after


class SecurityLogger:
    """Stateless security event logger with direct PostgreSQL persistence and rate limiting."""

    def __init__(self, rate_limit: int = 100, rate_window: int = 60) -> None:
        """Initialize security logger with rate limiting.

        Args:
            rate_limit: Maximum events per rate window
            rate_window: Rate limiting window in seconds
        """
        self._db_manager = get_database_manager()
        self._is_initialized = False

        # Rate limiting configuration
        self._rate_limit = rate_limit
        self._rate_window = rate_window
        self._rate_tracker: dict[str, list[datetime]] = {}
        self._rate_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the security logger and database."""
        if self._is_initialized:
            return

        # Initialize database manager
        await self._db_manager.initialize()

        self._is_initialized = True
        logger.info(
            "SecurityLogger initialized with stateless PostgreSQL backend (rate limit: %d/%ds)",
            self._rate_limit,
            self._rate_window,
        )

    async def _check_rate_limit(self, key: str = "global") -> None:
        """Check if rate limit is exceeded.

        Args:
            key: Rate limiting key (e.g., IP address, user ID)

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        async with self._rate_lock:
            current_time = datetime.now(UTC)

            # Initialize tracker for this key if needed
            if key not in self._rate_tracker:
                self._rate_tracker[key] = []

            # Remove old entries outside the time window
            cutoff_time = current_time - timedelta(seconds=self._rate_window)
            self._rate_tracker[key] = [timestamp for timestamp in self._rate_tracker[key] if timestamp > cutoff_time]

            # Check if rate limit would be exceeded
            if len(self._rate_tracker[key]) >= self._rate_limit:
                oldest_time = min(self._rate_tracker[key])
                retry_after = int((oldest_time + timedelta(seconds=self._rate_window) - current_time).total_seconds())
                raise RateLimitExceededError(
                    f"Rate limit exceeded for key '{key}': {self._rate_limit} events per {self._rate_window}s",
                    retry_after=max(1, retry_after),
                )

            # Add current timestamp
            self._rate_tracker[key].append(current_time)

    def _get_rate_limit_key(self, event: SecurityEventCreate) -> str:
        """Generate rate limiting key based on event characteristics.

        Args:
            event: Security event to generate key for

        Returns:
            Rate limiting key
        """
        # Use IP address if available, fallback to user ID, then global
        if event.ip_address:
            return f"ip:{event.ip_address}"
        if event.user_id:
            return f"user:{event.user_id}"
        return "global"

    async def log_security_event(
        self,
        event: SecurityEventCreate | None = None,
        event_type: EventType | None = None,
        severity: EventSeverity | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
        risk_score: int = 0,
    ) -> SecurityEventResponse:
        """Log a security event directly to PostgreSQL.

        Args:
            event: Complete event object (if provided, other params are ignored)
            event_type: Type of security event
            severity: Event severity level
            user_id: Optional user identifier
            ip_address: Optional IP address
            user_agent: Optional user agent string
            session_id: Optional session identifier
            details: Optional additional details
            risk_score: Risk score (0-100)

        Returns:
            SecurityEventResponse with generated ID and timestamp
        """
        if event:
            # Use provided event directly
            return await self._log_event_internal(event)
        # Create event from parameters
        return await self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=details,
            risk_score=risk_score,
        )

    async def _log_event_internal(self, event: SecurityEventCreate) -> SecurityEventResponse:
        """Internal method to log an event directly to database with rate limiting."""
        if not self._is_initialized:
            await self.initialize()

        # Apply rate limiting
        rate_key = self._get_rate_limit_key(event)
        try:
            await self._check_rate_limit(rate_key)
        except RateLimitExceededError as e:
            logger.warning("Security event rate limit exceeded: %s", e)
            # For rate limit violations, still create a response but mark as rate limited
            event_id = uuid4()
            timestamp = datetime.now(UTC)
            return SecurityEventResponse(
                id=event_id,
                event_type="RATE_LIMITED",
                severity="WARNING",
                user_id=event.user_id,
                ip_address=event.ip_address,
                timestamp=timestamp,
                risk_score=10,
                details={
                    "original_event_type": str(event.event_type),
                    "rate_limit_key": rate_key,
                    "retry_after": e.retry_after,
                    "message": str(e),
                },
            )

        # Generate unique ID and timestamp
        event_id = uuid4()
        timestamp = datetime.now(UTC)

        # Insert using SQLAlchemy ORM
        async with self._db_manager.get_session() as session:
            db_event = SecurityEventLogger(
                id=event_id,
                event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                severity=event.severity.value if hasattr(event.severity, "value") else str(event.severity),
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                session_id=event.session_id,
                details=sanitize_event_details(event.details),
                risk_score=event.risk_score,
                timestamp=timestamp,
            )

            session.add(db_event)
            await session.commit()

        # Return response
        return SecurityEventResponse(
            id=event_id,
            event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
            severity=event.severity.value if hasattr(event.severity, "value") else str(event.severity),
            user_id=event.user_id,
            ip_address=event.ip_address,
            timestamp=timestamp,
            risk_score=event.risk_score,
            details=sanitize_event_details(event.details),
        )

    async def log_event(
        self,
        event_type: EventType,
        severity: EventSeverity,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
        risk_score: int = 0,
    ) -> SecurityEventResponse:
        """Log a security event directly to PostgreSQL.

        Args:
            event_type: Type of security event
            severity: Event severity level
            user_id: Optional user identifier
            ip_address: Optional IP address
            user_agent: Optional user agent string
            session_id: Optional session identifier
            details: Optional additional details
            risk_score: Risk score (0-100)

        Returns:
            SecurityEventResponse with generated ID and timestamp
        """
        if not self._is_initialized:
            await self.initialize()

        event = SecurityEventCreate(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=sanitize_event_details(details),
            risk_score=risk_score,
        )

        return await self._log_event_internal(event)

    async def get_recent_events(
        self,
        limit: int = 100,
        severity: EventSeverity | None = None,
        event_type: EventType | None = None,
        hours_back: int = 24,
    ) -> list[SecurityEventResponse]:
        """Get recent security events from PostgreSQL.

        Args:
            limit: Maximum number of events to return
            severity: Optional severity filter
            event_type: Optional event type filter
            hours_back: Number of hours to look back

        Returns:
            List of recent security events
        """
        if not self._is_initialized:
            await self.initialize()

        # Calculate cutoff time
        cutoff = datetime.now(UTC) - timedelta(hours=hours_back)

        # Build query using SQLAlchemy ORM
        query = select(SecurityEventLogger).where(SecurityEventLogger.timestamp >= cutoff)

        if severity:
            query = query.where(SecurityEventLogger.severity == severity.value)

        if event_type:
            query = query.where(SecurityEventLogger.event_type == event_type.value)

        query = query.order_by(desc(SecurityEventLogger.timestamp)).limit(limit)

        async with self._db_manager.get_session() as session:
            result = await session.execute(query)
            rows = result.fetchall()

            return [
                SecurityEventResponse(
                    id=row.id,
                    event_type=row.event_type,
                    severity=row.severity,
                    user_id=row.user_id,
                    ip_address=str(row.ip_address) if row.ip_address else None,
                    timestamp=row.timestamp,
                    risk_score=row.risk_score,
                    details=row.details or {},
                )
                for row in rows
            ]

    async def get_events_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        event_type: EventType | None = None,
        severity: EventSeverity | None = None,
    ) -> list[SecurityEventResponse]:
        """Get security events for a specific user from PostgreSQL.

        Args:
            user_id: User identifier
            limit: Maximum number of events to return
            offset: Number of events to skip
            event_type: Optional event type filter
            severity: Optional severity filter

        Returns:
            List of user's security events
        """
        if not self._is_initialized:
            await self.initialize()

        # Build query using SQLAlchemy ORM
        query = select(SecurityEventLogger).where(SecurityEventLogger.user_id == user_id)

        if event_type:
            query = query.where(SecurityEventLogger.event_type == event_type.value)

        if severity:
            query = query.where(SecurityEventLogger.severity == severity.value)

        query = query.order_by(desc(SecurityEventLogger.timestamp)).limit(limit).offset(offset)

        async with self._db_manager.get_session() as session:
            result = await session.execute(query)
            rows = result.fetchall()

            return [
                SecurityEventResponse(
                    id=row.id,
                    event_type=row.event_type,
                    severity=row.severity,
                    user_id=row.user_id,
                    ip_address=str(row.ip_address) if row.ip_address else None,
                    timestamp=row.timestamp,
                    risk_score=row.risk_score,
                    details=row.details or {},
                )
                for row in rows
            ]

    async def log_security_events_batch(
        self,
        events: list[SecurityEventCreate],
        audit_service: "AuditService | None" = None,
    ) -> list[SecurityEventResponse]:
        """Log multiple security events in a single transaction for performance.

        Args:
            events: List of security events to log
            audit_service: Optional audit service for compliance logging

        Returns:
            List of SecurityEventResponse objects with generated IDs and timestamps
        """
        if not self._is_initialized:
            await self.initialize()

        if not events:
            return []

        responses = []
        timestamp = datetime.now(UTC)

        async with self._db_manager.get_session() as session:
            # Create all events in memory first
            db_events = []
            for event in events:
                event_id = uuid4()
                db_event = SecurityEventLogger(
                    id=event_id,
                    event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                    severity=event.severity.value if hasattr(event.severity, "value") else str(event.severity),
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    session_id=event.session_id,
                    details=sanitize_event_details(event.details),
                    risk_score=event.risk_score,
                    timestamp=timestamp,
                )
                db_events.append(db_event)

                # Create response object
                response = SecurityEventResponse(
                    id=event_id,
                    event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                    severity=event.severity.value if hasattr(event.severity, "value") else str(event.severity),
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    timestamp=timestamp,
                    risk_score=event.risk_score,
                    details=sanitize_event_details(event.details),
                )
                responses.append(response)

            # Add all events to session
            session.add_all(db_events)
            # Single commit for all events
            await session.commit()

        # Log to audit service if provided (for compliance)
        if audit_service:
            for response in responses:
                await audit_service.log_security_event(response)

        return responses

    async def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """Clean up old security events from PostgreSQL.

        Args:
            days_to_keep: Number of days to retain events

        Returns:
            Number of events deleted
        """
        if not self._is_initialized:
            await self.initialize()

        cutoff = datetime.now(UTC) - timedelta(days=days_to_keep)

        async with self._db_manager.get_session() as session:
            query = text("DELETE FROM security_events WHERE timestamp < :cutoff RETURNING id")
            result = await session.execute(query, {"cutoff": cutoff})
            deleted_rows = result.fetchall()
            await session.commit()

            return len(deleted_rows)

    async def close(self) -> None:
        """Close the security logger."""
        # No background tasks to cancel in stateless implementation
        await self._db_manager.close()
        self._is_initialized = False

    async def __aenter__(self) -> "SecurityLogger":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool:
        """Async context manager exit."""
        await self.close()
        return False
