#!/usr/bin/env python3
"""
Integration Test for HydeProcessor and VectorStore Components

This test verifies that the HyDE processor and vector store integration is working
correctly by testing imports, basic functionality, and interface compatibility.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_imports():
    """Test that all required modules can be imported successfully."""
    print("Testing imports...")

    try:
        # Core imports
        from core.hyde_processor import (
            EnhancedQuery,
            HydeProcessor,
            HypotheticalDocument,
            QueryAnalysis,
            RankedResults,
            SearchResult,
            SpecificityLevel,
        )

        print("✓ HydeProcessor imports successful")

        from core.vector_store import (
            AbstractVectorStore,
            ConnectionStatus,
            EnhancedMockVectorStore,
            QdrantVectorStore,
            SearchParameters,
            SearchStrategy,
            VectorDocument,
            VectorStoreFactory,
            VectorStoreType,
        )

        print("✓ VectorStore imports successful")

        from config.settings import get_settings

        print("✓ Settings import successful")

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


async def test_vector_store_factory():
    """Test VectorStoreFactory functionality."""
    print("\nTesting VectorStoreFactory...")

    try:
        from core.vector_store import VectorStoreFactory, VectorStoreType

        # Test mock vector store creation
        mock_config = {
            "type": VectorStoreType.MOCK,
            "simulate_latency": True,
            "error_rate": 0.0,
        }

        mock_store = VectorStoreFactory.create_vector_store(mock_config)
        print(f"✓ Created mock vector store: {type(mock_store).__name__}")

        # Test auto-detection (should fall back to mock)
        auto_config = {
            "type": VectorStoreType.AUTO,
        }

        auto_store = VectorStoreFactory.create_vector_store(auto_config)
        print(f"✓ Auto-detected vector store: {type(auto_store).__name__}")

        return True

    except Exception as e:
        print(f"✗ VectorStoreFactory test failed: {e}")
        return False


async def test_search_parameters():
    """Test SearchParameters creation and usage."""
    print("\nTesting SearchParameters...")

    try:
        from core.vector_store import SearchParameters, SearchStrategy

        # Create mock embeddings
        test_embeddings = [[0.1, 0.2, 0.3] * 100]  # 300-dimensional mock embedding

        search_params = SearchParameters(
            embeddings=test_embeddings,
            limit=10,
            collection="test_collection",
            strategy=SearchStrategy.SEMANTIC,
            score_threshold=0.5,
        )

        print(f"✓ Created SearchParameters with {len(search_params.embeddings)} embeddings")
        print(f"  - Limit: {search_params.limit}")
        print(f"  - Collection: {search_params.collection}")
        print(f"  - Strategy: {search_params.strategy}")
        print(f"  - Threshold: {search_params.score_threshold}")

        return True

    except Exception as e:
        print(f"✗ SearchParameters test failed: {e}")
        return False


async def test_hyde_processor_initialization():
    """Test HydeProcessor initialization with different configurations."""
    print("\nTesting HydeProcessor initialization...")

    try:
        from core.hyde_processor import HydeProcessor
        from core.vector_store import EnhancedMockVectorStore

        # Test with explicit mock vector store
        mock_store = EnhancedMockVectorStore(
            {
                "simulate_latency": False,
                "error_rate": 0.0,
            },
        )

        processor = HydeProcessor(vector_store=mock_store)
        print("✓ Created HydeProcessor with explicit mock vector store")

        # Test with auto-initialization (should create its own vector store)
        auto_processor = HydeProcessor()
        print(
            f"✓ Created HydeProcessor with auto-initialized vector store: {type(auto_processor.vector_store).__name__}",
        )

        return True

    except Exception as e:
        print(f"✗ HydeProcessor initialization test failed: {e}")
        return False


async def test_mock_vector_store_operations():
    """Test basic vector store operations with mock implementation."""
    print("\nTesting mock vector store operations...")

    try:
        from core.vector_store import EnhancedMockVectorStore, SearchParameters, SearchStrategy

        # Create mock vector store
        store = EnhancedMockVectorStore(
            {
                "simulate_latency": False,
                "error_rate": 0.0,
            },
        )

        # Test connection
        await store.connect()
        print("✓ Connected to mock vector store")

        # Test health check
        health = await store.health_check()
        print(f"✓ Health check: {health.status}")

        # Test search operation
        search_params = SearchParameters(
            embeddings=[[0.1] * 300],  # Mock 300-dimensional embedding
            limit=5,
            collection="test",
            strategy=SearchStrategy.SEMANTIC,
            score_threshold=0.3,
        )

        results = await store.search(search_params)
        print(f"✓ Search completed: {len(results)} results")

        # Test disconnect
        await store.disconnect()
        print("✓ Disconnected from mock vector store")

        return True

    except Exception as e:
        print(f"✗ Mock vector store operations test failed: {e}")
        return False


async def test_hyde_processor_query_processing():
    """Test HydeProcessor query processing pipeline."""
    print("\nTesting HydeProcessor query processing...")

    try:
        from core.hyde_processor import HydeProcessor

        # Create processor with default configuration
        processor = HydeProcessor()

        # Test three-tier analysis
        test_query = "How do I implement authentication in a Python web application?"

        enhanced_query = await processor.three_tier_analysis(test_query)
        print("✓ Three-tier analysis completed")
        print(f"  - Original query: {enhanced_query.original_query}")
        print(f"  - Processing strategy: {enhanced_query.processing_strategy}")
        print(f"  - Specificity level: {enhanced_query.specificity_analysis.specificity_level}")

        # Test hypothetical document generation
        hypo_docs = await processor.generate_hypothetical_docs(test_query)
        print(f"✓ Generated {len(hypo_docs)} hypothetical documents")

        # Test complete query processing
        results = await processor.process_query(test_query)
        print("✓ Query processing completed")
        print(f"  - Total found: {results.total_found}")
        print(f"  - Results returned: {len(results.results)}")
        print(f"  - HyDE enhanced: {results.hyde_enhanced}")
        print(f"  - Processing time: {results.processing_time:.3f}s")

        return True

    except Exception as e:
        print(f"✗ HydeProcessor query processing test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and edge cases."""
    print("\nTesting error handling...")

    try:
        from core.hyde_processor import HydeProcessor

        processor = HydeProcessor()

        # Test empty query
        try:
            await processor.three_tier_analysis("")
            print("✗ Empty query should have raised ValueError")
            return False
        except ValueError:
            print("✓ Empty query properly rejected")

        # Test whitespace-only query
        try:
            await processor.three_tier_analysis("   ")
            print("✗ Whitespace query should have raised ValueError")
            return False
        except ValueError:
            print("✓ Whitespace query properly rejected")

        # Test valid query (should not raise)
        await processor.three_tier_analysis("test query")
        print("✓ Valid query processed without error")

        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("=== HydeProcessor and VectorStore Integration Test ===\n")

    tests = [
        test_imports,
        test_vector_store_factory,
        test_search_parameters,
        test_hyde_processor_initialization,
        test_mock_vector_store_operations,
        test_hyde_processor_query_processing,
        test_error_handling,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")

    print("\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")

    if passed == total:
        print("🎉 All tests passed! HyDE and VectorStore integration is working correctly.")
        return True
    print("❌ Some tests failed. Check the output above for details.")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
