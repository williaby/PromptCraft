---
category: meta
complexity: low
estimated_time: "< 2 minutes"
dependencies: []
sub_commands: []
version: "2.0"
---

# Meta List Commands

Display all available custom slash commands organized by category: $ARGUMENTS

## Usage Options
- `all` - Display all commands across categories (default)
- `workflow` - Show workflow orchestration commands only
- `validation` - Show validation and compliance commands only
- `creation` - Show file and artifact creation commands only
- `migration` - Show data migration and conversion commands only
- `meta` - Show command management utilities only

## Available Command Categories

### Workflow Commands (`workflow-*.md`)
**Complex multi-step orchestration for major development tasks**

#### `/project:workflow-resolve-issue`
**Purpose**: Main issue resolution orchestrator with modular components
**Usage**: `/project:workflow-resolve-issue standard phase 1 issue 3`
**Description**: Systematically resolves project issues through scope analysis, plan validation, implementation, and review cycles. Supports quick/standard/expert modes.

#### `/project:workflow-scope-analysis`
**Purpose**: Define issue boundaries and prevent scope creep
**Usage**: `/project:workflow-scope-analysis phase 1 issue 3`
**Description**: Analyzes issue definition, creates scope boundary documentation, identifies dependencies and unclear requirements.

#### `/project:workflow-plan-validation`
**Purpose**: Create and validate implementation plan
**Usage**: `/project:workflow-plan-validation phase 1 issue 3`
**Description**: Develops action plan aligned with acceptance criteria, validates scope boundaries, optional IT manager consultation.

#### `/project:workflow-implementation`
**Purpose**: Execute approved plan with quality standards
**Usage**: `/project:workflow-implementation phase 1 issue 3`
**Description**: Implements solution using subagents and MCP orchestration, follows security best practices and coding standards.

#### `/project:workflow-review-cycle`
**Purpose**: Comprehensive testing and multi-agent validation
**Usage**: `/project:workflow-review-cycle phase 1 issue 3`
**Description**: Pre-commit validation, multi-agent review (O3 testing, Gemini review), consensus validation and final approval.

### Validation Commands (`validation-*.md`)
**Standalone validation and compliance checking**

#### `/project:validation-lint-doc`
**Purpose**: Comprehensive document compliance checking
**Usage**: `/project:validation-lint-doc docs/planning/exec.md`
**Description**: Validates YAML front matter, heading structure, internal links, and markdown formatting against project standards.

#### `/project:validation-frontmatter`
**Purpose**: Validate and fix YAML front matter
**Usage**: `/project:validation-frontmatter knowledge/security_agent/auth-guide.md`
**Description**: File-type specific validation of YAML metadata including title consistency, agent ID matching, and tag format compliance.

#### `/project:validation-precommit`
**Purpose**: Pre-commit hook validation and linting
**Usage**: `/project:validation-precommit`
**Description**: Runs comprehensive pre-commit checks including file-specific linting, security scans, and code quality validation.

#### `/project:validation-agent-structure`
**Purpose**: Comprehensive validation of agent directory structure
**Usage**: `/project:validation-agent-structure knowledge/security_agent/`
**Description**: Validates naming conventions, metadata consistency, and integration compliance for agent directories.

#### `/project:validation-naming-conventions`
**Purpose**: Check project-wide naming convention compliance
**Usage**: `/project:validation-naming-conventions src/agents/`
**Description**: Validates snake_case, kebab-case, PascalCase usage per development guidelines across the project.

#### `/project:validation-knowledge-chunk`
**Purpose**: Ensure H3 sections are atomic and RAG-optimized
**Usage**: `/project:validation-knowledge-chunk knowledge/security_agent/oauth2-guide.md`
**Description**: Validates content for self-containment, completeness, and vector search optimization.

#### `/project:validation-standardize-planning-doc`
**Purpose**: Standardize planning documents with proper compliance
**Usage**: `/project:validation-standardize-planning-doc docs/planning/PC_Setup.md`
**Description**: Adds proper YAML front matter, fixes linting issues, ensures compliance with development standards.

### Creation Commands (`creation-*.md`)
**File and artifact generation with proper structure**

#### `/project:creation-knowledge-file`
**Purpose**: Create new knowledge base files with proper structure
**Usage**: `/project:creation-knowledge-file security authentication best practices`
**Description**: Generates knowledge files following C.R.E.A.T.E. framework with correct YAML front matter and atomic H3 sections.

#### `/project:creation-agent-skeleton`
**Purpose**: Create complete agent directory structure and base files
**Usage**: `/project:creation-agent-skeleton tax_preparation_agent "Tax form preparation"`
**Description**: Generates agent directory, knowledge files, Python class, registry entry, and configurations.

#### `/project:creation-planning-doc`
**Purpose**: Create new planning documents with proper structure
**Usage**: `/project:creation-planning-doc "API Gateway Strategy" architecture`
**Description**: Generates planning documents with appropriate templates, front matter, and cross-references.

### Migration Commands (`migration-*.md`)
**Data migration and format conversion**

#### `/project:migration-knowledge-file`
**Purpose**: Move knowledge files between agents with metadata updates
**Usage**: `/project:migration-knowledge-file knowledge/create_agent/auth.md security_agent`
**Description**: Migrates files with proper metadata updates, cross-reference fixes, and agent ID consistency.

#### `/project:migration-legacy-knowledge`
**Purpose**: Convert old knowledge files to new format
**Usage**: `/project:migration-legacy-knowledge knowledge/old-format/security-guide.md`
**Description**: Converts legacy formats, updates front matter, modernizes links, and optimizes structure.

#### `/project:migration-qdrant-schema`
**Purpose**: Generate Qdrant collection schemas and configurations
**Usage**: `/project:migration-qdrant-schema security_agent`
**Description**: Generates optimized collection configs, blue-green deployment setup, and integration configurations.

### Meta Commands (`meta-*.md`)
**Command management and discovery utilities**

#### `/project:meta-list-commands`
**Purpose**: Display available commands organized by category
**Usage**: `/project:meta-list-commands workflow`
**Description**: Shows all custom slash commands with usage examples, descriptions, and category organization.

#### `/project:meta-fix-links`
**Purpose**: Analyze and fix broken internal links
**Usage**: `/project:meta-fix-links docs/planning/exec.md`
**Description**: Identifies broken repository links, provides smart suggestions using fuzzy matching, and generates corrected content.

## How to Use Commands

### Basic Usage
1. **Type `/`** in Claude Code to open the slash command menu
2. **Select command** from the list or type the full command name
3. **Add arguments** as specified in the usage examples
4. **Commands reference** project standards from CLAUDE.md and style guides

### Command Discovery
```bash
# List commands by category
/project:meta-list-commands workflow
/project:meta-list-commands validation

# Show all commands
/project:meta-list-commands all
```

### Progressive Workflow Usage
```bash
# Quick issue resolution (30-45 min)
/project:workflow-resolve-issue quick phase 1 issue 3

# Standard workflow (60-90 min) - RECOMMENDED
/project:workflow-resolve-issue standard phase 1 issue 3

# Expert mode (15-30 min)
/project:workflow-resolve-issue expert phase 1 issue 3

# Individual workflow components
/project:workflow-scope-analysis phase 1 issue 3
/project:workflow-plan-validation phase 1 issue 3
/project:workflow-implementation phase 1 issue 3
/project:workflow-review-cycle phase 1 issue 3
```

## Command Development Standards

### Naming Convention
```
{category}-{action}-{object}.md
```

### Categories
- **workflow**: Complex multi-step orchestration (15+ min)
- **validation**: Standalone validation and compliance (< 15 min)
- **creation**: File and artifact generation (5-15 min)
- **migration**: Data migration and conversion (5-15 min)
- **meta**: Command management utilities (< 5 min)

### File Location
- **All commands**: `.claude/commands/` (flat structure)
- **Configuration**: `.claude/README.md` for setup guide
- **Standards**: `docs/planning/slash-command-spec.md` for development guidelines

## Quick Reference Examples

```bash
# Document validation and fixing
/project:validation-lint-doc docs/planning/exec.md
/project:meta-fix-links docs/planning/project-hub.md

# Knowledge base management
/project:creation-knowledge-file security oauth2 implementation
/project:validation-knowledge-chunk knowledge/create_agent/prompt-basics.md
/project:migration-knowledge-file knowledge/old/auth.md security_agent

# Agent development
/project:creation-agent-skeleton tax_agent "Tax preparation and compliance"
/project:validation-agent-structure knowledge/security_agent/

# Pre-commit and quality
/project:validation-precommit
/project:validation-naming-conventions src/agents/
```

## Support and Documentation

- **Command Configuration**: `.claude/README.md`
- **Development Standards**: `CLAUDE.md`
- **Project Hub**: `docs/planning/project-hub.md`
- **Slash Command Spec**: `docs/planning/slash-command-spec.md`
- **Interactive Help**: Commands provide built-in error handling and examples

---

*Commands are automatically loaded by Claude Code and provide intelligent, context-aware development assistance following PromptCraft-Hybrid standards.*
