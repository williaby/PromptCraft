-- Database migration: 001_auth_schema.sql
-- Description: Create service tokens table for AUTH-2 service token management
-- Author: Claude Code Assistant
-- Date: 2025-08-01
-- Version: 1.0

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create service_tokens table
CREATE TABLE IF NOT EXISTS service_tokens (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Token identification
    token_name VARCHAR(255) NOT NULL UNIQUE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used TIMESTAMPTZ NULL,
    expires_at TIMESTAMPTZ NULL,

    -- Usage tracking
    usage_count INTEGER NOT NULL DEFAULT 0,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Flexible metadata storage
    token_metadata JSONB NULL,

    -- Constraints
    CONSTRAINT valid_expiration_date CHECK (expires_at IS NULL OR expires_at > created_at),
    CONSTRAINT non_negative_usage_count CHECK (usage_count >= 0)
);

-- Add table comment
COMMENT ON TABLE service_tokens IS 'Service tokens for API authentication and authorization';

-- Add column comments
COMMENT ON COLUMN service_tokens.id IS 'Unique identifier for the service token';
COMMENT ON COLUMN service_tokens.token_name IS 'Human-readable name for the token';
COMMENT ON COLUMN service_tokens.token_hash IS 'SHA-256 hash of the actual token value';
COMMENT ON COLUMN service_tokens.created_at IS 'Timestamp when token was created';
COMMENT ON COLUMN service_tokens.last_used IS 'Timestamp when token was last used';
COMMENT ON COLUMN service_tokens.expires_at IS 'Token expiration timestamp (null for non-expiring tokens)';
COMMENT ON COLUMN service_tokens.usage_count IS 'Number of times token has been used';
COMMENT ON COLUMN service_tokens.is_active IS 'Whether the token is currently active';
COMMENT ON COLUMN service_tokens.token_metadata IS 'Additional token metadata (permissions, client info, etc.)';

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_service_tokens_token_hash ON service_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_service_tokens_token_name ON service_tokens(token_name);
CREATE INDEX IF NOT EXISTS idx_service_tokens_active ON service_tokens(is_active);
CREATE INDEX IF NOT EXISTS idx_service_tokens_expires_at ON service_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_service_tokens_last_used ON service_tokens(last_used);

-- Composite index for active tokens lookup (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_service_tokens_active_hash ON service_tokens(is_active, token_hash);

-- Index on JSONB metadata for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_service_tokens_metadata_gin ON service_tokens USING GIN(metadata);

-- Create a partial index for only active tokens (performance optimization)
CREATE INDEX IF NOT EXISTS idx_service_tokens_active_only ON service_tokens(token_hash, expires_at)
WHERE is_active = true;

-- Create function to automatically update last_used timestamp
CREATE OR REPLACE FUNCTION update_service_token_last_used()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if usage_count is being incremented
    IF NEW.usage_count > OLD.usage_count THEN
        NEW.last_used = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update last_used when usage_count changes
CREATE TRIGGER trigger_update_service_token_last_used
    BEFORE UPDATE ON service_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_service_token_last_used();

-- Create function to check token expiration
CREATE OR REPLACE FUNCTION is_service_token_expired(token_expires_at TIMESTAMPTZ)
RETURNS BOOLEAN AS $$
BEGIN
    IF token_expires_at IS NULL THEN
        RETURN FALSE;
    END IF;
    RETURN NOW() > token_expires_at;
END;
$$ LANGUAGE plpgsql;

-- Create function to check token validity (active and not expired)
CREATE OR REPLACE FUNCTION is_service_token_valid(token_is_active BOOLEAN, token_expires_at TIMESTAMPTZ)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN token_is_active AND NOT is_service_token_expired(token_expires_at);
END;
$$ LANGUAGE plpgsql;

-- Create view for valid tokens only (frequently used in queries)
CREATE OR REPLACE VIEW valid_service_tokens AS
SELECT
    id,
    token_name,
    token_hash,
    created_at,
    last_used,
    expires_at,
    usage_count,
    is_active,
    metadata,
    is_service_token_expired(expires_at) as is_expired,
    is_service_token_valid(is_active, expires_at) as is_valid
FROM service_tokens
WHERE is_service_token_valid(is_active, expires_at);

-- Add view comment
COMMENT ON VIEW valid_service_tokens IS 'View of all valid (active and non-expired) service tokens';

-- Create stored procedure for token validation with usage tracking
CREATE OR REPLACE FUNCTION validate_service_token(
    p_token_hash VARCHAR(255),
    p_increment_usage BOOLEAN DEFAULT TRUE
)
RETURNS TABLE(
    token_id UUID,
    token_name VARCHAR(255),
    expires_at TIMESTAMPTZ,
    usage_count INTEGER,
    metadata JSONB,
    is_valid BOOLEAN
) AS $$
DECLARE
    token_record RECORD;
BEGIN
    -- Find and validate token
    SELECT
        st.id,
        st.token_name,
        st.expires_at,
        st.usage_count,
        st.metadata,
        is_service_token_valid(st.is_active, st.expires_at) as valid
    INTO token_record
    FROM service_tokens st
    WHERE st.token_hash = p_token_hash;

    -- Return empty result if token not found
    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Increment usage count if requested and token is valid
    IF p_increment_usage AND token_record.valid THEN
        UPDATE service_tokens
        SET usage_count = usage_count + 1
        WHERE token_hash = p_token_hash;

        -- Update the usage count in our return record
        token_record.usage_count := token_record.usage_count + 1;
    END IF;

    -- Return token information
    token_id := token_record.id;
    token_name := token_record.token_name;
    expires_at := token_record.expires_at;
    usage_count := token_record.usage_count;
    metadata := token_record.metadata;
    is_valid := token_record.valid;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Add stored procedure comment
COMMENT ON FUNCTION validate_service_token(VARCHAR, BOOLEAN) IS 'Validate service token and optionally increment usage count';

-- Create cleanup procedure for expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens(
    p_delete_expired BOOLEAN DEFAULT FALSE,
    p_deactivate_expired BOOLEAN DEFAULT TRUE
)
RETURNS TABLE(
    cleaned_count INTEGER,
    action_taken VARCHAR(50)
) AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    -- Count expired tokens
    SELECT COUNT(*) INTO expired_count
    FROM service_tokens
    WHERE is_service_token_expired(expires_at) AND is_active = true;

    IF p_delete_expired THEN
        -- Delete expired tokens
        DELETE FROM service_tokens
        WHERE is_service_token_expired(expires_at);

        cleaned_count := expired_count;
        action_taken := 'deleted';
    ELSIF p_deactivate_expired THEN
        -- Deactivate expired tokens
        UPDATE service_tokens
        SET is_active = false
        WHERE is_service_token_expired(expires_at) AND is_active = true;

        cleaned_count := expired_count;
        action_taken := 'deactivated';
    ELSE
        cleaned_count := expired_count;
        action_taken := 'counted_only';
    END IF;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Add cleanup procedure comment
COMMENT ON FUNCTION cleanup_expired_tokens(BOOLEAN, BOOLEAN) IS 'Clean up expired service tokens by deletion or deactivation';

-- Grant appropriate permissions (adjust as needed for your environment)
-- Note: These are example permissions - adjust based on your security requirements

-- Create roles if they don't exist (optional - may already exist in your environment)
-- DO $$ BEGIN
--     CREATE ROLE promptcraft_api;
--     CREATE ROLE promptcraft_admin;
-- EXCEPTION
--     WHEN duplicate_object THEN null;
-- END $$;

-- Grant permissions to API role (read/write access)
-- GRANT SELECT, INSERT, UPDATE ON service_tokens TO promptcraft_api;
-- GRANT USAGE ON SEQUENCE service_tokens_id_seq TO promptcraft_api;
-- GRANT SELECT ON valid_service_tokens TO promptcraft_api;
-- GRANT EXECUTE ON FUNCTION validate_service_token(VARCHAR, BOOLEAN) TO promptcraft_api;

-- Grant permissions to admin role (full access)
-- GRANT ALL ON service_tokens TO promptcraft_admin;
-- GRANT ALL ON valid_service_tokens TO promptcraft_admin;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO promptcraft_admin;

-- Insert sample data for testing (remove in production)
-- INSERT INTO service_tokens (token_name, token_hash, metadata) VALUES
-- ('test-token-1', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '{"environment": "test", "permissions": ["read"]}'),
-- ('test-token-2', 'ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d', '{"environment": "test", "permissions": ["read", "write"]}');

-- Migration completion log
-- Note: In a real migration system, you would track this in a migrations table
-- INSERT INTO schema_migrations (version, description, applied_at) VALUES
-- ('001', 'Create service tokens table for AUTH-2', NOW());

-- Migration completed successfully
-- The service_tokens table is now ready for use with:
-- - Proper indexing for performance
-- - Constraints for data integrity
-- - Stored procedures for common operations
-- - Triggers for automatic timestamp updates
-- - View for efficient valid token queries
