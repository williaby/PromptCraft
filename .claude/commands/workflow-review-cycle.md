---
category: workflow
complexity: medium
estimated_time: "15-30 minutes"
dependencies: ["workflow-implementation", "validation-precommit"]
sub_commands: ["validation-precommit"]
version: "1.1"
models_required: ["testing", "review", "consensus"]
model_preferences:
  testing: ["o3", "o3-mini", "microsoft/phi-4-reasoning:free"]
  review: ["anthropic/claude-opus-4", "anthropic/claude-sonnet-4", "google/gemini-2.5-pro"]
  consensus: ["deepseek/deepseek-chat-v3-0324:free", "google/gemini-2.0-flash-exp:free"]
---

# Workflow Review Cycle

Comprehensive testing, validation, and multi-agent review of implemented solution: $ARGUMENTS

## Usage Options

- `phase X issue Y` - Full review cycle with multi-agent validation
- `quick phase X issue Y` - Essential testing and validation only
- `consensus phase X issue Y` - Multi-model consensus review
- `--model=[name]` - Override default model for all roles
- `--testing-model=[name]` - Specific model for testing development
- `--review-model=[name]` - Specific model for code review
- `--consensus-model=[name]` - Specific model for consensus validation

**Automatic Branch Detection**: Works on current issue branch or detects from phase/issue arguments.

## Prerequisites

This command requires completed implementation. Implementation must pass basic quality gates before review.

## Instructions

### Step 0: Model Configuration

1. **Parse Arguments and Configure Models**:

   ```bash
   # Parse model overrides using shared function
   source .claude/commands/shared/model_utils.sh

   PHASE=$(echo "$ARGUMENTS" | grep -oP "phase\s+\K\d+" || echo "1")
   ISSUE=$(echo "$ARGUMENTS" | grep -oP "issue\s+\K\d+" || echo "")
   MODE=$(echo "$ARGUMENTS" | grep -oP "^(quick|consensus)" || echo "standard")

   # Configure models with fallback chains
   TESTING_MODEL=$(get_model_override "testing" "$ARGUMENTS" "o3")
   REVIEW_MODEL=$(get_model_override "review" "$ARGUMENTS" "anthropic/claude-opus-4")
   CONSENSUS_MODEL=$(get_model_override "consensus" "$ARGUMENTS" "deepseek/deepseek-chat-v3-0324:free")

   # Add free model support for premium workflows
   if [[ ! "$TESTING_MODEL" =~ ":free" ]] && [[ "$MODE" != "quick" ]]; then
       TESTING_SUPPORT_MODEL="microsoft/phi-4-reasoning:free"
   fi
   if [[ ! "$REVIEW_MODEL" =~ ":free" ]] && [[ "$MODE" != "quick" ]]; then
       REVIEW_SUPPORT_MODEL="google/gemini-2.0-flash-exp:free"
   fi
   ```

2. **Model Availability Validation**:

   ```bash
   # Test model availability with graceful fallbacks
   AVAILABLE_MODELS=()
   for model in "$TESTING_MODEL" "$REVIEW_MODEL" "$CONSENSUS_MODEL"; do
       if zen_test_model "$model" 2>/dev/null; then
           AVAILABLE_MODELS+=("$model")
       else
           echo "⚠️  Model $model unavailable, using fallback"
       fi
   done

   # Ensure minimum functionality
   if [[ ${#AVAILABLE_MODELS[@]} -eq 0 ]]; then
       echo "🔄 No preferred models available, using free fallbacks"
       TESTING_MODEL="microsoft/phi-4-reasoning:free"
       REVIEW_MODEL="deepseek/deepseek-chat-v3-0324:free"
       CONSENSUS_MODEL="google/gemini-2.0-flash-exp:free"
   fi
   ```

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

1. **Testing Strategy Development**:

   ```bash
   echo "🧪 Testing Strategy using: $TESTING_MODEL"
   zen_mcp_call "$TESTING_MODEL" \
       --role "Testing Strategist and Quality Engineer" \
       --context "Implementation validation and edge case testing" \
       --request "Review implementation against acceptance criteria and develop comprehensive test strategy" \
       --tasks "
         - Review the implementation against acceptance criteria
         - Develop edge case tests
         - Identify potential failure modes
         - Suggest additional validation approaches"

   # Free model support for additional test ideas
   if [[ -n "$TESTING_SUPPORT_MODEL" ]]; then
       echo "💡 Additional testing insights using: $TESTING_SUPPORT_MODEL"
       zen_mcp_call "$TESTING_SUPPORT_MODEL" \
           --role "Test Case Generator" \
           --request "Generate additional edge cases and boundary condition tests"
   fi
   ```

2. **Code Quality Review**:

   ```bash
   echo "🔍 Code Review using: $REVIEW_MODEL"
   zen_mcp_call "$REVIEW_MODEL" \
       --role "Senior Code Reviewer and Architect" \
       --context "Code quality, security, and architecture assessment" \
       --request "Perform comprehensive code review with focus on quality and security" \
       --tasks "
         - Assess code quality and architecture
         - Review security implications
         - Validate against development standards
         - Check for potential improvements"

   # Free model support for quick validation
   if [[ -n "$REVIEW_SUPPORT_MODEL" ]]; then
       echo "✅ Quick validation using: $REVIEW_SUPPORT_MODEL"
       zen_mcp_call "$REVIEW_SUPPORT_MODEL" \
           --role "Code Validator" \
           --request "Quick validation check - identify obvious issues or concerns"
   fi
   ```

3. **Consensus Validation**:

   ```bash
   echo "🤝 Building consensus using: $CONSENSUS_MODEL"

   if [[ "$MODE" == "consensus" ]]; then
       # Use Zen consensus tool with multiple models
       zen_mcp_consensus \
           --models "$TESTING_MODEL,$REVIEW_MODEL,$CONSENSUS_MODEL" \
           --topic "Implementation quality and completeness assessment" \
           --request "Evaluate if implementation meets all acceptance criteria"
   else
       # Standard consensus validation
       zen_mcp_call "$CONSENSUS_MODEL" \
           --role "Technical Consensus Builder" \
           --request "Synthesize review findings and identify any conflicts or required changes"
   fi
   ```

   **Key Validation Points:**
   - Compare review findings across all models
   - Resolve any conflicting recommendations
   - Document consensus decisions
   - Identify required changes

### Step 4: Final Validation Report

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
### Testing Strategy Results (${TESTING_MODEL})
- [Key findings and additional tests developed]
- [Edge cases identified]
- [Recommendations]
${TESTING_SUPPORT_MODEL:+
### Additional Testing Insights (${TESTING_SUPPORT_MODEL})
- [Additional test cases and boundary conditions]
}

### Code Quality Review (${REVIEW_MODEL})
- [Code quality assessment]
- [Security evaluation]
- [Improvement suggestions]
${REVIEW_SUPPORT_MODEL:+
### Quick Validation Check (${REVIEW_SUPPORT_MODEL})
- [Obvious issues or validation points]
}

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
# Full review cycle with auto-detected models
/project:workflow-review-cycle phase 1 issue 3

# Quick validation only
/project:workflow-review-cycle quick phase 2 issue 7

# Multi-model consensus review
/project:workflow-review-cycle consensus phase 1 issue 1

# Override specific models
/project:workflow-review-cycle phase 3 issue 5 --testing-model=o3 --review-model=opus-4

# Use free models for cost-effective review
/project:workflow-review-cycle phase 2 issue 4 --model=deepseek --testing-model=phi-4

# Premium models with free support
/project:workflow-review-cycle consensus phase 1 issue 8 --review-model=sonnet --testing-model=o3-mini
```

## Model Roles and Recommendations

- **Premium**: `o3`, `o3-mini` (advanced reasoning for edge cases)
- **Free Alternative**: `phi-4-reasoning`, `deepseek-r1`, `mai-ds` (good logical thinking)

- **Premium**: `opus-4`, `sonnet-4`, `gemini-pro` (comprehensive analysis)
- **Free Alternative**: `deepseek-v3`, `gemini-free` (solid code review)

- **Free First**: `deepseek-v3`, `gemini-free` (cost-effective synthesis)
- **Premium Backup**: `sonnet-4`, `gemini-flash` (complex decisions)

## Final User Approval

**CRITICAL**: Report completion status and request final user approval after all validations pass.

Present summary of:

- ✅ Acceptance criteria met
- ✅ Quality standards achieved
- ✅ Multi-agent approval obtained
- ✅ Implementation ready for deployment

Request explicit user sign-off before considering issue resolved.
