# Test Engineering Agent

The TestEngineeringAgent is a specialized AI agent designed to assist developers with all aspects of software testing in the PromptCraft codebase.

## Overview

This agent provides capabilities for:

- Test generation and scaffolding
- Test execution and debugging
- Coverage analysis and improvement
- Performance optimization
- Error diagnosis and resolution

## Usage

To use the TestEngineeringAgent, you can interact with it through the PromptCraft interface or directly through the agent API.

### Example Tasks

1. **Generate Tests**

   ```
   Task: generate_tests
   Content: Create unit tests for src/core/query_counselor.py
   Context: {"test_type": "unit"}
   ```

2. **Run Tests**

   ```
   Task: run_tests
   Content: tests/unit/test_query_counselor.py
   Context: {"with_coverage": true}
   ```

3. **Debug Tests**

   ```
   Task: debug_tests
   Content: tests/unit/test_query_counselor.py::test_complex_function
   Context: {"debug_level": "verbose"}
   ```

4. **Analyze Coverage**

   ```
   Task: analyze_coverage
   Content: src/core/query_counselor.py
   Context: {"detailed": true}
   ```

## Capabilities

- **Test Generation**: Creates test skeletons for modules
- **Test Execution**: Runs tests with various options
- **Debugging**: Analyzes failing tests with detailed output
- **Coverage Analysis**: Checks test coverage statistics
- **Coverage Improvement**: Suggests ways to increase coverage
- **Performance Optimization**: Optimizes test execution speed
- **Error Diagnosis**: Troubleshoots common test errors

## Configuration

The agent can be configured with:

- `default_test_type`: Default test type when not specified (default: "unit")
- `coverage_target`: Target coverage percentage (default: 80.0)
- `timeout`: Test execution timeout in seconds (default: 300)
- `enable_debug_mode`: Enable verbose debugging output (default: False)
