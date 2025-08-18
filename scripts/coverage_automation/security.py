"""
Security utilities for coverage automation.
"""

import html
import string
from pathlib import Path
from typing import Any


class SecurityValidator:
    """Security validation utilities."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
    
    def validate_path(self, file_path: Path | str) -> bool:
        """Validate that a file path is within project bounds and safe."""
        try:
            path = Path(file_path).resolve()
            return path.is_relative_to(self.project_root)
        except (ValueError, OSError):
            return False
    
    def validate_file_size(self, file_path: Path, max_size_mb: float = 1.0) -> bool:
        """Validate file size to prevent memory exhaustion."""
        try:
            file_size = file_path.stat().st_size
            max_bytes = max_size_mb * 1024 * 1024
            return file_size <= max_bytes
        except (OSError, FileNotFoundError):
            return False
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize content by removing dangerous characters."""
        # Remove null bytes and other control characters
        content = content.replace('\x00', '')
        
        # Remove other control characters except standard whitespace
        printable_chars = string.printable
        sanitized = ''.join(char for char in content if char in printable_chars)
        
        return sanitized
    
    def validate_import_path(self, import_path: str) -> bool:
        """Validate that an import path is safe."""
        if not import_path or len(import_path) > 100:
            return False
        
        # Prevent path traversal
        if '..' in import_path:
            return False
        
        # Only allow valid module names
        import re
        pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.]*$')
        return bool(pattern.match(import_path))


class HTMLSanitizer:
    """HTML sanitization utilities."""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML content."""
        return html.escape(text)
    
    @staticmethod
    def escape_html_attribute(text: str) -> str:
        """Escape HTML attribute values."""
        return html.escape(text, quote=True)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe HTML links."""
        # Remove path separators and dangerous characters
        filename = filename.replace('..', '').replace('/', '_').replace('\\', '_')
        return HTMLSanitizer.escape_html(filename)
    
    @staticmethod
    def sanitize_coverage_percentage(percentage: Any) -> str:
        """Sanitize and validate coverage percentage."""
        try:
            val = float(percentage)
            # Clamp to valid range
            val = max(0.0, min(100.0, val))
            return f"{val:.1f}"
        except (ValueError, TypeError):
            return "0.0"