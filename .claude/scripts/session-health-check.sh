#!/bin/bash

# Session Health Check Hook Script
# Verifies MCP servers, agent files, and critical permissions at session start
# for the hybrid MCP architecture

set -euo pipefail

HEALTH_LOG="/home/byron/.claude/logs/session-health.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$HEALTH_LOG")"

# Function to log health check results
log_health() {
    echo "$TIMESTAMP,$1,$2,$3" >> "$HEALTH_LOG"
}

# Check MCP servers are configured
MCP_SERVERS=0
if command -v claude >/dev/null 2>&1; then
    MCP_SERVERS=$(claude mcp list 2>/dev/null | grep -c "Connected" || echo "0")
fi

if [[ "$MCP_SERVERS" -gt 0 ]]; then
    log_health "MCP_SERVERS" "HEALTHY" "$MCP_SERVERS servers connected"
else
    log_health "MCP_SERVERS" "WARNING" "No MCP servers connected"
fi

# Check agent files are accessible
AGENT_FILES=$(find /home/byron/.claude/agents -name "*.md" -type f 2>/dev/null | wc -l || echo "0")
if [[ "$AGENT_FILES" -gt 15 ]]; then
    log_health "AGENT_FILES" "HEALTHY" "$AGENT_FILES agent files found"
else
    log_health "AGENT_FILES" "WARNING" "Only $AGENT_FILES agent files found"
fi

# Check critical directories exist
CRITICAL_DIRS=(
    "/home/byron/.claude"
    "/home/byron/.claude/agents" 
    "/home/byron/.claude/docs"
    "/home/byron/.claude/scripts"
    "/home/byron/.claude/logs"
)

MISSING_DIRS=0
for dir in "${CRITICAL_DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
        log_health "DIRECTORIES" "ERROR" "Missing directory: $dir"
        ((MISSING_DIRS++))
    fi
done

if [[ "$MISSING_DIRS" -eq 0 ]]; then
    log_health "DIRECTORIES" "HEALTHY" "All critical directories exist"
fi

# Check hybrid architecture documentation is current
DOCS_CURRENT=true
if [[ ! -f "/home/byron/.claude/docs/agent-context-analysis.md" ]]; then
    log_health "DOCUMENTATION" "WARNING" "Agent context analysis missing"
    DOCS_CURRENT=false
fi

if [[ ! -f "/home/byron/.claude/docs/hybrid-mcp-conversion-goals.md" ]]; then
    log_health "DOCUMENTATION" "WARNING" "Hybrid MCP goals documentation missing"
    DOCS_CURRENT=false
fi

if [[ "$DOCS_CURRENT" == true ]]; then
    log_health "DOCUMENTATION" "HEALTHY" "Architecture documentation current"
fi

# Check disk space for logs
LOG_SPACE=$(df /home/byron/.claude/logs 2>/dev/null | awk 'NR==2 {print $4}' || echo "0")
LOG_SPACE=$(echo "$LOG_SPACE" | tr -d '\n\r' | grep -o '[0-9]*' || echo "0")
if [[ "$LOG_SPACE" -gt 1000000 ]]; then  # >1GB free
    log_health "DISK_SPACE" "HEALTHY" "${LOG_SPACE}KB available"
else
    log_health "DISK_SPACE" "WARNING" "Low disk space: ${LOG_SPACE}KB"
fi

# Summary log entry
WARNINGS=$(grep "$TIMESTAMP.*WARNING" "$HEALTH_LOG" 2>/dev/null | wc -l || echo "0")
WARNINGS=$(echo "$WARNINGS" | tr -d '\n\r' | grep -o '[0-9]*' || echo "0")
ERRORS=$(grep "$TIMESTAMP.*ERROR" "$HEALTH_LOG" 2>/dev/null | wc -l || echo "0") 
ERRORS=$(echo "$ERRORS" | tr -d '\n\r' | grep -o '[0-9]*' || echo "0")

if [[ "$ERRORS" -gt 0 ]]; then
    log_health "SESSION_HEALTH" "ERROR" "$ERRORS errors, $WARNINGS warnings"
elif [[ "$WARNINGS" -gt 0 ]]; then
    log_health "SESSION_HEALTH" "WARNING" "$WARNINGS warnings detected"
else
    log_health "SESSION_HEALTH" "HEALTHY" "All systems operational"
fi

# Exit successfully (don't block session start)
exit 0