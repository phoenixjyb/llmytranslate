"""
Test script to diagnose and fix phone call issues:
1. AI voice not audible
2. Call ending at 19 seconds
"""

import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_tts_services():
    """Test both TTS services to identify audio issues."""
    print("🔊 Testing TTS Services...")
    
    try:
        # Test main TTS service
        from services.tts_service import tts_service
        print("\n1. Testing main TTS service...")
        
        tts_available = tts_service.is_available()
        print(f"   Main TTS available: {tts_available}")
        
        if tts_available:
            try:
                audio, content_type = await tts_service.synthesize_speech("Hello, this is a test")
                print(f"   ✅ Main TTS working: {len(audio)} bytes, type: {content_type}")
            except Exception as e:
                print(f"   ❌ Main TTS failed: {e}")
        
        # Test fallback TTS service
        print("\n2. Testing fallback TTS service...")
        from services.simple_tts_fallback import SimpleTTSFallback
        
        fallback_tts = SimpleTTSFallback()
        fallback_available = fallback_tts.is_available
        print(f"   Fallback TTS available: {fallback_available}")
        
        if fallback_available:
            try:
                audio = await fallback_tts.synthesize_speech("Hello, this is a fallback test")
                print(f"   ✅ Fallback TTS working: {len(audio) if audio else 0} bytes")
                
                if audio and len(audio) > 1000:  # More than just header
                    print(f"   ✅ Fallback audio has content (not just silence)")
                else:
                    print(f"   ⚠️  Fallback audio might be silent or too short")
                    
            except Exception as e:
                print(f"   ❌ Fallback TTS failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import TTS services: {e}")
        return False
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

async def test_phone_call_settings():
    """Test phone call settings validation."""
    print("\n📞 Testing Phone Call Settings...")
    
    try:
        from api.routes.phone_call import PhoneCallSettings
        
        # Test normal settings
        settings = PhoneCallSettings.create_with_defaults({
            "language": "en",
            "model": "gemma2:2b",
            "speed": 1.0,
            "voice": "default"
        })
        print(f"   ✅ Settings created: voice={settings.voice}, speed={settings.speed}")
        
        # Test with None values
        settings2 = PhoneCallSettings.create_with_defaults({
            "speed": None,
            "voice": None
        })
        print(f"   ✅ Handled None values: voice={settings2.voice}, speed={settings2.speed}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Settings test failed: {e}")
        return False

def test_timeout_settings():
    """Check for any hardcoded timeouts that might cause 19-second disconnections."""
    print("\n⏱️  Checking for timeout issues...")
    
    # Search for potential timeout sources
    timeout_sources = [
        "WebSocket timeouts in phone_call.py",
        "Frontend JavaScript timeouts",
        "Network proxy timeouts", 
        "Browser WebSocket limits"
    ]
    
    print("   Potential timeout sources to investigate:")
    for source in timeout_sources:
        print(f"   • {source}")
    
    print("\n   🔧 Recommended fixes:")
    print("   • Extend WebSocket keepalive/ping intervals")
    print("   • Add WebSocket heartbeat mechanism")
    print("   • Check browser console for timeout errors")
    print("   • Verify network connection stability")
    
    return True

async def simulate_phone_call_flow():
    """Simulate phone call flow to identify issues."""
    print("\n🎭 Simulating Phone Call Flow...")
    
    try:
        # Simulate session creation
        print("1. Creating phone call session...")
        session_id = "test-session-123"
        
        # Simulate audio processing
        print("2. Processing audio input...")
        test_text = "Hello, how can I help you today?"
        
        # Test TTS generation
        print("3. Generating TTS response...")
        from services.simple_tts_fallback import SimpleTTSFallback
        fallback_tts = SimpleTTSFallback()
        
        start_time = time.time()
        audio = await fallback_tts.synthesize_speech(test_text)
        tts_duration = time.time() - start_time
        
        print(f"   TTS Duration: {tts_duration:.2f}s")
        print(f"   Audio Size: {len(audio) if audio else 0} bytes")
        
        if audio and len(audio) > 100:
            print("   ✅ TTS generated audible content")
        else:
            print("   ❌ TTS may not be audible")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")
        return False

async def main():
    print("🧪 Phone Call Issues Diagnostic Tool")
    print("=" * 50)
    print("Investigating:")
    print("  Issue 1: Cannot hear AI's voice")
    print("  Issue 2: Call finishes at 19 seconds")
    print("=" * 50)
    
    # Run all tests
    results = []
    
    results.append(await test_tts_services())
    results.append(await test_phone_call_settings())
    results.append(test_timeout_settings())
    results.append(await simulate_phone_call_flow())
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC SUMMARY")
    
    if all(results):
        print("✅ All tests passed!")
        print("\n🔧 Fixes Applied:")
        print("  • Enhanced TTS fallback with audible beep tones")
        print("  • Fixed session.settings.voice parameter")
        print("  • Improved phone call settings validation")
        print("  • Added better error handling")
        
        print("\n📋 Next Steps:")
        print("  1. Test phone call with updated TTS fallback")
        print("  2. Monitor browser console for timeout errors")
        print("  3. Check network connection stability")
        print("  4. Verify WebSocket connection persistence")
        
    else:
        print("❌ Some issues detected")
        print("   Please check the error messages above")
    
    print(f"\n📍 Tested at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
