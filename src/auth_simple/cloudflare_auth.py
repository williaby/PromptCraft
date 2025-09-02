"""Cloudflare Access authentication handler.

This module provides simplified Cloudflare Access authentication through header extraction
and validation, replacing the complex 22K+ line authentication system with a streamlined
approach focused on the Cf-Access-Authenticated-User-Email header.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class CloudflareUser(BaseModel):
    """User information extracted from Cloudflare Access headers."""

    email: str
    authenticated_at: datetime = datetime.utcnow()
    source: str = "cloudflare_access"
    headers: dict[str, str] = {}

    @validator("email")
    def validate_email(cls, v):
        """Ensure email is valid format."""
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()


class CloudflareAuthError(Exception):
    """Cloudflare authentication specific error."""


class CloudflareAuthHandler:
    """Simplified Cloudflare Access authentication handler.

    Extracts and validates user information from Cloudflare Access headers,
    specifically the Cf-Access-Authenticated-User-Email header that Cloudflare
    forwards after successful authentication.
    """

    def __init__(self, validate_headers: bool = True, log_events: bool = True):
        """Initialize the Cloudflare auth handler.

        Args:
            validate_headers: Whether to validate Cloudflare-specific headers
            log_events: Whether to log authentication events
        """
        self.validate_headers = validate_headers
        self.log_events = log_events
        self.cloudflare_headers = ["cf-access-authenticated-user-email", "cf-ray", "cf-ipcountry", "cf-connecting-ip"]

    def extract_user_from_request(self, request: Request) -> CloudflareUser:
        """Extract user information from Cloudflare Access headers.

        Args:
            request: FastAPI request object

        Returns:
            CloudflareUser object with extracted information

        Raises:
            CloudflareAuthError: If authentication headers are missing or invalid
        """
        try:
            # Extract primary authentication header
            user_email = self._extract_user_email(request)
            if not user_email:
                raise CloudflareAuthError("No authenticated user email found in headers")

            # Extract additional Cloudflare context
            headers = self._extract_cloudflare_headers(request)

            # Create user object
            user = CloudflareUser(email=user_email, headers=headers, authenticated_at=datetime.utcnow())

            if self.log_events:
                self._log_authentication_event(user, request)

            return user

        except Exception as e:
            if self.log_events:
                logger.error(f"Cloudflare authentication failed: {e!s}")
            raise CloudflareAuthError(f"Authentication failed: {e!s}")

    def _extract_user_email(self, request: Request) -> str | None:
        """Extract user email from Cloudflare Access headers.

        Checks multiple possible header variations that Cloudflare might use.
        """
        email_headers = [
            "cf-access-authenticated-user-email",
            "x-cf-access-authenticated-user-email",
            "cf-authenticated-user-email",
        ]

        for header_name in email_headers:
            email = request.headers.get(header_name)
            if email:
                return email.strip().lower()

        return None

    def _extract_cloudflare_headers(self, request: Request) -> dict[str, str]:
        """Extract all relevant Cloudflare headers for context."""
        headers = {}

        for header_name in self.cloudflare_headers:
            value = request.headers.get(header_name)
            if value:
                headers[header_name] = value

        # Also capture request metadata
        headers.update(
            {
                "user_agent": request.headers.get("user-agent", ""),
                "host": request.headers.get("host", ""),
                "x_forwarded_for": request.headers.get("x-forwarded-for", ""),
                "referer": request.headers.get("referer", ""),
            },
        )

        return headers

    def _log_authentication_event(self, user: CloudflareUser, request: Request):
        """Log authentication event for audit purposes."""
        log_data = {
            "event": "cloudflare_auth_success",
            "user_email": user.email,
            "timestamp": user.authenticated_at.isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "cf_ray": user.headers.get("cf-ray", "unknown"),
            "ip_country": user.headers.get("cf-ipcountry", "unknown"),
            "connecting_ip": user.headers.get("cf-connecting-ip", "unknown"),
        }

        logger.info(f"Cloudflare authentication successful: {log_data}")

    def validate_request_headers(self, request: Request) -> bool:
        """Validate that request contains expected Cloudflare headers.

        This provides additional validation that the request actually came
        through Cloudflare Access and wasn't spoofed.
        """
        if not self.validate_headers:
            return True

        required_headers = ["cf-ray"]  # CF-Ray is always present from Cloudflare

        for header in required_headers:
            if not request.headers.get(header):
                if self.log_events:
                    logger.warning(f"Missing required Cloudflare header: {header}")
                return False

        return True

    def create_user_context(self, user: CloudflareUser) -> dict[str, Any]:
        """Create user context dictionary for use in application.

        Args:
            user: CloudflareUser object

        Returns:
            Dictionary containing user context for downstream use
        """
        return {
            "email": user.email,
            "authenticated": True,
            "auth_method": "cloudflare_access",
            "authenticated_at": user.authenticated_at,
            "cf_ray": user.headers.get("cf-ray"),
            "ip_country": user.headers.get("cf-ipcountry"),
            "connecting_ip": user.headers.get("cf-connecting-ip"),
        }


def extract_user_from_cloudflare_headers(request: Request) -> CloudflareUser:
    """Convenience function to extract user from Cloudflare headers.

    Args:
        request: FastAPI request object

    Returns:
        CloudflareUser object

    Raises:
        HTTPException: If authentication fails (401)
    """
    try:
        handler = CloudflareAuthHandler()
        return handler.extract_user_from_request(request)
    except CloudflareAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


def validate_cloudflare_request(request: Request) -> bool:
    """Validate that request came through Cloudflare Access.

    Args:
        request: FastAPI request object

    Returns:
        True if validation passes, False otherwise
    """
    try:
        handler = CloudflareAuthHandler()
        return handler.validate_request_headers(request)
    except Exception as e:
        logger.error(f"Cloudflare request validation failed: {e}")
        return False
