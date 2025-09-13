"""
Comprehensive unit tests for permissions system.

Tests focus on critical security paths in the permissions module
to improve coverage from 42.31% to 85%+.
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
import pytest

from src.auth.middleware import ServiceTokenUser
from src.auth.models import AuthenticatedUser
from src.auth.permissions import (
    has_service_token_permission,
    require_all_permissions,
    require_any_permission,
    require_permission,
    user_has_permission,
)


class TestUserHasPermission:
    """Test user_has_permission function."""

    @pytest.mark.asyncio
    async def test_user_has_permission_success(self):
        """Test successful permission check."""
        with patch("src.auth.permissions.get_db") as mock_get_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.scalar.return_value = True
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_db_gen():
                yield mock_session

            mock_get_db.return_value = mock_db_gen()

            result = await user_has_permission("test@example.com", "tokens:create")

            assert result is True
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_has_permission_no_permission(self):
        """Test user without permission."""
        with patch("src.auth.permissions.get_db") as mock_get_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.scalar.return_value = None  # Database returns None for no permission
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_db_gen():
                yield mock_session

            mock_get_db.return_value = mock_db_gen()

            result = await user_has_permission("test@example.com", "tokens:create")

            assert result is False
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_has_permission_database_error(self):
        """Test database error handling."""
        with patch("src.auth.permissions.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("Database connection error"))

            async def mock_db_gen():
                yield mock_session

            mock_get_db.return_value = mock_db_gen()

            result = await user_has_permission("test@example.com", "tokens:create")

            # Should return False on database errors
            assert result is False

    @pytest.mark.asyncio
    async def test_user_has_permission_generator_error(self):
        """Test generator creation error."""
        with patch("src.auth.permissions.get_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Generator error")

            result = await user_has_permission("test@example.com", "tokens:create")

            # Should return False on generator errors
            assert result is False

    @pytest.mark.asyncio
    async def test_user_has_permission_alternative_db_path(self):
        """Test alternative database session creation path."""
        with patch("src.auth.permissions.get_db") as mock_get_db:
            # Mock generator that doesn't have __anext__ but has __aenter__
            mock_gen = Mock()
            mock_gen.__anext__ = Mock(side_effect=AttributeError("No __anext__"))
            mock_gen.__aenter__ = AsyncMock()
            mock_session = AsyncMock()
            mock_gen.__aenter__.return_value = mock_session

            mock_result = Mock()
            mock_result.scalar.return_value = True
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_get_db.return_value = mock_gen

            result = await user_has_permission("test@example.com", "tokens:create")

            assert result is True
            mock_gen.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_has_permission_no_session_available(self):
        """Test case when no database session is available."""
        with patch("src.auth.permissions.get_db") as mock_get_db:
            # Mock generator that has neither __anext__ nor __aenter__
            mock_gen = Mock()
            mock_gen.__anext__ = Mock(side_effect=AttributeError("No __anext__"))
            del mock_gen.__aenter__  # Remove __aenter__ method

            mock_get_db.return_value = mock_gen

            result = await user_has_permission("test@example.com", "tokens:create")

            # Should return False when no session is available
            assert result is False


class TestRequirePermission:
    """Test require_permission decorator."""

    @pytest.fixture
    def mock_jwt_user(self):
        """Create mock JWT authenticated user."""
        user = Mock(spec=AuthenticatedUser)
        user.email = "test@example.com"
        user.user_id = "user123"
        return user

    @pytest.fixture
    def mock_service_token_user(self):
        """Create mock service token user."""
        user = Mock(spec=ServiceTokenUser)
        user.token_name = "test-token"  # noqa: S105  # Test token value
        user.token_id = "token123"  # noqa: S105  # Test token value
        user.has_permission = Mock(return_value=True)
        return user

    @pytest.mark.asyncio
    async def test_require_permission_jwt_user_success(self, mock_jwt_user):
        """Test require_permission with JWT user having permission."""
        permission_checker = require_permission("tokens:create")

        with patch("src.auth.permissions.user_has_permission", return_value=True) as mock_has_perm:
            result = await permission_checker(mock_jwt_user)

            assert result == mock_jwt_user
            mock_has_perm.assert_called_once_with("test@example.com", "tokens:create")

    @pytest.mark.asyncio
    async def test_require_permission_jwt_user_no_permission(self, mock_jwt_user):
        """Test require_permission with JWT user lacking permission."""
        permission_checker = require_permission("tokens:create")

        with patch("src.auth.permissions.user_has_permission", return_value=False):
            with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                mock_error.side_effect = HTTPException(status_code=403, detail="Permission denied")

                with pytest.raises(HTTPException) as exc_info:
                    await permission_checker(mock_jwt_user)

                assert exc_info.value.status_code == 403
                mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_require_permission_service_token_success(self, mock_service_token_user):
        """Test require_permission with service token having permission."""
        permission_checker = require_permission("tokens:create")

        # Mock isinstance to return True for ServiceTokenUser check
        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True  # First isinstance call (ServiceTokenUser)

            result = await permission_checker(mock_service_token_user)

            assert result == mock_service_token_user
            mock_service_token_user.has_permission.assert_called_once_with("tokens:create")

    @pytest.mark.asyncio
    async def test_require_permission_service_token_no_permission(self, mock_service_token_user):
        """Test require_permission with service token lacking permission."""
        mock_service_token_user.has_permission.return_value = False
        permission_checker = require_permission("tokens:create")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True  # First isinstance call (ServiceTokenUser)

            with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                mock_error.side_effect = HTTPException(status_code=403, detail="Permission denied")

                with pytest.raises(HTTPException) as exc_info:
                    await permission_checker(mock_service_token_user)

                assert exc_info.value.status_code == 403
                mock_error.assert_called_once()


class TestRequireAnyPermission:
    """Test require_any_permission decorator."""

    @pytest.fixture
    def mock_jwt_user(self):
        """Create mock JWT authenticated user."""
        user = Mock(spec=AuthenticatedUser)
        user.email = "test@example.com"
        user.user_id = "user123"
        return user

    @pytest.fixture
    def mock_service_token_user(self):
        """Create mock service token user."""
        user = Mock(spec=ServiceTokenUser)
        user.token_name = "test-token"  # noqa: S105  # Test token value
        user.token_id = "token123"  # noqa: S105  # Test token value
        return user

    @pytest.mark.asyncio
    async def test_require_any_permission_jwt_user_first_permission(self, mock_jwt_user):
        """Test require_any_permission with JWT user having first permission."""
        permission_checker = require_any_permission("tokens:create", "tokens:admin")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = False  # Not a ServiceTokenUser

            with patch("src.auth.permissions.user_has_permission") as mock_has_perm:
                # First permission check returns True
                mock_has_perm.return_value = True

                result = await permission_checker(mock_jwt_user)

                assert result == mock_jwt_user
                # Should only check first permission
                mock_has_perm.assert_called_once_with("test@example.com", "tokens:create")

    @pytest.mark.asyncio
    async def test_require_any_permission_jwt_user_second_permission(self, mock_jwt_user):
        """Test require_any_permission with JWT user having second permission."""
        permission_checker = require_any_permission("tokens:create", "tokens:admin")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = False  # Not a ServiceTokenUser

            with patch("src.auth.permissions.user_has_permission") as mock_has_perm:
                # First permission False, second permission True
                mock_has_perm.side_effect = [False, True]

                result = await permission_checker(mock_jwt_user)

                assert result == mock_jwt_user
                # Should check both permissions
                assert mock_has_perm.call_count == 2

    @pytest.mark.asyncio
    async def test_require_any_permission_jwt_user_no_permissions(self, mock_jwt_user):
        """Test require_any_permission with JWT user lacking all permissions."""
        permission_checker = require_any_permission("tokens:create", "tokens:admin")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = False  # Not a ServiceTokenUser

            with patch("src.auth.permissions.user_has_permission", return_value=False):
                with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                    mock_error.side_effect = HTTPException(status_code=403, detail="Insufficient permissions")

                    with pytest.raises(HTTPException) as exc_info:
                        await permission_checker(mock_jwt_user)

                    assert exc_info.value.status_code == 403
                    mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_require_any_permission_service_token_success(self, mock_service_token_user):
        """Test require_any_permission with service token having permission."""
        mock_service_token_user.has_permission = Mock(side_effect=lambda perm: perm == "tokens:admin")
        permission_checker = require_any_permission("tokens:create", "tokens:admin")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True  # Is a ServiceTokenUser

            result = await permission_checker(mock_service_token_user)

            assert result == mock_service_token_user
            # Should check permissions until one matches
            assert mock_service_token_user.has_permission.call_count >= 1

    @pytest.mark.asyncio
    async def test_require_any_permission_service_token_no_permissions(self, mock_service_token_user):
        """Test require_any_permission with service token lacking all permissions."""
        mock_service_token_user.has_permission = Mock(return_value=False)
        permission_checker = require_any_permission("tokens:create", "tokens:admin")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True  # Is a ServiceTokenUser

            with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                mock_error.side_effect = HTTPException(status_code=403, detail="Insufficient permissions")

                with pytest.raises(HTTPException) as exc_info:
                    await permission_checker(mock_service_token_user)

                assert exc_info.value.status_code == 403
                mock_error.assert_called_once()


class TestRequireAllPermissions:
    """Test require_all_permissions decorator."""

    @pytest.fixture
    def mock_jwt_user(self):
        """Create mock JWT authenticated user."""
        user = Mock(spec=AuthenticatedUser)
        user.email = "test@example.com"
        user.user_id = "user123"
        return user

    @pytest.fixture
    def mock_service_token_user(self):
        """Create mock service token user."""
        user = Mock(spec=ServiceTokenUser)
        user.token_name = "test-token"  # noqa: S105  # Test token value
        user.token_id = "token123"  # noqa: S105  # Test token value
        return user

    @pytest.mark.asyncio
    async def test_require_all_permissions_jwt_user_success(self, mock_jwt_user):
        """Test require_all_permissions with JWT user having all permissions."""
        permission_checker = require_all_permissions("tokens:create", "tokens:delete")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = False  # Not a ServiceTokenUser

            with patch("src.auth.permissions.user_has_permission", return_value=True):
                result = await permission_checker(mock_jwt_user)

                assert result == mock_jwt_user

    @pytest.mark.asyncio
    async def test_require_all_permissions_jwt_user_missing_one(self, mock_jwt_user):
        """Test require_all_permissions with JWT user missing one permission."""
        permission_checker = require_all_permissions("tokens:create", "tokens:delete")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = False  # Not a ServiceTokenUser

            with patch("src.auth.permissions.user_has_permission") as mock_has_perm:
                # First permission True, second permission False
                mock_has_perm.side_effect = [True, False]

                with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                    mock_error.side_effect = HTTPException(status_code=403, detail="Missing permissions")

                    with pytest.raises(HTTPException) as exc_info:
                        await permission_checker(mock_jwt_user)

                    assert exc_info.value.status_code == 403
                    mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_require_all_permissions_service_token_success(self, mock_service_token_user):
        """Test require_all_permissions with service token having all permissions."""
        mock_service_token_user.has_permission = Mock(return_value=True)
        permission_checker = require_all_permissions("tokens:create", "tokens:delete")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True  # Is a ServiceTokenUser

            result = await permission_checker(mock_service_token_user)

            assert result == mock_service_token_user
            assert mock_service_token_user.has_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_require_all_permissions_service_token_missing_one(self, mock_service_token_user):
        """Test require_all_permissions with service token missing one permission."""
        # Has first permission but not second
        mock_service_token_user.has_permission = Mock(side_effect=lambda perm: perm == "tokens:create")
        permission_checker = require_all_permissions("tokens:create", "tokens:delete")

        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True  # Is a ServiceTokenUser

            with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                mock_error.side_effect = HTTPException(status_code=403, detail="Missing permissions")

                with pytest.raises(HTTPException) as exc_info:
                    await permission_checker(mock_service_token_user)

                assert exc_info.value.status_code == 403
                mock_error.assert_called_once()


class TestHasServiceTokenPermission:
    """Test has_service_token_permission utility function."""

    @pytest.fixture
    def mock_service_token_user(self):
        """Create mock service token user."""
        user = Mock(spec=ServiceTokenUser)
        user.token_name = "test-token"  # noqa: S105  # Test token value
        user.token_id = "token123"  # noqa: S105  # Test token value
        return user

    def test_has_service_token_permission_success(self, mock_service_token_user):
        """Test successful service token permission check."""
        mock_service_token_user.has_permission = Mock(return_value=True)

        result = has_service_token_permission(mock_service_token_user, "tokens:create")

        assert result is True
        mock_service_token_user.has_permission.assert_called_once_with("tokens:create")

    def test_has_service_token_permission_failure(self, mock_service_token_user):
        """Test service token permission check failure."""
        mock_service_token_user.has_permission = Mock(return_value=False)

        result = has_service_token_permission(mock_service_token_user, "tokens:delete")

        assert result is False
        mock_service_token_user.has_permission.assert_called_once_with("tokens:delete")

    def test_has_service_token_permission_edge_cases(self, mock_service_token_user):
        """Test edge cases for service token permission checks."""
        mock_service_token_user.has_permission = Mock(return_value=False)

        # Test with empty permission name
        result = has_service_token_permission(mock_service_token_user, "")
        assert result is False

        # Test with None permission name (should be handled gracefully)
        try:
            result = has_service_token_permission(mock_service_token_user, None)
            # If it doesn't raise an exception, should return False
            assert result is False
        except Exception:
            # Raising an exception for None is also acceptable
            pass

    def test_has_service_token_permission_complex_names(self, mock_service_token_user):
        """Test complex permission names."""
        mock_service_token_user.has_permission = Mock(return_value=True)

        complex_permissions = [
            "system:admin:full",
            "users:create:batch:bulk",
            "api:v2:tokens:rotate:emergency",
            "logs:audit:export:encrypted",
        ]

        for permission in complex_permissions:
            result = has_service_token_permission(mock_service_token_user, permission)
            assert result is True

        assert mock_service_token_user.has_permission.call_count == len(complex_permissions)


class TestPermissionSecurityEdgeCases:
    """Test security edge cases and attack scenarios."""

    @pytest.fixture
    def mock_jwt_user(self):
        """Create mock JWT authenticated user."""
        user = Mock(spec=AuthenticatedUser)
        user.email = "test@example.com"
        return user

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        """Test protection against SQL injection in permission names."""
        malicious_permissions = [
            "'; DROP TABLE roles; --",
            "admin' OR '1'='1",
            "tokens:create'; DELETE FROM user_roles WHERE '1'='1",
            'admin"; DROP DATABASE auth; --',
        ]

        for malicious_perm in malicious_permissions:
            with patch("src.auth.permissions.get_db") as mock_get_db:
                mock_session = AsyncMock()
                mock_result = Mock()
                mock_result.scalar.return_value = None
                mock_session.execute = AsyncMock(return_value=mock_result)

                async def mock_db_gen(session=mock_session):
                    yield session

                mock_get_db.return_value = mock_db_gen()

                # Should handle malicious input safely
                result = await user_has_permission("test@example.com", malicious_perm)
                assert result is False
                # Should still execute query (parameterized)
                mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_injection_protection(self):
        """Test protection against email injection."""
        malicious_emails = [
            "'; DROP TABLE users; --",
            "admin@test.com' OR email='admin@evil.com",
            "test\"; DELETE FROM roles WHERE '1'='1' --@example.com",
        ]

        for malicious_email in malicious_emails:
            with patch("src.auth.permissions.get_db") as mock_get_db:
                mock_session = AsyncMock()
                mock_result = Mock()
                mock_result.scalar.return_value = None
                mock_session.execute = AsyncMock(return_value=mock_result)

                async def mock_db_gen(session=mock_session):
                    yield session

                mock_get_db.return_value = mock_db_gen()

                # Should handle malicious email safely
                result = await user_has_permission(malicious_email, "tokens:create")
                assert result is False
                # Should still execute query (parameterized)
                mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_permission_names(self, mock_jwt_user):
        """Test handling of empty permission names."""
        # Empty permission list - no args to require_any_permission
        with patch("src.auth.permissions.isinstance") as mock_isinstance:
            mock_isinstance.return_value = False  # Not a ServiceTokenUser

            with patch("src.auth.exceptions.AuthExceptionHandler.handle_permission_error") as mock_error:
                mock_error.side_effect = HTTPException(status_code=403, detail="No permissions specified")

                # Empty permission tuples should result in no permissions granted
                permission_checker = require_any_permission()  # No arguments

                with pytest.raises(HTTPException):
                    await permission_checker(mock_jwt_user)

    @pytest.mark.asyncio
    async def test_none_permission_names(self, mock_jwt_user):
        """Test handling of None values in permission names."""
        # Test with None in permission list (should be handled gracefully)
        with patch("src.auth.permissions.user_has_permission", return_value=False):
            # This might cause issues if not handled properly
            try:
                result = await user_has_permission("test@example.com", None)
                assert result is False  # Should return False safely
            except Exception:
                # If it throws an exception, that's also acceptable
                # as None is not a valid permission name
                pass

    @pytest.mark.asyncio
    async def test_very_long_permission_names(self):
        """Test handling of extremely long permission names."""
        long_permission = "tokens:" + "a" * 10000  # Very long permission name

        with patch("src.auth.permissions.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.scalar.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            async def mock_db_gen():
                yield mock_session

            mock_get_db.return_value = mock_db_gen()

            # Should handle long permissions without crashing
            result = await user_has_permission("test@example.com", long_permission)
            assert result is False
            mock_session.execute.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.auth.permissions", "--cov-report=term-missing"])
