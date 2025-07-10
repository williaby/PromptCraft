# Project Structure

## Source Directory Layout

```text
src/
├── agents/          # Multi-agent system framework
│   ├── base_agent.py      # Base agent interface (placeholder)
│   ├── create_agent.py    # Agent factory/creation logic
│   └── registry.py        # Agent registry and discovery
├── config/          # Configuration management
│   ├── health.py          # Health check system (COMPLETE)
│   ├── settings.py        # Pydantic settings with environment loading
│   └── __init__.py
├── core/            # Core business logic
│   ├── query_counselor.py # Query processing and routing (placeholder)
│   ├── hyde_processor.py  # HyDE-enhanced retrieval (placeholder)
│   └── vector_store.py    # Vector database interface (placeholder)
├── ui/              # Gradio interface components
├── ingestion/       # Knowledge processing pipeline
├── mcp_integration/ # MCP server integration
└── utils/           # Shared utilities
    ├── encryption.py       # GPG encryption utilities
    └── __init__.py
```

## Knowledge Base Structure

```text
knowledge/           # Knowledge base with C.R.E.A.T.E. framework
├── create/          # Structured knowledge files
└── domain_specific/ # Specialized domain knowledge
```

## Documentation Structure

```text
docs/
├── planning/        # Project planning and documentation
│   ├── project_hub.md     # Central documentation index
│   ├── phase-1-index.md   # Phase 1 planning document
│   └── TODO.md           # Technical debt and improvements
├── style_guide.md   # Knowledge file formatting standards
└── context7-package-reference.md  # Context7 integration guide
```

## Testing Structure

```text
tests/
├── unit/            # Unit tests
│   ├── config/      # Configuration tests
│   └── utils/       # Utility tests
├── integration/     # Integration tests
└── fixtures/        # Test fixtures
```

## Configuration Files

- **pyproject.toml**: Primary Python configuration (Poetry, tools, metadata)
- **noxfile.py**: Automation for testing and quality checks
- **.pre-commit-config.yaml**: Git hooks for code quality
- **docker-compose.zen-vm.yaml**: Development environment setup
- **Dockerfile**: Multi-stage container builds

## Key Files Status

### Completed Components
- ✅ **src/config/health.py**: Complete health check system
- ✅ **src/config/settings.py**: Pydantic configuration system
- ✅ **src/utils/encryption.py**: GPG encryption utilities
- ✅ **src/main.py**: FastAPI application with health endpoints

### Placeholder Components (Early Development)
- 📋 **src/agents/**: Multi-agent framework (architecture defined)
- 📋 **src/core/**: Core business logic (planning phase)
- 📋 **src/ui/**: Gradio interface (basic structure)
- 📋 **src/ingestion/**: Knowledge processing pipeline (planned)

## Development Philosophy Integration

### Reuse First
- CI/CD patterns from ledgerbase repository
- Documentation templates from FISProject
- GitHub Actions from .github repository
- UI components from existing promptcraft_app.py

### Configure Don't Build
- Zen MCP Server for orchestration
- Heimdall MCP Server for analysis
- AssuredOSS packages for security
- External Qdrant for vector database

### Focus on Unique Value
- Claude.md generation logic
- Prompt composition intelligence
- User preference learning
- C.R.E.A.T.E. framework implementation
