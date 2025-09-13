"""
Standards Discovery System

Intelligent discovery system for development standards with hybrid approach:
Project-level (.claude/standards/) -> User-level (~/.claude/standards/) fallback.
"""

from dataclasses import dataclass
from datetime import datetime
from src.utils.datetime_compat import UTC
import logging
from pathlib import Path
from typing import Any

from src.utils.datetime_compat import utc_now
from src.utils.logging_mixin import LoggerMixin


logger = logging.getLogger(__name__)


@dataclass
class StandardDefinition:
    """Definition of a development standard."""

    standard_id: str
    name: str
    description: str
    file_path: Path
    source_type: str  # 'project', 'user', 'default'
    content: str | None = None
    version: str | None = None
    last_updated: datetime | None = None


class StandardsDiscoverySystem(LoggerMixin):
    """Discovery system for development standards with project-first, user-fallback approach."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__()
        self.project_root = project_root or Path.cwd()
        self.project_standards_path = self.project_root / ".claude" / "standards"
        self.user_standards_path = Path.home() / ".claude" / "standards"

        # Cache for discovered standards
        self._standards_cache: dict[str, StandardDefinition] = {}
        self._cache_timestamp: datetime | None = None
        self._cache_ttl_seconds = 300  # 5 minutes

        self.logger.info(
            "Standards discovery initialized - Project: %s, User: %s",
            self.project_standards_path,
            self.user_standards_path,
        )

    def get_available_standards(self, refresh_cache: bool = False) -> list[str]:
        """Get list of available standard IDs."""
        if refresh_cache or self._should_refresh_cache():
            self._refresh_standards_cache()

        return list(self._standards_cache.keys())

    def get_standard(self, standard_id: str) -> StandardDefinition | None:
        """Get a specific standard definition with cascade loading."""
        if self._should_refresh_cache():
            self._refresh_standards_cache()

        return self._standards_cache.get(standard_id)

    def get_standard_content(self, standard_id: str) -> str | None:
        """Get the content of a specific standard."""
        standard = self.get_standard(standard_id)
        if not standard:
            return None

        if standard.content is None:
            # Load content if not cached
            try:
                standard.content = standard.file_path.read_text(encoding="utf-8")
            except Exception as e:
                self.logger.error("Failed to load content for %s: %s", standard_id, e)
                return None

        return standard.content

    def discover_standard(self, standard_id: str) -> StandardDefinition | None:
        """Discover a specific standard using cascade loading."""
        search_strategies = [
            ("project", self._search_project_standards),
            ("user", self._search_user_standards),
            ("default", self._search_default_standards),
        ]

        for source_type, search_func in search_strategies:
            try:
                standard = search_func(standard_id)
                if standard:
                    standard.source_type = source_type
                    self.logger.info("Found standard '%s' from %s source", standard_id, source_type)
                    return standard
            except Exception as e:
                self.logger.warning("Error searching %s standards for %s: %s", source_type, standard_id, e)
                continue

        self.logger.warning("Standard '%s' not found in any source", standard_id)
        return None

    def _search_project_standards(self, standard_id: str) -> StandardDefinition | None:
        """Search for standard in project-level directory."""
        if not self.project_standards_path.exists():
            return None

        standard_file = self.project_standards_path / f"{standard_id}.md"
        if standard_file.exists():
            try:
                return self._create_standard_definition(standard_id, standard_file, "project")
            except Exception as e:
                self.logger.warning("Failed to create project standard %s: %s", standard_id, e)
                return None

        return None

    def _search_user_standards(self, standard_id: str) -> StandardDefinition | None:
        """Search for standard in user-level directory."""
        if not self.user_standards_path.exists():
            return None

        standard_file = self.user_standards_path / f"{standard_id}.md"
        if standard_file.exists():
            try:
                return self._create_standard_definition(standard_id, standard_file, "user")
            except Exception as e:
                self.logger.warning("Failed to create user standard %s: %s", standard_id, e)
                return None

        return None

    def _search_default_standards(self, standard_id: str) -> StandardDefinition | None:
        """Search for standard in default/built-in standards."""
        # For now, we don't have built-in defaults, but this could be extended
        # to include standards shipped with the application
        return None

    def _create_standard_definition(self, standard_id: str, file_path: Path, source_type: str) -> StandardDefinition:
        """Create a StandardDefinition from a file path."""
        try:
            # Extract metadata from file if available
            content = file_path.read_text(encoding="utf-8")

            # Simple metadata extraction (could be enhanced with YAML frontmatter parsing)
            name = standard_id.replace("-", " ").replace("_", " ").title()
            description = f"{name} development standard"
            version = None

            # Check if file has YAML frontmatter
            if content.startswith("---\n"):
                try:
                    import yaml  # noqa: PLC0415  # Optional/conditional import

                    frontmatter_end = content.find("\n---\n", 4)
                    if frontmatter_end != -1:
                        frontmatter = yaml.safe_load(content[4:frontmatter_end])
                        name = frontmatter.get("title", name)
                        description = frontmatter.get("description", description)
                        version = frontmatter.get("version", version)
                except Exception as e:
                    self.logger.debug("Failed to parse frontmatter for %s: %s", standard_id, e)

            return StandardDefinition(
                standard_id=standard_id,
                name=name,
                description=description,
                file_path=file_path,
                source_type=source_type,
                content=content,
                version=version,
                last_updated=datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC),
            )
        except Exception as e:
            self.logger.error("Failed to create standard definition for %s: %s", standard_id, e)
            raise

    def _refresh_standards_cache(self) -> None:
        """Refresh the standards cache by scanning all available sources."""
        self.logger.debug("Refreshing standards cache")
        self._standards_cache.clear()

        # Collect all standard IDs from all sources
        all_standard_ids = set()

        # Scan project standards
        if self.project_standards_path.exists():
            try:
                for file_path in self.project_standards_path.glob("*.md"):
                    standard_id = file_path.stem
                    all_standard_ids.add(standard_id)
            except Exception as e:
                self.logger.warning("Failed to scan project standards directory: %s", e)

        # Scan user standards
        if self.user_standards_path.exists():
            try:
                for file_path in self.user_standards_path.glob("*.md"):
                    standard_id = file_path.stem
                    all_standard_ids.add(standard_id)
            except Exception as e:
                self.logger.warning("Failed to scan user standards directory: %s", e)

        # Discover each standard (project-first, user-fallback)
        for standard_id in all_standard_ids:
            standard = self.discover_standard(standard_id)
            if standard:
                self._standards_cache[standard_id] = standard

        self._cache_timestamp = utc_now()
        self.logger.info("Refreshed standards cache with %s standards", len(self._standards_cache))

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed."""
        if self._cache_timestamp is None:
            return True

        age_seconds = (utc_now() - self._cache_timestamp).total_seconds()
        return age_seconds > self._cache_ttl_seconds

    def get_discovery_status(self) -> dict[str, Any]:
        """Get status information about standards discovery."""
        return {
            "project_standards_path": str(self.project_standards_path),
            "user_standards_path": str(self.user_standards_path),
            "project_standards_available": self.project_standards_path.exists(),
            "user_standards_available": self.user_standards_path.exists(),
            "cached_standards_count": len(self._standards_cache),
            "cache_age_seconds": (
                (utc_now() - self._cache_timestamp).total_seconds() if self._cache_timestamp else None
            ),
            "available_standards": self.get_available_standards(),
        }


class StandardsManager(LoggerMixin):
    """High-level manager for development standards."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__()
        self.discovery_system = StandardsDiscoverySystem(project_root)

    def get_linting_standard(self) -> str | None:
        """Get the linting standard content."""
        return self.discovery_system.get_standard_content("linting")

    def get_python_standard(self) -> str | None:
        """Get the Python development standard content."""
        return self.discovery_system.get_standard_content("python")

    def get_git_workflow_standard(self) -> str | None:
        """Get the Git workflow standard content."""
        return self.discovery_system.get_standard_content("git-workflow")

    def get_security_standard(self) -> str | None:
        """Get the security standard content."""
        return self.discovery_system.get_standard_content("security")

    def validate_project_compliance(self, standard_ids: list[str] | None = None) -> dict[str, bool]:
        """Validate project compliance against specified standards."""
        if standard_ids is None:
            standard_ids = ["linting", "python", "git-workflow", "security"]

        compliance_results = {}

        for standard_id in standard_ids:
            standard = self.discovery_system.get_standard(standard_id)
            if standard:
                # TODO: Implement actual compliance checking logic
                # For now, just check if standard is available
                compliance_results[standard_id] = True
            else:
                compliance_results[standard_id] = False
                self.logger.warning("Standard '%s' not available for compliance check", standard_id)

        return compliance_results


__all__ = [
    "StandardDefinition",
    "StandardsDiscoverySystem",
    "StandardsManager",
]
