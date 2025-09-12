"""Permission-based access control decorators and utilities for AUTH-3.

This module provides FastAPI dependency injection system for fine-grained permission checks.
It integrates with both JWT users (AUTH-1) and service tokens (AUTH-2) to provide unified
permission validation across the application.

Key Features:
- FastAPI dependency injection for permission checks
- Support for both JWT and service token authentication
- Database-backed permission resolution for JWT users
- Metadata-based permission checks for service tokens
- Hierarchical role inheritance for JWT users
"""

from collections.abc import Callable
import logging
from typing import Any

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import ServiceTokenUser, require_authentication
from src.auth.exceptions import AuthExceptionHandler
from src.auth.types import AuthenticatedUserType
from src.database.connection import get_db


logger = logging.getLogger(__name__)


async def user_has_permission(user_email: str, permission_name: str, session: AsyncSession | None = None) -> bool:
    """Check if a JWT user has a specific permission through their assigned roles.

    This function queries the database to check if a user has been assigned
    roles that grant the specified permission, including inherited permissions
    from parent roles.

    Args:
        user_email: Email address of the user
        permission_name: Name of the permission to check (e.g., 'tokens:create')
        session: Optional database session to use (for testing)

    Returns:
        True if user has the permission, False otherwise

    Raises:
        Exception: If database query fails (logged but not re-raised)
    """
    try:
        if session is None:
            db_gen = get_db()
            try:
                session = await db_gen.__anext__()
            except AttributeError:
                if hasattr(db_gen, "__aenter__"):
                    session = await db_gen.__aenter__()
                else:
                    raise RuntimeError("No database session available") from None

        # Try PostgreSQL function first, fall back to SQLAlchemy queries
        try:
            # Use the database function for permission checking (PostgreSQL)
            if session is None:
                raise RuntimeError("Database session not available")
            result = await session.execute(
                text("SELECT user_has_permission(:user_email, :permission_name)"),
                {"user_email": user_email, "permission_name": permission_name},
            )
            has_permission = result.scalar()
            logger.debug(f"User {user_email} permission check for '{permission_name}' (PG function): {has_permission}")
            return bool(has_permission)
        except Exception as pg_error:
            # Fallback to SQLAlchemy queries for SQLite compatibility
            logger.debug(f"PostgreSQL function unavailable, using SQLAlchemy fallback: {pg_error}")

            from sqlalchemy import select  # noqa: PLC0415  # Fallback import only when PostgreSQL unavailable

            from src.database.models import (  # noqa: PLC0415  # Fallback import only when PostgreSQL unavailable
                Permission,
                Role,
                UserSession,
                role_permissions_table,
                user_roles_table,
            )

            # Check if user exists and get their roles with permissions
            # This mimics the PostgreSQL function behavior using pure SQLAlchemy
            user_permissions_query = (
                select(Permission.name)
                .select_from(
                    UserSession.__table__.join(user_roles_table, UserSession.id == user_roles_table.c.user_id)
                    .join(Role.__table__, user_roles_table.c.role_id == Role.id)
                    .join(role_permissions_table, Role.id == role_permissions_table.c.role_id)
                    .join(Permission.__table__, role_permissions_table.c.permission_id == Permission.id),
                )
                .where(UserSession.email == user_email)
                .distinct()
            )

            if session is None:
                raise RuntimeError("Database session not available") from None
            result = await session.execute(user_permissions_query)
            user_permissions = [row[0] for row in result.fetchall()]

            has_permission = permission_name in user_permissions
            logger.debug(f"User {user_email} permission check for '{permission_name}' (SQLAlchemy): {has_permission}")
            logger.debug(f"User {user_email} has permissions: {user_permissions}")
            return has_permission

    except Exception as e:
        logger.error(f"Permission check failed for user {user_email}, permission {permission_name}: {e}")
        # Fail-safe: deny permission on database errors
        return False


def require_permission(permission_name: str) -> Callable[..., Any]:
    """FastAPI dependency factory for permission-based access control.

    Creates a FastAPI dependency that validates the current user has the specified
    permission. Works with both JWT users (through database role checks) and
    service tokens (through metadata permission checks).

    Args:
        permission_name: Name of the required permission (e.g., 'tokens:create')

    Returns:
        FastAPI dependency function that validates permission and returns authenticated user

    Example:
        @app.post("/tokens")
        async def create_token(
            current_user = Depends(require_permission("tokens:create"))
        ):
            # User is guaranteed to have 'tokens:create' permission
            pass
    """

    async def permission_checker(
        current_user: AuthenticatedUserType = Depends(require_authentication),
    ) -> AuthenticatedUserType:
        """Check if current user has the required permission.

        Args:
            current_user: Authenticated user from middleware

        Returns:
            The authenticated user if permission check passes

        Raises:
            HTTPException: 403 if user lacks the required permission
        """
        if isinstance(current_user, ServiceTokenUser):
            # Service token permission check (existing AUTH-2 logic)
            if not current_user.has_permission(permission_name):
                raise AuthExceptionHandler.handle_permission_error(
                    permission_name=permission_name,
                    user_identifier=f"service token '{current_user.token_name}'",
                    detail=f"Service token lacks required permission: {permission_name}",
                )
            logger.debug(
                f"Service token '{current_user.token_name}' granted access with permission '{permission_name}'",
            )
        else:
            # JWT user permission check (new AUTH-3 logic)
            if not await user_has_permission(current_user.email, permission_name):
                raise AuthExceptionHandler.handle_permission_error(
                    permission_name=permission_name,
                    user_identifier=current_user.email,
                )
            logger.debug(f"User '{current_user.email}' granted access with permission '{permission_name}'")

        return current_user

    return permission_checker


def require_any_permission(*permission_names: str) -> Callable[..., Any]:
    """FastAPI dependency factory for multiple permission options.

    Creates a FastAPI dependency that validates the current user has at least one
    of the specified permissions. Useful for endpoints that can be accessed by
    users with different but equivalent permissions.

    Args:
        *permission_names: Variable number of permission names

    Returns:
        FastAPI dependency function that validates any permission and returns authenticated user

    Example:
        @app.get("/data")
        async def get_data(
            current_user = Depends(require_any_permission("data:read", "data:admin"))
        ):
            # User has either 'data:read' OR 'data:admin' permission
            pass
    """

    async def any_permission_checker(
        current_user: AuthenticatedUserType = Depends(require_authentication),
    ) -> AuthenticatedUserType:
        """Check if current user has any of the required permissions.

        Args:
            current_user: Authenticated user from middleware

        Returns:
            The authenticated user if any permission check passes

        Raises:
            HTTPException: 403 if user lacks all required permissions
        """
        has_any_permission = False

        if isinstance(current_user, ServiceTokenUser):
            # Service token permission check
            for permission_name in permission_names:
                if current_user.has_permission(permission_name):
                    has_any_permission = True
                    logger.debug(
                        f"Service token '{current_user.token_name}' granted access with permission '{permission_name}'",
                    )
                    break
        else:
            # JWT user permission check
            for permission_name in permission_names:
                if await user_has_permission(current_user.email, permission_name):
                    has_any_permission = True
                    logger.debug(f"User '{current_user.email}' granted access with permission '{permission_name}'")
                    break

        if not has_any_permission:
            user_identifier = (
                f"service token '{current_user.token_name}'"
                if isinstance(current_user, ServiceTokenUser)
                else current_user.email
            )
            raise AuthExceptionHandler.handle_permission_error(
                user_identifier=user_identifier,
                detail=f"Insufficient permissions: one of {list(permission_names)} required",
            )

        return current_user

    return any_permission_checker


def require_all_permissions(*permission_names: str) -> Callable[..., Any]:
    """FastAPI dependency factory for multiple required permissions.

    Creates a FastAPI dependency that validates the current user has all
    of the specified permissions. Useful for highly privileged operations
    that require multiple specific permissions.

    Args:
        *permission_names: Variable number of permission names (all required)

    Returns:
        FastAPI dependency function that validates all permissions and returns authenticated user

    Example:
        @app.delete("/system/reset")
        async def system_reset(
            current_user = Depends(require_all_permissions("system:admin", "system:reset"))
        ):
            # User must have BOTH 'system:admin' AND 'system:reset' permissions
            pass
    """

    async def all_permissions_checker(
        current_user: AuthenticatedUserType = Depends(require_authentication),
    ) -> AuthenticatedUserType:
        """Check if current user has all required permissions.

        Args:
            current_user: Authenticated user from middleware

        Returns:
            The authenticated user if all permission checks pass

        Raises:
            HTTPException: 403 if user lacks any required permission
        """
        missing_permissions = []

        if isinstance(current_user, ServiceTokenUser):
            # Service token permission check
            for permission_name in permission_names:
                if not current_user.has_permission(permission_name):
                    missing_permissions.append(permission_name)
        else:
            # JWT user permission check
            for permission_name in permission_names:
                if not await user_has_permission(current_user.email, permission_name):
                    missing_permissions.append(permission_name)

        if missing_permissions:
            user_identifier = (
                f"service token '{current_user.token_name}'"
                if isinstance(current_user, ServiceTokenUser)
                else current_user.email
            )
            raise AuthExceptionHandler.handle_permission_error(
                user_identifier=user_identifier,
                detail=f"Insufficient permissions: missing {missing_permissions}",
            )

        logger.debug(
            f"{'Service token' if isinstance(current_user, ServiceTokenUser) else 'User'} "
            f"granted access with all required permissions: {list(permission_names)}",
        )
        return current_user

    return all_permissions_checker


def has_service_token_permission(service_token_user: ServiceTokenUser, permission_name: str) -> bool:
    """Utility function to check service token permissions without dependency injection.

    Args:
        service_token_user: Service token user instance
        permission_name: Name of the permission to check

    Returns:
        True if service token has the permission, False otherwise
    """
    return service_token_user.has_permission(permission_name)


# Common permission constants for consistent usage across the application
class Permissions:
    """Common permission names as constants for type safety and consistency."""

    # Service token management
    TOKENS_CREATE = "tokens:create"
    TOKENS_READ = "tokens:read"
    TOKENS_UPDATE = "tokens:update"
    TOKENS_DELETE = "tokens:delete"
    TOKENS_ROTATE = "tokens:rotate"

    # User management
    USERS_READ = "users:read"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    # Role management
    ROLES_CREATE = "roles:create"
    ROLES_READ = "roles:read"
    ROLES_UPDATE = "roles:update"
    ROLES_DELETE = "roles:delete"
    ROLES_ASSIGN = "roles:assign"

    # Permission management
    PERMISSIONS_CREATE = "permissions:create"
    PERMISSIONS_READ = "permissions:read"
    PERMISSIONS_UPDATE = "permissions:update"
    PERMISSIONS_DELETE = "permissions:delete"

    # System administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_STATUS = "system:status"
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_MONITOR = "system:monitor"

    # API access
    API_ACCESS = "api:access"
    API_ADMIN = "api:admin"
