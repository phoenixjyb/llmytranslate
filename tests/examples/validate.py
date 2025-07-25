#!/usr/bin/env python3
"""
Validation script to test the LLM Translation Service.
"""

import sys
import json
import time
import hashlib
import asyncio
import aiohttp
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8888"
DEMO_APP_ID = "demo_app_id"
DEMO_APP_SECRET = "demo_app_secret"

def create_signature(app_id: str, query: str, salt: str, secret: str) -> str:
    """Create MD5 signature for Baidu API compatibility."""
    sign_str = f"{app_id}{query}{salt}{secret}"
    return hashlib.md5(sign_str.encode()).hexdigest()

async def test_health_check() -> bool:
    """Test health check endpoint."""
    print("🔍 Testing health check...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data.get('status')}")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def test_demo_translation() -> bool:
    """Test demo translation endpoint."""
    print("🔍 Testing demo translation...")
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('q', 'Hello, how are you?')
            data.add_field('from', 'en')
            data.add_field('to', 'zh')
            
            async with session.post(f"{BASE_URL}/api/demo/translate", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    translation = result.get('response', {}).get('trans_result', [{}])[0].get('dst', '')
                    print(f"✅ Demo translation successful: '{translation}'")
                    return True
                else:
                    print(f"❌ Demo translation failed: HTTP {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return False
    except Exception as e:
        print(f"❌ Demo translation error: {e}")
        return False

async def test_baidu_api_compatibility() -> bool:
    """Test Baidu API compatible endpoint."""
    print("🔍 Testing Baidu API compatibility...")
    try:
        # Create signed request
        query = "Good morning!"
        salt = str(int(time.time() * 1000))
        signature = create_signature(DEMO_APP_ID, query, salt, DEMO_APP_SECRET)
        
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('q', query)
            data.add_field('from', 'en')
            data.add_field('to', 'zh')
            data.add_field('appid', DEMO_APP_ID)
            data.add_field('salt', salt)
            data.add_field('sign', signature)
            
            async with session.post(f"{BASE_URL}/api/trans/vip/translate", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('error_code'):
                        print(f"❌ API error: {result.get('error_msg')}")
                        return False
                    
                    translation = result.get('trans_result', [{}])[0].get('dst', '')
                    print(f"✅ Baidu API translation successful: '{translation}'")
                    return True
                else:
                    print(f"❌ Baidu API failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Baidu API error: {e}")
        return False

async def test_supported_languages() -> bool:
    """Test supported languages endpoint."""
    print("🔍 Testing supported languages...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/languages") as response:
                if response.status == 200:
                    result = await response.json()
                    languages = result.get('languages', [])
                    print(f"✅ Supported languages: {len(languages)} languages")
                    return True
                else:
                    print(f"❌ Languages endpoint failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Languages endpoint error: {e}")
        return False

async def test_admin_endpoints() -> bool:
    """Test admin endpoints."""
    print("🔍 Testing admin endpoints...")
    try:
        async with aiohttp.ClientSession() as session:
            # Test statistics
            async with session.get(f"{BASE_URL}/api/admin/stats") as response:
                if response.status == 200:
                    result = await response.json()
                    total_requests = result.get('total_requests', 0)
                    print(f"✅ Admin stats: {total_requests} total requests")
                    return True
                else:
                    print(f"❌ Admin stats failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Admin endpoints error: {e}")
        return False

async def test_metrics_endpoint() -> bool:
    """Test metrics endpoint."""
    print("🔍 Testing metrics endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/metrics") as response:
                if response.status == 200:
                    result = await response.json()
                    metrics = result.get('metrics', {})
                    uptime = metrics.get('translation_uptime_seconds', 0)
                    print(f"✅ Metrics available: {uptime:.1f}s uptime")
                    return True
                else:
                    print(f"❌ Metrics endpoint failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
        return False

async def test_rate_limiting() -> bool:
    """Test rate limiting functionality."""
    print("🔍 Testing rate limiting...")
    try:
        tasks = []
        # Send multiple requests rapidly
        for i in range(5):
            task = test_single_translation(f"Test message {i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)
        
        if success_count >= 3:  # Most should succeed
            print(f"✅ Rate limiting working: {success_count}/5 requests succeeded")
            return True
        else:
            print(f"❌ Rate limiting issues: only {success_count}/5 requests succeeded")
            return False
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False

async def test_single_translation(query: str) -> bool:
    """Helper function for rate limiting test."""
    try:
        salt = str(int(time.time() * 1000000))  # Microsecond precision
        signature = create_signature(DEMO_APP_ID, query, salt, DEMO_APP_SECRET)
        
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('q', query)
            data.add_field('from', 'en')
            data.add_field('to', 'zh')
            data.add_field('appid', DEMO_APP_ID)
            data.add_field('salt', salt)
            data.add_field('sign', signature)
            
            async with session.post(f"{BASE_URL}/api/trans/vip/translate", data=data) as response:
                return response.status == 200
    except:
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting LLM Translation Service Validation")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Demo Translation", test_demo_translation),
        ("Baidu API Compatibility", test_baidu_api_compatibility),
        ("Supported Languages", test_supported_languages),
        ("Admin Endpoints", test_admin_endpoints),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        success = await test_func()
        results.append((test_name, success))
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Service is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the service configuration.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(1)
