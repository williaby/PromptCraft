---
category: workflow
complexity: high
estimated_time: "5-45 minutes (adaptive)"
dependencies: ["workflow-review-cycle", "validation-precommit"]
sub_commands: ["validation-precommit", "workflow-review-cycle"]
version: "2.0"
models_required: ["zen", "consensus"]
adaptive_analysis: true
auto_scaling: true
---

# Workflow PR Review

Adaptive GitHub PR review with intelligent scaling, error handling, and early exit for clear cases: $ARGUMENTS

## Usage Options

- `<pr-url>` - Adaptive analysis (starts light, escalates if needed)
- `<pr-url> quick` - Essential review only (quality gates + basic analysis)
- `<pr-url> thorough` - Full multi-agent analysis regardless of complexity
- `<pr-url> security-focus` - Security-focused review with additional security agents
- `<pr-url> performance-focus` - Performance-focused review with optimization analysis

## Prerequisites

### Environment Prerequisites Validation

1. **Validate PR Review Environment**:

   ```bash
   # MANDATORY: Validate environment before review
   poetry run python src/utils/setup_validator.py --scope pr-review
   ```

2. **Required Access**:
   - GitHub API access for PR data fetching
   - Zen MCP Server running for agent orchestration
   - Context7 server for codebase analysis (if available)

3. **File Change Logging** (MANDATORY):
   - Log ALL file changes to `docs/planning/claude-file-change-log.md`
   - Format: `YYYY-MM-DD HH:MM:SS | CHANGE_TYPE | RELATIVE_FILE_PATH`

## Instructions

### Step 1: Smart PR Analysis & Early Assessment

1. **Extract PR Information with Error Handling**:
   - Parse GitHub PR URL: $ARGUMENTS and extract mode (quick/thorough/security-focus/performance-focus)
   - Use GitHub CLI with fallback strategies:


     TOTAL_LINES=$((additions + deletions))
     FILE_COUNT=$(echo "$files" | jq length)

     if [[ $TOTAL_LINES -gt 20000 || $FILE_COUNT -gt 50 ]]; then
         echo "🔍 Large PR detected ($TOTAL_LINES lines, $FILE_COUNT files) - using sampling strategy"
         ANALYSIS_MODE="sampled"
     else
         ANALYSIS_MODE="full"
     fi
     ```

2. **Early Exit Detection**:
   - Check CI/CD status first - if critical failures exist, provide immediate feedback
   - Run basic quality gates (linting, security) before expensive analysis
   - For clear-cut cases (multiple failing checks + obvious violations), skip multi-agent analysis

### Step 2: Adaptive Quality Gate Validation

1. **Progressive Quality Checks with Early Exit**:

   ```bash
   echo "🔍 Running quality gates..."

   # Start with fastest checks first
   QUALITY_ISSUES=0



   # CI/CD Status Check (fastest)
   if gh pr checks $PR_NUMBER | grep -q "fail"; then
       echo "❌ CI/CD checks failing - blocking issues detected"
       QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
   fi



   # File-type specific linting (sample core files for large PRs)
   if [[ $ANALYSIS_MODE == "sampled" ]]; then
       # Focus on core changed files only
       CORE_FILES=$(gh pr view $PR_NUMBER --json files | \
         jq -r '.files[] | select(.path | test("(src/|tests/).*\\.(py|md|yml|yaml)$")) | .path' | head -10)

   


   # File-type specific linting (sample core files for large PRs)
   if [[ $ANALYSIS_MODE == "sampled" ]]; then
       # Focus on core changed files only
       CORE_FILES=$(gh pr view $PR_NUMBER --json files | jq -r '.files[] | select(.path | test("(src/|tests/).*\\.(py|md|yml|yaml)$")) | .path' | head -10)

   else
       # Full analysis for smaller PRs
       CORE_FILES=$(gh pr view $PR_NUMBER --json files | jq -r '.files[].path')
   fi


   



   # Run linting with progress indicators
   for file in $CORE_FILES; do
       echo "  📋 Checking $file..."
       case "$file" in


           *.py)
               poetry run ruff check "$file" 2>/dev/null || QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
               ;;
           *.md)
               markdownlint "$file" 2>/dev/null || QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
               ;;
           *.yml|*.yaml)

           *.py) 

           *.py)

               poetry run ruff check "$file" 2>/dev/null || QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
               ;;
           *.md)
               markdownlint "$file" 2>/dev/null || QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
               ;;

           *.yml|*.yaml) 


           *.yml|*.yaml)

               yamllint "$file" 2>/dev/null || QUALITY_ISSUES=$((QUALITY_ISSUES + 1))
               ;;
       esac
   done


   



   # Early exit for clear rejection cases
   if [[ $QUALITY_ISSUES -gt 10 ]]; then
       echo "🚫 Major quality issues detected ($QUALITY_ISSUES violations) - providing immediate feedback"
       SKIP_MULTI_AGENT=true
   fi
   ```



### Step 3: Conditional Multi-Agent Analysis

### Step 3: Conditional Multi-Agent Analysis 

### Step 3: Conditional Multi-Agent Analysis



**Note**: This step is only executed if `SKIP_MULTI_AGENT` is false (quality issues < 10)

1. **Intelligent Agent Selection Based on PR Characteristics**:



   ```bash
   # Determine which agents are needed based on PR content
   AGENTS_NEEDED=()

   if [[ $MODE == "security-focus" ]] || grep -q "auth\|security\|encrypt\|token" <<< "$PR_DESCRIPTION"; then
       AGENTS_NEEDED+=("security")
   fi

   if [[ $MODE == "performance-focus" ]] || grep -q "performance\|optimize\|cache\|database" <<< "$PR_DESCRIPTION"; then
       AGENTS_NEEDED+=("performance")
   fi




   ```bash
   # Determine which agents are needed based on PR content
   AGENTS_NEEDED=()

   if [[ $MODE == "security-focus" ]] || grep -q "auth\|security\|encrypt\|token" <<< "$PR_DESCRIPTION"; then
       AGENTS_NEEDED+=("security")
   fi

   if [[ $MODE == "performance-focus" ]] || grep -q "performance\|optimize\|cache\|database" <<< "$PR_DESCRIPTION"; then
       AGENTS_NEEDED+=("performance")
   fi

   



   # Always include basic analysis for complex PRs
   if [[ $QUALITY_ISSUES -gt 5 ]] || [[ $MODE == "thorough" ]]; then
       AGENTS_NEEDED+=("edge-case" "test-architect")
   fi


   



   echo "🤖 Coordinating ${#AGENTS_NEEDED[@]} specialized agents: ${AGENTS_NEEDED[*]}"
   ```

2. **Model Validation and Fallbacks**:



   ```bash
   # Validate model availability before agent coordination
   MODELS_AVAILABLE=()


   ```bash
   # Validate model availability before agent coordination
   MODELS_AVAILABLE=()
   

   ```bash
   # Validate model availability before agent coordination
   MODELS_AVAILABLE=()


   # Test each model with a simple call first
   for model in "anthropic/claude-opus-4" "o3" "deepseek/deepseek-chat-v3-0324:free"; do
       if zen_mcp_test_model "$model" 2>/dev/null; then
           MODELS_AVAILABLE+=("$model")
       else
           echo "⚠️  Model $model unavailable, using fallback"
       fi
   done


   



   # Ensure we have at least one working model
   if [[ ${#MODELS_AVAILABLE[@]} -eq 0 ]]; then
       echo "🔄 All preferred models unavailable, falling back to single-agent analysis"
       SKIP_MULTI_AGENT=true
   fi
   ```

3. **Streamlined Agent Coordination** (only if needed):
   - **Security Analysis** (conditional):





     ```text
     Use Zen MCP Server for Security Auditor (validated model):
     - Model: First available from [claude-opus-4, anthropic/claude-sonnet-4]
     - Focus: Critical security patterns in changed files only
     - Quick assessment: authentication, input validation, dependency risks
     ```

   - **Performance Analysis** (conditional):



     ```text
     Use Zen MCP Server for Performance Analyst (validated model):
     - Model: First available from [o3, o4-mini]

     ```text
     Use Zen MCP Server for Performance Analyst (validated model):
     - Model: First available from [o3, o4-mini]  


     ```text
     Use Zen MCP Server for Performance Analyst (validated model):
     - Model: First available from [o3, o4-mini]

     - Focus: Algorithm complexity and resource usage patterns
     - Quick assessment: obvious performance bottlenecks only
     ```

### Step 4: Smart Consensus Decision

1. **Adaptive Consensus Strategy**:





   ```bash
   # Choose consensus approach based on complexity and quality issues
   if [[ $SKIP_MULTI_AGENT == "true" ]]; then
       echo "📋 Clear rejection case - generating direct feedback report"
       CONSENSUS_MODE="direct"
   elif [[ $QUALITY_ISSUES -le 3 ]] && [[ ${#AGENTS_NEEDED[@]} -le 1 ]]; then
       echo "✅ Straightforward case - lightweight consensus"
       CONSENSUS_MODE="lightweight"
   else
       echo "🤔 Complex case - full multi-agent consensus"
       CONSENSUS_MODE="comprehensive"
   fi
   ```

2. **Consensus Execution with Model Validation**:



   ```text
   Only run full consensus for complex cases:

   /zen:consensus (if CONSENSUS_MODE == "comprehensive")

   Models to consult (validated availability):
   - First available: [anthropic/claude-opus-4, anthropic/claude-sonnet-4]
   - First available: [o3, o4-mini]
   - First available: [deepseek/deepseek-chat-v3-0324:free, google/gemini-2.5-flash]




   ```text
   Only run full consensus for complex cases:

   /zen:consensus (if CONSENSUS_MODE == "comprehensive")

   Models to consult (validated availability):
   - First available: [anthropic/claude-opus-4, anthropic/claude-sonnet-4]
   - First available: [o3, o4-mini]
   - First available: [deepseek/deepseek-chat-v3-0324:free, google/gemini-2.5-flash]

   



   For lightweight cases, use single high-quality model assessment.
   For direct cases, skip consensus and generate immediate actionable feedback.
   ```

### Step 5: Testing Execution and Validation

1. **Execute Enhanced Test Suite**:
   - Run existing tests: `poetry run pytest -v --cov=src`
   - Execute security tests from Security Auditor recommendations
   - Run edge case scenarios from Edge Case Hunter analysis
   - Validate performance benchmarks if applicable

2. **Integration Testing**:
   - Test with external dependencies (Qdrant, Azure AI)
   - Validate multi-agent coordination if agents modified
   - Check UI/API integration points affected by changes

### Step 6: Generate Actionable PR Review Report

Generate mode-appropriate review report with GitHub integration:

```markdown
# PR Review Report: [PR Title]





**PR URL**: $ARGUMENTS
**Review Date**: [Current Date]
**Review Mode**: [adaptive/quick/thorough/security-focus/performance-focus]
**Analysis Strategy**: [full/sampled] ([TOTAL_LINES] lines, [FILE_COUNT] files)


## ⚡ Quick Summary
**Recommendation**: **[APPROVE ✅ / REQUEST CHANGES ❌ / COMMENT 💬]**
**Review Confidence**: [High/Medium/Low] ([CONSENSUS_MODE] consensus)
**Time to Review**: [X] minutes

## 📊 PR Overview
- **Author**: [Author] | **CI/CD**: [✅ Pass / ❌ Fail / ⏳ Pending]
- **Base**: [branch] → **Head**: [branch]

**PR URL**: $ARGUMENTS  
**Review Date**: [Current Date]  
**Review Mode**: [adaptive/quick/thorough/security-focus/performance-focus]  
**Analysis Strategy**: [full/sampled] ([TOTAL_LINES] lines, [FILE_COUNT] files)  



## ⚡ Quick Summary
**Recommendation**: **[APPROVE ✅ / REQUEST CHANGES ❌ / COMMENT 💬]**
**Review Confidence**: [High/Medium/Low] ([CONSENSUS_MODE] consensus)
**Time to Review**: [X] minutes

## 📊 PR Overview
- **Author**: [Author] | **CI/CD**: [✅ Pass / ❌ Fail / ⏳ Pending]

- **Base**: [branch] → **Head**: [branch]  


- **Base**: [branch] → **Head**: [branch]

- **Impact**: [FILE_COUNT] files, +[additions]/-[deletions] lines

## 🔍 Quality Gate Results
### Automated Compliance
- [✅/❌] **CI/CD Checks**: [status summary]
- [✅/❌] **Code Quality**: [QUALITY_ISSUES] violations found
- [✅/❌] **Security Scans**: [security status]
- [✅/❌] **Test Coverage**: [coverage%] (requirement: 80%)

## 🤖 Analysis Summary
[Conditional sections based on analysis performed]

### Quality Issues Found ([QUALITY_ISSUES] total)
[For each major issue, include:]
- **Issue**: [Description]
- **Location**: `[file]:[line]`
- **Fix Command**: `[specific command to fix]`
- **Priority**: [High/Medium/Low]

### Security Assessment (if performed)
- **Security Level**: [Low/Medium/High Risk]
- **Critical Issues**: [count] (see details below)

### Performance Impact (if assessed)
- **Performance Risk**: [Low/Medium/High]
- **Resource Impact**: [description]

## 🔧 Required Actions

### Immediate Blockers (Must Fix)
1. **[Issue Type]**: [Description]
   ```bash
   # Fix command:
   [exact command to run]
   ```



   **Files**: `[file1]`, `[file2]`

### Recommended Improvements

[Lower priority items with specific guidance]

## 📋 Copy-Paste Fix Commands




   **Files**: `[file1]`, `[file2]`

### Recommended Improvements

[Lower priority items with specific guidance]

## 📋 Copy-Paste Fix Commands

```bash
# Run these commands to address major issues:
[List of exact commands the developer can copy-paste]

# Verify fixes:
gh pr checks [PR_NUMBER]
poetry run ruff check [changed files]
```

## 🎯 Next Steps



- [ ] **Author**: Address blocking issues above
- [ ] **Author**: Run copy-paste fix commands

- [ ] **Author**: Address blocking issues above
- [ ] **Author**: Run copy-paste fix commands  


- [ ] **Author**: Address blocking issues above
- [ ] **Author**: Run copy-paste fix commands

- [ ] **Reviewer**: Re-review after fixes applied
- [ ] **CI/CD**: All checks must pass before merge

---
**📝 Review Notes**: [Any additional context or edge cases]
**🕒 Generated**: [timestamp] | **🤖 Agents Used**: [list of agents if multi-agent]



```markdown



```


## ✅ Adaptive Completion Criteria

Review is complete when appropriate criteria are met for the analysis mode:

### Quick Mode
1. ✅ **Basic quality gates** checked (CI/CD, linting, security)
2. ✅ **Direct recommendation** provided with specific fix commands
3. ✅ **Actionable report** generated (< 5 minutes)

### Adaptive Mode (Default)
1. ✅ **Quality assessment** determines analysis depth needed
2. ✅ **Appropriate agents** consulted based on PR content
3. ✅ **Smart consensus** reached using suitable approach
4. ✅ **Actionable report** with copy-paste fixes provided

### Thorough Mode
1. ✅ **Full multi-agent analysis** regardless of complexity
2. ✅ **Comprehensive consensus** from all available models
3. ✅ **Detailed report** with extensive recommendations

## 🛠️ Enhanced Error Handling

### GitHub API Resilience
```bash
# Primary → Fallback → Manual
gh pr view $PR || curl -s "https://api.github.com/repos/$REPO/pulls/$PR" || {
    echo "⚠️  GitHub unavailable - provide PR URL for manual analysis"
    exit 1
}
```

### Model Availability Issues





```bash
# Test models before use, provide graceful fallbacks
if ! test_model_availability; then
    echo "🔄 Advanced models unavailable - using basic analysis"
    ANALYSIS_MODE="basic"
fi
```

### Progress Indicators





```bash
# Show progress for long-running operations
echo "🔍 Step 1/4: Analyzing PR structure..."
echo "⚡ Step 2/4: Running quality gates..."


echo "🤖 Step 3/4: Coordinating agents..."

echo "🤖 Step 3/4: Coordinating agents..." 


echo "🤖 Step 3/4: Coordinating agents..."

echo "📝 Step 4/4: Generating report..."
```

## 📚 Usage Examples

```bash
# Adaptive review (default) - automatically scales based on PR complexity
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/143



# Quick review - essential checks only, ideal for small/obvious PRs

# Quick review - essential checks only, ideal for small/obvious PRs  


# Quick review - essential checks only, ideal for small/obvious PRs

/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/147 quick

# Thorough review - full multi-agent analysis regardless of size
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/148 thorough

# Security-focused - enhanced security analysis with specialized agents
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/149 security-focus



# Performance-focused - algorithm and resource usage analysis

# Performance-focused - algorithm and resource usage analysis  


# Performance-focused - algorithm and resource usage analysis

/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/150 performance-focus
```

## 📈 Performance Improvements

**Version 2.0 Enhancements:**





- ⚡ **5-45 minute adaptive timing** (vs. fixed 20-45 minutes)
- 🎯 **Early exit for clear cases** (quality issues > 10 → immediate feedback)
- 📊 **Large PR handling** (>20K lines → sampling strategy)
- 🔧 **Copy-paste fix commands** (actionable developer guidance)
- 🤖 **Model validation** (test availability before use)
- 📱 **Progress indicators** (real-time feedback during analysis)
- 🛡️ **Enhanced error handling** (graceful degradation strategies)

## Integration Notes

This command leverages existing project infrastructure:

- **Zen MCP Server**: For agent orchestration and coordination
- **Existing workflow commands**: validation-precommit, workflow-review-cycle patterns
- **Context7 integration**: For codebase understanding when available
- **Project standards**: CLAUDE.md compliance, style guides, quality gates

The command extends the project's multi-agent capabilities to GitHub PR review while maintaining


consistency with existing workflow patterns and development standards.

consistency with existing workflow patterns and development standards.


consistency with existing workflow patterns and development standards.

