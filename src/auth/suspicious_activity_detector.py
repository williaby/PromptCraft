"""Suspicious activity detection for security monitoring."""

import asyncio
import contextlib
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import Any

from .models import SecurityEventResponse, SecurityEventSeverity, SecurityEventType

logger = logging.getLogger(__name__)


class ActivityPattern:
    """Represents a suspicious activity pattern."""

    def __init__(
        self,
        name: str,
        description: str,
        severity: SecurityEventSeverity,
        threshold: int = 5,
        time_window: int = 300,
    ) -> None:
        """Initialize activity pattern.

        Args:
            name: Pattern name
            description: Pattern description
            severity: Severity level when detected
            threshold: Number of events to trigger detection
            time_window: Time window in seconds
        """
        self.name = name
        self.description = description
        self.severity = severity
        self.threshold = threshold
        self.time_window = time_window


class SuspiciousActivityDetector:
    """Advanced suspicious activity detection system."""

    def __init__(
        self,
        sensitivity: float = 0.7,
        learning_mode: bool = False,
    ) -> None:
        """Initialize suspicious activity detector.

        Args:
            sensitivity: Detection sensitivity (0.0 to 1.0)
            learning_mode: Whether to learn from activity patterns
        """
        self.sensitivity = sensitivity
        self.learning_mode = learning_mode

        # Pattern definitions
        self._patterns: dict[str, ActivityPattern] = self._init_patterns()

        # Activity tracking
        self._activity_log: dict[str, list[tuple[datetime, dict[str, Any]]]] = defaultdict(list)
        self._detected_patterns: list[tuple[str, datetime, dict[str, Any]]] = []
        self._suspicious_entities: set[str] = set()

        # Machine learning state (simulated)
        self._pattern_scores: dict[str, float] = defaultdict(float)
        self._entity_scores: dict[str, float] = defaultdict(float)

        # Background tasks
        self._analysis_task: asyncio.Task | None = None
        self._is_initialized = False

    def _init_patterns(self) -> dict[str, ActivityPattern]:
        """Initialize suspicious activity patterns."""
        return {
            "brute_force": ActivityPattern(
                name="brute_force",
                description="Multiple failed authentication attempts",
                severity=SecurityEventSeverity.CRITICAL,
                threshold=5,
                time_window=60,
            ),
            "credential_stuffing": ActivityPattern(
                name="credential_stuffing",
                description="Rapid login attempts with different credentials",
                severity=SecurityEventSeverity.CRITICAL,
                threshold=10,
                time_window=120,
            ),
            "privilege_escalation": ActivityPattern(
                name="privilege_escalation",
                description="Attempts to access elevated privileges",
                severity=SecurityEventSeverity.CRITICAL,
                threshold=3,
                time_window=300,
            ),
            "data_exfiltration": ActivityPattern(
                name="data_exfiltration",
                description="Unusual data access patterns",
                severity=SecurityEventSeverity.CRITICAL,
                threshold=5,
                time_window=600,
            ),
            "account_takeover": ActivityPattern(
                name="account_takeover",
                description="Suspicious account behavior changes",
                severity=SecurityEventSeverity.CRITICAL,
                threshold=3,
                time_window=180,
            ),
            "api_abuse": ActivityPattern(
                name="api_abuse",
                description="Excessive API requests",
                severity=SecurityEventSeverity.WARNING,
                threshold=100,
                time_window=60,
            ),
            "geo_anomaly": ActivityPattern(
                name="geo_anomaly",
                description="Login from unusual geographic location",
                severity=SecurityEventSeverity.WARNING,
                threshold=1,
                time_window=3600,
            ),
            "time_anomaly": ActivityPattern(
                name="time_anomaly",
                description="Activity at unusual times",
                severity=SecurityEventSeverity.INFO,
                threshold=5,
                time_window=3600,
            ),
        }

    async def initialize(self) -> None:
        """Initialize the suspicious activity detector."""
        if self._is_initialized:
            return

        # Start analysis task
        self._analysis_task = asyncio.create_task(self._analyze_patterns())

        self._is_initialized = True
        logger.info(
            "SuspiciousActivityDetector initialized with sensitivity=%.2f, learning=%s",
            self.sensitivity,
            self.learning_mode,
        )

    async def analyze_event(self, event: SecurityEventResponse) -> list[str]:
        """Analyze a security event for suspicious patterns.

        Args:
            event: Security event to analyze

        Returns:
            List of detected pattern names
        """
        if not self._is_initialized:
            await self.initialize()

        detected_patterns = []

        # Track activity
        entity_key = self._get_entity_key(event)
        if entity_key:
            self._activity_log[entity_key].append((event.timestamp, self._event_to_dict(event)))

        # Check for brute force
        if event.event_type == SecurityEventType.LOGIN_FAILURE.value:
            if await self._check_pattern("brute_force", entity_key, event):
                detected_patterns.append("brute_force")

        # Check for privilege escalation (using SUSPICIOUS_ACTIVITY as closest match)
        if event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY.value:
            if await self._check_pattern("privilege_escalation", entity_key, event):
                detected_patterns.append("privilege_escalation")

        # Check for API abuse
        if "api" in event.event_type.lower():
            if await self._check_pattern("api_abuse", entity_key, event):
                detected_patterns.append("api_abuse")

        # Check for anomalies based on risk score
        if event.risk_score > 70:
            # High risk events trigger additional checks
            if await self._check_behavioral_anomaly(entity_key, event):
                detected_patterns.append("account_takeover")

        # Update scores
        if detected_patterns:
            self._update_scores(entity_key, detected_patterns)

            # Mark as suspicious if threshold met
            if self._entity_scores[entity_key] > self.sensitivity * 100:
                self._suspicious_entities.add(entity_key)

        # Store detected patterns
        for pattern in detected_patterns:
            self._detected_patterns.append((pattern, event.timestamp, self._event_to_dict(event)))

        return detected_patterns

    def _get_entity_key(self, event: SecurityEventResponse) -> str:
        """Get entity key for tracking.

        Args:
            event: Security event

        Returns:
            Entity key string
        """
        if event.user_id:
            return f"user:{event.user_id}"
        if event.ip_address:
            return f"ip:{event.ip_address}"
        return f"session:{event.details.get('session_id', 'unknown')}"

    def _event_to_dict(self, event: SecurityEventResponse) -> dict[str, Any]:
        """Convert event to dictionary for storage.

        Args:
            event: Security event

        Returns:
            Event dictionary
        """
        return {
            "type": event.event_type,
            "severity": event.severity,
            "risk_score": event.risk_score,
            "ip": event.ip_address,
            "user": event.user_id,
            "details": event.details,
        }

    async def _check_pattern(
        self,
        pattern_name: str,
        entity_key: str,
        event: SecurityEventResponse,
    ) -> bool:
        """Check if a pattern is detected.

        Args:
            pattern_name: Name of pattern to check
            entity_key: Entity identifier
            event: Current event

        Returns:
            True if pattern detected
        """
        pattern = self._patterns.get(pattern_name)
        if not pattern:
            return False

        # Get recent activity
        now = event.timestamp
        cutoff = now - timedelta(seconds=pattern.time_window)

        recent_activity = [(ts, data) for ts, data in self._activity_log[entity_key] if ts > cutoff]

        # Apply sensitivity adjustment
        adjusted_threshold = int(pattern.threshold * (1.5 - self.sensitivity))

        # Check if threshold met
        return len(recent_activity) >= adjusted_threshold

    async def _check_behavioral_anomaly(
        self,
        entity_key: str,
        event: SecurityEventResponse,
    ) -> bool:
        """Check for behavioral anomalies.

        Args:
            entity_key: Entity identifier
            event: Current event

        Returns:
            True if anomaly detected
        """
        # Get historical behavior
        history = self._activity_log[entity_key]

        if len(history) < 10:
            # Not enough history
            return False

        # Simple anomaly detection based on risk score deviation
        historical_scores = [data["risk_score"] for _, data in history[-10:]]
        avg_score = sum(historical_scores) / len(historical_scores)

        # Check if current score deviates significantly
        deviation = abs(event.risk_score - avg_score)
        threshold = 30 * self.sensitivity

        return deviation > threshold

    def _update_scores(self, entity_key: str, patterns: list[str]) -> None:
        """Update pattern and entity scores.

        Args:
            entity_key: Entity identifier
            patterns: Detected patterns
        """
        for pattern_name in patterns:
            pattern = self._patterns[pattern_name]

            # Update pattern score
            self._pattern_scores[pattern_name] += 1.0

            # Update entity score based on severity
            if pattern.severity == SecurityEventSeverity.CRITICAL:
                self._entity_scores[entity_key] += 10.0
            elif pattern.severity == SecurityEventSeverity.CRITICAL:
                self._entity_scores[entity_key] += 5.0
            elif pattern.severity == SecurityEventSeverity.WARNING:
                self._entity_scores[entity_key] += 2.0
            else:
                self._entity_scores[entity_key] += 1.0

    async def _analyze_patterns(self) -> None:
        """Background task to analyze activity patterns."""
        while True:
            try:
                await asyncio.sleep(30)  # Analyze every 30 seconds

                # Clean old activity
                now = datetime.now(UTC)
                cutoff = now - timedelta(hours=1)

                for entity_key in list(self._activity_log.keys()):
                    self._activity_log[entity_key] = [
                        (ts, data) for ts, data in self._activity_log[entity_key] if ts > cutoff
                    ]

                    # Remove empty entries
                    if not self._activity_log[entity_key]:
                        del self._activity_log[entity_key]

                # Decay scores
                for key in list(self._entity_scores.keys()):
                    self._entity_scores[key] *= 0.95

                    # Remove low scores
                    if self._entity_scores[key] < 1.0:
                        del self._entity_scores[key]

                        # Remove from suspicious if score too low
                        if key in self._suspicious_entities:
                            self._suspicious_entities.remove(key)

                # Learn from patterns if enabled
                if self.learning_mode:
                    await self._learn_from_patterns()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Pattern analysis error: %s", e)

    async def _learn_from_patterns(self) -> None:
        """Learn from detected patterns to improve detection."""
        # Only learn if learning mode is enabled
        if not self.learning_mode:
            return

        # Simulate learning by adjusting thresholds based on detection frequency
        for pattern_name, score in self._pattern_scores.items():
            pattern = self._patterns[pattern_name]

            # If pattern is detected too frequently, it might be too sensitive
            if score > 100:
                pattern.threshold = min(pattern.threshold + 1, pattern.threshold * 2)
                self._pattern_scores[pattern_name] = 0  # Reset
                logger.info("Adjusted %s threshold to %d", pattern_name, pattern.threshold)

    async def get_suspicious_entities(self) -> set[str]:
        """Get list of suspicious entities.

        Returns:
            Set of suspicious entity identifiers
        """
        return self._suspicious_entities.copy()

    async def get_entity_score(self, entity_key: str) -> float:
        """Get suspicion score for an entity.

        Args:
            entity_key: Entity identifier

        Returns:
            Suspicion score
        """
        return self._entity_scores.get(entity_key, 0.0)

    async def get_detection_stats(self) -> dict[str, Any]:
        """Get detection statistics.

        Returns:
            Detection statistics
        """
        pattern_counts = defaultdict(int)
        for pattern_name, _, _ in self._detected_patterns:
            pattern_counts[pattern_name] += 1

        return {
            "total_detections": len(self._detected_patterns),
            "suspicious_entities": len(self._suspicious_entities),
            "tracked_entities": len(self._activity_log),
            "pattern_counts": dict(pattern_counts),
            "top_patterns": sorted(
                pattern_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            "sensitivity": self.sensitivity,
            "learning_mode": self.learning_mode,
        }

    async def close(self) -> None:
        """Close the suspicious activity detector."""
        if self._analysis_task:
            self._analysis_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._analysis_task

        self._is_initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Async context manager exit."""
        await self.close()
        return False
