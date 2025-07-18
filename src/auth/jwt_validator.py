"""JWT validation module for Cloudflare Access authentication.

This module provides secure JWT token validation including:
- Signature verification against JWKS
- Payload extraction and email claim validation
- Expiration and audience validation
- Security-focused error handling
"""

import logging
from typing import Any

import jwt
from jwt.algorithms import RSAAlgorithm

from .jwks_client import JWKSClient
from .models import AuthenticatedUser, JWTValidationError, UserRole

logger = logging.getLogger(__name__)


class JWTValidator:
    """Validator for Cloudflare Access JWT tokens."""

    def __init__(
        self,
        jwks_client: JWKSClient,
        audience: str | None = None,
        issuer: str | None = None,
        algorithm: str = "RS256",
    ) -> None:
        """Initialize JWT validator.

        Args:
            jwks_client: JWKS client for key retrieval
            audience: Expected audience (aud) claim
            issuer: Expected issuer (iss) claim
            algorithm: JWT algorithm (default RS256)
        """
        self.jwks_client = jwks_client
        self.audience = audience
        self.issuer = issuer
        self.algorithm = algorithm

    def validate_token(self, token: str, email_whitelist: list[str] | None = None) -> AuthenticatedUser:
        """Validate JWT token and extract user information.

        Args:
            token: JWT token string
            email_whitelist: Optional list of allowed email addresses/domains

        Returns:
            AuthenticatedUser with validated user information

        Raises:
            JWTValidationError: If token validation fails
        """
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise JWTValidationError("JWT token missing 'kid' in header", "missing_kid")

            # Get signing key from JWKS
            key_dict = self.jwks_client.get_key_by_kid(kid)
            if not key_dict:
                raise JWTValidationError(f"Key with kid '{kid}' not found in JWKS", "key_not_found")

            # Convert JWK to RSA public key
            try:
                public_key = RSAAlgorithm.from_jwk(key_dict)
            except Exception as e:
                logger.error(f"Failed to convert JWK to public key: {e}")
                raise JWTValidationError(f"Invalid JWK format: {e}", "invalid_jwk") from e

            # Prepare verification options
            verify_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "require": ["exp", "iat", "email"],
            }

            # Add audience/issuer verification if configured
            if self.audience:
                verify_options["verify_aud"] = True
            if self.issuer:
                verify_options["verify_iss"] = True

            # Decode and validate token
            try:
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=[self.algorithm],
                    audience=self.audience,
                    issuer=self.issuer,
                    options=verify_options,
                )
            except jwt.ExpiredSignatureError as e:
                logger.warning("JWT token has expired")
                raise JWTValidationError("Token has expired", "expired_token") from e
            except jwt.InvalidTokenError as e:
                logger.warning(f"JWT token validation failed: {e}")
                raise JWTValidationError(f"Invalid token: {e}", "invalid_token") from e

            # Extract and validate email from payload (CRITICAL: not from headers)
            email = payload.get("email")
            if not email:
                raise JWTValidationError("JWT payload missing required 'email' claim", "missing_email")

            if not isinstance(email, str) or "@" not in email:
                raise JWTValidationError("Invalid email format in JWT payload", "invalid_email")

            # Validate email against whitelist if provided
            if email_whitelist and not self._is_email_allowed(email, email_whitelist):
                logger.warning(f"Email '{email}' not in whitelist")
                raise JWTValidationError(f"Email '{email}' not authorized", "email_not_authorized")

            # Determine user role (basic implementation)
            role = self._determine_user_role(email, payload)

            logger.info(f"Successfully validated JWT for user: {email}")

            return AuthenticatedUser(
                email=email,
                role=role,
                jwt_claims=payload,
            )

        except JWTValidationError:
            # Re-raise JWT validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {e}")
            raise JWTValidationError(f"Unexpected validation error: {e}", "unknown_error") from e

    def _is_email_allowed(self, email: str, email_whitelist: list[str]) -> bool:
        """Check if email is allowed based on whitelist.

        Args:
            email: Email address to check
            email_whitelist: List of allowed emails or domains

        Returns:
            True if email is allowed, False otherwise
        """
        email_lower = email.lower()

        for allowed in email_whitelist:
            allowed_lower = allowed.lower()

            # Exact email match
            if email_lower == allowed_lower:
                return True

            # Domain match (if allowed entry starts with @)
            if allowed_lower.startswith("@") and email_lower.endswith(allowed_lower):
                return True

        return False

    def _determine_user_role(self, email: str, payload: dict[str, Any]) -> UserRole:
        """Determine user role based on email and JWT claims.

        Args:
            email: User email address
            payload: JWT payload

        Returns:
            UserRole for the user
        """
        # Basic role determination - can be enhanced later
        # Check for admin indicators in email or claims
        if any(admin_indicator in email.lower() for admin_indicator in ["admin", "owner"]):
            return UserRole.ADMIN

        # Check for admin role in JWT claims (if Cloudflare provides it)
        groups = payload.get("groups", [])
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, str) and "admin" in group.lower():
                    return UserRole.ADMIN

        # Default to user role
        return UserRole.USER

    def validate_token_format(self, token: str) -> bool:
        """Basic token format validation without signature verification.

        Args:
            token: JWT token string

        Returns:
            True if token format is valid, False otherwise
        """
        try:
            # Check basic JWT format (3 parts separated by dots)
            parts = token.split(".")
            if len(parts) != 3:
                return False

            # Try to decode header without verification
            jwt.get_unverified_header(token)
            return True

        except Exception:
            return False
