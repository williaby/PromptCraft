#!/usr/bin/env python3
"""Demonstration of the Phase 2 Core Configuration System.

This script shows how to use the environment-specific configuration loading
in your PromptCraft-Hybrid applications.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import get_settings


def main():
    """Demonstrate configuration system usage."""
    # Get settings using the factory function
    settings = get_settings()

    print("🚀 PromptCraft-Hybrid Configuration")
    print(f"   App: {settings.app_name} v{settings.version}")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug Mode: {'ON' if settings.debug else 'OFF'}")
    print(f"   API Server: http://{settings.api_host}:{settings.api_port}")

    # Environment-specific behavior
    if settings.environment == "dev":
        print("   🔧 Development mode active - verbose logging enabled")
    elif settings.environment == "staging":
        print("   🧪 Staging mode active - testing with production-like settings")
    elif settings.environment == "prod":
        print("   🏭 Production mode active - optimized for performance")


if __name__ == "__main__":
    main()
