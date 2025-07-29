#!/usr/bin/env python3
"""
Test Ollama client methods directly to verify full functionality after the httpx→requests fix.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.ollama_client import ollama_client

async def test_ollama():
    print("=== Testing Ollama LLM Integration ===")
    
    # Test health check
    print("\n1. Testing health check...")
    health = await ollama_client.health_check()
    print(f"Health check result: {health}")
    
    # Test list models
    print("\n2. Testing list models...")
    models = await ollama_client.list_models()
    print(f"Available models: {models}")
    
    # Test chat completion
    print("\n3. Testing chat completion...")
    try:
        response = await ollama_client.chat_completion(
            message="Hello! Please respond with just: Ollama is working!",
            model="llama3.1:8b"
        )
        print(f"Chat completion test: {response}")
    except Exception as e:
        print(f"Chat completion error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
