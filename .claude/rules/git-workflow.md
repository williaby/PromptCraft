# Git Workflow Rule

**Scope:** Any git operation in this repository.

## Commits

- Commits **must be signed** (`git config user.signingkey` must be set).
- Use **conventional commit** prefixes: `feat`, `fix`, `docs`, `test`,
  `chore`, `style`, `refactor`, `security`, `build`, `ci`.
- Never use `--no-verify`, `--no-gpg-sign`, or `-c commit.gpgsign=false`
  unless the user has explicitly asked for it. If a hook fails, fix the
  underlying issue rather than bypassing.
- Prefer new commits over `--amend` after a pre-commit hook failure; the
  failed commit never happened, so `--amend` would modify the prior one.

## Branches

- **Branch prefixes:** `feature/`, `fix/`, `hotfix/`, `release/`, `docs/`,
  `refactor/`.
- **Main branch:** `main`.
- Branch names are `kebab-case` after the prefix slash.

## Worktrees

- Worktrees live at `.worktrees/<branch-slug>` inside this project.
- Never create worktrees at `~/.config/...`, `~/.claude/...`, or any
  global-scope path.

## Deep References

- `docs/standards/git-workflow.md` - full branch lifecycle and examples.
- Global: `~/.claude/.claude/rules/git-workflow.md`.
