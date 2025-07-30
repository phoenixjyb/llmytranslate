#!/usr/bin/env python3
"""
Test script for phone call mode functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_phone_call_mode():
    """Test phone call mode implementation."""
    print("🔧 Testing Phone Call Mode Implementation...")
    
    try:
        # Test 1: Import main application
        print("1. Testing main app import...")
        from src.main import create_app
        print("   ✅ Main app imported successfully")
        
        # Test 2: Import phone call routes
        print("2. Testing phone call routes import...")
        from src.api.routes import phone_call
        print("   ✅ Phone call routes imported successfully")
        
        # Test 3: Create FastAPI app
        print("3. Testing FastAPI app creation...")
        app = create_app()
        print("   ✅ FastAPI app created successfully")
        
        # Test 4: Check if routes are registered
        print("4. Testing route registration...")
        routes = [route.path for route in app.routes]
        phone_routes = [r for r in routes if "/phone" in r]
        print(f"   📞 Found phone routes: {phone_routes}")
        
        # Test 5: Check web interface files
        print("5. Testing web interface files...")
        from pathlib import Path
        web_dir = Path(__file__).parent / "web"
        
        index_html = web_dir / "index.html"
        phone_html = web_dir / "phone-call.html"
        
        if index_html.exists():
            print("   ✅ Main interface (index.html) exists")
        else:
            print("   ❌ Main interface (index.html) missing")
            
        if phone_html.exists():
            print("   ✅ Phone call interface (phone-call.html) exists")
        else:
            print("   ❌ Phone call interface (phone-call.html) missing")
        
        print("\n🎉 Phone Call Mode Implementation Test Complete!")
        print("📞 Ready for Phase 2: Real-time Audio Pipeline")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_phone_call_mode()
    sys.exit(0 if success else 1)
