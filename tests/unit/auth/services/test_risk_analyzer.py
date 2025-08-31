"""
Test suite for Risk Analyzer Service.

Tests risk assessment, behavioral analysis, and anomaly detection functionality.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.auth.services.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzerInitialization:
    """Test risk analyzer initialization and configuration."""

    def test_init_default_configuration(self):
        """Test risk analyzer initializes with default configuration."""
        analyzer = RiskAnalyzer()

        assert analyzer._risk_cache == {}
        assert analyzer._behavioral_patterns == {}
        assert analyzer._baseline_metrics == {}


class TestUserRiskProfileAnalysis:
    """Test comprehensive user risk profile analysis."""

    @pytest.fixture
    def analyzer(self):
        """Create a risk analyzer instance for testing."""
        return RiskAnalyzer()

    @pytest.fixture
    def sample_activity_data(self):
        """Create sample activity data for testing."""
        base_time = datetime.now(UTC)
        return {
            "login_events": [
                {"success": True, "location": "New York", "timestamp": base_time - timedelta(hours=i)}
                for i in range(5)
            ] + [
                {"success": False, "location": "Unknown", "timestamp": base_time - timedelta(hours=i)}
                for i in range(3)
            ],
            "access_events": [
                {"access_type": "read", "sensitivity": "high", "record_count": 10}
                for _ in range(20)
            ] + [
                {"access_type": "bulk_export", "sensitivity": "critical", "record_count": 1000}
                for _ in range(2)
            ],
            "behavior_metrics": {
                "avg_session_duration_minutes": 45.0,
                "actions_per_minute": 2.5,
                "error_rate_percent": 5.0,
                "unique_pages_visited": 8,
                "total_page_views": 20,
            },
            "temporal_patterns": {
                "off_hours_percentage": 15.0,
                "weekend_percentage": 20.0,
                "clustering_score": 30.0,
                "timezone_variance": 1,
            },
            "last_activity_timestamp": base_time - timedelta(hours=2),
        }

    async def test_analyze_user_risk_profile_comprehensive(self, analyzer, sample_activity_data):
        """Test comprehensive user risk profile analysis."""
        result = await analyzer.analyze_user_risk_profile(
            user_id="test_user_001",
            activity_data=sample_activity_data,
            time_window_hours=168,
        )

        assert result["user_id"] == "test_user_001"
        assert "analysis_timestamp" in result
        assert result["time_window_hours"] == 168
        assert 0 <= result["overall_risk_score"] <= 100
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        # Verify risk factors are analyzed
        assert "risk_factors" in result
        risk_factors = result["risk_factors"]
        assert "login_patterns" in risk_factors
        assert "access_patterns" in risk_factors
        assert "behavioral_anomalies" in risk_factors
        assert "temporal_patterns" in risk_factors

        # Verify recommendations are provided
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

        # Verify confidence score
        assert 0 <= result["confidence_score"] <= 100

    async def test_analyze_user_risk_profile_high_risk_scenario(self, analyzer):
        """Test risk analysis for high-risk user scenario."""
        high_risk_data = {
            "login_events": [
                {"success": False, "location": f"Location_{i}", "timestamp": datetime.now(UTC) - timedelta(hours=i)}
                for i in range(10)  # Many failed logins from different locations
            ] + [
                {"success": True, "location": "Unknown", "timestamp": datetime.now(UTC).replace(hour=3)}
                for _ in range(60)  # High frequency logins at unusual hours
            ],
            "access_events": [
                {"access_type": "bulk_export", "sensitivity": "critical", "record_count": 5000}
                for _ in range(20)  # Many bulk operations on critical data
            ],
            "behavior_metrics": {
                "avg_session_duration_minutes": 600.0,  # Very long sessions
                "actions_per_minute": 15.0,  # High activity velocity
                "error_rate_percent": 25.0,  # High error rate
                "unique_pages_visited": 2,
                "total_page_views": 100,  # Highly repetitive
            },
            "temporal_patterns": {
                "off_hours_percentage": 80.0,  # Mostly off-hours activity
                "weekend_percentage": 60.0,  # High weekend activity
                "clustering_score": 90.0,  # Potential automation
                "timezone_variance": 5,  # Multiple timezones
            },
            "last_activity_timestamp": datetime.now(UTC) - timedelta(minutes=30),
        }

        result = await analyzer.analyze_user_risk_profile(
            user_id="high_risk_user",
            activity_data=high_risk_data,
        )

        # Should be high or critical risk
        assert result["overall_risk_score"] >= 60
        assert result["risk_level"] in ["HIGH", "CRITICAL"]

        # Should have many risk indicators
        assert len(result["risk_indicators"]) >= 5

        # Should have security-focused recommendations
        recommendations = result["recommendations"]
        security_recommendations = [r for r in recommendations if "security" in r.lower() or "review" in r.lower()]
        assert len(security_recommendations) >= 1

    async def test_analyze_user_risk_profile_low_risk_scenario(self, analyzer):
        """Test risk analysis for low-risk user scenario."""
        low_risk_data = {
            "login_events": [
                {"success": True, "location": "Office", "timestamp": datetime.now(UTC).replace(hour=10)}
                for _ in range(5)  # Few successful logins during business hours
            ],
            "access_events": [
                {"access_type": "read", "sensitivity": "low", "record_count": 1}
                for _ in range(10)  # Limited, low-sensitivity access
            ],
            "behavior_metrics": {
                "avg_session_duration_minutes": 30.0,
                "actions_per_minute": 1.0,
                "error_rate_percent": 2.0,
                "unique_pages_visited": 10,
                "total_page_views": 15,
            },
            "temporal_patterns": {
                "off_hours_percentage": 5.0,
                "weekend_percentage": 10.0,
                "clustering_score": 20.0,
                "timezone_variance": 1,
            },
            "last_activity_timestamp": datetime.now(UTC) - timedelta(hours=1),
        }

        result = await analyzer.analyze_user_risk_profile(
            user_id="low_risk_user",
            activity_data=low_risk_data,
        )

        # Should be low risk
        assert result["overall_risk_score"] <= 40
        assert result["risk_level"] in ["LOW", "MEDIUM"]

        # Should have basic monitoring recommendation
        recommendations = result["recommendations"]
        baseline_recommendations = [r for r in recommendations if "baseline" in r.lower() or "low risk" in r.lower()]
        assert len(baseline_recommendations) >= 1

    async def test_analyze_user_risk_profile_empty_data(self, analyzer):
        """Test risk analysis with empty activity data."""
        empty_data = {
            "login_events": [],
            "access_events": [],
            "behavior_metrics": {},
            "temporal_patterns": {},
        }

        result = await analyzer.analyze_user_risk_profile(
            user_id="empty_user",
            activity_data=empty_data,
        )

        assert result["user_id"] == "empty_user"
        assert result["overall_risk_score"] == 0.0
        assert result["risk_level"] == "LOW"
        assert len(result["risk_indicators"]) == 0

        # Should still provide basic recommendations
        assert len(result["recommendations"]) > 0

    async def test_analyze_user_risk_profile_exception_handling(self, analyzer):
        """Test risk analysis exception handling."""
        # Patch one of the analysis methods to raise an exception
        original_method = analyzer._analyze_login_patterns

        async def failing_method(*args, **kwargs):
            raise ValueError("Simulated analysis error")

        analyzer._analyze_login_patterns = failing_method

        try:
            result = await analyzer.analyze_user_risk_profile(
                user_id="error_user",
                activity_data={"login_events": [{"test": "data"}]},
            )

            assert "error" in result
            assert result["overall_risk_score"] == 50.0  # Default moderate risk
            assert result["risk_level"] == "MEDIUM"
            assert result["confidence_score"] == 0.0
        finally:
            # Restore original method
            analyzer._analyze_login_patterns = original_method


class TestSuspiciousActivityDetection:
    """Test suspicious activity detection functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create a risk analyzer instance for testing."""
        return RiskAnalyzer()

    @pytest.fixture
    def sample_activity_list(self):
        """Create sample activity list for testing."""
        base_time = datetime.now(UTC)
        return [
            {
                "user_id": "user_001",
                "action_type": "login",
                "timestamp": base_time - timedelta(minutes=i),
                "location": "Office",
            }
            for i in range(10)
        ] + [
            {
                "user_id": "user_002",
                "action_type": "data_export",
                "timestamp": base_time - timedelta(seconds=i),  # Rapid actions
                "location": "Remote",
            }
            for i in range(5)
        ]

    async def test_detect_suspicious_activities_normal_case(self, analyzer, sample_activity_list):
        """Test suspicious activity detection with normal sensitivity."""
        suspicious = await analyzer.detect_suspicious_activities(
            activity_data=sample_activity_list,
            sensitivity=0.7,
            time_window_hours=24,
        )

        assert isinstance(suspicious, list)

        # Should detect rapid actions from user_002
        rapid_patterns = [s for s in suspicious if s.get("pattern_type") == "rapid_actions"]
        assert len(rapid_patterns) > 0

        # Results should be sorted by suspicion score
        if len(suspicious) > 1:
            for i in range(1, len(suspicious)):
                assert suspicious[i-1]["suspicion_score"] >= suspicious[i]["suspicion_score"]

    async def test_detect_suspicious_activities_high_sensitivity(self, analyzer):
        """Test suspicious activity detection with high sensitivity."""
        rapid_activities = [
            {
                "user_id": "rapid_user",
                "action_type": "data_access",
                "timestamp": datetime.now(UTC) - timedelta(milliseconds=100 * i),
            }
            for i in range(10)
        ]

        suspicious = await analyzer.detect_suspicious_activities(
            activity_data=rapid_activities,
            sensitivity=0.9,
            time_window_hours=24,
        )

        # High sensitivity should detect more patterns
        assert len(suspicious) > 0

        # Should have high suspicion scores
        max_score = max(s["suspicion_score"] for s in suspicious) if suspicious else 0
        assert max_score > 80

    async def test_detect_suspicious_activities_empty_data(self, analyzer):
        """Test suspicious activity detection with empty data."""
        suspicious = await analyzer.detect_suspicious_activities(
            activity_data=[],
            sensitivity=0.7,
        )

        assert suspicious == []

    async def test_detect_suspicious_activities_repetitive_patterns(self, analyzer):
        """Test detection of repetitive action patterns."""
        repetitive_activities = [
            {
                "user_id": "repeat_user",
                "action_type": "same_action",
                "timestamp": datetime.now(UTC) - timedelta(minutes=i),
            }
            for i in range(50)  # Same action repeated many times (need more for threshold)
        ]

        suspicious = await analyzer.detect_suspicious_activities(
            activity_data=repetitive_activities,
            sensitivity=1.0,  # Higher sensitivity to lower the threshold: 50 * (0.8 / 1.0) = 40
        )

        # Should detect repetitive patterns
        repetitive_patterns = [s for s in suspicious if s.get("pattern_type") == "repetitive_actions"]
        assert len(repetitive_patterns) > 0

        repetitive_pattern = repetitive_patterns[0]
        assert repetitive_pattern["repetition_count"] == 50
        assert repetitive_pattern["suspicion_score"] > 50

    async def test_detect_suspicious_activities_privilege_escalation(self, analyzer):
        """Test detection of privilege escalation attempts."""
        escalation_activities = [
            {
                "user_id": "escalation_user",
                "action_type": action_type,
                "timestamp": datetime.now(UTC) - timedelta(minutes=i),
            }
            for i, action_type in enumerate(["user_management", "permission_change", "role_assignment"] * 2)
        ]

        suspicious = await analyzer.detect_suspicious_activities(
            activity_data=escalation_activities,
            sensitivity=0.7,
        )

        # Should detect privilege escalation
        escalation_patterns = [s for s in suspicious if s.get("pattern_type") == "privilege_escalation"]
        assert len(escalation_patterns) > 0

        escalation_pattern = escalation_patterns[0]
        assert escalation_pattern["suspicion_score"] > 50
        assert len(escalation_pattern["admin_actions"]) == 6


class TestAnomalyScoreCalculation:
    """Test anomaly score calculation functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create a risk analyzer instance for testing."""
        return RiskAnalyzer()

    async def test_calculate_anomaly_score_with_baseline(self, analyzer):
        """Test anomaly score calculation with provided baseline."""
        current_behavior = {
            "login_frequency": 10.0,
            "session_duration": 120.0,
            "access_volume": 50.0,
            "geographic_variance": 3.0,
        }

        baseline = {
            "login_frequency": 3.0,
            "login_frequency_std": 1.0,
            "session_duration": 45.0,
            "session_duration_std": 10.0,
            "access_volume": 25.0,
            "access_volume_std": 5.0,
            "geographic_variance": 1.0,
            "geographic_variance_std": 0.5,
        }

        score, reasons = await analyzer.calculate_anomaly_score(
            user_id="test_user",
            current_behavior=current_behavior,
            historical_baseline=baseline,
        )

        assert 0 <= score <= 100
        assert isinstance(reasons, list)

        # Should detect anomalies in multiple metrics
        assert len(reasons) > 0

        # Check specific anomaly reasons
        login_anomaly = any("login frequency" in reason.lower() for reason in reasons)
        session_anomaly = any("session duration" in reason.lower() for reason in reasons)
        assert login_anomaly or session_anomaly

    async def test_calculate_anomaly_score_no_baseline(self, analyzer):
        """Test anomaly score calculation without baseline."""
        current_behavior = {
            "login_frequency": 5.0,
            "session_duration": 60.0,
        }

        # Should create and use baseline
        score, reasons = await analyzer.calculate_anomaly_score(
            user_id="new_user",
            current_behavior=current_behavior,
        )

        assert 0 <= score <= 100
        assert isinstance(reasons, list)

    async def test_calculate_anomaly_score_no_baseline_data(self, analyzer):
        """Test anomaly score when no baseline data is available."""
        # Mock the baseline method to return None
        analyzer._baseline_metrics = {}  # Ensure no cached baseline

        current_behavior = {"login_frequency": 5.0}

        # This will generate a mock baseline in _get_user_baseline
        score, reasons = await analyzer.calculate_anomaly_score(
            user_id="no_baseline_user",
            current_behavior=current_behavior,
        )

        assert 0 <= score <= 100
        assert isinstance(reasons, list)

    async def test_calculate_anomaly_score_exception_handling(self, analyzer):
        """Test anomaly score calculation exception handling."""
        # Pass invalid data to trigger exception
        invalid_behavior = None

        score, reasons = await analyzer.calculate_anomaly_score(
            user_id="error_user",
            current_behavior=invalid_behavior,  # This will cause an exception
        )

        assert score == 0.0
        assert len(reasons) == 1
        assert "error" in reasons[0].lower()


class TestPrivateHelperMethods:
    """Test private helper methods."""

    @pytest.fixture
    def analyzer(self):
        """Create a risk analyzer instance for testing."""
        return RiskAnalyzer()

    def test_calculate_risk_level(self, analyzer):
        """Test risk level calculation from score."""
        assert analyzer._calculate_risk_level(90) == "CRITICAL"
        assert analyzer._calculate_risk_level(80) == "CRITICAL"
        assert analyzer._calculate_risk_level(70) == "HIGH"
        assert analyzer._calculate_risk_level(60) == "HIGH"
        assert analyzer._calculate_risk_level(50) == "MEDIUM"
        assert analyzer._calculate_risk_level(40) == "MEDIUM"
        assert analyzer._calculate_risk_level(30) == "LOW"
        assert analyzer._calculate_risk_level(10) == "LOW"

    def test_calculate_confidence_score_high_data_volume(self, analyzer):
        """Test confidence score with high data volume."""
        activity_data = {
            "login_events": [{"id": i} for i in range(30)],
            "access_events": [{"id": i} for i in range(25)],
            "behavior_metrics": {"avg_session_duration": 45},
            "temporal_patterns": {"off_hours_percentage": 10},
            "last_activity_timestamp": datetime.now(UTC) - timedelta(hours=12),
        }

        confidence = analyzer._calculate_confidence_score(activity_data)

        # Should have high confidence with complete, recent data
        assert confidence >= 80.0

    def test_calculate_confidence_score_low_data_volume(self, analyzer):
        """Test confidence score with low data volume."""
        activity_data = {
            "login_events": [{"id": i} for i in range(3)],
            "access_events": [{"id": i} for i in range(2)],
            "last_activity_timestamp": datetime.now(UTC) - timedelta(days=10),
        }

        confidence = analyzer._calculate_confidence_score(activity_data)

        # Should have lower confidence with limited, old data
        assert confidence <= 60.0

    def test_calculate_confidence_score_no_activity_timestamp(self, analyzer):
        """Test confidence score without last activity timestamp."""
        activity_data = {
            "login_events": [{"id": i} for i in range(20)],
            "access_events": [{"id": i} for i in range(10)],
            # No last_activity_timestamp
        }

        confidence = analyzer._calculate_confidence_score(activity_data)

        # Should still calculate confidence but with penalty for missing timestamp
        assert 0 <= confidence <= 100

    async def test_get_user_baseline_caching(self, analyzer):
        """Test user baseline caching mechanism."""
        user_id = "cache_test_user"

        # First call should create baseline
        baseline1 = await analyzer._get_user_baseline(user_id)
        assert baseline1 is not None
        assert "login_frequency" in baseline1

        # Second call should return cached baseline
        baseline2 = await analyzer._get_user_baseline(user_id)
        assert baseline1 == baseline2
        assert baseline1 is baseline2  # Same object reference


class TestRiskFactorAnalysis:
    """Test individual risk factor analysis methods."""

    @pytest.fixture
    def analyzer(self):
        """Create a risk analyzer instance for testing."""
        return RiskAnalyzer()

    async def test_analyze_login_patterns_high_risk(self, analyzer):
        """Test login pattern analysis for high-risk scenario."""
        high_risk_login_data = {
            "login_events": [
                {"success": False, "location": f"Location_{i}", "timestamp": datetime.now(UTC).replace(hour=3)}
                for i in range(10)  # Many failed logins at unusual hours from different locations
            ] + [
                {"success": True, "location": "Unknown", "timestamp": datetime.now(UTC)}
                for _ in range(60)  # High frequency successful logins
            ],
        }

        result = await analyzer._analyze_login_patterns("test_user", high_risk_login_data)

        assert result["risk_score"] > 50
        assert len(result["indicators"]) >= 2

        # Should detect high frequency and failed logins
        indicators_text = " ".join(result["indicators"])
        assert "frequency" in indicators_text.lower() or "failed" in indicators_text.lower()

    async def test_analyze_access_patterns_bulk_operations(self, analyzer):
        """Test access pattern analysis with bulk operations."""
        bulk_access_data = {
            "access_events": [
                {"access_type": "bulk_export", "sensitivity": "critical", "record_count": 5000}
                for _ in range(10)
            ] + [
                {"access_type": "read", "sensitivity": "high", "record_count": 1}
                for _ in range(150)  # High volume access
            ],
        }

        result = await analyzer._analyze_access_patterns("test_user", bulk_access_data)

        assert result["risk_score"] > 40
        assert len(result["indicators"]) >= 1

        # Should detect bulk operations and high volume
        indicators_text = " ".join(result["indicators"])
        assert "bulk" in indicators_text.lower() or "volume" in indicators_text.lower()

    async def test_analyze_behavioral_anomalies_extreme_values(self, analyzer):
        """Test behavioral anomaly analysis with extreme values."""
        extreme_behavior_data = {
            "behavior_metrics": {
                "avg_session_duration_minutes": 720.0,  # 12 hours
                "actions_per_minute": 20.0,  # Very high activity
                "error_rate_percent": 30.0,  # High error rate
                "unique_pages_visited": 1,
                "total_page_views": 1000,  # Extremely repetitive
            },
        }

        result = await analyzer._analyze_behavioral_anomalies("test_user", extreme_behavior_data)

        assert result["risk_score"] > 60
        assert len(result["indicators"]) >= 3

        # Should detect multiple behavioral anomalies
        indicators_text = " ".join(result["indicators"])
        assert "session" in indicators_text.lower()
        assert "activity" in indicators_text.lower()

    async def test_analyze_temporal_patterns_off_hours_activity(self, analyzer):
        """Test temporal pattern analysis with high off-hours activity."""
        off_hours_data = {
            "temporal_patterns": {
                "off_hours_percentage": 90.0,  # Mostly off-hours
                "weekend_percentage": 80.0,   # High weekend activity
                "clustering_score": 95.0,     # Potential automation
                "timezone_variance": 6,       # Many timezones
            },
        }

        result = await analyzer._analyze_temporal_patterns("test_user", off_hours_data)

        assert result["risk_score"] > 50
        assert len(result["indicators"]) >= 3

        # Should detect off-hours, automation, and timezone variance
        indicators_text = " ".join(result["indicators"])
        assert any(keyword in indicators_text.lower()
                  for keyword in ["off-hours", "automated", "timezone"])


class TestDetectionPatterns:
    """Test specific detection patterns for suspicious activities."""

    @pytest.fixture
    def analyzer(self):
        """Create a risk analyzer instance for testing."""
        return RiskAnalyzer()

    async def test_detect_rapid_actions_high_frequency(self, analyzer):
        """Test rapid action detection with high frequency actions."""
        rapid_activities = [
            {
                "user_id": "rapid_user",
                "action_type": "data_access",
                "timestamp": datetime.now(UTC) - timedelta(milliseconds=50 * i),
            }
            for i in range(5)
        ]

        suspicious = await analyzer._detect_rapid_actions("rapid_user", rapid_activities, 0.8)

        assert len(suspicious) > 0

        # Should have high suspicion scores for rapid actions
        for pattern in suspicious:
            assert pattern["pattern_type"] == "rapid_actions"
            assert pattern["suspicion_score"] > 50
            assert len(pattern["activities"]) == 2  # Previous and current

    async def test_detect_unusual_sequences_repetitive(self, analyzer):
        """Test unusual sequence detection with highly repetitive actions."""
        repetitive_activities = [
            {
                "action_type": "same_action",
                "timestamp": datetime.now(UTC) - timedelta(minutes=i),
            }
            for i in range(50)  # Need more repetitions for threshold (50 > 50 * (0.8/0.6) = 66.7 - so use higher sensitivity)
        ]

        suspicious = await analyzer._detect_unusual_sequences("repeat_user", repetitive_activities, 0.9)  # Higher sensitivity

        assert len(suspicious) > 0

        repetitive_pattern = suspicious[0]
        assert repetitive_pattern["pattern_type"] == "repetitive_actions"
        assert repetitive_pattern["repetition_count"] == 50
        assert repetitive_pattern["suspicion_score"] > 50

    async def test_detect_escalation_attempts_admin_actions(self, analyzer):
        """Test privilege escalation detection with admin actions."""
        admin_activities = [
            {
                "action_type": action_type,
                "timestamp": datetime.now(UTC) - timedelta(minutes=i),
            }
            for i, action_type in enumerate([
                "user_management", "permission_change", "system_config",
                "security_setting", "role_assignment",
            ])
        ]

        suspicious = await analyzer._detect_escalation_attempts("admin_user", admin_activities, 0.7)

        assert len(suspicious) > 0

        escalation_pattern = suspicious[0]
        assert escalation_pattern["pattern_type"] == "privilege_escalation"
        assert len(escalation_pattern["admin_actions"]) == 5
        assert escalation_pattern["suspicion_score"] > 50

    async def test_detect_escalation_attempts_low_suspicion(self, analyzer):
        """Test privilege escalation detection with low suspicion scenario."""
        limited_admin_activities = [
            {
                "action_type": "user_management",
                "timestamp": datetime.now(UTC),
            },
        ]

        suspicious = await analyzer._detect_escalation_attempts("limited_user", limited_admin_activities, 0.3)

        # With low sensitivity and limited admin actions, suspicion should be low
        if suspicious:
            assert suspicious[0]["suspicion_score"] <= 50
        else:
            # Or no suspicious patterns detected
            assert len(suspicious) == 0
