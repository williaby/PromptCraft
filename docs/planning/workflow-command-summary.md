---
title: "Workflow Command Summary Sheet"
version: "1.0"
status: "published"
component: "Process-Management"
tags: ["workflow", "commands", "reference", "claude-code"]
purpose: "Quick reference for full cycle workflow commands and usage options"
---

# Workflow Command Summary Sheet

## Full Cycle Workflow Commands

The complete workflow consists of four main commands that form a complete issue resolution cycle:

### Core Workflow Sequence

1. **`/project:workflow-scope-analysis`** - Define issue boundaries and prevent scope creep
2. **`/project:workflow-plan-validation`** - Create and validate implementation plan
3. **`/project:workflow-implementation`** - Execute approved plan with quality standards
4. **`/project:workflow-review-cycle`** - Comprehensive testing and multi-agent validation

### Orchestrator Command

- **`/project:workflow-resolve-issue`** - Orchestrates all four commands in sequence

---

## Command Details and Usage Options

### 1. Workflow Scope Analysis
**Command**: `/project:workflow-scope-analysis`
**Purpose**: Analyze and define boundaries for a project issue to prevent scope creep
**Estimated Time**: 10-15 minutes

#### Usage Options:
- **Standard**: `/project:workflow-scope-analysis phase X issue Y`
  - Complete boundary analysis with dependency mapping
  - Automated scope validation checks
  - Comprehensive documentation output

- **Quick**: `/project:workflow-scope-analysis quick phase X issue Y`
  - Essential boundary definition only
  - Minimal validation steps
  - Streamlined output format

- **Detailed**: `/project:workflow-scope-analysis detailed phase X issue Y`
  - Comprehensive analysis with extensive validation
  - Additional contextual research
  - Enhanced error detection and reporting

---

### 2. Workflow Plan Validation
**Command**: `/project:workflow-plan-validation`
**Purpose**: Create and validate implementation plan against defined scope boundaries
**Estimated Time**: 10-15 minutes

#### Usage Options:
- **Standard**: `/project:workflow-plan-validation phase X issue Y`
  - Complete planning with scope validation
  - Dependency impact analysis
  - Automated plan consistency checks

- **Quick**: `/project:workflow-plan-validation quick phase X issue Y`
  - Essential plan creation only
  - Minimal validation steps
  - Basic scope checking

- **Expert**: `/project:workflow-plan-validation expert phase X issue Y`
  - Plan with IT manager consultation via Zen
  - Enhanced validation through expert review
  - Comprehensive rollback procedures

---

### 3. Workflow Implementation
**Command**: `/project:workflow-implementation`
**Purpose**: Execute approved implementation plan with security and quality standards
**Estimated Time**: Variable based on issue complexity

#### Usage Options:
- **Standard**: `/project:workflow-implementation phase X issue Y`
  - Standard implementation workflow
  - Full quality gate validation
  - Comprehensive progress tracking

- **Quick**: `/project:workflow-implementation quick phase X issue Y`
  - Essential implementation only
  - Minimal validation steps
  - Streamlined testing

- **Subagent**: `/project:workflow-implementation subagent phase X issue Y`
  - Use specialized subagents for implementation
  - Enhanced agent coordination through Zen MCP Server
  - Advanced task delegation and monitoring

---

### 4. Workflow Review Cycle
**Command**: `/project:workflow-review-cycle`
**Purpose**: Comprehensive testing, validation, and multi-agent review of implemented solution
**Estimated Time**: 15-30 minutes

#### Usage Options:
- **Standard**: `/project:workflow-review-cycle phase X issue Y`
  - Full review cycle with multi-agent validation
  - Comprehensive quality gate checks
  - Complete acceptance criteria validation

- **Quick**: `/project:workflow-review-cycle quick phase X issue Y`
  - Essential testing and validation only
  - Basic quality checks
  - Minimal agent consultation

- **Consensus**: `/project:workflow-review-cycle consensus phase X issue Y`
  - Multi-model consensus review
  - Enhanced agent coordination and consistency
  - Comprehensive validation reporting

---

### 5. Workflow Resolve Issue (Orchestrator)
**Command**: `/project:workflow-resolve-issue`
**Purpose**: Systematically resolve any project issue through modular workflow orchestration
**Estimated Time**: 60-90 minutes (full cycle)

#### Usage Options:
- **Standard**: `/project:workflow-resolve-issue standard phase X issue Y`
  - Full workflow with validation (60-90 min)
  - All four workflow components executed in sequence
  - Complete user approval gates

- **Quick**: `/project:workflow-resolve-issue quick phase X issue Y`
  - Essential workflow steps only (30-45 min)
  - Streamlined process with minimal validation
  - Rapid issue resolution

- **Expert**: `/project:workflow-resolve-issue expert phase X issue Y`
  - Minimal prompts for experienced users (15-30 min)
  - Advanced features and detailed analysis
  - Expert-level validation and consensus

---

## Usage Examples

### Individual Commands
```bash
# Scope analysis with different detail levels
/project:workflow-scope-analysis phase 1 issue 3
/project:workflow-scope-analysis quick phase 1 issue 3
/project:workflow-scope-analysis detailed phase 1 issue 3

# Plan validation with different approaches
/project:workflow-plan-validation phase 1 issue 3
/project:workflow-plan-validation quick phase 1 issue 3
/project:workflow-plan-validation expert phase 1 issue 3

# Implementation with different strategies
/project:workflow-implementation phase 1 issue 3
/project:workflow-implementation quick phase 1 issue 3
/project:workflow-implementation subagent phase 1 issue 3

# Review cycle with different depths
/project:workflow-review-cycle phase 1 issue 3
/project:workflow-review-cycle quick phase 1 issue 3
/project:workflow-review-cycle consensus phase 1 issue 3
```

### Full Orchestration
```bash
# Complete issue resolution workflows
/project:workflow-resolve-issue standard phase 1 issue 3
/project:workflow-resolve-issue quick phase 1 issue 3
/project:workflow-resolve-issue expert phase 1 issue 3
```

---

## Key Features

### Mandatory Requirements
- **File Change Logging**: All commands log changes to `docs/planning/claude-file-change-log.md`
- **Environment Validation**: Each command validates prerequisites before execution
- **User Approval Gates**: Critical checkpoints require explicit user approval
- **Scope Boundary Enforcement**: Prevents scope creep throughout workflow

### Quality Standards
- **80% Minimum Test Coverage**: Enforced during implementation and review
- **Security Compliance**: GPG/SSH key validation, encrypted secrets, vulnerability scanning
- **Code Quality**: Black formatting, Ruff linting, MyPy type checking
- **Documentation**: C.R.E.A.T.E. framework compliance for knowledge files

### Development Philosophy Integration
- **Reuse First**: Leverage existing solutions from ledgerbase, FISProject, .github
- **Configure Don't Build**: Use Zen MCP Server, Heimdall MCP Server, AssuredOSS packages
- **Focus on Unique Value**: Build only PromptCraft-specific functionality

---

## Command Selection Guide

### Choose Based on Requirements:

**Time Constraints**:
- **Quick**: When time is limited and basic functionality is sufficient
- **Standard**: For most production workflows requiring full validation
- **Expert/Detailed**: When comprehensive analysis and validation are critical

**Complexity Level**:
- **Quick**: Simple issues with well-defined requirements
- **Standard**: Most typical development tasks
- **Expert/Detailed/Consensus**: Complex issues requiring multiple expert perspectives

**Team Experience**:
- **Quick**: Experienced teams familiar with the process
- **Standard**: Mixed experience levels, recommended default
- **Expert**: Senior developers who need minimal guidance

**Risk Tolerance**:
- **Quick**: Low-risk changes with minimal impact
- **Standard**: Standard business risk acceptance
- **Expert/Consensus**: High-risk changes requiring maximum validation
