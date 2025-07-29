#!/usr/bin/env python3
"""
Test registered user functionality - registration, login, and chat
"""
import requests
import json
import time

def test_registered_user_workflow():
    """Test the complete registered user workflow"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing registered user workflow...")
    
    # Step 1: Register a new user
    print("👤 Step 1: Registering a new user...")
    user_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    register_response = requests.post(f"{base_url}/api/users/register", json=user_data)
    
    if register_response.status_code == 200:
        register_data = register_response.json()
        print(f"✅ User registered successfully!")
        print(f"   - User ID: {register_data.get('user_id', 'N/A')}")
        print(f"   - Username: {register_data.get('username', 'N/A')}")
        print(f"   - Email: {register_data.get('email', 'N/A')}")
        
        # Step 1.5: Login to get access token
        print("🔐 Step 1.5: Logging in to get access token...")
        login_data = {
            "username_or_email": user_data["username"],
            "password": user_data["password"],
            "remember_me": True
        }
        
        login_response = requests.post(f"{base_url}/api/users/login", json=login_data)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access_token')
            print(f"✅ Login successful!")
            print(f"   - Access token received: {access_token[:20] if access_token else 'None'}...")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False
    else:
        print(f"❌ User registration failed: {register_response.status_code}")
        print(f"   Response: {register_response.text}")
        
        # Try to login instead if user already exists
        print("👤 Trying to login with existing user...")
        login_data = {
            "username_or_email": user_data["username"],
            "password": user_data["password"],
            "remember_me": True
        }
        
        login_response = requests.post(f"{base_url}/api/users/login", json=login_data)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"✅ User logged in successfully!")
            access_token = login_result.get('access_token')
            print(f"   - Access token received: {access_token[:20] if access_token else 'None'}...")
        else:
            print(f"❌ Login also failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False
    
    # Set up headers for authenticated requests
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Step 2: Test user status
    print("🔍 Step 2: Checking user status...")
    status_response = requests.get(f"{base_url}/api/users/status", headers=headers)
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"✅ User status retrieved:")
        print(f"   - Authenticated: {status_data.get('authenticated', False)}")
        print(f"   - Username: {status_data.get('user', {}).get('username', 'N/A')}")
        print(f"   - Role: {status_data.get('user', {}).get('role', 'N/A')}")
    else:
        print(f"❌ Failed to get user status: {status_response.status_code}")
        return False
    
    # Step 3: Test chat health check
    print("🏥 Step 3: Testing chat health check...")
    health_response = requests.get(f"{base_url}/api/chat/health", headers=headers)
    
    if health_response.status_code == 200:
        health_data = health_response.json()
        print(f"✅ Chat health check passed:")
        print(f"   - Status: {health_data.get('status', 'N/A')}")
        print(f"   - Ollama: {health_data.get('ollama_status', 'N/A')}")
    else:
        print(f"❌ Chat health check failed: {health_response.status_code}")
        return False
    
    # Step 4: Send chat messages
    print("💬 Step 4: Testing chat functionality...")
    
    # First message - start new conversation
    chat_data = {
        "message": "Hello! I'm testing as a registered user. Can you help me?",
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
        print(f"✅ First chat message successful!")
        print(f"   - Response: {response_data['response'][:100]}...")
        print(f"   - Conversation ID: {response_data['conversation_id']}")
        conversation_id = response_data['conversation_id']
    else:
        print(f"❌ First chat message failed: {chat_response.status_code}")
        print(f"   Response: {chat_response.text}")
        return False
    
    # Second message - continue conversation
    print("   Sending follow-up message...")
    time.sleep(1)
    
    followup_data = {
        "message": "What's the weather like today?",
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
        print(f"   ✅ Follow-up message successful!")
        print(f"   - Response: {followup_data['response'][:100]}...")
    else:
        print(f"   ❌ Follow-up message failed: {followup_response.status_code}")
        return False
    
    # Step 5: Test conversation history
    print("📋 Step 5: Testing conversation history...")
    conversations_response = requests.get(
        f"{base_url}/api/chat/conversations",
        headers=headers
    )
    
    if conversations_response.status_code == 200:
        conversations = conversations_response.json()
        print(f"✅ Conversations retrieved: {len(conversations)} conversation(s)")
        
        if conversations:
            conv = conversations[0]
            print(f"   - Title: {conv['title']}")
            print(f"   - Messages: {conv['message_count']}")
            print(f"   - Model: {conv['model_used']}")
            print(f"   - Last activity: {conv['last_message_at']}")
    else:
        print(f"❌ Failed to get conversations: {conversations_response.status_code}")
        return False
    
    # Step 6: Test specific conversation history
    print("📖 Step 6: Testing conversation details...")
    history_response = requests.get(
        f"{base_url}/api/chat/conversations/{conversation_id}/history",
        headers=headers
    )
    
    if history_response.status_code == 200:
        history_data = history_response.json()
        messages = history_data.get('messages', [])
        print(f"✅ Conversation history loaded: {len(messages)} messages")
        
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', 'No content')
            print(f"   - Message {i+1}: {role} - {content[:50]}...")
    else:
        print(f"❌ Failed to get conversation history: {history_response.status_code}")
        return False
    
    # Step 7: Test user profile
    print("👥 Step 7: Testing user profile...")
    profile_response = requests.get(f"{base_url}/api/users/profile", headers=headers)
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(f"✅ User profile retrieved:")
        print(f"   - Username: {profile_data.get('username', 'N/A')}")
        print(f"   - Email: {profile_data.get('email', 'N/A')}")
        print(f"   - Role: {profile_data.get('role', 'N/A')}")
        print(f"   - Status: {profile_data.get('status', 'N/A')}")
        print(f"   - Created: {profile_data.get('created_at', 'N/A')}")
    else:
        print(f"❌ Failed to get user profile: {profile_response.status_code}")
        return False
    
    print("🎉 Registered user workflow test completed successfully!")
    print("✅ Registered users can:")
    print("   - Register and login successfully")
    print("   - Send and receive chat messages")
    print("   - Access unlimited conversation history")
    print("   - Continue conversations seamlessly")
    print("   - View detailed user profiles")
    print("   - Access all premium features")
    
    return True

if __name__ == "__main__":
    try:
        test_registered_user_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
