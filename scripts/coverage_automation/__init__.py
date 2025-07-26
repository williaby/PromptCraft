"""
Coverage Automation Package

Modular coverage automation system for PromptCraft.
Provides automated coverage analysis with intelligent test type detection,
context-aware HTML reports, and Codecov integration.
"""

__version__ = "2.0.0"
__author__ = "PromptCraft Team"

from .types import TestType, TestTargetMapping, TestFileAnalysis, CoverageFileData, CoverageContext
from .config import TestPatternConfig
from .watcher import CoverageWatcher
from .classifier import TestTypeClassifier
from .renderer import CoverageRenderer
from .cli import CoverageAutomationCLI

__all__ = [
    "TestType",
    "TestTargetMapping", 
    "TestFileAnalysis",
    "CoverageFileData",
    "CoverageContext",
    "TestPatternConfig",
    "CoverageWatcher",
    "TestTypeClassifier",
    "CoverageRenderer",
    "CoverageAutomationCLI",
]