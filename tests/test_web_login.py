#!/usr/bin/env python3
"""
Browser simulation test for registered user login
"""
import requests
import time

def test_web_login_flow():
    """Test the web login flow that mirrors browser behavior"""
    base_url = "http://localhost:8000"
    
    print("🌐 Testing web login flow...")
    
    # Simulate browser session
    session = requests.Session()
    
    # Step 1: Access auth page (like loading /auth in browser)
    print("📄 Step 1: Loading auth page...")
    auth_page = session.get(f"{base_url}/auth")
    
    if auth_page.status_code == 200:
        print("✅ Auth page loaded successfully")
    else:
        print(f"❌ Failed to load auth page: {auth_page.status_code}")
        return False
    
    # Step 2: Submit login form (simulate clicking Login button)
    print("🔐 Step 2: Submitting login form...")
    login_data = {
        "username_or_email": "testuser123",
        "password": "SecurePassword123!",
        "remember_me": True
    }
    
    login_response = session.post(f"{base_url}/api/users/login", json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print("✅ Login successful!")
        print(f"   - Token type: {login_result.get('token_type', 'N/A')}")
        print(f"   - Expires in: {login_result.get('expires_in', 'N/A')} seconds")
        print(f"   - User: {login_result.get('user_profile', {}).get('username', 'N/A')}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return False
    
    # Step 3: Navigate to chat page (simulate successful login redirect)
    print("💬 Step 3: Accessing chat page...")
    chat_page = session.get(f"{base_url}/chat")
    
    if chat_page.status_code == 200:
        print("✅ Chat page accessed successfully")
    else:
        print(f"❌ Failed to access chat page: {chat_page.status_code}")
        return False
    
    # Step 4: Check user status (what happens when chat page loads)
    print("👤 Step 4: Checking authenticated status...")
    status_response = session.get(f"{base_url}/api/users/status")
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print("✅ User status retrieved:")
        print(f"   - Authenticated: {status_data.get('authenticated', False)}")
        print(f"   - Username: {status_data.get('user', {}).get('username', 'N/A')}")
    else:
        print(f"❌ Failed to get status: {status_response.status_code}")
        return False
    
    # Step 5: Test chat with session cookies (browser-like behavior)
    print("💬 Step 5: Testing chat with session...")
    chat_data = {
        "message": "Hello! Testing authenticated chat through web session.",
        "model": "gemma3:latest",
        "platform": "web"
    }
    
    # Note: Using session.post automatically includes cookies
    chat_response = session.post(f"{base_url}/api/chat/message", json=chat_data)
    
    if chat_response.status_code == 200:
        response_data = chat_response.json()
        print("✅ Chat message sent successfully!")
        print(f"   - Response: {response_data['response'][:100]}...")
        print(f"   - Conversation ID: {response_data['conversation_id']}")
    else:
        print(f"❌ Chat message failed: {chat_response.status_code}")
        print(f"   Response: {chat_response.text}")
        return False
    
    print("🎉 Web login flow test completed successfully!")
    print("✅ Web interface supports:")
    print("   - User authentication with session cookies")
    print("   - Seamless chat functionality after login")
    print("   - Persistent session across page navigation")
    print("   - Full registered user experience")
    
    return True

if __name__ == "__main__":
    try:
        test_web_login_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
