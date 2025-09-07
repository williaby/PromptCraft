# Qwen Test Engineer Agent

The QwenTestEngineerAgent is a specialized AI agent designed specifically to assist Qwen Code with all aspects of software testing in the PromptCraft codebase.

## Overview

This agent provides capabilities tailored for an AI assistant working with testing infrastructure:

- Test generation and scaffolding
- Test execution and debugging assistance
- Coverage analysis and improvement suggestions
- Error diagnosis for common test failures
- Best practices and quality recommendations

## Usage

To use the QwenTestEngineerAgent, you can interact with it through the PromptCraft interface or directly through the agent API.

### Example Tasks

1. **Generate Tests**

   ```
   Task: generate_tests
   Content: src/core/query_counselor.py
   Context: {"test_type": "unit"}
   ```

2. **Run Tests**

   ```
   Task: run_tests
   Content: tests/unit/
   Context: {"markers": ["unit"]}
   ```

3. **Analyze Coverage**

   ```
   Task: analyze_coverage
   Content: .
   Context: None
   ```

4. **Debug Failures**

   ```
   Task: debug_failures
   Content: tests/unit/test_example.py
   Context: None
   ```

5. **Suggest Improvements**

   ```
   Task: suggest_improvements
   Content: any text (not used)
   Context: None
   ```

## Key Features

- **Clear Output Formatting**: Responses are formatted specifically for AI assistant consumption
- **Actionable Recommendations**: Provides specific, implementable suggestions
- **Project-Specific Knowledge**: Deep understanding of PromptCraft's testing infrastructure
- **Error Pattern Recognition**: Identifies common failure patterns and suggests solutions
- **Best Practice Guidance**: Recommends testing best practices tailored to PromptCraft

## Capabilities

- **Test Generation**: Creates test skeletons with TODO comments for implementation
- **Test Execution**: Runs tests and provides clear pass/fail summaries
- **Coverage Analysis**: Analyzes coverage and identifies gaps
- **Failure Debugging**: Parses test output to identify and explain failures
- **Quality Improvement**: Suggests improvements for test maintainability and coverage
