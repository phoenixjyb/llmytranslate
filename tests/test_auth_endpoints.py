#!/usr/bin/env python3
"""
Test the /auth endpoint fix
"""
import requests

def test_auth_endpoints():
    """Test both /auth and /auth.html endpoints"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing auth endpoints...")
    
    # Test /auth endpoint
    print("📄 Testing /auth endpoint...")
    auth_response = requests.get(f"{base_url}/auth")
    
    if auth_response.status_code == 200:
        print("✅ /auth endpoint working!")
        print(f"   - Status: {auth_response.status_code}")
        print(f"   - Content type: {auth_response.headers.get('content-type', 'N/A')}")
        print(f"   - Content length: {len(auth_response.text)} characters")
    else:
        print(f"❌ /auth endpoint failed: {auth_response.status_code}")
        print(f"   Response: {auth_response.text}")
    
    # Test /auth.html endpoint
    print("📄 Testing /auth.html endpoint...")
    auth_html_response = requests.get(f"{base_url}/auth.html")
    
    if auth_html_response.status_code == 200:
        print("✅ /auth.html endpoint working!")
        print(f"   - Status: {auth_html_response.status_code}")
        print(f"   - Content type: {auth_html_response.headers.get('content-type', 'N/A')}")
        print(f"   - Content length: {len(auth_html_response.text)} characters")
    else:
        print(f"❌ /auth.html endpoint failed: {auth_html_response.status_code}")
        print(f"   Response: {auth_html_response.text}")
    
    # Compare content to ensure they're the same
    if auth_response.status_code == 200 and auth_html_response.status_code == 200:
        if auth_response.text == auth_html_response.text:
            print("✅ Both endpoints serve identical content!")
        else:
            print("⚠️ Endpoints serve different content")
            print(f"   /auth length: {len(auth_response.text)}")
            print(f"   /auth.html length: {len(auth_html_response.text)}")
    
    # Test that content includes expected elements
    if auth_response.status_code == 200:
        content = auth_response.text.lower()
        checks = [
            ("title tag", "user account" in content),
            ("login form", "login" in content),
            ("register form", "register" in content),
            ("guest access", "guest" in content),
            ("user-auth.js", "user-auth.js" in content)
        ]
        
        print("🔍 Content validation:")
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}: {'Found' if result else 'Not found'}")
    
    print("🎉 Auth endpoint testing complete!")

if __name__ == "__main__":
    try:
        test_auth_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
