"""Comprehensive unit tests for alert_engine.py - AUTH-4 Enhanced Security Event Logging."""

import asyncio
import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.auth.alert_engine import Alert, AlertChannel, AlertEngine, AlertPriority


class TestAlertPriority:
    """Test AlertPriority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert AlertPriority.LOW.value == "low"
        assert AlertPriority.MEDIUM.value == "medium"
        assert AlertPriority.HIGH.value == "high"
        assert AlertPriority.CRITICAL.value == "critical"

    def test_priority_comparison(self):
        """Test priority comparisons."""
        priorities = [AlertPriority.LOW, AlertPriority.MEDIUM, AlertPriority.HIGH, AlertPriority.CRITICAL]
        assert len(set(priorities)) == 4  # All unique


class TestAlertChannel:
    """Test AlertChannel enum."""

    def test_channel_values(self):
        """Test channel enum values."""
        assert AlertChannel.EMAIL.value == "email"
        assert AlertChannel.SMS.value == "sms"
        assert AlertChannel.SLACK.value == "slack"
        assert AlertChannel.WEBHOOK.value == "webhook"
        assert AlertChannel.LOG.value == "log"

    def test_all_channels_available(self):
        """Test all expected channels are available."""
        expected_channels = {"email", "sms", "slack", "webhook", "log"}
        actual_channels = {channel.value for channel in AlertChannel}
        assert actual_channels == expected_channels


class TestAlert:
    """Test Alert data structure."""

    def test_alert_initialization_minimal(self):
        """Test alert creation with minimal parameters."""
        alert = Alert(
            alert_type="test_alert",
            message="Test message",
            priority=AlertPriority.MEDIUM,
        )

        assert alert.alert_type == "test_alert"
        assert alert.message == "Test message"
        assert alert.priority == AlertPriority.MEDIUM
        assert alert.target is None
        assert alert.details == {}
        assert alert.channels == [AlertChannel.LOG]
        assert isinstance(alert.timestamp, datetime)
        assert alert.timestamp.tzinfo == UTC
        assert alert.id.startswith("test_alert_None_")

    def test_alert_initialization_full(self):
        """Test alert creation with all parameters."""
        details = {"key": "value", "count": 5}
        channels = [AlertChannel.EMAIL, AlertChannel.SLACK]

        alert = Alert(
            alert_type="security_breach",
            message="Critical security event",
            priority=AlertPriority.CRITICAL,
            target="192.168.1.100",
            details=details,
            channels=channels,
        )

        assert alert.alert_type == "security_breach"
        assert alert.message == "Critical security event"
        assert alert.priority == AlertPriority.CRITICAL
        assert alert.target == "192.168.1.100"
        assert alert.details == details
        assert alert.channels == channels
        assert alert.id.startswith("security_breach_192.168.1.100_")

    def test_alert_id_generation(self):
        """Test alert ID generation is unique."""
        alert1 = Alert("test", "message", AlertPriority.LOW)
        alert2 = Alert("test", "message", AlertPriority.LOW)

        assert alert1.id != alert2.id  # Should be different due to timestamp


class TestAlertEngine:
    """Test AlertEngine functionality."""

    @pytest.fixture
    def alert_engine(self):
        """Create AlertEngine for testing."""
        return AlertEngine(rate_limit=5, rate_window=60)

    @pytest.fixture
    def initialized_alert_engine(self, alert_engine):
        """Create and initialize AlertEngine for testing."""
        async def _init():
            await alert_engine.initialize()
            return alert_engine
        return _init

    def test_alert_engine_initialization(self, alert_engine):
        """Test AlertEngine initialization parameters."""
        assert alert_engine.rate_limit == 5
        assert alert_engine.rate_window == 60
        assert alert_engine.default_channels == [AlertChannel.LOG]
        assert not alert_engine._is_initialized
        assert alert_engine._alert_history == []
        assert isinstance(alert_engine._alert_queue, asyncio.Queue)
        assert alert_engine._processing_task is None

    def test_alert_engine_custom_channels(self):
        """Test AlertEngine with custom default channels."""
        custom_channels = [AlertChannel.EMAIL, AlertChannel.SLACK]
        engine = AlertEngine(default_channels=custom_channels)

        assert engine.default_channels == custom_channels

    @pytest.mark.asyncio
    async def test_alert_engine_initialize(self, alert_engine):
        """Test AlertEngine initialization process."""
        assert not alert_engine._is_initialized

        await alert_engine.initialize()

        assert alert_engine._is_initialized
        assert alert_engine._processing_task is not None
        assert not alert_engine._processing_task.done()

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_alert_engine_initialize_idempotent(self, alert_engine):
        """Test AlertEngine initialization is idempotent."""
        await alert_engine.initialize()
        first_task = alert_engine._processing_task

        await alert_engine.initialize()
        second_task = alert_engine._processing_task

        assert first_task == second_task

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_send_alert_basic(self, initialized_alert_engine):
        """Test basic alert sending."""
        alert_engine = await initialized_alert_engine()

        result = await alert_engine.send_alert(
            alert_type="test_alert",
            message="Test message",
        )

        assert result is True
        assert len(alert_engine._alert_history) == 1

        alert = alert_engine._alert_history[0]
        assert alert.alert_type == "test_alert"
        assert alert.message == "Test message"
        assert alert.priority == AlertPriority.MEDIUM

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_send_alert_with_all_params(self, initialized_alert_engine):
        """Test alert sending with all parameters."""
        alert_engine = await initialized_alert_engine()

        result = await alert_engine.send_alert(
            alert_type="security_breach",
            message="Critical security event",
            priority=AlertPriority.CRITICAL,
            target="192.168.1.100",
            details={"attempts": 10, "user": "admin"},
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
        )

        assert result is True
        assert len(alert_engine._alert_history) == 1

        alert = alert_engine._alert_history[0]
        assert alert.alert_type == "security_breach"
        assert alert.priority == AlertPriority.CRITICAL
        assert alert.target == "192.168.1.100"
        assert alert.details == {"attempts": 10, "user": "admin"}
        assert alert.channels == [AlertChannel.EMAIL, AlertChannel.SLACK]

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_alert_rate_limiting(self, alert_engine):
        """Test alert rate limiting functionality."""
        # Set low rate limit for testing
        alert_engine.rate_limit = 2
        alert_engine.rate_window = 60
        await alert_engine.initialize()

        # Send alerts up to rate limit
        result1 = await alert_engine.send_alert("test", "message 1")
        result2 = await alert_engine.send_alert("test", "message 2")

        assert result1 is True
        assert result2 is True

        # Next alert should be rate limited
        result3 = await alert_engine.send_alert("test", "message 3")
        assert result3 is False

        # Check history only has 2 alerts
        assert len(alert_engine._alert_history) == 2

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_alert_rate_limiting_different_types(self, alert_engine):
        """Test rate limiting is per alert type."""
        alert_engine.rate_limit = 1
        await alert_engine.initialize()

        # Different alert types should have separate limits
        result1 = await alert_engine.send_alert("type1", "message")
        result2 = await alert_engine.send_alert("type2", "message")

        assert result1 is True
        assert result2 is True
        assert len(alert_engine._alert_history) == 2

        # Same type should be limited
        result3 = await alert_engine.send_alert("type1", "message")
        assert result3 is False

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self, alert_engine):
        """Test old rate limit entries are cleaned up."""
        alert_engine.rate_limit = 2
        alert_engine.rate_window = 1  # 1 second window
        await alert_engine.initialize()

        # Send alerts to reach limit
        result1 = await alert_engine.send_alert("test", "message 1")
        result2 = await alert_engine.send_alert("test", "message 2")

        assert result1 is True
        assert result2 is True

        # Should be rate limited
        result3 = await alert_engine.send_alert("test", "message 3")
        assert result3 is False

        # Wait for window to pass
        await asyncio.sleep(1.1)

        # Should work again after cleanup
        result4 = await alert_engine.send_alert("test", "message 4")
        assert result4 is True

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_channel_handlers_registration(self, alert_engine):
        """Test channel handlers are properly registered."""
        await alert_engine.initialize()

        expected_channels = {
            AlertChannel.LOG,
            AlertChannel.EMAIL,
            AlertChannel.SLACK,
            AlertChannel.WEBHOOK,
            AlertChannel.SMS,
        }

        assert set(alert_engine._channel_handlers.keys()) == expected_channels

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_log_handler(self, alert_engine):
        """Test log handler functionality."""
        await alert_engine.initialize()

        alert = Alert(
            alert_type="test",
            message="Test message",
            priority=AlertPriority.HIGH,
            target="test_target",
        )

        with patch("src.auth.alert_engine.logger") as mock_logger:
            await alert_engine._log_handler(alert)

            mock_logger.log.assert_called_once_with(
                logging.ERROR,
                "Security Alert: [%s] %s (target=%s, priority=%s)",
                "test",
                "Test message",
                "test_target",
                "high",
            )

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_log_handler_warning_level(self, alert_engine):
        """Test log handler uses warning level for low/medium priority."""
        await alert_engine.initialize()

        alert = Alert(
            alert_type="test",
            message="Test message",
            priority=AlertPriority.MEDIUM,
        )

        with patch("src.auth.alert_engine.logger") as mock_logger:
            await alert_engine._log_handler(alert)

            mock_logger.log.assert_called_once_with(
                logging.WARNING,
                "Security Alert: [%s] %s (target=%s, priority=%s)",
                "test",
                "Test message",
                None,
                "medium",
            )

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_placeholder_handlers(self, alert_engine):
        """Test placeholder handlers for different channels."""
        await alert_engine.initialize()

        alert = Alert("test", "message", AlertPriority.MEDIUM)

        with patch("src.auth.alert_engine.logger") as mock_logger:
            await alert_engine._email_handler(alert)
            await alert_engine._slack_handler(alert)
            await alert_engine._webhook_handler(alert)
            await alert_engine._sms_handler(alert)

            # Should log 4 info messages
            assert mock_logger.info.call_count == 4

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_custom_channel_handler(self, alert_engine):
        """Test registering custom channel handler."""
        await alert_engine.initialize()

        custom_handler = AsyncMock()
        alert_engine.register_channel_handler(AlertChannel.EMAIL, custom_handler)

        assert alert_engine._channel_handlers[AlertChannel.EMAIL] == custom_handler

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_alert_dispatch(self, alert_engine):
        """Test alert dispatching to multiple channels."""
        await alert_engine.initialize()

        # Mock handlers
        log_handler = AsyncMock()
        email_handler = AsyncMock()

        alert_engine._channel_handlers[AlertChannel.LOG] = log_handler
        alert_engine._channel_handlers[AlertChannel.EMAIL] = email_handler

        alert = Alert(
            "test",
            "message",
            AlertPriority.MEDIUM,
            channels=[AlertChannel.LOG, AlertChannel.EMAIL],
        )

        await alert_engine._dispatch_alert(alert)

        log_handler.assert_called_once_with(alert)
        email_handler.assert_called_once_with(alert)

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_alert_dispatch_handler_error(self, alert_engine):
        """Test alert dispatch handles handler errors gracefully."""
        await alert_engine.initialize()

        # Mock handler that raises exception
        failing_handler = AsyncMock(side_effect=Exception("Handler error"))
        working_handler = AsyncMock()

        alert_engine._channel_handlers[AlertChannel.LOG] = failing_handler
        alert_engine._channel_handlers[AlertChannel.EMAIL] = working_handler

        alert = Alert(
            "test",
            "message",
            AlertPriority.MEDIUM,
            channels=[AlertChannel.LOG, AlertChannel.EMAIL],
        )

        with patch("src.auth.alert_engine.logger") as mock_logger:
            await alert_engine._dispatch_alert(alert)

            # Should log error for failed handler
            mock_logger.error.assert_called_once()

        # Working handler should still be called
        working_handler.assert_called_once_with(alert)

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_get_alert_history(self, initialized_alert_engine):
        """Test getting alert history."""
        alert_engine = await initialized_alert_engine()

        # Send different alerts
        await alert_engine.send_alert("type1", "message1", AlertPriority.LOW)
        await alert_engine.send_alert("type2", "message2", AlertPriority.HIGH)
        await alert_engine.send_alert("type1", "message3", AlertPriority.MEDIUM)

        # Get all history
        history = await alert_engine.get_alert_history()
        assert len(history) == 3

        # Should be sorted by timestamp desc
        timestamps = [alert.timestamp for alert in history]
        assert timestamps == sorted(timestamps, reverse=True)

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_get_alert_history_filtered(self, initialized_alert_engine):
        """Test getting filtered alert history."""
        alert_engine = await initialized_alert_engine()

        # Send different alerts
        await alert_engine.send_alert("type1", "message1", AlertPriority.LOW)
        await alert_engine.send_alert("type2", "message2", AlertPriority.HIGH)
        await alert_engine.send_alert("type1", "message3", AlertPriority.HIGH)

        # Filter by priority
        high_priority = await alert_engine.get_alert_history(priority=AlertPriority.HIGH)
        assert len(high_priority) == 2
        assert all(alert.priority == AlertPriority.HIGH for alert in high_priority)

        # Filter by type
        type1_alerts = await alert_engine.get_alert_history(alert_type="type1")
        assert len(type1_alerts) == 2
        assert all(alert.alert_type == "type1" for alert in type1_alerts)

        # Filter by both
        type1_high = await alert_engine.get_alert_history(
            priority=AlertPriority.HIGH,
            alert_type="type1",
        )
        assert len(type1_high) == 1
        assert type1_high[0].alert_type == "type1"
        assert type1_high[0].priority == AlertPriority.HIGH

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_get_alert_history_limit(self, initialized_alert_engine):
        """Test alert history limit parameter."""
        alert_engine = await initialized_alert_engine()

        # Send more alerts than limit
        for i in range(5):
            await alert_engine.send_alert(f"type{i}", f"message{i}")

        # Get limited history
        history = await alert_engine.get_alert_history(limit=3)
        assert len(history) == 3

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_get_alert_stats(self, initialized_alert_engine):
        """Test getting alert statistics."""
        alert_engine = await initialized_alert_engine()

        # Send various alerts
        await alert_engine.send_alert("brute_force", "msg1", AlertPriority.CRITICAL)
        await alert_engine.send_alert("brute_force", "msg2", AlertPriority.CRITICAL)
        await alert_engine.send_alert("api_abuse", "msg3", AlertPriority.LOW)

        stats = await alert_engine.get_alert_stats()

        assert stats["total_alerts"] == 3
        assert stats["queued_alerts"] >= 0  # May have been processed

        # Check priority counts
        assert stats["by_priority"]["critical"] == 2
        assert stats["by_priority"]["low"] == 1
        assert stats["by_priority"]["medium"] == 0
        assert stats["by_priority"]["high"] == 0

        # Check type counts
        assert stats["by_type"]["brute_force"] == 2
        assert stats["by_type"]["api_abuse"] == 1

        # Rate limited types should be empty (within limits)
        assert stats["rate_limited_types"] == []

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_get_alert_stats_rate_limited(self, alert_engine):
        """Test alert stats show rate limited types."""
        # Set very low rate limit
        alert_engine.rate_limit = 1
        alert_engine.rate_window = 3600  # 1 hour
        await alert_engine.initialize()

        # Send alerts to trigger rate limiting
        await alert_engine.send_alert("test", "msg1")
        await alert_engine.send_alert("test", "msg2")  # This should be rate limited

        stats = await alert_engine.get_alert_stats()

        # Should show rate limited type
        assert "test" in stats["rate_limited_types"]

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_close_alert_engine(self, alert_engine):
        """Test closing alert engine properly cancels tasks."""
        await alert_engine.initialize()

        processing_task = alert_engine._processing_task
        assert processing_task is not None
        assert not processing_task.done()

        await alert_engine.close()

        assert processing_task.cancelled()
        assert not alert_engine._is_initialized

    @pytest.mark.asyncio
    async def test_close_uninitialized_engine(self, alert_engine):
        """Test closing uninitialized engine doesn't raise errors."""
        assert not alert_engine._is_initialized
        assert alert_engine._processing_task is None

        # Should not raise exception
        await alert_engine.close()

        assert not alert_engine._is_initialized

    @pytest.mark.asyncio
    async def test_critical_alert_priority_processing(self, alert_engine):
        """Test critical alerts are processed immediately."""
        await alert_engine.initialize()

        # Mock the dispatch method to track calls
        original_dispatch = alert_engine._dispatch_alert
        dispatch_calls = []

        async def mock_dispatch(alert):
            dispatch_calls.append(alert)
            return await original_dispatch(alert)

        alert_engine._dispatch_alert = mock_dispatch

        # Send critical alert
        await alert_engine.send_alert(
            "critical_test",
            "Critical message",
            AlertPriority.CRITICAL,
        )

        # Give processing task time to run
        await asyncio.sleep(0.1)

        # Should have been dispatched
        assert len(dispatch_calls) == 1
        assert dispatch_calls[0].priority == AlertPriority.CRITICAL

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_processing_task_error_handling(self, alert_engine):
        """Test processing task handles errors gracefully."""
        await alert_engine.initialize()

        # Mock dispatch to raise error
        alert_engine._dispatch_alert = AsyncMock(side_effect=Exception("Test error"))

        with patch("src.auth.alert_engine.logger") as mock_logger:
            # Send alert that will trigger error
            await alert_engine.send_alert("test", "message")

            # Give processing task more time to handle error and log
            await asyncio.sleep(0.3)

            # Should log error but continue running
            mock_logger.error.assert_called()

        # Task should still be running
        assert not alert_engine._processing_task.done()

        # Cleanup
        await alert_engine.close()


class TestAlertEngineIntegration:
    """Integration tests for AlertEngine with full workflow."""

    @pytest.mark.asyncio
    async def test_complete_alert_workflow(self):
        """Test complete alert workflow from creation to dispatch."""
        alert_engine = AlertEngine(rate_limit=10, rate_window=60)

        # Mock all handlers to verify calls
        log_handler = AsyncMock()
        email_handler = AsyncMock()
        slack_handler = AsyncMock()

        await alert_engine.initialize()

        alert_engine._channel_handlers[AlertChannel.LOG] = log_handler
        alert_engine._channel_handlers[AlertChannel.EMAIL] = email_handler
        alert_engine._channel_handlers[AlertChannel.SLACK] = slack_handler

        # Send alert with multiple channels
        await alert_engine.send_alert(
            alert_type="security_incident",
            message="Multiple failed login attempts detected",
            priority=AlertPriority.HIGH,
            target="user@example.com",
            details={"attempts": 10, "source_ip": "192.168.1.100"},
            channels=[AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.SLACK],
        )

        # Give processing time
        await asyncio.sleep(0.2)

        # Verify alert was created and stored
        assert len(alert_engine._alert_history) == 1
        alert = alert_engine._alert_history[0]
        assert alert.alert_type == "security_incident"
        assert alert.priority == AlertPriority.HIGH
        assert alert.target == "user@example.com"
        assert alert.details["attempts"] == 10

        # Verify handlers were called
        log_handler.assert_called_once()
        email_handler.assert_called_once()
        slack_handler.assert_called_once()

        # Verify all handlers received the same alert
        log_alert = log_handler.call_args[0][0]
        email_alert = email_handler.call_args[0][0]
        slack_alert = slack_handler.call_args[0][0]

        assert log_alert.id == email_alert.id == slack_alert.id

        # Test statistics
        stats = await alert_engine.get_alert_stats()
        assert stats["total_alerts"] == 1
        assert stats["by_priority"]["high"] == 1
        assert stats["by_type"]["security_incident"] == 1

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_alert_engine_stress_test(self):
        """Test alert engine under load with many concurrent alerts."""
        alert_engine = AlertEngine(rate_limit=100, rate_window=60)
        await alert_engine.initialize()

        # Send many alerts concurrently
        tasks = []
        for i in range(50):
            task = alert_engine.send_alert(
                f"test_alert_{i % 5}",  # 5 different types
                f"Message {i}",
                AlertPriority.MEDIUM if i % 2 else AlertPriority.LOW,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed (within rate limit)
        assert all(results)

        # Give processing time
        await asyncio.sleep(0.5)

        # Check statistics
        stats = await alert_engine.get_alert_stats()
        assert stats["total_alerts"] == 50
        assert len(stats["by_type"]) == 5  # 5 different types

        # Cleanup
        await alert_engine.close()

    @pytest.mark.asyncio
    async def test_auto_initialization_on_send(self):
        """Test AlertEngine auto-initializes when sending first alert."""
        alert_engine = AlertEngine()

        # Should not be initialized
        assert not alert_engine._is_initialized

        # Send alert should trigger initialization
        result = await alert_engine.send_alert("test", "message")

        assert result is True
        assert alert_engine._is_initialized
        assert alert_engine._processing_task is not None

        # Cleanup
        await alert_engine.close()
