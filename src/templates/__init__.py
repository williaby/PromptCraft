"""Templates Discovery and Management System."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class TemplateDefinition:
    """Definition of a project template."""
    template_id: str
    name: str
    description: str
    file_path: Path
    source_type: str  # 'project', 'user'
    content: Optional[str] = None
    template_type: str = "markdown"
    last_updated: Optional[datetime] = None

class TemplatesManager:
    """Simple templates manager with hybrid discovery."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.project_templates_path = self.project_root / ".claude" / "templates"
        self.user_templates_path = Path.home() / ".claude" / "templates"
        self._templates_cache: Dict[str, TemplateDefinition] = {}
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template IDs."""
        self._refresh_cache()
        return list(self._templates_cache.keys())
    
    def get_template(self, template_id: str) -> Optional[TemplateDefinition]:
        """Get a specific template definition."""
        self._refresh_cache()
        return self._templates_cache.get(template_id)
    
    def get_template_content(self, template_id: str) -> Optional[str]:
        """Get template content."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        if template.content is None:
            try:
                template.content = template.file_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Failed to load template {template_id}: {e}")
                return None
        
        return template.content
    
    def _refresh_cache(self) -> None:
        """Refresh templates cache."""
        self._templates_cache.clear()
        
        # Scan project templates first (higher priority)
        if self.project_templates_path.exists():
            for file_path in self.project_templates_path.glob("*.md"):
                template_id = file_path.stem
                self._templates_cache[template_id] = self._create_template_definition(
                    template_id, file_path, "project"
                )
        
        # Scan user templates (fallback)
        if self.user_templates_path.exists():
            for file_path in self.user_templates_path.glob("*.md"):
                template_id = file_path.stem
                if template_id not in self._templates_cache:  # Project takes precedence
                    self._templates_cache[template_id] = self._create_template_definition(
                        template_id, file_path, "user"
                    )
    
    def _create_template_definition(self, template_id: str, file_path: Path, source_type: str) -> TemplateDefinition:
        """Create template definition from file path."""
        name = template_id.replace('-', ' ').replace('_', ' ').title()
        description = f"{name} template"
        
        return TemplateDefinition(
            template_id=template_id,
            name=name,
            description=description,
            file_path=file_path,
            source_type=source_type,
            last_updated=datetime.fromtimestamp(file_path.stat().st_mtime)
        )
    
    def get_discovery_status(self) -> Dict[str, Any]:
        """Get templates discovery status."""
        self._refresh_cache()
        templates_by_source = {"project": 0, "user": 0}
        
        for template in self._templates_cache.values():
            templates_by_source[template.source_type] += 1
        
        return {
            "project_templates_path": str(self.project_templates_path),
            "user_templates_path": str(self.user_templates_path),
            "project_templates_available": self.project_templates_path.exists(),
            "user_templates_available": self.user_templates_path.exists(),
            "cached_templates_count": len(self._templates_cache),
            "available_templates": self.get_available_templates(),
            "templates_by_source": templates_by_source
        }

__all__ = ["TemplateDefinition", "TemplatesManager"]