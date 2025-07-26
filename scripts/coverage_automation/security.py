"""
Security utilities for coverage automation.
Implements enhanced path validation and HTML sanitization.
"""

import html
import re
import string
from pathlib import Path
from typing import Optional
from .logging_utils import get_security_logger


class SecurityValidator:
    """Security validation utilities with enhanced path and content validation."""
    
    def __init__(self, project_root: Path):
        """Initialize with project root for path validation."""
        self.project_root = project_root.resolve()
        self.security_logger = get_security_logger()
        
        # Compiled regex patterns for performance and security
        self.valid_module_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.]*$')
        self.suspicious_patterns = [
            re.compile(r'\.\.'),  # Path traversal
            re.compile(r'[<>"\']'),  # HTML/script injection attempts
            re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]'),  # Control characters
        ]
    
    def validate_path(self, file_path: Path) -> bool:
        """
        Enhanced path validation using Path.resolve().is_relative_to().
        Returns True if path is safe, False otherwise.
        """
        try:
            # Resolve the path to handle symlinks and relative components
            resolved_path = file_path.resolve()
            
            # Check if resolved path is within project bounds
            if not resolved_path.is_relative_to(self.project_root):
                self.security_logger.log_path_validation_failure(
                    file_path, "Path outside project bounds"
                )
                return False
            
            # Additional security checks
            path_str = str(resolved_path)
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if pattern.search(path_str):
                    self.security_logger.log_path_validation_failure(
                        file_path, f"Suspicious pattern detected: {pattern.pattern}"
                    )
                    return False
            
            return True
            
        except (ValueError, OSError, RuntimeError) as e:
            self.security_logger.log_path_validation_failure(
                file_path, f"Path resolution error: {e}"
            )
            return False
    
    def validate_file_size(self, file_path: Path, max_size_mb: float = 1.0) -> bool:
        """
        Validate file size to prevent memory exhaustion attacks.
        Returns True if file size is acceptable, False otherwise.
        """
        try:
            file_size = file_path.stat().st_size
            max_size_bytes = int(max_size_mb * 1024 * 1024)
            
            if file_size > max_size_bytes:
                self.security_logger.log_file_size_violation(
                    file_path, file_size, max_size_bytes
                )
                return False
            
            return True
            
        except (OSError, FileNotFoundError) as e:
            self.security_logger.log_path_validation_failure(
                file_path, f"File access error: {e}"
            )
            return False
    
    def sanitize_content(self, content: str) -> str:
        """
        Sanitize file content before processing.
        Removes dangerous characters and limits length.
        """
        # Remove null bytes and control characters
        content = content.replace('\x00', '')
        
        # Limit content length to prevent ReDoS attacks
        max_length = 100000  # 100KB of text content
        if len(content) > max_length:
            content = content[:max_length]
        
        # Keep only printable characters plus standard whitespace
        sanitized = ''.join(
            char for char in content 
            if char in string.printable
        )
        
        return sanitized
    
    def validate_import_path(self, import_path: str) -> bool:
        """
        Validate import path for security.
        Returns True if import path is safe, False otherwise.
        """
        if not import_path:
            return False
        
        # Prevent path traversal attacks
        if '..' in import_path:
            self.security_logger.log_import_path_rejection(
                import_path, "Path traversal attempt"
            )
            return False
        
        # Check for directory separators in import paths (only actual slashes, not dots)
        if '/' in import_path or '\\' in import_path:
            self.security_logger.log_import_path_rejection(
                import_path, "Invalid directory separators"
            )
            return False
        
        # Limit reasonable module path length
        if len(import_path) > 100:
            self.security_logger.log_import_path_rejection(
                import_path, "Import path too long"
            )
            return False
        
        # Only allow valid module names
        if not self.valid_module_pattern.match(import_path):
            self.security_logger.log_import_path_rejection(
                import_path, "Invalid module name format"
            )
            return False
        
        return True


class HTMLSanitizer:
    """HTML sanitization utilities replacing manual string operations."""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        Properly escape HTML content using built-in html.escape().
        Replaces manual replace() operations for security.
        """
        return html.escape(text, quote=True)
    
    @staticmethod
    def escape_html_attribute(value: str) -> str:
        """
        Escape HTML attribute values safely.
        """
        # First escape HTML entities
        escaped = html.escape(value, quote=True)
        
        # Additional escaping for attribute context
        escaped = escaped.replace('\n', '&#10;')
        escaped = escaped.replace('\r', '&#13;')
        escaped = escaped.replace('\t', '&#9;')
        
        return escaped
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe use in HTML links.
        """
        # First remove path traversal sequences
        sanitized = filename.replace('..', '')
        
        # Remove any path separators and dangerous characters
        safe_chars = string.ascii_letters + string.digits + '._-'
        sanitized = ''.join(c if c in safe_chars else '_' for c in sanitized)
        
        # Escape for HTML context
        return HTMLSanitizer.escape_html(sanitized)
    
    @staticmethod
    def sanitize_coverage_percentage(value: float) -> str:
        """
        Sanitize coverage percentage for safe HTML display.
        """
        # Ensure value is within reasonable bounds
        if not isinstance(value, (int, float)):
            return "0.0"
        
        clamped_value = max(0.0, min(100.0, float(value)))
        return f"{clamped_value:.1f}"