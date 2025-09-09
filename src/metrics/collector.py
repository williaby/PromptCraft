"""
Central metrics collection service for production monitoring.

This module provides the main MetricsCollector class that coordinates
event creation, validation, and storage for comprehensive production
monitoring and business intelligence.
"""

import asyncio
import contextlib
import logging
from typing import Any

from .events import (
    MetricEvent,
    MetricEventBuilder,
    MetricEventType,
    create_conceptual_mismatch_event,
    create_error_event,
    create_query_processed_event,
    create_user_feedback_event,
)
from .storage import MetricsStorage


class MetricsCollector:
    """Central service for collecting and storing production metrics."""

    def __init__(self, storage_backend: str = "sqlite", database_path: str = "metrics.db") -> None:
        """Initialize metrics collector with storage backend."""
        self.logger = logging.getLogger(__name__)

        # Initialize storage
        if storage_backend == "sqlite":
            self.storage = MetricsStorage(database_path)
        else:
            raise ValueError(f"Unsupported storage backend: {storage_backend}")

        # Event buffer for batch processing
        self._event_buffer: list[MetricEvent] = []
        self._buffer_lock = asyncio.Lock()
        self._batch_size = 10
        self._flush_interval = 30  # seconds

        # Start background flush task
        self._flush_task: asyncio.Task[None] | None = None
        self._shutdown = False

    async def start(self) -> None:
        """Start the metrics collector with background processing."""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._background_flush())
            self.logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop the metrics collector and flush remaining events."""
        self._shutdown = True
        if self._flush_task:
            with contextlib.suppress(asyncio.CancelledError):
                await self._flush_task
        await self.flush_events()
        self.logger.info("Metrics collector stopped")

    async def record_query_processed(
        self,
        session_id: str,
        hyde_score: int | None,
        action_taken: str,
        response_time_ms: int,
        query_text: str | None,
        conceptual_issues: list[str] | None = None,
        vector_search_results: int | None = None,
        vector_store_type: str | None = None,
    ) -> str:
        """Record a query processing event."""
        try:
            event = create_query_processed_event(
                session_id=session_id,
                hyde_score=hyde_score,
                action_taken=action_taken,
                response_time_ms=response_time_ms,
                query_text=query_text,
                conceptual_issues=conceptual_issues or [],
            )

            # Add vector store metrics if provided
            if vector_search_results is not None:
                event.vector_search_results = vector_search_results
            if vector_store_type:
                event.vector_store_type = vector_store_type

            await self._add_event_to_buffer(event)

            self.logger.debug(
                "Recorded query processed: hyde_score=%s, action=%s, time=%dms",
                hyde_score,
                action_taken,
                response_time_ms,
            )

            return event.event_id

        except Exception as e:
            self.logger.error("Failed to record query processed event: %s", str(e))
            return ""

    async def record_user_feedback(
        self,
        session_id: str,
        feedback_type: str,
        feedback_target: str,
        feedback_score: int | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> str:
        """Record user feedback event."""
        try:
            event = create_user_feedback_event(
                session_id=session_id,
                feedback_type=feedback_type,
                feedback_target=feedback_target,
                feedback_score=feedback_score,
            )

            # Add additional context if provided
            if additional_context:
                event.additional_data.update(additional_context)

            await self._add_event_to_buffer(event)

            self.logger.debug(
                "Recorded user feedback: type=%s, target=%s, session=%s",
                feedback_type,
                feedback_target,
                session_id,
            )

            return event.event_id

        except Exception as e:
            self.logger.error("Failed to record user feedback event: %s", str(e))
            return ""

    async def record_conceptual_mismatch(
        self,
        session_id: str,
        domain_detected: str,
        mismatch_type: str,
        suggested_alternative: str,
        hyde_score: int,
        query_text: str | None = None,
    ) -> str:
        """Record conceptual mismatch detection event."""
        try:
            event = create_conceptual_mismatch_event(
                session_id=session_id,
                domain_detected=domain_detected,
                mismatch_type=mismatch_type,
                suggested_alternative=suggested_alternative,
                hyde_score=hyde_score,
            )

            # Add query analysis if text provided
            if query_text:
                import hashlib

                event.query_text_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]
                event.query_length = len(query_text.split())

            await self._add_event_to_buffer(event)

            self.logger.debug(
                "Recorded conceptual mismatch: domain=%s, type=%s, alternative=%s",
                domain_detected,
                mismatch_type,
                suggested_alternative,
            )

            return event.event_id

        except Exception as e:
            self.logger.error("Failed to record conceptual mismatch event: %s", str(e))
            return ""

    async def record_error(
        self,
        session_id: str,
        error_details: str,
        error_type: str,
        response_time_ms: int | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> str:
        """Record system error event."""
        try:
            event = create_error_event(
                session_id=session_id,
                error_details=error_details,
                error_type=error_type,
                response_time_ms=response_time_ms,
            )

            # Add additional context
            if additional_context:
                event.additional_data.update(additional_context)

            await self._add_event_to_buffer(event)

            self.logger.debug("Recorded error event: type=%s, session=%s", error_type, session_id)

            return event.event_id

        except Exception as e:
            self.logger.error("Failed to record error event: %s", str(e))
            return ""

    async def record_custom_event(self, event_type: MetricEventType, session_id: str, **kwargs: Any) -> str:
        """Record a custom event with flexible parameters."""
        try:
            builder = MetricEventBuilder(event_type, session_id)

            # Apply common kwargs
            if "hyde_score" in kwargs:
                builder.with_hyde_metrics(
                    kwargs.get("hyde_score"),
                    kwargs.get("action_taken", "unknown"),
                    kwargs.get("conceptual_issues", []),
                )

            if "response_time_ms" in kwargs:
                response_time = kwargs.get("response_time_ms")
                if isinstance(response_time, int):
                    builder.with_performance_metrics(response_time, kwargs.get("error_details"))

            if "query_text" in kwargs:
                builder.with_query_analysis(kwargs.get("query_text"), kwargs.get("query_category"))

            # Add any remaining kwargs as additional data
            additional_data = {
                k: v
                for k, v in kwargs.items()
                if k
                not in [
                    "hyde_score",
                    "action_taken",
                    "conceptual_issues",
                    "response_time_ms",
                    "error_details",
                    "query_text",
                    "query_category",
                ]
            }
            if additional_data:
                builder.with_additional_data(**additional_data)

            event = builder.build()
            await self._add_event_to_buffer(event)

            self.logger.debug("Recorded custom event: type=%s, session=%s", event_type.value, session_id)

            return event.event_id

        except Exception as e:
            self.logger.error("Failed to record custom event: %s", str(e))
            return ""

    async def get_current_metrics(self, hours: int = 1) -> dict[str, Any]:
        """Get current metrics for dashboard display."""
        try:
            # Flush any pending events first
            await self.flush_events()

            # Get metrics summary
            return await self.storage.get_metrics_summary(hours)

        except Exception as e:
            self.logger.error("Failed to get current metrics: %s", str(e))
            return {"error": str(e)}

    async def flush_events(self) -> int:
        """Manually flush all buffered events to storage."""
        async with self._buffer_lock:
            if not self._event_buffer:
                return 0

            events_to_flush = self._event_buffer.copy()
            self._event_buffer.clear()

        try:
            # Store events
            stored_count = await self.storage.store_events_batch(events_to_flush)
            self.logger.debug("Flushed %d events to storage", stored_count)
            return stored_count
        except Exception as e:
            self.logger.error("Failed to flush events to storage: %s", str(e))
            # Return events to buffer on failure
            async with self._buffer_lock:
                self._event_buffer.extend(events_to_flush)
            return 0

    async def _add_event_to_buffer(self, event: MetricEvent) -> None:
        """Add event to buffer and trigger flush if needed."""
        async with self._buffer_lock:
            self._event_buffer.append(event)

            # Auto-flush if buffer is full
            if len(self._event_buffer) >= self._batch_size:
                # Create a copy to flush without holding the lock
                events_to_flush = self._event_buffer.copy()
                self._event_buffer.clear()

                # Flush without holding lock
                asyncio.create_task(self._flush_events_batch(events_to_flush))

    async def _flush_events_batch(self, events: list[MetricEvent]) -> None:
        """Flush a batch of events to storage."""
        try:
            await self.storage.store_events_batch(events)
        except Exception as e:
            self.logger.error("Failed to flush events batch: %s", str(e))
            # Re-add events to buffer for retry
            async with self._buffer_lock:
                self._event_buffer.extend(events)

    async def _background_flush(self) -> None:
        """Background task to periodically flush events."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self._flush_interval)
                if not self._shutdown:
                    await self.flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in background flush: %s", str(e))

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics for monitoring."""
        return await self.storage.get_database_stats()

    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old metric data."""
        return await self.storage.cleanup_old_events(days_to_keep)

    def __del__(self) -> None:
        """Cleanup on garbage collection."""
        if hasattr(self, "_flush_task") and self._flush_task is not None and not self._flush_task.done():
            self._flush_task.cancel()


# Global metrics collector instance
_global_collector: MetricsCollector | None = None


async def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance."""
    global _global_collector

    if _global_collector is None:
        _global_collector = MetricsCollector()
        await _global_collector.start()

    return _global_collector


async def shutdown_metrics_collector() -> None:
    """Shutdown the global metrics collector."""
    global _global_collector

    if _global_collector is not None:
        await _global_collector.stop()
        _global_collector = None
