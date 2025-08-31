"""Comprehensive unit tests for MockDataService.

Tests mock data generation functionality for security analytics,
user activity simulation, system metrics, and behavioral patterns.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.auth.services.mock_data_service import DataGenerationMode, MockDataService


class TestMockDataServiceInitialization:
    """Test MockDataService initialization and basic functionality."""

    def test_init_default_mode(self):
        """Test MockDataService initialization with default mode."""
        service = MockDataService()

        # Check initialization
        assert service.mode == DataGenerationMode.REALISTIC
        assert isinstance(service._cache, dict)
        assert len(service._cache) == 0

        # Check data structures
        assert isinstance(service._event_types, list)
        assert len(service._event_types) == 12
        assert "user_login" in service._event_types
        assert "security_alert" in service._event_types

        assert isinstance(service._risk_levels, list)
        assert service._risk_levels == ["low", "medium", "high", "critical"]

        assert isinstance(service._user_agents, list)
        assert len(service._user_agents) == 4

        assert isinstance(service._ip_ranges, list)
        assert len(service._ip_ranges) == 6

    def test_init_custom_modes(self):
        """Test MockDataService initialization with different modes."""
        for mode in DataGenerationMode:
            service = MockDataService(mode=mode)
            assert service.mode == mode

    def test_data_generation_modes_enum(self):
        """Test DataGenerationMode enum values."""
        assert DataGenerationMode.REALISTIC.value == "realistic"
        assert DataGenerationMode.TESTING.value == "testing"
        assert DataGenerationMode.DEMO.value == "demo"
        assert DataGenerationMode.STRESS.value == "stress"


class TestSecurityEventsGeneration:
    """Test security events generation functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_generate_security_events_default_params(self, service):
        """Test security events generation with default parameters."""
        events = await service.generate_security_events()

        assert len(events) == 100  # Default count
        assert all(isinstance(event, dict) for event in events)

        # Check event structure
        event = events[0]
        required_keys = [
            "event_id",
            "event_type",
            "timestamp",
            "user_id",
            "ip_address",
            "user_agent",
            "risk_score",
            "details",
            "session_id",
            "location",
            "success",
        ]
        for key in required_keys:
            assert key in event

        # Verify chronological order
        timestamps = [event["timestamp"] for event in events]
        assert timestamps == sorted(timestamps)

    async def test_generate_security_events_custom_count(self, service):
        """Test security events generation with custom count."""
        events = await service.generate_security_events(count=50)
        assert len(events) == 50

    async def test_generate_security_events_custom_days_back(self, service):
        """Test security events generation with custom time range."""
        events = await service.generate_security_events(count=10, days_back=7)

        # All events should be within the last 7 days
        cutoff_time = datetime.now(UTC) - timedelta(days=7)
        for event in events:
            assert event["timestamp"] >= cutoff_time

    async def test_generate_security_events_custom_event_types(self, service):
        """Test security events generation with custom event types."""
        custom_types = ["user_login", "failed_login"]
        events = await service.generate_security_events(
            count=20,
            event_types=custom_types,
        )

        # All events should be of custom types only
        for event in events:
            assert event["event_type"] in custom_types

    async def test_generate_security_events_data_quality(self, service):
        """Test data quality of generated security events."""
        events = await service.generate_security_events(count=5)

        for event in events:
            # Check data types
            assert isinstance(event["event_id"], str)
            assert isinstance(event["event_type"], str)
            assert isinstance(event["timestamp"], datetime)
            assert isinstance(event["user_id"], str)
            assert isinstance(event["ip_address"], str)
            assert isinstance(event["user_agent"], str)
            assert isinstance(event["risk_score"], int)
            assert isinstance(event["details"], dict)
            assert isinstance(event["session_id"], str)
            assert isinstance(event["location"], dict)
            assert isinstance(event["success"], bool)

            # Check value ranges
            assert 0 <= event["risk_score"] <= 100
            assert len(event["session_id"]) == 16
            assert event["event_type"] in service._event_types

    async def test_generate_security_events_empty_event_types(self, service):
        """Test security events generation with empty event types list."""
        # Empty list causes IndexError in random.choices - this is expected behavior
        with pytest.raises(IndexError):
            await service.generate_security_events(count=5, event_types=[])

        # None should work fine using default event types
        events = await service.generate_security_events(count=5, event_types=None)
        assert len(events) == 5
        for event in events:
            assert event["event_type"] in service._event_types


class TestUserActivityGeneration:
    """Test user activity data generation functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_generate_user_activity_data_default_params(self, service):
        """Test user activity generation with default parameters."""
        user_activities = await service.generate_user_activity_data()

        assert len(user_activities) == 50  # Default user count
        assert all(isinstance(user_id, str) for user_id in user_activities)

        # Check user data structure
        user_id = next(iter(user_activities.keys()))
        user_data = user_activities[user_id]
        assert "profile" in user_data
        assert "activities" in user_data

        # Check profile structure
        profile = user_data["profile"]
        assert "user_id" in profile
        assert "role" in profile
        assert "department" in profile
        assert "risk_level" in profile
        assert "last_login" in profile

        # Check activities structure
        activities = user_data["activities"]
        assert isinstance(activities, list)
        assert len(activities) > 0

    async def test_generate_user_activity_data_custom_params(self, service):
        """Test user activity generation with custom parameters."""
        user_activities = await service.generate_user_activity_data(
            user_count=10,
            activity_window_days=7,
        )

        assert len(user_activities) == 10

        # Check time window for activities - activities are generated within the window
        # but can be older than cutoff_time due to random generation within the full range
        current_time = datetime.now(UTC)
        oldest_allowed = current_time - timedelta(days=7, hours=23, minutes=59)

        for user_data in user_activities.values():
            for activity in user_data["activities"]:
                # Activity should be within the specified time window (can be up to 7 days + 23:59 old)
                assert activity["timestamp"] >= oldest_allowed
                assert activity["timestamp"] <= current_time

    async def test_generate_user_activity_data_different_modes(self):
        """Test user activity generation with different modes."""
        realistic_service = MockDataService(DataGenerationMode.REALISTIC)
        testing_service = MockDataService(DataGenerationMode.TESTING)

        realistic_data = await realistic_service.generate_user_activity_data(user_count=5)
        testing_data = await testing_service.generate_user_activity_data(user_count=5)

        # Realistic mode should generate more activities per user
        realistic_activities = [len(data["activities"]) for data in realistic_data.values()]
        testing_activities = [len(data["activities"]) for data in testing_data.values()]

        # Realistic mode generates 10-100 activities, testing mode 5-20
        assert all(10 <= count <= 100 for count in realistic_activities)
        assert all(5 <= count <= 20 for count in testing_activities)

    async def test_user_activity_data_quality(self, service):
        """Test data quality of generated user activities."""
        user_activities = await service.generate_user_activity_data(user_count=3)

        for user_id, user_data in user_activities.items():
            profile = user_data["profile"]
            activities = user_data["activities"]

            # Check profile data types and values
            assert profile["user_id"] == user_id
            assert profile["role"] in ["admin", "user", "viewer", "analyst"]
            assert profile["department"] in ["IT", "Finance", "HR", "Marketing", "Operations"]
            assert profile["risk_level"] in service._risk_levels
            assert isinstance(profile["last_login"], datetime)

            # Check activity data
            for activity in activities:
                assert isinstance(activity["timestamp"], datetime)
                assert activity["action"] in ["login", "logout", "file_access", "api_call", "data_export"]
                assert isinstance(activity["resource"], str)
                assert isinstance(activity["ip_address"], str)
                assert isinstance(activity["success"], bool)
                assert isinstance(activity["duration_seconds"], int)
                assert isinstance(activity["bytes_transferred"], int)
                assert 1 <= activity["duration_seconds"] <= 3600
                assert 1024 <= activity["bytes_transferred"] <= 1048576


class TestSystemMetricsGeneration:
    """Test system metrics generation functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_generate_system_metrics_default_params(self, service):
        """Test system metrics generation with default parameters."""
        metrics = await service.generate_system_metrics()

        # Should generate 24 hours / 15 minutes = 96 + 1 data points
        expected_count = (24 * 60) // 15 + 1
        assert len(metrics) == expected_count

        # Check metric structure
        metric = metrics[0]
        required_keys = [
            "timestamp",
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
            "network_io_mbps",
            "disk_io_iops",
            "active_connections",
            "response_time_ms",
            "error_rate_percent",
            "throughput_rps",
        ]
        for key in required_keys:
            assert key in metric

        # Verify chronological order
        timestamps = [metric["timestamp"] for metric in metrics]
        assert timestamps == sorted(timestamps)

    async def test_generate_system_metrics_custom_params(self, service):
        """Test system metrics generation with custom parameters."""
        metrics = await service.generate_system_metrics(
            hours_back=12,
            granularity_minutes=30,
        )

        expected_count = (12 * 60) // 30 + 1
        assert len(metrics) == expected_count

    async def test_system_metrics_data_quality(self, service):
        """Test data quality of generated system metrics."""
        metrics = await service.generate_system_metrics(hours_back=1, granularity_minutes=15)

        for metric in metrics:
            # Check data types
            assert isinstance(metric["timestamp"], datetime)
            assert isinstance(metric["cpu_usage_percent"], (int, float))
            assert isinstance(metric["memory_usage_percent"], (int, float))
            assert isinstance(metric["disk_usage_percent"], float)
            assert isinstance(metric["network_io_mbps"], float)
            assert isinstance(metric["disk_io_iops"], int)
            assert isinstance(metric["active_connections"], int)
            assert isinstance(metric["response_time_ms"], float)
            assert isinstance(metric["error_rate_percent"], float)
            assert isinstance(metric["throughput_rps"], int)

            # Check value ranges
            assert 0 <= metric["cpu_usage_percent"] <= 100
            assert 0 <= metric["memory_usage_percent"] <= 100
            assert 20 <= metric["disk_usage_percent"] <= 80
            assert 10 <= metric["network_io_mbps"] <= 1000
            assert 100 <= metric["disk_io_iops"] <= 5000
            assert 50 <= metric["active_connections"] <= 500
            assert 50 <= metric["response_time_ms"] <= 500
            assert 0 <= metric["error_rate_percent"] <= 5
            assert 100 <= metric["throughput_rps"] <= 1000

    async def test_system_metrics_time_progression(self, service):
        """Test time progression in system metrics."""
        metrics = await service.generate_system_metrics(hours_back=2, granularity_minutes=60)

        # Should have 3 data points (0, 60, 120 minutes)
        assert len(metrics) == 3

        # Check time intervals
        time_diffs = []
        for i in range(1, len(metrics)):
            diff = (metrics[i]["timestamp"] - metrics[i - 1]["timestamp"]).total_seconds()
            time_diffs.append(diff)

        # All intervals should be 60 minutes (3600 seconds)
        assert all(abs(diff - 3600) < 1 for diff in time_diffs)


class TestBehavioralPatternsGeneration:
    """Test behavioral patterns generation functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_generate_behavioral_patterns_default_params(self, service):
        """Test behavioral patterns generation with default parameters."""
        patterns = await service.generate_behavioral_patterns()

        assert len(patterns) == 10  # Default count

        # Check pattern structure
        pattern = patterns[0]
        required_keys = [
            "pattern_id",
            "pattern_type",
            "description",
            "confidence_score",
            "risk_score",
            "affected_users",
            "first_observed",
            "last_observed",
            "frequency",
            "indicators",
            "related_events",
        ]
        for key in required_keys:
            assert key in pattern

    async def test_generate_behavioral_patterns_custom_params(self, service):
        """Test behavioral patterns generation with custom parameters."""
        patterns = await service.generate_behavioral_patterns(
            pattern_count=5,
            min_confidence=80.0,
        )

        assert len(patterns) == 5

        # All patterns should meet minimum confidence
        for pattern in patterns:
            assert pattern["confidence_score"] >= 80.0

    async def test_behavioral_patterns_data_quality(self, service):
        """Test data quality of generated behavioral patterns."""
        patterns = await service.generate_behavioral_patterns(pattern_count=3)

        expected_pattern_types = [
            "unusual_access",
            "anomalous_login",
            "data_exfiltration",
            "privilege_escalation",
            "lateral_movement",
            "brute_force",
            "time_anomaly",
            "location_anomaly",
            "device_anomaly",
        ]

        for pattern in patterns:
            # Check data types
            assert isinstance(pattern["pattern_id"], str)
            assert isinstance(pattern["pattern_type"], str)
            assert isinstance(pattern["description"], str)
            assert isinstance(pattern["confidence_score"], float)
            assert isinstance(pattern["risk_score"], int)
            assert isinstance(pattern["affected_users"], int)
            assert isinstance(pattern["first_observed"], datetime)
            assert isinstance(pattern["last_observed"], datetime)
            assert isinstance(pattern["frequency"], str)
            assert isinstance(pattern["indicators"], list)
            assert isinstance(pattern["related_events"], int)

            # Check value ranges and types
            assert pattern["pattern_type"] in expected_pattern_types
            assert 70.0 <= pattern["confidence_score"] <= 100.0  # Default min_confidence
            assert 1 <= pattern["affected_users"] <= 20
            assert pattern["frequency"] in ["rare", "occasional", "frequent", "persistent"]
            assert len(pattern["indicators"]) >= 1
            assert 5 <= pattern["related_events"] <= 100

            # Check time relationship
            assert pattern["last_observed"] >= pattern["first_observed"]


class TestAlertDataGeneration:
    """Test alert data generation functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_generate_alert_data_default_params(self, service):
        """Test alert data generation with default parameters."""
        alerts = await service.generate_alert_data()

        assert len(alerts) == 25  # Default count

        # Check alert structure
        alert = alerts[0]
        required_keys = [
            "alert_id",
            "alert_type",
            "severity",
            "timestamp",
            "status",
            "assigned_to",
            "source_ip",
            "affected_user",
            "description",
            "evidence_count",
            "false_positive_likelihood",
            "remediation_steps",
        ]
        for key in required_keys:
            assert key in alert

        # Verify reverse chronological order (newest first)
        timestamps = [alert["timestamp"] for alert in alerts]
        assert timestamps == sorted(timestamps, reverse=True)

    async def test_generate_alert_data_custom_params(self, service):
        """Test alert data generation with custom parameters."""
        alerts = await service.generate_alert_data(alert_count=15, days_back=3)

        assert len(alerts) == 15

        # All alerts should be within the last 3 days + some buffer for random hours/minutes
        current_time = datetime.now(UTC)
        oldest_allowed = current_time - timedelta(days=3, hours=23, minutes=59)

        for alert in alerts:
            assert alert["timestamp"] >= oldest_allowed
            assert alert["timestamp"] <= current_time

    async def test_alert_data_quality(self, service):
        """Test data quality of generated alert data."""
        alerts = await service.generate_alert_data(alert_count=5)

        expected_alert_types = [
            "Failed Login Attempts",
            "Suspicious File Access",
            "Privilege Escalation",
            "Data Exfiltration",
            "Malware Detection",
            "Network Anomaly",
            "Policy Violation",
            "Unauthorized Access",
            "Brute Force Attack",
        ]

        expected_severities = ["low", "medium", "high", "critical"]
        expected_statuses = ["open", "investigating", "resolved", "closed"]

        for alert in alerts:
            # Check data types
            assert isinstance(alert["alert_id"], str)
            assert isinstance(alert["alert_type"], str)
            assert isinstance(alert["severity"], str)
            assert isinstance(alert["timestamp"], datetime)
            assert isinstance(alert["status"], str)
            assert alert["assigned_to"] is None or isinstance(alert["assigned_to"], str)
            assert isinstance(alert["source_ip"], str)
            assert isinstance(alert["affected_user"], str)
            assert isinstance(alert["description"], str)
            assert isinstance(alert["evidence_count"], int)
            assert isinstance(alert["false_positive_likelihood"], float)
            assert isinstance(alert["remediation_steps"], list)

            # Check value ranges
            assert alert["alert_type"] in expected_alert_types
            assert alert["severity"] in expected_severities
            assert alert["status"] in expected_statuses
            assert 1 <= alert["evidence_count"] <= 10
            assert 0 <= alert["false_positive_likelihood"] <= 30
            assert len(alert["remediation_steps"]) == 3


class TestInvestigationDataGeneration:
    """Test investigation data generation functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_generate_investigation_data_basic(self, service):
        """Test investigation data generation with basic parameters."""
        start_time = datetime.now(UTC) - timedelta(hours=2)
        end_time = datetime.now(UTC)

        investigation_data = await service.generate_investigation_data(
            start_time=start_time,
            end_time=end_time,
            entity_count=3,
        )

        assert "entities" in investigation_data
        assert len(investigation_data["entities"]) == 3

        # Check entity structure
        entity = investigation_data["entities"][0]
        required_keys = [
            "entity_type",
            "entity_id",
            "risk_score",
            "anomaly_indicators",
            "events",
        ]
        for key in required_keys:
            assert key in entity

    async def test_investigation_data_quality(self, service):
        """Test data quality of investigation data."""
        start_time = datetime.now(UTC) - timedelta(hours=1)
        end_time = datetime.now(UTC)

        investigation_data = await service.generate_investigation_data(
            start_time=start_time,
            end_time=end_time,
            entity_count=2,
        )

        for entity in investigation_data["entities"]:
            # Check data types and values
            assert entity["entity_type"] in ["user", "ip_address", "device"]
            assert isinstance(entity["entity_id"], str)
            assert isinstance(entity["risk_score"], int)
            assert isinstance(entity["anomaly_indicators"], list)
            assert isinstance(entity["events"], list)

            # Check value ranges
            assert 20 <= entity["risk_score"] <= 95
            assert 3 <= len(entity["events"]) <= 25

            # Check event structure and time range
            for event in entity["events"]:
                assert isinstance(event["timestamp"], datetime)
                assert start_time <= event["timestamp"] <= end_time
                assert isinstance(event["event_type"], str)
                assert isinstance(event["risk_score"], int)
                assert isinstance(event["description"], str)
                assert 1 <= event["risk_score"] <= 100

            # Verify events are sorted by timestamp
            event_times = [event["timestamp"] for event in entity["events"]]
            assert event_times == sorted(event_times)


class TestPrivateHelperMethods:
    """Test private helper methods functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    def test_select_weighted_event_type(self, service):
        """Test weighted event type selection."""
        event_types = ["user_login", "failed_login", "data_access", "other_event"]

        # Test multiple selections to verify weighting works
        selections = []
        for _ in range(100):
            event_type = service._select_weighted_event_type(event_types)
            selections.append(event_type)
            assert event_type in event_types

        # Common events should appear more frequently
        login_count = selections.count("user_login")
        data_access_count = selections.count("data_access")
        failed_login_count = selections.count("failed_login")

        # Common events (weight 3) should be more frequent than security events (weight 1)
        assert login_count > failed_login_count
        assert data_access_count > failed_login_count

    def test_generate_ip_address(self, service):
        """Test IP address generation."""
        for _ in range(10):
            ip = service._generate_ip_address()
            assert isinstance(ip, str)

            # Should match one of the IP ranges
            ip_prefix = ".".join(ip.split(".")[:-1]) + "."
            assert ip_prefix in service._ip_ranges

            # Last octet should be 1-254
            last_octet = int(ip.split(".")[-1])
            assert 1 <= last_octet <= 254

    def test_generate_risk_score(self, service):
        """Test risk score generation for different event types."""
        # Test security events (high risk)
        security_events = ["failed_login", "suspicious_activity", "security_alert"]
        for event_type in security_events:
            risk_score = service._generate_risk_score(event_type)
            assert 60 <= risk_score <= 95

        # Test system events (medium risk)
        system_events = ["permission_change", "system_change"]
        for event_type in system_events:
            risk_score = service._generate_risk_score(event_type)
            assert 40 <= risk_score <= 80

        # Test normal events (low risk)
        normal_events = ["user_login", "data_access"]
        for event_type in normal_events:
            risk_score = service._generate_risk_score(event_type)
            assert 10 <= risk_score <= 50

    def test_generate_event_details(self, service):
        """Test event details generation."""
        # Test file upload details
        details = service._generate_event_details("file_upload")
        assert "source" in details
        assert "protocol" in details
        assert "file_size" in details
        assert "file_type" in details
        assert details["file_type"] in ["pdf", "doc", "xls", "img", "txt"]

        # Test data access details
        details = service._generate_event_details("data_access")
        assert "source" in details
        assert "protocol" in details
        assert "database" in details
        assert "query_type" in details
        assert details["query_type"] in ["select", "insert", "update", "delete"]

        # Test generic details
        details = service._generate_event_details("user_login")
        assert "source" in details
        assert "protocol" in details
        assert details["source"] in ["web", "api", "mobile", "desktop"]
        assert details["protocol"] in ["https", "http", "ssh", "ftp"]

    def test_generate_location(self, service):
        """Test location data generation."""
        for _ in range(10):
            location = service._generate_location()
            assert isinstance(location, dict)
            assert "country" in location
            assert "state" in location
            assert "city" in location

            # Should be one of the predefined locations
            expected_locations = [
                {"country": "US", "state": "CA", "city": "San Francisco"},
                {"country": "US", "state": "NY", "city": "New York"},
                {"country": "UK", "state": "England", "city": "London"},
                {"country": "DE", "state": "Bavaria", "city": "Munich"},
                {"country": "JP", "state": "Tokyo", "city": "Tokyo"},
            ]
            assert location in expected_locations

    def test_generate_success_status(self, service):
        """Test success status generation."""
        # Failed login should always return False
        assert service._generate_success_status("failed_login") is False

        # Test suspicious events (30% success rate)
        suspicious_results = []
        for _ in range(100):
            result = service._generate_success_status("suspicious_activity")
            suspicious_results.append(result)

        success_rate = sum(suspicious_results) / len(suspicious_results)
        assert 0.1 < success_rate < 0.5  # Allow some variance

        # Test normal events (95% success rate)
        normal_results = []
        for _ in range(100):
            result = service._generate_success_status("user_login")
            normal_results.append(result)

        success_rate = sum(normal_results) / len(normal_results)
        assert success_rate > 0.8  # Should be high success rate

    def test_calculate_pattern_risk_score(self, service):
        """Test pattern risk score calculation."""
        # Test high-risk patterns
        score = service._calculate_pattern_risk_score("data_exfiltration", 100.0)
        assert score == 90  # base_risk 90 * confidence 1.0

        score = service._calculate_pattern_risk_score("data_exfiltration", 80.0)
        assert score == 72  # base_risk 90 * confidence 0.8

        # Test lower-risk patterns
        score = service._calculate_pattern_risk_score("device_anomaly", 100.0)
        assert score == 35  # base_risk 35 * confidence 1.0

        # Test unknown pattern type
        score = service._calculate_pattern_risk_score("unknown_pattern", 80.0)
        assert score == 40  # default base_risk 50 * confidence 0.8

    def test_generate_pattern_description(self, service):
        """Test pattern description generation."""
        descriptions = {
            "unusual_access": "Unusual resource access patterns detected",
            "anomalous_login": "Login behavior differs from historical patterns",
            "data_exfiltration": "Potential data exfiltration activity identified",
        }

        for pattern_type, expected_desc in descriptions.items():
            desc = service._generate_pattern_description(pattern_type)
            assert desc == expected_desc

        # Test unknown pattern type
        desc = service._generate_pattern_description("unknown_pattern")
        assert desc == "Pattern of type unknown_pattern detected"

    def test_generate_pattern_indicators(self, service):
        """Test pattern indicators generation."""
        # Test specific pattern types
        indicators = service._generate_pattern_indicators("unusual_access")
        expected_indicators = [
            "Access to restricted resources",
            "Multiple resource access in short time",
            "Access outside normal working hours",
        ]
        assert all(indicator in expected_indicators for indicator in indicators)
        assert 1 <= len(indicators) <= 3

        # Test unknown pattern type
        indicators = service._generate_pattern_indicators("unknown_pattern")
        assert indicators == ["Generic suspicious activity"]


class TestCachingFunctionality:
    """Test caching functionality."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_cache_operations(self, service):
        """Test cache get, set, and clear operations."""
        # Test cache is initially empty
        cached_data = await service.get_cached_data("test_key")
        assert cached_data is None

        # Test setting cache
        test_data = {"test": "value"}
        await service.set_cached_data("test_key", test_data)

        cached_data = await service.get_cached_data("test_key")
        assert cached_data == test_data

        # Test cache clear
        await service.clear_cache()
        cached_data = await service.get_cached_data("test_key")
        assert cached_data is None

    async def test_cache_multiple_keys(self, service):
        """Test caching with multiple keys."""
        data1 = {"key1": "value1"}
        data2 = {"key2": "value2"}

        await service.set_cached_data("cache_key_1", data1)
        await service.set_cached_data("cache_key_2", data2)

        assert await service.get_cached_data("cache_key_1") == data1
        assert await service.get_cached_data("cache_key_2") == data2

        # Clear should remove all
        await service.clear_cache()
        assert await service.get_cached_data("cache_key_1") is None
        assert await service.get_cached_data("cache_key_2") is None


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_zero_count_requests(self, service):
        """Test behavior with zero count requests."""
        events = await service.generate_security_events(count=0)
        assert events == []

        user_activities = await service.generate_user_activity_data(user_count=0)
        assert user_activities == {}

        patterns = await service.generate_behavioral_patterns(pattern_count=0)
        assert patterns == []

        alerts = await service.generate_alert_data(alert_count=0)
        assert alerts == []

    async def test_negative_time_ranges(self, service):
        """Test behavior with negative time ranges."""
        events = await service.generate_security_events(count=5, days_back=0)
        assert len(events) == 5

        # All events should be very recent (within minutes)
        now = datetime.now(UTC)
        for event in events:
            time_diff = (now - event["timestamp"]).total_seconds()
            assert time_diff >= 0  # Should not be in the future

    async def test_investigation_data_same_start_end_time(self, service):
        """Test investigation data generation with same start and end time."""
        same_time = datetime.now(UTC)

        investigation_data = await service.generate_investigation_data(
            start_time=same_time,
            end_time=same_time,
            entity_count=1,
        )

        # Should still generate data, events should be at the same time
        assert len(investigation_data["entities"]) == 1
        entity = investigation_data["entities"][0]
        for event in entity["events"]:
            assert event["timestamp"] == same_time

    async def test_extreme_metric_granularity(self, service):
        """Test system metrics with very small granularity."""
        metrics = await service.generate_system_metrics(
            hours_back=1,
            granularity_minutes=1,
        )

        # Should generate 60 + 1 data points
        assert len(metrics) == 61

        # Check time progression
        for i in range(1, len(metrics)):
            time_diff = (metrics[i]["timestamp"] - metrics[i - 1]["timestamp"]).total_seconds()
            assert abs(time_diff - 60) < 1  # 1 minute intervals

    async def test_very_high_min_confidence(self, service):
        """Test behavioral patterns with very high minimum confidence."""
        patterns = await service.generate_behavioral_patterns(
            pattern_count=5,
            min_confidence=99.5,
        )

        assert len(patterns) == 5
        for pattern in patterns:
            assert pattern["confidence_score"] >= 99.5


class TestDataConsistency:
    """Test data consistency and relationships."""

    @pytest.fixture
    async def service(self):
        """Fixture providing MockDataService instance."""
        return MockDataService()

    async def test_event_timestamp_consistency(self, service):
        """Test that events maintain consistent time relationships."""
        events = await service.generate_security_events(count=10, days_back=5)

        # Events should be chronologically ordered
        for i in range(1, len(events)):
            assert events[i]["timestamp"] >= events[i - 1]["timestamp"]

    async def test_user_profile_consistency(self, service):
        """Test that user profiles maintain consistent relationships."""
        user_activities = await service.generate_user_activity_data(user_count=5)

        for user_id, user_data in user_activities.items():
            profile = user_data["profile"]
            activities = user_data["activities"]

            # Profile user_id should match key
            assert profile["user_id"] == user_id

            # Activities should be chronologically ordered
            activity_times = [activity["timestamp"] for activity in activities]
            assert activity_times == sorted(activity_times)

    async def test_pattern_time_relationships(self, service):
        """Test behavioral pattern time relationships."""
        patterns = await service.generate_behavioral_patterns(pattern_count=5)

        for pattern in patterns:
            # last_observed should be >= first_observed
            assert pattern["last_observed"] >= pattern["first_observed"]

            # Both should be in the past
            now = datetime.now(UTC)
            assert pattern["first_observed"] <= now
            assert pattern["last_observed"] <= now

    async def test_investigation_entity_uniqueness(self, service):
        """Test that investigation entities are unique within a dataset."""
        start_time = datetime.now(UTC) - timedelta(hours=1)
        end_time = datetime.now(UTC)

        investigation_data = await service.generate_investigation_data(
            start_time=start_time,
            end_time=end_time,
            entity_count=10,
        )

        entity_ids = [entity["entity_id"] for entity in investigation_data["entities"]]

        # Entity IDs should be unique within the same investigation
        assert len(entity_ids) == len(set(entity_ids))


class TestMockDataServiceRealExecution:
    """Test MockDataService functions with real execution to improve coverage."""

    async def test_generate_security_events_real_execution(self):
        """Test security events generation with real function execution."""
        service = MockDataService()

        events = await service.generate_security_events(count=10, days_back=5)

        assert isinstance(events, list)
        assert len(events) == 10
        assert all(isinstance(event, dict) for event in events)

        # Verify event structure
        event = events[0]
        required_keys = [
            "event_id",
            "event_type",
            "timestamp",
            "user_id",
            "ip_address",
            "user_agent",
            "risk_score",
            "details",
            "session_id",
            "location",
            "success",
        ]
        for key in required_keys:
            assert key in event

    async def test_generate_user_activity_data_real_execution(self):
        """Test user activity data generation with real function execution."""
        service = MockDataService()

        user_activities = await service.generate_user_activity_data(user_count=3, activity_window_days=7)

        assert isinstance(user_activities, dict)
        assert len(user_activities) == 3

        # Verify user data structure
        for _user_id, user_data in user_activities.items():
            assert "profile" in user_data
            assert "activities" in user_data
            assert isinstance(user_data["profile"], dict)
            assert isinstance(user_data["activities"], list)

    async def test_generate_system_metrics_real_execution(self):
        """Test system metrics generation with real function execution."""
        service = MockDataService()

        metrics = await service.generate_system_metrics(hours_back=2, granularity_minutes=30)

        assert isinstance(metrics, list)
        assert len(metrics) == 5  # 2 hours / 30 minutes + 1

        # Verify metric structure
        metric = metrics[0]
        required_keys = [
            "timestamp",
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
            "network_io_mbps",
            "disk_io_iops",
            "active_connections",
            "response_time_ms",
            "error_rate_percent",
            "throughput_rps",
        ]
        for key in required_keys:
            assert key in metric

    async def test_generate_behavioral_patterns_real_execution(self):
        """Test behavioral patterns generation with real function execution."""
        service = MockDataService()

        patterns = await service.generate_behavioral_patterns(pattern_count=5, min_confidence=75.0)

        assert isinstance(patterns, list)
        assert len(patterns) == 5

        # Verify pattern structure
        pattern = patterns[0]
        required_keys = [
            "pattern_id",
            "pattern_type",
            "description",
            "confidence_score",
            "risk_score",
            "affected_users",
            "first_observed",
            "last_observed",
            "frequency",
            "indicators",
            "related_events",
        ]
        for key in required_keys:
            assert key in pattern

    async def test_generate_alert_data_real_execution(self):
        """Test alert data generation with real function execution."""
        service = MockDataService()

        alerts = await service.generate_alert_data(alert_count=5, days_back=3)

        assert isinstance(alerts, list)
        assert len(alerts) == 5

        # Verify alert structure
        alert = alerts[0]
        required_keys = [
            "alert_id",
            "alert_type",
            "severity",
            "timestamp",
            "status",
            "source_ip",
            "affected_user",
            "description",
            "evidence_count",
            "false_positive_likelihood",
            "remediation_steps",
        ]
        for key in required_keys:
            assert key in alert

    async def test_generate_investigation_data_real_execution(self):
        """Test investigation data generation with real function execution."""
        service = MockDataService()

        start_time = datetime.now(UTC) - timedelta(hours=2)
        end_time = datetime.now(UTC) - timedelta(hours=1)

        investigation_data = await service.generate_investigation_data(
            start_time=start_time,
            end_time=end_time,
            entity_count=2,
        )

        assert isinstance(investigation_data, dict)
        assert "entities" in investigation_data
        assert len(investigation_data["entities"]) == 2

        # Verify entity structure
        entity = investigation_data["entities"][0]
        required_keys = ["entity_type", "entity_id", "risk_score", "anomaly_indicators", "events"]
        for key in required_keys:
            assert key in entity

    async def test_cache_operations_real_execution(self):
        """Test cache operations with real function execution."""
        service = MockDataService()

        # Test cache operations
        assert await service.get_cached_data("test_key") is None

        test_data = {"test": "value", "number": 42}
        await service.set_cached_data("test_key", test_data)

        cached_data = await service.get_cached_data("test_key")
        assert cached_data == test_data

        await service.clear_cache()
        assert await service.get_cached_data("test_key") is None

    async def test_private_helper_methods_real_execution(self):
        """Test private helper methods with real function execution."""
        service = MockDataService()

        # Test _select_weighted_event_type
        event_types = ["user_login", "failed_login", "data_access"]
        selected_type = service._select_weighted_event_type(event_types)
        assert selected_type in event_types

        # Test _generate_ip_address
        ip = service._generate_ip_address()
        assert isinstance(ip, str)
        assert len(ip.split(".")) == 4

        # Test _generate_risk_score
        risk_score = service._generate_risk_score("failed_login")
        assert isinstance(risk_score, int)
        assert 60 <= risk_score <= 95

        # Test _generate_event_details
        details = service._generate_event_details("file_upload")
        assert isinstance(details, dict)
        assert "source" in details
        assert "file_size" in details

        # Test _generate_location
        location = service._generate_location()
        assert isinstance(location, dict)
        assert "country" in location

        # Test _generate_success_status
        success = service._generate_success_status("failed_login")
        assert success is False

        # Test _calculate_pattern_risk_score
        risk_score = service._calculate_pattern_risk_score("data_exfiltration", 80.0)
        assert isinstance(risk_score, int)
        assert risk_score == 72  # 90 * 0.8

        # Test _generate_pattern_description
        description = service._generate_pattern_description("unusual_access")
        assert isinstance(description, str)
        assert description == "Unusual resource access patterns detected"

        # Test _generate_pattern_indicators
        indicators = service._generate_pattern_indicators("unusual_access")
        assert isinstance(indicators, list)
        assert len(indicators) >= 1
