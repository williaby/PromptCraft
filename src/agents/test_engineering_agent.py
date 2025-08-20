"""
Test Engineering Agent for PromptCraft-Hybrid.

This module implements a specialized agent for building, running, and troubleshooting tests
in the PromptCraft codebase. It provides capabilities for:

- Test generation and scaffolding
- Test execution and debugging
- Coverage analysis and improvement
- Test performance optimization
- Error diagnosis and resolution

The agent integrates with the existing testing infrastructure including:
- Pytest for test execution
- Nox for session management
- Coverage.py for coverage analysis
- Various quality tools (bandit, safety, etc.)

Architecture:
    The agent inherits from BaseAgent and implements the execute() method.
    It provides specialized methods for different testing tasks and integrates
    with the project's testing ecosystem.

Example:
    ```python
    from src.agents.test_engineering_agent import TestEngineeringAgent
    from src.agents.models import AgentInput
    from src.agents.registry import agent_registry

    # Get agent from registry
    agent = agent_registry.get_agent("test_engineering", {"agent_id": "test_engineering"})

    # Create input for test generation
    input_data = AgentInput(
        content="Create unit tests for src/core/query_counselor.py",
        context={"task": "generate_tests"},
        config_overrides={"test_type": "unit"}
    )

    # Process
    result = await agent.process(input_data)
    print(result.content)  # Generated test code
    ```

Dependencies:
    - src.agents.base_agent: BaseAgent interface
    - src.agents.models: AgentInput, AgentOutput data models
    - src.agents.registry: Agent registration system
    - src.agents.exceptions: Error handling classes
    - subprocess, asyncio: For executing test commands
    - json, yaml: For parsing configuration files

Called by:
    - Developer workflows for test creation and troubleshooting
    - Automated testing pipelines
    - Quality assurance processes

Complexity: Varies by operation (O(1) for simple queries, O(n) for code analysis)
"""

import asyncio
import json
import os
import re
import tempfile
from typing import Any

from src.agents.base_agent import BaseAgent
from src.agents.exceptions import AgentExecutionError, AgentValidationError
from src.agents.models import AgentInput, AgentOutput
from src.agents.registry import agent_registry


@agent_registry.register("test_engineering")
class TestEngineeringAgent(BaseAgent):
    """
    Specialized agent for test engineering tasks in PromptCraft.

    This agent provides comprehensive testing capabilities including:
    - Test generation and scaffolding
    - Test execution and debugging
    - Coverage analysis and improvement
    - Performance optimization
    - Error diagnosis

    Configuration Parameters:
        default_test_type (str): Default test type (unit, integration, etc.) (default: "unit")
        coverage_target (float): Target coverage percentage (default: 80.0)
        timeout (int): Default timeout for test execution (default: 300)
        enable_debug_mode (bool): Enable detailed debugging output (default: False)

    Example:
        ```python
        config = {
            "agent_id": "test_engineering",
            "default_test_type": "unit",
            "coverage_target": 85.0,
            "timeout": 600,
            "enable_debug_mode": True
        }

        agent = TestEngineeringAgent(config)

        input_data = AgentInput(
            content="Run unit tests for src/core/query_counselor.py",
            context={"task": "run_tests", "file_path": "src/core/query_counselor.py"}
        )

        result = await agent.process(input_data)
        ```
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the TestEngineeringAgent.

        Args:
            config: Configuration dictionary containing agent parameters

        Raises:
            AgentConfigurationError: If required configuration is missing
        """
        # Set default configuration values before calling super().__init__()
        self.default_test_type = config.get("default_test_type", "unit")
        self.coverage_target = config.get("coverage_target", 80.0)
        self.timeout = config.get("timeout", 300)
        self.enable_debug_mode = config.get("enable_debug_mode", False)

        super().__init__(config)

        self.logger.info("TestEngineeringAgent initialized", extra={"config": self.config})

    def _validate_configuration(self) -> None:
        """
        Validate agent-specific configuration.

        Raises:
            AgentConfigurationError: If configuration is invalid
        """
        super()._validate_configuration()

        # Validate default_test_type
        valid_test_types = ["unit", "integration", "component", "contract", "e2e", "perf", "security", "fast"]
        if self.default_test_type not in valid_test_types:
            raise AgentValidationError(
                message=f"Invalid default_test_type '{self.default_test_type}'. Must be one of: {valid_test_types}",
                error_code="INVALID_CONFIG_VALUE",
                context={"default_test_type": self.default_test_type, "valid_types": valid_test_types},
                agent_id=self.agent_id,
            )

        # Validate coverage_target
        if not isinstance(self.coverage_target, (int, float)) or not (0 <= self.coverage_target <= 100):
            raise AgentValidationError(
                message="coverage_target must be a number between 0 and 100",
                error_code="INVALID_CONFIG_VALUE",
                context={"coverage_target": self.coverage_target},
                agent_id=self.agent_id,
            )

        # Validate timeout
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise AgentValidationError(
                message="timeout must be a positive integer",
                error_code="INVALID_CONFIG_VALUE",
                context={"timeout": self.timeout},
                agent_id=self.agent_id,
            )

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute test engineering tasks on the provided input.

        Args:
            agent_input: Input data containing the test task

        Returns:
            AgentOutput: Results of the test engineering task

        Raises:
            AgentValidationError: If input is invalid
            AgentExecutionError: If task execution fails
        """
        try:
            # Validate input
            self._validate_input(agent_input)

            # Extract task from context
            task = agent_input.context.get("task", "help") if agent_input.context else "help"

            # Process the task based on type
            if task == "generate_tests":
                result = await self._generate_tests(agent_input.content, agent_input.context)
            elif task == "run_tests":
                result = await self._run_tests(agent_input.content, agent_input.context)
            elif task == "debug_tests":
                result = await self._debug_tests(agent_input.content, agent_input.context)
            elif task == "analyze_coverage":
                result = await self._analyze_coverage(agent_input.content, agent_input.context)
            elif task == "improve_coverage":
                result = await self._improve_coverage(agent_input.content, agent_input.context)
            elif task == "optimize_performance":
                result = await self._optimize_performance(agent_input.content, agent_input.context)
            elif task == "diagnose_errors":
                result = await self._diagnose_errors(agent_input.content, agent_input.context)
            elif task == "help":
                result = await self._provide_help()
            else:
                raise AgentExecutionError(
                    message=f"Unknown task: {task}",
                    error_code="UNKNOWN_TASK",
                    context={"task": task},
                    agent_id=self.agent_id,
                    request_id=agent_input.request_id,
                )

            return self._create_output(
                content=result["content"],
                metadata=result.get("metadata", {}),
                confidence=result.get("confidence", 0.9),
                request_id=agent_input.request_id,
            )

        except Exception as e:
            # Convert any unexpected errors to AgentExecutionError
            if not isinstance(e, AgentValidationError | AgentExecutionError):
                raise AgentExecutionError(
                    message=f"Test engineering task failed: {e!s}",
                    error_code="TASK_FAILED",
                    context={"error": str(e), "error_type": type(e).__name__},
                    agent_id=self.agent_id,
                    request_id=agent_input.request_id,
                ) from e
            raise

    def _validate_input(self, agent_input: AgentInput) -> None:
        """
        Validate the input data.

        Args:
            agent_input: Input data to validate

        Raises:
            AgentValidationError: If input is invalid
        """
        # Basic validation
        if not agent_input.content:
            raise AgentValidationError(
                message="Input content is required",
                error_code="MISSING_INPUT",
                context={},
                agent_id=self.agent_id,
                request_id=agent_input.request_id,
            )

        # Validate task if specified
        if agent_input.context and "task" in agent_input.context:
            valid_tasks = [
                "generate_tests",
                "run_tests",
                "debug_tests",
                "analyze_coverage",
                "improve_coverage",
                "optimize_performance",
                "diagnose_errors",
                "help",
            ]
            task = agent_input.context["task"]
            if task not in valid_tasks:
                raise AgentValidationError(
                    message=f"Invalid task '{task}'. Must be one of: {valid_tasks}",
                    error_code="INVALID_TASK",
                    context={"task": task, "valid_tasks": valid_tasks},
                    agent_id=self.agent_id,
                    request_id=agent_input.request_id,
                )

    async def _generate_tests(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Generate test code for a given module or function.

        Args:
            content: Description of what to test (e.g., file path, function name)
            context: Additional context including test type and requirements

        Returns:
            Dict containing generated test code and metadata
        """
        # Extract parameters
        test_type = context.get("test_type", self.default_test_type) if context else self.default_test_type
        target_module = content.strip()

        # Validate target module
        if not target_module:
            raise AgentValidationError(
                message="Target module must be specified",
                error_code="MISSING_TARGET",
                context={"content": content},
                agent_id=self.agent_id,
            )

        # Determine test file path
        test_file_path = self._determine_test_file_path(target_module, test_type)

        # Generate test code skeleton
        test_code = self._generate_test_skeleton(target_module, test_type)

        # Create helpful metadata
        metadata = {
            "task": "generate_tests",
            "target_module": target_module,
            "test_file_path": test_file_path,
            "test_type": test_type,
            "generated_lines": len(test_code.splitlines()),
            "next_steps": [
                f"Review the generated tests in {test_file_path}",
                "Add specific test cases for your functions",
                "Run the tests with: poetry run pytest " + test_file_path,
            ],
        }

        return {
            "content": f"Generated {test_type} tests for {target_module}:\n\n```python\n{test_code}\n```\n\n"
            f"Test file should be saved to: {test_file_path}\n\n"
            f"Next steps:\n" + "\n".join([f"- {step}" for step in metadata["next_steps"]]),
            "metadata": metadata,
            "confidence": 0.85,
        }

    def _determine_test_file_path(self, module_path: str, test_type: str) -> str:
        """
        Determine the appropriate test file path for a module.

        Args:
            module_path: Path to the module being tested
            test_type: Type of tests to generate

        Returns:
            Path to the test file
        """
        # Normalize module path
        normalized_path = module_path.replace("/", ".").replace("\\", ".").replace(".py", "")

        # Remove src prefix if present
        if normalized_path.startswith("src."):
            normalized_path = normalized_path[4:]

        # Split into parts
        parts = normalized_path.split(".")

        # Map test types to directory names
        test_type_mapping = {
            "unit": "unit",
            "integration": "integration",
            "component": "integration",  # Component tests go in integration directory
            "contract": "contract",
            "e2e": "e2e",
            "perf": "performance",
            "performance": "performance",
            "security": "security",
            "fast": "unit",  # Fast tests are typically unit tests
        }

        test_dir = test_type_mapping.get(test_type, "unit")

        # Construct test file path
        if len(parts) > 1:
            # Multi-level module (e.g., src.core.query_counselor)
            module_name = parts[-1]
            test_file_path = f"tests/{test_dir}/{'/'.join(parts[:-1])}/test_{module_name}.py"
        else:
            # Single module
            module_name = parts[0]
            test_file_path = f"tests/{test_dir}/test_{module_name}.py"

        return test_file_path

    def _generate_test_skeleton(self, module_path: str, test_type: str) -> str:
        """
        Generate a test code skeleton for a module.

        Args:
            module_path: Path to the module being tested
            test_type: Type of tests to generate

        Returns:
            Generated test code skeleton
        """
        # Normalize module path
        normalized_path = module_path.replace("/", ".").replace("\\", ".").replace(".py", "")

        # Remove src prefix if present
        if normalized_path.startswith("src."):
            module_import = normalized_path
        else:
            module_import = f"src.{normalized_path}"

        # Get module name
        module_name = normalized_path.split(".")[-1]

        # Generate test skeleton based on test type
        if test_type == "unit":
            skeleton = f'''"""Unit tests for {module_import}."""

import pytest
from {module_import} import *  # Import what you need


class Test{module_name.title()}:
    """Test cases for {module_name} module."""

    def test_example_functionality(self):
        """Test basic functionality.

        TODO: Replace with actual test for your function.
        """
        # Arrange
        # Set up test data and preconditions

        # Act
        # Call the function being tested

        # Assert
        # Verify the results are as expected
        assert True  # Replace with actual assertion

    def test_edge_case(self):
        """Test edge cases.

        TODO: Add tests for boundary conditions.
        """
        pass

    def test_error_conditions(self):
        """Test error handling.

        TODO: Add tests for expected exceptions.
        """
        pass'''
        else:
            # Generic test skeleton for other test types
            skeleton = f'''"""{test_type.title()} tests for {module_import}."""

import pytest


class Test{module_name.title()}:
    """{test_type.title()} test cases for {module_name} module."""

    def test_{test_type}_functionality(self):
        """Test {test_type} functionality.

        TODO: Implement {test_type} tests for {module_name}.
        """
        # TODO: Implement test
        assert True  # Replace with actual test'''
        return skeleton

    async def _run_tests(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Run tests using the project's testing infrastructure.

        Args:
            content: Description of tests to run (e.g., file path, marker)
            context: Additional context including test options

        Returns:
            Dict containing test results and metadata
        """
        # Extract parameters
        target = content.strip() if content.strip() else "."
        markers = context.get("markers", []) if context else []
        test_type = context.get("test_type", self.default_test_type) if context else self.default_test_type

        # Build pytest command
        cmd = ["poetry", "run", "pytest", "-v"]

        # Add markers if specified
        if markers:
            marker_expr = " and ".join(markers)
            cmd.extend(["-m", marker_expr])
        elif test_type and test_type != "all":
            cmd.extend(["-m", test_type])

        # Add target
        cmd.append(target)

        # Add coverage if requested
        if context and context.get("with_coverage", False):
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        # Add other options
        if context and context.get("verbose", False):
            cmd.append("-vv")
        if context and context.get("quiet", False):
            cmd.append("-q")

        # Execute command
        try:
            self.logger.info(f"Running tests: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            # Decode output
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""

            # Format results
            if process.returncode == 0:
                status = "success"
                summary = "Tests completed successfully"
            else:
                status = "failed"
                summary = "Tests failed"

            # Extract key information
            test_count_match = re.search(r"collected (\d+) item", stdout_str)
            test_count = int(test_count_match.group(1)) if test_count_match else 0

            failed_match = re.search(r"(\d+) failed", stdout_str)
            failed_count = int(failed_match.group(1)) if failed_match else 0

            passed_match = re.search(r"(\d+) passed", stdout_str)
            passed_count = int(passed_match.group(1)) if passed_match else 0

            # Create output
            output_lines = [
                f"Test Execution Results ({status.upper()})",
                "=" * 40,
                f"Command: {' '.join(cmd)}",
                f"Status: {status}",
                f"Summary: {summary}",
                "",
                "Results:",
                f"  Total tests: {test_count}",
                f"  Passed: {passed_count}",
                f"  Failed: {failed_count}",
            ]

            if stdout_str:
                output_lines.extend(
                    ["", "Output:", "```", stdout_str[:2000] + ("..." if len(stdout_str) > 2000 else ""), "```"],
                )

            if stderr_str:
                output_lines.extend(
                    ["", "Errors:", "```", stderr_str[:1000] + ("..." if len(stderr_str) > 1000 else ""), "```"],
                )

            # Add recommendations
            recommendations = []
            if failed_count > 0:
                recommendations.append("Review the failed test output above")
                recommendations.append("Use the debug_tests task to get more detailed information")
            if test_count == 0:
                recommendations.append("Check that the target path is correct")
                recommendations.append("Verify that test files exist and follow the naming convention (test_*.py)")

            if recommendations:
                output_lines.extend(["", "Recommendations:", ""] + [f"- {rec}" for rec in recommendations])

            metadata = {
                "task": "run_tests",
                "command": " ".join(cmd),
                "status": status,
                "test_count": test_count,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "return_code": process.returncode,
            }

            return {
                "content": "\n".join(output_lines),
                "metadata": metadata,
                "confidence": 0.95,
            }

        except TimeoutError:
            return {
                "content": f"Test execution timed out after {self.timeout} seconds",
                "metadata": {"task": "run_tests", "status": "timeout", "timeout": self.timeout},
                "confidence": 0.8,
            }
        except Exception as e:
            return {
                "content": f"Failed to run tests: {e!s}",
                "metadata": {"task": "run_tests", "status": "error", "error": str(e)},
                "confidence": 0.5,
            }

    async def _debug_tests(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Debug failing tests with detailed output.

        Args:
            content: Description of tests to debug (e.g., file path, test name)
            context: Additional context including debug options

        Returns:
            Dict containing debug information and suggestions
        """
        # Extract parameters
        target = content.strip() if content.strip() else "."
        debug_level = context.get("debug_level", "normal") if context else "normal"

        # Build debug command
        cmd = ["poetry", "run", "pytest", "-v"]

        # Add debug flags based on level
        if debug_level == "verbose":
            cmd.extend(["-vv", "--tb=long"])
        elif debug_level == "minimal":
            cmd.extend(["--tb=short"])
        else:  # normal
            cmd.extend(["--tb=short"])

        # Add target
        cmd.append(target)

        # Add debug-specific flags
        cmd.extend(["--no-header", "--no-summary"])

        # For deep debugging
        if debug_level == "deep":
            cmd.extend(["--showlocals", "-s"])

        # Execute command
        try:
            self.logger.info(f"Debugging tests: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            # Decode output
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""

            # Analyze failures
            failed_tests = self._extract_failed_tests(stdout_str)
            error_patterns = self._analyze_error_patterns(stdout_str, stderr_str)

            # Generate debug output
            output_lines = [
                "Test Debug Results",
                "=" * 30,
                f"Command: {' '.join(cmd)}",
                "",
            ]

            if failed_tests:
                output_lines.extend(
                    [
                        "Failed Tests:",
                        "-" * 15,
                    ],
                )
                for test in failed_tests[:5]:  # Limit to first 5
                    output_lines.append(f"  {test['name']}")
                    if test.get("error"):
                        output_lines.append(f"    Error: {test['error']}")
                    if test.get("file") and test.get("line"):
                        output_lines.append(f"    Location: {test['file']}:{test['line']}")
                if len(failed_tests) > 5:
                    output_lines.append(f"  ... and {len(failed_tests) - 5} more")

            if error_patterns:
                output_lines.extend(
                    [
                        "",
                        "Common Error Patterns:",
                        "-" * 20,
                    ],
                )
                for pattern in error_patterns[:5]:  # Limit to first 5
                    output_lines.append(f"  {pattern['type']}: {pattern['description']}")
                    if pattern.get("suggestion"):
                        output_lines.append(f"    Suggestion: {pattern['suggestion']}")

            # Add recommendations
            recommendations = self._generate_debug_recommendations(failed_tests, error_patterns)
            if recommendations:
                output_lines.extend(
                    [
                        "",
                        "Debugging Recommendations:",
                        "-" * 24,
                    ]
                    + [f"- {rec}" for rec in recommendations],
                )

            # Include raw output if in verbose mode
            if debug_level in ["verbose", "deep"] and (stdout_str or stderr_str):
                output_lines.extend(
                    [
                        "",
                        "Raw Output:",
                        "-" * 11,
                        "STDOUT:",
                        "```",
                        stdout_str[:1000] + ("..." if len(stdout_str) > 1000 else ""),
                        "```",
                    ],
                )
                if stderr_str:
                    output_lines.extend(
                        [
                            "STDERR:",
                            "```",
                            stderr_str[:500] + ("..." if len(stderr_str) > 500 else ""),
                            "```",
                        ],
                    )

            metadata = {
                "task": "debug_tests",
                "command": " ".join(cmd),
                "failed_tests_count": len(failed_tests),
                "error_patterns_count": len(error_patterns),
                "debug_level": debug_level,
            }

            return {
                "content": "\n".join(output_lines),
                "metadata": metadata,
                "confidence": 0.9,
            }

        except TimeoutError:
            return {
                "content": f"Debug execution timed out after {self.timeout} seconds",
                "metadata": {"task": "debug_tests", "status": "timeout", "timeout": self.timeout},
                "confidence": 0.8,
            }
        except Exception as e:
            return {
                "content": f"Failed to debug tests: {e!s}",
                "metadata": {"task": "debug_tests", "status": "error", "error": str(e)},
                "confidence": 0.5,
            }

    def _extract_failed_tests(self, output: str) -> list[dict[str, Any]]:
        """
        Extract information about failed tests from pytest output.

        Args:
            output: Pytest output string

        Returns:
            List of failed test information
        """
        failed_tests = []
        lines = output.splitlines()

        current_test = None
        for line in lines:
            # Match test failure lines
            if line.startswith("FAILED "):
                # Extract test name
                match = re.match(r"FAILED (.*::.*) - (.*)", line)
                if match:
                    test_name = match.group(1)
                    error = match.group(2)
                    failed_tests.append({"name": test_name, "error": error, "type": "assertion_failure"})
                else:
                    # Fallback match
                    match = re.match(r"FAILED (.*)", line)
                    if match:
                        failed_tests.append({"name": match.group(1), "type": "general_failure"})
            elif line.startswith("ERROR "):
                # Match test errors (not failures)
                match = re.match(r"ERROR (.*::.*) - (.*)", line)
                if match:
                    test_name = match.group(1)
                    error = match.group(2)
                    failed_tests.append({"name": test_name, "error": error, "type": "test_error"})

        return failed_tests

    def _analyze_error_patterns(self, stdout: str, stderr: str) -> list[dict[str, Any]]:
        """
        Analyze output for common error patterns.

        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest

        Returns:
            List of identified error patterns
        """
        error_patterns = []
        combined_output = stdout + stderr

        # Import error pattern
        if "ImportError" in combined_output or "ModuleNotFoundError" in combined_output:
            error_patterns.append(
                {
                    "type": "import_error",
                    "description": "Missing or incorrect imports detected",
                    "suggestion": "Check that all required modules are installed and import paths are correct",
                },
            )

        # Assertion error pattern
        if "AssertionError" in combined_output:
            error_patterns.append(
                {
                    "type": "assertion_error",
                    "description": "Test assertions are failing",
                    "suggestion": "Review the expected vs actual values in your assertions",
                },
            )

        # Syntax error pattern
        if "SyntaxError" in combined_output:
            error_patterns.append(
                {
                    "type": "syntax_error",
                    "description": "Syntax errors found in test code",
                    "suggestion": "Check for missing colons, parentheses, or incorrect indentation",
                },
            )

        # Timeout pattern
        if "timed out" in combined_output.lower():
            error_patterns.append(
                {
                    "type": "timeout",
                    "description": "Tests are timing out",
                    "suggestion": "Check for infinite loops or optimize slow operations",
                },
            )

        # Fixture error pattern
        if "fixture" in combined_output.lower() and (
            "not found" in combined_output.lower() or "duplicate" in combined_output.lower()
        ):
            error_patterns.append(
                {
                    "type": "fixture_error",
                    "description": "Test fixture issues detected",
                    "suggestion": "Check fixture names, scopes, and dependencies",
                },
            )

        return error_patterns

    def _generate_debug_recommendations(self, failed_tests: list[dict], error_patterns: list[dict]) -> list[str]:
        """
        Generate debugging recommendations based on failures and errors.

        Args:
            failed_tests: List of failed tests
            error_patterns: List of identified error patterns

        Returns:
            List of debugging recommendations
        """
        recommendations = []

        # General recommendations based on error patterns
        for pattern in error_patterns:
            if pattern.get("suggestion"):
                recommendations.append(pattern["suggestion"])

        # Specific recommendations for failed tests
        if failed_tests:
            recommendations.append("Run individual failing tests in isolation to get more detailed error information")
            recommendations.append("Use pytest --pdb to drop into the debugger on failures")
            recommendations.append("Add print statements or logging to trace execution flow")

        # If no specific issues found
        if not failed_tests and not error_patterns:
            recommendations.append("No obvious errors found. Consider adding more verbose logging to your tests")
            recommendations.append("Check that your test environment matches the expected setup")

        # Deduplicate recommendations
        return list(dict.fromkeys(recommendations))

    async def _analyze_coverage(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Analyze test coverage for a module or the entire project.

        Args:
            content: Target to analyze (e.g., file path, module name, "." for all)
            context: Additional context including analysis options

        Returns:
            Dict containing coverage analysis and metadata
        """
        # Extract parameters
        target = content.strip() if content.strip() else "."
        detailed = context.get("detailed", False) if context else False

        # Build coverage command
        cmd = ["poetry", "run", "pytest", "--cov=src", "--cov-report=json"]

        # Add target
        if target != ".":
            cmd.append(target)

        # Create temporary file for coverage output
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp_file:
            tmp_filename = tmp_file.name

        # Modify command to output to temporary file
        cmd.extend(["--cov-report", f"json:{tmp_filename}"])

        # Execute command
        try:
            self.logger.info(f"Analyzing coverage: {' '.join(cmd[:-2])} --cov-report json:[temporary]")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            # Read coverage data
            coverage_data = {}
            if os.path.exists(tmp_filename):
                try:
                    with open(tmp_filename) as f:
                        coverage_data = json.load(f)
                except Exception as e:
                    self.logger.error(f"Failed to read coverage data: {e}")
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_filename)

            # Parse coverage data
            if coverage_data and "totals" in coverage_data:
                totals = coverage_data["totals"]
                coverage_percent = totals.get("percent_covered", 0)
                lines_covered = totals.get("covered_lines", 0)
                lines_missed = totals.get("missing_lines", 0)
                lines_total = totals.get("num_statements", 0)

                # Format results
                output_lines = [
                    "Coverage Analysis Results",
                    "=" * 27,
                    f"Target: {target}",
                    f"Overall Coverage: {coverage_percent:.1f}%",
                    f"Lines Covered: {lines_covered}",
                    f"Lines Missed: {lines_missed}",
                    f"Total Lines: {lines_total}",
                ]

                # Add status indicator
                if coverage_percent >= self.coverage_target:
                    output_lines.append(f"✅ Coverage target ({self.coverage_target}%) met")
                else:
                    output_lines.append(f"❌ Coverage target ({self.coverage_target}%) not met")
                    lines_needed = int((self.coverage_target / 100 * lines_total) - lines_covered)
                    output_lines.append(f"   Need to cover {lines_needed} more lines to meet target")

                # Add detailed information if requested
                if detailed and "files" in coverage_data:
                    output_lines.extend(
                        [
                            "",
                            "File-by-File Coverage:",
                            "-" * 22,
                        ],
                    )

                    # Sort files by coverage percentage (lowest first)
                    files = sorted(coverage_data["files"].items(), key=lambda x: x[1].get("percent_covered", 0))

                    for file_path, file_data in files[:10]:  # Limit to first 10 files
                        file_coverage = file_data.get("percent_covered", 0)
                        file_lines = file_data.get("num_statements", 0)
                        file_missed = file_data.get("missing_lines", 0)
                        status = "❌" if file_coverage < self.coverage_target else "✅"
                        output_lines.append(
                            f"  {status} {file_path}: {file_coverage:.1f}% "
                            f"({file_lines - file_missed}/{file_lines} lines)",
                        )

                # Add recommendations
                recommendations = self._generate_coverage_recommendations(coverage_percent, coverage_data)
                if recommendations:
                    output_lines.extend(
                        [
                            "",
                            "Recommendations:",
                            "-" * 15,
                        ]
                        + [f"- {rec}" for rec in recommendations],
                    )

                metadata = {
                    "task": "analyze_coverage",
                    "target": target,
                    "coverage_percent": coverage_percent,
                    "lines_covered": lines_covered,
                    "lines_missed": lines_missed,
                    "lines_total": lines_total,
                    "coverage_target": self.coverage_target,
                    "target_met": coverage_percent >= self.coverage_target,
                }

                return {
                    "content": "\n".join(output_lines),
                    "metadata": metadata,
                    "confidence": 0.95,
                }

            return {
                "content": "Failed to analyze coverage. No coverage data was generated.",
                "metadata": {"task": "analyze_coverage", "status": "no_data"},
                "confidence": 0.5,
            }

        except TimeoutError:
            return {
                "content": f"Coverage analysis timed out after {self.timeout} seconds",
                "metadata": {"task": "analyze_coverage", "status": "timeout", "timeout": self.timeout},
                "confidence": 0.8,
            }
        except Exception as e:
            return {
                "content": f"Failed to analyze coverage: {e!s}",
                "metadata": {"task": "analyze_coverage", "status": "error", "error": str(e)},
                "confidence": 0.5,
            }

    def _generate_coverage_recommendations(self, coverage_percent: float, coverage_data: dict) -> list[str]:
        """
        Generate recommendations based on coverage analysis.

        Args:
            coverage_percent: Overall coverage percentage
            coverage_data: Full coverage data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Overall coverage recommendations
        if coverage_percent < self.coverage_target:
            gap = self.coverage_target - coverage_percent
            if gap > 20:
                recommendations.append(
                    "Coverage is significantly below target. Focus on creating basic happy-path tests first.",
                )
            elif gap > 10:
                recommendations.append(
                    "Coverage is moderately below target. Add tests for edge cases and error conditions.",
                )
            else:
                recommendations.append("Coverage is close to target. Focus on the remaining uncovered lines.")

        # File-specific recommendations
        if "files" in coverage_data:
            # Find files with very low coverage
            low_coverage_files = [
                file_path
                for file_path, file_data in coverage_data["files"].items()
                if file_data.get("percent_covered", 100) < 50
            ]

            if low_coverage_files:
                recommendations.append(
                    f"Found {len(low_coverage_files)} files with less than 50% coverage. Prioritize these files.",
                )

            # Find files missing from coverage
            all_files = set(coverage_data["files"].keys())
            src_files = self._find_python_files("src")
            uncovered_files = src_files - all_files

            if uncovered_files:
                recommendations.append(
                    f"Found {len(uncovered_files)} Python files in src/ not included in coverage. Consider adding tests.",
                )

        # General recommendations
        recommendations.append("Use the improve_coverage task to generate suggestions for increasing coverage")
        recommendations.append("Focus on unit tests for maximum coverage efficiency")
        recommendations.append("Consider using pytest parametrize for testing multiple inputs efficiently")

        return recommendations

    def _find_python_files(self, directory: str) -> set[str]:
        """
        Find all Python files in a directory.

        Args:
            directory: Directory to search

        Returns:
            Set of Python file paths
        """
        python_files = set()
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    python_files.add(os.path.join(root, file))
        return python_files

    async def _improve_coverage(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Suggest improvements to increase test coverage.

        Args:
            content: Target to improve (e.g., file path, module name, "." for all)
            context: Additional context including improvement options

        Returns:
            Dict containing coverage improvement suggestions and metadata
        """
        # Extract parameters
        target = content.strip() if content.strip() else "."
        focus_areas = (
            context.get("focus_areas", ["missing_lines", "edge_cases", "error_paths"])
            if context
            else ["missing_lines", "edge_cases", "error_paths"]
        )

        # For now, we'll provide general suggestions since detailed missing line analysis
        # would require parsing coverage data, which is complex in this context.
        # In a real implementation, this would analyze coverage reports to identify
        # specific lines that need tests.

        suggestions = [
            "1. Identify core functionality in your module that lacks tests",
            "2. Create tests for the 'happy path' - the most common execution path",
            "3. Add tests for edge cases like empty inputs, boundary values, and special conditions",
            "4. Test error handling by providing invalid inputs and checking for expected exceptions",
            "5. For functions with conditional logic, test each branch of the condition",
            "6. For loops, test with zero iterations, one iteration, and multiple iterations",
            "7. Use pytest parametrize to efficiently test multiple input combinations",
            "8. For integration tests, mock external dependencies to focus on your code's logic",
            "9. Test both success and failure scenarios for API endpoints",
            "10. Use fixtures to set up common test data and reduce duplication",
        ]

        # Add specific suggestions based on focus areas
        if "missing_lines" in focus_areas:
            suggestions.append(
                "11. Run 'poetry run pytest --cov=src --cov-report=term-missing' to see exactly which lines are missing coverage",
            )
        if "edge_cases" in focus_areas:
            suggestions.append(
                "12. Consider using hypothesis for property-based testing to automatically find edge cases",
            )
        if "error_paths" in focus_areas:
            suggestions.append("13. Use pytest.raises to test that appropriate exceptions are raised")

        # Format output
        output_lines = [
            "Coverage Improvement Suggestions",
            "=" * 31,
            f"Target: {target}",
            "",
            "Actionable Steps:",
            "-" * 16,
        ] + [f"{s}" for s in suggestions]

        # Add example
        output_lines.extend(
            [
                "",
                "Example Test Structure:",
                "-" * 21,
                "```python",
                "def test_function_with_edge_cases():",
                "    # Test normal case",
                '    assert my_function("normal_input") == expected_output',
                "",
                "    # Test edge case - empty input",
                '    assert my_function("") == expected_empty_output',
                "",
                "    # Test error case - invalid input",
                "    with pytest.raises(ValueError):",
                '        my_function("invalid_input")',
                "```",
            ],
        )

        metadata = {
            "task": "improve_coverage",
            "target": target,
            "focus_areas": focus_areas,
            "suggestion_count": len(suggestions),
        }

        return {
            "content": "\n".join(output_lines),
            "metadata": metadata,
            "confidence": 0.85,
        }

    async def _optimize_performance(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Optimize test performance and execution speed.

        Args:
            content: Description of performance issues (e.g., slow tests, long execution)
            context: Additional context including optimization options

        Returns:
            Dict containing performance optimization suggestions and metadata
        """
        suggestions = [
            "1. Use pytest markers to separate slow tests: @pytest.mark.slow",
            "2. Run fast tests more frequently: poetry run pytest -m 'not slow'",
            "3. Use pytest-xdist for parallel test execution: poetry run pytest -n auto",
            "4. Mock external dependencies like APIs, databases, and file systems",
            "5. Use fixtures with appropriate scopes (function, class, module, session)",
            "6. Avoid setup/teardown in loops - move to fixture with higher scope",
            "7. Use tmp_path and tmp_path_factory fixtures instead of creating temporary files manually",
            "8. Group related tests in classes to share setup",
            "9. Use parametrize instead of loops within tests",
            "10. Profile slow tests with pytest-benchmark",
            "11. Limit database transactions in tests - use transactions that roll back",
            "12. Use factory libraries like factory_boy for complex test data",
            "13. Cache expensive setup operations in session-scoped fixtures",
            "14. Use pytest --last-failed to run only failing tests during debugging",
            "15. Use pytest --stepwise to stop at the first failure",
        ]

        # Format output
        output_lines = [
            "Test Performance Optimization",
            "=" * 30,
            "",
            "Performance Issues:",
            "-" * 18,
            "Based on your input, here are suggestions to optimize test execution speed:",
            "",
            "Optimization Strategies:",
            "-" * 22,
        ] + [f"{s}" for s in suggestions]

        # Add specific commands
        output_lines.extend(
            [
                "",
                "Useful Commands:",
                "-" * 15,
                "# Run only fast tests",
                "poetry run pytest -m 'not slow'",
                "",
                "# Run tests in parallel",
                "poetry run pytest -n auto",
                "",
                "# Run only failed tests from last run",
                "poetry run pytest --lf",
                "",
                "# Profile test durations",
                "poetry run pytest --durations=10",
            ],
        )

        metadata = {
            "task": "optimize_performance",
            "suggestion_count": len(suggestions),
        }

        return {
            "content": "\n".join(output_lines),
            "metadata": metadata,
            "confidence": 0.9,
        }

    async def _diagnose_errors(self, content: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """
        Diagnose and provide solutions for common test errors.

        Args:
            content: Description of the error or issue
            context: Additional context including error details

        Returns:
            Dict containing error diagnosis and solutions
        """
        # Common error patterns and solutions
        error_solutions = {
            "ImportError|ModuleNotFoundError": {
                "problem": "Missing or incorrect imports",
                "solutions": [
                    "Check that all required packages are listed in pyproject.toml",
                    "Run 'poetry install' to ensure all dependencies are installed",
                    "Verify import paths are correct (use absolute imports from src/)",
                    "Check that __init__.py files exist in package directories",
                ],
            },
            "FixtureNotFound": {
                "problem": "Missing or incorrectly named pytest fixtures",
                "solutions": [
                    "Check fixture name spelling matches exactly",
                    "Verify fixture is in conftest.py or the same test file",
                    "Check fixture scope is appropriate for usage",
                    "Ensure fixture's import dependencies are available",
                ],
            },
            "AssertionError": {
                "problem": "Test assertions are failing",
                "solutions": [
                    "Add print statements or use pytest.set_trace() to debug values",
                    "Check that expected values match actual output exactly",
                    "Use pytest.approx() for floating point comparisons",
                    "Verify test data setup is correct",
                ],
            },
            "TimeoutError": {
                "problem": "Tests are taking too long to execute",
                "solutions": [
                    "Mock external services and APIs",
                    "Use smaller datasets in tests",
                    "Break large tests into smaller, focused tests",
                    "Optimize algorithms or use more efficient test data",
                ],
            },
            "SyntaxError": {
                "problem": "Python syntax errors in test files",
                "solutions": [
                    "Check for missing colons, parentheses, or brackets",
                    "Verify indentation is consistent (use 4 spaces)",
                    "Check for mismatched quotes or string delimiters",
                    "Ensure all parentheses and brackets are properly closed",
                ],
            },
        }

        # Format output
        output_lines = [
            "Error Diagnosis",
            "=" * 15,
            "",
            "Common Test Errors and Solutions:",
            "-" * 32,
        ]

        for error_type, info in error_solutions.items():
            output_lines.extend(
                [
                    f"\nProblem: {info['problem']}",
                    "Solutions:",
                ]
                + [f"  - {solution}" for solution in info["solutions"]],
            )

        # Add general troubleshooting steps
        output_lines.extend(
            [
                "",
                "General Troubleshooting Steps:",
                "-" * 29,
                "1. Run tests with verbose output: poetry run pytest -v",
                "2. Run a single test to isolate issues: poetry run pytest path/to/test::test_name",
                "3. Use the debugger: poetry run pytest --pdb",
                "4. Show local variables on failure: poetry run pytest --showlocals",
                "5. Check the full traceback: poetry run pytest --tb=long",
            ],
        )

        metadata = {
            "task": "diagnose_errors",
            "error_types_covered": list(error_solutions.keys()),
        }

        return {
            "content": "\n".join(output_lines),
            "metadata": metadata,
            "confidence": 0.85,
        }

    async def _provide_help(self) -> dict[str, Any]:
        """
        Provide help information about the test engineering agent.

        Returns:
            Dict containing help information
        """
        help_text = """
Test Engineering Agent Help
==========================

This agent helps with building, running, and troubleshooting tests in the PromptCraft codebase.

Available Tasks:
----------------
1. generate_tests - Create test code skeletons
2. run_tests - Execute tests with various options
3. debug_tests - Analyze failing tests with detailed output
4. analyze_coverage - Check test coverage statistics
5. improve_coverage - Get suggestions for increasing coverage
6. optimize_performance - Optimize test execution speed
7. diagnose_errors - Troubleshoot common test errors

Usage Examples:
---------------
# Generate unit tests for a module
{
  "content": "Create unit tests for src/core/query_counselor.py",
  "context": {
    "task": "generate_tests",
    "test_type": "unit"
  }
}

# Run unit tests with coverage
{
  "content": "tests/unit/test_query_counselor.py",
  "context": {
    "task": "run_tests",
    "test_type": "unit",
    "with_coverage": true
  }
}

# Debug failing tests
{
  "content": "tests/unit/test_query_counselor.py::test_complex_function",
  "context": {
    "task": "debug_tests",
    "debug_level": "verbose"
  }
}

# Analyze coverage for a module
{
  "content": "src/core/query_counselor.py",
  "context": {
    "task": "analyze_coverage",
    "detailed": true
  }
}

Configuration Options:
----------------------
- default_test_type (str): Default test type when not specified (default: "unit")
- coverage_target (float): Target coverage percentage (default: 80.0)
- timeout (int): Test execution timeout in seconds (default: 300)
- enable_debug_mode (bool): Enable verbose debugging output (default: False)

For more information on testing in PromptCraft, see:
- docs/testing/quick-reference.md
- docs/testing/local-execution-guide.md
- pyproject.toml test configuration
        """

        return {
            "content": help_text.strip(),
            "metadata": {"task": "help"},
            "confidence": 1.0,
        }

    def get_capabilities(self) -> dict[str, Any]:
        """
        Get the agent's capabilities.

        Returns:
            Dict containing capability information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": "TestEngineeringAgent",
            "input_types": ["text"],
            "output_types": ["text", "code", "analysis"],
            "operations": [
                "generate_tests",
                "run_tests",
                "debug_tests",
                "analyze_coverage",
                "improve_coverage",
                "optimize_performance",
                "diagnose_errors",
                "help",
            ],
            "default_test_type": self.default_test_type,
            "coverage_target": self.coverage_target,
            "timeout": self.timeout,
            "enable_debug_mode": self.enable_debug_mode,
            "async_execution": True,
            "timeout_support": True,
            "config_overrides": True,
        }


# Export the agent class
__all__ = ["TestEngineeringAgent"]
