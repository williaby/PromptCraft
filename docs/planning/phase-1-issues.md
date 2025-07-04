<!-- markdownlint-disable MD024 -->
# Phase 1: Foundation & Journey 1 Issues

This document contains detailed issues for **Milestone 1: Foundation & Journey 1 (Weeks 1-4)**.

## Related Documentation

- [Milestone Overview](milestones.md#milestone-1-foundation--journey-1-weeks-1-4)
- [Technical Specification - Phase 1](ts_1.md)
- [Four Journeys - Journey 1](four_journeys.md#journey-1-smart-templates)

---

## **Issue #1: Development Environment Setup**

**Worktree**: `foundation`
**Estimated Time**: 6 hours

### Description

Establish complete development environment with proper tooling, security validation, and
dependency management following project requirements.

### Issue Acceptance Criteria

- [ ] Python 3.11+ and Poetry installed and working
- [ ] Docker and Docker Compose operational (20.10+, 2.0+)
- [ ] GPG key generated and configured for .env encryption
- [ ] SSH key generated and configured for signed commits
- [ ] Pre-commit hooks installed and all checks passing
- [ ] Environment validation script passes
- [ ] Development containers start successfully

### Issue Dependencies

- Fresh clone of repository
- Admin/sudo access for installations
- Internet connection for downloads

### Issue Testing

```bash
# Complete environment validation
make setup
poetry run python src/utils/setup_validator.py

# Container startup test
make dev
curl http://localhost:7860/health

```

### Issue References

- CLAUDE.md security requirements
- `src/utils/encryption.py` - existing implementation pattern

---

## **Issue #2: Core Configuration System**

**Worktree**: `backend`
**Estimated Time**: 5 hours

### Description

Implement centralized configuration system with environment-specific settings, encrypted
secrets management, and validation.

### Issue Acceptance Criteria

- [ ] Configuration classes defined with Pydantic schema
- [ ] Environment-specific configs working (dev, staging, prod)
- [ ] .env file encryption/decryption integrated with settings loading
- [ ] All configuration parameters validated with appropriate error messages
- [ ] Default configurations allow immediate development start
- [ ] Health check endpoints return configuration status
- [ ] Sensitive values never logged or exposed in error messages

### Issue Dependencies

- Issue #1 completed (Development Environment Setup)
- `.env` file created based on provided example

### Issue Testing

```bash
# Configuration loading test
poetry run python -c "from src.config.settings import settings; print(f'Environment: {settings.environment}')"

# Health check test
poetry run uvicorn src.main:app --reload &
curl http://localhost:8000/health

```

### Issue References

- Pydantic Settings documentation
- `src/utils/encryption.py` integration pattern

---

## **Issue #3: Docker Development Environment**

**Worktree**: `foundation`
**Estimated Time**: 7 hours

### Description

Create a complete Docker development environment with all services, proper networking, and health checks for local development.

### Issue Acceptance Criteria

- [ ] Multi-stage Dockerfile builds successfully
- [ ] All services start and pass health checks (Gradio, FastAPI, Qdrant, Redis)
- [ ] Service-to-service communication working
- [ ] Volume mounts configured for hot reload during development
- [ ] Non-root user execution working (promptcraft:1000)
- [ ] Makefile commands operational for all common operations
- [ ] Container logs accessible and properly formatted
- [ ] Resource limits configured and respected

### TODO Items for Project Owner

- [ ] **TODO**: Provide Zen MCP Server Docker image and configuration when available
- [ ] **TODO**: Clarify production deployment target (Docker Swarm? Kubernetes? Single server?)
- [ ] **TODO**: Specify production resource requirements and scaling strategy

### Issue Dependencies

- Issue #2 completed (Core Configuration System)
- Docker and Docker Compose installed

### Issue Testing

```bash
# Start development environment
make dev

# Test all services
curl http://localhost:7860/health  # App health check
curl http://localhost:6333/health  # Qdrant health check
redis-cli -h localhost ping        # Redis connectivity

```

### Issue References

- Docker best practices documentation
- Docker Compose networking guide
- Multi-stage builds documentation

---

## **Issue #4: C.R.E.A.T.E. Framework Engine**

**Worktree**: `backend`
**Estimated Time**: 8 hours

### Description

Implement the core C.R.E.A.T.E. framework processor that transforms basic prompts into
comprehensive, structured outputs using the established methodology.

### Issue Acceptance Criteria

- [ ] `CreateProcessor` class implemented matching ts_1.md API contract
- [ ] All six C.R.E.A.T.E. components functional with Zen MCP integration
- [ ] Template system supporting 20+ domain-specific templates
- [ ] Input validation and sanitization preventing injection attacks
- [ ] Response time < 3 seconds for simple prompts (ts_1.md requirement)
- [ ] Unit tests with 90%+ coverage matching testing standards
- [ ] Integration with FastAPI endpoints following exact schema
- [ ] Error handling for all Zen MCP failure scenarios

### Issue Dependencies

- Issue #2 completed (Core Configuration System)
- Zen MCP Server deployed and accessible
- Template storage system designed

### Issue Testing

```bash
# Unit tests for C.R.E.A.T.E. components
poetry run pytest tests/unit/test_create_processor.py -v --cov=src.core.create_processor

# Performance validation
curl -X POST http://localhost:8000/api/v1/create \
  -H "Content-Type: application/json" \
  -d '{"input_prompt": "test", "domain": "security"}'

```

### Issue References

- `knowledge/create/00_quick-reference.md` - C.R.E.A.T.E. framework documentation
- `docs/planning/ts_1.md` - Phase 1 technical specifications

---

## **Issue #5: Gradio UI Foundation**

**Worktree**: `frontend`
**Estimated Time**: 6 hours

### Description

Create the foundational Gradio interface for Journey 1 with prompt input, enhancement
display, and user feedback collection. Reuses 70% of existing `promptcraft_app.py` from
PromptCraft repository.

### Issue Acceptance Criteria

- [ ] Gradio interface matching ts_1.md UI specifications
- [ ] Real-time prompt enhancement with < 5s response display
- [ ] C.R.E.A.T.E. component breakdown with collapsible sections
- [ ] Copy/export functionality for enhanced prompts
- [ ] User feedback collection (thumbs up/down, ratings)
- [ ] Responsive design working on mobile/tablet/desktop
- [ ] Loading states and comprehensive error handling
- [ ] Accessibility compliance (WCAG 2.1 AA)

### TODO Items for Project Owner

- [ ] **TODO**: Provide access to existing PromptCraft repository with promptcraft_app.py
- [ ] **TODO**: Define user feedback collection requirements and storage

### Issue Dependencies

- Issue #4 completed (C.R.E.A.T.E. Framework Engine)
- C.R.E.A.T.E. API endpoints available and functional
- Template system operational

### Issue Testing

```bash
# UI functionality testing
poetry run python src/ui/journey1_interface.py

```

### Issue References

- [Gradio documentation](https://gradio.app/docs/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

## **Issue #6: Template Library System**

**Worktree**: `knowledge`
**Estimated Time**: 5 hours

### Description

Create a comprehensive template library for common use cases with proper categorization,
search, filtering, and customization capabilities.

### Issue Acceptance Criteria

- [ ] Template categories: Communication, Documentation, Code, Analysis, Creative (5 core categories)
- [ ] 25+ professional templates covering common business and technical scenarios
- [ ] Template metadata with tags, difficulty levels, and use case descriptions
- [ ] Search and filtering functionality by category, tags, and complexity
- [ ] Template customization interface allowing parameter substitution
- [ ] Import/export for custom templates with validation
- [ ] Template versioning and update tracking
- [ ] Usage analytics and template performance metrics

### Issue Dependencies

- Issue #4 completed (C.R.E.A.T.E. Framework Engine)
- Template storage directory structure created
- FastAPI router integration available

### Issue Testing

```bash
# Template library testing
poetry run pytest tests/unit/test_template_library.py -v

# Template search testing
curl "http://localhost:8000/api/v1/templates/search?category=communication"

```

### Issue References

- [YAML specification](https://yaml.org/spec/1.2/spec.html)
- [FastAPI documentation](https://fastapi.tiangolo.com/)

---

## **Issue #7: Test Framework Implementation**

**Worktree**: `testing`
**Estimated Time**: 6 hours

### Description

Establish comprehensive testing framework with unit, integration, and end-to-end tests,
ensuring 80%+ coverage and reliable CI/CD validation.

### Issue Acceptance Criteria

- [ ] Pytest configuration with coverage reporting (HTML and terminal)
- [ ] Unit test suite for core components: CreateProcessor, TemplateLibrary, Journey1Interface
- [ ] Integration tests for API endpoints with real HTTP calls
- [ ] End-to-end tests covering complete user workflows
- [ ] Performance benchmarks with locust (10 concurrent users, < 3s response time)
- [ ] Security testing integration (bandit, safety checks)
- [ ] Test fixtures for templates, user inputs, and expected outputs
- [ ] CI/CD pipeline integration matching ledgerbase patterns

### Issue Dependencies

- Issues #4, #5, #6 completed (all components to test)
- Zen MCP Server accessible for integration testing
- Template library populated with test data

### Issue Testing

```bash
# Run complete test suite
make test

# Coverage validation
poetry run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

```

### Issue References

- [pytest documentation](https://docs.pytest.org/)
- Load testing best practices

---

## **Issue #8: Journey 1 Validation & Polish**

**Worktree**: `frontend`
**Estimated Time**: 7 hours

### Description

Complete Journey 1 with comprehensive validation, user experience polish, error handling, and production readiness checks.

### Issue Acceptance Criteria

- [ ] All user journeys tested with real user scenarios (5+ test users)
- [ ] Error handling for all identified edge cases with user-friendly messages
- [ ] Performance optimization: 95th percentile < 2s response time
- [ ] Accessibility compliance: WCAG 2.1 AA level validated
- [ ] Mobile responsiveness: fully functional on 320px+ screens
- [ ] Production configuration: environment-specific settings ready
- [ ] User documentation: help text and onboarding flow
- [ ] Analytics integration: user interaction tracking implemented

### Issue Dependencies

- Issue #7 completed (Test Framework Implementation)
- All Journey 1 components functional and tested
- Production infrastructure configuration available

### Issue Testing

```bash
# User experience validation
poetry run python tests/ux/test_user_scenarios.py

# Performance validation
poetry run pytest tests/performance/test_journey1_performance.py --benchmark-compare

```

### Issue References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- Performance best practices documentation

---

## **Issue #9: Security Implementation**

**Worktree**: `security`
**Estimated Time**: 8 hours

### Description

Implement comprehensive security measures including encryption, authentication, input validation, and security scanning integration.

### Issue Acceptance Criteria

- [ ] .env file encryption/decryption with GPG following existing pattern
- [ ] Input sanitization preventing XSS, injection attacks for all user inputs
- [ ] CORS configuration for production with specific allowed origins
- [ ] Security headers middleware (CSP, HSTS, X-Frame-Options)
- [ ] Rate limiting: 60 requests/minute per IP for API endpoints
- [ ] Dependency vulnerability scanning integrated in CI/CD
- [ ] Security testing suite with OWASP ZAP integration
- [ ] Audit logging for all security-relevant events

### Issue Dependencies

- Issue #2 completed (Core Configuration System with encryption.py)
- Production infrastructure configuration
- CI/CD pipeline access for security scanning integration

### Issue Testing

```bash
# Security validation
poetry run python src/security/validation.py

# Vulnerability scanning
poetry run safety check
poetry run bandit -r src/ -f json

```

### Issue References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- FastAPI security documentation
- Existing src/utils/encryption.py implementation

---

## **Issue #10: Production Deployment Preparation**

**Worktree**: `deployment`
**Estimated Time**: 6 hours

### Description

Prepare production deployment configuration with infrastructure as code, monitoring,
operational procedures, and deployment automation.

### Issue Acceptance Criteria

- [ ] Docker production builds optimized (multi-stage, minimal size)
- [ ] Environment-specific configurations (dev, staging, prod) working
- [ ] Health check endpoints for all services with dependency checks
- [ ] Logging configuration with structured JSON output to stdout
- [ ] Monitoring setup with Prometheus metrics and Grafana dashboards
- [ ] Backup procedures for templates, configuration, and user data
- [ ] Deployment automation with rollback capability
- [ ] Production runbook with operational procedures

### Issue Dependencies

- Issue #9 completed (Security Implementation)
- Production infrastructure (Unraid server) available
- Cloudflare tunnel configured

### Issue Testing

```bash
# Production build testing
docker build -t promptcraft:prod -f Dockerfile.prod .

# Health check validation
docker-compose -f docker-compose.prod.yml up -d
curl http://localhost:8000/health | jq .

# Deployment simulation
bash scripts/deploy.sh --dry-run --env=staging

```

### Issue References

- Docker production best practices
- Prometheus monitoring setup guide
- ts_1.md infrastructure specifications

---

## **Issue #34: Observability Infrastructure Setup**

**Worktree**: `observability`
**Estimated Time**: 8 hours

### Description

Implement comprehensive observability infrastructure including centralized logging, distributed tracing, and metrics monitoring as identified as mandatory requirements from the three-perspective analysis.

### Issue Acceptance Criteria

- [ ] ELK stack (Elasticsearch, Logstash, Kibana) or equivalent centralized logging deployed
- [ ] OpenTelemetry distributed tracing configured for all MCP service communications
- [ ] Prometheus metrics collection and Grafana dashboards for system monitoring
- [ ] Comprehensive health check endpoints for all services with dependency checks
- [ ] Real-time performance monitoring with alerting for response times and error rates
- [ ] Service mesh consideration for traffic management and circuit breakers
- [ ] Log aggregation from all containers with structured JSON format
- [ ] Alert manager configuration for critical system events

### Issue Dependencies

- Issue #3 completed (Docker Development Environment)
- Basic service architecture established
- Network connectivity between services configured

### Issue Testing

```bash
# Observability stack validation
docker-compose -f docker-compose.observability.yml up -d

# Verify log collection
curl http://localhost:5601  # Kibana dashboard
curl http://localhost:9090  # Prometheus metrics
curl http://localhost:3000  # Grafana dashboards

# Test distributed tracing
curl -X POST http://localhost:8000/api/v1/create \
  -H "Content-Type: application/json" \
  -d '{"input_prompt": "test observability", "domain": "general"}'
```

### Issue References

- ELK Stack documentation
- OpenTelemetry documentation
- Prometheus monitoring best practices
- Phase-1-feedback.md critical requirements

---

## **Issue #35: Development Environment Enhancement**

**Worktree**: `foundation`
**Estimated Time**: 6 hours

### Description

Enhance the development environment with hot reload capabilities, automated testing pipeline integration, and improved developer experience as identified in priority actions.

### Issue Acceptance Criteria

- [ ] Hot reload functionality for Python code changes without container restart
- [ ] Automated testing pipeline integration triggered on file changes
- [ ] File watching and automatic test execution for modified modules
- [ ] Development container optimization for faster startup and rebuild times
- [ ] IDE integration support (VS Code dev containers, debugger attachment)
- [ ] Local development documentation with troubleshooting guide
- [ ] Developer onboarding script for new team members
- [ ] Performance monitoring of development environment itself

### Issue Dependencies

- Issue #3 completed (Docker Development Environment)
- Issue #7 completed (Test Framework Implementation)
- Poetry and pytest configuration operational

### Issue Testing

```bash
# Hot reload testing
make dev-watch
# Modify src/core/create_processor.py and verify automatic reload

# Automated testing validation
touch src/core/test_file.py
# Verify tests run automatically

# Development environment performance
time make dev  # Should start in <30 seconds
```

### Issue References

- Docker development best practices
- Poetry hot reload configuration
- pytest-watch documentation
- VS Code dev containers guide

---

## **Issue #36: Code Reuse Architecture Setup**

**Worktree**: `architecture`
**Estimated Time**: 7 hours

### Description

Establish the foundational code reuse architecture with shared library structure, API design patterns, component versioning, and dependency management to achieve the 70% code reuse target.

### Issue Acceptance Criteria

- [ ] Shared library structure defined and implemented across repositories
- [ ] API design patterns and interface contracts established
- [ ] Component versioning strategy with semantic versioning implementation
- [ ] Dependency management system for shared components across projects
- [ ] Code reuse documentation with integration guidelines
- [ ] Automated compatibility testing between shared components
- [ ] Component registry for discovering and managing reusable modules
- [ ] Migration scripts for updating shared component versions

### Issue Dependencies

- Issue #2 completed (Core Configuration System)
- Access to ledgerbase, FISProject, .github, and PromptCraft repositories
- Poetry dependency management configured

### Issue Testing

```bash
# Shared library integration testing
poetry run python -c "from src.shared.base_interfaces import BaseProcessor; print('Shared libraries loaded')"

# Component versioning validation
poetry run python src/utils/component_version_check.py

# Dependency compatibility testing
make test-shared-components
```

### Issue References

- Semantic versioning specification
- Python packaging best practices
- ledgerbase, FISProject repository patterns
- ADR code reuse mapping (Appendix C)

---

## **Issue #37: Fallback Architecture Design**

**Worktree**: `architecture`
**Estimated Time**: 8 hours

### Description

Design and implement fallback architecture with monolithic deployment option, service consolidation plans, rollback procedures, and emergency recovery as identified in risk mitigation strategy.

### Issue Acceptance Criteria

- [ ] Monolithic deployment option designed and implemented as emergency fallback
- [ ] Service consolidation plan for reducing from 6 MCP services to core 4 services
- [ ] Rollback procedures documented and automated for rapid deployment reversion
- [ ] Emergency recovery procedures with step-by-step operational runbooks
- [ ] Graduated fallback plan implementation (Plans A, B, C, D from feedback)
- [ ] Architecture decision gates for triggering fallback scenarios
- [ ] Testing framework for validating fallback deployment options
- [ ] Performance comparison between distributed and monolithic architectures

### Issue Dependencies

- Issues #34, #35, #36 completed (observability and architecture foundation)
- Understanding of all MCP service dependencies
- Production deployment infrastructure available

### Issue Testing

```bash
# Monolithic deployment testing
docker-compose -f docker-compose.monolithic.yml up -d
curl http://localhost:8000/health

# Fallback scenario simulation
bash scripts/trigger-fallback.sh --scenario=plan-b
bash scripts/test-rollback.sh --target=previous-version

# Emergency recovery validation
bash scripts/emergency-recovery.sh --dry-run
```

### Issue References

- Phase-1-feedback.md risk mitigation strategy
- Docker Swarm vs single container deployment
- Service mesh degradation patterns
- Operational excellence best practices

---

## Implementation Notes

- All components must follow the base interface patterns
- Knowledge bases must be properly indexed in Qdrant
- Cost tracking should be implemented for all external API calls
- Error handling must be robust for MCP failures
- Performance targets: <3s average response time for Journey 1
- Focus on code reuse from existing repositories (70% target)
- All components must follow established coding standards
- Security-first approach throughout implementation
- Comprehensive documentation required for all components
- **NEW**: All 4 new priority issues must be completed before production deployment
- **NEW**: Observability infrastructure is non-negotiable for Phase 1 success
