# Code Style and Conventions

## Python Standards (from pyproject.toml)
- **Line Length**: 88 characters (Black/Ruff)
- **Target Versions**: Python 3.11, 3.12
- **Formatter**: Black with strict configuration
- **Linter**: Ruff with comprehensive rule set (E, W, F, I, C, B, UP, N, YTT, ANN, S, BLE, A, COM, C4, DTZ, ISC, ICN, G, INP, PIE, T20, PT, Q, RET, SIM, TID, ARG, PTH, ERA, PGH, PL, RUF)
- **Type Checking**: MyPy with strict configuration (disallow_untyped_defs, disallow_incomplete_defs, strict_equality)

## Naming Conventions (MANDATORY)
- **Agent ID**: snake_case (e.g., `security_agent`, `create_agent`)
- **Agent Classes**: PascalCase + "Agent" suffix (e.g., `SecurityAgent`, `CreateAgent`)
- **Python Files**: snake_case.py (e.g., `src/agents/security_agent.py`)
- **Python Classes**: PascalCase (e.g., `class BaseAgent:`)
- **Python Functions**: snake_case() (e.g., `def get_relevant_knowledge():`)
- **Python Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES = 3`)
- **Test Files**: test_snake_case.py (e.g., `test_security_agent.py`)

## Git Conventions
- **Branch Naming**: kebab-case with prefixes (e.g., `feature/add-claude-md-generator`)
- **Commit Messages**: Conventional Commits format (e.g., `feat(security): add SQL injection detection`)
- **PR Requirements**: Must link to GitHub issue (e.g., "Closes #21")
- **PR Size**: Keep under 400 lines when possible

## File-Specific Standards
- **Markdown**: 120 character line length (`.markdownlint.json`)
- **YAML**: 2-space indentation, 120 character line length (`.yamllint.yml`)
- **JSON**: Built-in validation via pre-commit hooks
- **EditorConfig**: Consistent with pyproject.toml Python settings

## Security Standards
- **Bandit**: Security scanning with B101, B601 exclusions
- **Secrets**: Use local encrypted .env files (no secrets in code)
- **Dependencies**: AssuredOSS packages when available
- **Encryption**: Follow ledgerbase encryption.py pattern

## Quality Requirements
- **Test Coverage**: Minimum 80% for all Python code
- **Type Annotations**: Required for all function parameters and returns
- **Docstrings**: Required for public methods and classes
- **Error Handling**: Proper exception handling with specific exception types