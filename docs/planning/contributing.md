# Contributing to PromptCraft-Hybrid

Thank you for considering contributing to PromptCraft-Hybrid! We welcome all types of contributions, from bug reports and documentation updates to new features.

This guide describes how to get started with development, our workflow, and how to submit high-quality contributions.

Please note: by participating in this project, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Table of Contents

1. [Getting Started](#getting-started)

   * [Prerequisites](#prerequisites)
   * [Local Setup](#local-setup)
2. [How to Contribute](#how-to-contribute)

   * [Reporting Bugs](#reporting-bugs)
   * [Suggesting Enhancements](#suggesting-enhancements)
3. [Development Workflow](#development-workflow)

   * [Branching Strategy](#branching-strategy)
   * [Coding Style](#coding-style)
   * [Testing](#testing)
   * [Commit Message Convention](#commit-message-convention)
4. [Submitting Your Contribution](#submitting-your-contribution)

   * [Pull Request Process](#pull-request-process)
5. [Style Guides & Standards](#style-guides--standards)
6. [Security Policy](#security-policy)

---

## Getting Started

Follow these steps to set up your local development environment.

### Prerequisites

* **Docker** and **Docker Compose**
* **Poetry** for Python dependency management
* **Nox** for automation and testing

### Local Setup

1. **Fork & Clone**

   ```bash
   git clone https://github.com/YOUR-USERNAME/PromptCraft-Hybrid.git
   cd PromptCraft-Hybrid
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys and configuration values.

3. **Install Dependencies**

   ```bash
   poetry install
   ```

4. **Launch Services**

   ```bash
   docker-compose up -d
   ```

   This starts services like Qdrant and Prefect required by the project.

5. **Run Initial Tests**

   ```bash
   nox -s tests
   ```

   Ensure all checks pass before proceeding.

---

## How to Contribute

### Reporting Bugs

1. Check existing issues: [https://github.com/williaby/PromptCraft-Hybrid/issues](https://github.com/williaby/PromptCraft-Hybrid/issues)
2. If not reported, open a new issue using the **Bug Report** template.
3. Include steps to reproduce, environment details, and expected vs. actual behavior.

### Suggesting Enhancements

1. Use the **Feature Request** template in Issues.
2. Describe the problem, proposed solution, and any relevant context.

---

## Development Workflow

### Branching Strategy

* **main**: Production-ready code. No direct commits.
* **develop**: Integration branch for features and fixes.
* **feature/**\*: New features (e.g., `feature/add-agent`).
* **bugfix/**\*: Non-critical bug fixes.
* **hotfix/**\*: Critical fixes off **main**.

### Coding Style

* Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

* Use **Black** and **Ruff**:

  ```bash
  black .
  ruff check . --fix
  ```

* These run automatically in `nox -s tests`.

### Testing

* **Unit tests** for individual components.
* **Integration tests** for end-to-end workflows.
* **RAG quality tests** for the retrieval pipeline.

Run tests:

```bash
nox -s tests
```

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

* **feat:** add new feature
* **fix:** bug fix
* **docs:** documentation only changes
* **test:** add or update tests

Example:

```text
feat: implement hyde generation strategy
fix: correct keyword matching logic
docs: update knowledge style guide directive
```

---

## Submitting Your Contribution

### Pull Request Process

1. Ensure all tests and linters pass (`nox -s tests`).
2. Push your branch to your fork.
3. Open a PR against **develop**.
4. Use the PR template and link related issues (e.g., `Closes #42`).
5. Review the automated summary, add any missing context.
6. Wait for CI checks and reviews; a core maintainer must approve before merge.

---

## Style Guides & Standards

* **Knowledge Base**: Follow the [Knowledge Base Style Guide](docs/knowledge_style_guide.md).
* **Markdown**: Lint with `markdownlint`.

---

## Security Policy

We take security seriously. If you discover a vulnerability:

1. **Do not** open a public issue.
2. Report privately via our [Security Policy](SECURITY.md).

---

Thank you for your contributions and helping make PromptCraft-Hybrid better!
