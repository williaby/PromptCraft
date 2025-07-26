"""
Coverage Automation Package

Modular coverage automation system for PromptCraft.
Provides automated coverage analysis with intelligent test type detection,
context-aware HTML reports, and Codecov integration.
"""

__version__ = "2.0.0"
__author__ = "PromptCraft Team"

from .classifier import TestTypeClassifier
from .cli import CoverageAutomationCLI
from .config import TestPatternConfig
from .renderer import CoverageRenderer
from .types import CoverageContext, CoverageFileData, TestFileAnalysis, TestTargetMapping, TestType
from .watcher import CoverageWatcher

__all__ = [
    "CoverageAutomationCLI",
    "CoverageContext",
    "CoverageFileData",
    "CoverageRenderer",
    "CoverageWatcher",
    "TestFileAnalysis",
    "TestPatternConfig",
    "TestTargetMapping",
    "TestType",
    "TestTypeClassifier",
]
