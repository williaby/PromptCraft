# PromptCraft-Hybrid Project Context for Qwen Code

## Project Overview

PromptCraft-Hybrid is an advanced, hybrid AI platform designed to transform user queries into highly accurate, context-aware, and structured outputs. It integrates on-premise hardware with specialized cloud services to deliver a powerful, cost-effective, and extensible AI development workbench.

### Core Features

* **Four Progressive Journeys**: A unique user model that guides users from simple prompt enhancement to full, multi-agent workflow automation.
* **Dual-Orchestration Model**: Uses Zen MCP Server for real-time, user-facing agent orchestration, and Prefect for background, scheduled data workflows like knowledge ingestion and quality assurance.
* **HyDE Query Enhancement**: A sophisticated pipeline that analyzes user queries for intent and ambiguity, generating hypothetical documents to improve retrieval accuracy.
* **Agent-First Design**: The system's expertise comes from specialized, independent AI agents with their own dedicated knowledge bases, allowing for scalable, domain-specific intelligence.
* **Hybrid Infrastructure**: A cost-effective model that leverages external Qdrant on Unraid (192.168.1.16) for vector search and Ubuntu VM deployment (192.168.1.205) for application services with minimal cloud dependencies.
* **Cost Control with Free Mode**: New toggle to use only free models (1000 requests/day) in Journey 4, perfect for development, testing, and cost-conscious usage.
* **Transparent Pricing**: See exactly which model is being used and its cost in real-time.
* **Smart Routing**: Automatically selects the best available free model when in Free Mode.

### Technology Stack Overview

| Component                    | Technology          | Purpose                                             |
| ---------------------------- | ------------------- | --------------------------------------------------- |
| **Real-Time Orchestration**  | Zen MCP Server      | Coordinates AI agents and tools for user queries.   |
| **Background Orchestration** | Prefect             | Manages scheduled data & maintenance workflows.     |
| **Query Intelligence**       | HyDE Engine         | Enhances ambiguous user queries.                    |
| **RAG Framework**            | LlamaIndex          | Manages data ingestion and retrieval pipelines.     |
| **Vector Database**          | Qdrant (External)   | High-speed semantic search on Unraid (192.168.1.16) |
| **UI Framework**             | Gradio + Code-Server| Journeys 1-4 web interface + IDE integration       |
| **Application Host**         | Ubuntu VM           | Hosts MCP stack on VM (192.168.1.205)               |
| **Unified Access**           | Cloudflared Tunnel  | Single domain access for all journeys              |

## Codebase Structure

The project follows a Python-based architecture with a modular structure:

* `src/`: Application code by domain (`agents/`, `api/`, `auth/`, `core/`, `database/`, `ui/`, `utils/`, `config/`) — entrypoint: `src/main.py`.
* `tests/`: Layered suites (`unit/`, `integration/`, `contract/`, `performance/`, `security/`) — layout: `tests/`.
* `docs/`: MkDocs site content; keep user-facing docs in sync with code.
* `scripts/`: Utility scripts run via `poetry` or `make`.
* `examples/` and `config/`: Sample flows and environment settings.
* Key files: `src/agents/registry.py`, `src/agents/base_agent.py`, `Makefile`, `pyproject.toml`, `noxfile.py`, `mkdocs.yml`.

## Development Environment

### Prerequisites

* Docker & Docker Compose
* Poetry for Python dependency management
* Nox for task automation
* External Qdrant instance running on Unraid at 192.168.1.16:6333
* Ubuntu VM at 192.168.1.205 for application deployment

### Installation and Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/williaby/PromptCraft.git
   cd PromptCraft-Hybrid
   ```

2. **Configure Environment**:
   * Copy the `.env.example` file to `.env`.
   * Populate the `.env` file with your Azure, Cloudflare, and other necessary API keys.
   * Configure external Qdrant connection (192.168.1.16:6333) and Ubuntu VM deployment target (192.168.1.205).

3. **Install Dependencies**:
   * Use Poetry to install all required Python packages from the `pyproject.toml` file.
   ```bash
   poetry install
   ```

4. **Deploy to Ubuntu VM**:
   * Deploy application services to Ubuntu VM (excludes Qdrant which runs externally on Unraid).
   ```bash
   # On Ubuntu VM (192.168.1.205)
   make dev
   # This starts all services except Qdrant (external dependency)
   ```

5. **Configure Cloudflared Tunnel** (Optional for remote access):
   * Set up cloudflared tunnel for unified web access to all journeys.
   * All services bind to localhost (127.0.0.1) for tunnel routing.

6. **Run Tests**:
   * Use Nox to run the test suite and ensure your environment is set up correctly.
   ```bash
   nox -s tests
   ```

## Building and Running

### Development Commands

* `make setup`: Install deps, install pre-commit, prime local tooling. See targets in `Makefile`.
* `make test`: Run full pytest with coverage (HTML in `htmlcov/`).
* `make test-fast`: Quick unit/auth subset for local loops.
* `make lint` / `make format`: Check/auto-fix with Black, Ruff; run mypy, markdownlint, yamllint.
* `make dev`: Start Dockerized dev stack (FastAPI, Gradio, MCP, Qdrant).
* Run API locally: `poetry run uvicorn src.main:app --reload`.

### Nox Test Sessions

* `nox -s tests`: Run the full test suite (all layers).
* `nox -s unit`: Run unit tests only (fast development cycle).
* `nox -s integration`: Run integration tests (slower, real services).
* `nox -s e2e`: Run end-to-end tests (full user journeys).
* `nox -s perf`: Run performance and load tests.
* `nox -s lint`: Run linters.
* `nox -s type_check`: Run type checking with mypy.
* `nox -s security`: Run security checks.

## Agent Architecture

### Base Agent Framework

All agents in PromptCraft must inherit from `BaseAgent` (defined in `src/agents/base_agent.py`) and implement the `execute()` method. The system uses dependency injection for configuration and supports runtime configuration overrides through `AgentInput`.

### Agent Registry

The `AgentRegistry` (in `src/agents/registry.py`) provides a centralized system for discovering and managing agent classes. It uses a decorator-based registration pattern that enables automatic agent discovery and type-safe agent instantiation.

To register a new agent:
```python
from src.agents.registry import agent_registry
from src.agents.base_agent import BaseAgent

@agent_registry.register("my_agent")
class MyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)

    async def execute(self, agent_input):
        # Implementation here
        pass
```

### Agent Execution Process

1. An agent is registered with the `AgentRegistry`.
2. When needed, the registry creates an instance of the agent.
3. The agent's `process()` method is called with an `AgentInput` object.
4. The `process()` method handles configuration merging, error handling, and performance tracking.
5. The agent's `execute()` method is called to perform the core functionality.
6. The result is returned as an `AgentOutput` object.

## Development Conventions

### Coding Style

* Python 3.11; format with Black (120 cols); lint with Ruff; type-check `mypy` (strict where applicable). Tooling in `pyproject.toml`.
* Imports follow isort (Black profile). Prefer `pathlib` and f-strings.
* Names: modules `snake_case`, classes `PascalCase`, constants `UPPER_CASE`.

### Testing Guidelines

* Framework: `pytest` (+ `pytest-cov`). Default markers exclude slow; notable markers: `unit`, `integration`, `contract`, `perf`, `security`, `smoke` (configured in `pyproject.toml`).
* Naming: files `test_*.py`, functions `test_*`. Put narrow tests near their domain (e.g., `tests/unit/api/`).
* Coverage: target ≥ 80% on full runs. Commands: `make test`, quick: `make test-fast`.

### Commit & Pull Request Guidelines

* Conventional Commits: `feat(scope): summary`, `fix(scope): summary`. Example: `feat(testing): add coverage analyzer`.
* Before PR: run `make test-pr` and `make lint`; update docs, add tests; include linked issues and screenshots for UI changes.
* Keep PRs focused and describe rationale, risk, and rollout notes.

### Security & Configuration

* Copy `.env.template` → `.env`; never commit secrets. Use environment-specific files (`.env.dev`, `.env.staging`, `.env.prod`). See `SECURITY.md` for guidance.
* Validate security: `make security` (Safety, Bandit). Pre-commit hooks (see `.pre-commit-config.yaml`) enforce lint/format.
