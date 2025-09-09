# PromptCraft Hybrid Infrastructure Deployment Guide

## Overview

The PromptCraft Hybrid Infrastructure provides intelligent discovery and deployment of MCP servers and agents with flexible resource management and anti-duplication strategies.

## Architecture

### Intelligent Discovery System

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Level    │    │  Project Level  │    │   Production    │
│ ~/.claude/      │───▶│   .mcp/         │───▶│   Docker        │
│   agents/       │    │   .agents/      │    │   Services      │
│   mcp/          │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Discovery Priority Order

1. **External Deployments** - Existing running services
2. **User Installations** - Developer's local setup  
3. **Project Configurations** - Bundled definitions
4. **Docker Services** - Containerized fallbacks
5. **NPX Cloud** - Cloud-based services

## Quick Start

### 1. Basic Deployment

```bash
# Clone and setup
git clone <repository>
cd PromptCraft
cp .env.template .env

# Deploy with intelligent discovery
./scripts/deploy-hybrid.sh
```

### 2. Development with External Services

```bash
# If you have zen-mcp-server running locally
# The system will automatically detect and use it

# Start only PromptCraft (will discover external services)
docker-compose -f docker-compose.hybrid.yml up promptcraft
```

### 3. Full Embedded Deployment

```bash
# Deploy everything locally
./scripts/deploy-hybrid.sh --monitoring
```

### 4. Production Deployment

```bash
# Production mode with load balancer
./scripts/deploy-hybrid.sh --production --monitoring
```

## Configuration

### Environment Variables

Create `.env` file with:

```bash
# External Services
QDRANT_HOST=192.168.1.16
QDRANT_PORT=6333
ZEN_MCP_URL=http://localhost:8000

# Resource Limits
MAX_CONCURRENT_AGENTS=10
AGENT_MEMORY_LIMIT=2048
MCP_RESOURCE_LIMIT=1024

# API Keys
UPSTASH_REDIS_REST_URL=your_upstash_url
UPSTASH_REDIS_REST_TOKEN=your_token
PERPLEXITY_API_KEY=your_key
SENTRY_AUTH_TOKEN=your_token

# Deployment
ENVIRONMENT=production
ENABLE_MONITORING=true
GRAFANA_PASSWORD=secure_password
```

### MCP Server Configuration

Edit `.mcp/discovery-config.yaml`:

```yaml
servers:
  zen-mcp:
    priority_order:
      1: external_deployment    # Your existing server
      2: user_installation      # ~/dev/zen-mcp-server
      3: docker_sidecar         # Docker container
    
    resource_requirements:
      memory_mb: 512
      cpu_cores: 0.5
```

### Agent Configuration

Edit `.agents/discovery-config.yaml`:

```yaml
agents:
  ai-engineer:
    priority_order:
      - project_specific   # Use project implementation
      - user_override      # Allow user customization
    
    dependencies:
      services:
        qdrant: "192.168.1.16:6333"
        zen_mcp: "auto_discover"
```

## Deployment Scenarios

### Scenario 1: Full Local Development

Perfect for developers working on PromptCraft core.

```bash
# Prerequisites: Docker, docker-compose
./scripts/deploy-hybrid.sh --build

# Services included:
# - PromptCraft (main app)
# - Redis (caching)
# - Zen MCP Server (if not external)
# - Qdrant (if not external)
```

**Resource Usage**: ~2GB RAM, 10GB disk

### Scenario 2: Hybrid Development

For developers with some external services.

```bash
# External Qdrant at 192.168.1.16:6333
# External Zen MCP at localhost:8000
export QDRANT_HOST=192.168.1.16
export ZEN_MCP_URL=http://localhost:8000

./scripts/deploy-hybrid.sh
```

**Resource Usage**: ~1GB RAM, 5GB disk

### Scenario 3: Production Deployment

Full production setup with monitoring and load balancing.

```bash
# Production environment
export ENVIRONMENT=production
export ENABLE_MONITORING=true

./scripts/deploy-hybrid.sh --production --monitoring

# Additional services:
# - Nginx (load balancer)
# - Prometheus (metrics)
# - Grafana (dashboards)
```

**Resource Usage**: ~4GB RAM, 20GB disk

### Scenario 4: Cloud/NPX Focused

Minimal local resources, maximum cloud usage.

```yaml
# .mcp/discovery-config.yaml
servers:
  context7:
    priority_order:
      1: npx_cloud  # Always prefer cloud
  
  perplexity:
    priority_order:
      1: npx_cloud  # Cloud-first
```

**Resource Usage**: ~500MB RAM, 2GB disk

## Service Discovery

### MCP Servers

The system automatically detects:

1. **Port Scanning**: Checks common ports (8000, 8001, 8002)
2. **Process Detection**: Looks for running server processes
3. **Environment Variables**: Checks for service URLs
4. **Lock Files**: Finds existing server instances
5. **Docker Containers**: Scans running containers

### Agents

The system searches in order:

1. **User Overrides**: `~/.claude/agents/` (your customizations)
2. **Project Core**: `.agents/core/` (essential agents)
3. **Project Specific**: `.agents/project/` (app-specific)
4. **Bundled Defaults**: `.agents/defaults/` (fallbacks)

## Resource Management

### Memory Management

```yaml
# Global limits
resource_limits:
  total_memory_mb: 2048
  max_concurrent_agents: 10
  model_limits:
    opus: 3
    sonnet: 8
    haiku: 15
```

### CPU Management

Each service has defined CPU limits:
- PromptCraft: 2.0 cores max
- Zen MCP: 0.5 cores max
- Qdrant: 1.0 cores max
- Redis: 0.2 cores max

### Anti-Duplication

The system prevents duplicate services through:

1. **Lock Files**: `/tmp/.mcp-{service}.lock`
2. **Port Checks**: Verifies service availability
3. **Health Checks**: Confirms service responsiveness
4. **Resource Tracking**: Monitors active instances

## Monitoring and Observability

### Health Endpoints

- PromptCraft: `http://localhost:7860/health`
- PromptCraft API: `http://localhost:7862/health`
- Zen MCP: `http://localhost:8000/health`
- Qdrant: `http://localhost:6333/health`

### Metrics Collection

With `--monitoring` flag:
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000`

Key metrics:
- Agent execution times
- MCP server response rates
- Memory and CPU usage
- Request throughput
- Error rates

### Logging

Centralized logging with structured format:

```bash
# View all logs
docker-compose -f docker-compose.hybrid.yml logs -f

# Service-specific logs
docker-compose -f docker-compose.hybrid.yml logs -f promptcraft
docker-compose -f docker-compose.hybrid.yml logs -f zen-mcp
```

## Troubleshooting

### Common Issues

#### 1. Service Discovery Failures

```bash
# Check discovery status
curl http://localhost:7862/api/discovery/status

# Manual service check
curl http://localhost:8000/health  # Zen MCP
curl http://192.168.1.16:6333/health  # Qdrant
```

#### 2. Resource Exhaustion

```bash
# Check resource usage
docker stats

# Adjust limits in .env
MAX_CONCURRENT_AGENTS=5
AGENT_MEMORY_LIMIT=1024
```

#### 3. Agent Loading Issues

```bash
# Check agent discovery
curl http://localhost:7862/api/agents/available

# Verify agent configurations
ls -la .agents/core/
ls -la .agents/project/
```

#### 4. MCP Server Connection Issues

```bash
# Check MCP server status
curl http://localhost:8000/health

# Verify configuration
cat .mcp/discovery-config.yaml
```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.hybrid.yml up
```

## Security Considerations

### Network Security

- Internal Docker network isolation
- External service authentication
- API key management through environment variables

### Container Security

- Non-root user execution
- Read-only filesystems where possible
- Resource limits and constraints
- Security context configuration

### Secret Management

```bash
# Use Docker secrets for production
echo "your_api_key" | docker secret create perplexity_key -

# Or encrypted .env files
gpg --symmetric --cipher-algo AES256 .env
```

## Scaling and Performance

### Horizontal Scaling

```yaml
# docker-compose.hybrid.yml
services:
  promptcraft:
    deploy:
      replicas: 3
```

### Load Balancing

Nginx configuration included for production deployments:

```nginx
upstream promptcraft {
    server promptcraft:7860;
    server promptcraft:7861;
    server promptcraft:7862;
}
```

### Caching Strategy

- Redis for session and response caching
- Qdrant for vector embeddings
- Agent result caching with TTL

## Migration Guide

### From User-Level to Project-Level

1. **Backup existing configurations**:
   ```bash
   cp -r ~/.claude/agents ~/.claude/agents.backup
   cp -r ~/.claude/mcp ~/.claude/mcp.backup
   ```

2. **Copy important customizations**:
   ```bash
   cp ~/.claude/agents/my-custom-agent.md .agents/project/
   cp ~/.claude/mcp/my-server.json .mcp/servers/
   ```

3. **Update references**:
   - Agent definitions automatically cascade
   - MCP configurations merge intelligently
   - No code changes required

4. **Test discovery**:
   ```bash
   ./scripts/deploy-hybrid.sh
   # Check that your customizations are detected
   ```

### From Docker to Hybrid

1. **Update compose file**:
   ```bash
   mv docker-compose.yml docker-compose.legacy.yml
   ln -s docker-compose.hybrid.yml docker-compose.yml
   ```

2. **Migrate configurations**:
   - Environment variables remain compatible
   - Volume mounts automatically adjusted
   - Service discovery handles transitions

3. **Deploy with discovery**:
   ```bash
   ./scripts/deploy-hybrid.sh
   ```

## Best Practices

### Development

1. **Use External Services**: Let the system discover your existing services
2. **Override Selectively**: Only customize what you need to change
3. **Monitor Resources**: Keep an eye on memory and CPU usage
4. **Test Discovery**: Verify service detection works as expected

### Production

1. **External Dependencies**: Use dedicated infrastructure for Qdrant/Redis
2. **Resource Limits**: Set appropriate memory and CPU constraints
3. **Health Monitoring**: Enable comprehensive health checks
4. **Backup Strategy**: Regular backups of configurations and data

### Security

1. **API Keys**: Use environment variables or Docker secrets
2. **Network Isolation**: Leverage Docker networks for service isolation
3. **Regular Updates**: Keep base images and dependencies updated
4. **Access Control**: Implement appropriate authentication and authorization

## Support and Maintenance

### Regular Maintenance

```bash
# Update images
docker-compose -f docker-compose.hybrid.yml pull

# Clean up unused resources
docker system prune -f

# Backup configurations
tar -czf backup-$(date +%Y%m%d).tar.gz .mcp .agents .env
```

### Monitoring Health

```bash
# Automated health check
./scripts/health-check.sh

# Manual verification
curl http://localhost:7862/api/health/detailed
```

This hybrid infrastructure approach ensures maximum flexibility while maintaining simplicity and preventing resource conflicts.