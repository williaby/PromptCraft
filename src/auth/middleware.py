"""FastAPI authentication middleware for Cloudflare Access integration.

This module provides FastAPI middleware for JWT-based authentication with:
- JWT token extraction from Cloudflare Access headers
- Email-based user identification and role mapping
- Rate limiting to prevent DOS attacks
- User context injection for downstream processing
"""

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .config import AuthenticationConfig
from .jwks_client import JWKSClient
from .jwt_validator import JWTValidator
from .models import AuthenticatedUser, AuthenticationError, JWTValidationError

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Cloudflare Access authentication."""

    def __init__(
        self,
        app: FastAPI,
        config: AuthenticationConfig,
        jwt_validator: JWTValidator,
        excluded_paths: list[str] | None = None,
    ) -> None:
        """Initialize authentication middleware.

        Args:
            app: FastAPI application instance
            config: Authentication configuration
            jwt_validator: JWT validator instance
            excluded_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        self.config = config
        self.jwt_validator = jwt_validator
        self.excluded_paths = excluded_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request through authentication middleware.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint handler

        Returns:
            HTTP response
        """
        # Skip authentication for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Skip authentication if disabled
        if not self.config.cloudflare_access_enabled:
            logger.debug("Cloudflare Access authentication is disabled")
            return await call_next(request)

        try:
            # Extract and validate JWT token
            authenticated_user = await self._authenticate_request(request)

            # Inject user context into request state
            request.state.authenticated_user = authenticated_user
            request.state.user_email = authenticated_user.email
            request.state.user_role = authenticated_user.role

            # Log successful authentication
            if self.config.auth_logging_enabled:
                logger.info(f"Authenticated user: {authenticated_user.email} with role: {authenticated_user.role}")

            # Proceed to next middleware/endpoint
            return await call_next(request)

        except AuthenticationError as e:
            # Log authentication failure
            if self.config.auth_logging_enabled:
                logger.warning(f"Authentication failed: {e.message}")

            # Return 401 response
            return self._create_auth_error_response(e)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in authentication middleware: {e}")

            # Return 500 response for unexpected errors
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "Authentication system error",
                },
            )

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from authentication.

        Args:
            path: Request path

        Returns:
            True if path should be excluded, False otherwise
        """
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True
        return False

    async def _authenticate_request(self, request: Request) -> AuthenticatedUser:
        """Authenticate the request and return user information.

        Args:
            request: HTTP request to authenticate

        Returns:
            AuthenticatedUser with validated user information

        Raises:
            AuthenticationError: If authentication fails
        """
        # Extract JWT token from Cloudflare Access header
        token = self._extract_jwt_token(request)
        if not token:
            raise AuthenticationError("Missing authentication token", 401)

        try:
            # Validate JWT token
            authenticated_user = self.jwt_validator.validate_token(
                token,
                email_whitelist=self.config.email_whitelist if self.config.email_whitelist_enabled else None,
            )

            return authenticated_user

        except JWTValidationError as e:
            # Convert JWT validation errors to authentication errors
            raise AuthenticationError(f"Token validation failed: {e.message}", 401) from e

    def _extract_jwt_token(self, request: Request) -> str | None:
        """Extract JWT token from Cloudflare Access headers.

        Args:
            request: HTTP request

        Returns:
            JWT token string if found, None otherwise
        """
        # Primary: Cloudflare Access JWT header
        cf_access_jwt = request.headers.get("CF-Access-Jwt-Assertion")
        if cf_access_jwt:
            logger.debug("Found JWT token in CF-Access-Jwt-Assertion header")
            return cf_access_jwt

        # Fallback: Standard Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            logger.debug("Found JWT token in Authorization header")
            return token

        # Fallback: Custom header for testing/development
        custom_jwt = request.headers.get("X-JWT-Token")
        if custom_jwt:
            logger.debug("Found JWT token in X-JWT-Token header")
            return custom_jwt

        logger.debug("No JWT token found in request headers")
        return None

    def _create_auth_error_response(self, error: AuthenticationError) -> JSONResponse:
        """Create JSON error response for authentication failures.

        Args:
            error: Authentication error

        Returns:
            JSON response with error details
        """
        content = {
            "error": "Authentication failed",
            "message": error.message if self.config.auth_error_detail_enabled else "Authentication required",
        }

        return JSONResponse(
            status_code=error.status_code,
            content=content,
        )


def create_rate_limiter(config: AuthenticationConfig) -> Limiter:
    """Create rate limiter for authentication endpoints.

    Args:
        config: Authentication configuration

    Returns:
        Configured Limiter instance
    """

    def get_rate_limit_key(request: Request) -> str:
        """Get rate limiting key based on configuration."""
        if config.rate_limit_key_func == "ip":
            return get_remote_address(request)
        if config.rate_limit_key_func == "email":
            # Use authenticated user email if available
            if hasattr(request.state, "user_email"):
                return request.state.user_email
            # Fallback to IP if no authenticated user
            return get_remote_address(request)
        if config.rate_limit_key_func == "user":
            # Use authenticated user email if available
            if hasattr(request.state, "authenticated_user"):
                return request.state.authenticated_user.email
            # Fallback to IP if no authenticated user
            return get_remote_address(request)
        # Default to IP-based rate limiting
        return get_remote_address(request)

    return Limiter(
        key_func=get_rate_limit_key,
        default_limits=[f"{config.rate_limit_requests}/{config.rate_limit_window}seconds"],
    )


def setup_authentication(
    app: FastAPI,
    config: AuthenticationConfig,
) -> tuple[AuthenticationMiddleware, Limiter]:
    """Setup authentication middleware and rate limiting for FastAPI app.

    Args:
        app: FastAPI application instance
        config: Authentication configuration

    Returns:
        Tuple of (AuthenticationMiddleware, Limiter) instances
    """
    # Create JWKS client
    jwks_client = JWKSClient(
        jwks_url=config.get_jwks_url(),
        cache_ttl=config.jwks_cache_ttl,
        max_cache_size=config.jwks_cache_max_size,
        timeout=config.jwks_timeout,
    )

    # Create JWT validator
    jwt_validator = JWTValidator(
        jwks_client=jwks_client,
        audience=config.cloudflare_audience,
        issuer=config.cloudflare_issuer,
        algorithm=config.jwt_algorithm,
    )

    # Create authentication middleware
    auth_middleware = AuthenticationMiddleware(
        app=app,
        config=config,
        jwt_validator=jwt_validator,
    )

    # Create rate limiter
    limiter = create_rate_limiter(config)

    # Add middleware to app
    app.add_middleware(auth_middleware)

    if config.rate_limiting_enabled:
        app.add_middleware(SlowAPIMiddleware)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logger.info("Authentication middleware and rate limiting configured")

    return auth_middleware, limiter


def get_current_user(request: Request) -> AuthenticatedUser | None:
    """Get current authenticated user from request state.

    Args:
        request: HTTP request

    Returns:
        AuthenticatedUser if authenticated, None otherwise
    """
    return getattr(request.state, "authenticated_user", None)


def require_authentication(request: Request) -> AuthenticatedUser:
    """Require authentication and return current user.

    Args:
        request: HTTP request

    Returns:
        AuthenticatedUser

    Raises:
        HTTPException: If user is not authenticated
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(request: Request, required_role: str) -> AuthenticatedUser:
    """Require specific role and return current user.

    Args:
        request: HTTP request
        required_role: Required user role

    Returns:
        AuthenticatedUser

    Raises:
        HTTPException: If user doesn't have required role
    """
    user = require_authentication(request)
    if user.role.value != required_role:
        raise HTTPException(status_code=403, detail=f"Role '{required_role}' required")
    return user
