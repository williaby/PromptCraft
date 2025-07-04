# Project Structure and Architecture

## Directory Structure
```
PromptCraft/
├── src/                    # Core application code
│   ├── agents/            # Multi-agent system framework
│   │   ├── base_agent.py      # Base agent interface (placeholder)
│   │   ├── create_agent.py    # Agent factory/creation logic
│   │   └── registry.py        # Agent registry and discovery
│   ├── core/              # Core business logic
│   │   ├── query_counselor.py # Query processing and routing (placeholder)
│   │   ├── hyde_processor.py  # HyDE-enhanced retrieval (placeholder)
│   │   └── vector_store.py    # Vector database interface (placeholder)
│   ├── ui/                # Gradio interface components
│   ├── ingestion/         # Knowledge processing pipeline
│   ├── mcp_integration/   # MCP server integration
│   ├── config/            # Configuration management
│   └── utils/             # Shared utilities
│       └── encryption.py      # GPG encryption utilities
├── knowledge/             # Knowledge base with C.R.E.A.T.E. framework
│   ├── create/            # Structured knowledge files
│   └── domain_specific/   # Specialized domain knowledge
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
├── docs/                  # Documentation
├── deployment/            # Infrastructure and deployment
├── scripts/               # Utility scripts
└── config/                # Configuration files
```

## Key Components

### Multi-Agent System
- **Base Framework**: `src/agents/base_agent.py` (currently placeholder)
- **Agent Registry**: `src/agents/registry.py` for discovery and coordination
- **Specialized Agents**: Coordinated through Zen MCP Server

### Query Processing
- **HyDE Enhancement**: `src/core/hyde_processor.py` (three-tier analysis, placeholder)
- **Query Routing**: `src/core/query_counselor.py` (placeholder)
- **Vector Interface**: `src/core/vector_store.py` (placeholder)

### Knowledge Management
- **External Vector DB**: Qdrant at 192.168.1.16:6333
- **C.R.E.A.T.E. Framework**: Knowledge files with YAML frontmatter
- **Style Guide**: `docs/style_guide.md` for markdown formatting
- **Ingestion Pipeline**: Processes various document types

## Development Status
- **Current Phase**: Early development with many core files as placeholders
- **Architecture**: Well-defined but implementation pending
- **Philosophy**: Configuration over custom development, reuse existing tools
- **Main Entry**: `src/main:app` (FastAPI/Uvicorn)
- **UI Access**: Gradio at http://192.168.1.205:7860
- **External Dependencies**: Qdrant vector database on Unraid infrastructure
