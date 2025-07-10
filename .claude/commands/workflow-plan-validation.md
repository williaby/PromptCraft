---
category: workflow
complexity: medium
estimated_time: "10-15 minutes"
dependencies: ["workflow-scope-analysis"]
sub_commands: []
version: "1.1"
models_required: ["planning", "validation"]
model_preferences:
  planning: ["google/gemini-2.5-pro", "deepseek/deepseek-chat-v3-0324:free"]
  validation: ["deepseek/deepseek-chat-v3-0324:free", "anthropic/claude-sonnet-4"]
---

# Workflow Plan Validation

Create and validate implementation plan against defined scope boundaries: $ARGUMENTS

## Usage Options

- `phase X issue Y` - Standard planning with validation
- `quick phase X issue Y` - Essential plan creation only
- `expert phase X issue Y` - Plan with IT manager consultation
- `--model=[name]` - Override default model (auto-converts to proper format)
- `--planning-model=[name]` - Specific model for planning phase
- `--validation-model=[name]` - Specific model for validation phase

**Automatic Branch Creation**: Creates `phase-{X}-issue-{Y}-[description]` branch if not already on appropriate issue branch.

## Prerequisites

This command requires completed scope analysis. If not done, run:

```bash
/project:workflow-scope-analysis phase X issue Y
```

## Instructions

### Step 0: Automatic Setup

1. **Parse Arguments and Detect Phase/Issue**:
   ```bash
   # Extract phase and issue from $ARGUMENTS
   PHASE=$(echo "$ARGUMENTS" | grep -oP "phase\s+\K\d+" || echo "1")
   ISSUE=$(echo "$ARGUMENTS" | grep -oP "issue\s+\K\d+" || echo "")
   MODE=$(echo "$ARGUMENTS" | grep -oP "^(quick|expert)" || echo "standard")

   # Parse model overrides
   PLANNING_MODEL=$(echo "$ARGUMENTS" | grep -oP "\-\-planning\-model=\K[^\s]+" || echo "")
   VALIDATION_MODEL=$(echo "$ARGUMENTS" | grep -oP "\-\-validation\-model=\K[^\s]+" || echo "")
   OVERRIDE_MODEL=$(echo "$ARGUMENTS" | grep -oP "\-\-model=\K[^\s]+" || echo "")
   ```

2. **Auto-Create Issue Branch** (if not on appropriate branch):
   ```bash
   CURRENT_BRANCH=$(git branch --show-current)
   EXPECTED_PHASE_BRANCH="feature/phase-${PHASE}-development"
   ISSUE_PATTERN="phase-${PHASE}-issue-${ISSUE}"

   if [[ ! "$CURRENT_BRANCH" =~ $ISSUE_PATTERN ]]; then
       # Generate issue description from scope analysis or user input
       ISSUE_DESC=$(echo "$ARGUMENTS" | sed 's/phase [0-9]* issue [0-9]*//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | tr ' ' '-')
       NEW_BRANCH="feature/phase-${PHASE}-issue-${ISSUE}-${ISSUE_DESC}"

       echo "🔄 Creating issue branch: $NEW_BRANCH"
       git checkout "$EXPECTED_PHASE_BRANCH" 2>/dev/null || git checkout -b "$EXPECTED_PHASE_BRANCH"
       git checkout -b "$NEW_BRANCH"
   fi
   ```

3. **Configure Models with Smart Conversion**:
   ```bash
   # Convert user-friendly names to proper model names
   convert_model_name() {
       case "$1" in
           "opus"|"opus-4"|"claude-opus") echo "anthropic/claude-opus-4" ;;
           "sonnet"|"sonnet-4"|"claude-sonnet") echo "anthropic/claude-sonnet-4" ;;
           "o3"|"openai-o3") echo "openai/o3" ;;
           "o3-mini") echo "openai/o3-mini" ;;
           "o3-pro") echo "openai/o3-pro" ;;
           "o4-mini") echo "openai/o4-mini" ;;
           "gemini-pro"|"gemini-2.5-pro") echo "google/gemini-2.5-pro" ;;
           "gemini-flash"|"gemini-2.5-flash") echo "google/gemini-2.5-flash" ;;
           "gemini-free"|"gemini-2.0-flash") echo "google/gemini-2.0-flash-exp:free" ;;
           "deepseek"|"deepseek-v3") echo "deepseek/deepseek-chat-v3-0324:free" ;;
           "deepseek-r1") echo "deepseek/deepseek-r1-0528:free" ;;
           *) echo "$1" ;;  # Return as-is if already properly formatted
       esac
   }

   # Set planning model (with fallback chain)
   if [[ -n "$OVERRIDE_MODEL" ]]; then
       PLANNING_MODEL=$(convert_model_name "$OVERRIDE_MODEL")
       VALIDATION_MODEL=$(convert_model_name "$OVERRIDE_MODEL")
   else
       PLANNING_MODEL=${PLANNING_MODEL:-$(convert_model_name "gemini-pro")}
       VALIDATION_MODEL=${VALIDATION_MODEL:-$(convert_model_name "deepseek-v3")}
   fi

   # Add free model for validation unless using free model already
   if [[ ! "$PLANNING_MODEL" =~ ":free" ]] && [[ "$MODE" != "quick" ]]; then
       VALIDATION_FREE_MODEL="deepseek/deepseek-chat-v3-0324:free"
   fi
   ```

### Step 1: Create Initial Action Plan

1. **Address ONLY Items in Acceptance Criteria**:
   - Break down into phases with time estimates
   - Include testing for acceptance criteria only
   - Consider code reuse from ledgerbase, FISProject, .github, PromptCraft repositories

2. **Follow Development Philosophy**:
   - **Reuse First**: Check existing repositories for solutions
   - **Configure Don't Build**: Use Zen MCP Server, Heimdall MCP Server, AssuredOSS packages
   - **Focus on Unique Value**: Build only what's truly unique to PromptCraft

### Step 2: MANDATORY Scope Check

1. **Compare Action Plan Against Acceptance Criteria**:
   - **Remove any items not explicitly required**
   - Flag any plan items that exceed the defined scope
   - **Document why each plan item is necessary for acceptance criteria**

2. **Scope Validation Questions**:
   - Does every action item directly address an acceptance criterion?
   - Are there any "nice to have" items that should be removed?
   - Does the plan stay within the estimated time?
   - Would this plan fully satisfy the acceptance criteria and nothing more?

### Step 3: IT Manager Consultation (Optional)

For expert mode, use Zen MCP Server for strategic planning consultation:

```bash
# Use configured planning model with free model validation
if [[ "$MODE" == "expert" ]]; then
    echo "🧠 Strategic Planning Consultation using: $PLANNING_MODEL"

    # Primary strategic analysis
    zen_mcp_call "$PLANNING_MODEL" \
        --role "IT Manager and Strategic Planner" \
        --context "Project scope validation and strategic planning" \
        --input "scope_boundary_document.md" \
        --request "Review acceptance criteria and validate action plan scope"

    # Free model validation (if using premium model)
    if [[ -n "$VALIDATION_FREE_MODEL" ]]; then
        echo "✅ Validation check using: $VALIDATION_FREE_MODEL"
        zen_mcp_call "$VALIDATION_FREE_MODEL" \
            --role "Technical Reviewer" \
            --request "Quick scope validation - identify any scope creep or missing items"
    fi
fi
```

**Key Requirements:**
- **Lead with the scope boundary document**
- Present ONLY the acceptance criteria requirements
- Get approval that the scope is correctly understood
- Present action plan with scope validation
- Ensure no scope creep in the discussion

### Step 4: Final Scope Validation

**MANDATORY FINAL CHECK**:

- Review action plan against original acceptance criteria one more time
- Remove any items that crept in during consultation
- Ensure plan addresses all acceptance criteria and nothing more
- Document final scope validation sign-off

## Output Format

Generate file: `/docs/planning/issue-plans/phase-{phase}-issue-{issue}-plan.md`

```markdown
---
title: "Phase {X} Issue {Y}: [Issue Title]"
version: "1.0"
status: "draft"
component: "Implementation-Plan"
tags: ["phase-{X}", "issue-{Y}", "implementation"]
purpose: "Implementation plan for resolving Phase {X} Issue {Y}"
---

# Phase {X} Issue {Y}: [Issue Title]

## Scope Boundary Analysis
✅ **INCLUDED in Issue**: [Items from acceptance criteria]
❌ **EXCLUDED from Issue**: [Items NOT in acceptance criteria]
🔍 **Scope Validation**: [Confirmation each action item maps to acceptance criteria]

## Issue Requirements
[Detailed requirements from analysis]

## Action Plan Scope Validation
- [ ] Every action item addresses a specific acceptance criterion
- [ ] No "nice to have" items included
- [ ] Plan stays within estimated time bounds
- [ ] Implementation satisfies acceptance criteria completely

## Action Plan
[Comprehensive implementation strategy]

## Testing Strategy
[Validation and testing approach]

## Dependencies and Prerequisites
[Required components and setup]

## Success Criteria
[How to know the issue is resolved]
```

## User Approval Process

**CRITICAL**: Present the planning document to the user and explicitly ask for approval before proceeding with implementation.

## Error Handling

- **Missing scope analysis**: Auto-run `/project:workflow-scope-analysis` first
- **Scope creep detected**: Highlight items that exceed boundaries
- **Plan-scope mismatch**: Generate specific warnings about misalignment
- **Time estimate exceeded**: Suggest scope reduction or time re-estimation

## Examples

```bash
# Standard plan validation (auto-creates phase-1-issue-3-[description] branch)
/project:workflow-plan-validation phase 1 issue 3

# Quick plan creation with model override
/project:workflow-plan-validation quick phase 2 issue 7 --model=opus-4

# Expert mode with specific models
/project:workflow-plan-validation expert phase 1 issue 1 --planning-model=gemini-pro --validation-model=deepseek

# Using user-friendly model names (auto-converted)
/project:workflow-plan-validation phase 3 issue 5 --model=o3
/project:workflow-plan-validation expert phase 1 issue 2 --planning-model=sonnet
```

## Model Conversion Reference

**User-Friendly Names → Proper Model Names:**
- `opus`, `opus-4`, `claude-opus` → `anthropic/claude-opus-4`
- `sonnet`, `sonnet-4`, `claude-sonnet` → `anthropic/claude-sonnet-4`
- `o3`, `openai-o3` → `openai/o3`
- `gemini-pro`, `gemini-2.5-pro` → `google/gemini-2.5-pro`
- `gemini-free`, `gemini-2.0-flash` → `google/gemini-2.0-flash-exp:free`
- `deepseek`, `deepseek-v3` → `deepseek/deepseek-chat-v3-0324:free`

## Next Steps

After user approval:

- Proceed to `/project:workflow-implementation`
- Maintain strict adherence to approved plan
- Use todo tracking for progress monitoring
