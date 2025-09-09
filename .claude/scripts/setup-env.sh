#!/bin/bash
# Setup Environment Variables for Claude Global Configuration
# This script helps set up the .env file securely

set -e

CLAUDE_DIR="$HOME/.claude"
ENV_FILE="$CLAUDE_DIR/.env"
ENV_EXAMPLE="$CLAUDE_DIR/.env.example"

echo "🔐 Claude Global Configuration - Environment Setup"
echo "================================================"
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  Warning: $ENV_FILE already exists"
    echo ""
    echo "Options:"
    echo "1. Keep existing .env file"
    echo "2. Create new .env from template (backup existing)"
    echo "3. Exit"
    echo ""
    read -p "Choose option [1-3]: " choice
    
    case $choice in
        1)
            echo "✅ Keeping existing .env file"
            exit 0
            ;;
        2)
            timestamp=$(date +%Y%m%d_%H%M%S)
            backup_file="${ENV_FILE}.backup.${timestamp}"
            mv "$ENV_FILE" "$backup_file"
            echo "✅ Backed up existing .env to: $backup_file"
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
fi

# Check if .env.example exists
if [ ! -f "$ENV_EXAMPLE" ]; then
    echo "❌ Error: $ENV_EXAMPLE not found"
    echo "Make sure you've cloned the .claude repository to ~/.claude"
    exit 1
fi

# Copy .env.example to .env
cp "$ENV_EXAMPLE" "$ENV_FILE"
echo "✅ Created $ENV_FILE from template"

# Set secure permissions (read/write for owner only)
chmod 600 "$ENV_FILE"
echo "✅ Set secure permissions on .env file"

echo ""
echo "📝 Next Steps:"
echo "1. Edit $ENV_FILE and add your API keys"
echo "2. Never commit this file to Git!"
echo "3. Keep your API keys secure"
echo ""
echo "To edit the file:"
echo "  nano $ENV_FILE"
echo "  # or"
echo "  vim $ENV_FILE"
echo ""
echo "Required API keys to configure:"
echo ""
echo "🔍 Search & Information:"
echo "  - PERPLEXITY_API_KEY"
echo "  - TAVILY_API_KEY"
echo ""
echo "🛠️  Development Tools:"
echo "  - GITHUB_PERSONAL_ACCESS_TOKEN"
echo "  - GIT_REPO_PATH (local path)"
echo ""
echo "🗄️  Infrastructure:"
echo "  - UPSTASH_REDIS_REST_URL & TOKEN (Context7)"
echo "  - SENTRY_AUTH_TOKEN, ORG & PROJECT"
echo ""
echo "⚡ Automation:"
echo "  - ZAPIER_API_KEY"
echo ""
echo "🤖 AI Assistants:"
echo "  - SERENA_INSTALL_PATH (local installation path)"
echo "  - SERENA_PROJECT_PATH (project to work with)"
echo ""
echo "🔒 Security Notes:"
echo "- The .env file has restricted permissions (600)"
echo "- It's automatically ignored by Git"
echo "- Never share your API keys"
echo "- Rotate keys regularly"
echo "- Consider using a password manager for key storage"