"""
Integration example for task detection algorithm in Claude Code

Demonstrates how the task detection system would integrate with the Claude Code
function loading system to achieve dynamic, intelligent function selection.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import our task detection system
from src.core.task_detection import DetectionResult, TaskDetectionSystem
from src.core.task_detection_config import ConfigManager


@dataclass
class FunctionDefinition:
    """Represents a Claude Code function definition"""
    name: str
    category: str
    tier: int
    description: str
    token_cost: int
    parameters: dict[str, Any]


@dataclass
class LoadingStats:
    """Statistics about function loading"""
    total_functions: int
    loaded_functions: int
    total_tokens: int
    loaded_tokens: int
    detection_time_ms: float
    token_savings_percent: float


class FunctionRegistry:
    """Registry of all available Claude Code functions"""

    def __init__(self) -> None:
        self.functions = self._initialize_functions()
        self.category_mapping = self._build_category_mapping()

    def _initialize_functions(self) -> dict[str, FunctionDefinition]:
        """Initialize function definitions based on actual Claude Code inventory"""
        return {
            # Tier 1: Core Development Operations
            "bash": FunctionDefinition(
                name="Bash", category="core", tier=1,
                description="Execute shell commands with timeout and security",
                token_cost=850, parameters={"command": "required"},
            ),
            "read": FunctionDefinition(
                name="Read", category="core", tier=1,
                description="Read file contents with offset/limit support",
                token_cost=420, parameters={"file_path": "required"},
            ),
            "write": FunctionDefinition(
                name="Write", category="core", tier=1,
                description="Write complete file contents",
                token_cost=380, parameters={"file_path": "required", "content": "required"},
            ),
            "edit": FunctionDefinition(
                name="Edit", category="core", tier=1,
                description="Single string replacement in files",
                token_cost=450, parameters={"file_path": "required", "old_string": "required"},
            ),
            "multiedit": FunctionDefinition(
                name="MultiEdit", category="core", tier=1,
                description="Multiple edits in single file operation",
                token_cost=520, parameters={"file_path": "required", "edits": "required"},
            ),
            "ls": FunctionDefinition(
                name="LS", category="core", tier=1,
                description="List directory contents with filtering",
                token_cost=280, parameters={"path": "required"},
            ),
            "glob": FunctionDefinition(
                name="Glob", category="core", tier=1,
                description="Pattern-based file discovery",
                token_cost=320, parameters={"pattern": "required"},
            ),
            "grep": FunctionDefinition(
                name="Grep", category="core", tier=1,
                description="Advanced text search with regex",
                token_cost=680, parameters={"pattern": "required"},
            ),

            # Git functions
            "git_status": FunctionDefinition(
                name="mcp__git__git_status", category="git", tier=1,
                description="Show working tree status",
                token_cost=180, parameters={"repo_path": "required"},
            ),
            "git_add": FunctionDefinition(
                name="mcp__git__git_add", category="git", tier=1,
                description="Stage files for commit",
                token_cost=210, parameters={"repo_path": "required", "files": "required"},
            ),
            "git_commit": FunctionDefinition(
                name="mcp__git__git_commit", category="git", tier=1,
                description="Record changes to repository",
                token_cost=200, parameters={"repo_path": "required", "message": "required"},
            ),

            # Tier 2: Analysis & Intelligence
            "analyze": FunctionDefinition(
                name="mcp__zen__analyze", category="analysis", tier=2,
                description="Comprehensive code analysis",
                token_cost=820, parameters={"step": "required", "findings": "required"},
            ),
            "debug": FunctionDefinition(
                name="mcp__zen__debug", category="debug", tier=2,
                description="Systematic debugging workflow",
                token_cost=920, parameters={"step": "required", "findings": "required"},
            ),
            "thinkdeep": FunctionDefinition(
                name="mcp__zen__thinkdeep", category="analysis", tier=2,
                description="Multi-stage deep investigation",
                token_cost=780, parameters={"step": "required", "findings": "required"},
            ),

            # Quality tools
            "codereview": FunctionDefinition(
                name="mcp__zen__codereview", category="quality", tier=2,
                description="Comprehensive code review workflow",
                token_cost=950, parameters={"step": "required", "findings": "required"},
            ),
            "refactor": FunctionDefinition(
                name="mcp__zen__refactor", category="quality", tier=2,
                description="Refactoring analysis and planning",
                token_cost=890, parameters={"step": "required", "findings": "required"},
            ),
            "testgen": FunctionDefinition(
                name="mcp__zen__testgen", category="test", tier=2,
                description="Comprehensive test generation",
                token_cost=850, parameters={"step": "required", "findings": "required"},
            ),
            "secaudit": FunctionDefinition(
                name="mcp__zen__secaudit", category="security", tier=2,
                description="Security audit workflow",
                token_cost=980, parameters={"step": "required", "findings": "required"},
            ),

            # Tier 3: External Services
            "resolve_library": FunctionDefinition(
                name="mcp__context7-sse__resolve-library-id", category="external", tier=3,
                description="Resolve library names to Context7 IDs",
                token_cost=280, parameters={"libraryName": "required"},
            ),
            "get_library_docs": FunctionDefinition(
                name="mcp__context7-sse__get-library-docs", category="external", tier=3,
                description="Fetch library documentation",
                token_cost=320, parameters={"context7CompatibleLibraryID": "required"},
            ),
            "check_security": FunctionDefinition(
                name="mcp__safety-mcp-sse__check_package_security", category="external", tier=3,
                description="Check package vulnerabilities",
                token_cost=450, parameters={"packages": "required"},
            ),

            # Infrastructure
            "bash_output": FunctionDefinition(
                name="BashOutput", category="infrastructure", tier=3,
                description="Get background bash output",
                token_cost=280, parameters={"bash_id": "required"},
            ),
            "list_mcp_resources": FunctionDefinition(
                name="ListMcpResourcesTool", category="infrastructure", tier=3,
                description="List MCP server resources",
                token_cost=220, parameters={},
            ),
        }


    def _build_category_mapping(self) -> dict[str, list[str]]:
        """Build mapping from categories to function names"""
        mapping = {}
        for func_name, func_def in self.functions.items():
            category = func_def.category
            if category not in mapping:
                mapping[category] = []
            mapping[category].append(func_name)
        return mapping

    def get_functions_by_category(self, category: str) -> list[FunctionDefinition]:
        """Get all functions in a category"""
        function_names = self.category_mapping.get(category, [])
        return [self.functions[name] for name in function_names]

    def get_functions_by_categories(self, categories: list[str]) -> list[FunctionDefinition]:
        """Get all functions in multiple categories"""
        functions = []
        for category in categories:
            functions.extend(self.get_functions_by_category(category))
        return functions

    def calculate_token_cost(self, functions: list[FunctionDefinition]) -> int:
        """Calculate total token cost for function list"""
        return sum(func.token_cost for func in functions)


class IntelligentFunctionLoader:
    """Intelligent function loader using task detection"""

    def __init__(self, config_name: str = "production") -> None:
        self.detection_system = TaskDetectionSystem()
        self.function_registry = FunctionRegistry()

        # Load configuration
        config_manager = ConfigManager()
        self.config = config_manager.get_config(config_name)

        # Initialize statistics
        self.loading_history: list[LoadingStats] = []
        self.accuracy_metrics: dict[str, list[float]] = {
            "precision": [],
            "recall": [],
            "token_savings": [],
        }

    async def load_functions_for_query(self, query: str,
                                     context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load appropriate functions for a given query"""
        if context is None:
            context = {}

        # Enhance context with environment information
        enhanced_context = await self._enhance_context(context)

        # Detect required categories
        detection_result = await self.detection_system.detect_categories(
            query, enhanced_context,
        )

        # Load functions based on detection result
        loaded_functions = self._load_functions_from_detection(detection_result)

        # Calculate statistics
        stats = self._calculate_loading_stats(loaded_functions, detection_result)

        # Record for learning
        self._record_loading_decision(query, enhanced_context, detection_result, stats)

        return {
            "functions": loaded_functions,
            "detection_result": detection_result,
            "stats": stats,
            "context_used": enhanced_context,
        }

    async def _enhance_context(self, base_context: dict[str, Any]) -> dict[str, Any]:
        """Enhance context with environment information"""
        enhanced = base_context.copy()

        # Add current working directory analysis
        if "working_directory" not in enhanced:
            enhanced["working_directory"] = str(Path.cwd())

        # Analyze project structure
        working_dir = Path(enhanced["working_directory"])

        # Check for common project indicators
        enhanced["has_git_repo"] = (working_dir / ".git").exists()
        enhanced["has_test_directories"] = any(
            (working_dir / test_dir).exists()
            for test_dir in ["tests", "test", "__tests__", "spec"]
        )
        enhanced["has_security_files"] = any(
            (working_dir / sec_file).exists()
            for sec_file in [".env", "secrets.yaml", "auth.py", "security.py"]
        )
        enhanced["has_ci_files"] = any(
            (working_dir / ci_file).exists()
            for ci_file in [".github", ".gitlab-ci.yml", "Jenkinsfile", ".circleci"]
        )
        enhanced["has_docs"] = any(
            (working_dir / doc_dir).exists()
            for doc_dir in ["docs", "documentation", "README.md"]
        )

        # Analyze file types in project
        file_extensions = set()
        try:
            for file_path in working_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix:
                    file_extensions.add(file_path.suffix.lower())
        except PermissionError:
            pass  # Skip inaccessible directories

        enhanced["file_extensions"] = list(file_extensions)

        # Determine project type
        if any(ext in file_extensions for ext in [".py", ".pyx"]):
            enhanced["project_language"] = "python"
        elif any(ext in file_extensions for ext in [".js", ".ts", ".jsx", ".tsx"]):
            enhanced["project_language"] = "javascript"
        elif any(ext in file_extensions for ext in [".java", ".kt"]):
            enhanced["project_language"] = "java"

        # Check for security-focused project
        if (enhanced.get("has_security_files") or
            "security" in str(working_dir).lower() or
            "auth" in str(working_dir).lower()):
            enhanced["project_type"] = "security"

        return enhanced

    def _load_functions_from_detection(self, detection_result: DetectionResult) -> list[FunctionDefinition]:
        """Load functions based on detection result"""
        loaded_functions = []

        # Load functions for each enabled category
        for category, should_load in detection_result.categories.items():
            if should_load:
                category_functions = self.function_registry.get_functions_by_category(category)
                loaded_functions.extend(category_functions)

        return loaded_functions

    def _calculate_loading_stats(self, loaded_functions: list[FunctionDefinition],
                               detection_result: DetectionResult) -> LoadingStats:
        """Calculate loading statistics"""
        total_functions = len(self.function_registry.functions)
        loaded_count = len(loaded_functions)

        total_tokens = self.function_registry.calculate_token_cost(
            list(self.function_registry.functions.values()),
        )
        loaded_tokens = self.function_registry.calculate_token_cost(loaded_functions)

        token_savings_percent = ((total_tokens - loaded_tokens) / total_tokens) * 100

        return LoadingStats(
            total_functions=total_functions,
            loaded_functions=loaded_count,
            total_tokens=total_tokens,
            loaded_tokens=loaded_tokens,
            detection_time_ms=detection_result.detection_time_ms,
            token_savings_percent=token_savings_percent,
        )

    def _record_loading_decision(self, query: str, context: dict[str, Any],
                               detection_result: DetectionResult, stats: LoadingStats) -> None:
        """Record loading decision for analysis and learning"""
        self.loading_history.append(stats)

        # Keep only recent history for memory management
        if len(self.loading_history) > 1000:
            self.loading_history = self.loading_history[-1000:]

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary statistics"""
        if not self.loading_history:
            return {}

        recent_stats = self.loading_history[-100:]  # Last 100 decisions

        avg_detection_time = sum(s.detection_time_ms for s in recent_stats) / len(recent_stats)
        avg_token_savings = sum(s.token_savings_percent for s in recent_stats) / len(recent_stats)
        avg_functions_loaded = sum(s.loaded_functions for s in recent_stats) / len(recent_stats)

        return {
            "average_detection_time_ms": avg_detection_time,
            "average_token_savings_percent": avg_token_savings,
            "average_functions_loaded": avg_functions_loaded,
            "total_decisions": len(self.loading_history),
            "performance_target_met": avg_detection_time < self.config.performance.max_detection_time_ms,
            "token_savings_target_met": avg_token_savings > 50.0,  # Target 50%+ savings
        }


class TaskDetectionDemo:
    """Demonstration of task detection in various scenarios"""

    def __init__(self) -> None:
        self.loader = IntelligentFunctionLoader("production")

    async def run_demo_scenarios(self) -> None:
        """Run demonstration scenarios"""
        scenarios = [
            {
                "name": "Git Workflow",
                "query": "check git status and commit my changes",
                "context": {"has_git_repo": True, "has_uncommitted_changes": True},
            },
            {
                "name": "Debug Session",
                "query": "debug the failing authentication tests",
                "context": {
                    "file_extensions": [".py"],
                    "has_tests": True,
                    "project_type": "security",
                },
            },
            {
                "name": "Code Analysis",
                "query": "analyze this codebase for security issues and performance problems",
                "context": {
                    "file_extensions": [".py", ".js"],
                    "has_security_files": True,
                    "project_language": "python",
                },
            },
            {
                "name": "Vague Request",
                "query": "help me improve this code",
                "context": {"file_extensions": [".py"]},
            },
            {
                "name": "Library Documentation",
                "query": "find documentation for fastapi routing",
                "context": {"project_language": "python"},
            },
            {
                "name": "Multi-domain Task",
                "query": "refactor the security tests and fix any vulnerabilities found",
                "context": {
                    "has_tests": True,
                    "has_security_files": True,
                    "file_extensions": [".py"],
                },
            },
        ]


        for _i, scenario in enumerate(scenarios, 1):

            # Load functions for this scenario
            result = await self.loader.load_functions_for_query(
                scenario["query"],
                scenario["context"],
            )

            # Display results
            [
                category for category, loaded
                in result["detection_result"].categories.items()
                if loaded
            ]


            if result["detection_result"].fallback_applied:
                pass

            # Show confidence scores for top categories
            top_scores = sorted(
                result["detection_result"].confidence_scores.items(),
                key=lambda x: x[1], reverse=True,
            )[:3]

            if top_scores:
                for _category, _score in top_scores:
                    pass

        # Performance summary

        summary = self.loader.get_performance_summary()
        for _key, value in summary.items():
            if isinstance(value, float):
                pass
            else:
                pass


class AccuracyValidator:
    """Validates detection accuracy against known scenarios"""

    def __init__(self) -> None:
        self.loader = IntelligentFunctionLoader("production")

        # Define test scenarios with expected categories
        self.test_scenarios = [
            {
                "query": 'git commit -m "fix bug"',
                "context": {"has_git_repo": True},
                "expected_categories": ["core", "git"],
                "name": "Simple Git Command",
            },
            {
                "query": "debug the failing unit tests",
                "context": {"has_tests": True, "file_extensions": [".py"]},
                "expected_categories": ["core", "git", "debug", "test"],
                "name": "Debug Tests",
            },
            {
                "query": "analyze security vulnerabilities in authentication",
                "context": {"has_security_files": True, "project_type": "security"},
                "expected_categories": ["core", "git", "analysis", "security"],
                "name": "Security Analysis",
            },
            {
                "query": "refactor code and improve test coverage",
                "context": {"has_tests": True, "file_extensions": [".py"]},
                "expected_categories": ["core", "git", "quality", "test"],
                "name": "Refactor and Test",
            },
        ]

    async def validate_accuracy(self) -> dict[str, float]:
        """Validate detection accuracy"""
        precision_scores = []
        recall_scores = []


        for scenario in self.test_scenarios:
            result = await self.loader.load_functions_for_query(
                scenario["query"],
                scenario["context"],
            )

            predicted_categories = {
                category for category, loaded
                in result["detection_result"].categories.items()
                if loaded
            }
            expected_categories = set(scenario["expected_categories"])

            # Calculate metrics
            true_positives = len(predicted_categories & expected_categories)
            precision = true_positives / len(predicted_categories) if predicted_categories else 0
            recall = true_positives / len(expected_categories) if expected_categories else 1

            precision_scores.append(precision)
            recall_scores.append(recall)


        avg_precision = sum(precision_scores) / len(precision_scores)
        avg_recall = sum(recall_scores) / len(recall_scores)
        f1_score = 2 * avg_precision * avg_recall / (avg_precision + avg_recall)


        return {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1_score": f1_score,
        }


async def main() -> None:
    """Main demonstration function"""

    # Run the main demo
    demo = TaskDetectionDemo()
    await demo.run_demo_scenarios()

    # Run accuracy validation
    validator = AccuracyValidator()
    await validator.validate_accuracy()

    # Configuration demonstration

    config_manager = ConfigManager()

    # Show available configurations
    configs = config_manager.list_configs()

    # Load different configurations and show differences
    for config_name in ["development", "production", "performance_critical"]:
        if config_name in configs:
            config_manager.get_config(config_name)



if __name__ == "__main__":
    asyncio.run(main())
