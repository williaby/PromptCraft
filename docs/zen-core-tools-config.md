# Zen Server Core Tools Configuration

## Current Zen Tools Analysis

Based on the MCP context analysis, here are all zen tools and their recommended configuration:

### Core Tools (Always Loaded) - 3.5k tokens

- `chat` (1.4k tokens) - Essential for general AI collaboration
- `layered_consensus` (1.6k tokens) - Critical for multi-model analysis
- `challenge` (0.5k tokens) - Lightweight critical validation

### Specialty Tools (Agent-Only Loading) - 16k+ tokens

- `thinkdeep` (1.9k tokens) → deep-thinking-agent
- `codereview` (2.2k tokens) → code-reviewer agent
- `debug` (2.1k tokens) → debug-investigator agent
- `secaudit` (2.3k tokens) → security-auditor agent
- `docgen` (1.3k tokens) → documentation-writer agent
- `analyze` (2.1k tokens) → analysis-agent
- `refactor` (2.3k tokens) → refactor-specialist agent
- `listmodels` (0.4k tokens) → utility (low priority)
- `version` (0.4k tokens) → utility (low priority)

## Optimal DISABLED_TOOLS Configuration

```bash
DISABLED_TOOLS=thinkdeep,codereview,debug,secaudit,docgen,analyze,refactor,listmodels,version,planner,precommit,pr_prepare,pr_review,model_evaluator,dynamic_model_selector,routing_status,consensus,testgen,tracer
```

This configuration:

- ✅ Keeps only 3 core tools (3.5k tokens)
- ❌ Disables 9 specialty tools (16k+ tokens saved)
- 💾 **Total Savings**: ~16k tokens from zen alone
