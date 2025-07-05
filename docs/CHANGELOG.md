# Configuration System Changelog

All notable changes to the PromptCraft Configuration System are documented here.

## [Unreleased]

### Added
- Phase 1-5 Core Configuration System implementation
- Environment-specific configuration loading (dev/staging/prod)
- Encrypted secrets management with GPG
- Health check endpoints for operational monitoring
- Comprehensive validation with helpful error messages
- Type-safe settings with Pydantic v2
- Security-first design with SecretStr protection

### Documentation
- Configuration System Guide
- Security Best Practices
- Usage Guide with examples
- Migration Guide from old configuration
- API Reference documentation
- Example scripts for all features

## Phase 5: Health Check Integration

### Added
- `ConfigurationStatusModel` for safe status reporting
- Health check endpoints: `/health`, `/health/config`, `/ping`
- Configuration health summary function
- Secret counting without value exposure
- Validation error sanitization
- Encryption availability detection

### Security
- No sensitive data exposed in health responses
- Automatic sanitization of error messages
- File path removal from error outputs

## Phase 4: Advanced Configuration

### Added
- Hierarchical configuration loading
- CORS configuration management
- Connection pooling settings
- Service integration settings (Qdrant, Azure)
- Custom validation decorators

### Changed
- Improved validation error messages
- Better production environment detection

## Phase 3: Secret Management

### Added
- GPG encryption support for .env files
- SecretStr fields for all sensitive values
- Automatic decryption of .env.{environment}.gpg files
- Key validation utilities

### Security
- All passwords use SecretStr
- Encrypted configuration files support
- No plaintext secrets in logs

## Phase 2: Environment Loading

### Added
- Environment-specific .env file loading
- Settings singleton pattern
- Configuration reload capability
- Environment detection logic

### Changed
- Moved from os.environ to pydantic-settings
- Added PROMPTCRAFT_ prefix for all settings

## Phase 1: Base Configuration

### Added
- Initial Pydantic settings schema
- Basic application configuration
- Type validation for all settings
- Default values for development

### Infrastructure
- Poetry dependency management
- Project structure setup
- Initial test framework

## Migration Notes

### From Manual Configuration
- Add PROMPTCRAFT_ prefix to all environment variables
- Replace os.getenv() with get_settings()
- Use SecretStr for sensitive values
- Add validation error handling

### Breaking Changes
- All environment variables must use PROMPTCRAFT_ prefix
- Secret values now use SecretStr type
- Validation is mandatory in production
- Debug mode forbidden in production environment
