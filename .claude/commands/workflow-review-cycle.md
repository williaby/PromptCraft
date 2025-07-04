---
category: workflow
complexity: medium
estimated_time: "15-30 minutes"
dependencies: ["workflow-implementation", "validation-precommit"]
sub_commands: ["validation-precommit"]
version: "1.1"
---

# Workflow Review Cycle

Comprehensive testing, validation, and multi-agent review of implemented solution: $ARGUMENTS

## Usage Options
- `phase X issue Y` - Full review cycle with multi-agent validation
- `quick phase X issue Y` - Essential testing and validation only
- `consensus phase X issue Y` - Multi-model consensus review

## Prerequisites

This command requires completed implementation. Implementation must pass basic quality gates before review.

### Environment Prerequisites Validation

1. **Validate Review Environment**:
   - Run environment validation using setup_validator.py
   - Ensure all testing and validation tools are available
   - Verify all dependencies are properly installed
   - Confirm access to external services (Qdrant, Azure AI)

2. **File Change Logging** (MANDATORY):
   - Log ALL file changes to `docs/planning/claude-file-change-log.md`
   - Format: `YYYY-MM-DD HH:MM:SS | CHANGE_TYPE | RELATIVE_FILE_PATH`
   - Change types: ADDED, MODIFIED, DELETED

```bash
# MANDATORY: Validate environment before review
poetry run python src/utils/setup_validator.py --scope review
```

## Instructions

### Step 1: Comprehensive Quality Gate Validation

1. **Run Comprehensive Pre-commit Checks**:
   ```bash
   /project:validation-precommit
   ```

2. **Automated Compliance Checking**:
   - **File-Type Specific Linting** (mandatory for all modified files):
     - Markdown: `markdownlint **/*.md`
     - YAML: `yamllint **/*.{yml,yaml}`
     - Python: `poetry run black --check .`
     - Python: `poetry run ruff check .`
     - Python: `poetry run mypy src`
   
   - **Security Compliance**:
     - Bandit security scan: `poetry run bandit -r src`
     - Dependency vulnerability check: `poetry run safety check`
     - GPG and SSH key validation
   
   - **Development Standards Compliance**:
     - Naming conventions validation (snake_case, kebab-case, PascalCase)
     - Knowledge file structure validation (C.R.E.A.T.E. framework)
     - Git commit signing verification

3. **Quality Standards Verification**:
   - **Test Coverage**: 80% minimum coverage validation
   - **Code Quality**: No critical linting violations
   - **Security**: Zero high-severity vulnerabilities
   - **Documentation**: All knowledge files follow style guide

### Step 2: Issue-Specific Testing

1. **Execute Acceptance Criteria Validation**:
   - Test each acceptance criterion individually
   - Document pass/fail status for each
   - Verify complete requirement satisfaction

2. **Follow Testing Requirements** from ts-{X}-testing.md:
   - Run unit tests: `poetry run pytest tests/unit/ -v`
   - Run integration tests: `poetry run pytest tests/integration/ -v`
   - Run security scans: `poetry run bandit -r src`
   - Run dependency checks: `poetry run safety check`

3. **Perform Integration Testing**:
   - Test with external dependencies (Qdrant, Azure AI)
   - Validate multi-agent coordination
   - Check UI/API integration points

### Step 3: Enhanced Multi-Agent Review Coordination

1. **Review Criteria Consistency Validation**:
   Before engaging agents, establish consistent review criteria:
   - Cross-check acceptance criteria against implementation scope
   - Verify review criteria align with original issue boundaries
   - Confirm evaluation standards match project requirements
   - Document review baseline for agent consistency

2. **Coordinated OpenAI O3 Testing**:
   Use Zen to have O3 develop additional test suite with specific focus:
   ```
   Provide O3 with:
   - Original acceptance criteria document
   - Implementation scope boundaries 
   - Current test coverage gaps
   
   Ask O3 to:
   - Review implementation against EXACT acceptance criteria
   - Develop edge case tests within scope boundaries
   - Identify potential failure modes for current scope only
   - Suggest additional validation approaches for defined requirements
   - Validate no scope creep in implementation
   ```

3. **Coordinated Gemini Final Review**:
   Use Zen to have Gemini perform final code review with consistency:
   ```
   Provide Gemini with:
   - Original scope boundary document
   - O3's testing findings for context
   - Development standards checklist
   
   Ask Gemini to:
   - Assess code quality and architecture within scope
   - Review security implications for implemented features only
   - Validate against development standards consistently
   - Check for potential improvements within boundaries
   - Cross-validate with O3 findings for consistency
   ```

4. **Multi-Agent Consensus Validation**:
   Ensure coordinated agent agreement with consistency checks:
   - **Cross-Agent Validation**: Compare review findings for consistency
   - **Scope Alignment**: Verify all agents evaluated within same boundaries
   - **Criteria Consistency**: Ensure agents used same evaluation standards
   - **Conflict Resolution**: Resolve conflicting recommendations systematically
   - **Consensus Documentation**: Document agreed-upon decisions and rationale
   - **Change Identification**: Identify required changes with agent consensus

### Step 4: Final Validation Report

Generate comprehensive validation report:

```markdown
# Implementation Review Report: Phase {X} Issue {Y}

## Environment Validation
- [ ] Review environment validated
- [ ] All testing tools available
- [ ] External service access confirmed
- [ ] Dependencies properly installed

## Acceptance Criteria Validation
- [ ] Criterion 1: [Description] - Status: Pass/Fail
- [ ] Criterion 2: [Description] - Status: Pass/Fail
- [ ] Criterion 3: [Description] - Status: Pass/Fail

## Comprehensive Quality Gates
### Automated Compliance Results
- [ ] Pre-commit hooks: Pass/Fail
- [ ] File-type specific linting: Pass/Fail
- [ ] Security compliance: Pass/Fail
- [ ] Development standards compliance: Pass/Fail

### Quality Standards Verification
- [ ] Test coverage ≥80%: Pass/Fail - [Actual %]
- [ ] Code quality: Pass/Fail - [Critical violations: X]
- [ ] Security: Pass/Fail - [High-severity vulnerabilities: X]
- [ ] Documentation: Pass/Fail - [Style guide compliance]

## Test Results
- **Unit Tests**: [X/Y passed] - [Coverage %]
- **Integration Tests**: [X/Y passed]
- **Security Scans**: [No vulnerabilities found / Issues identified]
- **Performance**: [Within acceptable bounds / Issues noted]

## Enhanced Multi-Agent Review Summary
### Review Criteria Consistency
- [ ] Acceptance criteria alignment verified
- [ ] Review boundaries consistent across agents
- [ ] Evaluation standards documented and applied

### O3 Testing Results (Coordinated)
- **Scope Validation**: [Implementation within boundaries: Yes/No]
- **Key Findings**: [Edge cases and additional tests developed]
- **Failure Modes**: [Potential issues identified within scope]
- **Recommendations**: [Validation approaches for defined requirements]

### Gemini Code Review (Coordinated)
- **Code Quality**: [Assessment within scope boundaries]
- **Security Evaluation**: [For implemented features only]
- **Standards Compliance**: [Development standards validation]
- **Cross-Validation**: [Consistency with O3 findings]

### Multi-Agent Consensus
- **Cross-Agent Validation**: [Findings consistency assessment]
- **Scope Alignment**: [All agents evaluated same boundaries: Yes/No]
- **Conflict Resolution**: [How disagreements were resolved]
- **Consensus Decisions**: [Agreed-upon changes and implementation decisions]

## Final Status
- [ ] All acceptance criteria met
- [ ] All comprehensive quality gates passed
- [ ] Multi-agent consensus achieved with consistency
- [ ] Review criteria consistently applied
- [ ] Ready for user approval

## Required Changes (if any)
- [List specific changes needed before approval with agent consensus]

## Recommendations for Future
- [Suggestions for improvement in future iterations with agent agreement]
```

## Enhanced Completion Criteria

The review cycle is complete when:
1. **Environment validation** passes all prerequisites
2. **All acceptance criteria** are validated as met with consistency
3. **All comprehensive quality gates** pass without exceptions
4. **Automated compliance checking** shows full compliance
5. **Multi-agent consensus** is achieved with coordinated consistency
6. **Review criteria consistency** is validated across all agents
7. **No critical issues** remain unresolved
8. **User approval** is obtained

## Error Handling

- **Quality gate failures**: Fix issues before proceeding to agent review
- **Test failures**: Address failing tests and re-run validation
- **Agent disagreement**: Facilitate consensus through additional clarification
- **Security issues**: Stop review and address security concerns immediately
- **Coverage below 80%**: Add tests to meet minimum coverage requirement

## Examples

```bash
# Full review cycle
/project:workflow-review-cycle phase 1 issue 3

# Quick validation only
/project:workflow-review-cycle quick phase 2 issue 7

# Multi-model consensus review
/project:workflow-review-cycle consensus phase 1 issue 1
```

## Final User Approval

**CRITICAL**: Report completion status and request final user approval after all validations pass.

Present summary of:
- ✅ Acceptance criteria met
- ✅ Quality standards achieved
- ✅ Multi-agent approval obtained
- ✅ Implementation ready for deployment

Request explicit user sign-off before considering issue resolved.
