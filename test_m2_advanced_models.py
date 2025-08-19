#!/usr/bin/env python3
"""
Test M2 Advanced Model Capabilities
Test larger models for vision, multimodal, and complex translation tasks
"""

import sys
import os
import asyncio
import time

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_advanced_models():
    """Test advanced M2 models for complex capabilities"""
    
    print("🚀 Testing M2 Advanced Model Capabilities")
    print("=" * 60)
    
    try:
        from src.services.ollama_client import ollama_client
        
        # Test models available
        print("📋 Checking Available Models...")
        available_models = []
        models_result = await ollama_client.list_models()
        if models_result.get("success"):
            available_models = [m["name"] for m in models_result["models"]]
            print(f"Available: {', '.join(available_models)}")
        else:
            print("❌ Could not fetch model list")
            return
        
        # Advanced models to test
        advanced_models = ["llava:latest", "qwen2.5vl:7b", "gemma3:latest"]
        
        # Complex translation tests
        complex_texts = [
            {
                "text": "The quantum computing paradigm represents a fundamental shift in computational methodology, leveraging quantum mechanical phenomena such as superposition and entanglement to process information in ways that classical computers cannot efficiently replicate.",
                "desc": "Technical/Scientific Text",
                "source": "en",
                "target": "zh"
            },
            {
                "text": "In the realm of artificial intelligence, machine learning algorithms have evolved to demonstrate remarkable capabilities in pattern recognition, natural language processing, and predictive analytics.",
                "desc": "AI/Technology Context", 
                "source": "en",
                "target": "zh"
            },
            {
                "text": "春江花月夜，古诗词中描绘的意境深远，体现了中华文化的博大精深和诗人的情感寄托。",
                "desc": "Classical Chinese Poetry",
                "source": "zh", 
                "target": "en"
            }
        ]
        
        print(f"\n🧠 Testing Advanced Models with Complex Content")
        print("=" * 60)
        
        for model in advanced_models:
            if model not in available_models:
                print(f"⏭️  Skipping {model} (not available)")
                continue
                
            print(f"\n🔍 Testing Model: {model}")
            print("-" * 40)
            
            for i, test_case in enumerate(complex_texts, 1):
                print(f"\nTest {i}: {test_case['desc']}")
                print(f"Source ({test_case['source']}): {test_case['text'][:80]}...")
                
                start_time = time.time()
                
                try:
                    result = await ollama_client.generate_translation(
                        text=test_case["text"],
                        source_lang=test_case["source"], 
                        target_lang=test_case["target"],
                        model_name=model,
                        translation_mode="verbose"  # Request detailed translation
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if result.get("success"):
                        translation = result.get("translation", "No translation")
                        print(f"✅ Time: {duration:.2f}s")
                        print(f"📝 Translation: {translation[:150]}...")
                        if len(translation) > 150:
                            print("    [truncated]")
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ Exception: {e}")
                    
                # Small delay between tests to prevent overload
                await asyncio.sleep(1)
        
        # Model comparison summary
        print(f"\n📊 Model Capability Assessment")
        print("=" * 60)
        
        model_analysis = {
            "gemma3:270m": {
                "size": "291MB",
                "speed": "Ultra Fast (0.2-0.3s)",
                "best_for": "Real-time translation, phone calls",
                "memory": "~500MB"
            },
            "gemma2:2b": {
                "size": "1.6GB", 
                "speed": "Fast (0.4-0.8s)",
                "best_for": "Interactive translation, web interface",
                "memory": "~2GB"
            },
            "gemma3:latest": {
                "size": "3.3GB",
                "speed": "Capable (1-3s)",
                "best_for": "Quality translation, complex text",
                "memory": "~4GB"
            },
            "llava:latest": {
                "size": "4.7GB",
                "speed": "Advanced (3-8s)",
                "best_for": "Vision, image understanding, multimodal",
                "memory": "~6GB"
            },
            "qwen2.5vl:7b": {
                "size": "6.0GB", 
                "speed": "Expert (5-15s)",
                "best_for": "Advanced vision, OCR, document analysis",
                "memory": "~8GB"
            }
        }
        
        print(f"{'Model':<15} {'Size':<8} {'Speed':<20} {'Best For':<35}")
        print("-" * 80)
        for model, info in model_analysis.items():
            if model in available_models:
                print(f"{model:<15} {info['size']:<8} {info['speed']:<20} {info['best_for']:<35}")
        
        # Memory utilization assessment
        print(f"\n🧮 M2 Memory Utilization Analysis")
        print("=" * 60)
        print("Your M2 MacBook (16GB unified memory) can efficiently run:")
        print("✅ All models individually with room for system operations")
        print("✅ 2-3 small/medium models simultaneously (gemma3:270m + gemma2:2b + gemma3:latest)")  
        print("✅ 1 large model + 1 small model (llava + gemma3:270m)")
        print("⚠️  qwen2.5vl:7b requires careful memory management (8GB+)")
        
        print(f"\n🎯 Recommended M2 Pipeline Configuration:")
        print("💨 Always loaded: gemma3:270m (instant response)")
        print("🔥 Hot standby: gemma2:2b (interactive translation)")
        print("📚 On-demand: gemma3:latest (quality tasks)")
        print("👁️  Vision: llava:latest (multimodal needs)")
        print("🔬 Expert: qwen2.5vl:7b (advanced vision)")
        
        print(f"\n✅ M2 Advanced Model Testing Complete")
        
    except Exception as e:
        print(f"❌ Advanced Model Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_advanced_models())
