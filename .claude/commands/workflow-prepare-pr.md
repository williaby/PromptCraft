# Prepare Pull Request (Enhanced with Branch Safety)

Generate a comprehensive, standardized pull request description and optionally create a draft PR on GitHub from git
commits and changes: $ARGUMENTS

## Analysis Required

0. **Branch Strategy Validation**: Validate current branch strategy and ensure proper targeting
1. **Git History Analysis**: Analyze commits between base and target branch
2. **Change Impact Assessment**: Calculate files, lines, and complexity metrics
3. **PR Template Integration**: Populate variables in pull request template
4. **Size Analysis & Splitting**: Evaluate PR size against review tool limits
5. **Content Generation**: Create structured descriptions from commit analysis
6. **GitHub Integration**: Optionally create draft PR with proper metadata

## Instructions

### 0. Branch Strategy Validation and Safety Checks

**CRITICAL**: This step runs before any PR preparation to ensure proper branch strategy.

```bash
# Execute branch validation
current_branch=$(git branch --show-current)
target_branch="${target_branch:-main}"
base_branch="${base_branch:-main}"

# Branch validation function
validate_branch_strategy() {
    local current="$1"
    local target="$2"
    local base="$3"

    echo "🔍 Analyzing branch strategy..."
    echo "Current branch: $current"
    echo "Target branch: $target"
    echo "Base branch: $base"

    # Check if targeting main from non-phase branch
    if [[ "$target" == "main" ]] && [[ "$current" != "phase-"*"-development" ]]; then
        echo "⚠️  WARNING: Targeting main branch from non-phase branch!"
        return 1
    fi

    # Check if on main branch with changes
    if [[ "$current" == "main" ]]; then
        echo "❌ ERROR: Cannot create PR from main branch!"
        return 2
    fi

    return 0
}

# Commit analysis for issue detection
analyze_commits_for_issue() {
    local base="$1"
    local current="$2"

    # Extract issue references from commits
    local commit_messages=$(git log --oneline "$base..$current" | head -10)
    local issue_refs=$(echo "$commit_messages" | grep -oE "(issue|Issue) #[0-9]+" | grep -oE "[0-9]+" | sort -u)
    local create_refs=$(echo "$commit_messages" | grep -iE "(create|c\.r\.e\.a\.t\.e)" | wc -l)

    echo "📋 Commit Analysis Results:"
    echo "- Issue references found: $issue_refs"
    echo "- C.R.E.A.T.E. related commits: $create_refs"

    # Return primary issue if detected
    if [[ -n "$issue_refs" ]]; then
        echo "$issue_refs" | head -1
    else
        echo ""
    fi
}

# Change pattern analysis
analyze_change_patterns() {
    local base="$1"
    local current="$2"

    echo "🔍 Analyzing change patterns..."

    # File change analysis
    local changed_files=$(git diff --name-only "$base..$current")
    local file_count=$(echo "$changed_files" | wc -l)

    # Pattern detection
    local security_changes=$(echo "$changed_files" | grep -E "(security|auth|encrypt)" | wc -l)
    local create_changes=$(echo "$changed_files" | grep -E "(create|core)" | wc -l)
    local ui_changes=$(echo "$changed_files" | grep -E "(ui|gradio|interface)" | wc -l)
    local test_changes=$(echo "$changed_files" | grep -E "(test|spec)" | wc -l)

    echo "📊 Change Pattern Analysis:"
    echo "- Files changed: $file_count"
    echo "- Security related: $security_changes files"
    echo "- C.R.E.A.T.E. related: $create_changes files"
    echo "- UI related: $ui_changes files"
    echo "- Test related: $test_changes files"

    # Generate recommendations
    if [[ $security_changes -gt 0 ]]; then
        echo "🔒 Security-related changes detected"
        echo "💡 Recommendation: Use issue-9-security-implementation branch"
    fi

    if [[ $create_changes -gt 0 ]]; then
        echo "⚡ C.R.E.A.T.E. framework changes detected"
        echo "💡 Recommendation: Use issue-4-create-framework branch"
    fi

    if [[ $ui_changes -gt 0 ]]; then
        echo "🖥️  UI changes detected"
        echo "💡 Recommendation: Use issue-5-gradio-ui branch"
    fi
}

# Intent confirmation for main branch targeting
handle_main_branch_targeting() {
    local primary_issue=$(analyze_commits_for_issue "$base_branch" "$current_branch")

    echo ""
    echo "🎯 BRANCH STRATEGY DECISION REQUIRED"
    echo "=========================================="
    echo ""
    echo "You're about to create a PR targeting 'main' from '$current_branch'."
    echo ""

    if [[ -n "$primary_issue" ]]; then
        echo "📋 Detected work on Issue #$primary_issue"
        echo "📁 Expected branch: issue-$primary_issue-* or phase-1-development"
        echo ""
    fi

    echo "Please choose your intent:"
    echo ""
    echo "1. 🎯 PHASE COMPLETION - This represents a completed phase (recommended for phase-*-development branches)"
    echo "2. 🔧 ISSUE WORK - This is work on a specific issue (should target phase branch)"
    echo "3. 🏗️  FEATURE BRANCH - This is part of larger feature work (needs issue branch)"
    echo "4. 🚨 HOTFIX - This is an urgent fix that must go directly to main"
    echo "5. ❌ CANCEL - Let me fix my branch strategy first"
    echo ""

    read -p "Enter your choice (1-5): " choice

    case $choice in
        1)
            echo "✅ Confirmed as phase completion PR"
            ;;
        2)
            suggest_phase_branch_target
            ;;
        3)
            suggest_issue_branch_creation
            ;;
        4)
            echo "⚠️  Hotfix confirmed - proceeding to main"
            ;;
        5)
            echo "✅ Cancelled. Fix your branch strategy and run again."
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please run the command again."
            exit 1
            ;;
    esac
}

# Suggest phase branch targeting
suggest_phase_branch_target() {
    echo ""
    echo "🎯 PHASE BRANCH TARGETING RECOMMENDED"
    echo "======================================"
    echo ""
    echo "This work should target the phase development branch instead of main."
    echo ""

    # Auto-detect phase
    local phase_branch="phase-1-development"
    if git branch -a | grep -q "origin/$phase_branch"; then
        echo "✅ Found existing phase branch: $phase_branch"
    else
        echo "❌ Phase branch '$phase_branch' not found."
        echo "🔧 Would you like me to create it? (y/n)"
        read -p "> " create_phase
        if [[ "$create_phase" == "y" ]]; then
            git checkout -b "$phase_branch" main
            git push -u origin "$phase_branch"
            echo "✅ Created and pushed $phase_branch"
        else
            echo "❌ Cannot proceed without phase branch. Exiting."
            exit 1
        fi
    fi

    echo ""
    echo "🔄 I'll update the target branch to: $phase_branch"
    echo "📤 Your PR will target: $phase_branch (instead of main)"
    echo ""

    # Update global variables
    target_branch="$phase_branch"
    base_branch="main"

    echo "✅ Branch strategy updated. Continuing with PR preparation..."
}

# Suggest issue branch creation
suggest_issue_branch_creation() {
    local primary_issue=$(analyze_commits_for_issue "$base_branch" "$current_branch")

    echo ""
    echo "🏗️  ISSUE BRANCH CREATION RECOMMENDED"
    echo "===================================="
    echo ""

    if [[ -n "$primary_issue" ]]; then
        local suggested_branch="issue-$primary_issue-implementation"
        echo "📋 Detected Issue #$primary_issue"
        echo "🌟 Suggested branch name: $suggested_branch"
    else
        echo "❓ No clear issue detected. Please specify:"
        read -p "Enter issue number: " issue_num
        local suggested_branch="issue-$issue_num-implementation"
        primary_issue="$issue_num"
    fi

    echo ""
    echo "🔧 I can move your changes to the correct branch structure:"
    echo "1. Create new branch: $suggested_branch"
    echo "2. Move your commits to this branch"
    echo "3. Target phase-1-development for the PR"
    echo ""

    read -p "Proceed with branch reorganization? (y/n): " proceed

    if [[ "$proceed" == "y" ]]; then
        move_changes_to_issue_branch "$suggested_branch" "$primary_issue"
    else
        echo "❌ Cancelled. Please organize your branches manually."
        exit 1
    fi
}

# Move changes to issue branch
move_changes_to_issue_branch() {
    local new_branch="$1"
    local issue_num="$2"
    local phase_branch="phase-1-development"

    echo ""
    echo "🔄 MOVING CHANGES TO CORRECT BRANCH"
    echo "==================================="
    echo ""

    # Ensure phase branch exists
    if ! git branch -a | grep -q "$phase_branch"; then
        echo "🔧 Creating phase branch: $phase_branch"
        git checkout -b "$phase_branch" main
        git push -u origin "$phase_branch"
    fi

    # Create issue branch from phase branch
    echo "🌟 Creating issue branch: $new_branch"
    git checkout "$phase_branch"
    git pull origin "$phase_branch" 2>/dev/null || true
    git checkout -b "$new_branch"

    # Cherry-pick commits from current branch
    echo "🍒 Moving commits to issue branch..."
    local commits=$(git log --oneline "$base_branch..$current_branch" --reverse | cut -d' ' -f1)

    for commit in $commits; do
        echo "  📝 Moving commit: $commit"
        git cherry-pick "$commit"
    done

    # Push new branch
    git push -u origin "$new_branch"

    # Update global variables
    target_branch="$phase_branch"
    base_branch="main"

    echo ""
    echo "✅ Branch reorganization complete!"
    echo "📍 Current branch: $new_branch"
    echo "🎯 PR will target: $phase_branch"
    echo "📋 Related to Issue #$issue_num"
}

# Main validation logic
validate_branch_strategy "$current_branch" "$target_branch" "$base_branch"
validation_result=$?

case $validation_result in
    1)
        echo ""
        echo "🤔 This looks like it should target a phase branch instead of main."
        echo "Let me help you determine the correct branch strategy..."
        analyze_change_patterns "$base_branch" "$current_branch"
        handle_main_branch_targeting
        ;;
    2)
        echo ""
        echo "🚨 You're on the main branch with changes. This needs to be fixed."
        echo "Please create a feature branch and move your changes there."
        exit 1
        ;;
    0)
        echo "✅ Branch strategy looks good!"
        ;;
esac
```

### 1.5. Dependency Validation and Requirements Generation

**CRITICAL**: This step runs before commit analysis to ensure dependency consistency and prevent Docker build failures.

```bash
# Dependency validation and requirements generation
validate_and_update_dependencies() {
    echo ""
    echo "🔍 DEPENDENCY VALIDATION AND REQUIREMENTS GENERATION"
    echo "=================================================="
    echo ""

    # Check if skip-deps flag is set
    if [[ "$skip_deps" == "true" ]]; then
        echo "⏭️  Skipping dependency validation (--skip-deps flag set)"
        return 0
    fi

    # Check if poetry.lock exists
    if [[ ! -f "poetry.lock" ]]; then
        echo "❌ ERROR: poetry.lock not found. Run 'poetry install' first."
        exit 1
    fi

    # Check if pyproject.toml has been modified
    local pyproject_modified=$(git diff --name-only "$base_branch..$current_branch" | grep -c "pyproject.toml" || echo "0")

    if [[ $pyproject_modified -gt 0 ]]; then
        echo "📦 pyproject.toml modifications detected. Updating dependencies..."

        # Check for dependency conflicts before updating
        echo "🔍 Checking for dependency conflicts..."
        if ! poetry check 2>/dev/null; then
            echo "⚠️  Lock file is inconsistent with pyproject.toml. Regenerating..."
            poetry lock
        fi

        # Install dependencies to ensure environment is consistent
        echo "📥 Installing dependencies..."
        poetry install

        # Validate the lock file after installation
        if ! poetry check; then
            echo "❌ ERROR: Poetry lock file validation failed after installation"
            exit 1
        fi

        echo "✅ Dependencies updated and validated"
    else
        echo "📦 No pyproject.toml changes detected. Validating existing dependencies..."

        # Quick validation of existing lock file
        if ! poetry check; then
            echo "❌ ERROR: Existing poetry.lock is inconsistent"
            echo "💡 Run 'poetry lock' to fix"
            exit 1
        fi

        echo "✅ Existing dependencies validated"
    fi

    # Generate requirements files
    echo ""
    echo "📋 Generating requirements files..."

    # Check if generate_requirements.sh exists
    if [[ ! -f "scripts/generate_requirements.sh" ]]; then
        echo "❌ ERROR: scripts/generate_requirements.sh not found"
        exit 1
    fi

    # Make script executable
    chmod +x scripts/generate_requirements.sh

    # Run requirements generation
    if ! ./scripts/generate_requirements.sh; then
        echo "❌ ERROR: Requirements generation failed"
        exit 1
    fi

    # Check if requirements files were generated/updated
    local req_files=("requirements.txt" "requirements-dev.txt" "requirements-docker.txt")
    local files_updated=0

    for file in "${req_files[@]}"; do
        if [[ -f "$file" ]]; then
            if git diff --quiet "$file" 2>/dev/null; then
                echo "📄 $file: No changes"
            else
                echo "📄 $file: Updated"
                files_updated=$((files_updated + 1))
            fi
        else
            echo "⚠️  $file: Missing (should be generated)"
        fi
    done

    # Stage updated requirements files
    if [[ $files_updated -gt 0 ]]; then
        echo ""
        echo "📤 Staging updated requirements files..."
        git add requirements*.txt poetry.lock 2>/dev/null || true

        # Commit requirements updates if there are changes
        if ! git diff --cached --quiet; then
            echo "💾 Committing requirements updates..."
            git commit -m "chore(deps): update requirements files from poetry.lock

- Generated requirements.txt, requirements-dev.txt, requirements-docker.txt
- Ensures Docker build consistency with poetry.lock
- Maintains hash verification for security

🤖 Generated with Claude Code"
        fi
    fi

    echo ""
    echo "✅ Dependency validation and requirements generation complete"
    echo "📋 Summary:"
    echo "  - poetry.lock: Validated and consistent"
    echo "  - requirements.txt: Generated with hashes"
    echo "  - requirements-dev.txt: Generated with dev dependencies"
    echo "  - requirements-docker.txt: Generated for production builds"
    echo ""
}

# Security validation for dependencies
validate_dependency_security() {
    echo "🔒 Running dependency security checks..."

    # Check for known vulnerabilities using safety
    if command -v poetry >/dev/null 2>&1; then
        echo "🛡️  Running Safety check..."
        if ! poetry run safety check --json > safety_report.json 2>/dev/null; then
            echo "⚠️  Safety check found potential vulnerabilities"
            echo "📄 Report saved to safety_report.json"

            # Show critical vulnerabilities
            if command -v jq >/dev/null 2>&1; then
                echo "🚨 Critical vulnerabilities found:"
                jq -r '.[] | select(.severity == "high" or .severity == "critical") |
                  "  - \(.package): \(.advisory)"' safety_report.json 2>/dev/null ||
                  echo "  (Could not parse safety report)"
            fi

            # Don't fail the build for security issues, but warn
            echo "⚠️  Please review security report before proceeding"
        else
            echo "✅ No known vulnerabilities found"
        fi

        # Clean up report file
        rm -f safety_report.json
    fi
}

# Run dependency validation
validate_and_update_dependencies

# Run security validation
validate_dependency_security
```

**Safety Features**:

- ✅ **Main Branch Protection**: Prevents accidental direct commits to main
- ✅ **Phase Targeting**: Ensures work targets appropriate phase branch
- ✅ **Issue Detection**: Identifies related issues and suggests proper branches
- ✅ **Change Analysis**: Analyzes patterns to recommend branch strategy
- ✅ **Branch Migration**: Automatically moves changes to correct branches
- ✅ **User Confirmation**: Confirms intent for main branch merges

### 1. Parse Command Arguments (Enhanced)

Extract options from `$ARGUMENTS` with new phase-aware options:

- `--branch [name]`: Target branch (default: auto-detected from validation)
- `--base [name]`: Base branch for comparison (default: auto-detected)
- `--type [type]`: Change type (feat, fix, docs, style, refactor, perf, test, chore)
- `--phase [number]`: Target phase number (auto-detects if not provided)
- `--issue [number]`: Related issue number from phase-X-index.md (references specific category file)
- `--phase-merge`: Flag for phase completion PR (targets main)
- `--force-target`: Override branch validation (use with caution)
- `--dry-run`: Run validation only, don't create PR
- `--breaking`: Flag for breaking changes
- `--security`: Flag for security-related changes
- `--performance`: Flag for performance impacts
- `--no-push`: Skip automatic push to GitHub (default: auto-push enabled)
- `--title [text]`: Custom PR title (auto-generate if not provided)
- `--wtd-summary`: Force include What The Diff summary shortcode (even if > 10k chars)
- `--no-wtd`: Exclude What The Diff summary shortcode (override auto-detection)
- `--skip-deps`: Skip dependency validation and requirements generation

### 2. Git Commit Analysis (Phase-Aware)

```bash
# Phase-aware git analysis
if [[ $base_branch == "main" ]] && [[ $target_branch == phase-*-development ]]; then
    # Phase completion PR - analyze entire phase
    git log --oneline main..${target_branch}
    git diff --stat main..${target_branch}
    # Include phase-specific metrics
elif [[ $base_branch == phase-*-development ]]; then
    # Feature branch targeting phase
    git log --oneline ${base_branch}..${target_branch}
    git diff --stat ${base_branch}..${target_branch}
else
    # Standard analysis
    git log --oneline ${base_branch}..${target_branch}
    git diff --stat ${base_branch}..${target_branch}
fi

git diff --numstat ${base_branch}..${target_branch}
git log --pretty=format:"%h %s %an %ae" ${base_branch}..${target_branch}
```

**Extract from commits**:

- Conventional commit types and scopes (feat, fix, docs, etc.)
- Breaking change indicators (BREAKING CHANGE:, !)
- Issue references (#123, closes #456, fixes #789)
- Phase-specific issue references (Issue #4, Issue #9, etc.)
- Co-authors from commit messages (especially Claude/Copilot)
- Feature flags or experimental changes
- Security-related keywords

**Group commits by**:

- Type (feat, fix, docs, etc.)
- Scope/component affected
- Risk level (breaking, security, performance)
- Phase relationship (phase completion vs. issue work)

### 3. Change Impact Calculation

**File Statistics**:

- Total files: added, modified, removed
- Language breakdown from file extensions
- Test file vs source file ratio
- Configuration file changes
- Documentation file changes

**Size Metrics**:

- Total lines added/removed
- PR size classification (Small < 100 lines, Medium < 400 lines, Large < 1000 lines, XL > 1000 lines)
- Token estimation for review tools
- Complexity score based on file types and change patterns

**Review Tool Compatibility**:

- GitHub Copilot: Max 28 files
- WhatTheDiff: Max 2500 tokens
- General review: Optimal < 400 lines

### 4. PR Template Variable Population

Use the pull request template from `docs/planning/pull-request-template.md` and populate these variables:

**Header Variables**:

- `${pr_emoji}`: Auto-select based on primary change type
- `${pr_title}`: Generate from commits or use --title argument

**Phase-Specific Variables**:

- `${phase_number}`: Current phase number (1, 2, 3, etc.)
- `${phase_name}`: Phase name (Foundation & Journey 1, etc.)
- `${issue_reference}`: Reference to phase-X-index.md with links to category files
- `${phase_context}`: Context about phase relationship

**Change Summary Variables**:

- `${files_changed}`: Total file count
- `${files_added}`, `${files_modified}`, `${files_removed}`: Breakdown counts
- `${lines_added}`, `${lines_removed}`: Line change counts
- `${coverage_before}`, `${coverage_after}`, `${coverage_delta}`: Test coverage analysis (if available)
- `${pr_size_label}`: Small/Medium/Large/XL classification
- `${review_tools_status}`: Compatibility with review tools

**Content Variables**:

- `${pr_summary}`: Generate comprehensive summary from commit messages and change analysis
- `${pr_motivation}`: Extract from issue references, commit context, and problem being solved
- `${changes_added}`: List of new features, files, capabilities
- `${changes_modified}`: List of enhanced/updated functionality
- `${changes_removed}`: List of deprecated/removed items
- `${usage_example}`: Extract key code examples from changes
- `${testing_instructions}`: Generate based on test file changes and functionality

**Technical Variables**:

- `${architecture_diagram}`: Generate Mermaid diagram if architectural changes detected
- `${performance_section}`: Analyze performance implications
- `${security_section}`: Identify security-related changes
- `${breaking_changes_section}`: Document breaking changes and migration steps

### 5. Phase-Aware PR Templates

#### Phase Completion PR Template

```markdown
## 🎯 Phase ${phase_number} Completion: ${phase_name}

### 📊 Phase Summary
| Metric | Value |
|--------|-------|
| **Issues Completed** | ${completed_issues}/${total_issues} |
| **Files Changed** | ${files_changed} |
| **Lines Added/Removed** | +${lines_added} / -${lines_removed} |
| **Test Coverage** | ${coverage_before}% → ${coverage_after}% |
| **Phase Duration** | ${phase_start} → ${phase_end} |

### ✅ Phase Acceptance Criteria
${phase_acceptance_criteria_checklist}

### 🔄 Issues Implemented
${completed_issues_list}

### 🧪 Phase Testing
${phase_testing_summary}

### 🚀 Version Release
This PR represents the completion of Phase ${phase_number} and will be tagged as version ${version_number}.
```

#### Phase Feature PR Template

```markdown
## ✨ Issue #${issue_number}: ${issue_title}

### 🎯 Phase Context
- **Phase**: ${phase_number} - ${phase_name}
- **Issue Reference**: [Issue #${issue_number}](../docs/planning/phase-${phase_number}-index.md#issue-${issue_number})
- **Target Branch**: `phase-${phase_number}-development`

### 📊 Change Summary
${standard_change_summary}

### 🔗 Phase Integration
This change integrates with phase-${phase_number}-development and will be included in the phase completion PR.
```

### 6. Size Analysis and PR Splitting Suggestions

**Phase-aware splitting suggestions**:

```markdown
## ⚠️ PR Size Warning

This PR exceeds recommended size limits for optimal review:

| Metric | Current | Limit | Status |
|--------|---------|-------|--------|
| Files Changed | ${current_files} | 28 (Copilot) | ${status_icon} |
| Total Lines | ${current_lines} | 400 (recommended) | ${status_icon} |
| Diff Tokens | ${current_tokens} | 2,500 (WhatTheDiff) | ${status_icon} |

### 🔀 Phase-Aware Splitting Strategy

For phase completion PRs:
1. Split by issue (create separate issue branches)
2. Target phase-${phase_number}-development
3. Merge phase branch to main when complete

For issue work:
1. Split by functionality within the issue
2. Keep related changes together
3. Target phase-${phase_number}-development
```

### 7. Security and Performance Analysis

**Security Analysis**:

- Authentication/authorization changes
- Credential/secret handling
- Input validation changes
- Permission model updates
- Dependency security updates

**Performance Analysis**:

- Startup time impact
- Memory usage changes
- Runtime performance implications
- Database query optimization
- Caching strategy updates

### 8. What The Diff Integration Logic

**Character Limit Detection**:

1. Calculate total PR description length (including all template content)
2. Apply the following logic for WTD shortcode inclusion:

```python
# Pseudo-code for WTD inclusion logic
total_chars = len(generated_pr_description)

if args.no_wtd:
    # User explicitly disabled WTD
    include_wtd = False
elif args.wtd_summary:
    # User explicitly requested WTD (override size limit)
    include_wtd = True
elif total_chars > 10000:
    # Auto-exclude WTD for large PRs to prevent overwhelming descriptions
    include_wtd = False
    print("⚠️ PR description exceeds 10,000 characters. WTD summary excluded.")
    print("   Use --wtd-summary to force inclusion if needed.")
else:
    # Default: include WTD for reasonably-sized PRs
    include_wtd = True
```

**WTD Shortcode Placement**:

- If `include_wtd == True`: Add `wtd:summary` shortcode after "Notes for Reviewers" section
- If `include_wtd == False`: Omit the shortcode entirely
- The shortcode should be on its own line with no surrounding text

**Note**: What The Diff works as a GitHub App, not a GitHub Action. The shortcode `wtd:summary` is processed by the
app when it's installed on the repository.

### 9. GitHub Integration (Automatic Push and PR Creation)

**Phase-aware Draft PR Creation Process**:

1. Validate GitHub CLI is available (`gh auth status`)
2. Push current branch to GitHub (unless --no-push flag used)
3. Apply phase-specific labels based on branch strategy
4. Create draft PR with generated content
5. Apply appropriate labels based on change types and phase
6. Assign suggested reviewers from CODEOWNERS or commit history
7. Link to related issues from commit messages

```bash
# GitHub Integration with automatic push
github_integration() {
    echo ""
    echo "🚀 GITHUB INTEGRATION"
    echo "===================="
    echo ""

    # Check if --no-push flag is set
    if [[ "$no_push" == "true" ]]; then
        echo "⏭️  Skipping automatic GitHub push (--no-push flag set)"
        echo "💡 Don't forget to push manually: git push origin $current_branch"
        return 0
    fi

    # Validate GitHub CLI is available
    if ! command -v gh >/dev/null 2>&1; then
        echo "❌ ERROR: GitHub CLI (gh) is not installed"
        echo "💡 Install from: https://cli.github.com/"
        exit 1
    fi

    # Check GitHub authentication
    if ! gh auth status >/dev/null 2>&1; then
        echo "❌ ERROR: GitHub CLI is not authenticated"
        echo "💡 Run: gh auth login"
        exit 1
    fi

    # Push current branch to GitHub
    echo "📤 Pushing branch to GitHub..."

    # Check if branch exists on remote
    if git ls-remote --exit-code --heads origin "$current_branch" >/dev/null 2>&1; then
        echo "📄 Branch exists on remote. Pushing updates..."
        git push origin "$current_branch"
    else
        echo "🆕 New branch. Pushing with upstream tracking..."
        git push -u origin "$current_branch"
    fi

    # Verify push was successful
    if [[ $? -eq 0 ]]; then
        echo "✅ Branch successfully pushed to GitHub"
    else
        echo "❌ ERROR: Failed to push branch to GitHub"
        exit 1
    fi

    # Generate suggested reviewers
    local suggested_reviewers=""
    if [[ -f ".github/CODEOWNERS" ]]; then
        suggested_reviewers=$(grep -E "^\*|^/.*" .github/CODEOWNERS | head -1 |
          cut -d' ' -f2- | tr -d '@' | tr ' ' ',' | head -c 50)
    fi

    # Generate additional labels based on change analysis
    local additional_labels=""
    if [[ "$breaking_changes" == "true" ]]; then
        additional_labels="breaking-change,"
    fi
    if [[ "$security_changes" == "true" ]]; then
        additional_labels="${additional_labels}security,"
    fi
    if [[ "$performance_changes" == "true" ]]; then
        additional_labels="${additional_labels}performance,"
    fi

    # Create PR with generated content
    echo "📋 Creating draft PR on GitHub..."

    # Write PR description to temporary file
    local temp_pr_description=$(mktemp)
    echo "${generated_pr_description}" > "$temp_pr_description"

    # Create draft PR command with phase awareness
    if [[ $target_branch == "main" ]] && [[ $current_branch == phase-*-development ]]; then
        # Phase completion PR
        if gh pr create \
          --title "🎯 Phase ${phase_number} Completion: ${phase_name}" \
          --body-file "$temp_pr_description" \
          --base "main" \
          --head "$current_branch" \
          --draft \
          --label "phase-completion,phase-${phase_number},${change_type},${size_label},${additional_labels%,}" \
          ${suggested_reviewers:+--assignee "$suggested_reviewers"}; then
            echo "✅ Phase completion PR created successfully"
        else
            echo "❌ ERROR: Failed to create phase completion PR"
            exit 1
        fi
    else
        # Standard PR
        if gh pr create \
          --title "${generated_title}" \
          --body-file "$temp_pr_description" \
          --base "$target_branch" \
          --head "$current_branch" \
          --draft \
          --label "phase-${phase_number},${change_type},${size_label},${additional_labels%,}" \
          ${suggested_reviewers:+--assignee "$suggested_reviewers"}; then
            echo "✅ Draft PR created successfully"
        else
            echo "❌ ERROR: Failed to create draft PR"
            exit 1
        fi
    fi

    # Get PR URL for user
    local pr_url=$(gh pr view --json url -q .url 2>/dev/null)
    if [[ -n "$pr_url" ]]; then
        echo "🔗 PR URL: $pr_url"
    fi

    # Clean up temporary file
    rm -f "$temp_pr_description"

    echo ""
    echo "🎉 PR preparation complete!"
    echo "✅ Branch pushed to GitHub"
    echo "✅ Draft PR created"
    echo "💡 Next steps:"
    echo "  1. Review the PR description and make any necessary edits"
    echo "  2. Mark the PR as ready for review when complete"
    echo "  3. Request reviews from team members"
    echo ""
}

# Run GitHub integration
github_integration
```

### 10. Emoji and Type Mapping

**Change Type Emojis**:

- `feat`: ✨ (sparkles)
- `fix`: 🐛 (bug)
- `docs`: 📚 (books)
- `style`: 💎 (gem)
- `refactor`: ♻️ (recycle)
- `perf`: ⚡ (zap)
- `test`: ✅ (white_check_mark)
- `chore`: 🔧 (wrench)
- `security`: 🔒 (lock)
- `breaking`: 💥 (boom)
- `phase-completion`: 🎯 (target)

**PR Size Labels**:

- Small (< 100 lines): `size/small`
- Medium (100-400 lines): `size/medium`
- Large (400-1000 lines): `size/large`
- XL (> 1000 lines): `size/xl`

### 11. Co-Author Detection and Attribution

**Identify AI Co-Authors**:

- Claude Code contributions
- GitHub Copilot contributions
- Other AI tools mentioned in commits

**Format Attribution**:

```text
Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: GitHub Copilot <noreply@github.com>
```

## Integration with Existing Workflow

This enhanced command integrates seamlessly with your phase-based development process:

**Before `/project:workflow-prepare-pr`**:

- Use `/project:workflow-review-cycle` to wrap up issue work
- Ensure all commits are clean and follow conventional format
- Complete testing and validation

**After `/project:workflow-prepare-pr`**:

- Review generated PR description
- Use subsequent slash command for PR review
- Create/update draft PR on GitHub
- Iterate based on team feedback

## Important Notes

- **Branch Safety First**: Always validates branch strategy before proceeding
- **Phase-Aware**: Understands your phase-based development approach
- **Issue Integration**: Connects with phase-X-index.md structure and category files
- **Prevents Fragmentation**: Guides toward proper branch consolidation
- **User-Friendly**: Provides clear guidance and automatic corrections
- **Flexible**: Supports both phase completion and issue work PRs
- **Automatic Push**: Pushes to GitHub and creates draft PR by default (use --no-push to disable)
- **Dependency Safety**: Validates poetry.lock and regenerates requirements files automatically
- **Security Integration**: Runs dependency security checks before PR creation
- **GitHub Integration**: Works with existing GitHub CLI and Actions
- **WTD Integration**: Properly handles What The Diff as a GitHub App
- **Backwards Compatible**: Maintains existing functionality while adding safety
