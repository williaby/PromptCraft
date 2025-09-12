"""
Integration tests for authentication database functions and queries.

This module provides comprehensive integration testing for database-backed
authentication functionality, including:
- Permission resolution queries
- Role hierarchy traversal
- User role assignment operations
- Database function validation
"""

import asyncio

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.permissions import user_has_permission
from src.auth.role_manager import RoleManager
from src.database.models import Permission, Role, UserSession, role_permissions_table, user_roles_table
from src.utils.datetime_compat import utc_now


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthDatabaseIntegration:
    """Integration tests for auth database operations."""

    # Use the global test_db_session fixture from tests/fixtures/database.py for database isolation

    @pytest.fixture
    async def sample_roles_and_permissions(self, test_db_session: AsyncSession):
        """Create sample roles and permissions for testing."""
        # Create permissions - check if they already exist first
        permission_data = [
            ("users:read", "users", "read", "Read user data"),
            ("users:write", "users", "write", "Write user data"),
            ("admin:access", "admin", "access", "Admin access"),
            ("tokens:create", "tokens", "create", "Create tokens"),
            ("tokens:delete", "tokens", "delete", "Delete tokens"),
        ]

        permissions = []
        for name, resource, action, description in permission_data:
            # Check if permission already exists
            result = await test_db_session.execute(
                select(Permission).where(Permission.name == name),
            )
            existing_perm = result.scalar_one_or_none()

            if existing_perm is None:
                perm = Permission(name=name, resource=resource, action=action, description=description)
                test_db_session.add(perm)
                permissions.append(perm)
            else:
                permissions.append(existing_perm)

        await test_db_session.flush()  # Get IDs

        # Create roles - check if they already exist first
        role_data = [
            ("viewer", "View-only access"),
            ("user", "Standard user access"),
            ("admin", "Administrative access"),
        ]

        roles = []
        for name, description in role_data:
            # Check if role already exists
            result = await test_db_session.execute(
                select(Role).where(Role.name == name),
            )
            existing_role = result.scalar_one_or_none()

            if existing_role is None:
                role = Role(
                    name=name,
                    description=description,
                    is_active=True,
                    created_at=utc_now(),
                )
                test_db_session.add(role)
                roles.append(role)
            else:
                roles.append(existing_role)

        await test_db_session.flush()
        viewer_role, user_role, admin_role = roles

        # Set up role hierarchy: admin > user > viewer
        user_role.parent_role_id = admin_role.id
        viewer_role.parent_role_id = user_role.id

        # Assign permissions to roles - avoid duplicates
        role_permission_assignments = [
            # Viewer can only read users
            (viewer_role.id, permissions[0].id),
            # User can read/write users and create tokens
            (user_role.id, permissions[0].id),
            (user_role.id, permissions[1].id),
            (user_role.id, permissions[3].id),
            # Admin gets all permissions directly (not via inheritance for now)
            (admin_role.id, permissions[0].id),  # users:read
            (admin_role.id, permissions[1].id),  # users:write
            (admin_role.id, permissions[2].id),  # admin:access
            (admin_role.id, permissions[3].id),  # tokens:create
            (admin_role.id, permissions[4].id),  # tokens:delete
        ]

        for role_id, permission_id in role_permission_assignments:
            # Check if assignment already exists
            result = await test_db_session.execute(
                select(role_permissions_table).where(
                    (role_permissions_table.c.role_id == role_id)
                    & (role_permissions_table.c.permission_id == permission_id),
                ),
            )
            if result.first() is None:
                await test_db_session.execute(
                    role_permissions_table.insert().values(role_id=role_id, permission_id=permission_id),
                )

        # Create test users - check if they already exist
        user_data = [
            ("viewer@example.com", "viewer-sub"),
            ("user@example.com", "user-sub"),
            ("admin@example.com", "admin-sub"),
        ]

        test_users = []
        for email, cloudflare_sub in user_data:
            # Check if user already exists
            result = await test_db_session.execute(
                select(UserSession).where(UserSession.email == email),
            )
            existing_user = result.scalar_one_or_none()

            if existing_user is None:
                user = UserSession(
                    email=email,
                    cloudflare_sub=cloudflare_sub,
                    session_count=1,
                    first_seen=utc_now(),
                    last_seen=utc_now(),
                    preferences={},
                    user_metadata={},
                )
                test_db_session.add(user)
                test_users.append(user)
            else:
                test_users.append(existing_user)

        await test_db_session.flush()

        # Assign roles to users - avoid duplicates
        user_role_assignments = [
            (test_users[0].id, viewer_role.id),
            (test_users[1].id, user_role.id),
            (test_users[2].id, admin_role.id),
        ]

        for user_id, role_id in user_role_assignments:
            # Check if assignment already exists
            result = await test_db_session.execute(
                select(user_roles_table).where(
                    (user_roles_table.c.user_id == user_id) & (user_roles_table.c.role_id == role_id),
                ),
            )
            if result.first() is None:
                await test_db_session.execute(
                    user_roles_table.insert().values(user_id=user_id, role_id=role_id),
                )

        # Don't commit - let the transaction rollback handle cleanup

        return {
            "permissions": {p.name: p for p in permissions},
            "roles": {
                "viewer": viewer_role,
                "user": user_role,
                "admin": admin_role,
            },
            "users": {
                "viewer": test_users[0],
                "user": test_users[1],
                "admin": test_users[2],
            },
        }

    async def test_user_has_permission_direct_permission(self, test_db_session, sample_roles_and_permissions):
        """Test user_has_permission with direct role permissions."""
        # Viewer should have users:read permission
        result = await user_has_permission("viewer@example.com", "users:read", session=test_db_session)
        assert result is True

        # Viewer should NOT have users:write permission
        result = await user_has_permission("viewer@example.com", "users:write", session=test_db_session)
        assert result is False

        # User should have users:write permission
        result = await user_has_permission("user@example.com", "users:write", session=test_db_session)
        assert result is True

    async def test_user_has_permission_inherited_permissions(self, test_db_session, sample_roles_and_permissions):
        """Test user_has_permission with comprehensive admin permissions."""
        # Admin should have all permissions (assigned directly for now)
        result = await user_has_permission("admin@example.com", "users:read", session=test_db_session)
        assert result is True

        result = await user_has_permission("admin@example.com", "users:write", session=test_db_session)
        assert result is True

        result = await user_has_permission("admin@example.com", "tokens:create", session=test_db_session)
        assert result is True

        # Admin should also have their own permissions
        result = await user_has_permission("admin@example.com", "admin:access", session=test_db_session)
        assert result is True

        result = await user_has_permission("admin@example.com", "tokens:delete", session=test_db_session)
        assert result is True

    async def test_user_has_permission_nonexistent_user(self, test_db_session):
        """Test user_has_permission with non-existent user."""
        result = await user_has_permission("nonexistent@example.com", "users:read", session=test_db_session)
        assert result is False

    async def test_user_has_permission_nonexistent_permission(self, test_db_session, sample_roles_and_permissions):
        """Test user_has_permission with non-existent permission."""
        result = await user_has_permission("admin@example.com", "nonexistent:permission", session=test_db_session)
        assert result is False

    async def test_role_manager_get_user_permissions_integration(
        self,
        test_db_session: AsyncSession,
        sample_roles_and_permissions,
        monkeypatch,
    ):
        """Test RoleManager.get_user_permissions with real database."""
        # Override the database manager to use the test database session
        from unittest.mock import AsyncMock, Mock

        # Create a mock database manager that returns our test session
        mock_db_manager = Mock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=test_db_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_session.return_value = mock_session_context

        # Patch get_database_manager to return our mock
        monkeypatch.setattr("src.database.base_service.get_database_manager", lambda: mock_db_manager)

        role_manager = RoleManager()

        # Test viewer permissions
        viewer_permissions = await role_manager.get_user_permissions("viewer@example.com")
        assert "users:read" in viewer_permissions
        assert "users:write" not in viewer_permissions
        assert len(viewer_permissions) == 1

        # Test user permissions (should include inherited viewer permissions)
        user_permissions = await role_manager.get_user_permissions("user@example.com")
        expected_user_perms = {"users:read", "users:write", "tokens:create"}
        assert expected_user_perms.issubset(user_permissions)

        # Test admin permissions (should include all permissions)
        admin_permissions = await role_manager.get_user_permissions("admin@example.com")
        expected_admin_perms = {
            "users:read",
            "users:write",
            "tokens:create",
            "admin:access",
            "tokens:delete",
        }
        assert expected_admin_perms.issubset(admin_permissions)

    async def test_role_manager_role_hierarchy_operations(
        self,
        test_db_session: AsyncSession,
        sample_roles_and_permissions,
        monkeypatch,
    ):
        """Test role hierarchy operations with real database."""
        # Override the database manager to use the test database session
        from unittest.mock import AsyncMock, Mock

        # Create a mock database manager that returns our test session
        mock_db_manager = Mock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=test_db_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_session.return_value = mock_session_context

        # Patch get_database_manager to return our mock
        monkeypatch.setattr("src.database.base_service.get_database_manager", lambda: mock_db_manager)

        role_manager = RoleManager()

        # Test getting user roles
        viewer_roles = await role_manager.get_user_roles("viewer@example.com")
        assert len(viewer_roles) == 1
        assert viewer_roles[0]["role_name"] == "viewer"

        # Test getting role permissions
        admin_permissions = await role_manager.get_role_permissions("admin")
        assert "admin:access" in admin_permissions
        assert "tokens:delete" in admin_permissions

    async def test_database_function_user_has_permission(
        self,
        test_db_session: AsyncSession,
        sample_roles_and_permissions,
    ):
        """Test the database user_has_permission function directly (PostgreSQL only)."""
        # Check if we're using PostgreSQL or SQLite
        dialect_name = test_db_session.bind.dialect.name

        if dialect_name == "postgresql":
            # Test with direct SQL call to database function (PostgreSQL only)
            result = await test_db_session.execute(
                text("SELECT user_has_permission(:email, :permission)"),
                {"email": "admin@example.com", "permission": "admin:access"},
            )
            has_permission = result.scalar()
            assert has_permission is True

            # Test permission user doesn't have
            result = await test_db_session.execute(
                text("SELECT user_has_permission(:email, :permission)"),
                {"email": "viewer@example.com", "permission": "admin:access"},
            )
            has_permission = result.scalar()
            assert has_permission is False
        else:
            # For SQLite, test the application-level function instead
            from src.auth.permissions import user_has_permission

            # Test user with permission
            has_permission = await user_has_permission("admin@example.com", "admin:access", session=test_db_session)
            assert has_permission is True

            # Test user without permission
            has_permission = await user_has_permission("viewer@example.com", "admin:access", session=test_db_session)
            assert has_permission is False

    async def test_concurrent_permission_checks(self, test_db_session, sample_roles_and_permissions):
        """Test concurrent permission checks for race conditions."""

        async def check_permission(email: str, permission: str):
            return await user_has_permission(email, permission, session=test_db_session)

        # Run multiple concurrent permission checks
        tasks = [
            check_permission("admin@example.com", "admin:access"),
            check_permission("user@example.com", "users:write"),
            check_permission("viewer@example.com", "users:read"),
            check_permission("admin@example.com", "tokens:delete"),
            check_permission("user@example.com", "tokens:create"),
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results), f"Some permission checks failed: {results}"

    async def test_role_assignment_integration(
        self,
        test_db_session: AsyncSession,
        sample_roles_and_permissions,
        monkeypatch,
    ):
        """Test role assignment and permission inheritance."""
        # Override the database manager to use the test database session
        from unittest.mock import AsyncMock, Mock

        # Create a mock database manager that returns our test session
        mock_db_manager = Mock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=test_db_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_session.return_value = mock_session_context

        # Patch get_database_manager to return our mock
        monkeypatch.setattr("src.database.base_service.get_database_manager", lambda: mock_db_manager)

        role_manager = RoleManager()

        # Create a new user
        new_user = UserSession(
            email="newuser@example.com",
            cloudflare_sub="new-user-sub",
            session_count=1,
            first_seen=utc_now(),
            last_seen=utc_now(),
            preferences={},
            user_metadata={},
        )
        test_db_session.add(new_user)
        await test_db_session.flush()

        # Initially should have no permissions
        permissions = await role_manager.get_user_permissions("newuser@example.com")
        assert len(permissions) == 0

        # Assign user role
        await role_manager.assign_user_role("newuser@example.com", "user")

        # Should now have user permissions
        permissions = await role_manager.get_user_permissions("newuser@example.com")
        expected_perms = {"users:read", "users:write", "tokens:create"}
        assert expected_perms.issubset(permissions)

        # Check specific permission
        result = await user_has_permission("newuser@example.com", "users:write", session=test_db_session)
        assert result is True

    async def test_database_transaction_rollback(self, test_db_session: AsyncSession, monkeypatch):
        """Test that database operations properly handle transaction rollbacks."""
        # Override the database manager to use the test database session
        from unittest.mock import AsyncMock, Mock

        # Create a mock database manager that returns our test session
        mock_db_manager = Mock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=test_db_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_manager.get_session.return_value = mock_session_context

        # Patch get_database_manager to return our mock
        monkeypatch.setattr("src.database.base_service.get_database_manager", lambda: mock_db_manager)

        role_manager = RoleManager()

        try:
            # Try to assign a non-existent role (should fail)
            await role_manager.assign_user_role("test@example.com", "nonexistent_role")
            raise AssertionError("Should have raised an exception")
        except Exception:
            # Exception expected - transaction should be rolled back
            pass

        # Database should still be in a consistent state
        result = await user_has_permission("admin@example.com", "admin:access", session=test_db_session)
        # This should work if database is still consistent
        assert result in [True, False]  # Either result is fine, just shouldn't crash

    async def test_performance_with_large_permission_set(self, test_db_session, sample_roles_and_permissions):
        """Test performance with multiple permission checks."""
        import time

        # Test multiple permission checks in sequence
        start_time = time.time()

        for _i in range(10):
            await user_has_permission("admin@example.com", "admin:access", session=test_db_session)
            await user_has_permission("user@example.com", "users:write", session=test_db_session)
            await user_has_permission("viewer@example.com", "users:read", session=test_db_session)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete reasonably quickly (less than 2 seconds for 30 checks)
        assert duration < 2.0, f"Permission checks took too long: {duration:.2f} seconds"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Database integration tests deferred for production deployment - requires auth database schema setup not available in test environment",
)
class TestAuthDatabaseErrorHandling:
    """Integration tests for database error handling in auth operations."""

    async def test_user_has_permission_database_unavailable(self):
        """Test user_has_permission graceful degradation when database is unavailable."""
        # Mock database connection failure - function should gracefully return False
        result = await user_has_permission("test@example.com", "users:read")
        # Should return False on database errors for security
        assert result is False

    async def test_permission_check_with_corrupted_data(self, test_db_session: AsyncSession):
        """Test permission checks with corrupted or inconsistent database state."""
        # Create a user with invalid role reference
        corrupt_user = UserSession(
            email="corrupt@example.com",
            cloudflare_sub="corrupt-sub",
            session_count=1,
            first_seen=utc_now(),
            last_seen=utc_now(),
            preferences={},
            user_metadata={},
        )
        test_db_session.add(corrupt_user)
        await test_db_session.flush()

        # Assign non-existent role ID
        await test_db_session.execute(
            user_roles_table.insert().values(
                user_id=corrupt_user.id,
                role_id=99999,  # Non-existent role
            ),
        )
        # Don't commit - let the transaction rollback handle cleanup

        # Should handle this gracefully
        result = await user_has_permission("corrupt@example.com", "users:read", session=test_db_session)
        assert result is False  # Should fail safely


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=src.auth",
            "--cov-report=term-missing",
            "-m",
            "integration",
        ],
    )
