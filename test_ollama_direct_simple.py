#!/usr/bin/env python3
"""
Simple test to verify Ollama is working with the requests library fix.
"""

import requests
import json

def test_ollama_direct():
    """Test Ollama API directly with requests library"""
    print("=== Testing Ollama API Directly ===")
    
    try:
        # Test the API that was failing before
        print("\n1. Testing /api/tags endpoint...")
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5.0)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"Models found: {len(models)}")
            for model in models:
                print(f"  - {model.get('name', 'Unknown')}")
        else:
            print(f"Error: {response.text}")
            
        # Test a simple chat completion
        print("\n2. Testing /api/generate endpoint...")
        chat_data = {
            "model": "llama3.1:8b",
            "prompt": "Hello! Please respond with just: Ollama is working!",
            "stream": False
        }
        
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json=chat_data,
            timeout=30.0
        )
        
        print(f"Chat Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data.get('response', 'No response')}")
        else:
            print(f"Chat Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama_direct()
