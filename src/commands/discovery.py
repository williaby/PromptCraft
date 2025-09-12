"""
Commands Discovery System

Intelligent discovery system for Claude Code slash commands with hybrid approach:
Project-level (.claude/commands/) -> User-level (~/.claude/commands/) fallback.
"""

from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Any

from src.utils.datetime_compat import utc_now
from src.utils.logging_mixin import LoggerMixin


logger = logging.getLogger(__name__)


@dataclass
class CommandDefinition:
    """Definition of a Claude Code slash command."""

    command_id: str
    name: str
    description: str
    file_path: Path
    source_type: str  # 'project', 'user', 'built-in'
    content: str | None = None
    version: str | None = None
    category: str | None = None
    parameters: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    last_updated: datetime | None = None


class CommandsDiscoverySystem(LoggerMixin):
    """Discovery system for Claude Code slash commands with project-first, user-fallback approach."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__()
        self.project_root = project_root or Path.cwd()
        self.project_commands_path = self.project_root / ".claude" / "commands"
        self.user_commands_path = Path.home() / ".claude" / "commands"

        # Cache for discovered commands
        self._commands_cache: dict[str, CommandDefinition] = {}
        self._cache_timestamp: datetime | None = None
        self._cache_ttl_seconds = 300  # 5 minutes

        # Command categories for organization
        self.command_categories = {
            "quality": ["quality-", "lint", "format"],
            "testing": ["test", "validate"],
            "security": ["security", "audit"],
            "workflow": ["workflow", "git", "deploy"],
            "creation": ["creation", "create", "generate"],
            "meta": ["meta-", "help", "list"],
        }

        self.logger.info(
            f"Commands discovery initialized - Project: {self.project_commands_path}, User: {self.user_commands_path}",
        )

    def get_available_commands(self, refresh_cache: bool = False) -> list[str]:
        """Get list of available command IDs."""
        if refresh_cache or self._should_refresh_cache():
            self._refresh_commands_cache()

        return list(self._commands_cache.keys())

    def get_commands_by_category(self, category: str) -> list[CommandDefinition]:
        """Get commands filtered by category."""
        if self._should_refresh_cache():
            self._refresh_commands_cache()

        category_commands = []
        category_prefixes = self.command_categories.get(category.lower(), [])

        for command in self._commands_cache.values():
            if any(command.command_id.startswith(prefix) for prefix in category_prefixes):
                command.category = category
                category_commands.append(command)

        return category_commands

    def get_command(self, command_id: str) -> CommandDefinition | None:
        """Get a specific command definition with cascade loading."""
        if self._should_refresh_cache():
            self._refresh_commands_cache()

        return self._commands_cache.get(command_id)

    def get_command_content(self, command_id: str) -> str | None:
        """Get the content of a specific command."""
        command = self.get_command(command_id)
        if not command:
            return None

        if command.content is None:
            # Load content if not cached
            if command.source_type == "built-in":
                # Built-in commands should have content defined when created
                # If they don't, it's an error in the built-in command definition
                self.logger.error(f"Built-in command {command_id} was created without content")
                return None

            try:
                command.content = command.file_path.read_text(encoding="utf-8")
                # Parse additional metadata from content
                self._parse_command_metadata(command)
            except Exception as e:
                self.logger.error(f"Failed to load content for {command_id}: {e}")
                return None

        return command.content

    def discover_command(self, command_id: str) -> CommandDefinition | None:
        """Discover a specific command using cascade loading."""
        search_strategies = [
            ("project", self._search_project_commands),
            ("user", self._search_user_commands),
            ("built-in", self._search_builtin_commands),
        ]

        for source_type, search_func in search_strategies:
            try:
                command = search_func(command_id)
                if command:
                    command.source_type = source_type
                    self.logger.info(f"Found command '{command_id}' from {source_type} source")
                    return command
            except Exception as e:
                self.logger.warning(f"Error searching {source_type} commands for {command_id}: {e}")
                continue

        self.logger.warning(f"Command '{command_id}' not found in any source")
        return None

    def search_commands(self, query: str) -> list[CommandDefinition]:
        """Search commands by name, description, or content."""
        if self._should_refresh_cache():
            self._refresh_commands_cache()

        query = query.lower()
        matching_commands = []

        for command in self._commands_cache.values():
            if (
                query in command.command_id.lower()
                or query in command.name.lower()
                or query in command.description.lower()
            ):
                matching_commands.append(command)

        return matching_commands

    def _search_project_commands(self, command_id: str) -> CommandDefinition | None:
        """Search for command in project-level directory."""
        if not self.project_commands_path.exists():
            return None

        command_file = self.project_commands_path / f"{command_id}.md"
        if command_file.exists():
            return self._create_command_definition(command_id, command_file, "project")

        return None

    def _search_user_commands(self, command_id: str) -> CommandDefinition | None:
        """Search for command in user-level directory."""
        if not self.user_commands_path.exists():
            return None

        command_file = self.user_commands_path / f"{command_id}.md"
        if command_file.exists():
            return self._create_command_definition(command_id, command_file, "user")

        return None

    def _search_builtin_commands(self, command_id: str) -> CommandDefinition | None:
        """Search for built-in commands (placeholder for future implementation)."""
        # Built-in commands could be defined here for essential functionality
        builtin_commands = {
            "help": {
                "name": "Help",
                "description": "Show available commands and usage",
                "content": "# Help Command\n\nBuilt-in help command for listing available slash commands.",
            },
        }

        if command_id in builtin_commands:
            builtin_info = builtin_commands[command_id]
            return CommandDefinition(
                command_id=command_id,
                name=builtin_info["name"],
                description=builtin_info["description"],
                file_path=Path("built-in"),
                source_type="built-in",
                content=builtin_info["content"],
                last_updated=utc_now(),
            )

        return None

    def _create_command_definition(self, command_id: str, file_path: Path, source_type: str) -> CommandDefinition:
        """Create a CommandDefinition from a file path."""
        try:
            # Extract basic metadata from filename and path
            name = command_id.replace("-", " ").replace("_", " ").title()
            description = f"{name} command"
            version = None
            category = None

            # Try to extract metadata from file content
            try:
                content = file_path.read_text(encoding="utf-8")

                # Parse YAML frontmatter if present
                if content.startswith("---\n"):
                    try:
                        import yaml

                        frontmatter_end = content.find("\n---\n", 4)
                        if frontmatter_end != -1:
                            frontmatter = yaml.safe_load(content[4:frontmatter_end])
                            name = frontmatter.get("title", name)
                            description = frontmatter.get("description", description)
                            version = frontmatter.get("version", version)
                            category = frontmatter.get("category", category)
                    except Exception as e:
                        self.logger.debug(f"Failed to parse frontmatter for {command_id}: {e}")

                # Extract description from first heading or paragraph if no frontmatter
                if description == f"{name} command":
                    # Look for first paragraph or description after frontmatter
                    lines = content.split("\n")
                    in_frontmatter = content.startswith("---\n")
                    frontmatter_count = 0

                    for line in lines[:15]:  # Check first 15 lines
                        line = line.strip()

                        # Skip frontmatter section
                        if in_frontmatter:
                            if line == "---":
                                frontmatter_count += 1
                                if frontmatter_count >= 2:  # Found closing ---
                                    in_frontmatter = False
                            continue

                        # Look for first meaningful content line
                        if line and not line.startswith("#") and not line.startswith("---"):
                            description = line[:100] + ("..." if len(line) > 100 else "")
                            break

            except Exception as e:
                self.logger.debug(f"Failed to read content for metadata extraction: {e}")
                content = None

            command_def = CommandDefinition(
                command_id=command_id,
                name=name,
                description=description,
                file_path=file_path,
                source_type=source_type,
                content=content,
                version=version,
                category=category,
                last_updated=datetime.fromtimestamp(file_path.stat().st_mtime),
            )

            # Parse additional metadata from content
            if content:
                self._parse_command_metadata(command_def)

            return command_def

        except Exception as e:
            self.logger.error(f"Failed to create command definition for {command_id}: {e}")
            raise

    def _parse_command_metadata(self, command: CommandDefinition) -> None:
        """Parse additional metadata from command content."""
        if not command.content:
            return

        # Extract parameters from content (handle multiple sections)
        param_pattern = r"(?:Parameters?|Args?|Arguments?):\s*\n((?:\s*[-*]\s*.+\n)*)"
        command.parameters = []
        for param_match in re.finditer(param_pattern, command.content, re.IGNORECASE | re.MULTILINE):
            param_text = param_match.group(1)
            params = re.findall(r"[-*]\s*([^\n]+)", param_text)
            command.parameters.extend(params)

        # Extract examples from content
        example_pattern = r"(?:Examples?|Usage):\s*\n((?:\s*```[\s\S]*?```\s*\n|(?:\s*[-*]?\s*.+\n)*)*)"
        example_match = re.search(example_pattern, command.content, re.IGNORECASE | re.MULTILINE)
        if example_match:
            example_text = example_match.group(1)
            # Extract code blocks or list items as examples
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", example_text, re.DOTALL)
            list_items = re.findall(r"[-*]\s*([^\n]+)", example_text)
            command.examples = code_blocks + list_items

        # Auto-categorize if not already set
        if not command.category:
            for category, prefixes in self.command_categories.items():
                if any(command.command_id.startswith(prefix) for prefix in prefixes):
                    command.category = category
                    break
            else:
                command.category = "general"

    def _refresh_commands_cache(self) -> None:
        """Refresh the commands cache by scanning all available sources."""
        self.logger.debug("Refreshing commands cache")
        self._commands_cache.clear()

        # Collect all command IDs from all sources
        all_command_ids = set()

        # Scan project commands
        if self.project_commands_path.exists():
            for file_path in self.project_commands_path.glob("*.md"):
                if file_path.stem.startswith("_"):  # Skip README and other meta files
                    continue
                command_id = file_path.stem
                all_command_ids.add(command_id)

        # Scan user commands
        if self.user_commands_path.exists():
            for file_path in self.user_commands_path.glob("*.md"):
                if file_path.stem.startswith("_"):  # Skip README and other meta files
                    continue
                command_id = file_path.stem
                all_command_ids.add(command_id)

        # Add built-in command IDs
        builtin_commands = {
            "help": {
                "name": "Help",
                "description": "Show available commands and usage",
                "content": "# Help Command\n\nBuilt-in help command for listing available slash commands.",
            },
        }
        all_command_ids.update(builtin_commands.keys())

        # Discover each command (project-first, user-fallback, then built-in)
        for command_id in all_command_ids:
            command = self.discover_command(command_id)
            if command:
                self._commands_cache[command_id] = command

        self._cache_timestamp = utc_now()
        self.logger.info(f"Refreshed commands cache with {len(self._commands_cache)} commands")

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed."""
        if self._cache_timestamp is None:
            return True

        age_seconds = (utc_now() - self._cache_timestamp).total_seconds()
        return age_seconds > self._cache_ttl_seconds

    def get_discovery_status(self) -> dict[str, Any]:
        """Get status information about commands discovery."""
        if self._should_refresh_cache():
            self._refresh_commands_cache()

        # Calculate statistics
        commands_by_source = {"project": 0, "user": 0, "built-in": 0}
        commands_by_category: dict[str, int] = {}

        for command in self._commands_cache.values():
            commands_by_source[command.source_type] = commands_by_source.get(command.source_type, 0) + 1
            category = command.category or "uncategorized"
            commands_by_category[category] = commands_by_category.get(category, 0) + 1

        return {
            "project_commands_path": str(self.project_commands_path),
            "user_commands_path": str(self.user_commands_path),
            "project_commands_available": self.project_commands_path.exists(),
            "user_commands_available": self.user_commands_path.exists(),
            "cached_commands_count": len(self._commands_cache),
            "cache_age_seconds": (
                (utc_now() - self._cache_timestamp).total_seconds() if self._cache_timestamp else None
            ),
            "available_commands": self.get_available_commands(),
            "commands_by_source": commands_by_source,
            "commands_by_category": commands_by_category,
            "supported_categories": list(self.command_categories.keys()),
        }


class CommandsManager(LoggerMixin):
    """High-level manager for Claude Code slash commands."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__()
        self.discovery_system = CommandsDiscoverySystem(project_root)

    def execute_command(self, command_id: str, parameters: list[str] | None = None) -> dict[str, Any]:
        """Execute a command and return results (placeholder for future implementation)."""
        command = self.discovery_system.get_command(command_id)
        if not command:
            return {
                "success": False,
                "error": f"Command '{command_id}' not found",
                "available_commands": self.discovery_system.get_available_commands()[:10],
            }

        # TODO: Implement actual command execution logic
        # This would involve parsing the command content and executing the appropriate actions
        return {
            "success": True,
            "command_id": command_id,
            "message": f"Command '{command.name}' found but execution not yet implemented",
            "source": command.source_type,
            "parameters": parameters or [],
        }

    def get_help(self, command_id: str | None = None) -> str:
        """Get help information for commands."""
        if command_id:
            command = self.discovery_system.get_command(command_id)
            if not command:
                return f"Command '{command_id}' not found"

            content = self.discovery_system.get_command_content(command_id)
            return content or f"No content available for command '{command_id}'"
        # Return list of all available commands
        commands = self.discovery_system.get_available_commands()
        status = self.discovery_system.get_discovery_status()

        help_text = f"Available Commands ({len(commands)}):\n\n"

        # Group by category
        for category in status["supported_categories"]:
            category_commands = self.discovery_system.get_commands_by_category(category)
            if category_commands:
                help_text += f"## {category.title()} Commands:\n"
                for cmd in category_commands:
                    help_text += f"- /{cmd.command_id}: {cmd.description}\n"
                help_text += "\n"

        return help_text


__all__ = [
    "CommandDefinition",
    "CommandsDiscoverySystem",
    "CommandsManager",
]
