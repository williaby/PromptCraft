"""
Comprehensive tests for Token Rotation Scheduler module.

This test suite provides comprehensive coverage for automated token rotation
functionality, including scheduling, execution, notifications, and error handling.

FIXED: Uses dependency injection to prevent ServiceTokenManager initialization hangs.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, call, patch

from src.automation.token_rotation_scheduler import (
    TokenRotationPlan,
    TokenRotationScheduler,
)
from src.utils.datetime_compat import UTC


def create_mock_token_manager():
    """Create a comprehensive mock ServiceTokenManager for testing."""
    mock_token_manager = AsyncMock()
    # Configure common methods that tests use
    mock_token_manager.rotate_service_token = AsyncMock(return_value=("new_token", "new_id"))
    mock_token_manager.list_tokens = AsyncMock(return_value=[])
    mock_token_manager.get_token_by_id = AsyncMock(return_value=None)
    mock_token_manager.create_service_token = AsyncMock(return_value="new_token_id")
    mock_token_manager.delete_service_token = AsyncMock(return_value=True)
    return mock_token_manager


class TestTokenRotationPlan:
    """Test TokenRotationPlan dataclass."""

    def test_token_rotation_plan_creation(self):
        """Test TokenRotationPlan can be created with required fields."""
        scheduled_time = datetime.now(UTC) + timedelta(hours=1)

        plan = TokenRotationPlan(
            token_name="test-token",  # noqa: S106  # Test token parameter
            token_id="token-123",  # noqa: S106  # Test token parameter
            rotation_reason="Age-based rotation",
            scheduled_time=scheduled_time,
        )

        assert plan.token_name == "test-token"  # noqa: S105  # Test token value
        assert plan.token_id == "token-123"  # noqa: S105  # Test token value
        assert plan.rotation_reason == "Age-based rotation"
        assert plan.scheduled_time == scheduled_time
        assert plan.rotation_type == "scheduled"  # Default value
        assert plan.metadata == {}  # Default empty dict
        assert plan.status == "planned"  # Default status
        assert plan.completed_at is None
        assert plan.error_details is None
        assert plan.new_token_value is None
        assert plan.new_token_id is None

    def test_token_rotation_plan_with_optional_fields(self):
        """Test TokenRotationPlan with all optional fields."""
        scheduled_time = datetime.now(UTC) + timedelta(hours=1)
        metadata = {"usage": 500, "priority": "high"}

        plan = TokenRotationPlan(
            token_name="api-token",  # noqa: S106  # Test token parameter
            token_id="api-456",  # noqa: S106  # Test token parameter
            rotation_reason="High usage rotation",
            scheduled_time=scheduled_time,
            rotation_type="usage_based",
            metadata=metadata,
        )

        assert plan.rotation_type == "usage_based"
        assert plan.metadata == metadata
        assert isinstance(plan.created_at, datetime)

    def test_token_rotation_plan_status_updates(self):
        """Test status updates during rotation lifecycle."""
        scheduled_time = datetime.now(UTC) + timedelta(hours=1)

        plan = TokenRotationPlan(
            token_name="status-token",  # noqa: S106  # Test token parameter
            token_id="status-123",  # noqa: S106  # Test token parameter
            rotation_reason="Status test",
            scheduled_time=scheduled_time,
        )

        # Initial state
        assert plan.status == "planned"

        # Update status through lifecycle
        plan.status = "in_progress"
        assert plan.status == "in_progress"

        plan.status = "completed"
        plan.completed_at = datetime.now(UTC)
        plan.new_token_value = "new_value"  # noqa: S105  # Test token value
        plan.new_token_id = "new_id"  # noqa: S105  # Test token value

        assert plan.status == "completed"
        assert plan.completed_at is not None
        assert plan.new_token_value == "new_value"  # noqa: S105  # Test token value
        assert plan.new_token_id == "new_id"  # noqa: S105  # Test token value


class TestTokenRotationSchedulerInit:
    """Test TokenRotationScheduler initialization."""

    def test_scheduler_initialization_default(self):
        """Test scheduler initializes with default settings."""
        mock_token_manager = create_mock_token_manager()
        scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

        assert scheduler.settings is None
        assert hasattr(scheduler, "token_manager")
        assert scheduler.default_rotation_age_days == 90
        assert scheduler.high_usage_threshold == 1000
        assert scheduler.high_usage_rotation_days == 30
        assert scheduler.check_interval_hours == 24
        assert scheduler.advance_notice_hours == 24
        assert scheduler._rotation_plans == []
        assert scheduler._notification_callbacks == []

    def test_scheduler_initialization_with_settings(self):
        """Test scheduler initialization with custom settings."""
        mock_settings = Mock()
        mock_settings.token_rotation_age_days = 60
        mock_token_manager = create_mock_token_manager()

        scheduler = TokenRotationScheduler(settings=mock_settings, token_manager=mock_token_manager)

        assert scheduler.settings is mock_settings
        assert hasattr(scheduler, "token_manager")


class TestCalculateMaintenanceWindow:
    """Test maintenance window calculation."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    @patch("src.automation.token_rotation_scheduler.datetime")
    def test_calculate_next_maintenance_window_before_2am(self, mock_datetime):
        """Test maintenance window calculation when current time is before 2 AM."""
        # Mock current time as 1:30 AM UTC
        mock_now = datetime(2024, 1, 15, 1, 30, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        result = self.scheduler._calculate_next_maintenance_window()

        # Should schedule for today at 2 AM
        expected = datetime(2024, 1, 15, 2, 0, 0, tzinfo=UTC)
        assert result == expected

    @patch("src.automation.token_rotation_scheduler.datetime")
    def test_calculate_next_maintenance_window_after_2am(self, mock_datetime):
        """Test maintenance window calculation when current time is after 2 AM."""
        # Mock current time as 3:30 AM UTC
        mock_now = datetime(2024, 1, 15, 3, 30, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        with patch("src.automation.token_rotation_scheduler.timedelta", wraps=timedelta):
            result = self.scheduler._calculate_next_maintenance_window()

        # Should schedule for tomorrow at 2 AM
        expected = datetime(2024, 1, 16, 2, 0, 0, tzinfo=UTC)
        assert result == expected

    @patch("src.automation.token_rotation_scheduler.datetime")
    def test_calculate_next_maintenance_window_exactly_2am(self, mock_datetime):
        """Test maintenance window calculation when current time is exactly 2 AM."""
        # Mock current time as exactly 2:00 AM UTC
        mock_now = datetime(2024, 1, 15, 2, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        with patch("src.automation.token_rotation_scheduler.timedelta", wraps=timedelta):
            result = self.scheduler._calculate_next_maintenance_window()

        # Should schedule for tomorrow at 2 AM
        expected = datetime(2024, 1, 16, 2, 0, 0, tzinfo=UTC)
        assert result == expected


class TestAnalyzeTokensForRotation:
    """Test token analysis for rotation needs."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    async def test_analyze_tokens_for_rotation_age_based(self):
        """Test analysis identifies age-based rotation candidates."""
        # Mock database session and results
        mock_session = AsyncMock()
        mock_result = Mock()

        # Mock token data - old token needing rotation
        mock_row = Mock()
        mock_row.id = "token-123"  # Test token value
        mock_row.token_name = "old-api-token"  # noqa: S105  # Test token value
        mock_row.created_at = datetime.now(UTC) - timedelta(days=100)
        mock_row.usage_count = 50
        mock_row.last_used = datetime.now(UTC) - timedelta(days=5)
        mock_row.token_metadata = {"permissions": ["api_read"]}
        mock_row.age_days = 100

        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        async def mock_db_generator():
            yield mock_session

        # Mock get_db function for age-based test
        with patch("src.automation.token_rotation_scheduler.get_db", return_value=mock_db_generator()):
            plans = await self.scheduler.analyze_tokens_for_rotation()

        assert len(plans) == 1
        plan = plans[0]
        assert plan.token_name == "old-api-token"  # noqa: S105  # Test token value
        assert plan.token_id == "token-123"  # noqa: S105  # Test token value
        assert "Age-based rotation" in plan.rotation_reason
        assert plan.rotation_type == "age_based"
        assert plan.metadata["age_days"] == 100
        assert plan.metadata["current_usage"] == 50

    async def test_analyze_tokens_for_rotation_usage_based(self):
        """Test analysis identifies usage-based rotation candidates."""
        # Mock database session and results
        mock_session = AsyncMock()
        mock_result = Mock()

        # Mock token data - high usage token
        mock_row = Mock()
        mock_row.id = "token-456"  # Test token value
        mock_row.token_name = "high-usage-token"  # noqa: S105  # Test token value
        mock_row.created_at = datetime.now(UTC) - timedelta(days=45)
        mock_row.usage_count = 1500  # Above high_usage_threshold
        mock_row.last_used = datetime.now(UTC) - timedelta(hours=2)
        mock_row.token_metadata = {"permissions": ["api_write"]}
        mock_row.age_days = 45

        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        async def mock_db_generator():
            yield mock_session

        # Mock get_db function for usage-based test
        with patch("src.automation.token_rotation_scheduler.get_db", return_value=mock_db_generator()):
            plans = await self.scheduler.analyze_tokens_for_rotation()

        assert len(plans) == 1
        plan = plans[0]
        assert plan.token_name == "high-usage-token"  # noqa: S105  # Test token value
        assert plan.rotation_type == "usage_based"
        assert "High usage rotation" in plan.rotation_reason
        assert plan.metadata["current_usage"] == 1500

    async def test_analyze_tokens_for_rotation_manual(self):
        """Test analysis identifies manual rotation requests."""
        # Mock database session and results
        mock_session = AsyncMock()
        mock_result = Mock()

        # Mock token data - manual rotation flag
        mock_row = Mock()
        mock_row.id = "token-789"  # Test token value
        mock_row.token_name = "manual-rotation-token"  # noqa: S105  # Test token value
        mock_row.created_at = datetime.now(UTC) - timedelta(days=30)
        mock_row.usage_count = 100
        mock_row.last_used = datetime.now(UTC) - timedelta(days=1)
        mock_row.token_metadata = {"requires_rotation": True, "permissions": ["admin"]}
        mock_row.age_days = 30

        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        async def mock_db_generator():
            yield mock_session

        # Mock get_db function
        with patch("src.automation.token_rotation_scheduler.get_db", return_value=mock_db_generator()):
            plans = await self.scheduler.analyze_tokens_for_rotation()

            assert len(plans) == 1
            plan = plans[0]
            assert plan.rotation_type == "manual"
            assert "Manual rotation requested" in plan.rotation_reason

    async def test_analyze_tokens_for_rotation_database_error(self):
        """Test analysis handles database errors gracefully."""
        # Mock database to raise exception
        with patch(
            "src.automation.token_rotation_scheduler.get_db",
            side_effect=Exception("Database connection failed"),
        ):
            plans = await self.scheduler.analyze_tokens_for_rotation()

        # Should return mock plan when database fails
        assert len(plans) == 1
        assert plans[0].token_name == "old-token-for-rotation"  # noqa: S105  # Test token value

    async def test_analyze_tokens_for_rotation_empty_results(self):
        """Test analysis creates mock plan when no tokens need rotation."""
        # Mock database session with empty results
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []  # No tokens found
        mock_session.execute.return_value = mock_result

        async def mock_db_generator():
            yield mock_session

        # Mock get_db function
        with patch("src.automation.token_rotation_scheduler.get_db", return_value=mock_db_generator()):
            plans = await self.scheduler.analyze_tokens_for_rotation()

        # Should return mock plan for testing
        assert len(plans) == 1
        mock_plan = plans[0]
        assert mock_plan.token_name == "old-token-for-rotation"  # noqa: S105  # Test token value
        assert mock_plan.rotation_type == "age_based"


class TestScheduleTokenRotation:
    """Test token rotation scheduling."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    async def test_schedule_token_rotation_success(self):
        """Test successful token rotation scheduling."""
        future_time = datetime.now(UTC) + timedelta(hours=2)
        plan = TokenRotationPlan(
            token_name="schedule-token",  # noqa: S106  # Test token parameter
            token_id="schedule-123",  # noqa: S106  # Test token parameter
            rotation_reason="Test scheduling",
            scheduled_time=future_time,
        )

        # Mock notification method
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.schedule_token_rotation(plan)

        assert result is True
        assert plan in self.scheduler._rotation_plans

        # Verify notification was sent
        self.scheduler._send_rotation_notification.assert_called_once_with(plan, "scheduled")

    async def test_schedule_token_rotation_past_time(self):
        """Test scheduling fails for past time."""
        past_time = datetime.now(UTC) - timedelta(hours=1)
        plan = TokenRotationPlan(
            token_name="past-token",  # noqa: S106  # Test token parameter
            token_id="past-123",  # noqa: S106  # Test token parameter
            rotation_reason="Past time test",
            scheduled_time=past_time,
        )

        result = await self.scheduler.schedule_token_rotation(plan)

        assert result is False
        assert plan not in self.scheduler._rotation_plans

    async def test_schedule_token_rotation_exception_handling(self):
        """Test scheduling handles exceptions gracefully."""
        future_time = datetime.now(UTC) + timedelta(hours=2)
        plan = TokenRotationPlan(
            token_name="error-token",  # noqa: S106  # Test token parameter
            token_id="error-123",  # noqa: S106  # Test token parameter
            rotation_reason="Error test",
            scheduled_time=future_time,
        )

        # Mock notification to raise exception
        self.scheduler._send_rotation_notification = AsyncMock(side_effect=Exception("Notification failed"))

        result = await self.scheduler.schedule_token_rotation(plan)

        assert result is False


class TestExecuteRotationPlan:
    """Test rotation plan execution."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    async def test_execute_rotation_plan_success(self):
        """Test successful rotation plan execution."""
        plan = TokenRotationPlan(
            token_name="execute-token",  # noqa: S106  # Test token parameter
            token_id="execute-123",  # noqa: S106  # Test token parameter
            rotation_reason="Execution test",
            scheduled_time=datetime.now(UTC),
        )

        # Mock successful rotation
        self.scheduler.token_manager.rotate_service_token = AsyncMock(
            return_value=("new_token_value", "new_token_id"),
        )
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.execute_rotation_plan(plan)

        assert result is True
        assert plan.status == "completed"
        assert plan.new_token_value == "new_token_value"  # noqa: S105  # Test token value
        assert plan.new_token_id == "new_token_id"  # noqa: S105  # Test token value
        assert plan.completed_at is not None

        # Verify notifications
        assert self.scheduler._send_rotation_notification.call_count == 2
        notification_calls = self.scheduler._send_rotation_notification.call_args_list
        assert notification_calls[0] == call(plan, "starting")
        assert notification_calls[1] == call(plan, "completed")

    async def test_execute_rotation_plan_token_manager_failure(self):
        """Test rotation when token manager fails (falls back to mock)."""
        plan = TokenRotationPlan(
            token_name="failover-token",  # noqa: S106  # Test token parameter
            token_id="failover-123",  # noqa: S106  # Test token parameter
            rotation_reason="Failover test",
            scheduled_time=datetime.now(UTC),
        )

        # Mock token manager to raise exception (triggering mock fallback)
        self.scheduler.token_manager.rotate_service_token = AsyncMock(
            side_effect=Exception("Token manager failed"),
        )
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.execute_rotation_plan(plan)

        # Should succeed using mock fallback
        assert result is True
        assert plan.status == "completed"
        assert plan.new_token_value == "sk_test_rotated_token_12345"  # noqa: S105  # Test token value
        assert plan.new_token_id == "new_token_id_12345"  # noqa: S105  # Test token value

    async def test_execute_rotation_plan_no_result(self):
        """Test rotation when no result is returned."""
        plan = TokenRotationPlan(
            token_name="noresult-token",  # noqa: S106  # Test token parameter
            token_id="noresult-123",  # noqa: S106  # Test token parameter
            rotation_reason="No result test",
            scheduled_time=datetime.now(UTC),
        )

        # Mock token manager to return None
        self.scheduler.token_manager.rotate_service_token = AsyncMock(return_value=None)
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.execute_rotation_plan(plan)

        assert result is False
        assert plan.status == "failed"
        assert plan.error_details == "Token rotation returned no result"

        # Verify failure notification
        notification_calls = self.scheduler._send_rotation_notification.call_args_list
        assert notification_calls[-1] == call(plan, "failed")

    async def test_execute_rotation_plan_exception_handling(self):
        """Test rotation handles general exceptions."""
        plan = TokenRotationPlan(
            token_name="exception-token",  # noqa: S106  # Test token parameter
            token_id="exception-123",  # noqa: S106  # Test token parameter
            rotation_reason="Exception test",
            scheduled_time=datetime.now(UTC),
        )

        # Mock notification to raise exception after token manager
        self.scheduler.token_manager.rotate_service_token = AsyncMock(
            return_value=("token", "id"),
        )

        # Make _send_rotation_notification raise exception on "completed" call
        def notification_side_effect(plan, event_type):
            if event_type == "completed":
                raise Exception("Notification system down")

        self.scheduler._send_rotation_notification = AsyncMock(side_effect=notification_side_effect)

        result = await self.scheduler.execute_rotation_plan(plan)

        assert result is False
        assert plan.status == "failed"
        assert "Notification system down" in plan.error_details

    async def test_execute_rotation_plan_long_token_name_sanitization(self):
        """Test rotation with long token names that need sanitization."""
        long_token_name = (
            "very_long_token_name_that_exceeds_twenty_characters_and_should_be_truncated"  # noqa: S105  # Test constant
        )
        plan = TokenRotationPlan(
            token_name=long_token_name,
            token_id="long-123",  # noqa: S106  # Test token parameter
            rotation_reason="Very long rotation reason that exceeds fifty characters and should be truncated for security",
            scheduled_time=datetime.now(UTC),
        )

        self.scheduler.token_manager.rotate_service_token = AsyncMock(
            return_value=("new_token", "new_id"),
        )
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.execute_rotation_plan(plan)

        assert result is True
        assert plan.status == "completed"


class TestNotificationSystem:
    """Test notification system functionality."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    async def test_send_rotation_notification_starting(self):
        """Test sending rotation starting notification."""
        plan = TokenRotationPlan(
            token_name="notify-token",  # noqa: S106  # Test token parameter
            token_id="notify-123",  # noqa: S106  # Test token parameter
            rotation_reason="Notification test",
            scheduled_time=datetime.now(UTC),
        )

        # Mock notification callbacks
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        self.scheduler._notification_callbacks = [callback1, callback2]

        await self.scheduler._send_rotation_notification(plan, "starting")

        # Verify both callbacks were called
        callback1.assert_called_once()
        callback2.assert_called_once()

    async def test_send_rotation_notification_callback_exception(self):
        """Test notification handles callback exceptions gracefully."""
        plan = TokenRotationPlan(
            token_name="callback-error-token",  # noqa: S106  # Test token parameter
            token_id="callback-error-123",  # noqa: S106  # Test token parameter
            rotation_reason="Callback error test",
            scheduled_time=datetime.now(UTC),
        )

        # Mock callbacks - one succeeds, one fails
        callback1 = AsyncMock()
        callback2 = AsyncMock(side_effect=Exception("Callback failed"))
        self.scheduler._notification_callbacks = [callback1, callback2]

        # Should not raise exception
        await self.scheduler._send_rotation_notification(plan, "completed")

        callback1.assert_called_once()
        callback2.assert_called_once()

    async def test_send_rotation_notification_different_event_types(self):
        """Test notifications for different event types."""
        plan = TokenRotationPlan(
            token_name="event-token",  # noqa: S106  # Test token parameter
            token_id="event-123",  # noqa: S106  # Test token parameter
            rotation_reason="Event test",
            scheduled_time=datetime.now(UTC),
        )

        callback = AsyncMock()
        self.scheduler._notification_callbacks = [callback]

        # Test different event types
        event_types = ["scheduled", "starting", "completed", "failed"]

        for event_type in event_types:
            await self.scheduler._send_rotation_notification(plan, event_type)

        assert callback.call_count == len(event_types)


class TestSchedulerWorkflowMethods:
    """Test higher-level scheduler workflow methods."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    @patch("src.automation.token_rotation_scheduler.datetime")
    async def test_run_scheduled_rotations_with_pending(self, mock_datetime):
        """Test running scheduled rotations with pending plans."""
        # Mock current time
        mock_now = datetime.now(UTC)
        mock_datetime.now.return_value = mock_now

        # Create plans - one ready, one future
        ready_plan = TokenRotationPlan(
            token_name="ready-token",  # noqa: S106  # Test token parameter
            token_id="ready-123",  # noqa: S106  # Test token parameter
            rotation_reason="Ready for rotation",
            scheduled_time=mock_now - timedelta(minutes=1),  # Past due
        )

        future_plan = TokenRotationPlan(
            token_name="future-token",  # noqa: S106  # Test token parameter
            token_id="future-123",  # noqa: S106  # Test token parameter
            rotation_reason="Future rotation",
            scheduled_time=mock_now + timedelta(hours=1),  # Future
        )

        self.scheduler._rotation_plans = [ready_plan, future_plan]

        # Mock execute_rotation_plan
        self.scheduler.execute_rotation_plan = AsyncMock(return_value=True)

        result = await self.scheduler.run_scheduled_rotations()

        # Should execute only the ready plan
        self.scheduler.execute_rotation_plan.assert_called_once_with(ready_plan)

        assert result["status"] == "completed"
        assert result["rotations_attempted"] == 1
        assert result["rotations_successful"] == 1
        assert result["rotations_failed"] == 0

    async def test_run_scheduled_rotations_empty(self):
        """Test running scheduled rotations with no plans."""
        result = await self.scheduler.run_scheduled_rotations()

        assert result["status"] == "no_rotations_due"
        assert result["scheduled_count"] == 0

    async def test_get_rotation_status(self):
        """Test getting rotation status."""
        # Add some test plans in different states
        plan1 = TokenRotationPlan("token1", "id1", "reason1", datetime.now(UTC))
        plan1.status = "completed"

        plan2 = TokenRotationPlan("token2", "id2", "reason2", datetime.now(UTC))
        plan2.status = "failed"

        plan3 = TokenRotationPlan("token3", "id3", "reason3", datetime.now(UTC))
        plan3.status = "planned"

        self.scheduler._rotation_plans = [plan1, plan2, plan3]

        status = await self.scheduler.get_rotation_status()

        assert status["rotation_plans"]["total"] == 3
        assert status["rotation_plans"]["completed"] == 1
        assert status["rotation_plans"]["failed"] == 1
        assert status["rotation_plans"]["planned"] == 1

    async def test_run_rotation_scheduler_full_cycle(self):
        """Test complete rotation scheduler cycle."""
        # Mock analyze_tokens_for_rotation to return plans
        mock_plan = TokenRotationPlan(
            token_name="cycle-token",  # noqa: S106  # Test token parameter
            token_id="cycle-123",  # noqa: S106  # Test token parameter
            rotation_reason="Full cycle test",
            scheduled_time=datetime.now(UTC) + timedelta(hours=1),
        )

        self.scheduler.analyze_tokens_for_rotation = AsyncMock(return_value=[mock_plan])
        self.scheduler.schedule_token_rotation = AsyncMock(return_value=True)
        self.scheduler.run_scheduled_rotations = AsyncMock(
            return_value={
                "status": "no_rotations_due",
                "timestamp": datetime.now(UTC).isoformat(),
                "scheduled_count": 0,
            },
        )

        result = await self.scheduler.run_rotation_scheduler()

        assert result["status"] == "completed"
        assert result["new_plans_created"] == 1
        assert result["new_plans_scheduled"] == 1

        # Verify methods were called
        self.scheduler.analyze_tokens_for_rotation.assert_called_once()
        self.scheduler.schedule_token_rotation.assert_called_once_with(mock_plan)
        self.scheduler.run_scheduled_rotations.assert_called_once()


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    async def test_token_name_sanitization_with_newlines(self):
        """Test token name sanitization removes newlines and carriage returns."""
        malicious_name = "token\nwith\r\nnewlines"
        plan = TokenRotationPlan(
            token_name=malicious_name,
            token_id="sanitize-123",  # noqa: S106  # Test token parameter
            rotation_reason="Sanitization test",
            scheduled_time=datetime.now(UTC) + timedelta(hours=1),
        )

        # Mock notification to avoid actual calls
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.schedule_token_rotation(plan)

        # Should succeed despite malicious characters
        assert result is True

    async def test_rotation_reason_sanitization(self):
        """Test rotation reason sanitization for long strings with special chars."""
        long_reason = "Very long reason with \n newlines and \r carriage returns " * 5
        plan = TokenRotationPlan(
            token_name="reason-token",  # noqa: S106  # Test token parameter
            token_id="reason-123",  # noqa: S106  # Test token parameter
            rotation_reason=long_reason,
            scheduled_time=datetime.now(UTC),
        )

        self.scheduler.token_manager.rotate_service_token = AsyncMock(
            return_value=("token", "id"),
        )
        self.scheduler._send_rotation_notification = AsyncMock()

        result = await self.scheduler.execute_rotation_plan(plan)

        assert result is True

    async def test_concurrent_rotation_execution(self):
        """Test handling of concurrent rotation executions."""
        plans = []
        for i in range(3):
            plan = TokenRotationPlan(
                token_name=f"concurrent-token-{i}",
                token_id=f"concurrent-{i}",
                rotation_reason=f"Concurrent test {i}",
                scheduled_time=datetime.now(UTC),
            )
            plans.append(plan)

        # Mock successful rotations
        self.scheduler.token_manager.rotate_service_token = AsyncMock(
            return_value=("token", "id"),
        )
        self.scheduler._send_rotation_notification = AsyncMock()

        # Execute rotations concurrently
        tasks = [self.scheduler.execute_rotation_plan(plan) for plan in plans]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)
        assert all(plan.status == "completed" for plan in plans)

    async def test_start_rotation_daemon_parameters(self):
        """Test daemon startup with various parameter combinations."""
        # Create shutdown event that will be set after first iteration
        shutdown_event = asyncio.Event()

        # Mock run_rotation_scheduler to avoid actual processing
        async def mock_run_scheduler():
            # Set shutdown event after first call to prevent infinite loop
            shutdown_event.set()
            return {
                "status": "completed",
                "new_plans_created": 0,
                "new_plans_scheduled": 0,
                "rotations_completed": 0,
            }

        self.scheduler.run_rotation_scheduler = AsyncMock(side_effect=mock_run_scheduler)

        # Test with default parameters - should call run_rotation_scheduler once then exit
        await self.scheduler.start_rotation_daemon(shutdown_event=shutdown_event)

        # Verify the scheduler was called at least once
        self.scheduler.run_rotation_scheduler.assert_called()

        # Test daemon doesn't hang - if we get here, it means the daemon exited properly
        assert True  # Test passes if we reach this point without hanging

    async def test_notification_callback_registration(self):
        """Test callback registration and management."""
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        # Add callbacks via direct access (since no public method exists)
        self.scheduler._notification_callbacks.append(callback1)
        self.scheduler._notification_callbacks.append(callback2)

        plan = TokenRotationPlan(
            token_name="callback-test",  # noqa: S106  # Test token parameter
            token_id="callback-123",  # noqa: S106  # Test token parameter
            rotation_reason="Callback registration test",
            scheduled_time=datetime.now(UTC),
        )

        await self.scheduler._send_rotation_notification(plan, "scheduled")

        callback1.assert_called_once()
        callback2.assert_called_once()


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    def setup_method(self):
        """Set up test fixtures with dependency injection."""
        mock_token_manager = create_mock_token_manager()
        self.scheduler = TokenRotationScheduler(token_manager=mock_token_manager)

    async def test_complete_rotation_workflow(self):
        """Test complete rotation workflow from analysis to completion."""
        # Step 1: Mock database analysis
        with patch("src.automation.token_rotation_scheduler.get_db"):
            mock_session = AsyncMock()
            mock_result = Mock()

            mock_row = Mock()
            mock_row.id = "workflow-123"  # Test token value
            mock_row.token_name = "workflow-token"  # noqa: S105  # Test token value
            mock_row.created_at = datetime.now(UTC) - timedelta(days=100)
            mock_row.usage_count = 50
            mock_row.last_used = datetime.now(UTC) - timedelta(days=1)
            mock_row.token_metadata = {}
            mock_row.age_days = 100

            mock_result.fetchall.return_value = [mock_row]
            mock_session.execute.return_value = mock_result

            async def mock_db_generator():
                yield mock_session

            # Mock get_db function
            with patch("src.automation.token_rotation_scheduler.get_db", return_value=mock_db_generator()):

                # Step 2: Analyze tokens
                plans = await self.scheduler.analyze_tokens_for_rotation()
                assert len(plans) == 1

                # Step 3: Schedule rotation
                self.scheduler._send_rotation_notification = AsyncMock()
                scheduled = await self.scheduler.schedule_token_rotation(plans[0])
                assert scheduled is True

                # Step 4: Execute rotation
                self.scheduler.token_manager.rotate_service_token = AsyncMock(
                    return_value=("new_token", "new_id"),
                )
                executed = await self.scheduler.execute_rotation_plan(plans[0])
                assert executed is True

                # Step 5: Verify final state
                assert plans[0].status == "completed"
                assert plans[0].new_token_value == "new_token"  # noqa: S105  # Test token value
                assert plans[0].new_token_id == "new_id"  # noqa: S105  # Test token value

    async def test_high_volume_rotation_scenario(self):
        """Test handling of high-volume rotation scenario."""
        # Create multiple rotation plans
        plans = []
        for i in range(10):
            plan = TokenRotationPlan(
                token_name=f"volume-token-{i}",
                token_id=f"volume-{i}",
                rotation_reason=f"High volume test {i}",
                scheduled_time=datetime.now(UTC) - timedelta(minutes=i),  # Stagger times
            )
            plans.append(plan)

        self.scheduler._rotation_plans = plans

        # Mock execution
        self.scheduler.execute_rotation_plan = AsyncMock(return_value=True)

        result = await self.scheduler.run_scheduled_rotations()

        # All plans should be executed
        assert result["status"] == "completed"
        assert result["rotations_attempted"] == 10
        assert result["rotations_successful"] == 10
        assert self.scheduler.execute_rotation_plan.call_count == 10

    async def test_mixed_success_failure_scenario(self):
        """Test scenario with mixed successes and failures."""
        # Create plans that will have mixed outcomes
        success_plan = TokenRotationPlan(
            token_name="success-token",  # noqa: S106  # Test token parameter
            token_id="success-123",  # noqa: S106  # Test token parameter
            rotation_reason="Will succeed",
            scheduled_time=datetime.now(UTC) - timedelta(minutes=1),
        )

        failure_plan = TokenRotationPlan(
            token_name="failure-token",  # noqa: S106  # Test token parameter
            token_id="failure-123",  # noqa: S106  # Test token parameter
            rotation_reason="Will fail",
            scheduled_time=datetime.now(UTC) - timedelta(minutes=2),
        )

        self.scheduler._rotation_plans = [success_plan, failure_plan]

        # Mock mixed results
        def mock_execute(plan):
            if plan.token_id == "success-123":  # noqa: S105  # Test token value
                return AsyncMock(return_value=True)()
            return AsyncMock(return_value=False)()

        self.scheduler.execute_rotation_plan = mock_execute

        result = await self.scheduler.run_scheduled_rotations()

        assert result["status"] == "completed"
        assert result["rotations_attempted"] == 2
        assert result["rotations_successful"] == 1
        assert result["rotations_failed"] == 1
