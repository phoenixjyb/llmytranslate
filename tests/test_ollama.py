#!/usr/bin/env python3
"""
Direct test of Ollama connectivity from our application context.
"""

import asyncio
import httpx

async def test_ollama_direct():
    """Test Ollama connectivity directly."""
    try:
        # Test without proxy
        async with httpx.AsyncClient(
            base_url="http://localhost:11434",
            timeout=httpx.Timeout(30)
        ) as client:
            print("Testing /api/tags...")
            response = await client.get("/api/tags")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Models: {[m['name'] for m in data.get('models', [])]}")
                
                # Test a simple generation
                print("\nTesting generation...")
                gen_data = {
                    "model": "llava:latest",
                    "prompt": "Translate 'Hello world' to Chinese:",
                    "stream": False
                }
                
                gen_response = await client.post("/api/generate", json=gen_data)
                print(f"Generation status: {gen_response.status_code}")
                if gen_response.status_code == 200:
                    gen_result = gen_response.json()
                    print(f"Response: {gen_result.get('response', 'No response')}")
                else:
                    print(f"Generation error: {gen_response.text}")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_direct())
