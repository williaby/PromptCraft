"""FastAPI middleware for simplified Cloudflare Access authentication.

This module provides streamlined authentication middleware that integrates
Cloudflare Access header extraction with email whitelist validation,
replacing complex JWT validation with simple header-based authentication.
"""

from collections.abc import Callable
from datetime import datetime
import logging
import secrets
from typing import Any

from fastapi import HTTPException, Request, Response
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.utils.datetime_compat import UTC

from .cloudflare_auth import CloudflareAuthError, CloudflareAuthHandler
from .whitelist import EmailWhitelistValidator


logger = logging.getLogger(__name__)


class SimpleSessionManager:
    """In-memory session management for streamlined authentication."""

    def __init__(self, session_timeout: int = 3600) -> None:
        """Initialize session manager.

        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: dict[str, dict] = {}
        self.session_timeout = session_timeout
        logger.info("Initialized session manager with %ss timeout", session_timeout)

    def create_session(
        self,
        email: str,
        is_admin: bool,
        user_tier: str,
        cf_context: dict[str, Any] | None = None,
    ) -> str:
        """Create a new session for the user.

        Args:
            email: User email address
            is_admin: Whether user has admin privileges
            user_tier: User tier (admin, full, limited)
            cf_context: Additional Cloudflare context

        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            "email": email,
            "is_admin": is_admin,
            "user_tier": user_tier,
            "created_at": datetime.now(UTC),
            "last_accessed": datetime.now(UTC),
            "cf_context": cf_context or {},
        }

        logger.debug("Created session %s for %s (admin: %s, tier: %s)", session_id, email, is_admin, user_tier)
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        """Get session if valid, clean up if expired.

        Args:
            session_id: Session identifier

        Returns:
            Session data if valid, None if expired or not found
        """
        if not session_id:
            return None

        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check if session is expired
        if self._is_session_expired(session):
            logger.debug("Session %s expired, removing", session_id)
            del self.sessions[session_id]
            return None

        # Update last accessed time
        session["last_accessed"] = datetime.now(UTC)
        return session

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session.

        Args:
            session_id: Session to invalidate

        Returns:
            True if session was found and removed
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.debug("Invalidated session %s", session_id)
            return True
        return False

    def _is_session_expired(self, session: dict) -> bool:
        """Check if session has expired."""
        from datetime import timedelta

        expiry = session["last_accessed"] + timedelta(seconds=self.session_timeout)
        return bool(datetime.now(UTC) > expiry)

    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions from memory."""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items() if self._is_session_expired(session)
        ]

        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            logger.debug("Cleaned up %s expired sessions", len(expired_sessions))


class CloudflareAccessMiddleware:
    """Streamlined Cloudflare Access middleware for email whitelist authentication.

    This middleware:
    1. Extracts user email from Cloudflare Access headers
    2. Validates email against whitelist
    3. Manages simple sessions
    4. Injects user context into request
    5. Handles authentication errors gracefully
    """

    def __init__(
        self,
        app: ASGIApp,
        whitelist_validator: EmailWhitelistValidator,
        session_manager: SimpleSessionManager | None = None,
        public_paths: set[str] | None = None,
        health_check_paths: set[str] | None = None,
        enable_session_cookies: bool = True,
    ) -> None:
        """Initialize the middleware.

        Args:
            app: ASGI application
            whitelist_validator: Email whitelist validator
            session_manager: Session manager (creates default if None)
            public_paths: Paths that don't require authentication
            health_check_paths: Health check paths (always public)
            enable_session_cookies: Whether to use session cookies
        """
        self.app = app
        self.validator = whitelist_validator
        self.whitelist_validator = whitelist_validator  # Alias for setup function compatibility
        self.session_manager = session_manager or SimpleSessionManager()
        self.cloudflare_auth = CloudflareAuthHandler()
        self.enable_session_cookies = enable_session_cookies

        # Default public paths
        self.public_paths = public_paths or {
            "/",
            "/ping",  # Basic application endpoints
            "/health",
            "/api/health",
            "/api/v1/health",  # Health endpoints
            "/docs",
            "/openapi.json",
            "/redoc",  # Documentation endpoints
            "/api/v1/validate",
            "/api/v1/search",  # Test/demo endpoints
        }
        self.health_check_paths = health_check_paths or {
            "/health",
            "/api/health",
            "/api/v1/health",
            "/health/config",
            "/health/mcp",
            "/health/circuit-breakers",
            "/api/v1/system/health",
            "/api/v1/auth/health",
            "/api/v1/create/health",
        }

        # Combine all public paths
        self.all_public_paths = self.public_paths | self.health_check_paths

        logger.info("Initialized Cloudflare Access middleware with %s public paths", len(self.all_public_paths))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Compatibility method for BaseHTTPMiddleware pattern."""
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)  # type: ignore[no-any-return]

        # Handle authentication
        try:
            await self._authenticate_request(request)
            response = await call_next(request)

            # Handle session cookies if enabled and new session was created
            if self.enable_session_cookies and hasattr(request.state, "user") and request.state.user.get("session_id"):
                # Check if this is a new session (not from existing cookie)
                session_id = request.state.user.get("session_id")
                existing_session_id = request.cookies.get("session_id")

                if session_id != existing_session_id:
                    # This is a new session, set the cookie and state
                    request.state.new_session_id = session_id
                    self._set_session_cookie(response, session_id)

            return response  # type: ignore[no-any-return]
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            logger.error("Middleware error: %s", e)
            return JSONResponse(status_code=500, content={"detail": "Internal authentication error"})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI middleware implementation.

        Args:
            scope: ASGI scope dict
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        try:
            # Skip authentication for public paths
            if self._is_public_path(request.url.path):
                await self.app(scope, receive, send)
                return

            # Handle authentication
            await self._authenticate_request(request)

            # Wrap send to intercept and modify response for session cookies
            if self.enable_session_cookies and hasattr(request.state, "user") and request.state.user.get("session_id"):

                # Check if this is a new session
                session_id = request.state.user.get("session_id")
                existing_session_id = request.cookies.get("session_id")

                if session_id != existing_session_id:
                    # Wrap send to add session cookie
                    send = self._wrap_send_for_session_cookie(send, session_id)

            # Continue to app
            await self.app(scope, receive, send)

        except HTTPException as e:
            # Convert HTTP exceptions to JSON responses
            response = JSONResponse(status_code=e.status_code, content={"detail": e.detail})
            await response(scope, receive, send)
        except Exception as e:
            logger.error("Middleware error: %s", e)
            response = JSONResponse(status_code=500, content={"detail": "Internal authentication error"})
            await response(scope, receive, send)

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no authentication required)."""
        return path in self.all_public_paths or path.startswith("/static/")

    async def _authenticate_request(self, request: Request) -> None:
        """Authenticate the request and set user context.

        Args:
            request: Request to authenticate

        Raises:
            HTTPException: If authentication fails
        """
        # Extract user from Cloudflare headers
        try:
            cloudflare_user = self.cloudflare_auth.extract_user_from_request(request)
        except CloudflareAuthError as e:
            logger.warning("Cloudflare authentication failed: %s", e)
            raise HTTPException(status_code=401, detail="No authenticated user found") from e

        # Validate against whitelist
        if not self.validator.is_authorized(cloudflare_user.email):
            logger.warning("Unauthorized email attempted access: %s", cloudflare_user.email)
            raise HTTPException(status_code=403, detail=f"Email {cloudflare_user.email} not authorized")

        # Get user tier information
        user_tier = self.validator.get_user_tier(cloudflare_user.email)

        # Check for existing session first
        session_id = None
        session_data = None
        existing_session_id = request.cookies.get("session_id")

        if existing_session_id:
            session_data = self.session_manager.get_session(existing_session_id)
            if session_data and session_data["email"] == cloudflare_user.email:
                # Use existing session but update with current tier info
                session_id = existing_session_id
                # Update session data with current tier information
                session_data["user_tier"] = user_tier.value
                session_data["is_admin"] = user_tier.has_admin_privileges
                session_data["can_access_premium"] = user_tier.can_access_premium_models

        if not session_id:
            # Create new session if no valid existing session
            try:
                session_id = self.session_manager.create_session(
                    email=cloudflare_user.email,
                    is_admin=user_tier.has_admin_privileges,
                    user_tier=user_tier.value,
                    cf_context={},
                )
                # Verify session was created successfully
                if not session_id or not self.session_manager.get_session(session_id):
                    raise HTTPException(status_code=500, detail="Session creation failed")
            except Exception as e:
                if isinstance(e, HTTPException):
                    raise
                logger.error("Session creation error: %s", e)
                raise HTTPException(status_code=500, detail="Session creation failed") from e

        # Create user context with session
        request.state.user = {
            "email": cloudflare_user.email,
            "is_admin": user_tier.has_admin_privileges,
            "user_tier": user_tier.value,
            "role": "admin" if user_tier.has_admin_privileges else "user",
            "can_access_premium": user_tier.can_access_premium_models,
            "session_id": session_id,
            "authenticated_at": session_data.get("authenticated_at") if session_data else datetime.now(UTC),
            "cf_context": session_data.get("cf_context", {}) if session_data else {},
        }

        logger.debug(
            "Authenticated user %s with tier %s (premium access: %s)",
            cloudflare_user.email,
            user_tier.value,
            user_tier.can_access_premium_models,
        )

    def _set_session_cookie(self, response: Response, session_id: str) -> None:
        """Set session cookie in response.

        Args:
            response: Response to modify
            session_id: Session ID to set
        """
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=self.session_manager.session_timeout,
        )

    def _wrap_send_for_session_cookie(self, send: Send, session_id: str) -> Send:
        """Wrap the ASGI send callable to add session cookie to response.

        Args:
            send: Original ASGI send callable
            session_id: Session ID to set in cookie

        Returns:
            Wrapped send callable that adds session cookie
        """

        async def wrapped_send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                # Create cookie header
                cookie_value = (
                    f"session_id={session_id}; "
                    f"Max-Age={self.session_manager.session_timeout}; "
                    "HttpOnly; Secure; SameSite=Strict"
                )
                headers.append([b"set-cookie", cookie_value.encode()])

                # Update message with new headers
                message = {**message, "headers": headers}

            await send(message)

        return wrapped_send  # type: ignore[return-value]


class AuthenticationDependency:
    """FastAPI dependency for authentication in route handlers."""

    def __init__(self, require_admin: bool = False) -> None:
        """Initialize authentication dependency.

        Args:
            require_admin: Whether to require admin privileges
        """
        self.require_admin = require_admin

    def __call__(self, request: Request) -> dict[str, Any]:
        """Extract and validate user from request state.

        Args:
            request: FastAPI request

        Returns:
            User context dictionary

        Raises:
            HTTPException: If authentication fails or insufficient privileges
        """
        if not hasattr(request.state, "user"):
            raise HTTPException(status_code=401, detail="Authentication required")

        user = request.state.user

        if self.require_admin and not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin privileges required")

        return user  # type: ignore[no-any-return]  # request.state.user is dynamically set


# Convenience dependency instances
require_auth = AuthenticationDependency(require_admin=False)
require_admin = AuthenticationDependency(require_admin=True)


def create_auth_middleware(
    whitelist_str: str,
    admin_emails_str: str = "",
    full_users_str: str = "",
    limited_users_str: str = "",
    session_timeout: int = 3600,
    public_paths: set[str] | None = None,
) -> CloudflareAccessMiddleware:
    """Factory function to create authentication middleware from configuration.

    Args:
        whitelist_str: Comma-separated whitelist emails/domains
        admin_emails_str: Comma-separated admin emails
        full_users_str: Comma-separated full tier users
        limited_users_str: Comma-separated limited tier users
        session_timeout: Session timeout in seconds
        public_paths: Additional public paths (optional)

    Returns:
        Configured CloudflareAccessMiddleware
    """
    from .whitelist import create_validator_from_env

    # Create whitelist validator with tier support
    validator = create_validator_from_env(whitelist_str, admin_emails_str, full_users_str, limited_users_str)

    # Create session manager
    session_manager = SimpleSessionManager(session_timeout=session_timeout)

    # Create and return middleware
    return CloudflareAccessMiddleware(
        app=None,  # type: ignore[arg-type] # Will be set by FastAPI
        whitelist_validator=validator,
        session_manager=session_manager,
        public_paths=public_paths,
    )
