#!/usr/bin/env python3
"""
OpenRouter Client Demo Script

This script demonstrates the basic usage of the OpenRouterClient implementation
for Phase 1 Issue NEW-11 (AI Tool Routing Implementation). It shows how to:

1. Initialize the OpenRouter client
2. Connect to the OpenRouter API
3. Validate user queries for security
4. Orchestrate agent workflows
5. Handle errors and disconnection

Usage:
    python examples/openrouter_client_demo.py

Requirements:
    - OpenRouter API key configured in environment (PROMPTCRAFT_OPENROUTER_API_KEY)
    - All dependencies installed via Poetry
"""

import asyncio
import logging
import os

from src.mcp_integration.mcp_client import MCPError, WorkflowStep
from src.mcp_integration.openrouter_client import OpenRouterClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def demo_basic_functionality():
    """Demonstrate basic OpenRouter client functionality."""
    logger.info("=== OpenRouter Client Demo ===")

    # Initialize client
    logger.info("1. Initializing OpenRouter client...")
    client = OpenRouterClient()

    try:
        # Connect to OpenRouter API
        logger.info("2. Connecting to OpenRouter API...")
        connected = await client.connect()

        if not connected:
            logger.warning("Failed to connect to OpenRouter API - continuing with demo")
            return

        logger.info("✓ Successfully connected to OpenRouter API")

        # Validate a query
        logger.info("3. Validating user query...")
        test_query = "What are the key principles of secure software development?"
        validation_result = await client.validate_query(test_query)

        logger.info(f"Query validation result: {validation_result}")

        if not validation_result["is_valid"]:
            logger.warning(f"Query validation failed: {validation_result['potential_issues']}")
            return

        # Check capabilities
        logger.info("4. Getting OpenRouter capabilities...")
        try:
            capabilities = await client.get_capabilities()
            logger.info(f"Available capabilities: {capabilities}")
        except MCPError as e:
            logger.warning(f"Could not retrieve capabilities: {e}")

        # Create a test workflow step
        logger.info("5. Creating test workflow step...")
        workflow_step = WorkflowStep(
            step_id="demo-step-1",
            agent_id="security-expert",
            input_data={
                "query": test_query,
                "task_type": "general",
                "max_tokens": 150,
                "temperature": 0.7,
            },
            timeout_seconds=30,
        )

        # Execute workflow (this will fail without a real API key)
        logger.info("6. Executing workflow step...")
        try:
            responses = await client.orchestrate_agents([workflow_step])

            if responses:
                response = responses[0]
                logger.info("✓ Workflow completed successfully")
                logger.info(f"Agent: {response.agent_id}")
                logger.info(f"Content: {response.content[:100]}...")
                logger.info(f"Confidence: {response.confidence}")
                logger.info(f"Processing time: {response.processing_time:.3f}s")
            else:
                logger.warning("No responses received from workflow")

        except MCPError as e:
            logger.warning(f"Workflow execution failed (expected without real API key): {e}")

        # Health check
        logger.info("7. Performing health check...")
        health_status = await client.health_check()
        logger.info(f"Health status: {health_status.status}")
        logger.info(f"Response time: {health_status.response_time:.3f}s")
        logger.info(f"Error count: {health_status.error_count}")

    except Exception as e:
        logger.error(f"Demo error: {e}")

    finally:
        # Disconnect
        logger.info("8. Disconnecting from OpenRouter API...")
        await client.disconnect()
        logger.info("✓ Disconnected successfully")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    logger.info("\n=== Error Handling Demo ===")

    # Test with invalid configuration
    client = OpenRouterClient(api_key="invalid-key", base_url="https://invalid-url.com/api/v1")

    try:
        logger.info("Testing connection with invalid configuration...")
        await client.connect()
    except MCPError as e:
        logger.info(f"✓ Correctly caught connection error: {type(e).__name__}")

    # Test query validation with suspicious content
    logger.info("Testing query validation with suspicious content...")
    suspicious_query = '<script>alert("xss")</script>What is 2+2?'

    try:
        validation = await client.validate_query(suspicious_query)
        if not validation["is_valid"]:
            logger.info(f"✓ Correctly identified security issues: {validation['potential_issues']}")
        else:
            logger.warning("Failed to detect security issues in suspicious query")
    except Exception as e:
        logger.error(f"Query validation error: {e}")


async def demo_model_integration():
    """Demonstrate ModelRegistry integration."""
    logger.info("\n=== Model Registry Integration Demo ===")

    client = OpenRouterClient()

    # Test different task types for model selection
    task_types = ["general", "reasoning", "vision", "analysis"]

    for task_type in task_types:
        logger.info(f"Testing model selection for task type: {task_type}")

        workflow_step = WorkflowStep(
            step_id=f"demo-{task_type}",
            agent_id=f"{task_type}-agent",
            input_data={
                "query": f"This is a {task_type} task",
                "task_type": task_type,
                "allow_premium": False,
                "max_tokens_needed": 4096,
            },
            timeout_seconds=30,
        )

        try:
            # This will trigger model selection through ModelRegistry
            await client._execute_single_step(workflow_step)
        except Exception as e:
            logger.info(f"Model selection for {task_type}: {type(e).__name__} (expected without real API)")


def check_environment():
    """Check environment configuration."""
    logger.info("\n=== Environment Check ===")

    api_key = os.getenv("PROMPTCRAFT_OPENROUTER_API_KEY")
    if api_key:
        logger.info("✓ OpenRouter API key is configured")
    else:
        logger.warning("OpenRouter API key not found in environment")
        logger.info("Set PROMPTCRAFT_OPENROUTER_API_KEY to test with real API")

    base_url = os.getenv("PROMPTCRAFT_OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    logger.info(f"OpenRouter base URL: {base_url}")


async def main():
    """Run all demo scenarios."""
    print("OpenRouter Client Demo - Phase 1 Issue NEW-11")
    print("=" * 50)

    # Check environment
    check_environment()

    # Run demos
    await demo_basic_functionality()
    await demo_error_handling()
    await demo_model_integration()

    print("\n" + "=" * 50)
    print("Demo completed! Check the logs above for results.")
    print("\nKey Implementation Features Demonstrated:")
    print("✓ MCPClientInterface compliance")
    print("✓ OpenRouter API integration")
    print("✓ Authentication and error handling")
    print("✓ Query validation and security")
    print("✓ ModelRegistry integration")
    print("✓ Comprehensive logging and monitoring")


if __name__ == "__main__":
    asyncio.run(main())
