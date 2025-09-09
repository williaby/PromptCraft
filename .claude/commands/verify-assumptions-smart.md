---
argument-hint: [--strategy=tiered] [--budget=balanced] [--scope=changed-files] [--explain] [--apply-fixes=review]
description: Intelligent tiered verification of code assumptions using multiple AI models
allowed-tools: Bash(git:*), Read, Grep, mcp__zen__chat, mcp__zen__dynamic_model_selector
---

# Verify Assumptions Smart - Tiered AI Model Verification

You are implementing the **Response-Aware Development (RAD)** methodology to systematically verify code assumptions using multiple AI models based on risk levels.

## Task Overview

Analyze code for assumption tags and route them to appropriate AI models:

- **#CRITICAL:** → Premium models (Gemini 2.5 Pro, O3-Mini)
- **#ASSUME:** → Dynamic free model selection (DeepSeek-R1, Qwen-Coder)
- **#EDGE:** → Fast batch processing (Gemini Flash Lite)

## Arguments Processing

Parse the following arguments from `$ARGUMENTS`:

- `--strategy`: `tiered` (default), `uniform`, `critical-only`
- `--budget`: `premium`, `balanced` (default), `free-only`
- `--scope`: `current-file`, `changed-files` (default), `all-files`
- `--explain`: Show model selection reasoning
- `--apply-fixes`: `auto`, `review` (default), `none`

## Implementation Steps

### 1. Parse Arguments and Set Defaults

```bash
# Extract arguments, default to balanced tiered approach
STRATEGY=$(echo "$ARGUMENTS" | grep -o '\--strategy=\w*' | cut -d'=' -f2 || echo "tiered")
BUDGET=$(echo "$ARGUMENTS" | grep -o '\--budget=\w*' | cut -d'=' -f2 || echo "balanced")
SCOPE=$(echo "$ARGUMENTS" | grep -o '\--scope=[\w-]*' | cut -d'=' -f2 || echo "changed-files")
```

### 2. Collect Assumptions by Scope

Based on scope parameter:

- **changed-files**: Use `git diff --name-only HEAD` and `git diff --name-only --cached`
- **current-file**: Focus on file in current context (if available)
- **all-files**: Search entire project for source files

Search for assumption patterns:

- `#CRITICAL:` - Production blockers, security, payments
- `#ASSUME:` - Standard assumptions, state management, APIs  
- `#EDGE:` - Edge cases, browser compatibility, performance

### 3. Categorize and Route Assumptions

**Critical Assumptions (Use Premium Models):**

- Payment/Financial → OpenAI O3-Mini or Gemini 2.5 Pro
- Security/Auth → Gemini 2.5 Pro
- Concurrency/Race → DeepSeek-R1 (free) or Gemini 2.5 Pro (paid)
- Database/Transactions → DeepSeek-R1

**Standard Assumptions (Use Dynamic Free Selection):**
Use `mcp__zen__dynamic_model_selector` with:

```
requirements: "Analyze code assumptions for [category]. Add defensive programming patterns and error handling."
model: "auto" 
complexity_level: "medium"
budget_preference: "cost-optimized"
```

**Edge Cases (Use Fast Free Models):**
Batch process with `mcp__zen__chat` using `gemini-2.0-flash-lite`.

### 4. Execute Verification Strategy

**Tiered Strategy:**

1. Process critical assumptions individually with premium models
2. Batch standard assumptions by category with free models  
3. Bulk process edge cases with fast models

**Critical-Only Strategy:**

1. Only process #CRITICAL: tagged assumptions
2. Use premium models exclusively
3. Skip standard and edge cases

**Uniform Strategy:**

1. Use same model for all assumptions
2. Model selection based on budget parameter

### 5. Generate Verification Report

Create comprehensive report with:

- **Summary**: Count of assumptions by category and processing time
- **Critical Issues**: Must fix before deploy (❌ BLOCKING status)
- **Standard Issues**: Should fix before PR (⚠️ REVIEW status)  
- **Edge Cases**: Can defer to backlog (💡 NOTE status)
- **Model Usage**: Explanation of model selection (if --explain used)
- **Cost Summary**: Estimated costs and free vs paid model usage
- **Next Steps**: Actionable checklist for fixes

### 6. Apply Fixes (If Requested)

Based on `--apply-fixes` parameter:

- **review**: Stage fixes for manual review with `git add -p`
- **auto**: Apply non-critical fixes automatically with backup
- **none**: Only report, no fixes applied

## Example Verification Prompts

### For Critical Assumptions

```
You are a senior security engineer reviewing production-critical code. You have NO knowledge of the original developer's intent.

## Code Context
File: [filename]:[line]
Assumption: [assumption text]
Category: [payment/security/concurrency]

## Task
1. Assume worst-case production conditions: high load, slow networks, unreliable services
2. Identify race conditions, timing dependencies, security vulnerabilities
3. Generate defensive code with proper error handling
4. Provide specific, actionable fixes

Focus on production failures, not theoretical issues.
```

### For Standard Assumptions  

```
You are a code reviewer focused on preventing bugs. Analyze this assumption under production stress conditions.

## Code Analysis
[code context]

Identify: state management issues, async timing problems, error handling gaps, validation missing

Generate: defensive programming patterns, proper error handling, validation logic
```

## Model Selection Logic

Implement intelligent routing:

```python
def select_model(assumption_text, category, budget):
    if budget == "free-only":
        return "deepseek/deepseek-r1" if "security" in category else "gemini-2.0-flash"
    elif "payment" in assumption_text.lower():
        return "openai/o3-mini" if budget == "premium" else "gemini-2.5-pro"  
    elif "security" in category or "auth" in assumption_text:
        return "gemini-2.5-pro"
    else:
        return "dynamic" # Let Zen choose best free model
```

## Success Criteria

Generate report showing:

- All assumptions found and categorized
- Appropriate model used for each risk level
- Concrete fixes for critical issues
- Cost-effective use of premium models (≤10% of total calls)
- Clear next steps for developer

## Error Handling

If no assumptions found:

```
# Assumption Verification Report

## Summary  
No assumption tags found in scope. Start using RAD methodology:

```javascript
// #CRITICAL: payment: Transaction assumed synchronous
// #VERIFY: Add timeout and retry logic
```

See: /docs/response-aware-development.md for complete guidance.

```

The goal is to catch production-breaking assumptions before they reach deployment while optimizing cost through intelligent model selection.
