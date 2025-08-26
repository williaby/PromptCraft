"""Comprehensive unit tests for SuspiciousActivityDetector.

Tests behavioral analysis, anomaly detection, risk scoring, and pattern recognition
for identifying suspicious user activities with machine learning capabilities.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.models import SecurityEvent, SecurityEventType
from src.auth.services.suspicious_activity_detector import (
    BehaviorProfile,
    RiskScore,
    SuspiciousActivityDetector,
)


class TestSuspiciousActivityDetectorInitialization:
    """Test suspicious activity detector initialization."""

    def test_init_default_configuration(self):
        """Test detector initialization with default settings."""
        detector = SuspiciousActivityDetector()

        # Check default thresholds
        assert detector.suspicious_threshold == 0.7
        assert detector.anomaly_threshold == 0.8
        assert detector.learning_period_days == 30
        assert detector.min_baseline_events == 50

        # Check analysis windows
        assert detector.short_term_window_hours == 1
        assert detector.medium_term_window_hours == 24
        assert detector.long_term_window_days == 7

        # Check internal state
        assert isinstance(detector._user_profiles, dict)
        assert isinstance(detector._activity_patterns, dict)
        assert isinstance(detector._risk_scores, dict)
        assert detector._db is not None
        assert detector._security_logger is not None

    def test_init_custom_configuration(self):
        """Test initialization with custom settings."""
        detector = SuspiciousActivityDetector(
            suspicious_threshold=0.6,
            anomaly_threshold=0.9,
            learning_period_days=14,
            min_baseline_events=25,
        )

        assert detector.suspicious_threshold == 0.6
        assert detector.anomaly_threshold == 0.9
        assert detector.learning_period_days == 14
        assert detector.min_baseline_events == 25

    def test_init_with_dependencies(self):
        """Test initialization with custom dependencies."""
        mock_db = MagicMock()
        mock_logger = MagicMock()

        detector = SuspiciousActivityDetector(db=mock_db, security_logger=mock_logger)

        assert detector._db == mock_db
        assert detector._security_logger == mock_logger


class TestSuspiciousActivityDetectorBehaviorAnalysis:
    """Test behavioral pattern analysis and profiling."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies."""
        with patch("src.auth.services.suspicious_activity_detector.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.suspicious_activity_detector.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                detector = SuspiciousActivityDetector()
                detector._db = mock_db
                detector._security_logger = mock_logger

                yield detector

    async def test_build_behavior_profile_sufficient_data(self, detector):
        """Test building behavior profile with sufficient historical data."""
        user_id = "profile_user"

        # Mock historical events for profile building
        base_time = datetime.now() - timedelta(days=20)
        mock_events = []

        # Regular login pattern: weekdays 9 AM - 5 PM
        for day in range(20):
            for hour in [9, 12, 17]:  # Login, lunch, logout
                event = SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user_id,
                    ip_address="192.168.1.100",
                    timestamp=base_time + timedelta(days=day, hours=hour),
                    severity="low",
                    source="auth",
                    metadata={"device": "laptop", "browser": "Chrome"},
                )
                mock_events.append(event)

        detector._db.get_events_by_user_id.return_value = mock_events

        profile = await detector.build_behavior_profile(user_id)

        assert profile is not None
        assert profile.user_id == user_id
        assert profile.total_events >= 50  # Should meet minimum baseline
        assert len(profile.typical_hours) > 0
        assert len(profile.common_ip_addresses) > 0
        assert len(profile.frequent_locations) >= 0  # May be empty if geolocation not available

        # Should identify weekday business hours pattern
        assert any(hour in range(9, 18) for hour in profile.typical_hours)

    async def test_build_behavior_profile_insufficient_data(self, detector):
        """Test building behavior profile with insufficient historical data."""
        user_id = "new_user"

        # Mock limited historical events
        mock_events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address="192.168.1.100",
                timestamp=datetime.now(),
                severity="low",
                source="auth",
            ),
        ]

        detector._db.get_events_by_user_id.return_value = mock_events

        profile = await detector.build_behavior_profile(user_id)

        # Should still create profile but mark as insufficient
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.total_events == 1
        assert profile.confidence_score < 0.5  # Low confidence due to insufficient data

    async def test_analyze_time_pattern_suspicious(self, detector):
        """Test time pattern analysis detecting suspicious activity."""
        user_id = "time_pattern_user"

        # Build baseline profile (business hours user)
        baseline_events = []
        base_time = datetime.now() - timedelta(days=30)

        for day in range(30):
            for hour in range(9, 18):  # Business hours
                event = SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user_id,
                    timestamp=base_time + timedelta(days=day, hours=hour),
                    severity="low",
                    source="auth",
                )
                baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test suspicious activity (login at 3 AM)
        suspicious_time = datetime.now().replace(hour=3, minute=0, second=0)
        suspicion_score = await detector.analyze_time_pattern(user_id, suspicious_time)

        assert suspicion_score > detector.suspicious_threshold
        assert suspicion_score <= 1.0

    async def test_analyze_time_pattern_normal(self, detector):
        """Test time pattern analysis for normal activity."""
        user_id = "normal_time_user"

        # Build baseline profile (business hours user)
        baseline_events = []
        base_time = datetime.now() - timedelta(days=30)

        for day in range(30):
            for hour in range(9, 18):  # Business hours
                event = SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user_id,
                    timestamp=base_time + timedelta(days=day, hours=hour),
                    severity="low",
                    source="auth",
                )
                baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test normal activity (login at 10 AM)
        normal_time = datetime.now().replace(hour=10, minute=0, second=0)
        suspicion_score = await detector.analyze_time_pattern(user_id, normal_time)

        assert suspicion_score < detector.suspicious_threshold

    async def test_analyze_location_pattern_new_country(self, detector):
        """Test location pattern analysis detecting new country access."""
        user_id = "location_pattern_user"

        # Build baseline profile (US-based user)
        baseline_events = []
        for i in range(60):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address=f"192.168.1.{i % 255}",  # US IP range
                timestamp=datetime.now() - timedelta(hours=i),
                severity="low",
                source="auth",
                metadata={"location": {"country": "US", "city": "New York"}},
            )
            baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test access from different country
        suspicion_score = await detector.analyze_location_pattern(
            user_id,
            "1.2.3.4",
            {"country": "RU", "city": "Moscow"},  # Different country IP
        )

        assert suspicion_score > detector.suspicious_threshold

    async def test_analyze_device_pattern_new_device(self, detector):
        """Test device pattern analysis detecting new device usage."""
        user_id = "device_pattern_user"

        # Build baseline profile (consistent device usage)
        baseline_events = []
        for i in range(60):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now() - timedelta(hours=i),
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                severity="low",
                source="auth",
                metadata={"device": "laptop", "browser": "Chrome", "os": "Windows"},
            )
            baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test access from new device type
        new_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
        suspicion_score = await detector.analyze_device_pattern(user_id, new_user_agent)

        assert suspicion_score > detector.suspicious_threshold

    async def test_analyze_velocity_pattern_rapid_locations(self, detector):
        """Test velocity analysis detecting impossible travel."""
        user_id = "velocity_user"

        events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address="192.168.1.1",
                timestamp=datetime.now() - timedelta(minutes=30),
                severity="low",
                source="auth",
                metadata={"location": {"country": "US", "city": "New York", "lat": 40.7128, "lon": -74.0060}},
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address="1.2.3.4",
                timestamp=datetime.now(),
                severity="low",
                source="auth",
                metadata={"location": {"country": "JP", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503}},
            ),
        ]

        suspicion_score = await detector.analyze_velocity_pattern(user_id, events)

        # Should detect impossible travel (NYC to Tokyo in 30 minutes)
        assert suspicion_score > detector.anomaly_threshold


class TestSuspiciousActivityDetectorAnomalyDetection:
    """Test anomaly detection algorithms."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies."""
        with patch("src.auth.services.suspicious_activity_detector.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.suspicious_activity_detector.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                detector = SuspiciousActivityDetector()
                detector._db = mock_db
                detector._security_logger = mock_logger

                yield detector

    async def test_detect_volume_anomaly_spike(self, detector):
        """Test detection of unusual activity volume spikes."""
        user_id = "volume_spike_user"

        # Mock normal baseline (5-10 events per hour)
        baseline_events = []
        base_time = datetime.now() - timedelta(days=7)

        for hour in range(7 * 24):  # 7 days of data
            event_count = 7  # Normal volume
            for i in range(event_count):
                event = SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user_id,
                    timestamp=base_time + timedelta(hours=hour, minutes=i * 8),
                    severity="low",
                    source="auth",
                )
                baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test current spike (50 events in last hour)
        current_time = datetime.now()
        spike_events = []
        for i in range(50):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=current_time - timedelta(minutes=i),
                severity="low",
                source="auth",
            )
            spike_events.append(event)

        anomaly_score = await detector.detect_volume_anomaly(user_id, spike_events)

        assert anomaly_score > detector.anomaly_threshold

    async def test_detect_frequency_anomaly_burst(self, detector):
        """Test detection of unusual frequency patterns."""
        user_id = "frequency_burst_user"

        # Normal pattern: events spread throughout the day
        baseline_events = []
        base_time = datetime.now() - timedelta(days=14)

        for day in range(14):
            # Normal: 10 events spread over 8 hours
            for i in range(10):
                event = SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user_id,
                    timestamp=base_time + timedelta(days=day, hours=9 + i, minutes=i * 5),
                    severity="low",
                    source="auth",
                )
                baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test burst pattern: 20 events in 5 minutes
        current_time = datetime.now()
        burst_events = []
        for i in range(20):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=current_time - timedelta(seconds=i * 15),  # Every 15 seconds
                severity="low",
                source="auth",
            )
            burst_events.append(event)

        anomaly_score = await detector.detect_frequency_anomaly(user_id, burst_events)

        assert anomaly_score > detector.anomaly_threshold

    async def test_detect_pattern_anomaly_deviation(self, detector):
        """Test detection of behavioral pattern deviations."""
        user_id = "pattern_deviation_user"

        # Establish consistent pattern: only login/logout events
        baseline_events = []
        for i in range(100):
            # Alternate between login and logout
            event_type = SecurityEventType.LOGIN_SUCCESS if i % 2 == 0 else SecurityEventType.LOGOUT
            event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                timestamp=datetime.now() - timedelta(hours=i),
                severity="low",
                source="auth",
            )
            baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Test deviation: administrative events (unusual for this user)
        deviation_events = [
            SecurityEvent(
                event_type=SecurityEventType.CONFIGURATION_CHANGED,
                user_id=user_id,
                timestamp=datetime.now(),
                severity="high",
                source="admin",
            ),
            SecurityEvent(
                event_type=SecurityEventType.SECURITY_ALERT,
                user_id=user_id,
                timestamp=datetime.now(),
                severity="critical",
                source="system",
            ),
        ]

        anomaly_score = await detector.detect_pattern_anomaly(user_id, deviation_events)

        assert anomaly_score > detector.suspicious_threshold

    async def test_statistical_outlier_detection(self, detector):
        """Test statistical outlier detection methods."""
        # Generate normal distribution of session lengths
        import random

        random.seed(42)  # Reproducible results

        normal_sessions = [random.gauss(60, 15) for _ in range(100)]  # Mean: 60 min, StdDev: 15 min

        # Test outlier detection
        outlier_score_normal = await detector.calculate_statistical_outlier_score(45, normal_sessions)
        outlier_score_extreme = await detector.calculate_statistical_outlier_score(180, normal_sessions)

        # 45 minutes should be relatively normal (within 1 std dev)
        assert outlier_score_normal < detector.suspicious_threshold

        # 180 minutes should be a significant outlier (8 std devs from mean)
        assert outlier_score_extreme > detector.anomaly_threshold

    async def test_machine_learning_anomaly_detection(self, detector):
        """Test machine learning-based anomaly detection."""
        user_id = "ml_anomaly_user"

        # Create feature vectors for normal behavior
        normal_features = []
        for i in range(100):
            # Normal features: consistent timing, location, device
            features = {
                "hour_of_day": 10 + (i % 8),  # Business hours
                "day_of_week": i % 5,  # Weekdays
                "session_length": 60 + (i % 30),  # 60-90 minutes
                "ip_entropy": 0.1,  # Low IP diversity
                "failed_attempts": 0,  # No failures
            }
            normal_features.append(features)

        # Train or update model with normal behavior
        await detector.update_ml_model(user_id, normal_features, is_anomalous=False)

        # Test anomalous features
        anomalous_features = {
            "hour_of_day": 3,  # 3 AM (unusual)
            "day_of_week": 6,  # Sunday (unusual)
            "session_length": 300,  # 5 hours (unusual)
            "ip_entropy": 0.9,  # High IP diversity (unusual)
            "failed_attempts": 5,  # Multiple failures (unusual)
        }

        anomaly_score = await detector.predict_anomaly_ml(user_id, anomalous_features)

        assert anomaly_score > detector.anomaly_threshold


class TestSuspiciousActivityDetectorRiskScoring:
    """Test risk scoring and assessment."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies."""
        with patch("src.auth.services.suspicious_activity_detector.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.suspicious_activity_detector.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                detector = SuspiciousActivityDetector()
                detector._db = mock_db
                detector._security_logger = mock_logger

                yield detector

    async def test_calculate_comprehensive_risk_score(self, detector):
        """Test comprehensive risk score calculation."""
        user_id = "risk_score_user"

        # Setup current activity context
        current_activity = {
            "time_suspicion": 0.8,  # Unusual time
            "location_suspicion": 0.6,  # Moderately suspicious location
            "device_suspicion": 0.3,  # Familiar device
            "velocity_suspicion": 0.9,  # Impossible travel
            "volume_anomaly": 0.5,  # Normal volume
            "frequency_anomaly": 0.7,  # Slightly unusual frequency
            "pattern_anomaly": 0.4,  # Minor pattern deviation
        }

        risk_score = await detector.calculate_comprehensive_risk_score(user_id, current_activity)

        assert isinstance(risk_score, RiskScore)
        assert 0 <= risk_score.overall_score <= 1
        assert risk_score.overall_score > detector.suspicious_threshold  # Should be high risk

        # Check risk factors are properly weighted
        assert risk_score.risk_factors["velocity"] == 0.9  # Highest contributing factor
        assert risk_score.risk_factors["time"] == 0.8  # Second highest

        # Check risk level classification
        if risk_score.overall_score >= detector.anomaly_threshold:
            assert risk_score.risk_level == "CRITICAL"
        elif risk_score.overall_score >= detector.suspicious_threshold:
            assert risk_score.risk_level == "HIGH"

    async def test_risk_score_weighting_factors(self, detector):
        """Test risk score weighting based on different factors."""
        user_id = "weighting_test_user"

        # Test different weighting scenarios
        test_scenarios = [
            # Scenario 1: High velocity risk (should dominate)
            {
                "input": {"velocity_suspicion": 1.0, "time_suspicion": 0.1},
                "expected_min": 0.8,  # Velocity should heavily weight the score
            },
            # Scenario 2: Multiple moderate risks (should compound)
            {
                "input": {"time_suspicion": 0.5, "location_suspicion": 0.5, "device_suspicion": 0.5},
                "expected_min": 0.6,  # Combined moderate risks
            },
            # Scenario 3: Single high behavioral anomaly
            {"input": {"pattern_anomaly": 0.9, "volume_anomaly": 0.1}, "expected_min": 0.7},  # Pattern anomaly weighted
        ]

        for i, scenario in enumerate(test_scenarios):
            risk_score = await detector.calculate_comprehensive_risk_score(f"{user_id}_{i}", scenario["input"])
            assert (
                risk_score.overall_score >= scenario["expected_min"]
            ), f"Scenario {i+1} failed: {risk_score.overall_score} < {scenario['expected_min']}"

    async def test_risk_level_classification(self, detector):
        """Test risk level classification thresholds."""
        test_cases = [(0.2, "LOW"), (0.5, "MEDIUM"), (0.75, "HIGH"), (0.9, "CRITICAL")]

        for score, expected_level in test_cases:
            risk_score = RiskScore(user_id="test_user", overall_score=score, risk_factors={}, timestamp=datetime.now())

            classified_level = await detector.classify_risk_level(score)
            assert classified_level == expected_level

    async def test_historical_risk_trend_analysis(self, detector):
        """Test analysis of historical risk trends."""
        user_id = "trend_analysis_user"

        # Create historical risk scores showing escalating pattern
        historical_scores = []
        base_time = datetime.now() - timedelta(days=7)

        for day in range(7):
            score = 0.3 + (day * 0.1)  # Gradually increasing risk
            risk_score = RiskScore(
                user_id=user_id,
                overall_score=score,
                risk_factors={"trend_test": score},
                timestamp=base_time + timedelta(days=day),
            )
            historical_scores.append(risk_score)

        # Store historical scores
        for score in historical_scores:
            detector._risk_scores[f"{user_id}_{score.timestamp.date()}"] = score

        trend_analysis = await detector.analyze_risk_trends(user_id, days=7)

        assert trend_analysis["trend_direction"] == "INCREASING"
        assert trend_analysis["risk_acceleration"] > 0
        assert trend_analysis["days_analyzed"] == 7
        assert trend_analysis["current_trend_score"] > trend_analysis["initial_trend_score"]

    async def test_contextual_risk_adjustment(self, detector):
        """Test contextual risk score adjustments."""
        user_id = "contextual_user"

        # Base risk scenario
        base_risk_factors = {"time_suspicion": 0.6, "location_suspicion": 0.4}

        # Test different contexts
        contexts = [
            {
                "name": "business_hours_weekday",
                "context": {"is_business_hours": True, "is_weekday": True},
                "expected_adjustment": -0.1,  # Lower risk during business hours
            },
            {
                "name": "after_hours_weekend",
                "context": {"is_business_hours": False, "is_weekday": False},
                "expected_adjustment": 0.1,  # Higher risk during off hours
            },
            {
                "name": "high_security_environment",
                "context": {"environment_security": "HIGH", "privileged_access": True},
                "expected_adjustment": 0.2,  # Higher risk for privileged users
            },
        ]

        for context_test in contexts:
            adjusted_risk = await detector.calculate_contextual_risk_score(
                user_id,
                base_risk_factors,
                context_test["context"],
            )

            base_score = await detector.calculate_comprehensive_risk_score(user_id, base_risk_factors)

            if context_test["expected_adjustment"] > 0:
                assert adjusted_risk.overall_score > base_score.overall_score
            elif context_test["expected_adjustment"] < 0:
                assert adjusted_risk.overall_score < base_score.overall_score


class TestSuspiciousActivityDetectorRealTimeProcessing:
    """Test real-time activity processing and monitoring."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies."""
        with patch("src.auth.services.suspicious_activity_detector.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.suspicious_activity_detector.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                detector = SuspiciousActivityDetector()
                detector._db = mock_db
                detector._security_logger = mock_logger

                yield detector

    async def test_process_activity_event_real_time(self, detector):
        """Test real-time processing of activity events."""
        # Setup baseline profile
        user_id = "realtime_user"
        baseline_events = []
        for i in range(60):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address="192.168.1.100",
                timestamp=datetime.now() - timedelta(hours=i),
                severity="low",
                source="auth",
            )
            baseline_events.append(event)

        detector._db.get_events_by_user_id.return_value = baseline_events
        await detector.build_behavior_profile(user_id)

        # Process suspicious event in real-time
        suspicious_event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address="1.2.3.4",  # Different IP
            timestamp=datetime.now().replace(hour=3),  # Unusual time
            user_agent="Unknown Browser",  # Unusual device
            severity="medium",
            source="auth",
        )

        detection_result = await detector.process_activity_event(suspicious_event)

        assert detection_result is not None
        assert detection_result.is_suspicious is True
        assert detection_result.risk_score.overall_score > detector.suspicious_threshold
        assert len(detection_result.anomaly_reasons) > 0

    async def test_batch_activity_analysis(self, detector):
        """Test batch processing of multiple activity events."""
        user_id = "batch_user"

        # Create batch of events to analyze
        events_batch = []
        for i in range(10):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS if i % 2 == 0 else SecurityEventType.LOGOUT,
                user_id=user_id,
                ip_address=f"192.168.1.{100 + i}",
                timestamp=datetime.now() - timedelta(minutes=i * 5),
                severity="low",
                source="auth",
            )
            events_batch.append(event)

        # Mock baseline for comparison
        detector._db.get_events_by_user_id.return_value = events_batch[:5]  # Use first 5 as baseline

        batch_results = await detector.analyze_activity_batch(user_id, events_batch)

        assert len(batch_results) == len(events_batch)
        assert all(result.risk_score is not None for result in batch_results)

        # Results should be ordered by risk score (descending)
        risk_scores = [result.risk_score.overall_score for result in batch_results]
        assert risk_scores == sorted(risk_scores, reverse=True)

    async def test_streaming_analysis_window(self, detector):
        """Test streaming analysis with sliding time windows."""
        user_id = "streaming_user"

        # Simulate streaming events
        streaming_events = []
        current_time = datetime.now()

        for i in range(20):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=current_time - timedelta(minutes=i),
                severity="low",
                source="auth",
            )
            streaming_events.append(event)

        # Process events in streaming fashion
        window_analyses = []
        for i in range(5, 20, 5):  # Process every 5 events
            window_events = streaming_events[:i]
            analysis = await detector.analyze_streaming_window(user_id, window_events, window_size_minutes=60)
            window_analyses.append(analysis)

        assert len(window_analyses) == 3  # 3 windows processed

        # Each analysis should have temporal metrics
        for analysis in window_analyses:
            assert "events_in_window" in analysis
            assert "window_start" in analysis
            assert "window_end" in analysis
            assert "anomaly_scores" in analysis

    async def test_real_time_alerting_integration(self, detector):
        """Test integration with real-time alerting system."""
        user_id = "alerting_user"

        # Mock alert engine
        mock_alert_engine = AsyncMock()
        detector._alert_engine = mock_alert_engine

        # Create high-risk event
        high_risk_event = SecurityEvent(
            event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
            user_id=user_id,
            ip_address="malicious.ip.address",
            timestamp=datetime.now(),
            severity="critical",
            source="security",
        )

        # Process event (should trigger alert)
        detection_result = await detector.process_activity_event(high_risk_event)

        # Verify alert was triggered for high-risk detection
        if detection_result.risk_score.overall_score >= detector.anomaly_threshold:
            mock_alert_engine.trigger_alert.assert_called()

            # Check alert parameters
            call_args = mock_alert_engine.trigger_alert.call_args
            assert call_args[1]["priority"] in ["HIGH", "CRITICAL"]
            assert user_id in call_args[1]["message"]


class TestSuspiciousActivityDetectorPerformance:
    """Test performance requirements for suspicious activity detection."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies."""
        with patch("src.auth.services.suspicious_activity_detector.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.suspicious_activity_detector.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                detector = SuspiciousActivityDetector()
                detector._db = mock_db
                detector._security_logger = mock_logger

                yield detector

    @pytest.mark.performance
    async def test_process_activity_event_performance(self, detector):
        """Test that activity event processing meets <50ms requirement."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id="perf_test_user",
            timestamp=datetime.now(),
            severity="low",
            source="auth",
        )

        # Mock minimal baseline to speed up test
        detector._db.get_events_by_user_id.return_value = []

        start_time = time.time()
        await detector.process_activity_event(event)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 50, f"process_activity_event took {execution_time:.2f}ms (>50ms limit)"

    @pytest.mark.performance
    async def test_behavior_profile_building_performance(self, detector):
        """Test behavior profile building performance."""
        user_id = "profile_perf_user"

        # Mock moderate dataset for profile building
        mock_events = []
        for i in range(100):  # 100 events for baseline
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now() - timedelta(hours=i),
                severity="low",
                source="auth",
            )
            mock_events.append(event)

        detector._db.get_events_by_user_id.return_value = mock_events

        start_time = time.time()
        await detector.build_behavior_profile(user_id)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 200, f"build_behavior_profile took {execution_time:.2f}ms (>200ms limit)"

    @pytest.mark.performance
    async def test_anomaly_detection_performance(self, detector):
        """Test anomaly detection algorithm performance."""
        user_id = "anomaly_perf_user"

        # Setup behavior profile
        await detector.build_behavior_profile(user_id)

        # Test various anomaly detection methods
        test_events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now(),
                severity="low",
                source="auth",
            ),
        ]

        detection_methods = [
            detector.detect_volume_anomaly,
            detector.detect_frequency_anomaly,
            detector.detect_pattern_anomaly,
        ]

        for method in detection_methods:
            start_time = time.time()
            await method(user_id, test_events)
            end_time = time.time()

            execution_time = (end_time - start_time) * 1000
            assert execution_time < 100, f"{method.__name__} took {execution_time:.2f}ms (>100ms limit)"

    @pytest.mark.performance
    async def test_concurrent_detection_performance(self, detector):
        """Test concurrent detection processing performance."""

        async def process_user_activities(user_prefix: str, events_count: int):
            """Process activities for performance testing."""
            for i in range(events_count):
                event = SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=f"{user_prefix}_user_{i}",
                    timestamp=datetime.now() - timedelta(minutes=i),
                    severity="low",
                    source="auth",
                )
                await detector.process_activity_event(event)

        # Process concurrent activities
        start_time = time.time()
        await asyncio.gather(
            process_user_activities("batch1", 20),
            process_user_activities("batch2", 20),
            process_user_activities("batch3", 20),
            process_user_activities("batch4", 20),
            process_user_activities("batch5", 20),
        )
        end_time = time.time()

        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time_per_event = total_time / 100

        assert avg_time_per_event < 100, f"Concurrent detection avg {avg_time_per_event:.2f}ms per event"

    @pytest.mark.performance
    async def test_memory_efficiency_under_load(self, detector):
        """Test memory efficiency under high load."""
        import gc

        # Force garbage collection before test
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Process high volume of activities
        for i in range(1000):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=f"memory_test_user_{i % 20}",  # 20 different users
                timestamp=datetime.now() - timedelta(minutes=i),
                severity="low",
                source="auth",
            )
            await detector.process_activity_event(event)

            # Periodic cleanup
            if i % 100 == 0:
                await detector.cleanup_expired_profiles()

        # Force garbage collection after test
        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory growth should be reasonable
        memory_growth_ratio = final_objects / initial_objects
        assert memory_growth_ratio < 3.0, f"Memory usage grew by {memory_growth_ratio:.2f}x"


class TestSuspiciousActivityDetectorErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies."""
        with patch("src.auth.services.suspicious_activity_detector.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.suspicious_activity_detector.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                detector = SuspiciousActivityDetector()
                detector._db = mock_db
                detector._security_logger = mock_logger

                yield detector

    async def test_process_activity_event_missing_user_id(self, detector):
        """Test handling of events with missing user_id."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=None,  # Missing user_id
            timestamp=datetime.now(),
            severity="low",
            source="auth",
        )

        with pytest.raises(ValueError, match="user_id cannot be None"):
            await detector.process_activity_event(event)

    async def test_database_error_handling(self, detector):
        """Test handling of database errors."""
        user_id = "db_error_user"
        detector._db.get_events_by_user_id.side_effect = Exception("Database connection failed")

        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            timestamp=datetime.now(),
            severity="low",
            source="auth",
        )

        # Should handle gracefully and return default risk assessment
        result = await detector.process_activity_event(event)

        # Should return low-confidence result due to lack of baseline data
        assert result is not None
        assert result.risk_score.confidence_score < 0.5

    async def test_malformed_event_data_handling(self, detector):
        """Test handling of malformed event data."""
        user_id = "malformed_data_user"

        # Event with malformed timestamp
        malformed_event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            timestamp=None,  # Invalid timestamp
            severity="low",
            source="auth",
        )

        # Should handle gracefully
        result = await detector.process_activity_event(malformed_event)

        # Should still process but with lower confidence
        assert result is not None
        assert result.risk_score.confidence_score < 1.0

    async def test_insufficient_baseline_data_handling(self, detector):
        """Test handling when insufficient baseline data is available."""
        user_id = "new_user_no_baseline"

        # Mock very limited historical data
        detector._db.get_events_by_user_id.return_value = []

        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            timestamp=datetime.now(),
            severity="low",
            source="auth",
        )

        result = await detector.process_activity_event(event)

        # Should create result but with very low confidence
        assert result is not None
        assert result.risk_score.confidence_score < 0.3
        assert "insufficient_baseline" in result.anomaly_reasons

    async def test_concurrent_profile_building_race_condition(self, detector):
        """Test handling of concurrent profile building race conditions."""
        user_id = "concurrent_profile_user"

        # Mock database to return data
        mock_events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now() - timedelta(hours=i),
                severity="low",
                source="auth",
            )
            for i in range(60)
        ]
        detector._db.get_events_by_user_id.return_value = mock_events

        # Attempt concurrent profile building
        tasks = [detector.build_behavior_profile(user_id) for _ in range(5)]

        profiles = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle concurrency gracefully
        successful_profiles = [p for p in profiles if not isinstance(p, Exception)]
        assert len(successful_profiles) >= 1  # At least one should succeed

        # All successful profiles should be equivalent
        if len(successful_profiles) > 1:
            first_profile = successful_profiles[0]
            for profile in successful_profiles[1:]:
                assert profile.user_id == first_profile.user_id
                assert profile.total_events == first_profile.total_events

    async def test_extreme_data_values_handling(self, detector):
        """Test handling of extreme or edge case data values."""
        user_id = "extreme_values_user"

        # Event with extreme timestamp (far future)
        extreme_event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            timestamp=datetime.now() + timedelta(days=365 * 10),  # 10 years in future
            severity="low",
            source="auth",
            metadata={
                "session_length": -1,  # Negative session length
                "location": {"lat": 999, "lon": 999},  # Invalid coordinates
                "device_id": "x" * 1000,  # Extremely long device ID
            },
        )

        # Should handle without crashing
        result = await detector.process_activity_event(extreme_event)

        assert result is not None
        # Should flag as suspicious due to data anomalies
        assert result.is_suspicious is True

    async def test_resource_exhaustion_handling(self, detector):
        """Test handling of resource exhaustion scenarios."""
        # Simulate memory pressure by creating large profile data
        user_id = "resource_exhaustion_user"

        # Create very large behavior profile
        large_profile = BehaviorProfile(
            user_id=user_id,
            typical_hours=list(range(24)),
            common_ip_addresses=["192.168.1." + str(i) for i in range(1000)],  # 1000 IPs
            frequent_locations=[{"city": f"City{i}", "country": "US"} for i in range(1000)],
            device_patterns=["Device" + str(i) for i in range(1000)],
            activity_volume_stats={"events": list(range(10000))},  # Large stats
            total_events=10000,
            confidence_score=0.9,
            last_updated=datetime.now(),
        )

        # Store large profile
        detector._user_profiles[user_id] = large_profile

        # Process event - should handle large profile gracefully
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            timestamp=datetime.now(),
            severity="low",
            source="auth",
        )

        result = await detector.process_activity_event(event)

        # Should complete without exhausting resources
        assert result is not None
        assert isinstance(result.risk_score.overall_score, float)
        assert 0 <= result.risk_score.overall_score <= 1
