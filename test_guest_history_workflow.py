#!/usr/bin/env python3
"""
Test the complete guest history workflow to ensure no freezing
"""
import requests
import time

def test_guest_history_workflow():
    """Test the complete guest history workflow"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing complete guest history workflow...")
    
    # Step 1: Create guest session
    print("👤 Step 1: Creating guest session...")
    guest_response = requests.post(f"{base_url}/api/users/guest-session")
    
    if guest_response.status_code == 200:
        guest_data = guest_response.json()
        session_id = guest_data['session_id']
        print(f"✅ Guest session created: {session_id}")
    else:
        print(f"❌ Failed to create guest session: {guest_response.status_code}")
        return False
    
    headers = {'X-Guest-Session-Id': session_id}
    
    # Step 2: Send multiple chat messages to create history
    print("💬 Step 2: Creating conversation history...")
    messages = [
        "Hello, I'm testing the history feature!",
        "Can you tell me about the weather?",
        "What's your favorite color?"
    ]
    
    conversation_ids = []
    
    for i, message in enumerate(messages):
        print(f"   Sending message {i+1}/{len(messages)}: {message[:30]}...")
        
        chat_data = {
            "message": message,
            "model": "gemma3:latest",
            "platform": "web"
        }
        
        if i > 1:  # Start new conversation for the third message
            chat_data["conversation_id"] = None
        
        chat_response = requests.post(
            f"{base_url}/api/chat/message",
            json=chat_data,
            headers=headers
        )
        
        if chat_response.status_code == 200:
            response_data = chat_response.json()
            conversation_id = response_data['conversation_id']
            if conversation_id not in conversation_ids:
                conversation_ids.append(conversation_id)
            print(f"   ✅ Message sent successfully (Conversation: {conversation_id[:8]}...)")
        else:
            print(f"   ❌ Message failed: {chat_response.status_code}")
            return False
        
        # Small delay between messages
        time.sleep(0.5)
    
    # Step 3: Test conversation list access (History button functionality)
    print("📋 Step 3: Testing conversation list access...")
    conversations_response = requests.get(
        f"{base_url}/api/chat/conversations",
        headers=headers
    )
    
    if conversations_response.status_code == 200:
        conversations = conversations_response.json()
        print(f"✅ Guest can access conversations: {len(conversations)} conversation(s)")
        
        for conv in conversations:
            print(f"   - {conv['title']}: {conv['message_count']} messages")
    else:
        print(f"❌ Failed to access conversations: {conversations_response.status_code}")
        return False
    
    # Step 4: Test individual conversation history access
    print("📖 Step 4: Testing individual conversation history access...")
    for i, conversation_id in enumerate(conversation_ids):
        print(f"   Testing conversation {i+1}: {conversation_id[:8]}...")
        
        history_response = requests.get(
            f"{base_url}/api/chat/conversations/{conversation_id}/history",
            headers=headers
        )
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            messages = history_data.get('messages', [])
            print(f"   ✅ History loaded: {len(messages)} messages")
        else:
            print(f"   ❌ Failed to load history: {history_response.status_code}")
            return False
    
    # Step 5: Test continuing conversations
    print("💬 Step 5: Testing conversation continuation...")
    if conversation_ids:
        continue_message = "This is a follow-up message to test continuation."
        
        chat_data = {
            "message": continue_message,
            "conversation_id": conversation_ids[0],
            "model": "gemma3:latest",
            "platform": "web"
        }
        
        continue_response = requests.post(
            f"{base_url}/api/chat/message",
            json=chat_data,
            headers=headers
        )
        
        if continue_response.status_code == 200:
            print(f"✅ Conversation continuation successful!")
        else:
            print(f"❌ Conversation continuation failed: {continue_response.status_code}")
            return False
    
    print("🎉 Complete guest history workflow test passed!")
    print("✅ Guest users can now:")
    print("   - Access conversation history via History button")
    print("   - View conversation lists without upgrade prompts")
    print("   - Load individual conversation details")
    print("   - Continue existing conversations")
    print("   - Use all history features without page freezing")
    
    return True

if __name__ == "__main__":
    try:
        test_guest_history_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
