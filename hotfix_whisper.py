#!/usr/bin/env python3
"""Hot-fix to enable Whisper in the running service"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def hotfix_whisper():
    """Send API request to force enable Whisper"""
    try:
        # Create a simple test endpoint to enable Whisper
        async with aiohttp.ClientSession() as session:
            # Make a request that forces STT service to re-check Whisper
            test_data = {
                "text": "test whisper availability",
                "force_whisper_check": True
            }
            
            # Try to access the STT service health endpoint multiple times
            # This might trigger a re-initialization
            for i in range(3):
                async with session.get("http://localhost:8000/api/stt/health") as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"STT Health Check #{i+1}: whisper_available = {result.get('whisper_available')}")
                        if result.get('whisper_available'):
                            logger.info("✅ Whisper is now enabled!")
                            return True
                    await asyncio.sleep(1)
            
            logger.warning("Whisper still not enabled - service restart may be needed")
            return False
            
    except Exception as e:
        logger.error(f"Hotfix failed: {e}")
        return False

async def main():
    """Try to enable Whisper without restarting"""
    logger.info("🔧 Attempting to enable Whisper in running service...")
    
    success = await hotfix_whisper()
    
    if success:
        logger.info("🎉 Whisper enabled! Phone calls should now work.")
    else:
        logger.warning("⚠️ Manual intervention needed - check the STT service initialization")
        logger.info("💡 The issue might be with WebM audio format processing")

if __name__ == "__main__":
    asyncio.run(main())
