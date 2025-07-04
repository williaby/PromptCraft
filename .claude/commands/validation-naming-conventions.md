# Validate Naming Conventions

Check entire project or specific directory for naming convention compliance per development guidelines: $ARGUMENTS

## Expected Arguments

- **Target Path**: Directory or file path to validate (e.g., `src/agents/`, `knowledge/`, or specific file)

## Analysis Required

1. **Convention Detection**: Identify file/directory types and applicable naming rules
2. **Pattern Matching**: Validate against development.md naming conventions
3. **Cross-Reference Validation**: Check consistency across related components
4. **Integration Point Validation**: Verify naming affects imports, configs, and references
5. **Exception Handling**: Identify legitimate exceptions vs. violations

## Naming Convention Rules by Component

### Core Components
| Component | Convention | Pattern | Example |
|-----------|------------|---------|---------|
| Agent ID | snake_case | `[a-z][a-z0-9_]*` | `security_agent`, `tax_prep_agent` |
| Agent Classes | PascalCase + "Agent" | `[A-Z][a-zA-Z0-9]*Agent` | `SecurityAgent`, `TaxPrepAgent` |
| Knowledge Folders | snake_case (matches agent_id) | `/knowledge/[a-z][a-z0-9_]*/` | `/knowledge/security_agent/` |
| Knowledge Files | kebab-case.md | `[a-z][a-z0-9-]*.md` | `auth-best-practices.md` |

### Code & Files
| Component | Convention | Pattern | Example |
|-----------|------------|---------|---------|
| Python Files | snake_case.py | `[a-z][a-z0-9_]*.py` | `query_counselor.py` |
| Python Classes | PascalCase | `[A-Z][a-zA-Z0-9]*` | `BaseAgent`, `QueryCounselor` |
| Python Functions | snake_case() | `[a-z][a-z0-9_]*` | `process_query()` |
| Python Constants | UPPER_SNAKE_CASE | `[A-Z][A-Z0-9_]*` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private Methods | _snake_case() | `_[a-z][a-z0-9_]*` | `_validate_input()` |
| Test Files | test_snake_case.py | `test_[a-z][a-z0-9_]*.py` | `test_security_agent.py` |

### Infrastructure & Deployment
| Component | Convention | Pattern | Example |
|-----------|------------|---------|---------|
| Docker Services | kebab-case | `[a-z][a-z0-9-]*` | `gradio-ui`, `zen-mcp-server` |
| Environment Variables | UPPER_SNAKE_CASE | `[A-Z][A-Z0-9_]*` | `QDRANT_HOST`, `AZURE_KEY_VAULT_URL` |
| Configuration Files | snake_case.ext | `[a-z][a-z0-9_]*.yaml` | `agents_config.yaml` |

### Git & Development
| Component | Convention | Pattern | Example |
|-----------|------------|---------|---------|
| Git Branches | kebab-case with prefixes | `(feature\|bugfix\|hotfix)/[a-z0-9-]*` | `feature/add-security-agent` |
| Git Tags | v + semver | `v[0-9]+\.[0-9]+\.[0-9]+` | `v1.2.3`, `v2.0.0-beta.1` |

### API & Web
| Component | Convention | Pattern | Example |
|-----------|------------|---------|---------|
| REST Endpoints | kebab-case, plural | `/api/v[0-9]+/[a-z][a-z0-9-]*` | `/api/v1/agents`, `/api/v1/claude-md` |
| URL Parameters | snake_case | `[a-z][a-z0-9_]*` | `?agent_id=security_agent` |
| JSON Fields | snake_case | `[a-z][a-z0-9_]*` | `{"agent_id": "security_agent"}` |

## Validation Logic

### Directory Structure Analysis
1. **Agent Directories**: Validate `/knowledge/{agent_id}/` naming
2. **Source Files**: Check `src/` hierarchy for Python naming
3. **Test Files**: Validate test file naming and organization
4. **Configuration Files**: Check config file naming patterns

### Cross-Reference Validation
1. **Agent ID Consistency**: Verify agent_id matches across:
   - Knowledge folder name
   - YAML front matter
   - Python class name conversion
   - Registry entries
   - Qdrant collection names

2. **Import Path Consistency**: Check Python module imports match file names
3. **Configuration References**: Validate config file references use correct names

### Pattern Matching Implementation
```regex
# Agent ID Pattern
^[a-z][a-z0-9_]*$

# Python Class Pattern (with Agent suffix)
^[A-Z][a-zA-Z0-9]*Agent$

# Kebab Case Pattern (files)
^[a-z][a-z0-9-]*\.md$

# Python File Pattern
^[a-z][a-z0-9_]*\.py$

# Test File Pattern
^test_[a-z][a-z0-9_]*\.py$

# Environment Variable Pattern
^[A-Z][A-Z0-9_]*$
```

## Validation Categories

### Critical Violations (Must Fix)
- Agent ID inconsistency across components
- Python class naming violates PascalCase
- Import paths don't match file names
- Configuration references broken due to naming

### Standard Violations (Should Fix)
- File names don't follow case conventions
- Function/method names violate snake_case
- Constants not in UPPER_SNAKE_CASE
- Test files don't follow naming pattern

### Style Violations (Consider Fixing)
- Inconsistent spacing in compound names
- Non-descriptive single-letter variables
- Overly long names that could be simplified
- Mixed naming styles within same file

## Required Output Format

### Validation Report Structure

```markdown
# Naming Convention Validation Report

## Scope: {target_path}

### 🚨 CRITICAL VIOLATIONS
**Agent ID Inconsistencies:**
- knowledge/security_agent/ → class SecurityAgentHandler (expected: SecurityAgent)
- YAML agent_id: sec_agent (expected: security_agent)

**Import Path Mismatches:**
- src/agents/securityAgent.py → should be: src/agents/security_agent.py
- import references will fail

### ⚠️ STANDARD VIOLATIONS
**File Naming:**
- knowledge/security_agent/Auth_Best_Practices.md → auth-best-practices.md
- src/utils/queryProcessor.py → query_processor.py

**Function Naming:**
- def processQuery() → process_query()
- def GetUserPrefs() → get_user_prefs()

**Constant Naming:**
- max_retries = 3 → MAX_RETRIES = 3
- default_timeout = 30 → DEFAULT_TIMEOUT = 30

### 📝 STYLE VIOLATIONS
**Descriptive Naming:**
- Variable 'a' in loop → consider 'agent' or 'item'
- Method 'proc()' → consider 'process()' or 'process_query()'

### ✅ COMPLIANT COMPONENTS
- knowledge/create_agent/ structure: Perfect
- src/agents/base_agent.py: Follows all conventions
- test_query_counselor.py: Proper test naming

### 📊 COMPLIANCE SUMMARY
- **Critical**: 3 violations (must fix for functionality)
- **Standard**: 8 violations (should fix for consistency)
- **Style**: 5 violations (consider fixing for clarity)
- **Compliant**: 47 components following conventions

**Overall Score**: 85% compliant (52/60 total components)

### 🔧 RECOMMENDED FIXES
1. **Priority 1 (Critical)**:
   ```bash
   # Fix agent ID inconsistency
   mv src/agents/securityAgent.py src/agents/security_agent.py
   # Update class name: SecurityAgentHandler → SecurityAgent
   # Fix YAML agent_id fields
   ```

2. **Priority 2 (Standard)**:
   ```bash
   # Fix file naming
   mv knowledge/security_agent/Auth_Best_Practices.md knowledge/security_agent/auth-best-practices.md
   # Update function names in src/core/query_counselor.py
   ```

3. **Priority 3 (Style)**:
   - Review variable naming in loops
   - Consider expanding abbreviated method names
```

## Validation Scope Options

### Full Project Validation
- Scan entire repository for naming violations
- Cross-reference all component relationships
- Generate comprehensive compliance report

### Directory-Specific Validation
- Focus on specific component type (agents, knowledge, tests)
- Detailed analysis of related naming patterns
- Targeted recommendations for improvement

### Component-Specific Validation
- Single file or component analysis
- Context-aware validation (e.g., test files, config files)
- Integration impact assessment

## Important Notes

- Validation enforces docs/planning/development.md standards strictly
- Critical violations break functionality and must be fixed immediately
- Standard violations should be addressed during development cycles
- Style violations are suggestions for improved maintainability
- Cross-reference validation ensures naming consistency affects all integration points
- Provides automated fix suggestions where possible
- Considers legitimate exceptions (e.g., third-party library conventions)
