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
- `--issue [number]`: Related issue number from phase-X-issues.md
- `--phase-merge`: Flag for phase completion PR (targets main)
- `--force-target`: Override branch validation (use with caution)
- `--dry-run`: Run validation only, don't create PR
- `--breaking`: Flag for breaking changes
- `--security`: Flag for security-related changes
- `--performance`: Flag for performance impacts
- `--create`: Create draft PR on GitHub after generation
- `--title [text]`: Custom PR title (auto-generate if not provided)
- `--wtd-summary`: Force include What The Diff summary shortcode (even if > 10k chars)
- `--no-wtd`: Exclude What The Diff summary shortcode (override auto-detection)

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
- `${issue_reference}`: Reference to phase-X-issues.md
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
- **Issue Reference**: [Issue #${issue_number}](../docs/planning/phase-${phase_number}-issues.md#${issue_number})
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

### 9. GitHub Integration (if --create flag used)

**Phase-aware Draft PR Creation Process**:

1. Validate GitHub CLI is available (`gh auth status`)
2. Apply phase-specific labels based on branch strategy
3. Create draft PR with generated content
4. Apply appropriate labels based on change types and phase
5. Assign suggested reviewers from CODEOWNERS or commit history
6. Link to related issues from commit messages

```bash
# Create draft PR command with phase awareness
if [[ $target_branch == "main" ]] && [[ $current_branch == phase-*-development ]]; then
    # Phase completion PR
    gh pr create \
      --title "🎯 Phase ${phase_number} Completion: ${phase_name}" \
      --body-file "${temp_pr_description}" \
      --base "main" \
      --head "${current_branch}" \
      --draft \
      --label "phase-completion,${phase_number},${change_type},${size_label}" \
      --assignee "${suggested_reviewers}"
else
    # Standard PR
    gh pr create \
      --title "${generated_title}" \
      --body-file "${temp_pr_description}" \
      --base "${base_branch}" \
      --head "${target_branch}" \
      --draft \
      --label "phase-${phase_number},${change_type},${size_label},${additional_labels}" \
      --assignee "${suggested_reviewers}"
fi
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
- **Issue Integration**: Connects with phase-X-issues.md structure
- **Prevents Fragmentation**: Guides toward proper branch consolidation
- **User-Friendly**: Provides clear guidance and automatic corrections
- **Flexible**: Supports both phase completion and issue work PRs
- **GitHub Integration**: Works with existing GitHub CLI and Actions
- **WTD Integration**: Properly handles What The Diff as a GitHub App
- **Backwards Compatible**: Maintains existing functionality while adding safety
