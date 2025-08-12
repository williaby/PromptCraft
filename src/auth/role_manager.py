"""Role hierarchy management and permission resolution for AUTH-3.

This module provides role management functionality including:
- Role hierarchy traversal and permission inheritance
- Role assignment and revocation for users
- Permission management for roles
- Role validation and consistency checks

The role system supports hierarchical inheritance where child roles
automatically inherit permissions from their parent roles.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError

from src.database.connection import get_db
from src.database.models import Permission, Role, UserSession, role_permissions_table, user_roles_table

logger = logging.getLogger(__name__)


class RoleManagerError(Exception):
    """Base exception for role management operations."""

    pass


class RoleNotFoundError(RoleManagerError):
    """Raised when a role is not found."""

    pass


class UserNotFoundError(RoleManagerError):
    """Raised when a user is not found."""

    pass


class PermissionNotFoundError(RoleManagerError):
    """Raised when a permission is not found."""

    pass


class CircularRoleHierarchyError(RoleManagerError):
    """Raised when a circular dependency is detected in role hierarchy."""

    pass


class RoleManager:
    """Manages role hierarchy, assignments, and permission resolution."""

    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        parent_role_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new role.

        Args:
            name: Unique role name (lowercase, underscore-separated)
            description: Optional human-readable description
            parent_role_name: Optional parent role name for inheritance

        Returns:
            Dictionary with role information

        Raises:
            RoleManagerError: If role creation fails
            RoleNotFoundError: If parent role doesn't exist
        """
        try:
            async for session in get_db():
                # Validate parent role if specified
                parent_role_id = None
                if parent_role_name:
                    parent_result = await session.execute(
                        select(Role.id).where(Role.name == parent_role_name, Role.is_active == True)  # noqa: E712
                    )
                    parent_role = parent_result.scalar_one_or_none()
                    if not parent_role:
                        raise RoleNotFoundError(f"Parent role '{parent_role_name}' not found")
                    parent_role_id = parent_role

                # Create the role
                new_role = Role(
                    name=name,
                    description=description,
                    parent_role_id=parent_role_id,
                )

                session.add(new_role)
                await session.commit()
                await session.refresh(new_role)

                logger.info(f"Created role '{name}' with ID {new_role.id}")
                return {
                    "id": new_role.id,
                    "name": new_role.name,
                    "description": new_role.description,
                    "parent_role_id": new_role.parent_role_id,
                    "created_at": new_role.created_at,
                    "is_active": new_role.is_active,
                }

        except IntegrityError as e:
            logger.error(f"Role creation failed - integrity error: {e}")
            if "unique constraint" in str(e).lower():
                raise RoleManagerError(f"Role '{name}' already exists") from e
            raise RoleManagerError(f"Role creation failed: {e}") from e
        except Exception as e:
            logger.error(f"Role creation failed: {e}")
            raise RoleManagerError(f"Failed to create role: {e}") from e

    async def get_role(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get role information by name.

        Args:
            role_name: Name of the role to retrieve

        Returns:
            Dictionary with role information or None if not found
        """
        try:
            async for session in get_db():
                result = await session.execute(
                    select(Role).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role = result.scalar_one_or_none()

                if not role:
                    return None

                # Get parent role name if exists
                parent_name = None
                if role.parent_role_id:
                    parent_result = await session.execute(select(Role.name).where(Role.id == role.parent_role_id))
                    parent_name = parent_result.scalar_one_or_none()

                return {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "parent_role_id": role.parent_role_id,
                    "parent_role_name": parent_name,
                    "created_at": role.created_at,
                    "updated_at": role.updated_at,
                    "is_active": role.is_active,
                }

        except Exception as e:
            logger.error(f"Failed to get role '{role_name}': {e}")
            return None

    async def list_roles(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """List all roles.

        Args:
            include_inactive: Whether to include inactive roles

        Returns:
            List of role dictionaries
        """
        try:
            async for session in get_db():
                query = select(Role)
                if not include_inactive:
                    query = query.where(Role.is_active == True)  # noqa: E712

                result = await session.execute(query.order_by(Role.name))
                roles = result.scalars().all()

                role_list = []
                for role in roles:
                    # Get parent role name if exists
                    parent_name = None
                    if role.parent_role_id:
                        parent_result = await session.execute(select(Role.name).where(Role.id == role.parent_role_id))
                        parent_name = parent_result.scalar_one_or_none()

                    role_list.append(
                        {
                            "id": role.id,
                            "name": role.name,
                            "description": role.description,
                            "parent_role_id": role.parent_role_id,
                            "parent_role_name": parent_name,
                            "created_at": role.created_at,
                            "updated_at": role.updated_at,
                            "is_active": role.is_active,
                        }
                    )

                return role_list

        except Exception as e:
            logger.error(f"Failed to list roles: {e}")
            return []

    async def get_role_permissions(self, role_name: str) -> Set[str]:
        """Get all permissions for a role including inherited permissions.

        Args:
            role_name: Name of the role

        Returns:
            Set of permission names

        Raises:
            RoleNotFoundError: If role doesn't exist
        """
        try:
            async for session in get_db():
                # Get role ID
                role_result = await session.execute(
                    select(Role.id).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role_id = role_result.scalar_one_or_none()
                if not role_id:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                # Use database function for permission resolution
                result = await session.execute(text("SELECT permission_name FROM get_role_permissions(:role_id)"), {"role_id": role_id})
                permissions = {row[0] for row in result.fetchall()}

                logger.debug(f"Role '{role_name}' has {len(permissions)} permissions (including inherited)")
                return permissions

        except RoleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get permissions for role '{role_name}': {e}")
            return set()

    async def assign_permission_to_role(self, role_name: str, permission_name: str) -> bool:
        """Assign a permission to a role.

        Args:
            role_name: Name of the role
            permission_name: Name of the permission

        Returns:
            True if assignment was successful

        Raises:
            RoleNotFoundError: If role doesn't exist
            PermissionNotFoundError: If permission doesn't exist
        """
        try:
            async for session in get_db():
                # Get role ID
                role_result = await session.execute(
                    select(Role.id).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role_id = role_result.scalar_one_or_none()
                if not role_id:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                # Get permission ID
                perm_result = await session.execute(
                    select(Permission.id).where(Permission.name == permission_name, Permission.is_active == True)  # noqa: E712
                )
                permission_id = perm_result.scalar_one_or_none()
                if not permission_id:
                    raise PermissionNotFoundError(f"Permission '{permission_name}' not found")

                # Assign permission to role (ignore if already assigned)
                await session.execute(
                    insert(role_permissions_table)
                    .values(role_id=role_id, permission_id=permission_id)
                    .on_conflict_do_nothing()
                )
                await session.commit()

                logger.info(f"Assigned permission '{permission_name}' to role '{role_name}'")
                return True

        except (RoleNotFoundError, PermissionNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to assign permission '{permission_name}' to role '{role_name}': {e}")
            raise RoleManagerError(f"Permission assignment failed: {e}") from e

    async def revoke_permission_from_role(self, role_name: str, permission_name: str) -> bool:
        """Revoke a permission from a role.

        Args:
            role_name: Name of the role
            permission_name: Name of the permission

        Returns:
            True if revocation was successful

        Raises:
            RoleNotFoundError: If role doesn't exist
            PermissionNotFoundError: If permission doesn't exist
        """
        try:
            async for session in get_db():
                # Get role ID
                role_result = await session.execute(
                    select(Role.id).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role_id = role_result.scalar_one_or_none()
                if not role_id:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                # Get permission ID
                perm_result = await session.execute(
                    select(Permission.id).where(Permission.name == permission_name, Permission.is_active == True)  # noqa: E712
                )
                permission_id = perm_result.scalar_one_or_none()
                if not permission_id:
                    raise PermissionNotFoundError(f"Permission '{permission_name}' not found")

                # Revoke permission from role
                await session.execute(
                    delete(role_permissions_table).where(
                        role_permissions_table.c.role_id == role_id,
                        role_permissions_table.c.permission_id == permission_id,
                    )
                )
                await session.commit()

                logger.info(f"Revoked permission '{permission_name}' from role '{role_name}'")
                return True

        except (RoleNotFoundError, PermissionNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to revoke permission '{permission_name}' from role '{role_name}': {e}")
            raise RoleManagerError(f"Permission revocation failed: {e}") from e

    async def assign_user_role(self, user_email: str, role_name: str, assigned_by: Optional[str] = None) -> bool:
        """Assign a role to a user.

        Args:
            user_email: Email address of the user
            role_name: Name of the role to assign
            assigned_by: Email of the admin who assigned the role

        Returns:
            True if assignment was successful

        Raises:
            UserNotFoundError: If user doesn't exist
            RoleNotFoundError: If role doesn't exist
        """
        try:
            async for session in get_db():
                # Validate user exists
                user_result = await session.execute(select(UserSession.email).where(UserSession.email == user_email))
                if not user_result.scalar_one_or_none():
                    raise UserNotFoundError(f"User '{user_email}' not found")

                # Get role ID
                role_result = await session.execute(
                    select(Role.id).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role_id = role_result.scalar_one_or_none()
                if not role_id:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                # Use database function for assignment
                await session.execute(
                    text("SELECT assign_user_role(:user_email, :role_id, :assigned_by)"),
                    {"user_email": user_email, "role_id": role_id, "assigned_by": assigned_by},
                )
                await session.commit()

                logger.info(f"Assigned role '{role_name}' to user '{user_email}' by '{assigned_by}'")
                return True

        except (UserNotFoundError, RoleNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to assign role '{role_name}' to user '{user_email}': {e}")
            raise RoleManagerError(f"Role assignment failed: {e}") from e

    async def revoke_user_role(self, user_email: str, role_name: str) -> bool:
        """Revoke a role from a user.

        Args:
            user_email: Email address of the user
            role_name: Name of the role to revoke

        Returns:
            True if revocation was successful

        Raises:
            RoleNotFoundError: If role doesn't exist
        """
        try:
            async for session in get_db():
                # Get role ID
                role_result = await session.execute(
                    select(Role.id).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role_id = role_result.scalar_one_or_none()
                if not role_id:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                # Use database function for revocation
                result = await session.execute(
                    text("SELECT revoke_user_role(:user_email, :role_id)"), {"user_email": user_email, "role_id": role_id}
                )
                success = result.scalar()
                await session.commit()

                if success:
                    logger.info(f"Revoked role '{role_name}' from user '{user_email}'")
                else:
                    logger.warning(f"Role '{role_name}' was not assigned to user '{user_email}'")

                return bool(success)

        except RoleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to revoke role '{role_name}' from user '{user_email}': {e}")
            raise RoleManagerError(f"Role revocation failed: {e}") from e

    async def get_user_roles(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all roles assigned to a user.

        Args:
            user_email: Email address of the user

        Returns:
            List of role dictionaries with assignment information
        """
        try:
            async for session in get_db():
                # Use database function to get user roles
                result = await session.execute(text("SELECT * FROM get_user_roles(:user_email)"), {"user_email": user_email})
                rows = result.fetchall()

                roles = []
                for row in rows:
                    roles.append(
                        {
                            "role_id": row.role_id,
                            "role_name": row.role_name,
                            "role_description": row.role_description,
                            "assigned_at": row.assigned_at,
                        }
                    )

                logger.debug(f"User '{user_email}' has {len(roles)} assigned roles")
                return roles

        except Exception as e:
            logger.error(f"Failed to get roles for user '{user_email}': {e}")
            return []

    async def get_user_permissions(self, user_email: str) -> Set[str]:
        """Get all permissions for a user through their assigned roles.

        Args:
            user_email: Email address of the user

        Returns:
            Set of permission names
        """
        try:
            user_roles = await self.get_user_roles(user_email)
            all_permissions = set()

            for role_info in user_roles:
                role_permissions = await self.get_role_permissions(role_info["role_name"])
                all_permissions.update(role_permissions)

            logger.debug(f"User '{user_email}' has {len(all_permissions)} total permissions")
            return all_permissions

        except Exception as e:
            logger.error(f"Failed to get permissions for user '{user_email}': {e}")
            return set()

    async def validate_role_hierarchy(self, role_name: str, parent_role_name: str) -> bool:
        """Validate that adding a parent role won't create a circular dependency.

        Args:
            role_name: Name of the role to modify
            parent_role_name: Name of the proposed parent role

        Returns:
            True if hierarchy is valid, False if it would create a circular dependency

        Raises:
            RoleNotFoundError: If either role doesn't exist
        """
        try:
            async for session in get_db():
                # Get role IDs
                role_result = await session.execute(
                    select(Role.id).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role_id = role_result.scalar_one_or_none()
                if not role_id:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                parent_result = await session.execute(
                    select(Role.id).where(Role.name == parent_role_name, Role.is_active == True)  # noqa: E712
                )
                parent_id = parent_result.scalar_one_or_none()
                if not parent_id:
                    raise RoleNotFoundError(f"Parent role '{parent_role_name}' not found")

                # Check if parent role is already a descendant of the role (would create circular dependency)
                # Use a recursive query to check the hierarchy
                result = await session.execute(
                    text(
                        """
                        WITH RECURSIVE role_descendants AS (
                            SELECT id, parent_role_id, 0 as depth
                            FROM roles
                            WHERE id = :role_id AND is_active = true
                            
                            UNION ALL
                            
                            SELECT r.id, r.parent_role_id, rd.depth + 1
                            FROM roles r
                            INNER JOIN role_descendants rd ON r.parent_role_id = rd.id
                            WHERE r.is_active = true AND rd.depth < 10
                        )
                        SELECT EXISTS(SELECT 1 FROM role_descendants WHERE id = :parent_id)
                    """
                    ),
                    {"role_id": role_id, "parent_id": parent_id},
                )

                would_create_cycle = result.scalar()
                return not would_create_cycle

        except RoleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate role hierarchy for '{role_name}' -> '{parent_role_name}': {e}")
            return False

    async def delete_role(self, role_name: str, force: bool = False) -> bool:
        """Delete a role (soft delete by setting is_active=False).

        Args:
            role_name: Name of the role to delete
            force: If True, also removes all user assignments

        Returns:
            True if deletion was successful

        Raises:
            RoleNotFoundError: If role doesn't exist
            RoleManagerError: If role has dependencies and force=False
        """
        try:
            async for session in get_db():
                # Get role
                role_result = await session.execute(
                    select(Role).where(Role.name == role_name, Role.is_active == True)  # noqa: E712
                )
                role = role_result.scalar_one_or_none()
                if not role:
                    raise RoleNotFoundError(f"Role '{role_name}' not found")

                # Check for dependencies
                if not force:
                    # Check for child roles
                    child_result = await session.execute(
                        select(Role.name).where(Role.parent_role_id == role.id, Role.is_active == True)  # noqa: E712
                    )
                    child_roles = child_result.scalars().all()
                    if child_roles:
                        raise RoleManagerError(f"Role '{role_name}' has child roles: {list(child_roles)}. Use force=True to delete.")

                    # Check for user assignments
                    user_result = await session.execute(
                        select(user_roles_table.c.user_email).where(user_roles_table.c.role_id == role.id)
                    )
                    assigned_users = user_result.scalars().all()
                    if assigned_users:
                        raise RoleManagerError(
                            f"Role '{role_name}' is assigned to {len(assigned_users)} users. Use force=True to delete."
                        )

                # Perform soft delete
                if force:
                    # Remove user assignments
                    await session.execute(delete(user_roles_table).where(user_roles_table.c.role_id == role.id))

                    # Update child roles to remove parent
                    await session.execute(
                        update(Role)
                        .where(Role.parent_role_id == role.id)
                        .values(parent_role_id=None, updated_at=datetime.utcnow())
                    )

                # Soft delete the role
                await session.execute(
                    update(Role).where(Role.id == role.id).values(is_active=False, updated_at=datetime.utcnow())
                )
                await session.commit()

                logger.info(f"Deleted role '{role_name}' (force={force})")
                return True

        except (RoleNotFoundError, RoleManagerError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete role '{role_name}': {e}")
            raise RoleManagerError(f"Role deletion failed: {e}") from e