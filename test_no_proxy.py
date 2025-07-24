#!/usr/bin/env python3
"""
Test with proxy bypass for macOS environment.
"""

import urllib.request
import urllib.parse
import json
import os

def test_service_no_proxy():
    """Test service with proxy bypass."""
    
    # Temporarily disable proxy for localhost
    old_http_proxy = os.environ.get('http_proxy')
    old_https_proxy = os.environ.get('https_proxy')
    old_all_proxy = os.environ.get('all_proxy')
    
    try:
        # Clear proxy settings for localhost
        if 'http_proxy' in os.environ:
            del os.environ['http_proxy']
        if 'https_proxy' in os.environ:
            del os.environ['https_proxy']
        if 'all_proxy' in os.environ:
            del os.environ['all_proxy']
        
        print("🧪 Testing llmYTranslate Service (No Proxy)")
        print("=" * 50)
        
        # Test 1: Health Check
        print("\n1. Testing Health Endpoint...")
        try:
            url = "http://127.0.0.1:9000/api/health"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                print(f"   ✅ Health Status: {data['status']}")
                print(f"   📊 Services: {data['services']}")
        except Exception as e:
            print(f"   ❌ Health test failed: {e}")
        
        # Test 2: Demo Translation
        print("\n2. Testing Demo Translation...")
        try:
            url = "http://127.0.0.1:9000/api/demo/translate"
            data = urllib.parse.urlencode({
                'q': 'Hello world, how are you?',
                'from': 'en',
                'to': 'zh'
            }).encode()
            
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                print(f"   ✅ Translation successful!")
                print(f"   📝 Input: {result['request']['q']}")
                print(f"   🈯 Output: {result['response']['trans_result'][0]['dst']}")
        except Exception as e:
            print(f"   ❌ Translation test failed: {e}")
        
        # Test 3: Service Discovery
        print("\n3. Testing Service Discovery...")
        try:
            url = "http://127.0.0.1:9000/api/discovery/info"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                print(f"   ✅ Discovery working!")
                print(f"   🔍 Service: {data['service_name']}")
                print(f"   🌐 Mode: {data['deployment_mode']}")
        except Exception as e:
            print(f"   ❌ Discovery test failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")
        
    finally:
        # Restore proxy settings
        if old_http_proxy:
            os.environ['http_proxy'] = old_http_proxy
        if old_https_proxy:
            os.environ['https_proxy'] = old_https_proxy
        if old_all_proxy:
            os.environ['all_proxy'] = old_all_proxy

if __name__ == "__main__":
    test_service_no_proxy()
