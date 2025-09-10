"""
Metric event types and definitions.

This module defines the various types of metrics events that can be collected.
"""

from datetime import datetime
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
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
