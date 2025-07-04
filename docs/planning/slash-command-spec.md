---
title: Claude Code Slash Commands Specification
version: 2.0
status: published
component: Development-Tools
tags: ["slash-command", "claude-code", "documentation", "automation", "prompt-templates"]
source: "PromptCraft-Hybrid Project"
purpose: Defines standards and catalog for Claude Code slash commands in PromptCraft-Hybrid project.
---

# Claude Code Slash Commands Specification

## Overview

This document defines the standards for creating Claude Code slash commands in PromptCraft-Hybrid and catalogs all available commands. Claude Code slash commands are **prompt templates** stored as Markdown files in `.claude/commands/`, not executable scripts.

## Claude Code Slash Command Architecture

### How Claude Code Slash Commands Work

Claude Code slash commands are **prompt templates** that:
- Are stored as `.md` files in `.claude/commands/` directory
- Become available when typing `/` in Claude Code
- Use `$ARGUMENTS` placeholder for dynamic input
- Are invoked as `/project:command-name arguments`

### Command Structure

```markdown
# Command Title

Brief description of what this command does: $ARGUMENTS

## Instructions

1. Detailed step-by-step instructions
2. Specific validation rules or requirements
3. Expected behavior and output format

## Required Output

Specific format requirements for Claude's response.
```

## Development Standards for Slash Commands

### 1. Command Organization

**Directory Structure**:
```
.claude/commands/
├── lint-doc.md
├── create-knowledge-file.md
├── fix-links.md
├── validate-frontmatter.md
├── list-commands.md
└── [future-commands].md
```

**Flat Structure Benefits**:
- Simpler organization and navigation
- Easier command discovery
- Reduced complexity for team members
- Cleaner repository structure

### 2. Command Naming Standards

- **File naming**: kebab-case.md (e.g., `lint-doc.md`, `create-knowledge-file.md`)
- **Command invocation**: `/project:command-name arguments`
- **Flat organization**: All commands stored directly in `.claude/commands/`
- **Use verb-noun format**: `lint-doc`, `create-knowledge-file`, `fix-links`

### 3. Command Template Structure

```markdown
# Command Title

Brief description of command purpose: $ARGUMENTS

## Analysis Required / Instructions

1. Specific analysis steps
2. Validation rules to apply
3. Standards to check against

## Required Output

Exact format specification for Claude's response

## Important Notes

- Critical requirements
- Project-specific considerations
- Reference to CLAUDE.md standards
```

### 4. Command Content Standards

**Required Elements**:
- Clear command description with `$ARGUMENTS` placeholder
- Detailed instructions for Claude to follow
- Specific output format requirements
- Reference to project standards (CLAUDE.md, style guides)

**Best Practices**:
- Be specific about validation rules
- Provide exact format specifications
- Include error handling instructions
- Reference project-specific requirements
- Use consistent terminology across commands

## Available Slash Commands Catalog

### Core Documentation Commands

#### `/project:lint-doc`
**Purpose**: Comprehensive document compliance checking
**Usage**: `/project:lint-doc docs/planning/exec.md`
**Features**:
- File type detection (knowledge/planning/general)
- YAML front matter validation
- Heading structure compliance
- Link validation with TODO generation
- Compliance scoring and detailed reporting

#### `/project:create-knowledge-file`
**Purpose**: Create new knowledge base files with proper structure
**Usage**: `/project:create-knowledge-file security authentication best practices`
**Features**:
- Generates proper YAML front matter
- Creates atomic H3 knowledge chunks
- Ensures agent ID consistency
- Follows C.R.E.A.T.E. framework

#### `/project:fix-links`
**Purpose**: Analyze and fix broken internal links
**Usage**: `/project:fix-links docs/planning/exec.md`
**Features**:
- Identifies broken internal repository links
- Provides fuzzy-matched suggestions
- Generates corrected file content
- Handles relative and absolute paths

#### `/project:validate-frontmatter`
**Purpose**: Validate and fix YAML front matter
**Usage**: `/project:validate-frontmatter knowledge/security_agent/auth-guide.md`
**Features**:
- File-type specific validation rules
- Title/heading consistency checking
- Agent ID consistency for knowledge files
- Tag format validation

### Planning & Architecture Commands

#### `/project:standardize-planning-doc`
**Purpose**: Standardize planning documents with proper front matter and compliance
**Usage**: `/project:standardize-planning-doc docs/planning/PC_Setup.md`
**Features**:
- Document type detection and appropriate front matter generation
- Linting compliance fixes (markdownlint/yamllint)
- Heading structure standardization
- Development guidelines alignment

#### `/project:create-planning-doc`
**Purpose**: Create new planning documents with proper structure
**Usage**: `/project:create-planning-doc "API Gateway Strategy" architecture`
**Features**:
- Template-based document generation (ADR, runbook, process, planning)
- Proper front matter with type-specific metadata
- Cross-reference integration with related documents
- Stakeholder and approval workflow integration

### Agent Development Commands

#### `/project:create-agent-skeleton`
**Purpose**: Create complete agent directory structure and base files
**Usage**: `/project:create-agent-skeleton tax_preparation_agent "Tax form preparation and compliance"`
**Features**:
- Complete directory structure creation
- Knowledge base template files
- Python class skeleton with proper inheritance
- Registry integration and Qdrant configuration
- Test file generation

#### `/project:validate-agent-structure`
**Purpose**: Comprehensive validation of agent directory structure and consistency
**Usage**: `/project:validate-agent-structure knowledge/security_agent/`
**Features**:
- Directory structure compliance checking
- Agent ID consistency across all files
- Registry integration validation
- Content quality assessment with scoring

### Quality Assurance Commands

#### `/project:validate-naming-conventions`
**Purpose**: Check project-wide naming convention compliance
**Usage**: `/project:validate-naming-conventions src/agents/`
**Features**:
- Pattern matching for all naming conventions
- Cross-reference consistency validation
- Critical vs. standard violation classification
- Automated fix suggestions

#### `/project:validate-knowledge-chunk`
**Purpose**: Ensure H3 sections are atomic and RAG-optimized
**Usage**: `/project:validate-knowledge-chunk knowledge/security_agent/oauth2-guide.md`
**Features**:
- Self-containment analysis
- Context dependency detection
- RAG optimization assessment
- Content completeness validation

### Migration & Deployment Commands

#### `/project:migrate-knowledge-file`
**Purpose**: Move knowledge files between agents with metadata updates
**Usage**: `/project:migrate-knowledge-file knowledge/create_agent/auth.md security_agent`
**Features**:
- Content relevance assessment
- Metadata transformation with migration tracking
- Cross-reference impact analysis and updates
- Conflict resolution and merge strategies

#### `/project:generate-qdrant-schema`
**Purpose**: Create Qdrant collection schemas and configurations
**Usage**: `/project:generate-qdrant-schema security_agent`
**Features**:
- Performance-optimized collection configuration
- Blue-green deployment setup
- Integration with MCP servers and ingestion pipeline
- Monitoring and alerting configuration

#### `/project:convert-legacy-knowledge`
**Purpose**: Migrate old knowledge files to new format
**Usage**: `/project:convert-legacy-knowledge knowledge/old-format/security-guide.md`
**Features**:
- Legacy format detection (ANCHOR system, incomplete front matter)
- Content restructuring for atomic chunks
- Link modernization and cross-reference updates
- Agent domain classification

### Utility Commands

#### `/project:list-commands`
**Purpose**: Display catalog of all available commands
**Usage**: `/project:list-commands`
**Features**:
- Complete command catalog with descriptions
- Usage examples and best practices
- Command development guidelines
- Integration with project workflow

## Command Development Workflow

### 1. Creating New Commands

1. **Identify need**: Determine what repetitive documentation task needs automation
2. **Create command file**: Add `.md` file directly in `.claude/commands/` directory
3. **Follow template structure**: Use standard command template format
4. **Test command**: Verify command works as expected in Claude Code
5. **Update catalog**: Add new command to this specification document

### 2. Command Testing

- Test commands with various file types
- Verify output format meets requirements
- Ensure commands handle edge cases appropriately
- Validate against project standards in CLAUDE.md

### 3. Command Maintenance

- Update commands when project standards change
- Keep command catalog current in this document
- Version control all commands in git repository
- Review command effectiveness regularly

## Integration with Project Workflow

### Git Integration
- Commands are version controlled in `.claude/commands/`
- Available to entire team through repository
- Changes tracked through normal git workflow

### Documentation Integration
- Commands reference CLAUDE.md standards
- Align with knowledge base style guide
- Support project naming conventions

### Development Integration
- Commands assist with pre-commit workflows
- Support CI/CD documentation validation
- Enable consistent documentation standards

## Future Command Ideas

### Proposed Additional Commands

#### `/project:create-planning-doc`
Create new planning documents with proper structure and cross-references.

#### `/project:update-links`
Batch update links across multiple files when documents are moved or renamed.

#### `/project:validate-knowledge-agent`
Comprehensive validation of entire agent knowledge directory structure.

#### `/project:generate-toc`
Generate table of contents for planning documents.

#### `/project:check-cross-refs`
Validate cross-references between related planning documents.

## Benefits and Impact

### For Developers
- **Consistency**: Ensures all documentation follows project standards
- **Efficiency**: Reduces manual review time by 80%
- **Quality**: Maintains high documentation quality automatically
- **Learning**: Commands teach project standards through usage

### For Project
- **Standardization**: All documentation follows consistent format
- **Maintainability**: Easy to update and maintain documentation
- **Onboarding**: New team members learn standards through commands
- **Scalability**: Standards scale with project growth

## Conclusion

Claude Code slash commands provide a powerful way to automate and standardize documentation workflows in PromptCraft-Hybrid. By creating prompt templates that encode project knowledge and standards, we enable consistent, high-quality documentation across the entire project.

The commands developed here transform the manual exec.md standardization process into repeatable, automated workflows that any team member can use. This approach scales project standards and reduces the cognitive load of remembering complex validation rules.

Key success factors:
- **Comprehensive command coverage** for all documentation tasks
- **Regular command updates** as project standards evolve
- **Team adoption** and consistent command usage
- **Continuous improvement** based on usage feedback

These commands serve as both automation tools and living documentation of project standards, ensuring consistency and quality as the project grows.
