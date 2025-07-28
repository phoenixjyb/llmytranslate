#!/usr/bin/env python3
"""
Test guest session functionality.
"""

import asyncio
import aiohttp
import json

async def test_guest_session():
    """Test guest session creation and usage."""
    
    print("🔄 Testing guest session functionality...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Create guest session
            print("👤 Creating guest session...")
            async with session.post("http://localhost:8000/api/users/guest-session") as response:
                if response.status == 200:
                    guest_data = await response.json()
                    guest_session_id = guest_data.get("session_id")
                    print(f"✅ Guest session created: {guest_session_id}")
                    
                    # Test guest access to chat
                    headers = {"X-Guest-Session-Id": guest_session_id}
                    
                    print("💬 Testing guest chat access...")
                    async with session.get("http://localhost:8000/api/users/status", headers=headers) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            print(f"✅ Guest status check successful:")
                            print(f"   - Is guest: {status_data.get('is_guest')}")
                            print(f"   - Session ID: {status_data.get('session_id')}")
                            print(f"   - Authenticated: {status_data.get('authenticated')}")
                        else:
                            print(f"❌ Guest status check failed: {status_response.status}")
                    
                    # Test guest chat health
                    print("🏥 Testing guest chat health...")
                    async with session.get("http://localhost:8000/api/chat/health", headers=headers) as health_response:
                        if health_response.status == 200:
                            health_data = await health_response.json()
                            print(f"✅ Guest chat health check successful: {health_data.get('status')}")
                        else:
                            print(f"❌ Guest chat health failed: {health_response.status}")
                    
                    # Test guest conversation list
                    print("📋 Testing guest conversation list...")
                    async with session.get("http://localhost:8000/api/chat/conversations", headers=headers) as conv_response:
                        if conv_response.status == 200:
                            conversations = await conv_response.json()
                            print(f"✅ Guest conversations retrieved: {len(conversations)} conversations")
                        else:
                            print(f"❌ Guest conversations failed: {conv_response.status}")
                            error_text = await conv_response.text()
                            print(f"Error: {error_text}")
                    
                    print("\n🎉 Guest session testing complete!")
                    
                else:
                    print(f"❌ Guest session creation failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_guest_session())
