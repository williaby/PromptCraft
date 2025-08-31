"""Comprehensive unit tests for AUTH-4 SecurityLogger service.

Tests stateless security event logging, database integration, performance requirements (<10ms),
and all CRUD operations for the SecurityLogger component.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.auth.models import SecurityEventCreate, SecurityEventResponse, SecurityEventSeverity, SecurityEventType
from src.auth.security_logger import SecurityLogger
from src.auth.services.security_logger import LoggingConfig
from src.auth.services.security_logger import SecurityLogger as ServicesSecurityLogger
from src.utils.time_utils import utc_now


class TestSecurityLoggerInitialization:
    """Test SecurityLogger initialization and configuration."""

    def test_security_logger_initialization(self):
        """Test SecurityLogger initialization (stateless design)."""
        logger = SecurityLogger()

        assert logger._db_manager is not None
        assert logger._is_initialized is False

    def test_services_security_logger_parameter_validation(self):
        """Test parameter validation in ServicesSecurityLogger - covers lines 101-106."""
        # Test negative batch_size
        with pytest.raises(ValueError, match="batch_size must be positive"):
            ServicesSecurityLogger(batch_size=-1)

        # Test zero batch_size
        with pytest.raises(ValueError, match="batch_size must be positive"):
            ServicesSecurityLogger(batch_size=0)

        # Test negative batch_timeout_seconds
        with pytest.raises(ValueError, match="batch_timeout_seconds must be positive"):
            ServicesSecurityLogger(batch_timeout_seconds=-1.0)

        # Test zero batch_timeout_seconds
        with pytest.raises(ValueError, match="batch_timeout_seconds must be positive"):
            ServicesSecurityLogger(batch_timeout_seconds=0.0)

        # Test negative max_queue_size
        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            ServicesSecurityLogger(max_queue_size=-100)

        # Test zero max_queue_size
        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            ServicesSecurityLogger(max_queue_size=0)

    def test_services_security_logger_config_initialization(self):
        """Test ServicesSecurityLogger initialization with LoggingConfig - covers lines 109-113."""
        config = LoggingConfig(
            batch_size=25,
            batch_timeout_seconds=3.0,
            queue_max_size=500,
        )

        logger = ServicesSecurityLogger(config=config)

        # Verify config is used
        assert logger.config == config
        assert logger.batch_size == 25
        assert logger.batch_timeout_seconds == 3.0
        assert logger.max_queue_size == 500

    def test_services_security_logger_parameter_initialization(self):
        """Test ServicesSecurityLogger initialization with parameters - covers lines 114-123."""
        logger = ServicesSecurityLogger(
            batch_size=15,
            batch_timeout_seconds=2.5,
            max_queue_size=750,
        )

        # Verify parameters are used
        assert logger.batch_size == 15
        assert logger.batch_timeout_seconds == 2.5
        assert logger.max_queue_size == 750

        # Verify config is created from parameters
        assert logger.config.batch_size == 15
        assert logger.config.batch_timeout_seconds == 2.5
        assert logger.config.queue_max_size == 750

    @pytest.mark.asyncio
    async def test_security_logger_async_initialization(self):
        """Test SecurityLogger async initialization."""
        logger = SecurityLogger()

        # Mock database manager to avoid actual DB connection
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize = AsyncMock()

        await logger.initialize()

        assert logger._is_initialized is True
        logger._db_manager.initialize.assert_called_once()


class TestSecurityLoggerEventLogging:
    """Test core event logging functionality."""

    @pytest.fixture
    def logger_with_mock_db(self):
        """Fixture providing SecurityLogger with mocked database manager."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize = AsyncMock()

        # Mock session context manager
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        # Create proper async context manager mock
        async_context = AsyncMock()
        async_context.__aenter__ = AsyncMock(return_value=mock_session)
        async_context.__aexit__ = AsyncMock(return_value=None)
        logger._db_manager.get_session = MagicMock(return_value=async_context)

        return logger

    @pytest.mark.asyncio
    async def test_log_security_event_basic(self, logger_with_mock_db):
        """Test basic security event logging (stateless)."""
        logger = logger_with_mock_db
        await logger.initialize()

        result = await logger.log_security_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            user_id="test_user",
            ip_address="192.168.1.100",
            details={"login_method": "password"},
        )

        # Verify response
        assert isinstance(result, SecurityEventResponse)
        assert result.event_type == "login_success"
        assert result.severity == "info"
        assert result.user_id == "test_user"
        assert result.ip_address == "192.168.1.100"
        assert result.details == {"login_method": "password"}

        # Verify database interactions
        logger._db_manager.get_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_security_event_with_event_object(self, logger_with_mock_db):
        """Test logging with SecurityEventCreate object."""
        logger = logger_with_mock_db
        await logger.initialize()

        event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.WARNING,
            user_id="failed_user",
            ip_address="192.168.1.200",
            details={"reason": "invalid_password"},
            risk_score=25,
        )

        result = await logger.log_security_event(event=event)

        # Verify response matches event
        assert result.event_type == "login_failure"
        assert result.severity == "warning"
        assert result.user_id == "failed_user"
        assert result.risk_score == 25

    @pytest.mark.asyncio
    async def test_log_security_event_performance(self, logger_with_mock_db):
        """Test that security event logging meets <10ms performance requirement."""
        logger = logger_with_mock_db
        await logger.initialize()

        # Time the operation
        start_time = time.perf_counter()

        await logger.log_security_event(
            event_type=SecurityEventType.SERVICE_TOKEN_AUTH,
            severity=SecurityEventSeverity.INFO,
            user_id="performance_test",
            ip_address="192.168.1.50",
        )

        elapsed_time = (time.perf_counter() - start_time) * 1000  # Convert to ms

        # Should be well under 10ms with mocked database
        assert elapsed_time < 10, f"Security event logging took {elapsed_time:.2f}ms, exceeds 10ms requirement"

    @pytest.mark.asyncio
    async def test_log_security_event_auto_initialization(self, logger_with_mock_db):
        """Test that SecurityLogger auto-initializes if not initialized."""
        logger = logger_with_mock_db

        # Don't call initialize() explicitly
        assert logger._is_initialized is False

        await logger.log_security_event(
            event_type=SecurityEventType.SYSTEM_ERROR,
            severity=SecurityEventSeverity.CRITICAL,
            user_id="auto_init_test",
        )

        # Should have auto-initialized
        assert logger._is_initialized is True
        logger._db_manager.initialize.assert_called_once()


class TestSecurityLoggerQueries:
    """Test SecurityLogger query functionality."""

    @pytest.fixture
    def logger_with_mock_queries(self):
        """Fixture providing SecurityLogger with mocked query results."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize = AsyncMock()

        # Mock session for queries
        mock_session = AsyncMock()

        # Create proper async context manager mock
        async_context = AsyncMock()
        async_context.__aenter__ = AsyncMock(return_value=mock_session)
        async_context.__aexit__ = AsyncMock(return_value=None)
        logger._db_manager.get_session = MagicMock(return_value=async_context)

        return logger, mock_session

    @pytest.mark.asyncio
    async def test_get_recent_events(self, logger_with_mock_queries):
        """Test retrieving recent security events."""
        logger, mock_session = logger_with_mock_queries
        await logger.initialize()

        # Mock query result
        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.event_type = "login_success"
        mock_row.severity = "info"
        mock_row.user_id = "test_user"
        mock_row.ip_address = "192.168.1.100"
        mock_row.timestamp = utc_now()
        mock_row.risk_score = 0
        mock_row.details = {"test": "data"}

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        # Test query
        events = await logger.get_recent_events(limit=10)

        # Verify result
        assert len(events) == 1
        assert isinstance(events[0], SecurityEventResponse)
        assert events[0].event_type == "login_success"
        assert events[0].user_id == "test_user"

        # Verify SQL query was called
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_events_by_user(self, logger_with_mock_queries):
        """Test retrieving events for a specific user."""
        logger, mock_session = logger_with_mock_queries
        await logger.initialize()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        # Test user query
        events = await logger.get_events_by_user("test_user")

        # Verify query was made
        mock_session.execute.assert_called_once()
        assert events == []

    @pytest.mark.asyncio
    async def test_get_recent_events_with_filters(self, logger_with_mock_queries):
        """Test retrieving recent events with severity and type filters."""
        logger, mock_session = logger_with_mock_queries
        await logger.initialize()

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        # Test with filters
        await logger.get_recent_events(
            limit=50,
            severity=SecurityEventSeverity.CRITICAL,
            event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
            hours_back=48,
        )

        # Verify query was called with filters
        mock_session.execute.assert_called_once()

        # Check that the query text includes filter conditions
        call_args = mock_session.execute.call_args
        query_text = str(call_args[0][0])
        assert "severity = :severity" in query_text
        assert "event_type = :event_type" in query_text


class TestSecurityLoggerMaintenance:
    """Test SecurityLogger maintenance operations."""

    @pytest.fixture
    def logger_with_mock_maintenance(self):
        """Fixture providing SecurityLogger with mocked maintenance operations."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize = AsyncMock()

        mock_session = AsyncMock()

        # Create proper async context manager mock
        async_context = AsyncMock()
        async_context.__aenter__ = AsyncMock(return_value=mock_session)
        async_context.__aexit__ = AsyncMock(return_value=None)
        logger._db_manager.get_session = MagicMock(return_value=async_context)

        return logger, mock_session

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, logger_with_mock_maintenance):
        """Test cleaning up old security events."""
        logger, mock_session = logger_with_mock_maintenance
        await logger.initialize()

        # Mock deletion result
        mock_row1 = MagicMock()
        mock_row2 = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result

        # Test cleanup
        deleted_count = await logger.cleanup_old_events(days_to_keep=30)

        # Verify result
        assert deleted_count == 2
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_logger(self):
        """Test closing the SecurityLogger."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.close = AsyncMock()
        logger._is_initialized = True

        await logger.close()

        # Verify cleanup
        logger._db_manager.close.assert_called_once()
        assert logger._is_initialized is False


class TestSecurityLoggerAsyncContextManager:
    """Test SecurityLogger as async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test SecurityLogger as async context manager."""
        mock_db_manager = AsyncMock()
        mock_db_manager.initialize = AsyncMock()
        mock_db_manager.close = AsyncMock()

        with patch("src.auth.security_logger.get_database_manager", return_value=mock_db_manager):
            async with SecurityLogger() as logger:
                assert isinstance(logger, SecurityLogger)
                assert logger._is_initialized is True
                mock_db_manager.initialize.assert_called_once()

            # After context exit, should be closed
            mock_db_manager.close.assert_called_once()


class TestSecurityLoggerErrorHandling:
    """Test SecurityLogger error handling."""

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database connection errors."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize.side_effect = Exception("Database connection failed")

        # Should raise exception during initialization
        with pytest.raises(Exception, match="Database connection failed"):
            await logger.initialize()

    @pytest.mark.asyncio
    async def test_logging_error_recovery(self):
        """Test error recovery during event logging."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize = AsyncMock()

        # Mock session that fails on add
        mock_session = AsyncMock()
        mock_session.add = MagicMock(side_effect=Exception("Insert failed"))

        # Create proper async context manager mock
        async_context = AsyncMock()
        async_context.__aenter__ = AsyncMock(return_value=mock_session)
        async_context.__aexit__ = AsyncMock(return_value=None)
        logger._db_manager.get_session = MagicMock(return_value=async_context)

        await logger.initialize()

        # Should raise exception during logging
        with pytest.raises(Exception, match="Insert failed"):
            await logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                severity=SecurityEventSeverity.CRITICAL,
            )


class TestSecurityLoggerIntegration:
    """Integration tests with real database operations (if available)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_database_integration(self):
        """Test SecurityLogger with real database (requires test DB setup)."""
        # This test would run against a real test database
        # Skip if no test database is available
        pytest.skip("Integration test requires test database setup")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_logging_performance(self):
        """Test concurrent security event logging performance."""
        logger = SecurityLogger()
        logger._db_manager = AsyncMock()
        logger._db_manager.initialize = AsyncMock()

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        # Create proper async context manager mock
        async_context = AsyncMock()
        async_context.__aenter__ = AsyncMock(return_value=mock_session)
        async_context.__aexit__ = AsyncMock(return_value=None)
        logger._db_manager.get_session = MagicMock(return_value=async_context)

        await logger.initialize()

        # Test concurrent logging
        start_time = time.perf_counter()

        tasks = [
            logger.log_security_event(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                severity=SecurityEventSeverity.INFO,
                user_id=f"user_{i}",
                ip_address=f"192.168.1.{i % 255}",
            )
            for i in range(50)
        ]

        await asyncio.gather(*tasks)

        elapsed_time = (time.perf_counter() - start_time) * 1000

        # Should handle 50 concurrent events efficiently
        assert elapsed_time < 500, f"50 concurrent events took {elapsed_time:.2f}ms"

        # Verify all events were processed
        assert mock_session.add.call_count == 50
        assert mock_session.commit.call_count == 50


class TestServicesSecurityLoggerFunctionality:
    """Test ServicesSecurityLogger core functionality."""

    def test_rate_limiting_check(self):
        """Test rate limiting functionality - covers lines 231-246."""
        # Use very low rate limit for testing
        config = LoggingConfig(rate_limit_max_events=3)
        logger = ServicesSecurityLogger(config=config, batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Initially should allow events (first 3 should succeed)
        assert logger._check_rate_limit() is True
        assert logger._check_rate_limit() is True
        assert logger._check_rate_limit() is True

        # Should now be rate limited (4th call fails)
        assert logger._check_rate_limit() is False

        # Subsequent calls should also fail
        assert logger._check_rate_limit() is False

    def test_event_sanitization_sensitive_data(self):
        """Test event detail sanitization - covers lines 248-285."""
        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Test sensitive data redaction
        sensitive_details = {
            "password": "secret123",
            "user_token": "abc123def456789",  # Long value > 8 chars
            "auth_key": "key456789012345",   # Long value > 8 chars
            "secret_value": "confidential",
            "normal_field": "normal_value",
            "count": 42,
            "is_valid": True,
            "complex_object": {"nested": "data"},
        }

        sanitized = logger._sanitize_event_details(sensitive_details)

        # Check sensitive fields are redacted
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["user_token"] == "[REDACTED]"
        assert sanitized["auth_key"] == "[REDACTED]"
        assert sanitized["secret_value"] == "[REDACTED]"

        # Check normal fields are preserved
        assert sanitized["normal_field"] == "normal_value"
        assert sanitized["count"] == 42
        assert sanitized["is_valid"] is True
        assert sanitized["complex_object"] == str({"nested": "data"})[:500]

    def test_event_sanitization_short_sensitive_data(self):
        """Test sanitization of short sensitive values - covers redaction branch."""
        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Test short sensitive data (≤8 characters)
        details = {"password": "123", "token": "abc"}
        sanitized = logger._sanitize_event_details(details)

        assert sanitized["password"] == "[REDACTED_SHORT]"
        assert sanitized["token"] == "[REDACTED_SHORT]"

    def test_event_sanitization_dangerous_strings(self):
        """Test sanitization removes dangerous characters - covers string cleaning."""
        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Test dangerous character removal
        details = {
            "message": "Alert: <script>alert('xss')</script>",
            "description": 'Quote "test" and \'single\' quotes',
            "command": "echo `whoami`",
        }

        sanitized = logger._sanitize_event_details(details)

        # Check dangerous characters are removed
        assert "<" not in sanitized["message"]
        assert ">" not in sanitized["message"]
        assert "script" in sanitized["message"]  # Content preserved, tags removed
        assert '"' not in sanitized["description"]
        assert "'" not in sanitized["description"]
        assert "`" not in sanitized["command"]

    def test_metrics_update_exponential_moving_average(self):
        """Test metrics update with exponential moving average - covers lines 287-299."""
        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Initial metrics
        assert logger.metrics.total_events_logged == 0
        assert logger.metrics.average_logging_time_ms == 0.0

        # First update (should set initial value)
        logger._update_metrics(5.0)
        assert logger.metrics.total_events_logged == 1
        assert logger.metrics.average_logging_time_ms == 5.0

        # Second update (should use exponential moving average)
        logger._update_metrics(15.0)
        assert logger.metrics.total_events_logged == 2
        # EMA calculation: 0.1 * 15.0 + 0.9 * 5.0 = 1.5 + 4.5 = 6.0
        expected_ema = 0.1 * 15.0 + 0.9 * 5.0
        assert abs(logger.metrics.average_logging_time_ms - expected_ema) < 0.01

    @pytest.mark.asyncio
    async def test_log_event_rate_limiting(self):
        """Test log_event with rate limiting - covers lines 193-199."""
        config = LoggingConfig(rate_limit_max_events=2)  # Very low limit for testing
        logger = ServicesSecurityLogger(config=config)

        from src.auth.models import SecurityEventSeverity, SecurityEventType

        # First two events should succeed
        result1 = await logger.log_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
        )
        assert result1 is True

        result2 = await logger.log_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
        )
        assert result2 is True

        # Third event should be rate limited
        result3 = await logger.log_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
        )
        assert result3 is False

        # Check metrics were updated
        assert logger.metrics.rate_limit_hits >= 1
        assert logger.metrics.total_events_dropped >= 1

    @pytest.mark.asyncio
    async def test_log_event_queue_full(self):
        """Test log_event when queue is full - covers lines 227-229."""
        # Create logger with very small queue
        logger = ServicesSecurityLogger(batch_size=100, max_queue_size=1)

        from src.auth.models import SecurityEventSeverity, SecurityEventType

        # Fill the queue (first event should succeed)
        result1 = await logger.log_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
        )
        assert result1 is True

        # Second event should fail due to full queue
        result2 = await logger.log_event(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.WARNING,
        )
        assert result2 is False
        assert logger.metrics.total_events_dropped >= 1

    @pytest.mark.asyncio
    async def test_services_security_logger_initialize(self):
        """Test ServicesSecurityLogger.initialize() method - covers lines 141-154."""
        from unittest.mock import AsyncMock, patch

        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Mock the database manager initialization
        mock_db_manager = AsyncMock()
        mock_db_manager.initialize = AsyncMock()

        with patch("src.auth.services.security_logger.get_database_manager_async", return_value=mock_db_manager):
            await logger.initialize()

        # Verify database manager was initialized
        mock_db_manager.initialize.assert_called_once()

        # Verify batch processor was started
        assert logger._batch_processor_task is not None

        # Clean up
        await logger.shutdown()

    @pytest.mark.asyncio
    async def test_services_security_logger_get_metrics(self):
        """Test get_metrics method - covers lines 368-399."""
        logger = ServicesSecurityLogger(batch_size=10, batch_timeout_seconds=2.5, max_queue_size=200)

        # Update some metrics
        logger.metrics.total_events_logged = 42
        logger.metrics.total_events_dropped = 3
        logger.metrics.average_logging_time_ms = 4.25
        logger.metrics.rate_limit_hits = 1

        metrics = await logger.get_metrics()

        # Verify metrics structure and values
        assert "performance" in metrics
        assert "configuration" in metrics
        assert "health" in metrics

        # Check performance metrics
        assert metrics["performance"]["total_events_logged"] == 42
        assert metrics["performance"]["total_events_dropped"] == 3
        assert metrics["performance"]["average_logging_time_ms"] == 4.25
        assert metrics["performance"]["rate_limit_hits"] == 1

        # Check configuration metrics
        assert metrics["configuration"]["batch_size"] == 10
        assert metrics["configuration"]["batch_timeout_seconds"] == 2.5
        assert metrics["configuration"]["queue_max_size"] == 200

        # Check health metrics
        assert "is_processing" in metrics["health"]
        assert "queue_utilization_percent" in metrics["health"]
        assert "avg_processing_performance" in metrics["health"]

    @pytest.mark.asyncio
    async def test_services_security_logger_flush(self):
        """Test flush method - covers lines 401-413."""
        from unittest.mock import AsyncMock, patch

        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Mock the process_batch method
        with patch.object(logger, "_process_batch", new_callable=AsyncMock) as mock_process:
            # Add some events to the queue
            from src.auth.models import SecurityEventSeverity, SecurityEventType
            await logger.log_event(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                severity=SecurityEventSeverity.INFO,
            )

            # Flush should process remaining events
            await logger.flush()

            # Verify batch was processed
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_services_security_logger_cleanup_old_events(self):
        """Test cleanup_old_events method - covers lines 415-450."""
        from unittest.mock import AsyncMock, MagicMock, patch

        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Mock database manager and session
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()

        # Mock execute results for each severity
        mock_result_info = MagicMock()
        mock_result_info.rowcount = 5
        mock_result_warning = MagicMock()
        mock_result_warning.rowcount = 3
        mock_result_critical = MagicMock()
        mock_result_critical.rowcount = 1

        # Set up session execute to return different results for different calls
        mock_session.execute.side_effect = [mock_result_info, mock_result_warning, mock_result_critical]
        mock_session.commit = AsyncMock()

        # Create proper async context manager
        async_context = AsyncMock()
        async_context.__aenter__ = AsyncMock(return_value=mock_session)
        async_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_session = MagicMock(return_value=async_context)

        with patch("src.auth.services.security_logger.get_database_manager_async", return_value=mock_db_manager):
            cleanup_stats = await logger.cleanup_old_events()

        # Verify cleanup statistics
        assert cleanup_stats["info"] == 5
        assert cleanup_stats["warning"] == 3
        assert cleanup_stats["critical"] == 1

        # Verify database interactions
        assert mock_session.execute.call_count == 3  # One for each severity
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_services_security_logger_shutdown(self):
        """Test shutdown method - covers lines 452-464."""
        from unittest.mock import patch

        logger = ServicesSecurityLogger(batch_size=5, batch_timeout_seconds=1.0, max_queue_size=100)

        # Start the logger to have a batch processor task
        await logger.initialize()

        # Mock flush to avoid actual event processing
        with patch.object(logger, "flush", new_callable=AsyncMock) as mock_flush:
            await logger.shutdown()

            # Verify shutdown process
            assert logger._shutdown_event.is_set()
            mock_flush.assert_called_once()
