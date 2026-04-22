#!/bin/bash

# TDD Compliance Analysis Script
# Analyzes TDD enforcement logs alongside MCP usage for hybrid architecture insights

set -euo pipefail

TDD_LOG="/home/byron/.claude/logs/tdd-enforcement.log"
MCP_LOG="/home/byron/.claude/logs/mcp-usage.log"

echo "🧪 TDD Compliance Analysis Report"
echo "================================="
echo

if [[ ! -f "$TDD_LOG" ]]; then
    echo "No TDD enforcement log found. Hook may not have been triggered yet."
    exit 1
fi

# TDD Enforcement Statistics
TOTAL_CHECKS=$(wc -l < "$TDD_LOG" 2>/dev/null || echo "0")
BLOCKS=$(grep -c "BLOCK" "$TDD_LOG" 2>/dev/null || echo "0")
ALLOWS=$(grep -c "ALLOW" "$TDD_LOG" 2>/dev/null || echo "0")

echo "📊 TDD Enforcement Summary:"
echo "---------------------------"
echo "  Total enforcement checks: $TOTAL_CHECKS"
echo "  Blocked (no tests): $BLOCKS"
echo "  Allowed: $ALLOWS"

if [[ "$TOTAL_CHECKS" -gt 0 ]]; then
    COMPLIANCE_RATE=$(( (ALLOWS * 100) / TOTAL_CHECKS ))
    echo "  TDD compliance rate: ${COMPLIANCE_RATE}%"
fi

echo

# Breakdown by reason
echo "🚦 Enforcement Breakdown:"
echo "-------------------------"
if grep -q "HAS_TESTS" "$TDD_LOG" 2>/dev/null; then
    HAS_TESTS=$(grep -c "HAS_TESTS" "$TDD_LOG")
    echo "  ✅ Allowed (has tests): $HAS_TESTS"
fi
if grep -q "NO_TESTS" "$TDD_LOG" 2>/dev/null; then
    NO_TESTS=$(grep -c "NO_TESTS" "$TDD_LOG")
    echo "  ❌ Blocked (no tests): $NO_TESTS"
fi
if grep -q "TEST_FILE" "$TDD_LOG" 2>/dev/null; then
    TEST_FILES=$(grep -c "TEST_FILE" "$TDD_LOG")
    echo "  🧪 Test file modifications: $TEST_FILES"
fi
if grep -q "CONFIG_FILE" "$TDD_LOG" 2>/dev/null; then
    CONFIG_FILES=$(grep -c "CONFIG_FILE" "$TDD_LOG")
    echo "  ⚙️  Config/doc files: $CONFIG_FILES"
fi

echo

# Recently blocked files
echo "📋 Recent Enforcement Actions:"
echo "------------------------------"
tail -10 "$TDD_LOG" | while IFS=',' read timestamp action reason file_path; do
    time_part=$(echo "$timestamp" | cut -d' ' -f2)
    case "$action" in
        "BLOCK") echo "  $time_part ❌ BLOCKED: $file_path ($reason)" ;;
        "ALLOW") echo "  $time_part ✅ ALLOWED: $file_path ($reason)" ;;
    esac
done

echo

# Today's TDD activity
TODAY=$(date '+%Y-%m-%d')
TODAY_BLOCKS=$(grep "^$TODAY.*BLOCK" "$TDD_LOG" 2>/dev/null | wc -l || echo "0")
TODAY_ALLOWS=$(grep "^$TODAY.*ALLOW" "$TDD_LOG" 2>/dev/null | wc -l || echo "0")

echo "📅 Today's TDD Activity ($TODAY):"
echo "---------------------------------"
echo "  Blocked attempts: $TODAY_BLOCKS"
echo "  Successful operations: $TODAY_ALLOWS"

# Integration with MCP usage (if available)
if [[ -f "$MCP_LOG" ]]; then
    echo
    echo "🔗 MCP Integration Insights:"
    echo "---------------------------"

    TODAY_MCP=$(grep "^$TODAY.*POST_TOOL" "$MCP_LOG" 2>/dev/null | wc -l || echo "0")
    echo "  MCP tool uses today: $TODAY_MCP"
    echo "  TDD checks today: $((TODAY_BLOCKS + TODAY_ALLOWS))"

    if [[ "$TODAY_MCP" -gt 0 && $((TODAY_BLOCKS + TODAY_ALLOWS)) -gt 0 ]]; then
        TDD_TO_MCP_RATIO=$(( ((TODAY_BLOCKS + TODAY_ALLOWS) * 100) / TODAY_MCP ))
        echo "  TDD enforcement ratio: ${TDD_TO_MCP_RATIO}% of MCP usage"
    fi
fi

echo
echo "🎯 TDD Quality Metrics:"
echo "----------------------"
if [[ "$BLOCKS" -eq 0 ]]; then
    echo "  ✅ Perfect TDD compliance - no blocks detected!"
    echo "  🚀 All code changes following test-first approach"
elif [[ "$BLOCKS" -lt "$ALLOWS" ]]; then
    echo "  ✅ Good TDD compliance - more allows than blocks"
    echo "  💡 Consider reinforcing test-first development"
else
    echo "  ⚠️  TDD compliance needs improvement"
    echo "  📚 Focus on writing tests before implementation"
fi

echo
echo "💡 Recommendations:"
echo "  • Write tests before implementation code"
echo "  • Use test-engineer agent for test generation"
echo "  • Check logs regularly: tail -f $TDD_LOG"
echo "  • Review blocked attempts for patterns"
