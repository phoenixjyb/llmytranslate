#!/usr/bin/env python3
"""
Test guest chat message functionality.
"""

import asyncio
import aiohttp
import json

async def test_guest_chat():
    """Test guest chat messaging."""
    
    print("🔄 Testing guest chat messaging...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Create guest session
            print("👤 Creating guest session...")
            async with session.post("http://localhost:8000/api/users/guest-session") as response:
                if response.status == 200:
                    guest_data = await response.json()
                    guest_session_id = guest_data.get("session_id")
                    print(f"✅ Guest session created: {guest_session_id}")
                    
                    headers = {"X-Guest-Session-Id": guest_session_id}
                    
                    # Test sending a chat message
                    print("💬 Sending guest chat message...")
                    chat_request = {
                        "message": "Hello! I'm testing as a guest user.",
                        "model": "gemma3:latest"
                    }
                    
                    async with session.post(
                        "http://localhost:8000/api/chat/message",
                        json=chat_request,
                        headers=headers
                    ) as chat_response:
                        if chat_response.status == 200:
                            chat_data = await chat_response.json()
                            print(f"✅ Guest chat successful!")
                            print(f"   - Response: {chat_data.get('response', '')[:100]}...")
                            print(f"   - Conversation ID: {chat_data.get('conversation_id')}")
                            print(f"   - Model used: {chat_data.get('model_used')}")
                            print(f"   - Processing time: {chat_data.get('processing_time_ms')}ms")
                            
                            # Test conversation list after sending message
                            print("\n📋 Testing guest conversations after chat...")
                            async with session.get("http://localhost:8000/api/chat/conversations", headers=headers) as conv_response:
                                if conv_response.status == 200:
                                    conversations = await conv_response.json()
                                    print(f"✅ Guest conversations: {len(conversations)} found")
                                    if conversations:
                                        conv = conversations[0]
                                        print(f"   - Title: {conv.get('title')}")
                                        print(f"   - Messages: {conv.get('message_count')}")
                                else:
                                    print(f"❌ Conversations failed: {conv_response.status}")
                            
                        else:
                            print(f"❌ Guest chat failed: {chat_response.status}")
                            error_text = await chat_response.text()
                            print(f"Error: {error_text}")
                    
                    print("\n🎉 Guest chat testing complete!")
                    
                else:
                    print(f"❌ Guest session creation failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_guest_chat())
