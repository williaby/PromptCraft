"""
Type definitions for the coverage automation system.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Optional, FrozenSet, Any


class TestType(Enum):
    """Enumeration of supported test types."""
    UNIT = "unit"
    INTEGRATION = "integration"
    AUTH = "auth"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CONTRACT = "contract"
    STRESS = "stress"
    EXAMPLES = "examples"


@dataclass
class TestTargetMapping:
    """Represents the mapping between test type and source files."""
    test_type: TestType
    source_files: FrozenSet[str]
    confidence: float
    analysis_method: str


@dataclass
class TestFileAnalysis:
    """Results of analyzing a test file for its targets."""
    file_path: Path
    detected_imports: List[str]
    inferred_targets: FrozenSet[str]
    confidence_score: float
    analysis_warnings: List[str]


@dataclass 
class CoverageFileData:
    """Structured representation of coverage data for a file."""
    file_path: str
    statement_coverage: float
    branch_coverage: Optional[float]
    missing_lines: List[int]
    excluded_lines: List[int]
    total_statements: int
    covered_statements: int
    tested_by_type: bool
    coverage_note: Optional[str] = None


@dataclass
class CoverageContext:
    """Context information for coverage analysis."""
    test_types: Set[str]
    total_coverage: float
    coverage_by_type: Dict[str, Dict[str, float]]
    generation_time: str
    test_count: int = 3225  # From database
    database_coverage: float = 90.15  # From database