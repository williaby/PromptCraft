#!/bin/bash
set -euo pipefail  # Fail on errors, undefined vars, pipe failures
# Shared model utilities for slash commands
# Provides model name conversion and configuration management

# Validate model name contains only safe characters
validate_model_name() {
    local model="$1"
    # Ensure model name contains only safe characters: letters, numbers, /, -, :
    if [[ "$model" =~ ^[a-zA-Z0-9/_:-]+$ ]]; then
        return 0
    else
        echo "⚠️  Invalid model name: $model" >&2
        return 1
    fi
}

# Convert user-friendly model names to proper OpenRouter format
convert_model_name() {
    local model_name="$1"

    # Validate input first
    if ! validate_model_name "$model_name"; then
        echo "deepseek/deepseek-chat-v3-0324:free"  # Safe fallback
        return 1
    fi
    case "$model_name" in
        # Anthropic Claude models
        "opus"|"opus-4"|"claude-opus") echo "anthropic/claude-opus-4" ;;
        "sonnet"|"sonnet-4"|"claude-sonnet") echo "anthropic/claude-sonnet-4" ;;
        "haiku"|"haiku-3.5"|"claude-haiku") echo "anthropic/claude-3.5-haiku" ;;

        # OpenAI models (via OpenRouter - these are what's accessible through chat)
        "o3"|"openai-o3") echo "openai/o3" ;;
        "o3-mini"|"o3mini") echo "openai/o3-mini" ;;
        "o3-pro") echo "openai/o3-pro" ;;
        "o4-mini"|"o4mini"|"mini") echo "openai/o4-mini" ;;

        # Note: Native OpenAI models (o3, o3-mini, etc.) are available through
        # different Zen tools but not through the chat interface we use

        # Google Gemini models
        "gemini-pro"|"gemini-2.5-pro") echo "google/gemini-2.5-pro" ;;
        "gemini-flash"|"gemini-2.5-flash") echo "google/gemini-2.5-flash" ;;
        "gemini-free"|"gemini-2.0-flash") echo "google/gemini-2.0-flash-exp:free" ;;

        # DeepSeek models
        "deepseek"|"deepseek-v3") echo "deepseek/deepseek-chat-v3-0324:free" ;;
        "deepseek-r1") echo "deepseek/deepseek-r1-0528:free" ;;
        "deepseek-r1-paid") echo "deepseek/deepseek-r1-0528" ;;

        # Microsoft models
        "phi-4") echo "microsoft/phi-4" ;;
        "phi-4-reasoning") echo "microsoft/mai-ds-r1:free" ;;  # phi-4-reasoning:free not accessible via chat
        "mai-ds") echo "microsoft/mai-ds-r1:free" ;;

        # Meta models (llama-4-maverick currently unavailable - 503 errors)
        # "llama-4") echo "meta-llama/llama-4-maverick:free" ;;

        # Mistral models
        "mistral-large") echo "mistralai/mistral-large-2411" ;;
        "mistral-nemo") echo "mistralai/mistral-nemo:free" ;;

        # Qwen models
        "qwen-32b") echo "qwen/qwen3-32b:free" ;;
        "qwen-14b") echo "qwen/qwen3-14b:free" ;;
        "qwq") echo "qwen/qwq-32b:free" ;;

        # Return as-is if already properly formatted or unknown
        *) echo "$model_name" ;;
    esac
}

# Get model override from arguments with fallback
get_model_override() {
    local role="$1"
    local arguments="$2"
    local default_model="$3"

    # Check for global model override first
    local global_override
    global_override=$(echo "$arguments" | grep -oP "\-\-model=\K[^\s]+" || echo "")
    if [[ -n "$global_override" ]]; then
        convert_model_name "$global_override"
        return
    fi

    # Check for role-specific override
    local role_override
    role_override=$(echo "$arguments" | grep -oP "\-\-${role}\-model=\K[^\s]+" || echo "")
    if [[ -n "$role_override" ]]; then
        convert_model_name "$role_override"
        return
    fi

    # Return converted default
    convert_model_name "$default_model"
}

# Test if a model is available via Zen MCP
zen_test_model() {
    local model="$1"
    # Simple test call - adjust based on actual Zen MCP interface
    timeout 10s zen models test "$model" >/dev/null 2>&1
}

# Get fallback model chain based on model category
get_fallback_chain() {
    local category="$1"
    case "$category" in
        "premium-reasoning")
            echo "openai/o3 openai/o3-mini anthropic/claude-opus-4 microsoft/phi-4"
            ;;
        "premium-analysis")
            echo "anthropic/claude-opus-4 anthropic/claude-sonnet-4 google/gemini-2.5-pro openai/o3"
            ;;
        "large-context")
            echo "google/gemini-2.5-pro google/gemini-2.5-flash google/gemini-2.0-flash-exp:free deepseek/deepseek-chat-v3-0324:free"
            ;;
        "free-reasoning")
            echo "deepseek/deepseek-r1-0528:free microsoft/mai-ds-r1:free tngtech/deepseek-r1t2-chimera:free"
            ;;
        "free-general")
            echo "deepseek/deepseek-chat-v3-0324:free google/gemini-2.0-flash-exp:free qwen/qwen3-32b:free"
            ;;
        *)
            echo "deepseek/deepseek-chat-v3-0324:free google/gemini-2.0-flash-exp:free"
            ;;
    esac
}

# Select best available model from a chain
select_available_model() {
    local model_chain="$1"
    local model_array
    read -ra model_array <<< "$model_chain"

    for model in "${model_array[@]}"; do
        if zen_test_model "$model" 2>/dev/null; then
            echo "$model"
            return 0
        fi
    done
    # Return first free model as last resort
    echo "deepseek/deepseek-chat-v3-0324:free"
}

# Smart model selection based on task requirements
smart_model_select() {
    local task_type="$1"
    local arguments="$2"
    local allow_premium="${3:-true}"

    case "$task_type" in
        "planning")
            if [[ "$allow_premium" == "true" ]]; then
                get_model_override "planning" "$arguments" "google/gemini-2.5-pro"
            else
                get_model_override "planning" "$arguments" "deepseek/deepseek-chat-v3-0324:free"
            fi
            ;;
        "testing")
            if [[ "$allow_premium" == "true" ]]; then
                get_model_override "testing" "$arguments" "openai/o3"
            else
                get_model_override "testing" "$arguments" "microsoft/mai-ds-r1:free"
            fi
            ;;
        "review")
            if [[ "$allow_premium" == "true" ]]; then
                get_model_override "review" "$arguments" "anthropic/claude-opus-4"
            else
                get_model_override "review" "$arguments" "deepseek/deepseek-chat-v3-0324:free"
            fi
            ;;
        "consensus")
            get_model_override "consensus" "$arguments" "deepseek/deepseek-chat-v3-0324:free"
            ;;
        *)
            get_model_override "general" "$arguments" "deepseek/deepseek-chat-v3-0324:free"
            ;;
    esac
}

# Wrapper for Zen MCP calls with error handling
zen_mcp_call() {
    local model="$1"
    shift
    local args=("$@")

    echo "🤖 Calling $model via Zen MCP..."

    # Attempt the call with timeout and error handling
    if ! timeout 300s zen chat --model="$model" "${args[@]}"; then
        echo "⚠️  Call failed for $model, trying fallback..."

        # Try a free fallback
        local fallback_model="deepseek/deepseek-chat-v3-0324:free"
        if [[ "$model" != "$fallback_model" ]]; then
            echo "🔄 Retrying with fallback: $fallback_model"
            timeout 300s zen chat --model="$fallback_model" "${args[@]}"
        else
            echo "❌ Both primary and fallback models failed"
            return 1
        fi
    fi
}

# Multi-model consensus wrapper
zen_mcp_consensus() {
    local models_arg=""
    local topic=""
    local request=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --models)
                models_arg="$2"
                shift 2
                ;;
            --topic)
                topic="$2"
                shift 2
                ;;
            --request)
                request="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    echo "🤝 Building consensus across models: $models_arg"

    # Convert comma-separated models to array
    IFS=',' read -ra MODELS <<< "$models_arg"

    # Use Zen consensus tool if available, otherwise sequential calls
    if command -v zen >/dev/null && zen consensus --help >/dev/null 2>&1; then
        zen consensus --models="$models_arg" --topic="$topic" --request="$request"
    else
        echo "🔄 Sequential consensus (zen consensus not available)"
        for model in "${MODELS[@]}"; do
            echo "--- $model perspective ---"
            zen_mcp_call "$model" --request "$request (Topic: $topic)"
        done
    fi
}

# Export functions for use in slash commands
export -f validate_model_name
export -f convert_model_name
export -f get_model_override
export -f zen_test_model
export -f get_fallback_chain
export -f select_available_model
export -f smart_model_select
export -f zen_mcp_call
export -f zen_mcp_consensus
