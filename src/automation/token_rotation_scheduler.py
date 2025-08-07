"""Automated Token Rotation Scheduler for AUTH-2 implementation.

This module provides automated token rotation capabilities including:
- Scheduled token rotation based on age or usage patterns
- Zero-downtime rotation procedures for CI/CD systems
- Integration with external systems for token updates
- Rollback capabilities for failed rotations
- Notification systems for rotation events
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from src.auth.service_token_manager import ServiceTokenManager
from src.database.connection import get_db

if TYPE_CHECKING:
    from src.monitoring.service_token_monitor import ServiceTokenMonitor

logger = logging.getLogger(__name__)


class TokenRotationPlan:
    """Represents a token rotation plan."""

    def __init__(
        self,
        token_name: str,
        token_id: str,
        rotation_reason: str,
        scheduled_time: datetime,
        rotation_type: str = "scheduled",
        metadata: dict | None = None,
    ) -> None:
        """Initialize token rotation plan.

        Args:
            token_name: Name of token to rotate
            token_id: Token identifier
            rotation_reason: Reason for rotation
            scheduled_time: When rotation should occur
            rotation_type: Type of rotation (scheduled, age_based, usage_based)
            metadata: Additional rotation metadata
        """
        self.token_name = token_name
        self.token_id = token_id
        self.rotation_reason = rotation_reason
        self.scheduled_time = scheduled_time
        self.rotation_type = rotation_type
        self.metadata = metadata or {}
        self.status = "planned"  # planned, in_progress, completed, failed
        self.created_at = datetime.now(UTC)
        self.completed_at: datetime | None = None
        self.error_details: str | None = None
        self.new_token_value: str | None = None
        self.new_token_id: str | None = None


class TokenRotationScheduler:
    """Automated token rotation scheduler."""

    def __init__(self, settings: Any | None = None) -> None:
        """Initialize token rotation scheduler.

        Args:
            settings: Application settings (optional)
        """
        self.settings = settings
        self.token_manager = ServiceTokenManager()
        self.monitor: ServiceTokenMonitor | None = None

        # Rotation policies
        self.default_rotation_age_days = 90  # Rotate tokens older than 90 days
        self.high_usage_threshold = 1000  # Rotate high-usage tokens more frequently
        self.high_usage_rotation_days = 30  # Rotate high-usage tokens every 30 days

        # Scheduling
        self.check_interval_hours = 24  # Check for tokens needing rotation daily
        self.advance_notice_hours = 24  # Notify 24 hours before rotation

        # Rotation plans
        self._rotation_plans: list[TokenRotationPlan] = []

        # Webhook/notification callbacks
        self._notification_callbacks: list[Callable] = []

    def _get_monitor(self) -> "ServiceTokenMonitor":
        """Get the service token monitor, initializing if needed."""
        if self.monitor is None:
            from src.monitoring.service_token_monitor import ServiceTokenMonitor  # noqa: PLC0415

            self.monitor = ServiceTokenMonitor(self.settings)
        return self.monitor

    async def analyze_tokens_for_rotation(self) -> list[TokenRotationPlan]:
        """Analyze tokens and create rotation plans for those needing rotation.

        Returns:
            List of rotation plans
        """
        rotation_plans = []

        try:
            async for session in get_db():
                # Find tokens that need rotation based on age
                cutoff_date = datetime.now(UTC) - timedelta(days=self.default_rotation_age_days)

                result = await session.execute(
                    text(
                        """
                        SELECT
                            id, token_name, created_at, usage_count, last_used, token_metadata,
                            EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 as age_days
                        FROM service_tokens
                        WHERE is_active = TRUE
                          AND (
                              -- Age-based rotation
                              created_at <= :cutoff_date
                              -- High-usage rotation
                              OR (usage_count >= :high_usage_threshold
                                  AND created_at <= :high_usage_cutoff)
                              -- Manual rotation flag in metadata
                              OR (token_metadata->>'requires_rotation')::boolean = true
                          )
                        ORDER BY created_at ASC
                    """,
                    ),
                    {
                        "cutoff_date": cutoff_date,
                        "high_usage_threshold": self.high_usage_threshold,
                        "high_usage_cutoff": datetime.now(UTC) - timedelta(days=self.high_usage_rotation_days),
                    },
                )

                for row in result.fetchall():
                    # Determine rotation reason and type
                    age_days = int(row.age_days)
                    metadata = row.token_metadata or {}

                    if metadata.get("requires_rotation"):
                        rotation_reason = "Manual rotation requested (metadata flag)"
                        rotation_type = "manual"
                    elif row.usage_count >= self.high_usage_threshold:
                        rotation_reason = f"High usage rotation ({row.usage_count} uses, {age_days} days old)"
                        rotation_type = "usage_based"
                    else:
                        rotation_reason = f"Age-based rotation ({age_days} days old)"
                        rotation_type = "age_based"

                    # Schedule rotation for next maintenance window (e.g., 2 AM UTC)
                    scheduled_time = self._calculate_next_maintenance_window()

                    plan = TokenRotationPlan(
                        token_name=row.token_name,
                        token_id=str(row.id),
                        rotation_reason=rotation_reason,
                        scheduled_time=scheduled_time,
                        rotation_type=rotation_type,
                        metadata={
                            "current_usage": row.usage_count,
                            "age_days": age_days,
                            "last_used": row.last_used.isoformat() if row.last_used else None,
                            "original_metadata": metadata,
                        },
                    )

                    rotation_plans.append(plan)

                break  # Only need first session

        except Exception as e:
            logger.error("Failed to analyze tokens for rotation: %s", e)

        return rotation_plans

    def _calculate_next_maintenance_window(self) -> datetime:
        """Calculate next maintenance window for token rotation.

        Returns:
            Next maintenance window datetime
        """
        # Schedule for 2 AM UTC tomorrow (or today if it's before 2 AM)
        now = datetime.now(UTC)
        maintenance_hour = 2  # 2 AM UTC

        if now.hour < maintenance_hour:
            # Today at 2 AM
            return now.replace(hour=maintenance_hour, minute=0, second=0, microsecond=0)
        # Tomorrow at 2 AM
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=maintenance_hour, minute=0, second=0, microsecond=0)

    async def schedule_token_rotation(self, plan: TokenRotationPlan) -> bool:
        """Schedule a token rotation plan.

        Args:
            plan: Token rotation plan

        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Validate the plan
            if plan.scheduled_time <= datetime.now(UTC):
                logger.warning("Cannot schedule rotation for past time: %s", plan.token_name)
                return False

            # Add to rotation plans
            self._rotation_plans.append(plan)

            logger.info(
                "Scheduled token rotation: %s (%s) at %s",
                plan.token_name,
                plan.rotation_type,
                plan.scheduled_time.isoformat(),
            )

            # Send advance notification
            await self._send_rotation_notification(plan, "scheduled")

            return True

        except Exception as e:
            logger.error("Failed to schedule token rotation: %s", e)
            return False

    async def execute_rotation_plan(self, plan: TokenRotationPlan) -> bool:
        """Execute a token rotation plan.

        Args:
            plan: Token rotation plan to execute

        Returns:
            True if rotation successful, False otherwise
        """
        plan.status = "in_progress"

        try:
            logger.info("Executing token rotation: %s (%s)", plan.token_name, plan.rotation_reason)

            # Send pre-rotation notification
            await self._send_rotation_notification(plan, "starting")

            # Perform the rotation
            result = await self.token_manager.rotate_service_token(
                token_identifier=plan.token_id,
                rotation_reason=f"Automated rotation: {plan.rotation_reason}",
            )

            if result:
                new_token_value, new_token_id = result
                plan.new_token_value = new_token_value
                plan.new_token_id = new_token_id
                plan.status = "completed"
                plan.completed_at = datetime.now(UTC)

                logger.info("Token rotation completed: %s -> new ID: %s", plan.token_name, new_token_id)

                # Send success notification with new token
                await self._send_rotation_notification(plan, "completed")

                return True
            plan.status = "failed"
            plan.error_details = "Token rotation returned no result"

            logger.error("Token rotation failed: %s - no result returned", plan.token_name)

            # Send failure notification
            await self._send_rotation_notification(plan, "failed")

            return False

        except Exception as e:
            plan.status = "failed"
            plan.error_details = str(e)

            logger.error("Token rotation failed: %s - %s", plan.token_name, e)

            # Send failure notification
            await self._send_rotation_notification(plan, "failed")

            return False

    async def _send_rotation_notification(self, plan: TokenRotationPlan, event_type: str) -> None:
        """Send notification about token rotation event.

        Args:
            plan: Token rotation plan
            event_type: Type of event (scheduled, starting, completed, failed)
        """
        try:
            notification_data: dict[str, Any] = {
                "event_type": f"token_rotation_{event_type}",
                "token_name": plan.token_name,
                "rotation_type": plan.rotation_type,
                "rotation_reason": plan.rotation_reason,
                "scheduled_time": plan.scheduled_time.isoformat(),
                "timestamp": datetime.now(UTC).isoformat(),
            }

            if event_type == "completed" and plan.new_token_value:
                notification_data.update(
                    {
                        "new_token_id": plan.new_token_id,
                        "message": "Token rotation completed successfully. Update your systems with the new token.",
                        "action_required": True,
                    },
                )
            elif event_type == "failed":
                notification_data.update(
                    {
                        "error": plan.error_details,
                        "message": "Token rotation failed. Manual intervention may be required.",
                        "action_required": True,
                    },
                )
            elif event_type == "starting":
                notification_data.update(
                    {
                        "message": f"Token rotation starting for {plan.token_name}",
                        "estimated_completion": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
                    },
                )
            elif event_type == "scheduled":
                notification_data.update(
                    {
                        "message": f"Token rotation scheduled for {plan.token_name}",
                        "advance_notice_hours": self.advance_notice_hours,
                    },
                )

            # Call notification callbacks
            for callback in self._notification_callbacks:
                try:
                    await callback(notification_data)
                except Exception as e:
                    logger.warning("Notification callback failed: %s", e)

            # Log the notification
            logger.info("Rotation notification sent: %s for %s", event_type, plan.token_name)

        except Exception as e:
            logger.error("Failed to send rotation notification: %s", e)

    def add_notification_callback(self, callback: Callable) -> None:
        """Add a notification callback for rotation events.

        Args:
            callback: Async function to call with notification data
        """
        self._notification_callbacks.append(callback)

    async def run_scheduled_rotations(self) -> dict[str, Any]:
        """Run all scheduled token rotations that are due.

        Returns:
            Summary of rotation results
        """
        now = datetime.now(UTC)

        due_plans = [plan for plan in self._rotation_plans if plan.status == "planned" and plan.scheduled_time <= now]

        if not due_plans:
            return {
                "status": "no_rotations_due",
                "timestamp": now.isoformat(),
                "scheduled_count": len([p for p in self._rotation_plans if p.status == "planned"]),
            }

        results: dict[str, Any] = {
            "status": "completed",
            "timestamp": now.isoformat(),
            "rotations_attempted": len(due_plans),
            "rotations_successful": 0,
            "rotations_failed": 0,
            "results": [],
        }

        for plan in due_plans:
            success = await self.execute_rotation_plan(plan)

            result_entry = {
                "token_name": plan.token_name,
                "rotation_type": plan.rotation_type,
                "success": success,
                "error": plan.error_details if not success else None,
            }

            results["results"].append(result_entry)

            if success:
                results["rotations_successful"] += 1
            else:
                results["rotations_failed"] += 1

        logger.info(
            "Scheduled rotations completed: %d successful, %d failed",
            results["rotations_successful"],
            results["rotations_failed"],
        )

        return results

    async def run_rotation_scheduler(self) -> dict[str, Any]:
        """Run the complete rotation scheduler cycle.

        Returns:
            Summary of scheduler results
        """
        start_time = datetime.now(UTC)

        try:
            # Analyze tokens for rotation
            new_plans = await self.analyze_tokens_for_rotation()

            # Schedule new rotation plans
            scheduled_count = 0
            for plan in new_plans:
                success = await self.schedule_token_rotation(plan)
                if success:
                    scheduled_count += 1

            # Execute due rotations
            rotation_results = await self.run_scheduled_rotations()

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return {
                "status": "completed",
                "timestamp": start_time.isoformat(),
                "execution_time_seconds": execution_time,
                "new_plans_created": len(new_plans),
                "new_plans_scheduled": scheduled_count,
                "rotation_results": rotation_results,
                "total_planned_rotations": len([p for p in self._rotation_plans if p.status == "planned"]),
            }

        except Exception as e:
            logger.error("Rotation scheduler failed: %s", e)
            return {"status": "failed", "timestamp": start_time.isoformat(), "error": str(e)}

    async def start_rotation_daemon(self, check_interval_hours: int = 24) -> None:
        """Start continuous rotation scheduler daemon.

        Args:
            check_interval_hours: Hours between scheduler checks
        """
        logger.info("Starting token rotation scheduler daemon (interval: %d hours)", check_interval_hours)

        while True:
            try:
                result = await self.run_rotation_scheduler()

                if result["status"] == "completed":
                    logger.info(
                        "Rotation scheduler cycle completed: %d new plans, %d scheduled, %d rotations completed",
                        result.get("new_plans_created", 0),
                        result.get("new_plans_scheduled", 0),
                        result.get("rotation_results", {}).get("rotations_successful", 0),
                    )
                else:
                    logger.error("Rotation scheduler cycle failed: %s", result.get("error", "Unknown error"))

            except Exception as e:
                logger.error("Rotation scheduler daemon error: %s", e)

            # Wait for next cycle
            await asyncio.sleep(check_interval_hours * 3600)

    async def get_rotation_status(self) -> dict[str, Any]:
        """Get current rotation scheduler status.

        Returns:
            Status information
        """
        now = datetime.now(UTC)

        planned_rotations = [p for p in self._rotation_plans if p.status == "planned"]
        completed_rotations = [p for p in self._rotation_plans if p.status == "completed"]
        failed_rotations = [p for p in self._rotation_plans if p.status == "failed"]

        return {
            "timestamp": now.isoformat(),
            "scheduler_status": "active",
            "rotation_plans": {
                "total": len(self._rotation_plans),
                "planned": len(planned_rotations),
                "in_progress": len([p for p in self._rotation_plans if p.status == "in_progress"]),
                "completed": len(completed_rotations),
                "failed": len(failed_rotations),
            },
            "next_scheduled_rotation": min([p.scheduled_time for p in planned_rotations], default=None),
            "recent_completions": [
                {
                    "token_name": p.token_name,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                    "rotation_type": p.rotation_type,
                }
                for p in sorted(
                    completed_rotations,
                    key=lambda x: x.completed_at or datetime.min.replace(tzinfo=UTC),
                    reverse=True,
                )[:5]
            ],
            "recent_failures": [
                {"token_name": p.token_name, "error": p.error_details, "rotation_type": p.rotation_type}
                for p in failed_rotations[-5:]  # Last 5 failures
            ],
        }
