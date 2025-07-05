# **PromptCraft-Hybrid: Journey 3 Light Setup Guide**

Version: 2.0
Status: Updated for Enhanced Phase 1
Audience: Developers, Early Adopters

## **Overview**

Journey 3 Light brings AI-powered development directly into your IDE through Claude Code CLI. With the enhanced Phase 1 stack now being deployed on Unraid, developers will have access to sophisticated capabilities including natural language processing, GitHub integration, sequential thinking, and persistent memory.

### **What's New in Enhanced Phase 1**

The Phase 1 deployment (just started) includes:
- **Serena MCP**: Advanced natural language understanding
- **GitHub MCP**: Direct repository integration
- **Sequential Thinking MCP**: Step-by-step problem solving
- **FileSystem MCP**: Safe file operations
- **Qdrant Memory MCP**: Persistent context across sessions
- **Zen Orchestrator**: Intelligent routing between all MCPs

## **Current Status**

⚠️ **Note**: Enhanced Phase 1 deployment has just begun. This guide covers both:
1. What's available immediately (public MCPs via Zen)
2. What's coming as the Unraid deployment completes

### **Available Now**
- Claude Code CLI with public MCP access
- Google, DuckDuckGo, and URL reader tools
- Basic Zen orchestration

### **Coming Soon (Phase 1 Deployment)**
- Full 6-container MCP stack on Unraid
- Enhanced capabilities described in this guide
- Local network access to all MCPs

## **Prerequisites**

### **For Immediate Use (Public MCPs)**
- Claude Code CLI installed
- Internet connection
- Terminal access

### **For Full Phase 1 (In Progress)**
- Access to Unraid server (36GB RAM)
- Local network connectivity
- Docker containers deployed
- VPN access (for remote users)

## **Installation Guide**

### **Step 1: Install Claude Code CLI**

```bash
# Install via npm (recommended)
npm install -g claude-code-cli

# Or via curl
curl -fsSL https://claude.ai/install.sh | sh

# Verify installation
claude --version
```

### **Step 2: Configure for Public MCPs (Available Now)**

```bash
# Initialize configuration
claude init

# Set up API key
claude config set api_key YOUR_ANTHROPIC_KEY

# Enable public MCPs
claude config set mcp_mode public

# Test connection
claude "test connection"
```

### **Step 3: Configure for Unraid Server (When Deployed)**

```bash
# Set Unraid server endpoint
claude config set server_endpoint http://unraid.local:8080

# Or use IP address
claude config set server_endpoint http://192.168.1.100:8080

# Configure network access
claude config set network_mode local

# For remote access via VPN
claude config set server_endpoint https://vpn.company.com:8080
claude config set auth_token YOUR_AUTH_TOKEN
```

## **Network Configuration**

### **Local Network Access**

For developers on the same network as the Unraid server:

```yaml
# ~/.claude/config.yaml
network:
  mode: local
  server: unraid.local
  port: 8080
  timeout: 30
  retry: 3

mcp_endpoints:
  zen: http://unraid.local:8080
  qdrant: http://unraid.local:6333
  serena: http://unraid.local:8081
  github: http://unraid.local:8082
  sequential: http://unraid.local:8083
  filesystem: http://unraid.local:8084
```

### **Remote Access Configuration**

For developers working remotely:

```yaml
# ~/.claude/config.yaml
network:
  mode: remote
  vpn_required: true
  server: vpn.company.com
  port: 443
  auth: token

security:
  ssl: true
  verify_cert: true
  auth_token: ${CLAUDE_AUTH_TOKEN}
```

### **Laptop-to-Unraid Connection Testing**

```bash
# Test basic connectivity
ping unraid.local

# Test MCP endpoints
claude test connectivity

# Verbose mode for troubleshooting
claude test connectivity --verbose

# Check specific MCP
claude test mcp serena
```

## **Using Journey 3 Light**

### **Currently Available Commands**

```bash
# Web search via public MCPs
claude search "latest React best practices"

# URL content extraction
claude read "https://example.com/article"

# Basic query enhancement
claude enhance "write unit tests for auth module"
```

### **Enhanced Commands (After Phase 1 Deployment)**

```bash
# Sequential thinking for complex problems
claude think "design a scalable microservices architecture"

# GitHub integration
claude analyze repo "https://github.com/user/project"
claude review pr 123

# Natural language enhancement with Serena
claude explain "what does this regex do: /^(?=.*[A-Z])(?=.*[!@#$%^&*])/g"

# File operations
claude create project "my-new-app" --template react
claude update file "src/auth.js" --add-tests

# Using persistent memory
claude remember "project uses PostgreSQL with Prisma ORM"
claude recall "database setup"
```

## **Multi-MCP Workflows**

### **Example: Complex Code Generation**

```bash
# This workflow will use multiple MCPs automatically
claude create feature "user authentication with JWT"

# Behind the scenes:
# 1. Sequential Thinking plans the implementation
# 2. GitHub MCP checks for existing patterns in your repo
# 3. Serena enhances understanding of requirements
# 4. FileSystem MCP creates the necessary files
# 5. Qdrant stores the context for future reference
```

### **Example: Repository Analysis**

```bash
# Analyze and improve existing code
claude analyze codebase --suggest-improvements

# The system will:
# 1. Use GitHub MCP to scan repository structure
# 2. Sequential Thinking to identify improvement areas
# 3. Serena to generate clear explanations
# 4. Create a comprehensive report
```

## **Testing Your Setup**

### **Basic Connectivity Test**

```bash
# Test all MCPs
claude test all

# Expected output:
✓ Zen Orchestrator: Connected
✓ Public Search: Available
✓ Serena MCP: Connected (local)
✓ GitHub MCP: Connected (local)
✓ Sequential Thinking: Connected (local)
✓ FileSystem MCP: Connected (local)
✓ Qdrant Memory: Connected (local)
```

### **Performance Testing**

```bash
# Measure response times
claude benchmark

# Expected results (when fully deployed):
Public search: ~1000ms
Local MCPs: <200ms
Complex workflows: <5000ms
```

### **Integration Testing**

```bash
# Test a complete workflow
claude test workflow "create a README for my project"

# This tests:
# - Query enhancement
# - Multi-MCP coordination
# - File generation
# - Error handling
```

## **Troubleshooting**

### **Connection Issues**

```bash
# Check server status
claude status

# Detailed diagnostics
claude diagnose

# Reset configuration
claude config reset

# View logs
claude logs --tail 50
```

### **Common Problems**

**"Cannot connect to Unraid server"**
- Verify server IP/hostname
- Check firewall settings
- Ensure you're on VPN (if remote)

**"MCP timeout errors"**
- Check Unraid server resources
- Verify Docker containers are running
- Review network latency

**"Authentication failed"**
- Regenerate auth token
- Check API key configuration
- Verify server time sync

## **Best Practices**

### **Development Workflow**

1. **Start with Public MCPs**: Use available tools while Phase 1 deploys
2. **Test Incrementally**: Verify each MCP as it becomes available
3. **Cache Responses**: Use local caching for frequently accessed data
4. **Monitor Usage**: Track which MCPs provide most value

### **Security Considerations**

- Always use VPN for remote access
- Don't commit auth tokens to version control
- Use environment variables for sensitive data
- Regularly rotate access tokens

### **Performance Optimization**

- Use local MCPs for frequent operations
- Batch similar requests
- Enable response caching
- Monitor server resource usage

## **Migration Path**

### **From Public to Local MCPs**

As Phase 1 deployment completes, your commands automatically upgrade:

```bash
# Before (public MCP):
claude search "react hooks"  # Uses public search

# After (local deployment):
claude search "react hooks"  # Uses local Qdrant + enhanced search
```

### **Feature Availability Timeline**

| Week | Available Features          | Status          |
| :--- | :-------------------------- | :-------------- |
| 0-1  | Public MCPs, Basic CLI      | ✅ Available Now |
| 2-3  | Unraid deployment starts    | 🚧 Just Started  |
| 4-5  | Serena, Sequential Thinking | 📋 Coming Soon   |
| 6-7  | GitHub, FileSystem MCPs     | 📋 Planned       |
| 8-9  | Full integration testing    | 📋 Planned       |
| 10+  | Production ready            | 🎯 Target        |

## **Getting Help**

### **Resources**
- [MCP Server Reference](./PC_MCP_Servers.md)
- [Network Setup Guide](./PC_Setup.md)
- [Architecture Overview](./PC_ADR.md)

### **Support Channels**
- Discord: #journey-3-support
- GitHub Issues: [Report problems](https://github.com/promptcraft/issues)
- Email: support@promptcraft.ai

### **Status Updates**
- Check deployment status: `claude status --deployment`
- Join weekly progress calls
- Subscribe to deployment notifications

---

*Note: This guide will be updated as Phase 1 deployment progresses. Check back regularly for the latest information.*
