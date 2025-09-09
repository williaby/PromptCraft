# Gemini Code Assistant Context

This document provides a comprehensive overview of the PromptCraft-Hybrid project, its architecture, development conventions, and key commands. Use this as a guide for understanding the project and for providing assistance with development tasks.

## Project Overview

PromptCraft-Hybrid is an advanced, hybrid AI platform designed to transform user queries into highly accurate, context-aware, and structured outputs. It integrates on-premise hardware with specialized cloud services to deliver a powerful, cost-effective, and extensible AI development workbench.

The project is built on several key concepts and a unique hybrid architecture:

*   **Four Progressive Journeys**: A unique user model that guides users from simple prompt enhancement to full, multi-agent workflow automation.
*   **Dual-Orchestration Model**: It uses the best tool for the job. **Zen MCP Server** handles real-time, user-facing agent orchestration, while **Prefect** manages background, scheduled data workflows like knowledge ingestion and quality assurance.
*   **HyDE Query Enhancement**: A sophisticated pipeline that analyzes user queries for intent and ambiguity, generating hypothetical documents to improve retrieval accuracy.
*   **Agent-First Design**: The system's expertise comes from specialized, independent AI agents with their own dedicated knowledge bases, allowing for scalable, domain-specific intelligence.
*   **Hybrid Infrastructure**: A cost-effective model that leverages an external Qdrant instance for vector search and an Ubuntu VM for application services with minimal cloud dependencies.

### Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Real-Time Orchestration** | Zen MCP Server | Coordinates AI agents and tools for user queries. |
| **Background Orchestration** | Prefect | Manages scheduled data & maintenance workflows. |
| **Query Intelligence** | HyDE Engine | Enhances ambiguous user queries. |
| **RAG Framework** | LlamaIndex | Manages data ingestion and retrieval pipelines. |
| **Vector Database** | Qdrant (External) | High-speed semantic search. |
| **UI Framework** | Gradio | Journeys 1-4 web interface. |
| **Backend Framework** | FastAPI | The main application framework. |
| **Dependency Management** | Poetry | Manages Python dependencies. |
| **Task Automation** | Nox | Runs tests, linters, and other tasks. |

## Building and Running

The project uses a combination of `make`, `poetry`, and `nox` for building, running, and testing.

### Setup

To set up the development environment, run:

```bash
make setup
```

This command will install all dependencies using Poetry, set up pre-commit hooks, and generate necessary files.

### Running the Application

To start the development environment with all services, run:

```bash
make dev
```

This will start the FastAPI application, Gradio UI, and other services using Docker Compose.

*   **Gradio UI:** `http://192.168.1.205:7860`
*   **Zen MCP Server:** `http://192.168.1.205:3000`
*   **External Qdrant Dashboard:** `http://192.168.1.16:6333/dashboard`

### Testing

The project has a comprehensive test suite that can be run using `nox` or `make`.

*   **Run all tests:**
    ```bash
    nox -s tests
    ```
    or
    ```bash
    make test
    ```
*   **Run fast tests (for development):**
    ```bash
    make test-fast
    ```
*   **Run tests by layer (unit, component, integration, etc.):**
    ```bash
    nox -s unit
    nox -s component
    nox -s integration
    ```

## Development Conventions

The project follows a strict set of development conventions to ensure code quality and consistency.

### Coding Style

*   **Python 3.11+**
*   **Formatting:** Black with a line length of 120 columns.
*   **Linting:** Ruff.
*   **Type Checking:** Mypy with strict settings.

### Commit Messages

The project uses the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Branching

The project follows the GitFlow branching model.

*   **Main branch:** `main`
*   **Feature branches:** `feature/<issue-number>-<short-name>`
*   **Bug fixes:** `bugfix/<issue-number>`
*   **Hotfixes:** `hotfix/<issue-number>`

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality before committing. The hooks include:

*   `black`
*   `ruff`
*   `mypy`
*   `bandit`
*   `markdownlint`
*   `yamllint`

### Documentation

The project uses MkDocs for documentation. The main documentation hub is located at `docs/planning/project-hub.md`.

## Key Files and Directories

*   `src/`: The main source code for the application.
*   `tests/`: The test suite.
*   `docs/`: The project documentation.
*   `pyproject.toml`: The main configuration file for the project, including dependencies, tool configurations, and project metadata.
*   `noxfile.py`: The main file for defining Nox sessions for testing, linting, and other tasks.
*   `Makefile`: The main file for defining `make` commands for common development tasks.
*   `AGENTS.md`: A quick reference guide for developers.
*   `CONTRIBUTING.md`: A detailed guide for contributors.
