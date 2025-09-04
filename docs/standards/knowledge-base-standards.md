# Knowledge Base Standards

> **Comprehensive standards for creating and maintaining knowledge files in the PromptCraft system**

## File Structure Requirements

### Directory Convention
```text
/knowledge/{agent_id}/{kebab-case-filename}.md
```

### YAML Front Matter (MANDATORY)

Every knowledge file MUST include properly formatted front matter:

```yaml
---
title: [Human-readable title]
version: [X.Y or X.Y.Z]
status: [draft|in-review|published]
agent_id: [snake_case - MUST match folder name]
tags: ['lowercase', 'underscore_separated']
purpose: [Single sentence ending with period]
---
```

## Content Structure Standards

### Heading Hierarchy (STRICTLY ENFORCED)

- **H1 (#)**: Document title only (MUST match title in front matter)
- **H2 (##)**: Major sections
- **H3 (###)**: Atomic knowledge chunks (self-contained units)
- **H4 and below**: STRICTLY PROHIBITED (breaks RAG chunking)

### Content Rules

1. **Atomicity**: Each H3 section MUST be completely self-contained
2. **Machine Readability**: Documents must be flawlessly parsed by remark/TOC tools and RAG pipeline
3. **Human Clarity**: Raw Markdown should be as legible as rendered HTML
4. **Complex Content**: Tables, diagrams, code MUST be preceded by descriptive prose
5. **Agent Directives**: Use format `> **AGENT-DIRECTIVE:** instruction here`

## C.R.E.A.T.E. Framework Integration

Knowledge files should follow the C.R.E.A.T.E. Framework structure:

### Framework Components

- **C - Context**: Role, persona, background, goals
- **R - Request**: Core task, deliverable specifications
- **E - Examples**: Few-shot examples and demonstrations
- **A - Augmentations**: Frameworks, evidence, reasoning prompts
- **T - Tone & Format**: Voice, style, structural formatting
- **E - Evaluation**: Quality checks and verification

### Implementation Pattern

```markdown
## Context Section
> **AGENT-DIRECTIVE:** Establish clear context for this knowledge domain

### Role Definition
[Self-contained description of agent role and responsibilities]

### Background Knowledge
[Essential domain knowledge for effective agent operation]

## Request Specifications
> **AGENT-DIRECTIVE:** Define precise task requirements and deliverables

### Core Tasks
[Specific tasks this knowledge enables]

### Quality Criteria
[How to evaluate successful completion]

## Examples and Demonstrations
> **AGENT-DIRECTIVE:** Use these examples as patterns for similar tasks

### Example 1: [Scenario Name]
[Complete example with context, input, and expected output]

### Example 2: [Scenario Name]
[Another complete example showing variation]

## Augmentations and Frameworks
> **AGENT-DIRECTIVE:** Apply these frameworks when performing tasks

### Framework 1: [Name]
[Framework description and application guidance]

## Tone and Format Guidelines
> **AGENT-DIRECTIVE:** Maintain consistency in communication style

### Communication Style
[Specific guidance on tone, formality, technical depth]

### Output Formatting
[Structured format requirements for agent outputs]

## Evaluation Criteria
> **AGENT-DIRECTIVE:** Validate outputs against these quality standards

### Success Metrics
[Measurable criteria for successful task completion]

### Quality Checkpoints
[Validation steps to ensure output quality]
```

## File Lifecycle Management

### Status Progression

1. **draft**: Initial creation, work in progress
2. **in-review**: Ready for peer review and validation
3. **published**: Approved for RAG ingestion and production use

### Important Notes

- Only `status: published` files are ingested by RAG pipeline
- Files in `draft` or `in-review` status are visible but not searchable
- Version increments required for significant content changes

## Naming Conventions (MANDATORY)

### Component Naming

- **Agent ID**: snake_case (e.g., `security_agent`, `create_agent`)
- **Knowledge Folders**: snake_case matching agent_id (e.g., `/knowledge/security_agent/`)
- **Knowledge Files**: kebab-case.md (e.g., `auth-best-practices.md`)

### Consistency Requirements

- Agent ID in front matter MUST match folder name exactly
- File names should be descriptive and use kebab-case
- Avoid abbreviations unless they're domain-standard (e.g., `api`, `sql`, `jwt`)

## Validation Requirements

### Automated Validation

All knowledge files are automatically validated for:

- Correct YAML front matter syntax and required fields
- Proper heading hierarchy (no H4+ headings)
- File location matches agent_id in front matter
- Naming conventions compliance
- Internal link validity

### Manual Review Checklist

Before marking status as `published`:

- [ ] Content is accurate and complete
- [ ] Each H3 section is self-contained
- [ ] Agent directives are clear and actionable
- [ ] Examples are complete and demonstrate key concepts
- [ ] No broken internal references
- [ ] Follows C.R.E.A.T.E. Framework structure
- [ ] Tags are appropriate and lowercase/underscore format

## Integration with RAG System

### Chunking Strategy

- Each H3 section becomes an independent RAG chunk
- Chunks include relevant context from H2 section headers
- Front matter metadata used for filtering and routing
- Agent directives preserved in chunk metadata

### Search Optimization

- Use descriptive H3 headings that include key search terms
- Include synonyms and alternative terminology in content
- Front matter tags enable category-based filtering
- Purpose field provides concise chunk summaries

## Common Patterns and Templates

### Security Knowledge Template

```markdown
---
title: Security Best Practices for [Domain]
version: 1.0
status: draft
agent_id: security_agent
tags: ['security', 'best_practices', 'domain_specific']
purpose: Provides comprehensive security guidelines for [specific domain].
---

# Security Best Practices for [Domain]

## Threat Assessment
> **AGENT-DIRECTIVE:** Always begin security analysis with threat modeling

### Common Threats
[Self-contained list of domain-specific threats]

### Risk Evaluation Framework
[Complete framework for assessing security risks]

## Implementation Guidelines
> **AGENT-DIRECTIVE:** Follow these patterns for secure implementation

### Secure Configuration
[Step-by-step security hardening procedures]

### Validation Requirements
[Security testing and validation criteria]
```

### Technical Integration Template

```markdown
---
title: [Technology] Integration Guide
version: 1.0
status: draft
agent_id: integration_agent
tags: ['integration', 'technology_name', 'implementation']
purpose: Complete guide for integrating [technology] into PromptCraft system.
---

# [Technology] Integration Guide

## Prerequisites and Setup
> **AGENT-DIRECTIVE:** Verify all prerequisites before beginning integration

### Environment Requirements
[Complete environment setup requirements]

### Authentication Configuration
[Authentication and security setup procedures]

## Integration Implementation
> **AGENT-DIRECTIVE:** Follow this sequence for reliable integration

### Step-by-Step Procedure
[Detailed implementation steps with validation points]

### Configuration Templates
[Complete configuration examples and templates]

## Testing and Validation
> **AGENT-DIRECTIVE:** Execute all validation steps to ensure integration quality

### Integration Tests
[Specific tests to validate integration functionality]

### Performance Benchmarks
[Performance criteria and measurement procedures]
```

## Migration and Maintenance

### Legacy File Updates

When updating existing knowledge files:

1. Increment version number
2. Update status to `draft` during modifications
3. Preserve working examples and agent directives
4. Test changes against RAG system before publishing
5. Update cross-references in related files

### Deprecation Process

For outdated knowledge files:

1. Update status to `deprecated` (not searchable)
2. Add deprecation notice at top of file
3. Reference replacement files where applicable
4. Maintain for 6 months before archival
5. Archive to `/knowledge/archived/` directory
