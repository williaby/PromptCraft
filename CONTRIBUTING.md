---
title: Contributing to PromptCraft-Hybrid
version: 1.0
status: published
agent_id: create_agent
tags: ['contributing', 'development', 'guidelines', 'pull_request', 'code_standards']
source: "PromptCraft-Hybrid Project"
purpose: To provide comprehensive guidelines for contributing to the PromptCraft-Hybrid project.
---

# Contributing to PromptCraft-Hybrid

First off, thank you for considering contributing to PromptCraft-Hybrid! Your help is appreciated. Following these
guidelines helps to communicate that you respect the time of the developers managing and developing this open source
project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping
you finalize your pull requests.

## Code of Conduct

This project and everyone participating in it is governed by the Contributor Covenant Code of Conduct. By
participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following tools installed on your system:

- **Git**: For version control
- **Python 3.11+**: Core development language
- **Poetry**: Python dependency management (not Node.js/npm)
- **Docker & Docker Compose**: For containerized services
- **Nox**: Task automation and testing across Python versions
- **Pre-commit**: Automated code quality checks before commits

### Repository Setup

#### Fork and Clone the Repository

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/PromptCraft.git
cd PromptCraft-Hybrid
```

#### Install Dependencies

This project uses Python with Poetry for dependency management:

```bash
# Install dependencies with Poetry
poetry install --sync

# Install pre-commit hooks
poetry run pre-commit install

# Verify installation
nox -s tests
```

#### Set Up Development Environment

Follow the comprehensive setup process:

```bash
# Complete development setup (includes all dependencies and hooks)
make setup

# Verify environment is ready
make test
make lint
```

### Development Standards

#### Code Quality Requirements

All contributions must meet these quality standards:

- **Code Formatting**: Black (line length 88) and Ruff linting
- **Type Checking**: MyPy with strict configuration
- **Test Coverage**: Minimum 80% coverage required
- **Security**: Bandit security scanning must pass
- **Documentation**: All public APIs must have docstrings

#### Naming Conventions

Follow the project naming conventions defined in `docs/planning/development.md`:

- **Python Files**: snake_case.py
- **Python Classes**: PascalCase
- **Python Functions**: snake_case()
- **Constants**: UPPER_SNAKE_CASE
- **Agent IDs**: snake_case (must match directory names)
- **Knowledge Files**: kebab-case.md

#### Branch Strategy

Follow the Git workflow defined in development guidelines:

- **Main Branch**: `main` - Production-ready releases only
- **Feature Branches**: `feature/<issue-number>-<short-name>`
- **Bug Fixes**: `bugfix/<issue-number>`
- **Hot Fixes**: `hotfix/<issue-number>`

### Submitting Changes

#### Create a New Branch

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/123-add-new-agent
```

#### Make Your Changes

1. Make your changes to the code and/or documentation
2. Ensure your changes follow the project naming conventions
3. Add or update tests for your changes
4. Update documentation as needed
5. Run quality checks locally:

```bash
make lint      # Run all linting checks
make test      # Run test suite with coverage
make security  # Run security scans
```

#### Commit Your Changes

Use Conventional Commits format for commit messages:

```bash
git add .
git commit -m "feat(agents): add security agent for authentication patterns

- Implement SecurityAgent class with OAuth2 capabilities
- Add knowledge base for security best practices
- Include comprehensive test coverage
- Update agent registry and documentation

Closes #123"
```

**Commit Message Format**:
- `feat(scope): description` - New features
- `fix(scope): description` - Bug fixes
- `docs(scope): description` - Documentation changes
- `test(scope): description` - Test additions/changes
- `refactor(scope): description` - Code refactoring

#### Push to Your Fork

Push your branch to your forked repository:

```bash
git push origin feature/123-add-new-agent
```

#### Open a Pull Request

1. Go to the `williaby/PromptCraft` repository on GitHub
2. Open a pull request from your branch to the `main` branch
3. Use the pull request template if available
4. Provide a clear title and description linking to relevant issues
5. Ensure all automated checks pass before requesting review

### Pull Request Requirements

#### Automated Checks

All pull requests must pass these automated checks:

- [ ] **Black & Ruff**: Python formatting and linting
- [ ] **MyPy**: Type checking with strict configuration
- [ ] **Pytest**: Test suite with >80% coverage
- [ ] **Bandit**: Security vulnerability scanning
- [ ] **Pre-commit**: All hooks pass successfully

#### Review Checklist

Reviewers will verify:

- [ ] **Standards Compliance**: Follows all naming conventions and code standards
- [ ] **Architecture Alignment**: Integrates properly with existing systems
- [ ] **Documentation**: Includes appropriate documentation updates
- [ ] **Testing**: Adequate test coverage and quality
- [ ] **Security**: No security vulnerabilities introduced

### Development Workflow Integration

#### Claude Code Slash Commands

This project includes custom slash commands for development workflows:

```bash
# Validate your documentation changes
/project:lint-doc docs/planning/your-new-doc.md

# Create new agent structure
/project:create-agent-skeleton your_new_agent "Agent description"

# Validate agent implementation
/project:validate-agent-structure knowledge/your_new_agent/
```

#### Knowledge Base Contributions

When contributing to the knowledge base:

1. **Follow C.R.E.A.T.E. Framework**: Context, Request, Examples, Augmentations, Tone & Format, Evaluation
2. **Atomic H3 Sections**: Each H3 must be self-contained and retrievable independently
3. **Agent ID Consistency**: Ensure agent_id matches across folder, files, and metadata
4. **Use Slash Commands**: Leverage `/project:validate-knowledge-chunk` for quality assurance

#### Agent Development

When creating new agents:

1. **Use Agent Skeleton**: Start with `/project:create-agent-skeleton`
2. **Follow Naming Conventions**: snake_case for agent_id, PascalCase + "Agent" for class names
3. **Implement BaseAgent Interface**: Inherit from src/agents/base_agent.py
4. **Create Knowledge Base**: Include comprehensive knowledge files
5. **Update Registry**: Add agent to src/agents/registry.py
6. **Configure Qdrant**: Set up vector database collections

### Getting Help

#### Resources

- **Development Guidelines**: `docs/planning/development.md`
- **Architecture Overview**: `docs/planning/ADR.md`
- **Knowledge Style Guide**: `docs/planning/knowledge_style_guide.md`
- **Slash Commands**: `docs/planning/slash-command-spec.md`

#### Communication

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Discord**: [Community Server](https://discord.gg/promptcraft) for real-time collaboration

### Dependency Management

PromptCraft follows a secure dependency management strategy (ADR-009) that all contributors must understand and follow.

#### Adding New Dependencies

When adding any new package dependency, follow this exact process:

##### 1. Check AssuredOSS Availability

Always check if the package is available in Google's AssuredOSS repository first:

```bash
# Search for the package in AssuredOSS
poetry search package-name --source assured-oss

# Check for alternatives if not found
poetry search alternative-package --source assured-oss
```

##### 2. Add the Dependency

Use Poetry to add dependencies with appropriate version constraints:

```bash
# Production dependency
poetry add "package-name>=1.0.0,<2.0.0"

# Development dependency
poetry add --group dev "dev-package>=1.0.0"

# Optional dependency
poetry add --optional "optional-package>=1.0.0"
```

##### 3. Update Requirements Files

**CRITICAL**: Always regenerate requirements files after any dependency change:

```bash
# Regenerate with hash verification (default/secure mode)
./scripts/generate_requirements.sh

# For development/testing only (without hashes)
./scripts/generate_requirements.sh --without-hashes
```

##### 4. Commit All Changes

Always commit poetry files AND requirements files together:

```bash
git add pyproject.toml poetry.lock requirements*.txt
git commit -m "feat(deps): add package-name for specific functionality

- Add package-name for [specific use case]
- Updated requirements files with hash verification
- Verified AssuredOSS compatibility

Closes #issue-number"
```

#### Security Classification

Understanding package security classification is critical:

**Security-Critical Packages** (immediate individual PRs from Renovate):
- Authentication/crypto: `cryptography`, `pyjwt`, `passlib`, `bcrypt`, `pyotp`
- Core frameworks: `fastapi`, `uvicorn`, `gradio`, `pydantic`, `httpx`
- Azure services: `azure-identity`, `azure-keyvault-secrets`
- AI/ML core: `anthropic`, `openai`, `qdrant-client`

**Routine Packages** (monthly batched PRs from Renovate):
- Development tools: `pytest`, `black`, `ruff`, `mypy`
- Utilities: `python-dateutil`, `tenacity`, `rich`, `structlog`
- Data processing: `pandas`, `numpy` (unless CVE)

#### Version Constraints Guidelines

**Production Dependencies** (pyproject.toml):
```toml
# Use caret ranges for automatic security updates
fastapi = "^0.110.0"        # Allows 0.110.x and 0.x.y
cryptography = "^42.0.2"    # Critical security package

# Use explicit ranges for tighter control
requests = ">=2.31.0,<3.0.0"  # Block major version bumps
```

**Development Dependencies**:
```toml
# More flexible for dev tools
pytest = "^8.0.0"          # Can update more freely
black = "^24.0.0"          # Formatting tools
ruff = "^0.2.0"            # Linting tools
```

#### Troubleshooting Common Issues

**Hash Verification Failures**:
```bash
# Regenerate requirements files
./scripts/generate_requirements.sh

# Check which source provided the package
poetry show --source package-name
```

**Dependency Conflicts**:
```bash
# Check dependency tree
poetry show --tree

# Update conflicting constraints
poetry add "conflicting-package>=compatible-version"
```

**CI Pipeline Failures**:
```bash
# Verify requirements synchronization
poetry export --format=requirements.txt --output=test-check.txt
diff requirements.txt test-check.txt
rm test-check.txt
```

#### Pull Request Checklist for Dependencies

When submitting a PR that adds or updates dependencies:

- [ ] **AssuredOSS checked**: Verified package availability in secure repository
- [ ] **Version constraints**: Used appropriate ranges (not exact pins)
- [ ] **Requirements updated**: Ran `./scripts/generate_requirements.sh`
- [ ] **All files committed**: pyproject.toml, poetry.lock, requirements*.txt
- [ ] **Security classification**: Documented if package is security-critical
- [ ] **Testing**: Verified application works with new dependencies
- [ ] **Justification**: Clear explanation of why dependency is needed

#### Security Guidelines

##### Secrets Management

- **Never commit secrets**: Use local encrypted .env files with GPG/SSH keys
- **Follow ledgerbase pattern**: Reference existing security implementations
- **Azure Key Vault**: For production secrets management
- **Environment Variables**: Use UPPER_SNAKE_CASE naming

##### Code Security

- **Input Validation**: Always validate user inputs
- **SQL Injection Prevention**: Use parameterized queries
- **XSS Protection**: Sanitize outputs appropriately
- **Authentication**: Follow OAuth2 and JWT best practices
- **Dependencies**: Prefer AssuredOSS packages for security-critical components

## Recognition

Contributors are recognized in several ways:

- **Contributors Section**: Added to project README
- **Release Notes**: Mentioned in changelog for significant contributions
- **Community Recognition**: Highlighted in Discord and discussions

Thank you for your contribution to PromptCraft-Hybrid!
