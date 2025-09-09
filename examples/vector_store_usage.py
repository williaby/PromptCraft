"""
Vector Store Usage Examples for PromptCraft-Hybrid.

This module demonstrates how to use the vector store interfaces with both
mock and real Qdrant implementations. It shows practical patterns for
integration with HydeProcessor and other PromptCraft components.
"""

import asyncio
import contextlib
import logging
import time

from src.core.hyde_processor import HydeProcessor
from src.core.vector_store import (
    DEFAULT_VECTOR_DIMENSIONS,
    SearchParameters,
    SearchStrategy,
    VectorDocument,
    VectorStoreFactory,
    VectorStoreType,
    vector_store_connection,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreExamples:
    """Comprehensive examples of vector store usage patterns."""

    @staticmethod
    async def basic_mock_store_usage() -> None:
        """Example 1: Basic mock vector store usage."""

        # Configuration for mock store
        config = {
            "type": VectorStoreType.MOCK,
            "simulate_latency": True,
            "error_rate": 0.0,  # No errors for this example
            "base_latency": 0.01,
        }

        # Create and connect to vector store
        store = VectorStoreFactory.create_vector_store(config)
        await store.connect()

        # Check health
        await store.health_check()

        # Insert some documents
        documents = [
            VectorDocument(
                id="python_caching",
                content="Implementing Redis caching in Python applications for improved performance",
                embedding=[0.8, 0.2, 0.9] + [0.1] * (DEFAULT_VECTOR_DIMENSIONS - 3),
                metadata={"language": "python", "topic": "caching", "difficulty": "intermediate"},
                collection="programming",
            ),
            VectorDocument(
                id="async_programming",
                content="Asynchronous programming patterns in Python using asyncio and coroutines",
                embedding=[0.7, 0.8, 0.3] + [0.2] * (DEFAULT_VECTOR_DIMENSIONS - 3),
                metadata={"language": "python", "topic": "async", "difficulty": "advanced"},
                collection="programming",
            ),
            VectorDocument(
                id="api_design",
                content="RESTful API design principles and best practices for scalable web services",
                embedding=[0.6, 0.9, 0.2] + [0.3] * (DEFAULT_VECTOR_DIMENSIONS - 3),
                metadata={"topic": "api", "type": "design", "difficulty": "intermediate"},
                collection="programming",
            ),
        ]

        # Batch insert
        await store.insert_documents(documents)

        # Search for similar documents
        query_embedding = [0.75, 0.5, 0.6] + [0.2] * (DEFAULT_VECTOR_DIMENSIONS - 3)
        search_params = SearchParameters(
            embeddings=[query_embedding],
            limit=3,
            collection="programming",
            strategy=SearchStrategy.SEMANTIC,
        )

        search_results = await store.search(search_params)
        for _i, _result in enumerate(search_results):
            pass

        # Get metrics
        store.get_metrics()

        await store.disconnect()

    @staticmethod
    async def advanced_search_strategies() -> None:
        """Example 2: Advanced search strategies and filtering."""

        config = {"type": VectorStoreType.MOCK, "simulate_latency": False}

        async with vector_store_connection(config) as store:
            # Insert documents with rich metadata
            documents = [
                VectorDocument(
                    id="ml_basics",
                    content="Introduction to machine learning algorithms and concepts",
                    embedding=[0.9, 0.1, 0.8] + [0.1] * (DEFAULT_VECTOR_DIMENSIONS - 3),
                    metadata={
                        "category": "machine_learning",
                        "difficulty": "beginner",
                        "tags": ["tutorial", "basics", "algorithms"],
                        "author": "John Doe",
                        "year": 2023,
                    },
                    collection="ml_docs",
                ),
                VectorDocument(
                    id="deep_learning",
                    content="Advanced deep learning techniques using neural networks",
                    embedding=[0.95, 0.05, 0.9] + [0.05] * (DEFAULT_VECTOR_DIMENSIONS - 3),
                    metadata={
                        "category": "machine_learning",
                        "difficulty": "advanced",
                        "tags": ["neural_networks", "deep_learning", "advanced"],
                        "author": "Jane Smith",
                        "year": 2023,
                    },
                    collection="ml_docs",
                ),
                VectorDocument(
                    id="data_preprocessing",
                    content="Data preprocessing and feature engineering for ML pipelines",
                    embedding=[0.7, 0.3, 0.8] + [0.2] * (DEFAULT_VECTOR_DIMENSIONS - 3),
                    metadata={
                        "category": "data_science",
                        "difficulty": "intermediate",
                        "tags": ["preprocessing", "features", "pipeline"],
                        "author": "Bob Johnson",
                        "year": 2022,
                    },
                    collection="ml_docs",
                ),
            ]

            await store.insert_documents(documents)

            # Test different search strategies
            query_embedding = [0.85, 0.15, 0.85] + [0.1] * (DEFAULT_VECTOR_DIMENSIONS - 3)

            strategies = [
                (SearchStrategy.EXACT, "Exact similarity matching"),
                (SearchStrategy.SEMANTIC, "Semantic similarity search"),
                (SearchStrategy.HYBRID, "Hybrid search with embeddings"),
                (SearchStrategy.FILTERED, "Filtered search"),
            ]

            for strategy, _description in strategies:

                search_params = SearchParameters(
                    embeddings=[query_embedding],
                    collection="ml_docs",
                    strategy=strategy,
                    limit=3,
                )

                results = await store.search(search_params)
                for result in results:
                    if strategy == SearchStrategy.HYBRID and result.embedding:
                        pass

            # Test filtered search

            filter_examples = [
                ({"difficulty": "beginner"}, "Beginner level documents"),
                ({"category": "machine_learning"}, "Machine learning category"),
                ({"year": 2023}, "Documents from 2023"),
                ({"tags": ["advanced"]}, "Documents tagged as advanced"),
            ]

            for filters, _description in filter_examples:
                search_params = SearchParameters(
                    embeddings=[query_embedding],
                    collection="ml_docs",
                    filters=filters,
                    strategy=SearchStrategy.FILTERED,
                )

                results = await store.search(search_params)

    @staticmethod
    async def hyde_processor_integration() -> None:
        """Example 3: Integration with HydeProcessor."""

        # Create enhanced vector store for storage
        enhanced_config = {"type": VectorStoreType.MOCK, "simulate_latency": False}
        enhanced_store = VectorStoreFactory.create_vector_store(enhanced_config)
        await enhanced_store.connect()

        # Create HydeProcessor with compatible mock store
        hyde_processor = HydeProcessor()

        # Test queries with different specificity levels
        test_queries = [
            "Python caching",  # Low specificity - should ask for clarification
            "How to implement Redis caching in Python web applications",  # Medium specificity - HyDE
            "Implement Redis connection pooling with retry logic in Django REST API using redis-py library",  # High specificity - direct
        ]

        for query in test_queries:

            # Analyze query specificity
            enhanced_query = await hyde_processor.three_tier_analysis(query)

            if enhanced_query.processing_strategy == "standard_hyde":

                # Store hypothetical documents in enhanced vector store
                vector_docs = []
                for i, hyde_doc in enumerate(enhanced_query.hypothetical_docs):
                    vector_doc = VectorDocument(
                        id=f"hyde_{hash(query)}_{i}",
                        content=hyde_doc.content,
                        embedding=hyde_doc.embedding,
                        metadata={
                            "source": "hyde_generated",
                            "original_query": query,
                            "relevance_score": hyde_doc.relevance_score,
                            "generation_method": hyde_doc.generation_method,
                            **hyde_doc.metadata,
                        },
                        collection="hyde_docs",
                    )
                    vector_docs.append(vector_doc)

                # Insert hypothetical documents
                if vector_docs:
                    await enhanced_store.insert_documents(vector_docs)

                    # Search using enhanced embeddings
                    embeddings = await hyde_processor.enhance_embeddings(query, enhanced_query.hypothetical_docs)
                    search_params = SearchParameters(
                        embeddings=embeddings,
                        collection="hyde_docs",
                        strategy=SearchStrategy.HYBRID,
                    )

                    await enhanced_store.search(search_params)

            elif enhanced_query.processing_strategy == "clarification_needed":
                for _question in enhanced_query.specificity_analysis.guiding_questions:
                    pass

        await enhanced_store.disconnect()

    @staticmethod
    async def performance_monitoring() -> None:
        """Example 4: Performance monitoring and optimization."""

        config = {"type": VectorStoreType.MOCK, "simulate_latency": True, "base_latency": 0.02}

        store = VectorStoreFactory.create_vector_store(config)
        await store.connect()

        # Generate test data
        documents = []
        for i in range(100):
            doc = VectorDocument(
                id=f"perf_doc_{i}",
                content=f"Performance test document {i} about topic {i % 10}",
                embedding=[0.1 * (i % 10)] * DEFAULT_VECTOR_DIMENSIONS,
                metadata={"index": i, "topic": i % 10},
                collection="performance_test",
            )
            documents.append(doc)

        # Batch insert with timing
        start_time = time.time()
        await store.insert_documents(documents)
        time.time() - start_time

        # Multiple searches with timing
        search_times = []
        for i in range(20):
            query_embedding = [0.1 * (i % 5)] * DEFAULT_VECTOR_DIMENSIONS
            search_params = SearchParameters(embeddings=[query_embedding], collection="performance_test", limit=5)

            start_time = time.time()
            await store.search(search_params)
            search_time = time.time() - start_time
            search_times.append(search_time)

        # Calculate search statistics
        sum(search_times) / len(search_times)
        max(search_times)
        min(search_times)

        # Get comprehensive metrics
        store.get_metrics()

        await store.disconnect()

    @staticmethod
    async def error_handling_and_resilience() -> None:
        """Example 5: Error handling and resilience patterns."""

        # Configure store with some error simulation
        config = {"type": VectorStoreType.MOCK, "simulate_latency": False, "error_rate": 0.3}  # 30% error rate

        store = VectorStoreFactory.create_vector_store(config)
        await store.connect()

        # Test resilient search pattern

        query_embedding = [0.5] * DEFAULT_VECTOR_DIMENSIONS
        search_params = SearchParameters(embeddings=[query_embedding])

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await store.search(search_params)
                break
            except Exception:
                if attempt == max_retries - 1:
                    pass
                else:
                    await asyncio.sleep(0.1 * (2**attempt))  # Exponential backoff

        # Test circuit breaker behavior

        error_store = VectorStoreFactory.create_vector_store(
            {"type": VectorStoreType.MOCK, "error_rate": 1.0},  # Always error
        )
        await error_store.connect()

        # Trigger circuit breaker
        for _i in range(8):
            with contextlib.suppress(Exception):
                await error_store.search(search_params)

        # Circuit breaker should now prevent operations
        await error_store.search(search_params)

        await store.disconnect()
        await error_store.disconnect()

    @staticmethod
    async def qdrant_configuration_example() -> None:
        """Example 6: Qdrant configuration (demonstrates interface, won't connect)."""

        # Production Qdrant configuration for PromptCraft
        qdrant_config = {
            "type": VectorStoreType.QDRANT,
            "host": "192.168.1.16",  # External Qdrant on Unraid
            "port": 6333,
            "api_key": None,  # Set from environment in production
            "timeout": 30.0,
        }

        # Create Qdrant store (won't actually connect without qdrant-client)
        with contextlib.suppress(Exception):
            VectorStoreFactory.create_vector_store(qdrant_config)

            # Example of what production usage would look like

    @staticmethod
    async def collection_management() -> None:
        """Example 7: Collection management operations."""

        config = {"type": VectorStoreType.MOCK, "simulate_latency": False}

        async with vector_store_connection(config) as store:
            # List initial collections
            await store.list_collections()

            # Create new collections
            new_collections = [("user_knowledge", 512), ("code_examples", 768), ("documentation", 384)]

            for name, vector_size in new_collections:
                success = await store.create_collection(name, vector_size)

                if success:
                    await store.get_collection_info(name)

            # List all collections
            all_collections = await store.list_collections()

            # Insert documents into different collections
            documents_by_collection = {
                "user_knowledge": [
                    VectorDocument(
                        id="user_pref_1",
                        content="User prefers Python over JavaScript for backend development",
                        embedding=[0.1] * 512,
                        metadata={"type": "preference", "user": "john_doe"},
                        collection="user_knowledge",
                    ),
                ],
                "code_examples": [
                    VectorDocument(
                        id="python_async_example",
                        content="async def fetch_data(): return await api_call()",
                        embedding=[0.2] * 768,
                        metadata={"language": "python", "pattern": "async"},
                        collection="code_examples",
                    ),
                ],
                "documentation": [
                    VectorDocument(
                        id="api_docs_1",
                        content="The authenticate endpoint requires a valid JWT token",
                        embedding=[0.3] * 384,
                        metadata={"type": "api_doc", "endpoint": "authenticate"},
                        collection="documentation",
                    ),
                ],
            }

            for collection_name, docs in documents_by_collection.items():
                if collection_name in all_collections:
                    await store.insert_documents(docs)

            # Search across different collections
            query_embedding_512 = [0.15] * 512
            query_embedding_768 = [0.25] * 768
            query_embedding_384 = [0.35] * 384

            collection_searches = [
                ("user_knowledge", [query_embedding_512]),
                ("code_examples", [query_embedding_768]),
                ("documentation", [query_embedding_384]),
            ]

            for collection_name, embeddings in collection_searches:
                if collection_name in all_collections:
                    search_params = SearchParameters(embeddings=embeddings, collection=collection_name, limit=5)

                    await store.search(search_params)


async def main() -> None:
    """Run all vector store examples."""

    examples = VectorStoreExamples()

    # Run all examples
    example_methods = [
        examples.basic_mock_store_usage,
        examples.advanced_search_strategies,
        examples.hyde_processor_integration,
        examples.performance_monitoring,
        examples.error_handling_and_resilience,
        examples.qdrant_configuration_example,
        examples.collection_management,
    ]

    for example_method in example_methods:
        try:
            await example_method()
        except Exception:
            logger.exception("Example failed")


if __name__ == "__main__":
    asyncio.run(main())
