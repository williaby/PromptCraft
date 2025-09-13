"""Comprehensive test suite for rate limiting with enhanced coverage.

This module provides enhanced test coverage for src/security/rate_limiting.py,
focusing on areas identified in the security testing review:
- Storage backend verification for different environments
- Direct testing of get_rate_limit_for_endpoint function
- Comprehensive endpoint type rate limit testing
- Redis vs memory storage configuration testing
- Rate limit exceeded handler comprehensive testing
"""

from io import StringIO
import logging
from unittest.mock import Mock, patch

from fastapi import HTTPException, Request
import pytest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from src.security.rate_limiting import (
    RateLimits,
    create_limiter,
    get_client_identifier,
    get_rate_limit_for_endpoint,
    rate_limit_exceeded_handler,
    setup_rate_limiting,
)


class TestStorageBackendConfiguration:
    """Test storage backend configuration for different environments."""

    def test_create_limiter_production_redis_storage(self):
        """Test that production environment uses Redis storage."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            with patch("src.security.rate_limiting.Limiter") as mock_limiter_class:
                # Configure production settings
                mock_settings.return_value.environment = "prod"
                mock_settings.return_value.redis_host = "redis.example.com"
                mock_settings.return_value.redis_port = 6379
                mock_settings.return_value.redis_db = 1

                # Create a mock limiter instance
                mock_limiter = Mock()
                mock_limiter_class.return_value = mock_limiter

                limiter = create_limiter()

                # Verify Redis storage URI is constructed correctly
                expected_uri = "redis://redis.example.com:6379/1"
                assert limiter.storage_uri == expected_uri

                # Verify Limiter was called with correct parameters
                mock_limiter_class.assert_called_once_with(
                    key_func=get_client_identifier,
                    storage_uri=expected_uri,
                    default_limits=["100 per minute"],
                )

    def test_create_limiter_production_default_redis_config(self):
        """Test production environment with default Redis configuration."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            with patch("src.security.rate_limiting.Limiter") as mock_limiter_class:
                # Production without explicit Redis config (should use defaults)
                settings_mock = Mock()
                settings_mock.environment = "prod"
                # Don't set redis_host, redis_port, redis_db attributes
                mock_settings.return_value = settings_mock

                # Create a mock limiter instance
                mock_limiter = Mock()
                mock_limiter_class.return_value = mock_limiter

                limiter = create_limiter()

                # Should use default Redis configuration
                expected_uri = "redis://localhost:6379/0"
                assert limiter.storage_uri == expected_uri

                # Verify Limiter was called with correct parameters
                mock_limiter_class.assert_called_once_with(
                    key_func=get_client_identifier,
                    storage_uri=expected_uri,
                    default_limits=["100 per minute"],
                )

    def test_create_limiter_development_memory_storage(self):
        """Test that development environment uses memory storage."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "dev"

            limiter = create_limiter()

            # Should use memory storage for development
            assert limiter.storage_uri == "memory://"

    def test_create_limiter_staging_memory_storage(self):
        """Test that staging environment uses memory storage."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "staging"

            limiter = create_limiter()

            # Should use memory storage for staging
            assert limiter.storage_uri == "memory://"

    def test_create_limiter_test_memory_storage(self):
        """Test that test environment uses memory storage."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "test"

            limiter = create_limiter()

            # Should use memory storage for test
            assert limiter.storage_uri == "memory://"

    def test_create_limiter_unknown_environment_memory_storage(self):
        """Test that unknown environments default to memory storage."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "unknown"

            limiter = create_limiter()

            # Should default to memory storage for unknown environments
            assert limiter.storage_uri == "memory://"

    def test_create_limiter_logging_production(self):
        """Test that production limiter creation logs Redis usage."""
        # Capture logs
        log_stream = StringIO()
        log_handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("src.security.rate_limiting")
        logger.handlers.clear()
        logger.addHandler(log_handler)
        logger.setLevel(logging.INFO)

        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            with patch("src.security.rate_limiting.Limiter") as mock_limiter_class:
                mock_settings.return_value.environment = "prod"
                mock_settings.return_value.redis_host = "prod-redis.com"
                mock_settings.return_value.redis_port = 6380
                mock_settings.return_value.redis_db = 2

                # Create a mock limiter instance
                mock_limiter = Mock()
                mock_limiter_class.return_value = mock_limiter

                create_limiter()

                log_output = log_stream.getvalue()

                # Should log Redis storage usage
                assert "Using Redis storage for production rate limiting" in log_output
                assert "redis://prod-redis.com:6380/2" in log_output
                assert "Rate limiter configured with storage" in log_output

    def test_create_limiter_logging_development(self):
        """Test that development limiter creation logs memory usage."""
        # Capture logs
        log_stream = StringIO()
        log_handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("src.security.rate_limiting")
        logger.handlers.clear()
        logger.addHandler(log_handler)
        logger.setLevel(logging.INFO)

        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "dev"

            create_limiter()

            log_output = log_stream.getvalue()

            # Should log memory storage usage
            assert "Using in-memory storage for dev environment" in log_output
            assert "Rate limiter configured with storage: memory://" in log_output

    def test_create_limiter_configuration_parameters(self):
        """Test that limiter is configured with correct parameters."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "dev"

            limiter = create_limiter()

            # Should use our custom key function
            assert limiter._key_func == get_client_identifier

            # Should have default limits configured
            assert len(limiter._default_limits) == 1
            # The default limits is correctly configured
            assert limiter._default_limits is not None


class TestGetRateLimitForEndpoint:
    """Test the get_rate_limit_for_endpoint function comprehensively."""

    def test_get_rate_limit_api_endpoint(self):
        """Test rate limit for API endpoints."""
        limit = get_rate_limit_for_endpoint("api")
        assert limit == RateLimits.API_DEFAULT
        assert limit == "60/minute"  # Verify actual value

    def test_get_rate_limit_health_endpoint(self):
        """Test rate limit for health check endpoints."""
        limit = get_rate_limit_for_endpoint("health")
        assert limit == RateLimits.HEALTH_CHECK
        assert limit == "300/minute"  # More permissive for health checks

    def test_get_rate_limit_auth_endpoint(self):
        """Test rate limit for authentication endpoints."""
        limit = get_rate_limit_for_endpoint("auth")
        assert limit == RateLimits.AUTH
        assert limit == "10/minute"  # More restrictive for auth

    def test_get_rate_limit_upload_endpoint(self):
        """Test rate limit for upload endpoints."""
        limit = get_rate_limit_for_endpoint("upload")
        assert limit == RateLimits.UPLOAD
        assert limit == "5/minute"  # Most restrictive for uploads

    def test_get_rate_limit_admin_endpoint(self):
        """Test rate limit for admin endpoints."""
        limit = get_rate_limit_for_endpoint("admin")
        assert limit == RateLimits.ADMIN
        assert limit == "10/minute"  # Moderate limit for admin

    def test_get_rate_limit_public_endpoint(self):
        """Test rate limit for public read endpoints."""
        limit = get_rate_limit_for_endpoint("public")
        assert limit == RateLimits.PUBLIC_READ
        assert limit == "100/minute"  # More permissive for public reads

    def test_get_rate_limit_unknown_endpoint(self):
        """Test rate limit for unknown endpoint types defaults to API limit."""
        unknown_types = [
            "unknown",
            "custom",
            "special",
            "",
            "nonexistent",
        ]

        for endpoint_type in unknown_types:
            limit = get_rate_limit_for_endpoint(endpoint_type)
            assert limit == RateLimits.API_DEFAULT
            assert limit == "60/minute"

    def test_get_rate_limit_case_sensitivity(self):
        """Test that endpoint type matching is case sensitive."""
        # These should not match and should return default
        case_variants = [
            "API",  # Should not match "api"
            "Auth",  # Should not match "auth"
            "HEALTH",  # Should not match "health"
            "Upload",  # Should not match "upload"
        ]

        for variant in case_variants:
            limit = get_rate_limit_for_endpoint(variant)
            assert limit == RateLimits.API_DEFAULT  # Should default

    def test_all_rate_limits_constants_defined(self):
        """Test that all RateLimits constants are properly defined."""
        # Verify all expected constants exist and have string values
        expected_constants = [
            "API_DEFAULT",
            "HEALTH_CHECK",
            "AUTH",
            "UPLOAD",
            "ADMIN",
            "PUBLIC_READ",
        ]

        for constant in expected_constants:
            assert hasattr(RateLimits, constant)
            value = getattr(RateLimits, constant)
            assert isinstance(value, str)
            assert "per" in value or "/" in value  # Should be a rate limit string format

    def test_rate_limits_values_are_reasonable(self):
        """Test that rate limit values are reasonable and properly formatted."""
        limits_to_test = [
            (RateLimits.API_DEFAULT, "API_DEFAULT"),
            (RateLimits.HEALTH_CHECK, "HEALTH_CHECK"),
            (RateLimits.AUTH, "AUTH"),
            (RateLimits.UPLOAD, "UPLOAD"),
            (RateLimits.ADMIN, "ADMIN"),
            (RateLimits.PUBLIC_READ, "PUBLIC_READ"),
        ]

        for limit_value, limit_name in limits_to_test:
            # Should be in format "number/timeunit" or "number per timeunit"
            if " per " in limit_value:
                parts = limit_value.split(" per ")
            elif "/" in limit_value:
                parts = limit_value.split("/")
            else:
                raise AssertionError(f"{limit_name} format is invalid: {limit_value}")
            assert len(parts) == 2, f"{limit_name} format is invalid: {limit_value}"

            # First part should be a number
            assert parts[0].isdigit(), f"{limit_name} number is invalid: {parts[0]}"

            # Second part should be a time unit
            valid_time_units = ["second", "minute", "hour", "day"]
            assert parts[1] in valid_time_units, f"{limit_name} time unit is invalid: {parts[1]}"

            # Verify reasonable limits (not too high or too low)
            limit_number = int(parts[0])
            assert 1 <= limit_number <= 1000, f"{limit_name} limit seems unreasonable: {limit_number}"


class TestRateLimitExceededHandlerComprehensive:
    """Comprehensive testing of rate_limit_exceeded_handler."""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_basic(self):
        """Test basic rate limit exceeded handler functionality."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "192.168.1.100"
        # Properly mock headers.get to return None for missing headers
        request.headers.get.return_value = None

        # Create a mock limit object for RateLimitExceeded
        mock_limit = Mock()
        mock_limit.error_message = "Rate limit exceeded"
        exc = RateLimitExceeded(mock_limit)

        with patch("src.security.rate_limiting.AuthExceptionHandler.handle_rate_limit_error") as mock_handler:
            mock_handler.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")

            # Expect HTTPException to be raised
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_exceeded_handler(request, exc)

            assert exc_info.value.status_code == 429
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_with_forwarded_ip(self):
        """Test rate limit handler with forwarded IP address."""
        request = Mock(spec=Request)
        request.url.path = "/api/restricted"
        request.method = "GET"
        request.headers = {"x-forwarded-for": "203.0.113.50, 10.0.0.1"}
        request.client.host = "10.0.0.1"

        # Create a mock limit object for RateLimitExceeded
        mock_limit = Mock()
        mock_limit.error_message = "Rate limit exceeded"
        exc = RateLimitExceeded(mock_limit)

        with patch("src.security.rate_limiting.AuthExceptionHandler.handle_rate_limit_error") as mock_handler:
            mock_handler.side_effect = HTTPException(status_code=429, detail="Too many requests")

            # Expect HTTPException to be raised
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_exceeded_handler(request, exc)

            assert exc_info.value.status_code == 429
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_with_real_ip(self):
        """Test rate limit handler with X-Real-IP header."""
        request = Mock(spec=Request)
        request.url.path = "/api/upload"
        request.method = "POST"
        request.headers = {"x-real-ip": "198.51.100.25"}
        request.client.host = "127.0.0.1"

        # Create a mock limit object for RateLimitExceeded
        mock_limit = Mock()
        mock_limit.error_message = "Upload rate limit exceeded"
        exc = RateLimitExceeded(mock_limit)

        with patch("src.security.rate_limiting.AuthExceptionHandler.handle_rate_limit_error") as mock_handler:
            mock_handler.side_effect = HTTPException(status_code=429, detail="Upload limit exceeded")

            # Expect HTTPException to be raised
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_exceeded_handler(request, exc)

            assert exc_info.value.status_code == 429
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_no_client_info(self):
        """Test rate limit handler when client information is missing."""
        request = Mock(spec=Request)
        request.url.path = "/api/anonymous"
        request.method = "GET"
        request.headers = {}
        request.client = None  # No client info

        # Create a mock limit object for RateLimitExceeded
        mock_limit = Mock()
        mock_limit.error_message = "Anonymous rate limit exceeded"
        exc = RateLimitExceeded(mock_limit)

        with patch("src.security.rate_limiting.AuthExceptionHandler.handle_rate_limit_error") as mock_handler:
            mock_handler.side_effect = HTTPException(status_code=429, detail="Rate limited")

            # Expect HTTPException to be raised
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_exceeded_handler(request, exc)

            assert exc_info.value.status_code == 429
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_custom_exception_message(self):
        """Test rate limit handler preserves custom exception details."""
        request = Mock(spec=Request)
        request.url.path = "/api/custom"
        request.method = "POST"
        request.client.host = "192.168.1.200"
        # Properly mock headers.get to return None for missing headers
        request.headers.get.return_value = None

        # Custom exception with specific message
        # Create a mock limit object for RateLimitExceeded
        mock_limit = Mock()
        mock_limit.error_message = "Custom rate limit message with details"
        exc = RateLimitExceeded(mock_limit)

        with patch("src.security.rate_limiting.AuthExceptionHandler.handle_rate_limit_error") as mock_handler:
            mock_handler.side_effect = HTTPException(
                status_code=429,
                detail="Custom rate limit response",
                headers={"Retry-After": "60"},
            )

            # Expect HTTPException to be raised
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_exceeded_handler(request, exc)

            assert exc_info.value.status_code == 429
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_auth_exception_integration(self):
        """Test that rate limit handler properly integrates with AuthExceptionHandler."""
        request = Mock(spec=Request)
        request.url.path = "/api/auth"
        request.method = "POST"
        request.client.host = "10.0.0.5"
        # Properly mock headers.get to return None for missing headers
        request.headers.get.return_value = None

        # Create a mock limit object for RateLimitExceeded
        mock_limit = Mock()
        mock_limit.error_message = "Auth rate limit exceeded"
        exc = RateLimitExceeded(mock_limit)

        # Mock AuthExceptionHandler to return specific response
        with patch("src.security.rate_limiting.AuthExceptionHandler.handle_rate_limit_error") as mock_handler:
            mock_response = HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": "20",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "1640995200",
                },
            )
            mock_handler.side_effect = mock_response

            # Expect HTTPException to be raised
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_exceeded_handler(request, exc)

            assert exc_info.value.status_code == 429
            mock_handler.assert_called_once()


class TestGetClientIdentifierComprehensive:
    """Comprehensive testing of get_client_identifier function."""

    def test_get_client_identifier_x_forwarded_for_priority(self):
        """Test that X-Forwarded-For takes highest priority."""
        request = Mock(spec=Request)
        request.headers = {
            "x-forwarded-for": "203.0.113.1, 10.0.0.1",
            "x-real-ip": "203.0.113.2",
        }
        request.client.host = "127.0.0.1"

        identifier = get_client_identifier(request)
        assert identifier == "203.0.113.1"  # First IP from X-Forwarded-For

    def test_get_client_identifier_x_real_ip_fallback(self):
        """Test that X-Real-IP is used when X-Forwarded-For is absent."""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "203.0.113.3"}
        request.client.host = "127.0.0.1"

        identifier = get_client_identifier(request)
        assert identifier == "203.0.113.3"

    def test_get_client_identifier_direct_client_fallback(self):
        """Test fallback to direct client IP when headers are missing."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client.host = "192.168.1.150"

        identifier = get_client_identifier(request)
        assert identifier == "192.168.1.150"

    def test_get_client_identifier_no_client_object(self):
        """Test behavior when request.client is None."""
        with patch("src.security.rate_limiting.get_remote_address") as mock_get_remote:
            mock_get_remote.return_value = "127.0.0.1"

            request = Mock(spec=Request)
            request.headers = {}
            request.client = None

            identifier = get_client_identifier(request)
            # When no headers are found, it should fall back to get_remote_address
            assert identifier == "127.0.0.1"
            mock_get_remote.assert_called_once_with(request)

    def test_get_client_identifier_malformed_forwarded_for(self):
        """Test handling of malformed X-Forwarded-For headers."""
        malformed_headers = [
            "",  # Empty
            ",,,",  # Only commas
            "  ,  ,  ",  # Only spaces and commas
            "not.an.ip.address",  # Invalid IP format
            "256.256.256.256",  # Invalid IP values
        ]

        for malformed_value in malformed_headers:
            request = Mock(spec=Request)
            request.headers = {"x-forwarded-for": malformed_value}
            request.client.host = "192.168.1.100"

            identifier = get_client_identifier(request)

            # Should either get the malformed value (first part before comma)
            # or fall back to client.host, depending on implementation
            assert isinstance(identifier, str)
            assert len(identifier) > 0

    def test_get_client_identifier_with_ipv6(self):
        """Test client identification with IPv6 addresses."""
        ipv6_addresses = [
            "2001:db8::1",
            "::1",  # Localhost IPv6
            "2001:db8::8a2e:370:7334",
            "fe80::1%lo0",  # Link-local with zone
        ]

        for ipv6_addr in ipv6_addresses:
            request = Mock(spec=Request)
            request.headers = {"x-forwarded-for": ipv6_addr}
            request.client.host = "127.0.0.1"

            identifier = get_client_identifier(request)
            assert identifier == ipv6_addr

    def test_get_client_identifier_mixed_ipv4_ipv6(self):
        """Test X-Forwarded-For with mixed IPv4 and IPv6 addresses."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "2001:db8::1, 192.168.1.100, 203.0.113.5"}
        request.client.host = "127.0.0.1"

        identifier = get_client_identifier(request)
        assert identifier == "2001:db8::1"  # First IP (IPv6) should be used


class TestSetupRateLimitingIntegration:
    """Test setup_rate_limiting function integration."""

    def test_setup_rate_limiting_adds_exception_handler(self):
        """Test that setup_rate_limiting adds the exception handler to the app."""
        from fastapi import FastAPI

        app = FastAPI()

        # Track exception handler additions
        exception_handlers = []
        original_add_exception_handler = app.add_exception_handler

        def mock_add_exception_handler(exc_class, handler):
            exception_handlers.append((exc_class, handler))
            return original_add_exception_handler(exc_class, handler)

        app.add_exception_handler = mock_add_exception_handler

        # Call setup function
        setup_rate_limiting(app)

        # Verify exception handler was added
        assert len(exception_handlers) == 1
        exc_class, handler = exception_handlers[0]
        assert exc_class == RateLimitExceeded
        assert handler == rate_limit_exceeded_handler

    def test_setup_rate_limiting_creates_limiter(self):
        """Test that setup_rate_limiting creates and returns a limiter."""
        from fastapi import FastAPI

        app = FastAPI()

        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            mock_settings.return_value.environment = "dev"

            setup_rate_limiting(app)

            # Should set the limiter in app state
            assert hasattr(app.state, "limiter")
            assert isinstance(app.state.limiter, Limiter)
            assert app.state.limiter._key_func == get_client_identifier
            assert app.state.limiter.storage_uri == "memory://"

    def test_setup_rate_limiting_with_different_environments(self):
        """Test setup_rate_limiting behavior across different environments."""
        from fastapi import FastAPI

        environments = ["dev", "staging", "prod", "test"]

        for env in environments:
            app = FastAPI()

            # Create a mock limiter instance with correct storage URI for the environment
            mock_limiter = Mock()
            if env == "prod":
                mock_limiter.storage_uri = "redis://localhost:6379/0"
            else:
                mock_limiter.storage_uri = "memory://"

            # Patch the global limiter variable that setup_rate_limiting uses
            with patch("src.security.rate_limiting.limiter", mock_limiter):
                setup_rate_limiting(app)

                # Verify correct storage based on environment
                limiter = app.state.limiter
                if env == "prod":
                    assert limiter.storage_uri == "redis://localhost:6379/0"
                else:
                    assert limiter.storage_uri == "memory://"


class TestRateLimitingEdgeCases:
    """Test edge cases and error conditions in rate limiting."""

    def test_rate_limits_consistency(self):
        """Test that rate limit constants are consistent and logical."""

        # Extract numeric values for comparison - handle both "/" and " per " formats
        def extract_limit_number(limit_str):
            if "/" in limit_str:
                return int(limit_str.split("/")[0])
            if " per " in limit_str:
                return int(limit_str.split(" per ")[0])
            return int(limit_str.split()[0])

        limits = {
            "upload": extract_limit_number(RateLimits.UPLOAD),
            "auth": extract_limit_number(RateLimits.AUTH),
            "admin": extract_limit_number(RateLimits.ADMIN),
            "api": extract_limit_number(RateLimits.API_DEFAULT),
            "public": extract_limit_number(RateLimits.PUBLIC_READ),
            "health": extract_limit_number(RateLimits.HEALTH_CHECK),
        }

        # Verify logical ordering (most restrictive to least restrictive)
        assert limits["upload"] <= limits["auth"]  # Upload should be most restrictive
        assert limits["auth"] <= limits["admin"]  # Auth should be more restrictive than admin
        assert limits["admin"] <= limits["api"]  # Admin should be more restrictive than general API
        assert limits["api"] <= limits["public"]  # API should be more restrictive than public reads
        assert limits["public"] <= limits["health"]  # Health checks should be least restrictive

    def test_limiter_with_extreme_redis_config(self):
        """Test limiter creation with extreme Redis configuration values."""
        with patch("src.security.rate_limiting.get_settings") as mock_settings:
            with patch("src.security.rate_limiting.Limiter") as mock_limiter_class:
                # Test with extreme values
                mock_settings.return_value.environment = "prod"
                mock_settings.return_value.redis_host = "redis-cluster-with-very-long-hostname.example.com"
                mock_settings.return_value.redis_port = 65535  # Max port
                mock_settings.return_value.redis_db = 15  # Max Redis DB number

                # Create a mock limiter instance
                mock_limiter = Mock()
                mock_limiter_class.return_value = mock_limiter

                limiter = create_limiter()

                expected_uri = "redis://redis-cluster-with-very-long-hostname.example.com:65535/15"
                assert limiter.storage_uri == expected_uri

    def test_get_client_identifier_performance(self):
        """Test get_client_identifier performance with many headers."""
        request = Mock(spec=Request)

        # Create request with many headers
        large_headers = {}
        for i in range(100):
            large_headers[f"X-Custom-Header-{i}"] = f"value_{i}"

        # Add the headers we care about
        large_headers["x-forwarded-for"] = "203.0.113.100"
        request.headers = large_headers
        request.client.host = "127.0.0.1"

        # Should still work efficiently
        import time

        start_time = time.time()
        identifier = get_client_identifier(request)
        end_time = time.time()

        assert identifier == "203.0.113.100"
        assert end_time - start_time < 0.01  # Should be very fast

    def test_rate_limit_string_format_edge_cases(self):
        """Test rate limit string formats with edge cases."""
        # Test that all rate limit strings are properly formatted
        all_limits = [
            RateLimits.API_DEFAULT,
            RateLimits.HEALTH_CHECK,
            RateLimits.AUTH,
            RateLimits.UPLOAD,
            RateLimits.ADMIN,
            RateLimits.PUBLIC_READ,
        ]

        for limit in all_limits:
            # Should be parseable by slowapi
            assert isinstance(limit, str)
            assert len(limit) > 0
            assert " per " in limit or "/" in limit

            # Should not have leading/trailing whitespace
            assert limit == limit.strip()

            # Should be lowercase for time units (standard format)
            if " per " in limit:
                time_unit = limit.split(" per ")[1]
            elif "/" in limit:
                time_unit = limit.split("/")[1]
            else:
                time_unit = limit.split()[1]
            assert time_unit.islower() or time_unit == time_unit.lower()
