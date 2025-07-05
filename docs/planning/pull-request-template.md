# Pull Request Template

<!--
This template is used by the /prepare-pr slash command.
Sections marked with placeholders ${} will be auto-populated.
WhatTheDiff placeholders (wtd:) can be used for AI-generated content.
-->

## ${pr_emoji} ${pr_title}

### 📊 Change Summary
| Metric | Value |
|--------|-------|
| **Files Changed** | ${files_changed} (${files_added} added, ${files_modified} modified, ${files_removed} removed) |
| **Lines of Code** | +${lines_added} / -${lines_removed} |
| **Test Coverage** | ${coverage_before}% → ${coverage_after}% (${coverage_delta}) |
| **PR Size** | ${pr_size_label} |
| **Review Tools** | ${review_tools_status} |

${pr_size_warnings}

### 🎯 Summary
${pr_summary}

<!-- WhatTheDiff AI Summary (remove if using /prepare-pr) -->
<!-- wtd:summary -->

<!-- This section is auto-generated from commit messages and PR analysis -->

### 💡 Motivation
${pr_motivation}

<!-- Why is this change needed? What problem does it solve? -->

### 🔄 Changes Made

#### ✨ Added
${changes_added}

#### 📝 Modified
${changes_modified}

#### 🗑️ Removed
${changes_removed}

### 🔀 PR Splitting Suggestions
${pr_splitting_suggestions}

<!-- This section appears only when PR exceeds size limits -->

### 🏗️ Architecture Overview
${architecture_diagram}

<!-- Mermaid diagram or ASCII art showing component relationships if significant architectural changes -->

### 💻 Usage Example
```${primary_language}
${usage_example}
```

<!-- Key code example showing how to use the new/modified functionality -->

### 🧪 Testing

#### Test Coverage
${test_coverage_report}

#### How to Test
${testing_instructions}

1. **Unit Tests**
   ```bash
   ${unit_test_command}
   ```

2. **Integration Tests**
   ```bash
   ${integration_test_command}
   ```

3. **Manual Testing Steps**
   ${manual_test_steps}

### 📸 Screenshots/Output
${screenshots_section}

<!-- Add screenshots, command output, or UI changes if applicable -->

### ⚡ Performance Impact
${performance_section}

- **Startup Time**: ${startup_impact}
- **Memory Usage**: ${memory_impact}
- **Runtime Performance**: ${runtime_impact}
- **Database Queries**: ${db_impact}

### 🔒 Security Considerations
${security_section}

- **Authentication**: ${auth_changes}
- **Authorization**: ${authz_changes}
- **Data Protection**: ${data_protection}
- **Vulnerabilities Addressed**: ${vulnerabilities}

### 💥 Breaking Changes
${breaking_changes_section}

<!-- List any breaking changes and migration steps -->

### 📋 Migration Guide
${migration_guide}

<!-- Step-by-step migration instructions if breaking changes exist -->

### ✅ PR Checklist

#### Code Quality
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No debugging code left

#### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Test coverage maintained or improved

#### Documentation
- [ ] Code comments updated
- [ ] README updated (if needed)
- [ ] API documentation updated (if needed)
- [ ] Changelog updated

#### Security
- [ ] No secrets/credentials in code
- [ ] Security best practices followed
- [ ] Dependencies scanned for vulnerabilities
- [ ] Input validation implemented

#### Review
- [ ] PR is focused and single-purpose
- [ ] Commits are clean and well-described
- [ ] No unrelated changes included
- [ ] Ready for review

### 🔗 Related Issues
${related_issues}

<!-- GitHub will auto-close issues with these keywords: -->
Closes: #
Fixes: #
Resolves: #
Related to: #

### 🏷️ Metadata

**Type**: `${change_type}`
**Priority**: `${priority}`
**Risk Level**: `${risk_level}`
**Estimated Review Time**: `${review_time}`

### 👥 Suggested Reviewers
${suggested_reviewers}

<!-- Based on code ownership and expertise areas -->

### 📝 Notes for Reviewers
${reviewer_notes}

<!-- Specific areas to focus on or context needed for review -->

### 🎭 For Your Entertainment
<!-- Optional: Add a developer joke or poem about this PR -->
<!-- wtd:joke -->
<!-- wtd:poem -->

### 🚀 Next Steps
${next_steps}

<!-- What happens after this PR is merged? -->

---

### 🤖 Generated Information
- **Generated with**: `/prepare-pr` command
- **Timestamp**: ${generation_timestamp}
- **Commit Range**: ${commit_range}
- **Base Branch**: `${base_branch}`
- **Target Branch**: `${target_branch}`

<!--
Co-Authored-By: ${co_authors}
-->

### 📊 Detailed Statistics
<details>
<summary>Click to expand detailed changes</summary>

${detailed_statistics}

</details>

### 🔍 File Changes
<details>
<summary>Click to view all changed files</summary>

${file_tree}

</details>
