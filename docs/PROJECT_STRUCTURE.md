# Project Structure

This document describes the organized structure of the PromptCraft project after the production cleanup.

## Root Directory

The project root now contains only essential configuration and core project files:

### Configuration Files
- `pyproject.toml` - Python project configuration and dependencies
- `poetry.lock` - Python dependency lock file
- `package.json` / `package-lock.json` - Node.js tools and dependencies
- `Dockerfile` - Container build configuration
- `docker-compose*.yml` - Container orchestration
- `Makefile` - Build and development commands
- Various dotfiles (`.gitignore`, `.pre-commit-config.yaml`, etc.)

### Core Documentation
- `README.md` - Project overview and getting started
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policies
- `LICENSE` - Project license
- `CLAUDE.md` - Claude Code development guidance

## Directory Structure

### `/docs/`
Organized documentation with clear separation of concerns:

- `docs/agents/` - AI agent documentation (AGENTS.md, GEMINI.md, QWEN.md)
- `docs/reports/` - Generated reports and analysis
  - `docs/reports/auth/` - Authentication implementation reports
  - `docs/reports/database/` - Database migration and consolidation reports
  - `docs/reports/testing/` - Testing and performance reports
  - `docs/reports/ci/` - CI/CD analysis
  - `docs/reports/claude/` - Claude optimization reports
- `docs/guides/` - Implementation guides and setup documentation
- `docs/architecture/` - Architecture decisions and recommendations

### `/database/`
Database-related files:

- `database/schemas/` - PostgreSQL schema definitions

### `/scripts/`
All executable scripts:

- Shell scripts for common operations
- Python utility scripts
- Development automation tools

### `/src/`
Source code organized by domain

### `/tests/`
Test files organized by type and domain

## Cleanup Summary

### Files Removed
- Local database files (`*.db`) - 4MB+ freed
- Build artifacts (`coverage.json`, `junit.xml`, etc.)
- Analysis reports (`*_analysis.json`, `*_results.json`)
- Temporary directories (`backup/`, `agents-backup/`, etc.)
- Redundant requirements files (`requirements.txt`, `requirements-dev.txt`)

### Files Moved
- 35+ documentation files organized into logical directories
- 4 database schema files to `database/schemas/`
- 6 shell scripts and utilities to `scripts/`

### Files Updated
- `.gitignore` - Enhanced with patterns for generated files
- `pyproject.toml` - Fixed Black configuration regex
- Created symbolic link `requirements.txt` -> `requirements-docker.txt` for CI compatibility

## Production Readiness

The cleaned-up structure provides:

- **Clear separation of concerns** - Configuration, source, tests, docs all organized
- **Reduced clutter** - 60+ files moved from root to appropriate directories  
- **Better maintainability** - Related files grouped logically
- **CI/CD compatibility** - All workflows continue to function
- **Documentation clarity** - Reports and guides easy to find

This structure is now ready for production deployment with a clean, professional appearance and improved developer experience.