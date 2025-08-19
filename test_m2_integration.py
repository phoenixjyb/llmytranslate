#!/usr/bin/env python3
"""
M2 MacBook Integration Test
Quick test to verify ollama integration with your available models
"""

import asyncio
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_m2_integration():
    """Test M2 MacBook integration with available models"""
    
    print("🍎 M2 MacBook Integration Test")
    print("=" * 50)
    
    try:
        # Import the ollama client from your existing code
        from src.services.ollama_client import ollama_client
        
        # Test health check first
        print("\n1. Testing Ollama Health Check...")
        health_result = await ollama_client.health_check()
        print(f"✅ Health: {health_result}")
        
        # Test listing models
        print("\n2. Testing Model List...")
        models_result = await ollama_client.list_models()
        print(f"✅ Models: {models_result}")
        
        # Test your available models with translation
        available_models = ['gemma3:270m', 'gemma2:2b']
        test_text = "Hello world"
        
        for model in available_models:
            print(f"\n3. Testing {model}...")
            start_time = time.time()
            
            try:
                result = await ollama_client.generate_translation(
                    text=test_text,
                    source_lang="en",
                    target_lang="zh",
                    model_name=model
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if result.get("success"):
                    print(f"   ✅ Model: {model}")
                    print(f"   ⏱️  Time: {duration:.2f}s")
                    print(f"   📝 Translation: {result.get('translation', 'N/A')}")
                else:
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print(f"\n🎯 M2 Integration Test Complete")
        print("=" * 50)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Suggestion: Ensure you're in the correct environment")
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_m2_integration())
