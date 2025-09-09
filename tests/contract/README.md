# MCP Contract Tests

Consumer-driven contract tests for PromptCraft MCP integrations using Pact and local servers.

## Overview

These tests validate API contracts between PromptCraft (consumer) and MCP servers (providers):
- **zen-mcp-server**: Query processing, health checks, knowledge retrieval
- **heimdall-mcp-server**: Security analysis, code quality analysis (using stub)

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PromptCraft   │    │   zen-mcp-server │    │  heimdall-stub  │
│   (Consumer)    │◄──►│   (Provider)     │    │   (Provider)    │
│                 │    │  localhost:8080  │    │  localhost:8081 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐                              ┌─────────────────┐
│  Pact Contracts │                              │  Pact Contracts │
│  zen-server.json│                              │ heimdall.json   │
└─────────────────┘                              └─────────────────┘
```

## Setup

### 1. Install Dependencies

```bash
# Install pact-python (already enabled in pyproject.toml)
poetry install

# Optional: Install pact-ruby-standalone for full Pact features
gem install pact-mock_service
```

### 2. Prepare Local Servers

**zen-mcp-server**: Ensure you have it available at:
- `/home/byron/dev/zen-mcp-server/server.py`
- `/home/byron/dev/PromptCraft/zen-mcp-server/server.py`

**heimdall-stub**: Built-in test stub (no setup required)

## Running Tests

### Quick Start
```bash
# Run all contract tests
./run_contract_tests.py

# Or with poetry directly
poetry run pytest tests/contract/ -m contract -v
```

### Manual Test Execution
```bash
# Run specific test classes
poetry run pytest tests/contract/test_mcp_contracts.py::TestZenMCPContracts -v
poetry run pytest tests/contract/test_mcp_contracts.py::TestHeimdalMCPContracts -v

# Run with server requirements
poetry run pytest tests/contract/ -m "contract and requires_servers" -v
```

## Test Configuration

### Environment Variables
- `PACT_TEST_MODE`: `consumer` | `provider` | `both` (default: consumer)
- `CONTRACT_TEST`: `true` (enables contract test mode)
- `LOG_LEVEL`: `DEBUG` | `INFO` | `WARNING` (default: INFO)

### Pact Configuration
- **Consumer**: `promptcraft`
- **Providers**: `zen-mcp-server`, `heimdall-mcp-server`
- **Mock Ports**: 1234 (zen), 1235 (heimdall)
- **Real Ports**: 8080 (zen), 8081 (heimdall)
- **Pact Files**: `./pacts/`

## Test Structure

### TestZenMCPContracts
- `test_query_processing_contract()`: POST /api/v1/query/process
- `test_agent_health_check_contract()`: GET /health, /health/agents
- `test_knowledge_retrieval_contract()`: POST /api/v1/knowledge/search
- `test_error_handling_contract()`: Error response validation

### TestHeimdalMCPContracts  
- `test_security_analysis_contract()`: POST /api/v1/analyze/security
- `test_code_quality_contract()`: POST /api/v1/analyze/quality

## Generated Artifacts

After running tests, you'll find:
- `./pacts/promptcraft-zen_mcp_server.json`: Zen server contract
- `./pacts/promptcraft-heimdall_mcp_server.json`: Heimdall server contract

## Troubleshooting

### Server Connection Issues
```bash
# Check if servers are running
curl http://localhost:8080/health  # zen-mcp-server
curl http://localhost:8081/health  # heimdall-stub
```

### Test Skipping
Tests may be skipped if:
- `pact-python` not installed → Install with `poetry install`
- `zen-mcp-server` not found → Clone/install zen-mcp-server locally
- Servers fail to start → Check server logs and ports

### Missing Pact Binary
While optional, install for full Pact features:
```bash
# macOS/Linux
gem install pact-mock_service

# Or download pact-ruby-standalone
# https://github.com/pact-foundation/pact-ruby-standalone
```

## Best Practices

1. **Contract-First**: Tests define expected API behavior
2. **Real Servers**: Tests run against actual server implementations
3. **Graceful Degradation**: Tests handle missing/unimplemented endpoints
4. **Deterministic**: Stub server provides consistent responses
5. **Fast Execution**: Local servers for quick feedback

## Integration with CI/CD

```yaml
# Example GitHub Actions
- name: Run Contract Tests
  run: |
    poetry install
    poetry run pytest tests/contract/ -m contract -v
    
- name: Upload Pact Files
  # Optional: Upload to Pact Broker
  run: |
    # pact-broker publish ./pacts --consumer-app-version=${{ github.sha }}
```