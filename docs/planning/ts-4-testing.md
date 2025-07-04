---
title: PromptCraft-Hybrid Phase 4 Testing Strategy
version: 2.0
status: published
component: Architecture
tags: ['phase-4', 'testing', 'quality-assurance', 'enterprise', 'validation']
source: PromptCraft-Hybrid Project
purpose: To provide comprehensive testing approach and quality assurance framework for Phase 4 enterprise features.
---

# PromptCraft-Hybrid: Phase 4 Testing Strategy

Version: 2.0
Status: Updated for v7.0 Architecture
Audience: QA Engineers, Test Architects, DevOps Engineers

## 1. Testing Overview

### 1.1. Testing Philosophy

Phase 4 testing focuses on enterprise-grade reliability, security, scalability, and compliance validation. The testing strategy emphasizes:

- **Enterprise Security**: SSO integration, audit logging, and compliance validation
- **Automated Agent Creation**: Factory reliability, template accuracy, and deployment success
- **Analytics Accuracy**: Data integrity, insight correctness, and ML model validation
- **Scalability & Performance**: Load handling, concurrent user support, and resource optimization
- **Business Continuity**: Disaster recovery, backup validation, and failover testing

### 1.2. Testing Pyramid for Enterprise Features

```mermaid
graph TD
    A[Unit Tests - 50%] --> B[Integration Tests - 30%]
    B --> C[System Tests - 15%]
    C --> D[End-to-End Tests - 5%]

    subgraph "Unit Tests"
        E[Agent Factory Logic]
        F[Analytics Calculations]
        G[SSO Authentication]
        H[Audit Logging]
        I[MCP Validation]
    end

    subgraph "Integration Tests"
        J[Enterprise Workflows]
        K[Database Analytics]
        L[Security Integration]
        M[ML Pipeline]
        N[Container Orchestration]
    end

    subgraph "System Tests"
        O[Load Testing]
        P[Security Scanning]
        Q[Compliance Validation]
        R[Performance Benchmarking]
    end

    subgraph "E2E Tests"
        S[User Journey Testing]
        T[Disaster Recovery]
        U[Multi-Tenant Scenarios]
    end
```

### 1.3. Quality Gates

**Critical Quality Gates for Phase 4:**
- **Security**: 100% pass rate on OWASP ZAP scans
- **Performance**: p95 response time < 2s under 1000 concurrent users
- **Availability**: 99.9% uptime validation through chaos engineering
- **Compliance**: 100% audit event capture and retention
- **Analytics**: 95% accuracy in ML optimization recommendations

## 2. Enterprise Security Testing

### 2.1. SSO Integration Test Suite

```python
# tests/enterprise/test_sso_integration.py
import pytest
import asyncio
import jwt
from unittest.mock import Mock, patch
from src.enterprise.sso_integration import EnterpriseSSOManager
from src.enterprise.audit_logger import AuditLogger

class TestEnterpriseSSOIntegration:
    """Comprehensive SSO integration testing"""

    @pytest.fixture
    async def sso_manager(self):
        """Setup SSO manager with test configuration"""
        config = {
            "keycloak_server_url": "http://test-keycloak:8080/auth",
            "keycloak_client_id": "test-client",
            "keycloak_realm": "test-realm",
            "keycloak_client_secret": "test-secret",
            "redis_url": "redis://test-redis:6379",
            "analytics_db_url": "postgresql://test:test@test-db:5432/test_analytics"
        }
        manager = EnterpriseSSOManager(config)
        await manager.initialize()
        return manager

    @pytest.mark.asyncio
    async def test_valid_token_authentication(self, sso_manager):
        """Test successful authentication with valid JWT token"""
        # Mock Keycloak response
        mock_token_info = {
            "active": True,
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "organization": "TestOrg",
            "realm_access": {"roles": ["user", "analyst"]},
            "resource_access": {"promptcraft-app": {"roles": ["read", "write"]}}
        }

        with patch.object(sso_manager.keycloak_client, 'introspect', return_value=mock_token_info):
            mock_request = Mock()
            mock_request.client.host = "192.168.1.100"
            mock_request.headers = {"user-agent": "test-client"}

            result = await sso_manager.authenticate_user("valid-jwt-token", mock_request)

            assert result['user']['user_id'] == "user123"
            assert result['user']['username'] == "testuser"
            assert result['user']['organization'] == "TestOrg"
            assert "user" in result['user']['roles']
            assert "analyst" in result['user']['roles']
            assert result['session_id'] is not None

    @pytest.mark.asyncio
    async def test_invalid_token_authentication(self, sso_manager):
        """Test authentication failure with invalid token"""
        mock_token_info = {"active": False}

        with patch.object(sso_manager.keycloak_client, 'introspect', return_value=mock_token_info):
            mock_request = Mock()
            mock_request.client.host = "192.168.1.100"

            with pytest.raises(HTTPException) as exc_info:
                await sso_manager.authenticate_user("invalid-token", mock_request)

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_session_creation_and_storage(self, sso_manager):
        """Test session creation and Redis storage"""
        user_info = {
            "user_id": "user123",
            "username": "testuser",
            "organization": "TestOrg",
            "roles": ["user", "analyst"]
        }

        session_id = await sso_manager._create_user_session(user_info, "test-token")

        # Verify session stored in Redis
        session_data = await sso_manager.redis_client.hgetall(f"session:{session_id}")
        assert session_data['user_id'] == "user123"
        assert session_data['username'] == "testuser"
        assert "user,analyst" in session_data['roles']

        # Verify session expiry is set
        ttl = await sso_manager.redis_client.ttl(f"session:{session_id}")
        assert ttl > 0 and ttl <= 28800  # 8 hours

    @pytest.mark.asyncio
    async def test_audit_logging_on_authentication(self, sso_manager):
        """Test that authentication events are properly audited"""
        mock_request = Mock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "test-client", "x-request-id": "req123"}
        mock_request.method = "POST"
        mock_request.url.path = "/auth/sso"

        with patch.object(sso_manager.audit_logger, '_store_audit_event') as mock_store:
            await sso_manager.audit_logger.log_authentication(
                user_id="user123",
                session_id="session123",
                request=mock_request,
                status="success"
            )

            mock_store.assert_called_once()
            audit_event = mock_store.call_args[0][0]

            assert audit_event['user_id'] == "user123"
            assert audit_event['session_id'] == "session123"
            assert audit_event['event_type'] == "authentication"
            assert audit_event['event_category'] == "security"
            assert audit_event['outcome']['status'] == "success"
```

### 2.2. Security Compliance Test Suite

```python
# tests/enterprise/test_security_compliance.py
import pytest
import asyncio
from src.enterprise.compliance_validator import ComplianceValidator
from src.enterprise.security_scanner import SecurityScanner

class TestSecurityCompliance:
    """Security and compliance validation tests"""

    @pytest.fixture
    def compliance_validator(self):
        return ComplianceValidator({
            "compliance_standards": ["SOC2", "HIPAA", "GDPR"],
            "audit_retention_days": 2555,
            "data_classification_enabled": True
        })

    @pytest.mark.asyncio
    async def test_audit_event_retention_compliance(self, compliance_validator):
        """Test audit event retention meets compliance requirements"""
        # Test SOC2 requirement (7 years retention)
        soc2_compliant = await compliance_validator.validate_retention_policy("SOC2")
        assert soc2_compliant == True

        # Test HIPAA requirement (6 years retention)
        hipaa_compliant = await compliance_validator.validate_retention_policy("HIPAA")
        assert hipaa_compliant == True

    @pytest.mark.asyncio
    async def test_data_classification_enforcement(self, compliance_validator):
        """Test data classification is properly enforced"""
        test_data = {
            "user_email": "test@example.com",
            "credit_card": "1234-5678-9012-3456",
            "public_info": "product documentation"
        }

        classification = await compliance_validator.classify_data(test_data)

        assert classification["user_email"] == "PII"
        assert classification["credit_card"] == "SENSITIVE"
        assert classification["public_info"] == "PUBLIC"

    @pytest.mark.asyncio
    async def test_gdpr_data_portability(self, compliance_validator):
        """Test GDPR data portability compliance"""
        user_id = "user123"

        user_data = await compliance_validator.export_user_data(user_id)

        # Verify all user data is included
        assert "profile" in user_data
        assert "usage_history" in user_data
        assert "preferences" in user_data
        assert "audit_logs" in user_data

        # Verify data is in machine-readable format
        assert isinstance(user_data, dict)
        assert user_data["format"] == "JSON"

    @pytest.mark.security
    async def test_owasp_top_10_compliance(self):
        """Test compliance with OWASP Top 10 security requirements"""
        scanner = SecurityScanner()

        # Test injection vulnerabilities
        injection_results = await scanner.test_injection_vulnerabilities()
        assert injection_results["sql_injection"] == "PASS"
        assert injection_results["nosql_injection"] == "PASS"
        assert injection_results["command_injection"] == "PASS"

        # Test broken authentication
        auth_results = await scanner.test_authentication_security()
        assert auth_results["session_management"] == "PASS"
        assert auth_results["password_policy"] == "PASS"
        assert auth_results["multi_factor_auth"] == "PASS"

        # Test sensitive data exposure
        data_results = await scanner.test_data_exposure()
        assert data_results["encryption_at_rest"] == "PASS"
        assert data_results["encryption_in_transit"] == "PASS"
        assert data_results["data_masking"] == "PASS"
```

## 3. Agent Factory Testing

### 3.1. Automated Agent Creation Test Suite

```python
# tests/enterprise/test_agent_factory.py
import pytest
import asyncio
import tempfile
import docker
from pathlib import Path
from src.enterprise.agent_factory import AgentFactory, AgentSpec
from unittest.mock import Mock, patch

class TestAgentFactory:
    """Comprehensive agent factory testing"""

    @pytest.fixture
    def agent_factory(self):
        config = {
            "git_base_url": "https://github.com/test-org",
            "registry_url": "localhost:5000",
            "mcp_registry_url": "http://localhost:8001",
            "zen_mcp_url": "http://localhost:3000"
        }
        return AgentFactory(config)

    @pytest.fixture
    def sample_agent_spec(self):
        return AgentSpec(
            name="test_security_agent",
            display_name="Test Security Agent",
            description="Test agent for security analysis",
            domain="security",
            keywords=["security", "analysis", "testing"],
            capabilities=["code_scanning", "vulnerability_detection"],
            knowledge_sources=[
                {"type": "markdown", "source": "security_guidelines.md", "update_frequency": "weekly"}
            ]
        )

    @pytest.mark.asyncio
    async def test_agent_code_generation(self, agent_factory, sample_agent_spec):
        """Test agent code generation from templates"""
        generated_code = await agent_factory._generate_agent_code(sample_agent_spec)

        # Verify all required files are generated
        assert "src/agent.py" in generated_code
        assert "config/config.yaml" in generated_code
        assert "README.md" in generated_code
        assert "requirements.txt" in generated_code
        assert "pyproject.toml" in generated_code
        assert "Dockerfile" in generated_code

        # Verify agent class contains correct information
        agent_code = generated_code["src/agent.py"]
        assert "TestSecurityAgent" in agent_code
        assert "security analysis" in agent_code.lower()
        assert "code_scanning" in agent_code
        assert "vulnerability_detection" in agent_code

        # Verify requirements include domain-specific dependencies
        requirements = generated_code["requirements.txt"]
        assert "bandit>=1.7.0" in requirements  # Security domain
        assert "safety>=2.0.0" in requirements
        assert "promptcraft-sdk>=1.0.0" in requirements

    @pytest.mark.asyncio
    async def test_repository_creation(self, agent_factory, sample_agent_spec):
        """Test Git repository creation and structure"""
        agent_code = {
            "src/agent.py": "# Test agent code",
            "config/config.yaml": "agent_id: test_security_agent",
            "README.md": "# Test Security Agent"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('git.Repo.init') as mock_git:
                mock_repo = Mock()
                mock_git.return_value = mock_repo

                repo_url = await agent_factory._create_repository(sample_agent_spec, agent_code)

                # Verify repository initialization
                mock_git.assert_called_once()
                mock_repo.index.add.assert_called_once()
                mock_repo.index.commit.assert_called_once_with(
                    "Initial commit for Test Security Agent agent"
                )

    @pytest.mark.asyncio
    async def test_docker_build_process(self, agent_factory, sample_agent_spec):
        """Test Docker image building and validation"""
        deployment_config = {
            "environment": "development",
            "auto_deploy": True,
            "resource_limits": {"memory": "512M", "cpu": "0.5"}
        }

        with patch.object(agent_factory.docker_client.images, 'build') as mock_build:
            mock_image = Mock()
            mock_build.return_value = [mock_image, {}]

            with patch.object(agent_factory, '_deploy_agent_container') as mock_deploy:
                await agent_factory._build_and_deploy(
                    sample_agent_spec,
                    "/tmp/test-repo",
                    deployment_config
                )

                # Verify Docker build was called
                mock_build.assert_called_once()
                build_args = mock_build.call_args[1]
                assert build_args['tag'] == "localhost:5000/agent-test_security_agent:latest"
                assert build_args['dockerfile'] == "Dockerfile"

                # Verify deployment was attempted
                mock_deploy.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_registration(self, agent_factory, sample_agent_spec):
        """Test MCP server registration process"""
        with patch('src.enterprise.agent_factory.MCPRegistryClient') as mock_registry:
            with patch('src.enterprise.agent_factory.ZenOrchestratorClient') as mock_zen:
                mock_registry_instance = Mock()
                mock_zen_instance = Mock()
                mock_registry.return_value = mock_registry_instance
                mock_zen.return_value = mock_zen_instance

                await agent_factory._register_mcp(sample_agent_spec, "/tmp/test-repo")

                # Verify MCP registry registration
                mock_registry_instance.register_mcp.assert_called_once()
                manifest = mock_registry_instance.register_mcp.call_args[0][0]
                assert manifest['metadata']['name'] == "agent-test_security_agent"
                assert manifest['spec']['image'] == "localhost:5000/agent-test_security_agent:latest"

                # Verify Zen orchestrator update
                mock_zen_instance.add_agent_config.assert_called_once()
                agent_config = mock_zen_instance.add_agent_config.call_args[0][0]
                assert agent_config['agent_id'] == "test_security_agent"

    @pytest.mark.integration
    async def test_end_to_end_agent_creation(self, agent_factory, sample_agent_spec):
        """Integration test for complete agent creation workflow"""
        deployment_config = {
            "environment": "development",
            "auto_deploy": False,  # Skip deployment for test
            "resource_limits": {"memory": "512M", "cpu": "0.5"}
        }

        with patch.multiple(
            agent_factory,
            _create_repository=Mock(return_value="/tmp/test-repo"),
            _generate_knowledge_schema=Mock(),
            _create_docker_config=Mock(),
            _generate_tests=Mock(),
            _register_mcp=Mock()
        ):
            creation_id = await agent_factory.create_agent(sample_agent_spec, deployment_config)

            # Verify creation ID is returned
            assert creation_id.startswith("agent_creation_test_security_agent_")

            # Verify all steps were called
            agent_factory._create_repository.assert_called_once()
            agent_factory._generate_knowledge_schema.assert_called_once()
            agent_factory._create_docker_config.assert_called_once()
            agent_factory._generate_tests.assert_called_once()
            agent_factory._register_mcp.assert_called_once()
```

## 4. Analytics and ML Testing

### 4.1. Analytics Engine Test Suite

```python
# tests/enterprise/test_analytics_engine.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.enterprise.analytics_engine import AdvancedAnalyticsEngine
from unittest.mock import Mock, patch

class TestAdvancedAnalyticsEngine:
    """Analytics engine testing with ML validation"""

    @pytest.fixture
    def analytics_engine(self):
        config = {
            "analytics_db_url": "postgresql://test:test@localhost:5432/test_analytics",
            "mlflow_url": "http://localhost:5000"
        }
        return AdvancedAnalyticsEngine(config)

    @pytest.fixture
    def sample_execution_data(self):
        """Generate sample execution data for testing"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = []

        for i, date in enumerate(dates):
            data.extend([
                {
                    'date': date.date(),
                    'agent_id': 'security_agent',
                    'user_id': f'user{i % 10}',
                    'status': 'completed' if i % 5 != 0 else 'failed',
                    'processing_time_ms': np.random.normal(1500, 300),
                    'total_cost': np.random.uniform(0.05, 0.50),
                    'steps_completed': np.random.randint(3, 8),
                    'security_issues_found': np.random.randint(0, 5),
                    'test_success_rate': np.random.uniform(0.8, 1.0)
                },
                {
                    'date': date.date(),
                    'agent_id': 'web_dev_agent',
                    'user_id': f'user{(i + 5) % 10}',
                    'status': 'completed',
                    'processing_time_ms': np.random.normal(2000, 500),
                    'total_cost': np.random.uniform(0.08, 0.70),
                    'steps_completed': np.random.randint(4, 10),
                    'security_issues_found': 0,
                    'test_success_rate': np.random.uniform(0.85, 1.0)
                }
            ])

        return pd.DataFrame(data)

    @pytest.mark.asyncio
    async def test_summary_metrics_calculation(self, analytics_engine, sample_execution_data):
        """Test accuracy of summary metrics calculation"""
        with patch.object(analytics_engine, '_fetch_execution_data', return_value=sample_execution_data):
            insights = await analytics_engine.generate_usage_insights("30d")

            summary = insights['summary']

            # Verify basic counts
            assert summary['total_queries'] == len(sample_execution_data)
            assert summary['unique_users'] == sample_execution_data['user_id'].nunique()

            # Verify statistical calculations
            expected_avg_time = sample_execution_data['processing_time_ms'].mean()
            assert abs(summary['avg_response_time_ms'] - expected_avg_time) < 1.0

            expected_success_rate = (sample_execution_data['status'] == 'completed').mean()
            assert abs(summary['success_rate'] - expected_success_rate) < 0.01

            # Verify cost calculations
            expected_total_cost = sample_execution_data['total_cost'].sum()
            assert abs(summary['total_cost'] - expected_total_cost) < 0.01

    @pytest.mark.asyncio
    async def test_agent_performance_analysis(self, analytics_engine, sample_execution_data):
        """Test agent performance comparison accuracy"""
        with patch.object(analytics_engine, '_fetch_execution_data', return_value=sample_execution_data):
            insights = await analytics_engine.generate_usage_insights("30d")

            agent_performance = insights['agent_performance']

            # Verify both agents are analyzed
            agent_ids = [agent['agent_id'] for agent in agent_performance]
            assert 'security_agent' in agent_ids
            assert 'web_dev_agent' in agent_ids

            # Verify performance metrics for security agent
            security_agent = next(agent for agent in agent_performance if agent['agent_id'] == 'security_agent')
            security_data = sample_execution_data[sample_execution_data['agent_id'] == 'security_agent']

            expected_query_count = len(security_data)
            assert security_agent['query_count'] == expected_query_count

            expected_avg_time = security_data['processing_time_ms'].mean()
            assert abs(security_agent['avg_response_time'] - expected_avg_time) < 1.0

    @pytest.mark.asyncio
    async def test_user_behavior_clustering(self, analytics_engine, sample_execution_data):
        """Test user behavior clustering analysis"""
        with patch.object(analytics_engine, '_fetch_execution_data', return_value=sample_execution_data):
            insights = await analytics_engine.generate_usage_insights("30d")

            user_behavior = insights['user_behavior']

            # Verify clustering results
            assert 'cluster_analysis' in user_behavior
            clusters = user_behavior['cluster_analysis']

            # Should have 3 clusters (as configured in the engine)
            assert len(clusters) == 3

            # Verify cluster characteristics
            total_users = sum(cluster['user_count'] for cluster in clusters)
            expected_users = sample_execution_data['user_id'].nunique()
            assert total_users == expected_users

    @pytest.mark.asyncio
    async def test_ml_optimization_recommendations(self, analytics_engine, sample_execution_data):
        """Test ML-based optimization recommendations"""
        with patch.object(analytics_engine, '_fetch_execution_data', return_value=sample_execution_data):
            with patch.object(analytics_engine, '_train_optimization_models') as mock_train:
                mock_train.return_value = {
                    'cost_recommendations': [
                        {'type': 'cost', 'priority': 'high', 'description': 'Optimize model selection'}
                    ],
                    'performance_recommendations': [
                        {'type': 'performance', 'priority': 'medium', 'description': 'Cache frequent queries'}
                    ]
                }

                insights = await analytics_engine.generate_usage_insights("30d")

                recommendations = insights['optimization_recommendations']

                # Verify recommendations are generated
                assert len(recommendations) > 0

                # Verify recommendation structure
                for rec in recommendations:
                    assert 'type' in rec
                    assert 'priority' in rec
                    assert 'description' in rec
                    assert rec['type'] in ['cost', 'performance', 'accuracy']
                    assert rec['priority'] in ['high', 'medium', 'low']

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, analytics_engine, sample_execution_data):
        """Test analytics caching mechanism"""
        with patch.object(analytics_engine, '_fetch_execution_data', return_value=sample_execution_data) as mock_fetch:
            # First call should fetch data
            insights1 = await analytics_engine.generate_usage_insights("30d")
            assert mock_fetch.call_count == 1

            # Second call should use cache
            insights2 = await analytics_engine.generate_usage_insights("30d")
            assert mock_fetch.call_count == 1  # No additional fetch

            # Results should be identical
            assert insights1['summary'] == insights2['summary']
```

## 5. Performance and Load Testing

### 5.1. Load Testing Framework

```python
# tests/performance/test_load_testing.py
import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

class TestPerformanceAndLoad:
    """Comprehensive performance and load testing"""

    @pytest.mark.performance
    async def test_concurrent_user_load(self):
        """Test system performance under concurrent user load"""
        api_base_url = "http://localhost:8000/api/v4"
        concurrent_users = 1000
        requests_per_user = 10

        async def user_session(session, user_id):
            """Simulate a user session with multiple requests"""
            response_times = []

            for request_num in range(requests_per_user):
                start_time = time.time()

                # Simulate different API calls
                endpoints = [
                    "/analytics/insights?time_range=7d",
                    "/agents/list",
                    "/workflows/execute",
                    "/admin/system/health"
                ]

                endpoint = endpoints[request_num % len(endpoints)]

                try:
                    async with session.get(f"{api_base_url}{endpoint}") as response:
                        await response.text()
                        response_time = (time.time() - start_time) * 1000
                        response_times.append(response_time)

                        # Verify response is successful
                        assert response.status < 500

                except Exception as e:
                    pytest.fail(f"Request failed for user {user_id}: {str(e)}")

            return response_times

        # Execute concurrent user sessions
        async with aiohttp.ClientSession() as session:
            tasks = [
                user_session(session, user_id)
                for user_id in range(concurrent_users)
            ]

            all_response_times = await asyncio.gather(*tasks)

        # Flatten response times
        flat_response_times = [time for user_times in all_response_times for time in user_times]

        # Performance assertions
        p95_response_time = statistics.quantiles(flat_response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(flat_response_times, n=100)[98]  # 99th percentile
        avg_response_time = statistics.mean(flat_response_times)

        # SLA requirements
        assert p95_response_time < 2000, f"P95 response time {p95_response_time}ms exceeds 2s SLA"
        assert p99_response_time < 5000, f"P99 response time {p99_response_time}ms exceeds 5s limit"
        assert avg_response_time < 1000, f"Average response time {avg_response_time}ms exceeds 1s target"

        print(f"Performance Results:")
        print(f"  Concurrent Users: {concurrent_users}")
        print(f"  Total Requests: {len(flat_response_times)}")
        print(f"  Average Response Time: {avg_response_time:.2f}ms")
        print(f"  P95 Response Time: {p95_response_time:.2f}ms")
        print(f"  P99 Response Time: {p99_response_time:.2f}ms")

    @pytest.mark.performance
    async def test_database_query_performance(self):
        """Test analytics database query performance under load"""
        from src.enterprise.analytics_engine import AdvancedAnalyticsEngine

        config = {
            "analytics_db_url": "postgresql://test:test@localhost:5432/test_analytics"
        }
        analytics_engine = AdvancedAnalyticsEngine(config)

        # Test complex analytics queries
        query_times = []

        for _ in range(100):  # 100 parallel analytics queries
            start_time = time.time()

            try:
                insights = await analytics_engine.generate_usage_insights("30d")
                query_time = (time.time() - start_time) * 1000
                query_times.append(query_time)

                # Verify query returns valid results
                assert 'summary' in insights
                assert 'trends' in insights

            except Exception as e:
                pytest.fail(f"Analytics query failed: {str(e)}")

        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)

        # Database performance requirements
        assert avg_query_time < 5000, f"Average query time {avg_query_time}ms exceeds 5s limit"
        assert max_query_time < 10000, f"Max query time {max_query_time}ms exceeds 10s limit"

    @pytest.mark.performance
    async def test_agent_factory_scalability(self):
        """Test agent factory performance under multiple concurrent creations"""
        from src.enterprise.agent_factory import AgentFactory, AgentSpec

        config = {
            "git_base_url": "https://github.com/test-org",
            "registry_url": "localhost:5000"
        }
        agent_factory = AgentFactory(config)

        # Create multiple agents concurrently
        agent_specs = [
            AgentSpec(
                name=f"test_agent_{i}",
                display_name=f"Test Agent {i}",
                description=f"Test agent number {i}",
                domain="testing",
                keywords=["test", f"agent{i}"],
                capabilities=["testing"],
                knowledge_sources=[]
            )
            for i in range(20)  # 20 concurrent agent creations
        ]

        deployment_config = {
            "environment": "development",
            "auto_deploy": False,
            "resource_limits": {"memory": "256M", "cpu": "0.25"}
        }

        start_time = time.time()

        with patch.multiple(
            agent_factory,
            _create_repository=Mock(return_value="/tmp/test-repo"),
            _generate_knowledge_schema=Mock(),
            _create_docker_config=Mock(),
            _generate_tests=Mock(),
            _register_mcp=Mock()
        ):
            tasks = [
                agent_factory.create_agent(spec, deployment_config)
                for spec in agent_specs
            ]

            creation_ids = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Verify all agents were created successfully
        assert len(creation_ids) == 20
        assert all(creation_id.startswith("agent_creation_") for creation_id in creation_ids)

        # Performance requirements
        avg_creation_time = total_time / 20
        assert avg_creation_time < 30, f"Average agent creation time {avg_creation_time}s exceeds 30s limit"
        assert total_time < 300, f"Total creation time {total_time}s exceeds 5 minute limit"
```

## 6. Disaster Recovery Testing

### 6.1. Disaster Recovery Test Suite

```python
# tests/enterprise/test_disaster_recovery.py
import pytest
import asyncio
import docker
import time
from unittest.mock import patch

class TestDisasterRecovery:
    """Disaster recovery and business continuity testing"""

    @pytest.fixture
    def docker_client(self):
        return docker.from_env()

    @pytest.mark.disaster_recovery
    async def test_database_failover(self, docker_client):
        """Test database failover and recovery"""
        # Simulate primary database failure
        try:
            primary_db = docker_client.containers.get("promptcraft-postgres")
            primary_db.stop()

            # Wait for failover detection
            await asyncio.sleep(30)

            # Verify secondary database takes over
            from src.enterprise.analytics_engine import AdvancedAnalyticsEngine
            config = {
                "analytics_db_url": "postgresql://test:test@localhost:5433/test_analytics"  # Secondary
            }
            analytics_engine = AdvancedAnalyticsEngine(config)

            # Test database connectivity
            insights = await analytics_engine.generate_usage_insights("7d")
            assert 'summary' in insights

        finally:
            # Restore primary database
            primary_db.start()
            await asyncio.sleep(20)  # Allow startup time

    @pytest.mark.disaster_recovery
    async def test_service_auto_recovery(self, docker_client):
        """Test automatic service recovery after failure"""
        services_to_test = [
            "promptcraft-api-1",
            "promptcraft-redis",
            "zen-mcp-1"
        ]

        for service_name in services_to_test:
            try:
                # Stop service
                service_container = docker_client.containers.get(service_name)
                service_container.stop()

                # Wait for recovery (should auto-restart)
                await asyncio.sleep(60)

                # Verify service is running again
                service_container.reload()
                assert service_container.status == "running"

                # Verify service health
                health = service_container.attrs['State'].get('Health', {})
                if health:
                    assert health['Status'] == 'healthy'

            except Exception as e:
                pytest.fail(f"Service {service_name} failed to recover: {str(e)}")

    @pytest.mark.disaster_recovery
    async def test_backup_restoration(self):
        """Test backup and restoration procedures"""
        from src.enterprise.backup_manager import BackupManager

        backup_manager = BackupManager({
            "backup_location": "/tmp/test-backups",
            "databases": ["promptcraft_analytics"],
            "volumes": ["knowledge_data", "user_data"]
        })

        # Create test backup
        backup_id = await backup_manager.create_backup()
        assert backup_id is not None

        # Simulate data corruption/loss
        # ... (simulate data loss)

        # Restore from backup
        restore_success = await backup_manager.restore_backup(backup_id)
        assert restore_success == True

        # Verify data integrity after restoration
        # ... (verify restored data)

    @pytest.mark.disaster_recovery
    async def test_cross_region_failover(self):
        """Test failover to different geographic region"""
        # This would test failover to a different data center/region
        # Implementation depends on specific infrastructure setup
        pass
```

## 7. CI/CD Pipeline Testing

### 7.1. Pipeline Validation

```yaml
# .github/workflows/phase4-testing.yml
name: Phase 4 Enterprise Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with dev,test

    - name: Run unit tests
      run: |
        poetry run pytest tests/unit/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_analytics
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with dev,test

    - name: Run integration tests
      run: |
        poetry run pytest tests/integration/ -v
      env:
        ANALYTICS_DB_URL: postgresql://postgres:test@localhost:5432/test_analytics
        REDIS_URL: redis://localhost:6379

  security-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
    - uses: actions/checkout@v4

    - name: Run OWASP ZAP scan
      uses: zaproxy/action-full-scan@v0.4.0
      with:
        target: 'http://localhost:8000'

    - name: Run security compliance tests
      run: |
        poetry run pytest tests/enterprise/test_security_compliance.py -v -m security

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
    - uses: actions/checkout@v4

    - name: Set up test environment
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 60  # Wait for services to start

    - name: Run performance tests
      run: |
        poetry run pytest tests/performance/ -v -m performance

    - name: Cleanup
      run: |
        docker-compose -f docker-compose.test.yml down

  disaster-recovery-tests:
    runs-on: ubuntu-latest
    needs: [security-tests, performance-tests]
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Run disaster recovery tests
      run: |
        poetry run pytest tests/enterprise/test_disaster_recovery.py -v -m disaster_recovery
```

## 8. Quality Gates and Success Criteria

### 8.1. Automated Quality Gates

**Security Quality Gate:**
- [ ] 100% pass rate on OWASP ZAP security scans
- [ ] Zero critical vulnerabilities in dependency scans
- [ ] 100% audit event capture for all user actions
- [ ] SSO integration tested with major identity providers

**Performance Quality Gate:**
- [ ] P95 response time < 2s under 1000 concurrent users
- [ ] Database queries complete within 5s average
- [ ] Agent creation completes within 15 minutes
- [ ] 99.9% system availability validated

**Functionality Quality Gate:**
- [ ] 95% test coverage across all Phase 4 components
- [ ] 100% API contract validation
- [ ] Analytics accuracy within 95% for ML recommendations
- [ ] Disaster recovery RTO < 4 hours validated

**Compliance Quality Gate:**
- [ ] SOC2 compliance requirements validated
- [ ] GDPR data portability tested
- [ ] Audit retention policies meet 7-year requirement
- [ ] Data classification enforced for all sensitive data

### 8.2. Manual Validation Checklist

**Enterprise Features:**
- [ ] SSO login flow works with corporate identity provider
- [ ] Analytics dashboard displays accurate usage insights
- [ ] Agent factory creates functional agents from templates
- [ ] Custom MCP servers deploy and integrate successfully
- [ ] Compliance reports generate required audit data

**User Experience:**
- [ ] Multi-tenant isolation verified
- [ ] Role-based access control enforced
- [ ] Performance remains consistent under enterprise load
- [ ] Error handling provides meaningful feedback
- [ ] Documentation covers all enterprise features

**Operations:**
- [ ] Monitoring alerts trigger appropriately
- [ ] Backup and restoration procedures validated
- [ ] Log aggregation captures all relevant events
- [ ] Service discovery works across all components
- [ ] Scaling procedures tested and documented

This comprehensive testing strategy ensures Phase 4 enterprise features meet the highest standards for security, performance, compliance, and reliability required for enterprise deployment.
