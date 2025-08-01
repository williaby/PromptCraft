# Standardize Planning Doc

Standardize docs/planning/*.md files with proper front matter, linting compliance, and development requirements: $ARGUMENTS

## Analysis Required

1. **File Type Detection**: Determine if this is an architecture document, runbook, technical spec, or general planning document
2. **Current State Assessment**: Check existing front matter, heading structure, and compliance issues
3. **Front Matter Creation**: Generate proper YAML front matter based on file type and content
4. **Content Structure**: Ensure proper heading hierarchy (H1-H3 only)
5. **Linting Compliance**: Fix all markdownlint and yamllint issues
6. **Link Validation**: Check and fix internal repository links
7. **Development Standards**: Ensure alignment with docs/planning/development.md requirements

## Front Matter Standards by Document Type

### Architecture Documents (ADR, technical specs)

```yaml
---
title: [Document Title]
version: [X.Y]
status: [draft|in-review|published]
component: Architecture
tags: ["architecture", "technical-spec", "relevant-tech"]
source: "PromptCraft-Hybrid Project"
purpose: [Single sentence describing architectural decision or specification.]
---
```

### Planning Documents (project plans, timelines, runbooks)

```yaml
---
title: [Document Title]
version: [X.Y]
status: [draft|in-review|published]
component: Planning
tags: ["planning", "process", "relevant-area"]
source: "PromptCraft-Hybrid Project"
purpose: [Single sentence describing planning objective.]
---
```

### Process Documents (contributing, setup guides)

```yaml
---
title: [Document Title]
version: [X.Y]
status: [draft|in-review|published]
component: Process
tags: ["process", "documentation", "workflow"]
source: "PromptCraft-Hybrid Project"
purpose: [Single sentence describing process or workflow.]
---
```

## Validation Rules

### Heading Structure

- **H1 (`#`)**: Document title only - must match front matter title
- **H2 (`##`)**: Major sections
- **H3 (`###`)**: Subsections and detailed topics
- **H4+ prohibited**: Breaks document consistency

### Content Standards

- Line length: Max 120 characters
- Proper list formatting with consistent indentation
- Table formatting with proper alignment
- Code blocks with language identifiers
- Consistent spacing around headings and sections

### Link Standards

- Internal links: Use relative paths from repository root
- External links: Use full URLs with https://
- Reference links: Use descriptive text, not "click here"

## Required Output

Provide the corrected file content with:

1. **Proper YAML front matter** with all required fields
2. **Fixed heading structure** following H1-H3 hierarchy
3. **Resolved linting issues** for both markdown and YAML
4. **Corrected internal links** with valid repository paths
5. **Consistent formatting** following project style guide
6. **Summary of changes** made during standardization

## Important Notes

- Reference CLAUDE.md development standards throughout
- Maintain original content meaning while improving structure
- Use docs/planning/exec.md as the reference standard for format
- Ensure front matter component field matches document purpose
- All planning documents should reference related documents appropriately
- Follow conventional commits format for any suggested Git workflow changes
