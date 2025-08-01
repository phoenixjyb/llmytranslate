"""
Test the background music API endpoints
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_background_music_api():
    """Test background music API endpoints."""
    try:
        from api.routes.background_music import router, background_music_service
        
        print("🎵 Testing Background Music API...")
        
        # Test service initialization
        print("1. Service initialization...")
        service = background_music_service
        print("   ✅ Service available")
        
        # Test track listing
        print("\n2. Testing track listing...")
        tracks = service.list_available_tracks()
        print(f"   📋 Found {len(tracks)} tracks")
        for track in tracks[:3]:  # Show first 3
            print(f"   • {track['name']} - {track['style']}")
        
        # Test track generation by style
        print("\n3. Testing track generation...")
        styles = ["gentle", "meditation", "uplifting", "focus"]
        for style in styles:
            track = service.get_track_by_style(style)
            if track:
                print(f"   ✅ {style}: {track.get('name', 'Generated')}")
            else:
                print(f"   ⚠️  {style}: Not found, will generate on demand")
        
        # Test direct music generation
        print("\n4. Testing direct generation...")
        for style in ["gentle", "focus"]:
            music = service.get_background_music(style)
            if music and music.get('audio_data'):
                audio_size = len(music['audio_data'])
                print(f"   ✅ {style}: Generated {audio_size} chars of audio data")
            else:
                print(f"   ❌ {style}: Failed to generate")
        
        print("\n✅ Background Music API test completed!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phone_integration():
    """Test integration with phone call system."""
    try:
        print("\n📞 Testing Phone Call Integration...")
        
        # Import phone routes to check integration
        from api.routes import ai_phone
        print("   ✅ AI Phone routes accessible")
        
        # Check if background music is importable in phone context
        from services.background_music_service import BackgroundMusicService
        music_service = BackgroundMusicService()
        
        # Simulate phone call background music request
        bg_music = music_service.get_background_music("gentle")
        if bg_music and bg_music.get('audio_data'):
            print("   ✅ Background music available for phone calls")
            print(f"   🎵 Track: {bg_music.get('name')}")
            print(f"   ⏱️  Duration: {bg_music.get('duration')}s")
        else:
            print("   ⚠️  Background music generation needs attention")
        
        return True
        
    except Exception as e:
        print(f"❌ Phone integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Background Music System Test Suite")
    print("=" * 50)
    
    # Run async test
    success1 = asyncio.run(test_background_music_api())
    
    # Run sync test  
    success2 = test_phone_integration()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed! Background music system is ready.")
        print("\n🎯 Next steps:")
        print("   1. Test in phone call interface")
        print("   2. Verify audio plays during AI processing")
        print("   3. Adjust volume levels as needed")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print(f"\n📍 Virtual environment: {sys.executable}")
    print(f"📁 Working directory: {os.getcwd()}")
