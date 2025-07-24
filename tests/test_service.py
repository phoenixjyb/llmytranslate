#!/usr/bin/env python3
"""
Simple test script for the LLM Translation Service.
"""

import requests
import json

def test_health():
    """Test the health endpoint."""
    try:
        response = requests.get("http://127.0.0.1:8888/health")
        print(f"Health Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_translation():
    """Test the translation endpoint."""
    try:
        # Test with form data (Baidu API compatible)
        data = {
            "q": "Hello world",
            "from": "en", 
            "to": "zh"
        }
        
        response = requests.post(
            "http://127.0.0.1:8888/translate",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Translation Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Original: {data['q']}")
            print(f"Translated: {result.get('trans_result', [{}])[0].get('dst', 'No translation')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Translation test failed: {e}")
        return False

def test_api_docs():
    """Test if API documentation is accessible."""
    try:
        response = requests.get("http://127.0.0.1:8888/docs")
        print(f"API Docs Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"API docs test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing LLM Translation Service")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint...")
    health_ok = test_health()
    
    # Test API documentation
    print("\n2. Testing API Documentation...")
    docs_ok = test_api_docs()
    
    # Test translation
    print("\n3. Testing Translation...")
    translation_ok = test_translation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"✅ API Docs: {'PASS' if docs_ok else 'FAIL'}")
    print(f"✅ Translation: {'PASS' if translation_ok else 'FAIL'}")
    
    if all([health_ok, docs_ok, translation_ok]):
        print("\n🎉 All tests passed! Your LLM Translation Service is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
