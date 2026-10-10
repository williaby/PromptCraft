# Project-Scoped Rules

Operational rules that apply while Claude Code edits this project. They layer on top of the global standards at
`~/.claude/CLAUDE.md`. Where a rule here conflicts with global, project wins.

Each rule file states its **scope** at the top, stays lean, and points to the deeper source of truth.

## Rule Files

| File | Scope |
| --- | --- |
| `python.md` | `src/**/*.py`, `tests/**/*.py` |
| `testing.md` | `tests/**` |
| `git-workflow.md` | Any git operation in this repo |
| `pre-commit.md` | Before every commit |
| `writing.md` | All text output (docs, commits, comments) |
