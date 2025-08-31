"""Stateless security monitor implementation for real-time threat detection.

Converted from stateful to stateless design for multi-worker FastAPI deployment.
All state is now stored in PostgreSQL database using DatabaseConnection.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from src.auth.alert_engine import AlertEngine
from src.auth.security_logger import SecurityLogger
from src.database.connection import get_database_manager
from src.database.models import BlockedEntity, MonitoringThreshold, SecurityEvent, ThreatScore

from .models import SecurityEventResponse, SecurityEventSeverity, SecurityEventType

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Stateless real-time security monitoring and threat detection system.

    Converted from stateful to stateless design for multi-worker FastAPI deployment.
    All monitoring state is now persisted in PostgreSQL database.

    Key Changes:
    - Removed in-memory state (_event_history, _blocked_ips, _blocked_users, _threat_scores)
    - Removed background tasks (_monitoring_task, _alert_callbacks)
    - All operations now use database queries
    - Maintains identical public API for compatibility
    """

    def __init__(
        self,
        alert_threshold: int = 5,
        time_window: int = 60,
        suspicious_patterns: list[str] | None = None,
    ) -> None:
        """Initialize stateless security monitor.

        Args:
            alert_threshold: Number of events to trigger alert
            time_window: Time window in seconds for event correlation
            suspicious_patterns: List of suspicious activity patterns
        """
        self.alert_threshold = alert_threshold
        self.time_window = time_window
        self.suspicious_patterns = suspicious_patterns or [
            "multiple_failed_logins",
            "rapid_requests",
            "suspicious_user_agent",
            "ip_hopping",
            "privilege_escalation_attempt",
        ]

        # Initialize dependencies (PostgreSQL only - no hybrid approach)
        self._security_logger = SecurityLogger()
        self._alert_engine = AlertEngine()

        # Database manager for all PostgreSQL operations
        self._db_manager = get_database_manager()

    async def initialize(self) -> None:
        """Initialize the security monitor.

        Sets up database thresholds if they don't exist.
        No longer creates background tasks (stateless design).
        """
        async with self._db_manager.get_session() as session:
            # Ensure monitoring thresholds exist in database
            await self._ensure_thresholds_exist(session)

        logger.info(
            "SecurityMonitor initialized (stateless) with threshold=%d, window=%ds",
            self.alert_threshold,
            self.time_window,
        )

    async def _ensure_thresholds_exist(self, session: Any) -> None:
        """Ensure monitoring thresholds exist in database."""
        thresholds = [
            ("alert_threshold", self.alert_threshold, "Number of events to trigger alert"),
            ("time_window", self.time_window, "Time window in seconds for event correlation"),
        ]

        for name, value, description in thresholds:
            stmt = select(MonitoringThreshold).where(MonitoringThreshold.threshold_name == name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                threshold = MonitoringThreshold(
                    threshold_name=name,
                    threshold_value=value,
                    description=description,
                    is_active=True,
                    threshold_metadata={"created_by": "SecurityMonitor"},
                )
                session.add(threshold)

        await session.commit()

    async def track_event(self, event: SecurityEventResponse) -> None:
        """Track a security event for monitoring.

        Args:
            event: Security event to track
        """
        async with self._db_manager.get_session() as session:
            # Store event in database
            await self._store_security_event(session, event)

            # Check for threshold breaches
            if event.ip_address:
                ip_key = f"ip:{event.ip_address}"
                if await self._check_threshold(session, ip_key, event.timestamp):
                    await self._trigger_alert("ip_threshold", event.ip_address)

            if event.user_id:
                user_key = f"user:{event.user_id}"
                if await self._check_threshold(session, user_key, event.timestamp):
                    await self._trigger_alert("user_threshold", event.user_id)

            # Check for suspicious patterns
            await self._check_patterns(session, event)

            # Update threat scores
            await self._update_threat_scores(session, event)

            await session.commit()

    async def track_events_batch(self, events: list) -> None:
        """Track multiple security events in a single transaction for performance.

        Args:
            events: List of SecurityEventResponse objects to track
        """
        if not events:
            return

        async with self._db_manager.get_session() as session:
            # First, store all events efficiently
            db_events = []
            for event in events:
                # Determine entity key
                entity_key = ""
                if event.user_id:
                    entity_key = f"user:{event.user_id}"
                elif event.ip_address:
                    entity_key = f"ip:{event.ip_address}"
                else:
                    entity_key = "session:unknown"

                security_event = SecurityEvent(
                    entity_key=entity_key,
                    event_type=event.event_type,
                    severity=event.severity,
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    risk_score=event.risk_score,
                    event_details=event.details or {},
                    timestamp=event.timestamp,
                )
                db_events.append(security_event)

            # Bulk add all events
            session.add_all(db_events)

            # Simplified threshold checking - just count events per user/IP
            user_counts: dict[str, int] = {}
            ip_counts: dict[str, int] = {}

            for event in events:
                if event.user_id:
                    user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
                if event.ip_address:
                    ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1

            # Trigger alerts for high counts (simplified threshold check)
            for user_id, count in user_counts.items():
                if count >= 3:  # Threshold for user alerts
                    await self._trigger_alert("user_threshold", user_id)

            for ip_address, count in ip_counts.items():
                if count >= 3:  # Threshold for IP alerts
                    await self._trigger_alert("ip_threshold", ip_address)

            # Single commit for all events
            await session.commit()

    async def _store_security_event(self, session: Any, event: SecurityEventResponse) -> None:
        """Store security event in database."""
        # Determine entity key
        entity_key = ""
        if event.user_id:
            entity_key = f"user:{event.user_id}"
        elif event.ip_address:
            entity_key = f"ip:{event.ip_address}"
        else:
            entity_key = "session:unknown"

        security_event = SecurityEvent(
            entity_key=entity_key,
            event_type=event.event_type,
            severity=event.severity,
            user_id=event.user_id,
            ip_address=event.ip_address,
            risk_score=event.risk_score,
            event_details=event.details,
            timestamp=event.timestamp,
        )
        session.add(security_event)

    async def _check_threshold(self, session: Any, entity_key: str, event_timestamp: datetime) -> bool:
        """Check if event threshold is breached using database queries.

        Args:
            session: Database session
            entity_key: Event tracking key
            event_timestamp: Timestamp of current event

        Returns:
            True if threshold breached
        """
        # Get current threshold from database
        stmt = select(MonitoringThreshold).where(
            and_(MonitoringThreshold.threshold_name == "alert_threshold", MonitoringThreshold.is_active),
        )
        result = await session.execute(stmt)
        threshold_record = result.scalar_one_or_none()
        current_threshold = threshold_record.threshold_value if threshold_record else self.alert_threshold

        # Get time window from database
        stmt = select(MonitoringThreshold).where(
            and_(MonitoringThreshold.threshold_name == "time_window", MonitoringThreshold.is_active),
        )
        result = await session.execute(stmt)
        window_record = result.scalar_one_or_none()
        current_window = window_record.threshold_value if window_record else self.time_window

        # Calculate cutoff time
        cutoff = event_timestamp - timedelta(seconds=current_window)

        # Count recent events for this entity
        count_stmt = select(func.count(SecurityEvent.id)).where(
            and_(SecurityEvent.entity_key == entity_key, SecurityEvent.timestamp > cutoff),
        )
        result = await session.execute(count_stmt)
        event_count = result.scalar() or 0

        return event_count >= current_threshold

    async def _check_patterns(self, session: Any, event: SecurityEventResponse) -> None:
        """Check for suspicious patterns in event using database queries.

        Args:
            session: Database session
            event: Security event to analyze
        """
        # Check for multiple failed logins
        if event.event_type == SecurityEventType.LOGIN_FAILURE.value:
            if event.user_id:
                entity_key = f"failed_login:{event.user_id}"
                if await self._check_pattern_threshold(session, entity_key, event.timestamp):
                    await self._trigger_alert("multiple_failed_logins", event.user_id)

        # Check for rapid requests
        if event.ip_address:
            # Check if requests are too rapid (more than 10 per second)
            one_second_ago = event.timestamp - timedelta(seconds=1)

            stmt = select(func.count(SecurityEvent.id)).where(
                and_(SecurityEvent.ip_address == event.ip_address, SecurityEvent.timestamp > one_second_ago),
            )
            result = await session.execute(stmt)
            recent_count = result.scalar() or 0

            if recent_count > 10:
                await self._trigger_alert("rapid_requests", event.ip_address)

    async def _check_pattern_threshold(self, session: Any, entity_key: str, event_timestamp: datetime) -> bool:
        """Check pattern-specific threshold."""
        cutoff = event_timestamp - timedelta(seconds=self.time_window)

        stmt = select(func.count(SecurityEvent.id)).where(
            and_(SecurityEvent.entity_key == entity_key, SecurityEvent.timestamp > cutoff),
        )
        result = await session.execute(stmt)
        event_count = result.scalar() or 0

        return event_count >= self.alert_threshold

    async def _update_threat_scores(self, session: Any, event: SecurityEventResponse) -> None:
        """Update threat scores based on event using database operations.

        Args:
            session: Database session
            event: Security event to score
        """
        # Base score from event risk score
        score = event.risk_score

        # Add severity multiplier
        if event.severity == SecurityEventSeverity.CRITICAL.value:
            score *= 3
        elif event.severity == SecurityEventSeverity.WARNING.value:
            score = int(score * 1.5)

        # Update scores for IP and user
        entities_to_update = []

        if event.ip_address:
            entities_to_update.append({"key": f"ip:{event.ip_address}", "type": "ip", "value": event.ip_address})

        if event.user_id:
            entities_to_update.append({"key": f"user:{event.user_id}", "type": "user", "value": event.user_id})

        for entity in entities_to_update:
            await self._upsert_threat_score(session, entity["key"], entity["type"], entity["value"], int(score))

    async def _upsert_threat_score(
        self,
        session: Any,
        entity_key: str,
        entity_type: str,
        entity_value: str,
        score_increment: int,
    ) -> None:
        """Upsert threat score using PostgreSQL upsert."""
        stmt = insert(ThreatScore).values(
            entity_key=entity_key,
            entity_type=entity_type,
            entity_value=entity_value,
            score=score_increment,
            score_details={"last_event_score": score_increment},
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["entity_key"],
            set_={
                "score": ThreatScore.score + stmt.excluded.score,
                "last_updated": func.now(),
                "score_details": stmt.excluded.score_details,
            },
        )

        await session.execute(stmt)

    async def _trigger_alert(self, alert_type: str, target: str) -> None:
        """Trigger a security alert.

        Args:
            alert_type: Type of alert
            target: Target of alert (IP or user)
        """
        logger.warning("Security alert triggered: type=%s, target=%s", alert_type, target)

        # Use alert engine to send alert
        await self._alert_engine.send_alert(
            alert_type=alert_type,
            message=f"Security threshold exceeded for {target}",
            target=target,
            details={"alert_type": alert_type, "target": target},
        )

    async def get_threat_score(self, identifier: str, id_type: str = "ip") -> int:
        """Get current threat score for identifier using database query.

        Args:
            identifier: IP address or user ID
            id_type: Type of identifier ("ip" or "user")

        Returns:
            Current threat score
        """
        entity_key = f"{id_type}:{identifier}"

        async with self._db_manager.get_session() as session:
            stmt = select(ThreatScore.score).where(ThreatScore.entity_key == entity_key)
            result = await session.execute(stmt)
            score = result.scalar()

            return score if score is not None else 0

    async def block_ip(self, ip_address: str, reason: str = "Security violation") -> None:
        """Block an IP address using database storage.

        Args:
            ip_address: IP to block
            reason: Reason for blocking
        """
        async with self._db_manager.get_session() as session:
            entity_key = f"ip:{ip_address}"

            # Check if already blocked
            stmt = select(BlockedEntity).where(
                and_(BlockedEntity.entity_key == entity_key, BlockedEntity.is_active),
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                blocked_entity = BlockedEntity(
                    entity_key=entity_key,
                    entity_type="ip",
                    entity_value=ip_address,
                    reason=reason,
                    blocked_by="SecurityMonitor",
                    is_active=True,
                )
                session.add(blocked_entity)
                await session.commit()

                logger.info("Blocked IP address: %s (reason: %s)", ip_address, reason)

    async def block_user(self, user_id: str, reason: str = "Security violation") -> None:
        """Block a user using database storage.

        Args:
            user_id: User to block
            reason: Reason for blocking
        """
        async with self._db_manager.get_session() as session:
            entity_key = f"user:{user_id}"

            # Check if already blocked
            stmt = select(BlockedEntity).where(
                and_(BlockedEntity.entity_key == entity_key, BlockedEntity.is_active),
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                blocked_entity = BlockedEntity(
                    entity_key=entity_key,
                    entity_type="user",
                    entity_value=user_id,
                    reason=reason,
                    blocked_by="SecurityMonitor",
                    is_active=True,
                )
                session.add(blocked_entity)
                await session.commit()

                logger.info("Blocked user: %s (reason: %s)", user_id, reason)

    def is_blocked(self, identifier: str, id_type: str = "ip") -> bool:
        """Check if identifier is blocked using database query.

        DEPRECATED: Use is_blocked_async() instead for proper async handling.

        Args:
            identifier: IP address or user ID
            id_type: Type of identifier

        Returns:
            True if blocked, False if not blocked or async check fails

        Note: This method is deprecated due to async/sync mixing issues.
        Returns False by default and logs a warning. Use is_blocked_async() instead.
        """
        logger.warning(
            "is_blocked() is deprecated due to sync/async issues. Use is_blocked_async() instead. "
            "Returning False for identifier: %s (type: %s)",
            identifier,
            id_type,
        )
        return False

    async def is_blocked_async(self, identifier: str, id_type: str = "ip") -> bool:
        """Async version of is_blocked for better performance.

        Args:
            identifier: IP address or user ID
            id_type: Type of identifier

        Returns:
            True if blocked
        """
        entity_key = f"{id_type}:{identifier}"

        async with self._db_manager.get_session() as session:
            stmt = select(BlockedEntity).where(
                and_(BlockedEntity.entity_key == entity_key, BlockedEntity.is_active),
            )
            result = await session.execute(stmt)
            blocked_entity = result.scalar_one_or_none()

            if blocked_entity:
                # Check if block has expired
                return blocked_entity.is_valid_block

            return False

    async def get_monitoring_stats(self) -> dict[str, Any]:
        """Get monitoring statistics using database queries.

        Returns:
            Dictionary of monitoring stats
        """
        async with self._db_manager.get_session() as session:
            # Count tracked IPs and users
            ip_stmt = select(func.count(func.distinct(SecurityEvent.entity_key))).where(
                SecurityEvent.entity_key.like("ip:%"),
            )
            ip_result = await session.execute(ip_stmt)
            tracked_ips = ip_result.scalar() or 0

            user_stmt = select(func.count(func.distinct(SecurityEvent.entity_key))).where(
                SecurityEvent.entity_key.like("user:%"),
            )
            user_result = await session.execute(user_stmt)
            tracked_users = user_result.scalar() or 0

            # Count blocked entities
            blocked_ips_stmt = select(func.count(BlockedEntity.id)).where(
                and_(BlockedEntity.entity_type == "ip", BlockedEntity.is_active),
            )
            blocked_ips_result = await session.execute(blocked_ips_stmt)
            blocked_ips = blocked_ips_result.scalar() or 0

            blocked_users_stmt = select(func.count(BlockedEntity.id)).where(
                and_(BlockedEntity.entity_type == "user", BlockedEntity.is_active),
            )
            blocked_users_result = await session.execute(blocked_users_stmt)
            blocked_users = blocked_users_result.scalar() or 0

            # Count threat scores
            threat_scores_stmt = select(func.count(ThreatScore.id)).where(ThreatScore.score > 0)
            threat_scores_result = await session.execute(threat_scores_stmt)
            threat_scores = threat_scores_result.scalar() or 0

            return {
                "tracked_ips": tracked_ips,
                "tracked_users": tracked_users,
                "blocked_ips": blocked_ips,
                "blocked_users": blocked_users,
                "threat_scores": threat_scores,
                "alert_callbacks": 0,  # No longer applicable in stateless design
                "stateless_design": True,
                "database_backend": "PostgreSQL",
            }

    async def cleanup_old_data(self, retention_hours: int = 24) -> dict[str, int]:
        """Clean up old monitoring data.

        Args:
            retention_hours: Hours of data to retain

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)

        async with self._db_manager.get_session() as session:
            # Clean old security events
            events_stmt = delete(SecurityEvent).where(SecurityEvent.timestamp < cutoff)
            events_result = await session.execute(events_stmt)
            deleted_events = events_result.rowcount

            # Clean expired blocks
            blocks_stmt = delete(BlockedEntity).where(
                and_(BlockedEntity.expires_at.isnot(None), BlockedEntity.expires_at < datetime.now(UTC)),
            )
            blocks_result = await session.execute(blocks_stmt)
            expired_blocks = blocks_result.rowcount

            # Decay threat scores (reduce by 5% for old scores)
            score_cutoff = datetime.now(UTC) - timedelta(hours=1)
            decay_stmt = (
                update(ThreatScore)
                .where(ThreatScore.last_updated < score_cutoff)
                .values(score=func.greatest(ThreatScore.score * 0.95, 0), last_updated=func.now())
            )
            decay_result = await session.execute(decay_stmt)
            decayed_scores = decay_result.rowcount

            # Remove very low scores
            cleanup_stmt = delete(ThreatScore).where(ThreatScore.score < 1)
            cleanup_result = await session.execute(cleanup_stmt)
            cleaned_scores = cleanup_result.rowcount

            await session.commit()

            logger.info(
                "Cleaned up monitoring data: %d events, %d expired blocks, %d decayed scores, %d removed scores",
                deleted_events,
                expired_blocks,
                decayed_scores,
                cleaned_scores,
            )

            return {
                "deleted_events": deleted_events,
                "expired_blocks": expired_blocks,
                "decayed_scores": decayed_scores,
                "cleaned_scores": cleaned_scores,
            }

    async def get_security_metrics(self) -> dict[str, Any]:
        """Get comprehensive security metrics.

        Returns:
            Dictionary with security metrics including monitoring stats
        """
        return await self.get_monitoring_stats()

    async def get_recent_events(
        self,
        limit: int = 50,
        offset: int = 0,
        severity: str | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent security events from the database.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            severity: Filter by severity level
            event_type: Filter by event type

        Returns:
            List of security event dictionaries
        """
        async with self._db_manager.get_session() as session:
            # Build query for recent events
            stmt = select(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).offset(offset).limit(limit)

            # Apply filters if provided
            if severity:
                stmt = stmt.where(SecurityEvent.severity == severity)
            if event_type:
                stmt = stmt.where(SecurityEvent.event_type == event_type)

            result = await session.execute(stmt)
            events = result.scalars().all()

            # Convert to dictionaries
            event_list = []
            for event in events:
                event_dict = {
                    "id": str(event.id),
                    "entity_key": event.entity_key,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "user_id": event.user_id,
                    "ip_address": str(event.ip_address) if event.ip_address else None,
                    "risk_score": event.risk_score,
                    "details": event.event_details,
                    "timestamp": event.timestamp,
                    "created_at": event.created_at,
                    "resolved": False,  # Add default resolved field
                }
                event_list.append(event_dict)

            return event_list

    async def close(self) -> None:
        """Close the security monitor.

        No longer needs to cancel background tasks (stateless design).
        Database connections are managed by DatabaseManager.
        """
        logger.info("SecurityMonitor closed (stateless design)")
