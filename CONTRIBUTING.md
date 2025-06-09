# Contributing to PromptCraft

First off, thank you for considering contributing to PromptCraft! Your help is appreciated. Following
these guidelines helps to communicate that you respect the time of the developers managing and developing
this open source project. In return, they should reciprocate that respect in addressing your issue, assessing
changes, and helping you finalize your pull requests.

## Code of Conduct

This project and everyone participating in it is governed by the Contributor Covenant Code of
Conduct. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following tools installed on your system:

- Git: For version control.
- Node.js: We recommend using the latest LTS (Long-Term Support) version (e.g., 18.x or newer).
- Azure CLI: To interact with Azure resources from your command line.
- Pre-commit: To run automated checks before each commit.

### Repository Setup

#### Fork and Clone the Repository

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone <https://github.com/YOUR_USERNAME/PromptCraft.git>
cd PromptCraft
```

#### Install Dependencies

The Azure Function (GetAnchor) is written in Node.js. Navigate to its directory and install the
required npm packages:

```bash
cd src/functions
npm install
cd ../..
```

(Note: The exact path src/functions may be adjusted as the project structure is finalized.)

#### Set Up Pre-commit Hooks

Install the hooks defined in .pre-commit-config.yaml. This will ensure your code is linted and formatted
correctly before you commit.

```bash
pre-commit install
```

### Submitting Changes

#### Create a New Branch

Create a new branch for your feature or bug fix:

```bash
git checkout -b your-branch-name
```

#### Make Your Changes

1. Make your changes to the code and/or documentation.
2. Ensure your changes are covered by tests if applicable.

#### Commit Your Changes

Stage your changes and commit them. The pre-commit hooks will run automatically. If they fail, address
the issues and re-commit.

```bash
git add .
git commit -m "feat: A brief description of your feature"
```

#### Push to Your Fork

Push your branch to your forked repository:

```bash
git push origin your-branch-name
```

#### Open a Pull Request

Go to the williaby/PromptCraft repository on GitHub and open a pull request from your branch to the main
branch.
Provide a clear title and description for your pull request, linking to any relevant issues.

Thank you for your contribution!
