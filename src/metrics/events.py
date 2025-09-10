"""
Metric event types and definitions.

This module defines the various types of metrics events that can be collected.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MetricEventType(Enum):
    """Types of metric events that can be recorded."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    PERFORMANCE = "performance"
    USER_ACTION = "user_action"
    SYSTEM = "system"

    # Additional event types for metrics tracking
    QUERY_PROCESSED = "query_processed"
    USER_FEEDBACK = "user_feedback"
    CONCEPTUAL_MISMATCH = "conceptual_mismatch"
    ERROR_OCCURRED = "error_occurred"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    VECTOR_SEARCH = "vector_search"


class MetricEvent:
    """Base class for metric events."""

    def __init__(
        self,
        event_type: MetricEventType,
        data: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> None:
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
