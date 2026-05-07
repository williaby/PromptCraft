# Project-Scoped Rules

Operational rules that apply while Claude Code is editing files in this
project. These layer on top of the global standards at `~/.claude/CLAUDE.md`
and the global rules under `~/.claude/.claude/rules/`. Where a rule here
conflicts with global, project wins.

Each rule file should:

- State its **scope** at the top (which paths it applies to).
- Stay lean: the rule itself, followed by a pointer to the deep specification
  under `docs/standards/` or the global docs.
- Not duplicate global rules verbatim; only document overrides or additions.

## Rule Files

| File | Scope |
| --- | --- |
| `python.md` | `src/**/*.py`, `tests/**/*.py` |
| `testing.md` | `tests/**` |
| `knowledge-base.md` | `knowledge/**` |
| `git-workflow.md` | Any git operation in this repo |
| `pre-commit.md` | Before every commit |
| `writing.md` | All text output (docs, commits, comments) |

If you add a rule that only applies to a subtree, place it at
`src/<area>/CLAUDE.md` instead; this directory is for rules that cross
subtrees but still need project-specific overrides.
