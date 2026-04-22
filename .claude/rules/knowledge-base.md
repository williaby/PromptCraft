# Knowledge Base Rule

**Scope:** `knowledge/**`

## File Location

```text
knowledge/{agent_id}/{kebab-case-filename}.md
```

`agent_id` must match the subfolder name and must be `snake_case`.

## Required YAML Front Matter

```yaml
---
title: [Human-readable title]
version: [X.Y or X.Y.Z]
status: [draft|in-review|published]
agent_id: [snake_case, must match folder]
tags: ['lowercase', 'underscore_separated']
purpose: [Single sentence ending with period.]
---
```

## Content Rules

- Each H3 section must be **completely self-contained**. RAG chunking splits
  at H3, so a section that references prior context will chunk incorrectly.
- **No H4 or deeper headings.** Flatten or split into multiple H3 sections.
- Only files with `status: published` are ingested by the RAG pipeline.
  Drafts stay local.

## Deep Reference

`docs/standards/knowledge-base-standards.md` has the full specification,
including style guidance and validation rules.
