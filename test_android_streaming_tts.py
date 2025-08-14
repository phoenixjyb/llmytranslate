#!/usr/bin/env python3
"""
Test Android Streaming TTS Integration

This script tests the new streaming TTS functionality for Android clients.
"""

import asyncio
import json
import time
import websockets
from typing import Dict, Any

# Test configuration
WEBSOCKET_URL = "ws://localhost:8000/ws/android"
TEST_SESSION_ID = "test_streaming_android_001"

class AndroidStreamingTTSTest:
    def __init__(self):
        self.websocket = None
        self.messages_received = []
        
    async def connect(self):
        """Connect to Android WebSocket endpoint."""
        print("🔗 Connecting to Android WebSocket...")
        self.websocket = await websockets.connect(WEBSOCKET_URL)
        print("✅ Connected to Android WebSocket")
        
    async def send_message(self, message: Dict[str, Any]):
        """Send message to Android WebSocket."""
        message_json = json.dumps(message)
        await self.websocket.send(message_json)
        print(f"📤 Sent: {message['type']} - {message.get('text', message.get('message', ''))[:50]}...")
        
    async def receive_messages(self, timeout: int = 30):
        """Receive and log messages for a specified duration."""
        print(f"👂 Listening for messages for {timeout} seconds...")
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    # Wait for message with shorter timeout
                    message_str = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=2.0
                    )
                    message = json.loads(message_str)
                    self.messages_received.append(message)
                    
                    msg_type = message.get("type", "unknown")
                    
                    if msg_type == "streaming_audio_chunk":
                        chunk_idx = message.get("chunk_index", 0)
                        total_chunks = message.get("total_chunks", 0)
                        text = message.get("text", "")
                        is_final = message.get("is_final", False)
                        
                        print(f"🎵 Chunk {chunk_idx+1}/{total_chunks}: '{text[:40]}...' {'(FINAL)' if is_final else ''}")
                        
                    elif msg_type == "tts_streaming_started":
                        print(f"🚀 Streaming started: {message.get('message', '')}")
                        
                    elif msg_type == "tts_streaming_completed":
                        summary = message.get("summary", {})
                        print(f"✅ Streaming completed: {summary.get('total_chunks', 0)} chunks in {summary.get('total_duration_ms', 0)}ms")
                        
                    elif msg_type == "tts_streaming_error":
                        print(f"❌ Streaming error: {message.get('error', 'Unknown error')}")
                        
                    else:
                        print(f"📥 Received: {msg_type} - {str(message)[:100]}...")
                        
                except asyncio.TimeoutError:
                    # No message received in timeout, continue listening
                    continue
                    
        except Exception as e:
            print(f"❌ Error receiving messages: {e}")
            
    async def test_traditional_tts(self):
        """Test traditional (non-streaming) TTS."""
        print("\n🧪 Testing Traditional TTS...")
        
        # Start session
        await self.send_message({
            "type": "session_start",
            "session_id": TEST_SESSION_ID,
            "settings": {
                "model": "gemma2:2b",
                "language": "en-US",
                "kid_friendly": False
            }
        })
        
        # Wait for session start response
        await asyncio.sleep(1)
        
        # Send text input WITHOUT streaming flag
        await self.send_message({
            "type": "text_input",
            "session_id": TEST_SESSION_ID,
            "text": "Hello, how are you today?",
            "use_streaming_tts": False  # Traditional approach
        })
        
        # Listen for responses
        await self.receive_messages(timeout=15)
        
    async def test_streaming_tts(self):
        """Test streaming TTS functionality."""
        print("\n🎵 Testing Streaming TTS...")
        
        # Send text input WITH streaming flag
        await self.send_message({
            "type": "text_input",
            "session_id": TEST_SESSION_ID,
            "text": "Tell me an interesting story about space exploration.",
            "use_streaming_tts": True  # NEW: Enable streaming TTS
        })
        
        # Listen for streaming responses
        await self.receive_messages(timeout=20)
        
    async def cleanup(self):
        """Clean up session."""
        print("\n🧹 Cleaning up...")
        
        # End session
        await self.send_message({
            "type": "session_end",
            "session_id": TEST_SESSION_ID
        })
        
        # Close connection
        await self.websocket.close()
        print("✅ Session ended and connection closed")
        
    def analyze_results(self):
        """Analyze the test results."""
        print("\n📊 Test Results Analysis:")
        print(f"Total messages received: {len(self.messages_received)}")
        
        # Count message types
        message_types = {}
        streaming_chunks = []
        
        for msg in self.messages_received:
            msg_type = msg.get("type", "unknown")
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            if msg_type == "streaming_audio_chunk":
                streaming_chunks.append(msg)
                
        print("Message type breakdown:")
        for msg_type, count in message_types.items():
            print(f"  {msg_type}: {count}")
            
        if streaming_chunks:
            print(f"\n🎵 Streaming TTS Analysis:")
            print(f"  Total chunks: {len(streaming_chunks)}")
            
            # Check chunk order
            chunk_indices = [chunk.get("chunk_index", -1) for chunk in streaming_chunks]
            expected_indices = list(range(len(streaming_chunks)))
            
            if chunk_indices == expected_indices:
                print("  ✅ Chunks received in correct order")
            else:
                print(f"  ❌ Chunk order issue: expected {expected_indices}, got {chunk_indices}")
                
            # Find final chunk
            final_chunks = [chunk for chunk in streaming_chunks if chunk.get("is_final", False)]
            if len(final_chunks) == 1:
                print("  ✅ Exactly one final chunk found")
            else:
                print(f"  ❌ Expected 1 final chunk, found {len(final_chunks)}")
                
    async def run_full_test(self):
        """Run the complete test suite."""
        try:
            await self.connect()
            
            # Test both traditional and streaming approaches
            await self.test_traditional_tts()
            await asyncio.sleep(2)  # Brief pause between tests
            await self.test_streaming_tts()
            
            await self.cleanup()
            self.analyze_results()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            if self.websocket:
                await self.websocket.close()

async def main():
    """Main test runner."""
    print("🧪 Android Streaming TTS Integration Test")
    print("=" * 50)
    
    tester = AndroidStreamingTTSTest()
    await tester.run_full_test()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
