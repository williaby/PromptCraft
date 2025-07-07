"""Rate limiting for FastAPI applications using slowapi.

This module provides comprehensive rate limiting capabilities to protect
against abuse and ensure fair resource usage across all API endpoints.
"""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """Extract client identifier for rate limiting.

    This function determines how to identify clients for rate limiting purposes.
    It checks for forwarded headers first (for reverse proxy setups) and falls
    back to the direct client IP.

    Args:
        request: The incoming request

    Returns:
        Client identifier string for rate limiting
    """
    # Check for forwarded headers (common in reverse proxy setups)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        client_ip = forwarded_for.split(",")[0].strip()
        logger.debug("Using X-Forwarded-For IP for rate limiting: %s", client_ip)
        return client_ip

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        client_ip = real_ip.strip()
        logger.debug("Using X-Real-IP for rate limiting: %s", client_ip)
        return client_ip

    # Fall back to slowapi's default method
    client_ip = get_remote_address(request)
    logger.debug("Using direct client IP for rate limiting: %s", client_ip)
    return client_ip


def create_limiter() -> Limiter:
    """Create and configure the rate limiter instance.

    Returns:
        Configured Limiter instance
    """
    settings = get_settings(validate_on_startup=False)

    # Configure storage backend based on environment
    if settings.environment == "prod":
        # Production: Use Redis for distributed rate limiting
        redis_host = getattr(settings, "redis_host", "localhost")
        redis_port = getattr(settings, "redis_port", 6379)
        redis_db = getattr(settings, "redis_db", 0)
        storage_uri = f"redis://{redis_host}:{redis_port}/{redis_db}"
        logger.info("Using Redis storage for production rate limiting: %s", storage_uri)
    else:
        # Development/staging: in-memory storage is fine
        storage_uri = "memory://"
        logger.info("Using in-memory storage for %s environment", settings.environment)

    # Create limiter with custom key function
    limiter = Limiter(
        key_func=get_client_identifier,
        storage_uri=storage_uri,
        default_limits=["100 per minute"],  # Default fallback limit for unspecified endpoints
    )

    logger.info(
        "Rate limiter configured with storage: %s (Environment: %s)",
        storage_uri,
        settings.environment,
    )

    return limiter


# Global limiter instance
limiter = create_limiter()


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Any:
    """Custom handler for rate limit exceeded errors.

    This handler provides detailed rate limiting information while maintaining
    security by not exposing internal implementation details.

    Args:
        request: The incoming request
        exc: The rate limit exceeded exception

    Returns:
        JSON response with rate limit information
    """
    client_ip = get_client_identifier(request)

    # Log rate limit violation
    logger.warning(
        "Rate limit exceeded for client %s on %s %s (Limit: %s)",
        client_ip,
        request.method,
        request.url.path,
        exc.detail,
    )

    # Calculate retry-after header
    default_retry_after = 60  # Default retry time in seconds
    retry_after = exc.retry_after if hasattr(exc, "retry_after") else default_retry_after

    # Create detailed error response
    error_detail = {
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please slow down and try again later.",
        "retry_after": retry_after,
        "limit": exc.detail if hasattr(exc, "detail") else f"{default_retry_after} per minute",
    }

    # Return HTTP 429 with rate limit headers
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=error_detail,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail) if hasattr(exc, "detail") else str(default_retry_after),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(retry_after),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )


def setup_rate_limiting(app: Any) -> None:
    """Configure rate limiting for the FastAPI application.

    This function sets up the rate limiter and its error handler.

    Args:
        app: The FastAPI application instance
    """
    # Add rate limiter to app state for access in routes
    app.state.limiter = limiter

    # Add custom rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    logger.info("Rate limiting configured for application")


# Common rate limit decorators for different endpoint types
class RateLimits:
    """Predefined rate limits for common endpoint types."""

    # API endpoints (60 requests per minute per IP)
    API_DEFAULT = "60/minute"

    # Health check endpoints (higher limit for monitoring)
    HEALTH_CHECK = "300/minute"

    # Authentication endpoints (stricter limits)
    AUTH = "10/minute"

    # File upload endpoints (very strict)
    UPLOAD = "5/minute"

    # Administrative endpoints (very strict)
    ADMIN = "10/minute"

    # Public read-only endpoints (moderate limits)
    PUBLIC_READ = "100/minute"


def get_rate_limit_for_endpoint(endpoint_type: str) -> str:
    """Get appropriate rate limit for endpoint type.

    Args:
        endpoint_type: Type of endpoint (api, health, auth, upload, admin, public)

    Returns:
        Rate limit string for the endpoint type
    """
    limits_map = {
        "api": RateLimits.API_DEFAULT,
        "health": RateLimits.HEALTH_CHECK,
        "auth": RateLimits.AUTH,
        "upload": RateLimits.UPLOAD,
        "admin": RateLimits.ADMIN,
        "public": RateLimits.PUBLIC_READ,
    }

    return limits_map.get(endpoint_type, RateLimits.API_DEFAULT)


# Utility function to create rate limit decorator
def rate_limit(limit: str) -> Callable:
    """Create a rate limit decorator for endpoints.

    Args:
        limit: Rate limit string (e.g., "60/minute")

    Returns:
        Decorator function for applying rate limits
    """
    return limiter.limit(limit)
