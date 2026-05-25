# Configuration System Changelog

All notable changes to the PromptCraft Configuration System are documented here.

## [Unreleased]

### Changed

- **Build system migration: Poetry to uv** (ADR-0001). Build backend swapped
  from `poetry-core` to `hatchling`. `poetry.lock` plus three tracked
  `requirements*.txt` files (10,540 lines) replaced by a single `uv.lock`.
  Dev loop, CI workflows, devcontainer, and production Dockerfile all moved
  to `uv sync --frozen` / `uv export`. Rollback anchor: signed tag
  `legacy/pre-uv-migration` at `6533dbc` (retention 90 days).
- **Major version bumps across direct + dev dependencies** to clear ~92
  transitive CVEs the stale `requirements*.txt` exports had been hiding.
  Includes pytest 9, mypy 2, qdrant-client 1.10+, and 22 other majors.
  Breakage footprint: 5 small code fixes across 4 files (see ADR-0001 §
  Breakage triage).
- **Black removed entirely.** `ruff format` is now the sole formatter
  (project line length 120). `[tool.black]` config block, `black>=26.0.0`
  dev dependency, and Black calls in `Makefile` + `noxfile.py` all deleted.
- **`fips-compatibility.yml` and `setup-assured-oss.yml` workflows deleted.**
  Repo has no FIPS components; assured-oss reusable workflow was unused.

### Known migration regressions (follow-up required)

- **`[tool.pytest.benchmark]` config block dropped.** The block was a
  non-standard nested table that pytest-benchmark did not actually read
  (the correct location is `[pytest-benchmark]` in `pytest.ini`), so the
  previously-claimed regression thresholds (`compare_fail`, `min_rounds`,
  etc.) were never enforced. Restoring them via a proper pytest-benchmark
  config file is tracked separately.

### Fixed

- Align project with global Claude Code v1.4.0 standards: rewrite `CLAUDE.md`,
  introduce `.claude/rules/` for path-scoped overrides, remove retired Zen MCP
  project-level configuration
- Resolve 35+ pre-existing MyPy errors across infrastructure modules
- Correct hookimpl signature and remove UP036 dead code in hooks
- Restore `_request` parameter naming in API endpoints for slowapi rate-limiting
- Resolve yamllint indentation and markdownlint blank-line errors in config files
- Add `.claude/` to ruff exclude; fix pre-commit and yamllint configuration
- Resolve SonarCloud S7503/S7487 async violations in MCP discovery and bridge
- Make path handling assertions portable across CI environments
- Remove stale `core.json` assertion from infrastructure integration test
- Update assertions for UP036 runtime version check removal

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
