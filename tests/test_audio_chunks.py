#!/usr/bin/env python3
"""
Test script to diagnose audio chunk processing.
This will make a test call and monitor the chunked audio delivery.
"""

import asyncio
import websockets
import json
import logging
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chunked_audio():
    """Test the chunked audio delivery system."""
    uri = "ws://localhost:8000/api/phone/stream"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket")
            
            # First send session_start message
            session_start = {
                "type": "session_start",
                "session_id": "test_session_001",
                "user_id": "test_user",
                "settings": {
                    "kid_friendly": False,
                    "model": "gemma2:2b"
                }
            }
            
            await websocket.send(json.dumps(session_start))
            logger.info("📤 Sent session_start message")
            
            # Wait for session acknowledgment
            ack = await websocket.recv()
            logger.info(f"📥 Session start response: {ack}")
            
            # Send a simple test message that should trigger audio response
            # Create minimal base64 audio data for testing
            dummy_audio = base64.b64encode(b"dummy_audio_data_for_testing").decode('utf-8')
            
            test_message = {
                "type": "audio_data",
                "session_id": "test_session_001",
                "audio_data": dummy_audio,
                "text": "Hello, can you hear me?"
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("📤 Sent test message")
            
            chunk_count = 0
            audio_chunks = []
            
            # Listen for responses
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"📥 Received: {data.get('type', 'unknown type')}")
                    
                    if data.get("type") == "audio_chunk":
                        chunk_count += 1
                        chunk_index = data.get("chunk_index", -1)
                        total_chunks = data.get("total_chunks", -1)
                        audio_chunk = data.get("audio_chunk", "")
                        
                        logger.info(f"🎵 Audio chunk {chunk_index + 1}/{total_chunks} received ({len(audio_chunk)} chars)")
                        
                        # Store chunk
                        if len(audio_chunks) <= chunk_index:
                            audio_chunks.extend([None] * (chunk_index + 1 - len(audio_chunks)))
                        audio_chunks[chunk_index] = audio_chunk
                        
                        # Check if we have all chunks
                        received_chunks = sum(1 for chunk in audio_chunks if chunk is not None)
                        logger.info(f"📊 Progress: {received_chunks}/{total_chunks} chunks received")
                        
                        if received_chunks == total_chunks:
                            # Combine all chunks
                            complete_audio = "".join(audio_chunks)
                            logger.info(f"✅ All chunks received! Complete audio: {len(complete_audio)} chars")
                            
                            # Try to decode and validate the base64 audio
                            try:
                                audio_bytes = base64.b64decode(complete_audio)
                                logger.info(f"🎵 Audio decoded successfully: {len(audio_bytes)} bytes")
                                
                                # Check if it looks like WAV format
                                if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:20]:
                                    logger.info("✅ Audio appears to be valid WAV format")
                                else:
                                    logger.warning("⚠️ Audio doesn't appear to be WAV format")
                                    logger.info(f"First 20 bytes: {audio_bytes[:20]}")
                                    
                            except Exception as e:
                                logger.error(f"❌ Failed to decode base64 audio: {e}")
                            
                            break
                    
                    elif data.get("type") == "error":
                        logger.error(f"❌ Server error: {data.get('message')}")
                        break
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse message: {e}")
                    
            logger.info("🏁 Test completed")
            
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_chunked_audio())
