---
title: Contributing to PromptCraft-Hybrid
version: 1.0
status: published
component: Documentation
tags: ["contributing", "development", "guidelines", "pull-request", "code-standards"]
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

### Security Guidelines

#### Secrets Management

- **Never commit secrets**: Use local encrypted .env files with GPG/SSH keys
- **Follow ledgerbase pattern**: Reference existing security implementations
- **Azure Key Vault**: For production secrets management
- **Environment Variables**: Use UPPER_SNAKE_CASE naming

#### Code Security

- **Input Validation**: Always validate user inputs
- **SQL Injection Prevention**: Use parameterized queries
- **XSS Protection**: Sanitize outputs appropriately
- **Authentication**: Follow OAuth2 and JWT best practices

## Recognition

Contributors are recognized in several ways:

- **Contributors Section**: Added to project README
- **Release Notes**: Mentioned in changelog for significant contributions
- **Community Recognition**: Highlighted in Discord and discussions

Thank you for your contribution to PromptCraft-Hybrid!