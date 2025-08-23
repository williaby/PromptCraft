# AI Tools Integration for PromptCraft-Hybrid

This document describes the automated AI coding tools validation and setup system for VS Code development.

## Overview

When you open the PromptCraft repository in VS Code, the system automatically:

1. **Validates** installed AI coding CLI tools
2. **Creates** configuration templates for missing tools
3. **Reports** installation and configuration status
4. **Suggests** installation steps for missing tools

## Supported AI Tools

| Tool | Command | Description | Auto-Install |
|------|---------|-------------|--------------|
| [Claude Code](https://claude.ai/code) | `claude` | Anthropic's official CLI | Manual |
| [GitHub Copilot CLI](https://cli.github.com/) | `gh copilot` | GitHub's AI assistant | Via `gh` extension |
| [Gemini CLI](https://ai.google.dev/gemini-api/docs/cli) | `gemini` | Google's AI CLI | Manual |
| [Qwen Code CLI](https://github.com/QwenLM/Qwen-CLI) | `qwen` | Alibaba's coding assistant | Manual |
| [OpenAI CLI](https://platform.openai.com/docs/api-reference) | `openai` | OpenAI's official CLI | Via `pip` |

## Automatic Integration

### VS Code Tasks

The system adds a VS Code task that runs automatically when the folder is opened:

```json
{
  "label": "Validate AI Tools",
  "type": "shell",
  "command": "python",
  "args": ["scripts/ai_tools_validator.py", "--create-templates"],
  "runOptions": {
    "runOn": "folderOpen"
  }
}
```

### VS Code Settings

AI tools configuration is tracked in `.vscode/settings.json`:

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

## Configuration Templates

The system automatically creates configuration files for each tool:

### Claude Code: `.claude/settings.json`
```json
{
  "mcp": {
    "servers": {
      "zen-mcp-server": {
        "command": "python",
        "args": ["-m", "zen_mcp_server"]
      }
    }
  }
}
```

### GitHub Copilot: `.github/copilot.yml`
```yaml
suggestions:
  enabled: true
  languages:
    python: true
    # ... other languages
exclude:
  - "*.env*"
  - "**/node_modules/**"
  # ... other exclusions
```

### Gemini CLI: `.gemini/config.json`
```json
{
  "project": "PromptCraft-Hybrid",
  "settings": {
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.3
  },
  "project_context": {
    "architecture": "hybrid-ai-workbench"
  }
}
```

### Qwen CLI: `.qwen/config.json`
```json
{
  "project": "PromptCraft-Hybrid",
  "code_assistance": {
    "languages": {
      "python": {
        "style": "black",
        "linting": ["ruff", "mypy"]
      }
    }
  }
}
```

### OpenAI CLI: `.openai/config.json`
```json
{
  "project": "PromptCraft-Hybrid",
  "models": {
    "code": "gpt-4-turbo",
    "chat": "gpt-4"
  },
  "coding_standards": {
    "python": {
      "formatter": "black",
      "type_checking": "mypy"
    }
  }
}
```

## Manual Setup

### Quick Setup (Interactive)
```bash
# Run the interactive setup script
./scripts/setup_ai_tools.sh
```

### Individual Tool Validation
```bash
# Check all tools with full report
python scripts/ai_tools_validator.py

# Check all tools with quiet output
python scripts/ai_tools_validator.py --quiet

# Create configuration templates only
python scripts/ai_tools_validator.py --create-templates

# Attempt auto-installation where possible
python scripts/ai_tools_validator.py --install-missing
```

## Environment Variables

Create a `.env` file (copy from `.env.example`) with your API keys:

```bash
# AI Tool API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
GITHUB_TOKEN=your_github_token_here
```

## Project-Specific Context

Each tool is configured with PromptCraft-specific context:

- **Architecture**: Hybrid AI workbench with agent-based design
- **Primary Language**: Python 3.11+ with Poetry
- **Frameworks**: FastAPI, Gradio, Prefect
- **AI Integration**: Zen MCP Server, Heimdall MCP Server
- **Code Standards**: Black (88 chars), Ruff, MyPy
- **Testing**: Pytest with 80% coverage minimum
- **Knowledge Base**: Structured markdown with YAML frontmatter

## Troubleshooting

### Tool Not Detected
1. Check if the tool is in your PATH: `which <command>`
2. Verify installation: `<command> --version`
3. Check VS Code terminal environment
4. Restart VS Code after installing tools

### Configuration Issues
1. Check for missing API keys in `.env`
2. Verify configuration file syntax
3. Run validation manually: `python scripts/ai_tools_validator.py`
4. Recreate templates: `python scripts/ai_tools_validator.py --create-templates`

### VS Code Integration
1. Ensure tasks.json includes the "Validate AI Tools" task
2. Check if task runs on folder open: "runOn": "folderOpen"
3. View task output in VS Code Terminal panel
4. Manually run task: Ctrl/Cmd + Shift + P → "Tasks: Run Task" → "Validate AI Tools"

## Exit Codes

The validator returns specific exit codes:

- `0`: All tools installed and configured
- `1`: Some tools installed but not fully configured  
- `2`: No tools installed

## File Structure

```
.claude/
├── CLAUDE.md              # Project instructions (existing)
└── settings.json          # Claude Code configuration

.github/
├── copilot.yml            # GitHub Copilot configuration
└── ... (other GitHub files)

.gemini/
└── config.json            # Gemini CLI configuration

.qwen/
└── config.json            # Qwen CLI configuration

.openai/
└── config.json            # OpenAI CLI configuration

.vscode/
├── settings.json          # VS Code settings (with ai-tools config)
└── tasks.json             # VS Code tasks (with validation task)

scripts/
├── ai_tools_validator.py  # Main validation script
└── setup_ai_tools.sh      # Interactive setup script

.env.example               # Environment variables template
.env                       # Your actual API keys (gitignored)
```

## Integration Benefits

1. **Consistency**: All developers have the same AI tools setup
2. **Automation**: No manual configuration steps after initial setup
3. **Validation**: Regular checks ensure tools remain configured
4. **Project Context**: All tools understand PromptCraft architecture
5. **Best Practices**: Configurations follow project standards
6. **Quick Start**: New developers can get productive quickly

## Future Enhancements

Potential improvements to the system:

- VS Code extension for visual tool status
- Integration with development containers
- Automatic API key rotation
- Tool usage analytics
- Custom tool configurations per developer role
- Integration with CI/CD pipelines