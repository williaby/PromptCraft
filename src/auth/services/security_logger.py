"""High-performance security event logging service with comprehensive features.

This service provides security event logging with:
- < 10ms logging performance through async batch processing
- Rate limiting with sliding window algorithm to prevent DOS
- Queue management with configurable batch sizes and timeouts
- Security event sanitization (redacting passwords, tokens, keys)
- Embedded configuration pattern (no separate config files)
- Exponential moving average for performance metrics tracking
- Retention policies by severity level (14 days to 1 year)

Performance target: < 10ms per log_event call
Architecture: Async batch processing with PostgreSQL backend
"""

import asyncio
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete

from src.auth.models import SecurityEventCreate, SecurityEventSeverity, SecurityEventType
from src.database.connection import get_database_manager_async
from src.database.models import SecurityEvent as SecurityEventModel


@dataclass
class LoggingConfig:
    """Embedded configuration for security logging (no external config file)."""

    # Performance settings
    batch_size: int = 50  # Events per batch insert
    batch_timeout_seconds: float = 2.0  # Max time to wait for batch
    queue_max_size: int = 1000  # Max events in queue

    # Rate limiting (sliding window)
    rate_limit_window_seconds: int = 60  # 1 minute window
    rate_limit_max_events: int = 500  # Max events per window

    # Retention policies by severity (days)
    retention_days_info: int = 14  # INFO events kept for 14 days
    retention_days_warning: int = 90  # WARNING events kept for 90 days
    retention_days_critical: int = 365  # CRITICAL events kept for 1 year

    # Security sanitization patterns
    sensitive_patterns: set[str] = field(
        default_factory=lambda: {
            "password",
            "passwd",
            "pwd",
            "secret",
            "key",
            "token",
            "auth",
            "credential",
            "private",
            "confidential",
        },
    )


@dataclass
class LoggingMetrics:
    """Performance metrics for monitoring logging system health."""

    total_events_logged: int = 0
    total_events_dropped: int = 0
    average_logging_time_ms: float = 0.0
    current_queue_size: int = 0
    rate_limit_hits: int = 0
    last_batch_time: datetime | None = None

    # Exponential moving average parameters
    _ema_alpha: float = 0.1  # Smoothing factor for moving average


class SecurityLogger:
    """High-performance async security event logger with batch processing."""

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout_seconds: float = 5.0,
        max_queue_size: int = 1000,
        config: LoggingConfig | None = None,
    ) -> None:
        """Initialize security logger with embedded configuration.

        Args:
            batch_size: Number of events to batch before writing
            batch_timeout_seconds: Maximum time to wait for batch
            max_queue_size: Maximum queue size
            config: Logging configuration (uses defaults if None)
        """
        # Validate parameters
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if batch_timeout_seconds <= 0:
            raise ValueError(f"batch_timeout_seconds must be positive, got {batch_timeout_seconds}")
        if max_queue_size <= 0:
            raise ValueError(f"max_queue_size must be positive, got {max_queue_size}")

        # Support both config-based and parameter-based initialization
        if config:
            self.config = config
            self.batch_size = config.batch_size
            self.batch_timeout_seconds = config.batch_timeout_seconds
            self.max_queue_size = config.queue_max_size
        else:
            self.batch_size = batch_size
            self.batch_timeout_seconds = batch_timeout_seconds
            self.max_queue_size = max_queue_size
            # Create config from parameters
            self.config = LoggingConfig(
                batch_size=batch_size,
                batch_timeout_seconds=batch_timeout_seconds,
                queue_max_size=max_queue_size,
            )

        self.metrics = LoggingMetrics()
        self._performance_metrics: list[float] = []

        # No database instance stored - will get DatabaseManager per operation

        # Async event processing
        self._event_queue: asyncio.Queue[SecurityEventCreate] = asyncio.Queue(maxsize=self.max_queue_size)
        self._batch_processor_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

        # Rate limiting (sliding window)
        self._rate_limit_window: deque = deque()

        # Start background processing
        self._start_batch_processor()

    async def initialize(self) -> None:
        """Initialize the security logger and start background processing.

        This method ensures the database is initialized and background processing is running.
        It's idempotent and can be called multiple times safely.
        """
        # Ensure database manager is initialized
        db_manager = await get_database_manager_async()
        await db_manager.initialize()

        # Restart batch processor if needed
        if not self._batch_processor_task or self._batch_processor_task.done():
            self._start_batch_processor()

    def _start_batch_processor(self) -> None:
        """Start the background batch processor task."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._batch_processor_task = loop.create_task(self._batch_processor())
        except RuntimeError:
            # No event loop running, will be started when needed
            pass

    async def log_event(
        self,
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
        risk_score: int = 0,
    ) -> bool:
        """Log security event with high performance async processing.

        Args:
            event_type: Type of security event
            severity: Event severity level
            user_id: User identifier (email or service token name)
            ip_address: Client IP address
            user_agent: User agent string
            session_id: Session identifier
            details: Additional event details (will be sanitized)
            risk_score: Risk score from 0-100

        Returns:
            True if event was queued successfully, False if dropped due to rate limiting

        Performance target: < 10ms per call
        """
        start_time = time.time()

        # Rate limiting check
        if not self._check_rate_limit():
            self.metrics.rate_limit_hits += 1
            self.metrics.total_events_dropped += 1
            return False

        # Sanitize sensitive data in details
        sanitized_details = self._sanitize_event_details(details) if details else None

        # Create security event
        event = SecurityEventCreate(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=sanitized_details,
            risk_score=min(max(risk_score, 0), 100),  # Clamp to 0-100 range
            timestamp=datetime.now(UTC),
        )

        try:
            # Non-blocking queue addition
            self._event_queue.put_nowait(event)

            # Update metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_metrics(processing_time_ms)

            return True

        except asyncio.QueueFull:
            self.metrics.total_events_dropped += 1
            return False

    def _check_rate_limit(self) -> bool:
        """Check rate limiting using sliding window algorithm."""
        current_time = time.time()
        window_start = current_time - self.config.rate_limit_window_seconds

        # Remove expired entries from sliding window
        while self._rate_limit_window and self._rate_limit_window[0] < window_start:
            self._rate_limit_window.popleft()

        # Check if we're within rate limit
        if len(self._rate_limit_window) >= self.config.rate_limit_max_events:
            return False

        # Add current timestamp to window
        self._rate_limit_window.append(current_time)
        return True

    def _sanitize_event_details(self, details: dict[str, Any]) -> dict[str, Any]:
        """Sanitize event details to redact sensitive information.

        Args:
            details: Event details dictionary

        Returns:
            Sanitized details with sensitive values redacted
        """
        if not details:
            return {}

        sanitized = {}

        for key, value in details.items():
            key_lower = key.lower()

            # Check if key contains sensitive patterns
            is_sensitive = any(pattern in key_lower for pattern in self.config.sensitive_patterns)

            if is_sensitive:
                # Redact sensitive values
                if isinstance(value, str) and value:
                    sanitized[key] = "[REDACTED]" if len(value) > 8 else "[REDACTED_SHORT]"
                else:
                    sanitized[key] = "[REDACTED]"
            # Keep non-sensitive values, but sanitize strings for safety
            elif isinstance(value, str):
                # Remove potentially dangerous characters and limit length
                sanitized_value = re.sub(r'[<>"\'`]', "", str(value))
                sanitized[key] = sanitized_value[:1000]  # Limit length
            elif isinstance(value, (int, float, bool, type(None))):
                sanitized[key] = value
            else:
                # Convert complex types to safe string representation
                sanitized[key] = str(value)[:500]

        return sanitized

    def _update_metrics(self, processing_time_ms: float) -> None:
        """Update performance metrics using exponential moving average."""
        self.metrics.total_events_logged += 1
        self.metrics.current_queue_size = self._event_queue.qsize()

        # Update exponential moving average for processing time
        if self.metrics.average_logging_time_ms == 0:
            self.metrics.average_logging_time_ms = processing_time_ms
        else:
            self.metrics.average_logging_time_ms = (
                self.metrics._ema_alpha * processing_time_ms
                + (1 - self.metrics._ema_alpha) * self.metrics.average_logging_time_ms
            )

    async def _batch_processor(self) -> None:
        """Background task for batch processing events to database."""
        # Ensure database manager is initialized
        db_manager = await get_database_manager_async()
        await db_manager.initialize()

        batch: list[SecurityEventCreate] = []
        last_batch_time = time.time()

        while not self._shutdown_event.is_set():
            try:
                # Wait for events or timeout
                timeout = self.batch_timeout_seconds
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=timeout)
                    batch.append(event)
                except TimeoutError:
                    pass  # Continue to batch processing

                current_time = time.time()
                time_since_last_batch = current_time - last_batch_time

                # Process batch if conditions are met
                should_process = len(batch) >= self.batch_size or (
                    batch and time_since_last_batch >= self.batch_timeout_seconds
                )

                if should_process and batch:
                    await self._process_batch(batch)
                    batch.clear()
                    last_batch_time = current_time
                    self.metrics.last_batch_time = datetime.now(UTC)

            except Exception:
                # Log error but continue processing
                batch.clear()  # Clear corrupted batch

    async def _process_batch(self, batch: list[SecurityEventCreate]) -> None:
        """Process a batch of events to the database.

        Args:
            batch: List of events to process
        """
        try:
            db_manager = await get_database_manager_async()
            async with db_manager.get_session() as session:
                # Process each event in the batch
                for event in batch:
                    db_event = SecurityEventModel(
                        id=uuid.uuid4(),
                        entity_key=f"user:{event.user_id}" if event.user_id else f"ip:{event.ip_address or 'unknown'}",
                        event_type=event.event_type.value,
                        severity=event.severity.value,
                        user_id=event.user_id,
                        ip_address=event.ip_address,
                        risk_score=event.risk_score,
                        event_details=event.details or {},
                        timestamp=event.timestamp or datetime.now(UTC),
                    )
                    session.add(db_event)

                await session.commit()

        except Exception:
            # On error, increment dropped events count
            self.metrics.total_events_dropped += len(batch)

    async def get_metrics(self) -> dict[str, Any]:
        """Get current logging system metrics.

        Returns:
            Dictionary with current metrics and performance statistics
        """
        return {
            "performance": {
                "total_events_logged": self.metrics.total_events_logged,
                "total_events_dropped": self.metrics.total_events_dropped,
                "average_logging_time_ms": round(self.metrics.average_logging_time_ms, 2),
                "current_queue_size": self.metrics.current_queue_size,
                "rate_limit_hits": self.metrics.rate_limit_hits,
                "last_batch_time": self.metrics.last_batch_time.isoformat() if self.metrics.last_batch_time else None,
            },
            "configuration": {
                "batch_size": self.batch_size,
                "batch_timeout_seconds": self.batch_timeout_seconds,
                "queue_max_size": self.max_queue_size,
                "rate_limit_max_events": self.config.rate_limit_max_events,
                "rate_limit_window_seconds": self.config.rate_limit_window_seconds,
            },
            "health": {
                "is_processing": self._batch_processor_task and not self._batch_processor_task.done(),
                "queue_utilization_percent": (self.metrics.current_queue_size / self.max_queue_size) * 100,
                "avg_processing_performance": (
                    "excellent"
                    if self.metrics.average_logging_time_ms < 5
                    else "good" if self.metrics.average_logging_time_ms < 10 else "degraded"
                ),
            },
        }

    async def flush(self) -> None:
        """Flush any pending events to database immediately."""
        # Process any remaining events in the queue
        remaining_events = []
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                remaining_events.append(event)
            except asyncio.QueueEmpty:
                break

        if remaining_events:
            await self._process_batch(remaining_events)

    async def cleanup_old_events(self) -> dict[str, int]:
        """Clean up old events based on retention policies.

        Returns:
            Dictionary with cleanup statistics by severity level
        """
        cleanup_stats = {}

        # Clean up by severity with different retention periods
        severity_retention = {
            SecurityEventSeverity.INFO: self.config.retention_days_info,
            SecurityEventSeverity.WARNING: self.config.retention_days_warning,
            SecurityEventSeverity.CRITICAL: self.config.retention_days_critical,
        }

        try:
            db_manager = await get_database_manager_async()
            async with db_manager.get_session() as session:
                for severity, retention_days in severity_retention.items():
                    cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

                    # Delete events older than retention period for this severity
                    delete_stmt = delete(SecurityEventModel).where(
                        SecurityEventModel.severity == severity.value,
                        SecurityEventModel.timestamp < cutoff_date,
                    )
                    result = await session.execute(delete_stmt)
                    cleanup_stats[severity.value] = result.rowcount or 0

                await session.commit()

        except Exception:
            # Return empty stats on error
            cleanup_stats = {severity.value: 0 for severity in severity_retention}

        return cleanup_stats

    async def shutdown(self) -> None:
        """Gracefully shutdown the security logger."""
        # Signal shutdown
        self._shutdown_event.set()

        # Flush any pending events
        await self.flush()

        # Wait for batch processor to complete
        if self._batch_processor_task:
            await self._batch_processor_task

        # Database connections managed by DatabaseManager, no explicit close needed

    def __del__(self) -> None:
        """Cleanup when logger is destroyed."""
        if (
            hasattr(self, "_batch_processor_task")
            and self._batch_processor_task
            and not self._batch_processor_task.done()
        ):
            self._batch_processor_task.cancel()
