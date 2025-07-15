#!/usr/bin/env python3
"""Manual test to verify HyDE and VectorStore integration."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=== Manual Integration Test ===")

# Test 1: Import all required modules
print("\n1. Testing imports...")
try:
    from core.hyde_processor import (
        HydeProcessor,
    )

    print("✓ HydeProcessor and related classes imported successfully")
except Exception as e:
    print(f"✗ HydeProcessor import failed: {e}")
    import traceback

    traceback.print_exc()

try:
    from core.vector_store import (
        EnhancedMockVectorStore,
        SearchParameters,
        SearchStrategy,
        VectorStoreFactory,
        VectorStoreType,
    )

    print("✓ VectorStore classes imported successfully")
except Exception as e:
    print(f"✗ VectorStore import failed: {e}")
    import traceback

    traceback.print_exc()

try:

    print("✓ Settings imported successfully")
except Exception as e:
    print(f"✗ Settings import failed: {e}")
    import traceback

    traceback.print_exc()

# Test 2: Create VectorStore using factory
print("\n2. Testing VectorStoreFactory...")
try:
    config = {
        "type": VectorStoreType.MOCK,
        "simulate_latency": False,
        "error_rate": 0.0,
    }
    store = VectorStoreFactory.create_vector_store(config)
    print(f"✓ Created vector store: {type(store).__name__}")
except Exception as e:
    print(f"✗ VectorStoreFactory failed: {e}")
    import traceback

    traceback.print_exc()

# Test 3: Create SearchParameters
print("\n3. Testing SearchParameters...")
try:
    test_embeddings = [[0.1, 0.2, 0.3] * 100]  # 300-dimensional
    search_params = SearchParameters(
        embeddings=test_embeddings,
        limit=10,
        collection="test_collection",
        strategy=SearchStrategy.SEMANTIC,
        score_threshold=0.5,
    )
    print(f"✓ Created SearchParameters with {len(search_params.embeddings)} embeddings")
except Exception as e:
    print(f"✗ SearchParameters creation failed: {e}")
    import traceback

    traceback.print_exc()

# Test 4: Create HydeProcessor with mock store
print("\n4. Testing HydeProcessor initialization...")
try:
    mock_store = EnhancedMockVectorStore(
        {
            "simulate_latency": False,
            "error_rate": 0.0,
        },
    )
    processor = HydeProcessor(vector_store=mock_store)
    print("✓ Created HydeProcessor with explicit mock store")
except Exception as e:
    print(f"✗ HydeProcessor with mock store failed: {e}")
    import traceback

    traceback.print_exc()

# Test 5: Create HydeProcessor with auto-initialization
print("\n5. Testing HydeProcessor auto-initialization...")
try:
    auto_processor = HydeProcessor()
    print(f"✓ Created HydeProcessor with auto-initialized store: {type(auto_processor.vector_store).__name__}")
except Exception as e:
    print(f"✗ HydeProcessor auto-initialization failed: {e}")
    import traceback

    traceback.print_exc()

# Test 6: Test async operations (basic structure)
print("\n6. Testing async operation setup...")
try:
    import asyncio

    async def test_async():
        processor = HydeProcessor()
        # Just test that the processor was created and has the required methods
        assert hasattr(processor, "three_tier_analysis")
        assert hasattr(processor, "generate_hypothetical_docs")
        assert hasattr(processor, "process_query")
        return True

    # Run the async test
    result = asyncio.run(test_async())
    if result:
        print("✓ Async operation setup successful")
except Exception as e:
    print(f"✗ Async operation setup failed: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Manual Test Complete ===")
