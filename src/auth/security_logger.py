"""Security logger implementation for AUTH-4 Enhanced Security Event Logging."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from src.database.connection import get_database_manager
from src.database.models import SecurityEventLogger

from .models import (
    EventSeverity,
    EventType,
    SecurityEventCreate,
    SecurityEventResponse,
)

logger = logging.getLogger(__name__)


class SecurityLogger:
    """Stateless security event logger with direct PostgreSQL persistence."""

    def __init__(self) -> None:
        """Initialize security logger."""
        self._db_manager = get_database_manager()
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the security logger and database."""
        if self._is_initialized:
            return

        # Initialize database manager
        await self._db_manager.initialize()

        self._is_initialized = True
        logger.info("SecurityLogger initialized with stateless PostgreSQL backend")

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
        """Internal method to log an event directly to database."""
        if not self._is_initialized:
            await self.initialize()

        # Generate unique ID and timestamp
        event_id = uuid4()
        timestamp = datetime.now(timezone.utc)

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
                details=event.details or {},
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
            details=event.details or {},
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
            details=details or {},
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
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Build query with filters
        conditions = ["timestamp >= :cutoff"]
        params = {"cutoff": cutoff}

        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity.value

        if event_type:
            conditions.append("event_type = :event_type")
            params["event_type"] = event_type.value

        query = text(
            f"""
            SELECT id, event_type, severity, user_id, ip_address,
                   user_agent, session_id, details, risk_score, timestamp
            FROM security_events
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT :limit
        """,
        )
        params["limit"] = limit

        async with self._db_manager.get_session() as session:
            result = await session.execute(query, params)
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

        # Build query with filters
        conditions = ["user_id = :user_id"]
        params = {"user_id": user_id}

        if event_type:
            conditions.append("event_type = :event_type")
            params["event_type"] = event_type.value

        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity.value

        query = text(
            f"""
            SELECT id, event_type, severity, user_id, ip_address,
                   user_agent, session_id, details, risk_score, timestamp
            FROM security_events
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """,
        )
        params["limit"] = limit
        params["offset"] = offset

        async with self._db_manager.get_session() as session:
            result = await session.execute(query, params)
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

    async def log_security_events_batch(self, events: list[SecurityEventCreate], audit_service=None) -> list[SecurityEventResponse]:
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
        timestamp = datetime.now(timezone.utc)
        
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
                    details=event.details or {},
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
                    details=event.details or {},
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

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

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

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
