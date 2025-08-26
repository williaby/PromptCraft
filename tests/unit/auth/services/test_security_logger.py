"""Comprehensive unit tests for AUTH-4 SecurityLogger service.

Tests stateless security event logging, database integration, performance requirements (<10ms),
and all CRUD operations for the SecurityLogger component.
"""

import asyncio
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.auth.models import SecurityEventCreate, SecurityEventResponse, SecurityEventSeverity, SecurityEventType
from src.auth.security_logger import SecurityLogger


class TestSecurityLoggerInitialization:
    """Test SecurityLogger initialization and configuration."""

    def test_security_logger_initialization(self):
        """Test SecurityLogger initialization (stateless design)."""
        logger = SecurityLogger()

        assert logger._db_manager is not None
        assert logger._is_initialized is False

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
            event_type=SecurityEventType.SYSTEM_ERROR, severity=SecurityEventSeverity.CRITICAL, user_id="auto_init_test",
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
        mock_row.timestamp = datetime.now(UTC)
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
                event_type=SecurityEventType.SYSTEM_ERROR, severity=SecurityEventSeverity.CRITICAL,
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
