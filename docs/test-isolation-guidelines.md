# Test Isolation Guidelines for PromptCraft

This document provides comprehensive guidelines for maintaining proper test isolation in the PromptCraft test suite, preventing state leakage between tests and ensuring consistent, reliable test results.

## Overview

Test isolation ensures that each test runs in a clean environment, independent of other tests. This prevents:

- State leakage between tests
- Order-dependent test failures
- Inconsistent test results
- Hard-to-debug test failures

## Core Isolation Principles

### 1. Clean State Between Tests

Each test should start with a clean slate:

- No shared global variables
- No persistent mock configurations
- No environment variable modifications
- No leftover temporary files

### 2. Isolated Dependencies

Tests should not depend on:

- External services (use mocks)
- File system state (use temporary directories)
- Network resources (use mock responses)
- Shared databases (use transactions or in-memory databases)

### 3. Predictable Cleanup

All test resources should be cleaned up automatically:

- Mock objects should be stopped
- Temporary files should be deleted
- Environment variables should be restored
- Database transactions should be rolled back

## Available Isolation Tools

### Automatic Isolation (`auto_isolation` fixture)

All tests automatically get basic isolation through the `auto_isolation` fixture:

```python
def test_example():
    # This test automatically gets:
    # - Clean authentication state
    # - Isolated context management
    # - Automatic cleanup after test completion
    pass
```

### Factory Pattern for Authentication

Use factories for creating consistent, isolated test objects:

```python
from tests.utils.auth_factories import JWTValidatorFactory, JWTTokenFactory, AuthenticatedUserFactory

def test_jwt_validation():
    # Each call creates a fresh, isolated instance
    validator = JWTValidatorFactory.create_validator()
    token = JWTTokenFactory.create_valid_token(email="test@example.com")
    user = AuthenticatedUserFactory.create_admin_user()

    # Test with clean objects...
```

### Environment Variable Isolation

For tests that need to modify environment variables:

```python
from tests.fixtures.isolation import isolated_environment_vars

def test_with_env_vars():
    with isolated_environment_vars(DEBUG="true", API_KEY="test-key"):
        # Environment variables are set only within this context
        assert os.environ.get("DEBUG") == "true"
    # Variables are automatically restored after the context
```

### Temporary Directory Isolation

For tests that need file system operations:

```python
from tests.fixtures.isolation import isolated_temp_directory

def test_file_operations():
    with isolated_temp_directory() as temp_dir:
        # All file operations happen in isolated directory
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
    # Directory is automatically cleaned up
```

### Mock Isolation

For isolated mock management:

```python
from tests.fixtures.isolation import isolated_mock_context

def test_with_mocks():
    with isolated_mock_context('src.auth.jwt_validator.JWTValidator') as mocks:
        validator_mock = mocks[0]
        validator_mock.validate.return_value = True
        # Use mocks...
    # Mocks are automatically stopped and cleaned up
```

### Database Session Isolation

For tests that modify database state:

```python
def test_database_operations(isolated_database_session):
    session = isolated_database_session
    # All database operations are automatically rolled back
    # No data persists between tests
```

### Comprehensive Isolation

For tests that need multiple isolation patterns:

```python
def test_comprehensive(comprehensive_isolation):
    context = comprehensive_isolation
    # Provides:
    # - Environment variable isolation
    # - Temporary directory
    # - Mock cleanup
    # - Database session isolation
```

## Best Practices

### 1. Use Factory Pattern

**DO:**

```python
def test_user_authentication():
    # Fresh instances for each test
    validator = JWTValidatorFactory.create_validator()
    token = JWTTokenFactory.create_valid_token()
```

**DON'T:**

```python
# Shared instance across tests - can leak state
SHARED_VALIDATOR = JWTValidator(...)

def test_user_authentication():
    # This can be affected by other tests
    result = SHARED_VALIDATOR.validate(token)
```

### 2. Avoid Global State

**DO:**

```python
def test_configuration():
    # Create isolated config for test
    config = {"debug": True, "api_key": "test"}
    result = process_config(config)
```

**DON'T:**

```python
# Modifying global state
import src.config as config
config.DEBUG = True  # Affects other tests

def test_configuration():
    result = process_config()
```

### 3. Use Context Managers for Resource Management

**DO:**

```python
def test_file_processing():
    with isolated_temp_directory() as temp_dir:
        test_file = temp_dir / "input.txt"
        test_file.write_text("test data")
        result = process_file(test_file)
    # Automatic cleanup
```

**DON'T:**

```python
def test_file_processing():
    # Manual cleanup - error prone
    test_file = Path("/tmp/test_input.txt")
    try:
        test_file.write_text("test data")
        result = process_file(test_file)
    finally:
        test_file.unlink()  # Might fail, leaving files behind
```

### 4. Validate Isolation

Use validation functions to ensure proper isolation:

```python
from tests.fixtures.isolation import assert_no_state_leakage, validate_test_isolation

def test_example():
    # Validate clean state at start (optional)
    assert_no_state_leakage(strict=False)

    # Your test logic...

# Validate that test follows isolation patterns
assert validate_test_isolation(test_example)
```

## Common Anti-Patterns to Avoid

### 1. Shared Mocks at Class Level

**BAD:**

```python
class TestUserManagement:
    @patch('src.auth.jwt_validator.JWTValidator')
    def setUp(self):
        # Mock shared across all test methods
        self.mock_validator = Mock()

    def test_method1(self):
        # Uses shared mock - state can leak
        pass

    def test_method2(self):
        # Inherits state from test_method1
        pass
```

**GOOD:**

```python
class TestUserManagement:
    def test_method1(self):
        # Fresh mock for each test
        with isolated_mock_context('src.auth.jwt_validator.JWTValidator') as mocks:
            validator_mock = mocks[0]
            # Test logic...

    def test_method2(self):
        # Completely independent mock
        validator = JWTValidatorFactory.create_validator()
        # Test logic...
```

### 2. Environment Variable Pollution

**BAD:**

```python
def test_debug_mode():
    os.environ['DEBUG'] = 'true'
    # Test logic...
    # DEBUG remains set for other tests!

def test_production_mode():
    # This test might fail because DEBUG is still 'true'
    pass
```

**GOOD:**

```python
def test_debug_mode():
    with isolated_environment_vars(DEBUG='true'):
        # Test logic...
    # DEBUG is automatically restored

def test_production_mode():
    # Clean environment, DEBUG is not set
    pass
```

### 3. Database State Leakage

**BAD:**

```python
def test_user_creation():
    user = User.create(email="test@example.com")
    user.save()  # Persists to database
    # Other tests can see this user!

def test_user_listing():
    users = User.all()
    # Might include user from previous test
```

**GOOD:**

```python
def test_user_creation(isolated_database_session):
    session = isolated_database_session
    user = User(email="test@example.com")
    session.add(user)
    session.commit()
    # Automatically rolled back after test

def test_user_listing(isolated_database_session):
    session = isolated_database_session
    users = session.query(User).all()
    # Clean database state
```

## Validation and Debugging

### Detecting State Leakage

If tests fail inconsistently or only when run in certain orders:

1. **Use strict validation:**

```python
def test_suspicious():
    assert_no_state_leakage(strict=True)  # Fails if state detected
    # Your test logic...
```

2. **Check for common leakage patterns:**
   - Shared mock objects
   - Environment variables not restored
   - Temporary files not cleaned up
   - Database transactions not rolled back

3. **Run tests in isolation:**

```bash
# Run single test to verify it passes alone
poetry run pytest tests/test_module.py::test_function -v

# Run tests in different orders
poetry run pytest --random-order tests/test_module.py
```

### Performance Monitoring

Test isolation shouldn't significantly impact performance:

```python
def test_performance_impact():
    import time
    start = time.perf_counter()

    # Run multiple isolated operations
    for i in range(100):
        with isolated_environment_vars(TEST_VAR=f"value_{i}"):
            pass

    duration = time.perf_counter() - start
    assert duration < 1.0, f"Isolation overhead too high: {duration}s"
```

## Integration with Existing Tests

### Migrating Existing Tests

1. **Identify problematic patterns:**
   - Class-level mocks
   - Global variable modifications
   - Shared test fixtures

2. **Replace with isolation patterns:**
   - Use factory functions instead of shared fixtures
   - Use context managers instead of setup/teardown
   - Use isolated fixtures for resources

3. **Validate the migration:**
   - Run tests multiple times in different orders
   - Check for consistent results
   - Use validation functions

### Example Migration

**Before:**

```python
class TestAuthenticationOld:
    def setUp(self):
        self.validator = JWTValidator()
        os.environ['JWT_SECRET'] = 'test-secret'

    def tearDown(self):
        del os.environ['JWT_SECRET']

    def test_valid_token(self):
        token = create_jwt_token()
        result = self.validator.validate(token)
        assert result.is_valid
```

**After:**

```python
class TestAuthenticationNew:
    def test_valid_token(self):
        validator = JWTValidatorFactory.create_validator()
        token = JWTTokenFactory.create_valid_token()

        with isolated_environment_vars(JWT_SECRET='test-secret'):
            result = validator.validate(token)
            assert result.is_valid
```

## Conclusion

Proper test isolation is essential for maintaining a reliable test suite. By following these guidelines and using the provided isolation tools, you can ensure that:

- Tests run consistently regardless of execution order
- State doesn't leak between tests
- Test failures are easier to debug
- The test suite remains maintainable as it grows

Remember: **Every test should be able to run in isolation and produce the same result every time.**
