#!/usr/bin/env python3
"""
Test the conversation history API functionality.
"""

import asyncio
import sys
import json
import aiohttp
from pathlib import Path

async def test_conversation_history():
    """Test conversation history retrieval."""
    
    print("🔄 Testing conversation history API...")
    
    # First, login to get authentication token
    login_data = {
        "username_or_email": "demo_user",
        "password": "Password123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Login
            print("🔐 Logging in as demo_user...")
            async with session.post(
                "http://localhost:8000/api/users/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    auth_token = login_result.get("access_token")
                    print(f"✅ Login successful! Token: {auth_token[:20]}...")
                    
                    headers = {"Authorization": f"Bearer {auth_token}"}
                    
                    # Get list of conversations
                    print("📋 Fetching conversation list...")
                    async with session.get(
                        "http://localhost:8000/api/chat/conversations",
                        headers=headers
                    ) as conv_response:
                        if conv_response.status == 200:
                            conversations = await conv_response.json()
                            print(f"✅ Found {len(conversations)} conversations:")
                            
                            for i, conv in enumerate(conversations):
                                print(f"  {i+1}. {conv.get('title', 'Untitled')} (ID: {conv['conversation_id'][:8]}...)")
                            
                            # Test loading history for the first conversation
                            if conversations:
                                first_conv_id = conversations[0]['conversation_id']
                                print(f"\n💬 Loading history for conversation: {conversations[0].get('title', 'Untitled')}")
                                
                                async with session.get(
                                    f"http://localhost:8000/api/chat/conversations/{first_conv_id}/history",
                                    headers=headers
                                ) as history_response:
                                    if history_response.status == 200:
                                        history = await history_response.json()
                                        print(f"✅ Loaded conversation history:")
                                        print(f"   - Title: {history.get('summary', {}).get('title', 'N/A')}")
                                        print(f"   - Message count: {len(history.get('messages', []))}")
                                        
                                        # Show first few messages
                                        messages = history.get('messages', [])
                                        for j, msg in enumerate(messages[:4]):  # Show first 4 messages
                                            role = msg['role'].upper()
                                            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                                            print(f"   - {role}: {content}")
                                        
                                        if len(messages) > 4:
                                            print(f"   - ... and {len(messages) - 4} more messages")
                                        
                                        print("\n🎉 Conversation history API is working correctly!")
                                        
                                    else:
                                        print(f"❌ Failed to load conversation history: {history_response.status}")
                                        error_text = await history_response.text()
                                        print(f"Error: {error_text}")
                            else:
                                print("⚠️ No conversations found to test history loading")
                                
                        else:
                            print(f"❌ Failed to fetch conversations: {conv_response.status}")
                            error_text = await conv_response.text()
                            print(f"Error: {error_text}")
                    
                else:
                    print(f"❌ Login failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(test_conversation_history())
