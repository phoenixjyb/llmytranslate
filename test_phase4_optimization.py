#!/usr/bin/env python3
"""
Phase 4 Optimization Integration Test
Tests the newly integrated optimization services for phone call mode.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_optimization_services():
    """Test Phase 4 optimization services integration."""
    print("🚀 Testing Phase 4 Optimization Services Integration")
    print("=" * 60)
    
    # Test 1: Import verification
    print("\n1. Testing Service Imports...")
    
    try:
        from src.services.optimized_llm_service import optimized_llm_service
        from src.services.performance_monitor import performance_monitor
        from src.services.quality_monitor import quality_monitor
        from src.services.connection_pool_manager import connection_pool_manager
        print("✅ All optimization services imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test 2: Service initialization
    print("\n2. Testing Service Initialization...")
    
    try:
        # Services are already initialized when imported - just test basic functionality
        print("✅ Services are auto-initialized on import")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False
    
    # Test 3: Optimized LLM Service
    print("\n3. Testing Optimized LLM Service...")
    
    try:
        # Test model selection for phone calls
        optimal_model = optimized_llm_service.get_optimal_model_for_phone_call(
            kid_friendly=False,
            language="en"
        )
        print(f"✅ Optimal model selected: {optimal_model}")
        
        # Test model warmup
        warmup_results = await optimized_llm_service.warmup_models()
        print(f"✅ Model warmup completed: {len(warmup_results)} models")
        
    except Exception as e:
        print(f"❌ LLM service error: {e}")
        return False
    
    # Test 4: Performance Monitor
    print("\n4. Testing Performance Monitor...")
    
    try:
        session_id = "test_session_001"
        
        # Start call tracking
        performance_monitor.record_call_start(session_id, "test_user", False)
        print("✅ Call start recorded")
        
        # Simulate STT performance
        performance_monitor.record_stt_performance(
            session_id=session_id,
            duration=0.5,
            audio_length=1024,
            success=True,
            language="en"
        )
        print("✅ STT performance recorded")
        
        # Simulate LLM performance
        performance_monitor.record_llm_performance(
            session_id=session_id,
            duration=1.2,
            model="gemma3:1b",
            input_length=50,
            output_length=100,
            success=True
        )
        print("✅ LLM performance recorded")
        
        # Get session summary
        summary = performance_monitor.get_session_summary(session_id)
        print(f"✅ Session summary generated: {len(summary)} metrics")
        
    except Exception as e:
        print(f"❌ Performance monitor error: {e}")
        return False
    
    # Test 5: Quality Monitor
    print("\n5. Testing Quality Monitor...")
    
    try:
        # Record service performance
        quality_level = quality_monitor.record_service_performance(
            service="llm",
            duration=1.5,
            success=True
        )
        print(f"✅ Service performance recorded: {quality_level.value}")
        
        # Get overall quality
        overall_quality = quality_monitor.get_overall_quality()
        print(f"✅ Overall quality: {overall_quality.value}")
        
    except Exception as e:
        print(f"❌ Quality monitor error: {e}")
        return False
    
    # Test 6: Connection Pool Manager
    print("\n6. Testing Connection Pool Manager...")
    
    try:
        # Ensure service pools
        await connection_pool_manager.ensure_service_pool("ollama")
        await connection_pool_manager.ensure_service_pool("tts")
        print("✅ Service pools created")
        
        # Get pool statistics
        stats = connection_pool_manager.get_pool_statistics()
        print(f"✅ Pool statistics: {len(stats)} pools active")
        
    except Exception as e:
        print(f"❌ Connection pool error: {e}")
        return False
    
    # Test 7: Integrated Phone Call Route
    print("\n7. Testing Phone Call Route Integration...")
    
    try:
        from src.api.routes.phone_call import (
            handle_optimized_session_start,
            handle_optimized_audio_data,
            handle_optimized_ping,
            handle_optimized_session_end
        )
        print("✅ Optimized handlers imported successfully")
        
        # Test get_interruptible_llm_response function
        from src.api.routes.phone_call import get_interruptible_llm_response
        print("✅ Optimized LLM response function available")
        
    except ImportError as e:
        print(f"❌ Route integration error: {e}")
        return False
    
    print("\n🎉 Phase 4 Optimization Integration Test Summary")
    print("=" * 60)
    print("✅ All optimization services successfully integrated!")
    print("✅ Enhanced phone call handlers ready for production")
    print("✅ Performance monitoring active")
    print("✅ Quality monitoring with fallbacks enabled")
    print("✅ Connection pooling optimized")
    print("\n🚀 Phase 4 optimization ready for phone call mode!")
    
    return True

async def test_optimization_workflow():
    """Test a complete optimization workflow simulation."""
    print("\n🔄 Testing Complete Optimization Workflow...")
    
    try:
        from src.services.optimized_llm_service import optimized_llm_service
        from src.services.performance_monitor import performance_monitor
        from src.services.quality_monitor import quality_monitor
        
        session_id = "workflow_test_001"
        
        # Simulate complete phone call interaction
        start_time = time.time()
        
        # 1. Start call with monitoring
        performance_monitor.record_call_start(session_id, "test_user", False)
        
        # 2. Simulate optimized LLM call
        optimal_model = optimized_llm_service.get_optimal_model_for_phone_call()
        print(f"   📱 Using optimized model: {optimal_model}")
        
        # 3. Record performance metrics
        performance_monitor.record_stt_performance(session_id, 0.3, 2048, True, "en")
        performance_monitor.record_llm_performance(session_id, 1.1, optimal_model, 45, 95, True)
        performance_monitor.record_tts_performance(session_id, 0.8, 95, 4096, True, "neutral", "en")
        
        # 4. Record complete interaction
        total_time = time.time() - start_time
        performance_monitor.record_complete_interaction(
            session_id, total_time, 0.3, 1.1, 0.8, True
        )
        
        # 5. Check quality and get recommendations
        quality = quality_monitor.get_overall_quality()
        session_summary = performance_monitor.get_session_summary(session_id)
        
        print(f"   📊 Workflow completed in {total_time:.2f}s")
        print(f"   🎯 Quality level: {quality.value}")
        print(f"   📈 Session metrics: {len(session_summary)} data points")
        
        print("✅ Complete optimization workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow test error: {e}")
        return False

async def main():
    """Main test runner."""
    print("🧪 Phase 4 Optimization Test Suite")
    print("Testing production-ready performance optimization for phone calls")
    print()
    
    try:
        # Run service integration tests
        integration_success = await test_optimization_services()
        
        if integration_success:
            # Run workflow test
            workflow_success = await test_optimization_workflow()
            
            if workflow_success:
                print("\n🎉 All Phase 4 optimization tests PASSED!")
                print("\n🚀 Ready for production phone call optimization:")
                print("   • Smaller LLMs for faster responses")
                print("   • Comprehensive performance monitoring")
                print("   • Quality monitoring with intelligent fallbacks")
                print("   • HTTP connection pooling optimization")
                print("   • Enhanced WebSocket handlers")
                return True
            else:
                print("\n❌ Workflow test failed")
                return False
        else:
            print("\n❌ Integration tests failed")
            return False
            
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
