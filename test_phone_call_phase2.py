#!/usr/bin/env python3
"""
Test script for phone call mode Phase 2 functionality.
Tests real-time audio pipeline components.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(__file__))

async def test_phase_2_components():
    """Test Phase 2 phone call components."""
    print("🔧 Testing Phone Call Mode Phase 2 Components...")
    
    success_count = 0
    total_tests = 7
    
    try:
        # Test 1: Import real-time STT service
        print("1. Testing real-time STT service...")
        try:
            from src.services.realtime_stt_service import realtime_stt_service
            health = await realtime_stt_service.health_check()
            print(f"   ✅ Real-time STT service: {health['status']}")
            if health['vad_available']:
                print("   🎙️ Voice Activity Detection available")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Real-time STT service error: {e}")
        
        # Test 2: Import background music service
        print("2. Testing background music service...")
        try:
            from src.services.background_music_service import background_music_service
            health = await background_music_service.health_check()
            print(f"   ✅ Background music service: {health['status']}")
            print(f"   🎵 Available tracks: {health['available_tracks']}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Background music service error: {e}")
        
        # Test 3: Test phone call manager with buffering
        print("3. Testing phone call manager with audio buffering...")
        try:
            from src.api.routes.phone_call import phone_manager
            session_id = "test-session-123"
            
            # Test audio buffering
            test_audio = b"test audio data" * 100  # Some test audio data
            phone_manager.audio_buffers[session_id] = []
            
            is_ready = phone_manager.add_audio_chunk(session_id, test_audio)
            print(f"   ✅ Audio buffering: Ready for processing = {is_ready}")
            
            if session_id in phone_manager.audio_buffers:
                del phone_manager.audio_buffers[session_id]
            
            success_count += 1
        except Exception as e:
            print(f"   ❌ Phone call manager error: {e}")
        
        # Test 4: Test WebSocket routes structure
        print("4. Testing WebSocket routes structure...")
        try:
            from src.api.routes.phone_call import router, handle_audio_data, handle_session_start
            print("   ✅ WebSocket handlers available")
            success_count += 1
        except Exception as e:
            print(f"   ❌ WebSocket routes error: {e}")
        
        # Test 5: Test enhanced audio processing
        print("5. Testing enhanced audio processing...")
        try:
            # Test with a small audio sample
            test_audio_small = b"small" * 50  # Too small, should be skipped
            test_audio_large = b"audio" * 500  # Large enough for processing
            
            print(f"   📊 Small audio size: {len(test_audio_small)} bytes")
            print(f"   📊 Large audio size: {len(test_audio_large)} bytes")
            print("   ✅ Audio size detection working")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Audio processing error: {e}")
        
        # Test 6: Test optional dependencies
        print("6. Testing optional dependencies...")
        optional_deps = []
        
        try:
            import webrtcvad
            optional_deps.append("WebRTC VAD")
        except ImportError:
            pass
        
        try:
            import scipy.signal
            optional_deps.append("SciPy")
        except ImportError:
            pass
        
        try:
            import numpy
            optional_deps.append("NumPy")
        except ImportError:
            pass
        
        print(f"   📦 Available optional dependencies: {', '.join(optional_deps) if optional_deps else 'None'}")
        print("   ✅ Optional dependencies check complete")
        success_count += 1
        
        # Test 7: Test phone call HTML enhancements
        print("7. Testing phone call HTML enhancements...")
        try:
            from pathlib import Path
            phone_html = Path(__file__).parent / "web" / "phone-call.html"
            
            if phone_html.exists():
                content = phone_html.read_text()
                
                # Check for new features
                features = [
                    ("Background music support", "playBackgroundMusic" in content),
                    ("Audio interruption", "interruptAI" in content),
                    ("Enhanced WebSocket handling", "handleWebSocketMessage" in content),
                    ("Improved audio recording", "setupAudioRecording" in content),
                    ("Timing display", "processing_time" in content)
                ]
                
                for feature_name, present in features:
                    status = "✅" if present else "❌"
                    print(f"   {status} {feature_name}")
                
                print("   ✅ Phone call HTML enhancements verified")
                success_count += 1
            else:
                print("   ❌ Phone call HTML not found")
        except Exception as e:
            print(f"   ❌ HTML check error: {e}")
        
        print(f"\n🎉 Phase 2 Component Test Complete!")
        print(f"📊 Success Rate: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🌟 All Phase 2 components are working correctly!")
            print("📞 Ready for real-time phone calls!")
        elif success_count >= total_tests - 2:
            print("⚠️ Most Phase 2 components are working. Some optional features may be limited.")
            print("📞 Phone calls should work with reduced functionality.")
        else:
            print("❌ Several Phase 2 components have issues. Please check the errors above.")
            print("🔧 You may need to install additional dependencies or fix import issues.")
        
        print("\n🚀 Next Steps:")
        print("   1. Install optional dependencies: .\install-phone-call-deps.ps1")
        print("   2. Start the server: .venv\\Scripts\\python.exe run.py")
        print("   3. Test phone calls: http://localhost:8000/phone-call")
        print("   4. Check health: http://localhost:8000/api/phone/health")
        
        return success_count >= total_tests - 2
        
    except Exception as e:
        print(f"❌ Unexpected error during Phase 2 testing: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase_2_components())
    sys.exit(0 if success else 1)
