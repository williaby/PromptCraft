#!/bin/bash

# PromptCraft Startup Script with Zen MCP Integration
# ====================================================
# This script starts PromptCraft with the correct environment configuration
# to enable MCP integration with the Zen MCP Server via stdio protocol.

set -euo pipefail

# Colors for output
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info "Starting PromptCraft with Zen MCP Server integration..."

# Verify zen server is available
if [[ ! -f "/home/byron/dev/zen-mcp-server/.zen_venv/bin/python" ]]; then
    print_error "Zen MCP Server Python environment not found"
    print_error "Please run './run-server.sh' in the zen-mcp-server directory first"
    exit 1
fi

if [[ ! -f "/home/byron/dev/zen-mcp-server/server.py" ]]; then
    print_error "Zen MCP Server not found at expected location"
    exit 1
fi

print_success "Zen MCP Server files found"

# Check MCP configuration
if [[ ! -f ".mcp.json" ]]; then
    print_error ".mcp.json configuration file not found"
    exit 1
fi

print_success "MCP configuration file found"

# Set environment variables for proper MCP integration
export PROMPTCRAFT_ENVIRONMENT=dev
export PROMPTCRAFT_MCP_ENABLED=false  # Disable HTTP MCP client
export PROMPTCRAFT_DEBUG=true

# Set Zen MCP Hub optimization variables for 60-80% tool reduction
export ZEN_HUB_ENABLED=true
export ZEN_HUB_FILTERING=true
export ZEN_HUB_MAX_TOOLS=25
export ZEN_HUB_DETECTION_TIMEOUT=5
export ZEN_HUB_LOGGING=true

print_info "Environment configured:"
print_info "  - Environment: ${PROMPTCRAFT_ENVIRONMENT}"
print_info "  - HTTP MCP Client: disabled (using stdio MCP servers instead)"
print_info "  - Debug mode: enabled"
print_info "  - Zen MCP Hub: enabled with intelligent tool filtering"
print_info "  - Max tools per context: ${ZEN_HUB_MAX_TOOLS} (60-80% reduction)"

# Start PromptCraft
print_info "Starting PromptCraft application..."

if command -v poetry &> /dev/null; then
    poetry run python src/main.py
else
    python src/main.py
fi
