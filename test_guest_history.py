#!/usr/bin/env python3
"""
Test guest history functionality to reproduce the freezing issue
"""
import requests
import time

def test_guest_history_flow():
    """Test the guest history button clicking flow"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing guest history flow...")
    
    # Step 1: Create guest session
    print("👤 Creating guest session...")
    guest_response = requests.post(f"{base_url}/api/users/guest-session")
    
    if guest_response.status_code == 200:
        guest_data = guest_response.json()
        session_id = guest_data['session_id']
        print(f"✅ Guest session created: {session_id}")
    else:
        print(f"❌ Failed to create guest session: {guest_response.status_code}")
        return False
    
    # Step 2: Send a chat message first
    print("💬 Sending initial chat message...")
    headers = {'X-Guest-Session-Id': session_id}
    chat_data = {
        "message": "Hello! Test message for history",
        "model": "gemma3:latest",
        "platform": "web"
    }
    
    chat_response = requests.post(
        f"{base_url}/api/chat/message",
        json=chat_data,
        headers=headers
    )
    
    if chat_response.status_code == 200:
        response_data = chat_response.json()
        print(f"✅ Chat message successful!")
        conversation_id = response_data['conversation_id']
    else:
        print(f"❌ Chat message failed: {chat_response.status_code}")
        return False
    
    # Step 3: Try to access conversations as guest (what happens when clicking History)
    print("📋 Testing guest conversations access (simulating History button)...")
    conversations_response = requests.get(
        f"{base_url}/api/chat/conversations",
        headers=headers
    )
    
    if conversations_response.status_code == 200:
        conversations = conversations_response.json()
        print(f"✅ Guest can access conversations: {len(conversations)} found")
        
        # Step 4: Try to load conversation history
        if conversations:
            conversation_id = conversations[0]['conversation_id']
            print(f"📖 Testing conversation history access...")
            
            history_response = requests.get(
                f"{base_url}/api/chat/conversations/{conversation_id}/history",
                headers=headers
            )
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                print(f"✅ Guest can access conversation history: {len(history_data.get('messages', []))} messages")
            else:
                print(f"❌ Guest cannot access conversation history: {history_response.status_code}")
                print(f"   Response: {history_response.text}")
                return False
        
    else:
        print(f"⚠️ Guest conversations access: {conversations_response.status_code}")
        print(f"   Response: {conversations_response.text}")
        print("   This might be expected behavior for guests")
    
    print("🎉 Guest history flow test completed!")
    return True

if __name__ == "__main__":
    try:
        test_guest_history_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
