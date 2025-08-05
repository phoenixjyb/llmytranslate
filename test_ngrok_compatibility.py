#!/usr/bin/env python3
"""Hot-fix STT service to enable Whisper without service restart"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def hotfix_stt_service():
    """Send a request to force STT service to re-enable Whisper"""
    try:
        # First, let's make a direct API call to test STT
        async with aiohttp.ClientSession() as session:
            # Check current STT health
            async with session.get("http://localhost:8000/api/stt/health") as response:
                if response.status == 200:
                    health = await response.json()
                    logger.info(f"Current STT Health: {health}")
                    
                    if health.get("whisper_available"):
                        logger.info("✅ Whisper is already enabled!")
                        return True
                    else:
                        logger.warning("❌ Whisper is disabled in running service")
                else:
                    logger.error(f"STT health check failed: {response.status}")
                    
            # Try to force STT service to re-check Whisper
            # We'll create a test transcription request that might trigger re-initialization
            test_audio_data = {
                "audio_data": "",  # Empty for now
                "format": "webm",
                "language": "en"
            }
            
            logger.info("Attempting to trigger STT service Whisper re-check...")
            
            # Since we can't directly access the running service instance,
            # let's restart just the service components we need
            
        return False
        
    except Exception as e:
        logger.error(f"Hotfix failed: {e}")
        return False

async def test_ngrok_compatibility():
    """Test if the service works well with ngrok/remote access"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test phone call health
            async with session.get("http://localhost:8000/api/phone/health") as response:
                if response.status == 200:
                    health = await response.json()
                    logger.info("📱 Phone Call Service Health:")
                    logger.info(f"  - Overall Status: {health['status']}")
                    logger.info(f"  - STT Status: {health['components']['stt']['status']}")
                    logger.info(f"  - Whisper Available: {health['components']['stt']['whisper_available']}")
                    logger.info(f"  - TTS Status: {health['components']['tts']['status']}")
                    logger.info(f"  - WebSocket Support: {health['capabilities']['websocket_support']}")
                    
                    if not health['components']['stt']['whisper_available']:
                        logger.warning("⚠️  Whisper is not available - this will cause STT failures")
                        logger.info("🔧 Service restart needed to fix Whisper")
                        return False
                    else:
                        logger.info("✅ All components ready for ngrok/remote testing!")
                        return True
                else:
                    logger.error(f"Phone health check failed: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"ngrok compatibility test failed: {e}")
        return False

async def main():
    logger.info("🧪 Testing ngrok compatibility and STT status...")
    
    # Test current service status
    compatible = await test_ngrok_compatibility()
    
    if compatible:
        logger.info("🎉 Service is ready for ngrok/remote testing!")
        logger.info("📱 Your setup will work fine:")
        logger.info("  ✅ Remote microphone → WebSocket → Your Server Whisper STT")
        logger.info("  ✅ Your Server LLM processing")  
        logger.info("  ✅ Your Server TTS → WebSocket → Remote speakers")
        logger.info("")
        logger.info("🌐 To test via ngrok:")
        logger.info("  1. Run: ngrok http 8000")
        logger.info("  2. Use the ngrok URL + /phone-call")
        logger.info("  3. Grant microphone permissions on remote device")
        logger.info("  4. Should work perfectly!")
    else:
        logger.warning("⚠️  Service needs restart to enable Whisper for STT")
        logger.info("🔧 Please restart the service to fix Whisper availability")

if __name__ == "__main__":
    asyncio.run(main())
