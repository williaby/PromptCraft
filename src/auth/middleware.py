"""FastAPI authentication middleware for Cloudflare Access integration.

This module provides FastAPI middleware for JWT-based authentication with:
- JWT token extraction from Cloudflare Access headers
- Service token validation for non-interactive API access
- Email-based user identification and role mapping
- Rate limiting to prevent DOS attacks
- User context injection for downstream processing
- Database tracking for usage analytics and audit logging
"""

from collections.abc import Awaitable, Callable
import hashlib
import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import func, select, text, update
from starlette.middleware.base import BaseHTTPMiddleware

from src.database import DatabaseError
from src.database.connection import get_db
from src.database.models import AuthenticationEvent, UserSession

from .models import AuthenticatedUser, AuthenticationError, JWTValidationError, SecurityEventSeverity, SecurityEventType


# Import auth_simple compatibility types
try:
    from src.auth_simple import AuthConfig as AuthenticationConfig
    from src.auth_simple.cloudflare_auth import JWTValidator
except ImportError:
    # Fallback types for compatibility
    class AuthenticationConfig:
        """Compatibility placeholder for AuthenticationConfig."""

    class JWTValidator:
        """Compatibility placeholder for JWTValidator."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Initialize placeholder JWTValidator."""

        def validate_token(self, token: str, **kwargs: Any) -> None:
            """Placeholder token validation that returns None."""
            return


# Security logging compatibility
class SecurityLogger:
    """Compatibility security logger that uses standard logging."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("security")

    def log_security_event(self, event_type: str, message: str, severity: str = "INFO", **kwargs: str) -> None:
        """Log a security event."""
        log_message = f"[{event_type}] {message}"
        if kwargs:
            log_message += f" | Data: {kwargs}"

        if severity == "CRITICAL":
            self.logger.critical(log_message)
        elif severity == "HIGH":
            self.logger.error(log_message)
        elif severity == "MEDIUM":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    async def log_event(
        self,
        event_type: str,
        severity: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Log an event with structured data - compatibility method for middleware.

        Args:
            event_type: Type of event (SecurityEventType enum value)
            severity: Event severity (SecurityEventSeverity enum value)
            user_id: User identifier (email for regular users, None for service tokens)
            ip_address: Client IP address
            user_agent: User agent string
            session_id: Session identifier
            details: Additional event details as dictionary
        """
        # Convert enums to strings for logging
        # Use enum name (e.g., "LOGIN_SUCCESS") instead of value (e.g., "login_success") to match test expectations
        event_type_str = str(event_type.name) if hasattr(event_type, "name") else str(event_type)
        severity_str = str(severity.value) if hasattr(severity, "value") else str(severity or "INFO")

        # Build log message
        log_data = {
            "event_type": event_type_str,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
        }

        # Add details if provided
        if details:
            log_data.update(details)

        # Create formatted log message
        log_message = f"[{event_type_str}] Security event"
        if user_id:
            log_message += f" for user {user_id}"
        if ip_address:
            log_message += f" from {ip_address}"

        # Add details to log message
        filtered_data = {k: v for k, v in log_data.items() if v is not None}
        if filtered_data:
            log_message += f" | Data: {filtered_data}"

        # Log at appropriate level based on severity
        if severity_str.upper() in ["CRITICAL"]:
            self.logger.critical(log_message)
        elif severity_str.upper() in ["HIGH", "ERROR"]:
            self.logger.error(log_message)
        elif severity_str.upper() in ["MEDIUM", "WARNING"]:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)


# Security monitoring compatibility
class SecurityMonitor:
    """Compatibility security monitor for failed authentication tracking."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("security.monitor")
        self.failed_attempts = {}

    def record_failed_attempt(self, identifier: str, request_info: dict | None = None) -> None:
        """Record a failed authentication attempt."""
        self.failed_attempts[identifier] = self.failed_attempts.get(identifier, 0) + 1
        self.logger.warning(
            f"Failed authentication attempt for {identifier} (count: {self.failed_attempts[identifier]})",
        )

    def is_blocked(self, identifier: str) -> bool:
        """Check if an identifier is blocked due to too many failed attempts."""
        return self.failed_attempts.get(identifier, 0) > 10

    def reset_failed_attempts(self, identifier: str) -> None:
        """Reset failed attempts for an identifier."""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]

    async def track_failed_authentication(
        self,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        details: dict | None = None,
        endpoint: str | None = None,
        error_type: str | None = None,
    ) -> None:
        """Track failed authentication attempt and return alerts if any."""
        identifier = user_id or ip_address or "unknown"
        self.record_failed_attempt(
            identifier,
            {
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id,
                "details": details,
                "endpoint": endpoint,
                "error_type": error_type,
            },
        )

        # Return empty list for alerts - simplified security monitoring
        return []


logger = logging.getLogger(__name__)


class ServiceTokenUser:
    """Represents an authenticated service token user."""

    def __init__(self, token_id: str, token_name: str, metadata: dict, usage_count: int = 0) -> None:
        """Initialize service token user.

        Args:
            token_id: Unique token identifier
            token_name: Human-readable token name
            metadata: Token metadata including permissions
            usage_count: Current usage count
        """
        self.token_id = token_id
        self.token_name = token_name
        self.metadata = metadata
        # Add email attribute for compatibility (service tokens use token_name as email)
        self.email = f"{token_name}@service.local"
        self.usage_count = usage_count
        self.user_type = "service_token"

    def has_permission(self, permission: str) -> bool:
        """Check if token has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if token has permission, False otherwise
        """
        permissions = self.metadata.get("permissions", [])
        return permission in permissions or "admin" in permissions


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Cloudflare Access authentication."""

    def __init__(
        self,
        app: FastAPI,
        config: "AuthenticationConfig | None" = None,
        jwt_validator: "JWTValidator | None" = None,
        excluded_paths: list[str] | None = None,
        database_enabled: bool = True,
    ) -> None:
        """Initialize authentication middleware.

        Args:
            app: FastAPI application instance
            config: Authentication configuration
            jwt_validator: JWT validator instance
            excluded_paths: List of paths to exclude from authentication
            database_enabled: Whether database integration is enabled
        """
        super().__init__(app)
        # Store configuration parameters
        self.config = config
        self.jwt_validator = jwt_validator
        self.database_enabled = database_enabled
        self.excluded_paths = excluded_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        # Initialize security event logger
        self.security_logger = SecurityLogger()

        # Initialize security monitor for failed authentication tracking
        self.security_monitor = SecurityMonitor()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request through authentication middleware.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint handler

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Skip authentication for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Skip authentication if disabled
        if not self.config.cloudflare_access_enabled:
            logger.debug("Cloudflare Access authentication is disabled")
            return await call_next(request)

        try:
            # Extract and validate JWT token
            jwt_start = time.time()
            authenticated_user = await self._authenticate_request(request)
            jwt_time = (time.time() - jwt_start) * 1000  # Convert to milliseconds

            # Database session tracking (if enabled)
            db_start = time.time()
            if self.database_enabled:
                await self._update_user_session(authenticated_user, request)
            db_time = (time.time() - db_start) * 1000  # Convert to milliseconds

            # Inject user context into request state
            request.state.authenticated_user = authenticated_user

            # Handle different user types
            if isinstance(authenticated_user, ServiceTokenUser):
                request.state.user_email = None  # Service tokens don't have email
                request.state.user_role = None  # Service tokens don't have roles
                request.state.token_metadata = authenticated_user.metadata
            else:
                request.state.user_email = authenticated_user.email
                request.state.user_role = authenticated_user.role

            # Enhanced security event logging
            if isinstance(authenticated_user, ServiceTokenUser):
                # Log service token authentication success
                await self.security_logger.log_event(
                    event_type=SecurityEventType.SERVICE_TOKEN_AUTH,
                    severity=SecurityEventSeverity.INFO,
                    user_id=None,  # Service tokens don't have user IDs
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    session_id=authenticated_user.token_id,
                    details={
                        "token_name": authenticated_user.token_name,
                        "token_usage_count": authenticated_user.usage_count,
                        "endpoint": str(request.url.path),
                        "method": request.method,
                        "cloudflare_ray_id": request.headers.get("cf-ray"),
                        "auth_time_ms": jwt_time,
                        "db_time_ms": db_time,
                    },
                )

                if self.config.auth_logging_enabled:
                    logger.info(f"Authenticated service token: {authenticated_user.token_name}")
            else:
                # Log JWT authentication success
                await self.security_logger.log_event(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    severity=SecurityEventSeverity.INFO,
                    user_id=authenticated_user.email,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    session_id=authenticated_user.session_id if hasattr(authenticated_user, "session_id") else None,
                    details={
                        "user_email": authenticated_user.email,
                        "user_role": authenticated_user.role.value if authenticated_user.role else None,
                        "endpoint": str(request.url.path),
                        "method": request.method,
                        "cloudflare_ray_id": request.headers.get("cf-ray"),
                        "auth_time_ms": jwt_time,
                        "db_time_ms": db_time,
                    },
                )

                if self.config.auth_logging_enabled:
                    logger.info(f"Authenticated user: {authenticated_user.email} with role: {authenticated_user.role}")

            # Legacy database event logging (if enabled) - maintain backward compatibility
            if self.database_enabled:
                total_time = (time.time() - start_time) * 1000
                await self._log_authentication_event(
                    request,
                    user_email=authenticated_user.email if authenticated_user else None,
                    service_token_name=None,
                    event_type="auth_success",
                    success=True,
                    error_details=None,
                )

            # Proceed to next middleware/endpoint
            return await call_next(request)

        except AuthenticationError as e:
            # Track failed authentication attempt with security monitor
            client_ip = self._get_client_ip(request)
            alerts = await self.security_monitor.track_failed_authentication(
                user_id=None,  # Unknown user for failed authentication
                ip_address=client_ip or "unknown",
                user_agent=request.headers.get("user-agent"),
                endpoint=str(request.url.path),
                error_type=e.message,
                session_id=None,
            )

            # Enhanced security event logging for authentication failures
            await self.security_logger.log_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                severity=SecurityEventSeverity.WARNING,
                user_id=None,  # Unknown user for failed authentication
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent"),
                session_id=None,
                details={
                    "error_message": e.message,
                    "error_code": e.status_code,
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "cloudflare_ray_id": request.headers.get("cf-ray"),
                    "auth_attempt_time_ms": (time.time() - start_time) * 1000,
                    "alerts_generated": len(alerts),
                    "alert_types": [alert.alert_type for alert in alerts] if alerts else [],
                },
            )

            # Traditional logging
            if self.config.auth_logging_enabled:
                # Sanitize error message to prevent log injection
                sanitized_message = str(e.message).replace("\n", " ").replace("\r", " ")
                logger.warning(f"Authentication failed: {sanitized_message}")
                if alerts:
                    logger.warning(f"Security alerts generated: {[repr(alert.alert_type) for alert in alerts]}")

            # Legacy database event logging for failures (if enabled) - maintain backward compatibility
            if self.database_enabled:
                total_time = (time.time() - start_time) * 1000
                await self._log_authentication_event(
                    request,
                    user_email=None,
                    service_token_name=None,
                    event_type="auth_failure",
                    success=False,
                    error_details={"error": str(e), "processing_time_ms": total_time},
                )

            # Return 401 response
            return self._create_auth_error_response(e)

        except Exception as e:
            # Enhanced security event logging for system errors
            await self.security_logger.log_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                severity=SecurityEventSeverity.CRITICAL,
                user_id=None,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                session_id=None,
                details={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "cloudflare_ray_id": request.headers.get("cf-ray"),
                    "processing_time_ms": (time.time() - start_time) * 1000,
                },
            )

            # Traditional error logging
            logger.error(f"Unexpected error in authentication middleware: {e}")

            # Legacy database event logging for errors (if enabled) - maintain backward compatibility
            if self.database_enabled:
                total_time = (time.time() - start_time) * 1000
                await self._log_authentication_event(
                    request,
                    user_email=None,
                    service_token_name=None,
                    event_type="auth_failure",
                    success=False,
                    error_details={"error": str(e), "processing_time_ms": total_time},
                )

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
            # Exact match or prefix match with trailing slash
            if path == excluded or path.startswith(excluded + "/"):
                return True
        return False

    async def _authenticate_request(self, request: Request) -> AuthenticatedUser | ServiceTokenUser:
        """Authenticate the request and return user information.

        Args:
            request: HTTP request to authenticate

        Returns:
            AuthenticatedUser or ServiceTokenUser with validated information

        Raises:
            AuthenticationError: If authentication fails
        """
        # Extract authentication token (JWT or Service Token)
        token = self._extract_auth_token(request)
        if not token:
            raise AuthenticationError("Missing authentication token", 401)

        # Check if this is a service token (starts with 'sk_')
        if token.startswith("sk_"):
            return await self._validate_service_token(request, token)
        # Handle JWT token validation (existing flow)
        return await self._validate_jwt_token(request, token)

    async def _validate_jwt_token(self, request: Request, token: str) -> AuthenticatedUser:
        """Validate JWT token using existing flow.

        Args:
            request: HTTP request
            token: JWT token string

        Returns:
            AuthenticatedUser with validated user information

        Raises:
            AuthenticationError: If validation fails
        """
        try:
            # Validate JWT token
            authenticated_user = self.jwt_validator.validate_token(
                token,
                email_whitelist=self.config.email_whitelist if self.config.email_whitelist_enabled else None,
            )

            # Log authentication event
            await self._log_authentication_event(
                request,
                user_email=authenticated_user.email,
                event_type="jwt_auth",
                success=True,
            )

            return authenticated_user

        except JWTValidationError as e:
            # Log failed authentication
            await self._log_authentication_event(
                request,
                event_type="jwt_auth",
                success=False,
                error_details={"error": str(e), "message": e.message},
            )
            # Convert JWT validation errors to authentication errors
            raise AuthenticationError(f"Token validation failed: {e.message}", 401) from e

    async def _validate_service_token(self, request: Request, token: str) -> ServiceTokenUser:
        """Validate service token against database.

        Args:
            request: HTTP request
            token: Service token string

        Returns:
            ServiceTokenUser with validated token information

        Raises:
            AuthenticationError: If validation fails
        """
        try:
            # Hash the token for database lookup
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Get database session and validate token
            async for session in get_db():
                # Query for active, non-expired token
                result = await session.execute(
                    text(
                        """
                        SELECT id, token_name, token_metadata, usage_count, is_active,
                               CASE
                                   WHEN expires_at IS NULL THEN FALSE
                                   WHEN expires_at > NOW() THEN FALSE
                                   ELSE TRUE
                               END as is_expired
                        FROM service_tokens
                        WHERE token_hash = :token_hash
                    """,
                    ),
                    {"token_hash": token_hash},
                )

                token_record = result.fetchone()

                if not token_record:
                    await self._log_authentication_event(
                        request,
                        event_type="service_token_auth",
                        success=False,
                        error_details={"error": "token_not_found"},
                    )
                    raise AuthenticationError("Invalid service token", 401)

                # Check if token is active and not expired
                if not token_record.is_active:
                    await self._log_authentication_event(
                        request,
                        service_token_name=token_record.token_name,
                        event_type="service_token_auth",
                        success=False,
                        error_details={"error": "token_inactive"},
                    )
                    raise AuthenticationError("Service token is inactive", 401)

                if token_record.is_expired:
                    await self._log_authentication_event(
                        request,
                        service_token_name=token_record.token_name,
                        event_type="service_token_auth",
                        success=False,
                        error_details={"error": "token_expired"},
                    )
                    raise AuthenticationError("Service token has expired", 401)

                # Update usage count and last_used timestamp
                await session.execute(
                    text(
                        """
                        UPDATE service_tokens
                        SET usage_count = usage_count + 1, last_used = NOW()
                        WHERE token_hash = :token_hash
                    """,
                    ),
                    {"token_hash": token_hash},
                )
                await session.commit()

                # Log successful authentication
                await self._log_authentication_event(
                    request,
                    service_token_name=token_record.token_name,
                    event_type="service_token_auth",
                    success=True,
                )

                # Create ServiceTokenUser
                service_user = ServiceTokenUser(
                    token_id=str(token_record.id),
                    token_name=token_record.token_name,
                    metadata=token_record.token_metadata or {},
                    usage_count=token_record.usage_count + 1,
                )

                return service_user

        except AuthenticationError:
            # Re-raise authentication errors as-is
            raise
        except Exception as e:
            logger.error(f"Service token validation error: {e}")
            await self._log_authentication_event(
                request,
                event_type="service_token_auth",
                success=False,
                error_details={"error": "validation_exception", "details": str(e)},
            )
            raise AuthenticationError("Service token validation failed", 500) from e

    def _extract_auth_token(self, request: Request) -> str | None:
        """Extract authentication token (JWT or Service Token) from headers.

        Args:
            request: HTTP request

        Returns:
            Authentication token string if found, None otherwise
        """
        # Primary: Cloudflare Access JWT header
        cf_access_jwt = request.headers.get("CF-Access-Jwt-Assertion")
        if cf_access_jwt:
            logger.debug("Found JWT token in CF-Access-Jwt-Assertion header")
            return cf_access_jwt

        # Standard Authorization header (supports both JWT and Service Tokens)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            token_type = "service token" if token.startswith("sk_") else "JWT token"
            logger.debug(f"Found {token_type} in Authorization header")
            return token

        # Fallback: Custom header for testing/development
        custom_jwt = request.headers.get("X-JWT-Token")
        if custom_jwt:
            logger.debug("Found JWT token in X-JWT-Token header")
            return custom_jwt

        # Service token specific headers (for non-interactive access)
        service_token = request.headers.get("X-Service-Token")
        if service_token:
            logger.debug("Found service token in X-Service-Token header")
            return service_token

        logger.debug("No authentication token found in request headers")
        return None

    def _extract_jwt_token(self, request: Request) -> str | None:
        """Extract JWT token from Cloudflare Access headers (legacy method).

        Args:
            request: HTTP request

        Returns:
            JWT token string if found, None otherwise
        """
        return self._extract_auth_token(request)

    async def _log_authentication_event(
        self,
        request: Request,
        user_email: str | None = None,
        service_token_name: str | None = None,
        event_type: str = "auth",
        success: bool = True,
        error_details: dict | None = None,
    ) -> None:
        """Log authentication event to database.

        Args:
            request: HTTP request
            user_email: User email (for JWT auth)
            service_token_name: Service token name (for service token auth)
            event_type: Type of authentication event
            success: Whether authentication was successful
            error_details: Error details for failed authentication
        """
        try:
            async for session in get_db():
                # For service tokens, use service_token_name as user_email
                # For JWT auth, use provided user_email
                # For failures with no user context, use "unknown"
                final_user_email = user_email or service_token_name or "unknown"

                # If we have service token info, add it to error_details for context
                final_error_details = error_details or {}
                if service_token_name and event_type == "service_token_auth":
                    final_error_details["service_token_name"] = service_token_name

                # Create authentication event record
                auth_event = AuthenticationEvent(
                    user_email=final_user_email,
                    event_type=event_type,
                    success=success,
                    ip_address=(
                        getattr(request.client, "host", None) if hasattr(request, "client") and request.client else None
                    ),
                    user_agent=request.headers.get("user-agent"),
                    cloudflare_ray_id=request.headers.get("cf-ray"),
                    error_details=final_error_details if final_error_details else None,
                )

                session.add(auth_event)
                await session.commit()

                break  # Only need first session

        except Exception as e:
            # Don't fail authentication due to logging errors
            logger.warning(f"Failed to log authentication event: {e}")

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

    async def _update_user_session(self, authenticated_user: AuthenticatedUser, request: Request) -> None:
        """Update user session in database with graceful degradation.

        Args:
            authenticated_user: Authenticated user information
            request: HTTP request for context
        """
        if not self.database_enabled:
            return

        try:
            # Use the legacy get_db() which works as async context manager
            async for session in get_db():
                # Extract Cloudflare subject from JWT claims
                cloudflare_sub = authenticated_user.jwt_claims.get("sub", "unknown")

                # Try to find existing session
                stmt = select(UserSession).where(UserSession.email == authenticated_user.email)
                result = await session.execute(stmt)
                existing_session = result.scalar_one_or_none()

                if existing_session:
                    # Update existing session
                    update_stmt = (
                        update(UserSession)
                        .where(
                            UserSession.email == authenticated_user.email,
                        )
                        .values(
                            session_count=UserSession.session_count + 1,
                            last_seen=func.now(),
                            cloudflare_sub=cloudflare_sub,
                        )
                    )
                    await session.execute(update_stmt)
                else:
                    # Create new session
                    new_session = UserSession(
                        email=authenticated_user.email,
                        cloudflare_sub=cloudflare_sub,
                        session_count=1,
                        preferences={},
                        user_metadata={},
                    )
                    session.add(new_session)

                await session.commit()
                # Break after first (and only) session
                break

        except DatabaseError as e:
            # Log database errors but don't fail authentication
            logger.warning(f"Database session update failed (graceful degradation): {e}")
        except Exception as e:
            # Log unexpected errors but don't fail authentication
            logger.warning(f"Unexpected error updating session (graceful degradation): {e}")

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP address from request headers.

        Args:
            request: HTTP request

        Returns:
            Client IP address or None if not available
        """
        # Check Cloudflare headers first
        cf_connecting_ip = request.headers.get("CF-Connecting-IP")
        if cf_connecting_ip:
            return cf_connecting_ip

        # Check standard forwarded headers
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Take the first IP in the chain
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip

        # Fallback to client host
        if hasattr(request, "client") and request.client:
            # Ensure we get a string, not a MagicMock object
            host = getattr(request.client, "host", None)
            if host and isinstance(host, str):
                # Validate it looks like a reasonable IP address (max 39 chars for IPv6)
                if len(host) <= 39:
                    return host
                return None
            try:
                host_str = str(host)
                # Validate it looks like an IP address (max 39 chars for IPv6)
                if len(host_str) <= 39:
                    return host_str
            except Exception:  # nosec B110  # noqa: S110
                # Silently ignore IP parsing errors - acceptable for IP extraction
                pass

        return None


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
    database_enabled: bool = True,
) -> Limiter:
    """Setup authentication middleware and rate limiting for FastAPI app.

    Args:
        app: FastAPI application instance
        config: Authentication configuration
        database_enabled: Whether database integration is enabled

    Returns:
        Limiter instance
    """
    # Create JWKS client (compatibility placeholder)
    jwks_client = None  # Placeholder for compatibility

    # Create JWT validator
    jwt_validator = JWTValidator(
        jwks_client=jwks_client,
        audience=config.cloudflare_audience,
        issuer=config.cloudflare_issuer,
        algorithm=config.jwt_algorithm,
    )

    # Add middleware using standard FastAPI method with kwargs
    app.add_middleware(
        AuthenticationMiddleware,
        config=config,
        jwt_validator=jwt_validator,
        database_enabled=database_enabled,
    )

    # Setup rate limiting only if enabled
    limiter = None
    if config.rate_limiting_enabled:
        limiter = create_rate_limiter(config)
        app.add_middleware(SlowAPIMiddleware)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    else:
        # Create a dummy limiter for compatibility but don't set app.state.limiter
        limiter = create_rate_limiter(config)

    logger.info("Authentication middleware and rate limiting configured")

    return limiter


def get_current_user(request: Request) -> AuthenticatedUser | None:
    """Get current authenticated user from request state.

    Args:
        request: HTTP request

    Returns:
        AuthenticatedUser if authenticated, None otherwise
    """
    # Handle case where request.state doesn't exist
    if not hasattr(request, "state"):
        return None
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
