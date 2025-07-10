---
category: workflow
complexity: medium
estimated_time: "10-15 minutes"
dependencies: ["workflow-scope-analysis"]
sub_commands: []
version: "1.0"
---

# Workflow Plan Validation

Create and validate implementation plan against defined scope boundaries: $ARGUMENTS

## Usage Options

- `phase X issue Y` - Standard planning with validation
- `quick phase X issue Y` - Essential plan creation only
- `expert phase X issue Y` - Plan with IT manager consultation

## Prerequisites

This command requires completed scope analysis. If not done, run:

```bash
/project:workflow-scope-analysis phase X issue Y
```

## Instructions

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

For expert mode, use Zen to consult with Gemini in IT manager role:

<!-- TODO: Fix hardcoded model reference - should use configurable model selection -->

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
# Standard plan validation
/project:workflow-plan-validation phase 1 issue 3

# Quick plan creation
/project:workflow-plan-validation quick phase 2 issue 7

# Expert mode with IT manager consultation
/project:workflow-plan-validation expert phase 1 issue 1
```

## Next Steps

After user approval:

- Proceed to `/project:workflow-implementation`
- Maintain strict adherence to approved plan
- Use todo tracking for progress monitoring
