"""Comprehensive unit tests for SecurityMonitor.

Tests brute force detection, rate limiting, suspicious activity monitoring,
and real-time threat detection with <10ms performance requirements.
"""

import asyncio
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.models import SecurityEvent, SecurityEventType, SecurityEventSeverity
from src.auth.services.security_monitor import FailedAttempt, SecurityMonitor
from tests.fixtures.security_service_mocks import MockSecurityLogger


class TestSecurityMonitorInitialization:
    """Test security monitor initialization and configuration."""

    def test_init_default_configuration(self):
        """Test security monitor initialization with default settings."""
        monitor = SecurityMonitor()

        # Check default brute force settings
        assert monitor.brute_force_threshold == 5
        assert monitor.brute_force_window_minutes == 15
        assert monitor.lockout_duration_minutes == 30

        # Check default rate limiting settings
        assert monitor.rate_limit_requests == 100
        assert monitor.rate_limit_window_seconds == 60

        # Check internal state
        assert isinstance(monitor._failed_attempts, dict)
        assert isinstance(monitor._locked_accounts, dict)
        assert isinstance(monitor._rate_limit_tracker, dict)
        assert monitor._db is not None
        assert monitor._security_logger is not None
        assert monitor._alert_engine is not None

    def test_init_custom_configuration(self):
        """Test security monitor initialization with custom settings."""
        monitor = SecurityMonitor(
            brute_force_threshold=10,
            brute_force_window_minutes=30,
            lockout_duration_minutes=60,
            rate_limit_requests=50,
            rate_limit_window_seconds=30,
        )

        assert monitor.brute_force_threshold == 10
        assert monitor.brute_force_window_minutes == 30
        assert monitor.lockout_duration_minutes == 60
        assert monitor.rate_limit_requests == 50
        assert monitor.rate_limit_window_seconds == 30

    def test_init_with_dependencies(self):
        """Test initialization with custom dependencies."""
        mock_db = MagicMock()
        mock_logger = MagicMock()
        mock_alert_engine = MagicMock()

        monitor = SecurityMonitor(db=mock_db, security_logger=mock_logger, alert_engine=mock_alert_engine)

        assert monitor._db == mock_db
        assert monitor._security_logger == mock_logger
        assert monitor._alert_engine == mock_alert_engine


class TestSecurityMonitorBruteForceDetection:
    """Test brute force attack detection and prevention."""

    @pytest.fixture
    def monitor(self):
        """Create security monitor with mocked dependencies."""
        # Create mocked dependencies directly
        mock_db = AsyncMock()
        mock_logger = MockSecurityLogger()  # Use MockSecurityLogger instead of AsyncMock
        mock_alert_engine = AsyncMock()

        # Create monitor with injected dependencies
        monitor = SecurityMonitor(
            failed_attempts_threshold=3,  # Lock account after 3 attempts
            brute_force_threshold=3,      # Detect brute force after 3 attempts
            brute_force_window_minutes=5,
            db=mock_db,
            security_logger=mock_logger,
            alert_engine=mock_alert_engine
        )

        yield monitor

    async def test_record_failed_login_first_attempt(self, monitor):
        """Test recording first failed login attempt."""
        user_id = "test_user"
        ip_address = "192.168.1.100"

        result = await monitor.record_failed_login(user_id, ip_address)

        assert result is False  # Not yet brute force
        assert user_id in monitor._failed_attempts
        assert len(monitor._failed_attempts[user_id]) == 1
        assert monitor._failed_attempts[user_id][0].ip_address == ip_address

    async def test_record_failed_login_below_threshold(self, monitor):
        """Test recording failed logins below brute force threshold."""
        user_id = "test_user"
        ip_address = "192.168.1.100"

        # Record attempts below threshold
        for _i in range(monitor.brute_force_threshold - 1):
            result = await monitor.record_failed_login(user_id, ip_address)
            assert result is False

        assert len(monitor._failed_attempts[user_id]) == monitor.brute_force_threshold - 1

    async def test_record_failed_login_exceeds_threshold(self, monitor):
        """Test brute force detection when threshold is exceeded."""
        user_id = "test_user"
        ip_address = "192.168.1.100"

        # Record attempts up to threshold
        for _i in range(monitor.brute_force_threshold):
            result = await monitor.record_failed_login(user_id, ip_address)

        # Last attempt should trigger brute force detection
        assert result is True
        assert user_id in monitor._locked_accounts

        # Verify security event was logged
        monitor._security_logger.log_event.assert_called()
        call_args = monitor._security_logger.log_event.call_args
        assert call_args[1]["event_type"] == SecurityEventType.BRUTE_FORCE_ATTEMPT

        # Verify alert was triggered
        monitor._alert_engine.trigger_alert.assert_called()

    async def test_record_failed_login_different_ips(self, monitor):
        """Test brute force detection with attempts from different IPs."""
        user_id = "test_user"

        # Record attempts from different IP addresses
        for i in range(monitor.brute_force_threshold):
            ip_address = f"192.168.1.{i + 100}"
            result = await monitor.record_failed_login(user_id, ip_address)

        # Should still trigger brute force (same user, different IPs)
        assert result is True
        assert user_id in monitor._locked_accounts

    async def test_record_failed_login_outside_time_window(self, monitor):
        """Test that old failed attempts don't count toward brute force."""
        user_id = "test_user"
        ip_address = "192.168.1.100"

        # Mock old attempts outside time window
        old_time = datetime.now(UTC) - timedelta(minutes=monitor.failed_attempts_window_minutes + 1)
        monitor._failed_attempts_by_user[user_id] = deque([
            FailedAttempt(
                timestamp=old_time,
                ip_address=ip_address,
                user_agent="test-agent",
                endpoint="/login",
                error_type="invalid_password",
                user_id=user_id,
            ) for _ in range(5)
        ])

        # New attempt should not trigger brute force (old attempts expired)
        result = await monitor.record_failed_login(user_id, ip_address)
        assert result is False

        # Old attempts should be cleaned up
        assert len(monitor._failed_attempts_by_user[user_id]) == 1  # Only new attempt

    async def test_is_account_locked_true(self, monitor):
        """Test account lockout check when account is locked."""
        user_id = "test_user"

        # Simulate locked account
        monitor._locked_accounts[user_id] = datetime.now(UTC)

        is_locked = monitor.is_account_locked(user_id)
        assert is_locked is True

    async def test_is_account_locked_false(self, monitor):
        """Test account lockout check when account is not locked."""
        user_id = "test_user"

        is_locked = monitor.is_account_locked(user_id)
        assert is_locked is False

    async def test_is_account_locked_expired_lockout(self, monitor):
        """Test that expired lockouts are automatically cleared."""
        user_id = "test_user"

        # Simulate expired lockout
        old_lockout_time = datetime.now(UTC) - timedelta(minutes=monitor.lockout_duration_minutes + 1)
        monitor._locked_accounts[user_id] = old_lockout_time

        is_locked = monitor.is_account_locked(user_id)
        assert is_locked is False

        # Expired lockout should be removed
        assert user_id not in monitor._locked_accounts

    async def test_clear_failed_attempts_success(self, monitor):
        """Test clearing failed attempts on successful login."""
        user_id = "test_user"

        # Add some failed attempts
        monitor._failed_attempts[user_id] = [
            {"ip_address": "192.168.1.100", "timestamp": datetime.now()} for _ in range(3)
        ]

        await monitor.clear_failed_attempts(user_id)

        assert user_id not in monitor._failed_attempts

    async def test_unlock_account_manual(self, monitor):
        """Test manual account unlock."""
        user_id = "test_user"
        admin_user = "admin"

        # Lock account first
        monitor._locked_accounts[user_id] = datetime.now(UTC)

        result = await monitor.unlock_account(user_id, admin_user)

        assert result is True
        assert user_id not in monitor._locked_accounts

        # Verify security event was logged
        monitor._security_logger.log_event.assert_called()
        call_args = monitor._security_logger.log_event.call_args
        assert call_args[1]["event_type"] == SecurityEventType.ACCOUNT_UNLOCK
        assert call_args[1]["details"]["unlock_type"] == "manual"


class TestSecurityMonitorRateLimiting:
    """Test rate limiting functionality."""

    @pytest.fixture
    def monitor(self):
        """Create security monitor with mocked dependencies."""
        with patch("src.auth.services.security_monitor.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.security_monitor.SecurityLogger") as mock_logger_class:
                with patch("src.auth.services.security_monitor.AlertEngine") as mock_alert_class:
                    mock_db = AsyncMock()
                    mock_logger = MockSecurityLogger()  # Use MockSecurityLogger instead of AsyncMock
                    mock_alert_engine = AsyncMock()

                    mock_db_class.return_value = mock_db
                    mock_logger_class.return_value = mock_logger
                    mock_alert_class.return_value = mock_alert_engine

                    monitor = SecurityMonitor(rate_limit_requests=5, rate_limit_window_seconds=10)
                    monitor._db = mock_db
                    monitor._security_logger = mock_logger
                    monitor._alert_engine = mock_alert_engine

                    yield monitor

    async def test_check_rate_limit_within_limits(self, monitor):
        """Test rate limiting when requests are within limits."""
        user_id = "test_user"
        endpoint = "/api/login"

        # Make requests within limit
        for _i in range(monitor.rate_limit_requests - 1):
            is_limited = await monitor.check_rate_limit(user_id, endpoint)
            assert is_limited is False

    async def test_check_rate_limit_exceeds_limit(self, monitor):
        """Test rate limiting when request limit is exceeded."""
        user_id = "test_user"
        endpoint = "/api/login"

        # Make requests up to limit
        for _i in range(monitor.rate_limit_requests):
            is_limited = await monitor.check_rate_limit(user_id, endpoint)

        # Next request should be rate limited
        is_limited = await monitor.check_rate_limit(user_id, endpoint)
        assert is_limited is True

        # Verify rate limit event was logged
        monitor._security_logger.log_event.assert_called()
        call_args = monitor._security_logger.log_event.call_args
        assert call_args[1]["event_type"] == SecurityEventType.RATE_LIMIT_EXCEEDED

    async def test_check_rate_limit_different_endpoints(self, monitor):
        """Test rate limiting is per endpoint."""
        user_id = "test_user"
        endpoint1 = "/api/login"
        endpoint2 = "/api/data"

        # Use up rate limit for endpoint1
        for _i in range(monitor.rate_limit_requests):
            is_limited = await monitor.check_rate_limit(user_id, endpoint1)

        # endpoint2 should still be available
        is_limited = await monitor.check_rate_limit(user_id, endpoint2)
        assert is_limited is False

    async def test_check_rate_limit_different_users(self, monitor):
        """Test rate limiting is per user."""
        user1 = "user1"
        user2 = "user2"
        endpoint = "/api/login"

        # Use up rate limit for user1
        for _i in range(monitor.rate_limit_requests):
            is_limited = await monitor.check_rate_limit(user1, endpoint)

        # user2 should still be available
        is_limited = await monitor.check_rate_limit(user2, endpoint)
        assert is_limited is False

    async def test_rate_limit_window_expiry(self, monitor):
        """Test that rate limits reset after time window."""
        user_id = "test_user"
        endpoint = "/api/login"

        # Use up rate limit
        for _i in range(monitor.rate_limit_requests):
            await monitor.check_rate_limit(user_id, endpoint)

        # Mock time passing beyond window
        with patch("src.auth.services.security_monitor.datetime") as mock_datetime:
            future_time = datetime.now(UTC) + timedelta(seconds=monitor.rate_limit_window_seconds + 1)
            mock_datetime.now.return_value = future_time

            # Should be able to make requests again
            is_limited = await monitor.check_rate_limit(user_id, endpoint)
            assert is_limited is False


class TestSecurityMonitorSuspiciousActivity:
    """Test suspicious activity detection."""

    @pytest.fixture
    def monitor(self):
        """Create security monitor with mocked dependencies."""
        with patch("src.auth.services.security_monitor.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.security_monitor.SecurityLogger") as mock_logger_class:
                with patch("src.auth.services.security_monitor.AlertEngine") as mock_alert_class:
                    mock_db = AsyncMock()
                    mock_logger = MockSecurityLogger()  # Use MockSecurityLogger instead of AsyncMock
                    mock_alert_engine = AsyncMock()

                    mock_db_class.return_value = mock_db
                    mock_logger_class.return_value = mock_logger
                    mock_alert_class.return_value = mock_alert_engine

                    monitor = SecurityMonitor()
                    monitor._db = mock_db
                    monitor._security_logger = mock_logger
                    monitor._alert_engine = mock_alert_engine

                    yield monitor

    async def test_detect_unusual_location_new_country(self, monitor):
        """Test detection of login from unusual location."""
        user_id = "test_user"
        current_ip = "1.2.3.4"  # Different country IP

        # Mock previous logins from different location
        mock_events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address="192.168.1.100",  # Local IP
                severity=SecurityEventSeverity.INFO,
                source="auth",
                metadata={"location": "US"},
            ),
        ]
        monitor._db.get_events_by_user_id.return_value = mock_events

        is_suspicious = await monitor.detect_unusual_location(user_id, current_ip)

        # Should detect as suspicious (different location pattern)
        assert is_suspicious is True

        # Verify suspicious activity was logged
        monitor._security_logger.log_event.assert_called()

    async def test_detect_unusual_location_known_location(self, monitor):
        """Test no detection for known locations."""
        user_id = "test_user"
        current_ip = "192.168.1.101"  # Similar to known IPs

        # Mock previous logins from similar location
        mock_events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address="192.168.1.100",
                severity=SecurityEventSeverity.INFO,
                source="auth",
            ),
        ]
        monitor._db.get_events_by_user_id.return_value = mock_events

        is_suspicious = await monitor.detect_unusual_location(user_id, current_ip)

        assert is_suspicious is False

    async def test_detect_unusual_time_outside_pattern(self, monitor):
        """Test detection of login at unusual time."""
        user_id = "test_user"

        # Mock user typically logs in during business hours (9 AM - 5 PM)
        mock_events = []
        for hour in range(9, 17):  # 9 AM to 5 PM
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now().replace(hour=hour, minute=0, second=0),
                severity=SecurityEventSeverity.INFO,
                source="auth",
            )
            mock_events.append(event)

        monitor._db.get_events_by_user_id.return_value = mock_events

        # Test login at 3 AM (unusual time)
        unusual_time = datetime.now().replace(hour=3, minute=0, second=0)
        is_suspicious = await monitor.detect_unusual_time(user_id, unusual_time)

        assert is_suspicious is True

    async def test_detect_unusual_time_within_pattern(self, monitor):
        """Test no detection for typical login times."""
        user_id = "test_user"

        # Mock user typically logs in during business hours
        mock_events = []
        for hour in range(9, 17):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now().replace(hour=hour, minute=0, second=0),
                severity=SecurityEventSeverity.INFO,
                source="auth",
            )
            mock_events.append(event)

        monitor._db.get_events_by_user_id.return_value = mock_events

        # Test login at 11 AM (typical time)
        typical_time = datetime.now().replace(hour=11, minute=0, second=0)
        is_suspicious = await monitor.detect_unusual_time(user_id, typical_time)

        assert is_suspicious is False

    async def test_detect_multiple_simultaneous_sessions(self, monitor):
        """Test detection of suspicious concurrent sessions."""
        user_id = "test_user"

        # Mock multiple active sessions from different IPs
        mock_events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address=f"192.168.1.{i}",
                timestamp=datetime.now() - timedelta(minutes=5),
                severity=SecurityEventSeverity.INFO,
                source="auth",
            )
            for i in range(100, 105)  # 5 different IPs
        ]

        monitor._db.get_events_by_date_range.return_value = mock_events

        is_suspicious = await monitor.detect_multiple_simultaneous_sessions(user_id)

        assert is_suspicious is True

        # Verify alert was triggered
        monitor._alert_engine.trigger_alert.assert_called()

    async def test_analyze_user_behavior_patterns_deviation(self, monitor):
        """Test behavior pattern analysis for deviations."""
        user_id = "test_user"

        # Mock typical user behavior pattern
        mock_events = []
        # User typically has 10-15 events per day
        for i in range(12):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=user_id,
                timestamp=datetime.now() - timedelta(hours=i),
                severity=SecurityEventSeverity.INFO,
                source="auth",
            )
            mock_events.append(event)

        monitor._db.get_events_by_user_id.return_value = mock_events

        # Current session with unusually high activity (100 events)
        current_activity_count = 100

        behavior_score = await monitor.analyze_user_behavior_patterns(user_id, current_activity_count)

        # Should return high suspicion score (activity much higher than normal)
        assert behavior_score > 0.7  # 70% suspicious
        assert behavior_score <= 1.0


class TestSecurityMonitorRealTimeDetection:
    """Test real-time threat detection and monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create security monitor with mocked dependencies."""
        with patch("src.auth.services.security_monitor.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.security_monitor.SecurityLogger") as mock_logger_class:
                with patch("src.auth.services.security_monitor.AlertEngine") as mock_alert_class:
                    mock_db = AsyncMock()
                    mock_logger = MockSecurityLogger()  # Use MockSecurityLogger instead of AsyncMock
                    mock_alert_engine = AsyncMock()

                    mock_db_class.return_value = mock_db
                    mock_logger_class.return_value = mock_logger
                    mock_alert_class.return_value = mock_alert_engine

                    monitor = SecurityMonitor()
                    monitor._db = mock_db
                    monitor._security_logger = mock_logger
                    monitor._alert_engine = mock_alert_engine

                    yield monitor

    async def test_process_security_event_brute_force(self, monitor):
        """Test real-time processing of brute force events."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILURE,
            user_id="test_user",
            ip_address="192.168.1.100",
            severity=SecurityEventSeverity.WARNING,
            source="auth",
        )

        # Mock brute force detection
        with patch.object(monitor, "record_failed_login", return_value=True) as mock_record:
            await monitor.process_security_event(event)

            # Should have checked for brute force
            mock_record.assert_called_once_with("test_user", "192.168.1.100")

    async def test_process_security_event_suspicious_location(self, monitor):
        """Test real-time processing of location-based suspicions."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id="test_user",
            ip_address="1.2.3.4",
            severity=SecurityEventSeverity.INFO,
            source="auth",
        )

        # Mock unusual location detection
        with patch.object(monitor, "detect_unusual_location", return_value=True) as mock_location:
            await monitor.process_security_event(event)

            # Should have checked location
            mock_location.assert_called_once_with("test_user", "1.2.3.4")

    async def test_get_security_metrics_comprehensive(self, monitor):
        """Test comprehensive security metrics collection."""
        # Setup mock data
        monitor._failed_attempts = {
            "user1": [{"ip_address": "1.2.3.4", "timestamp": datetime.now()}],
            "user2": [{"ip_address": "5.6.7.8", "timestamp": datetime.now()}],
        }
        monitor._locked_accounts = {"locked_user": {"locked_at": datetime.now(), "ip_address": "9.10.11.12"}}
        monitor._rate_limit_tracker = {("user1", "/api/login"): [datetime.now(), datetime.now()]}

        metrics = await monitor.get_security_metrics()

        assert metrics["failed_login_attempts"] == 2
        assert metrics["locked_accounts"] == 1
        assert metrics["rate_limited_requests"] == 1
        assert "uptime_hours" in metrics
        assert "total_events_processed" in metrics

    async def test_cleanup_expired_data(self, monitor):
        """Test cleanup of expired tracking data."""
        # Add expired data
        old_time = datetime.now() - timedelta(hours=2)
        monitor._failed_attempts = {
            "user1": [{"ip_address": "1.2.3.4", "timestamp": old_time}],
            "user2": [{"ip_address": "5.6.7.8", "timestamp": datetime.now()}],
        }
        monitor._rate_limit_tracker = {("user1", "/api/login"): [old_time], ("user2", "/api/data"): [datetime.now()]}

        await monitor.cleanup_expired_data()

        # Old data should be cleaned up
        assert "user1" not in monitor._failed_attempts
        assert "user2" in monitor._failed_attempts
        assert ("user1", "/api/login") not in monitor._rate_limit_tracker
        assert ("user2", "/api/data") in monitor._rate_limit_tracker


class TestSecurityMonitorPerformance:
    """Test performance requirements for security monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create security monitor with mocked dependencies."""
        with patch("src.auth.services.security_monitor.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.security_monitor.SecurityLogger") as mock_logger_class:
                with patch("src.auth.services.security_monitor.AlertEngine") as mock_alert_class:
                    mock_db = AsyncMock()
                    mock_logger = MockSecurityLogger()  # Use MockSecurityLogger instead of AsyncMock
                    mock_alert_engine = AsyncMock()

                    mock_db_class.return_value = mock_db
                    mock_logger_class.return_value = mock_logger
                    mock_alert_class.return_value = mock_alert_engine

                    monitor = SecurityMonitor()
                    monitor._db = mock_db
                    monitor._security_logger = mock_logger
                    monitor._alert_engine = mock_alert_engine

                    yield monitor

    @pytest.mark.performance
    async def test_record_failed_login_performance(self, monitor):
        """Test that record_failed_login meets <10ms requirement."""
        start_time = time.time()
        await monitor.record_failed_login("test_user", "192.168.1.100")
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 10, f"record_failed_login took {execution_time:.2f}ms (>10ms limit)"

    @pytest.mark.performance
    async def test_is_account_locked_performance(self, monitor):
        """Test that account lock check meets <10ms requirement."""
        start_time = time.time()
        monitor.is_account_locked("test_user")
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 10, f"is_account_locked took {execution_time:.2f}ms (>10ms limit)"

    @pytest.mark.performance
    async def test_check_rate_limit_performance(self, monitor):
        """Test that rate limit check meets <10ms requirement."""
        start_time = time.time()
        await monitor.check_rate_limit("test_user", "/api/login")
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 10, f"check_rate_limit took {execution_time:.2f}ms (>10ms limit)"

    @pytest.mark.performance
    async def test_process_security_event_performance(self, monitor):
        """Test that event processing meets <10ms requirement."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id="test_user",
            ip_address="192.168.1.100",
            severity=SecurityEventSeverity.INFO,
            source="auth",
        )

        start_time = time.time()
        await monitor.process_security_event(event)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 10, f"process_security_event took {execution_time:.2f}ms (>10ms limit)"

    @pytest.mark.performance
    async def test_concurrent_monitoring_performance(self, monitor):
        """Test concurrent monitoring operations performance."""

        async def simulate_user_activity(user_id: str, operations: int):
            """Simulate user activity for performance testing."""
            for i in range(operations):
                await monitor.record_failed_login(user_id, f"192.168.1.{i % 255}")
                monitor.is_account_locked(user_id)
                await monitor.check_rate_limit(user_id, "/api/login")

        # Run concurrent monitoring for multiple users
        start_time = time.time()
        await asyncio.gather(
            simulate_user_activity("user1", 10),
            simulate_user_activity("user2", 10),
            simulate_user_activity("user3", 10),
            simulate_user_activity("user4", 10),
            simulate_user_activity("user5", 10),
        )
        end_time = time.time()

        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        operations_count = 5 * 10 * 3  # 5 users, 10 operations each, 3 calls per operation
        avg_time_per_operation = total_time / operations_count

        assert avg_time_per_operation < 15, f"Concurrent monitoring avg {avg_time_per_operation:.2f}ms per operation"

    @pytest.mark.performance
    async def test_memory_usage_stability(self, monitor):
        """Test that memory usage remains stable under load."""
        import gc

        # Force garbage collection before test
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Simulate high activity load
        for i in range(1000):
            await monitor.record_failed_login(f"user{i % 10}", f"192.168.1.{i % 255}")
            await monitor.check_rate_limit(f"user{i % 10}", f"/api/endpoint{i % 5}")

            # Clean up every 100 operations to prevent accumulation
            if i % 100 == 0:
                await monitor.cleanup_expired_data()

        # Force garbage collection after test
        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory growth should be reasonable (less than 50% increase)
        memory_growth_ratio = final_objects / initial_objects
        assert memory_growth_ratio < 1.5, f"Memory usage grew by {memory_growth_ratio:.2f}x"


class TestSecurityMonitorErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def monitor(self):
        """Create security monitor with mocked dependencies."""
        with patch("src.auth.services.security_monitor.SecurityEventsDatabase") as mock_db_class:
            with patch("src.auth.services.security_monitor.SecurityLogger") as mock_logger_class:
                with patch("src.auth.services.security_monitor.AlertEngine") as mock_alert_class:
                    mock_db = AsyncMock()
                    mock_logger = MockSecurityLogger()  # Use MockSecurityLogger instead of AsyncMock
                    mock_alert_engine = AsyncMock()

                    mock_db_class.return_value = mock_db
                    mock_logger_class.return_value = mock_logger
                    mock_alert_class.return_value = mock_alert_engine

                    monitor = SecurityMonitor()
                    monitor._db = mock_db
                    monitor._security_logger = mock_logger
                    monitor._alert_engine = mock_alert_engine

                    yield monitor

    async def test_record_failed_login_none_user_id(self, monitor):
        """Test handling of None user_id in failed login recording."""
        with pytest.raises(ValueError, match="user_id cannot be None"):
            await monitor.record_failed_login(None, "192.168.1.100")

    async def test_record_failed_login_empty_user_id(self, monitor):
        """Test handling of empty user_id in failed login recording."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            await monitor.record_failed_login("", "192.168.1.100")

    async def test_record_failed_login_invalid_ip(self, monitor):
        """Test handling of invalid IP address."""
        # Should still work but log the invalid IP
        result = await monitor.record_failed_login("test_user", "invalid_ip")
        assert result is False  # First attempt, not brute force yet

    async def test_database_error_handling(self, monitor):
        """Test handling of database errors."""
        monitor._db.get_events_by_user_id.side_effect = Exception("Database error")

        # Should handle gracefully without crashing
        is_suspicious = await monitor.detect_unusual_location("test_user", "192.168.1.100")

        # Should return safe default (not suspicious) on error
        assert is_suspicious is False

    async def test_logger_error_handling(self, monitor):
        """Test handling of logging errors."""
        monitor._security_logger.log_security_event.side_effect = Exception("Logging error")

        # Should not crash on logging error
        result = await monitor.record_failed_login("test_user", "192.168.1.100")
        assert isinstance(result, bool)

    async def test_alert_engine_error_handling(self, monitor):
        """Test handling of alert engine errors."""
        monitor._alert_engine.trigger_alert.side_effect = Exception("Alert error")

        # Should not crash on alert error
        for _i in range(monitor.brute_force_threshold):
            await monitor.record_failed_login("test_user", "192.168.1.100")

        # Should still detect brute force despite alert error
        assert "test_user" in monitor._locked_accounts

    async def test_concurrent_access_thread_safety(self, monitor):
        """Test thread safety under concurrent access."""
        user_id = "concurrent_user"

        async def concurrent_operations():
            """Perform concurrent operations on the same user."""
            tasks = []
            for i in range(10):
                tasks.append(monitor.record_failed_login(user_id, f"192.168.1.{i}"))
                # Check account lock status (sync method)
                monitor.is_account_locked(user_id)
                tasks.append(monitor.check_rate_limit(user_id, "/api/test"))

            await asyncio.gather(*tasks)

        # Run multiple concurrent operation sets
        await asyncio.gather(concurrent_operations(), concurrent_operations(), concurrent_operations())

        # System should remain consistent
        # If user got locked, they should stay locked
        is_locked = monitor.is_account_locked(user_id)
        if is_locked:
            assert user_id in monitor._locked_accounts

        # No crashes or corrupted state should occur
        assert isinstance(monitor._failed_attempts, dict)
        assert isinstance(monitor._locked_accounts, dict)
        assert isinstance(monitor._rate_limit_tracker, dict)
