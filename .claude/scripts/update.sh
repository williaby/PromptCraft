#!/bin/bash
# Update Global Claude Configuration
# This script updates the global Claude configuration to the latest version

set -e  # Exit on any error

CLAUDE_DIR="$HOME/.claude"

echo "🔄 Updating Global Claude Configuration..."

# Check if .claude directory exists and is a git repository
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "❌ Error: ~/.claude directory not found"
    echo "Run the initial setup first:"
    echo "cd ~ && git clone https://github.com/your-username/.claude.git"
    exit 1
fi

if [ ! -d "$CLAUDE_DIR/.git" ]; then
    echo "❌ Error: ~/.claude is not a git repository"
    echo "Please remove ~/.claude and run initial setup:"
    echo "rm -rf ~/.claude && cd ~ && git clone https://github.com/your-username/.claude.git"
    exit 1
fi

# Change to .claude directory
cd "$CLAUDE_DIR"

# Check for local modifications
if ! git diff --quiet; then
    echo "⚠️  Warning: Local modifications detected in ~/.claude/"
    echo "The following files have been modified:"
    git diff --name-only
    echo ""
    echo "These changes will be stashed before updating."
    echo "Use 'git stash pop' in ~/.claude to restore them after update."
    git stash push -m "Local modifications before update $(date)"
fi

# Fetch latest changes
echo "📡 Fetching latest changes..."
git fetch origin

# Check if updates are available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ Already up to date ($(git rev-parse --short HEAD))"
else
    echo "📥 Updates available, pulling changes..."
    
    # Show what's being updated
    echo ""
    echo "📋 Changes since last update:"
    git log --oneline --graph "$LOCAL..$REMOTE"
    echo ""
    
    # Pull changes
    git pull origin main
    
    echo "✅ Update complete!"
    echo "📌 Now on commit: $(git rev-parse --short HEAD)"
    echo "📄 Latest commit: $(git log -1 --pretty=format:'%s')"
fi

echo ""
echo "🎉 Global Claude configuration is up to date!"
echo ""
echo "Available universal commands:"
echo "  /universal:lint-check <file>        - Run appropriate linter"
echo "  /universal:security-validate        - Validate security setup"
echo "  /universal:format-code <file>       - Format code files"
echo "  /universal:git-workflow <command>   - Git workflow helpers"
echo ""
echo "Global standards are automatically loaded by Claude Code."