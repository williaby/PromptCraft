---
category: workflow
complexity: high
estimated_time: "Variable based on issue"
dependencies: ["workflow-plan-validation"]
sub_commands: ["validation-precommit"]
version: "1.1"
---

# Workflow Implementation

Execute approved implementation plan with security and quality standards: $ARGUMENTS

## Usage Options
- `phase X issue Y` - Standard implementation workflow
- `quick phase X issue Y` - Essential implementation only
- `subagent phase X issue Y` - Use specialized subagents for implementation

## Prerequisites

This command requires approved implementation plan. If not done, run:
```bash
/project:workflow-plan-validation phase X issue Y
```

**CRITICAL**: User approval of the planning document is required before proceeding.

## Instructions

### Step 1: Pre-Implementation Environment Validation

1. **Comprehensive Environment Check**:
   - Run environment validation using setup_validator.py
   - Validate all tools needed for specific implementation
   - Check that planned dependencies are actually available
   - Verify prerequisite issues are fully completed and deliverables accessible
   - Fail fast if environment doesn't match plan requirements

```bash
# MANDATORY: Validate environment before implementation
poetry run python src/utils/setup_validator.py --scope implementation
```

### Step 2: Implementation Setup

1. **Load Approved Plan**:
   - Read `/docs/planning/{phase}_{issue}_issue_plan.md`
   - Verify plan is approved and has "status: approved"
   - Confirm rollback procedures are documented
   - Create todo list from action plan items

2. **Initialize Progress Tracking**:
   - Create comprehensive todo list from action plan items using TodoWrite
   - Structure todos to match acceptance criteria from issue plan
   - Set up progress milestones aligned with plan timeline
   - Establish progress reporting checkpoints

3. **Environment Validation**:
   - Ensure GPG and SSH keys are present
   - Validate development environment is ready
   - Check dependencies are met

4. **File Change Logging** (MANDATORY):
   - Log ALL file changes to `docs/planning/claude-file-change-log.md`
   - Format: `YYYY-MM-DD HH:MM:SS | CHANGE_TYPE | RELATIVE_FILE_PATH`
   - Change types: ADDED, MODIFIED, DELETED

### Step 3: Implementation Execution

1. **Use Subagents** for implementation tasks:
   - Delegate complex coding tasks to specialized agents
   - Maintain coordination through Zen MCP Server
   - Follow agent-first design principles

2. **Follow the Action Plan** step by step:
   - Work through todo items sequentially
   - Mark items as in_progress before starting
   - Mark items as completed immediately after finishing
   - Never skip validation steps

3. **Implement Security Best Practices** throughout:
   - Use encrypted .env files for secrets
   - Follow security scanning requirements
   - Validate all inputs and outputs
   - Use AssuredOSS packages when available

4. **Follow Coding Standards** from CLAUDE.md:
   - Maintain naming conventions (snake_case, kebab-case, PascalCase)
   - Follow Python standards (Black 88 chars, Ruff, MyPy)
   - Ensure 80% minimum test coverage
   - Create atomic knowledge chunks for documentation

5. **Enhanced Progress Tracking**:
   - Use TodoWrite for all task management
   - Update progress in real-time at each milestone
   - Mark todos as in_progress before starting, completed immediately after finishing
   - Document blockers and decisions with timestamps
   - Track percentage completion against plan timeline
   - Keep scope boundaries in mind throughout

6. **Enhanced Error Handling and Recovery**:
   - Reference rollback procedures from the plan validation step
   - Monitor for common failure patterns (test failures, dependency issues, scope violations)
   - Apply rollback decision tree (when to rollback vs. continue)
   - Execute automated rollback procedures when triggered
   - Include error recovery and retry mechanisms

### Step 4: Automated Testing Integration

1. **Mandatory Test Execution at Milestones**:
   - Run test suite at each major implementation checkpoint
   - Execute coverage validation (80% minimum requirement)
   - Handle test failures with rollback triggers
   - Validate pre-commit hooks before proceeding

```bash
# MANDATORY: Test execution at milestones
make test  # or poetry run pytest -v --cov=src --cov-report=html --cov-report=term-missing
```

2. **Continuous Test Integration**:
   - Run relevant tests after each significant change
   - Validate test coverage hasn't decreased
   - Check for test failures that might trigger rollback
   - Ensure all tests pass before marking milestones complete

### Step 5: Continuous Validation

1. **Real-time Quality Checks**:
   - Run linters after each significant change
   - Validate against acceptance criteria continuously
   - Check for scope creep at each milestone

2. **Security Validation**:
   - Run security scans regularly
   - Validate encrypted storage is working
   - Check for exposed secrets or keys

## Implementation Patterns

### Code Reuse Strategy
1. **Check ledgerbase** for existing patterns
2. **Review FISProject** for similar implementations
3. **Use .github** for CI/CD templates
4. **Leverage PromptCraft** existing components

### Agent Coordination
```markdown
## Subagent Tasks
- **Security Agent**: Authentication and authorization
- **Create Agent**: Knowledge file generation
- **Testing Agent**: Test suite development
- **Review Agent**: Code quality validation
```

### Progress Tracking Template
```markdown
## Implementation Progress
- [ ] Task 1: [Description] - Status: pending/in_progress/completed
- [ ] Task 2: [Description] - Status: pending/in_progress/completed
- [ ] Task 3: [Description] - Status: pending/in_progress/completed

## Blockers and Decisions
- [Date] [Decision/Blocker]: [Description and resolution]

## Scope Validation
- Last checked: [Date]
- Scope drift detected: Yes/No
- Corrective actions taken: [List]
```

## Quality Gates

### Before Each Commit
```bash
# MANDATORY: Run pre-commit validation
/project:validation-precommit

# Check file-specific linting
markdownlint **/*.md  # For markdown changes
yamllint **/*.{yml,yaml}  # For YAML changes
poetry run black --check .  # For Python changes
poetry run ruff check .  # For Python changes
poetry run mypy src  # For Python changes
```

### Before Each Major Milestone
1. **Acceptance Criteria Check**: Verify progress against original criteria
2. **Security Scan**: Run Safety and Bandit checks
3. **Test Coverage**: Ensure 80% minimum coverage maintained
4. **Documentation**: Update knowledge files as needed

## Enhanced Error Handling

### Failure Detection Patterns
- **Plan not approved**: Stop and request user approval first
- **Environment validation failures**: Provide specific setup instructions and fail fast
- **Test failures**: Trigger rollback decision tree evaluation
- **Dependency conflicts**: Document and resolve systematically
- **Scope creep detected**: Halt and consult with user
- **Quality gate failures**: Fix issues before proceeding
- **Coverage below 80%**: Stop implementation until coverage restored

### Rollback Decision Tree
1. **Critical Failures** (security issues, data loss risk): Immediate rollback
2. **Test Failures** (functionality broken): Evaluate rollback vs. fix
3. **Quality Issues** (linting, coverage): Fix before proceeding
4. **Scope Creep** (plan deviation): Rollback to last safe checkpoint
5. **Dependency Issues** (missing prerequisites): Halt until resolved

### Rollback Execution
- Execute rollback procedures documented in the plan
- Restore to safe rollback points identified during planning
- Preserve data according to rollback requirements
- Update todo tracking to reflect rollback status
- Document rollback reason and lessons learned

## Examples

```bash
# Standard implementation
/project:workflow-implementation phase 1 issue 3

# Quick implementation (essential steps only)
/project:workflow-implementation quick phase 2 issue 7

# Subagent-coordinated implementation
/project:workflow-implementation subagent phase 1 issue 1
```

## Next Steps

After implementation completion:
- Proceed to `/project:workflow-review-cycle`
- Ensure all todo items are marked completed
- Prepare for comprehensive testing and validation
