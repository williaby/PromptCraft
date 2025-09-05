#!/usr/bin/env python
"""Debug script to test admin tab visibility in local development mode."""

import os
import logging

# Set up environment for local admin mode
os.environ['PROMPTCRAFT_DEV_MODE'] = 'true'
os.environ['PROMPTCRAFT_DEV_USER_EMAIL'] = 'byron@test.com'
os.environ['PROMPTCRAFT_LOCAL_ADMIN'] = 'true'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test admin tab creation and visibility."""
    print("🔍 Debug: Admin Tab Visibility Test")
    print("=" * 50)
    
    try:
        # Import after setting environment
        from src.ui.multi_journey_interface import MultiJourneyInterface
        
        print("✅ Step 1: Creating MultiJourneyInterface...")
        interface = MultiJourneyInterface()
        
        print(f"✅ Step 2: Admin interface type: {type(interface.admin_interface)}")
        print(f"✅ Step 3: Admin interface available: {interface.admin_interface is not None}")
        
        print("✅ Step 4: Testing user context...")
        user_context = interface._get_user_context()
        print(f"   - User context: {user_context}")
        
        print("✅ Step 5: Testing admin visibility logic...")
        is_admin = user_context.get('is_admin', False)
        user_tier = user_context.get('tier', 'limited')
        should_show = is_admin or user_tier == 'admin'
        
        print(f"   - is_admin: {is_admin}")
        print(f"   - user_tier: {user_tier}")
        print(f"   - should_show_admin_tab: {should_show}")
        
        if should_show:
            print("✅ Step 6: Admin tab should be visible!")
            print("🚀 Starting Gradio interface...")
            
            # Create the interface
            app = interface.create_interface()
            
            print("🌐 Interface created successfully!")
            print("🔗 Opening at: http://localhost:7860")
            print("👑 Look for 'Admin: Development Mode' or 'Admin: User Management' tab")
            
            # Launch with debug info
            app.launch(
                server_name="0.0.0.0", 
                server_port=7861, 
                share=False, 
                debug=True,
                show_error=True
            )
        else:
            print("❌ Step 6: Admin tab should NOT be visible")
            print("   Check environment variables and local admin mode logic")
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()