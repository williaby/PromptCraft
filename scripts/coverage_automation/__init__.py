"""
Coverage Automation Package

Modular coverage automation system for PromptCraft.
Provides automated coverage analysis that integrates with VS Code and codecov.yaml.
"""

from .classifier import TestTypeClassifier
from .cli import CoverageAutomationCLI
from .config import TestPatternConfig
from .renderer import CoverageRenderer
from .security import HTMLSanitizer, SecurityValidator
from .watcher import CoverageWatcher

__all__ = [
    "CoverageAutomationCLI",
    "CoverageRenderer",
    "CoverageWatcher",
    "HTMLSanitizer",
    "SecurityValidator",
    "TestPatternConfig",
    "TestTypeClassifier",
]
