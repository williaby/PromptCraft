"""End-to-end integration tests for PromptCraft-Hybrid.

This module tests the complete integration workflow from query input through
QueryCounselor, HydeProcessor, vector store operations, and MCP orchestration,
ensuring all components work together seamlessly in realistic scenarios.
"""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.config.health import HealthChecker
from src.config.settings import ApplicationSettings
from src.core.query_counselor import QueryCounselor
from src.core.vector_store import (
    DEFAULT_VECTOR_DIMENSIONS,
    ConnectionStatus,
    EnhancedMockVectorStore,
    VectorDocument,
)
from src.mcp_integration.config_manager import MCPConfigurationManager
from src.mcp_integration.mcp_client import (
    MCPConnectionState,
    MCPHealthStatus,
    MCPTimeoutError,
)


class TestEndToEndIntegration:
    """End-to-end integration tests for complete system workflows."""

    @pytest.fixture
    def full_system_settings(self):
        """Create full system configuration for end-to-end testing."""
        return ApplicationSettings(
            # MCP Configuration
            mcp_enabled=True,
            mcp_server_url="http://localhost:3000",
            mcp_timeout=30.0,
            mcp_max_retries=3,
            mcp_health_check_interval=60.0,
            # Vector Store Configuration
            qdrant_enabled=False,  # Use mock for testing
            vector_store_type="mock",
            vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
            # Performance Configuration
            performance_monitoring_enabled=True,
            max_concurrent_queries=10,
            query_timeout=30.0,
            # Health Check Configuration
            health_check_enabled=True,
            health_check_interval=30.0,
            # Error Handling Configuration
            error_recovery_enabled=True,
            circuit_breaker_enabled=True,
            retry_enabled=True,
        )

    @pytest.fixture
    def sample_knowledge_documents(self):
        """Create sample knowledge documents for testing."""
        return [
            VectorDocument(
                id="kb_doc_1",
                content="FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic API documentation, data validation, and serialization.",
                embedding=[0.8, 0.2, 0.9, 0.1, 0.7] + [0.1] * (DEFAULT_VECTOR_DIMENSIONS - 5),
                metadata={
                    "framework": "fastapi",
                    "topic": "web_development",
                    "difficulty": "intermediate",
                    "language": "python",
                    "category": "framework",
                },
                collection="knowledge_base",
            ),
            VectorDocument(
                id="kb_doc_2",
                content="Async programming in Python allows you to write concurrent code that can handle multiple tasks simultaneously. It's particularly useful for I/O-bound operations and network requests.",
                embedding=[0.7, 0.8, 0.3, 0.9, 0.2] + [0.2] * (DEFAULT_VECTOR_DIMENSIONS - 5),
                metadata={
                    "concept": "async_programming",
                    "topic": "concurrency",
                    "difficulty": "advanced",
                    "language": "python",
                    "category": "concept",
                },
                collection="knowledge_base",
            ),
            VectorDocument(
                id="kb_doc_3",
                content="Vector databases are specialized databases designed to store and search high-dimensional vectors efficiently. They're essential for semantic search, recommendation systems, and AI applications.",
                embedding=[0.9, 0.4, 0.7, 0.6, 0.8] + [0.3] * (DEFAULT_VECTOR_DIMENSIONS - 5),
                metadata={
                    "technology": "vector_database",
                    "topic": "data_storage",
                    "difficulty": "advanced",
                    "category": "technology",
                },
                collection="knowledge_base",
            ),
            VectorDocument(
                id="kb_doc_4",
                content="Machine learning model deployment involves taking a trained model and making it available for inference in production environments. This includes considerations for scalability, monitoring, and maintenance.",
                embedding=[0.6, 0.9, 0.1, 0.8, 0.4] + [0.4] * (DEFAULT_VECTOR_DIMENSIONS - 5),
                metadata={
                    "concept": "ml_deployment",
                    "topic": "machine_learning",
                    "difficulty": "advanced",
                    "category": "concept",
                },
                collection="knowledge_base",
            ),
            VectorDocument(
                id="kb_doc_5",
                content="Error handling in distributed systems requires careful consideration of failure modes, retry strategies, and circuit breaker patterns to ensure system resilience and reliability.",
                embedding=[0.3, 0.7, 0.8, 0.2, 0.9] + [0.5] * (DEFAULT_VECTOR_DIMENSIONS - 5),
                metadata={
                    "concept": "error_handling",
                    "topic": "distributed_systems",
                    "difficulty": "expert",
                    "category": "concept",
                },
                collection="knowledge_base",
            ),
        ]

    @pytest.fixture
    def sample_test_queries(self):
        """Create sample test queries for end-to-end testing."""
        return [
            {
                "query": "How do I build a REST API with FastAPI?",
                "expected_intent": "framework_usage",
                "expected_agents": ["create_agent", "code_agent"],
                "expected_knowledge_topics": ["fastapi", "web_development"],
            },
            {
                "query": "What are the best practices for async programming in Python?",
                "expected_intent": "best_practices",
                "expected_agents": ["create_agent", "analysis_agent"],
                "expected_knowledge_topics": ["async_programming", "concurrency"],
            },
            {
                "query": "How do I implement semantic search with vector databases?",
                "expected_intent": "implementation_guide",
                "expected_agents": ["create_agent", "technical_agent"],
                "expected_knowledge_topics": ["vector_database", "semantic_search"],
            },
            {
                "query": "What should I consider when deploying ML models to production?",
                "expected_intent": "deployment_guidance",
                "expected_agents": ["create_agent", "ml_agent"],
                "expected_knowledge_topics": ["ml_deployment", "production"],
            },
            {
                "query": "How do I handle errors in distributed systems?",
                "expected_intent": "error_handling",
                "expected_agents": ["create_agent", "system_agent"],
                "expected_knowledge_topics": ["error_handling", "distributed_systems"],
            },
        ]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_query_processing_workflow(
        self, full_system_settings, sample_knowledge_documents, sample_test_queries,
    ):
        """Test complete query processing workflow from input to output."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock MCP client with realistic responses
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.health_status = MCPHealthStatus.HEALTHY

            # Mock agent orchestration responses
            def mock_orchestrate_agents(agent_configs, query, context=None):
                return [
                    MagicMock(
                        agent_id=config.get("agent_id", "create_agent"),
                        success=True,
                        content=f"Response from {config.get('agent_id', 'create_agent')} for query: {query[:50]}...",
                        metadata={"processing_time": 0.5, "confidence": 0.9},
                        raw_response={
                            "status": "success",
                            "data": f"Processed by {config.get('agent_id', 'create_agent')}",
                        },
                    )
                    for config in agent_configs
                ]

            mock_mcp_client.orchestrate_agents = AsyncMock(side_effect=mock_orchestrate_agents)

            # Mock vector store with knowledge documents
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.01},
            )
            await mock_vector_store.connect()

            # Insert knowledge documents
            await mock_vector_store.insert_documents(sample_knowledge_documents)

            # Mock HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store

            def mock_process_query(query):
                return {
                    "original_query": query,
                    "enhanced_query": f"Enhanced: {query}",
                    "enhancement_score": 0.85,
                    "relevant_documents": [
                        {
                            "id": "kb_doc_1",
                            "content": "FastAPI framework information",
                            "score": 0.9,
                            "metadata": {"framework": "fastapi"},
                        },
                    ],
                    "enhancement_method": "semantic_expansion",
                    "processing_time": 0.2,
                }

            mock_hyde_processor.process_query = AsyncMock(side_effect=mock_process_query)

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                # Initialize QueryCounselor
                counselor = QueryCounselor()

                # Process each test query
                for test_case in sample_test_queries:
                    query = test_case["query"]
                    expected_intent = test_case["expected_intent"]
                    expected_agents = test_case["expected_agents"]

                    # Step 1: Analyze query intent
                    intent_analysis = await counselor.analyze_intent(query)

                    # Verify intent analysis
                    assert intent_analysis is not None
                    assert "intent" in intent_analysis
                    assert "confidence" in intent_analysis
                    assert intent_analysis["confidence"] > 0.5

                    # Step 2: Process query with HyDE
                    hyde_result = await counselor.hyde_processor.process_query(query)

                    # Verify HyDE processing
                    assert hyde_result["original_query"] == query
                    assert hyde_result["enhanced_query"].startswith("Enhanced:")
                    assert hyde_result["enhancement_score"] > 0.7
                    assert len(hyde_result["relevant_documents"]) > 0

                    # Step 3: Select appropriate agents
                    selected_agents = await counselor.select_agents(intent_analysis)

                    # Verify agent selection
                    assert len(selected_agents) > 0
                    assert any(agent.get("agent_id") == "create_agent" for agent in selected_agents)

                    # Step 4: Orchestrate workflow
                    final_responses = await counselor.orchestrate_workflow(
                        selected_agents,
                        hyde_result["enhanced_query"],
                        {"original_query": query, "intent": intent_analysis, "hyde_result": hyde_result},
                    )

                    # Verify final responses
                    assert len(final_responses) > 0
                    for response in final_responses:
                        assert response.success is True
                        assert response.content is not None
                        assert len(response.content) > 0
                        assert response.metadata["confidence"] > 0.5

                    # Step 5: Verify end-to-end performance
                    assert hyde_result["processing_time"] < 1.0  # HyDE processing under 1s

                    # Verify MCP orchestration was called correctly
                    mock_mcp_client.orchestrate_agents.assert_called()

                    # Verify vector store search was performed
                    assert mock_vector_store.get_metrics().search_count > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_performance_requirements(self, full_system_settings, sample_knowledge_documents):
        """Test that end-to-end performance meets requirements (<2s total)."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock fast MCP client
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.orchestrate_agents = AsyncMock(
                return_value=[
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content="Fast response from create_agent",
                        metadata={"processing_time": 0.1},
                        raw_response={"status": "success"},
                    ),
                ],
            )

            # Mock fast vector store
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.005},  # Very low latency
            )
            await mock_vector_store.connect()
            await mock_vector_store.insert_documents(sample_knowledge_documents)

            # Mock fast HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test query",
                    "enhanced_query": "Enhanced: test query",
                    "enhancement_score": 0.9,
                    "relevant_documents": [],
                    "processing_time": 0.05,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test performance with multiple queries
                test_queries = [
                    "How do I use FastAPI?",
                    "What is async programming?",
                    "How do vector databases work?",
                    "Best practices for ML deployment?",
                    "Error handling strategies?",
                ]

                for query in test_queries:
                    start_time = time.time()

                    # Execute complete workflow
                    intent = await counselor.analyze_intent(query)
                    hyde_result = await counselor.hyde_processor.process_query(query)
                    agents = await counselor.select_agents(intent)
                    responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                    total_time = time.time() - start_time

                    # Verify performance requirement
                    assert total_time < 2.0, f"Query processing took {total_time:.2f}s, exceeding 2s requirement"

                    # Verify response quality
                    assert len(responses) > 0
                    assert all(response.success for response in responses)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery_workflow(self, full_system_settings, sample_knowledge_documents):
        """Test end-to-end error recovery and graceful degradation."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock MCP client with intermittent failures
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED

            call_count = 0

            def mock_orchestrate_with_failures(agent_configs, query, context=None):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Fail every 3rd call
                    raise MCPTimeoutError("Simulated timeout")
                return [
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content="Recovered response",
                        metadata={"processing_time": 0.5},
                    ),
                ]

            mock_mcp_client.orchestrate_agents = AsyncMock(side_effect=mock_orchestrate_with_failures)

            # Mock vector store with error rate
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.2, "base_latency": 0.01},  # 20% error rate
            )
            await mock_vector_store.connect()
            await mock_vector_store.insert_documents(sample_knowledge_documents)

            # Mock HyDE processor with occasional failures
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store

            hyde_call_count = 0

            def mock_hyde_with_failures(query):
                nonlocal hyde_call_count
                hyde_call_count += 1
                if hyde_call_count % 4 == 0:  # Fail every 4th call
                    raise RuntimeError("Vector store connection failed")
                return {
                    "original_query": query,
                    "enhanced_query": f"Enhanced: {query}",
                    "enhancement_score": 0.8,
                    "relevant_documents": [],
                    "processing_time": 0.1,
                }

            mock_hyde_processor.process_query = AsyncMock(side_effect=mock_hyde_with_failures)

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test error recovery across multiple queries
                successful_queries = 0
                failed_queries = 0

                for i in range(15):  # Test with multiple queries
                    try:
                        query = f"Test query {i}"

                        # Execute workflow with error recovery
                        intent = await counselor.analyze_intent(query)

                        # Try HyDE processing with fallback
                        try:
                            hyde_result = await counselor.hyde_processor.process_query(query)
                        except RuntimeError:
                            # Fallback to original query
                            hyde_result = {
                                "original_query": query,
                                "enhanced_query": query,
                                "enhancement_score": 0.5,
                                "relevant_documents": [],
                                "processing_time": 0.0,
                            }

                        agents = await counselor.select_agents(intent)

                        # Try orchestration with retry
                        try:
                            responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])
                            successful_queries += 1
                        except MCPTimeoutError:
                            failed_queries += 1
                            # System should handle this gracefully
                            continue

                        # Verify responses when successful
                        assert len(responses) > 0
                        assert all(response.success for response in responses)

                    except Exception as e:
                        failed_queries += 1
                        # Should be controlled failures
                        assert isinstance(e, (MCPTimeoutError, RuntimeError))

                # Verify system resilience
                assert successful_queries > 0, "No queries succeeded - system not resilient"
                assert failed_queries > 0, "No failures occurred - test may not be realistic"

                # System should remain stable despite failures
                assert counselor.mcp_client is not None
                assert counselor.hyde_processor is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_concurrent_processing(self, full_system_settings, sample_knowledge_documents):
        """Test end-to-end concurrent query processing."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock MCP client with concurrent support
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED

            async def mock_concurrent_orchestration(agent_configs, query, context=None):
                await asyncio.sleep(0.1)  # Simulate processing time
                return [
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content=f"Concurrent response for: {query[:30]}...",
                        metadata={"processing_time": 0.1},
                    ),
                ]

            mock_mcp_client.orchestrate_agents = mock_concurrent_orchestration

            # Mock vector store with concurrent support
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.02},
            )
            await mock_vector_store.connect()
            await mock_vector_store.insert_documents(sample_knowledge_documents)

            # Mock HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store

            async def mock_concurrent_hyde(query):
                await asyncio.sleep(0.05)  # Simulate processing time
                return {
                    "original_query": query,
                    "enhanced_query": f"Enhanced: {query}",
                    "enhancement_score": 0.85,
                    "relevant_documents": [],
                    "processing_time": 0.05,
                }

            mock_hyde_processor.process_query = mock_concurrent_hyde

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test concurrent query processing
                concurrent_queries = [
                    "How do I implement authentication in FastAPI?",
                    "What are the best practices for async programming?",
                    "How do I optimize vector database searches?",
                    "What should I consider for ML model deployment?",
                    "How do I handle errors in distributed systems?",
                    "What are the latest trends in web development?",
                    "How do I implement caching strategies?",
                    "What are the security best practices for APIs?",
                ]

                async def process_single_query(query):
                    start_time = time.time()

                    intent = await counselor.analyze_intent(query)
                    hyde_result = await counselor.hyde_processor.process_query(query)
                    agents = await counselor.select_agents(intent)
                    responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                    processing_time = time.time() - start_time

                    return {
                        "query": query,
                        "responses": responses,
                        "processing_time": processing_time,
                        "success": len(responses) > 0 and all(r.success for r in responses),
                    }

                # Execute queries concurrently
                start_time = time.time()
                results = await asyncio.gather(
                    *[process_single_query(query) for query in concurrent_queries], return_exceptions=True,
                )
                total_time = time.time() - start_time

                # Verify concurrent processing
                successful_results = [r for r in results if not isinstance(r, Exception) and r["success"]]

                assert len(successful_results) >= len(concurrent_queries) * 0.8  # At least 80% success rate
                assert total_time < 10.0  # All queries should complete within 10 seconds

                # Verify individual query performance
                for result in successful_results:
                    assert result["processing_time"] < 3.0  # Each query under 3 seconds
                    assert len(result["responses"]) > 0
                    assert all(response.success for response in result["responses"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_health_monitoring_integration(self, full_system_settings, sample_knowledge_documents):
        """Test end-to-end health monitoring and system status."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock healthy MCP client
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.health_status = MCPHealthStatus.HEALTHY
            mock_mcp_client.get_health_status = AsyncMock(return_value=MCPHealthStatus.HEALTHY)
            mock_mcp_client.orchestrate_agents = AsyncMock(
                return_value=[MagicMock(agent_id="create_agent", success=True, content="Healthy response")],
            )

            # Mock healthy vector store
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.01},
            )
            await mock_vector_store.connect()
            await mock_vector_store.insert_documents(sample_knowledge_documents)

            # Mock healthy HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test",
                    "enhanced_query": "Enhanced: test",
                    "enhancement_score": 0.9,
                    "relevant_documents": [],
                    "processing_time": 0.05,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test health monitoring integration
                health_checker = HealthChecker(full_system_settings)

                # Check overall system health
                system_health = await health_checker.check_system_health()

                # Verify system health
                assert system_health["status"] == "healthy"
                assert system_health["components"]["mcp_client"]["status"] == "healthy"
                assert system_health["components"]["vector_store"]["status"] == "healthy"

                # Test query processing with health monitoring
                query = "Test query for health monitoring"

                # Execute workflow
                intent = await counselor.analyze_intent(query)
                hyde_result = await counselor.hyde_processor.process_query(query)
                agents = await counselor.select_agents(intent)
                responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                # Verify successful processing
                assert len(responses) > 0
                assert all(response.success for response in responses)

                # Check health after processing
                post_processing_health = await health_checker.check_system_health()
                assert post_processing_health["status"] == "healthy"

                # Verify component health checks
                mcp_health = await mock_mcp_client.get_health_status()
                assert mcp_health == MCPHealthStatus.HEALTHY

                vector_store_health = await mock_vector_store.health_check()
                assert vector_store_health.status == ConnectionStatus.HEALTHY

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_configuration_integration(self, full_system_settings):
        """Test end-to-end configuration management and validation."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock configuration manager
            config_manager = MCPConfigurationManager()

            # Test configuration validation
            is_valid = config_manager.validate_configuration()
            assert is_valid is True

            # Test configuration loading
            mcp_config = config_manager.get_mcp_configuration()
            assert mcp_config is not None
            assert mcp_config["server_url"] == "http://localhost:3000"
            assert mcp_config["timeout"] == 30.0

            # Test parallel execution configuration
            parallel_config = config_manager.get_parallel_execution_config()
            assert parallel_config is not None
            assert parallel_config["max_concurrent"] > 0
            assert parallel_config["timeout_seconds"] > 0

            # Mock MCP client with configuration
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.orchestrate_agents = AsyncMock(
                return_value=[MagicMock(agent_id="create_agent", success=True, content="Configured response")],
            )

            # Mock vector store with configuration
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.01},
            )
            await mock_vector_store.connect()

            # Mock HyDE processor with configuration
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test",
                    "enhanced_query": "Enhanced: test",
                    "enhancement_score": 0.9,
                    "relevant_documents": [],
                    "processing_time": 0.05,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test configuration-driven workflow
                query = "Test query for configuration integration"

                intent = await counselor.analyze_intent(query)
                hyde_result = await counselor.hyde_processor.process_query(query)
                agents = await counselor.select_agents(intent)
                responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                # Verify successful processing with configuration
                assert len(responses) > 0
                assert all(response.success for response in responses)

                # Verify configuration was applied
                mock_mcp_client.orchestrate_agents.assert_called_once()
                mock_hyde_processor.process_query.assert_called_once_with(query)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_real_world_scenario(self, full_system_settings, sample_knowledge_documents):
        """Test end-to-end processing with realistic user scenarios."""

        with patch("src.config.settings.get_settings", return_value=full_system_settings):
            # Mock realistic MCP client responses
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED

            def mock_realistic_orchestration(agent_configs, query, context=None):
                # Simulate different agent responses based on query content
                responses = []
                for config in agent_configs:
                    agent_id = config.get("agent_id", "create_agent")

                    if "fastapi" in query.lower():
                        content = "Here's how to build a REST API with FastAPI:\n\n1. Install FastAPI: `pip install fastapi uvicorn`\n2. Create a basic app:\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}\n```\n3. Run the server: `uvicorn main:app --reload`"
                    elif "async" in query.lower():
                        content = "Best practices for async programming in Python:\n\n1. Use async/await syntax consistently\n2. Don't mix blocking and non-blocking code\n3. Use asyncio.gather() for concurrent operations\n4. Handle exceptions properly in async functions\n5. Use connection pooling for database operations"
                    elif "vector" in query.lower() or "search" in query.lower():
                        content = "Implementing semantic search with vector databases:\n\n1. Choose a vector database (Qdrant, Pinecone, Chroma)\n2. Generate embeddings for your documents\n3. Store vectors with metadata\n4. Implement similarity search\n5. Add filtering and ranking capabilities"
                    else:
                        content = f"Comprehensive response from {agent_id} for the query about {query[:50]}..."

                    responses.append(
                        MagicMock(
                            agent_id=agent_id,
                            success=True,
                            content=content,
                            metadata={
                                "processing_time": 0.3,
                                "confidence": 0.92,
                                "sources": ["knowledge_base", "documentation"],
                                "word_count": len(content.split()),
                            },
                        ),
                    )

                return responses

            mock_mcp_client.orchestrate_agents = AsyncMock(side_effect=mock_realistic_orchestration)

            # Mock realistic vector store
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.02},
            )
            await mock_vector_store.connect()
            await mock_vector_store.insert_documents(sample_knowledge_documents)

            # Mock realistic HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store

            def mock_realistic_hyde(query):
                # Simulate realistic HyDE enhancement
                enhanced_query = f"Enhanced semantic query: {query}"

                # Simulate relevant document retrieval
                relevant_docs = []
                for doc in sample_knowledge_documents:
                    if any(keyword in query.lower() for keyword in doc.metadata.get("topic", "").lower().split("_")):
                        relevant_docs.append(
                            {
                                "id": doc.id,
                                "content": doc.content[:200] + "...",
                                "score": 0.85,
                                "metadata": doc.metadata,
                            },
                        )

                return {
                    "original_query": query,
                    "enhanced_query": enhanced_query,
                    "enhancement_score": 0.88,
                    "relevant_documents": relevant_docs[:3],  # Top 3 relevant documents
                    "enhancement_method": "semantic_expansion",
                    "processing_time": 0.15,
                }

            mock_hyde_processor.process_query = AsyncMock(side_effect=mock_realistic_hyde)

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test realistic user scenarios
                realistic_scenarios = [
                    {
                        "query": "I want to build a web API with FastAPI that can handle user authentication and database connections",
                        "expected_keywords": ["fastapi", "authentication", "database"],
                        "expected_response_length": 100,
                    },
                    {
                        "query": "What are the best practices for writing asynchronous code in Python for high-performance applications?",
                        "expected_keywords": ["async", "performance", "python"],
                        "expected_response_length": 80,
                    },
                    {
                        "query": "How can I implement a semantic search system using vector databases for my document collection?",
                        "expected_keywords": ["semantic", "search", "vector"],
                        "expected_response_length": 90,
                    },
                ]

                for scenario in realistic_scenarios:
                    query = scenario["query"]
                    expected_keywords = scenario["expected_keywords"]
                    expected_length = scenario["expected_response_length"]

                    # Execute complete workflow
                    start_time = time.time()

                    intent = await counselor.analyze_intent(query)
                    hyde_result = await counselor.hyde_processor.process_query(query)
                    agents = await counselor.select_agents(intent)
                    responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                    processing_time = time.time() - start_time

                    # Verify realistic processing
                    assert processing_time < 2.0  # Performance requirement
                    assert len(responses) > 0
                    assert all(response.success for response in responses)

                    # Verify response quality
                    for response in responses:
                        assert len(response.content) > expected_length
                        assert response.metadata["confidence"] > 0.8
                        assert response.metadata["word_count"] > 20

                        # Check that response contains expected keywords
                        response_lower = response.content.lower()
                        assert any(keyword in response_lower for keyword in expected_keywords)

                    # Verify HyDE enhancement
                    assert len(hyde_result["relevant_documents"]) > 0
                    assert hyde_result["enhancement_score"] > 0.8

                    # Verify that relevant documents were found
                    for doc in hyde_result["relevant_documents"]:
                        assert doc["score"] > 0.7
                        assert "metadata" in doc
                        assert "id" in doc
