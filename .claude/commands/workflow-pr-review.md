---
category: workflow
complexity: high
estimated_time: "20-45 minutes"
dependencies: ["workflow-review-cycle", "validation-precommit"]
sub_commands: ["validation-precommit", "workflow-review-cycle"]
version: "1.0"
models_required: ["zen", "consensus"]
---

# Workflow PR Review

Comprehensive GitHub PR review with multi-agent analysis, testing validation, and edge case discovery: $ARGUMENTS

## Usage Options

- `<pr-url>` - Full comprehensive PR review (default: thorough mode)
- `<pr-url> quick` - Essential review without extensive multi-agent analysis
- `<pr-url> security-focus` - Security-focused review with additional security agents
- `<pr-url> performance-focus` - Performance-focused review with optimization analysis

## Prerequisites

### Environment Prerequisites Validation

1. **Validate PR Review Environment**:

   ```bash
   # MANDATORY: Validate environment before review
   poetry run python src/utils/setup_validator.py --scope pr-review
   ```

2. **Required Access**:
   - GitHub API access for PR data fetching
   - Zen MCP Server running for agent orchestration
   - Context7 server for codebase analysis (if available)

3. **File Change Logging** (MANDATORY):
   - Log ALL file changes to `docs/planning/claude-file-change-log.md`
   - Format: `YYYY-MM-DD HH:MM:SS | CHANGE_TYPE | RELATIVE_FILE_PATH`

## Instructions

### Step 1: PR Context Analysis

1. **Extract PR Information**:
   - Parse GitHub PR URL: $ARGUMENTS
   - Use GitHub CLI or API to fetch:
     - PR metadata (title, description, author, base/head branches)
     - File changes and diffs
     - Existing comments and review status
     - CI/CD status and checks

2. **Codebase Context Analysis**:
   - If Context7 available: `/context7:get-context <relevant-packages>`
   - Analyze project structure and conventions from CLAUDE.md
   - Identify related code patterns and dependencies
   - Review existing test patterns and coverage

### Step 2: Comprehensive Quality Gate Validation

1. **Run Pre-commit Validation**:

   ```bash
   /project:validation-precommit
   ```

2. **PR-Specific Validation**:
   - **File-Type Specific Linting** for all changed files:
     - Markdown: `markdownlint` on changed .md files
     - YAML: `yamllint` on changed .yml/.yaml files
     - Python: `black --check`, `ruff check`, `mypy` on changed .py files

   - **Security Analysis**:
     - Run `bandit` on changed Python files
     - Check for secrets/credentials in diffs
     - Validate dependency changes with `safety check`

   - **Development Standards**:
     - Naming conventions compliance
     - Knowledge file structure (if applicable)
     - Git commit message format validation

### Step 3: Multi-Agent PR Analysis via Zen MCP Server

1. **Coordinate Edge Case Discovery**:
   Use Zen MCP Server to spawn Edge Case Hunter agent:

   ```text
   Request Zen to coordinate Edge Case Hunter with:
   - Model: deepseek-v3-0324 (primary for creative thinking)
   - Role: "Expert at finding edge cases, boundary conditions, and non-obvious failure modes"
   - Context: PR diff, existing tests, domain knowledge
   - Task: Multi-round edge case discovery:
     * Round 1: Brainstorm all possible edge cases
     * Round 2: Boundary value analysis
     * Round 3: State and concurrency analysis
     * Round 4: Integration failure scenarios
     * Round 5: Synthesize comprehensive edge case test scenarios
   ```

2. **Security Analysis Coordination**:
   Use Zen MCP Server for Security Auditor agent (if security-focus or thorough):

   ```text
   Request Zen to coordinate Security Auditor with:
   - Model: claude-opus-4 (primary for security expertise)
   - Role: "Senior security engineer specializing in application security"
   - Context: OWASP guidelines, security best practices, PR changes
   - Task:
     * Authentication/authorization review of changes
     * Input validation and sanitization analysis
     * Dependency security assessment
     * OWASP Top 10 compliance check
     * Generate security test scenarios
   ```

3. **Performance Analysis Coordination**:
   Use Zen MCP Server for Performance Analyst (if performance-focus or thorough):

   ```text
   Request Zen to coordinate Performance Analyst with:
   - Model: o3 (primary for systematic analysis)
   - Role: "Performance engineer focused on optimization and efficiency"
   - Context: Performance benchmarks, scalability requirements, PR changes
   - Task:
     * Algorithmic complexity analysis of changes
     * Database query optimization review
     * Memory and CPU usage impact assessment
     * Caching and performance pattern analysis
     * Generate performance test scenarios
   ```

4. **Test Architecture Review**:
   Use Zen MCP Server for Test Architect agent:

   ```text
   Request Zen to coordinate Test Architect with:
   - Model: deepseek-v3-0324 (primary for test strategy)
   - Role: "Test-driven development expert ensuring comprehensive coverage"
   - Context: Existing test patterns, testing frameworks, PR changes
   - Task:
     * Analyze test coverage gaps for changed code
     * Review test quality and patterns
     * Identify missing test scenarios from Edge Case Hunter findings
     * Validate integration test requirements
     * Generate comprehensive test enhancement plan
   ```

### Step 4: Multi-Agent Consensus via Zen Consensus

1. **Coordinate Multi-Agent Synthesis**:
   Use Zen Consensus tool to synthesize findings:

   ```text
   /zen:consensus

   Proposal: "Should this PR be approved for merge based on comprehensive analysis?"

   Models to consult:
   - claude-opus-4 (for overall code quality and architecture assessment)
   - o3 (for systematic risk analysis and edge case validation)
   - deepseek-v3-0324 (for implementation details and test adequacy)

   Provide each model with:
   - PR context and changes
   - Findings from specialized agents (Edge Case Hunter, Security Auditor, etc.)
   - Quality gate results
   - Test coverage analysis
   ```

2. **Consensus Evaluation Criteria**:
   - **Code Quality**: Architecture, maintainability, adherence to standards
   - **Security Posture**: Vulnerability assessment, security best practices
   - **Test Adequacy**: Coverage, edge cases, integration scenarios  
   - **Performance Impact**: Efficiency, scalability, resource usage
   - **Risk Assessment**: Potential failure modes, deployment risks

### Step 5: Testing Execution and Validation

1. **Execute Enhanced Test Suite**:
   - Run existing tests: `poetry run pytest -v --cov=src`
   - Execute security tests from Security Auditor recommendations
   - Run edge case scenarios from Edge Case Hunter analysis
   - Validate performance benchmarks if applicable

2. **Integration Testing**:
   - Test with external dependencies (Qdrant, Azure AI)
   - Validate multi-agent coordination if agents modified
   - Check UI/API integration points affected by changes

### Step 6: Generate Comprehensive PR Review Report

Generate detailed review report in markdown format:

```markdown
# PR Review Report: [PR Title]

**PR URL**: $ARGUMENTS
**Review Date**: [Current Date]
**Review Mode**: [thorough/quick/security-focus/performance-focus]

## PR Summary
- **Author**: [Author]
- **Base Branch**: [branch] → **Head Branch**: [branch]  
- **Files Changed**: [count] files, [additions] additions, [deletions] deletions
- **CI/CD Status**: [status]

## Quality Gate Results
### Automated Compliance
- [ ] Pre-commit hooks: Pass/Fail
- [ ] File-specific linting: Pass/Fail  
- [ ] Security scans: Pass/Fail
- [ ] Development standards: Pass/Fail

### Test Results  
- **Unit Tests**: [X/Y passed] - Coverage: [%]
- **Integration Tests**: [X/Y passed]
- **Security Tests**: [results]
- **Performance Tests**: [results if applicable]

## Multi-Agent Analysis Summary

### Edge Case Hunter Findings
- **Edge Cases Identified**: [count]
- **Critical Scenarios**: [list]
- **Test Recommendations**: [scenarios]
- **Risk Level**: [Low/Medium/High]

### Security Auditor Assessment (if applicable)
- **Security Issues**: [count and severity]
- **OWASP Compliance**: [status]
- **Authentication/Authorization**: [assessment]
- **Recommendations**: [security improvements]

### Performance Analyst Review (if applicable)  
- **Performance Impact**: [assessment]
- **Algorithmic Complexity**: [analysis]
- **Resource Usage**: [memory/CPU impact]
- **Optimization Opportunities**: [recommendations]

### Test Architect Evaluation
- **Coverage Analysis**: [current vs recommended]
- **Test Quality**: [assessment]
- **Missing Scenarios**: [gaps identified]
- **Test Enhancement Plan**: [recommendations]

## Multi-Agent Consensus Result
### Final Recommendation: **[APPROVE / REQUEST CHANGES / COMMENT]**

### Agent Agreement Summary:
- **Claude Opus 4**: [vote and rationale]
- **O3**: [vote and rationale]  
- **DeepSeek V3**: [vote and rationale]

### Consensus Rationale:
[Synthesized reasoning from all agents]

## Required Changes (if any)
1. [Specific change required with agent consensus]
2. [Another required change]

## Recommendations for Future
- [Improvement suggestions from agents]
- [Process improvements identified]

## Review Confidence: [High/Medium/Low]
**Based on**: [Quality gates + Agent consensus + Test coverage + Risk assessment]
```

## Enhanced Completion Criteria

The PR review is complete when:

1. **All quality gates** pass successfully
2. **Multi-agent analysis** is complete with specialized agent findings
3. **Consensus evaluation** reaches agreement on merge recommendation
4. **Test execution** validates enhanced test scenarios
5. **Comprehensive report** is generated with actionable findings
6. **Clear recommendation** (approve/request changes/comment) is provided

## Error Handling

- **GitHub API issues**: Retry with exponential backoff, fallback to manual diff analysis
- **Zen MCP Server unavailable**: Fall back to single-agent analysis with Claude
- **Agent coordination failures**: Continue with available agents, note limitations
- **Test failures**: Document failures and include in risk assessment
- **Quality gate failures**: Block approval recommendation until resolved

## Examples

```bash
# Full comprehensive review
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/143

# Quick essential review  
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/147 quick

# Security-focused review
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/148 security-focus

# Performance-focused review
/project:workflow-pr-review https://github.com/williaby/PromptCraft/pull/149 performance-focus
```

## Integration Notes

This command leverages existing project infrastructure:

- **Zen MCP Server**: For agent orchestration and coordination
- **Existing workflow commands**: validation-precommit, workflow-review-cycle patterns
- **Context7 integration**: For codebase understanding when available
- **Project standards**: CLAUDE.md compliance, style guides, quality gates

The command extends the project's multi-agent capabilities to GitHub PR review while maintaining
consistency with existing workflow patterns and development standards.
