# PromptCraft-Hybrid Development TODO

## Post-PR #151 Code Quality Improvements

### 🔴 HIGH PRIORITY - Technical Debt Prevention

#### 1. Eliminate Code Duplication - Secret Fields
- **Issue**: Secret field names hardcoded in multiple locations
- **Files**: 
  - `src/config/health.py:106-115` (SECRET_FIELD_NAMES list)
  - `src/config/settings.py:273-314` (SecretStr field definitions)
- **Impact**: Maintenance burden, potential inconsistency if fields are added/removed
- **Solution**: Create centralized configuration
  ```python
  # src/config/constants.py (NEW FILE)
  SECRET_FIELD_NAMES = [
      "database_password",
      "database_url", 
      "api_key",
      "secret_key",
      "azure_openai_api_key",
      "jwt_secret_key",
      "qdrant_api_key",
      "encryption_key",
  ]
  
  SENSITIVE_ERROR_PATTERNS = [
      ("password", "Password configuration issue (details hidden)"),
      ("api key", "API key configuration issue (details hidden)"), 
      ("secret", "Secret key configuration issue (details hidden)"),
      ("jwt.*secret", "JWT secret configuration issue (details hidden)"),
  ]
  ```
- **Estimated Effort**: 2-3 hours
- **Dependencies**: None

### 🟡 MEDIUM PRIORITY - Performance & Maintainability

#### 2. Optimize Validation Error Sanitization
- **Issue**: Multiple regex substitutions executed sequentially
- **File**: `src/config/health.py:196-197`
- **Impact**: Performance degradation with large error lists
- **Solution**: Compile patterns once and use single-pass processing
  ```python
  def _sanitize_validation_errors(errors: list[str]) -> list[str]:
      """Optimized version with compiled patterns and single-pass processing."""
      if not errors:
          return []
      
      # Compile patterns once (module level)
      compiled_patterns = [
          (re.compile(pattern, re.IGNORECASE), replacement)
          for pattern, replacement in SENSITIVE_ERROR_PATTERNS
      ]
      
      # Single pass processing
      sanitized = []
      for error in errors:
          sanitized_error = error
          for pattern, replacement in compiled_patterns:
              if pattern.search(sanitized_error):
                  sanitized_error = replacement
                  break
          else:
              # Generic sanitization for unmatched patterns
              sanitized_error = re.sub(r'["\''][^"\']*["\'']', '"***"', sanitized_error)
          sanitized.append(sanitized_error)
      
      return sanitized
  ```
- **Estimated Effort**: 1-2 hours
- **Dependencies**: Item #1 (constants.py)

#### 3. Resolve Import Pattern Inconsistency
- **Issue**: Try/except import pattern complicates testing and maintenance
- **File**: `src/main.py:16-39`
- **Impact**: Makes code harder to test and debug
- **Solution**: Use consistent absolute imports throughout codebase
  ```python
  # src/main.py - Use consistent absolute imports
  from src.config.health import (
      ConfigurationStatusModel,
      get_configuration_health_summary, 
      get_configuration_status,
  )
  from src.config.settings import (
      ApplicationSettings,
      ConfigurationValidationError,
      get_settings,
  )
  ```
- **Estimated Effort**: 1 hour
- **Dependencies**: None

### 🟢 LOW PRIORITY - Modularity Improvements

#### 4. Extract CORS Configuration
- **Issue**: CORS origins dictionary hardcoded in create_app()
- **File**: `src/main.py:117-121`
- **Impact**: Difficult to customize for different deployment scenarios
- **Solution**: Extract to configuration module
  ```python
  # src/config/cors.py (NEW FILE)
  CORS_ORIGINS_BY_ENVIRONMENT = {
      "dev": ["http://localhost:3000", "http://localhost:5173", "http://localhost:7860"],
      "staging": ["https://staging.promptcraft.io"],
      "prod": ["https://promptcraft.io"],
  }
  
  # Usage in main.py
  def create_app() -> FastAPI:
      # ...
      app.add_middleware(
          CORSMiddleware,
          allow_origins=CORS_ORIGINS_BY_ENVIRONMENT.get(
              settings.environment, 
              CORS_ORIGINS_BY_ENVIRONMENT["dev"]
          ),
          # ...
      )
  ```
- **Estimated Effort**: 30 minutes
- **Dependencies**: None

#### 5. Create Path Utility Functions
- **Issue**: File path checking logic could be extracted to utility function
- **File**: `src/config/health.py:_determine_config_source()`
- **Impact**: Code reusability and testability
- **Solution**: Extract to utility module
  ```python
  # src/utils/file_paths.py (NEW FILE)
  def determine_config_source_from_files(environment: str, project_root: Path) -> str:
      """Extracted file path checking logic from health.py"""
      env_files = [
          project_root / f".env.{environment}",
          project_root / f".env.{environment}.gpg", 
          project_root / ".env",
          project_root / ".env.gpg",
      ]
      return "env_files" if any(f.exists() for f in env_files) else "defaults"
  ```
- **Estimated Effort**: 1 hour
- **Dependencies**: None

#### 6. Make Response Limits Configurable
- **Issue**: Magic numbers for response limits
- **File**: `src/main.py:211-212`
- **Impact**: Reduces flexibility for different environments
- **Solution**: Define configurable constants
  ```python
  # In constants.py
  HEALTH_CHECK_ERROR_LIMIT = 5
  HEALTH_CHECK_SUGGESTION_LIMIT = 3
  
  # Usage in main.py
  detail = {
      "error": "Configuration validation failed",
      "field_errors": e.field_errors[:HEALTH_CHECK_ERROR_LIMIT],
      "suggestions": e.suggestions[:HEALTH_CHECK_SUGGESTION_LIMIT],
  }
  ```
- **Estimated Effort**: 15 minutes
- **Dependencies**: Item #1 (constants.py)

## Implementation Order

### Phase 1: Foundation (Week 1)
1. Create `src/config/constants.py` with centralized field definitions
2. Update health.py and settings.py to use centralized constants

### Phase 2: Performance (Week 2)
3. Optimize regex processing in sanitization
4. Standardize import patterns

### Phase 3: Modularity (Week 3)
5. Extract configuration constants (CORS, response limits)
6. Create utility modules for reusable logic

## Architecture Strengths to Maintain

- **Security**: Excellent sanitization prevents data leakage
- **Type Safety**: Comprehensive Pydantic model usage
- **Testing**: 90%+ test coverage with security validation
- **Documentation**: Clear examples and comprehensive docstrings
- **Error Handling**: Graceful degradation patterns

## Readiness Assessment

✅ **READY TO PROCEED** to Phase 1 Issue 3 with the following strategy:
- Implement HIGH priority changes first to prevent technical debt accumulation
- Consider MEDIUM priority optimizations for performance-critical paths
- LOW priority items can be addressed incrementally

The current implementation provides a solid foundation with excellent security practices. The recommended changes will significantly improve maintainability and code quality for future development phases.

---

*Generated from comprehensive code review of PR #151 - Health Check Integration*
*Last Updated: 2025-07-07*