# Task Completion Checklist

## Pre-Commit Requirements (MANDATORY)
Before committing ANY changes, ensure:

### Environment Validation
- [ ] GPG key present for .env encryption: `gpg --list-secret-keys`
- [ ] SSH key present for signed commits: `ssh-add -l`
- [ ] Git signing key configured: `git config --get user.signingkey`
- [ ] Environment validation passes: `poetry run python src/utils/encryption.py`

### Code Quality Checks
- [ ] **Python Files**: All linting passes
  ```bash
  poetry run black --check .
  poetry run ruff check .
  poetry run mypy src
  ```
- [ ] **Markdown Files**: `markdownlint **/*.md`
- [ ] **YAML Files**: `yamllint .`
- [ ] **Pre-commit hooks**: `poetry run pre-commit run --all-files`

### Testing and Coverage
- [ ] All tests pass: `make test` or `poetry run pytest -v`
- [ ] Test coverage ≥ 80%: Coverage reports in terminal and `htmlcov/`
- [ ] Integration tests pass: `poetry run pytest tests/integration/ -v`

### Security Validation
- [ ] Security scans pass: `make security`
- [ ] Safety check: `poetry run safety check`
- [ ] Bandit scan: `poetry run bandit -r src`
- [ ] No secrets in code or commits
- [ ] Encrypted .env files only (no plaintext secrets)

### Documentation Standards
- [ ] Knowledge files follow C.R.E.A.T.E. Framework
- [ ] YAML frontmatter correct and agent_id matches folder
- [ ] Heading hierarchy: H1 (title), H2 (sections), H3 (atomic chunks), NO H4+
- [ ] Internal links functional
- [ ] All `.md` files pass markdownlint validation

### Development Philosophy Compliance
- [ ] **Reuse First**: Checked ledgerbase, FISProject, .github for existing solutions
- [ ] **Configure Don't Build**: Used Zen MCP Server, Heimdall MCP Server, AssuredOSS packages
- [ ] **Focus on Unique Value**: Only built what's unique to PromptCraft
- [ ] Naming conventions followed (snake_case agents, PascalCase classes, etc.)

### Final Steps
- [ ] Commits are signed (GPG signature)
- [ ] PR links to GitHub issue
- [ ] Branch follows naming convention: `feature/<issue>-<name>`
- [ ] Commit messages follow Conventional Commits format
- [ ] All file-specific linters have been run for modified file types

## Quick Commands for Task Completion
```bash
# Full validation pipeline
make setup && make test && make lint && make security

# Or using nox for comprehensive checks
nox -s tests -s lint -s type_check -s security

# Manual environment validation
poetry run python src/utils/encryption.py
```
