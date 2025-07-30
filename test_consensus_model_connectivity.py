#!/usr/bin/env python3
"""
Consensus Model Connectivity Test Script

Tests connectivity to all consensus models mentioned in the test coverage documentation
through the MCP integration system. This validates that multi-model consensus workflow
will work as designed.

Standard Consensus Models:
1. O3
2. Gemini 2.5 Pro
3. Kimi K2 Free
4. Qwen3-Coder Free

Escalation Models:
5. Opus 4
6. O3-Pro

Usage:
    python test_consensus_model_connectivity.py
    python test_consensus_model_connectivity.py --verbose
    python test_consensus_model_connectivity.py --model=O3
"""

import argparse
import asyncio
import json
import logging
import sys
import traceback
from dataclasses import dataclass
from typing import Any

from src.mcp_integration.client import MCPClient, MCPClientError
from src.mcp_integration.model_registry import get_model_registry

# Constants for consensus workflow requirements
MIN_CONSENSUS_MODELS = 2  # Minimum models required for consensus decisions


@dataclass
class ConsensusModel:
    """Configuration for a consensus model."""

    name: str
    openrouter_id: str
    category: str
    is_escalation: bool = False
    expected_capabilities: list[str] = None

    def __post_init__(self):
        if self.expected_capabilities is None:
            self.expected_capabilities = []


# Consensus model configurations based on test documentation
CONSENSUS_MODELS = [
    # Standard Consensus Models
    ConsensusModel(
        name="O3",
        openrouter_id="openai/o3",
        category="premium_reasoning",
        expected_capabilities=["reasoning", "function_calling"],
    ),
    ConsensusModel(
        name="Gemini 2.5 Pro",
        openrouter_id="google/gemini-2.5-pro",
        category="premium_analysis",
        expected_capabilities=["vision", "function_calling", "large_context"],
    ),
    ConsensusModel(
        name="Kimi K2 Free",
        openrouter_id="moonshot/moonshot-v1-8k:free",  # Kimi mapping
        category="free_general",
        expected_capabilities=["general"],
    ),
    ConsensusModel(
        name="Qwen3-Coder Free",
        openrouter_id="qwen/qwen3-coder:free",
        category="free_reasoning",
        expected_capabilities=["reasoning"],
    ),
    # Escalation Models
    ConsensusModel(
        name="Opus 4",
        openrouter_id="anthropic/claude-opus-4",
        category="premium_analysis",
        is_escalation=True,
        expected_capabilities=["reasoning", "analysis", "function_calling"],
    ),
    ConsensusModel(
        name="O3-Pro",
        openrouter_id="openai/o3-pro",
        category="premium_reasoning",
        is_escalation=True,
        expected_capabilities=["reasoning", "function_calling", "large_context"],
    ),
]


class ConsensusModelTester:
    """Tests connectivity to consensus models for multi-model workflow validation."""

    def __init__(self, verbose: bool = False):
        """Initialize the tester.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.mcp_client = None
        self.model_registry = get_model_registry()
        self.results: dict[str, dict[str, Any]] = {}

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        return logging.getLogger(__name__)

    async def initialize_mcp_client(self) -> bool:
        """Initialize MCP client connection.

        Returns:
            True if initialization successful
        """
        try:
            self.mcp_client = MCPClient()
            self.logger.info("MCP Client initialized successfully")
            return True
        except Exception as e:
            self.logger.error("Failed to initialize MCP client: %s", e)
            return False

    async def test_model_connectivity(self, model: ConsensusModel) -> dict[str, Any]:
        """Test connectivity to a specific consensus model.

        Args:
            model: ConsensusModel configuration to test

        Returns:
            Dictionary with test results
        """
        result = {
            "model_name": model.name,
            "openrouter_id": model.openrouter_id,
            "category": model.category,
            "is_escalation": model.is_escalation,
            "status": "unknown",
            "connectivity": False,
            "response_received": False,
            "capabilities_verified": False,
            "error_message": None,
            "response_content": None,
            "registry_configured": False,
            "alternative_suggestions": [],
        }

        self.logger.info("Testing connectivity to %s (%s)", model.name, model.openrouter_id)

        try:
            # Check if model is configured in registry
            capabilities = self.model_registry.get_model_capabilities(model.openrouter_id)
            if capabilities:
                result["registry_configured"] = True
                result["status"] = "configured"
                self.logger.debug("Model %s found in registry", model.name)
            else:
                result["status"] = "not_configured"
                self.logger.warning("Model %s not found in registry", model.name)

                # Suggest alternatives
                alternatives = self._find_alternative_models(model)
                result["alternative_suggestions"] = alternatives

            # Test actual connectivity through MCP
            if self.mcp_client:
                connectivity_result = await self._test_mcp_connectivity(model)
                result.update(connectivity_result)
            else:
                result["error_message"] = "MCP client not initialized"

        except Exception as e:
            result["status"] = "error"
            result["error_message"] = str(e)
            self.logger.error("Error testing %s: %s", model.name, e)

        return result

    async def _test_mcp_connectivity(self, model: ConsensusModel) -> dict[str, Any]:
        """Test MCP connectivity for a model.

        Args:
            model: ConsensusModel to test

        Returns:
            Dictionary with connectivity results
        """
        connectivity_result = {
            "connectivity": False,
            "response_received": False,
            "response_content": None,
            "error_message": None,
        }

        try:
            # Attempt to connect to a model server (placeholder logic)
            # In real implementation, this would use the actual MCP protocol
            test_message = {
                "type": "test_message",
                "model": model.openrouter_id,
                "content": "Hello, this is a connectivity test for multi-model consensus validation",
                "test_id": f"consensus_test_{model.name.lower().replace(' ', '_')}",
            }

            # For now, simulate connectivity test
            # In real implementation, this would send to actual MCP server
            server_name = f"{model.name.lower().replace(' ', '_')}_server"

            # Check if we can establish connection
            connected = await self.mcp_client.connect_server(server_name)
            if connected:
                connectivity_result["connectivity"] = True

                # Send test message
                response = await self.mcp_client.send_message(server_name, test_message)
                connectivity_result["response_received"] = True
                connectivity_result["response_content"] = response

                self.logger.info("✅ Successfully connected to %s", model.name)

                # Disconnect after test
                self.mcp_client.disconnect_server(server_name)
            else:
                connectivity_result["error_message"] = f"Failed to connect to {server_name}"
                self.logger.warning("❌ Failed to connect to %s", model.name)

        except MCPClientError as e:
            connectivity_result["error_message"] = f"MCP Error: {e!s}"
            self.logger.error("❌ MCP error for %s: %s", model.name, e)
        except Exception as e:
            connectivity_result["error_message"] = f"Unexpected error: {e!s}"
            self.logger.error("❌ Unexpected error for %s: %s", model.name, e)

        return connectivity_result

    def _find_alternative_models(self, model: ConsensusModel) -> list[str]:
        """Find alternative models in the same category.

        Args:
            model: ConsensusModel to find alternatives for

        Returns:
            List of alternative model IDs
        """
        alternatives = []

        try:
            # Get models in the same category
            available_models = self.model_registry.list_models(category=model.category)

            for available_model in available_models[:3]:  # Limit to top 3
                if available_model.model_id != model.openrouter_id:
                    alternatives.append(available_model.model_id)

            # If no alternatives in category, get fallback chain
            if not alternatives:
                fallback_chain = self.model_registry.get_fallback_chain(model.category)
                alternatives = fallback_chain[:3]

        except Exception as e:
            self.logger.warning("Error finding alternatives for %s: %s", model.name, e)

        return alternatives

    async def run_full_test(self, specific_model: str = None) -> dict[str, Any]:
        """Run connectivity tests for all consensus models.

        Args:
            specific_model: Test only a specific model by name

        Returns:
            Complete test results
        """
        self.logger.info("Starting consensus model connectivity tests")

        # Initialize MCP client
        mcp_initialized = await self.initialize_mcp_client()
        if not mcp_initialized:
            self.logger.error("Failed to initialize MCP client - some tests may not work")

        # Filter models if specific model requested
        models_to_test = CONSENSUS_MODELS
        if specific_model:
            models_to_test = [m for m in CONSENSUS_MODELS if m.name.lower() == specific_model.lower()]
            if not models_to_test:
                self.logger.error("Model '%s' not found in consensus models", specific_model)
                return {"error": f"Model '{specific_model}' not found"}

        # Test each model
        for model in models_to_test:
            result = await self.test_model_connectivity(model)
            self.results[model.name] = result

        # Generate summary
        summary = self._generate_summary()

        return {
            "summary": summary,
            "detailed_results": self.results,
            "mcp_client_initialized": mcp_initialized,
            "models_tested": len(models_to_test),
            "timestamp": asyncio.get_event_loop().time(),
        }

    def _generate_summary(self) -> dict[str, Any]:
        """Generate test summary.

        Returns:
            Summary of test results
        """
        total_models = len(self.results)
        accessible_models = sum(1 for r in self.results.values() if r["connectivity"])
        configured_models = sum(1 for r in self.results.values() if r["registry_configured"])
        error_models = sum(1 for r in self.results.values() if r["status"] == "error")

        standard_models = [r for r in self.results.values() if not r["is_escalation"]]
        escalation_models = [r for r in self.results.values() if r["is_escalation"]]

        accessible_standard = sum(1 for r in standard_models if r["connectivity"])
        accessible_escalation = sum(1 for r in escalation_models if r["connectivity"])

        return {
            "total_models_tested": total_models,
            "accessible_models": accessible_models,
            "configured_models": configured_models,
            "error_models": error_models,
            "standard_models_accessible": f"{accessible_standard}/{len(standard_models)}",
            "escalation_models_accessible": f"{accessible_escalation}/{len(escalation_models)}",
            "consensus_workflow_ready": accessible_standard >= MIN_CONSENSUS_MODELS,  # Need at least 2 for consensus
            "escalation_available": accessible_escalation > 0,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on test results.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        accessible_count = sum(1 for r in self.results.values() if r["connectivity"])
        configured_count = sum(1 for r in self.results.values() if r["registry_configured"])

        if accessible_count == 0:
            recommendations.append("❌ No consensus models accessible - check MCP server configuration")
            recommendations.append("🔧 Verify OpenRouter API key is configured")
            recommendations.append("🔧 Check network connectivity to OpenRouter endpoints")
        elif accessible_count < MIN_CONSENSUS_MODELS:
            recommendations.append("⚠️ Only 1 model accessible - consensus requires at least 2 models")
            recommendations.append("🔧 Configure additional models or check connectivity")
        else:
            recommendations.append(f"✅ {accessible_count} models accessible - consensus workflow ready")

        if configured_count < len(self.results):
            recommendations.append(
                f"🔧 {len(self.results) - configured_count} models not in registry - add to openrouter_models.yaml",
            )

        # Check for specific model issues
        for model_name, result in self.results.items():
            if result["alternative_suggestions"]:
                alternatives = ", ".join(result["alternative_suggestions"][:2])
                recommendations.append(f"💡 Alternative models for {model_name}: {alternatives}")

        return recommendations

    def print_results(self, results: dict[str, Any]) -> None:
        """Print formatted test results.

        Args:
            results: Test results to print
        """
        print("\n" + "=" * 80)
        print("CONSENSUS MODEL CONNECTIVITY TEST RESULTS")
        print("=" * 80)

        summary = results["summary"]
        print("\n📊 SUMMARY:")
        print(f"   Total Models Tested: {summary['total_models_tested']}")
        print(f"   Accessible Models: {summary['accessible_models']}")
        print(f"   Configured in Registry: {summary['configured_models']}")
        print(f"   Standard Models: {summary['standard_models_accessible']}")
        print(f"   Escalation Models: {summary['escalation_models_accessible']}")
        print(f"   Consensus Ready: {'✅' if summary['consensus_workflow_ready'] else '❌'}")
        print(f"   Escalation Available: {'✅' if summary['escalation_available'] else '❌'}")

        print("\n🔍 DETAILED RESULTS:")
        for model_name, result in results["detailed_results"].items():
            status_icon = "✅" if result["connectivity"] else "❌"
            escalation_text = " (ESCALATION)" if result["is_escalation"] else ""

            print(f"\n   {status_icon} {model_name}{escalation_text}")
            print(f"      OpenRouter ID: {result['openrouter_id']}")
            print(f"      Status: {result['status']}")
            print(f"      Registry Configured: {'✅' if result['registry_configured'] else '❌'}")
            print(f"      Connectivity: {'✅' if result['connectivity'] else '❌'}")

            if result["error_message"]:
                print(f"      Error: {result['error_message']}")

            if result["alternative_suggestions"]:
                print(f"      Alternatives: {', '.join(result['alternative_suggestions'][:2])}")

        print("\n💡 RECOMMENDATIONS:")
        for rec in summary["recommendations"]:
            print(f"   {rec}")

        print("\n" + "=" * 80)


async def main():
    """Main entry point for the connectivity test."""
    parser = argparse.ArgumentParser(description="Test consensus model connectivity")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--model", "-m", help="Test specific model only")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Create tester
    tester = ConsensusModelTester(verbose=args.verbose)

    try:
        # Run tests
        results = await tester.run_full_test(specific_model=args.model)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            tester.print_results(results)

        # Exit with appropriate code
        if results.get("summary", {}).get("accessible_models", 0) >= MIN_CONSENSUS_MODELS:
            sys.exit(0)  # Success - consensus ready
        else:
            sys.exit(1)  # Failure - insufficient models accessible

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
