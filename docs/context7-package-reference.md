# Context7 MCP Server Package Reference

## Overview

This document provides a comprehensive reference for using package names with the Context7 MCP server. Context7 requires specific package identifiers to fetch documentation, and this guide helps identify the correct names for our project dependencies.

## Package Name Format

Context7 uses the format: `/org/project` or `/org/project/version`

Examples:
- `/tiangolo/fastapi` - FastAPI web framework
- `/pandas-dev/pandas` - Pandas data analysis library
- `/anthropics/anthropic-sdk-python` - Anthropic Python SDK

## Selection Criteria

When multiple packages match your search, prioritize by:

1. **Trust Score** (9-10 ideal, 7+ acceptable)
2. **Name Match** (exact package name preferred)
3. **Code Snippets** (higher count = better documentation coverage)
4. **Official Organization** (prefer official maintainer organizations)

## Workflow

1. **Search for Package**:
   ```
   mcp__context7-sse__resolve-library-id
   libraryName: "package_name"
   ```

2. **Review Options**:
   - Check trust scores (prefer 9+)
   - Verify it's the correct package
   - Note the Context7-compatible library ID

3. **Fetch Documentation**:
   ```
   mcp__context7-sse__get-library-docs
   context7CompatibleLibraryID: "/org/project"
   topic: "specific_topic" (optional)
   tokens: 1000-10000 (adjust as needed)
   ```

## Verified Package Mappings

Based on our pyproject.toml dependencies (✅ = verified, 🔍 = needs verification):

### Web Framework & Server
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| fastapi ✅ | `/tiangolo/fastapi` | 9.9 | Official FastAPI documentation |
| uvicorn ✅ | `/encode/uvicorn` | 7.5 | ASGI web server |
| gradio ✅ | `/gradio-app/gradio` | 9.8 | Official Gradio documentation |
| httpx 🔍 | *Need to verify* | - | HTTP client library |

### Data Processing & Validation
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| pandas ✅ | `/pandas-dev/pandas` | 9.2 | Official Pandas documentation |
| pydantic ✅ | `/pydantic/pydantic` | 9.6 | Official Pydantic documentation |
| pydantic-settings ✅ | `/pydantic/pydantic-settings` | 9.6 | Settings management |
| numpy 🔍 | *Need to verify* | - | Numerical computing |
| pyyaml 🔍 | *Need to verify* | - | YAML processing |
| python-multipart 🔍 | *Need to verify* | - | Multipart form handling |

### AI/ML Libraries
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| anthropic ✅ | `/anthropics/anthropic-sdk-python` | 8.8 | Official Python SDK |
| openai ✅ | `/openai/openai-python` | 9.1 | Official OpenAI Python library |
| sentence-transformers 🔍 | *Need to verify* | - | Embedding generation |
| tiktoken ✅ | `/openai/tiktoken` | 9.1 | OpenAI tokenizer |
| qdrant-client 🔍 | *Need to verify* | - | Vector database client |

### Azure Cloud Services
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| azure-identity 🔍 | *Need to verify* | - | Azure authentication |
| azure-keyvault-secrets 🔍 | *Need to verify* | - | Key Vault secrets |
| azure-storage-blob 🔍 | *Need to verify* | - | Azure Blob storage |

### Security & Crypto
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| cryptography 🔍 | *Need to verify* | - | Core cryptographic operations |
| pyjwt 🔍 | *Need to verify* | - | JWT handling |
| python-gnupg 🔍 | *Need to verify* | - | GPG operations |

### Development & Testing Tools
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| pytest ✅ | `/pytest-dev/pytest` | 9.5 | Official pytest documentation |
| pytest-asyncio ✅ | `/pytest-dev/pytest-asyncio` | 9.5 | Async testing support |
| pytest-cov ✅ | `/pytest-dev/pytest-cov` | 9.5 | Coverage plugin |
| pytest-mock ✅ | `/pytest-dev/pytest-mock` | 9.5 | Mock integration |
| pytest-timeout ✅ | `/pytest-dev/pytest-timeout` | 9.5 | Test timeout handling |
| pytest-xdist ✅ | `/pytest-dev/pytest-xdist` | 9.5 | Distributed testing |
| black 🔍 | *Need to verify* | - | Code formatter |
| ruff 🔍 | *Need to verify* | - | Linter |
| mypy 🔍 | *Need to verify* | - | Type checker |
| bandit 🔍 | *Need to verify* | - | Security scanner |

### Infrastructure & Utilities
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| redis 🔍 | *Need to verify* | - | Caching layer |
| prometheus-client 🔍 | *Need to verify* | - | Metrics collection |
| python-dotenv 🔍 | *Need to verify* | - | Environment config |
| structlog 🔍 | *Need to verify* | - | Structured logging |
| rich 🔍 | *Need to verify* | - | Rich text formatting |
| tenacity 🔍 | *Need to verify* | - | Retry mechanisms |
| python-dateutil 🔍 | *Need to verify* | - | Date utilities |
| aiofiles 🔍 | *Need to verify* | - | Async file operations |
| asyncer 🔍 | *Need to verify* | - | Async utilities |

### New Dependencies (Added in Latest Update)
| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| mcp 🔍 | *Need to verify* | - | MCP protocol client |
| spacy 🔍 | *Need to verify* | - | NLP processing |
| nltk 🔍 | *Need to verify* | - | Natural language utilities |
| detect-secrets 🔍 | *Need to verify* | - | Security scanning |
| sentry-sdk 🔍 | *Need to verify* | - | Error monitoring |
| opentelemetry-api 🔍 | *Need to verify* | - | Observability tracing |

## Usage Examples

### Getting Started Documentation
```bash
# FastAPI basic setup
mcp__context7-sse__get-library-docs
context7CompatibleLibraryID: "/tiangolo/fastapi"
topic: "getting started"
tokens: 2000
```

### Specific Feature Documentation
```bash
# Pandas data manipulation
mcp__context7-sse__get-library-docs
context7CompatibleLibraryID: "/pandas-dev/pandas"
topic: "dataframe operations"
tokens: 3000
```

### API Reference
```bash
# Anthropic API usage
mcp__context7-sse__get-library-docs
context7CompatibleLibraryID: "/anthropics/anthropic-sdk-python"
topic: "client initialization"
tokens: 1500
```

## Best Practices

1. **Always verify the package ID** using `resolve-library-id` first
2. **Check trust scores** - prefer packages with scores 9+ for critical dependencies
3. **Use specific topics** to get more relevant documentation
4. **Adjust token limits** based on how much context you need (1000-10000 range)
5. **Cache successful mappings** in this document for team reference

## Common Patterns

- **Official packages**: Often use the maintainer's GitHub org (e.g., `/tiangolo/fastapi`)
- **Python packages**: Sometimes include `-python` suffix (e.g., `/anthropics/anthropic-sdk-python`)
- **Organizations**: Major projects often use their official org name (e.g., `/pandas-dev/pandas`)

## Troubleshooting

If a package isn't found:
1. Try variations of the name (with/without python suffix)
2. Search for the organization name
3. Check if it's part of a larger ecosystem
4. Look for community-maintained alternatives

## TODO: Complete Package Mapping

The following packages from our pyproject.toml still need verification:
- [ ] gradio
- [ ] uvicorn
- [ ] httpx
- [ ] pydantic-settings
- [ ] openai
- [ ] tiktoken
- [ ] azure-identity
- [ ] azure-keyvault-secrets
- [ ] azure-storage-blob
- [ ] numpy
- [ ] pyyaml
- [ ] python-multipart
- [ ] redis
- [ ] prometheus-client
- [ ] python-dotenv
- [ ] structlog
- [ ] rich
- [ ] cryptography
- [ ] pyjwt
- [ ] python-gnupg
- [ ] tenacity
- [ ] python-dateutil
- [ ] aiofiles
- [ ] asyncer
- [ ] Development tools (pytest, black, ruff, mypy, etc.)

## Maintenance

This document should be updated whenever:
- New dependencies are added to pyproject.toml
- Package IDs change or become deprecated
- Better alternatives are discovered
- Trust scores significantly change

*Last updated: $(date)*