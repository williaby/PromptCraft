"""
Coverage file watcher and detection utilities.
Handles detection of VS Code coverage runs and file monitoring.
"""

import time
from pathlib import Path
from typing import Set, Optional
from .logging_utils import get_logger, get_performance_logger
from .config import TestPatternConfig


class CoverageWatcher:
    """Watches for coverage file changes and detects test execution."""
    
    def __init__(self, project_root: Path, config: TestPatternConfig):
        """Initialize coverage watcher."""
        self.project_root = project_root
        self.config = config
        self.logger = get_logger("watcher")
        self.perf_logger = get_performance_logger()
        
        # Coverage file locations
        self.coverage_file = self._find_coverage_file()
        self.coverage_json_path = self.project_root / "coverage.json"
        
        self.logger.info(
            "Coverage watcher initialized",
            coverage_file=str(self.coverage_file),
            project_root=str(self.project_root)
        )
    
    def _find_coverage_file(self) -> Path:
        """Find the appropriate coverage file (handles hostname suffixes)."""
        coverage_file = self.project_root / ".coverage"
        
        if not coverage_file.exists():
            # Look for coverage files with hostname suffixes
            coverage_files = list(self.project_root.glob(".coverage.*"))
            if coverage_files:
                # Use the most recent one
                coverage_file = max(coverage_files, key=lambda f: f.stat().st_mtime)
                self.logger.info(
                    "Using coverage file with hostname suffix",
                    coverage_file=str(coverage_file)
                )
        
        return coverage_file
    
    def detect_vscode_coverage_run(self, force_run: bool = False) -> bool:
        """
        Detect if VS Code just ran coverage by checking file timestamps.
        
        Args:
            force_run: If True, bypass timestamp checks
            
        Returns:
            True if recent coverage run detected, False otherwise
        """
        start_time = time.time()
        
        try:
            if force_run:
                self.logger.info("Forcing coverage run detection (--force)")
                return True
            
            if not self.coverage_file.exists():
                self.logger.warning(
                    "Coverage file not found",
                    coverage_file=str(self.coverage_file)
                )
                return False
            
            # Check if coverage file was updated in the last 60 seconds
            file_age = time.time() - self.coverage_file.stat().st_mtime
            recent_run = file_age < 60
            
            self.logger.info(
                "Coverage run detection completed",
                recent_run=recent_run,
                file_age_seconds=round(file_age, 2),
                coverage_file=str(self.coverage_file)
            )
            
            return recent_run
            
        except Exception as e:
            self.logger.error(
                "Error detecting coverage run",
                error=str(e),
                coverage_file=str(self.coverage_file)
            )
            return False
        
        finally:
            self.perf_logger.log_operation_timing(
                "detect_vscode_coverage_run",
                time.time() - start_time
            )
    
    def get_coverage_contexts(self) -> Set[str]:
        """
        Detect test types from test output and comprehensive coverage analysis.
        
        Returns:
            Set of test type contexts that were executed
        """
        start_time = time.time()
        contexts = set()
        current_time = time.time()
        
        try:
            # Method 1: Check which test directories exist and have recent activity
            test_dirs = self._get_test_directories_from_config()
            contexts.update(self._detect_contexts_from_recent_activity(test_dirs, current_time))
            
            # Method 2: Comprehensive coverage analysis
            contexts.update(self._detect_contexts_from_coverage_data(test_dirs))
            
            # Method 3: Check pytest cache
            contexts.update(self._detect_contexts_from_pytest_cache(test_dirs, current_time))
            
            # Fallback: if no contexts detected but we have coverage data
            if not contexts:
                contexts.update(self._fallback_context_detection(test_dirs, current_time))
            
            self.logger.info(
                "Coverage context detection completed",
                detected_contexts=sorted(contexts),
                context_count=len(contexts)
            )
            
            return contexts
            
        except Exception as e:
            self.logger.error(
                "Error detecting coverage contexts",
                error=str(e)
            )
            return {"unit", "auth", "integration"}  # Safe fallback
        
        finally:
            self.perf_logger.log_operation_timing(
                "get_coverage_contexts",
                time.time() - start_time,
                contexts_found=len(contexts)
            )
    
    def _get_test_directories_from_config(self) -> dict:
        """Build test directory mapping from configuration patterns."""
        test_dirs = {}
        
        for test_type in self.config.get_all_test_types():
            config = self.config.get_test_type_config(test_type)
            patterns = config.get('patterns', [])
            
            # Use the first directory pattern as the primary directory
            for pattern in patterns:
                if pattern.endswith('/'):
                    # Directory pattern
                    test_path = self.project_root / pattern.rstrip('/')
                    test_dirs[test_type] = test_path
                    break
            else:
                # Fallback to default pattern if no directory pattern found
                test_dirs[test_type] = self.project_root / "tests" / test_type
        
        return test_dirs
    
    def _detect_contexts_from_recent_activity(self, test_dirs: dict, current_time: float) -> Set[str]:
        """Detect contexts from recent .pyc file activity."""
        contexts = set()
        
        for test_type, test_dir in test_dirs.items():
            if test_dir.exists():
                # Check for recent .pyc files in __pycache__ directories
                pycache_dir = test_dir / "__pycache__"
                if pycache_dir.exists():
                    for pyc_file in pycache_dir.glob("*.pyc"):
                        try:
                            file_age = current_time - pyc_file.stat().st_mtime
                            if file_age < 3600:  # 1 hour
                                contexts.add(test_type)
                                self.logger.debug(
                                    "Context detected from recent activity",
                                    test_type=test_type,
                                    file_age_seconds=round(file_age, 2)
                                )
                                break
                        except OSError:
                            continue
        
        return contexts
    
    def _detect_contexts_from_coverage_data(self, test_dirs: dict) -> Set[str]:
        """Detect contexts from comprehensive coverage analysis."""
        contexts = set()
        
        try:
            if self.coverage_json_path.exists():
                import json
                with open(self.coverage_json_path) as f:
                    coverage_data = json.load(f)
                
                files = coverage_data.get('files', {})
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                
                # If we have high coverage (>80%) across many files, assume comprehensive test run
                if total_coverage > 80 and len(files) > 30:
                    self.logger.debug(
                        "High coverage detected, assuming comprehensive test run",
                        total_coverage=total_coverage,
                        file_count=len(files)
                    )
                    
                    # Add test types based on what directories exist
                    for test_type, test_dir in test_dirs.items():
                        if test_dir.exists():
                            contexts.add(test_type)
                    
                    # Also add based on coverage patterns
                    file_patterns = {
                        'auth': 'auth/',
                        'security': 'security/',
                        'examples': 'examples/'
                    }
                    
                    for test_type, pattern in file_patterns.items():
                        if any(pattern in f for f in files.keys()):
                            contexts.add(test_type)
                            
        except Exception as e:
            self.logger.debug(
                "Could not analyze coverage data",
                error=str(e)
            )
        
        return contexts
    
    def _detect_contexts_from_pytest_cache(self, test_dirs: dict, current_time: float) -> Set[str]:
        """Detect contexts from pytest cache activity."""
        contexts = set()
        
        pytest_cache = self.project_root / ".pytest_cache"
        if pytest_cache.exists():
            for cache_file in pytest_cache.rglob("*"):
                if cache_file.is_file():
                    try:
                        file_age = current_time - cache_file.stat().st_mtime
                        if file_age < 3600:  # 1 hour
                            self.logger.debug(
                                "Recent pytest cache detected",
                                file_age_seconds=round(file_age, 2)
                            )
                            # If we have recent pytest activity, add all existing test types
                            for test_type, test_dir in test_dirs.items():
                                if test_dir.exists():
                                    contexts.add(test_type)
                            break
                    except OSError:
                        continue
        
        return contexts
    
    def _fallback_context_detection(self, test_dirs: dict, current_time: float) -> Set[str]:
        """Fallback context detection when other methods fail."""
        contexts = set()
        
        if self.coverage_file.exists():
            try:
                file_age = current_time - self.coverage_file.stat().st_mtime
                if file_age < 7200:  # 2 hours
                    self.logger.debug(
                        "Using fallback test type detection",
                        coverage_file_age_seconds=round(file_age, 2)
                    )
                    # Add all test types that have directories
                    for test_type, test_dir in test_dirs.items():
                        if test_dir.exists():
                            contexts.add(test_type)
            except OSError:
                pass
        
        return contexts