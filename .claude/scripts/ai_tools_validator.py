#!/usr/bin/env python3
"""
Universal AI Tools Validator for VS Code Development Environment

This script checks for the presence and configuration of AI coding CLI tools
for any project, providing installation and setup guidance.

Supported Tools:
- Claude Code (Anthropic)
- OpenAI Codex CLI
- Gemini CLI (Google)
- Qwen Code CLI
- GitHub Copilot CLI

Usage:
    python ~/.claude/scripts/ai_tools_validator.py [--install-missing] [--quiet] [--setup-project]
"""

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


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


class UniversalAIToolsValidator:
    """Universal validator for AI coding CLI tools."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.home_dir = Path.home()
        self.project_type = self._detect_project_type()

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
                config_files=[".claude/settings.json"],
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

    def _detect_project_type(self) -> dict[str, any]:
        """Detect project type and characteristics."""
        project_info = {
            "type": "unknown",
            "languages": [],
            "frameworks": [],
            "package_managers": [],
        }

        # Check for common project files
        if (self.project_root / "pyproject.toml").exists() or (self.project_root / "setup.py").exists():
            project_info["type"] = "python"
            project_info["languages"].append("python")
            if (self.project_root / "poetry.lock").exists():
                project_info["package_managers"].append("poetry")
            elif (self.project_root / "requirements.txt").exists():
                project_info["package_managers"].append("pip")

        if (self.project_root / "package.json").exists():
            project_info["languages"].append("javascript")
            project_info["package_managers"].append("npm")

        if (self.project_root / "Cargo.toml").exists():
            project_info["type"] = "rust"
            project_info["languages"].append("rust")
            project_info["package_managers"].append("cargo")

        if (self.project_root / "go.mod").exists():
            project_info["type"] = "go"
            project_info["languages"].append("go")

        # Check for common frameworks
        if (self.project_root / "pyproject.toml").exists():
            try:
                import tomllib

                with Path(self.project_root / "pyproject.toml").open("rb") as f:
                    pyproject = tomllib.load(f)
                    deps = pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})
                    if "fastapi" in deps:
                        project_info["frameworks"].append("fastapi")
                    if "django" in deps:
                        project_info["frameworks"].append("django")
                    if "flask" in deps:
                        project_info["frameworks"].append("flask")
                    if "gradio" in deps:
                        project_info["frameworks"].append("gradio")
            except Exception:
                pass

        return project_info

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
                check=False,
                capture_output=True,
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
        status.configured = len(status.missing_files) == 0 and len(status.missing_env_vars) == 0

    def create_generic_config_templates(self) -> None:
        """Create generic configuration file templates."""
        # Claude Code configuration
        claude_dir = self.project_root / ".claude"
        if not claude_dir.exists():
            claude_dir.mkdir(exist_ok=True)

        claude_settings = claude_dir / "settings.json"
        if not claude_settings.exists():
            settings_template = {
                "project": {
                    "name": self.project_root.name,
                    "type": self.project_type["type"],
                    "languages": self.project_type["languages"],
                },
                "tools": {
                    "enabled": ["basic_commands"],
                    "disabled": [],
                },
            }

            with Path(claude_settings).open("w") as f:
                json.dump(settings_template, f, indent=2)

        # GitHub Copilot configuration
        github_dir = self.project_root / ".github"
        if not github_dir.exists():
            github_dir.mkdir(exist_ok=True)

        copilot_config = github_dir / "copilot.yml"
        if not copilot_config.exists():
            languages = self.project_type["languages"]
            lang_config = dict.fromkeys(languages, True) if languages else {"python": True, "javascript": True}

            copilot_template = f"""# GitHub Copilot Configuration
suggestions:
  enabled: true
  languages:
{chr(10).join(f'    {lang}: true' for lang in lang_config)}

# Exclude patterns
exclude:
  - "*.log"
  - "*.env*"
  - "**/node_modules/**"
  - "**/.venv/**"
  - "**/__pycache__/**"
"""
            with Path(copilot_config).open("w") as f:
                f.write(copilot_template)

        # Gemini CLI configuration
        gemini_dir = self.project_root / ".gemini"
        if not gemini_dir.exists():
            gemini_dir.mkdir(exist_ok=True)

        gemini_config = gemini_dir / "config.json"
        if not gemini_config.exists():
            gemini_template = {
                "project": self.project_root.name,
                "settings": {
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
                "project_context": {
                    "type": self.project_type["type"],
                    "languages": self.project_type["languages"],
                    "frameworks": self.project_type["frameworks"],
                },
                "exclusions": {
                    "files": ["*.env*", "*.log", "**/node_modules/**", "**/.venv/**", "**/__pycache__/**"],
                    "directories": [".mypy_cache", ".pytest_cache", "build", "dist"],
                },
            }

            with Path(gemini_config).open("w") as f:
                json.dump(gemini_template, f, indent=2)

        # Similar templates for other tools...
        self._create_qwen_config()
        self._create_openai_config()

    def _create_qwen_config(self) -> None:
        """Create Qwen configuration."""
        qwen_dir = self.project_root / ".qwen"
        if not qwen_dir.exists():
            qwen_dir.mkdir(exist_ok=True)

        qwen_config = qwen_dir / "config.json"
        if not qwen_config.exists():
            template = {
                "project": self.project_root.name,
                "model": "qwen-coder-plus",
                "project_context": {
                    "type": self.project_type["type"],
                    "languages": self.project_type["languages"],
                    "frameworks": self.project_type["frameworks"],
                },
                "ignore_patterns": ["*.env*", "*.log", "__pycache__", ".venv", "node_modules"],
            }

            with Path(qwen_config).open("w") as f:
                json.dump(template, f, indent=2)

    def _create_openai_config(self) -> None:
        """Create OpenAI configuration."""
        openai_dir = self.project_root / ".openai"
        if not openai_dir.exists():
            openai_dir.mkdir(exist_ok=True)

        openai_config = openai_dir / "config.json"
        if not openai_config.exists():
            template = {
                "project": self.project_root.name,
                "models": {"code": "gpt-4-turbo", "chat": "gpt-4"},
                "project_context": {
                    "type": self.project_type["type"],
                    "languages": self.project_type["languages"],
                    "frameworks": self.project_type["frameworks"],
                },
                "exclude_patterns": ["*.env*", "*.log", "**/node_modules/**", "**/.venv/**", "**/__pycache__/**"],
            }

            with Path(openai_config).open("w") as f:
                json.dump(template, f, indent=2)

    def setup_vscode_integration(self) -> bool:
        """Set up VS Code integration if .vscode directory exists."""
        vscode_dir = self.project_root / ".vscode"
        if not vscode_dir.exists():
            return False

        # Update settings.json
        settings_file = vscode_dir / "settings.json"
        settings = {}

        if settings_file.exists():
            try:
                with Path(settings_file).open() as f:
                    settings = json.load(f)
            except json.JSONDecodeError:
                pass

        # Add AI tools configuration
        if "ai-tools" not in settings:
            settings["ai-tools"] = {
                "validation": {
                    "enabled": True,
                    "checkOnOpen": True,
                    "createTemplates": True,
                    "tools": ["claude", "copilot", "gemini", "qwen", "codex"],
                },
            }

            with Path(settings_file).open("w") as f:
                json.dump(settings, f, indent=2)

        # Update tasks.json
        tasks_file = vscode_dir / "tasks.json"
        tasks = {"version": "2.0.0", "tasks": []}

        if tasks_file.exists():
            try:
                with Path(tasks_file).open() as f:
                    tasks = json.load(f)
            except json.JSONDecodeError:
                pass

        # Add AI tools validation task
        ai_tools_task = {
            "label": "Validate AI Tools",
            "type": "shell",
            "command": "python",
            "args": [str(Path.home() / ".claude" / "scripts" / "ai_tools_validator.py"), "--setup-project"],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "silent",
                "focus": False,
                "panel": "shared",
                "showReuseMessage": False,
                "clear": False,
            },
            "options": {"cwd": "${workspaceFolder}"},
            "problemMatcher": [],
            "runOptions": {"runOn": "folderOpen"},
        }

        # Check if task already exists
        task_exists = any(task.get("label") == "Validate AI Tools" for task in tasks["tasks"])
        if not task_exists:
            tasks["tasks"].append(ai_tools_task)

            with Path(tasks_file).open("w") as f:
                json.dump(tasks, f, indent=2)

        return True

    def validate_all_tools(self) -> dict[str, ToolStatus]:
        """Validate all configured tools."""
        results = {}

        for tool_name, tool_config in self.tools.items():
            status = self.check_tool_installation(tool_config)
            self.check_tool_configuration(tool_config, status)
            results[tool_name] = status

        return results

    def generate_report(self, results: dict[str, ToolStatus], quiet: bool = False) -> str:
        """Generate a validation report."""
        if quiet:
            installed_count = sum(1 for status in results.values() if status.installed)
            configured_count = sum(1 for status in results.values() if status.configured)
            return f"AI Tools: {installed_count}/{len(results)} installed, {configured_count}/{len(results)} configured"

        report = [f"🤖 AI Coding Tools Validation Report - {self.project_root.name}", "=" * 60]
        report.append(f"Project Type: {self.project_type['type'].title()}")
        report.append(f"Languages: {', '.join(self.project_type['languages']) or 'Unknown'}")
        report.append("")

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


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Universal AI coding tools validator")
    parser.add_argument("--install-missing", action="store_true", help="Attempt to install missing tools")
    parser.add_argument("--quiet", action="store_true", help="Output minimal summary only")
    parser.add_argument(
        "--setup-project",
        action="store_true",
        help="Set up project configuration and VS Code integration",
    )

    args = parser.parse_args()

    # Find project root
    current_dir = Path.cwd()
    project_root = current_dir

    # Look for common project indicators
    for parent in [current_dir, *list(current_dir.parents)]:
        if any((parent / indicator).exists() for indicator in [".git", "pyproject.toml", "package.json", ".vscode"]):
            project_root = parent
            break

    validator = UniversalAIToolsValidator(project_root)

    # Setup project if requested
    if args.setup_project:
        validator.create_generic_config_templates()
        vscode_setup = validator.setup_vscode_integration()
        if not args.quiet:
            if vscode_setup:
                pass

    # Validate tools
    results = validator.validate_all_tools()

    # Generate and print report
    validator.generate_report(results, args.quiet)

    # Exit with appropriate code
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
