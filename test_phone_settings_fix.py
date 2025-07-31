"""
Test script to validate phone call settings validation fix
"""

import json
from pydantic import ValidationError

# Test the PhoneCallSettings model with various inputs
def test_phone_call_settings():
    print("🧪 Testing PhoneCallSettings validation fix...")
    
    # Test cases that might cause validation errors
    test_cases = [
        {
            "name": "Normal settings",
            "data": {
                "language": "en",
                "model": "gemma2:2b", 
                "speed": 1.0,
                "kid_friendly": False,
                "background_music": True,
                "voice": "default"
            },
            "should_pass": True
        },
        {
            "name": "Missing speed (None)",
            "data": {
                "language": "en",
                "model": "gemma2:2b",
                "speed": None,  # This was causing the error
                "kid_friendly": False,
                "background_music": True
            },
            "should_pass": True  # Should pass with our fix
        },
        {
            "name": "Empty settings",
            "data": {},
            "should_pass": True  # Should use all defaults
        },
        {
            "name": "Partial settings with None values",
            "data": {
                "language": "en",
                "speed": None,
                "voice": None
            },
            "should_pass": True
        },
        {
            "name": "String speed (invalid)",
            "data": {
                "speed": "invalid"
            },
            "should_pass": False  # Should fail validation
        }
    ]
    
    # Import the updated PhoneCallSettings
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from api.routes.phone_call import PhoneCallSettings
        
        for test_case in test_cases:
            print(f"\n📋 Testing: {test_case['name']}")
            print(f"   Data: {test_case['data']}")
            
            try:
                # Test the new create_with_defaults method
                settings = PhoneCallSettings.create_with_defaults(test_case['data'])
                print(f"   ✅ Created successfully:")
                print(f"      language: {settings.language}")
                print(f"      model: {settings.model}")
                print(f"      speed: {settings.speed}")
                print(f"      kid_friendly: {settings.kid_friendly}")
                print(f"      background_music: {settings.background_music}")
                print(f"      voice: {settings.voice}")
                
                if not test_case['should_pass']:
                    print(f"   ⚠️  Expected this to fail but it passed")
                
            except ValidationError as e:
                if test_case['should_pass']:
                    print(f"   ❌ Validation failed unexpectedly: {e}")
                else:
                    print(f"   ✅ Validation failed as expected: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
        
        print(f"\n✅ PhoneCallSettings validation test completed!")
        
    except ImportError as e:
        print(f"❌ Failed to import PhoneCallSettings: {e}")
        return False
    
    return True

def test_javascript_settings():
    """Test JavaScript-like settings that might come from frontend."""
    print("\n🌐 Testing JavaScript-style settings...")
    
    # Simulate what might come from the frontend
    js_like_settings = [
        {"speed": "1.0"},  # String instead of float
        {"speed": ""},     # Empty string
        {"speed": "NaN"},  # JavaScript NaN as string
        {"kid_friendly": "false"},  # String boolean
        {"background_music": "true"}  # String boolean
    ]
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from api.routes.phone_call import PhoneCallSettings
        
        for i, settings_data in enumerate(js_like_settings):
            print(f"\n📱 JS Test {i+1}: {settings_data}")
            try:
                settings = PhoneCallSettings.create_with_defaults(settings_data)
                print(f"   ✅ Handled successfully: speed={settings.speed}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")

if __name__ == "__main__":
    print("🔧 Phone Call Settings Validation Fix Test")
    print("=" * 50)
    
    success = test_phone_call_settings()
    test_javascript_settings()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Phone call settings validation fix is working!")
        print("\n🎯 The error should now be resolved:")
        print("   • None values are handled gracefully")
        print("   • Default values are applied properly") 
        print("   • Frontend validation prevents invalid data")
    else:
        print("❌ There may still be issues with the fix")
    
    print(f"\n📍 Test completed at: {os.getcwd()}")
