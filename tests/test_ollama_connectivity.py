#!/usr/bin/env python3
"""Test Ollama connectivity and model availability."""

import asyncio
import httpx
import os

async def test_ollama():
    """Test Ollama connection and model."""
    
    # Test 1: Check if Ollama is running
    print("🔍 Testing Ollama connectivity...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/version")
            if response.status_code == 200:
                version_data = response.json()
                print(f"✅ Ollama is running: version {version_data.get('version', 'unknown')}")
            else:
                print(f"❌ Ollama responded with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False
    
    # Test 2: Check available models
    print("\n🔍 Checking available models...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                print(f"✅ Available models: {models}")
                
                if 'llama3.1:8b' in models:
                    print("✅ llama3.1:8b model is available")
                else:
                    print("❌ llama3.1:8b model not found")
                    return False
            else:
                print(f"❌ Failed to get models: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Failed to check models: {e}")
        return False
    
    # Test 3: Test generation
    print("\n🔍 Testing model generation...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "llama3.1:8b",
                "prompt": "Translate to Chinese: Hello",
                "stream": False
            }
            response = await client.post("http://localhost:11434/api/generate", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Generation successful: {result.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ Generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama())
    if success:
        print("\n🎉 All tests passed! Ollama is ready for translation.")
    else:
        print("\n❌ Some tests failed. Please check Ollama configuration.")
