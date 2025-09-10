"""
Metrics collector implementation.

This module provides the core metrics collection functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from .events import MetricEvent, MetricEventType

logger = logging.getLogger(__name__)

# Global collector instance
_collector: Optional["MetricsCollector"] = None


class MetricsCollector:
    """Main metrics collector class."""

    def __init__(self, buffer_size: int = 1000) -> None:
        """Initialize the metrics collector."""
        self.buffer_size = buffer_size
        self.events: list[MetricEvent] = []
        self.running = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the metrics collector."""
        self.running = True
        logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop the metrics collector."""
        self.running = False
        logger.info("Metrics collector stopped")

    async def record_event(
        self,
        event_type: MetricEventType,
        data: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> None:
        """Record a metric event."""
        event = MetricEvent(event_type, data, timestamp)

        async with self._lock:
            self.events.append(event)

            # Keep buffer size manageable
            if len(self.events) > self.buffer_size:
                self.events = self.events[-self.buffer_size :]

        logger.debug("Recorded metric event: %s", event_type.value)

    async def get_events(self) -> list[MetricEvent]:
        """Get all recorded events."""
        async with self._lock:
            return self.events.copy()

    async def clear_events(self) -> None:
        """Clear all recorded events."""
        async with self._lock:
            self.events.clear()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


async def shutdown_metrics_collector() -> None:
    """Shutdown the global metrics collector."""
    global _collector
    if _collector is not None:
        await _collector.stop()
        _collector = None
