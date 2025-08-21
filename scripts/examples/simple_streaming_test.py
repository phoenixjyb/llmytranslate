#!/usr/bin/env python3
"""
Simple Android Streaming TTS Test

This script tests if the streaming TTS WebSocket endpoint is working for Android.
"""

import asyncio
import json
import time
import websockets
import os

# Disable proxy for localhost
os.environ['no_proxy'] = 'localhost,127.0.0.1'

async def test_streaming_tts():
    """Test streaming TTS WebSocket endpoint."""
    print("🧪 Testing Android Streaming TTS")
    print("=" * 40)
    
    try:
        # Connect to WebSocket
        print("🔗 Connecting to ws://localhost:8000/ws/streaming-tts")
        websocket = await websockets.connect("ws://localhost:8000/ws/streaming-tts")
        print("✅ Connected successfully!")
        
        # Send a streaming chat request (like Android app would)
        request = {
            "type": "start_streaming_chat",
            "message": "Hello! Can you tell me a short joke?",
            "conversation_id": f"android_test_{int(time.time())}",
            "model": "gemma2:2b"
        }
        
        print(f"📤 Sending: {request['message']}")
        await websocket.send(json.dumps(request))
        
        # Listen for responses
        chunks_received = 0
        start_time = time.time()
        
        print("👂 Listening for streaming TTS chunks...")
        
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                
                message_type = data.get("type")
                print(f"📥 Received: {message_type}")
                
                if message_type == "tts_streaming_started":
                    session_id = data.get("session_id")
                    print(f"🚀 Streaming started (session: {session_id})")
                
                elif message_type == "streaming_audio_chunk":
                    chunks_received += 1
                    chunk_text = data.get("text", "")
                    chunk_index = data.get("chunk_index", 0)
                    total_chunks = data.get("total_chunks", 0)
                    is_final = data.get("is_final", False)
                    
                    print(f"🎵 Chunk {chunk_index + 1}/{total_chunks}: '{chunk_text}'")
                    print(f"   → Android would call: TTSService.addStreamingChunk('{chunk_text}', {chunk_index}, {chunk_index == 0})")
                    
                    if is_final:
                        print(f"🏁 Final chunk received")
                
                elif message_type == "tts_streaming_completed":
                    duration = time.time() - start_time
                    summary = data.get("summary", {})
                    
                    print(f"✅ Streaming completed!")
                    print(f"   Duration: {duration:.2f}s")
                    print(f"   Total chunks: {summary.get('total_chunks', chunks_received)}")
                    print(f"   Text length: {summary.get('text_length', 'unknown')}")
                    break
                
                elif message_type == "tts_streaming_error":
                    error = data.get("error", "Unknown error")
                    print(f"❌ Streaming error: {error}")
                    break
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for response")
                break
            except Exception as e:
                print(f"❌ Error receiving message: {e}")
                break
        
        await websocket.close()
        
        print(f"\n📊 Test Results:")
        print(f"Chunks received: {chunks_received}")
        print(f"Total duration: {time.time() - start_time:.2f}s")
        
        if chunks_received > 0:
            print("\n🎉 SUCCESS: Streaming TTS is working for Android!")
            print("\n📱 How it works in Android:")
            print("1. Android connects to WebSocket: ws://SERVER:8000/ws/streaming-tts")
            print("2. Sends 'start_streaming_chat' message with text")
            print("3. Receives 'streaming_audio_chunk' messages")
            print("4. Calls TTSService.addStreamingChunk() for each chunk")
            print("5. TTS service plays audio immediately as chunks arrive")
        else:
            print("\n❌ FAILURE: No streaming chunks received")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming_tts())
