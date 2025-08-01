#!/usr/bin/env python3
"""
Test script for TTS integration with the LLM Translation Service.
This script tests TTS functionality without requiring Coqui TTS to be installed.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.services.tts_service import tts_service, cached_tts_service


async def test_tts_availability():
    """Test if TTS service is available and properly configured."""
    print("🔄 Testing TTS Service Availability...")
    
    # Test health status
    health = await tts_service.get_health_status()
    print("\n📊 TTS Health Status:")
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Test available languages
    languages = await tts_service.get_available_languages()
    print(f"\n🌐 Available Languages: {len(languages)}")
    for lang in languages:
        print(f"  - {lang}")
    
    return health.get('tts_available', False)


async def test_tts_synthesis():
    """Test TTS synthesis functionality."""
    print("\n🔄 Testing TTS Synthesis...")
    
    test_cases = [
        {"text": "Hello, this is a test!", "language": "en"},
        {"text": "你好，这是一个测试！", "language": "zh"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['language']}")
        print(f"   Text: {case['text']}")
        
        try:
            result = await tts_service.synthesize_speech(
                text=case['text'],
                language=case['language'],
                voice_speed=1.0
            )
            
            if result['success']:
                print(f"   ✅ Success!")
                print(f"   ⏱️  Processing time: {result['processing_time']:.3f}s")
                print(f"   📏 Audio size: {result.get('audio_size_bytes', 0)} bytes")
                print(f"   🤖 Model used: {result.get('model_used', 'unknown')}")
                
                if 'detailed_timing' in result:
                    timing = result['detailed_timing']
                    print(f"   📊 Detailed timing:")
                    for key, value in timing.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")


async def test_cached_service():
    """Test cached TTS service."""
    print("\n🔄 Testing Cached TTS Service...")
    
    test_text = "This is a cache test message."
    
    # First call (should not be cached)
    print("📝 First call (should miss cache):")
    result1 = await cached_tts_service.synthesize_speech(
        text=test_text,
        language="en"
    )
    
    if result1['success']:
        print(f"   ⏱️  Processing time: {result1['processing_time']:.3f}s")
        print(f"   💾 Cache hit: {result1.get('cache_hit', False)}")
    
    # Second call (should be cached)
    print("\n📝 Second call (should hit cache):")
    result2 = await cached_tts_service.synthesize_speech(
        text=test_text,
        language="en"
    )
    
    if result2['success']:
        print(f"   ⏱️  Processing time: {result2['processing_time']:.3f}s")
        print(f"   💾 Cache hit: {result2.get('cache_hit', False)}")
    
    # Get cache stats
    if hasattr(cached_tts_service, 'get_cache_stats'):
        cache_stats = await cached_tts_service.get_cache_stats()
        print(f"\n📊 Cache Statistics:")
        for key, value in cache_stats.items():
            print(f"   {key}: {value}")


async def test_api_integration():
    """Test that the API routes can be imported without errors."""
    print("\n🔄 Testing API Integration...")
    
    try:
        from src.api.routes.tts import router
        print("   ✅ TTS router imported successfully")
        print(f"   📍 Routes count: {len(router.routes)}")
        
        # List available routes
        print("   📝 Available TTS endpoints:")
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"      {methods} {route.path}")
        
    except Exception as e:
        print(f"   ❌ API integration failed: {str(e)}")


async def main():
    """Run all TTS tests."""
    print("🎤 LLM Translation Service - TTS Integration Test")
    print("=" * 50)
    
    try:
        # Test TTS availability
        tts_available = await test_tts_availability()
        
        if tts_available:
            await test_tts_synthesis()
            await test_cached_service()
        else:
            print("\n⚠️  TTS library not available.")
            print("💡 To install TTS support, run:")
            print("   pip install coqui-tts")
            print("   pip install torch torchvision torchaudio")
        
        # Test API integration regardless of TTS availability
        await test_api_integration()
        
        print("\n✨ TTS Integration Test Complete!")
        
        if not tts_available:
            print("\n🔧 Installation Instructions:")
            print("1. Install Coqui TTS:")
            print("   pip install coqui-tts")
            print("\n2. Install PyTorch (with CUDA for GPU acceleration):")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            print("\n3. Restart the application to use TTS features")
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
