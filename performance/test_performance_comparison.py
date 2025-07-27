#!/usr/bin/env python3
"""
Quick Performance Comparison Test
Compares original vs optimized translation performance.
"""

import asyncio
import time
import requests
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.optimized_translation_service import optimized_translation_service, TranslationRequest

async def test_optimized_vs_direct():
    """Compare optimized service vs direct Ollama calls."""
    
    print("⚡ Performance Comparison: Optimized Service vs Direct Ollama")
    print("=" * 65)
    
    test_text = "Hello world, this is a test translation."
    
    # Test 1: Direct Ollama (baseline)
    print("\n🔄 Test 1: Direct Ollama Call")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:latest",
                "prompt": f"Translate to Chinese: {test_text}",
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 100}
            },
            timeout=30
        )
        
        direct_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            translation = result.get("response", "").strip()
            print(f"   ✅ Direct Ollama: {direct_time*1000:.1f}ms")
            print(f"   📝 Translation: {translation[:50]}...")
        else:
            print(f"   ❌ Direct Ollama failed: HTTP {response.status_code}")
            direct_time = None
            
    except Exception as e:
        print(f"   ❌ Direct Ollama error: {e}")
        direct_time = None
    
    # Test 2: Optimized service (first call - cold cache)
    print("\n🚀 Test 2: Optimized Service (Cold Cache)")
    
    await optimized_translation_service.initialize()
    
    request = TranslationRequest(
        text=test_text,
        from_lang="en",
        to_lang="zh",
        use_cache=True
    )
    
    start_time = time.time()
    result = await optimized_translation_service.translate(request)
    optimized_cold_time = time.time() - start_time
    
    if result.success:
        print(f"   ✅ Optimized (Cold): {optimized_cold_time*1000:.1f}ms")
        print(f"   📝 Translation: {result.translation[:50]}...")
        print(f"   🔍 Cache: {'HIT' if result.cached else 'MISS'}")
        
        # Show timing breakdown
        timing = result.timing_breakdown
        if timing:
            print(f"   ⏱️  Breakdown:")
            for key, value in timing.items():
                if key.endswith('_ms') and value > 0:
                    print(f"      • {key.replace('_ms', '').replace('_', ' ').title()}: {value:.1f}ms")
    else:
        print(f"   ❌ Optimized service failed: {result.error}")
        optimized_cold_time = None
    
    # Test 3: Optimized service (second call - warm cache)
    print("\n🔥 Test 3: Optimized Service (Warm Cache)")
    
    start_time = time.time()
    result = await optimized_translation_service.translate(request)
    optimized_warm_time = time.time() - start_time
    
    if result.success:
        print(f"   ✅ Optimized (Warm): {optimized_warm_time*1000:.1f}ms")
        print(f"   🔍 Cache: {'🔥 HIT' if result.cached else '❄️ MISS'}")
        
        if result.cached:
            print(f"   ⚡ Instant response from cache!")
        
    else:
        print(f"   ❌ Optimized service failed: {result.error}")
        optimized_warm_time = None
    
    # Performance Summary
    print(f"\n📊 PERFORMANCE SUMMARY")
    print("-" * 40)
    
    if direct_time and optimized_cold_time and optimized_warm_time:
        print(f"🔄 Direct Ollama:        {direct_time*1000:.1f}ms")
        print(f"🚀 Optimized (Cold):     {optimized_cold_time*1000:.1f}ms")
        print(f"🔥 Optimized (Warm):     {optimized_warm_time*1000:.1f}ms")
        
        # Calculate improvements
        cold_improvement = ((direct_time - optimized_cold_time) / direct_time) * 100 if direct_time > optimized_cold_time else 0
        warm_speedup = direct_time / optimized_warm_time if optimized_warm_time > 0 else 0
        
        print(f"\n💡 Improvements:")
        if cold_improvement > 0:
            print(f"   • Cold cache: {cold_improvement:.1f}% faster than direct")
        else:
            print(f"   • Cold cache: Similar to direct (expected)")
        
        print(f"   • Warm cache: {warm_speedup:.1f}x faster than direct")
        print(f"   • Cache saves: {(direct_time - optimized_warm_time)*1000:.1f}ms per request")
    
    # Get service stats
    stats = optimized_translation_service.get_performance_stats()
    trans_stats = stats.get("translation_service", {})
    
    print(f"\n📈 Service Statistics:")
    print(f"   • Total translations: {trans_stats.get('total_translations', 0)}")
    print(f"   • Cache hit rate: {trans_stats.get('cache_hit_rate_percent', 0):.1f}%")
    print(f"   • Average response: {trans_stats.get('average_response_time_ms', 0):.1f}ms")
    
    await optimized_translation_service.cleanup()

if __name__ == "__main__":
    asyncio.run(test_optimized_vs_direct())
