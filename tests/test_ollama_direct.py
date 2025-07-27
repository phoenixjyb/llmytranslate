#!/usr/bin/env python3
"""
Direct Ollama Translation Test - Bypassing Configuration Issues
Tests Ollama translation functionality with detailed timing breakdown.
"""

import time
import requests
import json
from typing import Dict, Optional

def test_ollama_translation(text: str, from_lang: str = "en", to_lang: str = "zh", model: str = "gemma3:latest") -> Dict:
    """Test Ollama translation directly with timing breakdown."""
    
    print(f"🔄 Testing Ollama translation: {from_lang} → {to_lang}")
    print(f"📝 Text: {text}")
    print(f"🤖 Model: {model}")
    
    # Start total timing
    total_start = time.time()
    
    # Prepare translation prompt
    if from_lang == "en" and to_lang == "zh":
        prompt = f"Translate the following English text to Chinese. Only return the translation, no explanations:\n\n{text}"
    elif from_lang == "zh" and to_lang == "en":
        prompt = f"Translate the following Chinese text to English. Only return the translation, no explanations:\n\n{text}"
    else:
        prompt = f"Translate from {from_lang} to {to_lang}: {text}"
    
    # Step 1: Connection timing
    print("⏱️  Step 1: Connecting to Ollama...")
    conn_start = time.time()
    
    try:
        # Test connection first
        health_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        conn_time = time.time() - conn_start
        print(f"   ✅ Connection: {conn_time*1000:.1f}ms")
        
        if health_response.status_code != 200:
            return {
                "success": False,
                "error": f"Ollama not accessible: HTTP {health_response.status_code}",
                "timing": {"connection_ms": conn_time*1000}
            }
        
    except Exception as e:
        conn_time = time.time() - conn_start
        return {
            "success": False,
            "error": f"Cannot connect to Ollama: {str(e)}",
            "timing": {"connection_ms": conn_time*1000}
        }
    
    # Step 2: LLM Inference timing
    print("⏱️  Step 2: Running LLM inference...")
    inference_start = time.time()
    
    try:
        # Make translation request
        ollama_payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 512
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=ollama_payload,
            timeout=30
        )
        
        inference_time = time.time() - inference_start
        print(f"   ✅ LLM Inference: {inference_time*1000:.1f}ms")
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Ollama generation failed: HTTP {response.status_code}",
                "timing": {
                    "connection_ms": conn_time*1000,
                    "inference_ms": inference_time*1000
                }
            }
        
    except Exception as e:
        inference_time = time.time() - inference_start
        return {
            "success": False,
            "error": f"LLM inference failed: {str(e)}",
            "timing": {
                "connection_ms": conn_time*1000,
                "inference_ms": inference_time*1000
            }
        }
    
    # Step 3: Response processing
    print("⏱️  Step 3: Processing response...")
    processing_start = time.time()
    
    try:
        result_data = response.json()
        translation = result_data.get("response", "").strip()
        
        # Extract additional metrics from Ollama response
        eval_count = result_data.get("eval_count", 0)
        eval_duration = result_data.get("eval_duration", 0)
        prompt_eval_count = result_data.get("prompt_eval_count", 0)
        prompt_eval_duration = result_data.get("prompt_eval_duration", 0)
        
        processing_time = time.time() - processing_start
        total_time = time.time() - total_start
        
        print(f"   ✅ Processing: {processing_time*1000:.1f}ms")
        print(f"📄 Translation: {translation}")
        
        # Calculate detailed timing breakdown
        timing_breakdown = {
            "total_ms": round(total_time * 1000, 2),
            "steps": {
                "connection": {
                    "duration_ms": round(conn_time * 1000, 2),
                    "percentage": round((conn_time / total_time) * 100, 1)
                },
                "llm_inference": {
                    "duration_ms": round(inference_time * 1000, 2),
                    "percentage": round((inference_time / total_time) * 100, 1)
                },
                "response_processing": {
                    "duration_ms": round(processing_time * 1000, 2),
                    "percentage": round((processing_time / total_time) * 100, 1)
                }
            },
            "ollama_metrics": {
                "eval_count": eval_count,
                "eval_duration_ns": eval_duration,
                "eval_duration_ms": round(eval_duration / 1_000_000, 2) if eval_duration else 0,
                "prompt_eval_count": prompt_eval_count,
                "prompt_eval_duration_ns": prompt_eval_duration,
                "prompt_eval_duration_ms": round(prompt_eval_duration / 1_000_000, 2) if prompt_eval_duration else 0,
                "tokens_per_second": round(eval_count / (eval_duration / 1_000_000_000), 2) if eval_duration and eval_count else 0
            }
        }
        
        return {
            "success": True,
            "translation": translation,
            "timing_breakdown": timing_breakdown,
            "original_text": text,
            "direction": f"{from_lang} → {to_lang}",
            "model": model
        }
        
    except Exception as e:
        processing_time = time.time() - processing_start
        total_time = time.time() - total_start
        
        return {
            "success": False,
            "error": f"Response processing failed: {str(e)}",
            "timing": {
                "connection_ms": conn_time*1000,
                "inference_ms": inference_time*1000,
                "processing_ms": processing_time*1000,
                "total_ms": total_time*1000
            }
        }

def run_comprehensive_test():
    """Run comprehensive translation tests with different scenarios."""
    
    print("🚀 Direct Ollama Translation Performance Test")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Simple English → Chinese",
            "text": "Hello world",
            "from": "en",
            "to": "zh"
        },
        {
            "name": "Simple Chinese → English", 
            "text": "你好世界",
            "from": "zh",
            "to": "en"
        },
        {
            "name": "Medium English → Chinese",
            "text": "Good morning! How are you today? I hope you have a wonderful day.",
            "from": "en",
            "to": "zh"
        },
        {
            "name": "Technical English → Chinese",
            "text": "Machine learning algorithms use neural networks to process natural language.",
            "from": "en",
            "to": "zh"
        }
    ]
    
    all_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 40)
        
        result = test_ollama_translation(
            text=test_case['text'],
            from_lang=test_case['from'],
            to_lang=test_case['to']
        )
        
        all_results.append({
            "test_name": test_case['name'],
            **result
        })
        
        if result['success']:
            timing = result['timing_breakdown']
            print(f"⏱️  Total Time: {timing['total_ms']}ms")
            print(f"🔍 Breakdown:")
            for step, data in timing['steps'].items():
                print(f"   • {step.replace('_', ' ').title()}: {data['duration_ms']}ms ({data['percentage']}%)")
            
            if timing.get('ollama_metrics', {}).get('tokens_per_second'):
                print(f"🚀 Speed: {timing['ollama_metrics']['tokens_per_second']} tokens/sec")
        else:
            print(f"❌ Failed: {result['error']}")
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print(f"\n📊 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    successful_tests = [r for r in all_results if r['success']]
    
    if successful_tests:
        total_times = [r['timing_breakdown']['total_ms'] for r in successful_tests]
        llm_times = [r['timing_breakdown']['steps']['llm_inference']['duration_ms'] for r in successful_tests]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(test_cases)}")
        print(f"⏱️  Average total time: {sum(total_times)/len(total_times):.1f}ms")
        print(f"🧠 Average LLM time: {sum(llm_times)/len(llm_times):.1f}ms")
        print(f"📈 LLM percentage: {(sum(llm_times)/sum(total_times)*100):.1f}%")
        
        fastest = min(successful_tests, key=lambda x: x['timing_breakdown']['total_ms'])
        slowest = max(successful_tests, key=lambda x: x['timing_breakdown']['total_ms'])
        
        print(f"🏃 Fastest: {fastest['test_name']} ({fastest['timing_breakdown']['total_ms']}ms)")
        print(f"🐌 Slowest: {slowest['test_name']} ({slowest['timing_breakdown']['total_ms']}ms)")
        
        # Check if Ollama is the bottleneck
        avg_llm_percentage = (sum(llm_times)/sum(total_times)*100)
        if avg_llm_percentage > 80:
            print(f"💡 LLM inference dominates ({avg_llm_percentage:.1f}%) - consider faster model")
        elif avg_llm_percentage < 50:
            print(f"💡 Overhead significant ({100-avg_llm_percentage:.1f}%) - check network/processing")
        else:
            print(f"✅ Good balance between LLM and overhead")
    
    # Save results
    with open("ollama_direct_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Detailed results saved to: ollama_direct_results.json")
    
    return all_results

if __name__ == "__main__":
    try:
        results = run_comprehensive_test()
        print(f"\n🎉 Test completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
