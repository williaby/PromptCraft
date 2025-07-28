# PromptCraft Coverage Automation v2.0

## Overview

The PromptCraft Coverage Automation system has been refactored to implement the priority improvements identified in the 7-model consensus review. This modular architecture provides enhanced security, maintainability, and Codecov integration while maintaining full backward compatibility.

## Key Improvements

### 🔧 Priority 1: Maintainability Improvements

- **Modular Architecture**: Broke down the monolithic `simplified_coverage_automation.py` (1,836 lines) into focused modules:
  - `watcher.py` - File detection and triggering (174 lines)
  - `classifier.py` - Test type classification (385 lines)
  - `renderer.py` - Report generation (421 lines)
  - `cli.py` - Command-line interface (208 lines)
  - Supporting modules: `types.py`, `config.py`, `security.py`, `logging_utils.py`

- **Enhanced Error Handling**: Implemented structured logging with context-specific information
  - `ContextAwareLogger` for component-specific logging
  - `SecurityLogger` for security events
  - `PerformanceLogger` for timing metrics

### 🛡️ Priority 2: Security Hardening

- **Enhanced Path Resolution**: Implemented `Path.resolve().is_relative_to(PROJECT_ROOT)` for secure path validation
- **HTML Sanitization**: Replaced manual `replace()` operations with proper `html.escape()` and security helpers
- **Content Security**: Added file size limits, path traversal protection, and input sanitization

### 🔄 Priority 4: Integration Enhancements

- **Codecov Flag Mapping**: Aligned YAML patterns with Codecov flags for unified local/remote views
- **Configuration Integration**: Extended `test_patterns.yaml` with Codecov integration section

## Architecture

```
scripts/coverage_automation/
├── __init__.py              # Package initialization and exports
├── types.py                 # Type definitions and data classes
├── config.py                # Configuration management with Codecov integration
├── security.py              # Security validation and HTML sanitization
├── logging_utils.py         # Structured logging utilities
├── watcher.py               # Coverage file detection and monitoring
├── classifier.py            # Test type classification and target mapping
├── renderer.py              # HTML report generation with security
├── cli.py                   # Command-line interface
└── README.md               # This documentation
```

## Usage

### Basic Usage

```bash
# After running "Run Tests with Coverage" in VS Code:
python scripts/simplified_coverage_automation_v2.py

# Force report generation:
python scripts/simplified_coverage_automation_v2.py --force

# Validate environment:
python scripts/simplified_coverage_automation_v2.py --validate
```

### Programmatic Usage

```python
from scripts.coverage_automation import (
    TestPatternConfig,
    CoverageWatcher,
    TestTypeClassifier,
    CoverageRenderer,
    CoverageAutomationCLI
)

# Initialize components
config = TestPatternConfig()
watcher = CoverageWatcher(project_root, config)
classifier = TestTypeClassifier(project_root, config)
renderer = CoverageRenderer(project_root, config, classifier)

# Run automation
cli = CoverageAutomationCLI(project_root)
success = cli.run_automation()
```

## Configuration

### Enhanced test_patterns.yaml

The configuration now includes Codecov integration:

```yaml
# Codecov integration for unified local/remote views
codecov_integration:
  enabled: true
  flag_mapping:
    unit:
      codecov_flag: "unit"
      source_paths:
        - "src/core/"
        - "src/agents/"
        - "src/config/"
    auth:
      codecov_flag: "auth"
      source_paths:
        - "src/auth/"
  status_targets:
    unit: 85.0
    integration: 75.0
    default: 80.0
```

## Security Features

### Path Validation

```python
# Enhanced path validation
validator = SecurityValidator(project_root)
is_safe = validator.validate_path(file_path)
```

Features:
- Uses `Path.resolve().is_relative_to()` for secure path resolution
- Prevents path traversal attacks
- Validates symlinks and resolves to actual paths
- Logs security violations with context

### HTML Sanitization

```python
# Proper HTML sanitization
safe_html = HTMLSanitizer.escape_html(user_content)
safe_attr = HTMLSanitizer.escape_html_attribute(attr_value)
safe_filename = HTMLSanitizer.sanitize_filename(filename)
```

Features:
- Replaces manual string operations with `html.escape()`
- Context-aware escaping for attributes
- Filename sanitization for safe links
- Coverage percentage validation

## Logging

### Structured Logging

```python
from coverage_automation.logging_utils import get_logger

logger = get_logger("component")
logger.info("Operation completed", duration=1.5, files_processed=10)
```

### Security Logging

```python
from coverage_automation.logging_utils import get_security_logger

security_logger = get_security_logger()
security_logger.log_path_validation_failure(file_path, "reason")
```

### Performance Logging

```python
from coverage_automation.logging_utils import get_performance_logger

perf_logger = get_performance_logger()
perf_logger.log_operation_timing("operation", duration, context="value")
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/unit/scripts/test_coverage_automation.py -v

# Run specific test classes
python -m pytest tests/unit/scripts/test_coverage_automation.py::TestSecurityValidatorEnhancements -v
```

### Test Coverage

The test suite covers:
- ✅ Security validator enhancements
- ✅ HTML sanitization improvements
- ✅ Modular architecture validation
- ✅ Codecov integration
- ✅ Structured logging
- ✅ Backward compatibility
- ✅ Error handling

## Migration Guide

### From v1.0 to v2.0

The new system maintains full backward compatibility:

1. **Direct Replacement**: Replace calls to `simplified_coverage_automation.py` with `simplified_coverage_automation_v2.py`

2. **Configuration**: Optionally update `config/test_patterns.yaml` to include Codecov integration

3. **Programmatic Usage**: Import from the new modular structure:
   ```python
   # Old (still works)
   from scripts.simplified_coverage_automation import SimplifiedCoverageAutomation

   # New (recommended)
   from scripts.coverage_automation import CoverageAutomationCLI
   ```

### Breaking Changes

None - the system maintains full backward compatibility.

## Performance Improvements

- **Caching**: LRU caches for test target mapping (32 entries) and file analysis (256 entries)
- **Compiled Regex**: Pre-compiled patterns for better performance
- **Structured Logging**: Reduced overhead with context-aware logging
- **Security Validation**: Efficient path validation with early termination

## Generated Reports

The system generates the following reports:

1. **Main Report**: `reports/coverage/simplified_report.html`
   - Enhanced with security-hardened HTML
   - Test type filtering with Codecov alignment
   - Interactive coverage pills

2. **Test Gap Analysis**: `reports/coverage/test_gap_analysis.html`
   - File-centric view of coverage gaps
   - Security-sanitized content

3. **Test Type Reports**: `reports/coverage/{type}_coverage.html`
   - Type-specific coverage analysis
   - Function and class coverage views

4. **Standard Report**: `htmlcov/index.html`
   - Standard coverage.py output with CSS injection

## Monitoring and Metrics

### Performance Metrics

The system logs detailed performance metrics:

```
2025-07-26 09:53:51 | coverage_automation.performance | INFO | Performance: detect_vscode_coverage_run completed | duration_seconds=0.002
2025-07-26 09:53:51 | coverage_automation.performance | INFO | Performance: get_coverage_contexts completed | duration_seconds=0.045 | contexts_found=3
```

### Security Events

Security violations are logged with full context:

```
2025-07-26 09:53:51 | coverage_automation.security | ERROR | Security: Path validation failed | file_path=/path/to/file | reason=Path outside project bounds
```

## Support and Maintenance

### Component Responsibilities

- **Config**: Test pattern loading, Codecov integration
- **Watcher**: File monitoring, test context detection
- **Classifier**: Test type mapping, target analysis
- **Renderer**: Report generation, HTML sanitization
- **CLI**: User interface, workflow orchestration

### Future Enhancements

- Watch mode for continuous monitoring
- Enhanced integration with VS Code
- Additional security validations
- Performance optimization
- Extended Codecov features

## Version History

- **v2.0.0**: Modular refactoring with security and Codecov integration
- **v1.0.0**: Original monolithic implementation
