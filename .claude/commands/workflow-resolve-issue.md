---
category: workflow
complexity: high
estimated_time: "60-90 minutes"
dependencies: []
sub_commands: ["workflow-scope-analysis", "workflow-plan-validation", "workflow-implementation", "workflow-review-cycle"]
version: "2.0"
---

# Workflow Resolve Issue (Orchestrator)

Systematically resolve any project issue through modular workflow orchestration: $ARGUMENTS

## Usage Options

- `quick phase X issue Y` - Essential workflow steps only (30-45 min)
- `standard phase X issue Y` - Full workflow with validation (60-90 min)
- `expert phase X issue Y` - Minimal prompts for experienced users (15-30 min)

## Workflow Components

This orchestrator executes the following workflow components in sequence:

### 1. Scope Analysis (`/project:workflow-scope-analysis`)

**Purpose**: Define issue boundaries and prevent scope creep

- Analyzes issue definition and acceptance criteria
- Creates scope boundary documentation
- Identifies dependencies and unclear requirements
- **Estimated Time**: 10-15 minutes

### 2. Plan Validation (`/project:workflow-plan-validation`)

**Purpose**: Create and validate implementation plan

- Develops action plan aligned with acceptance criteria
- Validates scope boundaries and removes scope creep
- Optional IT manager consultation via Zen
- **Estimated Time**: 10-15 minutes

### 3. Implementation (`/project:workflow-implementation`)

**Purpose**: Execute approved plan with quality standards

- Implements solution using subagents and MCP orchestration
- Follows security best practices and coding standards
- Maintains progress tracking and scope adherence
- **Estimated Time**: Variable based on issue complexity

### 4. Review Cycle (`/project:workflow-review-cycle`)

**Purpose**: Comprehensive testing and multi-agent validation

- Pre-commit validation and quality gate checks
- Multi-agent review (O3 testing, Gemini review)
- Consensus validation and final approval
- **Estimated Time**: 15-30 minutes

## Workflow Execution

### Quick Mode (`quick`)

```bash
/project:workflow-scope-analysis quick phase X issue Y
/project:workflow-implementation quick phase X issue Y
/project:workflow-review-cycle quick phase X issue Y
```

### Standard Mode (`standard`)

```bash
/project:workflow-scope-analysis phase X issue Y
/project:workflow-plan-validation phase X issue Y
/project:workflow-implementation phase X issue Y
/project:workflow-review-cycle phase X issue Y
```

### Expert Mode (`expert`)

```bash
/project:workflow-scope-analysis detailed phase X issue Y
/project:workflow-plan-validation expert phase X issue Y
/project:workflow-implementation subagent phase X issue Y
/project:workflow-review-cycle consensus phase X issue Y
```

## Required Output

Each workflow component produces specific deliverables:

1. **Scope Analysis**: Scope boundary document with clear inclusions/exclusions
2. **Plan Validation**: Approved implementation plan document
3. **Implementation**: Working code meeting acceptance criteria with progress tracking
4. **Review Cycle**: Comprehensive validation report with multi-agent consensus

## User Approval Gates

**CRITICAL**: The workflow includes mandatory user approval points:

- After scope analysis (for boundary confirmation)
- After plan validation (before implementation begins)
- After review cycle (for final acceptance)

## Error Handling and Recovery

- **Missing documentation**: Auto-generate templates or provide clear setup instructions
- **Invalid arguments**: Interactive prompts for clarification with examples
- **Workflow interruption**: Checkpoint capability to resume from any component
- **Scope creep detection**: Automatic boundary validation and user consultation
- **Quality gate failures**: Clear remediation steps with specific commands

## Development Philosophy Integration

All workflow components follow the project's core principles:

- **Reuse First**: Leverage existing solutions from ledgerbase, FISProject, .github
- **Configure Don't Build**: Use Zen MCP Server, Heimdall MCP Server, AssuredOSS packages
- **Focus on Unique Value**: Build only PromptCraft-specific functionality

## Examples

```bash
# Quick issue resolution (essential steps only)
/project:workflow-resolve-issue quick phase 1 issue 3

# Standard workflow (recommended)
/project:workflow-resolve-issue standard phase 2 issue 7

# Expert mode (minimal prompts)
/project:workflow-resolve-issue expert phase 1 issue 1
```
