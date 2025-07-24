#!/usr/bin/env python3
"""
Simple direct test for the translation service.
"""

import httpx
import asyncio

async def test_simple():
    """Simple test of the service."""
    async with httpx.AsyncClient() as client:
        try:
            # Test health
            print("Testing health endpoint...")
            health_response = await client.get("http://127.0.0.1:8888/health")
            print(f"Health: {health_response.status_code} - {health_response.text}")
            
            # Test translation
            print("\nTesting translation...")
            translation_data = {
                "q": "Hello world",
                "from": "en",
                "to": "zh"
            }
            
            translation_response = await client.post(
                "http://127.0.0.1:8888/translate",
                data=translation_data
            )
            print(f"Translation: {translation_response.status_code}")
            if translation_response.status_code == 200:
                print(f"Result: {translation_response.json()}")
            else:
                print(f"Error: {translation_response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())
