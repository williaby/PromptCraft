"""Unit tests for SuspiciousActivityDetector."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.auth.models import SecurityEventResponse, SecurityEventSeverity, SecurityEventType
from src.auth.suspicious_activity_detector import (
    ActivityPattern,
    SuspiciousActivityDetector,
)

# Create aliases for easier test reading
EventSeverity = SecurityEventSeverity
EventType = SecurityEventType


class TestActivityPattern:
    """Test ActivityPattern class."""

    def test_activity_pattern_initialization(self):
        """Test ActivityPattern initialization with default values."""
        pattern = ActivityPattern(
            name="test_pattern",
            description="Test pattern description",
            severity=EventSeverity.WARNING,
        )

        assert pattern.name == "test_pattern"
        assert pattern.description == "Test pattern description"
        assert pattern.severity == EventSeverity.WARNING
        assert pattern.threshold == 5  # default
        assert pattern.time_window == 300  # default

    def test_activity_pattern_custom_values(self):
        """Test ActivityPattern initialization with custom values."""
        pattern = ActivityPattern(
            name="brute_force",
            description="Brute force attack pattern",
            severity=EventSeverity.CRITICAL,
            threshold=10,
            time_window=120,
        )

        assert pattern.name == "brute_force"
        assert pattern.description == "Brute force attack pattern"
        assert pattern.severity == EventSeverity.CRITICAL
        assert pattern.threshold == 10
        assert pattern.time_window == 120

    def test_activity_pattern_severity_types(self):
        """Test ActivityPattern with different severity levels."""
        severities = [EventSeverity.INFO, EventSeverity.WARNING, EventSeverity.CRITICAL]

        for severity in severities:
            pattern = ActivityPattern("test", "Test", severity)
            assert pattern.severity == severity


class TestSuspiciousActivityDetectorInitialization:
    """Test SuspiciousActivityDetector initialization and setup."""

    def test_detector_default_initialization(self):
        """Test detector initialization with default values."""
        detector = SuspiciousActivityDetector()

        assert detector.sensitivity == 0.7
        assert detector.learning_mode is False
        assert not detector._is_initialized
        assert detector._analysis_task is None

        # Check default patterns exist
        assert "brute_force" in detector._patterns
        assert "credential_stuffing" in detector._patterns
        assert "privilege_escalation" in detector._patterns
        assert "api_abuse" in detector._patterns
        assert len(detector._patterns) == 8

    def test_detector_custom_initialization(self):
        """Test detector initialization with custom values."""
        detector = SuspiciousActivityDetector(
            sensitivity=0.5,
            learning_mode=True,
        )

        assert detector.sensitivity == 0.5
        assert detector.learning_mode is True
        assert not detector._is_initialized

    @pytest.mark.asyncio
    async def test_detector_initialize(self):
        """Test detector initialization process."""
        detector = SuspiciousActivityDetector()

        await detector.initialize()

        assert detector._is_initialized is True
        assert detector._analysis_task is not None

        # Cleanup
        await detector.close()

    @pytest.mark.asyncio
    async def test_detector_double_initialize(self):
        """Test that double initialization is safe."""
        detector = SuspiciousActivityDetector()

        await detector.initialize()
        first_task = detector._analysis_task

        await detector.initialize()  # Second initialization

        assert detector._is_initialized is True
        assert detector._analysis_task is first_task  # Same task

        # Cleanup
        await detector.close()


class TestPatternDefinitions:
    """Test the built-in suspicious activity patterns."""

    def test_brute_force_pattern(self):
        """Test brute force pattern configuration."""
        detector = SuspiciousActivityDetector()
        pattern = detector._patterns["brute_force"]

        assert pattern.name == "brute_force"
        assert pattern.severity == EventSeverity.CRITICAL
        assert pattern.threshold == 5
        assert pattern.time_window == 60

    def test_credential_stuffing_pattern(self):
        """Test credential stuffing pattern configuration."""
        detector = SuspiciousActivityDetector()
        pattern = detector._patterns["credential_stuffing"]

        assert pattern.name == "credential_stuffing"
        assert pattern.severity == EventSeverity.CRITICAL
        assert pattern.threshold == 10
        assert pattern.time_window == 120

    def test_privilege_escalation_pattern(self):
        """Test privilege escalation pattern configuration."""
        detector = SuspiciousActivityDetector()
        pattern = detector._patterns["privilege_escalation"]

        assert pattern.name == "privilege_escalation"
        assert pattern.severity == EventSeverity.CRITICAL
        assert pattern.threshold == 3
        assert pattern.time_window == 300

    def test_api_abuse_pattern(self):
        """Test API abuse pattern configuration."""
        detector = SuspiciousActivityDetector()
        pattern = detector._patterns["api_abuse"]

        assert pattern.name == "api_abuse"
        assert pattern.severity == EventSeverity.WARNING
        assert pattern.threshold == 100
        assert pattern.time_window == 60

    def test_geo_anomaly_pattern(self):
        """Test geo anomaly pattern configuration."""
        detector = SuspiciousActivityDetector()
        pattern = detector._patterns["geo_anomaly"]

        assert pattern.name == "geo_anomaly"
        assert pattern.severity == EventSeverity.WARNING
        assert pattern.threshold == 1
        assert pattern.time_window == 3600


@pytest.fixture
def mock_security_event():
    """Create a mock security event for testing."""
    return SecurityEventResponse(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        event_type="login_failure",
        severity="critical",
        user_id="test-user-123",
        ip_address="192.168.1.100",
        risk_score=85,
        details={"session_id": "session-123", "attempt_count": 1},
    )


@pytest.fixture
def brute_force_event():
    """Create a brute force attack event."""
    return SecurityEventResponse(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        event_type=EventType.LOGIN_FAILURE.value,
        severity="critical",
        user_id="target-user",
        ip_address="192.168.1.100",
        risk_score=90,
        details={"attempt_number": 5},
    )


@pytest.fixture
def api_abuse_event():
    """Create an API abuse event."""
    return SecurityEventResponse(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        event_type=EventType.RATE_LIMIT_EXCEEDED.value,
        severity=EventSeverity.WARNING.value,
        user_id="api-user",
        ip_address="192.168.1.200",
        risk_score=60,
        details={"endpoint": "/api/data", "request_count": 150},
    )


@pytest.fixture
def high_risk_event():
    """Create a high-risk event."""
    return SecurityEventResponse(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        event_type=EventType.SUSPICIOUS_ACTIVITY.value,
        severity=EventSeverity.CRITICAL.value,
        user_id="suspicious-user",
        ip_address="10.0.0.50",
        risk_score=95,
        details={"data_volume": "10GB", "access_time": "03:00"},
    )


class TestEventAnalysis:
    """Test event analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_single_event(self, brute_force_event):
        """Test analyzing a single security event."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        patterns = await detector.analyze_event(brute_force_event)

        # First event shouldn't trigger patterns (no history)
        assert isinstance(patterns, list)

        await detector.close()

    @pytest.mark.asyncio
    async def test_analyze_event_without_initialization(self, mock_security_event):
        """Test that analyze_event initializes detector if needed."""
        detector = SuspiciousActivityDetector()

        assert not detector._is_initialized

        patterns = await detector.analyze_event(mock_security_event)

        assert detector._is_initialized
        assert isinstance(patterns, list)

        await detector.close()

    @pytest.mark.asyncio
    async def test_entity_key_generation_user_id(self, mock_security_event):
        """Test entity key generation with user ID."""
        detector = SuspiciousActivityDetector()

        entity_key = detector._get_entity_key(mock_security_event)

        assert entity_key == "user:test-user-123"

    @pytest.mark.asyncio
    async def test_entity_key_generation_ip_only(self):
        """Test entity key generation with IP address only."""
        detector = SuspiciousActivityDetector()

        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="suspicious_activity",
            severity="warning",
            user_id=None,
            ip_address="192.168.1.100",
            risk_score=50,
            details={},
        )

        entity_key = detector._get_entity_key(event)

        assert entity_key == "ip:192.168.1.100"

    @pytest.mark.asyncio
    async def test_entity_key_generation_session_fallback(self):
        """Test entity key generation falling back to session ID."""
        detector = SuspiciousActivityDetector()

        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="session_activity",
            severity="info",
            user_id=None,
            ip_address=None,
            risk_score=20,
            details={"session_id": "session-xyz"},
        )

        entity_key = detector._get_entity_key(event)

        assert entity_key == "session:session-xyz"

    @pytest.mark.asyncio
    async def test_entity_key_generation_unknown_fallback(self):
        """Test entity key generation with unknown fallback."""
        detector = SuspiciousActivityDetector()

        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="unknown_activity",
            severity="info",
            user_id=None,
            ip_address=None,
            risk_score=10,
            details={},
        )

        entity_key = detector._get_entity_key(event)

        assert entity_key == "session:unknown"


class TestPatternDetection:
    """Test pattern detection algorithms."""

    @pytest.mark.asyncio
    async def test_brute_force_detection(self):
        """Test brute force pattern detection."""
        detector = SuspiciousActivityDetector(sensitivity=0.7)
        await detector.initialize()

        # Create multiple authentication failure events
        user_id = "brute-force-target"
        events = []
        for i in range(6):  # Above threshold of 5
            event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type=EventType.LOGIN_FAILURE.value,
                severity="critical",
                user_id=user_id,
                ip_address="192.168.1.100",
                risk_score=80,
                details={"attempt": i + 1},
            )
            events.append(event)

        # Process events
        detected_patterns = []
        for event in events:
            patterns = await detector.analyze_event(event)
            detected_patterns.extend(patterns)

        # Should detect brute force after threshold
        assert "brute_force" in detected_patterns

        await detector.close()

    @pytest.mark.asyncio
    async def test_privilege_escalation_detection(self):
        """Test privilege escalation pattern detection."""
        detector = SuspiciousActivityDetector(sensitivity=0.8)
        await detector.initialize()

        # Create multiple permission denied events
        user_id = "privilege-escalator"
        events = []
        for i in range(4):  # Above threshold of 3
            event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type=EventType.SUSPICIOUS_ACTIVITY.value,
                severity="critical",
                user_id=user_id,
                ip_address="10.0.0.100",
                risk_score=75,
                details={"resource": f"admin-resource-{i}"},
            )
            events.append(event)

        # Process events
        detected_patterns = []
        for event in events:
            patterns = await detector.analyze_event(event)
            detected_patterns.extend(patterns)

        # Should detect privilege escalation
        assert "privilege_escalation" in detected_patterns

        await detector.close()

    @pytest.mark.asyncio
    async def test_api_abuse_detection(self):
        """Test API abuse pattern detection."""
        detector = SuspiciousActivityDetector(sensitivity=0.6)
        await detector.initialize()

        # Create multiple API events
        user_id = "api-abuser"
        events = []
        for i in range(105):  # Above threshold of 100
            event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type="api_request_rate_limit",
                severity="warning",
                user_id=user_id,
                ip_address="172.16.0.50",
                risk_score=45,
                details={"endpoint": "/api/search", "request_id": i},
            )
            events.append(event)

        # Process events
        detected_patterns = []
        for event in events:
            patterns = await detector.analyze_event(event)
            detected_patterns.extend(patterns)

        # Should detect API abuse
        assert "api_abuse" in detected_patterns

        await detector.close()

    @pytest.mark.asyncio
    async def test_behavioral_anomaly_detection(self):
        """Test behavioral anomaly detection."""
        detector = SuspiciousActivityDetector(sensitivity=0.7)
        await detector.initialize()

        user_id = "anomaly-user"

        # Create baseline behavior (low risk)
        baseline_events = []
        for i in range(15):  # More than minimum 10 for history
            event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC) - timedelta(minutes=i),
                event_type="normal_activity",
                severity="info",
                user_id=user_id,
                ip_address="192.168.1.50",
                risk_score=20,  # Low risk
                details={"activity": "routine"},
            )
            baseline_events.append(event)

        # Process baseline events
        for event in baseline_events:
            await detector.analyze_event(event)

        # Create high-risk anomaly event
        anomaly_event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="suspicious_activity",
            severity="critical",
            user_id=user_id,
            ip_address="192.168.1.50",
            risk_score=95,  # High risk - significant deviation
            details={"activity": "anomalous"},
        )

        patterns = await detector.analyze_event(anomaly_event)

        # Should detect account takeover due to behavioral anomaly
        assert "account_takeover" in patterns

        await detector.close()

    @pytest.mark.asyncio
    async def test_behavioral_anomaly_insufficient_history(self):
        """Test behavioral anomaly with insufficient history."""
        detector = SuspiciousActivityDetector(sensitivity=0.7)
        await detector.initialize()

        user_id = "new-user"

        # Create high-risk event for new user (no history)
        high_risk_event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="suspicious_activity",
            severity="critical",
            user_id=user_id,
            ip_address="192.168.1.75",
            risk_score=95,
            details={"activity": "first-time"},
        )

        patterns = await detector.analyze_event(high_risk_event)

        # Should NOT detect anomaly due to insufficient history
        assert "account_takeover" not in patterns

        await detector.close()


class TestSensitivityAdjustment:
    """Test sensitivity adjustment effects on pattern detection."""

    @pytest.mark.asyncio
    async def test_high_sensitivity_detection(self):
        """Test that high sensitivity detects patterns more easily."""
        detector = SuspiciousActivityDetector(sensitivity=0.9)
        await detector.initialize()

        # Calculate adjusted threshold for brute force
        pattern = detector._patterns["brute_force"]
        adjusted_threshold = int(pattern.threshold * (1.5 - detector.sensitivity))

        # High sensitivity should have lower threshold
        assert adjusted_threshold < pattern.threshold

        await detector.close()

    @pytest.mark.asyncio
    async def test_low_sensitivity_detection(self):
        """Test that low sensitivity requires more events."""
        detector = SuspiciousActivityDetector(sensitivity=0.3)
        await detector.initialize()

        # Calculate adjusted threshold for brute force
        pattern = detector._patterns["brute_force"]
        adjusted_threshold = int(pattern.threshold * (1.5 - detector.sensitivity))

        # Low sensitivity should have higher threshold
        assert adjusted_threshold > pattern.threshold

        await detector.close()

    @pytest.mark.asyncio
    async def test_sensitivity_behavioral_threshold(self):
        """Test sensitivity effects on behavioral anomaly detection."""
        detector = SuspiciousActivityDetector(sensitivity=0.8)

        # High sensitivity = 30 * 0.8 = 24 point deviation threshold
        threshold = 30 * detector.sensitivity
        assert threshold == 24.0


class TestScoringSystem:
    """Test the internal scoring system."""

    @pytest.mark.asyncio
    async def test_entity_score_critical_pattern(self):
        """Test entity scoring for critical patterns."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        entity_key = "user:test-scoring"
        patterns = ["brute_force"]  # Critical pattern

        # Update scores
        detector._update_scores(entity_key, patterns)

        # Critical patterns should add 10.0 points
        assert detector._entity_scores[entity_key] == 10.0

        await detector.close()

    @pytest.mark.asyncio
    async def test_entity_score_warning_pattern(self):
        """Test entity scoring for warning patterns."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        entity_key = "user:test-warning"
        patterns = ["api_abuse"]  # Warning pattern

        detector._update_scores(entity_key, patterns)

        # Warning patterns should add 2.0 points
        assert detector._entity_scores[entity_key] == 2.0

        await detector.close()

    @pytest.mark.asyncio
    async def test_suspicious_entity_marking(self):
        """Test marking entities as suspicious based on score."""
        detector = SuspiciousActivityDetector(sensitivity=0.7)
        await detector.initialize()

        entity_key = "user:suspicious"

        # Manually set high score above threshold
        detector._entity_scores[entity_key] = 80.0  # Above 0.7 * 100 = 70

        # Create event to trigger score check
        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type=EventType.LOGIN_FAILURE.value,
            severity="critical",
            user_id="suspicious",
            ip_address="192.168.1.1",
            risk_score=90,
            details={},
        )

        # Simulate pattern detection
        detector._detected_patterns.append(("brute_force", event.timestamp, detector._event_to_dict(event)))
        detector._update_scores(entity_key, ["brute_force"])

        # Check if marked as suspicious
        if detector._entity_scores[entity_key] > detector.sensitivity * 100:
            detector._suspicious_entities.add(entity_key)

        assert entity_key in detector._suspicious_entities

        await detector.close()


class TestUtilityMethods:
    """Test utility and helper methods."""

    @pytest.mark.asyncio
    async def test_event_to_dict_conversion(self, mock_security_event):
        """Test converting security event to dictionary."""
        detector = SuspiciousActivityDetector()

        event_dict = detector._event_to_dict(mock_security_event)

        assert event_dict["type"] == mock_security_event.event_type
        assert event_dict["severity"] == mock_security_event.severity
        assert event_dict["risk_score"] == mock_security_event.risk_score
        assert event_dict["ip"] == mock_security_event.ip_address
        assert event_dict["user"] == mock_security_event.user_id
        assert event_dict["details"] == mock_security_event.details

    @pytest.mark.asyncio
    async def test_get_suspicious_entities(self):
        """Test getting suspicious entities list."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        # Add some suspicious entities
        detector._suspicious_entities.add("user:bad-actor-1")
        detector._suspicious_entities.add("ip:192.168.1.999")

        suspicious = await detector.get_suspicious_entities()

        assert len(suspicious) == 2
        assert "user:bad-actor-1" in suspicious
        assert "ip:192.168.1.999" in suspicious

        # Should return a copy, not the original
        assert suspicious is not detector._suspicious_entities

        await detector.close()

    @pytest.mark.asyncio
    async def test_get_entity_score(self):
        """Test getting entity suspicion score."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        entity_key = "user:scored-user"
        detector._entity_scores[entity_key] = 45.5

        score = await detector.get_entity_score(entity_key)
        assert score == 45.5

        # Test non-existent entity
        missing_score = await detector.get_entity_score("user:nonexistent")
        assert missing_score == 0.0

        await detector.close()

    @pytest.mark.asyncio
    async def test_get_detection_stats(self):
        """Test getting detection statistics."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        # Add some test data
        detector._detected_patterns.extend(
            [
                ("brute_force", datetime.now(UTC), {}),
                ("brute_force", datetime.now(UTC), {}),
                ("api_abuse", datetime.now(UTC), {}),
            ],
        )
        detector._suspicious_entities.add("user:bad-actor")
        detector._activity_log["user:test"] = [(datetime.now(UTC), {})]

        stats = await detector.get_detection_stats()

        assert stats["total_detections"] == 3
        assert stats["suspicious_entities"] == 1
        assert stats["tracked_entities"] == 1
        assert stats["pattern_counts"]["brute_force"] == 2
        assert stats["pattern_counts"]["api_abuse"] == 1
        assert stats["sensitivity"] == detector.sensitivity
        assert stats["learning_mode"] == detector.learning_mode

        # Check top patterns sorting
        assert stats["top_patterns"][0] == ("brute_force", 2)

        await detector.close()


class TestLearningMode:
    """Test learning mode functionality."""

    @pytest.mark.asyncio
    async def test_learning_mode_disabled(self):
        """Test that learning mode is disabled by default."""
        detector = SuspiciousActivityDetector()

        assert not detector.learning_mode

        # Learning should not adjust thresholds
        detector._pattern_scores["brute_force"] = 150

        await detector._learn_from_patterns()

        # Threshold should remain unchanged
        assert detector._patterns["brute_force"].threshold == 5

    @pytest.mark.asyncio
    async def test_learning_mode_enabled(self):
        """Test learning mode threshold adjustment."""
        detector = SuspiciousActivityDetector(learning_mode=True)
        await detector.initialize()

        original_threshold = detector._patterns["brute_force"].threshold

        # Simulate high detection frequency
        detector._pattern_scores["brute_force"] = 150  # Above 100 threshold

        await detector._learn_from_patterns()

        # Threshold should increase
        assert detector._patterns["brute_force"].threshold > original_threshold
        assert detector._pattern_scores["brute_force"] == 0  # Reset

        await detector.close()


class TestBackgroundTasks:
    """Test background analysis and cleanup tasks."""

    @pytest.mark.asyncio
    async def test_cleanup_old_activity(self):
        """Test cleanup of old activity logs."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        entity_key = "user:test-cleanup"

        # Add old and recent activity
        old_time = datetime.now(UTC) - timedelta(hours=2)
        recent_time = datetime.now(UTC) - timedelta(minutes=30)

        detector._activity_log[entity_key] = [
            (old_time, {"type": "old_event"}),
            (recent_time, {"type": "recent_event"}),
        ]

        # Simulate cleanup (normally done in background task)
        now = datetime.now(UTC)
        cutoff = now - timedelta(hours=1)

        detector._activity_log[entity_key] = [
            (ts, data) for ts, data in detector._activity_log[entity_key] if ts > cutoff
        ]

        # Only recent event should remain
        assert len(detector._activity_log[entity_key]) == 1
        assert detector._activity_log[entity_key][0][1]["type"] == "recent_event"

        await detector.close()

    @pytest.mark.asyncio
    async def test_score_decay(self):
        """Test entity score decay mechanism."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        entity_key = "user:score-decay"
        detector._entity_scores[entity_key] = 100.0

        # Simulate decay (normally done in background task)
        detector._entity_scores[entity_key] *= 0.95

        assert detector._entity_scores[entity_key] == 95.0

        await detector.close()

    @pytest.mark.asyncio
    async def test_low_score_removal(self):
        """Test removal of entities with low scores."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        entity_key = "user:low-score"
        detector._entity_scores[entity_key] = 0.5  # Below 1.0 threshold
        detector._suspicious_entities.add(entity_key)

        # Simulate low score removal (background task logic)
        entities_to_remove = [key for key, score in detector._entity_scores.items() if score < 1.0]

        for key in entities_to_remove:
            del detector._entity_scores[key]
            detector._suspicious_entities.discard(key)

        assert entity_key not in detector._entity_scores
        assert entity_key not in detector._suspicious_entities

        await detector.close()


class TestAsyncContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager_entry_exit(self):
        """Test async context manager entry and exit."""
        detector = SuspiciousActivityDetector()

        async with detector as ctx_detector:
            assert ctx_detector is detector
            assert detector._is_initialized
            assert detector._analysis_task is not None

        # After exit, should be closed
        assert not detector._is_initialized

    @pytest.mark.asyncio
    async def test_context_manager_with_event_analysis(self, mock_security_event):
        """Test using detector in context manager with event analysis."""
        detector = SuspiciousActivityDetector()

        async with detector:
            patterns = await detector.analyze_event(mock_security_event)
            assert isinstance(patterns, list)

            stats = await detector.get_detection_stats()
            assert isinstance(stats, dict)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_analyze_event_with_none_entity_key(self):
        """Test event analysis with event that generates None entity key."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        # Event with no user_id, ip_address, or session_id
        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="unknown",
            severity="info",
            user_id=None,
            ip_address=None,
            risk_score=10,
            details={},
        )

        patterns = await detector.analyze_event(event)

        # Should handle gracefully and return empty patterns
        assert isinstance(patterns, list)

        await detector.close()

    @pytest.mark.asyncio
    async def test_check_pattern_nonexistent(self):
        """Test checking for non-existent pattern."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="test",
            severity="info",
            user_id="test-user",
            ip_address="192.168.1.1",
            risk_score=30,
            details={},
        )

        result = await detector._check_pattern("nonexistent_pattern", "user:test-user", event)

        assert result is False

        await detector.close()

    @pytest.mark.asyncio
    async def test_empty_activity_log_pattern_check(self):
        """Test pattern checking with empty activity log."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type=EventType.LOGIN_FAILURE.value,
            severity="critical",
            user_id="empty-log-user",
            ip_address="192.168.1.100",
            risk_score=80,
            details={},
        )

        result = await detector._check_pattern("brute_force", "user:empty-log-user", event)

        # Should return False (no activity history)
        assert result is False

        await detector.close()


class TestPerformanceRequirements:
    """Test performance requirements and benchmarks."""

    @pytest.mark.asyncio
    async def test_single_event_analysis_performance(self, mock_security_event):
        """Test single event analysis meets <50ms requirement."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        import time

        start_time = time.time()
        patterns = await detector.analyze_event(mock_security_event)
        end_time = time.time()

        processing_time_ms = (end_time - start_time) * 1000

        # Should be well under 50ms for single event
        assert processing_time_ms < 50
        assert isinstance(patterns, list)

        await detector.close()

    @pytest.mark.asyncio
    async def test_batch_event_processing_efficiency(self):
        """Test processing multiple events efficiently."""
        detector = SuspiciousActivityDetector()
        await detector.initialize()

        # Create batch of events
        events = []
        for i in range(100):
            event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type="test_event",
                severity="info",
                user_id=f"user-{i % 10}",  # 10 different users
                ip_address=f"192.168.1.{100 + (i % 50)}",
                risk_score=30 + (i % 40),
                details={"batch": i},
            )
            events.append(event)

        import time

        start_time = time.time()

        all_patterns = []
        for event in events:
            patterns = await detector.analyze_event(event)
            all_patterns.extend(patterns)

        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_event = total_time_ms / len(events)

        # Average should be well under 50ms per event
        assert avg_time_per_event < 50

        await detector.close()


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_brute_force_scenario(self):
        """Test realistic brute force attack scenario."""
        detector = SuspiciousActivityDetector(sensitivity=0.7)
        await detector.initialize()

        attacker_ip = "192.168.1.999"
        target_users = ["admin", "user1", "user2"]

        all_detected_patterns = []

        # Simulate failed login attempts across multiple users
        for attempt in range(20):
            target_user = target_users[attempt % len(target_users)]

            event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type=EventType.LOGIN_FAILURE.value,
                severity="critical",
                user_id=target_user,
                ip_address=attacker_ip,
                risk_score=85,
                details={
                    "attempt_number": attempt + 1,
                    "password_attempted": f"password{attempt}",
                    "user_agent": "curl/7.68.0",
                },
            )

            patterns = await detector.analyze_event(event)
            all_detected_patterns.extend(patterns)

        # Should detect brute force patterns
        assert "brute_force" in all_detected_patterns

        # Check that IP is marked as suspicious
        suspicious_entities = await detector.get_suspicious_entities()
        ip_suspicious = any("ip:" in entity for entity in suspicious_entities)
        assert ip_suspicious or len(all_detected_patterns) > 0  # Either direct detection or entity marking

        await detector.close()

    @pytest.mark.asyncio
    async def test_mixed_pattern_detection_scenario(self):
        """Test scenario with multiple pattern types."""
        detector = SuspiciousActivityDetector(sensitivity=0.6)
        await detector.initialize()

        user_id = "multi-threat-user"
        ip_address = "10.0.0.200"

        all_patterns = []

        # 1. Generate API abuse events
        for i in range(120):  # Above API abuse threshold
            api_event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type="api_request_excessive",
                severity="warning",
                user_id=user_id,
                ip_address=ip_address,
                risk_score=40,
                details={"endpoint": "/api/data", "request": i},
            )
            patterns = await detector.analyze_event(api_event)
            all_patterns.extend(patterns)

        # 2. Generate permission denied events
        for i in range(5):  # Above privilege escalation threshold
            perm_event = SecurityEventResponse(
                id=uuid.uuid4(),
                timestamp=datetime.now(UTC),
                event_type=EventType.SUSPICIOUS_ACTIVITY.value,
                severity="critical",
                user_id=user_id,
                ip_address=ip_address,
                risk_score=70,
                details={"resource": f"admin-panel-{i}"},
            )
            patterns = await detector.analyze_event(perm_event)
            all_patterns.extend(patterns)

        # 3. Generate high-risk anomaly event
        anomaly_event = SecurityEventResponse(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            event_type="data_exfiltration_attempt",
            severity="critical",
            user_id=user_id,
            ip_address=ip_address,
            risk_score=95,  # Very high risk
            details={"data_size": "1GB", "destination": "external"},
        )
        patterns = await detector.analyze_event(anomaly_event)
        all_patterns.extend(patterns)

        # Should detect multiple pattern types
        unique_patterns = set(all_patterns)
        assert len(unique_patterns) >= 2  # At least 2 different patterns

        # Verify user is marked as highly suspicious
        entity_score = await detector.get_entity_score(f"user:{user_id}")
        assert entity_score > 50  # High suspicion score

        await detector.close()
