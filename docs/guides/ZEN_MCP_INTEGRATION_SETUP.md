# Zen MCP Server Integration Setup

This document outlines the configuration changes made to enable PromptCraft to connect to the Zen MCP Server properly.

## Issues Identified

1. **Wrong Connection Type**: PromptCraft was configured to connect to the Zen server via HTTP (`http://localhost:3000`), but Zen MCP Server uses stdio (standard input/output) protocol for MCP communication.

2. **Empty MCP Configuration**: The `.mcp.json` file had no MCP servers configured (`mcpServers: {}`).

3. **Environment Variable Configuration**: Environment variables were using incorrect prefixes (`MCP_*` instead of `PROMPTCRAFT_MCP_*`).

## Solutions Applied

### 1. Updated MCP Server Configuration (`.mcp.json`)

Added proper MCP server configurations for both the main zen server and hub server:

```json
{
  "version": "1.0",
  "mcpServers": {
    "zen": {
      "command": "/home/byron/dev/zen-mcp-server/.zen_venv/bin/python",
      "args": ["/home/byron/dev/zen-mcp-server/server.py"],
      "enabled": true,
      "priority": 100,
      "timeout": 30,
      "retry_attempts": 3,
      "self_hosted_features": ["zen_orchestration", "multi_agent", "consensus", "validation"]
    },
    "zen-hub": {
      "command": "/home/byron/dev/zen-mcp-server/.zen_venv/bin/python",
      "args": ["/home/byron/dev/zen-mcp-server/hub_server.py"],
      "enabled": false,
      "priority": 90
    }
  },
  "parallel_execution": true,
  "max_concurrent_servers": 5,
  "health_check_interval": 60
}
```

### 2. Updated Environment Configuration (`.env.dev`)

Added proper environment variables with the correct `PROMPTCRAFT_` prefix:

```bash
# MCP (Model Context Protocol) Configuration
# ==========================================
# Disable HTTP-based MCP integration in favor of direct stdio MCP servers
# The actual MCP servers are configured in .mcp.json
PROMPTCRAFT_MCP_ENABLED=false
PROMPTCRAFT_MCP_SERVER_URL=http://localhost:3000  # Not used when MCP_ENABLED=false
PROMPTCRAFT_MCP_TIMEOUT=30.0
PROMPTCRAFT_MCP_MAX_RETRIES=3
PROMPTCRAFT_MCP_HEALTH_CHECK_INTERVAL=60.0
```

### 3. Created Startup Script (`start-with-zen-mcp.sh`)

Created a convenience script that:
- Validates the Zen MCP Server is available
- Sets the correct environment variables
- Starts PromptCraft with proper configuration

## How It Works

### Architecture Overview

```
PromptCraft Application
    ↓
MCPConfigurationManager (.mcp.json)
    ↓
MCP Client (stdio protocol)
    ↓
Zen MCP Server (.zen_venv/bin/python server.py)
    ↓
Zen Tools (chat, thinkdeep, consensus, etc.)
```

### Connection Flow

1. **PromptCraft** loads MCP configuration from `.mcp.json`
2. **MCPConfigurationManager** finds enabled servers (`zen`)
3. **MCP Client** spawns the zen server process using stdio protocol:
   - Command: `/home/byron/dev/zen-mcp-server/.zen_venv/bin/python`
   - Args: `['/home/byron/dev/zen-mcp-server/server.py']`
4. **Communication** happens via stdin/stdout using MCP protocol
5. **Zen Server** provides access to all 22 tools (chat, thinkdeep, consensus, etc.)

## Usage

### Quick Start

```bash
# Start PromptCraft with Zen MCP integration
./start-with-zen-mcp.sh
```

### Manual Start

```bash
# Set environment variables
export PROMPTCRAFT_ENVIRONMENT=dev
export PROMPTCRAFT_MCP_ENABLED=false

# Start PromptCraft
poetry run python src/main.py
```

### Verification

Test the configuration:

```bash
python -c "
from src.mcp_integration.config_manager import MCPConfigurationManager
config_manager = MCPConfigurationManager()
print(f'Enabled servers: {config_manager.get_enabled_servers()}')
print(f'Configuration valid: {config_manager.validate_configuration()[\"valid\"]}')
"
```

## Configuration Details

### Key Settings

- **HTTP MCP Integration**: Disabled (`PROMPTCRAFT_MCP_ENABLED=false`)
- **Stdio MCP Servers**: Enabled via `.mcp.json` configuration
- **Primary Server**: `zen` (22 tools available)
- **Backup Server**: `zen-hub` (disabled by default, enables hub functionality)

### Environment Variables

| Variable | Value | Purpose |
|----------|--------|---------|
| `PROMPTCRAFT_ENVIRONMENT` | `dev` | Sets development mode |
| `PROMPTCRAFT_MCP_ENABLED` | `false` | Disables HTTP MCP client |
| `PROMPTCRAFT_DEBUG` | `true` | Enables debug logging |

### File Locations

- **MCP Config**: `/home/byron/dev/PromptCraft/.mcp.json`
- **Environment**: `/home/byron/dev/PromptCraft/.env.dev`
- **Zen Server**: `/home/byron/dev/zen-mcp-server/server.py`
- **Zen Python**: `/home/byron/dev/zen-mcp-server/.zen_venv/bin/python`

## Troubleshooting

### Common Issues

1. **"Zen MCP Server Python environment not found"**
   - Run `./run-server.sh` in the zen-mcp-server directory
   - Ensure virtual environment is created at `.zen_venv`

2. **"Configuration valid: False"**
   - Check that file paths in `.mcp.json` are correct
   - Verify zen server files exist and are executable

3. **"MCP integration components not available"**
   - Ensure `PROMPTCRAFT_MCP_ENABLED=false` is set
   - Check that `.mcp.json` has valid server configurations

### Validation Commands

```bash
# Test MCP configuration loading
PROMPTCRAFT_ENVIRONMENT=dev PROMPTCRAFT_MCP_ENABLED=false python -c "
from src.mcp_integration.config_manager import MCPConfigurationManager
config_manager = MCPConfigurationManager()
validation = config_manager.validate_configuration()
print(f'Valid: {validation[\"valid\"]}, Servers: {validation[\"enabled_count\"]}')
"

# Test zen server files exist
ls -la /home/byron/dev/zen-mcp-server/.zen_venv/bin/python
ls -la /home/byron/dev/zen-mcp-server/server.py
```

## Success Criteria

✅ **Configuration Status:**
- MCP configuration loads successfully
- Zen server is enabled and configured correctly
- HTTP MCP client is disabled
- File paths are valid and accessible

✅ **Expected Output:**
```
Enabled servers: ['zen']
Configuration valid: True
Server count: 2
Enabled count: 1
🎉 Zen server configuration is valid!
```

The configuration is now ready for PromptCraft to connect to the Zen MCP Server using the proper MCP stdio protocol.
