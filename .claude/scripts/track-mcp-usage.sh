#!/bin/bash

# MCP Usage Tracker Hook Script
# Tracks MCP tool usage, agent invocations, and performance metrics
# for the hybrid MCP architecture

set -euo pipefail

# Configuration
LOG_FILE="/home/byron/.claude/logs/mcp-usage.log"
HOOK_LOG="/home/byron/.claude/logs/hook-debug.log"
MAX_LOG_SIZE=10485760  # 10MB

# Create log file if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Rotate log if it's too large
if [[ -f "$LOG_FILE" && $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_SIZE ]]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
    touch "$LOG_FILE"
fi

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Parse hook input (expecting JSON)
if command -v jq >/dev/null 2>&1; then
    # Extract tool information using jq if available
    TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool // "unknown"' 2>/dev/null || echo "unknown")
    TOOL_RESULT=$(echo "$HOOK_INPUT" | jq -r '.result.type // "unknown"' 2>/dev/null || echo "unknown")
    EXECUTION_TIME=$(echo "$HOOK_INPUT" | jq -r '.executionTimeMs // "unknown"' 2>/dev/null || echo "unknown")
else
    # Fallback parsing without jq
    TOOL_NAME=$(echo "$HOOK_INPUT" | grep -o '"tool":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
    TOOL_RESULT="unknown"
    EXECUTION_TIME="unknown"
fi

# Determine if this is an MCP tool
MCP_SERVER=""
AGENT_TYPE=""
if [[ "$TOOL_NAME" =~ ^mcp__([^_]+)__(.+)$ ]]; then
    MCP_SERVER="${BASH_REMATCH[1]}"
    MCP_TOOL="${BASH_REMATCH[2]}"
    
    # Categorize by agent type based on tool usage patterns
    case "$MCP_SERVER" in
        "zen")
            case "$MCP_TOOL" in
                "chat"|"layered_consensus"|"challenge") AGENT_TYPE="core" ;;
                "secaudit") AGENT_TYPE="security-auditor" ;;
                "testgen") AGENT_TYPE="test-engineer" ;;
                "thinkdeep"|"codereview"|"debug"|"analyze"|"refactor"|"docgen") AGENT_TYPE="hybrid-tool-tester" ;;
                *) AGENT_TYPE="zen-other" ;;
            esac
            ;;
        "github") AGENT_TYPE="github-workflow-agent" ;;
        "playwright") AGENT_TYPE="frontend/ui-testing-agent" ;;
        "filesystem") AGENT_TYPE="file-operations-agent" ;;
        "semgrep") AGENT_TYPE="security-auditor" ;;
        "perplexity") AGENT_TYPE="research-agent" ;;
        "time") AGENT_TYPE="devops/research-agent" ;;
        "context7") AGENT_TYPE="main-context" ;;
        "sentry") AGENT_TYPE="main-context" ;;
        *) AGENT_TYPE="unknown-mcp" ;;
    esac
fi

# Log the usage
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_ENTRY="$TIMESTAMP,POST_TOOL,$TOOL_NAME,$MCP_SERVER,$MCP_TOOL,$AGENT_TYPE,$TOOL_RESULT,$EXECUTION_TIME"

echo "$LOG_ENTRY" >> "$LOG_FILE"

# Debug logging (can be disabled in production)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Hook executed for tool: $TOOL_NAME" >> "$HOOK_LOG" 2>/dev/null || true

# Generate daily summary if this is the first entry today
TODAY=$(date '+%Y-%m-%d')
if ! grep -q "DAILY_SUMMARY,$TODAY" "$LOG_FILE" 2>/dev/null; then
    # Count today's MCP usage
    MCP_COUNT=$(grep "^$TODAY" "$LOG_FILE" | grep -c "mcp__" || echo "0")
    AGENT_COUNT=$(grep "^$TODAY" "$LOG_FILE" | grep -v "main-context\|core" | wc -l || echo "0")
    
    echo "$TODAY,DAILY_SUMMARY,MCP_TOOLS_USED:$MCP_COUNT,AGENT_INVOCATIONS:$AGENT_COUNT" >> "$LOG_FILE"
fi

# Exit successfully (don't block tool execution)
exit 0