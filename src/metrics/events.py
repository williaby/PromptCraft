"""
Metric event definitions for production monitoring.

This module defines the structured events that capture all user interactions,
system performance, and business intelligence metrics for comprehensive
production monitoring and analysis.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MetricEventType(str, Enum):
    """Types of metric events for comprehensive system monitoring."""

    # Core HyDE Performance Events
    QUERY_PROCESSED = "query_processed"
    CLARIFICATION_SHOWN = "clarification_shown"
    CREATE_PROMPT_GENERATED = "create_prompt_generated"
    CONCEPTUAL_MISMATCH = "conceptual_mismatch"

    # User Interaction Events
    USER_FEEDBACK = "user_feedback"
    QUERY_MODIFIED = "query_modified"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"

    # System Performance Events
    ERROR_OCCURRED = "error_occurred"
    LATENCY_MEASURED = "latency_measured"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"

    # Vector Store Events
    VECTOR_SEARCH = "vector_search"
    VECTOR_INSERT = "vector_insert"
    QDRANT_CONNECTION = "qdrant_connection"

    # Business Intelligence Events
    DOMAIN_GAP_IDENTIFIED = "domain_gap_identified"
    FALSE_POSITIVE_REPORTED = "false_positive_reported"
    DIFFERENTIATION_SURVEY = "differentiation_survey"


class MetricEvent(BaseModel):
    """Structured metric event for comprehensive production monitoring."""

    # Event Identification
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: MetricEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Session and User Context
    session_id: str
    user_id: str | None = None

    # HyDE Specific Metrics
    hyde_score: int | None = Field(None, ge=0, le=100)
    action_taken: str | None = None  # "clarification" | "create_prompt" | "direct"
    conceptual_issues: list[str] | None = None
    query_specificity_level: str | None = None  # "low" | "medium" | "high"

    # User Feedback Metrics
    feedback_type: str | None = None  # "thumbs_up" | "thumbs_down" | "survey_response"
    feedback_target: str | None = None  # "clarification" | "create_prompt" | "concept_warning"
    feedback_score: int | None = Field(None, ge=1, le=5)  # 1-5 rating scale

    # Performance Metrics
    response_time_ms: int | None = Field(None, ge=0)
    error_details: str | None = None
    error_type: str | None = None
    latency_category: str | None = None  # "fast" | "normal" | "slow" | "timeout"

    # Query Analysis (Privacy-Safe)
    query_text_hash: str | None = None  # SHA-256 hash for privacy
    query_length: int | None = Field(None, ge=0)
    query_category: str | None = None  # "technical" | "business" | "creative" | "vague"
    query_language: str | None = None  # "en" | "es" | "fr" etc.

    # Vector Store Performance
    vector_search_results: int | None = Field(None, ge=0)
    vector_search_score_threshold: float | None = Field(None, ge=0.0, le=1.0)
    vector_store_type: str | None = None  # "qdrant" | "mock"

    # Domain-Specific Metrics
    domain_detected: str | None = None  # "excel" | "salesforce" | "slack" etc.
    mismatch_type: str | None = None  # Type of conceptual confusion
    suggested_alternative: str | None = None  # Tool suggested as alternative

    # Business Intelligence
    differentiation_value: str | None = None  # "high" | "medium" | "low"
    competitive_comparison: str | None = None  # vs other AI tools
    user_retention_indicator: bool | None = None  # Likely to continue using

    # System Context
    system_version: str | None = None
    feature_flags: dict[str, bool] | None = None
    environment: str | None = None  # "dev" | "staging" | "prod"

    # Additional Flexible Data
    additional_data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True

    def to_storage_dict(self) -> dict[str, Any]:
        """Convert to dictionary format suitable for database storage."""
        data = self.dict()

        # Convert datetime to timestamp for storage
        data["timestamp"] = self.timestamp.isoformat()

        # Convert lists to JSON strings for SQL storage
        if data.get("conceptual_issues"):
            data["conceptual_issues"] = ",".join(data["conceptual_issues"])
        elif "conceptual_issues" in data:
            data["conceptual_issues"] = ""

        # Convert feature_flags dict to JSON string
        if data.get("feature_flags"):
            import json

            data["feature_flags"] = json.dumps(data["feature_flags"])
        elif "feature_flags" in data:
            data["feature_flags"] = "{}"

        # Convert additional_data dict to JSON string
        if data.get("additional_data"):
            import json

            data["additional_data"] = json.dumps(data["additional_data"])
        elif "additional_data" in data:
            data["additional_data"] = "{}"

        return data

    @classmethod
    def from_storage_dict(cls, data: dict[str, Any]) -> "MetricEvent":
        """Create MetricEvent from storage dictionary format."""
        # Convert timestamp back from string
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert conceptual_issues back to list
        if data.get("conceptual_issues") and isinstance(data["conceptual_issues"], str):
            data["conceptual_issues"] = data["conceptual_issues"].split(",")

        # Convert JSON strings back to dicts
        for field in ["feature_flags", "additional_data"]:
            if data.get(field) and isinstance(data[field], str):
                import json

                data[field] = json.loads(data[field])

        return cls(**data)


class MetricEventBuilder:
    """Builder pattern for creating structured metric events."""

    def __init__(self, event_type: MetricEventType, session_id: str):
        """Initialize metric event builder."""
        self.event = MetricEvent(event_type=event_type, session_id=session_id)

    def with_hyde_metrics(
        self,
        hyde_score: int,
        action_taken: str,
        conceptual_issues: list[str] = None,
    ) -> "MetricEventBuilder":
        """Add HyDE-specific metrics."""
        self.event.hyde_score = hyde_score
        self.event.action_taken = action_taken
        self.event.conceptual_issues = conceptual_issues or []

        # Determine specificity level from score
        if hyde_score >= 85:
            self.event.query_specificity_level = "high"
        elif hyde_score >= 40:
            self.event.query_specificity_level = "medium"
        else:
            self.event.query_specificity_level = "low"

        return self

    def with_user_feedback(
        self,
        feedback_type: str,
        feedback_target: str,
        feedback_score: int = None,
    ) -> "MetricEventBuilder":
        """Add user feedback metrics."""
        self.event.feedback_type = feedback_type
        self.event.feedback_target = feedback_target
        self.event.feedback_score = feedback_score
        return self

    def with_performance_metrics(self, response_time_ms: int, error_details: str = None) -> "MetricEventBuilder":
        """Add performance metrics."""
        self.event.response_time_ms = response_time_ms
        self.event.error_details = error_details

        # Categorize latency
        if response_time_ms < 200:
            self.event.latency_category = "fast"
        elif response_time_ms < 1000:
            self.event.latency_category = "normal"
        elif response_time_ms < 5000:
            self.event.latency_category = "slow"
        else:
            self.event.latency_category = "timeout"

        return self

    def with_query_analysis(self, query_text: str, query_category: str = None) -> "MetricEventBuilder":
        """Add privacy-safe query analysis."""
        import hashlib

        # Create privacy-safe hash
        self.event.query_text_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]

        self.event.query_length = len(query_text.split())
        self.event.query_category = query_category
        return self

    def with_vector_metrics(self, search_results: int, score_threshold: float, store_type: str) -> "MetricEventBuilder":
        """Add vector store performance metrics."""
        self.event.vector_search_results = search_results
        self.event.vector_search_score_threshold = score_threshold
        self.event.vector_store_type = store_type
        return self

    def with_domain_detection(
        self,
        domain_detected: str,
        mismatch_type: str = None,
        suggested_alternative: str = None,
    ) -> "MetricEventBuilder":
        """Add domain-specific detection metrics."""
        self.event.domain_detected = domain_detected
        self.event.mismatch_type = mismatch_type
        self.event.suggested_alternative = suggested_alternative
        return self

    def with_system_context(
        self,
        version: str,
        environment: str,
        feature_flags: dict[str, bool] = None,
    ) -> "MetricEventBuilder":
        """Add system context information."""
        self.event.system_version = version
        self.event.environment = environment
        self.event.feature_flags = feature_flags or {}
        return self

    def with_additional_data(self, **kwargs) -> "MetricEventBuilder":
        """Add additional flexible data."""
        self.event.additional_data.update(kwargs)
        return self

    def build(self) -> MetricEvent:
        """Build the final metric event."""
        return self.event


# Factory functions for common event types
def create_query_processed_event(
    session_id: str,
    hyde_score: int,
    action_taken: str,
    response_time_ms: int,
    query_text: str,
    conceptual_issues: list[str] = None,
) -> MetricEvent:
    """Create a query processed event with common metrics."""
    return (
        MetricEventBuilder(MetricEventType.QUERY_PROCESSED, session_id)
        .with_hyde_metrics(hyde_score, action_taken, conceptual_issues)
        .with_performance_metrics(response_time_ms)
        .with_query_analysis(query_text)
        .build()
    )


def create_user_feedback_event(
    session_id: str,
    feedback_type: str,
    feedback_target: str,
    feedback_score: int = None,
) -> MetricEvent:
    """Create a user feedback event."""
    return (
        MetricEventBuilder(MetricEventType.USER_FEEDBACK, session_id)
        .with_user_feedback(feedback_type, feedback_target, feedback_score)
        .build()
    )


def create_error_event(
    session_id: str,
    error_details: str,
    error_type: str,
    response_time_ms: int = None,
) -> MetricEvent:
    """Create an error event."""
    builder = MetricEventBuilder(MetricEventType.ERROR_OCCURRED, session_id).with_additional_data(error_type=error_type)

    if response_time_ms is not None:
        builder.with_performance_metrics(response_time_ms, error_details)
    else:
        builder.event.error_details = error_details

    return builder.build()


def create_conceptual_mismatch_event(
    session_id: str,
    domain_detected: str,
    mismatch_type: str,
    suggested_alternative: str,
    hyde_score: int,
) -> MetricEvent:
    """Create a conceptual mismatch detection event."""
    return (
        MetricEventBuilder(MetricEventType.CONCEPTUAL_MISMATCH, session_id)
        .with_domain_detection(domain_detected, mismatch_type, suggested_alternative)
        .with_hyde_metrics(hyde_score, "clarification")
        .build()
    )
