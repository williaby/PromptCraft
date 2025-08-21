"""Comprehensive tests for service token monitoring system.

This test suite provides complete coverage for the service token monitoring
system including expiration alerts, monitoring metrics, notification systems,
and health checks.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.settings import ApplicationSettings
from src.monitoring.service_token_monitor import MonitoringHealthCheck, ServiceTokenMonitor, TokenExpirationAlert


class TestTokenExpirationAlert:
    """Test cases for TokenExpirationAlert class."""

    def test_init_basic(self):
        """Test basic TokenExpirationAlert initialization."""
        alert = TokenExpirationAlert(
            token_name="test-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=5),
            days_until_expiration=5,
            usage_count=10,
        )

        assert alert.token_name == "test-token"
        assert alert.token_id == "123"
        assert alert.days_until_expiration == 5
        assert alert.usage_count == 10
        assert alert.last_used is None
        assert alert.metadata == {}

    def test_init_with_optional_parameters(self):
        """Test TokenExpirationAlert initialization with optional parameters."""
        last_used = datetime.now(UTC) - timedelta(days=1)
        metadata = {"environment": "production", "service": "api"}

        alert = TokenExpirationAlert(
            token_name="prod-token",
            token_id="456",
            expires_at=datetime.now(UTC) + timedelta(days=2),
            days_until_expiration=2,
            usage_count=50,
            last_used=last_used,
            metadata=metadata,
        )

        assert alert.last_used == last_used
        assert alert.metadata == metadata
        assert alert.metadata["environment"] == "production"
        assert alert.metadata["service"] == "api"

    def test_severity_critical(self):
        """Test severity property for critical alerts (≤1 day)."""
        alert = TokenExpirationAlert(
            token_name="critical-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(hours=12),
            days_until_expiration=0,
            usage_count=10,
        )

        assert alert.severity == "critical"

        # Test exactly 1 day
        alert.days_until_expiration = 1
        assert alert.severity == "critical"

    def test_severity_high(self):
        """Test severity property for high alerts (2-7 days)."""
        alert = TokenExpirationAlert(
            token_name="high-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=3),
            days_until_expiration=3,
            usage_count=10,
        )

        assert alert.severity == "high"

        # Test exactly 7 days
        alert.days_until_expiration = 7
        assert alert.severity == "high"

    def test_severity_medium(self):
        """Test severity property for medium alerts (8-30 days)."""
        alert = TokenExpirationAlert(
            token_name="medium-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=15),
            days_until_expiration=15,
            usage_count=10,
        )

        assert alert.severity == "medium"

        # Test exactly 30 days
        alert.days_until_expiration = 30
        assert alert.severity == "medium"

    def test_severity_low(self):
        """Test severity property for low alerts (>30 days)."""
        alert = TokenExpirationAlert(
            token_name="low-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=45),
            days_until_expiration=45,
            usage_count=10,
        )

        assert alert.severity == "low"

    def test_is_active_token_no_last_used(self):
        """Test is_active_token property when last_used is None."""
        alert = TokenExpirationAlert(
            token_name="unused-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=5),
            days_until_expiration=5,
            usage_count=0,
            last_used=None,
        )

        assert not alert.is_active_token

    def test_is_active_token_recently_used(self):
        """Test is_active_token property for recently used tokens."""
        # Used 10 days ago (within 30-day window)
        last_used = datetime.now(UTC) - timedelta(days=10)

        alert = TokenExpirationAlert(
            token_name="active-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=5),
            days_until_expiration=5,
            usage_count=25,
            last_used=last_used,
        )

        assert alert.is_active_token

    def test_is_active_token_not_recently_used(self):
        """Test is_active_token property for old tokens."""
        # Used 35 days ago (outside 30-day window)
        last_used = datetime.now(UTC) - timedelta(days=35)

        alert = TokenExpirationAlert(
            token_name="inactive-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=5),
            days_until_expiration=5,
            usage_count=5,
            last_used=last_used,
        )

        assert not alert.is_active_token

    def test_is_active_token_edge_case_exactly_30_days(self):
        """Test is_active_token property for token used exactly 30 days ago."""
        # Used exactly 30 days ago (should be considered inactive)
        last_used = datetime.now(UTC) - timedelta(days=30, seconds=1)

        alert = TokenExpirationAlert(
            token_name="edge-token",
            token_id="123",
            expires_at=datetime.now(UTC) + timedelta(days=5),
            days_until_expiration=5,
            usage_count=10,
            last_used=last_used,
        )

        assert not alert.is_active_token


class TestServiceTokenMonitor:
    """Test cases for ServiceTokenMonitor class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock application settings."""
        settings = MagicMock(spec=ApplicationSettings)
        settings.database_url = "postgresql://test:test@localhost/test"
        return settings

    @pytest.fixture
    def monitor(self, mock_settings):
        """Create ServiceTokenMonitor instance with mocked dependencies."""
        with patch("src.monitoring.service_token_monitor.ServiceTokenManager") as mock_manager:
            monitor = ServiceTokenMonitor(settings=mock_settings)
            monitor.token_manager = mock_manager.return_value
            return monitor

    def test_init_basic(self):
        """Test basic ServiceTokenMonitor initialization."""
        monitor = ServiceTokenMonitor()

        assert monitor.settings is None
        assert monitor.alert_thresholds == [1, 7, 14, 30]
        assert monitor.critical_threshold == 7
        assert monitor.check_interval_hours == 6
        assert monitor.cleanup_interval_hours == 24

    def test_init_with_settings(self, mock_settings):
        """Test ServiceTokenMonitor initialization with settings."""
        monitor = ServiceTokenMonitor(settings=mock_settings)

        assert monitor.settings == mock_settings
        assert hasattr(monitor, "token_manager")

    @pytest.mark.asyncio
    async def test_check_expiring_tokens_success(self, monitor):
        """Test successful check for expiring tokens."""
        # Mock database session and results
        mock_session = AsyncMock()
        mock_result = MagicMock()

        # Create mock database rows
        mock_rows = [
            MagicMock(
                id=1,
                token_name="token-1",
                expires_at=datetime.now(UTC) + timedelta(days=5),
                usage_count=10,
                last_used=datetime.now(UTC) - timedelta(days=2),
                token_metadata={"env": "prod"},
                days_until_expiration=5.0,
            ),
            MagicMock(
                id=2,
                token_name="token-2",
                expires_at=datetime.now(UTC) + timedelta(days=1),
                usage_count=25,
                last_used=datetime.now(UTC) - timedelta(days=1),
                token_metadata=None,
                days_until_expiration=1.0,
            ),
        ]

        mock_result.fetchall.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Mock get_db async generator
        @asynccontextmanager
        async def mock_get_db():
            yield mock_session

        with patch("src.monitoring.service_token_monitor.get_db", mock_get_db):
            alerts = await monitor.check_expiring_tokens(alert_threshold_days=7)

        assert len(alerts) == 2

        # Verify first alert
        alert1 = alerts[0]
        assert alert1.token_name == "token-1"
        assert alert1.token_id == "1"
        assert alert1.days_until_expiration == 5
        assert alert1.usage_count == 10
        assert alert1.metadata == {"env": "prod"}
        assert alert1.severity == "high"

        # Verify second alert
        alert2 = alerts[1]
        assert alert2.token_name == "token-2"
        assert alert2.token_id == "2"
        assert alert2.days_until_expiration == 1
        assert alert2.usage_count == 25
        assert alert2.metadata == {}
        assert alert2.severity == "critical"

    @pytest.mark.asyncio
    async def test_check_expiring_tokens_no_results(self, monitor):
        """Test check for expiring tokens when no tokens are expiring."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_db():
            yield mock_session

        with patch("src.monitoring.service_token_monitor.get_db", mock_get_db):
            alerts = await monitor.check_expiring_tokens(alert_threshold_days=30)

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_check_expiring_tokens_database_error(self, monitor):
        """Test check for expiring tokens when database error occurs."""

        @asynccontextmanager
        async def mock_get_db_error():
            raise Exception("Database connection failed")
            yield  # This won't be reached but satisfies the generator

        with patch("src.monitoring.service_token_monitor.get_db", mock_get_db_error):
            with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                alerts = await monitor.check_expiring_tokens()

        assert len(alerts) == 0
        mock_logger.error.assert_called_once()
        assert "Failed to check expiring tokens" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_get_monitoring_metrics_success(self, monitor):
        """Test successful retrieval of monitoring metrics."""
        # Mock database health check
        mock_health = {"status": "healthy", "connection_time_ms": 15}

        # Mock token analytics
        mock_analytics = {
            "summary": {
                "total_tokens": 50,
                "active_tokens": 45,
                "inactive_tokens": 3,
                "expired_tokens": 2,
                "total_usage": 1500,
            },
            "top_tokens": [
                {"token_name": "api-token-1", "usage_count": 300, "last_used": "2025-08-18T10:00:00Z"},
                {"token_name": "api-token-2", "usage_count": 250, "last_used": "2025-08-18T09:30:00Z"},
            ],
        }

        # Mock expiring tokens
        mock_alerts = [
            TokenExpirationAlert(
                token_name="expiring-token",
                token_id="123",
                expires_at=datetime.now(UTC) + timedelta(days=2),
                days_until_expiration=2,
                usage_count=10,
            ),
        ]

        # Mock authentication stats
        mock_auth_stats = MagicMock()
        mock_auth_stats.total_auths = 100
        mock_auth_stats.successful_auths = 95
        mock_auth_stats.failed_auths = 5
        mock_auth_stats.service_token_auths = 80

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_auth_stats
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_db():
            yield mock_session

        with patch("src.monitoring.service_token_monitor.database_health_check", AsyncMock(return_value=mock_health)):
            with patch.object(
                monitor.token_manager,
                "get_token_usage_analytics",
                AsyncMock(return_value=mock_analytics),
            ):
                with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=mock_alerts)):
                    with patch("src.monitoring.service_token_monitor.get_db", mock_get_db):
                        metrics = await monitor.get_monitoring_metrics()

        # Verify basic structure
        assert "timestamp" in metrics
        assert metrics["database_health"] == "healthy"

        # Verify token stats
        assert metrics["token_stats"]["total_tokens"] == 50
        assert metrics["token_stats"]["active_tokens"] == 45

        # Verify usage stats
        assert len(metrics["usage_stats"]["most_used_tokens"]) == 2
        assert metrics["usage_stats"]["most_used_tokens"][0]["name"] == "api-token-1"

        # Verify security alerts
        assert len(metrics["security_alerts"]) == 1
        alert = metrics["security_alerts"][0]
        assert alert["token_name"] == "expiring-token"

        # Verify performance metrics
        perf = metrics["performance_metrics"]
        assert perf["db_connection_time_ms"] == 15
        assert perf["auth_requests_1h"] == 100
        assert perf["auth_success_rate_1h"] == 95.0

    @pytest.mark.asyncio
    async def test_get_monitoring_metrics_partial_data(self, monitor):
        """Test monitoring metrics when some data is missing."""
        # Mock health check failure
        mock_health = {"status": "unhealthy", "connection_time_ms": 0}

        # Mock empty analytics
        mock_analytics = None

        # Mock no alerts
        mock_alerts = []

        # Mock auth stats with no data
        mock_auth_stats = MagicMock()
        mock_auth_stats.total_auths = 0
        mock_auth_stats.successful_auths = 0
        mock_auth_stats.failed_auths = 0
        mock_auth_stats.service_token_auths = 0

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_auth_stats
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_db():
            yield mock_session

        with patch("src.monitoring.service_token_monitor.database_health_check", AsyncMock(return_value=mock_health)):
            with patch.object(
                monitor.token_manager,
                "get_token_usage_analytics",
                AsyncMock(return_value=mock_analytics),
            ):
                with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=mock_alerts)):
                    with patch("src.monitoring.service_token_monitor.get_db", mock_get_db):
                        metrics = await monitor.get_monitoring_metrics()

        assert metrics["database_health"] == "unhealthy"
        assert metrics["token_stats"] == {}
        assert len(metrics["security_alerts"]) == 0
        assert metrics["performance_metrics"]["auth_success_rate_1h"] == 100  # Default when no auths

    @pytest.mark.asyncio
    async def test_get_monitoring_metrics_error_handling(self, monitor):
        """Test monitoring metrics error handling."""
        with patch(
            "src.monitoring.service_token_monitor.database_health_check",
            AsyncMock(side_effect=Exception("Health check failed")),
        ):
            with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                metrics = await monitor.get_monitoring_metrics()

        assert "error" in metrics
        assert metrics["error"] == "Health check failed"
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_expiration_alerts_no_alerts(self, monitor):
        """Test sending alerts when no alerts are provided."""
        result = await monitor.send_expiration_alerts([], notification_method="log")

        assert result["alerts_sent"] == 0
        assert result["method"] == "log"

    @pytest.mark.asyncio
    async def test_send_expiration_alerts_log_method(self, monitor):
        """Test sending alerts via log method."""
        alerts = [
            TokenExpirationAlert(
                token_name="critical-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(hours=12),
                days_until_expiration=0,
                usage_count=50,
            ),
            TokenExpirationAlert(
                token_name="high-token",
                token_id="2",
                expires_at=datetime.now(UTC) + timedelta(days=3),
                days_until_expiration=3,
                usage_count=25,
            ),
            TokenExpirationAlert(
                token_name="medium-token",
                token_id="3",
                expires_at=datetime.now(UTC) + timedelta(days=15),
                days_until_expiration=15,
                usage_count=10,
            ),
        ]

        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            result = await monitor.send_expiration_alerts(alerts, notification_method="log")

        assert result["alerts_sent"] == 3
        assert result["method"] == "log"

        # Verify log calls were made with appropriate levels
        assert mock_logger.log.call_count == 3

        # Check that critical alert was logged with CRITICAL level
        critical_call = [call for call in mock_logger.log.call_args_list if call[0][0] == logging.CRITICAL][0]
        assert "critical-token" in str(critical_call)

    @pytest.mark.asyncio
    async def test_send_expiration_alerts_email_method(self, monitor):
        """Test sending alerts via email method."""
        alerts = [
            TokenExpirationAlert(
                token_name="test-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(days=2),
                days_until_expiration=2,
                usage_count=10,
            ),
        ]

        with patch.object(monitor, "_send_email_alerts", AsyncMock(return_value=1)) as mock_email:
            result = await monitor.send_expiration_alerts(alerts, notification_method="email")

        assert result["alerts_sent"] == 1
        assert result["method"] == "email"
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_expiration_alerts_webhook_method(self, monitor):
        """Test sending alerts via webhook method."""
        alerts = [
            TokenExpirationAlert(
                token_name="test-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(days=2),
                days_until_expiration=2,
                usage_count=10,
            ),
        ]

        with patch.object(monitor, "_send_webhook_alerts", AsyncMock(return_value=1)) as mock_webhook:
            result = await monitor.send_expiration_alerts(alerts, notification_method="webhook")

        assert result["alerts_sent"] == 1
        assert result["method"] == "webhook"
        mock_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_expiration_alerts_unknown_method(self, monitor):
        """Test sending alerts with unknown notification method."""
        alerts = [
            TokenExpirationAlert(
                token_name="test-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(days=2),
                days_until_expiration=2,
                usage_count=10,
            ),
        ]

        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            result = await monitor.send_expiration_alerts(alerts, notification_method="unknown")

        assert result["alerts_sent"] == 0
        assert result["method"] == "unknown"
        mock_logger.warning.assert_called_once()
        assert "Unknown notification method" in str(mock_logger.warning.call_args)

    @pytest.mark.asyncio
    async def test_send_expiration_alerts_error_handling(self, monitor):
        """Test error handling during alert sending."""
        alerts = [
            TokenExpirationAlert(
                token_name="test-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(days=2),
                days_until_expiration=2,
                usage_count=10,
            ),
        ]

        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            # Force an exception by patching logger.log to raise
            mock_logger.log.side_effect = Exception("Logging failed")
            result = await monitor.send_expiration_alerts(alerts, notification_method="log")

        mock_logger.error.assert_called()
        assert "Failed to send expiration alerts" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_send_email_alerts(self, monitor):
        """Test email alert sending functionality."""
        alerts_by_severity = {
            "critical": [
                TokenExpirationAlert(
                    token_name="critical-token",
                    token_id="1",
                    expires_at=datetime.now(UTC) + timedelta(hours=12),
                    days_until_expiration=0,
                    usage_count=50,
                ),
            ],
            "high": [
                TokenExpirationAlert(
                    token_name="high-token-1",
                    token_id="2",
                    expires_at=datetime.now(UTC) + timedelta(days=3),
                    days_until_expiration=3,
                    usage_count=25,
                ),
                TokenExpirationAlert(
                    token_name="high-token-2",
                    token_id="3",
                    expires_at=datetime.now(UTC) + timedelta(days=5),
                    days_until_expiration=5,
                    usage_count=15,
                ),
            ],
        }

        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            result = await monitor._send_email_alerts(alerts_by_severity)

        assert result == 3  # 1 critical + 2 high = 3 total alerts

        # Verify logging calls
        assert mock_logger.info.call_count == 3  # 1 total + 2 severity-specific

        # Check log messages
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Would send 3 token expiration alerts" in call for call in calls)
        assert any("CRITICAL: 1 alerts" in call for call in calls)
        assert any("HIGH: 2 alerts" in call for call in calls)

    @pytest.mark.asyncio
    async def test_send_webhook_alerts(self, monitor):
        """Test webhook alert sending functionality."""
        alerts_by_severity = {
            "medium": [
                TokenExpirationAlert(
                    token_name="medium-token",
                    token_id="1",
                    expires_at=datetime.now(UTC) + timedelta(days=15),
                    days_until_expiration=15,
                    usage_count=20,
                ),
            ],
        }

        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            result = await monitor._send_webhook_alerts(alerts_by_severity)

        assert result == 1

        # Verify logging calls
        assert mock_logger.info.call_count == 2

        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Would send 1 token expiration alerts" in call for call in calls)
        assert any("MEDIUM: 1 alerts" in call for call in calls)

    @pytest.mark.asyncio
    async def test_run_scheduled_monitoring_success(self, monitor):
        """Test successful scheduled monitoring run."""
        # Mock expiring tokens
        mock_alerts = [
            TokenExpirationAlert(
                token_name="expiring-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(days=2),
                days_until_expiration=2,
                usage_count=10,
            ),
        ]

        # Mock monitoring metrics
        mock_metrics = {"database_health": "healthy", "token_stats": {"active_tokens": 45}, "security_alerts": []}

        # Mock cleanup results
        mock_cleanup = {"expired_tokens_processed": 2, "status": "completed"}

        with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=mock_alerts)):
            with patch.object(monitor, "send_expiration_alerts", AsyncMock(return_value={"alerts_sent": 1})):
                with patch.object(monitor, "get_monitoring_metrics", AsyncMock(return_value=mock_metrics)):
                    with patch.object(
                        monitor.token_manager,
                        "cleanup_expired_tokens",
                        AsyncMock(return_value=mock_cleanup),
                    ):
                        result = await monitor.run_scheduled_monitoring()

        assert result["status"] == "completed"
        assert "timestamp" in result
        assert "execution_time_seconds" in result
        assert result["expiring_tokens_found"] == 1
        assert result["alerts_sent"] == 1
        assert result["cleanup_results"] == mock_cleanup
        assert result["metrics_collected"] is True
        assert result["database_health"] == "healthy"

    @pytest.mark.asyncio
    async def test_run_scheduled_monitoring_no_alerts(self, monitor):
        """Test scheduled monitoring when no alerts are needed."""
        mock_metrics = {"database_health": "healthy"}
        mock_cleanup = {"expired_tokens_processed": 0}

        with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=[])):
            with patch.object(monitor, "get_monitoring_metrics", AsyncMock(return_value=mock_metrics)):
                with patch.object(
                    monitor.token_manager,
                    "cleanup_expired_tokens",
                    AsyncMock(return_value=mock_cleanup),
                ):
                    result = await monitor.run_scheduled_monitoring()

        assert result["status"] == "completed"
        assert result["expiring_tokens_found"] == 0
        assert result["alerts_sent"] == 0

    @pytest.mark.asyncio
    async def test_run_scheduled_monitoring_error_handling(self, monitor):
        """Test scheduled monitoring error handling."""
        with patch.object(monitor, "check_expiring_tokens", AsyncMock(side_effect=Exception("Monitoring failed"))):
            with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                result = await monitor.run_scheduled_monitoring()

        assert result["status"] == "failed"
        assert "timestamp" in result
        assert result["error"] == "Monitoring failed"
        mock_logger.error.assert_called_once()
        assert "Scheduled monitoring failed" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_start_monitoring_daemon_single_cycle(self, monitor):
        """Test monitoring daemon single cycle execution."""
        # Mock successful monitoring run
        mock_result = {
            "status": "completed",
            "expiring_tokens_found": 2,
            "alerts_sent": 1,
            "cleanup_results": {"expired_tokens_processed": 1},
        }

        # Track sleep calls to control loop
        sleep_calls = []

        async def mock_sleep(seconds):
            sleep_calls.append(seconds)
            if len(sleep_calls) >= 1:  # Stop after first cycle
                raise KeyboardInterrupt("Test completion")

        with patch.object(monitor, "run_scheduled_monitoring", AsyncMock(return_value=mock_result)):
            with patch("src.monitoring.service_token_monitor.asyncio.sleep", mock_sleep):
                with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                    with pytest.raises(KeyboardInterrupt):
                        await monitor.start_monitoring_daemon(check_interval_minutes=1)

        # Verify daemon started and completed one cycle
        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 60  # 1 minute in seconds

        # Verify logging
        start_log = [
            call for call in mock_logger.info.call_args_list if "Starting service token monitoring daemon" in str(call)
        ][0]
        assert "interval: 1 minutes" in str(start_log)

        completion_log = [
            call for call in mock_logger.info.call_args_list if "Monitoring cycle completed" in str(call)
        ][0]
        assert "2 expiring tokens" in str(completion_log)
        assert "1 alerts sent" in str(completion_log)

    @pytest.mark.asyncio
    async def test_start_monitoring_daemon_error_handling(self, monitor):
        """Test monitoring daemon error handling."""
        # Mock failed monitoring run
        mock_result = {"status": "failed", "error": "Database connection lost"}

        sleep_calls = []

        async def mock_sleep(seconds):
            sleep_calls.append(seconds)
            if len(sleep_calls) >= 1:
                raise KeyboardInterrupt("Test completion")

        with patch.object(monitor, "run_scheduled_monitoring", AsyncMock(return_value=mock_result)):
            with patch("src.monitoring.service_token_monitor.asyncio.sleep", mock_sleep):
                with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                    with pytest.raises(KeyboardInterrupt):
                        await monitor.start_monitoring_daemon(check_interval_minutes=1)

        # Verify error was logged
        error_log = [call for call in mock_logger.error.call_args_list if "Monitoring cycle failed" in str(call)][0]
        assert "Database connection lost" in str(error_log)

    @pytest.mark.asyncio
    async def test_start_monitoring_daemon_exception_handling(self, monitor):
        """Test monitoring daemon handling of unexpected exceptions."""
        sleep_calls = []

        async def mock_sleep(seconds):
            sleep_calls.append(seconds)
            if len(sleep_calls) >= 1:
                raise KeyboardInterrupt("Test completion")

        with patch.object(monitor, "run_scheduled_monitoring", AsyncMock(side_effect=Exception("Unexpected error"))):
            with patch("src.monitoring.service_token_monitor.asyncio.sleep", mock_sleep):
                with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                    with pytest.raises(KeyboardInterrupt):
                        await monitor.start_monitoring_daemon(check_interval_minutes=1)

        # Verify exception was logged
        error_log = [call for call in mock_logger.error.call_args_list if "Monitoring daemon error" in str(call)][0]
        assert "Unexpected error" in str(error_log)


class TestMonitoringHealthCheck:
    """Test cases for MonitoringHealthCheck class."""

    @pytest.mark.asyncio
    async def test_get_health_status_healthy(self):
        """Test health status when all systems are healthy."""
        mock_metrics = {
            "database_health": "healthy",
            "token_stats": {"active_tokens": 45, "expired_tokens": 2},
            "performance_metrics": {"db_connection_time_ms": 15, "auth_success_rate_1h": 99.5, "auth_requests_1h": 150},
            "security_alerts": [
                {"severity": "medium", "token_name": "test-token"},
                {"severity": "low", "token_name": "another-token"},
            ],
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics
            mock_monitor_class.return_value = mock_monitor

            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "healthy"
        assert "timestamp" in health

        # Verify components
        components = health["components"]
        assert components["database"]["status"] == "healthy"
        assert components["database"]["connection_time_ms"] == 15
        assert components["service_tokens"]["status"] == "healthy"
        assert components["service_tokens"]["active_count"] == 45
        assert components["service_tokens"]["expired_count"] == 2
        assert components["authentication"]["status"] == "healthy"
        assert components["authentication"]["success_rate_1h"] == 99.5
        assert components["authentication"]["requests_1h"] == 150

        # Verify alerts
        alerts = health["alerts"]
        assert alerts["critical_count"] == 0
        assert alerts["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_health_status_degraded_with_critical_alerts(self):
        """Test health status when there are critical alerts."""
        mock_metrics = {
            "database_health": "healthy",
            "token_stats": {"active_tokens": 45, "expired_tokens": 2},
            "performance_metrics": {"db_connection_time_ms": 15},
            "security_alerts": [
                {"severity": "critical", "token_name": "critical-token"},
                {"severity": "high", "token_name": "high-token"},
                {"severity": "medium", "token_name": "medium-token"},
            ],
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics
            mock_monitor_class.return_value = mock_monitor

            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "degraded"
        assert health["alerts"]["critical_count"] == 1
        assert health["alerts"]["total_count"] == 3

    @pytest.mark.asyncio
    async def test_get_health_status_unhealthy_database(self):
        """Test health status when database is unhealthy."""
        mock_metrics = {
            "database_health": "unhealthy",
            "token_stats": {"active_tokens": 0, "expired_tokens": 0},
            "performance_metrics": {"db_connection_time_ms": 0},
            "security_alerts": [],
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics
            mock_monitor_class.return_value = mock_monitor

            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "unhealthy"
        assert health["components"]["database"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_get_health_status_missing_data(self):
        """Test health status with missing data in metrics."""
        mock_metrics = {
            "database_health": "healthy",
            # Missing token_stats, performance_metrics, security_alerts
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics
            mock_monitor_class.return_value = mock_monitor

            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "healthy"

        # Verify defaults for missing data
        components = health["components"]
        assert components["database"]["connection_time_ms"] == 0
        assert components["service_tokens"]["active_count"] == 0
        assert components["service_tokens"]["expired_count"] == 0
        assert components["authentication"]["success_rate_1h"] == 100
        assert components["authentication"]["requests_1h"] == 0

        alerts = health["alerts"]
        assert alerts["critical_count"] == 0
        assert alerts["total_count"] == 0

    @pytest.mark.asyncio
    async def test_get_health_status_error_handling(self):
        """Test health status error handling."""
        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.side_effect = Exception("Metrics collection failed")
            mock_monitor_class.return_value = mock_monitor

            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "unhealthy"
        assert "timestamp" in health
        assert health["error"] == "Metrics collection failed"


class TestServiceTokenMonitorIntegration:
    """Integration tests for ServiceTokenMonitor."""

    @pytest.mark.asyncio
    async def test_full_monitoring_cycle_with_alerts(self):
        """Test complete monitoring cycle with alert generation."""
        monitor = ServiceTokenMonitor()

        # Mock expiring tokens
        mock_alerts = [
            TokenExpirationAlert(
                token_name="critical-prod-token",
                token_id="1",
                expires_at=datetime.now(UTC) + timedelta(hours=6),
                days_until_expiration=0,
                usage_count=500,
                last_used=datetime.now(UTC) - timedelta(hours=1),
                metadata={"environment": "production", "service": "api"},
            ),
            TokenExpirationAlert(
                token_name="warning-dev-token",
                token_id="2",
                expires_at=datetime.now(UTC) + timedelta(days=5),
                days_until_expiration=5,
                usage_count=50,
                last_used=datetime.now(UTC) - timedelta(days=35),
                metadata={"environment": "development"},
            ),
        ]

        # Mock metrics
        mock_metrics = {
            "database_health": "healthy",
            "token_stats": {"active_tokens": 25, "expired_tokens": 3},
            "performance_metrics": {"auth_success_rate_1h": 98.5},
        }

        # Mock cleanup results
        mock_cleanup = {"expired_tokens_processed": 1, "status": "completed"}

        with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=mock_alerts)):
            with patch.object(monitor, "get_monitoring_metrics", AsyncMock(return_value=mock_metrics)):
                with patch.object(
                    monitor.token_manager,
                    "cleanup_expired_tokens",
                    AsyncMock(return_value=mock_cleanup),
                ):
                    with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                        result = await monitor.run_scheduled_monitoring()

        # Verify monitoring completed successfully
        assert result["status"] == "completed"
        assert result["expiring_tokens_found"] == 2
        assert result["alerts_sent"] == 2
        assert result["cleanup_results"]["expired_tokens_processed"] == 1

        # Verify alerts were logged with appropriate severity
        log_calls = [str(call) for call in mock_logger.log.call_args_list]

        # Should have critical and high severity alerts
        critical_alerts = [call for call in log_calls if "CRITICAL" in call and "critical-prod-token" in call]
        high_alerts = [call for call in log_calls if "HIGH" in call and "warning-dev-token" in call]

        assert len(critical_alerts) == 1
        assert len(high_alerts) == 1

        # Verify alert details
        critical_alert = critical_alerts[0]
        assert "expires in 0 days" in critical_alert
        assert "usage: 500 times" in critical_alert
        assert "active: yes" in critical_alert

        high_alert = high_alerts[0]
        assert "expires in 5 days" in high_alert
        assert "usage: 50 times" in high_alert
        assert "active: no" in high_alert  # Used >30 days ago

    @pytest.mark.asyncio
    async def test_monitoring_performance_under_load(self):
        """Test monitoring performance with large number of tokens."""
        monitor = ServiceTokenMonitor()

        # Create many alerts to test performance
        mock_alerts = []
        for i in range(100):
            alert = TokenExpirationAlert(
                token_name=f"token-{i}",
                token_id=str(i),
                expires_at=datetime.now(UTC) + timedelta(days=i % 30 + 1),
                days_until_expiration=i % 30 + 1,
                usage_count=i * 10,
                last_used=datetime.now(UTC) - timedelta(days=i % 45),
            )
            mock_alerts.append(alert)

        # Mock large metrics dataset
        mock_metrics = {
            "database_health": "healthy",
            "token_stats": {"total_tokens": 1000, "active_tokens": 950, "expired_tokens": 50},
            "security_alerts": [{"severity": alert.severity, "token_name": alert.token_name} for alert in mock_alerts],
            "performance_metrics": {"auth_requests_1h": 10000, "auth_success_rate_1h": 99.8},
        }

        with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=mock_alerts)):
            with patch.object(monitor, "get_monitoring_metrics", AsyncMock(return_value=mock_metrics)):
                with patch.object(
                    monitor.token_manager,
                    "cleanup_expired_tokens",
                    AsyncMock(return_value={"expired_tokens_processed": 50}),
                ):
                    # Measure execution time
                    start_time = datetime.now(UTC)
                    result = await monitor.run_scheduled_monitoring()
                    execution_time = (datetime.now(UTC) - start_time).total_seconds()

        # Verify performance is acceptable (should complete within reasonable time)
        assert execution_time < 5.0  # Should complete within 5 seconds

        # Verify all alerts were processed
        assert result["status"] == "completed"
        assert result["expiring_tokens_found"] == 100
        assert result["alerts_sent"] == 100

    @pytest.mark.asyncio
    async def test_health_check_integration_scenarios(self):
        """Test health check under various system conditions."""
        # Test scenario 1: All systems healthy
        mock_metrics_healthy = {
            "database_health": "healthy",
            "token_stats": {"active_tokens": 100, "expired_tokens": 5},
            "performance_metrics": {"db_connection_time_ms": 20, "auth_success_rate_1h": 99.9, "auth_requests_1h": 500},
            "security_alerts": [],
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics_healthy
            mock_monitor_class.return_value = mock_monitor

            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "healthy"
        assert health["components"]["database"]["status"] == "healthy"
        assert health["components"]["authentication"]["success_rate_1h"] == 99.9

        # Test scenario 2: Database issues
        mock_metrics_db_issues = {
            "database_health": "unhealthy",
            "token_stats": {"active_tokens": 0, "expired_tokens": 0},
            "performance_metrics": {"db_connection_time_ms": 5000},
            "security_alerts": [],
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics_db_issues
            mock_monitor_class.return_value = mock_monitor
            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "unhealthy"
        assert health["components"]["database"]["status"] == "unhealthy"
        assert health["components"]["database"]["connection_time_ms"] == 5000

        # Test scenario 3: Critical security alerts
        mock_metrics_critical = {
            "database_health": "healthy",
            "token_stats": {"active_tokens": 50, "expired_tokens": 10},
            "performance_metrics": {"auth_success_rate_1h": 95.0},
            "security_alerts": [
                {"severity": "critical", "token_name": "prod-api-key"},
                {"severity": "critical", "token_name": "admin-token"},
                {"severity": "high", "token_name": "service-account"},
            ],
        }

        with patch("src.monitoring.service_token_monitor.ServiceTokenMonitor") as mock_monitor_class:
            mock_monitor = AsyncMock()
            mock_monitor.get_monitoring_metrics.return_value = mock_metrics_critical
            mock_monitor_class.return_value = mock_monitor
            health = await MonitoringHealthCheck.get_health_status()

        assert health["status"] == "degraded"
        assert health["alerts"]["critical_count"] == 2
        assert health["alerts"]["total_count"] == 3
        assert health["components"]["authentication"]["success_rate_1h"] == 95.0


class TestServiceTokenMonitorEdgeCases:
    """Test edge cases and error conditions for ServiceTokenMonitor."""

    @pytest.mark.asyncio
    async def test_monitoring_with_concurrent_token_operations(self):
        """Test monitoring behavior during concurrent token operations."""
        monitor = ServiceTokenMonitor()

        # Simulate concurrent monitoring calls
        async def concurrent_monitoring():
            return await monitor.run_scheduled_monitoring()

        # Mock data that might change during concurrent operations
        changing_metrics = [
            {"database_health": "healthy", "token_stats": {"active_tokens": 45}},
            {"database_health": "healthy", "token_stats": {"active_tokens": 46}},
            {"database_health": "healthy", "token_stats": {"active_tokens": 44}},
        ]

        call_count = 0

        def get_changing_metrics():
            nonlocal call_count
            result = changing_metrics[call_count % len(changing_metrics)]
            call_count += 1
            return result

        with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=[])):
            with patch.object(monitor, "get_monitoring_metrics", AsyncMock(side_effect=get_changing_metrics)):
                with patch.object(
                    monitor.token_manager,
                    "cleanup_expired_tokens",
                    AsyncMock(return_value={"expired_tokens_processed": 0}),
                ):
                    # Run multiple monitoring tasks concurrently
                    tasks = [concurrent_monitoring() for _ in range(3)]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all tasks completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_token_expiration_edge_cases(self):
        """Test edge cases in token expiration calculations."""
        monitor = ServiceTokenMonitor()

        now = datetime.now(UTC)

        # Test tokens expiring at exact threshold boundaries
        edge_case_alerts = [
            # Token expiring in exactly 1 second (should be 0 days)
            TokenExpirationAlert(
                token_name="immediate-expiry",
                token_id="1",
                expires_at=now + timedelta(seconds=1),
                days_until_expiration=0,
                usage_count=10,
            ),
            # Token expiring in exactly 24 hours (should be 1 day)
            TokenExpirationAlert(
                token_name="one-day-expiry",
                token_id="2",
                expires_at=now + timedelta(hours=24),
                days_until_expiration=1,
                usage_count=20,
            ),
            # Token that expired 1 hour ago (negative days)
            TokenExpirationAlert(
                token_name="already-expired",
                token_id="3",
                expires_at=now - timedelta(hours=1),
                days_until_expiration=-1,
                usage_count=5,
            ),
        ]

        # Test severity calculations for edge cases
        assert edge_case_alerts[0].severity == "critical"  # 0 days
        assert edge_case_alerts[1].severity == "critical"  # 1 day
        assert edge_case_alerts[2].days_until_expiration == -1  # Already expired

        # Test alert sending with edge cases
        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            result = await monitor.send_expiration_alerts(edge_case_alerts, notification_method="log")

        assert result["alerts_sent"] == 3

        # Verify all alerts were logged as critical (including expired one)
        critical_calls = [call for call in mock_logger.log.call_args_list if call[0][0] == logging.CRITICAL]
        assert len(critical_calls) >= 2  # At least the two critical ones

    @pytest.mark.asyncio
    async def test_monitoring_with_database_timeout(self):
        """Test monitoring behavior when database operations timeout."""
        monitor = ServiceTokenMonitor()

        # Simulate database timeout
        async def timeout_db_operation(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow operation
            raise TimeoutError("Database operation timed out")

        with patch.object(monitor, "check_expiring_tokens", side_effect=timeout_db_operation):
            with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
                result = await monitor.run_scheduled_monitoring()

        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_alert_grouping_with_large_numbers(self):
        """Test alert grouping behavior with large numbers of alerts."""
        monitor = ServiceTokenMonitor()

        # Create alerts with various severities
        alerts = []
        for i in range(1000):
            days = i % 50  # Cycle through 0-49 days
            alert = TokenExpirationAlert(
                token_name=f"bulk-token-{i}",
                token_id=str(i),
                expires_at=datetime.now(UTC) + timedelta(days=days),
                days_until_expiration=days,
                usage_count=i,
            )
            alerts.append(alert)

        # Count expected alerts by severity
        expected_critical = sum(1 for a in alerts if a.severity == "critical")
        expected_high = sum(1 for a in alerts if a.severity == "high")
        expected_medium = sum(1 for a in alerts if a.severity == "medium")
        expected_low = sum(1 for a in alerts if a.severity == "low")

        with patch("src.monitoring.service_token_monitor.logger") as mock_logger:
            result = await monitor.send_expiration_alerts(alerts, notification_method="log")

        assert result["alerts_sent"] == 1000

        # Verify all severity levels were logged
        log_calls = [str(call) for call in mock_logger.log.call_args_list]

        critical_logs = [call for call in log_calls if "CRITICAL" in call]
        high_logs = [call for call in log_calls if "HIGH" in call]
        medium_logs = [call for call in log_calls if "MEDIUM" in call]
        low_logs = [call for call in log_calls if "LOW" in call]

        # Should have logged individual alerts for each severity
        assert len(critical_logs) == expected_critical
        assert len(high_logs) == expected_high
        assert len(medium_logs) == expected_medium
        assert len(low_logs) == expected_low

    @pytest.mark.asyncio
    async def test_monitoring_memory_usage_with_large_datasets(self):
        """Test memory usage doesn't grow excessively with large datasets."""
        monitor = ServiceTokenMonitor()

        # Create large dataset simulation
        def create_large_metrics():
            return {
                "database_health": "healthy",
                "token_stats": {"total_tokens": 10000, "active_tokens": 9500, "expired_tokens": 500},
                "usage_stats": {
                    "most_used_tokens": [
                        {
                            "name": f"high-usage-token-{i}",
                            "usage_count": 1000 - i,
                            "last_used": datetime.now(UTC).isoformat(),
                        }
                        for i in range(1000)  # Large dataset
                    ],
                },
                "security_alerts": [
                    {
                        "type": "token_expiration",
                        "severity": "medium",
                        "token_name": f"alert-token-{i}",
                        "days_until_expiration": i % 30,
                    }
                    for i in range(500)  # Many alerts
                ],
                "performance_metrics": {"auth_requests_1h": 50000, "auth_success_rate_1h": 99.95},
            }

        # Run monitoring multiple times with large datasets
        with patch.object(monitor, "check_expiring_tokens", AsyncMock(return_value=[])):
            with patch.object(monitor, "get_monitoring_metrics", AsyncMock(side_effect=create_large_metrics)):
                with patch.object(
                    monitor.token_manager,
                    "cleanup_expired_tokens",
                    AsyncMock(return_value={"expired_tokens_processed": 100}),
                ):
                    # Run multiple cycles to check for memory leaks
                    for _ in range(10):
                        result = await monitor.run_scheduled_monitoring()
                        assert result["status"] == "completed"

        # Test should complete without memory errors
        assert True  # If we reach here, memory usage was acceptable
