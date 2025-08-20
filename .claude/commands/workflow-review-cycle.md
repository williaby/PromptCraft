---
category: workflow
complexity: medium
estimated_time: "15-30 minutes"
dependencies: ["workflow-implementation", "validation-precommit"]
sub_commands: ["validation-precommit"]
version: "2.0"
models_required: ["testing", "review", "consensus"]
model_preferences:
  testing: ["o3", "o3-mini", "microsoft/phi-4-reasoning:free"]
  review: ["anthropic/claude-opus-4", "anthropic/claude-sonnet-4", "google/gemini-2.5-pro"]
  consensus: ["deepseek/deepseek-chat:free", "gemini-2.0-flash"]
---

# Workflow Review Cycle

Comprehensive testing, validation, and multi-agent review of implemented solution: $ARGUMENTS

## Usage Options

- `phase X issue Y` - Full review cycle with multi-agent validation
- `quick phase X issue Y` - Essential testing and validation only
- `consensus phase X issue Y` - Layered consensus review (strategic/analytical/practical)
- `strategic phase X issue Y` - Strategic consensus with business impact focus
- `layered phase X issue Y` - Full layered consensus across all three layers
- `technical phase X issue Y` - Technical-only layered consensus (analytical + practical)
- `--model=[name]` - Override default model for all roles
- `--testing-model=[name]` - Specific model for testing development
- `--review-model=[name]` - Specific model for code review
- `--consensus-model=[name]` - Specific model for consensus validation
- `--cost-preference=[level]` - Cost preference: cost-optimized/balanced/performance
- `--org-level=[level]` - Organization level: startup/scaleup/enterprise

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
   MODE=$(echo "$ARGUMENTS" | grep -oP "^(quick|consensus|strategic|layered|technical)" || echo "standard")

   # Configure models with fallback chains
   TESTING_MODEL=$(get_model_override "testing" "$ARGUMENTS" "o3")
   REVIEW_MODEL=$(get_model_override "review" "$ARGUMENTS" "anthropic/claude-opus-4")
   CONSENSUS_MODEL=$(get_model_override "consensus" "$ARGUMENTS" "deepseek/deepseek-chat:free")

   # Layered consensus configuration
   LAYERED_CONSENSUS_MODELS=5  # Default model count for layered analysis
   CONSENSUS_LAYERS="strategic,analytical,practical"
   ORG_LEVEL=$(echo "$ARGUMENTS" | grep -oP "org-level=\K\w+" || echo "startup")
   COST_PREFERENCE=$(echo "$ARGUMENTS" | grep -oP "cost-preference=\K[\w-]+" || echo "balanced")

   # Configure layered consensus based on mode
   case "$MODE" in
       "strategic")
           CONSENSUS_LAYERS="strategic"
           LAYERED_CONSENSUS_MODELS=3
           ;;
       "layered"|"consensus")
           CONSENSUS_LAYERS="strategic,analytical,practical"
           LAYERED_CONSENSUS_MODELS=5
           ;;
       "technical")
           CONSENSUS_LAYERS="analytical,practical"
           LAYERED_CONSENSUS_MODELS=4
           ;;
   esac

   # Add free model support for premium workflows
   if [[ ! "$TESTING_MODEL" =~ ":free" ]] && [[ "$MODE" != "quick" ]]; then
       TESTING_SUPPORT_MODEL="microsoft/phi-4-reasoning:free"
   fi
   if [[ ! "$REVIEW_MODEL" =~ ":free" ]] && [[ "$MODE" != "quick" ]]; then
       REVIEW_SUPPORT_MODEL="gemini-2.0-flash"
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
       REVIEW_MODEL="deepseek/deepseek-chat:free"
       CONSENSUS_MODEL="gemini-2.0-flash"
   fi
   ```

### Step 0: Branch State Validation and Synchronization

**CRITICAL**: Ensure branch is properly synchronized before review.

```bash
# Branch synchronization and conflict prevention
synchronize_branches() {
    local current_branch=$(git branch --show-current)
    local phase_branch="phase-1-development"  # TODO: Make dynamic based on context

    echo "🔄 Synchronizing branches..."

    # Fetch latest changes
    git fetch origin

    # Check for conflicts with phase branch
    echo "🔍 Checking for potential conflicts..."
    if ! git merge-tree $(git merge-base HEAD origin/$phase_branch) HEAD origin/$phase_branch | grep -q "<<<"; then
        echo "✅ No conflicts detected with $phase_branch"
    else
        echo "⚠️  Potential conflicts detected with $phase_branch"
        echo "💡 Resolve conflicts before proceeding with review"
        exit 1
    fi

    # Ensure local branch is up to date with remote
    if git status | grep -q "behind"; then
        echo "🔄 Pulling latest changes..."
        git pull origin "$current_branch"
    fi

    # Push any unpushed commits
    if git status | grep -q "ahead"; then
        echo "📤 Pushing local commits..."
        git push origin "$current_branch"
    fi

    echo "✅ Branch synchronization complete"
}

synchronize_branches
```

### Step 1: Comprehensive Pre-commit Validation

1. **Enhanced Pre-commit Checks with Immediate Fixes**:

   ```bash
   # Comprehensive validation with auto-fix capabilities
   enhanced_precommit_validation() {
       echo "🔍 Running enhanced pre-commit validation..."

       # 1. Dependency validation and auto-update
       echo "📦 Validating dependencies..."
       if ! poetry check; then
           echo "🔄 Auto-fixing poetry.lock..."
           poetry lock
           ./scripts/generate_requirements.sh
           git add poetry.lock requirements*.txt
           git commit -m "chore(deps): auto-update dependencies for review"
       fi

       # 2. Code formatting auto-fix
       echo "🎨 Auto-formatting code..."
       poetry run black .
       git add -A
       if ! git diff --cached --quiet; then
           git commit -m "style: auto-format code for review"
       fi

       # 3. Run all pre-commit hooks
       echo "🪝 Running pre-commit hooks..."
       if ! poetry run pre-commit run --all-files; then
           echo "❌ Pre-commit hooks failed - manual fixes required"
           exit 1
       fi

       # 4. Final quality validation
       echo "✅ Running final quality checks..."
       markdownlint **/*.md || echo "⚠️  Markdown issues need manual review"
       yamllint **/*.{yml,yaml} || echo "⚠️  YAML issues need manual review"
       poetry run ruff check . || exit 1
       poetry run mypy src || exit 1

       echo "✅ All pre-commit validation passed"
   }

   enhanced_precommit_validation
   ```

2. **Test Coverage Enforcement**:

   ```bash
   # Ensure test coverage before review
   enforce_test_coverage() {
       echo "📊 Enforcing test coverage requirements..."

       COVERAGE=$(poetry run pytest --cov=src --cov-report=term-missing | grep "TOTAL" | awk '{print $4}' | sed 's/%//')

       if [[ $COVERAGE -lt 80 ]]; then
           echo "❌ Test coverage below 80%: ${COVERAGE}%"
           echo "🧪 Generating additional tests..."

           # Use AI to suggest additional tests
           zen_mcp_call "microsoft/phi-4-reasoning:free" \
               --role "Test Generator" \
               --request "Generate additional unit tests to improve coverage above 80%"

           echo "💡 Add the suggested tests and re-run review"
           exit 1
       fi

       echo "✅ Test coverage: ${COVERAGE}%"
   }

   enforce_test_coverage
   ```

3. **Verify Code Quality Standards**:
   - 80% minimum test coverage (enforced above)
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

3. **Layered Consensus Validation**:

   ```bash
   echo "🏗️ Building layered consensus using: $LAYERED_CONSENSUS_MODELS models"

   case "$MODE" in
       "strategic"|"layered"|"consensus"|"technical")
           # Use enhanced layered consensus
           claude mcp zen layered_consensus \
               --question "Comprehensive evaluation: Is this implementation ready for production deployment? Consider code quality, security, performance, maintainability, and business value." \
               --layers "$CONSENSUS_LAYERS" \
               --model_count "$LAYERED_CONSENSUS_MODELS" \
               --cost_threshold "$COST_PREFERENCE" \
               --org_level "$ORG_LEVEL" \
               --files "$(find src tests -name '*.py' -type f | head -15 | tr '\n' ',')" \
               --relevant_files "$(git diff --name-only HEAD~1 2>/dev/null | tr '\n' ',')" \
               --model "gemini-2.5-pro"
           ;;
       *)
           # Fallback to standard consensus for quick/other modes
           zen_mcp_call "$CONSENSUS_MODEL" \
               --role "Technical Consensus Builder" \
               --request "Synthesize review findings and identify conflicts or required changes"
           ;;
   esac
   ```

   **Key Validation Points:**
   - Strategic layer: Business impact, long-term implications, competitive positioning
   - Analytical layer: Technical analysis, data-driven evaluation, objective assessment
   - Practical layer: Implementation feasibility, operational concerns, resource requirements
   - Cross-layer synthesis: Areas of consensus, key disagreements, final recommendation
   - Structured dissent: Devil's advocate challenges and assumption testing
   - Confidence calibration: Final recommendation with confidence levels

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

### Layered Consensus Results
${MODE:+
#### Strategic Layer Assessment
- [High-level business and architectural evaluation]
- [Strategic risks and opportunities]
- [Long-term implications and competitive positioning]

#### Analytical Layer Assessment
- [Technical analysis and data-driven evaluation]
- [Code quality metrics and objective assessment]
- [Risk analysis and evidence-based conclusions]

#### Practical Layer Assessment
- [Implementation feasibility and operational concerns]
- [Resource requirements and deployment considerations]
- [Maintenance and support implications]

#### Cross-Layer Synthesis
- [Areas of consensus across all layers]
- [Key disagreements and tensions identified]
- [Devil's advocate challenges and critical findings]
- [Final recommendation with confidence level]
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

### Step 5: Post-Review Branch Management

**CRITICAL**: Proper branch management after successful review.

```bash
# Post-review branch management
post_review_branch_management() {
    local current_branch=$(git branch --show-current)
    local phase_branch="phase-1-development"  # TODO: Make dynamic

    echo "🌿 Managing post-review branch state..."

    # Ensure all changes are committed
    if ! git diff --quiet; then
        echo "⚠️  Uncommitted changes detected"
        git add -A
        git commit -m "chore: final changes after review"
    fi

    # Push final state
    git push origin "$current_branch"

    # Prepare merge information
    echo "🔄 Branch ready for merge to $phase_branch"
    echo "📋 Merge checklist:"
    echo "  ✅ All quality gates passed"
    echo "  ✅ Multi-agent review complete"
    echo "  ✅ Test coverage ≥80%"
    echo "  ✅ No conflicts with target branch"
    echo "  ✅ Branch synchronized with remote"

    # Offer to create merge commit template
    echo ""
    echo "💡 Ready to merge? Run:"
    echo "   git checkout $phase_branch"
    echo "   git pull origin $phase_branch"
    echo "   git merge --no-ff $current_branch"
    echo "   git push origin $phase_branch"
    echo ""
    echo "🗑️  After merge, cleanup with:"
    echo "   git branch -d $current_branch"
    echo "   git push origin --delete $current_branch"
}

post_review_branch_management
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

# Strategic consensus focusing on business impact
/project:workflow-review-cycle strategic phase 1 issue 3

# Full layered consensus with all three layers
/project:workflow-review-cycle layered phase 2 issue 5

# Technical-only consensus (analytical + practical layers)
/project:workflow-review-cycle technical phase 1 issue 8

# Cost-optimized layered consensus
/project:workflow-review-cycle layered phase 3 issue 2 --cost-preference=cost-optimized

# Performance-focused layered consensus for critical features
/project:workflow-review-cycle layered phase 1 issue 1 --cost-preference=performance --org-level=enterprise
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
