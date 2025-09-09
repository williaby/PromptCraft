#!/bin/bash
# Serena MCP Server Wrapper Script
# This script automatically uses the current working directory as the project path

set -e

# Get Serena installation path from environment or use default
SERENA_INSTALL="${SERENA_INSTALL_PATH:-$HOME/dev/serena}"

# Validate Serena installation exists
if [ ! -d "$SERENA_INSTALL" ]; then
    echo "❌ Error: Serena installation not found at: $SERENA_INSTALL" >&2
    echo "Please set SERENA_INSTALL_PATH in ~/.claude/.env" >&2
    exit 1
fi

# Use current working directory as project path
PROJECT_PATH="$(pwd)"

# Log what we're doing (to stderr so it doesn't interfere with stdio)
echo "🚀 Starting Serena MCP Server" >&2
echo "📁 Serena Path: $SERENA_INSTALL" >&2
echo "📂 Project Path: $PROJECT_PATH" >&2

# Launch Serena with the correct paths
exec uv run --directory "$SERENA_INSTALL" serena-mcp-server \
    --context ide-assistant \
    --project "$PROJECT_PATH" \
    "$@"