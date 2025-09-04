#!/bin/bash
set -euo pipefail

# Setup script for AI coding tools in PromptCraft-Hybrid
# This script helps developers install and configure AI coding CLI tools

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Claude Code
install_claude() {
    log_info "Installing Claude Code..."

    if command_exists claude; then
        log_success "Claude Code already installed: $(claude --version)"
        return 0
    fi

    log_info "Please install Claude Code manually:"
    echo "1. Visit: https://claude.ai/code"
    echo "2. Download and install for your platform"
    echo "3. Run: claude auth login"
    echo "4. Verify with: claude --version"

    read -p "Press Enter when Claude Code is installed..."

    if command_exists claude; then
        log_success "Claude Code installed successfully"

        # Setup Claude configuration if it doesn't exist
        if [ ! -f "$PROJECT_ROOT/.claude/settings.json" ]; then
            log_info "Creating Claude configuration..."
            python "$PROJECT_ROOT/scripts/ai_tools_validator.py" --create-templates
        fi
    else
        log_error "Claude Code installation not detected"
        return 1
    fi
}

# Function to install GitHub Copilot CLI
install_copilot() {
    log_info "Installing GitHub Copilot CLI..."

    if ! command_exists gh; then
        log_error "GitHub CLI (gh) is required but not installed"
        log_info "Install from: https://cli.github.com/"
        return 1
    fi

    # Check if Copilot extension is already installed
    if gh extension list | grep -q "github/gh-copilot"; then
        log_success "GitHub Copilot CLI already installed"
        return 0
    fi

    # Install Copilot extension
    log_info "Installing GitHub Copilot extension..."
    if gh extension install github/gh-copilot; then
        log_success "GitHub Copilot CLI installed successfully"
    else
        log_error "Failed to install GitHub Copilot CLI"
        return 1
    fi

    # Authenticate if needed
    if ! gh auth status >/dev/null 2>&1; then
        log_info "GitHub authentication required..."
        gh auth login
    fi
}

# Function to install Gemini CLI
install_gemini() {
    log_info "Gemini CLI installation..."

    if command_exists gemini; then
        log_success "Gemini CLI already available: $(gemini --version 2>/dev/null || echo 'version unknown')"
        return 0
    fi

    log_warning "Gemini CLI not found"
    log_info "Please install manually:"
    echo "1. Visit: https://ai.google.dev/gemini-api/docs/cli"
    echo "2. Follow installation instructions for your platform"
    echo "3. Run: gemini auth login"
    echo "4. Set GOOGLE_AI_API_KEY or GEMINI_API_KEY environment variable"

    return 1
}

# Function to install Qwen Code CLI
install_qwen() {
    log_info "Qwen Code CLI installation..."

    if command_exists qwen; then
        log_success "Qwen CLI already available: $(qwen --version 2>/dev/null || echo 'version unknown')"
        return 0
    fi

    log_warning "Qwen CLI not found"
    log_info "Please install manually:"
    echo "1. Visit: https://github.com/QwenLM/Qwen-CLI"
    echo "2. Follow installation instructions"
    echo "3. Configure API credentials"
    echo "4. Set QWEN_API_KEY environment variable"

    return 1
}

# Function to install OpenAI CLI
install_openai() {
    log_info "Installing OpenAI CLI..."

    if command_exists openai; then
        log_success "OpenAI CLI already installed: $(openai --version 2>/dev/null || echo 'version unknown')"
        return 0
    fi

    # Try to install via pip
    if command_exists pip; then
        log_info "Installing OpenAI CLI via pip..."
        if pip install openai[cli]; then
            log_success "OpenAI CLI installed successfully"
        else
            log_error "Failed to install OpenAI CLI via pip"
            return 1
        fi
    else
        log_error "pip not found. Please install OpenAI CLI manually:"
        echo "pip install openai[cli]"
        return 1
    fi

    # Check for API key
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        log_warning "OPENAI_API_KEY environment variable not set"
        log_info "Please set your OpenAI API key: export OPENAI_API_KEY=your_key"
    fi
}

# Function to validate tools after installation
validate_tools() {
    log_info "Validating AI tools installation..."

    cd "$PROJECT_ROOT"
    python scripts/ai_tools_validator.py --create-templates

    local exit_code=$?

    case $exit_code in
        0)
            log_success "All AI tools are properly installed and configured"
            ;;
        1)
            log_warning "Some tools are installed but not fully configured"
            log_info "Check the output above for configuration issues"
            ;;
        2)
            log_error "No AI tools are installed"
            ;;
        *)
            log_error "Tool validation failed with exit code: $exit_code"
            ;;
    esac

    return $exit_code
}

# Function to create environment file template
create_env_template() {
    local env_file="$PROJECT_ROOT/.env.example"

    if [ -f "$env_file" ]; then
        log_info ".env.example already exists, skipping creation"
        return 0
    fi

    log_info "Creating .env.example template..."

    cat > "$env_file" << 'EOF'
# AI Tool API Keys
# Copy this file to .env and fill in your actual API keys

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google AI / Gemini
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Qwen
QWEN_API_KEY=your_qwen_api_key_here

# GitHub (for Copilot CLI)
GITHUB_TOKEN=your_github_token_here
EOF

    log_success ".env.example created"
    log_info "Copy to .env and fill in your API keys: cp .env.example .env"
}

# Main function
main() {
    log_info "🤖 PromptCraft AI Tools Setup"
    echo "================================"
    echo

    # Change to project directory
    cd "$PROJECT_ROOT"

    # Create configuration templates
    log_info "Creating configuration templates..."
    python scripts/ai_tools_validator.py --create-templates || {
        log_error "Failed to create configuration templates"
        exit 1
    }

    # Create environment template
    create_env_template

    # Install tools (interactive)
    echo
    log_info "Available AI tools to install:"
    echo "1. Claude Code (Anthropic)"
    echo "2. GitHub Copilot CLI"
    echo "3. Gemini CLI (Google)"
    echo "4. Qwen Code CLI"
    echo "5. OpenAI CLI"
    echo "a. Install all"
    echo "s. Skip installation, just validate"
    echo

    read -p "Select tools to install (e.g., 1,2,5 or 'a' for all): " selection

    case "$selection" in
        *"1"*|*"a"*) install_claude || true ;;
    esac

    case "$selection" in
        *"2"*|*"a"*) install_copilot || true ;;
    esac

    case "$selection" in
        *"3"*|*"a"*) install_gemini || true ;;
    esac

    case "$selection" in
        *"4"*|*"a"*) install_qwen || true ;;
    esac

    case "$selection" in
        *"5"*|*"a"*) install_openai || true ;;
    esac

    # Final validation
    echo
    validate_tools

    echo
    log_success "🎉 AI Tools setup complete!"
    log_info "Next steps:"
    echo "1. Configure API keys in .env file (copy from .env.example)"
    echo "2. Restart VS Code to activate tool validation"
    echo "3. Run validation anytime with: python scripts/ai_tools_validator.py"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
