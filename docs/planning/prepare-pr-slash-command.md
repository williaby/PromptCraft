# Prepare PR Slash Command

## Command Name: `/prepare-pr`

## Description
Analyzes commits and generates a comprehensive pull request description following best practices, including visual summaries, architecture diagrams, and structured documentation.

## Usage
```
/prepare-pr [options]
```

### Options:
- `--branch`: Target branch name (defaults to current branch)
- `--base`: Base branch for comparison (defaults to main)
- `--type`: PR type (feat, fix, docs, style, refactor, perf, test, chore)
- `--breaking`: Flag to indicate breaking changes
- `--security`: Flag to highlight security-related changes
- `--performance`: Flag to highlight performance impacts
- `--create`: Create draft PR on GitHub after generating description
- `--wtd`: Include WhatTheDiff placeholders (summary, joke, poem)
- `--title`: Custom PR title (otherwise auto-generated from commits)

## Command Implementation

```yaml
name: prepare-pr
description: Generate comprehensive PR documentation from commits
version: 1.0.0
author: your-username

parameters:
  - name: branch
    type: string
    default: current
    description: Target branch name
  - name: base
    type: string
    default: main
    description: Base branch for comparison
  - name: type
    type: string
    default: feat
    choices: [feat, fix, docs, style, refactor, perf, test, chore, build, ci]
    description: Type of change
  - name: breaking
    type: boolean
    default: false
    description: Contains breaking changes
  - name: security
    type: boolean
    default: false
    description: Contains security-related changes
  - name: performance
    type: boolean
    default: false
    description: Contains performance impacts
  - name: create
    type: boolean
    default: false
    description: Create draft PR on GitHub
  - name: wtd
    type: boolean
    default: true
    description: Include WhatTheDiff placeholders
  - name: title
    type: string
    default: auto
    description: Custom PR title

steps:
  - name: analyze_commits
    action: |
      1. Get commit history between base and target branch
      2. Parse commit messages for conventional commits
      3. Extract:
         - Commit types and scopes
         - Breaking change indicators
         - Issue references (#123, closes #456)
         - Co-authors
      4. Group commits by type
      5. Identify modified files and changes

  - name: analyze_code_changes
    action: |
      1. Get diff statistics:
         - Files added/modified/removed
         - Total lines added/removed
         - Language breakdown
      2. Identify:
         - New dependencies added
         - Configuration changes
         - API changes
         - Database migrations
         - Security-relevant files
      3. Check for:
         - Test file changes
         - Documentation updates
         - CI/CD modifications
      4. Calculate PR size metrics:
         - Total diff size in tokens
         - Number of changed files
         - Lines of code changed
         - Complexity score

  - name: calculate_test_coverage
    action: |
      1. Run test coverage if available
      2. Compare with base branch coverage
      3. Calculate coverage delta
      4. Identify uncovered new code

  - name: detect_architecture_changes
    action: |
      1. Analyze structural changes:
         - New modules/packages
         - Modified interfaces
         - Dependency graph changes
      2. Generate architecture diagram if significant changes
      3. Document integration points

  - name: generate_pr_content
    action: |
      1. Create structured PR description:
         - Summary from commit messages
         - Categorized changes
         - Visual elements (tables, diagrams)
         - Code examples
         - Testing instructions
      2. Auto-generate:
         - Review checklist
         - Migration guide (if needed)
         - Performance/security impacts
      3. Format using template
      4. Handle WhatTheDiff placeholders:
         - Keep wtd:summary if --wtd flag set
         - Add wtd:joke or wtd:poem if requested
         - Otherwise populate with generated content
      5. Prepare for GitHub creation if requested

  - name: create_visual_elements
    action: |
      1. Generate change summary table
      2. Create architecture diagrams (if applicable)
      3. Add emoji indicators for better scanning
      4. Format code examples with syntax highlighting

  - name: suggest_reviewers
    action: |
      1. Analyze changed files
      2. Check CODEOWNERS
      3. Review git history for frequent contributors
      4. Suggest appropriate reviewers by expertise area

output:
  format: markdown
  template: .github/pull_request_template.md
  sections:
    summary: ${pr_summary}
    motivation: ${pr_motivation}
    changes: ${categorized_changes}
    testing: ${testing_instructions}
    visuals: ${visual_elements}
    impacts: ${impact_analysis}
    checklist: ${review_checklist}
    metadata: ${pr_metadata}

features:
  - auto_emoji:
      feat: "✨"
      fix: "🐛"
      docs: "📚"
      style: "💎"
      refactor: "♻️"
      perf: "⚡"
      test: "✅"
      chore: "🔧"
      security: "🔒"
      breaking: "💥"

  - smart_detection:
      security_patterns:
        - "auth"
        - "security"
        - "token"
        - "secret"
        - "encryption"
        - "permission"
      performance_patterns:
        - "optimize"
        - "performance"
        - "speed"
        - "cache"
        - "index"
      breaking_patterns:
        - "BREAKING CHANGE"
        - "BREAKING:"
        - "incompatible"
        - "migration required"

  - diagram_generation:
      threshold: 5  # Generate diagrams for 5+ architectural changes
      types:
        - mermaid
        - ascii
      include:
        - dependency_graph
        - component_interaction
        - data_flow

configuration:
  template_path: ".github/pull_request_template.md"
  commit_format: "conventional"  # conventional, angular, custom
  include_stats: true
  include_coverage: true
  auto_assign: false
  draft_by_default: false

  # PR Size Limits
  size_limits:
    github_api:
      max_files: 300
      recommended_files: 100
      max_additions: 10000
      max_deletions: 10000
      max_diff_size_kb: 1024
      recommended_diff_size_kb: 300

    review_tools:
      copilot_max_files: 28
      whatthediff_max_tokens: 2500

    recommendations:
      optimal_lines_changed: 400
      max_lines_changed: 600
      optimal_files_changed: 10
      warning_files_changed: 20

  # PR Splitting Configuration
  splitting:
    enabled: true
    auto_suggest_threshold: 0.8  # 80% of any limit
    strategies:
      - by_module
      - by_change_type
      - by_dependency
      - by_risk
    prefer_strategy: by_module
```

## Example Usage

```bash
# Prepare PR with WhatTheDiff placeholders
/prepare-pr

# Prepare and create draft PR on GitHub
/prepare-pr --create

# Prepare PR without WhatTheDiff placeholders
/prepare-pr --no-wtd

# Prepare PR with custom title and create it
/prepare-pr --title "feat: Add OAuth2 authentication" --create

# Prepare PR with all options
/prepare-pr --type feat --security --create --wtd

# Prepare PR for performance improvements
/prepare-pr --type perf --performance
```

## WhatTheDiff Integration

The command intelligently handles WhatTheDiff placeholders:

### Default Behavior (--wtd enabled)
- Keeps `wtd:summary` placeholder in the summary section
- Optionally adds `wtd:joke` or `wtd:poem` for entertainment
- WhatTheDiff will replace these with AI-generated content after PR creation

### Without WTD (--no-wtd)
- Generates complete content for all sections
- No placeholders left for WhatTheDiff processing
- Useful when you want full control over PR content

### Mixed Mode
- Can use generated content for most sections
- Keep specific WTD placeholders where desired
- Best of both worlds approach

## Example Output

The command generates a complete PR description following the template, with:

1. **Auto-generated summary** from commit messages (or wtd:summary)
2. **Categorized change list** with file counts
3. **Visual diff summary** table
4. **Size analysis and warnings** when approaching limits
5. **PR splitting suggestions** when size exceeds limits
6. **Architecture diagrams** (when applicable)
7. **Code usage examples** extracted from changes
8. **Test coverage delta** with visual indicators
9. **Customized review checklist** based on changes
10. **Suggested reviewers** based on expertise
11. **Impact analysis** for security/performance
12. **Migration guide** (if breaking changes detected)
13. **WhatTheDiff placeholders** (if --wtd enabled)
14. **Direct PR creation** on GitHub (if --create used)

### Example Interaction

```
$ /prepare-pr --create --type feat --security

📝 Analyzing commits...
✅ Found 8 commits to analyze
📊 Calculating metrics...
⚠️  PR size: 35 files (exceeds Copilot limit of 28)

🔍 Generated PR Description:
=====================================
## ✨ feat(auth): Implement OAuth2 authentication system

### 📊 Change Summary
| Metric | Value |
|--------|-------|
| **Files Changed** | 35 (15 added, 18 modified, 2 removed) |
| **Lines of Code** | +892 / -156 |
| **Test Coverage** | 78.5% → 82.3% (+3.8% ✅) |
| **PR Size** | Large ⚠️ |
| **Review Tools** | ❌ Copilot (35/28 files) |

### 🎯 Summary
<!-- wtd:summary -->

[... rest of generated content ...]

🚀 Creating Draft PR on GitHub...
✅ Draft PR created successfully!

📎 PR URL: https://github.com/your-org/repo/pull/150
📋 Status: Draft (ready for your review)
🏷️ Labels applied: enhancement, security, large-pr

✨ Next Steps:
1. Review the generated description
2. WhatTheDiff will process placeholders shortly
3. Make any manual adjustments needed
4. Convert from draft to ready when satisfied

💡 Tip: This PR exceeds Copilot's 28-file limit. Consider:
   - Using our suggested split (shown above)
   - Focusing reviewer attention on critical files
```

### PR Size Analysis Example

```markdown
## ⚠️ PR Size Warning

This PR exceeds recommended size limits for optimal review:

| Metric | Current | Limit | Status |
|--------|---------|-------|--------|
| Files Changed | 45 | 28 (Copilot) | ❌ Exceeds |
| Total Lines | 1,250 | 600 (recommended) | ⚠️ Warning |
| Diff Tokens | 3,100 | 2,500 (WhatTheDiff) | ❌ Exceeds |

### 🔀 Suggested PR Split Plan

Based on the changes, we recommend splitting this PR into 3 smaller PRs:

#### PR 1: Core Configuration Module (Priority: High)
- **Files**: 12 files (250 lines)
- **Focus**: Base configuration classes and validators
- **Branch**: `feature/config-core`
```bash
git checkout -b feature/config-core
git cherry-pick abc123 def456  # commits for core config
```

#### PR 2: Environment-Specific Configs (Priority: Medium)
- **Files**: 15 files (400 lines)
- **Focus**: Dev/staging/prod configurations
- **Branch**: `feature/config-environments`
- **Depends on**: PR 1
```bash
git checkout -b feature/config-environments
git cherry-pick ghi789 jkl012  # commits for environments
```

#### PR 3: Tests and Documentation (Priority: Low)
- **Files**: 18 files (600 lines)
- **Focus**: Unit tests, integration tests, and docs
- **Branch**: `feature/config-tests`
- **Depends on**: PR 1, PR 2
```bash
git checkout -b feature/config-tests
git cherry-pick mno345 pqr678  # commits for tests/docs
```

### Merge Strategy
1. Review and merge PR 1 first (core functionality)
2. Rebase and merge PR 2 (environments)
3. Rebase and merge PR 3 (tests/docs)
```

## Integration with GitHub

The command can be integrated to:
- Auto-create draft PRs
- Update existing PR descriptions
- Add labels based on change types
- Assign suggested reviewers
- Set milestone based on issue references

## Advanced Features

### Commit Analysis
- Extracts conventional commit format
- Groups related commits
- Identifies feature flags
- Detects deprecated code removal

### Smart Categorization
- Groups changes by domain
- Identifies cross-cutting concerns
- Highlights risky changes
- Suggests PR splitting if too large

### Documentation Generation
- Extracts docstring changes
- Identifies API documentation needs
- Suggests README updates
- Creates migration guides

### Quality Checks
- Validates commit message format
- Checks for missing tests
- Identifies TODOs and FIXMEs
- Ensures documentation updates

## Configuration File

Create `.claude-code/prepare-pr.config.json`:

```json
{
  "prepare_pr": {
    "template": ".github/pull_request_template.md",
    "commit_format": "conventional",
    "auto_emojis": true,
    "include_diagrams": true,
    "coverage_threshold": 80,
    "whatthediff": {
      "enabled_by_default": true,
      "placeholders": {
        "summary": true,
        "joke": false,
        "poem": false
      },
      "max_tokens": 2500
    },
    "github": {
      "create_as_draft": true,
      "auto_assign_reviewers": true,
      "auto_apply_labels": true
    },
    "size_limits": {
      "files": {
        "optimal": 10,
        "warning": 20,
        "copilot_max": 28,
        "github_max": 100
      },
      "lines": {
        "optimal": 400,
        "warning": 600,
        "max": 1000
      },
      "tokens": {
        "whatthediff_max": 2500,
        "warning": 2000
      }
    },
    "splitting": {
      "auto_suggest": true,
      "threshold": 0.8,
      "strategies": ["by_module", "by_type", "by_risk"]
    },
    "required_sections": [
      "summary",
      "testing",
      "checklist"
    ],
    "reviewer_mapping": {
      "src/auth/": ["@security-team"],
      "src/api/": ["@backend-team"],
      "src/config/": ["@devops-team"],
      "tests/": ["@qa-team"]
    },
    "label_mapping": {
      "feat": ["enhancement", "feature"],
      "fix": ["bug", "bugfix"],
      "security": ["security", "priority-high"],
      "breaking": ["breaking-change", "major"],
      "perf": ["performance", "optimization"],
      "large-pr": ["needs-split", "complex-review"]
    }
  }
}
```

## Best Practices

1. **Run before creating PR** to ensure quality documentation
2. **Review auto-generated content** and adjust as needed
3. **Keep commits clean** with conventional format
4. **Update after significant changes** to PR
5. **Use flags** to highlight important aspects
6. **Customize template** for your team's needs

## Notes

- Works best with conventional commit format
- Can analyze up to 100 commits efficiently
- Integrates with existing git hooks
- Supports monorepo structures
- Can be combined with `/review-pr` command
