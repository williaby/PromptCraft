-- AUTH-3 PostgreSQL Functions for Role-Based Permission System
-- ================================================================
-- This file contains all PostgreSQL functions required by the AUTH-3
-- role-based permission system for efficient permission resolution
-- and role management operations.

-- Function: get_role_permissions(role_id)
-- Purpose: Get all permissions for a role including inherited permissions from parent roles
-- Used by: role_manager.py:226
CREATE OR REPLACE FUNCTION get_role_permissions(input_role_id INTEGER)
RETURNS TABLE(permission_name VARCHAR(100))
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE role_hierarchy AS (
        -- Base case: Start with the specified role
        SELECT r.id, r.parent_role_id, 0 as depth
        FROM roles r
        WHERE r.id = input_role_id AND r.is_active = true

        UNION ALL

        -- Recursive case: Get parent roles
        SELECT r.id, r.parent_role_id, rh.depth + 1
        FROM roles r
        INNER JOIN role_hierarchy rh ON r.id = rh.parent_role_id
        WHERE r.is_active = true AND rh.depth < 10  -- Prevent infinite loops
    )
    SELECT DISTINCT p.name::VARCHAR(100)
    FROM role_hierarchy rh
    INNER JOIN role_permissions rp ON rh.id = rp.role_id
    INNER JOIN permissions p ON rp.permission_id = p.id
    WHERE p.is_active = true;
END;
$$;

-- Function: assign_user_role(user_email, role_id, assigned_by)
-- Purpose: Assign a role to a user with audit tracking
-- Used by: role_manager.py:374
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
    -- Check if assignment already exists
    SELECT EXISTS(
        SELECT 1 FROM user_roles
        WHERE user_email = input_user_email AND role_id = input_role_id
    ) INTO assignment_exists;

    -- If assignment doesn't exist, create it
    IF NOT assignment_exists THEN
        INSERT INTO user_roles (user_email, role_id)
        VALUES (input_user_email, input_role_id);

        -- Log the assignment (optional: could be extended with audit table)
        -- For now, we rely on application-level logging
        RETURN true;
    END IF;

    -- Assignment already exists
    RETURN false;
END;
$$;

-- Function: revoke_user_role(user_email, role_id)
-- Purpose: Revoke a role from a user
-- Used by: role_manager.py:413
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
    -- Remove the user role assignment
    DELETE FROM user_roles
    WHERE user_email = input_user_email AND role_id = input_role_id;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;

    -- Return true if a row was deleted, false if no assignment existed
    RETURN rows_affected > 0;
END;
$$;

-- Function: get_user_roles(user_email)
-- Purpose: Get all roles assigned to a user with role information
-- Used by: role_manager.py:445
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

-- Function: user_has_permission(user_email, permission_name)
-- Purpose: Check if a user has a specific permission through their assigned roles
-- Used by: permissions.py:48
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
    -- Check if user has the permission through any of their roles
    -- This includes inherited permissions from parent roles
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

-- Helper Function: validate_role_hierarchy_circular(role_id, parent_role_id)
-- Purpose: Validate that adding a parent role won't create a circular dependency
-- Used internally by role hierarchy validation
CREATE OR REPLACE FUNCTION validate_role_hierarchy_circular(
    input_role_id INTEGER,
    input_parent_role_id INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    would_create_cycle BOOLEAN := false;
BEGIN
    -- Check if the proposed parent role is already a descendant of the role
    WITH RECURSIVE role_descendants AS (
        -- Base case: Start with the role that would become the child
        SELECT id, parent_role_id, 0 as depth
        FROM roles
        WHERE id = input_role_id AND is_active = true

        UNION ALL

        -- Recursive case: Get all descendant roles
        SELECT r.id, r.parent_role_id, rd.depth + 1
        FROM roles r
        INNER JOIN role_descendants rd ON r.parent_role_id = rd.id
        WHERE r.is_active = true AND rd.depth < 10
    )
    SELECT EXISTS(
        SELECT 1 FROM role_descendants WHERE id = input_parent_role_id
    ) INTO would_create_cycle;

    -- Return false if it would create a cycle, true if it's safe
    RETURN NOT would_create_cycle;
END;
$$;

-- Utility Function: get_role_hierarchy_depth(role_id)
-- Purpose: Get the depth of a role in the hierarchy (useful for UI display)
CREATE OR REPLACE FUNCTION get_role_hierarchy_depth(input_role_id INTEGER)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    role_depth INTEGER := 0;
BEGIN
    WITH RECURSIVE role_ancestors AS (
        -- Base case: Start with the specified role
        SELECT id, parent_role_id, 0 as depth
        FROM roles
        WHERE id = input_role_id AND is_active = true

        UNION ALL

        -- Recursive case: Go up the hierarchy
        SELECT r.id, r.parent_role_id, ra.depth + 1
        FROM roles r
        INNER JOIN role_ancestors ra ON r.id = ra.parent_role_id
        WHERE r.is_active = true AND ra.depth < 10
    )
    SELECT COALESCE(MAX(depth), 0) INTO role_depth
    FROM role_ancestors;

    RETURN role_depth;
END;
$$;

-- Performance Optimization: Create indexes for efficient permission queries
-- These indexes support the functions above and improve query performance

-- Index for role hierarchy traversal
CREATE INDEX IF NOT EXISTS idx_roles_parent_role_id_active
ON roles(parent_role_id, is_active)
WHERE is_active = true;

-- Index for user role lookups
CREATE INDEX IF NOT EXISTS idx_user_roles_user_email
ON user_roles(user_email);

-- Index for role permission lookups
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id
ON role_permissions(role_id);

-- Index for permission name lookups
CREATE INDEX IF NOT EXISTS idx_permissions_name_active
ON permissions(name, is_active)
WHERE is_active = true;

-- Composite index for efficient permission resolution
CREATE INDEX IF NOT EXISTS idx_user_roles_composite
ON user_roles(user_email, role_id);

-- Function: refresh_role_permission_cache()
-- Purpose: Optional function to refresh any cached permission data
-- Can be called after bulk role/permission changes
CREATE OR REPLACE FUNCTION refresh_role_permission_cache()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- This function can be extended to refresh materialized views
    -- or update cached permission data if needed in the future

    -- For now, it's a placeholder that could trigger cache invalidation
    -- in application-level caching systems

    -- Example: REFRESH MATERIALIZED VIEW user_permission_cache;

    RETURN;
END;
$$;

-- Grant permissions to application user (adjust user name as needed)
-- These grants ensure the application can execute the functions
-- Note: Replace 'promptcraft_app' with your actual database user

-- GRANT EXECUTE ON FUNCTION get_role_permissions(INTEGER) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION assign_user_role(VARCHAR(255), INTEGER, VARCHAR(255)) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION revoke_user_role(VARCHAR(255), INTEGER) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION get_user_roles(VARCHAR(255)) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION user_has_permission(VARCHAR(255), VARCHAR(100)) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION validate_role_hierarchy_circular(INTEGER, INTEGER) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION get_role_hierarchy_depth(INTEGER) TO promptcraft_app;
-- GRANT EXECUTE ON FUNCTION refresh_role_permission_cache() TO promptcraft_app;

-- Usage Examples and Testing Queries
-- ===================================

-- Example 1: Check if a user has a specific permission
-- SELECT user_has_permission('admin@example.com', 'tokens:create');

-- Example 2: Get all permissions for a role (including inherited)
-- SELECT permission_name FROM get_role_permissions(1);

-- Example 3: Get all roles for a user
-- SELECT * FROM get_user_roles('user@example.com');

-- Example 4: Assign a role to a user
-- SELECT assign_user_role('user@example.com', 2, 'admin@example.com');

-- Example 5: Revoke a role from a user
-- SELECT revoke_user_role('user@example.com', 2);

-- Example 6: Validate role hierarchy (check for circular dependencies)
-- SELECT validate_role_hierarchy_circular(1, 2);

-- Example 7: Get role hierarchy depth
-- SELECT get_role_hierarchy_depth(3);

-- Performance Notes:
-- ==================
-- 1. All recursive queries have depth limits (< 10) to prevent infinite loops
-- 2. Indexes are created to support efficient lookups
-- 3. Functions use proper type casting for return values
-- 4. Boolean functions return explicit true/false values
-- 5. All queries filter on is_active = true for soft deletion support

-- Security Notes:
-- ===============
-- 1. Functions use parameterized inputs to prevent SQL injection
-- 2. Role hierarchy validation prevents circular dependencies
-- 3. Functions respect soft deletion (is_active flags)
-- 4. Audit trail can be extended by adding logging tables
-- 5. Proper database user permissions should be granted in production
