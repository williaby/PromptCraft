---
category: workflow
complexity: medium
estimated_time: "5-15 minutes"
dependencies: []
version: "1.0"
---

# Workflow Git Helpers

Git workflow validation and helpers: $ARGUMENTS

## Instructions

Provide git workflow assistance based on the command or validation requested:

### Branch Name Validation

```bash
# Check current branch name follows conventions
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Valid patterns:
# - feature/<issue-number>-<short-name>
# - fix/<issue-number>-<short-name>  
# - hotfix/<issue-number>-<short-name>
# - chore/<issue-number>-<short-name>

if [[ $current_branch =~ ^(feature|fix|hotfix|chore)/[0-9]+-[a-z0-9-]+$ ]]; then
    echo "✅ Branch name follows conventions"
else
    echo "❌ Branch name should follow: type/<issue-number>-<short-name>"
    echo "Examples: feature/123-add-user-auth, fix/456-memory-leak"
fi
```

### Commit Message Validation

```bash
# Check last commit message follows Conventional Commits
last_commit=$(git log -1 --pretty=format:"%s")
echo "Last commit: $last_commit"

# Valid patterns: type(scope): description
# Types: feat, fix, docs, style, refactor, test, chore, ci, perf
if [[ $last_commit =~ ^(feat|fix|docs|style|refactor|test|chore|ci|perf)(\(.+\))?: .+ ]]; then
    echo "✅ Commit message follows Conventional Commits"
else
    echo "❌ Commit should follow: type(scope): description"
    echo "Examples: feat(auth): add user login, fix(api): resolve timeout issue"
fi
```

### Pre-Commit Validation

```bash
# Run pre-commit checks before committing
echo "Running pre-commit validation..."

# Check for staged changes
if ! git diff --cached --quiet; then
    echo "✅ Staged changes found"
    
    # Security check - no secrets in staged files
    if git diff --cached | grep -i -E "(password|secret|key|token|api_key)" | grep "^\+"; then
        echo "❌ Potential secrets found in staged changes!"
        echo "Review staged changes for sensitive information"
        git diff --cached | grep -i -E "(password|secret|key|token|api_key)" | grep "^\+"
    else
        echo "✅ No obvious secrets in staged changes"
    fi
    
    # Check file sizes
    large_files=$(git diff --cached --name-only | xargs ls -la 2>/dev/null | awk '$5 > 1048576 {print $9, $5}')
    if [ -n "$large_files" ]; then
        echo "⚠️  Large files detected (>1MB):"
        echo "$large_files"
    fi
    
else
    echo "❌ No staged changes to commit"
fi
```

### PR Readiness Check

```bash
# Check if branch is ready for pull request
echo "Checking PR readiness..."

# Check if ahead of main/master
main_branch=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
commits_ahead=$(git rev-list --count HEAD ^origin/$main_branch 2>/dev/null || echo "0")
commits_behind=$(git rev-list --count origin/$main_branch ^HEAD 2>/dev/null || echo "0")

echo "Commits ahead of $main_branch: $commits_ahead"
echo "Commits behind $main_branch: $commits_behind"

if [ "$commits_ahead" -gt 0 ]; then
    echo "✅ Branch has commits to merge"
    
    # Check PR size (line changes)
    changes=$(git diff --shortstat origin/$main_branch...HEAD 2>/dev/null | awk '{print $4+$6}')
    if [ -n "$changes" ] && [ "$changes" -gt 400 ]; then
        echo "⚠️  Large PR: $changes lines changed (consider splitting)"
    else
        echo "✅ PR size acceptable: ${changes:-0} lines changed"
    fi
    
    # Check for merge conflicts
    if git merge-tree $(git merge-base HEAD origin/$main_branch) HEAD origin/$main_branch | grep -q "^<<<<<"; then
        echo "❌ Merge conflicts detected with $main_branch"
    else
        echo "✅ No merge conflicts with $main_branch"
    fi
    
else
    echo "❌ No new commits to merge"
fi
```

### Git Status Summary

```bash
# Provide comprehensive git status
echo "=== Git Status Summary ==="
git status --porcelain=v1 | awk '
/^M / {modified++}
/^A / {added++} 
/^D / {deleted++}
/^R / {renamed++}
/^\?\?/ {untracked++}
END {
    if (modified) print "Modified files: " modified
    if (added) print "Added files: " added
    if (deleted) print "Deleted files: " deleted  
    if (renamed) print "Renamed files: " renamed
    if (untracked) print "Untracked files: " untracked
    if (!modified && !added && !deleted && !renamed && !untracked) print "Working tree clean"
}'
```

## Workflow Commands

**Create Feature Branch**:

```bash
git checkout -b feature/<issue-number>-<short-description>
```

**Commit with Conventional Format**:

```bash
git commit -m "type(scope): description"
```

**Update Branch with Latest Main**:

```bash
git fetch origin
git rebase origin/main
```

**Push Feature Branch**:

```bash
git push -u origin feature/<issue-number>-<short-description>
```

## Workflow Best Practices

- Keep branches focused on single features/fixes
- Use descriptive branch names with issue numbers
- Write clear, conventional commit messages
- Keep PRs under 400 lines when possible
- Rebase instead of merge to maintain clean history
- Sign all commits for security
- Never commit secrets or sensitive data
