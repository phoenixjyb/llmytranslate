#!/usr/bin/env python3
"""
Simple test to verify llmYTranslate service is working correctly.
"""

import requests
import json
import os

def test_service():
    """Test the llmYTranslate service endpoints."""
    base_url = "http://127.0.0.1:9002"
    
    # Disable proxy for localhost testing
    proxies = {
        'http': '',
        'https': ''
    }
    
    print("🧪 Testing llmYTranslate Service")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", proxies=proxies)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health Status: {health_data['status']}")
            print(f"   📊 Services: {health_data['services']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Demo Translation
    print("\n2. Testing Demo Translation...")
    try:
        translation_data = {
            "q": "Hello world, how are you?",
            "from": "en",
            "to": "zh"
        }
        
        response = requests.post(f"{base_url}/api/demo/translate", data=translation_data, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Translation successful!")
            print(f"   📝 Input: {result['request']['q']}")
            print(f"   🈯 Output: {result['response']['trans_result'][0]['dst']}")
        else:
            print(f"   ❌ Translation failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Translation error: {e}")
    
    # Test 3: Service Discovery
    print("\n3. Testing Service Discovery...")
    try:
        response = requests.get(f"{base_url}/api/discovery/info", proxies=proxies)
        if response.status_code == 200:
            info = response.json()
            print(f"   ✅ Discovery working!")
            print(f"   🔍 Service: {info['service_name']}")
            print(f"   🌐 Mode: {info['deployment_mode']}")
        else:
            print(f"   ❌ Discovery failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Discovery error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_service()
