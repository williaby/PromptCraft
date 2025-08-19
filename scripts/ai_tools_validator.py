#!/usr/bin/env python3
"""
AI Tools Validator for VS Code Development Environment

This script checks for the presence and configuration of AI coding CLI tools
when a project is opened in VS Code, providing installation and setup guidance.

Supported Tools:
- Claude Code (Anthropic)
- OpenAI Codex CLI
- Gemini CLI (Google)
- Qwen Code CLI
- GitHub Copilot CLI

Usage:
    python scripts/ai_tools_validator.py [--install-missing] [--quiet]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolConfig:
    """Configuration for an AI coding tool."""
    name: str
    command: str
    check_args: list[str]
    install_command: str | None = None
    install_instructions: str = ""
    config_files: list[str] = field(default_factory=list)
    environment_vars: list[str] = field(default_factory=list)
    version_regex: str = r"(\d+\.\d+(?:\.\d+)?)"


@dataclass
class ToolStatus:
    """Status information for a tool."""
    installed: bool = False
    version: str | None = None
    configured: bool = False
    config_issues: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    missing_env_vars: list[str] = field(default_factory=list)


class AIToolsValidator:
    """Validator for AI coding CLI tools."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.home_dir = Path.home()

        # Tool configurations
        self.tools: dict[str, ToolConfig] = {
            "claude": ToolConfig(
                name="Claude Code",
                command="claude",
                check_args=["--version"],
                install_instructions="""
Install Claude Code:
1. Install from: https://claude.ai/code
2. Run: claude auth login
3. Verify with: claude --version
                """,
                config_files=[".claude/CLAUDE.md", ".claude/settings.json"],
                environment_vars=["ANTHROPIC_API_KEY"],
            ),

            "copilot": ToolConfig(
                name="GitHub Copilot CLI",
                command="gh",
                check_args=["copilot", "--version"],
                install_command="gh extension install github/gh-copilot",
                install_instructions="""
Install GitHub Copilot CLI:
1. Install GitHub CLI: https://cli.github.com/
2. Run: gh extension install github/gh-copilot
3. Login: gh auth login
4. Verify with: gh copilot --version
                """,
                config_files=[".github/copilot.yml"],
                environment_vars=["GITHUB_TOKEN"],
            ),

            "gemini": ToolConfig(
                name="Gemini CLI",
                command="gemini",
                check_args=["--version"],
                install_instructions="""
Install Gemini CLI:
1. Install from: https://ai.google.dev/gemini-api/docs/cli
2. Run: gemini auth login
3. Verify with: gemini --version
                """,
                config_files=[".gemini/config.json"],
                environment_vars=["GOOGLE_AI_API_KEY", "GEMINI_API_KEY"],
            ),

            "qwen": ToolConfig(
                name="Qwen Code CLI",
                command="qwen",
                check_args=["--version"],
                install_instructions="""
Install Qwen Code CLI:
1. Install from: https://github.com/QwenLM/Qwen-CLI
2. Configure API credentials
3. Verify with: qwen --version
                """,
                config_files=[".qwen/config.json"],
                environment_vars=["QWEN_API_KEY"],
            ),

            "codex": ToolConfig(
                name="OpenAI Codex CLI",
                command="openai",
                check_args=["--version"],
                install_command="pip install openai[cli]",
                install_instructions="""
Install OpenAI Codex CLI:
1. Run: pip install openai[cli]
2. Set API key: export OPENAI_API_KEY=your_key
3. Verify with: openai --version
                """,
                config_files=[".openai/config.json"],
                environment_vars=["OPENAI_API_KEY"],
            ),
        }

    def check_tool_installation(self, tool_config: ToolConfig) -> ToolStatus:
        """Check if a tool is installed and get its version."""
        status = ToolStatus()

        try:
            # Check if command exists
            if not shutil.which(tool_config.command):
                return status

            # Run version check
            result = subprocess.run(
                [tool_config.command, *tool_config.check_args],
                check=False, capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                status.installed = True
                # Extract version if available
                import re
                version_match = re.search(tool_config.version_regex, result.stdout + result.stderr)
                if version_match:
                    status.version = version_match.group(1)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass

        return status

    def check_tool_configuration(self, tool_config: ToolConfig, status: ToolStatus) -> None:
        """Check if a tool is properly configured."""
        if not status.installed:
            return

        # Check config files
        for config_file in tool_config.config_files:
            config_path = self.project_root / config_file
            home_config_path = self.home_dir / config_file

            if not config_path.exists() and not home_config_path.exists():
                status.missing_files.append(config_file)

        # Check environment variables
        for env_var in tool_config.environment_vars:
            if not os.getenv(env_var):
                status.missing_env_vars.append(env_var)

        # Tool is configured if no missing files or env vars
        status.configured = (len(status.missing_files) == 0 and
                           len(status.missing_env_vars) == 0)

    def validate_all_tools(self) -> dict[str, ToolStatus]:
        """Validate all configured tools."""
        results = {}

        for tool_name, tool_config in self.tools.items():
            status = self.check_tool_installation(tool_config)
            self.check_tool_configuration(tool_config, status)
            results[tool_name] = status

        return results

    def create_config_templates(self) -> None:
        """Create configuration file templates for missing tools."""
        # Claude Code configuration
        claude_dir = self.project_root / ".claude"
        if not claude_dir.exists():
            claude_dir.mkdir(exist_ok=True)

        claude_settings = claude_dir / "settings.json"
        if not claude_settings.exists():
            settings_template = {
                "mcp": {
                    "servers": {
                        "zen-mcp-server": {
                            "command": "python",
                            "args": ["-m", "zen_mcp_server"],
                            "env": {},
                        },
                    },
                },
                "tools": {
                    "enabled": ["mcp__zen__chat", "mcp__zen__debug", "mcp__zen__analyze"],
                    "disabled": [],
                },
            }

            with open(claude_settings, "w") as f:
                json.dump(settings_template, f, indent=2)

        # GitHub Copilot configuration
        github_dir = self.project_root / ".github"
        if not github_dir.exists():
            github_dir.mkdir(exist_ok=True)

        copilot_config = github_dir / "copilot.yml"
        if not copilot_config.exists():
            copilot_template = """# GitHub Copilot Configuration
suggestions:
  enabled: true
  languages:
    python: true
    javascript: true
    typescript: true
    markdown: true

# Exclude patterns
exclude:
  - "*.log"
  - "*.env*"
  - "**/node_modules/**"
  - "**/.venv/**"
"""
            with open(copilot_config, "w") as f:
                f.write(copilot_template)

    def generate_report(self, results: dict[str, ToolStatus], quiet: bool = False) -> str:
        """Generate a validation report."""
        if quiet:
            # Just return summary counts
            installed_count = sum(1 for status in results.values() if status.installed)
            configured_count = sum(1 for status in results.values() if status.configured)
            return f"AI Tools: {installed_count}/{len(results)} installed, {configured_count}/{len(results)} configured"

        report = ["🤖 AI Coding Tools Validation Report", "=" * 50]

        for tool_name, status in results.items():
            tool_config = self.tools[tool_name]

            if status.installed:
                version_info = f" (v{status.version})" if status.version else ""
                status_icon = "✅" if status.configured else "⚠️"
                report.append(f"{status_icon} {tool_config.name}{version_info}")

                if not status.configured:
                    if status.missing_files:
                        report.append(f"   Missing files: {', '.join(status.missing_files)}")
                    if status.missing_env_vars:
                        report.append(f"   Missing env vars: {', '.join(status.missing_env_vars)}")
            else:
                report.append(f"❌ {tool_config.name} - Not installed")
                report.append(f"   {tool_config.install_instructions.strip()}")

            report.append("")

        return "\n".join(report)

    def install_missing_tools(self, results: dict[str, ToolStatus]) -> None:
        """Attempt to install missing tools with available install commands."""
        for tool_name, status in results.items():
            if not status.installed:
                tool_config = self.tools[tool_name]
                if tool_config.install_command:
                    print(f"Installing {tool_config.name}...")
                    try:
                        subprocess.run(
                            tool_config.install_command.split(),
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        print(f"✅ {tool_config.name} installed successfully")
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Failed to install {tool_config.name}: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate AI coding tools for VS Code")
    parser.add_argument("--install-missing", action="store_true",
                       help="Attempt to install missing tools")
    parser.add_argument("--quiet", action="store_true",
                       help="Output minimal summary only")
    parser.add_argument("--create-templates", action="store_true",
                       help="Create configuration file templates")

    args = parser.parse_args()

    # Find project root
    current_dir = Path.cwd()
    project_root = current_dir

    # Look for common project indicators
    for parent in [current_dir, *list(current_dir.parents)]:
        if any((parent / indicator).exists() for indicator in
               [".git", "pyproject.toml", "package.json", ".vscode"]):
            project_root = parent
            break

    validator = AIToolsValidator(project_root)

    # Create config templates if requested
    if args.create_templates:
        validator.create_config_templates()
        if not args.quiet:
            print("✅ Configuration templates created")

    # Validate tools
    results = validator.validate_all_tools()

    # Install missing tools if requested
    if args.install_missing:
        validator.install_missing_tools(results)
        # Re-validate after installation
        results = validator.validate_all_tools()

    # Generate and print report
    report = validator.generate_report(results, args.quiet)
    print(report)

    # Exit with error code if tools are missing/misconfigured
    installed_count = sum(1 for status in results.values() if status.installed)
    configured_count = sum(1 for status in results.values() if status.configured)

    if installed_count == 0:
        sys.exit(2)  # No tools installed
    elif configured_count < installed_count:
        sys.exit(1)  # Some tools not configured
    else:
        sys.exit(0)  # All good


if __name__ == "__main__":
    main()
