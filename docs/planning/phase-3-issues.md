<!-- markdownlint-disable MD024 -->
# Phase 3: End-to-End Execution Issues

This document contains detailed issues for **Milestone 3: End-to-End Execution (Weeks 9-12)**.

## Related Documentation

- [Milestone Overview](milestones.md#milestone-3-end-to-end-execution-weeks-9-12)
- [Technical Specification - Phase 3](ts_3.md)
- [Four Journeys - Journey 4](four_journeys.md#journey-4-autonomous-workflows)

---

## **Issue #18: Direct Execution Engine Framework**

**Worktree**: `execution-engine`
**Estimated Time**: 8 hours

### Description

Implement the core execution engine that enables Journey 4 (Direct Execution) capabilities,
allowing agents to safely execute code, manage workflows, and coordinate with human-in-the-loop approval systems.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What types of code execution should be supported and how are they isolated?**
**A1: Docker containerized execution for Python, Node.js, shell scripts with network isolation**

**Q2: How are execution permissions managed and what security boundaries exist?**
**A2: Role-based execution policies with resource limits, file system restrictions, and approval workflows**

**Q3: What workflow state management is required for long-running executions?**
**A3: Redis-backed state persistence with checkpointing and recovery capabilities**

**Q4: How does the execution engine integrate with existing multi-agent orchestration?**
**A4: Direct integration with Zen MCP Server using execution-specific message protocols**

### Acceptance Criteria

- [ ] Containerized code execution environment with security isolation
- [ ] Multi-language support (Python, Node.js, Shell, SQL)
- [ ] Execution state persistence and recovery mechanisms
- [ ] Resource usage monitoring and limits enforcement
- [ ] Integration with Human-in-Loop MCP for approval workflows
- [ ] Execution audit logging and compliance tracking
- [ ] Real-time execution monitoring and cancellation capabilities
- [ ] Error handling and graceful failure recovery

### Technical Details

**Execution Engine Architecture:**

```python
class ExecutionEngine:
    @dataclass
    class ExecutionRequest:
        execution_id: str
        code: str
        language: Literal["python", "nodejs", "bash", "sql"]
        context: ExecutionContext
        approval_required: bool
        resource_limits: ResourceLimits
        timeout_seconds: int

    @dataclass
    class ExecutionResult:
        execution_id: str
        status: Literal["pending", "running", "completed", "failed", "cancelled"]
        output: str
        error: Optional[str]
        resource_usage: ResourceUsage
        duration_seconds: float
        audit_trail: List[AuditEvent]

```text

**Security Isolation Configuration:**

```yaml
# config/execution-security.yaml
execution_environments:
  python:
    image: "python:3.11-alpine"
    network_mode: "none"
    resource_limits:
      memory: "512MB"
      cpu: "0.5"
      disk: "100MB"
    filesystem:
      read_only: true
      temp_mount: "/tmp"
    allowed_packages: ["requests", "pandas", "numpy"]

  nodejs:
    image: "node:18-alpine"
    network_mode: "restricted"
    allowed_domains: ["api.github.com", "npmjs.org"]

security_policies:
  default:
    require_approval: true
    max_execution_time: 300
    audit_level: "full"
  trusted_agent:
    require_approval: false
    max_execution_time: 600

```text

**State Management Integration:**

```python
class ExecutionStateManager:
    async def persist_execution_state(self, execution_id: str, state: ExecutionState)
    async def recover_execution_state(self, execution_id: str) -> Optional[ExecutionState]
    async def create_checkpoint(self, execution_id: str, checkpoint_data: dict)
    async def list_active_executions(self) -> List[ExecutionSummary]
    async def cancel_execution(self, execution_id: str, reason: str) -> bool

```python

**Performance Requirements:**

- Container startup: <10s for execution environments
- Code execution initialization: <3s
- State persistence: <100ms per checkpoint
- Resource monitoring: <50ms update intervals
- Execution cancellation: <5s response time

### Dependencies

- Issue #11: Multi-Agent Orchestration (integration with Zen MCP)
- Docker container infrastructure with security policies
- Redis state management system
- Human-in-Loop MCP Server integration
- Code execution security framework

### Testing Procedures

```bash
# Execution engine unit tests
pytest tests/unit/test_execution_engine.py -v

# Security isolation tests
pytest tests/security/test_execution_isolation.py -v

# State management and recovery tests
pytest tests/state/test_execution_state_management.py -v

# Performance and resource limit tests
pytest tests/performance/test_execution_performance.py -v

# Integration tests with Human-in-Loop MCP
pytest tests/integration/test_hitl_execution_approval.py -v

```bash

### **TODO for Project Owner**

- [ ] Define specific security policies for different execution types
- [ ] Provide approved container images and package allowlists
- [ ] Specify resource limit policies for different user roles
- [ ] Define execution audit retention and compliance requirements

---

## **Issue #19: Code Interpreter MCP Integration**

**Worktree**: `code-interpreter-mcp`
**Estimated Time**: 6 hours

### Description

Deploy and integrate Code Interpreter MCP Server to provide secure,
sandboxed code execution capabilities with comprehensive language support and safety mechanisms.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What programming languages and execution environments are required?**
**A1: Python 3.11+, Node.js 18+, shell scripting, SQL with containerized isolation**

**Q2: How are code dependencies and package installations managed securely?**
**A2: Pre-approved package allowlists with vulnerability scanning and isolated package management**

**Q3: What file system access and data persistence capabilities are needed?**
**A3: Restricted temporary file system with controlled input/output data exchange**

**Q4: How does code execution integrate with the broader agent workflow?**
**A4: Direct integration with Execution Engine through standardized MCP protocols**

### Acceptance Criteria

- [ ] Code Interpreter MCP Server deployed with multi-language support
- [ ] Secure sandboxed execution environment with network isolation
- [ ] Package management with security scanning and approval workflows
- [ ] File system isolation with controlled data input/output
- [ ] Integration with Execution Engine for workflow coordination
- [ ] Real-time execution monitoring and resource usage tracking
- [ ] Code validation and static analysis before execution
- [ ] Comprehensive logging and audit trail for all executions

### Technical Details

**Code Interpreter MCP Configuration:**

```yaml
# config/code-interpreter-mcp.yaml
server:
  port: 3002
  execution_timeout: 300
  max_concurrent_executions: 10

languages:
  python:
    version: "3.11"
    base_image: "python:3.11-alpine"
    allowed_packages:
      - "pandas>=1.5.0,<2.0.0"
      - "numpy>=1.21.0,<2.0.0"
      - "requests>=2.28.0,<3.0.0"
    security_profile: "restricted"

  nodejs:
    version: "18"
    base_image: "node:18-alpine"
    allowed_packages:
      - "lodash@^4.17.21"
      - "axios@^1.4.0"
    security_profile: "restricted"

security:
  network_access: false
  file_system: "temporary_only"
  resource_limits:
    memory: "1GB"
    cpu_shares: 512
    execution_time: 300

```text

**Execution Protocol Integration:**

```typescript
interface CodeExecutionRequest {
  language: "python" | "nodejs" | "bash" | "sql";
  code: string;
  input_data?: Record<string, any>;
  execution_context: ExecutionContext;
  security_profile: "restricted" | "standard" | "trusted";
}

interface CodeExecutionResponse {
  execution_id: string;
  status: ExecutionStatus;
  output: string;
  error?: string;
  resource_usage: ResourceMetrics;
  execution_time: number;
  files_created: string[];
}

```text

**Security Validation Pipeline:**

```python
class CodeSecurityValidator:
    async def validate_code_safety(self, code: str, language: str) -> ValidationResult
    async def scan_for_security_issues(self, code: str) -> List[SecurityIssue]
    async def check_package_dependencies(self, requirements: List[str]) -> DependencyReport
    async def validate_resource_usage_patterns(self, code: str) -> ResourceAnalysis

```python

**Performance Requirements:**

- Code validation: <5s for typical scripts
- Execution environment startup: <15s
- Package installation: <60s for approved packages
- Execution monitoring: <100ms update intervals
- Results retrieval: <2s for standard outputs

### Dependencies

- Issue #18: Direct Execution Engine (primary integration point)
- Docker container security infrastructure
- Package vulnerability scanning system
- Code analysis and validation tools

### Testing Procedures

```bash
# Code Interpreter MCP deployment tests
pytest tests/integration/test_code_interpreter_deployment.py -v

# Multi-language execution tests
pytest tests/execution/test_multi_language_support.py -v

# Security validation and sandboxing tests
pytest tests/security/test_code_execution_security.py -v

# Performance and resource limit tests
pytest tests/performance/test_execution_performance.py -v

```bash

### **TODO for Project Owner**

- [ ] Provide approved package lists for each programming language
- [ ] Define security profiles and their associated restrictions
- [ ] Specify package vulnerability scanning requirements and thresholds
- [ ] Define code execution monitoring and alerting requirements

---

## **Issue #20: Human-in-the-Loop MCP Integration**

**Worktree**: `hitl-mcp`
**Estimated Time**: 6 hours

### Description

Implement Human-in-the-Loop MCP Server to provide approval workflows,
manual intervention capabilities, and human oversight for critical automated operations.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What types of operations require human approval and what are the approval criteria?**
**A1: Code execution, file system modifications, external API calls, data exports, security changes**

**Q2: How are approval requests delivered and what response mechanisms exist?**
**A2: Multi-channel notifications (email, Slack, SMS) with web-based approval interface**

**Q3: What approval timeouts and escalation procedures are required?**
**A3: Configurable timeouts with automatic escalation chains and fallback approvers**

**Q4: How is approval context and decision history maintained for audit purposes?**
**A4: Complete audit logging with approval rationale, approver identity, and decision timestamps**

### Acceptance Criteria

- [ ] Human-in-Loop MCP Server with approval workflow management
- [ ] Multi-channel notification system (email, Slack, web interface)
- [ ] Configurable approval rules and escalation policies
- [ ] Web-based approval interface with context visualization
- [ ] Approval timeout handling and automatic escalation
- [ ] Comprehensive audit logging and decision tracking
- [ ] Integration with execution engine for operation gating
- [ ] Role-based approval permissions and delegation

### Technical Details

**HITL MCP Configuration:**

```yaml
# config/hitl-mcp.yaml
server:
  port: 3003
  web_interface_port: 8080

approval_rules:
  code_execution:
    required_approvers: 1
    timeout_minutes: 30
    escalation_chain: ["team_lead", "security_admin"]
    auto_approve_conditions:
      - "execution_time < 60"
      - "no_network_access"
      - "trusted_agent"

  file_system_access:
    required_approvers: 2
    timeout_minutes: 60
    requires_justification: true

notification_channels:
  email:
    smtp_server: "${SMTP_SERVER}"
    from_address: "promptcraft-approvals@domain.com"
  slack:
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#promptcraft-approvals"
  sms:
    provider: "twilio"
    numbers: ["+1234567890"]

```text

**Approval Workflow Integration:**

```python
class HumanApprovalWorkflow:
    @dataclass
    class ApprovalRequest:
        request_id: str
        operation_type: str
        requester_agent: str
        operation_details: Dict[str, Any]
        risk_level: Literal["low", "medium", "high", "critical"]
        justification: str
        timeout_minutes: int

    @dataclass
    class ApprovalResponse:
        request_id: str
        approved: bool
        approver_id: str
        decision_timestamp: datetime
        rationale: str
        conditions: Optional[List[str]]

```text

**Web Approval Interface:**

```typescript
interface ApprovalDashboard {
  pending_requests: ApprovalRequest[];
  approval_history: ApprovalDecision[];
  escalated_requests: EscalatedRequest[];
  approval_metrics: ApprovalMetrics;
}

interface ApprovalContext {
  operation_summary: string;
  risk_assessment: RiskAssessment;
  similar_operations: HistoricalOperation[];
  agent_context: AgentInformation;
  execution_preview: ExecutionPreview;
}

```text

**Escalation and Timeout Management:**

```python
class ApprovalEscalationManager:
    async def handle_approval_timeout(self, request_id: str)
    async def escalate_to_next_approver(self, request_id: str, reason: str)
    async def send_urgent_notification(self, request_id: str, channel: str)
    async def auto_approve_if_conditions_met(self, request: ApprovalRequest) -> bool

```python

**Performance Requirements:**

- Approval request processing: <3s
- Notification delivery: <10s across all channels
- Web interface response: <2s for approval actions
- Escalation processing: <30s
- Audit log persistence: <1s per decision

### Dependencies

- Issue #18: Direct Execution Engine (primary integration)
- Multi-channel notification infrastructure
- Web interface development framework
- User authentication and authorization system

### Testing Procedures

```bash
# HITL MCP deployment tests
pytest tests/integration/test_hitl_mcp_deployment.py -v

# Approval workflow tests
pytest tests/workflows/test_approval_workflows.py -v

# Multi-channel notification tests
pytest tests/notifications/test_notification_delivery.py -v

# Escalation and timeout handling tests
pytest tests/escalation/test_approval_escalation.py -v

# Web interface integration tests
pytest tests/ui/test_approval_web_interface.py -v

```typescript

### **TODO for Project Owner**

- [ ] Define specific approval rules and risk assessment criteria
- [ ] Provide notification channel configuration and credentials
- [ ] Specify approver roles, permissions, and escalation chains
- [ ] Define approval audit retention and compliance requirements

---

## **Issue #21: State Management & Persistence**

**Worktree**: `state-management`
**Estimated Time**: 6 hours

### Description

Implement comprehensive state management and persistence system for long-running workflows,
execution context, and multi-agent collaboration state using Redis and database technologies.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What types of state need to be persisted and for how long?**
**A1: Execution state (24h), workflow context (7d), agent conversations (30d), audit logs (1y)**

**Q2: How is state consistency maintained across multiple agents and execution environments?**
**A2: Redis-based distributed locking with atomic operations and transaction boundaries**

**Q3: What backup and recovery mechanisms are required for critical state data?**
**A3: Real-time Redis replication with automated backup to persistent storage every 6 hours**

**Q4: How does state management integrate with existing MCP orchestration?**
**A4: Direct integration with Zen MCP Server through state management API endpoints**

### Acceptance Criteria

- [ ] Redis-based distributed state management with clustering support
- [ ] Persistent state backup and recovery mechanisms
- [ ] Atomic state operations with transaction support
- [ ] State versioning and change tracking
- [ ] Cross-agent state synchronization and conflict resolution
- [ ] Performance-optimized state queries and updates
- [ ] State cleanup and archival policies
- [ ] Integration with audit logging and compliance systems

### Technical Details

**State Management Architecture:**

```python
class StateManager:
    @dataclass
    class StateEntry:
        key: str
        value: Dict[str, Any]
        version: int
        ttl_seconds: Optional[int]
        created_at: datetime
        updated_at: datetime
        tags: List[str]

    async def set_state(self, key: str, value: dict, ttl: Optional[int] = None) -> bool
    async def get_state(self, key: str) -> Optional[StateEntry]
    async def update_state(self, key: str, updates: dict, expected_version: int) -> bool
    async def delete_state(self, key: str) -> bool
    async def list_states(self, pattern: str, tags: List[str] = None) -> List[StateEntry]

```python

**Redis Configuration for High Availability:**

```yaml
# config/redis-cluster.yaml
redis:
  cluster:
    enabled: true
    nodes:
      - "redis-1:6379"
      - "redis-2:6379"
      - "redis-3:6379"

  persistence:
    save_intervals: ["900 1", "300 10", "60 10000"]
    appendonly: true
    appendfsync: "everysec"

  backup:
    schedule: "0 */6 * * *"  # Every 6 hours
    retention_days: 30
    storage_backend: "s3"

  performance:
    maxmemory: "2gb"
    maxmemory_policy: "allkeys-lru"
    tcp_keepalive: 60

```text

**State Synchronization Protocols:**

```python
class StateSync:
    async def acquire_lock(self, resource: str, timeout: int = 30) -> bool
    async def release_lock(self, resource: str) -> bool
    async def atomic_multi_update(self, operations: List[StateOperation]) -> bool
    async def resolve_state_conflict(self, key: str, conflicts: List[StateConflict]) -> StateEntry
    async def broadcast_state_change(self, key: str, change_event: StateChangeEvent)

```python

**Workflow State Management:**

```typescript
interface WorkflowState {
  workflow_id: string;
  current_step: string;
  execution_context: ExecutionContext;
  agent_assignments: Record<string, AgentAssignment>;
  step_history: WorkflowStep[];
  error_state?: ErrorState;
  recovery_checkpoints: RecoveryCheckpoint[];
}

interface ExecutionContext {
  variables: Record<string, any>;
  temporary_files: string[];
  network_connections: Connection[];
  resource_allocations: ResourceAllocation[];
}

```text

**Performance Requirements:**

- State read operations: <5ms for cached data
- State write operations: <15ms with persistence
- Lock acquisition: <100ms
- State synchronization: <200ms across nodes
- Backup operations: <5min for full state dump

### Dependencies

- Redis cluster infrastructure with high availability
- Persistent storage backend for backups
- Issue #18: Direct Execution Engine (state consumer)
- Issue #11: Multi-Agent Orchestration (state coordination)

### Testing Procedures

```bash
# State management unit tests
pytest tests/unit/test_state_manager.py -v

# Redis cluster and persistence tests
pytest tests/persistence/test_redis_cluster.py -v

# State synchronization and conflict resolution tests
pytest tests/sync/test_state_synchronization.py -v

# Performance and load testing
pytest tests/performance/test_state_performance.py -v

# Backup and recovery tests
pytest tests/backup/test_state_backup_recovery.py -v

```bash

### **TODO for Project Owner**

- [ ] Define specific state retention policies for different data types
- [ ] Provide Redis cluster configuration and sizing requirements
- [ ] Specify backup storage location and access credentials
- [ ] Define state cleanup and archival automation requirements

---

## **Issue #22: API Security & Authentication**

**Worktree**: `api-security`
**Estimated Time**: 6 hours

### Description

Implement comprehensive API security layer with authentication, authorization,
rate limiting, and security monitoring for production-ready Journey 3 and Journey 4 API endpoints.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What authentication methods are required and how are API keys managed?**
**A1: JWT tokens with refresh, API keys with rotation, OAuth2 integration for enterprise SSO**

**Q2: How are API permissions and role-based access controls implemented?**
**A2: Fine-grained permissions with role hierarchies, resource-based access control**

**Q3: What rate limiting and DDoS protection mechanisms are needed?**
**A3: Multi-tier rate limiting with IP-based, user-based, and endpoint-specific limits**

**Q4: How are security events monitored and anomalies detected?**
**A4: Real-time security monitoring with anomaly detection and automated response**

### Acceptance Criteria

- [ ] JWT-based authentication with token refresh and validation
- [ ] API key management with automatic rotation and scope control
- [ ] Role-based access control with fine-grained permissions
- [ ] Multi-level rate limiting and abuse prevention
- [ ] Security event logging and real-time monitoring
- [ ] API request/response encryption and data protection
- [ ] Intrusion detection and automated security response
- [ ] Integration with existing SSO systems and identity providers

### Technical Details

**Authentication Architecture:**

```python
class APISecurityManager:
    @dataclass
    class AuthenticationResult:
        authenticated: bool
        user_id: Optional[str]
        permissions: List[str]
        rate_limit_info: RateLimitInfo
        security_context: SecurityContext

    async def authenticate_jwt(self, token: str) -> AuthenticationResult
    async def authenticate_api_key(self, api_key: str) -> AuthenticationResult
    async def refresh_access_token(self, refresh_token: str) -> TokenPair
    async def revoke_token(self, token: str) -> bool

```python

**Security Configuration:**

```yaml
# config/api-security.yaml
authentication:
  jwt:
    secret_key: "${JWT_SECRET_KEY}"
    access_token_ttl: 3600  # 1 hour
    refresh_token_ttl: 604800  # 7 days
    algorithm: "HS256"

  api_keys:
    auto_rotation_days: 90
    scope_enforcement: true
    usage_tracking: true

authorization:
  roles:
    admin:
      permissions: ["*"]
    developer:
      permissions: ["execute_code", "access_agents", "read_state"]
    viewer:
      permissions: ["read_state", "view_results"]

rate_limiting:
  global:
    requests_per_minute: 1000
    burst_limit: 100
  per_user:
    requests_per_minute: 100
    execution_requests_per_hour: 50
  per_endpoint:
    "/api/v1/execute": 10  # per minute
    "/api/v1/agents": 50

```json

**Rate Limiting Implementation:**

```python
class RateLimiter:
    @dataclass
    class RateLimit:
        key: str
        limit: int
        window_seconds: int
        current_usage: int
        reset_time: datetime

    async def check_rate_limit(self, key: str, endpoint: str) -> RateLimitResult
    async def increment_usage(self, key: str, endpoint: str) -> bool
    async def get_rate_limit_status(self, key: str) -> Dict[str, RateLimit]
    async def reset_rate_limit(self, key: str, endpoint: str) -> bool

```python

**Security Monitoring:**

```typescript
interface SecurityEvent {
  event_id: string;
  event_type: "authentication_failure" | "rate_limit_exceeded" | "suspicious_activity";
  source_ip: string;
  user_id?: string;
  endpoint: string;
  timestamp: Date;
  severity: "low" | "medium" | "high" | "critical";
  details: Record<string, any>;
}

interface SecurityMonitor {
  track_event(event: SecurityEvent): void;
  detect_anomalies(time_window: number): Promise<Anomaly[]>;
  trigger_security_response(threat_level: string): Promise<void>;
}

```json

**Performance Requirements:**

- Authentication check: <50ms
- Permission validation: <20ms
- Rate limit check: <10ms
- Security event logging: <100ms
- Token refresh: <200ms

### Dependencies

- JWT library and cryptographic functions
- Redis for rate limiting and session storage
- Security monitoring infrastructure
- Integration with identity provider systems

### Testing Procedures

```bash
# API security unit tests
pytest tests/unit/test_api_security.py -v

# Authentication and authorization tests
pytest tests/auth/test_jwt_authentication.py -v
pytest tests/auth/test_rbac_permissions.py -v

# Rate limiting tests
pytest tests/security/test_rate_limiting.py -v

# Security monitoring tests
pytest tests/monitoring/test_security_events.py -v

# Integration tests with API endpoints
pytest tests/integration/test_secure_api_endpoints.py -v

```bash

### **TODO for Project Owner**

- [ ] Define specific user roles and permission matrices
- [ ] Provide JWT signing keys and rotation procedures
- [ ] Specify rate limiting thresholds for different user tiers
- [ ] Define security incident response procedures and notification channels

---

## **Issue #23: Enhanced FastAPI Gateway**

**Worktree**: `fastapi-gateway`
**Estimated Time**: 6 hours

### Description

Develop a production-ready FastAPI gateway that provides secure, scalable API endpoints for
Journey 3 (IDE Integration) and Journey 4 (Direct Execution) with comprehensive documentation and monitoring.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What API endpoints are required for IDE integration and direct execution?**
**A1: Agent interaction, code execution, state management, workflow control, real-time updates**

**Q2: How should API versioning and backward compatibility be managed?**
**A2: URI-based versioning (/api/v1/) with deprecation notices and migration paths**

**Q3: What documentation and developer experience features are needed?**
**A3: OpenAPI/Swagger docs, interactive API explorer, SDKs, comprehensive examples**

**Q4: How are API performance and reliability monitored in production?**
**A4: Prometheus metrics, distributed tracing, health checks, SLA monitoring**

### Acceptance Criteria

- [ ] FastAPI application with comprehensive endpoint coverage
- [ ] OpenAPI documentation with interactive API explorer
- [ ] Request/response validation and error handling
- [ ] Integration with API security layer and authentication
- [ ] Real-time WebSocket endpoints for live updates
- [ ] Comprehensive logging and metrics collection
- [ ] Health check and monitoring endpoints
- [ ] Production deployment configuration with load balancing

### Technical Details

**FastAPI Application Structure:**

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

app = FastAPI(
    title="PromptCraft-Hybrid API",
    description="AI-powered prompt enhancement and code execution platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

class APIEndpoints:
    # Agent Management
    @app.get("/api/v1/agents")
    async def list_agents(auth: AuthResult = Depends(authenticate))

    @app.post("/api/v1/agents/{agent_id}/invoke")
    async def invoke_agent(agent_id: str, request: AgentInvocationRequest)

    # Code Execution
    @app.post("/api/v1/execute")
    async def execute_code(request: CodeExecutionRequest)

    @app.get("/api/v1/executions/{execution_id}")
    async def get_execution_status(execution_id: str)

    # Workflow Management
    @app.post("/api/v1/workflows")
    async def create_workflow(workflow: WorkflowDefinition)

    @app.get("/api/v1/workflows/{workflow_id}/status")
    async def get_workflow_status(workflow_id: str)

```python

**API Data Models:**

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AgentInvocationRequest(BaseModel):
    prompt: str = Field(..., description="User prompt to process")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Agent parameters")

class CodeExecutionRequest(BaseModel):
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code to execute")
    input_data: Optional[Dict[str, Any]] = None
    approval_required: bool = Field(False, description="Require human approval")

class WorkflowDefinition(BaseModel):
    name: str
    steps: List[WorkflowStep]
    agents: List[str]
    approval_points: List[str]

```text

**WebSocket Integration:**

```python
from fastapi import WebSocket
import asyncio

@app.websocket("/api/v1/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    # Register client for real-time updates
    await websocket_manager.register_client(client_id, websocket)

    try:
        while True:
            # Handle client messages
            data = await websocket.receive_text()
            await handle_websocket_message(client_id, data)
    except WebSocketDisconnect:
        await websocket_manager.unregister_client(client_id)

```text

**Monitoring and Metrics:**

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics collection
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

```python

**Performance Requirements:**

- API response time: <200ms for simple requests
- Code execution initiation: <3s
- WebSocket message latency: <100ms
- Concurrent connections: 1000+ simultaneous clients
- Throughput: 10,000+ requests per minute

### Dependencies

- Issue #22: API Security & Authentication (security integration)
- Issue #18: Direct Execution Engine (execution endpoints)
- Issue #11: Multi-Agent Orchestration (agent endpoints)
- FastAPI, Pydantic, WebSocket infrastructure

### Testing Procedures

```bash
# FastAPI application tests
pytest tests/unit/test_fastapi_gateway.py -v

# API endpoint integration tests
pytest tests/api/test_api_endpoints.py -v

# WebSocket functionality tests
pytest tests/websocket/test_websocket_endpoints.py -v

# Performance and load testing
pytest tests/performance/test_api_performance.py -v

# API documentation validation
pytest tests/docs/test_openapi_documentation.py -v

```bash

### **TODO for Project Owner**

- [ ] Define specific API endpoint requirements for IDE integration patterns
- [ ] Provide API documentation standards and branding requirements
- [ ] Specify performance SLA requirements and monitoring thresholds
- [ ] Define API deprecation and versioning policies

---

## **Issue #24: Workflow Validation & Safety**

**Worktree**: `workflow-safety`
**Estimated Time**: 6 hours

### Description

Implement comprehensive workflow validation and safety mechanisms to ensure secure,
reliable execution of multi-step automated processes with proper safeguards and rollback capabilities.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What types of workflow validation are required before execution?**
**A1: Security analysis, resource validation, dependency checking, impact assessment**

**Q2: How are dangerous operations detected and prevented?**
**A2: Static analysis, pattern matching, resource impact modeling, approval requirements**

**Q3: What rollback and recovery mechanisms are needed for failed workflows?**
**A3: Checkpoint-based recovery, atomic operations, compensating transactions**

**Q4: How are workflow safety policies configured and enforced?**
**A4: YAML-based policy definitions with real-time validation and enforcement**

### Acceptance Criteria

- [ ] Pre-execution workflow validation and safety analysis
- [ ] Dangerous operation detection and prevention
- [ ] Checkpoint-based rollback and recovery mechanisms
- [ ] Resource impact assessment and safety limits
- [ ] Policy-based safety rule enforcement
- [ ] Real-time workflow monitoring and intervention
- [ ] Comprehensive audit logging for safety events
- [ ] Integration with human approval workflows for high-risk operations

### Technical Details

**Workflow Safety Framework:**

```python
class WorkflowSafetyValidator:
    @dataclass
    class SafetyCheckResult:
        passed: bool
        risk_level: Literal["low", "medium", "high", "critical"]
        detected_risks: List[SafetyRisk]
        required_approvals: List[str]
        mitigation_steps: List[str]

    async def validate_workflow_safety(self, workflow: WorkflowDefinition) -> SafetyCheckResult
    async def analyze_operation_risk(self, operation: WorkflowOperation) -> RiskAssessment
    async def check_resource_limits(self, workflow: WorkflowDefinition) -> ResourceValidation
    async def validate_dependencies(self, workflow: WorkflowDefinition) -> DependencyValidation

```python

**Safety Policy Configuration:**

```yaml
# config/workflow-safety-policies.yaml
safety_policies:
  file_operations:
    max_files_modified: 100
    restricted_paths: ["/etc", "/usr", "/bin", "/sbin"]
    require_backup: true
    approval_required: true

  network_operations:
    allowed_domains: ["api.github.com", "api.openai.com"]
    max_requests_per_minute: 60
    data_size_limit: "10MB"

  code_execution:
    max_execution_time: 300
    memory_limit: "1GB"
    cpu_limit: "2"
    dangerous_patterns:
      - "rm -rf"
      - "DROP TABLE"
      - "DELETE FROM"
      - "eval("

risk_thresholds:
  automatic_execution: "medium"
  requires_approval: "high"
  blocked_execution: "critical"

```text

**Rollback and Recovery System:**

```python
class WorkflowRecoveryManager:
    @dataclass
    class RecoveryCheckpoint:
        checkpoint_id: str
        workflow_id: str
        step_index: int
        state_snapshot: Dict[str, Any]
        created_at: datetime

    async def create_checkpoint(self, workflow_id: str, step_index: int) -> str
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool
    async def execute_compensating_actions(self, failed_operations: List[Operation]) -> bool
    async def validate_recovery_state(self, workflow_id: str) -> bool

```python

**Operation Risk Analysis:**

```typescript
interface RiskAssessment {
  operation_type: string;
  risk_factors: RiskFactor[];
  potential_impact: ImpactAnalysis;
  mitigation_strategies: string[];
  approval_requirements: ApprovalRequirement[];
}

interface SafetyRisk {
  risk_id: string;
  category: "security" | "data_loss" | "system_damage" | "compliance";
  severity: number;  // 1-10 scale
  description: string;
  affected_resources: string[];
}

```text

**Real-time Safety Monitoring:**

```python
class WorkflowSafetyMonitor:
    async def monitor_workflow_execution(self, workflow_id: str)
    async def detect_anomalous_behavior(self, execution_metrics: ExecutionMetrics) -> List[Anomaly]
    async def trigger_emergency_stop(self, workflow_id: str, reason: str) -> bool
    async def escalate_safety_incident(self, incident: SafetyIncident) -> bool

```python

**Performance Requirements:**

- Safety validation: <30s for complex workflows
- Risk analysis: <10s per operation
- Checkpoint creation: <5s
- Rollback execution: <60s
- Safety monitoring: <1s update intervals

### Dependencies

- Issue #18: Direct Execution Engine (workflow execution)
- Issue #20: Human-in-Loop MCP (approval integration)
- Issue #21: State Management (checkpoint storage)
- Policy engine and rule validation framework

### Testing Procedures

```bash
# Workflow safety validation tests
pytest tests/unit/test_workflow_safety.py -v

# Risk analysis and detection tests
pytest tests/safety/test_risk_analysis.py -v

# Rollback and recovery tests
pytest tests/recovery/test_workflow_recovery.py -v

# Safety policy enforcement tests
pytest tests/policies/test_safety_policy_enforcement.py -v

# Real-time monitoring tests
pytest tests/monitoring/test_safety_monitoring.py -v

```bash

### **TODO for Project Owner**

- [ ] Define specific safety policies for different types of operations
- [ ] Provide risk assessment criteria and scoring methodology
- [ ] Specify rollback requirements and recovery time objectives
- [ ] Define safety incident escalation procedures and notification channels

---

## **Issue #25: Journey 4 UI Implementation**

**Worktree**: `journey4-ui`
**Estimated Time**: 8 hours

### Description

Implement the complete Journey 4 user interface for Direct Execution capabilities,
providing workflow visualization, execution monitoring, approval management, and comprehensive user
experience for automated task execution.

### **CONTRACTOR QUESTIONS ADDRESSED:**

**Q1: What user interface components are needed for workflow creation and management?**
**A1: Drag-and-drop workflow builder, step configuration panels, agent selection, approval points**

**Q2: How should real-time execution monitoring and progress visualization be implemented?**
**A2: Live execution timeline, resource usage charts, agent status indicators, progress bars**

**Q3: What approval and human intervention interfaces are required?**
**A3: Approval queue dashboard, detailed operation context, one-click approve/deny, delegation**

**Q4: How should error handling and workflow recovery be presented to users?**
**A4: Error visualization, recovery options, rollback controls, incident reports**

### Acceptance Criteria

- [ ] Drag-and-drop workflow builder with visual step configuration
- [ ] Real-time execution monitoring with live updates
- [ ] Approval queue management and decision interface
- [ ] Workflow history and audit trail visualization
- [ ] Error handling and recovery controls
- [ ] Resource usage monitoring and alerts
- [ ] Export functionality for workflow definitions and results
- [ ] Mobile-responsive design for monitoring and approvals

### Technical Details

**Journey 4 UI Components:**

```python
# Extend existing Gradio interface for Journey 4
class Journey4Interface:
    def __init__(self, base_app):
        self.base_app = base_app
        self.workflow_builder = WorkflowBuilder()
        self.execution_monitor = ExecutionMonitor()
        self.approval_manager = ApprovalManager()

    def create_workflow_builder(self) -> gr.Interface:
        """Visual workflow creation interface"""
        pass

    def create_execution_dashboard(self) -> gr.Interface:
        """Real-time execution monitoring"""
        pass

    def create_approval_interface(self) -> gr.Interface:
        """Human approval management"""
        pass

```python

**Workflow Builder Interface:**

```typescript
interface WorkflowBuilderUI {
  workflow_canvas: CanvasComponent;
  step_palette: StepPalette;
  property_panel: PropertyPanel;
  validation_panel: ValidationPanel;
  preview_panel: PreviewPanel;
}

interface WorkflowStep {
  step_id: string;
  step_type: "agent_invoke" | "code_execute" | "approval_point" | "conditional";
  position: {x: number, y: number};
  configuration: StepConfiguration;
  connections: Connection[];
}

```yaml

**Execution Monitoring Dashboard:**

```python
class ExecutionMonitor:
    def create_monitoring_interface(self):
        with gr.Row():
            with gr.Column(scale=2):
                # Execution timeline
                execution_timeline = gr.Plot(label="Execution Progress")

                # Agent status grid
                agent_status = gr.DataFrame(
                    headers=["Agent", "Status", "Current Task", "Duration"],
                    label="Agent Status"
                )

            with gr.Column(scale=1):
                # Resource usage
                resource_chart = gr.Plot(label="Resource Usage")

                # Control buttons
                pause_btn = gr.Button("Pause Execution")
                stop_btn = gr.Button("Stop Execution")
                rollback_btn = gr.Button("Rollback")

```text

**Approval Management Interface:**

```typescript
interface ApprovalQueueUI {
  pending_approvals: ApprovalRequest[];
  approval_context: ApprovalContextPanel;
  decision_buttons: ApprovalDecisionButtons;
  approval_history: ApprovalHistoryTable;
  delegation_controls: DelegationPanel;
}

interface ApprovalRequest {
  request_id: string;
  operation_summary: string;
  risk_level: "low" | "medium" | "high" | "critical";
  requester: string;
  time_remaining: number;
  context: ApprovalContext;
}

```text

**Real-time Update System:**

```python
class RealTimeUpdater:
    async def update_execution_progress(self, workflow_id: str):
        """Update execution progress in real-time"""
        while execution_active:
            progress_data = await get_execution_progress(workflow_id)
            await self.broadcast_update("execution_progress", progress_data)
            await asyncio.sleep(1)

    async def update_approval_queue(self):
        """Update pending approvals"""
        approvals = await get_pending_approvals()
        await self.broadcast_update("approval_queue", approvals)

```text

**Performance Requirements:**

- UI responsiveness: <200ms for all interactions
- Real-time updates: <1s latency for status changes
- Workflow builder: <500ms for drag-and-drop operations
- Dashboard refresh: <2s for complete data reload
- Mobile responsiveness: Support for tablets and smartphones

### Dependencies

- Issue #18: Direct Execution Engine (execution data)
- Issue #20: Human-in-Loop MCP (approval integration)
- Issue #24: Workflow Validation (safety status)
- Existing Gradio application foundation
- WebSocket infrastructure for real-time updates

### Testing Procedures

```bash
# Journey 4 UI component tests
pytest tests/unit/test_journey4_ui.py -v

# Workflow builder functionality tests
pytest tests/ui/test_workflow_builder.py -v

# Real-time monitoring tests
pytest tests/ui/test_execution_monitoring.py -v

# Approval interface tests
pytest tests/ui/test_approval_interface.py -v

# Mobile responsiveness tests
pytest tests/ui/test_mobile_responsiveness.py -v

```bash

### **TODO for Project Owner**

- [ ] Define specific workflow builder requirements and step types
- [ ] Provide UI design preferences and branding guidelines
- [ ] Specify real-time update frequency and performance requirements
- [ ] Define approval interface workflow and user experience requirements

---

## Implementation Notes

- All execution must be sandboxed and secure by default
- Human approval workflows are mandatory for destructive operations
- Comprehensive logging and audit trails required
- Performance targets: End-to-end workflow execution tracking
- Safety-first approach - fail safely rather than proceed unsafely
- All components must follow established coding standards
- Security-first approach throughout execution implementation
- Integration with existing multi-agent system is essential
- Real-time monitoring and user feedback are critical for Journey 4 success
