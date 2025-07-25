#!/usr/bin/env python3
"""
Quick test using urllib instead of requests to avoid potential issues.
"""

import urllib.request
import urllib.parse
import json

def test_health():
    """Test health endpoint with urllib."""
    try:
        url = "http://127.0.0.1:9000/api/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print(f"✅ Health Status: {data['status']}")
            print(f"📊 Services: {data['services']}")
            return True
    except Exception as e:
        print(f"❌ Health test failed: {e}")
        return False

def test_demo_translation():
    """Test demo translation with urllib."""
    try:
        url = "http://127.0.0.1:9000/api/demo/translate"
        data = urllib.parse.urlencode({
            'q': 'Hello world',
            'from': 'en',
            'to': 'zh'
        }).encode()
        
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Translation successful!")
            print(f"📝 Input: {result['request']['q']}")
            print(f"🈯 Output: {result['response']['trans_result'][0]['dst']}")
            return True
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Quick Test with urllib")
    print("=" * 40)
    
    print("\n1. Testing Health...")
    test_health()
    
    print("\n2. Testing Translation...")
    test_demo_translation()
    
    print("\n✅ Test completed!")
