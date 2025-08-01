#!/usr/bin/env python3
"""Quick test to check if the service is running and health endpoint works."""

import requests
import json

def test_health_endpoint():
    """Test the health endpoint."""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Service is running!")
            print(f"Status: {data.get('status')}")
            print(f"Version: {data.get('version')}")
            print(f"Phase 4 Optimizations: {data.get('optimizations', {})}")
        else:
            print("❌ Service returned error status")
            
    except requests.exceptions.ConnectionError:
        print("❌ Service is not running - connection refused")
    except requests.exceptions.Timeout:
        print("❌ Service is not responding - timeout")
    except Exception as e:
        print(f"❌ Error testing service: {e}")

if __name__ == "__main__":
    print("Testing LLMyTranslate service health endpoint...")
    test_health_endpoint()
