# Claude Code Configuration

This directory contains Claude Code configuration for the PromptCraft-Hybrid project, including custom slash commands, settings, and user preferences.

## Directory Structure

```
.claude/
├── README.md                    # This file - configuration guide
├── commands/                    # Custom slash commands (flat structure)
│   ├── workflow-*.md           # Complex multi-step workflows
│   ├── validation-*.md         # Standalone validation commands
│   ├── creation-*.md           # File/artifact creation commands
│   ├── migration-*.md          # Data migration and conversion
│   └── meta-*.md              # Command management utilities
└── settings.local.json         # Local user preferences
```

## Configuration Levels

### Global Configuration (`~/.claude/CLAUDE.md`)

- **Universal development standards** across all projects
- **Security requirements** (GPG/SSH keys, encryption)
- **Code quality standards** (linting, formatting, testing)
- **Git workflow standards** (branch naming, commit messages)
- **Pre-commit linting requirements** for all file types

### Project Configuration (`./CLAUDE.md`)

- **Project-specific standards** and development commands
- **Architecture concepts** and design patterns
- **Development philosophy** (Reuse First, Configure Don't Build)
- **Naming conventions** and coding standards
- **Knowledge base standards** following C.R.E.A.T.E. Framework

### Local Settings (`settings.local.json`)

```json
{
  "command_defaults": {
    "timeout": "120m",
    "auto_context": true,
    "multi_agent": true,
    "complexity_preference": "standard"
  },
  "workflow_presets": {
    "quick_issue": ["workflow-scope-analysis", "workflow-implementation"],
    "full_cycle": ["workflow-scope-analysis", "workflow-plan-validation", "workflow-implementation", "workflow-review-cycle"]
  },
  "user_preferences": {
    "preferred_models": ["claude-sonnet-4", "o3"],
    "auto_todo_tracking": true,
    "verbose_output": false
  }
}
```

## Command Categories

### Workflow Commands (`workflow-*.md`)

**Complex multi-step orchestration for major development tasks**

- `workflow-resolve-issue.md` - Main issue resolution orchestrator
- `workflow-scope-analysis.md` - Issue analysis and boundary definition
- `workflow-plan-validation.md` - Planning and approval workflow
- `workflow-implementation.md` - Code development workflow
- `workflow-review-cycle.md` - Testing and validation workflow

**Usage**: `/project:workflow-resolve-issue quick phase 1 issue 3`

### Validation Commands (`validation-*.md`)

**Standalone validation and compliance checking**

- `validation-lint-doc.md` - Document compliance checking
- `validation-frontmatter.md` - YAML front matter validation
- `validation-precommit.md` - Pre-commit hook validation
- `validation-agent-structure.md` - Agent directory validation
- `validation-naming-conventions.md` - Project naming compliance
- `validation-knowledge-chunk.md` - RAG optimization validation

**Usage**: `/project:validation-lint-doc docs/planning/exec.md`

### Creation Commands (`creation-*.md`)

**File and artifact generation with proper structure**

- `creation-knowledge-file.md` - Knowledge base file creation
- `creation-agent-skeleton.md` - Complete agent structure creation
- `creation-planning-doc.md` - Planning document creation

**Usage**: `/project:creation-knowledge-file security authentication best practices`

### Migration Commands (`migration-*.md`)

**Data migration and format conversion**

- `migration-knowledge-file.md` - Move knowledge between agents
- `migration-legacy-knowledge.md` - Convert old format files
- `migration-qdrant-schema.md` - Generate Qdrant configurations

**Usage**: `/project:migration-knowledge-file knowledge/create_agent/auth.md security_agent`

### Meta Commands (`meta-*.md`)

**Command management and discovery utilities**

- `meta-list-commands.md` - Display available commands by category
- `meta-command-help.md` - Interactive command discovery
- `meta-fix-links.md` - Internal link analysis and repair

**Usage**: `/project:meta-list-commands workflow`

## Command Development Standards

### File Naming Convention

```
{category}-{action}-{object}.md
```

**Examples**:

- `workflow-resolve-issue.md`
- `validation-lint-doc.md`
- `creation-knowledge-file.md`
- `migration-legacy-knowledge.md`
- `meta-list-commands.md`

### Command Structure Template

```markdown
---
category: workflow|validation|creation|migration|meta
complexity: low|medium|high
estimated_time: "5-15 minutes"
dependencies: []
sub_commands: []
version: "1.0"
---

# {Category} {Action} {Object}

Brief description of command purpose: $ARGUMENTS

## Usage Options
- `quick [args]` - Essential steps only
- `standard [args]` - Full workflow
- `expert [args]` - Minimal prompts

## Instructions
[Detailed command instructions]

## Error Handling
[Recovery and fallback strategies]

## Examples
[Usage examples with expected outcomes]
```

### Complexity Guidelines

- **Low** (< 5 min): Single validation or simple file creation
- **Medium** (5-15 min): Multi-step validation or complex file generation
- **High** (15+ min): Full workflow orchestration with sub-commands

## Integration Features

### Auto-Context Loading

Commands automatically load relevant documentation based on:

- Command category and complexity
- Current git branch and file changes
- Issue phase and dependencies
- User preference settings

### Multi-Agent Orchestration

High-complexity commands can leverage:

- **Zen MCP Server** for real-time agent coordination
- **External models** (O3, Gemini) for specialized tasks
- **Consensus validation** across multiple AI models
- **Progressive disclosure** based on user experience level

### Smart Error Recovery

- **Missing dependencies**: Auto-generate templates or provide setup instructions
- **Invalid arguments**: Interactive prompts for clarification
- **Timeout scenarios**: Checkpoint and resume capabilities
- **Scope creep**: Automatic boundary validation and correction

## User Experience Features

### Progressive Disclosure

```bash
# Quick mode - essential steps only
/project:workflow-resolve-issue quick phase 1 issue 3

# Standard mode - full workflow with validation
/project:workflow-resolve-issue standard phase 1 issue 3

# Expert mode - minimal prompts for experienced users
/project:workflow-resolve-issue expert phase 1 issue 3
```

### Command Discovery

```bash
# List commands by category
/project:meta-list-commands workflow
/project:meta-list-commands validation

# Interactive command suggestion
/project:meta-command-help "I need to fix broken links"

# Context-aware suggestions based on git status
/project:meta-command-help auto
```

### Workflow Composition

```bash
# Run only specific workflow components
/project:workflow-scope-analysis phase 1 issue 3
/project:workflow-implementation phase 1 issue 3

# Custom workflow sequences
/project:workflow-resolve-issue preset=quick_cycle phase 1 issue 3
```

## Configuration Best Practices

### Local Settings Management

1. **Never commit** `settings.local.json` - it's user-specific
2. **Use presets** for common workflow combinations
3. **Set timeouts** appropriate for your development speed
4. **Configure model preferences** based on usage patterns

### Command Maintenance

1. **Follow naming conventions** strictly for discoverability
2. **Update dependencies** when commands reference each other
3. **Test error scenarios** to ensure graceful degradation
4. **Document examples** with expected outcomes

### Security Considerations

1. **Validate inputs** to prevent injection attacks
2. **Respect file permissions** and don't create files outside project
3. **Use encrypted storage** for any sensitive command parameters
4. **Follow global security standards** from `~/.claude/CLAUDE.md`

## Troubleshooting

### Common Issues

- **Command not found**: Check spelling and category prefix
- **Permission denied**: Ensure proper file permissions and git status
- **Timeout errors**: Increase timeout in `settings.local.json`
- **Missing dependencies**: Run `/project:validation-precommit` first

### Debug Mode

```bash
# Enable verbose output for troubleshooting
/project:workflow-resolve-issue debug phase 1 issue 3
```

### Support Resources

- **Command catalog**: `/project:meta-list-commands`
- **Interactive help**: `/project:meta-command-help`
- **Project documentation**: `docs/planning/project-hub.md`
- **Development standards**: `CLAUDE.md`

---

*This configuration is automatically loaded by Claude Code and provides the foundation for intelligent, context-aware development assistance.*
