"""Comprehensive tests for src/auth/__init__.py."""

from unittest.mock import Mock

from src.auth import (
    AuthenticatedUser,
    AuthenticationError,
    AuthenticationMiddleware,
    AuthExceptionHandler,
    JWKSError,
    JWTValidationError,
    SecurityEvent,
    SecurityEventCreate,
    SecurityEventResponse,
    SecurityEventSeverity,
    SecurityEventType,
    ServiceTokenManager,
    ServiceTokenUser,
    UserRole,
    get_current_user,
    require_authentication,
    require_role,
    setup_authentication,
)


class TestServiceTokenUser:
    """Test ServiceTokenUser class."""

    def test_init_with_all_params(self):
        """Test ServiceTokenUser initialization with all parameters."""
        metadata = {"permissions": ["read", "write"], "scopes": ["admin"]}
        user = ServiceTokenUser(token_id="token123", token_name="Test Token", metadata=metadata, usage_count=5)

        assert user.token_id == "token123"
        assert user.token_name == "Test Token"
        assert user.metadata == metadata
        assert user.usage_count == 5

    def test_init_with_minimal_params(self):
        """Test ServiceTokenUser initialization with minimal parameters."""
        user = ServiceTokenUser(token_id="token456", token_name="Simple Token", metadata=None)

        assert user.token_id == "token456"
        assert user.token_name == "Simple Token"
        assert user.metadata == {}
        assert user.usage_count == 0

    def test_init_with_empty_metadata(self):
        """Test ServiceTokenUser initialization with empty metadata."""
        user = ServiceTokenUser(token_id="token789", token_name="Empty Token", metadata={})

        assert user.token_id == "token789"
        assert user.token_name == "Empty Token"
        assert user.metadata == {}

    def test_has_permission_true(self):
        """Test has_permission returns True when permission exists."""
        metadata = {"permissions": ["read", "write", "delete"]}
        user = ServiceTokenUser("token1", "Test", metadata)

        assert user.has_permission("read") is True
        assert user.has_permission("write") is True
        assert user.has_permission("delete") is True

    def test_has_permission_false(self):
        """Test has_permission returns False when permission doesn't exist."""
        metadata = {"permissions": ["read", "write"]}
        user = ServiceTokenUser("token1", "Test", metadata)

        assert user.has_permission("delete") is False
        assert user.has_permission("admin") is False

    def test_has_permission_no_permissions_key(self):
        """Test has_permission when permissions key doesn't exist."""
        metadata = {"scopes": ["admin"]}
        user = ServiceTokenUser("token1", "Test", metadata)

        assert user.has_permission("read") is False
        assert user.has_permission("admin") is False

    def test_has_permission_empty_metadata(self):
        """Test has_permission with empty metadata."""
        user = ServiceTokenUser("token1", "Test", {})

        assert user.has_permission("read") is False

    def test_has_permission_none_metadata(self):
        """Test has_permission with None metadata."""
        user = ServiceTokenUser("token1", "Test", None)

        assert user.has_permission("read") is False

    def test_permissions_property_with_permissions(self):
        """Test permissions property when permissions exist."""
        metadata = {"permissions": ["read", "write", "admin"]}
        user = ServiceTokenUser("token1", "Test", metadata)

        permissions = user.permissions
        assert isinstance(permissions, list)
        assert permissions == ["read", "write", "admin"]

    def test_permissions_property_no_permissions_key(self):
        """Test permissions property when permissions key doesn't exist."""
        metadata = {"scopes": ["admin"]}
        user = ServiceTokenUser("token1", "Test", metadata)

        permissions = user.permissions
        assert isinstance(permissions, list)
        assert permissions == []

    def test_permissions_property_empty_metadata(self):
        """Test permissions property with empty metadata."""
        user = ServiceTokenUser("token1", "Test", {})

        permissions = user.permissions
        assert isinstance(permissions, list)
        assert permissions == []

    def test_permissions_property_non_list_permissions(self):
        """Test permissions property when permissions is not a list."""
        metadata = {"permissions": "invalid_format"}
        user = ServiceTokenUser("token1", "Test", metadata)

        permissions = user.permissions
        assert isinstance(permissions, list)
        assert permissions == []

    def test_permissions_property_none_permissions(self):
        """Test permissions property when permissions is None."""
        metadata = {"permissions": None}
        user = ServiceTokenUser("token1", "Test", metadata)

        permissions = user.permissions
        assert isinstance(permissions, list)
        assert permissions == []


class TestCompatibilityFunctions:
    """Test compatibility wrapper functions."""

    def test_require_authentication_with_user(self):
        """Test require_authentication with user in request."""
        mock_request = Mock()
        mock_user = {"email": "test@example.com", "role": "admin"}
        mock_request.user = mock_user

        result = require_authentication(mock_request)

        assert result == mock_user

    def test_require_authentication_without_user(self):
        """Test require_authentication without user in request."""
        mock_request = Mock()
        # Remove user attribute
        delattr(mock_request, "user") if hasattr(mock_request, "user") else None

        result = require_authentication(mock_request)

        assert result is None

    def test_require_authentication_no_request(self):
        """Test require_authentication with None request."""
        result = require_authentication(None)

        assert result is None

    def test_require_role_with_matching_role(self):
        """Test require_role with matching user role."""
        mock_request = Mock()
        mock_user = Mock()
        mock_user.role = "admin"
        mock_request.user = mock_user

        result = require_role(mock_request, "admin")

        assert result == mock_user

    def test_require_role_with_non_matching_role(self):
        """Test require_role with non-matching user role."""
        mock_request = Mock()
        mock_user = Mock()
        mock_user.role = "user"
        mock_request.user = mock_user

        result = require_role(mock_request, "admin")

        assert result is None

    def test_require_role_no_user(self):
        """Test require_role when no user is present."""
        mock_request = Mock()
        delattr(mock_request, "user") if hasattr(mock_request, "user") else None

        result = require_role(mock_request, "admin")

        assert result is None

    def test_require_role_user_without_role_attribute(self):
        """Test require_role with user that has no role attribute."""
        mock_request = Mock()
        mock_user = Mock()
        # Remove role attribute
        delattr(mock_user, "role") if hasattr(mock_user, "role") else None
        mock_request.user = mock_user

        result = require_role(mock_request, "admin")

        assert result is None

    def test_require_role_with_string_conversion(self):
        """Test require_role with role that needs string conversion."""
        mock_request = Mock()
        mock_user = Mock()
        mock_user.role = 123  # Non-string role
        mock_request.user = mock_user

        result = require_role(mock_request, "123")

        assert result == mock_user

    def test_get_current_user_delegates_to_require_authentication(self):
        """Test get_current_user delegates to require_authentication."""
        mock_request = Mock()
        mock_user = {"email": "test@example.com"}
        mock_request.user = mock_user

        result = get_current_user(mock_request)

        assert result == mock_user

    def test_get_current_user_no_user(self):
        """Test get_current_user when no user is present."""
        mock_request = Mock()
        delattr(mock_request, "user") if hasattr(mock_request, "user") else None

        result = get_current_user(mock_request)

        assert result is None

    def test_setup_authentication(self):
        """Test setup_authentication function (no-op)."""
        mock_app = Mock()

        # Should not raise any exceptions
        setup_authentication(mock_app)

        # Function is a no-op compatibility wrapper
        assert True


class TestAuthenticationMiddleware:
    """Test AuthenticationMiddleware compatibility class."""

    def test_middleware_instantiation(self):
        """Test AuthenticationMiddleware can be instantiated."""
        middleware = AuthenticationMiddleware()

        assert isinstance(middleware, AuthenticationMiddleware)


class TestModuleImports:
    """Test module imports and exports."""

    def test_all_exports_exist(self):
        """Test all items in __all__ can be imported."""
        from src.auth import (
            AuthenticationMiddleware,
            ServiceTokenUser,
            get_current_user,
            require_authentication,
            require_role,
            setup_authentication,
        )

        # Verify all imports are successful
        assert AuthExceptionHandler is not None
        assert AuthenticatedUser is not None
        assert AuthenticationError is not None
        assert AuthenticationMiddleware is not None
        assert JWKSError is not None
        assert JWTValidationError is not None
        assert SecurityEvent is not None
        assert SecurityEventCreate is not None
        assert SecurityEventResponse is not None
        assert SecurityEventSeverity is not None
        assert SecurityEventType is not None
        assert ServiceTokenManager is not None
        assert ServiceTokenUser is not None
        assert UserRole is not None
        assert get_current_user is not None
        assert require_authentication is not None
        assert require_role is not None
        assert setup_authentication is not None

    def test_service_token_user_in_all(self):
        """Test ServiceTokenUser is properly exported."""
        import src.auth

        assert "ServiceTokenUser" in src.auth.__all__
        assert hasattr(src.auth, "ServiceTokenUser")

    def test_compatibility_functions_in_all(self):
        """Test compatibility functions are properly exported."""
        import src.auth

        compatibility_functions = ["get_current_user", "require_authentication", "require_role", "setup_authentication"]

        for func_name in compatibility_functions:
            assert func_name in src.auth.__all__
            assert hasattr(src.auth, func_name)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_service_token_user_with_complex_metadata(self):
        """Test ServiceTokenUser with complex nested metadata."""
        metadata = {
            "permissions": ["read", "write"],
            "scopes": ["admin", "user"],
            "nested": {"level1": {"level2": "value"}},
            "empty_list": [],
            "null_value": None,
        }

        user = ServiceTokenUser("complex_token", "Complex Token", metadata)

        assert user.metadata == metadata
        assert user.has_permission("read") is True
        assert user.permissions == ["read", "write"]

    def test_require_authentication_edge_cases(self):
        """Test require_authentication with various edge cases."""
        # Request with user attribute set to None
        mock_request_none_user = Mock()
        mock_request_none_user.user = None

        result = require_authentication(mock_request_none_user)
        assert result is None

        # Request with user attribute set to empty dict
        mock_request_empty_user = Mock()
        mock_request_empty_user.user = {}

        result = require_authentication(mock_request_empty_user)
        assert result == {}

    def test_require_role_edge_cases(self):
        """Test require_role with various edge cases."""
        # User with None role
        mock_request = Mock()
        mock_user = Mock()
        mock_user.role = None
        mock_request.user = mock_user

        result = require_role(mock_request, "admin")
        assert result is None

        # Role comparison with empty string
        mock_user.role = ""
        result = require_role(mock_request, "")
        assert result == mock_user

    def test_service_token_user_usage_count_edge_cases(self):
        """Test ServiceTokenUser with various usage count values."""
        # Negative usage count
        user1 = ServiceTokenUser("token1", "Test", {}, usage_count=-1)
        assert user1.usage_count == -1

        # Very large usage count
        user2 = ServiceTokenUser("token2", "Test", {}, usage_count=999999)
        assert user2.usage_count == 999999

        # Zero usage count (default)
        user3 = ServiceTokenUser("token3", "Test", {})
        assert user3.usage_count == 0
