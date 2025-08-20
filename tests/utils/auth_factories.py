"""Factory utilities for creating authentication test objects with proper isolation.

This module provides factory functions for creating consistent, isolated test instances
of authentication components. These factories ensure clean test isolation by creating
fresh instances with no shared state between tests.
"""

import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import Mock

from src.auth.config import AuthenticationConfig
from src.auth.jwks_client import JWKSClient
from src.auth.jwt_validator import JWTValidator
from src.auth.models import AuthenticatedUser, UserRole


class JWTValidatorFactory:
    """Factory for creating JWTValidator instances with proper test isolation."""

    @staticmethod
    def create_mock_jwks_client(
        key_data: Optional[Dict[str, Any]] = None,
        side_effects: Optional[Dict[str, Any]] = None,
    ) -> Mock:
        """Create a mock JWKS client with configurable behavior.

        Args:
            key_data: Custom key data to return (uses default if None)
            side_effects: Dictionary mapping method names to side effects

        Returns:
            Mock JWKSClient with specified behavior
        """
        if key_data is None:
            key_data = {
                "kty": "RSA",
                "use": "sig",
                "kid": "test-key-id",
                "n": "test-modulus",
                "e": "AQAB",
            }

        client = Mock(spec=JWKSClient)
        client.get_key_by_kid.return_value = key_data

        # Apply any side effects
        if side_effects:
            for method_name, side_effect in side_effects.items():
                if hasattr(client, method_name):
                    getattr(client, method_name).side_effect = side_effect

        return client

    @staticmethod
    def create_mock_config(
        email_whitelist: Optional[list[str]] = None,
        **overrides: Any,
    ) -> Mock:
        """Create a mock AuthenticationConfig with configurable values.

        Args:
            email_whitelist: List of allowed emails/domains
            **overrides: Additional config values to override

        Returns:
            Mock AuthenticationConfig instance
        """
        config = Mock(spec=AuthenticationConfig)
        config.email_whitelist = email_whitelist or ["test@example.com"]

        # Apply any overrides
        for key, value in overrides.items():
            setattr(config, key, value)

        return config

    @staticmethod
    def create_validator(
        jwks_client: Optional[Mock] = None,
        config: Optional[Mock] = None,
        audience: str = "https://test-app.com",
        issuer: str = "https://test.cloudflareaccess.com",
        algorithm: str = "RS256",
    ) -> JWTValidator:
        """Create a JWTValidator instance with optional mocked dependencies.

        Args:
            jwks_client: Mock JWKS client (creates default if None)
            config: Mock config (creates default if None)
            audience: JWT audience
            issuer: JWT issuer
            algorithm: JWT algorithm

        Returns:
            JWTValidator instance with clean dependencies
        """
        if jwks_client is None:
            jwks_client = JWTValidatorFactory.create_mock_jwks_client()

        if config is None:
            config = JWTValidatorFactory.create_mock_config()

        return JWTValidator(
            jwks_client=jwks_client,
            config=config,
            audience=audience,
            issuer=issuer,
            algorithm=algorithm,
        )


class JWTTokenFactory:
    """Factory for creating JWT tokens with various test scenarios."""

    @staticmethod
    def create_payload(
        email: str = "test@example.com",
        issuer: str = "https://test.cloudflareaccess.com",
        audience: str = "https://test-app.com",
        exp_minutes: int = 60,
        **overrides: Any,
    ) -> Dict[str, Any]:
        """Create a JWT payload with configurable claims.

        Args:
            email: Email claim
            issuer: Issuer claim
            audience: Audience claim
            exp_minutes: Expiration time in minutes from now
            **overrides: Additional claims to add/override

        Returns:
            JWT payload dictionary
        """
        now = datetime.now(UTC)
        payload = {
            "iss": issuer,
            "aud": audience,
            "sub": "user123",
            "email": email,
            "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
        }

        # Apply overrides
        payload.update(overrides)

        return payload

    @staticmethod
    def create_header(
        kid: str = "test-key-id",
        alg: str = "RS256",
        typ: str = "JWT",
        **overrides: Any,
    ) -> Dict[str, Any]:
        """Create a JWT header with configurable values.

        Args:
            kid: Key ID
            alg: Algorithm
            typ: Token type
            **overrides: Additional header claims

        Returns:
            JWT header dictionary
        """
        header = {"alg": alg, "typ": typ, "kid": kid}
        header.update(overrides)
        return header

    @staticmethod
    def encode_token(
        payload: Dict[str, Any],
        header: Optional[Dict[str, Any]] = None,
        signature: str = "fake-signature",
    ) -> str:
        """Encode a JWT token from payload and header.

        Args:
            payload: JWT payload
            header: JWT header (uses default if None)
            signature: Mock signature

        Returns:
            Encoded JWT token string
        """
        if header is None:
            header = JWTTokenFactory.create_header()

        # Encode header and payload
        header_encoded = (
            base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
            .decode("utf-8")
            .rstrip("=")
        )

        payload_encoded = (
            base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
            .decode("utf-8")
            .rstrip("=")
        )

        # Create signature
        signature_encoded = base64.urlsafe_b64encode(signature.encode("utf-8")).decode("utf-8").rstrip("=")

        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

    @staticmethod
    def create_valid_token(**kwargs: Any) -> str:
        """Create a valid JWT token with customizable claims.

        Args:
            **kwargs: Claims to override in payload

        Returns:
            Valid JWT token string
        """
        payload = JWTTokenFactory.create_payload(**kwargs)
        return JWTTokenFactory.encode_token(payload)

    @staticmethod
    def create_expired_token(**kwargs: Any) -> str:
        """Create an expired JWT token.

        Args:
            **kwargs: Additional claims to override

        Returns:
            Expired JWT token string
        """
        kwargs.setdefault("exp_minutes", -60)  # Expired 1 hour ago
        payload = JWTTokenFactory.create_payload(**kwargs)
        return JWTTokenFactory.encode_token(payload)

    @staticmethod
    def create_token_missing_kid(**kwargs: Any) -> str:
        """Create a token missing the 'kid' header.

        Args:
            **kwargs: Claims to override in payload

        Returns:
            JWT token without 'kid' header
        """
        payload = JWTTokenFactory.create_payload(**kwargs)
        header = JWTTokenFactory.create_header()
        del header["kid"]
        return JWTTokenFactory.encode_token(payload, header)

    @staticmethod
    def create_token_missing_email(**kwargs: Any) -> str:
        """Create a token missing the 'email' claim.

        Args:
            **kwargs: Additional claims to override

        Returns:
            JWT token without email claim
        """
        payload = JWTTokenFactory.create_payload(**kwargs)
        del payload["email"]
        return JWTTokenFactory.encode_token(payload)

    @staticmethod
    def create_malformed_token() -> str:
        """Create a malformed JWT token.

        Returns:
            Malformed JWT token string
        """
        return "invalid.token.format"


class AuthenticatedUserFactory:
    """Factory for creating AuthenticatedUser instances for testing."""

    @staticmethod
    def create_user(
        email: str = "test@example.com",
        role: UserRole = UserRole.USER,
        jwt_claims: Optional[Dict[str, Any]] = None,
        **overrides: Any,
    ) -> AuthenticatedUser:
        """Create an AuthenticatedUser instance.

        Args:
            email: User email
            role: User role
            jwt_claims: JWT claims dictionary
            **overrides: Additional user attributes

        Returns:
            AuthenticatedUser instance
        """
        if jwt_claims is None:
            jwt_claims = {
                "sub": "user123",
                "email": email,
                "iss": "https://test.cloudflareaccess.com",
                "aud": "https://test-app.com",
                "exp": 1234567890,
                "iat": 1234567890,
                "nbf": 1234567890,
            }

        user_data = {
            "email": email,
            "role": role,
            "jwt_claims": jwt_claims,
        }

        user_data.update(overrides)

        return AuthenticatedUser(**user_data)

    @staticmethod
    def create_admin_user(**overrides: Any) -> AuthenticatedUser:
        """Create an admin user.

        Args:
            **overrides: User attributes to override

        Returns:
            AuthenticatedUser with admin role
        """
        defaults = {
            "email": "admin@example.com",
            "role": UserRole.ADMIN,
        }
        defaults.update(overrides)
        return AuthenticatedUserFactory.create_user(**defaults)

    @staticmethod
    def create_regular_user(**overrides: Any) -> AuthenticatedUser:
        """Create a regular user.

        Args:
            **overrides: User attributes to override

        Returns:
            AuthenticatedUser with user role
        """
        defaults = {
            "role": UserRole.USER,
        }
        defaults.update(overrides)
        return AuthenticatedUserFactory.create_user(**defaults)


# Isolation helpers
class IsolationHelpers:
    """Utilities for ensuring proper test isolation in auth tests."""

    @staticmethod
    def reset_module_state():
        """Reset any module-level state that might leak between tests."""
        # Clear any cached authentication data
        # This can be extended as needed for specific modules
        pass

    @staticmethod
    def create_isolated_validator_set() -> Dict[str, JWTValidator]:
        """Create a set of isolated validators for comprehensive testing.

        Returns:
            Dictionary of validator instances with different configurations
        """
        return {
            "default": JWTValidatorFactory.create_validator(),
            "no_audience": JWTValidatorFactory.create_validator(audience=None),
            "no_issuer": JWTValidatorFactory.create_validator(issuer=None),
            "custom_algorithm": JWTValidatorFactory.create_validator(algorithm="HS256"),
            "failing_jwks": JWTValidatorFactory.create_validator(
                jwks_client=JWTValidatorFactory.create_mock_jwks_client(
                    side_effects={"get_key_by_kid": Exception("JWKS failure")}
                )
            ),
        }
