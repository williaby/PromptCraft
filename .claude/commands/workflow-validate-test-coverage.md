# Validate Test Coverage

Comprehensive test coverage analysis for phase and issue work: $ARGUMENTS

## Analysis Required

1. **Phase and Issue Context**:
   - Extract phase number and issue number from arguments
   - Identify all files modified/created for this specific phase and issue
   - Focus analysis on newly created files and significant modifications

2. **Test Coverage Analysis**:
   - Analyze each identified file for existing test coverage
   - Check for tests across all test markers: unit, integration, auth, performance, stress, fast, slow, smoke
   - Verify test coverage for all public methods, classes, and functions
   - Assess edge cases and error handling test coverage

3. **Missing Test Identification**:
   - Identify files without any test coverage
   - Identify functions/methods without adequate test coverage
   - Identify missing test types (e.g., missing integration tests for API endpoints)
   - Identify missing edge case testing

4. **Test Quality Assessment**:
   - Review existing tests for completeness and quality
   - Check for proper use of pytest markers
   - Verify tests follow project testing conventions
   - Assess test isolation and independence

## Coverage Standards Validation

1. **Minimum Coverage Requirements**:
   - All new Python files must have minimum 80% test coverage
   - All public methods and functions must have unit tests
   - All API endpoints must have integration tests
   - All authentication-related code must have auth tests

2. **Test Marker Compliance**:
   - Unit tests: Fast, isolated, no external dependencies
   - Integration tests: Component interaction testing
   - Auth tests: Authentication and authorization flows
   - Performance tests: Response time and throughput validation
   - Stress tests: High-load and resource testing
   - Fast tests: Quick feedback for development loops
   - Slow tests: Comprehensive but time-intensive validation
   - Smoke tests: Basic functionality validation

3. **Test File Organization**:
   - Test files must be in appropriate directories (tests/unit/, tests/integration/, etc.)
   - Test file names must follow test_[module_name].py convention
   - Test class and method names must be descriptive and follow conventions

## Required Output

Provide a comprehensive test coverage report with the following sections:

### 1. Executive Summary
- Total files analyzed
- Overall test coverage percentage
- Number of files with missing/inadequate tests
- Critical gaps requiring immediate attention

### 2. File-by-File Analysis
For each file modified/created in this phase and issue:

```
## File: src/path/to/file.py
**Coverage Status**: ✅ Adequate | ⚠️ Partial | ❌ Missing
**Current Coverage**: X% (if measurable)
**Test Files**: List of associated test files
**Missing Tests**:
- [ ] Unit tests for method_name()
- [ ] Integration tests for API endpoint
- [ ] Error handling for exception_case
**Recommendations**: Specific actionable items
```

### 3. Test Gap Analysis
- **Critical Gaps**: Files/functions requiring immediate test coverage
- **Quality Gaps**: Existing tests needing improvement
- **Type Gaps**: Missing test categories (unit, integration, etc.)

### 4. Implementation Recommendations
- Priority order for addressing test gaps
- Specific test scenarios to implement
- Suggested test markers and organization
- Integration with existing test infrastructure

### 5. Validation Checklist
```
Pre-Commit Test Coverage Checklist:
- [ ] All new files have minimum 80% coverage
- [ ] All public methods have unit tests
- [ ] API endpoints have integration tests
- [ ] Authentication code has auth tests
- [ ] Error paths are tested
- [ ] Tests use appropriate markers
- [ ] Test files follow naming conventions
- [ ] Tests are properly isolated
```

## Important Notes

- Focus specifically on files impacted by the phase and issue work
- Consider the testing tier strategy: fast development loop vs comprehensive validation
- Ensure tests support the tiered testing approach (fast < 1min, pre-commit < 2min, PR < 5min)
- Reference project testing standards in CLAUDE.md and conftest.py configuration
- Consider performance implications of new tests on the CI/CD pipeline
- Validate that new tests integrate properly with existing pytest markers and coverage reporting
