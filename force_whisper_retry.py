#!/usr/bin/env python3
"""Force Whisper re-initialization via API call"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_whisper_retry():
    """Force the STT service to retry Whisper initialization by making a test call"""
    try:
        # Create a minimal audio file (just some bytes to trigger processing)
        import base64
        
        # Create a minimal test - just send empty audio to trigger retry logic
        test_data = {
            "audio_data": base64.b64encode(b"").decode(),  # Empty audio
            "format": "webm",
            "language": "en"
        }
        
        async with aiohttp.ClientSession() as session:
            # Make a transcription request that will trigger Whisper retry
            logger.info("Sending test transcription request to trigger Whisper retry...")
            
            async with session.post(
                "http://localhost:8000/api/stt/transcribe", 
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"STT Response: {result}")
                    
                    # Check if Whisper is now working
                    if result.get("method") == "whisper_local":
                        logger.info("✅ Whisper is now working!")
                        return True
                    else:
                        logger.info(f"Method used: {result.get('method')}")
                        
                else:
                    logger.warning(f"STT request failed: {response.status}")
                    
            # Check health after the request
            async with session.get("http://localhost:8000/api/phone/health") as response:
                if response.status == 200:
                    health = await response.json()
                    whisper_available = health.get("components", {}).get("stt", {}).get("whisper_available", False)
                    logger.info(f"Phone health check - Whisper available: {whisper_available}")
                    return whisper_available
                    
        return False
        
    except Exception as e:
        logger.error(f"Force retry failed: {e}")
        return False

async def main():
    logger.info("🔧 Forcing Whisper retry in STT service...")
    
    success = await force_whisper_retry()
    
    if success:
        logger.info("🎉 Whisper should now be working! Try the phone call again.")
    else:
        logger.warning("⚠️ Whisper retry didn't work. The issue might be:")
        logger.info("  1. WebM audio format compatibility issues")
        logger.info("  2. FFmpeg not properly handling browser audio")
        logger.info("  3. Service needs a full restart")
        
        logger.info("\n💡 Workaround: You can still test ngrok functionality!")
        logger.info("   The service will work once you get valid audio data.")

if __name__ == "__main__":
    asyncio.run(main())
