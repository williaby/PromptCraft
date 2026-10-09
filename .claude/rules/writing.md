# Writing Rule

**Scope:** All text output: docs, commits, ADRs, code comments, PR
descriptions, CHANGELOG, rule files, standards.

## Hard Rules

- **No em-dashes** anywhere. Replace with a comma, semicolon, colon, or
  restructured sentence. Pre-commit does not yet enforce this
  automatically; apply manually on every write.
- **No AI-signature phrasing.** Avoid "delve," "it's worth noting,"
  "in today's fast-paced world," "leveraging synergies," and similar
  filler.
- **Imperative voice** for standards and rule files; narrative voice
  only where context genuinely requires it.

## Project Specifics

- Spec files and legacy source material under `knowledge/**` follow
  this rule for any prose that is added or edited.
- Commit messages follow conventional commits (see
  `.claude/rules/git-workflow.md`).

## Deep Reference

Global: `~/.claude/.claude/rules/writing.md` and
`~/.claude/.claude/standards/writing-quality.md`.
