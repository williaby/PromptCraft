# PromptCraft-Hybrid: Development Guidelines

Version: 2.0
Status: Published
Audience: All Developers & Technical Contributors

## 1. Introduction

This document establishes the official development workflow, naming conventions, and quality standards for the PromptCraft-Hybrid project. Adherence to these guidelines is mandatory for all contributors.

The purpose of these guidelines is to:

- Ensure code consistency and readability across the entire project
- Streamline the development and code review process
- Minimize bugs and maintain a high standard of quality
- Clarify the process for contributing code from feature conception to deployment
- Maximize code reuse from existing repositories (ledgerbase, FISProject, .github)

This document is the authoritative source for "how we build." It complements the architectural deep dives ("what we build") and the CONTRIBUTING.md file (initial setup).

## 2. Development Philosophy

### 2.1. Reuse First

Before building any new component, check these repositories for existing solutions:

- **CI/CD & DevOps**: Copy from [ledgerbase](https://github.com/williaby/ledgerbase)
- **Documentation Templates**: Reuse from [FISProject](https://github.com/williaby/FISProject)
- **GitHub Actions**: Use workflows from [.github](https://github.com/williaby/.github)
- **UI Components**: Leverage existing `promptcraft_app.py` from PromptCraft

### 2.2. Configure, Don't Build

- **Orchestration**: Use [Zen MCP Server](https://github.com/BeehiveInnovations/zen-mcp-server) instead of custom orchestration
- **Analysis**: Integrate [Heimdall MCP Server](https://github.com/lcbcFoo/heimdall-mcp-server) rather than building analysis tools
- **Security**: Use AssuredOSS packages when available

### 2.3. Focus on Unique Value

Our unique contributions are:
- Claude.md generation logic
- Prompt composition intelligence
- User preference learning
- C.R.E.A.T.E. framework implementation

## 3. Naming Conventions

A consistent naming scheme is critical for our modular system. The following conventions MUST be followed:

### 3.1. Core Components

| Component              | Convention                   | Example                                                |
| ---------------------- | ---------------------------- | ------------------------------------------------------ |
| **Agent ID**           | snake_case                   | `security_agent`, `create_agent`, `irs_8867`           |
| **Agent Classes**      | PascalCase + "Agent" suffix  | `SecurityAgent`, `CreateAgent`, `IRS8867Agent`         |
| **MCP Server Names**   | kebab-case                   | `zen-mcp-server`, `heimdall-mcp`                       |
| **Knowledge Folders**  | snake_case matching agent_id | `/knowledge/security_agent/`, `/knowledge/irs_8867/`   |
| **Knowledge Files**    | kebab-case.md                | `auth-best-practices.md`, `due-diligence-checklist.md` |
| **Qdrant Collections** | snake_case matching agent_id | `security_agent`, `create_agent`, `irs_8867`           |

### 3.2. Code & Files

| Component                    | Convention           | Example                         |
| ---------------------------- | -------------------- | ------------------------------- |
| **Python Files**             | snake_case.py        | `src/agents/security_agent.py`  |
| **Python Classes**           | PascalCase           | `class BaseAgent:`              |
| **Python Functions/Methods** | snake_case()         | `def get_relevant_knowledge():` |
| **Python Constants**         | UPPER_SNAKE_CASE     | `MAX_RETRIES = 3`               |
| **Python Private Methods**   | _snake_case()        | `def _validate_input():`        |
| **Test Files**               | test_snake_case.py   | `test_security_agent.py`        |
| **Configuration Files**      | snake_case.yaml/json | `agents_config.yaml`            |

### 3.3. Infrastructure & Deployment

| Component                 | Convention             | Example                                   |
| ------------------------- | ---------------------- | ----------------------------------------- |
| **Docker Services**       | kebab-case             | `gradio-ui`, `code-interpreter-mcp`       |
| **Docker Images**         | kebab-case with org    | `promptcraft/security-agent:latest`       |
| **Docker Volumes**        | snake_case             | `qdrant_data`, `redis_cache`              |
| **Docker Networks**       | kebab-case             | `promptcraft-backend`                     |
| **Environment Variables** | UPPER_SNAKE_CASE       | `QDRANT_HOST`, `AZURE_KEY_VAULT_URL`      |
| **Azure Resources**       | kebab-case with prefix | `kv-promptcraft-prod`, `apim-promptcraft` |
| **Kubernetes Resources**  | kebab-case             | `security-agent-deployment`               |

### 3.4. Git & Development

| Component        | Convention               | Example                                       |
| ---------------- | ------------------------ | --------------------------------------------- |
| **Git Branches** | kebab-case with prefixes | `feature/add-claude-md-generator`             |
| **Git Tags**     | v + semver               | `v1.2.3`, `v2.0.0-beta.1`                     |
| **PR Titles**    | Conventional Commits     | `feat(security): add SQL injection detection` |
| **Issue Labels** | kebab-case               | `bug`, `enhancement`, `good-first-issue`      |

### 3.5. API & Web

| Component          | Convention               | Example                               |
| ------------------ | ------------------------ | ------------------------------------- |
| **REST Endpoints** | kebab-case, plural nouns | `/api/v1/agents`, `/api/v1/claude-md` |
| **GraphQL Types**  | PascalCase               | `Agent`, `QueryResult`                |
| **GraphQL Fields** | camelCase                | `agentId`, `createdAt`                |
| **URL Parameters** | snake_case               | `?agent_id=security_agent`            |
| **JSON Fields**    | snake_case               | `{"agent_id": "security_agent"}`      |
| **Headers**        | Pascal-Case              | `X-Request-Id`, `Content-Type`        |

### 3.6. CI/CD & Testing

| Component           | Convention     | Example                                   |
| ------------------- | -------------- | ----------------------------------------- |
| **GitHub Actions**  | kebab-case.yml | `security-scan.yml`, `deploy-staging.yml` |
| **Nox Sessions**    | snake_case     | `tests`, `lint`, `type_check`             |
| **Pytest Fixtures** | snake_case     | `mock_zen_client`, `test_database`        |
| **Test Markers**    | snake_case     | `@pytest.mark.integration`                |

### 3.8. Knowledge Base Components

| Component                  | Convention                       | Example                              |
| -------------------------- | -------------------------------- | ------------------------------------ |
| **YAML Front Matter Keys** | snake_case                       | `agent_id`, `status`, `version`      |
| **Status Values**          | lowercase                        | `draft`, `in-review`, `published`    |
| **Tags**                   | lowercase, spaces as underscores | `['compliance', 'tax', 'form_8867']` |
| **Directive Types**        | UPPER-CASE with hyphen           | `AGENT-DIRECTIVE`, `TOOL_CALL`       |

### 3.9. Special Naming Rules

1. **Agent ID Consistency**: The `agent_id` must be identical across:
   - Knowledge folder name: `/knowledge/{agent_id}/`
   - Qdrant collection name: `{agent_id}`
   - YAML front matter: `agent_id: {agent_id}`
   - Agent registry entry: `id: {agent_id}`

2. **File Path Hierarchy**: Knowledge files must follow strict path conventions:
   ```
   /knowledge/{agent_id}/{kebab-case-filename}.md
   ```

3. **Version Numbering**: Use semantic versioning for documents:
   - Major changes: `2.0`
   - Minor updates: `1.1`
   - Patches: `1.0.1`

## 4. Git Workflow & Branching Strategy

We follow a simplified Gitflow model optimized for our 7-week timeline:

### 4.1. Branch Definitions

- **main**: Production-ready releases only
- **develop**: Integration branch for features
- **feature/<issue-number>-<short-name>**: New features (e.g., `feature/21-claude-md-generator`)
- **bugfix/<issue-number>**: Bug fixes (e.g., `bugfix/45`)
- **hotfix/<issue-number>**: Critical production fixes

### 4.2. Commit Standards

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(claude-md): implement template selection logic
fix(security): patch Azure Key Vault connection issue
docs(api): update Claude.md generation endpoint docs
test(generator): add preference learning unit tests
refactor(ui): simplify Gradio interface components
```

## 5. Development Standards

### 5.1. Python Code Standards

```python
# Always use Zen MCP for orchestration
from zen_mcp import ZenClient

class ClaudeMdGenerator:
    """Generate Claude.md files with project context.

    This is our unique value - focus development here.
    """

    def __init__(self, zen_client: ZenClient):
        self.zen = zen_client
        self._setup_security()  # Always initialize security first

    def _setup_security(self):
        """Configure Azure Key Vault for secrets."""
        from azure.identity import ManagedIdentityCredential
        from azure.keyvault.secrets import SecretClient

        # Reuse pattern from ledgerbase
        credential = ManagedIdentityCredential()
        self.secrets = SecretClient(
            vault_url=os.getenv("AZURE_KEY_VAULT_URL"),
            credential=credential
        )
```

### 5.2. Security Requirements

- **Secrets**: All secrets MUST use Azure Key Vault
- **Dependencies**: Use AssuredOSS packages when available
- **Scanning**: All PRs must pass GitGuardian and Semgrep checks
- **Authentication**: Copy auth patterns from ledgerbase

### 5.3. Testing Requirements

```python
# Minimum test coverage: 80%
# Focus on unique components

def test_claude_md_generation():
    """Test our core value proposition."""
    generator = ClaudeMdGenerator(mock_zen_client)

    result = generator.generate(
        query="Build a REST API",
        context={"framework": "FastAPI"}
    )

    assert "# Claude.md" in result
    assert "FastAPI" in result
    assert validate_claude_md_format(result)
```

## 6. Code Review Process

### 6.1. Pull Request Requirements

1. **Title**: Must follow Conventional Commits format
2. **Description**: Link to GitHub issue (e.g., `Closes #21`)
3. **Size**: Keep PRs under 400 lines when possible
4. **Tests**: All new code must have tests
5. **Documentation**: Update relevant .md files

### 6.2. Automated Checks

All PRs must pass these automated checks:

- [ ] **Black & Ruff**: Python formatting and linting
- [ ] **pytest**: Unit tests with >80% coverage
- [ ] **GitGuardian**: No secrets detected
- [ ] **Semgrep**: No security vulnerabilities
- [ ] **Codecov**: Coverage report generated

### 6.3. Review Checklist

Reviewers must verify:

- [ ] **Reuse Check**: Could this use existing code from ledgerbase/FISProject?
- [ ] **Zen/Heimdall Usage**: Is orchestration done through MCP servers?
- [ ] **Security**: Are secrets in Key Vault? AssuredOSS used?
- [ ] **Focus**: Does this contribute to our unique value (Claude.md generation)?
- [ ] **Timeline**: Is this scoped appropriately for our 7-week sprint?

## 7. Integration Patterns

### 7.1. Zen MCP Integration

```python
# Standard pattern for all tool calls
async def analyze_codebase(self, path: str):
    """Use Heimdall through Zen orchestration."""
    result = await self.zen.call_tool(
        server="heimdall",
        tool="analyze_codebase",
        params={"path": path, "recursive": True}
    )
    return result
```

### 7.2. Gradio UI Pattern

```python
# Reuse patterns from existing promptcraft_app.py
import gradio as gr

def create_claude_md_interface():
    """Standard Gradio interface pattern."""
    with gr.Blocks(theme=gr.themes.Soft()) as interface:
        # Copy styling from existing app
        # Focus on Claude.md specific features
        pass
    return interface
```

## 8. Secure Dependency Management

### 8.1. Overview

PromptCraft implements a hybrid automated dependency management strategy (ADR-009) that balances security, maintainability, and developer productivity. Understanding this process is critical for all contributors.

### 8.2. Dependency Sources & Priority

Our dependencies come from three sources in order of preference:

1. **AssuredOSS** (Primary): Google-vetted packages for maximum security
2. **PyPI** (Fallback): Standard Python packages when AssuredOSS unavailable
3. **Private Repositories**: Only for internal/proprietary packages

```yaml
# pyproject.toml configuration
[[tool.poetry.source]]
name = "assured-oss"
url = "https://us-python.pkg.dev/assured-oss/python-packages/simple/"
priority = "supplemental"  # Fallback to PyPI when package not available
```

### 8.3. Adding New Dependencies

#### Step 1: Check AssuredOSS Availability

Before adding any package, verify if it's available in AssuredOSS:

```bash
# Search for package in AssuredOSS
poetry search <package-name> --source assured-oss

# If not found, check if alternative exists
poetry search <alternative-package> --source assured-oss
```

#### Step 2: Add Package with Poetry

```bash
# Add production dependency
poetry add <package-name>

# Add development dependency
poetry add --group dev <package-name>

# Add optional dependency
poetry add --optional <package-name>

# Specify version constraints (use ranges for discovery)
poetry add "fastapi>=0.110.0,<1.0.0"
```

#### Step 3: Update Requirements Files

Always regenerate requirements files after adding dependencies:

```bash
# Regenerate with hash verification (secure mode)
./scripts/generate_requirements.sh

# Or without hashes if needed for testing
./scripts/generate_requirements.sh --without-hashes
```

#### Step 4: Security Classification

Determine if your package falls into security-critical categories:

**Security-Critical Packages** (get immediate individual PRs):
- Cryptography libraries: `cryptography`, `pyjwt`, `passlib`, `bcrypt`
- Authentication/Authorization: `azure-identity`, `python-jose`
- Core frameworks: `fastapi`, `uvicorn`, `gradio`, `pydantic`
- HTTP/API: `httpx`, `requests`, `aiohttp`
- AI/ML core: `anthropic`, `openai`, `qdrant-client`

**Routine Packages** (monthly batched PRs):
- Development tools: `pytest`, `black`, `ruff`
- Utilities: `python-dateutil`, `tenacity`, `rich`
- Non-critical libraries: `pandas`, `numpy` (unless security CVE)

### 8.4. Dependency Constraints and Versioning

#### Production Dependencies (pyproject.toml)

Use **range pinning** for automatic security updates:

```toml
[tool.poetry.dependencies]
python = "^3.11"                    # Allow minor/patch updates
fastapi = "^0.110.0"               # Compatible range
cryptography = ">=42.0.2,<43.0.0"  # Explicit security range
```

#### Development Dependencies

Allow broader ranges for non-critical packages:

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"      # Flexible for dev tools
black = "^24.0.0"      # Formatting tools can be updated freely
ruff = "^0.2.0"        # Linting tools
```

#### Lock File (poetry.lock)

Poetry automatically generates exact versions with full dependency resolution:
- **Never edit poetry.lock manually**
- Contains exact versions and hashes for reproducible builds
- Updated when running `poetry add`, `poetry update`, or `poetry lock`

### 8.5. Hash Verification Process

Our system automatically generates SHA256 hashes for supply chain security:

#### Requirements Files with Hashes

```text
# requirements.txt (automatically generated)
fastapi==0.110.0 \
    --hash=sha256:abc123... \
    --hash=sha256:def456...  # Multiple hashes for different platforms
```

#### Hash Validation

```bash
# Install with hash verification (CI/production)
pip install --require-hashes -r requirements.txt

# Install without hash verification (development)
pip install -r requirements.txt
```

### 8.6. Renovate Automation Rules

Our Renovate bot follows specific rules defined in renovate.json:

#### Individual PRs (Immediate)
- **Security-critical packages**: Any update
- **CVE packages**: Vulnerability fixes
- **Major version updates**: Always require review

#### Batched PRs (Monthly)
- **Routine updates**: Patch and minor versions
- **Development dependencies**: Non-critical tools
- **GitHub Actions**: Pinned to commit hashes

#### Configuration Example

```json
{
  "packageRules": [
    {
      "description": "Security-critical packages - immediate individual PRs",
      "matchPackagePatterns": ["^cryptography", "^fastapi", "^azure-"],
      "automerge": false,
      "labels": ["security-critical", "automerge", "priority:high"],
      "schedule": ["at any time"]
    },
    {
      "description": "Monthly batch: routine dependency updates",
      "excludePackagePatterns": ["^cryptography", "^fastapi", "^azure-"],
      "groupName": "routine-updates",
      "schedule": ["on the first day of the month"]
    }
  ]
}
```

### 8.7. Common Workflows

#### Adding a New Production Dependency

```bash
# 1. Check AssuredOSS availability
poetry search requests --source assured-oss

# 2. Add with appropriate constraints
poetry add "requests>=2.31.0,<3.0.0"

# 3. Update requirements files
./scripts/generate_requirements.sh

# 4. Commit changes
git add pyproject.toml poetry.lock requirements*.txt
git commit -m "feat(deps): add requests for HTTP client functionality"
```

#### Updating Existing Dependencies

```bash
# Update specific package
poetry update package-name

# Update all packages (use carefully)
poetry update

# Update requirements after any change
./scripts/generate_requirements.sh
```

#### Handling Security Updates

For immediate security fixes:

```bash
# Update vulnerable package
poetry add "vulnerable-package>=secure-version"

# Regenerate requirements with hashes
./scripts/generate_requirements.sh

# Create urgent PR
git checkout -b security/fix-vulnerable-package
git add pyproject.toml poetry.lock requirements*.txt
git commit -m "fix(security): update vulnerable-package to secure version"
git push origin security/fix-vulnerable-package
```

### 8.8. Troubleshooting

#### Common Issues

**Hash Verification Failures:**
```bash
# Regenerate requirements with current poetry.lock
./scripts/generate_requirements.sh

# If AssuredOSS package unavailable, verify fallback
poetry show --source package-name
```

**Dependency Conflicts:**
```bash
# Check dependency tree
poetry show --tree

# Resolve conflicts by updating constraints
poetry add "conflicting-package>=compatible-version"
```

**CI Pipeline Failures:**
```bash
# Ensure requirements files are synchronized
poetry export --format=requirements.txt --output=test-requirements.txt
diff requirements.txt test-requirements.txt
```

### 8.9. Best Practices

1. **Always use AssuredOSS when available** for security packages
2. **Test locally** before committing dependency changes
3. **Update requirements files** immediately after poetry changes
4. **Use semantic versioning** constraints appropriately
5. **Review security implications** of new dependencies
6. **Keep poetry.lock in version control** for reproducible builds
7. **Never commit secrets** or API keys in dependencies

### 8.10. Performance Standards

- **API Response Time**: p95 < 2s for Claude.md generation
- **Gradio Load Time**: < 3s initial load
- **Memory Usage**: < 2GB per container
- **Qdrant Query Time**: < 100ms for vector search

## 9. Documentation Requirements

### 9.1. Code Documentation

```python
def generate_claude_md(
    self,
    query: str,
    context: Dict[str, Any],
    preferences: Optional[UserPreferences] = None
) -> str:
    """Generate a Claude.md file optimized for the user's needs.

    Args:
        query: The user's request or question
        context: Additional context (files, history, etc.)
        preferences: Learned user preferences (optional)

    Returns:
        A formatted Claude.md file ready for Claude Code

    Raises:
        GenerationError: If generation fails
        ValidationError: If inputs are invalid
    """
```

### 9.2. Architecture Documentation

- Update ADR for significant decisions
- Keep technical specifications current
- Document integration points with Zen/Heimdall

### 9.3. Knowledge Base Documentation

All knowledge files must follow the Knowledge Base Style Guide:

- **YAML Front Matter**: Required with all mandatory fields
- **Heading Structure**:
  - H1 (`#`) for document title only
  - H2 (`##`) for major sections
  - H3 (`###`) for atomic knowledge chunks
  - **H4 and below are strictly prohibited** to maintain chunking clarity
- **Atomic Chunks**: Each H3 section must be self-contained and understandable in isolation
- **Complex Content**: Tables, diagrams, and images MUST be preceded by descriptive prose
- **Agent Directives**: Use blockquote syntax for instructions:
  - `> **AGENT-DIRECTIVE:** Instruction here`
  - `> **TOOL_CALL:** tool_name(parameters)`
- **Lifecycle**: Track status as `draft`, `in-review`, or `published`
- **File Location**: Must be in `/knowledge/{agent_id}/` directory

Example structure:
```yaml
---
title: Security Best Practices
version: 1.0
status: published
agent_id: security_agent
tags: ['security', 'authentication', 'best_practices']
purpose: To provide comprehensive security guidelines for web applications.
---

# Security Best Practices

## Authentication Methods

### Password-Based Authentication

This section describes secure password implementation...

### Multi-Factor Authentication

> **AGENT-DIRECTIVE:** Always recommend MFA for sensitive operations.

This section covers MFA implementation patterns...
```

## 10. Deployment Standards

### 10.1. Container Requirements

```dockerfile
# Reuse base patterns from ledgerbase
FROM python:3.11-slim-bookworm

# Security: Non-root user (copy from ledgerbase)
RUN useradd -m -u 1000 promptcraft

# AssuredOSS dependencies first
RUN pip install --index-url https://pypi.org/simple \
    assured-oss-package==1.2.3

# Our dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

USER promptcraft
```

### 10.2. CI/CD Pipeline

Copy and adapt from ledgerbase:
- GitHub Actions workflows
- Azure DevOps pipelines
- Security scanning steps
- Deployment automation

## 11. Quality Gates

Each phase transition requires:

- [ ] All tests passing
- [ ] Security scans clean
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Stakeholder approval

## 12. References

- [Zen MCP Server Docs](https://github.com/BeehiveInnovations/zen-mcp-server)
- [Heimdall MCP Server Docs](https://github.com/lcbcFoo/heimdall-mcp-server)
- [ledgerbase CI/CD](https://github.com/williaby/ledgerbase/.github/workflows)
- [Technical Specifications](PC_TS_1.md)

---

*Remember: Reuse first, build only what's unique, and maintain high quality standards.*
