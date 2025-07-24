#!/usr/bin/env python3
"""
Simple test to verify our translation API works with a mock response.
"""

import requests

def test_with_mock():
    """Test the service with a mock response."""
    
    # Get signature
    sig_response = requests.get(
        "http://127.0.0.1:8888/api/demo/signature",
        params={"q": "Hello", "from_lang": "en", "to_lang": "zh"},
        proxies={"http": None, "https": None}
    )
    
    if sig_response.status_code == 200:
        sig_data = sig_response.json()
        params = sig_data["parameters"]
        
        print("🧪 Testing translation with signature:")
        print(f"Parameters: {params}")
        
        # Test translation
        trans_response = requests.post(
            "http://127.0.0.1:8888/api/trans/vip/translate",
            data={
                "q": params["q"],
                "from": params["from"], 
                "to": params["to"],
                "appid": params["appid"],
                "salt": params["salt"],
                "sign": params["sign"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            proxies={"http": None, "https": None}
        )
        
        print(f"Translation Status: {trans_response.status_code}")
        print(f"Response: {trans_response.text}")
        
        if trans_response.status_code == 200:
            result = trans_response.json()
            if result.get("error_code"):
                print(f"❌ Error: {result.get('error_msg')}")
            else:
                print("✅ Translation successful!")
                for item in result.get("trans_result", []):
                    print(f"   {item.get('src')} → {item.get('dst')}")
        else:
            print(f"❌ HTTP Error: {trans_response.status_code}")
    else:
        print(f"❌ Failed to get signature: {sig_response.status_code}")

if __name__ == "__main__":
    test_with_mock()
