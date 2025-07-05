---
title: "GitHub Workflows Implementation Plan"
version: "1.0"
status: "draft"
component: "Planning"
tags: ["workflows", "ci-cd", "implementation", "security", "multi-agent"]
source: "PromptCraft-Hybrid Project"
purpose: "Comprehensive implementation plan for GitHub workflow modernization based on expert consensus analysis."
---

# GitHub Workflows Implementation Plan

This document provides detailed implementation guidance for modernizing PromptCraft's CI/CD pipeline based on analysis of ledgerbase workflows and expert consensus from three AI models: Gemini 2.5 Pro, DeepSeek R1, and Claude Opus 4.

## Executive Summary

**Strategy**: "Augment and Unify" approach over wholesale replacement
**Timeline**: 4-week phased implementation
**Priority**: Security gaps (secrets scanning) as critical first target
**Architecture**: Nox-based script standardization with flat workflow structure

## Expert Consensus Analysis

### Model Responses Summary

**Gemini 2.5 Pro Recommendations**:
- Prioritize security gaps, especially secrets scanning (currently missing)
- Progressive enhancement with feature flags to minimize disruption
- Nox session standardization for complex logic
- Service virtualization for multi-agent testing

**DeepSeek R1 Analysis**:
- "Augment and Unify" strategy over replacement
- Ledgerbase patterns complement PromptCraft's superior renovate implementation
- Secrets scanning identified as critical security gap
- Emphasis on maintaining existing strengths

**Claude Opus 4 Validation**:
- Confirmed security-first approach with progressive rollout
- Endorsed service virtualization for hybrid architecture
- Recommended 4-week timeline with checkpoint reviews
- Emphasized risk mitigation through fallback options

### Unanimous Recommendations

1. **Security First**: Address secrets scanning gap immediately
2. **Progressive Enhancement**: Use feature flags for gradual rollout
3. **Preserve Strengths**: Keep PromptCraft's superior renovate-auto-merge.yml
4. **Nox Standardization**: Move complex logic to nox sessions
5. **Service Virtualization**: Enable fast PR testing with mocked MCP services

## Detailed Implementation Plan

### Phase 1: Workflow Architecture Modernization (Issue #41)
**Timeline**: Week 1
**Priority**: Foundation

#### Enhanced Noxfile Structure

```python
# Enhanced noxfile.py structure
import nox
from pathlib import Path

# Development workflow sessions
@nox.session(python=["3.11", "3.12"])
def dev_checks_format(session):
    """Run formatting checks for development workflow"""
    session.install("black", "ruff", "mypy")
    session.run("black", "--check", ".")
    session.run("ruff", "check", ".")
    session.run("mypy", "src")

@nox.session
def dev_checks_docs(session):
    """Run documentation linting"""
    session.install("markdownlint-cli", "yamllint")
    session.run("markdownlint", "**/*.md")
    session.run("yamllint", "**/*.{yml,yaml}")

# Security workflow sessions
@nox.session
def security_scan_secrets(session):
    """Run secrets scanning with gitleaks"""
    session.install("gitleaks")
    session.run("gitleaks", "detect", "--source", ".", "--verbose")

@nox.session
def security_scan_bandit(session):
    """Run Python security analysis"""
    session.install("bandit[toml]")
    session.run("bandit", "-r", "src/", "-f", "sarif", "-o", "bandit-results.sarif")

@nox.session
def security_scan_trivy(session):
    """Run container security scanning"""
    session.run("trivy", "image", "--format", "sarif", "--output", "trivy-results.sarif", "promptcraft:latest")

@nox.session
def security_scan_semgrep(session):
    """Run SAST with custom rules"""
    session.install("semgrep")
    session.run("semgrep", "--config=auto", "--sarif", "--output=semgrep-results.sarif", "src/")

@nox.session
def security_scan_comprehensive(session):
    """Run all security scans"""
    session.notify("security_scan_secrets")
    session.notify("security_scan_bandit")
    session.notify("security_scan_trivy")
    session.notify("security_scan_semgrep")

# Multi-agent testing sessions
@nox.session
def mcp_test_mock(session):
    """Test with mocked MCP services for fast PR validation"""
    session.install("pytest", "pytest-mock", "docker-compose")
    session.run("docker-compose", "-f", "docker-compose.test.yml", "up", "-d")
    session.run("pytest", "tests/integration/", "-m", "mcp_mock")
    session.run("docker-compose", "-f", "docker-compose.test.yml", "down")

@nox.session
def mcp_test_integration(session):
    """Test with real MCP services for main branch validation"""
    session.install("pytest", "docker-compose")
    session.run("docker-compose", "-f", "docker-compose.mcp.yml", "up", "-d")
    session.run("pytest", "tests/integration/", "-m", "mcp_integration")
    session.run("docker-compose", "-f", "docker-compose.mcp.yml", "down")

@nox.session
def mcp_contract_test(session):
    """Run contract testing for agent communication"""
    session.install("pytest", "pactman")
    session.run("pytest", "tests/contracts/", "-v")

@nox.session
def mcp_performance_benchmark(session):
    """Run performance benchmarks for multi-agent coordination"""
    session.install("pytest", "pytest-benchmark")
    session.run("pytest", "tests/performance/", "--benchmark-only")
```

#### Feature Flag Implementation

```yaml
# config/feature-flags.yaml
workflow_features:
  enhanced_security_scanning:
    enabled: false
    rollout_percentage: 0
    description: "Enhanced security scanning with multiple tools"

  multi_agent_testing:
    enabled: false
    rollout_percentage: 0
    description: "Service virtualization for multi-agent testing"

  performance_gates:
    enabled: false
    rollout_percentage: 0
    description: "Performance monitoring with rollback triggers"
```

#### Workflow Testing Framework

```bash
# Local workflow testing with nektos/act
# Install act: https://github.com/nektos/act

# Test all workflows locally
act -l  # List available workflows
act -n  # Dry run all workflows

# Test specific workflows
act pull_request  # Test PR workflows
act push         # Test push workflows

# Test with secrets (create .secrets file)
act -s GITHUB_TOKEN=your_token pull_request
```

### Phase 2: Enterprise Security Workflow Suite (Issue #42)
**Timeline**: Week 2
**Priority**: Critical Security Gaps

#### Security Tool Priority Implementation

**Week 2.1 (Critical - Days 1-3)**:
```yaml
# Enhanced CI workflow with secrets scanning
name: Enhanced CI with Security

on:
  pull_request:
  push:
    branches: [main]

jobs:
  security-critical:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for gitleaks

      - name: Secrets Scanning
        run: nox -s security_scan_secrets

      - name: Container Security Scan
        run: nox -s security_scan_trivy

      - name: Enhanced Dependency Scan
        run: |
          nox -s security_scan_bandit
          poetry run safety check --json --output safety-results.json
```

**Week 2.2 (Secondary - Days 4-7)**:
```yaml
  security-comprehensive:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: SAST with Custom Rules
        run: nox -s security_scan_semgrep

      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          languages: python, javascript
          queries: security-extended

      - name: SLSA Provenance Generation
        uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0
        with:
          base64-subjects: ${{ needs.build.outputs.hashes }}
```

#### SARIF Report Integration

```yaml
  upload-sarif:
    runs-on: ubuntu-latest
    needs: [security-critical, security-comprehensive]
    if: always()
    steps:
      - name: Upload Security Results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: |
            bandit-results.sarif
            trivy-results.sarif
            semgrep-results.sarif
          category: security-analysis
```

### Phase 3: Multi-Agent Workflow Integration (Issue #43)
**Timeline**: Week 3
**Priority**: Hybrid Architecture Support

#### Service Virtualization Strategy

```yaml
# Service virtualization for different testing contexts
test-strategy:
  pull_request:
    # Fast feedback with mocked services
    mcp_testing: mock
    timeout: 10m
    services:
      - heimdall-mock
      - github-mock
      - zen-mock

  main_branch:
    # Full validation with real services
    mcp_testing: integration
    timeout: 30m
    services:
      - heimdall-mcp
      - github-mcp
      - zen-mcp

  release:
    # Performance and resilience testing
    mcp_testing: performance
    timeout: 60m
    includes:
      - chaos_engineering
      - load_testing
      - security_scanning
```

#### Docker Compose Test Configurations

```yaml
# docker-compose.test.yml - Fast PR testing
version: '3.8'
services:
  heimdall-mock:
    image: mockserver/mockserver:latest
    environment:
      MOCKSERVER_PROPERTY_FILE: /config/heimdall-mock.properties
    volumes:
      - ./tests/mocks/heimdall-config:/config
    ports:
      - "3001:1080"

  github-mock:
    image: mockserver/mockserver:latest
    environment:
      MOCKSERVER_PROPERTY_FILE: /config/github-mock.properties
    volumes:
      - ./tests/mocks/github-config:/config
    ports:
      - "3002:1080"

# docker-compose.mcp.yml - Full integration testing
version: '3.8'
services:
  heimdall-mcp:
    image: heimdall-mcp:latest
    environment:
      - MCP_PORT=3001
      - SECURITY_PROFILE=testing
    ports:
      - "3001:3001"

  github-mcp:
    image: github-mcp:latest
    environment:
      - MCP_PORT=3002
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    ports:
      - "3002:3002"
```

#### Contract Testing Implementation

```python
# tests/contracts/test_agent_contracts.py
import pytest
from pactman import Consumer, Provider, Like, Term

@pytest.fixture
def security_agent_contract():
    return Consumer('security-agent').has_pact_with(
        Provider('heimdall-mcp'),
        pact_dir='tests/contracts/pacts'
    )

def test_security_scan_contract(security_agent_contract):
    # Define expected contract
    expected = {
        "scan_id": Like("abc123"),
        "status": Term(r"queued|running|completed|failed", "completed"),
        "findings": Like([]),
        "cvss_summary": Like({"max_score": 7.5})
    }

    # Set up interaction
    security_agent_contract.given(
        'A security scan request'
    ).upon_receiving(
        'A scan results request'
    ).with_request(
        method='GET',
        path='/scans/abc123',
        headers={'Content-Type': 'application/json'}
    ).will_respond_with(200, body=expected)

    # Test the contract
    with security_agent_contract:
        client = HeimdallMCPClient()
        result = client.get_scan_results("abc123")
        assert result.status in ["queued", "running", "completed", "failed"]
```

### Phase 4: Testing and Validation (Week 4)
**Timeline**: Week 4
**Priority**: Quality Assurance

#### Performance Benchmarking

```python
# tests/performance/test_workflow_performance.py
import pytest
import time
from unittest.mock import patch

@pytest.mark.benchmark
def test_security_scan_performance(benchmark):
    """Security scanning should complete within 5 minutes"""
    def run_security_scan():
        # Mock security scan execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            # Simulate security scan
            time.sleep(0.1)  # Simulate processing time
            return True

    result = benchmark(run_security_scan)
    assert result is True
    # Performance assertion: <5 minutes (300 seconds)
    assert benchmark.stats['mean'] < 300

@pytest.mark.benchmark
def test_mcp_coordination_performance(benchmark):
    """Multi-agent coordination should complete within 2 seconds"""
    def coordinate_agents():
        # Mock agent coordination
        agents = ["security", "web_dev", "tax"]
        for agent in agents:
            time.sleep(0.05)  # Simulate agent communication
        return len(agents)

    result = benchmark(coordinate_agents)
    assert result == 3
    # Performance target: <2s for agent coordination
    assert benchmark.stats['mean'] < 2.0
```

#### Integration Testing Suite

```bash
# tests/integration/test_complete_workflows.py
pytest tests/integration/test_github_workflows.py -v
pytest tests/integration/test_security_workflows.py -v
pytest tests/integration/test_multi_agent_workflows.py -v

# Performance validation
pytest tests/performance/ --benchmark-only --benchmark-min-time=1

# Contract testing validation
pytest tests/contracts/ -v --pact-broker-url=http://localhost:9292
```

## Risk Mitigation Strategy

### Graduated Fallback Plans

**Plan A (Ideal)**: Full distributed multi-agent architecture
- 6 MCP services running independently
- Service mesh with circuit breakers
- Complete observability stack

**Plan B (Reduced)**: Core 4 MCP services
- Combine secondary services into primary ones
- Reduced complexity while maintaining core functionality
- Faster deployment and easier management

**Plan C (Simplified)**: 2 MCP services
- Zen MCP + Heimdall MCP only
- Basic multi-agent capabilities
- Minimal complexity deployment

**Plan D (Emergency)**: Monolithic fallback
- Single container deployment
- All functionality in one service
- Maximum compatibility and reliability

### Rollback Procedures

```bash
# Automated rollback script
#!/bin/bash
# scripts/workflow-rollback.sh

set -euo pipefail

ROLLBACK_TARGET=${1:-"previous-version"}

echo "🔄 Initiating workflow rollback to: $ROLLBACK_TARGET"

# 1. Disable feature flags
yq eval '.workflow_features.*.enabled = false' -i config/feature-flags.yaml

# 2. Revert to backup workflows
cp .github/workflows-backup/*.yml .github/workflows/

# 3. Clear problematic caches
gh api repos/:owner/:repo/actions/caches --delete

# 4. Trigger verification workflow
gh workflow run "CI" --ref main

echo "✅ Rollback completed. Monitoring for 10 minutes..."
sleep 600

# 5. Validate rollback success
WORKFLOW_STATUS=$(gh run list --workflow="CI" --limit=1 --json status --jq '.[0].status')
if [ "$WORKFLOW_STATUS" = "completed" ]; then
    echo "✅ Rollback verification successful"
    exit 0
else
    echo "❌ Rollback verification failed"
    exit 1
fi
```

### Emergency Recovery

```bash
# Emergency recovery procedures
#!/bin/bash
# scripts/emergency-recovery.sh

echo "🚨 Emergency Recovery Mode Activated"

# 1. Switch to monolithic deployment
docker-compose -f docker-compose.monolithic.yml up -d

# 2. Bypass all CI/CD checks (emergency only)
git config core.hooksPath /dev/null

# 3. Deploy minimal working version
docker run -d -p 7860:7860 promptcraft:minimal

# 4. Notify stakeholders
curl -X POST "$SLACK_WEBHOOK" -d '{"text":"🚨 PromptCraft Emergency Recovery Mode Active"}'

echo "✅ Emergency recovery deployment complete"
```

## Performance Targets and Monitoring

### Key Performance Indicators

| Metric | Target | Monitoring |
|--------|--------|------------|
| Agent Coordination | <2s | Prometheus metrics |
| Multi-agent Consensus | <15s | Application logs |
| Security Scan Complete | <5min | GitHub Actions |
| Workflow Pipeline Total | <10min | GitHub Actions |
| Container Startup | <30s | Health checks |
| Memory Usage per Agent | <2GB | Docker stats |

### Monitoring Implementation

```yaml
# Prometheus monitoring configuration
monitoring:
  metrics:
    - name: workflow_duration_seconds
      type: histogram
      help: "Duration of GitHub workflow executions"
      labels: [workflow_name, branch, status]

    - name: agent_coordination_duration_seconds
      type: histogram
      help: "Time taken for multi-agent coordination"
      labels: [agent_count, task_type, success]

    - name: security_scan_findings_total
      type: counter
      help: "Total security findings by severity"
      labels: [severity, tool, repository]

  alerts:
    - name: WorkflowFailureRate
      expr: rate(workflow_failures_total[5m]) > 0.1
      severity: warning
      description: "Workflow failure rate exceeds 10%"

    - name: AgentCoordinationSlow
      expr: histogram_quantile(0.95, agent_coordination_duration_seconds) > 5
      severity: critical
      description: "95th percentile agent coordination >5s"
```

## Implementation Checklist

### Week 1: Foundation
- [ ] Enhanced `noxfile.py` with comprehensive sessions
- [ ] Feature flag system implementation
- [ ] Workflow testing framework with nektos/act
- [ ] Matrix strategy enhancement for multi-Python testing
- [ ] Performance gates with rollback triggers
- [ ] Documentation for new workflow architecture

### Week 2: Security
- [ ] Secrets scanning integration (gitleaks/trufflehog)
- [ ] Container security scanning (Trivy)
- [ ] Enhanced dependency scanning (Safety + pip-audit)
- [ ] SAST with custom rules (Semgrep)
- [ ] CodeQL comprehensive analysis
- [ ] SARIF report aggregation and upload

### Week 3: Multi-Agent
- [ ] Service virtualization framework
- [ ] Contract testing implementation
- [ ] Self-hosted runner configuration
- [ ] Staged end-to-end testing
- [ ] Network resilience testing with toxiproxy
- [ ] Performance benchmarking baseline

### Week 4: Validation
- [ ] Complete integration testing
- [ ] Performance validation against targets
- [ ] Security scanning validation
- [ ] Rollback procedure testing
- [ ] Emergency recovery validation
- [ ] Documentation finalization

## Configuration Templates

### GitHub Secrets Required

```bash
# Security scanning secrets
ASSURED_OSS_SERVICE_ACCOUNT  # Google Cloud service account JSON
ASSURED_OSS_PROJECT_ID       # Google Cloud project ID
GITLEAKS_LICENSE            # Optional: gitleaks enterprise license

# Multi-agent testing secrets
HEIMDALL_API_KEY            # Heimdall MCP authentication
GITHUB_MCP_TOKEN            # GitHub MCP access token
ZEN_MCP_ENDPOINT            # Zen MCP server endpoint

# Monitoring secrets
PROMETHEUS_WEBHOOK          # Prometheus alertmanager webhook
SLACK_WEBHOOK              # Emergency notification webhook
```

### Environment Variables

```bash
# Feature flag environment variables
WORKFLOW_ENHANCED_SECURITY=false
WORKFLOW_MULTI_AGENT_TESTING=false
WORKFLOW_PERFORMANCE_GATES=false

# Performance monitoring
PERFORMANCE_TARGET_COORDINATION=2000  # milliseconds
PERFORMANCE_TARGET_CONSENSUS=15000    # milliseconds
PERFORMANCE_TARGET_SECURITY=300000    # milliseconds (5 minutes)
```

## Success Criteria

### Technical Success Metrics
- [ ] All 43 phase issues successfully implemented with new workflow support
- [ ] Security scanning coverage >95% with zero critical gaps
- [ ] Multi-agent coordination performance <2s (95th percentile)
- [ ] Workflow pipeline completion time <10 minutes
- [ ] Zero security vulnerabilities in production deployment
- [ ] Successful fallback testing for all 4 contingency plans

### Operational Success Metrics
- [ ] Developer productivity maintained during transition
- [ ] Zero production incidents related to workflow changes
- [ ] 100% rollback capability validation
- [ ] Emergency recovery procedures tested and documented
- [ ] Team training completed on new workflow architecture
- [ ] Performance monitoring and alerting fully operational

## Conclusion

This implementation plan provides a comprehensive roadmap for modernizing PromptCraft's CI/CD pipeline based on expert consensus analysis. The phased approach minimizes risk while addressing critical security gaps and enabling advanced multi-agent testing capabilities.

**Key Success Factors**:
1. **Security First**: Immediate attention to secrets scanning gap
2. **Progressive Enhancement**: Feature flags enable safe rollout
3. **Preserve Strengths**: Maintain PromptCraft's superior renovate automation
4. **Risk Mitigation**: Multiple fallback options and tested recovery procedures
5. **Performance Focus**: Clear targets with monitoring and alerting

The plan balances innovation with stability, ensuring PromptCraft's CI/CD pipeline becomes a competitive advantage while maintaining operational excellence.
