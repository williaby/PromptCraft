"""Comprehensive test suite for AUTH-2 authentication API endpoints.

This module tests all authentication endpoints including:
- Token creation and management (admin-only)
- Current user/service token information
- Authentication status and health checks
- Usage analytics and audit logging
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

# Import the module for coverage
from src.api.auth_endpoints import (
    AuthHealthResponse,
    CurrentUserResponse,
    TokenCreationRequest,
    TokenCreationResponse,
    TokenInfo,
    auth_health_check,
    create_service_token,
    emergency_revoke_all_tokens,
    get_current_user_info,
    get_token_analytics,
    list_service_tokens,
    log_cicd_event,
    revoke_service_token,
    rotate_service_token,
    system_health,
    system_status,
)
from src.auth.constants import (
    API_STATUS_SUCCESS,
    EVENT_STATUS_COMPLETED,
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_OPERATIONAL,
    USER_TYPE_JWT_USER,
    USER_TYPE_SERVICE_TOKEN,
)
from src.auth.middleware import ServiceTokenUser


def create_mock_request() -> Request:
    """Create a mock Starlette Request object."""
    mock_request = Mock(spec=Request)
    mock_request.url = Mock()
    mock_request.url.path = "/test"
    mock_request.method = "GET"
    mock_request.headers = {}
    mock_request.client = Mock()
    mock_request.client.host = "127.0.0.1"
    return mock_request


def create_mock_jwt_user(email: str = "test@example.com", role: str = "admin") -> Mock:
    """Create a mock JWT user."""
    mock_user = Mock()
    mock_user.email = email
    mock_user.role = Mock()
    mock_user.role.value = role
    return mock_user


def create_mock_service_token_user(
    token_name: str = "test_token",  # noqa: S107  # Test fixture with mock token name
    token_id: str = "token_123",  # noqa: S107  # Test fixture with mock token ID
    permissions: list | None = None,
    usage_count: int = 5,
) -> ServiceTokenUser:
    """Create a mock ServiceTokenUser."""
    if permissions is None:
        permissions = ["tokens:create", "tokens:read"]

    # Create the ServiceTokenUser with all required attributes
    mock_user = Mock(spec=ServiceTokenUser)
    mock_user.token_name = token_name
    mock_user.token_id = token_id
    mock_user.usage_count = usage_count
    mock_user.metadata = {"permissions": permissions}
    return mock_user


class TestCurrentUserEndpoint:
    """Test suite for /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_info_service_token(self):
        """Test getting current user info for service token authentication."""
        # Arrange
        mock_request = create_mock_request()
        service_token_user = create_mock_service_token_user(
            token_name="api_service",  # noqa: S106  # Test token name
            token_id="st_123456",  # noqa: S106  # Test token ID
            permissions=["tokens:create", "tokens:read"],
            usage_count=42,
        )

        # Act
        result = await get_current_user_info(mock_request, service_token_user)

        # Assert
        assert isinstance(result, CurrentUserResponse)
        assert result.user_type == USER_TYPE_SERVICE_TOKEN
        assert result.token_name == "api_service"  # noqa: S105  # Test constant
        assert result.token_id == "st_123456"  # noqa: S105  # Test token value
        assert result.permissions == ["tokens:create", "tokens:read"]
        assert result.usage_count == 42
        assert result.email is None
        assert result.role is None

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.RoleManager")
    async def test_get_current_user_info_jwt_user(self, mock_role_manager_class):
        """Test getting current user info for JWT authentication."""
        # Arrange
        mock_request = create_mock_request()
        jwt_user = create_mock_jwt_user("admin@company.com", "admin")

        mock_role_manager = Mock()
        mock_role_manager.get_user_permissions = AsyncMock(return_value={"system:admin", "tokens:create"})
        mock_role_manager_class.return_value = mock_role_manager

        # Act
        result = await get_current_user_info(mock_request, jwt_user)

        # Assert
        assert isinstance(result, CurrentUserResponse)
        assert result.user_type == USER_TYPE_JWT_USER
        assert result.email == "admin@company.com"
        assert result.role == "admin"
        assert set(result.permissions) == {"system:admin", "tokens:create"}
        assert result.usage_count is None
        assert result.token_name is None
        assert result.token_id is None

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.RoleManager")
    async def test_get_current_user_info_jwt_user_role_system_unavailable(self, mock_role_manager_class):
        """Test JWT user info when role system is unavailable."""
        # Arrange
        mock_request = create_mock_request()
        jwt_user = create_mock_jwt_user("user@company.com", "user")

        mock_role_manager = Mock()
        mock_role_manager.get_user_permissions = AsyncMock(side_effect=Exception("Role system unavailable"))
        mock_role_manager_class.return_value = mock_role_manager

        # Act
        result = await get_current_user_info(mock_request, jwt_user)

        # Assert
        assert isinstance(result, CurrentUserResponse)
        assert result.user_type == USER_TYPE_JWT_USER
        assert result.email == "user@company.com"
        assert result.role == "user"
        assert result.permissions == []  # Fallback to empty permissions

    @pytest.mark.asyncio
    async def test_get_current_user_info_jwt_user_role_without_value_attribute(self):
        """Test JWT user info when role doesn't have value attribute."""
        # Arrange
        mock_request = create_mock_request()
        jwt_user = Mock()
        jwt_user.email = "test@example.com"
        jwt_user.role = "string_role"  # No .value attribute

        with patch("src.api.auth_endpoints.RoleManager") as mock_role_manager_class:
            mock_role_manager = Mock()
            mock_role_manager.get_user_permissions = AsyncMock(return_value=set())
            mock_role_manager_class.return_value = mock_role_manager

            # Act
            result = await get_current_user_info(mock_request, jwt_user)

            # Assert
            assert result.role == "string_role"


class TestAuthHealthEndpoint:
    """Test suite for /auth/health endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_auth_health_check_success(self, mock_service_token_manager_class):
        """Test successful auth health check."""
        # Arrange
        mock_manager = Mock()
        mock_analytics = {
            "summary": {
                "active_tokens": 5,
                "total_usage": 150,
            },
        }
        mock_manager.get_token_usage_analytics = AsyncMock(return_value=mock_analytics)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await auth_health_check()

        # Assert
        assert isinstance(result, AuthHealthResponse)
        assert result.status == HEALTH_STATUS_HEALTHY
        assert result.database_status == HEALTH_STATUS_HEALTHY
        assert result.active_tokens == 5
        assert result.recent_authentications == 150
        assert isinstance(result.timestamp, datetime)
        mock_manager.get_token_usage_analytics.assert_called_once_with(days=1)

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_auth_health_check_no_analytics(self, mock_service_token_manager_class):
        """Test auth health check with no analytics data."""
        # Arrange
        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(return_value=None)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await auth_health_check()

        # Assert
        assert result.status == HEALTH_STATUS_HEALTHY
        assert result.database_status == HEALTH_STATUS_HEALTHY
        assert result.active_tokens == -1
        assert result.recent_authentications == -1

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_auth_health_check_database_error(self, mock_service_token_manager_class):
        """Test auth health check with database error."""
        # Arrange
        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(side_effect=Exception("Database connection failed"))
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await auth_health_check()

        # Assert
        assert result.status == HEALTH_STATUS_DEGRADED
        assert "error: Database connection failed" in result.database_status
        assert result.active_tokens == -1
        assert result.recent_authentications == -1


class TestTokenCreationEndpoint:
    """Test suite for POST /auth/tokens endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_create_service_token_success(self, mock_service_token_manager_class):
        """Test successful service token creation."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user("admin@company.com", "admin")

        token_request = TokenCreationRequest(
            token_name="ci_cd_token",  # noqa: S106  # Test token name
            permissions=["tokens:create", "system:read"],
            expires_days=90,
            purpose="CI/CD automation",
            environment="production",
        )

        mock_manager = Mock()
        mock_token_value = "st_abcdef123456"  # noqa: S105  # Test token value
        mock_token_id = "token_789"  # noqa: S105  # Test mock value
        mock_manager.create_service_token = AsyncMock(return_value=(mock_token_value, mock_token_id))
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await create_service_token(mock_request, token_request, admin_user)

        # Assert
        assert isinstance(result, TokenCreationResponse)
        assert result.token_id == mock_token_id
        assert result.token_name == "ci_cd_token"  # noqa: S105  # Test constant
        assert result.token_value == mock_token_value
        assert result.expires_at is not None
        assert result.metadata["permissions"] == ["tokens:create", "system:read"]
        assert result.metadata["created_by"] == "admin@company.com"
        assert result.metadata["purpose"] == "CI/CD automation"
        assert result.metadata["environment"] == "production"
        assert result.metadata["created_via"] == "admin_api"

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_create_service_token_no_expiration(self, mock_service_token_manager_class):
        """Test service token creation without expiration."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()

        token_request = TokenCreationRequest(
            token_name="permanent_token",  # noqa: S106  # Test token name
            permissions=["tokens:read"],
        )

        mock_manager = Mock()
        mock_manager.create_service_token = AsyncMock(return_value=("st_token", "token_id"))
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await create_service_token(mock_request, token_request, admin_user)

        # Assert
        assert result.expires_at is None
        mock_manager.create_service_token.assert_called_once()
        call_args = mock_manager.create_service_token.call_args
        assert call_args.kwargs["expires_at"] is None

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_create_service_token_from_service_token_user(self, mock_service_token_manager_class):
        """Test service token creation by another service token."""
        # Arrange
        mock_request = create_mock_request()
        service_token_user = create_mock_service_token_user("admin_token", "st_admin")

        token_request = TokenCreationRequest(token_name="new_token")  # noqa: S106  # Test token name

        mock_manager = Mock()
        mock_manager.create_service_token = AsyncMock(return_value=("st_new", "new_id"))
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await create_service_token(mock_request, token_request, service_token_user)

        # Assert
        assert result.metadata["created_by"] == "admin_token"

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_create_service_token_creation_returns_none(
        self,
        mock_exception_handler,
        mock_service_token_manager_class,
    ):
        """Test service token creation when manager returns None."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_request = TokenCreationRequest(token_name="test_token")  # noqa: S106  # Test token name

        mock_manager = Mock()
        mock_manager.create_service_token = AsyncMock(return_value=None)
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_internal_error.side_effect = HTTPException(
            status_code=500,
            detail="Internal error",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await create_service_token(mock_request, token_request, admin_user)

        # Should be called twice: once for the ValueError and once for the resulting HTTPException
        assert mock_exception_handler.handle_internal_error.call_count == 2

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_create_service_token_name_already_exists(
        self,
        mock_exception_handler,
        mock_service_token_manager_class,
    ):
        """Test service token creation with duplicate name."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_request = TokenCreationRequest(token_name="existing_token")  # noqa: S106  # Test token name

        mock_manager = Mock()
        mock_manager.create_service_token = AsyncMock(side_effect=ValueError("Token name already exists"))
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_validation_error.side_effect = HTTPException(
            status_code=400,
            detail="Validation error",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await create_service_token(mock_request, token_request, admin_user)

        mock_exception_handler.handle_validation_error.assert_called_once_with(
            "Token name already exists",
            "token_name",
        )

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_create_service_token_unexpected_error(
        self,
        mock_exception_handler,
        mock_service_token_manager_class,
    ):
        """Test service token creation with unexpected error."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_request = TokenCreationRequest(token_name="test_token")  # noqa: S106  # Test token name

        mock_manager = Mock()
        mock_manager.create_service_token = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_internal_error.side_effect = HTTPException(
            status_code=500,
            detail="Internal error",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await create_service_token(mock_request, token_request, admin_user)

        mock_exception_handler.handle_internal_error.assert_called_once()


class TestTokenRevocationEndpoint:
    """Test suite for DELETE /auth/tokens/{token_identifier} endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_revoke_service_token_success(self, mock_service_token_manager_class):
        """Test successful service token revocation."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user("admin@company.com")
        token_identifier = "test_token_123"  # noqa: S105  # Test token value
        reason = "Security incident"

        mock_manager = Mock()
        mock_manager.revoke_service_token = AsyncMock(return_value=True)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await revoke_service_token(mock_request, token_identifier, reason, admin_user)

        # Assert
        assert result["status"] == API_STATUS_SUCCESS
        assert result["message"] == "Token 'test_token_123' has been revoked"
        assert result["revoked_by"] == "admin@company.com"
        assert result["reason"] == reason

        mock_manager.revoke_service_token.assert_called_once_with(
            token_identifier=token_identifier,
            revocation_reason=f"{reason} (revoked by admin@company.com via API)",
        )

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_revoke_service_token_not_found(self, mock_exception_handler, mock_service_token_manager_class):
        """Test token revocation when token not found."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_identifier = "nonexistent_token"  # noqa: S105  # Test constant
        reason = "Test"

        mock_manager = Mock()
        mock_manager.revoke_service_token = AsyncMock(return_value=False)
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_not_found_error.side_effect = HTTPException(
            status_code=404,
            detail="Token not found",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await revoke_service_token(mock_request, token_identifier, reason, admin_user)

        mock_exception_handler.handle_not_found_error.assert_called_once_with("token", token_identifier)

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_revoke_service_token_by_service_token(self, mock_service_token_manager_class):
        """Test token revocation by another service token."""
        # Arrange
        mock_request = create_mock_request()
        service_token_user = create_mock_service_token_user("admin_service_token")
        token_identifier = "target_token"  # noqa: S105  # Test constant
        reason = "Automated cleanup"

        mock_manager = Mock()
        mock_manager.revoke_service_token = AsyncMock(return_value=True)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await revoke_service_token(mock_request, token_identifier, reason, service_token_user)

        # Assert
        assert result["revoked_by"] == "admin_service_token"
        expected_reason = f"{reason} (revoked by admin_service_token via API)"
        mock_manager.revoke_service_token.assert_called_once_with(
            token_identifier=token_identifier,
            revocation_reason=expected_reason,
        )


class TestTokenRotationEndpoint:
    """Test suite for POST /auth/tokens/{token_identifier}/rotate endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_rotate_service_token_success(self, mock_service_token_manager_class):
        """Test successful service token rotation."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user("admin@company.com")
        token_identifier = "old_token_123"  # noqa: S105  # Test constant
        reason = "Regular rotation"

        mock_manager = Mock()
        new_token_value = "test_token_new"  # noqa: S105  # Test token value
        new_token_id = "new_token_id_789"  # noqa: S105  # Test constant
        mock_manager.rotate_service_token = AsyncMock(return_value=(new_token_value, new_token_id))

        mock_analytics = {
            "token_name": "rotated_service_token",
            "usage_count": 10,
        }
        mock_manager.get_token_usage_analytics = AsyncMock(return_value=mock_analytics)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await rotate_service_token(mock_request, token_identifier, reason, admin_user)

        # Assert
        assert isinstance(result, TokenCreationResponse)
        assert result.token_id == new_token_id
        assert result.token_name == "rotated_service_token"  # noqa: S105  # Test constant
        assert result.token_value == new_token_value
        assert result.expires_at is None
        assert result.metadata["rotated_by"] == "admin@company.com"
        assert result.metadata["rotation_reason"] == reason

        mock_manager.rotate_service_token.assert_called_once_with(
            token_identifier=token_identifier,
            rotation_reason=f"{reason} (rotated by admin@company.com via API)",
        )

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_rotate_service_token_no_analytics(self, mock_service_token_manager_class):
        """Test token rotation when analytics are unavailable."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_identifier = "old_token"  # noqa: S105  # Test constant

        mock_manager = Mock()
        new_token_value = "st_new"  # noqa: S105  # Test token value
        new_token_id = "new_id"  # noqa: S105  # Test constant
        mock_manager.rotate_service_token = AsyncMock(return_value=(new_token_value, new_token_id))
        mock_manager.get_token_usage_analytics = AsyncMock(return_value={"error": "Token not found"})
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await rotate_service_token(mock_request, token_identifier, "test", admin_user)

        # Assert
        assert result.token_name == "rotated_token"  # Fallback name  # noqa: S105  # Test constant

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_rotate_service_token_not_found(self, mock_exception_handler, mock_service_token_manager_class):
        """Test token rotation when token not found."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_identifier = "nonexistent_token"  # noqa: S105  # Test constant

        mock_manager = Mock()
        mock_manager.rotate_service_token = AsyncMock(return_value=None)
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_not_found_error.side_effect = HTTPException(
            status_code=404,
            detail="Token not found",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await rotate_service_token(mock_request, token_identifier, "test", admin_user)


class TestListTokensEndpoint:
    """Test suite for GET /auth/tokens endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_list_service_tokens_success(self, mock_service_token_manager_class):
        """Test successful token listing."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()

        mock_manager = Mock()

        # Mock analytics for the main call
        main_analytics = {
            "top_tokens": [
                {"token_name": "token1"},
                {"token_name": "token2"},
            ],
        }

        # Mock detailed analytics for each token
        token1_analytics = {
            "token_name": "token1",
            "usage_count": 25,
            "last_used": "2024-01-15T10:30:00",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
        }

        token2_analytics = {
            "token_name": "token2",
            "usage_count": 5,
            "last_used": None,
            "is_active": False,
            "created_at": "2024-01-10T12:00:00",
        }

        mock_manager.get_token_usage_analytics = AsyncMock()
        mock_manager.get_token_usage_analytics.side_effect = [
            main_analytics,  # First call for overall analytics
            token1_analytics,  # Second call for token1 details
            token2_analytics,  # Third call for token2 details
        ]
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await list_service_tokens(mock_request, admin_user)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

        token1_info = result[0]
        assert isinstance(token1_info, TokenInfo)
        assert token1_info.token_name == "token1"  # noqa: S105  # Test constant
        assert token1_info.usage_count == 25
        assert token1_info.is_active is True
        assert token1_info.last_used == datetime.fromisoformat("2024-01-15T10:30:00")

        token2_info = result[1]
        assert token2_info.token_name == "token2"  # noqa: S105  # Test constant
        assert token2_info.usage_count == 5
        assert token2_info.is_active is False
        assert token2_info.last_used is None

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_list_service_tokens_no_tokens(self, mock_service_token_manager_class):
        """Test token listing when no tokens exist."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()

        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(return_value={"top_tokens": []})
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await list_service_tokens(mock_request, admin_user)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_list_service_tokens_error(self, mock_exception_handler, mock_service_token_manager_class):
        """Test token listing with database error."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()

        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(side_effect=Exception("Database error"))
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_internal_error.side_effect = HTTPException(
            status_code=500,
            detail="Internal error",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await list_service_tokens(mock_request, admin_user)


class TestTokenAnalyticsEndpoint:
    """Test suite for GET /auth/tokens/{token_identifier}/analytics endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_get_token_analytics_success(self, mock_service_token_manager_class):
        """Test successful token analytics retrieval."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_identifier = "test_token"  # noqa: S105  # Test token value
        days = 30

        mock_analytics = {
            "token_name": "test_token",
            "usage_count": 100,
            "recent_events": [],
            "usage_by_day": {},
        }

        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(return_value=mock_analytics)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await get_token_analytics(mock_request, token_identifier, days, admin_user)

        # Assert
        assert result == mock_analytics
        mock_manager.get_token_usage_analytics.assert_called_once_with(token_identifier=token_identifier, days=days)

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_get_token_analytics_token_not_found(self, mock_exception_handler, mock_service_token_manager_class):
        """Test token analytics when token not found."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_identifier = "nonexistent_token"  # noqa: S105  # Test constant

        mock_analytics = {"error": "Token not found"}
        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(return_value=mock_analytics)
        mock_service_token_manager_class.return_value = mock_manager

        mock_exception_handler.handle_not_found_error.side_effect = HTTPException(
            status_code=404,
            detail="Token not found",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await get_token_analytics(mock_request, token_identifier, 30, admin_user)

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_get_token_analytics_no_data(self, mock_service_token_manager_class):
        """Test token analytics when no data available."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        token_identifier = "test_token"  # noqa: S105  # Test token value

        mock_manager = Mock()
        mock_manager.get_token_usage_analytics = AsyncMock(return_value=None)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await get_token_analytics(mock_request, token_identifier, 30, admin_user)

        # Assert
        assert result == {}


class TestEmergencyRevocationEndpoint:
    """Test suite for POST /auth/emergency-revoke endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_emergency_revoke_all_tokens_success(self, mock_service_token_manager_class):
        """Test successful emergency revocation of all tokens."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user("admin@company.com")
        reason = "Security breach detected"
        confirm = True

        mock_manager = Mock()
        mock_manager.emergency_revoke_all_tokens = AsyncMock(return_value=15)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await emergency_revoke_all_tokens(mock_request, reason, confirm, admin_user)

        # Assert
        assert result["status"] == EVENT_STATUS_COMPLETED
        assert result["tokens_revoked"] == 15
        assert result["revoked_by"] == "admin@company.com"
        assert result["reason"] == reason
        assert "timestamp" in result

        mock_manager.emergency_revoke_all_tokens.assert_called_once_with(
            emergency_reason=f"{reason} (emergency revoked by admin@company.com via API)",
        )

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.AuthExceptionHandler")
    async def test_emergency_revoke_all_tokens_no_confirmation(self, mock_exception_handler):
        """Test emergency revocation without confirmation."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        reason = "Test"
        confirm = False

        mock_exception_handler.handle_validation_error.side_effect = HTTPException(
            status_code=400,
            detail="Confirmation required",
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await emergency_revoke_all_tokens(mock_request, reason, confirm, admin_user)

        mock_exception_handler.handle_validation_error.assert_called_once_with(
            "Emergency revocation requires explicit confirmation (confirm=true)",
            "confirm",
        )

    @pytest.mark.asyncio
    @patch("src.api.auth_endpoints.ServiceTokenManager")
    async def test_emergency_revoke_all_tokens_no_tokens_revoked(self, mock_service_token_manager_class):
        """Test emergency revocation when no tokens exist."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        reason = "Test"
        confirm = True

        mock_manager = Mock()
        mock_manager.emergency_revoke_all_tokens = AsyncMock(return_value=None)
        mock_service_token_manager_class.return_value = mock_manager

        # Act
        result = await emergency_revoke_all_tokens(mock_request, reason, confirm, admin_user)

        # Assert
        assert result["tokens_revoked"] == 0


class TestSystemStatusEndpoint:
    """Test suite for GET /system/status endpoint."""

    @pytest.mark.asyncio
    async def test_system_status_jwt_user(self):
        """Test system status for JWT user."""
        # Arrange
        mock_request = create_mock_request()
        jwt_user = create_mock_jwt_user("admin@company.com")

        # Act
        result = await system_status(mock_request, jwt_user)

        # Assert
        assert result["status"] == HEALTH_STATUS_OPERATIONAL
        assert result["version"] == "1.0.0"
        assert result["authenticated_as"] == "admin@company.com"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_system_status_service_token(self):
        """Test system status for service token."""
        # Arrange
        mock_request = create_mock_request()
        service_token = create_mock_service_token_user("system_monitor_token")

        # Act
        result = await system_status(mock_request, service_token)

        # Assert
        assert result["authenticated_as"] == "system_monitor_token"


class TestSystemHealthEndpoint:
    """Test suite for GET /system/health endpoint."""

    @pytest.mark.asyncio
    async def test_system_health(self):
        """Test public system health check."""
        # Act
        result = await system_health()

        # Assert
        assert result["status"] == "healthy"
        assert "timestamp" in result


class TestAuditEndpoint:
    """Test suite for POST /audit/cicd-event endpoint."""

    @pytest.mark.asyncio
    async def test_log_cicd_event_jwt_user(self):
        """Test CI/CD event logging for JWT user."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user("ci@company.com")
        event_data = {
            "event_type": "deployment",
            "service": "api-gateway",
            "status": "success",
        }

        # Act
        result = await log_cicd_event(mock_request, event_data, admin_user)

        # Assert
        assert result["status"] == "logged"
        assert result["event_type"] == "deployment"
        assert result["logged_by"] == "ci@company.com"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_log_cicd_event_service_token(self):
        """Test CI/CD event logging for service token."""
        # Arrange
        mock_request = create_mock_request()
        service_token = create_mock_service_token_user("cicd_service_token")
        event_data = {"event_type": "build", "result": "failed"}

        # Act
        result = await log_cicd_event(mock_request, event_data, service_token)

        # Assert
        assert result["logged_by"] == "cicd_service_token"

    @pytest.mark.asyncio
    async def test_log_cicd_event_unknown_event_type(self):
        """Test CI/CD event logging with unknown event type."""
        # Arrange
        mock_request = create_mock_request()
        admin_user = create_mock_jwt_user()
        event_data = {}  # No event_type

        # Act
        result = await log_cicd_event(mock_request, event_data, admin_user)

        # Assert
        assert result["event_type"] == "unknown"


class TestPydanticModels:
    """Test suite for Pydantic model validation."""

    def test_token_creation_request_validation(self):
        """Test TokenCreationRequest validation."""
        # Valid request
        request = TokenCreationRequest(
            token_name="valid_token",  # noqa: S106  # Test token name
            permissions=["tokens:read"],
            expires_days=30,
            purpose="Testing",
            environment="test",
        )
        assert request.token_name == "valid_token"  # noqa: S105  # Test constant
        assert request.permissions == ["tokens:read"]
        assert request.expires_days == 30

    def test_token_creation_request_defaults(self):
        """Test TokenCreationRequest with default values."""
        request = TokenCreationRequest(token_name="test_token")  # noqa: S106  # Test token name
        assert request.permissions == []
        assert request.expires_days is None
        assert request.purpose is None
        assert request.environment is None

    def test_current_user_response_service_token(self):
        """Test CurrentUserResponse for service token."""
        response = CurrentUserResponse(
            user_type=USER_TYPE_SERVICE_TOKEN,
            token_name="test_token",  # noqa: S106  # Test token name
            token_id="token_123",  # noqa: S106  # Test token ID
            permissions=["tokens:read"],
            usage_count=10,
        )
        assert response.user_type == USER_TYPE_SERVICE_TOKEN
        assert response.email is None
        assert response.role is None

    def test_current_user_response_jwt_user(self):
        """Test CurrentUserResponse for JWT user."""
        response = CurrentUserResponse(
            user_type=USER_TYPE_JWT_USER,
            email="user@example.com",
            role="admin",
            permissions=["system:admin"],
        )
        assert response.user_type == USER_TYPE_JWT_USER
        assert response.token_name is None
        assert response.token_id is None
        assert response.usage_count is None

    def test_auth_health_response(self):
        """Test AuthHealthResponse model."""
        now = datetime.now(UTC)
        response = AuthHealthResponse(
            status=HEALTH_STATUS_HEALTHY,
            timestamp=now,
            database_status=HEALTH_STATUS_HEALTHY,
            active_tokens=5,
            recent_authentications=100,
        )
        assert response.status == HEALTH_STATUS_HEALTHY
        assert response.timestamp == now
        assert response.active_tokens == 5

    def test_token_info_model(self):
        """Test TokenInfo model."""
        now = datetime.now(UTC)
        token_info = TokenInfo(
            token_id="token_123",  # noqa: S106  # Test token ID
            token_name="test_token",  # noqa: S106  # Test token name
            usage_count=50,
            last_used=now,
            is_active=True,
            created_at=now,
            permissions=["tokens:read", "tokens:write"],
        )
        assert token_info.token_id == "token_123"  # noqa: S105  # Test constant
        assert token_info.usage_count == 50
        assert token_info.is_active is True
        assert len(token_info.permissions) == 2
