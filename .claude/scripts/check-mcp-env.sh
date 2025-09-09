#!/bin/bash
# Check MCP environment variables and their status

set -e

ENV_FILE="$HOME/.claude/.env"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "MCP Environment Variable Status"
echo "==============================="
echo ""

# Load .env file if it exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓ Found .env file at: $ENV_FILE${NC}"
    set -a
    source "$ENV_FILE"
    set +a
    echo ""
else
    echo -e "${RED}✗ No .env file found at: $ENV_FILE${NC}"
    echo "  Create one by copying .env.example:"
    echo "  cp ~/.claude/.env.example ~/.claude/.env"
    echo ""
fi

# Check each required environment variable
check_var() {
    local var_name=$1
    local service=$2
    
    if [ -n "${!var_name}" ]; then
        # Mask the value for security
        local masked_value="${!var_name:0:8}..."
        echo -e "${GREEN}✓ $var_name${NC} (for $service): Set [${masked_value}]"
    else
        echo -e "${RED}✗ $var_name${NC} (for $service): Not set"
    fi
}

echo "API Keys and Credentials:"
echo "------------------------"
check_var "PERPLEXITY_API_KEY" "Perplexity search"
check_var "TAVILY_API_KEY" "Tavily web search"
check_var "UPSTASH_REDIS_REST_URL" "Context7"
check_var "UPSTASH_REDIS_REST_TOKEN" "Context7"
check_var "SENTRY_AUTH_TOKEN" "Sentry monitoring"
check_var "SENTRY_ORG" "Sentry monitoring"
check_var "SENTRY_PROJECT" "Sentry monitoring"
check_var "GITHUB_PERSONAL_ACCESS_TOKEN" "GitHub API"
check_var "ZAPIER_API_KEY" "Zapier automation"

echo ""
echo "Path Variables:"
echo "--------------"
check_var "GIT_REPO_PATH" "Git MCP server"
check_var "SERENA_INSTALL_PATH" "Serena NLP"
check_var "SERENA_PROJECT_PATH" "Serena NLP"

echo ""
echo "Summary:"
echo "--------"
total_vars=12
set_vars=0

for var in PERPLEXITY_API_KEY TAVILY_API_KEY UPSTASH_REDIS_REST_URL \
           UPSTASH_REDIS_REST_TOKEN SENTRY_AUTH_TOKEN SENTRY_ORG \
           SENTRY_PROJECT GITHUB_PERSONAL_ACCESS_TOKEN ZAPIER_API_KEY \
           GIT_REPO_PATH SERENA_INSTALL_PATH SERENA_PROJECT_PATH; do
    if [ -n "${!var}" ]; then
        ((set_vars++))
    fi
done

if [ $set_vars -eq $total_vars ]; then
    echo -e "${GREEN}All environment variables are set! ($set_vars/$total_vars)${NC}"
elif [ $set_vars -gt 0 ]; then
    echo -e "${YELLOW}Partially configured: $set_vars/$total_vars variables set${NC}"
else
    echo -e "${RED}No environment variables are set!${NC}"
fi

echo ""
echo "Note: The MCP installation scripts will now automatically"
echo "load these environment variables from your .env file."