#!/usr/bin/env python3
"""Test the enhanced STT service with WebM processing improvements"""

import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_stt():
    """Test the enhanced STT service"""
    try:
        # Import the enhanced STT service
        from src.services.stt_service import stt_service
        
        logger.info("🎤 Testing Enhanced STT Service")
        logger.info("=" * 40)
        
        # Test health check
        health = await stt_service.health_check()
        logger.info(f"Health Check: {health}")
        
        # Test with sample WebM-like data
        webm_magic = b'\x1A\x45\xDF\xA3'
        sample_webm_data = webm_magic + b'\x00' * 10000  # 10KB of sample data
        
        logger.info(f"\n🔍 Testing WebM processing with {len(sample_webm_data)} bytes")
        logger.info(f"Magic bytes: {sample_webm_data[:4].hex()}")
        
        try:
            result = await stt_service.transcribe_audio_file(
                audio_data=sample_webm_data,
                format="webm",
                language="en"
            )
            
            logger.info(f"\n✅ STT Result: {result}")
            
            if result.get("success"):
                logger.info("🎉 Enhanced STT processing completed successfully!")
                if result.get("text"):
                    logger.info(f"Transcribed text: '{result['text']}'")
                else:
                    logger.info("No text transcribed (expected for test data)")
                
                if "audio_analysis" in result:
                    logger.info(f"Audio analysis: {result['audio_analysis']}")
                    
                return True
            else:
                logger.error(f"STT processing failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as stt_error:
            logger.error(f"STT transcription error: {stt_error}")
            return False
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def test_phone_call_simulation():
    """Simulate phone call audio processing"""
    try:
        from src.services.stt_service import stt_service
        
        logger.info("\n📞 Simulating Phone Call Audio Processing")
        logger.info("=" * 45)
        
        # Simulate the actual WebM data pattern from the logs
        webm_magic = bytes.fromhex("1a45dfa39f4286810142f7810142f2810442f381")
        padding_data = b'\x00' * 32000  # Simulate ~32KB like in the logs
        simulated_phone_data = webm_magic + padding_data
        
        logger.info(f"Simulating phone call data: {len(simulated_phone_data)} bytes")
        logger.info(f"Magic bytes: {simulated_phone_data[:20].hex()}")
        
        result = await stt_service.transcribe_audio_file(
            audio_data=simulated_phone_data,
            format="webm",
            language="en"
        )
        
        logger.info(f"\n📊 Phone Call Simulation Result:")
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"Method: {result.get('method', 'unknown')}")
        logger.info(f"Text: '{result.get('text', '')}'")
        logger.info(f"Processing time: {result.get('processing_time', 0):.2f}s")
        
        if "audio_analysis" in result:
            logger.info(f"Audio analysis: {result['audio_analysis']}")
        
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"Phone call simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🎤 Enhanced STT Service Test")
    print("===========================")
    
    # Run tests
    basic_test = asyncio.run(test_enhanced_stt())
    phone_test = asyncio.run(test_phone_call_simulation())
    
    print(f"\n📊 Test Results:")
    print(f"Basic STT Test: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"Phone Call Simulation: {'✅ PASS' if phone_test else '❌ FAIL'}")
    
    if basic_test and phone_test:
        print("\n🎉 All tests passed! Enhanced STT service is ready.")
        print("\n💡 Key improvements:")
        print("   • Enhanced WebM processing with audio filters")
        print("   • Multiple transcription strategies")
        print("   • Aggressive volume normalization")
        print("   • Better error handling and fallbacks")
        print("   • Detailed audio analysis for debugging")
    else:
        print("\n⚠️ Some tests failed. Check the logs for details.")
