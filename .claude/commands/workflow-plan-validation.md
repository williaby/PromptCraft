---
category: workflow
complexity: medium
estimated_time: "10-15 minutes"
dependencies: ["workflow-scope-analysis"]
sub_commands: []
version: "1.1"
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

### Environment Prerequisites Validation

1. **Validate Environment Readiness**:
   - Run environment validation using setup_validator.py
   - Ensure all development tools are properly configured
   - Verify prerequisite issues are completed before planning
   - Check that environment meets current issue requirements

2. **File Change Logging** (MANDATORY):
   - Log ALL file changes to `docs/planning/claude-file-change-log.md`
   - Format: `YYYY-MM-DD HH:MM:SS | CHANGE_TYPE | RELATIVE_FILE_PATH`
   - Change types: ADDED, MODIFIED, DELETED

```bash
# Validate environment before planning
poetry run python src/utils/setup_validator.py --scope planning
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

### Step 2: Dependency Impact Analysis

1. **Analyze Dependencies from Scope Analysis**:
   - Review what this issue provides to dependent issues
   - Document what issues depend on this one's completion
   - Use dependencies to CLARIFY plan boundaries, not expand them
   - Ensure plan deliverables align with dependency expectations

2. **Plan Consistency with Dependencies**:
   - Verify plan outputs match what dependent issues expect
   - Check that prerequisite issues provide what this plan needs
   - Document any dependency conflicts early in planning
   - Prevent scope creep through clear dependency analysis

### Step 3: MANDATORY Scope Check

1. **Compare Action Plan Against Acceptance Criteria**:
   - **Remove any items not explicitly required**
   - Flag any plan items that exceed the defined scope
   - **Document why each plan item is necessary for acceptance criteria**

2. **Enhanced Scope Validation Questions**:
   - Does every action item directly address an acceptance criterion?
   - Are there any "nice to have" items that should be removed?
   - Does the plan stay within the estimated time?
   - Would this plan fully satisfy the acceptance criteria and nothing more?
   - Do plan deliverables align with dependency analysis without expanding scope?

### Step 4: IT Manager Consultation (Optional)

For expert mode, use Zen to consult with Gemini in IT manager role:
- **Lead with the scope boundary document**
- Present ONLY the acceptance criteria requirements
- Get approval that the scope is correctly understood
- Present action plan with scope validation
- Ensure no scope creep in the discussion

### Step 5: Automated Plan Consistency Checks

1. **Cross-check Plan Against Dependency Analysis**:
   - Verify each acceptance criterion has corresponding plan items
   - Check that plan deliverables match dependency expectations
   - Identify potential overlap with other issues or phases
   - Validate time estimates against plan complexity

2. **Automated Validation Criteria**:
   - Clear pass/fail criteria for each plan component
   - Measurable success indicators for plan items
   - Dependency alignment verification
   - Resource availability confirmation

### Step 6: Rollback Procedures

1. **Define Plan Rollback Strategy**:
   - Document rollback steps for each major plan component
   - Identify safe rollback points during implementation
   - Plan for dependency chain impact if rollback needed
   - Establish rollback criteria and decision points

2. **Rollback Documentation Requirements**:
   - Clear rollback triggers (when to abort implementation)
   - Step-by-step rollback procedures
   - Data preservation requirements during rollback
   - Communication plan for rollback scenarios

### Step 7: Final Scope Validation

**MANDATORY FINAL CHECK**:
- Review action plan against original acceptance criteria one more time
- Remove any items that crept in during consultation
- Ensure plan addresses all acceptance criteria and nothing more
- Document final scope validation sign-off

## Output Format

Generate file: `/docs/planning/{phase}_{issue}_issue_plan.md`

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
