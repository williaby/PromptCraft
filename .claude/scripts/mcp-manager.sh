#!/bin/bash
# MCP Server Manager for Claude Code
# Manages installation and configuration of MCP servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../mcp"
LOG_FILE="${SCRIPT_DIR}/../mcp-install.log"
ENV_FILE="${SCRIPT_DIR}/../.env"

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE..."
    set -a  # Export all variables
    source "$ENV_FILE"
    set +a  # Stop exporting
else
    echo "Warning: No .env file found at $ENV_FILE"
    echo "Some MCP servers may not install correctly without API keys."
    echo ""
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if MCP server is already installed
is_server_installed() {
    local name=$1
    claude mcp list 2>/dev/null | grep -q "^${name}:" && return 0 || return 1
}

# Function to install stdio-based servers
install_stdio_server() {
    local name=$1
    local command=$2
    shift 2
    local args=("$@")
    
    local cmd="claude mcp add -s user \"$name\" \"$command\""
    for arg in "${args[@]}"; do
        cmd+=" \"$arg\""
    done
    
    print_status "$YELLOW" "Installing $name..."
    if eval "$cmd"; then
        print_status "$GREEN" "✓ $name installed successfully"
        log "Installed $name"
    else
        print_status "$RED" "✗ Failed to install $name"
        log "Failed to install $name"
        return 1
    fi
}

# Function to install HTTP-based servers (like Zapier)
install_http_server() {
    local name=$1
    local url=$2
    local auth_header=$3
    
    local cmd="claude mcp add -s user \"$name\" \"$url\" -t http"
    if [ -n "$auth_header" ]; then
        cmd+=" -H \"$auth_header\""
    fi
    
    print_status "$YELLOW" "Installing $name (HTTP)..."
    if eval "$cmd"; then
        print_status "$GREEN" "✓ $name installed successfully"
        log "Installed $name (HTTP)"
    else
        print_status "$RED" "✗ Failed to install $name"
        log "Failed to install $name (HTTP)"
        return 1
    fi
}

# Function to install servers with environment variables
install_server_with_env() {
    local name=$1
    local command=$2
    shift 2
    
    # Separate args and env vars
    local args=()
    local envs=()
    local parsing_envs=false
    
    for item in "$@"; do
        if [[ "$item" == "--env" ]]; then
            parsing_envs=true
        elif [[ "$parsing_envs" == true ]]; then
            envs+=("$item")
        else
            args+=("$item")
        fi
    done
    
    local cmd="claude mcp add -s user \"$name\" \"$command\""
    for arg in "${args[@]}"; do
        cmd+=" \"$arg\""
    done
    for env in "${envs[@]}"; do
        cmd+=" -e \"$env\""
    done
    
    print_status "$YELLOW" "Installing $name with environment variables..."
    if eval "$cmd"; then
        print_status "$GREEN" "✓ $name installed successfully"
        log "Installed $name with env vars"
    else
        print_status "$RED" "✗ Failed to install $name"
        log "Failed to install $name with env vars"
        return 1
    fi
}

# Main menu
show_menu() {
    echo "======================================"
    echo "    MCP Server Manager for Claude     "
    echo "======================================"
    echo "1) Install all recommended servers"
    echo "2) Install development tools"
    echo "3) Install AI/Search servers"
    echo "4) Install specific server"
    echo "5) List installed servers"
    echo "6) Remove server"
    echo "7) Show server details"
    echo "8) Exit"
    echo "======================================"
}

# Install all recommended servers
install_all() {
    print_status "$GREEN" "Installing all recommended MCP servers..."
    
    # Core servers
    install_stdio_server "zen" "/home/byron/dev/zen-mcp-server/.zen_venv/bin/python" "/home/byron/dev/zen-mcp-server/server.py"
    
    # Development tools
    install_stdio_server "sequential-thinking" "npx" "-y" "@modelcontextprotocol/server-sequential-thinking"
    install_server_with_env "git" "uvx" "mcp-server-git" "--repository" "\${PWD}"
    install_stdio_server "time" "uvx" "mcp-server-time"
    
    # AI/Search servers (check for API keys first)
    if [ -n "$PERPLEXITY_API_KEY" ]; then
        install_server_with_env "perplexity" "npx" "-y" "@modelcontextprotocol/server-perplexity-ask" "--env" "PERPLEXITY_API_KEY=\${PERPLEXITY_API_KEY}"
    else
        print_status "$YELLOW" "⚠ Skipping Perplexity (no API key found)"
    fi
    
    if [ -n "$TAVILY_API_KEY" ]; then
        install_server_with_env "tavily" "npx" "-y" "tavily-mcp@latest" "--env" "TAVILY_API_KEY=\${TAVILY_API_KEY}"
    else
        print_status "$YELLOW" "⚠ Skipping Tavily (no API key found)"
    fi
    
    # Context7 servers
    if [ -n "$UPSTASH_REDIS_REST_URL" ] && [ -n "$UPSTASH_REDIS_REST_TOKEN" ]; then
        install_server_with_env "context7" "npx" "-y" "@upstash/context7-mcp" "--env" "UPSTASH_REDIS_REST_URL=\${UPSTASH_REDIS_REST_URL}" "UPSTASH_REDIS_REST_TOKEN=\${UPSTASH_REDIS_REST_TOKEN}"
        install_http_server "context7-sse" "https://mcp.context7.com/sse" ""
    else
        print_status "$YELLOW" "⚠ Skipping Context7 (missing Redis credentials)"
    fi
    
    # Note: Serena is installed at project level only, not user level
    
    # GitHub server
    if [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
        install_server_with_env "github" "npx" "-y" "@modelcontextprotocol/server-github" "--env" "GITHUB_PERSONAL_ACCESS_TOKEN=\${GITHUB_PERSONAL_ACCESS_TOKEN}"
    else
        print_status "$YELLOW" "⚠ Skipping GitHub (no access token found)"
    fi
    
    print_status "$GREEN" "\n✓ Installation complete!"
}

# Install development tools
install_dev_tools() {
    print_status "$GREEN" "Installing development tool servers..."
    install_stdio_server "sequential-thinking" "npx" "-y" "@modelcontextprotocol/server-sequential-thinking"
    install_server_with_env "git" "uvx" "mcp-server-git" "--repository" "\${PWD}"
    install_stdio_server "time" "uvx" "mcp-server-time"
}

# Install AI/Search servers
install_ai_servers() {
    print_status "$GREEN" "Installing AI/Search servers..."
    
    # Check for required environment variables
    local missing_keys=()
    [ -z "$PERPLEXITY_API_KEY" ] && missing_keys+=("PERPLEXITY_API_KEY")
    [ -z "$TAVILY_API_KEY" ] && missing_keys+=("TAVILY_API_KEY")
    [ -z "$UPSTASH_REDIS_REST_URL" ] && missing_keys+=("UPSTASH_REDIS_REST_URL")
    [ -z "$UPSTASH_REDIS_REST_TOKEN" ] && missing_keys+=("UPSTASH_REDIS_REST_TOKEN")
    
    if [ ${#missing_keys[@]} -gt 0 ]; then
        print_status "$YELLOW" "⚠ Missing environment variables:"
        for key in "${missing_keys[@]}"; do
            echo "  - $key"
        done
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    # Install servers with available keys
    [ -n "$PERPLEXITY_API_KEY" ] && install_server_with_env "perplexity" "npx" "-y" "@perplexity-ai/mcp-server-perplexity" "--env" "PERPLEXITY_API_KEY=\${PERPLEXITY_API_KEY}"
    [ -n "$TAVILY_API_KEY" ] && install_server_with_env "tavily" "npx" "-y" "@tavily/mcp-server" "--env" "TAVILY_API_KEY=\${TAVILY_API_KEY}"
    
    if [ -n "$UPSTASH_REDIS_REST_URL" ] && [ -n "$UPSTASH_REDIS_REST_TOKEN" ]; then
        install_server_with_env "context7" "npx" "-y" "@upstash/context7-mcp" "--env" "UPSTASH_REDIS_REST_URL=\${UPSTASH_REDIS_REST_URL}" "UPSTASH_REDIS_REST_TOKEN=\${UPSTASH_REDIS_REST_TOKEN}"
    fi
}

# Main loop
main() {
    # Create log file if it doesn't exist
    touch "$LOG_FILE"
    
    while true; do
        show_menu
        read -p "Select an option: " choice
        
        case $choice in
            1) install_all ;;
            2) install_dev_tools ;;
            3) install_ai_servers ;;
            4) 
                read -p "Enter server name from config files (e.g., zen, perplexity): " server_name
                # TODO: Parse config file and install specific server
                print_status "$YELLOW" "Feature coming soon..."
                ;;
            5) 
                print_status "$GREEN" "Installed MCP servers:"
                claude mcp list
                ;;
            6)
                read -p "Enter server name to remove: " server_name
                if claude mcp remove "$server_name"; then
                    print_status "$GREEN" "✓ $server_name removed successfully"
                else
                    print_status "$RED" "✗ Failed to remove $server_name"
                fi
                ;;
            7)
                read -p "Enter server name for details: " server_name
                # TODO: Show server configuration details
                print_status "$YELLOW" "Feature coming soon..."
                ;;
            8)
                print_status "$GREEN" "Goodbye!"
                exit 0
                ;;
            *)
                print_status "$RED" "Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        clear
    done
}

# Run main function
main