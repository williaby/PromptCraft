---
category: workflow
complexity: medium
estimated_time: "10-15 minutes"
dependencies: []
sub_commands: []
version: "1.0"
---

# Workflow Scope Analysis

Analyze and define boundaries for a project issue to prevent scope creep: $ARGUMENTS

## Usage Options
- `phase X issue Y` - Standard analysis (e.g., "phase 1 issue 3")
- `quick phase X issue Y` - Essential boundary definition only
- `detailed phase X issue Y` - Comprehensive analysis with validation

## Instructions

### Step 1: Environment Prerequisites Validation

1. **Validate Environment Readiness** (if previous issues completed):
   - Run `poetry run python src/utils/setup_validator.py` if available
   - Check that prerequisite issues are completed
   - Validate environment meets requirements for current issue

2. **File Change Logging** (MANDATORY):
   - Log ALL file changes to `docs/planning/claude-file-change-log.md`
   - Format: `YYYY-MM-DD HH:MM:SS | CHANGE_TYPE | RELATIVE_FILE_PATH`
   - Change types: ADDED, MODIFIED, DELETED

### Step 2: Issue-Specific Analysis

1. **Read ONLY the Issue Definition First**:
   - `/docs/planning/phase-{X}-issues.md` - Find the SPECIFIC issue requirements
   - **STOP HERE** - Do not read broader documentation yet

2. **Extract and Isolate Issue Scope**:
   - Issue title and description
   - **Acceptance criteria** (this defines the boundary)
   - Dependencies listed in the issue
   - Testing requirements from the issue
   - Time estimates
   - **Document the EXACT scope boundary**

### Step 3: Dependency Cross-Referencing

1. **Identify Issue Dependencies** (Scope-Safe Analysis):
   - Scan `/docs/planning/phase-{X}-issues.md` for mentions of current issue
   - Document what issues depend ON this issue
   - Document what issues this issue depends ON
   - **Use dependency info to CLARIFY boundaries, not expand them**

2. **Boundary Clarification Through Dependencies**:
   ```
   DEPENDENCY CLARIFICATION:
   ✅ Current Issue Provides: [What this issue delivers to dependent issues]
   🔗 Dependent Issues: [What issues need this one completed]
   📋 Prerequisites: [What this issue requires from other issues]
   ❌ EXCLUDED: [What dependent issues will handle - NOT this issue]
   ```

### Step 4: Scope Boundary Validation

1. **Define Issue Boundaries**:
   - List what IS included in acceptance criteria
   - List what is NOT mentioned in acceptance criteria
   - Identify any ambiguous requirements that need clarification

2. **Automated Scope Boundary Validation**:
   - Cross-check acceptance criteria against dependency analysis
   - Verify each acceptance criterion has clear pass/fail criteria
   - Identify any acceptance criteria that might overlap with other issues
   - Validate time estimates against scope complexity

3. **Create Scope Constraint Document**:
   ```
   ISSUE SCOPE BOUNDARY:
   ✅ INCLUDED: [List from acceptance criteria]
   ❌ EXCLUDED: [Anything not in acceptance criteria]
   🔗 BOUNDARY CLARIFICATION: [How dependencies sharpen scope boundaries]
   ❓ UNCLEAR: [Items needing clarification]
   ✅ VALIDATION: [Automated checks passed]
   ```

### Step 5: Contextual Research (Only After Scope Definition)

**ONLY AFTER establishing scope boundaries**, read supporting documentation as needed:
- `/docs/planning/ADR.md` - Read ONLY architectural decisions relevant to your defined scope
- `/docs/planning/ts-{X}-overview.md` - Read ONLY sections relevant to your defined scope
- `/docs/planning/ts-{X}-implementation.md` - Read ONLY implementation details for items in scope
- `/docs/planning/project-hub.md` - Read ONLY if broader project context is needed for acceptance criteria
- `/docs/planning/four_journeys.md` - Read ONLY if journey context is explicitly mentioned in issue
- `/docs/planning/development.md` - Read ONLY for development standards relevant to acceptance criteria
- `README.md` - Read ONLY if basic project setup is part of acceptance criteria

**Research Constraint**: Only read sections that directly relate to items in your acceptance criteria. Skip all other content.

## Output Format

```markdown
# Scope Analysis: Phase {X} Issue {Y}

## Environment Prerequisites
- ✅ **Environment Status**: [Pass/Fail from validation]
- 📋 **Prerequisites Check**: [Previous issues completed status]
- 🔧 **Environment Ready**: [Yes/No for current issue requirements]

## Issue Overview
- **Title**: [Issue title]
- **Description**: [Brief description]
- **Estimated Time**: [From issue]

## Dependency Analysis
✅ **Current Issue Provides**:
- [What this issue delivers to dependent issues]

🔗 **Dependent Issues**:
- [What issues need this one completed]

📋 **Prerequisites**:
- [What this issue requires from other issues]

❌ **EXCLUDED** (Handled by Other Issues):
- [What dependent issues will handle - NOT this issue]

## Scope Boundaries
✅ **INCLUDED in Issue**:
- [Item 1 from acceptance criteria]
- [Item 2 from acceptance criteria]

❌ **EXCLUDED from Issue**:
- [Item not mentioned in acceptance criteria]
- [Another excluded item]

🔗 **BOUNDARY CLARIFICATION**:
- [How dependency analysis sharpens scope boundaries]

❓ **UNCLEAR Requirements**:
- [Ambiguous item needing clarification]

## Automated Validation
✅ **Scope Validation Checks**:
- [Cross-check results between acceptance criteria and dependencies]
- [Pass/fail criteria clarity verification]
- [Issue overlap validation]
- [Time estimate vs complexity validation]

## Next Steps
- Proceed to `/project:workflow-plan-validation` with these boundaries
- Address unclear requirements before planning
- Ensure environment prerequisites are met
```

## Error Handling

- **Environment validation fails**: Report specific failures and required fixes before proceeding
- **Issue file not found**: Report missing file path and suggest creating placeholder
- **No acceptance criteria**: Request clarification from user before proceeding
- **Ambiguous scope**: Generate specific clarifying questions
- **Dependencies missing**: List what needs to be resolved first
- **Dependency conflicts**: Flag issues where acceptance criteria overlap with other issues
- **Scope validation failures**: Report specific boundary validation issues

## Examples

```bash
# Standard scope analysis
/project:workflow-scope-analysis phase 1 issue 3

# Quick boundary definition
/project:workflow-scope-analysis quick phase 2 issue 7

# Detailed analysis with full validation
/project:workflow-scope-analysis detailed phase 1 issue 1
```
