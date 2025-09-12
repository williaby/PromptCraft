from src.utils.datetime_compat import utc_now


"""Comprehensive test suite for audit logging with enhanced coverage.

This module provides enhanced test coverage for src/security/audit_logging.py,
focusing on areas identified in the security testing review:
- Direct testing of _get_client_ip method
- Log content verification and inspection
- Edge cases with None values and missing fields
- JSON serialization and structured logging validation
"""

from datetime import datetime
from io import StringIO
import json
import logging
from unittest.mock import Mock, patch

from fastapi import Request

from src.security.audit_logging import (
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    AuditLogger,
    audit_logger_instance,
    log_api_request,
    log_authentication_failure,
    log_authentication_success,
    log_error_handler_triggered,
    log_rate_limit_exceeded,
    log_validation_failure,
)


class TestAuditEventClientIPExtraction:
    """Test the _get_client_ip method directly with comprehensive coverage."""

    def test_get_client_ip_x_forwarded_for_single_ip(self):
        """Test client IP extraction from X-Forwarded-For with single IP."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "192.168.1.100"}
        request.client.host = "10.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "192.168.1.100"

    def test_get_client_ip_x_forwarded_for_multiple_ips(self):
        """Test client IP extraction from X-Forwarded-For with multiple IPs (proxy chain)."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "203.0.113.1, 10.0.0.1, 192.168.1.100"}
        request.client.host = "127.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "203.0.113.1"  # First IP in chain (original client)

    def test_get_client_ip_x_forwarded_for_with_spaces(self):
        """Test client IP extraction from X-Forwarded-For with extra whitespace."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "  192.168.1.100  ,  10.0.0.1  "}
        request.client.host = "127.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "192.168.1.100"  # Should be stripped of whitespace

    def test_get_client_ip_x_real_ip_fallback(self):
        """Test client IP extraction fallback to X-Real-IP when X-Forwarded-For is not present."""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "203.0.113.50"}
        request.client.host = "10.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "203.0.113.50"

    def test_get_client_ip_x_forwarded_for_takes_precedence(self):
        """Test that X-Forwarded-For takes precedence over X-Real-IP."""
        request = Mock(spec=Request)
        request.headers = {
            "x-forwarded-for": "192.168.1.100",
            "x-real-ip": "203.0.113.50",
        }
        request.client.host = "10.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "192.168.1.100"  # X-Forwarded-For should win

    def test_get_client_ip_direct_client_fallback(self):
        """Test client IP extraction fallback to request.client.host when headers are missing."""
        request = Mock(spec=Request)
        request.headers = {}  # No proxy headers
        request.client.host = "127.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "127.0.0.1"

    def test_get_client_ip_no_client_object(self):
        """Test client IP extraction when request.client is None."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "unknown"

    def test_get_client_ip_case_insensitive_headers(self):
        """Test client IP extraction with different header casing."""
        request = Mock(spec=Request)
        # Mock headers object with proper get method
        headers_mock = Mock()
        headers_mock.get.side_effect = lambda key: {
            "x-forwarded-for": "192.168.1.100",
            "X-Forwarded-For": "192.168.1.100",
            "X-FORWARDED-FOR": "192.168.1.100",
        }.get(key)
        request.headers = headers_mock
        request.client.host = "10.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Test event",
            request=request,
        )

        result = event._get_client_ip(request)
        assert result == "192.168.1.100"


class TestAuditEventEdgeCases:
    """Test AuditEvent with edge cases and None values."""

    def test_audit_event_minimal_required_fields(self):
        """Test AuditEvent creation with only required fields."""
        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Minimal event",
        )

        event_dict = event.to_dict()

        # Required fields should be present
        assert event_dict["event_type"] == AuditEventType.API_REQUEST.value
        assert event_dict["severity"] == AuditEventSeverity.LOW.value
        assert event_dict["message"] == "Minimal event"
        assert "timestamp" in event_dict

        # Optional fields should not be present
        assert "user_id" not in event_dict
        assert "resource" not in event_dict
        assert "action" not in event_dict
        assert "outcome" not in event_dict
        assert "additional_data" not in event_dict
        assert "request" not in event_dict

    def test_audit_event_with_none_optional_fields(self):
        """Test AuditEvent creation with explicitly None optional fields."""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            severity=AuditEventSeverity.HIGH,
            message="Login failed",
            request=None,
            user_id=None,
            resource=None,
            action=None,
            outcome=None,
            additional_data=None,
        )

        event_dict = event.to_dict()

        # Should not raise errors and None fields should not be included
        assert event_dict["event_type"] == AuditEventType.AUTH_LOGIN_FAILURE.value
        assert event_dict["severity"] == AuditEventSeverity.HIGH.value
        assert event_dict["message"] == "Login failed"

        # None fields should not be in the output
        assert "user_id" not in event_dict
        assert "resource" not in event_dict
        assert "action" not in event_dict
        assert "outcome" not in event_dict
        assert "additional_data" not in event_dict
        assert "request" not in event_dict

    def test_audit_event_with_empty_additional_data(self):
        """Test AuditEvent with empty additional_data dict."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VALIDATION_FAILURE,
            severity=AuditEventSeverity.HIGH,
            message="Validation failed",
            additional_data={},  # Empty dict
        )

        event_dict = event.to_dict()

        # Empty dict should be included
        assert event_dict["additional_data"] == {}

    def test_audit_event_with_complex_additional_data(self):
        """Test AuditEvent with complex nested additional_data."""
        complex_data = {
            "error_details": {
                "code": "VALIDATION_ERROR",
                "fields": ["email", "password"],
                "counts": {"attempts": 3, "failures": 2},
            },
            "client_info": {
                "user_agent": "Mozilla/5.0",
                "platform": "web",
            },
            "metadata": [
                {"key": "session_id", "value": "abc123"},
                {"key": "request_id", "value": "req_456"},
            ],
        }

        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VALIDATION_FAILURE,
            severity=AuditEventSeverity.HIGH,
            message="Complex validation failure",
            additional_data=complex_data,
        )

        event_dict = event.to_dict()

        # Complex data should be preserved exactly
        assert event_dict["additional_data"] == complex_data
        assert event_dict["additional_data"]["error_details"]["code"] == "VALIDATION_ERROR"
        assert len(event_dict["additional_data"]["metadata"]) == 2

    def test_audit_event_timestamp_format(self):
        """Test that AuditEvent timestamps are in correct ISO format."""
        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Timestamp test",
        )

        event_dict = event.to_dict()

        # Should be able to parse the timestamp back
        timestamp_str = event_dict["timestamp"]
        parsed_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert isinstance(parsed_timestamp, datetime)

        # Should be recent (within last minute)
        time_diff = utc_now() - parsed_timestamp
        assert time_diff.total_seconds() < 60


class TestAuditLoggerContentVerification:
    """Test AuditLogger with log content verification and inspection."""

    def setup_method(self):
        """Set up test logging capture."""
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        # Add formatter to include log level in output
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        self.log_handler.setFormatter(formatter)
        self.logger = logging.getLogger("test_audit_logger")
        self.logger.handlers.clear()  # Clear any existing handlers
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.DEBUG)

    def test_log_event_critical_severity_content(self):
        """Test that CRITICAL events are logged with correct content and level."""
        audit_logger = AuditLogger()

        # Replace the logger with our test logger
        audit_logger.logger = self.logger

        event = AuditEvent(
            event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
            severity=AuditEventSeverity.CRITICAL,
            message="Suspicious login pattern detected",
            user_id="user123",
            resource="/api/admin",
            action="login",
            outcome="blocked",
            additional_data={"attempts": 5, "timeframe": "5 minutes"},
        )

        audit_logger.log_event(event)

        # Capture the logged content
        log_output = self.log_stream.getvalue()

        # Verify the log level and content
        assert "CRITICAL" in log_output
        assert "Suspicious login pattern detected" in log_output
        assert "user123" in log_output
        assert "/api/admin" in log_output
        assert "login" in log_output
        assert "blocked" in log_output

        # Verify JSON structure (if using JSON formatter)
        if log_output.strip().startswith("{"):
            log_data = json.loads(log_output.strip())
            assert log_data["message"] == "Suspicious login pattern detected"
            assert log_data["user_id"] == "user123"
            assert log_data["additional_data"]["attempts"] == 5

    def test_log_event_high_severity_content(self):
        """Test that HIGH events are logged with error level."""
        audit_logger = AuditLogger()
        audit_logger.logger = self.logger

        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            severity=AuditEventSeverity.HIGH,
            message="Authentication failed for user",
            user_id="user456",
            outcome="failure",
        )

        audit_logger.log_event(event)

        log_output = self.log_stream.getvalue()

        # Should use ERROR level for HIGH severity
        assert "ERROR" in log_output
        assert "Authentication failed for user" in log_output
        assert "user456" in log_output
        assert "failure" in log_output

    def test_log_event_medium_severity_content(self):
        """Test that MEDIUM events are logged with warning level."""
        audit_logger = AuditLogger()
        audit_logger.logger = self.logger

        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VALIDATION_FAILURE,
            severity=AuditEventSeverity.MEDIUM,
            message="Input validation failed",
            resource="/api/user/profile",
            action="update",
        )

        audit_logger.log_event(event)

        log_output = self.log_stream.getvalue()

        # Should use WARNING level for MEDIUM severity
        assert "WARNING" in log_output
        assert "Input validation failed" in log_output
        assert "/api/user/profile" in log_output
        assert "update" in log_output

    def test_log_event_low_severity_content(self):
        """Test that LOW events are logged with info level."""
        audit_logger = AuditLogger()
        audit_logger.logger = self.logger

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="API request processed",
            resource="/api/health",
            action="get",
            outcome="success",
        )

        audit_logger.log_event(event)

        log_output = self.log_stream.getvalue()

        # Should use INFO level for LOW severity
        assert "INFO" in log_output
        assert "API request processed" in log_output
        assert "/api/health" in log_output
        assert "get" in log_output
        assert "success" in log_output

    def test_log_authentication_event_content(self):
        """Test log_authentication_event produces correct log content."""
        audit_logger = AuditLogger()
        audit_logger.logger = self.logger

        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/auth/login"
        request.url.query = ""
        request.query_params = {}
        request.headers = {"user-agent": "test-browser"}
        request.client.host = "192.168.1.100"

        audit_logger.log_authentication_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            request,
            user_id="user789",
            outcome="success",
            additional_data={"session_id": "sess_abc123"},
        )

        log_output = self.log_stream.getvalue()

        # Verify all components are logged
        assert "user789" in log_output
        assert "success" in log_output
        assert "/auth/login" in log_output
        assert "192.168.1.100" in log_output
        assert "test-browser" in log_output
        assert "sess_abc123" in log_output

    def test_convenience_functions_log_content(self):
        """Test that convenience functions produce expected log content."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/test"
        request.url.query = "param=value"
        request.query_params = {"param": "value"}
        request.headers = {"user-agent": "test-agent", "x-forwarded-for": "203.0.113.1"}
        request.client.host = "127.0.0.1"

        # Capture logs from the global audit_logger_instance
        with patch.object(audit_logger_instance, "logger", self.logger):
            # Test log_authentication_success
            log_authentication_success(request, "user_success")

            # Test log_authentication_failure
            log_authentication_failure(request, "invalid_password")

            # Test log_rate_limit_exceeded
            log_rate_limit_exceeded(request, "100/hour")

            # Test log_validation_failure
            log_validation_failure(request, ["field1 required", "field2 invalid"])

            # Test log_error_handler_triggered
            log_error_handler_triggered(request, "ValueError", "Invalid input")

            # Test log_api_request
            log_api_request(request, 200, 0.150)

        log_output = self.log_stream.getvalue()

        # Verify all convenience functions logged appropriately
        assert "user_success" in log_output
        assert "invalid_password" in log_output
        assert "100/hour" in log_output
        assert "field1 required" in log_output
        assert "ValueError" in log_output
        assert "Invalid input" in log_output
        assert "203.0.113.1" in log_output  # X-Forwarded-For IP
        assert "0.15" in log_output  # Processing time

        # Should contain multiple log entries
        log_lines = [line for line in log_output.split("\n") if line.strip()]
        assert len(log_lines) >= 6  # At least one for each convenience function


class TestAuditLoggerEnvironmentIntegration:
    """Test AuditLogger integration with different environments."""

    def test_audit_logger_settings_integration(self):
        """Test that AuditLogger integrates properly with application settings."""
        audit_logger = AuditLogger()

        # Should have settings and logger initialized
        assert audit_logger.settings is not None
        assert audit_logger.logger is not None

        # Logger should be configured properly
        assert audit_logger.logger.name == "audit"

    def test_audit_logger_singleton_behavior(self):
        """Test that audit_logger_instance behaves as expected singleton."""
        # Should be the same instance
        assert audit_logger_instance is not None
        assert isinstance(audit_logger_instance, AuditLogger)

        # Should have same reference when imported multiple times
        from src.security.audit_logging import audit_logger_instance as second_import

        assert audit_logger_instance is second_import


class TestAuditEventRequestProcessing:
    """Test AuditEvent request processing with comprehensive scenarios."""

    def test_audit_event_with_complex_request(self):
        """Test AuditEvent with complex request containing various headers and data."""
        request = Mock(spec=Request)
        request.method = "PUT"
        request.url.path = "/api/users/123/profile"
        request.url.query = "include=avatar&format=json"
        request.query_params = {"include": "avatar", "format": "json"}
        request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "authorization": "Bearer token123",
            "content-type": "application/json",
            "x-forwarded-for": "203.0.113.195, 10.0.0.1",
            "x-real-ip": "203.0.113.195",
            "accept": "application/json",
            "referer": "https://app.example.com/profile",
        }
        request.client.host = "10.0.0.1"

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="User profile update",
            request=request,
            user_id="user_456",
            resource="/api/users/123/profile",
            action="update",
            outcome="success",
            additional_data={
                "fields_updated": ["name", "email", "avatar"],
                "update_size": "2.1KB",
            },
        )

        event_dict = event.to_dict()

        # Verify request information is captured correctly
        assert event_dict["request"]["method"] == "PUT"
        assert event_dict["request"]["path"] == "/api/users/123/profile"
        assert event_dict["request"]["query"] == "include=avatar&format=json"
        assert event_dict["request"]["user_agent"] == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert event_dict["request"]["client_ip"] == "203.0.113.195"  # From X-Forwarded-For

        # Verify all other fields
        assert event_dict["user_id"] == "user_456"
        assert event_dict["resource"] == "/api/users/123/profile"
        assert event_dict["action"] == "update"
        assert event_dict["outcome"] == "success"
        assert event_dict["additional_data"]["fields_updated"] == ["name", "email", "avatar"]

    def test_audit_event_request_with_missing_fields(self):
        """Test AuditEvent with request that has missing or incomplete fields."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/minimal"
        request.url.query = ""  # No query string
        request.query_params = {}
        request.headers = {}  # No headers
        request.client = None  # No client info

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditEventSeverity.LOW,
            message="Minimal request",
            request=request,
        )

        event_dict = event.to_dict()

        # Should handle missing fields gracefully
        assert event_dict["request"]["method"] == "GET"
        assert event_dict["request"]["path"] == "/api/minimal"
        assert event_dict["request"]["query"] == ""
        assert event_dict["request"]["user_agent"] == "unknown"
        assert event_dict["request"]["client_ip"] == "unknown"

        # Should not crash with missing client info
        assert "request" in event_dict


class TestAuditEventTypesCoverage:
    """Test comprehensive coverage of all audit event types and severities."""

    def test_all_audit_event_types_creation(self):
        """Test that all AuditEventType values can be used to create events."""
        all_event_types = [
            AuditEventType.API_REQUEST,
            AuditEventType.AUTH_LOGIN_SUCCESS,
            AuditEventType.AUTH_LOGIN_FAILURE,
            AuditEventType.AUTH_LOGOUT,
            AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED,
            AuditEventType.SECURITY_VALIDATION_FAILURE,
            AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
            AuditEventType.ADMIN_USER_CREATE,
            AuditEventType.ADMIN_USER_DELETE,
            AuditEventType.ADMIN_SYSTEM_STARTUP,
        ]

        for event_type in all_event_types:
            event = AuditEvent(
                event_type=event_type,
                severity=AuditEventSeverity.LOW,
                message=f"Test event for {event_type.value}",
            )

            event_dict = event.to_dict()
            assert event_dict["event_type"] == event_type.value

    def test_all_audit_event_severities_logging(self):
        """Test that all AuditEventSeverity values are handled correctly by logger."""
        audit_logger = AuditLogger()

        all_severities = [
            AuditEventSeverity.LOW,
            AuditEventSeverity.MEDIUM,
            AuditEventSeverity.HIGH,
            AuditEventSeverity.CRITICAL,
        ]

        with patch.object(audit_logger, "logger") as mock_logger:
            # Ensure mock is treated as standard logger (no bind method)
            del mock_logger.bind
            for severity in all_severities:
                # Reset mock calls for this iteration
                mock_logger.reset_mock()

                event = AuditEvent(
                    event_type=AuditEventType.API_REQUEST,
                    severity=severity,
                    message=f"Test event with {severity.value} severity",
                )

                audit_logger.log_event(event)

                # Verify the correct logging method was called
                if severity == AuditEventSeverity.CRITICAL:
                    mock_logger.critical.assert_called()
                elif severity == AuditEventSeverity.HIGH:
                    mock_logger.error.assert_called()
                elif severity == AuditEventSeverity.MEDIUM:
                    mock_logger.warning.assert_called()
                elif severity == AuditEventSeverity.LOW:
                    mock_logger.info.assert_called()
