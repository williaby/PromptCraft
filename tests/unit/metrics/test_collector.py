"""
Comprehensive tests for metrics collector module.

This test suite provides complete coverage for the MetricsCollector class,
including event recording, buffering, background processing, and global collector management.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.metrics.collector import MetricsCollector, get_metrics_collector, shutdown_metrics_collector
from src.metrics.events import MetricEventType


class TestMetricsCollectorInit:
    """Test MetricsCollector initialization."""

    def test_collector_initialization_default(self):
        """Test collector initializes with default settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.db")
            collector = MetricsCollector(database_path=db_path)

            assert collector.storage is not None
            assert collector._event_buffer == []
            assert collector._batch_size == 10
            assert collector._flush_interval == 30
            assert collector._shutdown is False
            assert collector._flush_task is None

    def test_collector_initialization_unsupported_backend(self):
        """Test collector raises error for unsupported storage backend."""
        with pytest.raises(ValueError, match="Unsupported storage backend"):
            MetricsCollector(storage_backend="invalid_backend")

    def test_collector_initialization_custom_database_path(self):
        """Test collector initialization with custom database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = str(Path(temp_dir) / "custom_metrics.db")
            collector = MetricsCollector(database_path=custom_path)

            assert collector.storage.database_path == custom_path


class TestMetricsCollectorLifecycle:
    """Test collector lifecycle management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "lifecycle_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_start_collector(self):
        """Test starting the metrics collector."""
        await self.collector.start()

        assert self.collector._flush_task is not None
        assert not self.collector._flush_task.done()

        # Clean up
        await self.collector.stop()

    @pytest.mark.asyncio
    async def test_start_collector_already_started(self):
        """Test starting collector when already started."""
        await self.collector.start()
        first_task = self.collector._flush_task

        # Start again - should not create new task
        await self.collector.start()
        second_task = self.collector._flush_task

        assert first_task is second_task

        # Clean up
        await self.collector.stop()

    @pytest.mark.asyncio
    async def test_stop_collector(self):
        """Test stopping the metrics collector."""
        await self.collector.start()
        assert self.collector._flush_task is not None

        await self.collector.stop()

        assert self.collector._shutdown is True
        assert self.collector._flush_task.done() or self.collector._flush_task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_collector_not_started(self):
        """Test stopping collector that was never started."""
        # Should not raise error
        await self.collector.stop()

        assert self.collector._shutdown is True


class TestMetricsCollectorEventRecording:
    """Test event recording functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "recording_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_record_query_processed_basic(self):
        """Test recording basic query processed event."""
        event_id = await self.collector.record_query_processed(
            session_id="test-session",
            hyde_score=85,
            action_taken="complete",
            response_time_ms=150,
            query_text="test query",
        )

        assert event_id != ""
        assert len(self.collector._event_buffer) == 1

        event = self.collector._event_buffer[0]
        assert event.event_type == MetricEventType.QUERY_PROCESSED
        assert event.session_id == "test-session"
        assert event.hyde_score == 85
        assert event.action_taken == "complete"
        assert event.response_time_ms == 150
        assert event.query_text_hash is not None
        assert event.query_length == 2  # "test query" has 2 words

    @pytest.mark.asyncio
    async def test_record_query_processed_with_optional_fields(self):
        """Test recording query processed event with optional fields."""
        event_id = await self.collector.record_query_processed(
            session_id="test-session",
            hyde_score=75,
            action_taken="clarification",
            response_time_ms=200,
            query_text="complex query",
            conceptual_issues=["domain_gap", "ambiguity"],
            vector_search_results=25,
            vector_store_type="qdrant",
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.conceptual_issues == ["domain_gap", "ambiguity"]
        assert event.vector_search_results == 25
        assert event.vector_store_type == "qdrant"

    @pytest.mark.asyncio
    async def test_record_query_processed_error_handling(self):
        """Test query processed recording handles errors gracefully."""
        # Mock buffer addition to raise exception
        self.collector._add_event_to_buffer = AsyncMock(side_effect=Exception("Buffer error"))

        # Should not raise exception, but return empty string
        event_id = await self.collector.record_query_processed(
            session_id="error-session",
            hyde_score=80,
            action_taken="error",
            response_time_ms=100,
            query_text="error query",
        )

        assert event_id == ""

    @pytest.mark.asyncio
    async def test_record_user_feedback_basic(self):
        """Test recording basic user feedback event."""
        event_id = await self.collector.record_user_feedback(
            session_id="feedback-session",
            feedback_type="thumbs_up",
            feedback_target="response_quality",
        )

        assert event_id != ""
        assert len(self.collector._event_buffer) == 1

        event = self.collector._event_buffer[0]
        assert event.event_type == MetricEventType.USER_FEEDBACK
        assert event.feedback_type == "thumbs_up"
        assert event.feedback_target == "response_quality"

    @pytest.mark.asyncio
    async def test_record_user_feedback_with_score(self):
        """Test recording user feedback with score and context."""
        additional_context = {"comment": "Great response!", "category": "helpful"}

        event_id = await self.collector.record_user_feedback(
            session_id="feedback-session",
            feedback_type="rating",
            feedback_target="overall",
            feedback_score=5,
            additional_context=additional_context,
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.feedback_score == 5
        assert event.additional_data["comment"] == "Great response!"
        assert event.additional_data["category"] == "helpful"

    @pytest.mark.asyncio
    async def test_record_conceptual_mismatch_basic(self):
        """Test recording basic conceptual mismatch event."""
        event_id = await self.collector.record_conceptual_mismatch(
            session_id="mismatch-session",
            domain_detected="finance",
            mismatch_type="domain_gap",
            suggested_alternative="business_general",
            hyde_score=45,
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.event_type == MetricEventType.CONCEPTUAL_MISMATCH
        assert event.domain_detected == "finance"
        assert event.mismatch_type == "domain_gap"
        assert event.suggested_alternative == "business_general"
        assert event.hyde_score == 45

    @pytest.mark.asyncio
    async def test_record_conceptual_mismatch_with_query_analysis(self):
        """Test conceptual mismatch recording with query text analysis."""
        query_text = "How do I calculate compound interest for my investment portfolio?"

        event_id = await self.collector.record_conceptual_mismatch(
            session_id="analysis-session",
            domain_detected="finance",
            mismatch_type="complexity",
            suggested_alternative="finance_basic",
            hyde_score=40,
            query_text=query_text,
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.query_text_hash is not None
        assert len(event.query_text_hash) == 16  # SHA256 truncated to 16 chars
        assert event.query_length == len(query_text.split())

    @pytest.mark.asyncio
    async def test_record_error_basic(self):
        """Test recording basic error event."""
        event_id = await self.collector.record_error(
            session_id="error-session",
            error_details="Database connection failed",
            error_type="database_error",
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.event_type == MetricEventType.ERROR_OCCURRED
        assert event.error_details == "Database connection failed"
        assert event.error_type == "database_error"

    @pytest.mark.asyncio
    async def test_record_error_with_timing_and_context(self):
        """Test recording error with response time and additional context."""
        context = {"component": "vector_store", "operation": "search", "retry_count": 2}

        event_id = await self.collector.record_error(
            session_id="error-session",
            error_details="Vector search timeout",
            error_type="timeout_error",
            response_time_ms=5000,
            additional_context=context,
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.response_time_ms == 5000
        assert event.additional_data["component"] == "vector_store"
        assert event.additional_data["retry_count"] == 2

    @pytest.mark.asyncio
    async def test_record_custom_event_basic(self):
        """Test recording basic custom event."""
        event_id = await self.collector.record_custom_event(
            event_type=MetricEventType.CACHE_HIT,
            session_id="custom-session",
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.event_type == MetricEventType.CACHE_HIT
        assert event.session_id == "custom-session"

    @pytest.mark.asyncio
    async def test_record_custom_event_with_all_fields(self):
        """Test recording custom event with all possible fields."""
        event_id = await self.collector.record_custom_event(
            event_type=MetricEventType.VECTOR_SEARCH,
            session_id="full-custom-session",
            hyde_score=90,
            action_taken="vector_search_complete",
            conceptual_issues=["none"],
            response_time_ms=75,
            error_details=None,
            query_text="search for relevant documents",
            query_category="document_retrieval",
            custom_field="custom_value",
            numeric_field=42,
        )

        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.hyde_score == 90
        assert event.action_taken == "vector_search_complete"
        assert event.response_time_ms == 75
        assert event.query_text_hash is not None
        assert event.query_length == 4  # "search for relevant documents" has 4 words
        assert event.additional_data["custom_field"] == "custom_value"
        assert event.additional_data["numeric_field"] == 42


class TestMetricsCollectorBuffering:
    """Test event buffering and flushing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "buffering_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_manual_flush_events(self):
        """Test manual flushing of buffered events."""
        # Add events to buffer
        for i in range(3):
            await self.collector.record_query_processed(
                session_id=f"flush-session-{i}",
                hyde_score=80 + i,
                action_taken="flush_test",
                response_time_ms=100,
                query_text=f"test query {i}",
            )

        assert len(self.collector._event_buffer) == 3

        # Flush events
        flushed_count = await self.collector.flush_events()

        assert flushed_count == 3
        assert len(self.collector._event_buffer) == 0

    @pytest.mark.asyncio
    async def test_flush_empty_buffer(self):
        """Test flushing empty event buffer."""
        flushed_count = await self.collector.flush_events()

        assert flushed_count == 0

    @pytest.mark.asyncio
    async def test_auto_flush_on_buffer_full(self):
        """Test automatic flushing when buffer reaches batch size."""
        # Set small batch size for testing
        self.collector._batch_size = 3

        # Mock storage to track calls
        self.collector.storage.store_events_batch = AsyncMock(return_value=3)

        # Add events to trigger auto-flush
        for i in range(3):
            await self.collector.record_query_processed(
                session_id=f"auto-flush-{i}",
                hyde_score=80,
                action_taken="auto_flush_test",
                response_time_ms=100,
                query_text="test",
            )

        # Buffer should be cleared due to auto-flush
        # Give a moment for async flush task to complete
        await asyncio.sleep(0.1)

        assert len(self.collector._event_buffer) == 0

    @pytest.mark.asyncio
    async def test_flush_events_storage_error(self):
        """Test flush handling when storage fails."""
        # Mock storage to fail
        self.collector.storage.store_events_batch = AsyncMock(side_effect=Exception("Storage failed"))

        # Add event to buffer
        await self.collector.record_query_processed(
            session_id="storage-error-session",
            hyde_score=80,
            action_taken="error_test",
            response_time_ms=100,
            query_text="test",
        )

        # Flush should handle error gracefully
        flushed_count = await self.collector.flush_events()

        # Should return 0 when storage fails
        assert flushed_count == 0


class TestMetricsCollectorBackgroundProcessing:
    """Test background processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "background_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_background_flush_task(self):
        """Test background flush task processes events."""
        # Set short flush interval for testing
        self.collector._flush_interval = 0.1

        # Mock storage
        self.collector.storage.store_events_batch = AsyncMock(return_value=1)

        # Start background processing
        await self.collector.start()

        # Add event to buffer
        await self.collector.record_query_processed(
            session_id="background-session",
            hyde_score=85,
            action_taken="background_test",
            response_time_ms=100,
            query_text="background test",
        )

        # Wait for background flush
        await asyncio.sleep(0.2)

        # Buffer should be empty after background flush
        assert len(self.collector._event_buffer) == 0

        # Clean up
        await self.collector.stop()

    @pytest.mark.asyncio
    async def test_background_flush_error_handling(self):
        """Test background flush handles errors gracefully."""
        # Set short interval
        self.collector._flush_interval = 0.1

        # Mock flush to fail once, then succeed
        call_count = {"count": 0}

        async def mock_flush():
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise Exception("First flush fails")
            return 0

        self.collector.flush_events = mock_flush

        # Start background processing
        await self.collector.start()

        # Wait for multiple flush attempts
        await asyncio.sleep(0.3)

        # Should have attempted multiple flushes despite error
        assert call_count["count"] >= 2

        # Clean up
        await self.collector.stop()

    @pytest.mark.asyncio
    async def test_background_flush_shutdown_handling(self):
        """Test background flush respects shutdown signal."""
        # Start collector
        await self.collector.start()

        # Immediately stop
        await self.collector.stop()

        # Background task should be stopped
        assert self.collector._shutdown is True
        assert self.collector._flush_task.done() or self.collector._flush_task.cancelled()


class TestMetricsCollectorAnalytics:
    """Test analytics and metrics retrieval functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "analytics_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_current_metrics(self):
        """Test retrieving current metrics summary."""
        # Add some test events
        await self.collector.record_query_processed(
            session_id="metrics-session",
            hyde_score=85,
            action_taken="complete",
            response_time_ms=150,
            query_text="test query",
        )

        await self.collector.record_user_feedback(
            session_id="metrics-session",
            feedback_type="thumbs_up",
            feedback_target="response_quality",
        )

        # Get metrics (should auto-flush first)
        metrics = await self.collector.get_current_metrics(hours=1)

        # Should contain structured metrics data
        assert isinstance(metrics, dict)
        # Buffer should be empty after auto-flush
        assert len(self.collector._event_buffer) == 0

    @pytest.mark.asyncio
    async def test_get_current_metrics_storage_error(self):
        """Test get_current_metrics handles storage errors."""
        # Mock storage to fail
        self.collector.storage.get_metrics_summary = AsyncMock(side_effect=Exception("Storage failed"))

        metrics = await self.collector.get_current_metrics()

        assert "error" in metrics
        assert "Storage failed" in metrics["error"]

    @pytest.mark.asyncio
    async def test_get_storage_stats(self):
        """Test retrieving storage statistics."""
        # Mock storage stats
        mock_stats = {
            "total_events": 10,
            "database_size_mb": 1.2,
            "oldest_event": "2024-01-01T00:00:00Z",
            "newest_event": "2024-01-02T00:00:00Z",
        }
        self.collector.storage.get_database_stats = AsyncMock(return_value=mock_stats)

        stats = await self.collector.get_storage_stats()

        assert stats == mock_stats

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self):
        """Test cleaning up old metric data."""
        # Mock storage cleanup
        self.collector.storage.cleanup_old_events = AsyncMock(return_value=5)

        deleted_count = await self.collector.cleanup_old_data(days_to_keep=30)

        assert deleted_count == 5
        self.collector.storage.cleanup_old_events.assert_called_once_with(30)


class TestMetricsCollectorGlobalInstance:
    """Test global collector instance management."""

    def setup_method(self):
        """Clean up global state before test."""
        # Reset global collector to ensure clean state
        import src.metrics.collector as collector_module

        collector_module._global_collector = None

    def teardown_method(self):
        """Clean up global state."""
        # Reset global collector
        import src.metrics.collector as collector_module

        collector_module._global_collector = None

    @pytest.mark.asyncio
    async def test_get_metrics_collector_creates_instance(self):
        """Test get_metrics_collector creates global instance."""
        with patch("src.metrics.collector.MetricsCollector") as MockCollector:
            mock_instance = AsyncMock()
            MockCollector.return_value = mock_instance

            collector = await get_metrics_collector()

            assert collector is mock_instance
            MockCollector.assert_called_once()
            mock_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_metrics_collector_returns_existing_instance(self):
        """Test get_metrics_collector returns existing instance."""
        with patch("src.metrics.collector.MetricsCollector") as MockCollector:
            mock_instance = AsyncMock()
            MockCollector.return_value = mock_instance

            # Get collector twice
            collector1 = await get_metrics_collector()
            collector2 = await get_metrics_collector()

            # Should return same instance
            assert collector1 is collector2
            # Constructor should only be called once
            MockCollector.assert_called_once()
            # Start should only be called once
            mock_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_metrics_collector(self):
        """Test shutdown of global metrics collector."""
        with patch("src.metrics.collector.MetricsCollector") as MockCollector:
            mock_instance = AsyncMock()
            MockCollector.return_value = mock_instance

            # Create global instance
            collector = await get_metrics_collector()
            assert collector is mock_instance

            # Shutdown
            await shutdown_metrics_collector()

            mock_instance.stop.assert_called_once()

            # Global collector should be reset
            import src.metrics.collector as collector_module

            assert collector_module._global_collector is None

    @pytest.mark.asyncio
    async def test_shutdown_metrics_collector_none(self):
        """Test shutdown when no global collector exists."""
        # Should not raise error
        await shutdown_metrics_collector()


class TestMetricsCollectorErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "error_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collector_destructor(self):
        """Test collector cleanup on garbage collection."""
        # Create collector with background task
        collector = MetricsCollector(database_path=self.db_path)
        collector._flush_task = Mock()
        collector._flush_task.done.return_value = False

        # Trigger destructor
        collector.__del__()

        collector._flush_task.cancel.assert_called_once()

    def test_collector_destructor_no_task(self):
        """Test collector destructor when no background task exists."""
        collector = MetricsCollector(database_path=self.db_path)

        # Should not raise error
        collector.__del__()

    def test_collector_destructor_completed_task(self):
        """Test collector destructor with completed task."""
        collector = MetricsCollector(database_path=self.db_path)
        collector._flush_task = Mock()
        collector._flush_task.done.return_value = True

        # Should not cancel completed task
        collector.__del__()

        collector._flush_task.cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_concurrent_event_recording(self):
        """Test concurrent event recording doesn't cause issues."""

        async def record_events(session_prefix: str, count: int):
            for i in range(count):
                await self.collector.record_query_processed(
                    session_id=f"{session_prefix}-{i}",
                    hyde_score=80,
                    action_taken="concurrent_test",
                    response_time_ms=100,
                    query_text="concurrent test",
                )

        # Record events concurrently
        tasks = [record_events("concurrent-a", 5), record_events("concurrent-b", 5), record_events("concurrent-c", 5)]

        await asyncio.gather(*tasks)

        # With batch_size=10, expect 10 events to be auto-flushed, leaving 5 in buffer
        assert len(self.collector._event_buffer) == 5

        # Verify total events were recorded by checking the remaining events
        # (The auto-flushed events would be in storage, not accessible via _event_buffer)

    @pytest.mark.asyncio
    async def test_event_recording_with_none_values(self):
        """Test event recording handles None values gracefully."""
        event_id = await self.collector.record_query_processed(
            session_id="none-test",
            hyde_score=None,  # None value
            action_taken="",  # Empty string
            response_time_ms=100,
            query_text=None,  # None value
            conceptual_issues=None,  # None list
        )

        # Should handle gracefully
        assert event_id != ""
        event = self.collector._event_buffer[0]
        assert event.hyde_score is None
        assert event.action_taken == ""
        assert event.query_text_hash == "null"  # None query_text becomes "null" hash
        assert event.query_length == 0  # None query_text becomes 0 length
        assert event.conceptual_issues == []  # None list becomes empty list

    @pytest.mark.asyncio
    async def test_flush_with_storage_partial_failure(self):
        """Test flush when storage partially fails."""
        # Mock storage to return partial success
        self.collector.storage.store_events_batch = AsyncMock(return_value=2)  # Only 2 out of 3

        # Add events
        for i in range(3):
            await self.collector.record_query_processed(
                session_id=f"partial-{i}",
                hyde_score=80,
                action_taken="partial_test",
                response_time_ms=100,
                query_text="test",
            )

        flushed_count = await self.collector.flush_events()

        # Should return what storage actually stored
        assert flushed_count == 2


class TestMetricsCollectorIntegration:
    """Integration tests for complete collector workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "integration_test.db")
        self.collector = MetricsCollector(database_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_metrics_collection_workflow(self):
        """Test complete workflow from startup to shutdown."""
        # Start collector
        await self.collector.start()

        # Record various types of events
        query_id = await self.collector.record_query_processed(
            session_id="integration-session",
            hyde_score=85,
            action_taken="complete",
            response_time_ms=150,
            query_text="integration test query",
        )

        feedback_id = await self.collector.record_user_feedback(
            session_id="integration-session",
            feedback_type="thumbs_up",
            feedback_target="response_quality",
            feedback_score=5,
        )

        error_id = await self.collector.record_error(
            session_id="integration-session",
            error_details="Test error for integration",
            error_type="test_error",
        )

        # All should succeed
        assert query_id != ""
        assert feedback_id != ""
        assert error_id != ""

        # Get current metrics
        metrics = await self.collector.get_current_metrics(hours=1)
        assert isinstance(metrics, dict)

        # Get storage stats
        stats = await self.collector.get_storage_stats()
        assert isinstance(stats, dict)

        # Stop collector cleanly
        await self.collector.stop()

        assert self.collector._shutdown is True

    @pytest.mark.asyncio
    async def test_high_volume_collection_performance(self):
        """Test collector performance with high volume of events."""
        import time

        start_time = time.time()

        # Record 50 events of different types
        tasks = []
        for i in range(50):
            if i % 3 == 0:
                task = self.collector.record_query_processed(
                    session_id=f"perf-session-{i}",
                    hyde_score=70 + (i % 30),
                    action_taken="performance_test",
                    response_time_ms=100 + (i % 100),
                    query_text=f"performance test query {i}",
                )
            elif i % 3 == 1:
                task = self.collector.record_user_feedback(
                    session_id=f"perf-session-{i}",
                    feedback_type="rating",
                    feedback_target="overall",
                    feedback_score=1 + (i % 5),
                )
            else:
                task = self.collector.record_error(
                    session_id=f"perf-session-{i}",
                    error_details=f"Performance test error {i}",
                    error_type="performance_test_error",
                )

            tasks.append(task)

        # Execute all recordings
        results = await asyncio.gather(*tasks)
        collection_time = time.time() - start_time

        # All should succeed
        assert all(event_id != "" for event_id in results)
        # Should complete in reasonable time
        assert collection_time < 5.0

        # Attempt to flush remaining events (should be 0 due to auto-flushing)
        start_flush_time = time.time()
        flushed_count = await self.collector.flush_events()
        flush_time = time.time() - start_flush_time

        # Auto-flush should have processed all events already, so buffer should be empty
        assert flushed_count == 0  # No remaining events to flush
        assert flush_time < 2.0

        # Verify events were auto-flushed by checking buffer is empty
        assert len(self.collector._event_buffer) == 0
