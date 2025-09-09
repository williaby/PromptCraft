# AI Tools Validation and Setup

> **Command**: `/tools:ai-validate [options]`  
> **Category**: Development Tools  
> **Purpose**: Validate and configure AI coding CLI tools for any development project

## Overview

This command provides comprehensive validation and setup of AI coding CLI tools across any development project. It automatically detects project type, validates tool installations, creates project-specific configurations, and sets up VS Code integration.

## Usage Patterns

### Basic Validation

```bash
/tools:ai-validate
```

- Validates all AI tools in current project
- Shows detailed installation and configuration status
- Provides setup instructions for missing tools

### Quick Status Check

```bash
/tools:ai-validate --quiet
```

- Returns summary: "AI Tools: 3/5 installed, 2/5 configured"
- Minimal output for scripting or quick checks

### Project Setup

```bash
/tools:ai-validate --setup
```

- Creates configuration templates for all supported tools
- Sets up VS Code integration (tasks and settings)
- Configures project-specific AI tool settings

### Installation Mode

```bash
/tools:ai-validate --install
```

- Attempts automatic installation of missing tools
- Shows manual installation instructions when auto-install isn't available
- Re-validates after installation attempts

## Supported AI Tools

| Tool | Command | Auto-Install | Configuration |
|------|---------|-------------|---------------|
| **Claude Code** | `claude` | Manual | `.claude/settings.json` |
| **GitHub Copilot CLI** | `gh copilot` | Via `gh extension` | `.github/copilot.yml` |
| **Gemini CLI** | `gemini` | Manual | `.gemini/config.json` |
| **Qwen Code CLI** | `qwen` | Manual | `.qwen/config.json` |
| **OpenAI CLI** | `openai` | Via `pip install` | `.openai/config.json` |

## Project Type Detection

The command automatically detects project characteristics and creates appropriate configurations:

- **Python**: Detects Poetry, pip, FastAPI, Django, Flask, Gradio
- **JavaScript/Node.js**: Detects npm, yarn, React, Vue, Express
- **Rust**: Detects Cargo, common Rust frameworks
- **Go**: Detects go.mod, Go framework patterns
- **Generic**: Creates basic configuration for unknown project types

## Configuration Templates

### Claude Code Configuration

```json
{
  "project": {
    "name": "project-name",
    "type": "python",
    "languages": ["python"]
  },
  "tools": {
    "enabled": ["basic_commands"],
    "disabled": []
  }
}
```

### GitHub Copilot Configuration

```yaml
suggestions:
  enabled: true
  languages:
    python: true
    javascript: true

exclude:
  - "*.env*"
  - "**/node_modules/**"
  - "**/.venv/**"
```

### VS Code Integration

The command automatically configures VS Code when `.vscode/` directory exists:

**Settings Integration**:

```json
{
  "ai-tools": {
    "validation": {
      "enabled": true,
      "checkOnOpen": true,
      "createTemplates": true,
      "tools": ["claude", "copilot", "gemini", "qwen", "codex"]
    }
  }
}
```

**Task Integration**:

```json
{
  "label": "Validate AI Tools",
  "type": "shell",
  "command": "python",
  "args": ["~/.claude/scripts/ai_tools_validator.py", "--setup-project"],
  "runOptions": {
    "runOn": "folderOpen"
  }
}
```

## Environment Variables

The command checks for required API keys:

```bash
# Required environment variables
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_AI_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key
QWEN_API_KEY=your_qwen_api_key
GITHUB_TOKEN=your_github_token
```

## Exit Codes and Status

- `0`: All tools installed and configured
- `1`: Some tools installed but not fully configured
- `2`: No tools installed

## Implementation

```python
import subprocess
import sys
from pathlib import Path

def execute_ai_tools_validation():
    """Execute AI tools validation command."""
    script_path = Path.home() / ".claude" / "scripts" / "ai_tools_validator.py"
    
    # Parse command arguments
    import shlex
    args = []
    
    # Check for common argument patterns
    user_input = context.get("user_input", "").lower()
    
    if "--quiet" in user_input or "quiet" in user_input:
        args.append("--quiet")
    
    if "--setup" in user_input or "setup" in user_input:
        args.append("--setup-project")
        
    if "--install" in user_input or "install" in user_input:
        args.append("--install-missing")
    
    # Execute the validation script
    try:
        result = subprocess.run(
            ["python", str(script_path)] + args,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Display results
        print(result.stdout)
        
        if result.stderr:
            print("Errors:", result.stderr)
        
        # Provide contextual guidance based on exit code
        if result.returncode == 0:
            print("\n✅ All AI tools are properly configured!")
        elif result.returncode == 1:
            print("\n⚠️  Some tools need configuration. Check API keys and config files above.")
        elif result.returncode == 2:
            print("\n❌ No AI tools detected. Run with --install option to set up tools.")
        
        return result.returncode
        
    except Exception as e:
        print(f"Error executing AI tools validation: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Python is available in PATH")
        print("2. Check that ~/.claude/scripts/ai_tools_validator.py exists")
        print("3. Verify file permissions")
        return 1

# Execute the command
exit_code = execute_ai_tools_validation()
```

## Examples

### Development Workflow Integration

```bash
# New project setup
cd /path/to/new/project
/tools:ai-validate --setup

# Daily development - quick check
/tools:ai-validate --quiet

# After installing new tools
/tools:ai-validate --install

# Troubleshooting configuration issues
/tools:ai-validate
```

### CI/CD Integration

```bash
# In CI pipeline
/tools:ai-validate --quiet
if [ $? -eq 0 ]; then
  echo "AI tools ready for development"
else
  echo "AI tools setup required"
fi
```

## Troubleshooting

### Tool Not Detected

- Verify tool is installed: `which <command>`
- Check PATH environment variable
- Restart terminal/VS Code after installation

### Configuration Issues  

- Check API keys in environment variables
- Verify configuration file syntax (JSON/YAML)
- Ensure proper file permissions

### VS Code Integration

- Confirm `.vscode/` directory exists
- Check `tasks.json` and `settings.json` syntax
- Restart VS Code after configuration changes

## Related Commands

- `/security:validate-env` - Validate environment variables and secrets
- `/quality:precommit-validate` - Run pre-commit validation
- `/workflow:git-helpers` - Git workflow assistance

---

*This command provides universal AI tools management across all development projects, with automatic project type detection and appropriate configuration generation.*
