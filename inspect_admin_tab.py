#!/usr/bin/env python
"""Inspect the admin tab structure without launching the interface."""

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
    """Inspect admin tab creation without launching."""
    print("🔍 Inspecting Admin Tab Structure")
    print("=" * 50)
    
    try:
        from src.ui.multi_journey_interface import MultiJourneyInterface
        
        print("✅ Creating interface...")
        interface = MultiJourneyInterface()
        
        print("✅ Testing admin interface...")
        admin_interface = interface.admin_interface
        print(f"   - Admin interface type: {type(admin_interface)}")
        print(f"   - Available methods: {[m for m in dir(admin_interface) if not m.startswith('_')]}")
        
        print("✅ Testing user context...")
        user_context = interface._get_user_context()
        print(f"   - User context: {user_context}")
        
        print("✅ Creating admin tab...")
        admin_tab = admin_interface.create_admin_interface()
        print(f"   - Admin tab type: {type(admin_tab)}")
        print(f"   - Admin tab visible: {admin_tab.visible}")
        print(f"   - Admin tab elem_id: {getattr(admin_tab, 'elem_id', 'None')}")
        
        print("✅ Testing visibility setup...")
        interface._setup_admin_visibility(admin_tab, user_context)
        print(f"   - Admin tab visible after setup: {admin_tab.visible}")
        
        # Check the tab label/title
        if hasattr(admin_tab, 'label'):
            print(f"   - Admin tab label: {admin_tab.label}")
        
        print("🎯 DIAGNOSTIC COMPLETE")
        print(f"   - Admin tab should be visible: {admin_tab.visible}")
        print(f"   - User has admin privileges: {user_context.get('is_admin', False)}")
        
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()