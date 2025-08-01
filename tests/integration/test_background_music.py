"""Test background music service functionality"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from services.background_music_service import BackgroundMusicService
    
    print("🎵 Testing Background Music Service...")
    
    # Initialize service
    service = BackgroundMusicService()
    print("✅ Service initialized")
    
    # Test different styles
    styles = ["gentle", "meditation", "uplifting", "focus", "default"]
    
    for style in styles:
        print(f"\n🎼 Testing {style} style...")
        track = service.get_background_music(style)
        
        if track:
            print(f"   ✅ Generated: {track.get('name')}")
            print(f"   ⏱️  Duration: {track.get('duration')}s")
            print(f"   🎚️  Volume: {track.get('volume')}")
            print(f"   🎵 Has audio: {'Yes' if track.get('audio_data') else 'No'}")
            if track.get('audio_data'):
                audio_len = len(track['audio_data'])
                print(f"   📊 Audio size: {audio_len} chars (base64)")
        else:
            print(f"   ❌ Failed to generate {style} track")
    
    # Test track listing
    print(f"\n📋 Available tracks:")
    tracks = service.list_available_tracks()
    for track in tracks:
        print(f"   • {track['name']} ({track['style']}) - {track['duration']}s")
    
    print(f"\n✅ Background music service test completed!")
    print(f"🎵 Total styles available: {len(styles)}")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
