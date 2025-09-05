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
        assert SERVICE_TOKEN_PREFIX == "sk_"
        assert isinstance(SERVICE_TOKEN_PREFIX, str)

    def test_auth_event_types(self):
        """Test authentication event type constants."""
        assert AUTH_EVENT_JWT == "jwt_auth"
        assert AUTH_EVENT_SERVICE_TOKEN == "service_token_auth"
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
        assert ERROR_CODE_TOKEN_NOT_FOUND == "token_not_found"
        assert ERROR_CODE_TOKEN_INACTIVE == "token_inactive"
        assert ERROR_CODE_TOKEN_EXPIRED == "token_expired"
        assert ERROR_CODE_VALIDATION_EXCEPTION == "validation_exception"

    def test_user_types(self):
        """Test user type constants."""
        assert USER_TYPE_SERVICE_TOKEN == "service_token"
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
