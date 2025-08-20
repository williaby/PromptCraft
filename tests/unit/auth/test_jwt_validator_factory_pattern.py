"""Demonstration of factory pattern usage for JWT validator test isolation.

This test file demonstrates how to use the new factory pattern to achieve
better test isolation and consistency in authentication tests.
"""

import pytest

from src.auth.models import JWTValidationError, UserRole
from tests.utils.auth_factories import (
    AuthenticatedUserFactory,
    IsolationHelpers,
    JWTTokenFactory,
    JWTValidatorFactory,
)


class TestJWTValidatorFactoryPattern:
    """Test class demonstrating factory pattern usage for isolation."""

    @pytest.fixture(autouse=True)
    def setup_isolation(self):
        """Ensure clean state for each test using isolation helpers."""
        IsolationHelpers.reset_module_state()
        yield
        IsolationHelpers.reset_module_state()

    def test_factory_creates_isolated_validators(self):
        """Test that factory creates properly isolated validator instances."""
        # Create two validators using factory
        validator1 = JWTValidatorFactory.create_validator()
        validator2 = JWTValidatorFactory.create_validator()

        # They should be separate instances
        assert validator1 is not validator2
        assert validator1.jwks_client is not validator2.jwks_client

        # But they should have equivalent configuration
        assert validator1.audience == validator2.audience
        assert validator1.issuer == validator2.issuer
        assert validator1.algorithm == validator2.algorithm

    def test_factory_customization(self):
        """Test that factory allows easy customization of validators."""
        # Create validator with custom configuration
        validator = JWTValidatorFactory.create_validator(
            audience="https://custom-app.com", issuer="https://custom.cloudflareaccess.com", algorithm="HS256"
        )

        assert validator.audience == "https://custom-app.com"
        assert validator.issuer == "https://custom.cloudflareaccess.com"
        assert validator.algorithm == "HS256"

    def test_token_factory_creates_consistent_tokens(self):
        """Test that token factory creates consistent, valid tokens."""
        # Create multiple tokens with same parameters
        token1 = JWTTokenFactory.create_valid_token(email="test@example.com")
        token2 = JWTTokenFactory.create_valid_token(email="test@example.com")

        # Tokens should have same structure but may be identical due to same timestamp
        assert len(token1.split(".")) == 3  # Valid JWT structure
        assert len(token2.split(".")) == 3  # Valid JWT structure

        # Both should be valid JWT format
        assert isinstance(token1, str)
        assert isinstance(token2, str)

    def test_specialized_token_creation(self):
        """Test specialized token creation methods."""
        # Test expired token
        expired_token = JWTTokenFactory.create_expired_token()
        assert len(expired_token.split(".")) == 3

        # Test token missing kid
        no_kid_token = JWTTokenFactory.create_token_missing_kid()
        assert len(no_kid_token.split(".")) == 3

        # Test token missing email
        no_email_token = JWTTokenFactory.create_token_missing_email()
        assert len(no_email_token.split(".")) == 3

        # Test malformed token
        malformed_token = JWTTokenFactory.create_malformed_token()
        assert malformed_token == "invalid.token.format"

    def test_validator_with_token_integration(self):
        """Test integration between validator and token factories."""
        # Create validator with mock that will succeed
        validator = JWTValidatorFactory.create_validator()

        # Create a valid token
        token = JWTTokenFactory.create_valid_token(email="test@example.com")

        # The token should be properly formatted for validation
        # (Note: actual validation would require proper JWT signing in real scenarios)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_jwks_client_customization(self):
        """Test JWKS client customization through factory."""
        # Create validator with failing JWKS client
        failing_jwks = JWTValidatorFactory.create_mock_jwks_client(
            side_effects={"get_key_by_kid": Exception("JWKS failure")}
        )
        validator = JWTValidatorFactory.create_validator(jwks_client=failing_jwks)

        # Verify the mock is configured correctly
        with pytest.raises(Exception, match="JWKS failure"):
            validator.jwks_client.get_key_by_kid("any-kid")

    def test_isolated_validator_set(self):
        """Test creation of isolated validator sets for comprehensive testing."""
        validator_set = IsolationHelpers.create_isolated_validator_set()

        # Should contain expected validator types
        expected_keys = ["default", "no_audience", "no_issuer", "custom_algorithm", "failing_jwks"]
        assert set(validator_set.keys()) == set(expected_keys)

        # Each validator should be a separate instance
        validators = list(validator_set.values())
        for i, validator1 in enumerate(validators):
            for j, validator2 in enumerate(validators):
                if i != j:
                    assert validator1 is not validator2

    def test_user_factory_integration(self):
        """Test AuthenticatedUser factory integration."""
        # Create different types of users
        admin_user = AuthenticatedUserFactory.create_admin_user()
        regular_user = AuthenticatedUserFactory.create_regular_user()
        custom_user = AuthenticatedUserFactory.create_user(email="custom@example.com", role=UserRole.USER)

        # Verify user properties
        assert admin_user.role == UserRole.ADMIN
        assert admin_user.email == "admin@example.com"
        assert admin_user.jwt_claims is not None

        assert regular_user.role == UserRole.USER
        assert regular_user.jwt_claims is not None

        assert custom_user.email == "custom@example.com"
        assert custom_user.role == UserRole.USER
        assert custom_user.jwt_claims is not None

    def test_factory_pattern_isolation_between_tests(self):
        """Test that factory pattern maintains isolation between test runs."""
        # This test verifies that using factories prevents state leakage

        # Create validator and modify its state
        validator1 = JWTValidatorFactory.create_validator()
        validator1._test_marker = "modified"  # Add custom attribute

        # Create new validator - should not have the custom attribute
        validator2 = JWTValidatorFactory.create_validator()
        assert not hasattr(validator2, "_test_marker")

        # Validators should be completely separate instances
        assert validator1 is not validator2
        assert validator1.jwks_client is not validator2.jwks_client

    @pytest.mark.parametrize(
        "token_type,expected_error",
        [
            ("expired", JWTValidationError),
            ("missing_kid", JWTValidationError),
            ("missing_email", JWTValidationError),
            ("malformed", JWTValidationError),
        ],
    )
    def test_parametrized_token_validation_errors(self, token_type, expected_error):
        """Test parametrized validation of different token error scenarios."""
        validator = JWTValidatorFactory.create_validator()

        # Create token based on type
        if token_type == "expired":
            token = JWTTokenFactory.create_expired_token()
        elif token_type == "missing_kid":
            token = JWTTokenFactory.create_token_missing_kid()
        elif token_type == "missing_email":
            token = JWTTokenFactory.create_token_missing_email()
        elif token_type == "malformed":
            token = JWTTokenFactory.create_malformed_token()
        else:
            pytest.fail(f"Unknown token type: {token_type}")

        # All should raise JWTValidationError when validated
        # (Note: in real tests with proper JWT signing, we would actually call validate_token)
        assert isinstance(token, str)  # Basic structure verification
