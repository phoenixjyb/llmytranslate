#!/usr/bin/env python3
"""
Performance Testing Script for LLM Translation Service
Tests various translation scenarios and provides detailed timing breakdown.
"""

import asyncio
import time
import requests
import json
from typing import Dict, List
import statistics

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Simple English",
        "text": "Hello world",
        "from": "en",
        "to": "zh"
    },
    {
        "name": "Simple Chinese", 
        "text": "你好世界",
        "from": "zh",
        "to": "en"
    },
    {
        "name": "Medium English",
        "text": "Good morning! How are you today? I hope you have a wonderful day.",
        "from": "en", 
        "to": "zh"
    },
    {
        "name": "Medium Chinese",
        "text": "早上好！你今天怎么样？我希望你今天过得愉快。",
        "from": "zh",
        "to": "en"
    },
    {
        "name": "Long English",
        "text": "Artificial intelligence has revolutionized the way we communicate across languages. Machine translation systems now use advanced neural networks to provide more accurate and context-aware translations than ever before.",
        "from": "en",
        "to": "zh"
    },
    {
        "name": "Long Chinese", 
        "text": "人工智能已经彻底改变了我们跨语言交流的方式。机器翻译系统现在使用先进的神经网络，提供比以往任何时候都更准确和上下文感知的翻译。",
        "from": "zh",
        "to": "en"
    }
]

def test_translation_performance(base_url: str = "http://localhost:8000") -> Dict:
    """Test translation performance and return detailed metrics."""
    
    results = {
        "overall_stats": {},
        "scenario_results": [],
        "timing_analysis": {}
    }
    
    all_response_times = []
    all_timing_breakdowns = []
    
    print("🚀 Starting Translation Performance Test")
    print("=" * 50)
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n📊 Test {i}/{len(TEST_SCENARIOS)}: {scenario['name']}")
        print(f"   Text: {scenario['text'][:50]}{'...' if len(scenario['text']) > 50 else ''}")
        print(f"   Direction: {scenario['from']} → {scenario['to']}")
        
        # Prepare form data
        form_data = {
            'q': scenario['text'],
            'from': scenario['from'],
            'to': scenario['to']
        }
        
        # Measure total request time
        start_time = time.time()
        
        try:
            # Make request
            response = requests.post(
                f"{base_url}/api/demo/translate",
                data=form_data,
                timeout=30
            )
            
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract performance data
                performance = data.get('performance', {})
                service_time = performance.get('total_time_ms', total_time * 1000)
                timing_breakdown = performance.get('timing_breakdown', {})
                
                # Extract translation result
                translation_result = None
                if data.get('response', {}).get('trans_result'):
                    translation_result = data['response']['trans_result'][0]['dst']
                
                result = {
                    "scenario": scenario['name'],
                    "text_length": len(scenario['text']),
                    "direction": f"{scenario['from']} → {scenario['to']}",
                    "success": True,
                    "total_request_time_ms": round(total_time * 1000, 2),
                    "service_processing_time_ms": round(service_time, 2),
                    "translation": translation_result,
                    "timing_breakdown": timing_breakdown
                }
                
                all_response_times.append(service_time)
                if timing_breakdown:
                    all_timing_breakdowns.append(timing_breakdown)
                
                # Print results
                print(f"   ✅ Success: {round(service_time, 1)}ms")
                if timing_breakdown and timing_breakdown.get('steps'):
                    print(f"   🔍 Key timings:")
                    steps = timing_breakdown['steps']
                    if 'llm_inference_actual' in steps:
                        llm_time = steps['llm_inference_actual']['duration_ms']
                        print(f"      🧠 LLM Inference: {llm_time}ms ({steps['llm_inference_actual']['percentage']}%)")
                    if 'cache_lookup' in steps:
                        cache_time = steps['cache_lookup']['duration_ms']
                        print(f"      🔍 Cache Lookup: {cache_time}ms ({steps['cache_lookup']['percentage']}%)")
                    if 'ollama_connection' in steps:
                        conn_time = steps['ollama_connection']['duration_ms']
                        print(f"      🔗 Connection: {conn_time}ms ({steps['ollama_connection']['percentage']}%)")
                
                print(f"   📝 Translation: {translation_result}")
                
            else:
                result = {
                    "scenario": scenario['name'],
                    "text_length": len(scenario['text']),
                    "direction": f"{scenario['from']} → {scenario['to']}",
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "total_request_time_ms": round(total_time * 1000, 2)
                }
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            total_time = time.time() - start_time
            result = {
                "scenario": scenario['name'],
                "text_length": len(scenario['text']),
                "direction": f"{scenario['from']} → {scenario['to']}",
                "success": False,
                "error": str(e),
                "total_request_time_ms": round(total_time * 1000, 2)
            }
            print(f"   ❌ Error: {str(e)}")
        
        results["scenario_results"].append(result)
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Calculate overall statistics
    if all_response_times:
        results["overall_stats"] = {
            "total_tests": len(TEST_SCENARIOS),
            "successful_tests": len(all_response_times),
            "average_time_ms": round(statistics.mean(all_response_times), 2),
            "median_time_ms": round(statistics.median(all_response_times), 2),
            "min_time_ms": round(min(all_response_times), 2),
            "max_time_ms": round(max(all_response_times), 2),
            "std_deviation_ms": round(statistics.stdev(all_response_times) if len(all_response_times) > 1 else 0, 2)
        }
    
    # Analyze timing patterns
    if all_timing_breakdowns:
        step_averages = {}
        for breakdown in all_timing_breakdowns:
            if breakdown.get('steps'):
                for step, data in breakdown['steps'].items():
                    if step not in step_averages:
                        step_averages[step] = []
                    step_averages[step].append(data['duration_ms'])
        
        results["timing_analysis"] = {
            step: {
                "average_ms": round(statistics.mean(times), 2),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2)
            }
            for step, times in step_averages.items()
            if times
        }
    
    return results

def print_summary(results: Dict):
    """Print a comprehensive summary of test results."""
    
    print("\n" + "="*60)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("="*60)
    
    stats = results.get("overall_stats", {})
    if stats:
        print(f"🎯 Overall Performance:")
        print(f"   • Total Tests: {stats['total_tests']}")
        print(f"   • Successful: {stats['successful_tests']}")
        print(f"   • Average Time: {stats['average_time_ms']}ms")
        print(f"   • Median Time: {stats['median_time_ms']}ms")
        print(f"   • Range: {stats['min_time_ms']}ms - {stats['max_time_ms']}ms")
        print(f"   • Std Deviation: {stats['std_deviation_ms']}ms")
    
    timing_analysis = results.get("timing_analysis", {})
    if timing_analysis:
        print(f"\n🔍 Timing Breakdown Analysis:")
        
        # Sort by average time (descending)
        sorted_steps = sorted(timing_analysis.items(), 
                            key=lambda x: x[1]['average_ms'], 
                            reverse=True)
        
        for step, times in sorted_steps:
            step_names = {
                'llm_inference_actual': '🧠 LLM Inference',
                'ollama_connection': '🔗 Ollama Connection', 
                'cache_lookup': '🔍 Cache Lookup',
                'request_validation': '📋 Request Validation',
                'response_formatting': '🎨 Response Formatting',
                'cache_write': '💾 Cache Write',
                'llm_response_processing': '📤 Response Processing'
            }
            
            display_name = step_names.get(step, step.replace('_', ' ').title())
            avg = times['average_ms']
            range_str = f"{times['min_ms']}-{times['max_ms']}"
            
            print(f"   • {display_name}: {avg}ms (range: {range_str}ms)")
    
    # Performance recommendations
    print(f"\n💡 Performance Insights:")
    
    if stats and stats.get('average_time_ms'):
        avg_time = stats['average_time_ms']
        
        if avg_time < 1000:
            print(f"   ✅ Excellent performance (<1s average)")
        elif avg_time < 2000:
            print(f"   ✅ Good performance (<2s average)")
        elif avg_time < 5000:
            print(f"   ⚠️  Moderate performance (<5s average)")
        else:
            print(f"   🔴 Slow performance (>5s average)")
    
    if timing_analysis:
        llm_time = timing_analysis.get('llm_inference_actual', {}).get('average_ms', 0)
        total_avg = stats.get('average_time_ms', 1)
        
        if llm_time > 0 and total_avg > 0:
            llm_percentage = (llm_time / total_avg) * 100
            print(f"   🧠 LLM inference takes {llm_percentage:.1f}% of total time")
            
            if llm_percentage > 80:
                print(f"   💡 Consider using a faster model for better performance")
            elif llm_percentage < 50:
                print(f"   💡 Non-LLM overhead is significant - check network/caching")

def main():
    """Main function to run performance tests."""
    
    print("🌐 LLM Translation Service - Performance Analyzer")
    print("=" * 55)
    
    try:
        # Test service availability
        print("🔍 Checking service availability...")
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service is healthy: {health_data.get('status', 'unknown')}")
            
            # Run performance tests
            results = test_translation_performance()
            
            # Print summary
            print_summary(results)
            
            # Save detailed results to file
            with open("performance_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n📁 Detailed results saved to: performance_results.json")
            
        else:
            print(f"❌ Service health check failed: HTTP {response.status_code}")
            print("💡 Make sure the translation service is running on localhost:8000")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to translation service")
        print("💡 Make sure the service is running: python run.py")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
