---
category: quality
complexity: medium
estimated_time: "10-15 minutes"
dependencies: []
version: "1.0"
---

# Quality Naming Conventions

Check and validate naming convention compliance across project files and code: $ARGUMENTS

## Usage Options

- `directory/` - Check naming conventions in specific directory
- `--language python|javascript|typescript|go|rust` - Language-specific rules
- `--type files|functions|variables|classes|all` - What to validate
- `--auto-suggest` - Provide rename suggestions for violations
- `--config-file path/to/config.yaml` - Use custom naming rules

## Naming Convention Standards

### Universal File Naming

**Rules Applied**:

- **kebab-case** for documentation files (`user-guide.md`, `api-reference.md`)
- **snake_case** for code files (`main_module.py`, `user_service.py`)
- **PascalCase** for class/component files (`UserController.js`, `PaymentService.go`)
- **lowercase** for package/module directories (`src/`, `docs/`, `tests/`)

### Language-Specific Conventions

#### Python

**File Names**: `snake_case.py`

- ✅ `user_service.py`, `payment_processor.py`
- ❌ `UserService.py`, `payment-processor.py`

**Class Names**: `PascalCase`

- ✅ `UserService`, `PaymentProcessor`
- ❌ `userService`, `payment_processor`

**Function Names**: `snake_case`

- ✅ `get_user_data()`, `process_payment()`
- ❌ `getUserData()`, `processPayment()`

**Variable Names**: `snake_case`

- ✅ `user_id`, `payment_amount`
- ❌ `userId`, `paymentAmount`

**Constants**: `UPPER_SNAKE_CASE`

- ✅ `MAX_RETRIES`, `DEFAULT_TIMEOUT`
- ❌ `maxRetries`, `defaultTimeout`

#### JavaScript/TypeScript

**File Names**: `kebab-case.js/ts` or `PascalCase.jsx/tsx`

- ✅ `user-service.js`, `UserComponent.tsx`
- ❌ `user_service.js`, `userComponent.jsx`

**Class Names**: `PascalCase`

- ✅ `UserService`, `PaymentProcessor`
- ❌ `userService`, `payment_processor`

**Function Names**: `camelCase`

- ✅ `getUserData()`, `processPayment()`
- ❌ `get_user_data()`, `ProcessPayment()`

**Variable Names**: `camelCase`

- ✅ `userId`, `paymentAmount`
- ❌ `user_id`, `PaymentAmount`

**Constants**: `UPPER_SNAKE_CASE`

- ✅ `MAX_RETRIES`, `DEFAULT_TIMEOUT`
- ❌ `maxRetries`, `defaultTimeout`

#### Go

**File Names**: `snake_case.go`

- ✅ `user_service.go`, `payment_processor.go`
- ❌ `UserService.go`, `payment-processor.go`

**Package Names**: `lowercase`

- ✅ `userservice`, `paymentprocessor`
- ❌ `UserService`, `payment_processor`

**Function/Method Names**: `PascalCase` (public) or `camelCase` (private)

- ✅ `GetUserData()`, `processPayment()`
- ❌ `getUserData()`, `ProcessPayment()` (for private)

#### Rust

**File Names**: `snake_case.rs`

- ✅ `user_service.rs`, `payment_processor.rs`
- ❌ `UserService.rs`, `payment-processor.rs`

**Function Names**: `snake_case`

- ✅ `get_user_data()`, `process_payment()`
- ❌ `getUserData()`, `ProcessPayment()`

**Struct Names**: `PascalCase`

- ✅ `UserService`, `PaymentProcessor`
- ❌ `userService`, `payment_processor`

## Implementation

### 1. File Detection and Analysis

```bash
analyze_naming_conventions() {
    local target="$1"
    local language="$2"
    local type="$3"
    
    echo "🔍 Analyzing naming conventions in: $target"
    echo "Language: ${language:-auto-detect}"
    echo "Type: ${type:-all}"
    
    # Detect files to analyze
    if [ -f "$target" ]; then
        analyze_single_file "$target" "$language"
    elif [ -d "$target" ]; then
        analyze_directory "$target" "$language" "$type"
    else
        echo "❌ Target not found: $target"
        return 1
    fi
}

analyze_directory() {
    local dir="$1"
    local language="$2"
    local type="$3"
    
    local total_files=0
    local violations=0
    
    # Find relevant files
    find "$dir" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" -o -name "*.md" \) | while read -r file; do
        total_files=$((total_files + 1))
        
        # Auto-detect language if not specified
        local file_lang="$language"
        if [ -z "$file_lang" ]; then
            file_lang=$(detect_language "$file")
        fi
        
        # Analyze file
        local file_violations=$(analyze_single_file "$file" "$file_lang")
        violations=$((violations + file_violations))
    done
    
    echo "📊 Summary: $total_files files analyzed, $violations violations found"
}
```

### 2. Language Detection

```bash
detect_language() {
    local file="$1"
    local extension="${file##*.}"
    
    case "$extension" in
        py) echo "python" ;;
        js|jsx) echo "javascript" ;;
        ts|tsx) echo "typescript" ;;
        go) echo "go" ;;
        rs) echo "rust" ;;
        md) echo "markdown" ;;
        *) echo "generic" ;;
    esac
}
```

### 3. File Name Validation

```bash
validate_file_naming() {
    local file="$1"
    local language="$2"
    local filename=$(basename "$file")
    local name_without_ext="${filename%.*}"
    
    echo "📁 Checking file name: $filename"
    
    case "$language" in
        python)
            if [[ "$name_without_ext" =~ ^[a-z][a-z0-9_]*$ ]]; then
                echo "✅ Python file naming compliant"
                return 0
            else
                echo "❌ Python files should use snake_case"
                suggest_python_filename "$name_without_ext"
                return 1
            fi
            ;;
        javascript|typescript)
            if [[ "$name_without_ext" =~ ^[a-z][a-z0-9-]*$ ]] || [[ "$name_without_ext" =~ ^[A-Z][A-Za-z0-9]*$ ]]; then
                echo "✅ JS/TS file naming compliant"
                return 0
            else
                echo "❌ JS/TS files should use kebab-case or PascalCase"
                suggest_js_filename "$name_without_ext"
                return 1
            fi
            ;;
        go)
            if [[ "$name_without_ext" =~ ^[a-z][a-z0-9_]*$ ]]; then
                echo "✅ Go file naming compliant"
                return 0
            else
                echo "❌ Go files should use snake_case"
                suggest_go_filename "$name_without_ext"
                return 1
            fi
            ;;
        rust)
            if [[ "$name_without_ext" =~ ^[a-z][a-z0-9_]*$ ]]; then
                echo "✅ Rust file naming compliant"
                return 0
            else
                echo "❌ Rust files should use snake_case"
                suggest_rust_filename "$name_without_ext"
                return 1
            fi
            ;;
        markdown)
            if [[ "$name_without_ext" =~ ^[a-z][a-z0-9-]*$ ]] || [[ "$name_without_ext" =~ ^[A-Z][A-Z0-9_]*$ ]]; then
                echo "✅ Markdown file naming compliant"
                return 0
            else
                echo "❌ Markdown files should use kebab-case"
                suggest_markdown_filename "$name_without_ext"
                return 1
            fi
            ;;
    esac
}
```

### 4. Code Content Analysis

```bash
analyze_code_naming() {
    local file="$1"
    local language="$2"
    
    echo "🔍 Analyzing code naming in: $(basename "$file")"
    
    case "$language" in
        python)
            analyze_python_naming "$file"
            ;;
        javascript|typescript)
            analyze_js_naming "$file"
            ;;
        go)
            analyze_go_naming "$file"
            ;;
        rust)
            analyze_rust_naming "$file"
            ;;
    esac
}

analyze_python_naming() {
    local file="$1"
    local violations=0
    
    # Check class names (should be PascalCase)
    grep -n "^class " "$file" | while read -r line; do
        local class_name=$(echo "$line" | sed -n 's/.*class \([A-Za-z_][A-Za-z0-9_]*\).*/\1/p')
        if [[ "$class_name" =~ ^[A-Z][A-Za-z0-9]*$ ]]; then
            echo "✅ Class name compliant: $class_name"
        else
            echo "❌ Class should be PascalCase: $class_name"
            violations=$((violations + 1))
        fi
    done
    
    # Check function names (should be snake_case)
    grep -n "^def " "$file" | while read -r line; do
        local func_name=$(echo "$line" | sed -n 's/.*def \([A-Za-z_][A-Za-z0-9_]*\).*/\1/p')
        if [[ "$func_name" =~ ^[a-z][a-z0-9_]*$ ]]; then
            echo "✅ Function name compliant: $func_name"
        else
            echo "❌ Function should be snake_case: $func_name"
            violations=$((violations + 1))
        fi
    done
    
    # Check constants (should be UPPER_SNAKE_CASE)
    grep -n "^[A-Z_][A-Z0-9_]* =" "$file" | while read -r line; do
        local const_name=$(echo "$line" | sed -n 's/^\([A-Z_][A-Z0-9_]*\) =.*/\1/p')
        if [[ "$const_name" =~ ^[A-Z][A-Z0-9_]*$ ]]; then
            echo "✅ Constant name compliant: $const_name"
        else
            echo "❌ Constant should be UPPER_SNAKE_CASE: $const_name"
            violations=$((violations + 1))
        fi
    done
    
    return $violations
}
```

### 5. Suggestion Generation

```bash
suggest_python_filename() {
    local name="$1"
    local suggestion
    
    # Convert PascalCase to snake_case
    suggestion=$(echo "$name" | sed 's/\([A-Z]\)/_\1/g' | sed 's/^_//' | tr '[:upper:]' '[:lower:]')
    
    # Convert kebab-case to snake_case
    suggestion=$(echo "$suggestion" | tr '-' '_')
    
    echo "💡 Suggested name: $suggestion.py"
}

suggest_js_filename() {
    local name="$1"
    local suggestion
    
    # Convert snake_case to kebab-case
    suggestion=$(echo "$name" | tr '_' '-' | tr '[:upper:]' '[:lower:]')
    
    echo "💡 Suggested name: $suggestion.js"
}

suggest_class_name() {
    local name="$1"
    local language="$2"
    local suggestion
    
    case "$language" in
        python|javascript|typescript|go|rust)
            # Convert to PascalCase
            suggestion=$(echo "$name" | sed 's/_\([a-z]\)/\U\1/g' | sed 's/^[a-z]/\U&/')
            echo "💡 Suggested class name: $suggestion"
            ;;
    esac
}

suggest_function_name() {
    local name="$1"
    local language="$2"
    local suggestion
    
    case "$language" in
        python|rust)
            # Convert to snake_case
            suggestion=$(echo "$name" | sed 's/\([A-Z]\)/_\1/g' | sed 's/^_//' | tr '[:upper:]' '[:lower:]')
            echo "💡 Suggested function name: $suggestion"
            ;;
        javascript|typescript)
            # Convert to camelCase
            suggestion=$(echo "$name" | sed 's/_\([a-z]\)/\U\1/g' | sed 's/^[A-Z]/\L&/')
            echo "💡 Suggested function name: $suggestion"
            ;;
    esac
}
```

### 6. Configuration Support

```bash
load_naming_config() {
    local config_file="$1"
    
    if [ -f "$config_file" ]; then
        echo "📋 Loading naming configuration from: $config_file"
        # Parse YAML config (simplified)
        source "$config_file" 2>/dev/null || echo "⚠️  Config file format not supported"
    else
        echo "📋 Using default naming conventions"
    fi
}
```

## Configuration File Example

```yaml
# .naming-conventions.yaml
naming_conventions:
  python:
    files: snake_case
    classes: PascalCase
    functions: snake_case
    variables: snake_case
    constants: UPPER_SNAKE_CASE
  
  javascript:
    files: kebab-case
    classes: PascalCase
    functions: camelCase
    variables: camelCase
    constants: UPPER_SNAKE_CASE
  
  documentation:
    files: kebab-case
    sections: title-case
  
  exceptions:
    files:
      - "README.md"
      - "CHANGELOG.md"
      - "__init__.py"
    patterns:
      - "test_*.py"  # Test files can have test_ prefix
```

## Examples

```bash
# Check all files in directory
/universal:quality-naming-conventions src/

# Python-specific validation
/universal:quality-naming-conventions src/ --language python

# Check only function names
/universal:quality-naming-conventions src/ --type functions --auto-suggest

# Use custom configuration
/universal:quality-naming-conventions . --config-file .naming-conventions.yaml
```

## Integration with Development Workflow

```bash
# Complete code quality workflow
/universal:quality-naming-conventions src/      # Check naming conventions
/universal:quality-format-code src/             # Apply formatting
/universal:quality-lint-check src/              # Lint code
/universal:quality-precommit-validate           # Final validation
```

---

*This command provides universal naming convention validation that adapts to different programming languages while maintaining consistency and readability.*
