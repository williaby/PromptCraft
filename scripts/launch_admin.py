#!/usr/bin/env python
"""Launch PromptCraft with admin interface enabled."""

import logging
import os


# Set up environment for local admin mode
os.environ["PROMPTCRAFT_DEV_MODE"] = "true"
os.environ["PROMPTCRAFT_DEV_USER_EMAIL"] = "byron@test.com"
os.environ["PROMPTCRAFT_LOCAL_ADMIN"] = "true"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Launch the interface with admin access."""
    print("🚀 Launching PromptCraft with Admin Interface")
    print("=" * 50)
    print("✅ Environment configured for local admin access")
    print("✅ Admin tab will be visible as: '👑 Admin: Development Mode'")
    print("🌐 Interface will be available at: http://localhost:7861")
    print()

    try:
        from src.ui.multi_journey_interface import MultiJourneyInterface

        # Create and launch interface
        interface = MultiJourneyInterface()
        app = interface.create_interface()

        print("✅ Interface created successfully with admin access!")
        print("👑 Look for the 'Admin: Development Mode' tab")

        # Launch on an available port
        app.launch(
            server_name="0.0.0.0",
            server_port=7861,
            share=False,
            debug=True,
            show_error=True,
            inbrowser=True,  # Auto-open browser
        )

    except Exception as e:
        print(f"❌ Error launching interface: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
