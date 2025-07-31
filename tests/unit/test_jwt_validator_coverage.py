"""Tests specifically for jwt_validator module coverage.

This test file ensures that jwt_validator.py gets proper coverage measurement.
"""

from unittest.mock import Mock

import pytest

from src.auth.jwks_client import JWKSClient
from src.auth.jwt_validator import JWTValidator
from src.auth.models import UserRole


class TestJWTValidatorCoverage:
    """Test JWTValidator for coverage completion."""

    @pytest.mark.unit
    @pytest.mark.stress
    def test_jwt_validator_initialization(self):
        """Test JWTValidator initialization."""
        mock_jwks_client = Mock(spec=JWKSClient)

        validator = JWTValidator(
            jwks_client=mock_jwks_client,
            audience="test-audience",
            issuer="test-issuer",
            algorithm="RS256",
        )

        assert validator.jwks_client == mock_jwks_client
        assert validator.audience == "test-audience"
        assert validator.issuer == "test-issuer"
        assert validator.algorithm == "RS256"

    @pytest.mark.unit
    @pytest.mark.stress
    def test_jwt_validator_defaults(self):
        """Test JWTValidator with default values."""
        mock_jwks_client = Mock(spec=JWKSClient)

        validator = JWTValidator(jwks_client=mock_jwks_client)

        assert validator.jwks_client == mock_jwks_client
        assert validator.audience is None
        assert validator.issuer is None
        assert validator.algorithm == "RS256"

    @pytest.mark.unit
    @pytest.mark.stress
    def test_is_email_allowed_exact_match(self):
        """Test _is_email_allowed with exact email match."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        email_whitelist = ["user@example.com", "admin@test.com"]

        assert validator._is_email_allowed("user@example.com", email_whitelist) is True
        assert validator._is_email_allowed("USER@EXAMPLE.COM", email_whitelist) is True  # Case insensitive
        assert validator._is_email_allowed("other@example.com", email_whitelist) is False

    @pytest.mark.unit
    @pytest.mark.stress
    def test_is_email_allowed_domain_match(self):
        """Test _is_email_allowed with domain matching."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        email_whitelist = ["@example.com", "@test.org"]

        assert validator._is_email_allowed("user@example.com", email_whitelist) is True
        assert validator._is_email_allowed("admin@test.org", email_whitelist) is True
        assert validator._is_email_allowed("user@other.com", email_whitelist) is False

    @pytest.mark.unit
    @pytest.mark.stress
    def test_is_email_allowed_mixed(self):
        """Test _is_email_allowed with mixed exact and domain entries."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        email_whitelist = ["specific@exact.com", "@domain.com"]

        assert validator._is_email_allowed("specific@exact.com", email_whitelist) is True
        assert validator._is_email_allowed("anyone@domain.com", email_whitelist) is True
        assert validator._is_email_allowed("other@exact.com", email_whitelist) is False

    @pytest.mark.unit
    @pytest.mark.stress
    def test_determine_user_role_admin_email(self):
        """Test _determine_user_role with admin in email."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        payload = {"email": "admin@example.com"}

        role = validator._determine_user_role("admin@example.com", payload)
        assert role == UserRole.ADMIN

        role = validator._determine_user_role("owner@example.com", payload)
        assert role == UserRole.ADMIN

    @pytest.mark.unit
    @pytest.mark.stress
    def test_determine_user_role_admin_groups(self):
        """Test _determine_user_role with admin in groups."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        payload = {"groups": ["users", "admin-group"]}

        role = validator._determine_user_role("user@example.com", payload)
        assert role == UserRole.ADMIN

    @pytest.mark.unit
    @pytest.mark.stress
    def test_determine_user_role_default_user(self):
        """Test _determine_user_role default to USER role."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        payload = {"groups": ["users", "viewers"]}

        role = validator._determine_user_role("user@example.com", payload)
        assert role == UserRole.USER

    @pytest.mark.unit
    @pytest.mark.stress
    def test_determine_user_role_no_groups(self):
        """Test _determine_user_role with no groups in payload."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        payload = {}

        role = validator._determine_user_role("user@example.com", payload)
        assert role == UserRole.USER

    @pytest.mark.unit
    @pytest.mark.stress
    def test_determine_user_role_invalid_groups(self):
        """Test _determine_user_role with invalid groups format."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        payload = {"groups": "not-a-list"}

        role = validator._determine_user_role("user@example.com", payload)
        assert role == UserRole.USER

    @pytest.mark.unit
    @pytest.mark.stress
    def test_validate_token_format_valid(self):
        """Test validate_token_format with valid token format."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        # Valid JWT format (3 parts separated by dots) - Synthetic test token for format validation
        # This is a test-only JWT with fake/test data - NOT a real secret
        valid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0ZXN0IjoidGVzdCIsImV4cCI6OTk5OTk5OTk5OX0.test_signature_not_real"  # noqa: S105

        assert validator.validate_token_format(valid_token) is True

    @pytest.mark.unit
    @pytest.mark.stress
    def test_validate_token_format_invalid_parts(self):
        """Test validate_token_format with invalid number of parts."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        # Invalid - only 2 parts
        invalid_token = "header.payload"  # noqa: S105

        assert validator.validate_token_format(invalid_token) is False

    @pytest.mark.unit
    @pytest.mark.stress
    def test_validate_token_format_invalid_base64(self):
        """Test validate_token_format with invalid base64 encoding."""
        mock_jwks_client = Mock(spec=JWKSClient)
        validator = JWTValidator(jwks_client=mock_jwks_client)

        # Invalid - malformed base64
        invalid_token = "invalid.invalid.invalid"  # noqa: S105

        assert validator.validate_token_format(invalid_token) is False
