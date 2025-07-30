---
category: meta
complexity: low
estimated_time: "< 3 minutes"
dependencies: []
sub_commands: []
version: "1.0"
---

# Meta Command Help

Interactive command discovery and smart suggestion system: $ARGUMENTS

## Usage Options

- `"I need to [description]"` - Natural language command suggestion
- `auto` - Context-aware suggestions based on current git status
- `category [workflow|validation|creation|migration|meta]` - Browse commands by category
- `quick` - Show quick reference for common tasks

## Interactive Command Discovery

### Natural Language Queries

Describe what you need to do and get smart command suggestions:

```bash
# Examples of natural language queries
/project:meta-command-help "I need to fix broken links in my documentation"
/project:meta-command-help "I want to create a new knowledge file for security"
/project:meta-command-help "I need to validate my agent structure"
/project:meta-command-help "I want to resolve an issue systematically"
```

**Expected Responses**:

- **Link fixing**: Suggests `/project:meta-fix-links docs/planning/filename.md`
- **Knowledge creation**: Suggests `/project:creation-knowledge-file security [topic] [subtopic]`
- **Agent validation**: Suggests `/project:validation-agent-structure knowledge/agent_name/`
- **Issue resolution**: Suggests `/project:workflow-resolve-issue standard phase X issue Y`

### Context-Aware Suggestions

Get recommendations based on your current development context:

```bash
/project:meta-command-help auto
```

**Context Analysis**:

- **Modified .md files**: Suggests validation commands
- **New branch with issue**: Suggests workflow commands
- **Modified knowledge files**: Suggests validation and migration commands
- **Modified Python files**: Suggests pre-commit validation
- **Uncommitted changes**: Suggests validation-precommit

### Category Browsing

Explore commands by category with examples:

```bash
# Browse specific categories
/project:meta-command-help category workflow
/project:meta-command-help category validation
/project:meta-command-help category creation
/project:meta-command-help category migration
/project:meta-command-help category meta
```

## Smart Suggestion Logic

### Based on File Types

- **`.md` files**: Document validation, link fixing, front matter validation
- **Knowledge files**: Knowledge chunk validation, agent structure validation
- **Planning docs**: Planning doc standardization, lint checking
- **Python files**: Pre-commit validation, naming convention checks

### Based on Git Status

- **New branch**: Issue resolution workflow
- **Modified files**: Validation commands appropriate to file types
- **Untracked files**: Creation commands for proper structure
- **Merge conflicts**: Link fixing and validation commands

### Based on Directory Context

- **`knowledge/` directory**: Knowledge file operations, agent validation
- **`docs/planning/` directory**: Planning document operations, link fixing
- **`src/` directory**: Code validation, naming convention checks
- **`.claude/commands/` directory**: Command development and validation

## Quick Reference Mode

```bash
/project:meta-command-help quick
```

**Common Task Shortcuts**:

### Daily Development Tasks

```bash
# Before committing any changes
/project:validation-precommit

# Fix documentation issues
/project:validation-lint-doc [file.md]
/project:meta-fix-links [file.md]

# Create new content
/project:creation-knowledge-file [agent] [topic] [subtopic]
/project:creation-planning-doc "[title]" [type]
```

### Issue Resolution Workflow

```bash
# Quick issue resolution (30-45 min)
/project:workflow-resolve-issue quick phase X issue Y

# Standard workflow (60-90 min) - RECOMMENDED
/project:workflow-resolve-issue standard phase X issue Y

# Individual components
/project:workflow-scope-analysis phase X issue Y
/project:workflow-plan-validation phase X issue Y
```

### Quality Assurance

```bash
# Validate agent structures
/project:validation-agent-structure knowledge/[agent_name]/

# Check naming conventions
/project:validation-naming-conventions [directory]

# Validate knowledge chunks
/project:validation-knowledge-chunk [file.md]
```

## Advanced Features

### Command Chaining Suggestions

Based on your query, suggest sequences of commands:

**Example**: "I need to create and validate a new agent"
**Suggested Sequence**:

1. `/project:creation-agent-skeleton [agent_name] "[description]"`
2. `/project:validation-agent-structure knowledge/[agent_name]/`
3. `/project:validation-naming-conventions knowledge/[agent_name]/`

### Error Recovery Assistance

When commands fail, suggest recovery actions:

**Example**: Link validation fails
**Suggested Recovery**:

1. `/project:meta-fix-links [failing_file.md]`
2. `/project:validation-lint-doc [failing_file.md]`
3. Re-run original command

### Progressive Disclosure

Start with simple suggestions and offer more advanced options:

**Level 1**: Basic command suggestion
**Level 2**: Command with common options
**Level 3**: Full workflow with all parameters

## Output Format

```markdown
## Command Suggestions for: "[Your Query]"

### Recommended Command
`/project:[command-name] [suggested arguments]`

**Why**: [Explanation of why this command fits your need]
**Estimated Time**: [Time estimate]
**Prerequisites**: [Any setup or dependencies needed]

### Alternative Options
- `/project:[alt-command-1]` - [Brief description]
- `/project:[alt-command-2]` - [Brief description]

### Follow-up Commands
After running the recommended command, you might want to:
1. `/project:[followup-1]` - [Description]
2. `/project:[followup-2]` - [Description]

### Quick Help
- **Usage**: [Detailed usage example]
- **Common Issues**: [Troubleshooting tips]
- **Examples**: [Real-world usage examples]
```

## Examples

```bash
# Natural language discovery
/project:meta-command-help "I need to create a security authentication guide"
# Returns: /project:creation-knowledge-file security authentication best-practices

# Context-aware help
/project:meta-command-help auto
# Analyzes current git status and suggests relevant commands

# Category exploration
/project:meta-command-help category workflow
# Shows all workflow commands with descriptions

# Quick reference
/project:meta-command-help quick
# Shows common daily commands
```

## Error Handling

- **Ambiguous queries**: Ask clarifying questions with examples
- **Unknown context**: Provide general command overview with categories
- **No git context**: Suggest manual command selection by category
- **Invalid category**: List available categories with descriptions

## Integration

This command integrates with:

- **Git status analysis** for context-aware suggestions
- **File type detection** for appropriate command recommendations
- **Project standards** from CLAUDE.md for accurate guidance
- **Command metadata** for complexity and time estimates

---

*This command helps bridge the gap between what you want to accomplish and the specific commands available in the PromptCraft-Hybrid development environment.*
