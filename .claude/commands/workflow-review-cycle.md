---
category: workflow
complexity: medium
estimated_time: "15-30 minutes"
dependencies: ["workflow-implementation", "validation-precommit"]
sub_commands: ["validation-precommit"]
version: "1.0"
---

# Workflow Review Cycle

Comprehensive testing, validation, and multi-agent review of implemented solution: $ARGUMENTS

## Usage Options

- `phase X issue Y` - Full review cycle with multi-agent validation
- `quick phase X issue Y` - Essential testing and validation only
- `consensus phase X issue Y` - Multi-model consensus review

## Prerequisites

This command requires completed implementation. Implementation must pass basic quality gates before review.

## Instructions

### Step 1: Pre-commit Validation

1. **Run Comprehensive Pre-commit Checks**:

   ```bash
   /project:validation-precommit
   ```

2. **Ensure All Linting Passes**:
   - Markdown: `markdownlint **/*.md`
   - YAML: `yamllint **/*.{yml,yaml}`
   - Python: `poetry run black --check .`
   - Python: `poetry run ruff check .`
   - Python: `poetry run mypy src`

3. **Verify Code Quality Standards**:
   - 80% minimum test coverage
   - No security vulnerabilities
   - All naming conventions followed

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

### Step 3: Multi-Agent Review

<!-- TODO: Fix hardcoded model references - O3 and Gemini should be configurable -->
<!-- TODO: When using consensus mode, the Zen MCP consensus tool expects exact model names from available models list -->

1. **OpenAI O3 Testing**:
   Use Zen to have O3 develop additional test suite:

   ```text
   Ask O3 to:
   - Review the implementation against acceptance criteria
   - Develop edge case tests
   - Identify potential failure modes
   - Suggest additional validation approaches
   ```

2. **Gemini Final Review**:
   Use Zen to have Gemini perform final code review:

   ```text
   Ask Gemini to:
   - Assess code quality and architecture
   - Review security implications
   - Validate against development standards
   - Check for potential improvements
   ```

3. **Consensus Validation**:
   Ensure all agents agree the code is implemented correctly:
   - Compare review findings across agents
   - Resolve any conflicting recommendations
   - Document consensus decisions
   - Identify required changes

### Step 4: Final Validation Report

Generate comprehensive validation report:

```markdown
# Implementation Review Report: Phase {X} Issue {Y}

## Acceptance Criteria Validation
- [ ] Criterion 1: [Description] - Status: Pass/Fail
- [ ] Criterion 2: [Description] - Status: Pass/Fail
- [ ] Criterion 3: [Description] - Status: Pass/Fail

## Quality Gates
- [ ] Pre-commit hooks: Pass/Fail
- [ ] Test coverage ≥80%: Pass/Fail
- [ ] Security scans: Pass/Fail
- [ ] Linting compliance: Pass/Fail
- [ ] Naming conventions: Pass/Fail

## Test Results
- **Unit Tests**: [X/Y passed] - [Coverage %]
- **Integration Tests**: [X/Y passed]
- **Security Scans**: [No vulnerabilities found / Issues identified]
- **Performance**: [Within acceptable bounds / Issues noted]

## Multi-Agent Review Summary
### O3 Testing Results
- [Key findings and additional tests developed]
- [Edge cases identified]
- [Recommendations]

### Gemini Code Review
- [Code quality assessment]
- [Security evaluation]
- [Improvement suggestions]

### Consensus Decisions
- [Agreed-upon changes required]
- [Accepted implementation decisions]
- [Future improvement opportunities]

## Final Status
- [ ] All acceptance criteria met
- [ ] All quality gates passed
- [ ] All agents approve implementation
- [ ] Ready for user approval

## Required Changes (if any)
- [List specific changes needed before approval]

## Recommendations for Future
- [Suggestions for improvement in future iterations]
```

## Completion Criteria

The review cycle is complete when:

1. **All acceptance criteria** are validated as met
2. **All quality gates** pass without exceptions
3. **Multi-agent consensus** is achieved
4. **No critical issues** remain unresolved
5. **User approval** is obtained

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
