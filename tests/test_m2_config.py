#!/usr/bin/env python3
"""
Test M2 Pipeline Configuration
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_m2_config():
    """Test M2 pipeline configuration loading"""
    
    print("🔧 Testing M2 Pipeline Configuration")
    print("=" * 50)
    
    try:
        from src.config.m2_pipeline import m2_config
        
        if m2_config is None:
            print("❌ M2 config failed to load")
            return
            
        # Test configuration loading
        print(m2_config.summary())
        
        # Test model tier selection
        print("🎯 Model Selection Tests:")
        print(f"For real-time (0.3s): {m2_config.get_model_for_speed_requirement(0.3)}")
        print(f"For interactive (0.8s): {m2_config.get_model_for_speed_requirement(0.8)}")
        print(f"For batch (2.0s): {m2_config.get_model_for_speed_requirement(2.0)}")
        print(f"For complex (5.0s): {m2_config.get_model_for_speed_requirement(5.0)}")
        
        # Test fallback order
        print(f"\n🔄 Fallback Order: {m2_config.get_fallback_models()}")
        
        # Test startup configuration
        print(f"🚀 Startup Models: {m2_config.get_startup_models()}")
        print(f"⏳ Lazy Load Models: {m2_config.get_lazy_load_models()}")
        
        # Test performance settings
        print(f"\n⚡ Performance Settings:")
        print(f"Max Concurrent: {m2_config.get_concurrent_request_limit()}")
        print(f"Memory Threshold: {m2_config.get_memory_threshold()*100}%")
        print(f"Bypass Proxy: {m2_config.should_bypass_proxy()}")
        
        print("\n✅ M2 Configuration Test Complete")
        
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_m2_config()
