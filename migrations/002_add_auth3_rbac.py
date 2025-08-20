"""Add AUTH-3 Role-Based Access Control schema and functions

Revision ID: 002_add_auth3_rbac
Revises: 001_auth_schema
Create Date: 2025-01-13 10:30:00.000000

This migration adds the AUTH-3 role-based access control system including:
- Roles and permissions tables
- Junction tables for many-to-many relationships
- PostgreSQL functions for efficient permission resolution
- Indexes for optimal query performance
- Seed data for common permissions and roles

"""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_auth3_rbac"
down_revision = "001_auth_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply AUTH-3 schema changes."""

    # =============================================================================
    # CREATE ROLES TABLE
    # =============================================================================

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True, comment="Unique role identifier"),
        sa.Column("name", sa.String(50), nullable=False, comment="Unique role name (e.g., admin, user, api_user)"),
        sa.Column("description", sa.Text(), nullable=True, comment="Human-readable description of the role"),
        sa.Column(
            "parent_role_id",
            sa.Integer(),
            nullable=True,
            comment="Parent role ID for inheritance (NULL for top-level roles)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Role creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Role last update timestamp",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Whether the role is active and can be assigned",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["parent_role_id"],
            ["roles.id"],
        ),
        sa.UniqueConstraint("name"),
        comment="Role hierarchy for permission inheritance",
    )

    # Create indexes for roles table
    op.create_index("ix_roles_name", "roles", ["name"])
    op.create_index(
        "idx_roles_parent_role_id_active",
        "roles",
        ["parent_role_id", "is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # =============================================================================
    # CREATE PERMISSIONS TABLE
    # =============================================================================

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True, comment="Unique permission identifier"),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="Unique permission name (e.g., tokens:create, users:read)",
        ),
        sa.Column(
            "resource",
            sa.String(50),
            nullable=False,
            comment="Resource type this permission applies to (e.g., tokens, users)",
        ),
        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
            comment="Action this permission allows (e.g., create, read, update, delete)",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="Human-readable description of the permission"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Permission creation timestamp",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Whether the permission is active and can be assigned",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        comment="Granular permissions for resource access control",
    )

    # Create indexes for permissions table
    op.create_index("ix_permissions_name", "permissions", ["name"])
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_index("ix_permissions_action", "permissions", ["action"])
    op.create_index(
        "idx_permissions_name_active",
        "permissions",
        ["name", "is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # =============================================================================
    # CREATE JUNCTION TABLES
    # =============================================================================

    # Many-to-many relationship between roles and permissions
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
        ),
        comment="Junction table for role-permission assignments",
    )

    # Create indexes for role_permissions table
    op.create_index("idx_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("idx_role_permissions_permission_id", "role_permissions", ["permission_id"])

    # Many-to-many relationship between users and roles
    op.create_table(
        "user_roles",
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("user_email", "role_id"),
        sa.ForeignKeyConstraint(
            ["user_email"],
            ["user_sessions.email"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        comment="Junction table for user-role assignments",
    )

    # Create indexes for user_roles table
    op.create_index("idx_user_roles_user_email", "user_roles", ["user_email"])
    op.create_index("idx_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("idx_user_roles_composite", "user_roles", ["user_email", "role_id"])

    # =============================================================================
    # APPLY POSTGRESQL FUNCTIONS
    # =============================================================================

    # Read and execute the PostgreSQL functions file
    import os

    # Get the path to the functions file relative to this migration
    functions_file = os.path.join(os.path.dirname(__file__), "auth3_functions.sql")

    if os.path.exists(functions_file):
        with open(functions_file) as f:
            functions_sql = f.read()

        # Execute the functions SQL
        op.execute(sa.text(functions_sql))
    else:
        # Fallback: inline essential functions if file not found
        op.execute(
            sa.text(
                """
        -- Essential AUTH-3 functions for role-based permission system

        -- Function: get_role_permissions(role_id)
        CREATE OR REPLACE FUNCTION get_role_permissions(input_role_id INTEGER)
        RETURNS TABLE(permission_name VARCHAR(100))
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            WITH RECURSIVE role_hierarchy AS (
                SELECT r.id, r.parent_role_id, 0 as depth
                FROM roles r
                WHERE r.id = input_role_id AND r.is_active = true

                UNION ALL

                SELECT r.id, r.parent_role_id, rh.depth + 1
                FROM roles r
                INNER JOIN role_hierarchy rh ON r.id = rh.parent_role_id
                WHERE r.is_active = true AND rh.depth < 10
            )
            SELECT DISTINCT p.name::VARCHAR(100)
            FROM role_hierarchy rh
            INNER JOIN role_permissions rp ON rh.id = rp.role_id
            INNER JOIN permissions p ON rp.permission_id = p.id
            WHERE p.is_active = true;
        END;
        $$;

        -- Function: user_has_permission(user_email, permission_name)
        CREATE OR REPLACE FUNCTION user_has_permission(
            input_user_email VARCHAR(255),
            input_permission_name VARCHAR(100)
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        AS $$
        DECLARE
            has_permission BOOLEAN := false;
        BEGIN
            SELECT EXISTS(
                SELECT 1
                FROM user_roles ur
                INNER JOIN get_role_permissions(ur.role_id) grp ON true
                WHERE ur.user_email = input_user_email
                  AND grp.permission_name = input_permission_name
            ) INTO has_permission;

            RETURN has_permission;
        END;
        $$;

        -- Function: assign_user_role(user_email, role_id, assigned_by)
        CREATE OR REPLACE FUNCTION assign_user_role(
            input_user_email VARCHAR(255),
            input_role_id INTEGER,
            input_assigned_by VARCHAR(255) DEFAULT NULL
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        AS $$
        DECLARE
            assignment_exists BOOLEAN := false;
        BEGIN
            SELECT EXISTS(
                SELECT 1 FROM user_roles
                WHERE user_email = input_user_email AND role_id = input_role_id
            ) INTO assignment_exists;

            IF NOT assignment_exists THEN
                INSERT INTO user_roles (user_email, role_id)
                VALUES (input_user_email, input_role_id);
                RETURN true;
            END IF;

            RETURN false;
        END;
        $$;

        -- Function: revoke_user_role(user_email, role_id)
        CREATE OR REPLACE FUNCTION revoke_user_role(
            input_user_email VARCHAR(255),
            input_role_id INTEGER
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        AS $$
        DECLARE
            rows_affected INTEGER;
        BEGIN
            DELETE FROM user_roles
            WHERE user_email = input_user_email AND role_id = input_role_id;

            GET DIAGNOSTICS rows_affected = ROW_COUNT;
            RETURN rows_affected > 0;
        END;
        $$;

        -- Function: get_user_roles(user_email)
        CREATE OR REPLACE FUNCTION get_user_roles(input_user_email VARCHAR(255))
        RETURNS TABLE(
            role_id INTEGER,
            role_name VARCHAR(50),
            role_description TEXT,
            assigned_at TIMESTAMP WITH TIME ZONE
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                r.id::INTEGER,
                r.name::VARCHAR(50),
                r.description::TEXT,
                COALESCE(r.created_at, CURRENT_TIMESTAMP)::TIMESTAMP WITH TIME ZONE
            FROM user_roles ur
            INNER JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_email = input_user_email
              AND r.is_active = true
            ORDER BY r.name;
        END;
        $$;
        """,
            ),
        )


def upgrade_seed_data() -> None:
    """Insert seed data for common permissions and roles."""

    # =============================================================================
    # SEED PERMISSIONS
    # =============================================================================

    permissions_data = [
        # Service token management
        ("tokens:create", "tokens", "create", "Create new service tokens"),
        ("tokens:read", "tokens", "read", "View service token information"),
        ("tokens:update", "tokens", "update", "Update service token metadata"),
        ("tokens:delete", "tokens", "delete", "Delete service tokens"),
        ("tokens:rotate", "tokens", "rotate", "Rotate service tokens"),
        # User management
        ("users:read", "users", "read", "View user information"),
        ("users:update", "users", "update", "Update user profiles"),
        ("users:delete", "users", "delete", "Delete users"),
        # Role management
        ("roles:create", "roles", "create", "Create new roles"),
        ("roles:read", "roles", "read", "View role information"),
        ("roles:update", "roles", "update", "Update role details"),
        ("roles:delete", "roles", "delete", "Delete roles"),
        ("roles:assign", "roles", "assign", "Assign roles to users"),
        # Permission management
        ("permissions:create", "permissions", "create", "Create new permissions"),
        ("permissions:read", "permissions", "read", "View permission information"),
        ("permissions:update", "permissions", "update", "Update permission details"),
        ("permissions:delete", "permissions", "delete", "Delete permissions"),
        # System administration
        ("system:admin", "system", "admin", "Full system administration access"),
        ("system:status", "system", "status", "View system status"),
        ("system:audit", "system", "audit", "Access audit logs"),
        ("system:monitor", "system", "monitor", "Monitor system performance"),
        # API access
        ("api:access", "api", "access", "Basic API access"),
        ("api:admin", "api", "admin", "Administrative API access"),
    ]

    # Insert permissions
    for name, resource, action, description in permissions_data:
        op.execute(
            sa.text(
                """
            INSERT INTO permissions (name, resource, action, description, created_at, is_active)
            VALUES (:name, :resource, :action, :description, :created_at, true)
            ON CONFLICT (name) DO NOTHING
        """,
            ),
            {
                "name": name,
                "resource": resource,
                "action": action,
                "description": description,
                "created_at": datetime.now(UTC),
            },
        )

    # =============================================================================
    # SEED ROLES
    # =============================================================================

    roles_data = [
        ("super_admin", "Super Administrator with full system access", None),
        ("admin", "Administrator with management permissions", None),
        ("user_manager", "Manages users and their roles", "admin"),
        ("token_manager", "Manages service tokens", "admin"),
        ("api_user", "Basic API access for applications", None),
        ("readonly_user", "Read-only access to system information", None),
    ]

    # Insert roles
    for name, description, parent_name in roles_data:
        parent_id_query = ""
        params = {"name": name, "description": description, "created_at": datetime.now(UTC)}

        if parent_name:
            params["parent_name"] = parent_name

            # Use parameterized subquery to avoid SQL injection concerns
            op.execute(
                sa.text("""
                INSERT INTO roles (name, description, parent_role_id, created_at, is_active)
                VALUES (:name, :description, (SELECT id FROM roles WHERE name = :parent_name), :created_at, true)
                ON CONFLICT (name) DO NOTHING
                """),
                params,
            )
        else:
            op.execute(
                sa.text(
                    """
                INSERT INTO roles (name, description, parent_role_id, created_at, is_active)
                VALUES (:name, :description, NULL, :created_at, true)
                ON CONFLICT (name) DO NOTHING
            """,
                ),
                params,
            )

    # =============================================================================
    # ASSIGN PERMISSIONS TO ROLES
    # =============================================================================

    # Super admin gets all permissions
    op.execute(
        sa.text(
            """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.name = 'super_admin'
        ON CONFLICT DO NOTHING
    """,
        ),
    )

    # Admin gets most permissions (excluding super admin privileges)
    admin_permissions = [
        "tokens:create",
        "tokens:read",
        "tokens:update",
        "tokens:delete",
        "tokens:rotate",
        "users:read",
        "users:update",
        "users:delete",
        "roles:create",
        "roles:read",
        "roles:update",
        "roles:delete",
        "roles:assign",
        "permissions:read",
        "system:status",
        "system:audit",
        "system:monitor",
        "api:admin",
    ]

    for perm in admin_permissions:
        op.execute(
            sa.text(
                """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'admin' AND p.name = :perm
            ON CONFLICT DO NOTHING
        """,
            ),
            {"perm": perm},
        )

    # User manager permissions
    user_manager_permissions = ["users:read", "users:update", "roles:read", "roles:assign", "api:access"]

    for perm in user_manager_permissions:
        op.execute(
            sa.text(
                """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'user_manager' AND p.name = :perm
            ON CONFLICT DO NOTHING
        """,
            ),
            {"perm": perm},
        )

    # Token manager permissions
    token_manager_permissions = [
        "tokens:create",
        "tokens:read",
        "tokens:update",
        "tokens:delete",
        "tokens:rotate",
        "api:access",
    ]

    for perm in token_manager_permissions:
        op.execute(
            sa.text(
                """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'token_manager' AND p.name = :perm
            ON CONFLICT DO NOTHING
        """,
            ),
            {"perm": perm},
        )

    # API user permissions
    api_user_permissions = ["api:access", "system:status"]

    for perm in api_user_permissions:
        op.execute(
            sa.text(
                """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'api_user' AND p.name = :perm
            ON CONFLICT DO NOTHING
        """,
            ),
            {"perm": perm},
        )

    # Readonly user permissions
    readonly_permissions = ["users:read", "roles:read", "permissions:read", "system:status", "api:access"]

    for perm in readonly_permissions:
        op.execute(
            sa.text(
                """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'readonly_user' AND p.name = :perm
            ON CONFLICT DO NOTHING
        """,
            ),
            {"perm": perm},
        )


def downgrade() -> None:
    """Remove AUTH-3 schema changes."""

    # Drop PostgreSQL functions
    op.execute(sa.text("DROP FUNCTION IF EXISTS get_role_permissions(INTEGER)"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS user_has_permission(VARCHAR(255), VARCHAR(100))"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS assign_user_role(VARCHAR(255), INTEGER, VARCHAR(255))"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS revoke_user_role(VARCHAR(255), INTEGER)"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS get_user_roles(VARCHAR(255))"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS validate_role_hierarchy_circular(INTEGER, INTEGER)"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS get_role_hierarchy_depth(INTEGER)"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS refresh_role_permission_cache()"))

    # Drop junction tables
    op.drop_table("user_roles")
    op.drop_table("role_permissions")

    # Drop main tables
    op.drop_table("permissions")
    op.drop_table("roles")


# Apply seed data after table creation
def upgrade() -> None:
    """Main upgrade function that applies schema and seed data."""
    upgrade_schema()
    upgrade_seed_data()


def upgrade_schema() -> None:
    """Apply only the schema changes without seed data."""
    # Move the existing upgrade() function content here

    # =============================================================================
    # CREATE ROLES TABLE
    # =============================================================================

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True, comment="Unique role identifier"),
        sa.Column("name", sa.String(50), nullable=False, comment="Unique role name (e.g., admin, user, api_user)"),
        sa.Column("description", sa.Text(), nullable=True, comment="Human-readable description of the role"),
        sa.Column(
            "parent_role_id",
            sa.Integer(),
            nullable=True,
            comment="Parent role ID for inheritance (NULL for top-level roles)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Role creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Role last update timestamp",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Whether the role is active and can be assigned",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["parent_role_id"],
            ["roles.id"],
        ),
        sa.UniqueConstraint("name"),
        comment="Role hierarchy for permission inheritance",
    )

    # Create indexes for roles table
    op.create_index("ix_roles_name", "roles", ["name"])
    op.create_index(
        "idx_roles_parent_role_id_active",
        "roles",
        ["parent_role_id", "is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # =============================================================================
    # CREATE PERMISSIONS TABLE
    # =============================================================================

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True, comment="Unique permission identifier"),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="Unique permission name (e.g., tokens:create, users:read)",
        ),
        sa.Column(
            "resource",
            sa.String(50),
            nullable=False,
            comment="Resource type this permission applies to (e.g., tokens, users)",
        ),
        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
            comment="Action this permission allows (e.g., create, read, update, delete)",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="Human-readable description of the permission"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Permission creation timestamp",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Whether the permission is active and can be assigned",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        comment="Granular permissions for resource access control",
    )

    # Create indexes for permissions table
    op.create_index("ix_permissions_name", "permissions", ["name"])
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_index("ix_permissions_action", "permissions", ["action"])
    op.create_index(
        "idx_permissions_name_active",
        "permissions",
        ["name", "is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # =============================================================================
    # CREATE JUNCTION TABLES
    # =============================================================================

    # Many-to-many relationship between roles and permissions
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
        ),
        comment="Junction table for role-permission assignments",
    )

    # Create indexes for role_permissions table
    op.create_index("idx_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("idx_role_permissions_permission_id", "role_permissions", ["permission_id"])

    # Many-to-many relationship between users and roles
    op.create_table(
        "user_roles",
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("user_email", "role_id"),
        sa.ForeignKeyConstraint(
            ["user_email"],
            ["user_sessions.email"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
        ),
        comment="Junction table for user-role assignments",
    )

    # Create indexes for user_roles table
    op.create_index("idx_user_roles_user_email", "user_roles", ["user_email"])
    op.create_index("idx_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("idx_user_roles_composite", "user_roles", ["user_email", "role_id"])

    # =============================================================================
    # APPLY POSTGRESQL FUNCTIONS
    # =============================================================================

    # Read and execute the PostgreSQL functions file
    import os

    # Get the path to the functions file relative to this migration
    functions_file = os.path.join(os.path.dirname(__file__), "auth3_functions.sql")

    if os.path.exists(functions_file):
        with open(functions_file) as f:
            functions_sql = f.read()

        # Execute the functions SQL
        op.execute(sa.text(functions_sql))
    else:
        # Fallback: inline essential functions if file not found
        op.execute(
            sa.text(
                """
        -- Essential AUTH-3 functions for role-based permission system

        -- Function: get_role_permissions(role_id)
        CREATE OR REPLACE FUNCTION get_role_permissions(input_role_id INTEGER)
        RETURNS TABLE(permission_name VARCHAR(100))
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            WITH RECURSIVE role_hierarchy AS (
                SELECT r.id, r.parent_role_id, 0 as depth
                FROM roles r
                WHERE r.id = input_role_id AND r.is_active = true

                UNION ALL

                SELECT r.id, r.parent_role_id, rh.depth + 1
                FROM roles r
                INNER JOIN role_hierarchy rh ON r.id = rh.parent_role_id
                WHERE r.is_active = true AND rh.depth < 10
            )
            SELECT DISTINCT p.name::VARCHAR(100)
            FROM role_hierarchy rh
            INNER JOIN role_permissions rp ON rh.id = rp.role_id
            INNER JOIN permissions p ON rp.permission_id = p.id
            WHERE p.is_active = true;
        END;
        $$;

        -- Function: user_has_permission(user_email, permission_name)
        CREATE OR REPLACE FUNCTION user_has_permission(
            input_user_email VARCHAR(255),
            input_permission_name VARCHAR(100)
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        AS $$
        DECLARE
            has_permission BOOLEAN := false;
        BEGIN
            SELECT EXISTS(
                SELECT 1
                FROM user_roles ur
                INNER JOIN get_role_permissions(ur.role_id) grp ON true
                WHERE ur.user_email = input_user_email
                  AND grp.permission_name = input_permission_name
            ) INTO has_permission;

            RETURN has_permission;
        END;
        $$;

        -- Function: assign_user_role(user_email, role_id, assigned_by)
        CREATE OR REPLACE FUNCTION assign_user_role(
            input_user_email VARCHAR(255),
            input_role_id INTEGER,
            input_assigned_by VARCHAR(255) DEFAULT NULL
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        AS $$
        DECLARE
            assignment_exists BOOLEAN := false;
        BEGIN
            SELECT EXISTS(
                SELECT 1 FROM user_roles
                WHERE user_email = input_user_email AND role_id = input_role_id
            ) INTO assignment_exists;

            IF NOT assignment_exists THEN
                INSERT INTO user_roles (user_email, role_id)
                VALUES (input_user_email, input_role_id);
                RETURN true;
            END IF;

            RETURN false;
        END;
        $$;

        -- Function: revoke_user_role(user_email, role_id)
        CREATE OR REPLACE FUNCTION revoke_user_role(
            input_user_email VARCHAR(255),
            input_role_id INTEGER
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        AS $$
        DECLARE
            rows_affected INTEGER;
        BEGIN
            DELETE FROM user_roles
            WHERE user_email = input_user_email AND role_id = input_role_id;

            GET DIAGNOSTICS rows_affected = ROW_COUNT;
            RETURN rows_affected > 0;
        END;
        $$;

        -- Function: get_user_roles(user_email)
        CREATE OR REPLACE FUNCTION get_user_roles(input_user_email VARCHAR(255))
        RETURNS TABLE(
            role_id INTEGER,
            role_name VARCHAR(50),
            role_description TEXT,
            assigned_at TIMESTAMP WITH TIME ZONE
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                r.id::INTEGER,
                r.name::VARCHAR(50),
                r.description::TEXT,
                COALESCE(r.created_at, CURRENT_TIMESTAMP)::TIMESTAMP WITH TIME ZONE
            FROM user_roles ur
            INNER JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_email = input_user_email
              AND r.is_active = true
            ORDER BY r.name;
        END;
        $$;
        """,
            ),
        )
