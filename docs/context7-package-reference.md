# Context7 MCP Server Package Reference

## Overview

This document provides a comprehensive reference for using package names with the Context7 MCP server.
Context7 requires specific package identifiers to fetch documentation, and this guide helps identify the
correct names for our project dependencies.

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

   ```bash
   mcp__context7-sse__resolve-library-id
   libraryName: "package_name"
   ```

2. **Review Options**:
   - Check trust scores (prefer 9+)
   - Verify it's the correct package
   - Note the Context7-compatible library ID

3. **Fetch Documentation**:

   ```bash
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
| httpx ✅ | `/encode/httpx` | 7.5 | HTTP client library |

### Data Processing & Validation

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| pandas ✅ | `/pandas-dev/pandas` | 9.2 | Official Pandas documentation |
| pydantic ✅ | `/pydantic/pydantic` | 9.6 | Official Pydantic documentation |
| pydantic-settings ✅ | `/pydantic/pydantic-settings` | 9.6 | Settings management |
| numpy ✅ | `/numpy/numpy` | 10.0 | Numerical computing |
| pyyaml ✅ | `/yaml/pyyaml` | 7.4 | YAML processing |
| python-multipart ✅ | `/kludex/python-multipart` | 10.0 | Multipart form handling |

### AI/ML Libraries

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| anthropic ✅ | `/anthropics/anthropic-sdk-python` | 8.8 | Official Python SDK |
| openai ✅ | `/openai/openai-python` | 9.1 | Official OpenAI Python library |
| sentence-transformers ✅ | `/ukplab/sentence-transformers` | 7.8 | Embedding generation |
| tiktoken ✅ | `/openai/tiktoken` | 9.1 | OpenAI tokenizer |
| qdrant-client ✅ | `/qdrant/qdrant-client` | 9.8 | Vector database client |

### Azure Cloud Services

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| azure-identity 🔍 | *Need to verify* | - | Azure authentication |
| azure-keyvault-secrets 🔍 | *Need to verify* | - | Key Vault secrets |
| azure-storage-blob 🔍 | *Need to verify* | - | Azure Blob storage |

### Security & Crypto

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| cryptography ✅ | `/pyca/cryptography` | 8.0 | Core cryptographic operations |
| pyjwt ✅ | `/jpadilla/pyjwt` | 9.9 | JWT handling |
| python-gnupg 🔍 | *Need to verify* | - | GPG operations (No high-trust match found) |

### Development & Testing Tools

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| pytest ✅ | `/pytest-dev/pytest` | 9.5 | Official pytest documentation |
| pytest-asyncio ✅ | `/pytest-dev/pytest-asyncio` | 9.5 | Async testing support |
| pytest-cov ✅ | `/pytest-dev/pytest-cov` | 9.5 | Coverage plugin |
| pytest-mock ✅ | `/pytest-dev/pytest-mock` | 9.5 | Mock integration |
| pytest-timeout ✅ | `/pytest-dev/pytest-timeout` | 9.5 | Test timeout handling |
| pytest-xdist ✅ | `/pytest-dev/pytest-xdist` | 9.5 | Distributed testing |
| black ✅ | `/psf/black` | 7.3 | Python code formatter |
| ruff ✅ | `/astral-sh/ruff` | 9.4 | Fast Python linter and formatter |
| mypy ✅ | `/python/mypy` | 8.9 | Optional static typing for Python |
| bandit ✅ | `/pycqa/bandit` | 8.1 | Security issue scanner for Python |

### Infrastructure & Utilities

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| redis ✅ | `/redis/redis-py` | 9.0 | Redis Python client |
| prometheus-client ✅ | `/prometheus/client_python` | 7.4 | Metrics collection |
| python-dotenv ✅ | `/theskumar/python-dotenv` | 8.1 | Environment config |
| structlog ✅ | `/hynek/structlog` | 9.2 | Structured logging |
| rich ✅ | `/textualize/rich` | 9.4 | Rich text formatting |
| tenacity ✅ | `/jd/tenacity` | 9.9 | Retry mechanisms |
| python-dateutil ✅ | `/dateutil/dateutil` | 7.0 | Date utilities |
| aiofiles ✅ | `/tinche/aiofiles` | 9.4 | Async file operations |
| asyncer 🔍 | *Need to verify* | - | Async utilities (No high-trust match found) |

### New Dependencies (Added in Latest Update)

| Package | Context7 ID | Trust Score | Notes |
|---------|-------------|-------------|-------|
| mcp 🔍 | *Need to verify* | - | MCP protocol client |
| spacy ✅ | `/explosion/spacy` | 9.9 | NLP processing |
| nltk ✅ | `/nltk/nltk` | 6.9 | Natural language utilities |
| detect-secrets ✅ | `/yelp/detect-secrets` | 8.2 | Security scanning |
| sentry-sdk ✅ | `/getsentry/sentry-python` | 9.0 | Error monitoring |
| opentelemetry-api ✅ | `/open-telemetry/opentelemetry-python` | 9.3 | Observability tracing |

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

## Package Mapping Status

**Completed Verification:**

- [x] Web Framework & Server: gradio, fastapi, uvicorn, httpx ✅
- [x] Data Processing: pandas, pydantic, pydantic-settings, numpy, pyyaml, python-multipart ✅
- [x] AI/ML Libraries: anthropic, openai, tiktoken, sentence-transformers, qdrant-client, spacy, nltk ✅
- [x] Security & Crypto: cryptography, pyjwt ✅
- [x] Infrastructure: redis, prometheus-client, python-dotenv, structlog, rich, tenacity, python-dateutil, aiofiles ✅
- [x] Testing Tools: pytest, pytest-asyncio, pytest-cov, pytest-mock, pytest-timeout, pytest-xdist ✅
- [x] Development Tools: black, ruff, mypy, bandit ✅
- [x] Observability: sentry-sdk, opentelemetry-api, detect-secrets ✅

**Remaining Packages (No Context7 Coverage):**

- [ ] azure-identity (Azure packages not specifically covered in Context7)
- [ ] azure-keyvault-secrets (Azure packages not specifically covered in Context7)
- [ ] azure-storage-blob (Azure packages not specifically covered in Context7)
- [ ] python-gnupg (No high-trust match found)
- [ ] asyncer (No high-trust match found - FastAPI team utility)
- [ ] mcp (No results returned from Context7)

## Maintenance

This document should be updated whenever:

- New dependencies are added to pyproject.toml
- Package IDs change or become deprecated
- Better alternatives are discovered
- Trust scores significantly change

## Last Updated

$(date)
