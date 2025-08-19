#!/usr/bin/env python3
"""
Test M2 Pipeline Integration
"""

import sys
import os
import asyncio

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_m2_pipeline_integration():
    """Test M2 pipeline integration with intelligent routing"""
    
    print("🔗 Testing M2 Pipeline Integration")
    print("=" * 50)
    
    try:
        from src.services.m2_pipeline_manager import m2_pipeline
        
        # Initialize the pipeline
        print("🚀 Initializing M2 Pipeline...")
        await m2_pipeline.startup()
        
        # Test health check
        print("\n🏥 Testing Health Check...")
        health = await m2_pipeline.health_check()
        print(f"Status: {health.get('status')}")
        print(f"Memory Usage: {health.get('memory_usage', 0)*100:.1f}%")
        
        # Test pipeline status
        print("\n📊 Testing Pipeline Status...")
        status = await m2_pipeline.get_pipeline_status()
        print(f"Loaded Models: {status.get('loaded_models')}")
        print(f"Chip: {status.get('chip')}")
        print(f"GPU Acceleration: {status.get('gpu_acceleration')}")
        
        # Test intelligent translation with different speed requirements
        test_text = "Hello world"
        
        print("\n🎯 Testing Intelligent Translation...")
        
        # Real-time translation (< 0.5s)
        print("Testing real-time translation...")
        result1 = await m2_pipeline.intelligent_translate(
            text=test_text,
            source_lang="en", 
            target_lang="zh",
            max_response_time=0.5
        )
        print(f"✅ Real-time: {result1.get('model_tier')} | {result1.get('response_time', 0):.3f}s | {result1.get('translation')}")
        
        # Interactive translation (< 1.0s) 
        print("Testing interactive translation...")
        result2 = await m2_pipeline.intelligent_translate(
            text=test_text,
            source_lang="en",
            target_lang="zh", 
            max_response_time=1.0
        )
        print(f"✅ Interactive: {result2.get('model_tier')} | {result2.get('response_time', 0):.3f}s | {result2.get('translation')}")
        
        # Quality translation
        print("Testing quality-focused translation...")
        result3 = await m2_pipeline.intelligent_translate(
            text=test_text,
            source_lang="en",
            target_lang="zh",
            quality_mode="quality"
        )
        print(f"✅ Quality: {result3.get('model_tier')} | {result3.get('response_time', 0):.3f}s | {result3.get('translation')}")
        
        # Show performance stats
        print(f"\n📈 Performance Summary:")
        final_status = await m2_pipeline.get_pipeline_status()
        perf_stats = final_status.get('performance_stats', {})
        
        for model, stats in perf_stats.items():
            print(f"  {model}: {stats['requests']} requests, avg {stats['avg_time']:.3f}s")
        
        print("\n✅ M2 Pipeline Integration Test Complete")
        
    except Exception as e:
        print(f"❌ Integration Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_m2_pipeline_integration())
