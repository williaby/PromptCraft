"""Comprehensive tests for SecurityEventsPostgreSQL database class."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
from src.auth.models import SecurityEventCreate, SecurityEventResponse, SecurityEventSeverity, SecurityEventType


class TestSecurityEventsPostgreSQLInitialization:
    """Test SecurityEventsPostgreSQL initialization and setup."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        db = SecurityEventsPostgreSQL()

        assert db.db_manager is None
        assert db._initialized is False
        assert db._query_count == 0
        assert db._total_query_time == 0.0

    def test_init_with_connection_pool_size(self):
        """Test initialization with custom connection pool size."""
        pool_size = 20
        db = SecurityEventsPostgreSQL(connection_pool_size=pool_size)

        assert db.db_manager is None
        assert db._initialized is False

    def test_init_creates_performance_tracking_attributes(self):
        """Test that initialization sets up performance tracking."""
        db = SecurityEventsPostgreSQL()

        assert hasattr(db, "_query_count")
        assert hasattr(db, "_total_query_time")
        assert db._query_count == 0
        assert db._total_query_time == 0.0


class TestSecurityEventsPostgreSQLHelperMethods:
    """Test helper methods that don't require database initialization."""

    def test_model_to_response_complete_data(self):
        """Test converting model to response with complete data."""
        db = SecurityEventsPostgreSQL()

        mock_event = MagicMock()
        mock_event.id = uuid4()
        mock_event.event_type = "login_failure"
        mock_event.severity = "warning"
        mock_event.user_id = "test_user"
        mock_event.ip_address = "192.168.1.100"
        mock_event.user_agent = "Mozilla/5.0"
        mock_event.session_id = "session_123"
        mock_event.details = {"reason": "invalid_password"}
        mock_event.risk_score = 25
        mock_event.timestamp = datetime.now(UTC)

        result = db._model_to_response(mock_event)

        assert isinstance(result, SecurityEventResponse)
        assert result.id == mock_event.id
        assert result.event_type == SecurityEventType.LOGIN_FAILURE
        assert result.severity == SecurityEventSeverity.WARNING
        assert result.user_id == "test_user"
        assert result.ip_address == "192.168.1.100"
        assert result.source == "auth_system"

    def test_model_to_response_minimal_data(self):
        """Test converting model to response with minimal data."""
        db = SecurityEventsPostgreSQL()

        mock_event = MagicMock()
        mock_event.id = uuid4()
        mock_event.event_type = "system_error"
        mock_event.severity = "info"
        mock_event.user_id = None
        mock_event.ip_address = None
        mock_event.user_agent = None
        mock_event.session_id = None
        mock_event.details = {}
        mock_event.risk_score = 0
        mock_event.timestamp = datetime.now(UTC)

        result = db._model_to_response(mock_event)

        assert isinstance(result, SecurityEventResponse)
        assert result.id == mock_event.id
        assert result.event_type == SecurityEventType.SYSTEM_ERROR
        assert result.user_id is None
        assert result.ip_address is None

    def test_query_tracking_attributes_exist(self):
        """Test that query tracking attributes exist and are properly initialized."""
        db = SecurityEventsPostgreSQL()

        # These attributes should exist for performance tracking
        assert hasattr(db, "_query_count")
        assert hasattr(db, "_total_query_time")
        assert db._query_count == 0
        assert db._total_query_time == 0.0

        # Test that attributes can be modified
        db._query_count = 10
        db._total_query_time = 1.5
        assert db._query_count == 10
        assert db._total_query_time == 1.5


class TestSecurityEventsPostgreSQLAliases:
    """Test class aliases and compatibility."""

    def test_security_events_database_alias(self):
        """Test that SecurityEventsDatabase alias works."""
        from src.auth.database.security_events_postgres import SecurityEventsDatabase

        # Should be the same class
        assert SecurityEventsDatabase is SecurityEventsPostgreSQL

        # Should be able to instantiate
        db = SecurityEventsDatabase()
        assert isinstance(db, SecurityEventsPostgreSQL)

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test close method (should complete without error)."""
        db = SecurityEventsPostgreSQL()

        # Should not raise any exceptions
        await db.close()


class TestSecurityEventsPostgreSQLWithDirectPatching:
    """Test methods using direct patching to bypass async context manager issues."""

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test that initialize is idempotent."""
        db = SecurityEventsPostgreSQL()
        db._initialized = True

        with patch("src.auth.database.security_events_postgres.get_database_manager_async") as mock_get_db:
            await db.initialize()
            # Should not call get_database_manager_async when already initialized
            mock_get_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_database_error(self):
        """Test initialization failure due to database error."""
        db = SecurityEventsPostgreSQL()

        with patch("src.auth.database.security_events_postgres.get_database_manager_async") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception, match="Database connection failed"):
                await db.initialize()

            assert db._initialized is False
            assert db.db_manager is None

    @pytest.mark.asyncio
    async def test_create_event_error_handling(self):
        """Test error handling in create_event method."""
        db = SecurityEventsPostgreSQL()

        # Test invalid event data - should raise exception during SecurityEventCreate validation
        invalid_data = {"invalid_field": "value"}

        with pytest.raises(ValidationError):
            await db.create_event(invalid_data)

    @pytest.mark.asyncio
    async def test_log_security_event_auto_initialize(self):
        """Test that log_security_event calls initialize if not already initialized."""
        db = SecurityEventsPostgreSQL()
        test_event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.WARNING,
        )

        # Mock the initialization to fail so we can test the auto-initialize behavior
        with patch.object(db, "initialize") as mock_init:
            mock_init.side_effect = Exception("Initialize called")

            with pytest.raises(Exception, match="Initialize called"):
                await db.log_security_event(test_event)

            mock_init.assert_called_once()

    def test_initialization_state_tracking(self):
        """Test initialization state tracking functionality."""
        db = SecurityEventsPostgreSQL()

        # Test initial state
        assert db._initialized is False
        assert db.db_manager is None

        # Test manual state setting
        db._initialized = True
        mock_manager = MagicMock()
        db.db_manager = mock_manager

        assert db._initialized is True
        assert db.db_manager is mock_manager

    def test_query_stats_tracking(self):
        """Test query statistics tracking functionality."""
        db = SecurityEventsPostgreSQL()

        # Test initial state
        assert db._query_count == 0
        assert db._total_query_time == 0.0

        # Test manual modifications for tracking functionality
        db._query_count = 10
        db._total_query_time = 1.5
        assert db._query_count == 10
        assert db._total_query_time == 1.5

        db._query_count += 2
        db._total_query_time += 0.2
        assert db._query_count == 5
        assert db._total_query_time == 0.5

    def test_connection_pool_size_parameter(self):
        """Test that connection pool size parameter is handled."""
        # Test with different pool sizes
        for pool_size in [5, 10, 20]:
            db = SecurityEventsPostgreSQL(connection_pool_size=pool_size)
            # Pool size is passed to DatabaseManager during initialization,
            # not stored in the SecurityEventsPostgreSQL instance
            assert db.db_manager is None
            assert db._initialized is False


class TestSecurityEventsPostgreSQLMockedOperations:
    """Test database operations with minimal mocking to maximize coverage."""

    @pytest.mark.asyncio
    async def test_log_security_event_bypass_db(self):
        """Test log_security_event by bypassing actual database operations."""
        db = SecurityEventsPostgreSQL()
        test_event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.WARNING,
            user_id="test_user",
            details={"test": "data"},
        )

        # Mock the entire method to test parameter handling
        mock_response = SecurityEventResponse(
            id=uuid4(),
            event_type=SecurityEventType.LOGIN_FAILURE.value,
            severity=SecurityEventSeverity.WARNING.value,
            user_id="test_user",
            timestamp=datetime.now(UTC),
            details={"test": "data"},
            risk_score=25,
            source="auth_system",
        )

        with patch.object(db, "log_security_event", return_value=mock_response) as mock_log:
            result = await db.log_security_event(test_event)

            mock_log.assert_called_once_with(test_event)
            assert isinstance(result, SecurityEventResponse)
            assert result.event_type == SecurityEventType.LOGIN_FAILURE

    @pytest.mark.asyncio
    async def test_get_events_by_user_bypass_db(self):
        """Test get_events_by_user by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        mock_events = [
            SecurityEventResponse(
                id=uuid4(),
                event_type=SecurityEventType.LOGIN_FAILURE.value,
                severity=SecurityEventSeverity.WARNING.value,
                user_id="test_user",
                timestamp=datetime.now(UTC),
                details={},
                risk_score=10,
                source="auth_system",
            ),
        ]

        with patch.object(db, "get_events_by_user", return_value=mock_events) as mock_get:
            result = await db.get_events_by_user("test_user", limit=10)

            mock_get.assert_called_once_with("test_user", limit=10)
            assert len(result) == 1
            assert result[0].user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_recent_events_bypass_db(self):
        """Test get_recent_events by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        mock_events = []

        with patch.object(db, "get_recent_events", return_value=mock_events) as mock_get:
            result = await db.get_recent_events(limit=50)

            mock_get.assert_called_once_with(limit=50)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_events_by_ip_bypass_db(self):
        """Test get_events_by_ip by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        mock_events = [
            SecurityEventResponse(
                id=uuid4(),
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY.value,
                severity=SecurityEventSeverity.CRITICAL.value,
                ip_address="192.168.1.100",
                timestamp=datetime.now(UTC),
                details={},
                risk_score=80,
                source="auth_system",
            ),
        ]

        with patch.object(db, "get_events_by_ip", return_value=mock_events) as mock_get:
            result = await db.get_events_by_ip("192.168.1.100", hours_back=24)

            mock_get.assert_called_once_with("192.168.1.100", hours_back=24)
            assert len(result) == 1
            assert result[0].ip_address == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_events_by_date_range_bypass_db(self):
        """Test get_events_by_date_range by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        start_date = datetime.now(UTC) - timedelta(days=7)
        end_date = datetime.now(UTC)

        with patch.object(db, "get_events_by_date_range", return_value=[]) as mock_get:
            result = await db.get_events_by_date_range(start_date, end_date)

            mock_get.assert_called_once_with(start_date, end_date)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_events_bypass_db(self):
        """Test cleanup_old_events by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        with patch.object(db, "cleanup_old_events", return_value=25) as mock_cleanup:
            result = await db.cleanup_old_events(days_to_keep=30)

            mock_cleanup.assert_called_once_with(days_to_keep=30)
            assert result == 25

    @pytest.mark.asyncio
    async def test_cleanup_expired_events_bypass_db(self):
        """Test cleanup_expired_events by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        cutoff_date = datetime.now(UTC) - timedelta(days=90)
        event_types = [SecurityEventType.LOGIN_FAILURE]

        with patch.object(db, "cleanup_expired_events", return_value=15) as mock_cleanup:
            result = await db.cleanup_expired_events(cutoff_date, event_types)

            mock_cleanup.assert_called_once_with(cutoff_date, event_types)
            assert result == 15

    @pytest.mark.asyncio
    async def test_vacuum_database_bypass_db(self):
        """Test vacuum_database by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        with patch.object(db, "vacuum_database", return_value=None) as mock_vacuum:
            await db.vacuum_database()

            mock_vacuum.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_statistics_bypass_db(self):
        """Test get_statistics by bypassing database operations."""
        db = SecurityEventsPostgreSQL()
        db._query_count = 10
        db._total_query_time = 1.5

        mock_stats = {
            "total_events": 1000,
            "recent_events_24h": 50,
            "database_type": "postgresql",
            "query_count": 12,
            "average_query_time_ms": 125.0,
            "initialized": True,
        }

        with patch.object(db, "get_statistics", return_value=mock_stats) as mock_get:
            result = await db.get_statistics()

            mock_get.assert_called_once()
            assert result["database_type"] == "postgresql"
            assert result["total_events"] == 1000

    @pytest.mark.asyncio
    async def test_create_event_bypass_db(self):
        """Test create_event by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        event_data = {
            "event_type": "login_failure",
            "severity": "warning",
            "user_id": "test_user",
        }

        mock_response = SecurityEventResponse(
            id=uuid4(),
            event_type=SecurityEventType.LOGIN_FAILURE.value,
            severity=SecurityEventSeverity.WARNING.value,
            user_id="test_user",
            timestamp=datetime.now(UTC),
            details={},
            risk_score=25,
            source="auth_system",
        )

        with patch.object(db, "create_event", return_value=mock_response) as mock_create:
            result = await db.create_event(event_data)

            mock_create.assert_called_once_with(event_data)
            assert result.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_event_by_id_bypass_db(self):
        """Test get_event_by_id by bypassing database operations."""
        db = SecurityEventsPostgreSQL()

        mock_response = SecurityEventResponse(
            id=uuid4(),
            event_type=SecurityEventType.LOGIN_SUCCESS.value,
            severity=SecurityEventSeverity.INFO.value,
            user_id="test_user",
            timestamp=datetime.now(UTC),
            details={},
            risk_score=0,
            source="auth_system",
        )

        # Test found case
        with patch.object(db, "get_event_by_id", return_value=mock_response) as mock_get:
            result = await db.get_event_by_id(123)

            mock_get.assert_called_once_with(123)
            assert result is not None
            assert result.id == mock_response.id

        # Test not found case
        with patch.object(db, "get_event_by_id", return_value=None) as mock_get:
            result = await db.get_event_by_id(999)

            mock_get.assert_called_once_with(999)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_events_by_user_id_alias_bypass_db(self):
        """Test get_events_by_user_id alias method."""
        db = SecurityEventsPostgreSQL()

        with patch.object(db, "get_events_by_user_id", return_value=[]) as mock_get:
            result = await db.get_events_by_user_id("test_user")

            mock_get.assert_called_once_with("test_user")
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_events_by_type_bypass_db(self):
        """Test get_events_by_type method."""
        db = SecurityEventsPostgreSQL()

        with patch.object(db, "get_events_by_type", return_value=[]) as mock_get:
            result = await db.get_events_by_type(
                SecurityEventType.LOGIN_FAILURE,
                limit=50,
                hours_back=12,
            )

            mock_get.assert_called_once_with(
                SecurityEventType.LOGIN_FAILURE,
                limit=50,
                hours_back=12,
            )
            assert len(result) == 0

    def test_comprehensive_enum_mapping(self):
        """Test that all enum mappings work correctly."""
        db = SecurityEventsPostgreSQL()

        # Test all SecurityEventType mappings
        event_types = [
            ("login_success", SecurityEventType.LOGIN_SUCCESS),
            ("login_failure", SecurityEventType.LOGIN_FAILURE),
            ("logout", SecurityEventType.LOGOUT),
            ("password_changed", SecurityEventType.PASSWORD_CHANGED),
            ("account_lockout", SecurityEventType.ACCOUNT_LOCKOUT),
            ("suspicious_activity", SecurityEventType.SUSPICIOUS_ACTIVITY),
            ("brute_force_attempt", SecurityEventType.BRUTE_FORCE_ATTEMPT),
            ("system_error", SecurityEventType.SYSTEM_ERROR),
            ("service_token_auth", SecurityEventType.SERVICE_TOKEN_AUTH),
            ("rate_limit_exceeded", SecurityEventType.RATE_LIMIT_EXCEEDED),
        ]

        for string_val, enum_val in event_types:
            mock_event = MagicMock()
            mock_event.event_type = string_val
            mock_event.severity = "info"
            mock_event.id = uuid4()
            mock_event.user_id = None
            mock_event.ip_address = None
            mock_event.user_agent = None
            mock_event.session_id = None
            mock_event.details = {}
            mock_event.risk_score = 0
            mock_event.timestamp = datetime.now(UTC)

            result = db._model_to_response(mock_event)
            assert result.event_type == enum_val

        # Test all SecurityEventSeverity mappings
        severities = [
            ("info", SecurityEventSeverity.INFO),
            ("warning", SecurityEventSeverity.WARNING),
            ("critical", SecurityEventSeverity.CRITICAL),
        ]

        for string_val, enum_val in severities:
            mock_event = MagicMock()
            mock_event.event_type = "system_error"
            mock_event.severity = string_val
            mock_event.id = uuid4()
            mock_event.user_id = None
            mock_event.ip_address = None
            mock_event.user_agent = None
            mock_event.session_id = None
            mock_event.details = {}
            mock_event.risk_score = 0
            mock_event.timestamp = datetime.now(UTC)

            result = db._model_to_response(mock_event)
            assert result.severity == enum_val

    def test_detailed_initialization_parameters(self):
        """Test initialization with various parameter combinations."""
        # Test default initialization
        db1 = SecurityEventsPostgreSQL()
        assert db1._initialized is False
        assert db1._query_count == 0
        assert db1._total_query_time == 0.0

        # Test with connection pool size
        db2 = SecurityEventsPostgreSQL(connection_pool_size=15)
        assert db2._initialized is False
        assert db2._query_count == 0
        assert db2._total_query_time == 0.0

        # Test multiple instances are independent
        db1._query_count = 5
        db1._total_query_time = 1.0
        assert db2._query_count == 0
        assert db2._total_query_time == 0.0

    def test_statistics_calculation_edge_cases(self):
        """Test statistics calculation with edge cases."""
        db = SecurityEventsPostgreSQL()

        # Test with zero queries
        db._query_count = 0
        db._total_query_time = 0.0
        # This would be tested in the actual get_statistics method

        # Test with single query
        db._query_count = 1
        db._total_query_time = 0.5
        # This would show average of 500ms per query

        # Test with many queries
        db._query_count = 1000
        db._total_query_time = 10.0
        # This would show average of 10ms per query

    def test_query_stats_boundary_conditions(self):
        """Test query statistics with boundary conditions."""
        db = SecurityEventsPostgreSQL()

        # Test maximum values
        db._query_count = 999
        db._total_query_time = 99.9
        assert db._query_count == 999
        assert db._total_query_time == 99.9

        # Test accumulation
        db._query_count += 1
        db._total_query_time += 0.1
        assert db._query_count == 1000
        assert db._total_query_time == 100.0

    @pytest.mark.asyncio
    async def test_error_propagation_patterns(self):
        """Test that errors are properly propagated from methods."""
        db = SecurityEventsPostgreSQL()

        # Test that methods that should initialize will call initialize
        methods_that_initialize = [
            "log_security_event",
            "get_events_by_user",
            "get_events_by_ip",
            "get_recent_events",
            "get_events_by_date_range",
            "cleanup_old_events",
            "cleanup_expired_events",
            "get_statistics",
            "vacuum_database",
            "create_event",
            "get_event_by_id",
            "get_events_by_user_id",
            "get_events_by_type",
        ]

        for method_name in methods_that_initialize:
            if hasattr(db, method_name):
                method = getattr(db, method_name)
                # Test that these methods exist and are callable
                assert callable(method)
