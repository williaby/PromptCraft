#!/usr/bin/env python3
"""Demonstration of the Phase 2 Core Configuration System.

This script shows how to use the environment-specific configuration loading
in your PromptCraft-Hybrid applications.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import get_settings


def main() -> None:
    """Demonstrate configuration system usage."""
    # Get settings using the factory function
    settings = get_settings()

    # Use logging instead of print statements
    logger = logging.getLogger(__name__)
    logger.info("🚀 PromptCraft-Hybrid Configuration")
    logger.info("   App: %s v%s", settings.app_name, settings.version)
    logger.info("   Environment: %s", settings.environment)
    logger.info("   Debug Mode: %s", "ON" if settings.debug else "OFF")
    logger.info("   API Server: http://%s:%s", settings.api_host, settings.api_port)

    # Environment-specific behavior
    if settings.environment == "dev":
        logger.info("   🔧 Development mode active - verbose logging enabled")
    elif settings.environment == "staging":
        logger.info("   🧪 Staging mode active - testing with production-like settings")
    elif settings.environment == "prod":
        logger.info("   🏭 Production mode active - optimized for performance")


if __name__ == "__main__":
    main()
