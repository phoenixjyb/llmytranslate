#!/usr/bin/env python3
"""
Complete end-to-end test of guest functionality including the web interface flow
"""
import requests
import json
import sys

def test_complete_guest_flow():
    """Test the complete guest user flow"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing complete guest user flow...")
    
    # Step 1: Create guest session (simulates clicking "Try as Guest")
    print("👤 Step 1: Creating guest session...")
    guest_response = requests.post(f"{base_url}/api/users/guest-session")
    
    if guest_response.status_code == 200:
        guest_data = guest_response.json()
        session_id = guest_data['session_id']
        print(f"✅ Guest session created: {session_id}")
    else:
        print(f"❌ Failed to create guest session: {guest_response.status_code}")
        return False
    
    # Step 2: Test health check with guest session
    print("🏥 Step 2: Testing health check...")
    headers = {'X-Guest-Session-Id': session_id}
    health_response = requests.get(f"{base_url}/api/health", headers=headers)
    
    if health_response.status_code == 200:
        print("✅ Health check passed")
    else:
        print(f"❌ Health check failed: {health_response.status_code}")
        return False
    
    # Step 3: Send chat message (simulates typing and sending message)
    print("💬 Step 3: Sending chat message...")
    chat_data = {
        "message": "Hello! I'm testing the guest chat feature. Can you respond?",
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
        print(f"   - Response: {response_data['response'][:100]}...")
        print(f"   - Conversation ID: {response_data['conversation_id']}")
        conversation_id = response_data['conversation_id']
    else:
        print(f"❌ Chat message failed: {chat_response.status_code}")
        print(f"   Response: {chat_response.text}")
        return False
    
    # Step 4: Get conversation history (simulates loading chat history)
    print("📜 Step 4: Getting conversation history...")
    conversations_response = requests.get(
        f"{base_url}/api/chat/conversations",
        headers=headers
    )
    
    if conversations_response.status_code == 200:
        conversations = conversations_response.json()
        print(f"✅ Conversations retrieved: {len(conversations)} found")
        if conversations:
            print(f"   - Latest conversation: {conversations[0]['title']}")
            print(f"   - Message count: {conversations[0]['message_count']}")
    else:
        print(f"❌ Failed to get conversations: {conversations_response.status_code}")
        return False
    
    # Step 5: Get specific conversation messages
    print("📖 Step 5: Getting conversation messages...")
    messages_response = requests.get(
        f"{base_url}/api/chat/conversations/{conversation_id}/history",
        headers=headers
    )
    
    if messages_response.status_code == 200:
        history_data = messages_response.json()
        messages = history_data.get('messages', [])
        print(f"✅ Messages retrieved: {len(messages)} messages")
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', 'No content')
            print(f"   - Message {i+1}: {role} - {content[:50]}...")
    else:
        print(f"❌ Failed to get messages: {messages_response.status_code}")
        return False
    
    # Step 6: Send follow-up message
    print("💬 Step 6: Sending follow-up message...")
    followup_data = {
        "message": "Great! Can you tell me what features are available?",
        "conversation_id": conversation_id,
        "model": "gemma3:latest",
        "platform": "web"
    }
    
    followup_response = requests.post(
        f"{base_url}/api/chat/message",
        json=followup_data,
        headers=headers
    )
    
    if followup_response.status_code == 200:
        followup_data = followup_response.json()
        print(f"✅ Follow-up message successful!")
        print(f"   - Response: {followup_data['response'][:100]}...")
    else:
        print(f"❌ Follow-up message failed: {followup_response.status_code}")
        return False
    
    print("🎉 Complete guest flow test passed!")
    print("✅ Guest users can:")
    print("   - Create sessions via 'Try as Guest' button")
    print("   - Send and receive chat messages")
    print("   - View conversation history")
    print("   - Continue conversations")
    print("   - Access all chat features without registration")
    
    return True

if __name__ == "__main__":
    try:
        success = test_complete_guest_flow()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
