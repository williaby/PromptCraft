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

- Knowledge-base files under `knowledge/**` have their own structure
  (see `.claude/rules/knowledge-base.md`); this rule still applies to
  their prose content.
- Commit messages follow conventional commits (see
  `.claude/rules/git-workflow.md`).

## Deep Reference

Global: `~/.claude/.claude/rules/writing.md` and
`~/.claude/.claude/standards/writing-quality.md`.
