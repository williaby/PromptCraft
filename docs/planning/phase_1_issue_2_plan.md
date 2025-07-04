---
title: "Phase 1 Issue 2: Core Configuration System"
version: "1.0"
status: "approved"
component: "Implementation-Plan"
tags: ["phase-1", "issue-2", "implementation", "configuration"]
purpose: "Implementation plan for resolving Phase 1 Issue 2"
---

# Phase 1 Issue 2: Core Configuration System

## Scope Boundary Analysis
✅ **INCLUDED in Issue**:
- Configuration classes defined with Pydantic schema
- Environment-specific configs working (dev, staging, prod)
- .env file encryption/decryption integrated with settings loading
- All configuration parameters validated with appropriate error messages
- Default configurations allow immediate development start
- Health check endpoints return configuration status
- Sensitive values never logged or exposed in error messages

❌ **EXCLUDED from Issue**:
- Actual deployment configurations (just the system to manage them)
- Zen MCP Server specific configurations
- Docker compose configurations
- CI/CD pipeline configurations
- Production infrastructure settings
- Monitoring/alerting configurations
- Rate limiting configurations
- CORS and security headers configuration

🔍 **Scope Validation**: Each action item below directly maps to acceptance criteria. No scope creep detected after IT manager review.

## Issue Requirements
Create a centralized configuration system that:
1. Uses Pydantic for schema validation and type safety
2. Supports environment-specific configurations (dev, staging, prod)
3. Integrates with existing encryption.py for secure .env file handling
4. Provides clear validation errors for misconfiguration
5. Enables immediate development with sensible defaults
6. Exposes configuration status via health endpoints
7. Prevents sensitive data exposure in logs or responses

## Action Plan Scope Validation
- [x] Every action item addresses a specific acceptance criterion
- [x] No "nice to have" items included
- [x] Plan stays within estimated time bounds (revised to 8 hours)
- [x] Implementation satisfies acceptance criteria completely

## Action Plan

### Phase 1: Core Configuration Schema (2 hours)
**Maps to criteria**: "Configuration classes defined with Pydantic schema"

1. Create `src/config/settings.py` with Pydantic BaseSettings class
2. Define core application settings:
   ```python
   - app_name: str
   - version: str
   - environment: Literal["dev", "staging", "prod"]
   - debug: bool
   - api_host: str = "0.0.0.0"
   - api_port: int = 8000
   ```
3. Configure Pydantic with:
   - `extra='forbid'` to prevent unknown settings
   - Clear field descriptions for error messages
   - Proper type annotations with validation
4. Create custom validators for complex fields

### Phase 2: Environment-Specific Loading (1.5 hours)
**Maps to criteria**: "Environment-specific configs working" & "Default configurations allow immediate development"

1. Implement environment detection logic
2. Set up file loading hierarchy:
   - Environment variables (highest priority)
   - `.env.{environment}` file
   - `.env` file
   - Pydantic field defaults (lowest priority)
3. Create settings factory function:
   ```python
   def get_settings() -> Settings:
       """Get settings instance based on current environment."""
   ```
4. Ensure all fields have sensible defaults for development

### Phase 3: Encryption Integration (2 hours)
**Maps to criteria**: ".env file encryption/decryption integrated"

1. Integrate existing `encryption.py` module:
   - Import `load_encrypted_env` function
   - Handle `.env.gpg` files when present
2. Implement secure loading pattern:
   ```python
   - Try loading .env.gpg (production)
   - Fall back to .env (development)
   - Apply environment variable overrides
   ```
3. Use Pydantic `SecretStr` for sensitive values:
   - Database passwords
   - API keys
   - Other credentials
4. Add proper error handling for decryption failures

### Phase 4: Validation & Error Handling (1.5 hours)
**Maps to criteria**: "All configuration parameters validated with appropriate error messages"

1. Implement comprehensive validation:
   - Port ranges (1-65535)
   - Valid environment values
   - Required fields based on environment
2. Create custom validation error messages:
   - Field-specific guidance
   - Example valid values
   - Environment-specific requirements
3. Add configuration validation on startup
4. Log configuration loading process (without sensitive data)

### Phase 5: Health Check Integration (1 hour)
**Maps to criteria**: "Health check endpoints return configuration status" & "Sensitive values never logged"

1. Create configuration status model:
   ```python
   - environment: str
   - version: str
   - debug: bool
   - config_loaded: bool
   - encryption_enabled: bool
   ```
2. Implement `/health` endpoint response
3. Add configuration validation status
4. Ensure SecretStr values are never exposed
5. Test health endpoint security

### Phase 6: Testing & Documentation (1 hour)
**Maps to criteria**: All acceptance criteria validation

1. Unit tests:
   - Valid configuration loading
   - Invalid configuration rejection
   - Environment-specific loading
   - Encryption integration
   - Health check security
2. Integration tests:
   - Full configuration lifecycle
   - Error scenarios
3. Documentation:
   - Configuration usage examples
   - Environment setup guide
   - Security best practices

## Testing Strategy

### Unit Tests
- Test each configuration field validation
- Test environment-specific loading precedence
- Test encryption/decryption integration
- Test error message clarity
- Test SecretStr handling

### Integration Tests
- Test full application startup with various configs
- Test health endpoint responses
- Test configuration errors halt startup appropriately

### Security Tests
- Verify sensitive values never appear in logs
- Verify health endpoint doesn't expose secrets
- Test encrypted file handling

## Dependencies and Prerequisites
- Issue #1 completed (Development Environment Setup)
- GPG keys configured for encryption
- SSH keys configured for signed commits
- `.env.example` file as template
- Access to existing `encryption.py` module

## Dependency Impact Analysis
**What this provides to dependent issues:**
- Issue #3: Base configuration pattern for Docker settings
- Issue #4: Configuration access for C.R.E.A.T.E. engine
- Issue #9: Secure configuration pattern for security settings
- Issue #36: Reusable configuration pattern for shared components

**What this requires from prerequisites:**
- Issue #1: Working development environment with keys

## Success Criteria
1. Configuration loads successfully from multiple sources
2. Environment-specific settings work correctly
3. Encrypted .env files decrypt and load properly
4. Validation errors are clear and actionable
5. Health endpoint shows config status without secrets
6. All tests pass with 90%+ coverage
7. Development can start with zero configuration

## Rollback Procedures
1. **Configuration Loading Failure**:
   - Fall back to hardcoded defaults
   - Log detailed error for debugging
   - Allow application to start in "safe mode"

2. **Encryption Integration Issues**:
   - Disable encryption temporarily
   - Use plain .env files with warning
   - Document manual encryption steps

3. **Validation Too Strict**:
   - Temporarily relax validation rules
   - Log warnings instead of failing
   - Create migration plan for invalid configs

## Time Estimate Revision
Based on IT manager feedback, revised from 5 to **8 hours**:
- Added time for robust error handling
- Added time for comprehensive testing
- Added time for security validation
- Maintained focus on acceptance criteria only

## Notes
- Following existing `encryption.py` pattern from ledgerbase
- Using Pydantic best practices for configuration
- Prioritizing security with SecretStr usage
- Ensuring clear separation from other issues' configurations
