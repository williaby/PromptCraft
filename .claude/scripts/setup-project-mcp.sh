#!/bin/bash
# Setup MCP servers for a specific project
# Usage: ./setup-project-mcp.sh [server-names...]

set -e

# Load environment variables from ~/.claude/.env if it exists
ENV_FILE="$HOME/.claude/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE..."
    set -a  # Export all variables
    source "$ENV_FILE"
    set +a  # Stop exporting
fi

# Default servers for all projects
DEFAULT_SERVERS=("zen" "git" "sequential-thinking")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_usage() {
    echo "Usage: $0 [server-names...]"
    echo ""
    echo "Setup MCP servers for the current project."
    echo ""
    echo "Options:"
    echo "  --all          Install all available servers"
    echo "  --dev          Install development tool servers"
    echo "  --ai           Install AI/search servers"
    echo "  --list         List available servers"
    echo ""
    echo "Examples:"
    echo "  $0                    # Install default servers"
    echo "  $0 zen perplexity     # Install specific servers"
    echo "  $0 --dev --ai         # Install dev and AI servers"
}

# Check if running in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    echo "This script should be run from within a project directory"
    exit 1
fi

PROJECT_ROOT=$(git rev-parse --show-toplevel)
PROJECT_NAME=$(basename "$PROJECT_ROOT")

echo -e "${GREEN}Setting up MCP servers for project: $PROJECT_NAME${NC}"
echo "Project path: $PROJECT_ROOT"
echo ""

# Create .claude directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/.claude"

# Create project-specific MCP configuration
cat > "$PROJECT_ROOT/.claude/mcp.json" << 'EOF'
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "${PWD}"]
    }
  }
}
EOF

echo -e "${GREEN}✓ Created $PROJECT_ROOT/.claude/mcp.json${NC}"

# Parse arguments
SERVERS_TO_INSTALL=()

if [ $# -eq 0 ]; then
    # No arguments, use defaults
    SERVERS_TO_INSTALL=("${DEFAULT_SERVERS[@]}")
else
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                SERVERS_TO_INSTALL=("zen" "git" "sequential-thinking" "time" "tavily" "context7-sse" "github")
                ;;
            --dev)
                SERVERS_TO_INSTALL+=("git" "sequential-thinking" "time")
                ;;
            --ai)
                SERVERS_TO_INSTALL+=("tavily" "context7-sse")
                ;;
            --list)
                echo "Available MCP servers:"
                echo "  Core: zen"
                echo "  Dev Tools: git, sequential-thinking, time"
                echo "  AI/Search: tavily, context7-sse"
                echo "  Special: github, zapier"
                echo "  Project-Only: serena (requires project context)"
                exit 0
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                SERVERS_TO_INSTALL+=("$1")
                ;;
        esac
        shift
    done
fi

# Remove duplicates
SERVERS_TO_INSTALL=($(printf "%s\n" "${SERVERS_TO_INSTALL[@]}" | sort -u))

echo "Installing servers: ${SERVERS_TO_INSTALL[*]}"
echo ""

# Install each server using claude mcp add
for server in "${SERVERS_TO_INSTALL[@]}"; do
    echo -e "${YELLOW}Installing $server...${NC}"
    
    case $server in
        "zen")
            claude mcp add -s project "$server" "/home/byron/dev/zen-mcp-server/.zen_venv/bin/python" "/home/byron/dev/zen-mcp-server/server.py"
            ;;
        "git")
            # Git server is already in the mcp.json
            echo "Git server configured in project mcp.json"
            ;;
        "sequential-thinking")
            claude mcp add -s project "$server" "npx" "-y" "@modelcontextprotocol/server-sequential-thinking"
            ;;
        "time")
            claude mcp add -s project "$server" "uvx" "mcp-server-time"
            ;;
        "perplexity")
            if [ -z "$PERPLEXITY_API_KEY" ]; then
                echo -e "${YELLOW}⚠ Skipping Perplexity (no API key found)${NC}"
                continue
            fi
            claude mcp add -s project "$server" "npx" "-y" "@perplexity-ai/mcp-server-perplexity" -e "PERPLEXITY_API_KEY=\${PERPLEXITY_API_KEY}"
            ;;
        "tavily")
            if [ -z "$TAVILY_API_KEY" ]; then
                echo -e "${YELLOW}⚠ Skipping Tavily (no API key found)${NC}"
                continue
            fi
            claude mcp add -s project "$server" "npx" "-y" "@tavily/mcp-server" -e "TAVILY_API_KEY=\${TAVILY_API_KEY}"
            ;;
        "context7")
            if [ -z "$UPSTASH_REDIS_REST_URL" ] || [ -z "$UPSTASH_REDIS_REST_TOKEN" ]; then
                echo -e "${YELLOW}⚠ Skipping Context7 (missing Redis credentials)${NC}"
                continue
            fi
            claude mcp add -s project "$server" "npx" "-y" "@upstash/context7-mcp" -e "UPSTASH_REDIS_REST_URL=\${UPSTASH_REDIS_REST_URL}" -e "UPSTASH_REDIS_REST_TOKEN=\${UPSTASH_REDIS_REST_TOKEN}"
            ;;
        "context7-sse")
            claude mcp add -s project "$server" "https://mcp.context7.com/sse" -t sse
            ;;
        "serena")
            if [ -z "$SERENA_INSTALL_PATH" ]; then
                echo -e "${YELLOW}⚠ Skipping Serena (SERENA_INSTALL_PATH not set)${NC}"
                continue
            fi
            # Use current project directory as the project path
            claude mcp add -s project "$server" "uv" "run" "--directory" "\${SERENA_INSTALL_PATH}" "serena-mcp-server" "--context" "ide-assistant" "--project" "\${PWD}"
            ;;
        "github")
            if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
                echo -e "${YELLOW}⚠ Skipping GitHub (no access token found)${NC}"
                continue
            fi
            claude mcp add -s project "$server" "npx" "-y" "@modelcontextprotocol/server-github" -e "GITHUB_PERSONAL_ACCESS_TOKEN=\${GITHUB_PERSONAL_ACCESS_TOKEN}"
            ;;
        *)
            echo -e "${RED}Unknown server: $server${NC}"
            ;;
    esac
done

echo ""
echo -e "${GREEN}✓ MCP server setup complete for $PROJECT_NAME${NC}"
echo ""
echo "The following files were created/modified:"
echo "  - $PROJECT_ROOT/.claude/mcp.json"
echo ""
echo "To verify installation, run:"
echo "  claude mcp list"