"""
Comprehensive tests for metrics storage module.

This test suite provides complete coverage for the MetricsStorage class,
including database operations, event storage, querying, and cleanup functionality.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import tempfile

import pytest

from src.metrics.events import MetricEvent, MetricEventType
from src.metrics.storage import MetricsStorage


class TestMetricsStorageInit:
    """Test MetricsStorage initialization."""

    def test_storage_initialization_default_path(self):
        """Test storage initializes with default database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            storage = MetricsStorage(str(db_path))

            assert storage.database_path == str(db_path)
            assert Path(db_path).exists()

    def test_storage_initialization_creates_parent_directories(self):
        """Test storage creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "deep" / "metrics.db"
            MetricsStorage(str(nested_path))

            assert nested_path.parent.exists()
            assert nested_path.exists()

    def test_storage_initialization_creates_schema(self):
        """Test storage creates database schema on initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "schema_test.db"
            MetricsStorage(str(db_path))

            # Check that tables were created
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            table_names = [table[0] for table in tables]
            assert "metric_events" in table_names


class TestMetricsStorageEventStorage:
    """Test event storage functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_events.db"
        self.storage = MetricsStorage(str(self.db_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_store_event_success(self):
        """Test successful event storage."""
        event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="test-session-123",
            user_id="test-user",
            hyde_score=85,
            action_taken="analysis_complete",
            query_text="test query",
            additional_data={"source": "test"},
        )

        result = await self.storage.store_event(event)

        assert result is True

    @pytest.mark.asyncio
    async def test_store_event_with_minimal_data(self):
        """Test storing event with minimal required data."""
        event = MetricEvent(
            event_type=MetricEventType.USER_FEEDBACK,
            session_id="minimal-session",
            feedback_type="thumbs_up",
            feedback_target="response_quality",
        )

        result = await self.storage.store_event(event)

        assert result is True

    @pytest.mark.asyncio
    async def test_store_event_database_error(self):
        """Test event storage handles database errors gracefully."""
        # Close the database to simulate error
        self.storage.database_path = "/invalid/path/cannot/write.db"

        event = MetricEvent(event_type=MetricEventType.ERROR_OCCURRED, session_id="error-session")

        result = await self.storage.store_event(event)

        assert result is False

    @pytest.mark.asyncio
    async def test_store_events_batch_success(self):
        """Test successful batch event storage."""
        events = []
        for i in range(5):
            event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=f"batch-session-{i}",
                hyde_score=80 + i,
                action_taken="batch_test",
            )
            events.append(event)

        stored_count = await self.storage.store_events_batch(events)

        assert stored_count == 5

    @pytest.mark.asyncio
    async def test_store_events_batch_empty_list(self):
        """Test batch storage with empty event list."""
        stored_count = await self.storage.store_events_batch([])

        assert stored_count == 0

    @pytest.mark.asyncio
    async def test_store_events_batch_partial_failure(self):
        """Test batch storage continues despite individual event errors."""
        # Create mix of valid and invalid events
        events = []

        # Valid event
        valid_event = MetricEvent(event_type=MetricEventType.QUERY_PROCESSED, session_id="valid-session", hyde_score=85)
        events.append(valid_event)

        # Invalid event (will trigger constraint error with duplicate ID)
        invalid_event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="invalid-session",
            event_id=valid_event.event_id,  # Duplicate ID
        )
        events.append(invalid_event)

        stored_count = await self.storage.store_events_batch(events)

        # Should store at least the valid event
        assert stored_count >= 1


class TestMetricsStorageQuerying:
    """Test event querying functionality."""

    def setup_method(self):
        """Set up test fixtures with sample data."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_queries.db"
        self.storage = MetricsStorage(str(self.db_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_events_by_session_id(self):
        """Test retrieving events by session ID."""
        session_id = "query-test-session"

        # Store test events
        for i in range(3):
            event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=session_id,
                hyde_score=70 + i * 5,
                action_taken=f"test_action_{i}",
            )
            await self.storage.store_event(event)

        # Store event with different session ID
        other_event = MetricEvent(event_type=MetricEventType.QUERY_PROCESSED, session_id="other-session", hyde_score=90)
        await self.storage.store_event(other_event)

        # Query events for specific session
        events = await self.storage.get_events(
            session_id=session_id,
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        assert len(events) == 3
        assert all(event.session_id == session_id for event in events)

    @pytest.mark.asyncio
    async def test_get_events_by_event_type(self):
        """Test retrieving events by event type."""
        session_id = "type-test-session"

        # Store different types of events
        query_event = MetricEvent(event_type=MetricEventType.QUERY_PROCESSED, session_id=session_id, hyde_score=85)
        await self.storage.store_event(query_event)

        feedback_event = MetricEvent(
            event_type=MetricEventType.USER_FEEDBACK,
            session_id=session_id,
            feedback_type="thumbs_up",
        )
        await self.storage.store_event(feedback_event)

        # Query only feedback events
        events = await self.storage.get_events(
            event_types=[MetricEventType.USER_FEEDBACK],
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        assert len(events) == 1
        assert events[0].event_type == MetricEventType.USER_FEEDBACK

    @pytest.mark.asyncio
    async def test_get_events_with_time_range(self):
        """Test retrieving events within specific time range."""
        session_id = "time-test-session"

        # Store event with specific timestamp
        old_time = datetime.utcnow() - timedelta(hours=2)
        old_event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id=session_id,
            timestamp=old_time,
            hyde_score=75,
        )
        await self.storage.store_event(old_event)

        # Store recent event
        recent_event = MetricEvent(event_type=MetricEventType.QUERY_PROCESSED, session_id=session_id, hyde_score=85)
        await self.storage.store_event(recent_event)

        # Query only recent events (last hour)
        events = await self.storage.get_events(
            session_id=session_id,
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        # Should only get the recent event
        assert len(events) == 1
        assert events[0].event_id == recent_event.event_id

    @pytest.mark.asyncio
    async def test_get_events_with_limit(self):
        """Test retrieving events with limit parameter."""
        session_id = "limit-test-session"

        # Store multiple events
        for i in range(10):
            event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=session_id,
                hyde_score=70 + i,
                action_taken=f"action_{i}",
            )
            await self.storage.store_event(event)

        # Query with limit
        events = await self.storage.get_events(
            session_id=session_id,
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
            limit=5,
        )

        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_events_no_results(self):
        """Test querying events with no matching results."""
        events = await self.storage.get_events(
            session_id="nonexistent-session",
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        assert len(events) == 0
        assert events == []


class TestMetricsStorageAnalytics:
    """Test analytics and summary functionality."""

    def setup_method(self):
        """Set up test fixtures with sample data."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.storage = MetricsStorage(str(self.db_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_metrics_summary_with_data(self):
        """Test metrics summary generation with sample data."""
        # Store sample events
        events = [
            MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id="summary-session-1",
                hyde_score=85,
                action_taken="complete",
                response_time_ms=150,
            ),
            MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id="summary-session-2",
                hyde_score=75,
                action_taken="clarification",
                response_time_ms=200,
            ),
            MetricEvent(
                event_type=MetricEventType.USER_FEEDBACK,
                session_id="summary-session-1",
                feedback_type="thumbs_up",
                feedback_score=5,
            ),
        ]

        for event in events:
            await self.storage.store_event(event)

        summary = await self.storage.get_metrics_summary(hours=24)

        assert "hyde_performance" in summary
        assert "user_feedback" in summary
        assert "latency_distribution" in summary
        assert summary["hyde_performance"]["total_queries"] == 2
        assert summary["hyde_performance"]["avg_hyde_score"] == 80.0
        assert len(summary["user_feedback"]) == 1

    @pytest.mark.asyncio
    async def test_get_metrics_summary_empty_database(self):
        """Test metrics summary with empty database."""
        summary = await self.storage.get_metrics_summary(hours=24)

        # Should return structure with zero values
        assert "hyde_performance" in summary
        assert summary["hyde_performance"]["total_queries"] == 0
        assert len(summary["user_feedback"]) == 0

    @pytest.mark.asyncio
    async def test_get_metrics_summary_time_filtering(self):
        """Test metrics summary respects time filtering."""
        # Store old event
        old_event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="old-session",
            timestamp=datetime.utcnow() - timedelta(days=2),
            hyde_score=90,
        )
        await self.storage.store_event(old_event)

        # Store recent event
        recent_event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="recent-session",
            hyde_score=80,
        )
        await self.storage.store_event(recent_event)

        # Get summary for last 24 hours only
        summary = await self.storage.get_metrics_summary(hours=24)

        # Should only include recent event
        assert summary["hyde_performance"]["total_queries"] == 1


class TestMetricsStorageMaintenanceAndStats:
    """Test database maintenance and statistics functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_maintenance.db"
        self.storage = MetricsStorage(str(self.db_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self):
        """Test cleanup of old events."""
        # Store old events
        old_time = datetime.utcnow() - timedelta(days=35)
        for i in range(3):
            old_event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=f"old-session-{i}",
                timestamp=old_time,
                hyde_score=80,
            )
            await self.storage.store_event(old_event)

        # Store recent events
        for i in range(2):
            recent_event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=f"recent-session-{i}",
                hyde_score=85,
            )
            await self.storage.store_event(recent_event)

        # Cleanup events older than 30 days
        deleted_count = await self.storage.cleanup_old_events(days_to_keep=30)

        assert deleted_count == 3

        # Verify recent events still exist
        recent_events = await self.storage.get_events(
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )
        assert len(recent_events) == 2

    @pytest.mark.asyncio
    async def test_cleanup_old_events_no_old_data(self):
        """Test cleanup when no old events exist."""
        # Store only recent events
        for i in range(2):
            event = MetricEvent(event_type=MetricEventType.QUERY_PROCESSED, session_id=f"recent-{i}", hyde_score=85)
            await self.storage.store_event(event)

        # Attempt cleanup
        deleted_count = await self.storage.cleanup_old_events(days_to_keep=30)

        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_get_database_stats(self):
        """Test database statistics retrieval."""
        # Store sample events
        for i in range(5):
            event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=f"stats-session-{i}",
                hyde_score=80 + i,
            )
            await self.storage.store_event(event)

        stats = await self.storage.get_database_stats()

        assert "total_events" in stats
        assert "database_size_mb" in stats
        assert "oldest_event" in stats
        assert "newest_event" in stats
        assert stats["total_events"] == 5
        assert stats["database_size_mb"] > 0

    @pytest.mark.asyncio
    async def test_get_database_stats_empty_database(self):
        """Test database statistics with empty database."""
        stats = await self.storage.get_database_stats()

        assert stats["total_events"] == 0
        assert stats["oldest_event"] is None
        assert stats["newest_event"] is None
        assert stats["database_size_mb"] >= 0  # Empty database still has some size


class TestMetricsStorageErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_errors.db"
        self.storage = MetricsStorage(str(self.db_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_concurrent_database_access(self):
        """Test concurrent database access doesn't cause issues."""

        async def store_events(session_prefix: str, count: int):
            for i in range(count):
                event = MetricEvent(
                    event_type=MetricEventType.QUERY_PROCESSED,
                    session_id=f"{session_prefix}-{i}",
                    hyde_score=80,
                )
                await self.storage.store_event(event)

        # Run concurrent storage operations
        tasks = [store_events("concurrent-a", 5), store_events("concurrent-b", 5), store_events("concurrent-c", 5)]

        await asyncio.gather(*tasks)

        # Verify all events were stored
        all_events = await self.storage.get_events(
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        assert len(all_events) == 15

    @pytest.mark.asyncio
    async def test_database_corruption_resilience(self):
        """Test resilience to database corruption/access issues."""
        # Store a valid event first
        valid_event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="corruption-test",
            hyde_score=85,
        )
        await self.storage.store_event(valid_event)

        # Simulate database path corruption
        original_path = self.storage.database_path
        self.storage.database_path = "/invalid/nonexistent/path.db"

        # Subsequent operations should handle errors gracefully
        invalid_event = MetricEvent(event_type=MetricEventType.ERROR_OCCURRED, session_id="invalid-session")

        result = await self.storage.store_event(invalid_event)
        assert result is False

        # Restore path
        self.storage.database_path = original_path

    @pytest.mark.asyncio
    async def test_malformed_event_handling(self):
        """Test handling of malformed event data."""
        # Create event with None values that might cause issues
        event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="malformed-test",
            hyde_score=None,  # This should be handled gracefully
            query_text="",  # Empty string
        )

        result = await self.storage.store_event(event)

        # Should handle gracefully (True or False, but shouldn't crash)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_large_event_data_handling(self):
        """Test handling of events with large data payloads."""
        # Create event with large additional_data
        large_data = {"large_field": "x" * 10000}  # 10KB string

        event = MetricEvent(
            event_type=MetricEventType.QUERY_PROCESSED,
            session_id="large-data-test",
            hyde_score=85,
            additional_data=large_data,
        )

        result = await self.storage.store_event(event)

        assert result is True

        # Verify we can retrieve the large event
        events = await self.storage.get_events(
            session_id="large-data-test",
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        assert len(events) == 1
        assert len(str(events[0].additional_data.get("large_field", ""))) == 10000


class TestMetricsStorageIntegration:
    """Integration tests for complete storage workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_integration.db"
        self.storage = MetricsStorage(str(self.db_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_metrics_workflow(self):
        """Test complete workflow from storage to analysis to cleanup."""
        session_id = "workflow-test"

        # Step 1: Store various types of events
        events = [
            MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=session_id,
                hyde_score=85,
                action_taken="complete",
                response_time_ms=150,
            ),
            MetricEvent(
                event_type=MetricEventType.USER_FEEDBACK,
                session_id=session_id,
                feedback_type="thumbs_up",
                feedback_score=5,
            ),
            MetricEvent(
                event_type=MetricEventType.ERROR_OCCURRED,
                session_id=session_id,
                error_type="validation_error",
                error_details="Sample error for testing",
            ),
        ]

        # Store events individually and in batch
        await self.storage.store_event(events[0])
        batch_count = await self.storage.store_events_batch(events[1:])

        assert batch_count == 2

        # Step 2: Query and analyze data
        all_events = await self.storage.get_events(
            session_id=session_id,
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )
        assert len(all_events) == 3

        # Get metrics summary
        summary = await self.storage.get_metrics_summary(hours=1)
        assert summary["hyde_performance"]["total_queries"] == 1
        assert len(summary["user_feedback"]) == 1

        # Step 3: Check database stats
        stats = await self.storage.get_database_stats()
        assert stats["total_events"] == 3

        # Step 4: Cleanup (should not affect recent data)
        deleted = await self.storage.cleanup_old_events(days_to_keep=1)
        assert deleted == 0

        # Verify data still exists
        final_events = await self.storage.get_events(
            session_id=session_id,
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )
        assert len(final_events) == 3

    @pytest.mark.asyncio
    async def test_high_volume_storage_performance(self):
        """Test storage performance with high volume of events."""
        import time

        start_time = time.time()

        # Store 100 events in batch
        events = []
        for i in range(100):
            event = MetricEvent(
                event_type=MetricEventType.QUERY_PROCESSED,
                session_id=f"perf-session-{i % 10}",  # 10 different sessions
                hyde_score=70 + (i % 30),  # Vary scores
                action_taken="performance_test",
                response_time_ms=100 + (i % 200),
            )
            events.append(event)

        stored_count = await self.storage.store_events_batch(events)
        storage_time = time.time() - start_time

        assert stored_count == 100
        # Should complete in reasonable time (less than 5 seconds)
        assert storage_time < 5.0

        # Verify data integrity
        start_query_time = time.time()
        all_events = await self.storage.get_events(
            start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            end_time=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
            limit=1000,
        )
        query_time = time.time() - start_query_time

        assert len(all_events) == 100
        # Query should also be fast
        assert query_time < 2.0
