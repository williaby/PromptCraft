"""Alert engine for security event notifications and incident response."""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.auth.database.security_events_postgres import SecurityEventsDatabase
from src.auth.security_logger import SecurityLogger

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels."""

    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


class Alert:
    """Security alert data structure."""

    def __init__(
        self,
        alert_type: str,
        message: str,
        priority: AlertPriority,
        target: str | None = None,
        details: dict[str, Any] | None = None,
        channels: list[AlertChannel] | None = None,
    ) -> None:
        """Initialize alert.

        Args:
            alert_type: Type of alert
            message: Alert message
            priority: Alert priority level
            target: Target of alert (IP, user, etc.)
            details: Additional alert details
            channels: Notification channels to use
        """
        self.alert_type = alert_type
        self.message = message
        self.priority = priority
        self.target = target
        self.details = details or {}
        self.channels = channels or [AlertChannel.LOG]
        self.timestamp = datetime.now(timezone.utc)
        self.id = f"{alert_type}_{target}_{self.timestamp.timestamp()}"


class AlertEngine:
    """Security alert engine for incident response and notifications."""

    def __init__(
        self,
        rate_limit: int = 10,
        rate_window: int = 60,
        default_channels: list[AlertChannel] | None = None,
    ) -> None:
        """Initialize alert engine.

        Args:
            rate_limit: Maximum alerts per window
            rate_window: Rate limit window in seconds
            default_channels: Default notification channels
        """
        self.rate_limit = rate_limit
        self.rate_window = rate_window
        self.default_channels = default_channels or [AlertChannel.LOG]

        # Initialize dependencies
        self._db = SecurityEventsDatabase()
        self._security_logger = SecurityLogger()

        # Alert tracking
        self._alert_history: list[Alert] = []
        self._alert_queue: asyncio.Queue = asyncio.Queue()
        self._channel_handlers: dict[AlertChannel, Callable] = {}
        self._processing_task: asyncio.Task | None = None
        self._is_initialized = False

        # Rate limiting
        self._alert_counts: dict[str, list[datetime]] = {}

    async def initialize(self) -> None:
        """Initialize the alert engine."""
        if self._is_initialized:
            return

        # Register default handlers
        self._register_default_handlers()

        # Start processing task
        self._processing_task = asyncio.create_task(self._process_alerts())

        self._is_initialized = True
        logger.info("AlertEngine initialized with rate_limit=%d/%ds", self.rate_limit, self.rate_window)

    def _register_default_handlers(self) -> None:
        """Register default channel handlers."""
        self._channel_handlers[AlertChannel.LOG] = self._log_handler
        self._channel_handlers[AlertChannel.EMAIL] = self._email_handler
        self._channel_handlers[AlertChannel.SLACK] = self._slack_handler
        self._channel_handlers[AlertChannel.WEBHOOK] = self._webhook_handler
        self._channel_handlers[AlertChannel.SMS] = self._sms_handler

    async def send_alert(
        self,
        alert_type: str,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        target: str | None = None,
        details: dict[str, Any] | None = None,
        channels: list[AlertChannel] | None = None,
    ) -> bool:
        """Send a security alert.

        Args:
            alert_type: Type of alert
            message: Alert message
            priority: Alert priority level
            target: Target of alert
            details: Additional details
            channels: Notification channels

        Returns:
            True if alert was queued successfully
        """
        if not self._is_initialized:
            await self.initialize()

        # Check rate limit
        if not await self._check_rate_limit(alert_type):
            logger.warning("Alert rate limit exceeded for type: %s", alert_type)
            return False

        # Create alert
        alert = Alert(
            alert_type=alert_type,
            message=message,
            priority=priority,
            target=target,
            details=details,
            channels=channels or self.default_channels,
        )

        # Queue alert
        await self._alert_queue.put(alert)

        # Track alert
        self._alert_history.append(alert)

        return True

    async def _check_rate_limit(self, alert_type: str) -> bool:
        """Check if alert is within rate limit.

        Args:
            alert_type: Type of alert

        Returns:
            True if within rate limit
        """
        now = datetime.now(timezone.utc)

        # Clean old entries
        if alert_type in self._alert_counts:
            cutoff = now.timestamp() - self.rate_window
            self._alert_counts[alert_type] = [ts for ts in self._alert_counts[alert_type] if ts.timestamp() > cutoff]
        else:
            self._alert_counts[alert_type] = []

        # Check limit
        if len(self._alert_counts[alert_type]) >= self.rate_limit:
            return False

        # Add new entry
        self._alert_counts[alert_type].append(now)
        return True

    async def _process_alerts(self) -> None:
        """Process queued alerts."""
        while True:
            try:
                # Get next alert
                alert = await self._alert_queue.get()

                # Process by priority
                if alert.priority == AlertPriority.CRITICAL:
                    # Process immediately
                    await self._dispatch_alert(alert)
                else:
                    # Add small delay for batching
                    await asyncio.sleep(0.1)
                    await self._dispatch_alert(alert)

            except asyncio.CancelledError:
                # Process remaining alerts before shutdown
                while not self._alert_queue.empty():
                    try:
                        alert = self._alert_queue.get_nowait()
                        await self._dispatch_alert(alert)
                    except asyncio.QueueEmpty:
                        break
                break
            except Exception as e:
                logger.error("Alert processing error: %s", e)

    async def _dispatch_alert(self, alert: Alert) -> None:
        """Dispatch alert to configured channels.

        Args:
            alert: Alert to dispatch
        """
        for channel in alert.channels:
            handler = self._channel_handlers.get(channel)
            if handler:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error("Alert dispatch error for channel %s: %s", channel, e)

    async def _log_handler(self, alert: Alert) -> None:
        """Log alert handler.

        Args:
            alert: Alert to log
        """
        level = logging.ERROR if alert.priority in [AlertPriority.HIGH, AlertPriority.CRITICAL] else logging.WARNING
        logger.log(
            level,
            "Security Alert: [%s] %s (target=%s, priority=%s)",
            alert.alert_type,
            alert.message,
            alert.target,
            alert.priority.value,
        )

    async def _email_handler(self, alert: Alert) -> None:
        """Email alert handler (placeholder).

        Args:
            alert: Alert to email
        """
        logger.info("Email alert: %s to configured recipients", alert.message)

    async def _slack_handler(self, alert: Alert) -> None:
        """Slack alert handler (placeholder).

        Args:
            alert: Alert to send to Slack
        """
        logger.info("Slack alert: %s to configured channel", alert.message)

    async def _webhook_handler(self, alert: Alert) -> None:
        """Webhook alert handler (placeholder).

        Args:
            alert: Alert to send via webhook
        """
        logger.info("Webhook alert: %s to configured endpoint", alert.message)

    async def _sms_handler(self, alert: Alert) -> None:
        """SMS alert handler (placeholder).

        Args:
            alert: Alert to send via SMS
        """
        logger.info("SMS alert: %s to configured numbers", alert.message)

    def register_channel_handler(self, channel: AlertChannel, handler: Callable) -> None:
        """Register a custom channel handler.

        Args:
            channel: Alert channel
            handler: Async handler function
        """
        self._channel_handlers[channel] = handler

    async def get_alert_history(
        self,
        limit: int = 100,
        priority: AlertPriority | None = None,
        alert_type: str | None = None,
    ) -> list[Alert]:
        """Get alert history.

        Args:
            limit: Maximum alerts to return
            priority: Filter by priority
            alert_type: Filter by alert type

        Returns:
            List of historical alerts
        """
        filtered = self._alert_history

        if priority:
            filtered = [a for a in filtered if a.priority == priority]

        if alert_type:
            filtered = [a for a in filtered if a.alert_type == alert_type]

        # Sort by timestamp desc and limit
        filtered.sort(key=lambda a: a.timestamp, reverse=True)
        return filtered[:limit]

    async def get_active_alerts(
        self,
        limit: int = 50,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Get active/recent alerts.

        Args:
            limit: Maximum alerts to return
            status: Filter by status (optional)

        Returns:
            Dictionary with alerts data
        """
        # Get recent alerts from history
        recent_alerts = await self.get_alert_history(limit=limit)
        
        # Filter by status if provided (for now, treat all alerts as active)
        if status and status != "active":
            recent_alerts = []
        
        # Convert alerts to dictionary format expected by endpoints
        alerts_data = []
        for alert in recent_alerts:
            alert_dict = {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "priority": alert.priority.value,
                "target": alert.target,
                "timestamp": alert.timestamp.isoformat(),
                "details": alert.details,
                "channels": [channel.value for channel in alert.channels],
            }
            alerts_data.append(alert_dict)
        
        return {
            "alerts": alerts_data,
            "total": len(alerts_data),
            "active_count": len([a for a in recent_alerts if True]),  # All are considered active for now
        }

    async def get_alert_stats(self) -> dict[str, Any]:
        """Get alert statistics.

        Returns:
            Alert statistics
        """
        stats = {
            "total_alerts": len(self._alert_history),
            "queued_alerts": self._alert_queue.qsize(),
            "by_priority": {},
            "by_type": {},
            "rate_limited_types": [],
        }

        # Count by priority
        for priority in AlertPriority:
            count = sum(1 for a in self._alert_history if a.priority == priority)
            stats["by_priority"][priority.value] = count

        # Count by type
        alert_types = {a.alert_type for a in self._alert_history}
        for alert_type in alert_types:
            count = sum(1 for a in self._alert_history if a.alert_type == alert_type)
            stats["by_type"][alert_type] = count

        # Check rate limited types
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - self.rate_window

        for alert_type, timestamps in self._alert_counts.items():
            recent = [ts for ts in timestamps if ts.timestamp() > cutoff]
            if len(recent) >= self.rate_limit:
                stats["rate_limited_types"].append(alert_type)

        return stats

    async def close(self) -> None:
        """Close the alert engine."""
        if self._processing_task:
            self._processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processing_task

        self._is_initialized = False
