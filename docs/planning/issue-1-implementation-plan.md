---
title: "Phase 1 Issue 1: Development Environment Setup - Implementation Plan"
version: "1.0"
status: draft
component: Planning
tags: ['phase-1', 'issue-1', 'development-environment', 'implementation']
source: PromptCraft-Hybrid Project
purpose: Detailed implementation plan for resolving Phase 1 Issue 1 with step-by-step deployment guide.
---

# Phase 1 Issue 1: Development Environment Setup - Implementation Plan

## 1. Issue Summary

**Issue ID**: Phase 1, Issue 1
**Title**: Development Environment Setup
**Worktree**: foundation
**Estimated Time**: 6 hours
**Status**: Ready for Implementation

### 1.1. Scope & Objectives

Establish complete development environment with proper tooling, security validation, and dependency management for PromptCraft-Hybrid Phase 1 MVP.

**Key Deliverables:**
- Unraid server deployment with 6-MCP orchestration stack
- Journey 1 (Web UI) and Journey 3 (IDE Integration) capabilities
- Development environment with Python 3.11+, Poetry, Docker
- Security validation with GPG/SSH keys and pre-commit hooks
- Performance targets: <2s response times, >99.5% uptime

## 2. Technical Requirements Analysis

### 2.1. Infrastructure Requirements

| Component | Specification | Purpose |
|:----------|:-------------|:--------|
| **Server**: | Unraid with 256GB RAM | Primary deployment target |
| **Storage**: | NVMe for Qdrant DB | High-speed vector operations |
| **Network**: | Gigabit LAN, <5ms latency | Local development performance |
| **External**: | Qdrant at 192.168.1.16:6333 | Vector database service |

### 2.2. Software Stack Requirements

```yaml
core_technologies:
  runtime:
    python: "3.11+"
    nodejs: "18.x LTS"
    docker: "25.x"

  dependency_management:
    python: "Poetry"
    javascript: "npm"

  container_orchestration:
    docker_compose: "v3.8+"
    unraid: "native container management"

  security:
    gpg_key: "required for .env encryption"
    ssh_key: "required for signed commits"
    pre_commit: "mandatory hooks"
```

## 3. Implementation Plan

### 3.1. Phase 1: Infrastructure Foundation (2 hours)

#### Step 1.1: Unraid Server Setup
```bash
# Deploy Docker Compose stack
cd /home/byron/dev/PromptCraft
docker-compose -f docker-compose.phase1.yml up -d

# Verify container deployment
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

#### Step 1.2: MCP Server Configuration
```yaml
mcp_servers:
  zen-mcp-server:
    port: 3000
    resources: {cpu: 4, memory: "8GB"}
    purpose: "Central orchestration"

  serena-mcp:
    port: 8000
    resources: {cpu: 2, memory: "4GB"}
    purpose: "Semantic code analysis"

  filesystem-mcp:
    port: 8001
    resources: {cpu: 1, memory: "1GB"}
    purpose: "Secure file access"

  github-mcp:
    port: 8002
    resources: {cpu: 1, memory: "1GB"}
    purpose: "Repository context"

  sequential-thinking-mcp:
    port: 8003
    resources: {cpu: 1, memory: "2GB"}
    purpose: "Enhanced reasoning"

  qdrant-memory-mcp:
    port: 8004
    resources: {cpu: 1, memory: "1GB"}
    purpose: "Vector search optimization"

  context7-mcp:
    port: 8005
    resources: {cpu: 1, memory: "1GB"}
    purpose: "External search"
```

#### Step 1.3: External Qdrant Connection
```bash
# Test external Qdrant connectivity
curl -X GET "http://192.168.1.16:6333/cluster"

# Verify collection access
curl -X GET "http://192.168.1.16:6333/collections"
```

### 3.2. Phase 2: Development Environment (2 hours)

#### Step 2.1: Local Development Setup
```bash
# Install Poetry if not present
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install --sync

# Install pre-commit hooks
poetry run pre-commit install
```

#### Step 2.2: Security Validation Setup
```bash
# Validate GPG keys (required for .env encryption)
gpg --list-secret-keys
if [ $? -ne 0 ]; then
    echo "ERROR: GPG key required for .env encryption"
    exit 1
fi

# Validate SSH keys (required for signed commits)
ssh-add -l
if [ $? -ne 0 ]; then
    echo "ERROR: SSH key required for signed commits"
    exit 1
fi

# Configure Git signing key
git config --get user.signingkey
if [ $? -ne 0 ]; then
    echo "ERROR: Git signing key not configured"
    exit 1
fi
```

#### Step 2.3: Environment Configuration
```bash
# Copy and configure environment file
cp .env.example .env

# Configure key environment variables
cat >> .env << 'EOF'
# Azure AI Configuration
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_KEY=your_key_here

# External Qdrant Configuration
QDRANT_HOST=192.168.1.16
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_key_here

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
EOF

# Encrypt .env file using GPG (following ledgerbase pattern)
poetry run python src/utils/encryption.py --encrypt .env
```

### 3.3. Phase 3: IDE Integration Setup (1.5 hours)

#### Step 3.1: Claude Code CLI Configuration
```bash
# Install Claude Code CLI (if not present)
curl -fsSL https://claude.ai/install.sh | sh

# Configure connection to self-hosted Zen MCP server
claude config set mcp-server-url http://192.168.1.205:3000
claude config set mcp-auth-token your_auth_token_here
```

#### Step 3.2: Journey 3 IDE Integration Test
```bash
# Test semantic code analysis via Serena MCP
claude "analyze the code structure of src/agents/base_agent.py"

# Test repository context via GitHub MCP
claude "show me the dependencies of this project"

# Test sequential thinking capabilities
claude "create a plan for implementing the query counselor"
```

#### Step 3.3: Performance Validation
```bash
# Test symbol lookup performance (<500ms target)
time claude "find all classes in the src directory"

# Test context generation performance (<2s target)
time claude "explain the purpose of the HyDE processor"

# Test repository scanning performance (<5s target)
time claude "give me an overview of the project structure"
```

### 3.4. Phase 4: Testing & Validation (0.5 hours)

#### Step 4.1: Container Health Checks
```bash
# Check all container health status
docker ps --filter "status=running" --format "table {{.Names}}\t{{.Status}}"

# Test MCP server connectivity
for port in 3000 8000 8001 8002 8003 8004 8005; do
    curl -f "http://localhost:${port}/health" || echo "Port ${port} failed"
done
```

#### Step 4.2: Integration Testing
```bash
# Test Journey 1 Web UI
curl -X POST "http://localhost:7860/api/enhance_prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "write email about project delay"}'

# Test Journey 3 IDE Integration
claude "test the multi-MCP orchestration workflow"
```

#### Step 4.3: Resource Utilization Check
```bash
# Verify resource usage within targets (<40GB total)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Calculate total memory usage
docker stats --no-stream --format "{{.MemUsage}}" | awk '{sum += $1} END {print "Total Memory:", sum "MB"}'
```

## 4. Success Criteria & Validation

### 4.1. Acceptance Criteria Validation

| Requirement | Validation Method | Success Criteria |
|:------------|:------------------|:-----------------|
| Python 3.11+ | `python --version` | Version ≥ 3.11.0 |
| Poetry | `poetry --version` | Successfully installed |
| Docker/Compose | `docker-compose --version` | Successfully installed |
| GPG Key | `gpg --list-secret-keys` | At least one key present |
| SSH Key | `ssh-add -l` | At least one key loaded |
| Pre-commit | `pre-commit run --all-files` | All hooks pass |
| Environment Validation | `poetry run python src/utils/encryption.py` | Validation successful |
| Container Health | Health check endpoints | All containers healthy |

### 4.2. Performance Benchmarks

```yaml
performance_targets:
  journey_1_web_ui:
    simple_prompts: "<2 seconds"
    complex_analysis: "<10 seconds"
    concurrent_users: "5-10 without degradation"

  journey_3_ide_integration:
    symbol_lookup: "<500ms"
    context_generation: "<2 seconds"
    repository_scan: "<5 seconds"

  system_reliability:
    uptime_target: ">99.5%"
    memory_usage: "<40GB total"
    response_time_p95: "<2 seconds"
```

### 4.3. Security Validation

```bash
# Run security scans
poetry run safety check
poetry run bandit -r src

# Validate container security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image zen-mcp:latest

# Test encrypted .env handling
poetry run python -c "
from src.utils.encryption import load_encrypted_env
env_vars = load_encrypted_env('.env.encrypted')
print('Environment loaded successfully')
"
```

## 5. Risk Mitigation & Contingency Plans

### 5.1. Common Issues & Solutions

| Risk | Impact | Mitigation Strategy |
|:-----|:-------|:-------------------|
| **MCP Server Failure** | High | Health checks, automatic retry, circuit breaker |
| **Resource Exhaustion** | High | Container limits, 60% headroom, monitoring |
| **External Qdrant Unavailable** | Medium | Local fallback, connection retry logic |
| **Network Latency** | Low | Local gigabit LAN, <5ms target |
| **GPG/SSH Key Issues** | Medium | Clear setup documentation, validation scripts |

### 5.2. Rollback Procedures

```bash
# Stop all containers if issues occur
docker-compose -f docker-compose.phase1.yml down

# Clean up volumes if needed
docker volume prune -f

# Reset to clean state
git clean -fd
git reset --hard HEAD
```

## 6. Next Steps & Phase 2 Preparation

### 6.1. Immediate Next Actions
1. Execute implementation plan step-by-step
2. Document any deviations or issues encountered
3. Validate all acceptance criteria
4. Prepare Phase 2 infrastructure requirements

### 6.2. Phase 2 Readiness Checklist
- [ ] Multi-MCP orchestration patterns proven
- [ ] 220GB RAM headroom available for expansion
- [ ] Container management and service discovery established
- [ ] Agent registry and base classes ready for specialized agents
- [ ] Performance baseline established for scaling decisions

## 7. Documentation & Handoff

### 7.1. Required Documentation Updates
- Update CLAUDE.md with new development commands
- Document MCP server configuration and troubleshooting
- Create deployment runbook for future updates
- Update README.md with installation verification steps

### 7.2. Team Handoff Items
- Share access credentials for MCP servers
- Document troubleshooting procedures
- Establish monitoring and alerting for production deployment
- Schedule Phase 2 planning session

---

**Implementation Timeline**: 6 hours total
**Resource Allocation**: 37GB RAM, 14 CPU cores
**Success Metrics**: >99.5% uptime, <2s response times, 70% code reuse
**Next Phase**: Phase 2 Multi-Agent Capabilities

This implementation plan provides comprehensive step-by-step guidance for resolving Phase 1 Issue 1 while establishing the foundation for future development phases.
