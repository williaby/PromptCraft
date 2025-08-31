"""Tests for stateless SecurityMonitor implementation.

Tests the conversion from stateful to stateless design for multi-worker deployment.
All monitoring state is now persisted in PostgreSQL database.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.auth.models import SecurityEventResponse, SecurityEventSeverity, SecurityEventType
from src.auth.security_monitor import SecurityMonitor
from src.database.models import SecurityEvent
from src.utils.time_utils import utc_now


class TestStatelessSecurityMonitor:
    """Test the stateless SecurityMonitor implementation."""

    @pytest.fixture
    async def security_monitor(self):
        """Create a SecurityMonitor instance for testing."""
        with patch("src.auth.security_monitor.get_database_manager") as mock_db_manager:
            mock_session = AsyncMock()
            mock_db_manager.return_value.get_session.return_value.__aenter__.return_value = mock_session
            mock_db_manager.return_value.get_session.return_value.__aexit__.return_value = None

            monitor = SecurityMonitor(alert_threshold=3, time_window=30)
            monitor._db_manager = mock_db_manager.return_value
            return monitor

    @pytest.fixture
    def sample_security_event(self):
        """Create a sample security event for testing."""
        return SecurityEventResponse(
            id=uuid4(),
            event_type=SecurityEventType.LOGIN_FAILURE.value,
            severity=SecurityEventSeverity.WARNING.value,
            user_id="test_user_123",
            ip_address="192.168.1.100",
            timestamp=utc_now(),
            risk_score=75,
            details={"user_agent": "TestBrowser", "reason": "invalid_credentials"},
        )

    async def test_initialization_stateless(self, security_monitor):
        """Test that initialization is stateless and sets up database thresholds."""
        mock_session = AsyncMock()

        # Mock threshold queries
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # alert_threshold not found
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # time_window not found
        ]

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        await security_monitor.initialize()

        # Verify thresholds were created
        assert mock_session.add.call_count == 2
        mock_session.commit.assert_called_once()

        # Verify no background tasks or in-memory state
        assert not hasattr(security_monitor, "_monitoring_task")
        assert not hasattr(security_monitor, "_event_history")
        assert not hasattr(security_monitor, "_blocked_ips")
        assert not hasattr(security_monitor, "_blocked_users")
        assert not hasattr(security_monitor, "_threat_scores")

    async def test_track_event_database_storage(self, security_monitor, sample_security_event):
        """Test that events are stored in database instead of memory."""
        mock_session = AsyncMock()

        # Mock threshold queries returning default values
        threshold_mock = MagicMock()
        threshold_mock.threshold_value = 5
        
        # Create comprehensive mock responses for all database queries
        mock_threshold_result = MagicMock(scalar_one_or_none=MagicMock(return_value=threshold_mock))
        mock_count_result = MagicMock(scalar=MagicMock(return_value=2))
        
        # Setup alternating return values for different query types
        def mock_execute_side_effect(*args, **kwargs):
            # Check query type by analyzing the SQL or parameters
            query_str = str(args[0])
            if "count(" in query_str.lower():
                return mock_count_result
            else:
                return mock_threshold_result
        
        mock_session.execute.side_effect = mock_execute_side_effect
        mock_session.add = AsyncMock()
        mock_session.commit = AsyncMock()

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        await security_monitor.track_event(sample_security_event)

        # Verify event was stored in database
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

        # Verify database queries were made instead of in-memory checks
        assert mock_session.execute.call_count >= 2  # At least threshold queries

    async def test_check_threshold_database_query(self, security_monitor):
        """Test that threshold checking uses database queries."""
        mock_session = AsyncMock()

        # Mock threshold configuration
        threshold_mock = MagicMock()
        threshold_mock.threshold_value = 3

        # Mock database responses
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=threshold_mock)),  # alert_threshold
            MagicMock(scalar_one_or_none=MagicMock(return_value=threshold_mock)),  # time_window (30s)
            MagicMock(scalar=MagicMock(return_value=5)),  # event count (exceeds threshold)
        ]

        entity_key = "ip:192.168.1.100"
        event_timestamp = utc_now()

        result = await security_monitor._check_threshold(mock_session, entity_key, event_timestamp)

        # Should trigger threshold (5 >= 3)
        assert result is True

        # Verify database queries were made
        assert mock_session.execute.call_count == 3

    async def test_threat_score_upsert(self, security_monitor, sample_security_event):
        """Test that threat scores use database upsert operations."""
        mock_session = AsyncMock()

        await security_monitor._update_threat_scores(mock_session, sample_security_event)

        # Verify upsert operations were called for both IP and user
        assert mock_session.execute.call_count == 2  # IP and user

    async def test_block_ip_database_storage(self, security_monitor):
        """Test that IP blocking uses database storage."""
        mock_session = AsyncMock()
        
        # Mock for checking if IP is already blocked (returns None = not blocked)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        await security_monitor.block_ip("192.168.1.100", "Suspicious activity")

        # Verify blocked entity was added to database
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_block_user_database_storage(self, security_monitor):
        """Test that user blocking uses database storage."""
        mock_session = AsyncMock()
        
        # Mock for checking if user is already blocked (returns None = not blocked)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        await security_monitor.block_user("test_user_123", "Account compromise")

        # Verify blocked entity was added to database
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_is_blocked_async_database_query(self, security_monitor):
        """Test that block checking uses database queries."""
        mock_session = AsyncMock()

        # Mock blocked entity
        blocked_entity = MagicMock()
        blocked_entity.is_valid_block = True
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = blocked_entity
        mock_session.execute.return_value = mock_result

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        result = await security_monitor.is_blocked_async("192.168.1.100", "ip")

        assert result is True
        mock_session.execute.assert_called_once()

    async def test_get_threat_score_database_query(self, security_monitor):
        """Test that threat score retrieval uses database queries."""
        mock_session = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 85
        mock_session.execute.return_value = mock_result

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        score = await security_monitor.get_threat_score("192.168.1.100", "ip")

        assert score == 85
        mock_session.execute.assert_called_once()

    async def test_get_monitoring_stats_database_aggregation(self, security_monitor):
        """Test that monitoring stats use database aggregation queries."""
        mock_session = AsyncMock()

        # Mock database aggregation results
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=15)),  # tracked_ips
            MagicMock(scalar=MagicMock(return_value=8)),  # tracked_users
            MagicMock(scalar=MagicMock(return_value=3)),  # blocked_ips
            MagicMock(scalar=MagicMock(return_value=1)),  # blocked_users
            MagicMock(scalar=MagicMock(return_value=12)),  # threat_scores
        ]

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        stats = await security_monitor.get_monitoring_stats()

        # Verify stats are from database queries
        assert stats["tracked_ips"] == 15
        assert stats["tracked_users"] == 8
        assert stats["blocked_ips"] == 3
        assert stats["blocked_users"] == 1
        assert stats["threat_scores"] == 12
        assert stats["stateless_design"] is True
        assert stats["database_backend"] == "PostgreSQL"
        assert stats["alert_callbacks"] == 0  # No longer applicable

        # Verify multiple database queries were made
        assert mock_session.execute.call_count == 5

    async def test_cleanup_old_data_database_operations(self, security_monitor):
        """Test that cleanup operations use database DELETE and UPDATE statements."""
        mock_session = AsyncMock()

        # Mock cleanup operation results
        mock_session.execute.side_effect = [
            MagicMock(rowcount=25),  # deleted_events
            MagicMock(rowcount=2),  # expired_blocks
            MagicMock(rowcount=8),  # decayed_scores
            MagicMock(rowcount=3),  # cleaned_scores
        ]

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        cleanup_stats = await security_monitor.cleanup_old_data(retention_hours=12)

        # Verify cleanup statistics
        assert cleanup_stats["deleted_events"] == 25
        assert cleanup_stats["expired_blocks"] == 2
        assert cleanup_stats["decayed_scores"] == 8
        assert cleanup_stats["cleaned_scores"] == 3

        # Verify database operations were performed
        assert mock_session.execute.call_count == 4
        mock_session.commit.assert_called_once()

    async def test_suspicious_pattern_detection_database_queries(self, security_monitor):
        """Test that suspicious pattern detection uses database queries."""
        mock_session = AsyncMock()

        # Mock pattern detection queries
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=3)),  # failed login count
            MagicMock(scalar=MagicMock(return_value=15)),  # rapid request count
        ]

        # Create event with failed authentication
        event = SecurityEventResponse(
            id=uuid4(),
            event_type=SecurityEventType.LOGIN_FAILURE.value,
            severity=SecurityEventSeverity.WARNING.value,
            user_id="test_user_123",
            ip_address="192.168.1.100",
            timestamp=utc_now(),
            risk_score=75,
            details={},
        )

        await security_monitor._check_patterns(mock_session, event)

        # Verify database queries for pattern detection
        assert mock_session.execute.call_count >= 1

    async def test_no_background_tasks_created(self, security_monitor):
        """Test that no background tasks are created in stateless design."""
        await security_monitor.initialize()

        # Verify no background monitoring task
        assert not hasattr(security_monitor, "_monitoring_task")

        # Verify close method doesn't need to cancel tasks
        await security_monitor.close()  # Should not raise any errors

    async def test_alert_engine_integration(self, security_monitor):
        """Test that alerts are sent through AlertEngine instead of callbacks."""
        # Mock alert engine
        mock_alert_engine = AsyncMock()
        security_monitor._alert_engine = mock_alert_engine

        await security_monitor._trigger_alert("test_alert", "192.168.1.100")

        # Verify alert was sent through AlertEngine
        mock_alert_engine.send_alert.assert_called_once_with(
            alert_type="test_alert",
            message="Security threshold exceeded for 192.168.1.100",
            target="192.168.1.100",
            details={"alert_type": "test_alert", "target": "192.168.1.100"},
        )

    async def test_entity_key_generation(self, security_monitor, sample_security_event):
        """Test that entity keys are correctly generated for database storage."""
        mock_session = AsyncMock()

        await security_monitor._store_security_event(mock_session, sample_security_event)

        # Verify SecurityEvent was created with correct entity_key
        mock_session.add.assert_called_once()

        # Get the SecurityEvent that was added
        added_event = mock_session.add.call_args[0][0]
        assert isinstance(added_event, SecurityEvent)
        assert added_event.entity_key == f"user:{sample_security_event.user_id}"
        assert added_event.event_type == sample_security_event.event_type
        assert added_event.severity == sample_security_event.severity

    async def test_stateless_compatibility_maintained(self, security_monitor):
        """Test that public API remains compatible with stateful version."""
        # All public methods should still exist
        assert hasattr(security_monitor, "track_event")
        assert hasattr(security_monitor, "get_threat_score")
        assert hasattr(security_monitor, "block_ip")
        assert hasattr(security_monitor, "block_user")
        assert hasattr(security_monitor, "is_blocked")
        assert hasattr(security_monitor, "get_monitoring_stats")
        assert hasattr(security_monitor, "initialize")
        assert hasattr(security_monitor, "close")

        # New async methods for better performance
        assert hasattr(security_monitor, "is_blocked_async")
        assert hasattr(security_monitor, "cleanup_old_data")

    @pytest.mark.integration
    async def test_database_integration_flow(self, security_monitor, sample_security_event):
        """Integration test for complete database flow."""
        # This would require an actual database connection in integration tests
        # For now, verify the flow with mocks

        mock_session = AsyncMock()

        # Create a mock query result that can handle different query types
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            # Default to returning None for scalar_one_or_none queries
            result.scalar_one_or_none.return_value = None
            # Return low counts for scalar queries to avoid triggering alerts  
            result.scalar.return_value = 1
            return result
            
        mock_session.execute.side_effect = mock_execute_side_effect

        security_monitor._db_manager.get_session.return_value.__aenter__.return_value = mock_session

        # Full flow: initialize -> track event -> check stats
        await security_monitor.initialize()
        await security_monitor.track_event(sample_security_event)

        # Verify database operations were performed in correct sequence
        assert mock_session.add.call_count >= 2  # thresholds + event
        assert mock_session.commit.call_count >= 2  # init + track
        assert mock_session.execute.call_count >= 5  # various queries


@pytest.mark.asyncio
class TestStatelessSecurityMonitorPerformance:
    """Test performance characteristics of stateless design."""

    async def test_no_memory_leaks_from_state(self):
        """Test that stateless design prevents memory leaks."""
        with patch("src.auth.security_monitor.get_database_manager") as mock_db_manager:
            mock_session = AsyncMock()
            mock_db_manager.return_value.get_session.return_value.__aenter__.return_value = mock_session

            monitor = SecurityMonitor()

            # Create a reusable mock execute function to avoid StopIteration
            def mock_execute_side_effect(*args, **kwargs):
                result = MagicMock()
                # Default to returning None for threshold queries
                result.scalar_one_or_none.return_value = None
                # Return low counts to avoid triggering alerts
                result.scalar.return_value = 0
                return result
            
            mock_session.execute.side_effect = mock_execute_side_effect

            # Process many events
            for i in range(100):
                event = SecurityEventResponse(
                    id=uuid4(),
                    event_type=SecurityEventType.SYSTEM_ERROR.value,
                    severity=SecurityEventSeverity.INFO.value,
                    user_id=f"user_{i}",
                    ip_address=f"192.168.1.{i % 255}",
                    timestamp=utc_now(),
                    risk_score=10,
                    details={},
                )

                await monitor.track_event(event)

            # Verify no in-memory state accumulation
            assert not hasattr(monitor, "_event_history")
            assert not hasattr(monitor, "_blocked_ips")
            assert not hasattr(monitor, "_blocked_users")
            assert not hasattr(monitor, "_threat_scores")

    async def test_database_query_efficiency(self):
        """Test that database queries are efficient and not excessive."""
        with patch("src.auth.security_monitor.get_database_manager") as mock_db_manager:
            mock_session = AsyncMock()
            mock_db_manager.return_value.get_session.return_value.__aenter__.return_value = mock_session

            monitor = SecurityMonitor()

            # Create a reusable mock execute function to avoid StopIteration
            def mock_execute_side_effect(*args, **kwargs):
                result = MagicMock()
                # For threshold queries, return a configured threshold
                threshold_mock = MagicMock()
                threshold_mock.threshold_value = 10
                result.scalar_one_or_none.return_value = threshold_mock
                # For count queries, return low counts to avoid triggering alerts
                result.scalar.return_value = 1
                return result
            
            mock_session.execute.side_effect = mock_execute_side_effect

            event = SecurityEventResponse(
                id=uuid4(),
                event_type=SecurityEventType.LOGIN_SUCCESS.value,
                severity=SecurityEventSeverity.INFO.value,
                user_id="test_user",
                ip_address="192.168.1.1",
                timestamp=utc_now(),
                risk_score=5,
                details={},
            )

            await monitor.track_event(event)

            # Verify reasonable number of database queries (not excessive)
            query_count = mock_session.execute.call_count
            assert query_count <= 10, f"Too many database queries: {query_count}"
