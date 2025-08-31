"""
Comprehensive unit tests for notification_handlers.py module.

Tests cover:
- WebhookHandler with retry logic and error handling
- EmailHandler with HTML/text templates
- SlackHandler with message formatting
- Template substitution and validation
- Session management and cleanup
- Configuration validation
- Network failures and edge cases

Target: >90% test coverage
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.auth.services.notification_handlers import (
    WebhookConfig,
    EmailConfig, 
    SlackConfig,
    WebhookHandler,
    EmailHandler,
    SlackHandler,
    create_notification_handlers,
)
from src.auth.services.alert_engine import SecurityAlert, AlertSeverity, AlertType


class TestWebhookConfig:
    """Test WebhookConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = WebhookConfig(url="https://example.com/webhook")
        assert config.url == "https://example.com/webhook"
        assert config.timeout_seconds == 5.0
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 1.0
        assert config.headers == {}
        assert config.auth_token is None
        assert config.custom_payload_template is None
        assert config.include_full_event_data is True
        
    def test_custom_values(self):
        """Test custom configuration values."""
        headers = {"Authorization": "Bearer token"}
        template = {"message": "{title}"}
        
        config = WebhookConfig(
            url="https://example.com/webhook",
            timeout_seconds=10.0,
            retry_attempts=5,
            retry_delay_seconds=2.0,
            headers=headers,
            auth_token="test_token",
            custom_payload_template=template,
            include_full_event_data=False
        )
        
        assert config.timeout_seconds == 10.0
        assert config.retry_attempts == 5
        assert config.retry_delay_seconds == 2.0
        assert config.headers == headers
        assert config.auth_token == "test_token"
        assert config.custom_payload_template == template
        assert config.include_full_event_data is False


class TestEmailConfig:
    """Test EmailConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"]
        )
        
        assert config.smtp_server == "smtp.test.com"
        assert config.username == "test@example.com"
        assert config.password == "password"
        assert config.from_address == "from@example.com"
        assert config.to_addresses == ["to@example.com"]
        assert config.smtp_port == 587
        assert config.use_tls is True
        assert config.cc_addresses == []
        
    def test_custom_values(self):
        """Test custom configuration values."""
        config = EmailConfig(
            smtp_server="smtp.custom.com",
            username="user@test.com",
            password="secret",
            from_address="sender@test.com",
            to_addresses=["recipient@test.com"],
            smtp_port=465,
            use_tls=False,
            cc_addresses=["cc@test.com"],
            subject_template="Alert: {alert_type}",
            html_template="<h1>{title}</h1>",
            text_template="{description}"
        )
        
        assert config.smtp_server == "smtp.custom.com"
        assert config.smtp_port == 465
        assert config.use_tls is False
        assert config.cc_addresses == ["cc@test.com"]
        assert config.subject_template == "Alert: {alert_type}"


class TestSlackConfig:
    """Test SlackConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = SlackConfig(webhook_url="https://hooks.slack.com/test")
        
        assert config.webhook_url == "https://hooks.slack.com/test"
        assert config.channel is None
        assert config.username == "Security Bot"
        assert config.icon_emoji == ":warning:"
        assert config.include_attachments is True
        assert AlertSeverity.LOW in config.color_map
        
    def test_custom_values(self):
        """Test custom configuration values."""
        color_map = {AlertSeverity.HIGH: "#ff0000"}
        
        config = SlackConfig(
            webhook_url="https://custom.slack.com/webhook",
            channel="#security",
            username="CustomBot",
            icon_emoji=":robot:",
            include_attachments=False,
            color_map=color_map
        )
        
        assert config.webhook_url == "https://custom.slack.com/webhook"
        assert config.channel == "#security"
        assert config.username == "CustomBot"
        assert config.icon_emoji == ":robot:"
        assert config.include_attachments is False
        assert config.color_map == color_map


class TestWebhookHandler:
    """Test WebhookHandler functionality."""
    
    @pytest.fixture
    def webhook_config(self):
        """Create webhook configuration for testing."""
        return WebhookConfig(
            url="https://example.com/webhook",
            timeout_seconds=5.0,
            retry_attempts=3,
            retry_delay_seconds=1.0
        )
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample security alert for testing."""
        return SecurityAlert(
            id="alert-123",
            alert_type=AlertType.SUSPICIOUS_LOGIN,
            severity=AlertSeverity.HIGH,
            title="Suspicious Login Detected",
            description="Multiple failed login attempts detected",
            timestamp=datetime.now(),
            affected_user="testuser",
            affected_ip="192.168.1.100",
            risk_score=75,
            rule_id="rule-001",
            triggering_events=[]
        )
    
    def test_init(self, webhook_config):
        """Test webhook handler initialization."""
        handler = WebhookHandler(webhook_config)
        assert handler.config == webhook_config
        assert handler.session is None
        
    @pytest.mark.asyncio
    async def test_successful_webhook_call(self, webhook_config, sample_alert):
        """Test successful webhook notification."""
        handler = WebhookHandler(webhook_config)
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await handler(sample_alert)
            
            assert result is True
            mock_post.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_webhook_retry_on_failure(self, webhook_config, sample_alert):
        """Test webhook retry logic on failure."""
        handler = WebhookHandler(webhook_config)
        
        mock_response = AsyncMock()
        mock_response.status = 500
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await handler(sample_alert)
            
            assert result is False
            assert mock_post.call_count == webhook_config.retry_attempts
            
    @pytest.mark.asyncio
    async def test_webhook_timeout_handling(self, webhook_config, sample_alert):
        """Test webhook timeout handling."""
        handler = WebhookHandler(webhook_config)
        
        with patch("aiohttp.ClientSession.post", side_effect=asyncio.TimeoutError()):
            result = await handler(sample_alert)
            
            assert result is False
            
    def test_build_payload_default(self, webhook_config, sample_alert):
        """Test building default payload."""
        handler = WebhookHandler(webhook_config)
        payload = handler._build_payload(sample_alert)
        
        assert payload["alert_id"] == "alert-123"
        assert payload["alert_type"] == "suspicious_login"
        assert payload["severity"] == "high"
        assert payload["title"] == "Suspicious Login Detected"
        
    def test_build_payload_custom_template(self, sample_alert):
        """Test building payload with custom template."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            custom_payload_template={"message": "{title} - {severity}"}
        )
        handler = WebhookHandler(config)
        
        payload = handler._build_payload(sample_alert)
        
        assert payload["message"] == "Suspicious Login Detected - high"
        
    def test_build_headers_default(self, webhook_config):
        """Test building default headers."""
        handler = WebhookHandler(webhook_config)
        headers = handler._build_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers
        
    def test_build_headers_with_auth_token(self, sample_alert):
        """Test building headers with auth token."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            auth_token="test_token"
        )
        handler = WebhookHandler(config)
        
        headers = handler._build_headers()
        
        assert headers["Authorization"] == "Bearer test_token"
        
    @pytest.mark.asyncio
    async def test_close_session(self, webhook_config):
        """Test closing HTTP session."""
        handler = WebhookHandler(webhook_config)
        
        mock_session = AsyncMock()
        handler.session = mock_session
        
        await handler.close()
        
        mock_session.close.assert_called_once()
        assert handler.session is None


class TestEmailHandler:
    """Test EmailHandler functionality."""
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration for testing."""
        return EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"]
        )
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample security alert for testing."""
        return SecurityAlert(
            id="alert-123",
            alert_type=AlertType.ACCOUNT_LOCKOUT,
            severity=AlertSeverity.CRITICAL,
            title="Account Locked",
            description="Account locked due to suspicious activity",
            timestamp=datetime.now(),
            affected_user="testuser",
            affected_ip="192.168.1.100",
            risk_score=90,
            rule_id="rule-002",
            triggering_events=[]
        )
    
    def test_init(self, email_config):
        """Test email handler initialization."""
        handler = EmailHandler(email_config)
        assert handler.config == email_config
        
    @pytest.mark.asyncio
    async def test_successful_email_send(self, email_config, sample_alert):
        """Test successful email sending."""
        handler = EmailHandler(email_config)
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            
            result = await handler(sample_alert)
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_email_smtp_exception(self, email_config, sample_alert):
        """Test email sending with SMTP exception."""
        handler = EmailHandler(email_config)
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")
            
            result = await handler(sample_alert)
            
            assert result is False
            
    def test_build_message_default_template(self, email_config, sample_alert):
        """Test building email message with default template."""
        handler = EmailHandler(email_config)
        message = handler._build_message(sample_alert)
        
        assert isinstance(message, MIMEMultipart)
        assert "Account Lockout" in message["Subject"]
        assert message["From"] == email_config.from_address
        assert message["To"] == ", ".join(email_config.to_addresses)
        
    def test_build_message_with_cc(self, sample_alert):
        """Test building email message with CC addresses."""
        config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"],
            cc_addresses=["cc@example.com"]
        )
        handler = EmailHandler(config)
        
        message = handler._build_message(sample_alert)
        
        assert message["Cc"] == "cc@example.com"
        
    def test_build_text_content_default(self, email_config, sample_alert):
        """Test building default text content."""
        handler = EmailHandler(email_config)
        content = handler._build_text_content(sample_alert)
        
        assert "SECURITY ALERT" in content
        assert "Account Locked" in content
        assert "testuser" in content
        assert "192.168.1.100" in content
        
    def test_build_text_content_custom_template(self, sample_alert):
        """Test building text content with custom template."""
        config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"],
            text_template="Alert: {title} for {affected_user}"
        )
        handler = EmailHandler(config)
        
        content = handler._build_text_content(sample_alert)
        
        assert content == "Alert: Account Locked for testuser"
        
    def test_build_html_content_default(self, email_config, sample_alert):
        """Test building default HTML content."""
        handler = EmailHandler(email_config)
        content = handler._build_html_content(sample_alert)
        
        assert "<!DOCTYPE html>" in content
        assert "Account Locked" in content
        assert "#dc3545" in content  # Critical severity color
        
    def test_build_html_content_custom_template(self, sample_alert):
        """Test building HTML content with custom template."""
        config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"],
            html_template="<div>{title}</div>"
        )
        handler = EmailHandler(config)
        
        content = handler._build_html_content(sample_alert)
        
        assert content == "<div>Account Locked</div>"
        
    def test_send_email_without_tls(self, sample_alert):
        """Test sending email without TLS."""
        config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"],
            use_tls=False
        )
        handler = EmailHandler(config)
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            
            # Call _send_email directly without mocking event loop
            handler._send_email(handler._build_message(sample_alert))
            
            mock_server.starttls.assert_not_called()  # TLS disabled
            mock_server.login.assert_called_once()


class TestSlackHandler:
    """Test SlackHandler functionality."""
    
    @pytest.fixture
    def slack_config(self):
        """Create Slack configuration for testing."""
        return SlackConfig(
            webhook_url="https://hooks.slack.com/test",
            channel="#security",
            username="SecurityBot"
        )
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample security alert for testing."""
        return SecurityAlert(
            id="alert-456",
            alert_type=AlertType.BRUTE_FORCE,
            severity=AlertSeverity.HIGH,
            title="Brute Force Attack",
            description="Multiple failed login attempts from same IP",
            timestamp=datetime.now(),
            affected_user="victim",
            affected_ip="10.0.0.1",
            risk_score=85,
            rule_id="rule-003",
            triggering_events=[]
        )
    
    def test_init(self, slack_config):
        """Test Slack handler initialization."""
        handler = SlackHandler(slack_config)
        assert handler.config == slack_config
        assert handler.session is None
        
    @pytest.mark.asyncio
    async def test_successful_slack_notification(self, slack_config, sample_alert):
        """Test successful Slack notification."""
        handler = SlackHandler(slack_config)
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await handler(sample_alert)
            
            assert result is True
            mock_post.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_slack_notification_failure(self, slack_config, sample_alert):
        """Test Slack notification failure."""
        handler = SlackHandler(slack_config)
        
        mock_response = AsyncMock()
        mock_response.status = 400
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await handler(sample_alert)
            
            assert result is False
            
    @pytest.mark.asyncio
    async def test_slack_network_exception(self, slack_config, sample_alert):
        """Test Slack notification with network exception."""
        handler = SlackHandler(slack_config)
        
        with patch("aiohttp.ClientSession.post", side_effect=Exception("Network error")):
            result = await handler(sample_alert)
            
            assert result is False
            
    def test_build_slack_payload_with_attachments(self, slack_config, sample_alert):
        """Test building Slack payload with attachments."""
        handler = SlackHandler(slack_config)
        payload = handler._build_slack_payload(sample_alert)
        
        assert payload["username"] == "SecurityBot"
        assert payload["icon_emoji"] == ":warning:"
        assert "Brute Force Attack" in payload["text"]
        assert "attachments" in payload
        
        attachment = payload["attachments"][0]
        assert attachment["color"] == "#fd7e14"  # High severity color
        assert attachment["title"] == "Brute Force Attack"
        
    def test_build_slack_payload_without_attachments(self, sample_alert):
        """Test building Slack payload without attachments."""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/test",
            include_attachments=False
        )
        handler = SlackHandler(config)
        
        payload = handler._build_slack_payload(sample_alert)
        
        assert "attachments" not in payload
        
    @pytest.mark.asyncio
    async def test_close_session(self, slack_config):
        """Test closing HTTP session."""
        handler = SlackHandler(slack_config)
        
        mock_session = AsyncMock()
        handler.session = mock_session
        
        await handler.close()
        
        mock_session.close.assert_called_once()
        assert handler.session is None


class TestCreateNotificationHandlers:
    """Test create_notification_handlers function."""
    
    def test_create_empty_handlers(self):
        """Test creating handlers with no configurations."""
        handlers = create_notification_handlers()
        assert handlers == []
        
    def test_create_webhook_handlers(self):
        """Test creating webhook handlers."""
        webhook_configs = [
            WebhookConfig(url="https://webhook1.com"),
            WebhookConfig(url="https://webhook2.com")
        ]
        
        handlers = create_notification_handlers(webhook_configs=webhook_configs)
        
        assert len(handlers) == 2
        assert all(isinstance(h, WebhookHandler) for h in handlers)
        
    def test_create_email_handler(self):
        """Test creating email handler."""
        email_config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"]
        )
        
        handlers = create_notification_handlers(email_config=email_config)
        
        assert len(handlers) == 1
        assert isinstance(handlers[0], EmailHandler)
        
    def test_create_slack_handler(self):
        """Test creating Slack handler."""
        slack_config = SlackConfig(webhook_url="https://hooks.slack.com/test")
        
        handlers = create_notification_handlers(slack_config=slack_config)
        
        assert len(handlers) == 1
        assert isinstance(handlers[0], SlackHandler)
        
    def test_create_all_handlers(self):
        """Test creating all types of handlers."""
        webhook_configs = [WebhookConfig(url="https://webhook.com")]
        email_config = EmailConfig(
            smtp_server="smtp.test.com",
            username="test@example.com",
            password="password",
            from_address="from@example.com",
            to_addresses=["to@example.com"]
        )
        slack_config = SlackConfig(webhook_url="https://hooks.slack.com/test")
        
        handlers = create_notification_handlers(
            webhook_configs=webhook_configs,
            email_config=email_config,
            slack_config=slack_config
        )
        
        assert len(handlers) == 3
        assert isinstance(handlers[0], WebhookHandler)
        assert isinstance(handlers[1], EmailHandler)
        assert isinstance(handlers[2], SlackHandler)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_template_substitution_with_none_values(self):
        """Test template substitution with None values."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            custom_payload_template={"user": "{affected_user}"}
        )
        handler = WebhookHandler(config)
        
        alert = SecurityAlert(
            id="alert-789",
            alert_type=AlertType.SUSPICIOUS_LOGIN,
            severity=AlertSeverity.LOW,
            title="Test Alert",
            description="Test description",
            timestamp=datetime.now(),
            affected_user=None,  # None value
            affected_ip=None,
            risk_score=10
        )
        
        payload = handler._build_payload(alert)
        
        assert payload["user"] == "unknown"  # Should substitute None with "unknown"
        
    def test_alert_severity_color_mapping(self):
        """Test alert severity to color mapping."""
        config = SlackConfig(webhook_url="https://hooks.slack.com/test")
        handler = SlackHandler(config)
        
        # Test all severity levels
        for severity in AlertSeverity:
            assert severity in config.color_map
            
        # Test default color for unknown severity
        payload = handler._build_slack_payload(
            SecurityAlert(
                id="test",
                alert_type=AlertType.SUSPICIOUS_LOGIN,
                severity=AlertSeverity.MEDIUM,
                title="Test",
                description="Test",
                timestamp=datetime.now()
            )
        )
        
        if config.include_attachments:
            attachment = payload["attachments"][0]
            assert attachment["color"] == "#ffaa00"  # Medium severity color
            
    @pytest.mark.asyncio
    async def test_concurrent_notifications(self):
        """Test concurrent notification sending."""
        config = WebhookConfig(url="https://example.com/webhook")
        handler = WebhookHandler(config)
        
        alerts = [
            SecurityAlert(
                id=f"alert-{i}",
                alert_type=AlertType.SUSPICIOUS_LOGIN,
                severity=AlertSeverity.LOW,
                title=f"Alert {i}",
                description=f"Description {i}",
                timestamp=datetime.now()
            )
            for i in range(5)
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Send notifications concurrently
            tasks = [handler(alert) for alert in alerts]
            results = await asyncio.gather(*tasks)
            
            assert all(result is True for result in results)
            assert mock_post.call_count == 5