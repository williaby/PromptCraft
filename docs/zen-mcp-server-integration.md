# Zen MCP Server Fork Integration

This document describes the integration of the `williaby/zen-mcp-server` fork into the PromptCraft project.

## Overview

PromptCraft now includes your forked Zen MCP Server as an integrated component, providing complete control
over the AI agent orchestration layer while maintaining the sophisticated routing and fallback capabilities
already built into the system.

## Integration Strategy

### Architecture

- **Git Submodule**: Zen MCP Server fork added as submodule for version control
- **Docker Integration**: Fully integrated into docker-compose.zen-vm.yaml
- **Service-Oriented**: Maintains proper service separation while enabling single-command startup

### Key Benefits

1. **Full Control**: Own fork enables PromptCraft-specific customizations
2. **Version Consistency**: Submodule ensures exact version coordination
3. **Development Efficiency**: Single `make dev` command runs everything
4. **CI/CD Ready**: Automated testing against your specific fork

## Changes Made

### 1. Configuration Updates

- ✅ **testing/.mcp.json**: Updated to point to `williaby/zen-mcp-server`
- ✅ **.mcp.json**: Added complete server configuration with API key support

### 2. Infrastructure Integration

- ✅ **Git Submodule**: Added zen-mcp-server as submodule
- ✅ **Docker Compose**: Integrated zen-mcp-server service with proper networking
- ✅ **Makefile**: Updated to reflect integrated setup

### 3. Documentation Cleanup

- ✅ **Module Documentation**: Clarified component roles in `__init__.py`
- ✅ **Legacy Deprecation**: Marked legacy `client.py` as deprecated

## Usage

### Development Workflow

```bash
# Start entire development environment (including zen-mcp-server)
make dev

# Access services:
# - Gradio UI: http://127.0.0.1:7860 (Journeys 1, 2, 4)
# - FastAPI Backend: http://127.0.0.1:8000 (API endpoints)
# - Zen MCP Server: http://127.0.0.1:3000 (AI Agent Orchestration)
# - Code-Server IDE: http://127.0.0.1:8080 (Journey 3)
```

### Submodule Management

```bash
# Update submodule to latest
git submodule update --remote zen-mcp-server

# Work on zen-mcp-server
cd zen-mcp-server
# Make changes...
git add . && git commit -m "Custom changes"
git push origin main

# Update PromptCraft to use new version
cd ..
git add zen-mcp-server
git commit -m "Update zen-mcp-server to latest version"
```

## Docker Service Configuration

The zen-mcp-server service includes:

- **Port**: 3000 (localhost only for cloudflared tunnel)
- **Resources**: 1.5 CPU / 3GB memory (production-ready)
- **Security**: Non-root user, no-new-privileges, minimal capabilities
- **Health Checks**: Automatic health monitoring with retry logic
- **Environment**: Full API key support (OpenAI, Gemini, Anthropic, OpenRouter)

## MCP Client Architecture

PromptCraft's sophisticated MCP integration provides:

### Primary Components

- **HybridRouter**: Main entry point with intelligent routing
- **ZenMCPClient**: Direct Zen MCP Server integration
- **MCPClientFactory**: Configuration-driven client creation

### Advanced Features

- Circuit breaker protection for OpenRouter
- Gradual rollout capabilities (0-100% traffic routing)
- Comprehensive metrics and monitoring
- Multiple routing strategies (primary, round-robin, load-balanced, capability-based)
- Fallback mechanisms between services

## Development Benefits

### Before Integration

- Manual zen-mcp-server setup required
- Version coordination challenges
- Complex developer onboarding
- Separate service management

### After Integration

- Single `make dev` command starts everything
- Automatic version consistency
- Simplified developer experience
- Unified service management
- Testing against your specific fork

## Next Steps

1. **Customization**: Add PromptCraft-specific tools to zen-mcp-server
2. **Testing**: Validate integration with existing test suite
3. **CI/CD**: Update deployment pipelines for integrated setup
4. **Monitoring**: Leverage existing health check infrastructure

## Technical Notes

### Service Dependencies

The zen-mcp-server service depends on:

- Redis (for shared state)
- Network connectivity for API providers
- Environment variables for API keys

### Health Monitoring

- Health checks every 30 seconds
- 40-second startup grace period
- 3 retry attempts before marking unhealthy
- Integrates with PromptCraft's monitoring system

### Security

- Non-root user (1000:1000)
- Minimal Linux capabilities
- no-new-privileges security option
- Localhost-only binding for tunnel routing

This integration maintains PromptCraft's architectural excellence while providing complete control
over the Zen MCP Server orchestration layer.
