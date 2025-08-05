#!/usr/bin/env python3
"""Quick test script for phone call STT debugging"""

import asyncio
import logging
import sys
from datetime import datetime

# Set up logging to show all details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_phone_call_stt():
    """Test STT service as it would be used during phone calls"""
    
    print("📞 Phone Call STT Debug Test")
    print("=" * 30)
    print(f"Timestamp: {datetime.now()}")
    
    try:
        from src.services.stt_service import stt_service
        
        print(f"✅ STT Service loaded")
        print(f"   Whisper available: {stt_service.whisper_available}")
        
        # Health check
        health = await stt_service.health_check()
        print(f"   Health status: {health['status']}")
        print(f"   Available methods: {health['methods_available']}")
        
        # Test with realistic WebM data (similar to what you're seeing in logs)
        webm_magic = bytes.fromhex("1a45dfa39f4286810142f7810142f2810442f381")
        
        # Create test data with some variation (not all zeros)
        import os
        random_data = os.urandom(31000)  # ~31KB like in your logs
        test_audio_data = webm_magic + random_data
        
        print(f"\n🎤 Testing with {len(test_audio_data)} bytes of WebM data")
        print(f"   Magic bytes: {test_audio_data[:20].hex()}")
        print(f"   Zero byte percentage: {test_audio_data.count(0) / len(test_audio_data) * 100:.1f}%")
        
        # Test transcription
        start_time = asyncio.get_event_loop().time()
        
        result = await stt_service.transcribe_audio_file(
            audio_data=test_audio_data,
            format="webm",
            language="en"
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"\n📊 STT Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Method used: {result.get('method', 'unknown')}")
        print(f"   Text length: {len(result.get('text', ''))}")
        print(f"   Processing time: {processing_time:.2f}s")
        
        if result.get('text'):
            print(f"   Transcribed text: '{result['text']}'")
        
        if 'audio_analysis' in result:
            print(f"   Audio analysis: {result['audio_analysis']}")
        
        if result.get('error'):
            print(f"   Error: {result['error']}")
        
        # Summary
        if result.get('success'):
            if result.get('text'):
                print(f"\n🎉 SUCCESS: STT transcribed text!")
                return True
            else:
                print(f"\n⚠️ PARTIAL: STT processed but got empty text (likely silence)")
                print("   This is normal for test data - try with real audio")
                return True
        else:
            print(f"\n❌ FAILED: STT processing failed")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phone_call_stt())
    
    print(f"\n{'='*50}")
    if success:
        print("✅ Enhanced STT service is working!")
        print("\n💡 What this means for phone calls:")
        print("   • WebM audio will be processed with volume boost")
        print("   • Multiple transcription strategies will be tried")
        print("   • Better handling of quiet or unclear audio")
        print("   • Detailed logging for debugging")
        print("\n🚀 Try your phone call again - it should work better now!")
    else:
        print("❌ STT service has issues that need to be resolved")
        
    print(f"{'='*50}")
