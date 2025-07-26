"""
Command-line interface for coverage automation.
Provides the main entry point and argument parsing.
"""

import sys
import time
from pathlib import Path
from typing import Optional
from .config import TestPatternConfig
from .watcher import CoverageWatcher
from .classifier import TestTypeClassifier
from .renderer import CoverageRenderer
from .logging_utils import get_logger, get_performance_logger


class CoverageAutomationCLI:
    """Command-line interface for the coverage automation system."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the CLI with project root."""
        self.project_root = project_root or self._detect_project_root()
        self.logger = get_logger("cli")
        self.perf_logger = get_performance_logger()
        
        # Initialize components
        self.config = TestPatternConfig()
        self.watcher = CoverageWatcher(self.project_root, self.config)
        self.classifier = TestTypeClassifier(self.project_root, self.config)
        self.renderer = CoverageRenderer(self.project_root, self.config, self.classifier)
        
        self.logger.info(
            "Coverage automation CLI initialized",
            project_root=str(self.project_root),
            version="2.0.0"
        )
    
    def _detect_project_root(self) -> Path:
        """Detect project root from current file location."""
        # Go up from scripts/coverage_automation/ to project root
        return Path(__file__).parent.parent.parent
    
    def run_automation(self, force_run: bool = False, watch_mode: bool = False) -> bool:
        """
        Main automation workflow.
        
        Args:
            force_run: Force report generation regardless of file timestamps
            watch_mode: Run in watch mode (future enhancement)
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            self.logger.info("🤖 Starting Coverage Automation v2.0")
            self.logger.info("=" * 50)
            
            if watch_mode:
                return self._run_watch_mode()
            
            # Detect recent coverage run
            if not self.watcher.detect_vscode_coverage_run(force_run):
                self.logger.warning("⚠️  No recent coverage run detected")
                self.logger.info("   Run 'Run Tests with Coverage' in VS Code first")
                return False
            
            self.logger.info("✅ Recent coverage run detected")
            self.logger.info("📊 Generating enhanced coverage reports...")
            
            # Get coverage contexts
            used_contexts = self.watcher.get_coverage_contexts()
            if not used_contexts:
                self.logger.warning("No test contexts detected, using fallback")
                used_contexts = {"unit", "auth", "integration"}
            
            # Generate reports
            report_path = self.renderer.generate_coverage_reports(used_contexts)
            
            if report_path:
                self.logger.info(f"✅ Reports generated successfully")
                self.logger.info(f"📋 Main report: {report_path}")
                self.logger.info(f"🌐 Open in browser: file://{report_path}")
                
                # Log additional useful paths
                gap_analysis_path = Path(report_path).parent / "test_gap_analysis.html"
                if gap_analysis_path.exists():
                    self.logger.info(f"📊 Gap analysis: {gap_analysis_path}")
                
                return True
            else:
                self.logger.error("❌ Failed to generate reports")
                return False
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Operation cancelled by user")
            return False
            
        except Exception as e:
            self.logger.error(
                "Unexpected error during automation",
                error=str(e),
                error_type=type(e).__name__
            )
            return False
        
        finally:
            duration = time.time() - start_time
            self.perf_logger.log_operation_timing(
                "run_automation",
                duration,
                force_run=force_run,
                watch_mode=watch_mode
            )
            
            self.logger.info(
                f"🏁 Automation completed in {duration:.2f} seconds"
            )
    
    def _run_watch_mode(self) -> bool:
        """
        Run in watch mode (future enhancement).
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("🔍 Watch mode not yet implemented")
        self.logger.info("   Use --force to generate reports immediately")
        return False
    
    def display_help(self) -> None:
        """Display help information."""
        help_text = """
🤖 PromptCraft Coverage Automation v2.0

DESCRIPTION:
    Automated coverage analysis that detects VS Code test runs and generates
    context-aware HTML reports with Codecov integration.

USAGE:
    python -m scripts.coverage_automation.cli [OPTIONS]

OPTIONS:
    --force         Force report generation regardless of file timestamps
    --watch         Run in watch mode (future enhancement)
    --help, -h      Show this help message

EXAMPLES:
    # Generate reports after running "Run Tests with Coverage" in VS Code:
    python -m scripts.coverage_automation.cli

    # Force report generation:
    python -m scripts.coverage_automation.cli --force

FEATURES:
    ✅ Automatic test type detection (unit, auth, integration, security, etc.)
    ✅ Enhanced HTML reports with test-type filtering
    ✅ Codecov flag alignment for unified local/remote views
    ✅ Comprehensive test gap analysis
    ✅ Security-hardened path validation and HTML sanitization
    ✅ Structured logging with performance metrics
    ✅ Modular architecture for maintainability

REPORTS GENERATED:
    📋 reports/coverage/simplified_report.html    - Main coverage report
    📊 reports/coverage/test_gap_analysis.html    - Test gap analysis
    🔍 reports/coverage/*_coverage.html           - Test-type specific reports
    📈 htmlcov/index.html                         - Standard coverage.py report

CONFIGURATION:
    📁 config/test_patterns.yaml                  - Test pattern configuration
    📁 codecov.yaml                               - Codecov integration settings

For more information, see: https://github.com/your-org/PromptCraft
"""
        print(help_text)
    
    def validate_environment(self) -> bool:
        """
        Validate that the environment is properly configured.
        
        Returns:
            True if environment is valid, False otherwise
        """
        try:
            # Check project structure
            required_dirs = [
                self.project_root / "src",
                self.project_root / "tests",
                self.project_root / "config"
            ]
            
            for dir_path in required_dirs:
                if not dir_path.exists():
                    self.logger.error(
                        "Required directory not found",
                        directory=str(dir_path)
                    )
                    return False
            
            # Check configuration
            if not self.config.config_path.exists():
                self.logger.warning(
                    "Configuration file not found, using fallback",
                    config_path=str(self.config.config_path)
                )
            
            # Validate Poetry environment
            try:
                import subprocess
                result = subprocess.run(
                    ["poetry", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    self.logger.error("Poetry not available or not working properly")
                    return False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.error("Poetry not found in PATH")
                return False
            
            self.logger.info("✅ Environment validation passed")
            return True
            
        except Exception as e:
            self.logger.error(
                "Error validating environment",
                error=str(e)
            )
            return False


def main() -> int:
    """Main entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PromptCraft Coverage Automation v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force report generation regardless of file timestamps"
    )
    
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run in watch mode (future enhancement)"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate environment configuration and exit"
    )
    
    args = parser.parse_args()
    
    try:
        cli = CoverageAutomationCLI()
        
        if args.validate:
            success = cli.validate_environment()
            return 0 if success else 1
        
        success = cli.run_automation(
            force_run=args.force,
            watch_mode=args.watch
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 130
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())