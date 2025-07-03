---
title: PromptCraft Pro Knowledge File Style Guide
version: 1.2
status: published
component: Tone-Format
tags: ["style-guide", "markdown", "knowledge-files"]
source: "PromptCraft Pro Project"
purpose: Provides the official style, formatting, and structural guidelines for all
  Markdown-based knowledge files within the PromptCraft Pro project.
---

## PromptCraft Pro Knowledge File Style Guide

<!-- toc -->
<!-- tocstop -->

## Overview

**Version:** 1.2
**Audience:** Content teams, technical writers, and developer-doc contributors.

This guide establishes the canonical rules for every Markdown knowledge file in **PromptCraft Pro**.
Follow it to guarantee:

* **Machine-readability** - Documents must be flawlessly parsed by our remark/TOC tool-chain
  and RAG ingestion pipeline.
* **Human clarity** - Raw Markdown should be as legible as the rendered HTML.
* **Maintainability** - A predictable structure lowers error rates and eases long-term scaling.

---

## 1. Guiding Principles

1. **Machine-Readability** - Structure is not decoration; it drives automation.
2. **Human-Clarity** - Optimize for plain-text comprehension.
3. **Maintainability** - Consistency simplifies reviews and future edits.

---

## 2. File & Naming Conventions

All knowledge files live in the `/knowledge/` directory.
Filenames are lowercase, use hyphens, and describe the content succinctly.

### Do

```text
01-context-blocks.md
11-python-guide.md
```

### Don't

```text
01_ContextBlocks.md
Python.md
```

---

## 3. Document Structure & Metadata

### 3.1 YAML Front Matter

Every file starts with a YAML block that drives RAG filtering.

Mandatory keys:

| Key       | Description                                                                                     |
|-----------|-------------------------------------------------------------------------------------------------|
| `title`   | Human-readable document name.                                                                   |
| `version` | Semantic version (e.g. `1.2`).                                                                  |
| `status`  | One of `draft`, `in-review`, `published`.                                                       |
| `component` | One of `Context`, `Request`, `Examples`, `Augmentations`, `Tone-Format`, `Evaluation`.        |
| `tags`    | Array of keywords - `["persona","role","swot"]`.                                                |
| `source`  | Originating document if applicable.                                                             |
| `purpose` | One-sentence statement of intent.                                                               |

Example:

```yaml
---
title: Quick-Reference
version: 2.1
status: published
component: Evaluation
tags: ["eblock", "qa", "rigor"]
source: "AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework v1 (May 2025)"
purpose: Provides essential quick-reference materials from the C.R.E.A.T.E. Framework.
---
```

### 3.2 Table of Contents

Insert the comment pair immediately after the H1:

```markdown
<!-- toc -->
<!-- tocstop -->
```

The `remark-toc` plugin populates the list automatically.

---

## 4. Headings

| Level | Purpose                               | Rule                                     |
|-------|---------------------------------------|------------------------------------------|
| `#`   | **Document title** - only one per file | **Required** - placed before front-matter TOC comments |
| `##`  | Major sections                        | Use plural nouns where possible          |
| `###` | Atomic knowledge chunks               | Strive for fine-grained, self-contained topics |
| `####` & below | **Prohibited**                    | Depth >3 breaks RAG precision            |

---

## 5. Content Identifiers & Linking

### 5.1 Heading Slugs

The legacy `ANCHOR-XX-#` system is **deprecated**.
`remark-slug` auto-generates unique IDs from heading text.

*Old (deprecated)* `### ANCHOR-QR-2`
*New* `### Depth and Length Tiers`

### 5.2 Link Syntax

* **Intra-file** - `See the [Depth and Length Tiers](#depth-and-length-tiers).`
* **Inter-file** - `See [Context Blocks](./01-context-blocks.md#defining-the-role-and-persona-clause).`

---

## 6. Content Formatting

*Paragraphs* - Separate with one blank line.
*Emphasis* - `**bold**` for critical terms; `*italics*` for new or referenced items.
*Lists* - Hyphens for unordered, `1.` for ordered.
*Tables* - GitHub-flavoured, include header row.
*Code* - Fenced blocks with language identifier.
*Horizontal rules* - three asterisks `***`.

---

## 7. Callout Blocks & Directives

Use typed block-quotes for all non-prose directives.

Syntax:

```markdown
> **TYPE:** Content
```

Defined types:

> **AGENT-DIRECTIVE:** Instruction the PromptCraft Pro agent must obey.
> **VERBATIM-INJECTION:** Next code block must be copied exactly.
> **HUMAN-NOTE:** Information for human readers, ignored by the agent.
> **EXAMPLE:** Illustrative sample content.
> **RELATED:** Cross-reference to another knowledge chunk.

### Example

> **AGENT-DIRECTIVE:** Insert this directive into the A-block of the generated prompt.

---

## 8. Tone & Voice

* Professional, instructive, approachable.
* Prefer clarity over brevity.
* Use active voice and direct address ("you").
* Avoid contractions.
* Replace em-dashes with colons or parentheses.

---

## 9. Tooling & Automation

### 9.1 Remark

`.remarkrc.yaml` configures:

* `remark-frontmatter` - YAML parsing
* `remark-slug` - heading IDs
* `remark-toc` - TOC generation

### 9.2 Markdown Linting

Enforce this guide with **markdownlint** using project-root `.markdownlint.json`.

---

## 10. Content Templates

### Template - New Knowledge File

```yaml
---
title: [File Title]
version: 1.0
status: draft
component: [Context|Request|Examples|Augmentations|Tone-Format|Evaluation]
tags: ["tag1", "tag2"]
source: [Source Document, if any]
purpose: [One-sentence purpose.]
---
```

```markdown
# [File Title]

<!-- toc -->
<!-- tocstop -->

## [First Major Section]

### [First Atomic Knowledge Chunk]

[Content here...]

> **RELATED:** See...
```

---

> **HUMAN-NOTE:** End of style guide.
