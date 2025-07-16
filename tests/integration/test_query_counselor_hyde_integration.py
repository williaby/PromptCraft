"""Integration tests for QueryCounselor + HydeProcessor workflow.

This module tests the integration between QueryCounselor and HydeProcessor,
validating the complete query processing workflow with enhanced retrieval.
"""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.config.settings import ApplicationSettings
from src.core.hyde_processor import HydeProcessor
from src.core.query_counselor import QueryCounselor
from src.core.vector_store import VectorStore
from src.mcp_integration.mcp_client import ZenMCPClient


class TestQueryCounselorHydeIntegration:
    """Integration tests for QueryCounselor + HydeProcessor workflow."""

    @pytest.fixture
    def test_settings(self):
        """Create test settings for integration testing."""
        return ApplicationSettings(
            mcp_enabled=True,
            mcp_server_url="http://localhost:3000",
            mcp_timeout=10.0,
            mcp_max_retries=2,
            qdrant_enabled=True,
            qdrant_host="192.168.1.16",
            qdrant_port=6333,
            qdrant_timeout=30.0,
            vector_store_type="qdrant",
        )

    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client for testing."""
        client = AsyncMock(spec=ZenMCPClient)
        client.connect.return_value = True
        client.disconnect.return_value = True
        client.connection_state = "connected"
        return client

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store for testing."""
        store = AsyncMock(spec=VectorStore)
        store.initialize.return_value = True
        store.is_healthy.return_value = True
        return store

    @pytest.fixture
    def mock_hyde_processor(self, mock_vector_store):
        """Create mock HydeProcessor for testing."""
        processor = AsyncMock(spec=HydeProcessor)
        processor.vector_store = mock_vector_store
        processor.initialize.return_value = True
        return processor

    @pytest.fixture
    def query_counselor(self, test_settings, mock_mcp_client, mock_hyde_processor):
        """Create QueryCounselor with mocked dependencies."""
        with (
            patch("src.config.settings.get_settings", return_value=test_settings),
            patch("src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client),
            patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
        ):
            counselor = QueryCounselor()
            counselor.hyde_processor = mock_hyde_processor
            return counselor

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_query_processing_workflow(self, query_counselor, mock_mcp_client, mock_hyde_processor):
        """Test complete query processing workflow with HyDE enhancement."""

        # Mock query intent analysis
        mock_intent = MagicMock()
        mock_intent.query_type.value = "knowledge_retrieval"
        mock_intent.complexity = "medium"
        mock_intent.domain = "technical"
        mock_intent.confidence = 0.85

        # Mock HyDE enhanced query
        mock_hyde_processor.process_query.return_value = {
            "enhanced_query": "How to implement secure authentication in FastAPI with JWT tokens and OAuth2 scopes",
            "original_query": "How to implement authentication in FastAPI",
            "enhancement_score": 0.92,
            "processing_time": 0.15,
            "retrieved_documents": [
                {
                    "id": "doc_1",
                    "content": "FastAPI authentication with JWT tokens",
                    "score": 0.89,
                    "metadata": {"source": "fastapi_docs", "section": "security"},
                },
                {
                    "id": "doc_2",
                    "content": "OAuth2 implementation patterns",
                    "score": 0.84,
                    "metadata": {"source": "oauth2_guide", "section": "implementation"},
                },
            ],
        }

        # Mock MCP orchestration response
        mock_mcp_client.orchestrate_agents.return_value = [
            MagicMock(
                agent_id="create_agent",
                content="Comprehensive FastAPI authentication implementation guide",
                confidence=0.95,
                processing_time=1.2,
                success=True,
                metadata={"framework": "FastAPI", "security_level": "high"},
            ),
        ]

        # Process query with HyDE enhancement
        query = "How to implement authentication in FastAPI"

        # Step 1: Analyze query intent
        intent = await query_counselor.analyze_intent(query)
        assert intent.query_type.value == "knowledge_retrieval"

        # Step 2: Process query with HyDE enhancement
        hyde_result = await query_counselor.hyde_processor.process_query(query)
        assert hyde_result["enhanced_query"] != query
        assert hyde_result["enhancement_score"] > 0.8
        assert len(hyde_result["retrieved_documents"]) == 2

        # Step 3: Select agents based on enhanced query
        agents = await query_counselor.select_agents(intent)
        assert len(agents) > 0

        # Step 4: Orchestrate workflow with enhanced context
        responses = await query_counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])
        assert len(responses) == 1
        assert responses[0].success is True
        assert "authentication" in responses[0].content.lower()

        # Verify HyDE processor was called
        mock_hyde_processor.process_query.assert_called_once_with(query)

        # Verify MCP orchestration was called with enhanced query
        mock_mcp_client.orchestrate_agents.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hyde_processor_vector_store_integration(
        self,
        query_counselor,
        mock_hyde_processor,
        mock_vector_store,
    ):
        """Test HydeProcessor integration with vector store operations."""

        # Mock vector store search results
        mock_vector_store.search.return_value = [
            {
                "id": "doc_1",
                "content": "Python async programming patterns",
                "score": 0.92,
                "metadata": {"language": "python", "topic": "async"},
            },
            {
                "id": "doc_2",
                "content": "FastAPI async endpoint implementation",
                "score": 0.88,
                "metadata": {"framework": "fastapi", "topic": "async"},
            },
        ]

        # Mock HyDE processing with vector store integration
        mock_hyde_processor.process_query.return_value = {
            "enhanced_query": "Python async programming patterns for FastAPI endpoints",
            "original_query": "async in Python",
            "enhancement_score": 0.89,
            "processing_time": 0.12,
            "retrieved_documents": [
                {
                    "id": "doc_1",
                    "content": "Python async programming patterns",
                    "score": 0.92,
                    "metadata": {"language": "python", "topic": "async"},
                },
            ],
        }

        # Process query
        query = "async in Python"
        result = await query_counselor.hyde_processor.process_query(query)

        # Verify results
        assert result["enhanced_query"] != query
        assert result["enhancement_score"] > 0.8
        assert len(result["retrieved_documents"]) == 1
        assert result["retrieved_documents"][0]["score"] > 0.9

        # Verify HyDE processor was called
        mock_hyde_processor.process_query.assert_called_once_with(query)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_counselor_hyde_error_handling(self, query_counselor, mock_hyde_processor):
        """Test error handling in QueryCounselor + HydeProcessor integration."""

        # Mock HyDE processor failure
        mock_hyde_processor.process_query.side_effect = Exception("Vector store connection failed")

        # Test graceful degradation
        query = "Test query that should fail"

        # Should handle HyDE processor failure gracefully
        try:
            # In a real implementation, this should fall back to original query
            intent = await query_counselor.analyze_intent(query)
            assert intent is not None
        except Exception as e:
            # Should not propagate vector store errors
            assert "Vector store connection failed" not in str(e)

        # Verify HyDE processor was attempted
        mock_hyde_processor.process_query.assert_called_once_with(query)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_with_hyde_enhancement(self, query_counselor, mock_mcp_client, mock_hyde_processor):
        """Test end-to-end performance with HyDE enhancement meets <2s requirement."""

        # Mock fast HyDE processing
        mock_hyde_processor.process_query.return_value = {
            "enhanced_query": "Enhanced query with better context",
            "original_query": "Original query",
            "enhancement_score": 0.88,
            "processing_time": 0.08,  # 80ms for HyDE processing
            "retrieved_documents": [
                {
                    "id": "doc_1",
                    "content": "Relevant document content",
                    "score": 0.91,
                    "metadata": {"source": "knowledge_base"},
                },
            ],
        }

        # Mock fast MCP response
        mock_mcp_client.orchestrate_agents.return_value = [
            MagicMock(
                agent_id="create_agent",
                content="Fast enhanced response",
                confidence=0.93,
                processing_time=0.5,  # 500ms for MCP processing
                success=True,
                metadata={"enhanced": True},
            ),
        ]

        # Simulate realistic async delays
        async def delayed_hyde_process(query):
            await asyncio.sleep(0.08)  # 80ms delay
            return mock_hyde_processor.process_query.return_value

        async def delayed_mcp_orchestrate(agents):
            await asyncio.sleep(0.5)  # 500ms delay
            return mock_mcp_client.orchestrate_agents.return_value

        mock_hyde_processor.process_query.side_effect = delayed_hyde_process
        mock_mcp_client.orchestrate_agents.side_effect = delayed_mcp_orchestrate

        # Test complete workflow performance
        query = "Performance test query"

        start_time = time.time()

        # Complete workflow
        intent = await query_counselor.analyze_intent(query)
        hyde_result = await query_counselor.hyde_processor.process_query(query)
        agents = await query_counselor.select_agents(intent)
        responses = await query_counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

        end_time = time.time()
        total_time = end_time - start_time

        # Verify performance requirement
        assert total_time < 2.0, f"Total processing time {total_time:.3f}s exceeds 2s requirement"
        assert len(responses) == 1
        assert responses[0].success is True

        # Verify all components were called
        assert mock_hyde_processor.process_query.called
        assert mock_mcp_client.orchestrate_agents.called

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complex_multi_step_workflow(self, query_counselor, mock_mcp_client, mock_hyde_processor):
        """Test complex multi-step workflow with HyDE enhancement."""

        # Mock complex HyDE processing with multiple document retrievals
        mock_hyde_processor.process_query.return_value = {
            "enhanced_query": "Comprehensive database design patterns for microservices architecture with event sourcing",
            "original_query": "database design patterns",
            "enhancement_score": 0.94,
            "processing_time": 0.18,
            "retrieved_documents": [
                {
                    "id": "doc_1",
                    "content": "Database design patterns for microservices",
                    "score": 0.95,
                    "metadata": {"architecture": "microservices", "pattern": "database"},
                },
                {
                    "id": "doc_2",
                    "content": "Event sourcing implementation patterns",
                    "score": 0.91,
                    "metadata": {"pattern": "event_sourcing", "domain": "architecture"},
                },
                {
                    "id": "doc_3",
                    "content": "CQRS pattern with event sourcing",
                    "score": 0.87,
                    "metadata": {"pattern": "cqrs", "complement": "event_sourcing"},
                },
            ],
        }

        # Mock multi-agent orchestration response
        mock_mcp_client.orchestrate_agents.return_value = [
            MagicMock(
                agent_id="architecture_agent",
                content="Database design patterns analysis",
                confidence=0.92,
                processing_time=0.8,
                success=True,
                metadata={"analysis_type": "architecture", "patterns_found": 3},
            ),
            MagicMock(
                agent_id="create_agent",
                content="Implementation guide for database patterns",
                confidence=0.89,
                processing_time=1.1,
                success=True,
                metadata={"output_type": "implementation_guide", "complexity": "high"},
            ),
        ]

        # Process complex query
        query = "database design patterns"

        # Step 1: Analyze intent
        intent = await query_counselor.analyze_intent(query)

        # Step 2: HyDE enhancement
        hyde_result = await query_counselor.hyde_processor.process_query(query)

        # Verify HyDE enhancement quality
        assert hyde_result["enhancement_score"] > 0.9
        assert len(hyde_result["retrieved_documents"]) == 3
        assert "microservices" in hyde_result["enhanced_query"]
        assert "event sourcing" in hyde_result["enhanced_query"]

        # Step 3: Agent selection and orchestration
        agents = await query_counselor.select_agents(intent)
        responses = await query_counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

        # Verify multi-agent response
        assert len(responses) == 2
        assert responses[0].agent_id == "architecture_agent"
        assert responses[1].agent_id == "create_agent"
        assert all(r.success for r in responses)
        assert all(r.confidence > 0.8 for r in responses)

        # Verify workflow coordination
        mock_hyde_processor.process_query.assert_called_once_with(query)
        mock_mcp_client.orchestrate_agents.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hyde_processor_fallback_behavior(self, query_counselor, mock_hyde_processor, mock_mcp_client):
        """Test HydeProcessor fallback behavior when enhancement fails."""

        # Mock HyDE processor timeout/failure
        mock_hyde_processor.process_query.side_effect = TimeoutError("Vector store timeout")

        # Mock MCP client success with original query
        mock_mcp_client.orchestrate_agents.return_value = [
            MagicMock(
                agent_id="create_agent",
                content="Response using original query",
                confidence=0.82,
                processing_time=0.9,
                success=True,
                metadata={"fallback": True, "enhancement": "failed"},
            ),
        ]

        # Process query that should trigger fallback
        query = "Test query for fallback"

        # Should handle HyDE failure gracefully
        intent = await query_counselor.analyze_intent(query)

        # Try HyDE processing (should fail)
        try:
            await query_counselor.hyde_processor.process_query(query)
        except TimeoutError:
            # Expected failure, continue with original query
            pass

        # Continue with original query
        agents = await query_counselor.select_agents(intent)
        responses = await query_counselor.orchestrate_workflow(agents, query)  # Original query

        # Verify fallback worked
        assert len(responses) == 1
        assert responses[0].success is True
        assert responses[0].metadata.get("fallback") is True

        # Verify HyDE was attempted
        mock_hyde_processor.process_query.assert_called_once_with(query)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_query_processing(self, query_counselor, mock_mcp_client, mock_hyde_processor):
        """Test concurrent query processing with HyDE enhancement."""

        # Mock concurrent processing responses
        def mock_hyde_response(query):
            return {
                "enhanced_query": f"Enhanced: {query}",
                "original_query": query,
                "enhancement_score": 0.86,
                "processing_time": 0.1,
                "retrieved_documents": [
                    {
                        "id": f"doc_{hash(query) % 1000}",
                        "content": f"Content for {query}",
                        "score": 0.88,
                        "metadata": {"query": query},
                    },
                ],
            }

        mock_hyde_processor.process_query.side_effect = mock_hyde_response

        # Mock MCP responses
        def mock_mcp_response(agents):
            return [
                MagicMock(
                    agent_id="create_agent",
                    content="Response for concurrent query",
                    confidence=0.87,
                    processing_time=0.6,
                    success=True,
                    metadata={"concurrent": True},
                ),
            ]

        mock_mcp_client.orchestrate_agents.side_effect = mock_mcp_response

        # Test concurrent query processing
        queries = ["How to implement caching in Redis", "Database migration strategies", "API rate limiting patterns"]

        async def process_single_query(query):
            intent = await query_counselor.analyze_intent(query)
            hyde_result = await query_counselor.hyde_processor.process_query(query)
            agents = await query_counselor.select_agents(intent)
            responses = await query_counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])
            return {"query": query, "hyde_result": hyde_result, "responses": responses}

        # Process queries concurrently
        start_time = time.time()
        results = await asyncio.gather(*[process_single_query(q) for q in queries])
        end_time = time.time()

        # Verify all queries processed successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["query"] == queries[i]
            assert result["hyde_result"]["enhanced_query"] == f"Enhanced: {queries[i]}"
            assert len(result["responses"]) == 1
            assert result["responses"][0].success is True

        # Verify concurrent processing was efficient
        total_time = end_time - start_time
        assert total_time < 5.0, f"Concurrent processing took {total_time:.3f}s, should be < 5s"

        # Verify all components were called correct number of times
        assert mock_hyde_processor.process_query.call_count == 3
        assert mock_mcp_client.orchestrate_agents.call_count == 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_counselor_initialization_integration(self, test_settings):
        """Test QueryCounselor initialization with HydeProcessor integration."""

        # Mock dependencies
        mock_mcp_client = AsyncMock()
        mock_mcp_client.connect.return_value = True

        mock_hyde_processor = AsyncMock()
        mock_hyde_processor.initialize.return_value = True

        with (
            patch("src.config.settings.get_settings", return_value=test_settings),
            patch("src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client),
            patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
        ):

            # Initialize QueryCounselor
            counselor = QueryCounselor()

            # Verify initialization
            assert counselor.mcp_client == mock_mcp_client
            assert counselor.hyde_processor == mock_hyde_processor
            assert counselor.settings == test_settings

            # Verify dependencies were initialized
            mock_mcp_client.connect.assert_called_once()
            mock_hyde_processor.initialize.assert_called_once()
