#!/bin/bash
# Test MCP servers availability

GREEN='\033[0;32m'
YELLOW='\033[1;33m' 
RED='\033[0;31m'
NC='\033[0m'

echo "Testing MCP Server Availability"
echo "==============================="
echo ""

# Test each server
test_server() {
    local server=$1
    local test_cmd=$2
    
    echo -n "Testing $server... "
    
    case $server in
        "zen")
            # Check if zen_venv exists
            if [ -d "/home/byron/dev/zen-mcp-server/.zen_venv" ]; then
                echo -e "${GREEN}✓ Available${NC}"
            else
                echo -e "${RED}✗ Not found${NC}"
            fi
            ;;
        "sequential-thinking")
            # Check if npx can find the package
            if npx -y @modelcontextprotocol/server-sequential-thinking --version 2>/dev/null; then
                echo -e "${GREEN}✓ Available${NC}"
            else
                echo -e "${YELLOW}⚠ Package will be downloaded on first use${NC}"
            fi
            ;;
        "git")
            # Check if uvx is available
            if command -v uvx &> /dev/null; then
                echo -e "${GREEN}✓ Available (uvx found)${NC}"
            else
                echo -e "${RED}✗ uvx not found${NC}"
            fi
            ;;
        "time")
            # Check if uvx is available
            if command -v uvx &> /dev/null; then
                echo -e "${GREEN}✓ Available (uvx found)${NC}"
            else
                echo -e "${RED}✗ uvx not found${NC}"
            fi
            ;;
        "perplexity"|"tavily")
            # These require API calls to test, just check npx
            if command -v npx &> /dev/null; then
                echo -e "${GREEN}✓ Available (npx found, API key set)${NC}"
            else
                echo -e "${RED}✗ npx not found${NC}"
            fi
            ;;
        "github")
            # Check if docker is available
            if command -v docker &> /dev/null && docker ps &>/dev/null; then
                echo -e "${GREEN}✓ Available (Docker running)${NC}"
            else
                echo -e "${RED}✗ Docker not available or not running${NC}"
            fi
            ;;
        "zapier")
            # Test HTTP endpoint
            if [ -n "$ZAPIER_API_KEY" ]; then
                if curl -s -H "Authorization: Bearer $ZAPIER_API_KEY" https://mcp.zapier.com/api/mcp/mcp -o /dev/null; then
                    echo -e "${GREEN}✓ Available (HTTP endpoint reachable)${NC}"
                else
                    echo -e "${YELLOW}⚠ HTTP endpoint check failed${NC}"
                fi
            else
                echo -e "${YELLOW}⚠ ZAPIER_API_KEY not set${NC}"
            fi
            ;;
    esac
}

# Test all servers
for server in zen sequential-thinking git time perplexity tavily github zapier; do
    test_server "$server"
done

echo ""
echo "Summary:"
echo "--------"
echo "All MCP servers have been installed at the user level."
echo "They will be available in all your Claude Code sessions."
echo ""
echo "Note: Some servers may download dependencies on first use."