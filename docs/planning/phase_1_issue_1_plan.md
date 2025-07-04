---
title: "Phase 1 Issue 1: Development Environment Setup"
version: "1.0"
status: "draft"
component: "Implementation-Plan"
tags: ["phase-1", "issue-1", "implementation", "environment-setup"]
purpose: "Implementation plan for resolving Phase 1 Issue 1 - Development Environment Setup"
---

# Phase 1 Issue 1: Development Environment Setup

## Scope Boundary Analysis

✅ **INCLUDED in Issue**:
- Python 3.11+ and Poetry installed and working
- Docker and Docker Compose operational (20.10+, 2.0+)
- GPG key generated and configured for .env encryption
- SSH key generated and configured for signed commits
- Pre-commit hooks installed and all checks passing
- Environment validation script passes
- Development containers start successfully

❌ **EXCLUDED from Issue**:
- Core configuration system implementation (Issue #2)
- Docker development environment configuration (Issue #3)
- Application code development
- Testing framework setup (Issue #7)
- UI development
- Template library creation
- Security implementation beyond basic key setup
- Production deployment preparation

🔍 **Scope Validation**: Each action item below directly maps to a specific acceptance criterion with no scope creep.

## Issue Requirements

**Objective**: Establish complete development environment with proper tooling, security validation, and dependency management following project requirements.

**Estimated Time**: 6 hours

**Dependencies**:
- Fresh clone of repository
- Admin/sudo access for installations
- Internet connection for downloads

## Action Plan Scope Validation

- [x] Every action item addresses a specific acceptance criterion
- [x] No "nice to have" items included
- [x] Plan stays within estimated time bounds (6 hours)
- [x] Implementation satisfies acceptance criteria completely

## Action Plan

### Phase 1: Environment Prerequisites (1.5 hours)

**1.1 Python 3.11+ Installation and Verification** (30 minutes)
- **Maps to**: "Python 3.11+ and Poetry installed and working"
- Check current Python version: `python3 --version`
- Install Python 3.11+ if needed (via pyenv or system package manager)
- Verify installation: `python3.11 --version`

**1.2 Poetry Installation and Configuration** (30 minutes)
- **Maps to**: "Python 3.11+ and Poetry installed and working"
- Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Configure Poetry: `poetry config virtualenvs.in-project true`
- Verify Poetry installation: `poetry --version`
- Install project dependencies: `poetry install --sync`

**1.3 Docker and Docker Compose Installation** (30 minutes)
- **Maps to**: "Docker and Docker Compose operational (20.10+, 2.0+)"
- Check current versions: `docker --version`, `docker-compose --version`
- Install/upgrade Docker to 20.10+ if needed
- Install/upgrade Docker Compose to 2.0+ if needed
- Verify Docker service is running: `docker info`
- Test Docker functionality: `docker run hello-world`

### Phase 2: Security Key Setup (2 hours)

**2.1 GPG Key Generation and Configuration** (1 hour)
- **Maps to**: "GPG key generated and configured for .env encryption"
- Check existing GPG keys: `gpg --list-secret-keys`
- Generate new GPG key if needed: `gpg --full-generate-key`
- Export GPG key for .env encryption usage
- Test GPG functionality: encrypt/decrypt test file
- Document GPG key ID for environment configuration

**2.2 SSH Key Generation and Git Configuration** (1 hour)
- **Maps to**: "SSH key generated and configured for signed commits"
- Check existing SSH keys: `ssh-add -l`
- Generate new SSH key if needed: `ssh-keygen -t ed25519 -C "email@example.com"`
- Add SSH key to ssh-agent: `ssh-add ~/.ssh/id_ed25519`
- Configure Git for signed commits: `git config --global user.signingkey [GPG-KEY-ID]`
- Configure Git to sign commits: `git config --global commit.gpgsign true`
- Test SSH key: `ssh -T git@github.com`

### Phase 3: Development Tools Setup (1.5 hours)

**3.1 Pre-commit Hooks Installation** (45 minutes)
- **Maps to**: "Pre-commit hooks installed and all checks passing"
- Install pre-commit: `poetry run pre-commit install`
- Run pre-commit on all files: `poetry run pre-commit run --all-files`
- Fix any issues identified by pre-commit hooks
- Verify all checks pass: `poetry run pre-commit run --all-files`

**3.2 Environment Validation Script Setup** (45 minutes)
- **Maps to**: "Environment validation script passes"
- Locate existing validation script: `src/utils/setup_validator.py`
- Create validation script if missing (following ledgerbase pattern)
- Run validation script: `poetry run python src/utils/setup_validator.py`
- Address any validation failures
- Ensure script passes completely

### Phase 4: Container Environment Verification (1 hour)

**4.1 Development Container Startup** (1 hour)
- **Maps to**: "Development containers start successfully"
- Run make setup: `make setup`
- Start development environment: `make dev`
- Verify containers are running: `docker ps`
- Test health endpoint: `curl http://localhost:7860/health`
- Verify all services are operational
- Document any container startup issues and resolutions

## Testing Strategy

### Acceptance Criteria Validation Tests

**Test 1: Python and Poetry Verification**
```bash
# Verify Python 3.11+
python3 --version | grep -E "3\.1[1-9]|3\.[2-9]"

# Verify Poetry functionality
poetry --version
poetry install --dry-run
```

**Test 2: Docker and Docker Compose Verification**
```bash
# Verify Docker version 20.10+
docker --version | grep -E "20\.(1[0-9]|[2-9][0-9])|[2-9][0-9]\."

# Verify Docker Compose version 2.0+
docker-compose --version | grep -E "v?2\."

# Test Docker functionality
docker run --rm hello-world
```

**Test 3: Security Keys Validation**
```bash
# Verify GPG key exists
gpg --list-secret-keys

# Verify SSH key is loaded
ssh-add -l

# Verify Git signing configuration
git config --get user.signingkey
git config --get commit.gpgsign
```

**Test 4: Pre-commit and Validation**
```bash
# Verify pre-commit hooks pass
poetry run pre-commit run --all-files

# Verify environment validation passes
poetry run python src/utils/setup_validator.py
```

**Test 5: Container Environment**
```bash
# Complete environment validation
make setup
poetry run python src/utils/setup_validator.py

# Container startup test
make dev
curl http://localhost:7860/health
```

## Dependencies and Prerequisites

### System Requirements
- Admin/sudo access for system package installation
- Internet connection for downloads
- Fresh clone of PromptCraft repository
- Git configured with user email and name

### External Dependencies
- Python 3.11+ available for installation
- Docker installation packages available
- GPG and SSH utilities available
- Access to system package manager (apt, yum, brew, etc.)

## Success Criteria

**Issue Complete When**:
- [ ] All acceptance criteria tests pass
- [ ] Environment validation script returns success
- [ ] Pre-commit hooks execute without errors
- [ ] Development containers start and respond to health checks
- [ ] All security keys are properly configured and functional
- [ ] Make commands (setup, dev) execute successfully

**Validation Commands**:
```bash
# Final validation sequence
make setup
poetry run python src/utils/setup_validator.py
make dev
curl http://localhost:7860/health
poetry run pre-commit run --all-files
```

**Definition of Done**:
All acceptance criteria from Phase 1 Issue 1 are satisfied, with no additional scope beyond the specified requirements. The development environment is ready for Issue #2 (Core Configuration System) implementation.