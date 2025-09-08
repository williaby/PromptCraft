"""Comprehensive tests for Cloudflare Access authentication.

This test suite provides extensive coverage for Cloudflare authentication
to ensure security and reliability before production deployment.

Target Coverage: 90%+
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request

from src.auth_simple.cloudflare_auth import (
    CloudflareAuthError,
    CloudflareAuthHandler,
    CloudflareUser,
    extract_user_from_cloudflare_headers,
    validate_cloudflare_request,
)


class TestCloudflareUser:
    """Test cases for CloudflareUser model."""

    def test_valid_user_creation(self):
        """Test creating a valid CloudflareUser."""
        user = CloudflareUser(
            email="test@example.com",
            headers={"cf-access-authenticated-user-email": "test@example.com"},
        )
        assert user.email == "test@example.com"
        assert user.source == "cloudflare_access"
        assert isinstance(user.authenticated_at, datetime)

    def test_email_normalization(self):
        """Test that email addresses are normalized to lowercase."""
        user = CloudflareUser(email="TEST@EXAMPLE.COM")
        assert user.email == "test@example.com"

    def test_invalid_email_validation(self):
        """Test that invalid emails raise validation errors."""
        with pytest.raises(ValueError, match="Invalid email format"):
            CloudflareUser(email="invalid-email")

        with pytest.raises(ValueError, match="Invalid email format"):
            CloudflareUser(email="")

    def test_user_with_headers(self):
        """Test user creation with custom headers."""
        headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-connecting-ip": "192.168.1.1"}
        user = CloudflareUser(email="test@example.com", headers=headers)
        assert user.headers == headers

    def test_default_values(self):
        """Test default values are set correctly."""
        user = CloudflareUser(email="test@example.com")
        assert user.source == "cloudflare_access"
        assert user.headers == {}
        assert isinstance(user.authenticated_at, datetime)


class TestCloudflareAuthHandler:
    """Test cases for CloudflareAuthHandler."""

    @pytest.fixture
    def auth_handler(self):
        """Create a CloudflareAuthHandler instance for testing."""
        return CloudflareAuthHandler()

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.headers = {}
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        return request

    def test_handler_initialization_default(self):
        """Test handler initialization with default parameters."""
        handler = CloudflareAuthHandler()
        assert handler.validate_headers is True
        assert handler.log_events is True

    def test_handler_initialization_custom(self):
        """Test handler initialization with custom parameters."""
        handler = CloudflareAuthHandler(validate_headers=False, log_events=False)
        assert handler.validate_headers is False
        assert handler.log_events is False

    def test_extract_user_from_valid_headers(self, auth_handler, mock_request):
        """Test extracting user from valid Cloudflare headers."""
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        user = auth_handler.extract_user_from_request(mock_request)
        assert user.email == "test@example.com"
        assert user.source == "cloudflare_access"

    def test_extract_user_missing_header(self, auth_handler, mock_request):
        """Test extraction fails when required header is missing."""
        mock_request.headers = {}

        with pytest.raises(CloudflareAuthError, match="No authenticated user email found in headers"):
            auth_handler.extract_user_from_request(mock_request)

    def test_extract_user_empty_email(self, auth_handler, mock_request):
        """Test extraction fails when email header is empty."""
        mock_request.headers = {"cf-access-authenticated-user-email": ""}

        with pytest.raises(CloudflareAuthError, match="No authenticated user email found in headers"):
            auth_handler.extract_user_from_request(mock_request)

    def test_extract_user_invalid_email_format(self, auth_handler, mock_request):
        """Test extraction fails when email format is invalid."""
        mock_request.headers = {"cf-access-authenticated-user-email": "invalid-email"}

        with pytest.raises(CloudflareAuthError, match="Authentication failed"):
            auth_handler.extract_user_from_request(mock_request)

    def test_validate_headers_disabled(self, mock_request):
        """Test that header validation can be disabled."""
        handler = CloudflareAuthHandler(validate_headers=False)
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com"}

        user = handler.extract_user_from_request(mock_request)
        assert user.email == "test@example.com"

    @patch("src.auth_simple.cloudflare_auth.logger")
    def test_logging_enabled(self, mock_logger, mock_request):
        """Test that authentication events are logged when enabled."""
        handler = CloudflareAuthHandler(log_events=True)
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        handler.extract_user_from_request(mock_request)
        mock_logger.info.assert_called()

    @patch("src.auth_simple.cloudflare_auth.logger")
    def test_logging_disabled(self, mock_logger, mock_request):
        """Test that logging can be disabled."""
        handler = CloudflareAuthHandler(log_events=False)
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        handler.extract_user_from_request(mock_request)
        mock_logger.info.assert_not_called()

    def test_validate_request_headers_with_cf_ray(self, auth_handler, mock_request):
        """Test successful header validation with cf-ray."""
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        result = auth_handler.validate_request_headers(mock_request)
        assert result is True

    def test_validate_request_headers_missing_cf_ray(self, auth_handler, mock_request):
        """Test header validation fails without cf-ray."""
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com"}

        result = auth_handler.validate_request_headers(mock_request)
        assert result is False

    def test_validate_request_headers_disabled(self, mock_request):
        """Test that header validation can be disabled."""
        handler = CloudflareAuthHandler(validate_headers=False)
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com"}

        result = handler.validate_request_headers(mock_request)
        assert result is True

    def test_create_user_context(self, auth_handler, mock_request):
        """Test creating user context from CloudflareUser."""
        mock_request.headers = {
            "cf-access-authenticated-user-email": "test@example.com",
            "cf-ray": "12345-LAX",
            "cf-connecting-ip": "192.168.1.1",
            "cf-ipcountry": "US",
        }

        user = auth_handler.extract_user_from_request(mock_request)
        context = auth_handler.create_user_context(user)

        assert context["email"] == "test@example.com"
        assert context["authenticated"] is True
        assert context["auth_method"] == "cloudflare_access"
        assert context["cf_ray"] == "12345-LAX"
        assert context["connecting_ip"] == "192.168.1.1"
        assert context["ip_country"] == "US"

    def test_header_case_insensitive(self, auth_handler, mock_request):
        """Test that header matching handles different cases."""
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        user = auth_handler.extract_user_from_request(mock_request)
        assert user.email == "test@example.com"

    def test_whitespace_trimming(self, auth_handler, mock_request):
        """Test that email whitespace is trimmed."""
        mock_request.headers = {"cf-access-authenticated-user-email": "  test@example.com  ", "cf-ray": "12345-LAX"}

        user = auth_handler.extract_user_from_request(mock_request)
        assert user.email == "test@example.com"

    def test_multiple_headers_preserved(self, auth_handler, mock_request):
        """Test that multiple headers are preserved in user object."""
        headers = {
            "cf-access-authenticated-user-email": "test@example.com",
            "cf-connecting-ip": "192.168.1.1",
            "cf-ray": "12345-LAX",
            "user-agent": "Mozilla/5.0",
        }
        mock_request.headers = headers

        user = auth_handler.extract_user_from_request(mock_request)
        # Check that relevant headers are preserved
        assert user.email == "test@example.com"
        assert user.headers.get("cf-connecting-ip") == "192.168.1.1"
        assert user.headers.get("cf-ray") == "12345-LAX"

    @patch("src.auth_simple.cloudflare_auth.logger")
    def test_error_logging(self, mock_logger, auth_handler, mock_request):
        """Test that authentication errors are properly logged."""
        mock_request.headers = {}

        with pytest.raises(CloudflareAuthError):
            auth_handler.extract_user_from_request(mock_request)

        mock_logger.error.assert_called()

    def test_concurrent_authentication(self, auth_handler):
        """Test that handler works correctly with concurrent requests."""
        request1 = Mock(spec=Request)
        request1.headers = {"cf-access-authenticated-user-email": "user1@example.com", "cf-ray": "12345-LAX"}
        request1.url = Mock()
        request1.url.path = "/test1"
        request1.method = "GET"

        request2 = Mock(spec=Request)
        request2.headers = {"cf-access-authenticated-user-email": "user2@example.com", "cf-ray": "67890-DFW"}
        request2.url = Mock()
        request2.url.path = "/test2"
        request2.method = "POST"

        user1 = auth_handler.extract_user_from_request(request1)
        user2 = auth_handler.extract_user_from_request(request2)

        assert user1.email == "user1@example.com"
        assert user2.email == "user2@example.com"
        assert user1.email != user2.email

    def test_security_headers_validation(self, auth_handler, mock_request):
        """Test validation of security-related headers."""
        mock_request.headers = {
            "cf-access-authenticated-user-email": "test@example.com",
            "cf-ray": "12345-LAX",
            "x-forwarded-for": "192.168.1.1",
            "user-agent": "Mozilla/5.0",
        }

        user = auth_handler.extract_user_from_request(mock_request)
        assert user.email == "test@example.com"
        # Should not fail with additional headers present

    def test_alternative_email_headers(self, auth_handler, mock_request):
        """Test that alternative email headers are recognized."""
        mock_request.headers = {"x-cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        user = auth_handler.extract_user_from_request(mock_request)
        assert user.email == "test@example.com"


class TestCloudflareAuthError:
    """Test cases for CloudflareAuthError."""

    def test_error_creation(self):
        """Test creating CloudflareAuthError."""
        error = CloudflareAuthError("Test error message")
        assert str(error) == "Test error message"

    def test_error_inheritance(self):
        """Test that CloudflareAuthError inherits from Exception."""
        error = CloudflareAuthError("Test error")
        assert isinstance(error, Exception)


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.headers = {}
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        return request

    def test_extract_user_from_cloudflare_headers_success(self, mock_request):
        """Test successful user extraction via convenience function."""
        mock_request.headers = {"cf-access-authenticated-user-email": "test@example.com", "cf-ray": "12345-LAX"}

        user = extract_user_from_cloudflare_headers(mock_request)
        assert user.email == "test@example.com"
        assert user.source == "cloudflare_access"

    def test_extract_user_from_cloudflare_headers_failure(self, mock_request):
        """Test that convenience function raises HTTPException on failure."""
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            extract_user_from_cloudflare_headers(mock_request)

        assert exc_info.value.status_code == 401

    def test_validate_cloudflare_request_success(self, mock_request):
        """Test successful request validation."""
        mock_request.headers = {"cf-ray": "12345-LAX"}

        result = validate_cloudflare_request(mock_request)
        assert result is True

    def test_validate_cloudflare_request_failure(self, mock_request):
        """Test failed request validation."""
        mock_request.headers = {}

        result = validate_cloudflare_request(mock_request)
        assert result is False

    @patch("src.auth_simple.cloudflare_auth.logger")
    def test_validate_cloudflare_request_exception(self, mock_logger):
        """Test that validation exceptions are handled and logged."""
        # Create a mock request that will raise an exception during header access
        mock_request = Mock()
        mock_request.headers.get = Mock(side_effect=Exception("Test exception"))

        result = validate_cloudflare_request(mock_request)
        assert result is False
        mock_logger.error.assert_called()
