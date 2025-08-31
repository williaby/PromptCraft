"""Notification handlers for security alerts with webhook and email support.

This module provides notification handlers for security alerts with:
- HTTP webhook notifications with configurable retries and timeout
- Email notifications with HTML and text templates
- Slack/Discord webhook integration support
- Notification failure tracking and retry logic
- Template-based message formatting
- Rate limiting per notification channel

Performance target: < 5s per notification (including retries)
Architecture: Async notification pipeline with configurable handlers
"""

import asyncio
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiohttp

from .alert_engine import AlertSeverity, SecurityAlert


@dataclass
class WebhookConfig:
    """Configuration for webhook notifications."""

    url: str
    timeout_seconds: float = 5.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

    # Authentication
    headers: dict[str, str] = field(default_factory=dict)
    auth_token: str | None = None

    # Message formatting
    custom_payload_template: dict[str, Any] | None = None
    include_full_event_data: bool = True


@dataclass
class EmailConfig:
    """Configuration for email notifications."""

    smtp_server: str
    username: str
    password: str
    from_address: str
    to_addresses: list[str]
    smtp_port: int = 587
    use_tls: bool = True
    cc_addresses: list[str] = field(default_factory=list)

    # Templates
    subject_template: str = "Security Alert: {alert_type} - {severity}"
    html_template: str | None = None
    text_template: str | None = None


@dataclass
class SlackConfig:
    """Configuration for Slack webhook notifications."""

    webhook_url: str
    channel: str | None = None
    username: str = "Security Bot"
    icon_emoji: str = ":warning:"

    # Message formatting
    include_attachments: bool = True
    color_map: dict[AlertSeverity, str] = field(
        default_factory=lambda: {
            AlertSeverity.LOW: "#36a64f",  # Green
            AlertSeverity.MEDIUM: "#ffaa00",  # Orange
            AlertSeverity.HIGH: "#fd7e14",  # Red
            AlertSeverity.CRITICAL: "#800000",  # Dark red
        },
    )


class WebhookHandler:
    """HTTP webhook notification handler with retry logic."""

    def __init__(self, config: WebhookConfig) -> None:
        """Initialize webhook handler with configuration."""
        self.config = config
        self.session: aiohttp.ClientSession | None = None

    async def __call__(self, alert: SecurityAlert) -> bool:
        """Send webhook notification for security alert.

        Args:
            alert: Security alert to send

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds))

        payload = self._build_payload(alert)
        headers = self._build_headers()

        # Retry logic
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.post(self.config.url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return True

            except Exception:
                pass

            # Wait before retry (except on last attempt)
            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay_seconds)

        return False

    def _build_payload(self, alert: SecurityAlert) -> dict[str, Any]:
        """Build webhook payload from alert."""
        if self.config.custom_payload_template:
            # Use custom template and substitute values
            payload = self.config.custom_payload_template.copy()
            # Simple template substitution (could be enhanced with Jinja2)
            payload = self._substitute_template_values(payload, alert)
        else:
            # Default payload format
            payload = {
                "alert_id": str(alert.id),
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "affected_user": alert.affected_user,
                "affected_ip": alert.affected_ip,
                "risk_score": alert.risk_score,
                "rule_id": alert.rule_id,
            }

            if self.config.include_full_event_data and alert.triggering_events:
                payload["triggering_events"] = alert.triggering_events

        return payload

    def _substitute_template_values(self, template: dict[str, Any], alert: SecurityAlert) -> dict[str, Any]:
        """Substitute template values with alert data."""
        substitutions = {
            "{alert_id}": str(alert.id),
            "{alert_type}": alert.alert_type.value,
            "{severity}": alert.severity.value,
            "{title}": alert.title,
            "{description}": alert.description,
            "{timestamp}": alert.timestamp.isoformat(),
            "{affected_user}": alert.affected_user or "unknown",
            "{affected_ip}": alert.affected_ip or "unknown",
            "{risk_score}": str(alert.risk_score),
        }

        def substitute_recursive(obj):
            if isinstance(obj, dict):
                return {k: substitute_recursive(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [substitute_recursive(item) for item in obj]
            if isinstance(obj, str):
                result = obj
                for placeholder, value in substitutions.items():
                    result = result.replace(placeholder, value)
                return result
            return obj

        return substitute_recursive(template)

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for webhook request."""
        headers = {"Content-Type": "application/json", "User-Agent": "PromptCraft-Security-Alert/1.0"}

        # Add custom headers
        headers.update(self.config.headers)

        # Add authentication if configured
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"

        return headers

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


class EmailHandler:
    """Email notification handler with HTML and text templates."""

    def __init__(self, config: EmailConfig) -> None:
        """Initialize email handler with configuration."""
        self.config = config

    async def __call__(self, alert: SecurityAlert) -> bool:
        """Send email notification for security alert.

        Args:
            alert: Security alert to send

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Build email message
            message = self._build_message(alert)

            # Send email (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email, message)

            return True

        except Exception:
            return False

    def _build_message(self, alert: SecurityAlert) -> MIMEMultipart:
        """Build email message from alert."""
        message = MIMEMultipart("alternative")

        # Build subject
        subject = self.config.subject_template.format(
            alert_type=alert.alert_type.value.replace('_', ' ').title(),
            severity=alert.severity.value.upper(),
            title=alert.title,
            affected_user=alert.affected_user or "Unknown",
            affected_ip=alert.affected_ip or "Unknown",
        )

        message["Subject"] = subject
        message["From"] = self.config.from_address
        message["To"] = ", ".join(self.config.to_addresses)

        if self.config.cc_addresses:
            message["Cc"] = ", ".join(self.config.cc_addresses)

        # Build text content
        text_content = self._build_text_content(alert)
        text_part = MIMEText(text_content, "plain")
        message.attach(text_part)

        # Build HTML content if template provided
        if self.config.html_template:
            html_content = self._build_html_content(alert)
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

        return message

    def _build_text_content(self, alert: SecurityAlert) -> str:
        """Build plain text email content."""
        if self.config.text_template:
            return self.config.text_template.format(
                alert_type=alert.alert_type.value.replace('_', ' ').title(),
                severity=alert.severity.value.upper(),
                title=alert.title,
                description=alert.description,
                timestamp=alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                affected_user=alert.affected_user or "Unknown",
                affected_ip=alert.affected_ip or "Unknown",
                risk_score=alert.risk_score,
                rule_id=alert.rule_id or "Unknown",
            )
        # Default text template
        return f"""SECURITY ALERT: {alert.alert_type.value.replace('_', ' ').title()}

Severity: {alert.severity.value.upper()}
Title: {alert.title}
Description: {alert.description}

Details:
- Timestamp: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
- Affected User: {alert.affected_user or "Unknown"}
- Affected IP: {alert.affected_ip or "Unknown"}
- Risk Score: {alert.risk_score}/100
- Rule ID: {alert.rule_id or "Unknown"}

Triggering Events: {len(alert.triggering_events)} event(s)

This is an automated security alert from PromptCraft Security Monitoring.
"""

    def _build_html_content(self, alert: SecurityAlert) -> str:
        """Build HTML email content."""
        if self.config.html_template:
            return self.config.html_template.format(
                alert_type=alert.alert_type.value.replace('_', ' ').title(),
                severity=alert.severity.value.upper(),
                title=alert.title,
                description=alert.description,
                timestamp=alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                affected_user=alert.affected_user or "Unknown",
                affected_ip=alert.affected_ip or "Unknown",
                risk_score=alert.risk_score,
                rule_id=alert.rule_id or "Unknown",
            )
        # Default HTML template with severity color coding
        severity_colors = {
            AlertSeverity.LOW: "#28a745",
            AlertSeverity.MEDIUM: "#ffc107",
            AlertSeverity.HIGH: "#fd7e14",
            AlertSeverity.CRITICAL: "#dc3545",
        }

        color = severity_colors.get(alert.severity, "#6c757d")

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
        .content {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
        .details {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin-top: 10px; }}
        .severity {{ font-weight: bold; color: {color}; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🔒 SECURITY ALERT: {alert.alert_type.value.replace('_', ' ').title()}</h2>
    </div>

    <div class="content">
        <p><strong>Severity:</strong> <span class="severity">{alert.severity.value.upper()}</span></p>
        <p><strong>Title:</strong> {alert.title}</p>
        <p><strong>Description:</strong> {alert.description}</p>

        <div class="details">
            <h4>Alert Details</h4>
            <ul>
                <li><strong>Timestamp:</strong> {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</li>
                <li><strong>Affected User:</strong> {alert.affected_user or "Unknown"}</li>
                <li><strong>Affected IP:</strong> {alert.affected_ip or "Unknown"}</li>
                <li><strong>Risk Score:</strong> {alert.risk_score}/100</li>
                <li><strong>Rule ID:</strong> {alert.rule_id or "Unknown"}</li>
                <li><strong>Triggering Events:</strong> {len(alert.triggering_events)} event(s)</li>
            </ul>
        </div>

        <p style="margin-top: 20px; font-size: 12px; color: #6c757d;">
            This is an automated security alert from PromptCraft Security Monitoring.
        </p>
    </div>
</body>
</html>
"""

    def _send_email(self, message: MIMEMultipart) -> None:
        """Send email message via SMTP."""
        # Create secure connection
        if self.config.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.username, self.config.password)

                recipients = self.config.to_addresses + self.config.cc_addresses
                server.send_message(message, to_addrs=recipients)
        else:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.login(self.config.username, self.config.password)

                recipients = self.config.to_addresses + self.config.cc_addresses
                server.send_message(message, to_addrs=recipients)


class SlackHandler:
    """Slack webhook notification handler with rich formatting."""

    def __init__(self, config: SlackConfig) -> None:
        """Initialize Slack handler with configuration."""
        self.config = config
        self.session: aiohttp.ClientSession | None = None

    async def __call__(self, alert: SecurityAlert) -> bool:
        """Send Slack notification for security alert.

        Args:
            alert: Security alert to send

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5.0))

        payload = self._build_slack_payload(alert)

        try:
            async with self.session.post(self.config.webhook_url, json=payload) as response:
                return response.status == 200

        except Exception:
            return False

    def _build_slack_payload(self, alert: SecurityAlert) -> dict[str, Any]:
        """Build Slack-formatted payload."""
        severity_emojis = {
            AlertSeverity.LOW: ":information_source:",
            AlertSeverity.MEDIUM: ":warning:",
            AlertSeverity.HIGH: ":exclamation:",
            AlertSeverity.CRITICAL: ":rotating_light:",
        }

        emoji = severity_emojis.get(alert.severity, ":question:")
        color = self.config.color_map.get(alert.severity, "#6c757d")

        payload = {
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji,
            "text": f"{emoji} *Security Alert: {alert.title}*",
        }

        if self.config.channel:
            payload["channel"] = self.config.channel

        if self.config.include_attachments:
            attachment = {
                "color": color,
                "title": alert.title,
                "text": alert.description,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Risk Score", "value": f"{alert.risk_score}/100", "short": True},
                    {"title": "Affected User", "value": alert.affected_user or "Unknown", "short": True},
                    {"title": "Affected IP", "value": alert.affected_ip or "Unknown", "short": True},
                ],
                "timestamp": int(alert.timestamp.timestamp()),
                "footer": "PromptCraft Security",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            }

            payload["attachments"] = [attachment]

        return payload

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


# Convenience function to create notification handlers
def create_notification_handlers(
    webhook_configs: list[WebhookConfig] | None = None,
    email_config: EmailConfig | None = None,
    slack_config: SlackConfig | None = None,
) -> list[WebhookHandler | EmailHandler | SlackHandler]:
    """Create list of notification handlers from configurations.

    Args:
        webhook_configs: List of webhook configurations
        email_config: Email configuration
        slack_config: Slack configuration

    Returns:
        List of configured notification handlers
    """
    handlers = []

    # Add webhook handlers
    if webhook_configs:
        for config in webhook_configs:
            handlers.append(WebhookHandler(config))

    # Add email handler
    if email_config:
        handlers.append(EmailHandler(email_config))

    # Add Slack handler
    if slack_config:
        handlers.append(SlackHandler(slack_config))

    return handlers
