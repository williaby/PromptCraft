#!/bin/bash

# MCP Usage Analysis Script
# Analyzes the MCP usage logs to provide insights into hybrid architecture performance

set -euo pipefail

LOG_FILE="/home/byron/.claude/logs/mcp-usage.log"
HEALTH_LOG="/home/byron/.claude/logs/session-health.log"

if [[ ! -f "$LOG_FILE" ]]; then
    echo "No MCP usage log found at $LOG_FILE"
    echo "Start using MCP tools to generate usage data."
    exit 1
fi

echo "🔍 MCP Usage Analysis Report"
echo "=================================="
echo

# Basic statistics
TOTAL_ENTRIES=$(grep -c "POST_TOOL" "$LOG_FILE" 2>/dev/null || echo "0")
echo "📊 Total MCP tool invocations: $TOTAL_ENTRIES"

if [[ "$TOTAL_ENTRIES" -eq 0 ]]; then
    echo "No MCP tool usage data available yet."
    exit 0
fi

# Agent usage breakdown
echo
echo "🤖 Agent Usage Breakdown:"
echo "-------------------------"
grep "POST_TOOL" "$LOG_FILE" | cut -d',' -f6 | sort | uniq -c | sort -nr | while read count agent; do
    echo "  $agent: $count invocations"
done

# MCP server usage
echo
echo "🌐 MCP Server Usage:"
echo "--------------------"
grep "POST_TOOL" "$LOG_FILE" | cut -d',' -f4 | grep -v "^$" | sort | uniq -c | sort -nr | while read count server; do
    echo "  $server: $count invocations"
done

# Most used tools
echo
echo "🛠️  Most Used MCP Tools:"
echo "------------------------"
grep "POST_TOOL" "$LOG_FILE" | cut -d',' -f3 | sort | uniq -c | sort -nr | head -10 | while read count tool; do
    echo "  $tool: $count times"
done

# Today's activity
TODAY=$(date '+%Y-%m-%d')
TODAY_COUNT=$(grep "^$TODAY" "$LOG_FILE" | grep -c "POST_TOOL" 2>/dev/null || echo "0")
echo
echo "📅 Today's Activity ($TODAY):"
echo "-----------------------------"
echo "  MCP tool invocations: $TODAY_COUNT"

# Recent activity (last 10 entries)
echo
echo "📝 Recent MCP Tool Usage (Last 10):"
echo "------------------------------------"
grep "POST_TOOL" "$LOG_FILE" | tail -10 | while IFS=',' read timestamp event tool server mcp_tool agent result exec_time; do
    time_part=$(echo "$timestamp" | cut -d' ' -f2)
    echo "  $time_part - $agent used $server::$mcp_tool"
done

# Performance metrics (if execution time is available)
echo
echo "⚡ Performance Insights:"
echo "------------------------"
CORE_TOOLS=$(grep "POST_TOOL.*core" "$LOG_FILE" | wc -l || echo "0")
AGENT_TOOLS=$(grep "POST_TOOL" "$LOG_FILE" | grep -v "core\|main-context" | wc -l || echo "0")

echo "  Core tools (main context): $CORE_TOOLS invocations"
echo "  Agent tools (specialized): $AGENT_TOOLS invocations"

if [[ "$AGENT_TOOLS" -gt 0 && "$CORE_TOOLS" -gt 0 ]]; then
    RATIO=$(( (AGENT_TOOLS * 100) / (CORE_TOOLS + AGENT_TOOLS) ))
    echo "  Agent tool usage ratio: ${RATIO}% (target: >80%)"
fi

# Health check summary (if available)
if [[ -f "$HEALTH_LOG" ]]; then
    echo
    echo "🏥 System Health Summary:"
    echo "-------------------------"
    RECENT_HEALTH=$(tail -5 "$HEALTH_LOG" | grep "SESSION_HEALTH" | tail -1)
    if [[ -n "$RECENT_HEALTH" ]]; then
        STATUS=$(echo "$RECENT_HEALTH" | cut -d',' -f3)
        MESSAGE=$(echo "$RECENT_HEALTH" | cut -d',' -f4)
        echo "  Latest status: $STATUS - $MESSAGE"
    fi
fi

echo
echo "🎯 Hybrid Architecture Status:"
echo "------------------------------"
if [[ "$AGENT_TOOLS" -gt "$CORE_TOOLS" ]]; then
    echo "  ✅ SUCCESS: Agents handling majority of MCP tool usage"
    echo "  ✅ Context optimization is working as designed"
else
    echo "  ⚠️  NOTICE: Core tools still heavily used"
    echo "  💡 Consider moving more tools to agent-only access"
fi

echo
echo "📈 Next Steps:"
echo "  • Continue using specialized agents for best efficiency"
echo "  • Run this analysis weekly to track optimization progress"
echo "  • Use 'tail -f $LOG_FILE' to monitor real-time usage"