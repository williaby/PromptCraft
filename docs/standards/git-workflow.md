# Git Workflow Standards

> **Comprehensive Git workflow standards for PromptCraft development**

## Branch Strategy

### Branch Structure

- **Main Branch**: `main` (production-ready code)
- **Development Branch**: `knowledgebase_edits` (current active development)
- **Feature Branches**: `feature/<issue-number>-<short-name>`
- **Hotfix Branches**: `hotfix/<issue-number>-<short-name>`

### Branch Naming Conventions (MANDATORY)

```bash
# Feature branches
feature/123-add-claude-md-generator
feature/456-implement-security-audit
feature/789-optimize-vector-search

# Hotfix branches
hotfix/321-fix-authentication-bug
hotfix/654-resolve-memory-leak

# Release branches (if needed)
release/v1.2.0
release/v2.0.0-beta
```

## Commit Standards

### Conventional Commits (MANDATORY)

All commits MUST follow Conventional Commits specification:

```bash
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: New feature for the user
- **fix**: Bug fix for the user
- **docs**: Documentation changes
- **style**: Formatting changes (no code logic changes)
- **refactor**: Code refactoring (no functionality changes)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI/CD configuration
- **chore**: Maintenance tasks

### Examples

```bash
# Good commit messages
feat(auth): add JWT token validation middleware
fix(ui): resolve responsive layout issue on mobile
docs(api): update authentication endpoint documentation
test(core): add unit tests for query processing
refactor(db): optimize database connection pooling
perf(search): implement caching for vector queries

# Commit with body and footer
feat(mcp): add intelligent tool filtering system

Implement dynamic tool filtering based on query context to reduce
MCP tool loading by 60-80%. Includes category mappings and
environment variable configuration.

Closes #123
Co-authored-by: Agent <agent@promptcraft.ai>
```

## Signing Requirements (MANDATORY)

### GPG Commit Signing

All commits MUST be signed with GPG keys:

```bash
# Configure Git signing
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true

# Verify signing is working
git commit -S -m "test: verify commit signing"
git log --show-signature -1
```

### SSH Commit Signing (Alternative)

```bash
# Configure SSH signing
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true

# Verify SSH signing
ssh-add -l  # Confirm SSH key is loaded
git commit -S -m "test: verify SSH commit signing"
```

### Validation Requirements

```bash
# Required validation before commits
gpg --list-secret-keys                # Must show GPG keys
ssh-add -l                           # Must show SSH keys (if using SSH signing)
git config --get user.signingkey     # Must show signing key configuration
git config --get commit.gpgsign      # Must show "true"
```

## Pull Request Standards

### PR Title Format

Follow Conventional Commits format:

```bash
feat(auth): implement OAuth2 integration with Azure AD
fix(ui): resolve mobile responsive layout issues
docs(api): add comprehensive API documentation
```

### PR Description Template

```markdown
## Summary
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## Testing
- [ ] Tests pass locally with my changes
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Coverage remains at or above 80%

## Security
- [ ] Security scans pass (Safety, Bandit, GitGuardian)
- [ ] No secrets or sensitive data in commits
- [ ] Input validation implemented where applicable
- [ ] Authentication/authorization changes reviewed

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules

## Issue Reference
Closes #123
Related to #456

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Additional Notes
[Any additional information that reviewers should know]
```

### PR Size Guidelines

- **Small**: < 100 lines changed (preferred)
- **Medium**: 100-400 lines changed (acceptable)
- **Large**: 400-1000 lines changed (requires justification)
- **Extra Large**: > 1000 lines (strongly discouraged)

## Code Review Process

### Review Requirements

- **Minimum Reviewers**: 1 for small PRs, 2 for large PRs
- **Required Checks**: All CI/CD checks must pass
- **Security Review**: Required for security-related changes
- **Documentation**: Required for API or architecture changes

### Review Checklist

#### Code Quality

- [ ] Code follows project standards and conventions
- [ ] Logic is clear and well-documented
- [ ] No code duplication or unnecessary complexity
- [ ] Error handling is appropriate and comprehensive
- [ ] Performance implications considered

#### Security

- [ ] Input validation implemented
- [ ] No hardcoded secrets or sensitive data
- [ ] Authentication/authorization properly implemented
- [ ] SQL injection and XSS vulnerabilities addressed
- [ ] Dependency security issues resolved

#### Testing

- [ ] Adequate test coverage (minimum 80%)
- [ ] Tests are meaningful and test actual functionality
- [ ] Edge cases and error conditions tested
- [ ] Integration tests included where appropriate
- [ ] Performance tests for performance-critical changes

#### Documentation

- [ ] Code comments explain complex logic
- [ ] API documentation updated if applicable
- [ ] Knowledge base updated for new features
- [ ] README and setup instructions current

## Workflow Patterns

### Feature Development Workflow

```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/123-implement-new-feature

# 2. Make changes and commit (signed)
git add .
git commit -S -m "feat(scope): implement new feature functionality"

# 3. Push and create PR
git push -u origin feature/123-implement-new-feature
gh pr create --title "feat(scope): implement new feature" --body-file pr-template.md

# 4. Address review feedback
git add .
git commit -S -m "fix(scope): address review feedback"
git push

# 5. Merge after approval
gh pr merge --squash  # or merge/rebase as appropriate
```

### Hotfix Workflow

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/456-critical-security-fix

# 2. Implement fix
git add .
git commit -S -m "fix(security): resolve critical authentication vulnerability"

# 3. Create urgent PR
gh pr create --title "fix(security): resolve critical authentication vulnerability" --label "priority:urgent"

# 4. Fast-track review and merge
gh pr merge --squash
```

### Release Workflow

```bash
# 1. Create release branch
git checkout main
git checkout -b release/v1.2.0

# 2. Update version numbers and changelog
# Edit version files and CHANGELOG.md
git add .
git commit -S -m "chore(release): prepare v1.2.0 release"

# 3. Create release PR
gh pr create --title "chore(release): v1.2.0" --base main

# 4. After merge, create git tag
git checkout main
git pull origin main
git tag -s v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# 5. Create GitHub release
gh release create v1.2.0 --title "v1.2.0" --notes-file CHANGELOG.md
```

## Git Hooks and Automation

### Pre-commit Hooks (MANDATORY)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.246
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Commit Message Validation

```bash
# .gitmessage template
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>

# Example:
# feat(auth): add OAuth2 integration
#
# Implement OAuth2 authentication flow with Azure AD.
# Includes token validation and refresh mechanisms.
#
# Closes #123
# Co-authored-by: Team Member <member@example.com>
```

## Repository Management

### Branch Protection Rules

**Main Branch Protection**:

- Require pull request reviews before merging
- Dismiss stale PR approvals when new commits are pushed
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require conversation resolution before merging
- Require signed commits
- Include administrators in restrictions

### Required Status Checks

- **CI/CD Pipeline**: All tests must pass
- **Security Scans**: GitGuardian, Semgrep, Bandit clear
- **Code Quality**: Linting and formatting pass
- **Coverage**: Minimum 80% code coverage maintained
- **Documentation**: Documentation builds successfully

### Merge Strategies

- **Squash and Merge**: Preferred for feature branches (clean history)
- **Merge Commit**: For release merges (preserve branch history)
- **Rebase and Merge**: For small changes (linear history)

## Troubleshooting Common Issues

### Commit Signing Issues

```bash
# GPG agent issues
export GPG_TTY=$(tty)
gpg-connect-agent updatestartuptty /bye

# SSH signing issues
ssh-add ~/.ssh/id_ed25519
export GIT_SSH_COMMAND="ssh -o IdentitiesOnly=yes"

# Verify signing configuration
git config --list | grep -E "(signingkey|gpgsign)"
```

### Merge Conflicts

```bash
# Resolve merge conflicts
git pull origin main  # Update main branch
git checkout feature/branch
git rebase main       # Rebase feature branch

# If conflicts occur
git status            # View conflicted files
# Edit files to resolve conflicts
git add resolved-file.py
git rebase --continue

# Alternative: merge strategy
git merge main
# Resolve conflicts and commit
git commit -S -m "fix: resolve merge conflicts"
```

### Large File Issues

```bash
# Remove large files from history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch large-file.bin' \
  --prune-empty --tag-name-filter cat -- --all

# Use Git LFS for large files
git lfs track "*.bin"
git lfs track "*.model"
git add .gitattributes
git commit -S -m "chore: add Git LFS tracking for binary files"
```

### Performance Optimization

```bash
# Optimize repository performance
git gc --aggressive --prune=now
git remote prune origin

# Clean up merged branches
git branch --merged main | grep -v main | xargs -n 1 git branch -d

# Shallow clone for large repositories
git clone --depth 1 https://github.com/repo/project.git
```
