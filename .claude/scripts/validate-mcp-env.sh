#!/bin/bash

# MCP Environment Validation Script
# Validates that required environment variables and executables are available

set -e

echo "🔍 MCP Environment Validation"
echo "============================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize counters
WARNINGS=0
ERRORS=0

# Helper functions
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
        ((WARNINGS++))
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}✗${NC} $message"
        ((ERRORS++))
    fi
}

check_executable() {
    local cmd=$1
    local name=$2
    if command -v "$cmd" >/dev/null 2>&1; then
        print_status "OK" "$name executable found: $(which $cmd)"
    else
        print_status "ERROR" "$name executable not found"
    fi
}

check_env_var() {
    local var=$1
    local name=$2
    local optional=${3:-false}
    if [ -n "${!var}" ]; then
        print_status "OK" "$name environment variable set"
    elif [ "$optional" = "true" ]; then
        print_status "WARN" "$name environment variable not set (optional)"
    else
        print_status "ERROR" "$name environment variable not set (required for $name server)"
    fi
}

check_path() {
    local path=$1
    local name=$2
    if [ -e "$path" ]; then
        print_status "OK" "$name path exists: $path"
    else
        print_status "ERROR" "$name path not found: $path"
    fi
}

echo "📋 Checking Required Executables"
echo "---------------------------------"
check_executable "python3" "Python3"
check_executable "node" "Node.js"
check_executable "npm" "NPM"
check_executable "npx" "NPX"
check_executable "docker" "Docker"
check_executable "uvx" "UVX"
check_executable "uv" "UV"

echo ""
echo "🔑 Checking API Keys & Environment Variables"
echo "---------------------------------------------"

# Core development tools
check_env_var "GIT_REPO_PATH" "Git Repository" true

# External API services
check_env_var "PERPLEXITY_API_KEY" "Perplexity" true
check_env_var "TAVILY_API_KEY" "Tavily" true
check_env_var "GITHUB_PERSONAL_ACCESS_TOKEN" "GitHub" true
check_env_var "ZAPIER_API_KEY" "Zapier" true

# Context7/Redis
check_env_var "UPSTASH_REDIS_REST_URL" "Upstash Redis URL" true
check_env_var "UPSTASH_REDIS_REST_TOKEN" "Upstash Redis Token" true

# Sentry
check_env_var "SENTRY_AUTH_TOKEN" "Sentry Auth Token" true
check_env_var "SENTRY_ORG" "Sentry Organization" true
check_env_var "SENTRY_PROJECT" "Sentry Project" true

# Serena
check_env_var "SERENA_INSTALL_PATH" "Serena Install Path" true
check_env_var "SERENA_PROJECT_PATH" "Serena Project Path" true

echo ""
echo "📁 Checking Critical Paths"
echo "---------------------------"

# Zen server paths
check_path "/home/byron/dev/zen-mcp-server/server.py" "Zen server script"
check_path "/home/byron/dev/zen-mcp-server/.zen_venv/bin/python" "Zen Python environment"

# Check Serena path if environment variable is set
if [ -n "$SERENA_INSTALL_PATH" ]; then
    check_path "$SERENA_INSTALL_PATH" "Serena installation directory"
fi

echo ""
echo "⚙️  Checking Claude Code Configuration"
echo "---------------------------------------"
check_path "/home/byron/.claude/mcp-servers.json" "Consolidated MCP configuration"
check_path "/home/byron/.claude/settings/base-settings.json" "Base settings file"

# Check if enableAllProjectMcpServers is set
if [ -f "/home/byron/.claude/settings/base-settings.json" ]; then
    if grep -q '"enableAllProjectMcpServers": true' "/home/byron/.claude/settings/base-settings.json"; then
        print_status "OK" "enableAllProjectMcpServers is enabled"
    else
        print_status "WARN" "enableAllProjectMcpServers is not enabled"
    fi
fi

echo ""
echo "📊 Validation Summary"
echo "====================="
echo "Warnings: $WARNINGS"
echo "Errors: $ERRORS"

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Validation completed with warnings${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Validation failed with $ERRORS errors${NC}"
    echo ""
    echo "💡 Next Steps:"
    echo "- Install missing executables"
    echo "- Set required environment variables"
    echo "- Check file paths and permissions"
    echo "- Run 'claude mcp list' to test MCP server loading"
    exit 1
fi