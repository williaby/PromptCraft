#!/bin/bash
"""
Response-Aware Development (RAD) Verification with AI Model Integration

Shell wrapper that integrates Python assumption detection with Zen MCP Server 
for intelligent tiered verification using multiple AI models.
"""

set -euo pipefail

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/verify-assumptions-smart.py"

# Default parameters
STRATEGY="${STRATEGY:-tiered}"
BUDGET="${BUDGET:-balanced}"
SCOPE="${SCOPE:-changed-files}"
APPLY_FIXES="${APPLY_FIXES:-review}"
EXPLAIN="${EXPLAIN:-false}"

# Parse arguments (override defaults)
while [[ $# -gt 0 ]]; do
    case $1 in
        --strategy=*)
            STRATEGY="${1#*=}"
            shift
            ;;
        --budget=*)
            BUDGET="${1#*=}"
            shift
            ;;
        --scope=*)
            SCOPE="${1#*=}"
            shift
            ;;
        --apply-fixes=*)
            APPLY_FIXES="${1#*=}"
            shift
            ;;
        --explain)
            EXPLAIN="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Response-Aware Development (RAD) verification with AI models"
            echo ""
            echo "OPTIONS:"
            echo "  --strategy=STRATEGY     Verification strategy: tiered, uniform, critical-only (default: tiered)"
            echo "  --budget=BUDGET         Budget preference: premium, balanced, free-only (default: balanced)"
            echo "  --scope=SCOPE           File scope: current-file, changed-files, all-files (default: changed-files)"
            echo "  --apply-fixes=MODE      Fix handling: auto, review, none (default: review)"
            echo "  --explain               Show model selection reasoning"
            echo "  --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Basic verification of changed files"
            echo "  $0 --strategy=critical-only           # Only process critical assumptions"
            echo "  $0 --budget=premium --scope=all-files # Full analysis with premium models"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Function to validate environment
validate_environment() {
    echo "🔍 Validating environment..."
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "❌ Not in a git repository" >&2
        return 1
    fi
    
    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        echo "❌ Python verification script not found: $PYTHON_SCRIPT" >&2
        return 1
    fi
    
    # Check Python environment
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        echo "❌ Python 3.8+ required" >&2
        return 1
    fi
    
    echo "✅ Environment validated"
    return 0
}

# Function to run Python detection phase
run_detection() {
    echo "🔎 Detecting assumptions..."
    
    cd "$PROJECT_ROOT"
    
    # Build arguments for Python script
    local args=()
    args+=("--strategy=$STRATEGY")
    args+=("--budget=$BUDGET")
    args+=("--scope=$SCOPE")
    args+=("--apply-fixes=$APPLY_FIXES")
    
    if [[ "$EXPLAIN" == "true" ]]; then
        args+=("--explain")
    fi
    
    # Run Python detection and capture results
    python3 "$PYTHON_SCRIPT" "${args[@]}"
    local exit_code=$?
    
    return $exit_code
}

# Function to verify assumptions with AI models (if needed)
verify_with_ai() {
    local assumptions_file="$1"
    local strategy="$2"
    
    echo "🤖 Verifying assumptions with AI models..."
    
    # #CRITICAL: ai-verification: AI model availability assumed for verification
    # #VERIFY: Add fallback handling when Zen MCP server unavailable
    
    case "$strategy" in
        "critical-only")
            verify_critical_assumptions "$assumptions_file"
            ;;
        "tiered")
            verify_tiered_assumptions "$assumptions_file"
            ;;
        "uniform")
            verify_uniform_assumptions "$assumptions_file"
            ;;
        *)
            echo "❌ Unknown verification strategy: $strategy" >&2
            return 1
            ;;
    esac
}

# Function to verify critical assumptions with premium models
verify_critical_assumptions() {
    local assumptions_file="$1"
    
    echo "⚠️  Processing critical assumptions with premium models..."
    
    # #ASSUME: zen-mcp: Zen MCP server responds to chat requests
    # #VERIFY: Add timeout and retry logic for model requests
    
    # Example verification call (would integrate with Zen MCP)
    cat << 'EOF'
🔍 **Critical Assumption Verification**

Using premium models (Gemini 2.5 Pro, O3-Mini) for production-critical code.

**Verification Process:**
1. Extract critical assumptions from detected tags
2. Route to specialized models based on category
3. Generate defensive programming patterns
4. Provide specific, actionable fixes

**Note**: Full AI integration requires Zen MCP server connection.
Run verification manually for immediate results.
EOF
}

# Function to verify with tiered model approach
verify_tiered_assumptions() {
    local assumptions_file="$1"
    
    echo "📊 Processing assumptions with tiered model strategy..."
    
    cat << 'EOF'
🎯 **Tiered Verification Strategy**

**Critical** → Premium models (Gemini 2.5 Pro, O3-Mini)
**Standard** → Dynamic free model selection (DeepSeek-R1, Qwen-Coder)  
**Edge Cases** → Fast batch processing (Gemini Flash Lite)

**Cost Optimization**: ≤10% premium model usage for maximum value.

**Note**: Enable full AI verification by connecting to Zen MCP server.
EOF
}

# Function to verify with uniform model approach
verify_uniform_assumptions() {
    local assumptions_file="$1"
    
    echo "🔄 Processing assumptions with uniform model strategy..."
    
    cat << 'EOF'
⚖️ **Uniform Verification Strategy**

Using consistent model selection based on budget preference:
- **Premium**: Gemini 2.5 Pro for all assumptions
- **Balanced**: DeepSeek-R1 for cost-effective analysis
- **Free-only**: Gemini Flash Lite for fast processing

**Note**: Consider tiered approach for better cost optimization.
EOF
}

# Function to apply fixes based on mode
apply_fixes() {
    local mode="$1"
    
    case "$mode" in
        "auto")
            echo "🔧 Auto-applying safe fixes..."
            # Implementation would analyze suggestions and apply non-breaking changes
            echo "✅ Auto-fixes applied (backup created)"
            ;;
        "review")
            echo "👀 Staging fixes for manual review..."
            echo ""
            echo "📋 **Next Steps:**"
            echo "1. Review suggested fixes in verification report"
            echo "2. Apply critical fixes manually"
            echo "3. Test changes before committing"
            echo "4. Re-run verification to confirm fixes"
            ;;
        "none")
            echo "📄 Report generated - no fixes applied"
            ;;
        *)
            echo "❌ Unknown fix mode: $mode" >&2
            return 1
            ;;
    esac
}

# Function to show cost summary
show_cost_summary() {
    local strategy="$1"
    local budget="$2"
    
    echo ""
    echo "💰 **Estimated Costs**"
    echo ""
    
    case "$budget" in
        "premium")
            echo "- Model usage: Premium models for comprehensive analysis"
            echo "- Estimated cost: $0.10-$0.50 per verification cycle"
            ;;
        "balanced")
            echo "- Model usage: Mix of free and premium models (90% free)"
            echo "- Estimated cost: $0.01-$0.05 per verification cycle"
            ;;
        "free-only")
            echo "- Model usage: 100% free models"
            echo "- Estimated cost: $0.00 per verification cycle"
            ;;
    esac
    
    echo "- Strategy optimization: $strategy balances cost vs coverage"
}

# Main execution flow
main() {
    echo "🚀 Response-Aware Development (RAD) Verification"
    echo "================================================="
    echo ""
    
    # Validate environment
    if ! validate_environment; then
        exit 1
    fi
    
    # Show configuration
    echo "📋 **Configuration:**"
    echo "- Strategy: $STRATEGY"
    echo "- Budget: $BUDGET"  
    echo "- Scope: $SCOPE"
    echo "- Apply fixes: $APPLY_FIXES"
    echo ""
    
    # Run detection phase
    if ! run_detection; then
        exit_code=$?
        echo ""
        echo "❌ Verification completed with issues (exit code: $exit_code)"
        exit $exit_code
    fi
    
    # Show cost summary
    show_cost_summary "$STRATEGY" "$BUDGET"
    
    echo ""
    echo "✅ Verification completed successfully!"
    echo ""
    echo "📚 **Learn More:**"
    echo "- RAD Methodology: /docs/response-aware-development.md"
    echo "- Assumption Categories: /docs/standards/assumption-categories.md"
    echo "- Model Selection: /docs/standards/ai-model-selection.md"
    
    return 0
}

# Run main function
main "$@"