# Technology Stack

## Core Technologies
- **Python**: 3.11+ (primary development language)
- **Dependency Management**: Poetry (not Node.js/npm)
- **Web Framework**: Gradio UI + FastAPI backend
- **Container Platform**: Docker with multi-stage builds

## AI/ML Stack
- **Real-Time Orchestration**: Zen MCP Server
- **Background Orchestration**: Prefect
- **Query Intelligence**: HyDE Engine
- **RAG Framework**: LlamaIndex
- **Vector Database**: Qdrant (external at 192.168.1.16:6333)
- **AI Providers**: Anthropic, OpenAI, Azure AI

## Key Dependencies (from pyproject.toml)
- **Web**: gradio ^4.19.2, fastapi ^0.110.0, uvicorn ^0.27.1
- **AI/ML**: qdrant-client ^1.8.0, sentence-transformers ^2.5.1, anthropic ^0.18.1, openai ^1.12.0
- **Data**: pydantic ^2.6.1, numpy ^1.26.4, pandas ^2.2.0
- **Azure**: azure-identity ^1.15.0, azure-keyvault-secrets ^4.8.0
- **Security**: cryptography ^42.0.2, python-gnupg ^0.5.2
- **Infrastructure**: redis ^5.0.1, prometheus-client ^0.20.0

## Development Tools
- **Testing**: pytest ^8.0.1 with coverage, asyncio, and memory profiling
- **Code Quality**: black ^24.2.0, ruff ^0.2.2, mypy ^1.8.0
- **Security**: bandit ^1.7.7, safety ^3.0.1
- **Automation**: nox ^2024.3.2, pre-commit ^3.6.2
