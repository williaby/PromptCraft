# Create Knowledge File

Create a new knowledge base file following PromptCraft-Hybrid standards for: $ARGUMENTS

## Instructions

Create a new knowledge file with the following requirements:

### 1. Determine File Location and Naming
- **Location**: `/knowledge/{agent_id}/{kebab-case-filename}.md`
- **Agent ID**: Use snake_case (e.g., `security_agent`, `create_agent`)
- **Filename**: Use kebab-case (e.g., `auth-best-practices.md`)
- **Ensure agent_id consistency** across folder name and metadata

### 2. Create Proper YAML Front Matter
```yaml
---
title: [Descriptive title matching H1]
version: 1.0
status: draft
agent_id: [snake_case matching folder name]
tags: ['relevant', 'lowercase', 'underscore_separated']
purpose: [Single sentence describing the document's goal ending with period]
---
```

### 3. Follow Heading Structure (MANDATORY)
```markdown
# [Title - Must Match YAML Title]

## [Major Topic Area]

### [Atomic Knowledge Chunk 1]

> **AGENT-DIRECTIVE:** [Optional instruction for AI agent when using this chunk]

Complete, self-contained explanation of this specific concept. This H3 section must make sense without context from other sections since it may be retrieved independently by the RAG system.

### [Atomic Knowledge Chunk 2]

Another self-contained knowledge chunk. Include examples, best practices, or implementation details as appropriate.

## [Second Major Topic Area]

### [Specific Implementation Pattern]

> **EXAMPLE:** The following demonstrates the recommended approach.

Detailed explanation with code examples or step-by-step instructions.
```

### 4. Content Requirements

**Critical Rules**:
- Each H3 section MUST be completely self-contained
- NO H4 or deeper headings (breaks RAG chunking)
- Complex content (tables, code blocks) MUST be preceded by descriptive prose
- Use agent directives: `> **AGENT-DIRECTIVE:** instruction`
- Ensure content follows C.R.E.A.T.E. Framework where applicable

**Content Guidelines**:
- Write for both human readers and AI retrieval
- Include practical examples and implementation details
- Reference other knowledge files with full paths: `/knowledge/agent_id/filename.md`
- Keep line length under 120 characters

### 5. Lifecycle Management
- Start with `status: draft`
- Move to `status: in-review` when ready for review
- Change to `status: published` after approval (only published files are ingested)

## Output

Provide the complete file content ready to be saved at the appropriate location, including:
1. Proper YAML front matter
2. Correctly structured headings
3. Self-contained content sections
4. Appropriate agent directives
5. Examples and implementation details

Ensure the file follows ALL project standards defined in CLAUDE.md and the knowledge base style guide.
