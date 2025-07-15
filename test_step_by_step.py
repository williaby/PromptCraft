#!/usr/bin/env python3
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=== Step-by-Step Integration Test ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {__file__}")

# Step 1: Test basic imports
print("\n1. Testing imports...")
try:
    from core.hyde_processor import HydeProcessor

    print("✓ HydeProcessor imported")
except Exception as e:
    print(f"✗ HydeProcessor import failed: {e}")

try:
    from core.vector_store import VectorStoreFactory, VectorStoreType

    print("✓ VectorStore imports successful")
except Exception as e:
    print(f"✗ VectorStore import failed: {e}")

try:

    print("✓ Settings imported")
except Exception as e:
    print(f"✗ Settings import failed: {e}")

# Step 2: Test factory
print("\n2. Testing VectorStoreFactory...")
try:
    config = {"type": VectorStoreType.MOCK, "simulate_latency": False}
    store = VectorStoreFactory.create_vector_store(config)
    print(f"✓ Created store: {type(store).__name__}")
except Exception as e:
    print(f"✗ Factory failed: {e}")

# Step 3: Test processor
print("\n3. Testing HydeProcessor...")
try:
    processor = HydeProcessor()
    print(f"✓ Created processor with: {type(processor.vector_store).__name__}")
except Exception as e:
    print(f"✗ Processor failed: {e}")

print("\n=== Test Complete ===")
