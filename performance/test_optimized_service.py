#!/usr/bin/env python3
"""
Optimized Translation Service Performance Test
Tests the new optimized service with all performance enhancements.
"""

import asyncio
import time
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.optimized_translation_service import optimized_translation_service, TranslationRequest

async def test_optimized_service():
    """Test the optimized translation service."""
    
    print("🚀 Optimized Translation Service Performance Test")
    print("=" * 55)
    
    # Initialize the service
    print("🔧 Initializing optimized service...")
    init_start = time.time()
    await optimized_translation_service.initialize()
    init_time = time.time() - init_start
    print(f"   ✅ Initialized in {init_time:.2f}s")
    
    # Test scenarios
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
        },
        {
            "name": "Long English → Chinese",
            "text": "Artificial intelligence has revolutionized the way we communicate across languages. Machine translation systems now use advanced neural networks to provide more accurate and context-aware translations than ever before. These systems can handle complex linguistic nuances and cultural context.",
            "from": "en",
            "to": "zh"
        }
    ]
    
    all_results = []
    
    # First pass - cold cache
    print(f"\n📊 FIRST PASS - Cold Cache Testing")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 Test {i}/{len(test_cases)}: {test_case['name']}")
        
        request = TranslationRequest(
            text=test_case['text'],
            from_lang=test_case['from'],
            to_lang=test_case['to'],
            use_cache=True
        )
        
        result = await optimized_translation_service.translate(request)
        
        test_result = {
            "test_name": test_case['name'],
            "pass": "first",
            "success": result.success,
            "cached": result.cached,
            "translation": result.translation,
            "timing": result.timing_breakdown,
            "model": result.model_used,
            "error": result.error
        }
        
        all_results.append(test_result)
        
        if result.success:
            total_time = result.timing_breakdown.get('total_ms', 0)
            llm_time = result.timing_breakdown.get('llm_inference_ms', 0)
            cache_time = result.timing_breakdown.get('cache_lookup_ms', 0)
            
            print(f"   ✅ Success: {total_time:.1f}ms total")
            print(f"   🔍 Cache lookup: {cache_time:.1f}ms")
            print(f"   🧠 LLM inference: {llm_time:.1f}ms")
            print(f"   📝 Translation: {result.translation[:50]}{'...' if len(result.translation) > 50 else ''}")
        else:
            print(f"   ❌ Failed: {result.error}")
        
        # Small delay
        await asyncio.sleep(0.5)
    
    # Second pass - warm cache
    print(f"\n🔥 SECOND PASS - Warm Cache Testing")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n⚡ Test {i}/{len(test_cases)}: {test_case['name']} (cached)")
        
        request = TranslationRequest(
            text=test_case['text'],
            from_lang=test_case['from'],
            to_lang=test_case['to'],
            use_cache=True
        )
        
        result = await optimized_translation_service.translate(request)
        
        test_result = {
            "test_name": test_case['name'],
            "pass": "second",
            "success": result.success,
            "cached": result.cached,
            "translation": result.translation,
            "timing": result.timing_breakdown,
            "model": result.model_used,
            "error": result.error
        }
        
        all_results.append(test_result)
        
        if result.success:
            total_time = result.timing_breakdown.get('total_ms', 0)
            cache_status = "🔥 CACHED" if result.cached else "❄️ MISS"
            
            print(f"   ✅ Success: {total_time:.1f}ms total ({cache_status})")
            if result.cached:
                print(f"   ⚡ Cache hit - instant response!")
            else:
                print(f"   ⚠️  Cache miss - unexpected")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    # Performance analysis
    print(f"\n📊 PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    # Get service statistics
    stats = optimized_translation_service.get_performance_stats()
    
    print(f"🎯 Translation Service Stats:")
    trans_stats = stats["translation_service"]
    print(f"   • Total translations: {trans_stats['total_translations']}")
    print(f"   • Cache hit rate: {trans_stats['cache_hit_rate_percent']:.1f}%")
    print(f"   • Average response: {trans_stats['average_response_time_ms']:.1f}ms")
    print(f"   • Time saved: {trans_stats['total_time_saved_seconds']:.1f}s")
    print(f"   • Model usage: {trans_stats['model_usage']}")
    
    print(f"\n💾 Cache Service Stats:")
    cache_stats = stats["cache_service"]
    print(f"   • Total entries: {cache_stats['total_entries']}")
    print(f"   • Memory usage: {cache_stats['memory_usage_mb']:.1f}MB")
    print(f"   • Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
    print(f"   • Compressions: {cache_stats['total_compressions']}")
    
    print(f"\n🔗 Ollama Client Stats:")
    ollama_stats = stats["ollama_client"]
    if ollama_stats.get("total_requests", 0) > 0:
        print(f"   • Total requests: {ollama_stats['total_requests']}")
        print(f"   • Average response: {ollama_stats['average_response_time_ms']:.1f}ms")
        print(f"   • Connection reuse: {ollama_stats['connection_reuse_rate_percent']:.1f}%")
    
    # Compare first vs second pass
    first_pass = [r for r in all_results if r['pass'] == 'first' and r['success']]
    second_pass = [r for r in all_results if r['pass'] == 'second' and r['success']]
    
    if first_pass and second_pass:
        first_avg = sum(r['timing']['total_ms'] for r in first_pass) / len(first_pass)
        second_avg = sum(r['timing']['total_ms'] for r in second_pass) / len(second_pass)
        speedup = first_avg / second_avg if second_avg > 0 else 0
        
        print(f"\n⚡ PERFORMANCE COMPARISON:")
        print(f"   • First pass (cold): {first_avg:.1f}ms average")
        print(f"   • Second pass (warm): {second_avg:.1f}ms average")
        print(f"   • Speedup: {speedup:.1f}x faster with cache")
        
        cache_hits = sum(1 for r in second_pass if r['cached'])
        cache_rate = (cache_hits / len(second_pass)) * 100
        print(f"   • Cache effectiveness: {cache_rate:.1f}%")
    
    # Run optimization
    print(f"\n🔧 RUNNING OPTIMIZATIONS...")
    optimization_result = await optimized_translation_service.optimize_performance()
    
    print(f"Applied optimizations:")
    for opt in optimization_result["optimizations_applied"]:
        print(f"   • {opt}")
    
    print(f"\nRecommendations:")
    for rec in optimization_result["recommendations"]:
        print(f"   💡 {rec}")
    
    # Save detailed results
    results_file = "optimized_service_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_results": all_results,
            "performance_stats": stats,
            "optimization_results": optimization_result
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Cleanup
    await optimized_translation_service.cleanup()
    
    return all_results, stats

async def main():
    """Main test function."""
    try:
        print("🌐 Testing Optimized LLM Translation Service")
        print("=" * 50)
        
        results, stats = await test_optimized_service()
        
        print(f"\n🎉 Test completed successfully!")
        print(f"📈 Overall improvement summary:")
        
        # Calculate key metrics
        trans_stats = stats["translation_service"]
        cache_stats = stats["cache_service"]
        
        if trans_stats["total_translations"] > 0:
            avg_time = trans_stats["average_response_time_ms"]
            cache_rate = trans_stats["cache_hit_rate_percent"]
            time_saved = trans_stats["total_time_saved_seconds"]
            
            print(f"   • Average response time: {avg_time:.1f}ms")
            print(f"   • Cache hit rate: {cache_rate:.1f}%")
            print(f"   • Total time saved: {time_saved:.1f}s")
            
            if avg_time < 2000:
                print(f"   ✅ Excellent performance achieved!")
            elif avg_time < 5000:
                print(f"   ✅ Good performance achieved!")
            else:
                print(f"   ⚠️  Performance needs improvement")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
