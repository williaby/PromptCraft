"""Test authentication constants."""

from src.auth.constants import (
    ADMIN_ROLE_PREFIXES,
    API_STATUS_NO_CHANGE,
    API_STATUS_SUCCESS,
    AUTH_EVENT_GENERAL,
    AUTH_EVENT_JWT,
    AUTH_EVENT_SERVICE_TOKEN,
    ERROR_CODE_TOKEN_EXPIRED,
    ERROR_CODE_TOKEN_INACTIVE,
    ERROR_CODE_TOKEN_NOT_FOUND,
    ERROR_CODE_VALIDATION_EXCEPTION,
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_LOGGED,
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_OPERATIONAL,
    JWT_CLAIM_EMAIL,
    JWT_CLAIM_EXP,
    JWT_CLAIM_GROUPS,
    JWT_CLAIM_IAT,
    JWT_CLAIM_SUB,
    PERMISSION_ADMIN,
    PERMISSION_CREATE,
    PERMISSION_DELETE,
    PERMISSION_NAME_ACCESS,
    PERMISSION_NAME_EMAIL_AUTHORIZATION,
    PERMISSION_READ,
    PERMISSION_UPDATE,
    PERMISSION_WRITE,
    RATE_LIMIT_KEY_EMAIL,
    RATE_LIMIT_KEY_IP,
    RATE_LIMIT_KEY_USER,
    ROLE_ADMIN,
    ROLE_USER,
    SERVICE_TOKEN_PREFIX,
    USER_TYPE_JWT,
    USER_TYPE_JWT_USER,
    USER_TYPE_SERVICE_TOKEN,
    VALIDATION_FIELD_IS_VALID,
)


class TestAuthConstants:
    """Test authentication constants values and types."""

    def test_role_constants(self):
        """Test user role constants."""
        assert ROLE_ADMIN == "admin"
        assert ROLE_USER == "user"
        assert isinstance(ROLE_ADMIN, str)
        assert isinstance(ROLE_USER, str)

    def test_admin_role_prefixes(self):
        """Test admin role prefixes list."""
        expected_prefixes = ["admin", "administrator", "root", "superuser", "owner"]
        assert expected_prefixes == ADMIN_ROLE_PREFIXES
        assert isinstance(ADMIN_ROLE_PREFIXES, list)
        assert all(isinstance(prefix, str) for prefix in ADMIN_ROLE_PREFIXES)

    def test_permission_constants(self):
        """Test permission constants."""
        assert PERMISSION_ADMIN == "admin"
        assert PERMISSION_READ == "read"
        assert PERMISSION_WRITE == "write"
        assert PERMISSION_DELETE == "delete"
        assert PERMISSION_CREATE == "create"
        assert PERMISSION_UPDATE == "update"

        # Test permission name constants
        assert PERMISSION_NAME_EMAIL_AUTHORIZATION == "email_authorization"
        assert PERMISSION_NAME_ACCESS == "access"

    def test_rate_limit_constants(self):
        """Test rate limiting key constants."""
        assert RATE_LIMIT_KEY_IP == "ip"
        assert RATE_LIMIT_KEY_EMAIL == "email"
        assert RATE_LIMIT_KEY_USER == "user"

    def test_service_token_prefix(self):
        """Test service token prefix."""
        assert SERVICE_TOKEN_PREFIX == "sk_"  # noqa: S105  # Test constant
        assert isinstance(SERVICE_TOKEN_PREFIX, str)

    def test_auth_event_types(self):
        """Test authentication event type constants."""
        assert AUTH_EVENT_JWT == "jwt_auth"
        assert AUTH_EVENT_SERVICE_TOKEN == "service_token_auth"  # noqa: S105  # Test constant
        assert AUTH_EVENT_GENERAL == "auth"

    def test_jwt_claim_names(self):
        """Test JWT claim name constants."""
        assert JWT_CLAIM_EMAIL == "email"
        assert JWT_CLAIM_SUB == "sub"
        assert JWT_CLAIM_GROUPS == "groups"
        assert JWT_CLAIM_EXP == "exp"
        assert JWT_CLAIM_IAT == "iat"

    def test_error_codes(self):
        """Test error code constants."""
        assert ERROR_CODE_TOKEN_NOT_FOUND == "token_not_found"  # noqa: S105  # Test constant
        assert ERROR_CODE_TOKEN_INACTIVE == "token_inactive"  # noqa: S105  # Test constant
        assert ERROR_CODE_TOKEN_EXPIRED == "token_expired"  # noqa: S105  # Test constant
        assert ERROR_CODE_VALIDATION_EXCEPTION == "validation_exception"

    def test_user_types(self):
        """Test user type constants."""
        assert USER_TYPE_SERVICE_TOKEN == "service_token"  # noqa: S105  # Test constant
        assert USER_TYPE_JWT == "jwt"
        assert USER_TYPE_JWT_USER == "jwt_user"

    def test_api_response_statuses(self):
        """Test API response status constants."""
        assert API_STATUS_SUCCESS == "success"
        assert API_STATUS_NO_CHANGE == "no_change"

    def test_health_statuses(self):
        """Test system health status constants."""
        assert HEALTH_STATUS_HEALTHY == "healthy"
        assert HEALTH_STATUS_DEGRADED == "degraded"
        assert HEALTH_STATUS_OPERATIONAL == "operational"

    def test_event_log_statuses(self):
        """Test event/log status constants."""
        assert EVENT_STATUS_LOGGED == "logged"
        assert EVENT_STATUS_COMPLETED == "emergency_revocation_completed"

    def test_validation_response_fields(self):
        """Test validation response field constants."""
        assert VALIDATION_FIELD_IS_VALID == "is_valid"

    def test_constants_are_final(self):
        """Test that constants maintain their immutable nature."""
        # These should not raise errors when accessed
        assert len(ADMIN_ROLE_PREFIXES) == 5
        assert SERVICE_TOKEN_PREFIX.startswith("sk")
        assert JWT_CLAIM_EMAIL in ["email"]

        # Test string constants are non-empty
        string_constants = [
            ROLE_ADMIN,
            ROLE_USER,
            PERMISSION_ADMIN,
            PERMISSION_READ,
            SERVICE_TOKEN_PREFIX,
            AUTH_EVENT_JWT,
            JWT_CLAIM_EMAIL,
            ERROR_CODE_TOKEN_NOT_FOUND,
            USER_TYPE_SERVICE_TOKEN,
            API_STATUS_SUCCESS,
            HEALTH_STATUS_HEALTHY,
            EVENT_STATUS_LOGGED,
            VALIDATION_FIELD_IS_VALID,
        ]

        for constant in string_constants:
            assert constant
            assert isinstance(constant, str)
            assert len(constant.strip()) > 0

    def test_admin_prefix_detection_pattern(self):
        """Test that admin prefix constants can detect admin emails."""
        admin_emails = [
            "admin@example.com",
            "administrator@company.com",
            "root@system.com",
            "superuser@org.com",
            "owner@business.com",
        ]

        non_admin_emails = ["user@example.com", "john.doe@company.com", "support@helpdesk.com"]

        def is_admin_email(email: str) -> bool:
            """Helper function to test admin detection pattern."""
            username = email.split("@")[0].lower()
            return any(username.startswith(prefix) for prefix in ADMIN_ROLE_PREFIXES)

        for email in admin_emails:
            assert is_admin_email(email), f"Should detect {email} as admin"

        for email in non_admin_emails:
            assert not is_admin_email(email), f"Should not detect {email} as admin"

    def test_service_token_prefix_detection(self):
        """Test that service token prefix can identify service tokens."""
        valid_service_tokens = ["sk_123456789", "sk_abcdef123", "sk_test_token"]

        invalid_tokens = [
            "pk_123456789",  # Different prefix
            "123456789",  # No prefix
            "token_sk_123",  # Prefix in wrong position
            "",  # Empty string
        ]

        for token in valid_service_tokens:
            assert token.startswith(
                SERVICE_TOKEN_PREFIX,
            ), f"Token {token} should be identified as service token"

        for token in invalid_tokens:
            assert not token.startswith(
                SERVICE_TOKEN_PREFIX,
            ), f"Token {token} should not be identified as service token"

    def test_jwt_claims_can_be_used_as_dict_keys(self):
        """Test that JWT claim constants work as dictionary keys."""
        jwt_payload = {
            JWT_CLAIM_EMAIL: "user@example.com",
            JWT_CLAIM_SUB: "123456",
            JWT_CLAIM_GROUPS: ["users", "admins"],
            JWT_CLAIM_EXP: 1234567890,
            JWT_CLAIM_IAT: 1234567800,
        }

        assert jwt_payload[JWT_CLAIM_EMAIL] == "user@example.com"
        assert jwt_payload[JWT_CLAIM_SUB] == "123456"
        assert jwt_payload[JWT_CLAIM_GROUPS] == ["users", "admins"]
        assert jwt_payload[JWT_CLAIM_EXP] == 1234567890
        assert jwt_payload[JWT_CLAIM_IAT] == 1234567800

    def test_error_codes_for_exception_handling(self):
        """Test that error code constants can be used in exception handling."""
        error_mapping = {
            ERROR_CODE_TOKEN_NOT_FOUND: "Token was not found in the system",
            ERROR_CODE_TOKEN_INACTIVE: "Token is inactive and cannot be used",
            ERROR_CODE_TOKEN_EXPIRED: "Token has expired and must be refreshed",
            ERROR_CODE_VALIDATION_EXCEPTION: "Validation failed for the request",
        }

        # Test that all error codes have meaningful messages
        for error_code in error_mapping:
            assert len(error_mapping[error_code]) > 10, f"Error code {error_code} should have meaningful message"
            assert isinstance(error_code, str), f"Error code {error_code} should be string"
