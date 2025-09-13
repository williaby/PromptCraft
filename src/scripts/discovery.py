"""
Scripts Discovery System

Intelligent discovery system for automation scripts with hybrid approach:
Project-level (.claude/scripts/) -> User-level (~/.claude/scripts/) fallback.
"""

from dataclasses import dataclass, field
from datetime import datetime
from src.utils.datetime_compat import UTC
import logging
import os
from pathlib import Path
from typing import Any

from src.utils.datetime_compat import utc_now
from src.utils.logging_mixin import LoggerMixin


logger = logging.getLogger(__name__)


@dataclass
class ScriptDefinition:
    """Definition of an automation script."""

    script_id: str
    name: str
    description: str
    file_path: Path
    source_type: str  # 'project', 'user', 'built-in'
    script_type: str  # 'shell', 'python', 'javascript', 'other'
    is_executable: bool = False
    content: str | None = None
    version: str | None = None
    category: str | None = None
    dependencies: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)
    last_updated: datetime | None = None


class ScriptsDiscoverySystem(LoggerMixin):
    """Discovery system for automation scripts with project-first, user-fallback approach."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__()
        self.project_root = project_root or Path.cwd()
        self.project_scripts_path = self.project_root / ".claude" / "scripts"
        self.user_scripts_path = Path.home() / ".claude" / "scripts"

        # Cache for discovered scripts
        self._scripts_cache: dict[str, ScriptDefinition] = {}
        self._cache_timestamp: datetime | None = None
        self._cache_ttl_seconds = 300  # 5 minutes

        # Script categories for organization
        self.script_categories = {
            "setup": ["setup", "install", "config", "init"],
            "validation": ["validate", "check", "verify", "test"],
            "deployment": ["deploy", "build", "release"],
            "maintenance": ["update", "clean", "backup", "migrate"],
            "analysis": ["analyze", "report", "audit"],
            "mcp": ["mcp", "server", "client"],
            "development": ["dev", "debug", "tool"],
        }

        # Supported script types
        self.script_extensions = {
            ".py": "python",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".js": "javascript",
            ".mjs": "javascript",
            ".ts": "typescript",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
        }

        self.logger.info(
            "Scripts discovery initialized - Project: %s, User: %s",
            self.project_scripts_path,
            self.user_scripts_path,
        )

    def get_available_scripts(self, refresh_cache: bool = False) -> list[str]:
        """Get list of available script IDs."""
        if refresh_cache or self._should_refresh_cache():
            self._refresh_scripts_cache()

        return list(self._scripts_cache.keys())

    def get_scripts_by_category(self, category: str) -> list[ScriptDefinition]:
        """Get scripts filtered by category."""
        if self._should_refresh_cache():
            self._refresh_scripts_cache()

        category_scripts = []
        category_keywords = self.script_categories.get(category.lower(), [])

        for script in self._scripts_cache.values():
            if script.category == category or any(keyword in script.script_id.lower() for keyword in category_keywords):
                script.category = category
                category_scripts.append(script)

        return category_scripts

    def get_scripts_by_type(self, script_type: str) -> list[ScriptDefinition]:
        """Get scripts filtered by script type (python, shell, etc.)."""
        if self._should_refresh_cache():
            self._refresh_scripts_cache()

        return [script for script in self._scripts_cache.values() if script.script_type == script_type]

    def get_executable_scripts(self) -> list[ScriptDefinition]:
        """Get only executable scripts."""
        if self._should_refresh_cache():
            self._refresh_scripts_cache()

        return [script for script in self._scripts_cache.values() if script.is_executable]

    def get_script(self, script_id: str) -> ScriptDefinition | None:
        """Get a specific script definition with cascade loading."""
        if self._should_refresh_cache():
            self._refresh_scripts_cache()

        return self._scripts_cache.get(script_id)

    def get_script_content(self, script_id: str) -> str | None:
        """Get the content of a specific script."""
        script = self.get_script(script_id)
        if not script:
            return None

        if script.content is None:
            # Load content if not cached
            try:
                script.content = script.file_path.read_text(encoding="utf-8")
                # Parse additional metadata from content
                self._parse_script_metadata(script)
            except Exception as e:
                self.logger.error("Failed to load content for %s: %s", script_id, e)
                return None

        return script.content

    def discover_script(self, script_id: str) -> ScriptDefinition | None:
        """Discover a specific script using cascade loading."""
        search_strategies = [
            ("project", self._search_project_scripts),
            ("user", self._search_user_scripts),
            ("built-in", self._search_builtin_scripts),
        ]

        for source_type, search_func in search_strategies:
            try:
                script = search_func(script_id)
                if script:
                    script.source_type = source_type
                    self.logger.info("Found script '%s' from %s source", script_id, source_type)
                    return script
            except Exception as e:
                self.logger.warning("Error searching %s scripts for %s: %s", source_type, script_id, e)
                continue

        self.logger.warning("Script '%s' not found in any source", script_id)
        return None

    def search_scripts(self, query: str) -> list[ScriptDefinition]:
        """Search scripts by name, description, or content."""
        if self._should_refresh_cache():
            self._refresh_scripts_cache()

        query = query.lower()
        matching_scripts = []

        for script in self._scripts_cache.values():
            if query in script.script_id.lower() or query in script.name.lower() or query in script.description.lower():
                matching_scripts.append(script)

        return matching_scripts

    def _search_project_scripts(self, script_id: str) -> ScriptDefinition | None:
        """Search for script in project-level directory."""
        if not self.project_scripts_path.exists():
            return None

        # Try different extensions
        for ext, _script_type in self.script_extensions.items():
            script_file = self.project_scripts_path / f"{script_id}{ext}"
            if script_file.exists():
                return self._create_script_definition(script_id, script_file, "project")

        # Try exact filename match
        script_file = self.project_scripts_path / script_id
        if script_file.exists():
            return self._create_script_definition(script_id, script_file, "project")

        return None

    def _search_user_scripts(self, script_id: str) -> ScriptDefinition | None:
        """Search for script in user-level directory."""
        if not self.user_scripts_path.exists():
            return None

        # Try different extensions
        for ext, _script_type in self.script_extensions.items():
            script_file = self.user_scripts_path / f"{script_id}{ext}"
            if script_file.exists():
                return self._create_script_definition(script_id, script_file, "user")

        # Try exact filename match
        script_file = self.user_scripts_path / script_id
        if script_file.exists():
            return self._create_script_definition(script_id, script_file, "user")

        return None

    def _search_builtin_scripts(self, script_id: str) -> ScriptDefinition | None:
        """Search for built-in scripts (placeholder for future implementation)."""
        # Built-in scripts could be defined here for essential functionality
        return None

    def _create_script_definition(self, script_id: str, file_path: Path, source_type: str) -> ScriptDefinition:
        """Create a ScriptDefinition from a file path."""
        try:
            # Determine script type from extension
            suffix = file_path.suffix.lower()
            script_type = self.script_extensions.get(suffix, "other")

            # Check if executable
            is_executable = os.access(file_path, os.X_OK)

            # Extract basic metadata
            name = script_id.replace("-", " ").replace("_", " ").title()
            description = f"{name} script"

            # Try to extract metadata from file content
            content = None
            version = None
            category = None

            try:
                content = file_path.read_text(encoding="utf-8")

                # Extract description from comments at top of file
                lines = content.split("\n")[:20]  # Check first 20 lines
                description_found = False

                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith(("#", '"""', "'''")):
                        # Skip shebang lines
                        if stripped_line.startswith("#!"):
                            continue

                        # Extract comment content
                        comment_text = stripped_line.lstrip("#\"'").strip()
                        if comment_text and not description_found and len(comment_text) > 10:
                            description = comment_text[:100] + ("..." if len(comment_text) > 100 else "")
                            description_found = True

                        # Look for version information
                        if "version" in line.lower():
                            version_match = line.split(":")
                            if len(version_match) > 1:
                                version = version_match[1].strip().strip("\"'")

            except Exception as e:
                self.logger.debug("Failed to read content for metadata extraction: %s", e)

            script_def = ScriptDefinition(
                script_id=script_id,
                name=name,
                description=description,
                file_path=file_path,
                source_type=source_type,
                script_type=script_type,
                is_executable=is_executable,
                content=content,
                version=version,
                category=category,
                last_updated=datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC),
            )

            # Parse additional metadata from content
            if content:
                self._parse_script_metadata(script_def)

            return script_def

        except Exception as e:
            self.logger.error("Failed to create script definition for %s: %s", script_id, e)
            raise

    def _parse_script_metadata(self, script: ScriptDefinition) -> None:
        """Parse additional metadata from script content."""
        if not script.content:
            return

        lines = script.content.split("\n")

        # Look for shebang line
        if lines and lines[0].startswith("#!"):
            shebang = lines[0][2:].strip()
            if "python" in shebang:
                script.script_type = "python"
            elif "bash" in shebang or "sh" in shebang:
                script.script_type = "shell"
            elif "node" in shebang:
                script.script_type = "javascript"

        # Extract dependencies and parameters from comments
        in_header = True
        for i, line in enumerate(lines[:50]):  # Check first 50 lines
            stripped_line = line.strip()

            # Stop looking once we hit actual code
            if (
                stripped_line
                and not stripped_line.startswith("#")
                and not stripped_line.startswith('"""')
                and not stripped_line.startswith("'''")
            ):
                if i > 5:  # Allow some initial lines
                    in_header = False
                    break

            if in_header and stripped_line:
                # Look for dependencies
                if "depends:" in stripped_line.lower() or "requires:" in stripped_line.lower():
                    deps_part = stripped_line.split(":", 1)[1] if ":" in stripped_line else ""
                    deps = [dep.strip() for dep in deps_part.replace(",", " ").split() if dep.strip()]
                    script.dependencies.extend(deps)

                # Look for parameters
                if "params:" in line.lower() or "arguments:" in line.lower():
                    params_part = line.split(":", 1)[1] if ":" in line else ""
                    params = [param.strip() for param in params_part.replace(",", " ").split() if param.strip()]
                    script.parameters.extend(params)

        # Auto-categorize if not already set
        if not script.category:
            for category, keywords in self.script_categories.items():
                if any(keyword in script.script_id.lower() for keyword in keywords):
                    script.category = category
                    break
            else:
                script.category = "general"

    def _refresh_scripts_cache(self) -> None:
        """Refresh the scripts cache by scanning all available sources."""
        self.logger.debug("Refreshing scripts cache")
        self._scripts_cache.clear()

        # Collect all script files from all sources
        all_script_files = {}

        # Scan project scripts
        if self.project_scripts_path.exists():
            for file_path in self.project_scripts_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith("."):
                    script_id = file_path.stem if file_path.suffix else file_path.name
                    all_script_files[script_id] = file_path

        # Scan user scripts (only if not already found in project)
        if self.user_scripts_path.exists():
            for file_path in self.user_scripts_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith("."):
                    script_id = file_path.stem if file_path.suffix else file_path.name
                    if script_id not in all_script_files:  # Project takes precedence
                        all_script_files[script_id] = file_path

        # Create script definitions for all found files
        for script_id, file_path in all_script_files.items():
            try:
                source_type = "project" if self.project_scripts_path in file_path.parents else "user"
                script = self._create_script_definition(script_id, file_path, source_type)
                self._scripts_cache[script_id] = script
            except Exception as e:
                self.logger.warning("Failed to process script %s: %s", script_id, e)

        self._cache_timestamp = utc_now()
        self.logger.info("Refreshed scripts cache with %s scripts", len(self._scripts_cache))

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed."""
        if self._cache_timestamp is None:
            return True

        age_seconds = (utc_now() - self._cache_timestamp).total_seconds()
        return age_seconds > self._cache_ttl_seconds

    def get_discovery_status(self) -> dict[str, Any]:
        """Get status information about scripts discovery."""
        if self._should_refresh_cache():
            self._refresh_scripts_cache()

        # Calculate statistics
        scripts_by_source = {"project": 0, "user": 0, "built-in": 0}
        scripts_by_type: dict[str, int] = {}
        scripts_by_category: dict[str, int] = {}
        executable_count = 0

        for script in self._scripts_cache.values():
            scripts_by_source[script.source_type] = scripts_by_source.get(script.source_type, 0) + 1
            scripts_by_type[script.script_type] = scripts_by_type.get(script.script_type, 0) + 1
            category = script.category or "uncategorized"
            scripts_by_category[category] = scripts_by_category.get(category, 0) + 1
            if script.is_executable:
                executable_count += 1

        return {
            "project_scripts_path": str(self.project_scripts_path),
            "user_scripts_path": str(self.user_scripts_path),
            "project_scripts_available": self.project_scripts_path.exists(),
            "user_scripts_available": self.user_scripts_path.exists(),
            "cached_scripts_count": len(self._scripts_cache),
            "executable_scripts_count": executable_count,
            "cache_age_seconds": (
                (utc_now() - self._cache_timestamp).total_seconds() if self._cache_timestamp else None
            ),
            "available_scripts": self.get_available_scripts(),
            "scripts_by_source": scripts_by_source,
            "scripts_by_type": scripts_by_type,
            "scripts_by_category": scripts_by_category,
            "supported_categories": list(self.script_categories.keys()),
            "supported_types": list(self.script_extensions.values()),
        }


class ScriptsManager(LoggerMixin):
    """High-level manager for automation scripts."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__()
        self.discovery_system = ScriptsDiscoverySystem(project_root)

    def execute_script(
        self,
        script_id: str,
        parameters: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Execute a script and return results (placeholder - security considerations apply)."""
        script = self.discovery_system.get_script(script_id)
        if not script:
            return {
                "success": False,
                "error": f"Script '{script_id}' not found",
                "available_scripts": self.discovery_system.get_available_scripts()[:10],
            }

        if dry_run:
            return {
                "success": True,
                "script_id": script_id,
                "message": f"Script '{script.name}' found (dry-run mode - not executed)",
                "source": script.source_type,
                "type": script.script_type,
                "executable": script.is_executable,
                "parameters": parameters or [],
            }
        # TODO: Implement actual script execution with proper security measures
        # This would require:
        # 1. Security validation (whitelist, sandboxing)
        # 2. Parameter validation and sanitization
        # 3. Execution environment setup
        # 4. Output capture and logging
        # 5. Error handling and cleanup
        return {
            "success": False,
            "error": "Script execution not implemented for security reasons",
            "recommendation": "Use dry_run=True to validate script availability",
        }

    def get_maintenance_scripts(self) -> list[ScriptDefinition]:
        """Get scripts categorized as maintenance."""
        return self.discovery_system.get_scripts_by_category("maintenance")

    def get_setup_scripts(self) -> list[ScriptDefinition]:
        """Get scripts categorized as setup/installation."""
        return self.discovery_system.get_scripts_by_category("setup")

    def get_validation_scripts(self) -> list[ScriptDefinition]:
        """Get scripts categorized as validation/testing."""
        return self.discovery_system.get_scripts_by_category("validation")


__all__ = [
    "ScriptDefinition",
    "ScriptsDiscoverySystem",
    "ScriptsManager",
]
