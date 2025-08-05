#!/usr/bin/env python3
"""Debug script to check call_history_service add_message method"""

import sys
import inspect

def test_call_history_service():
    """Test the call_history_service to see its add_message signature"""
    try:
        # Import the service
        from src.services.call_history_service import call_history_service
        
        print("🔍 Debugging CallHistoryService.add_message()")
        print("=" * 60)
        
        # Check the add_message method signature
        method = call_history_service.add_message
        signature = inspect.signature(method)
        
        print(f"📋 Method: {method}")
        print(f"🔧 Signature: {signature}")
        print(f"📝 Parameters:")
        
        for name, param in signature.parameters.items():
            print(f"   - {name}: {param}")
        
        # Check if there are any other add_message methods that might be called
        print(f"\n🏭 Service type: {type(call_history_service)}")
        print(f"📦 Service module: {call_history_service.__class__.__module__}")
        
        # Test a correct call
        print(f"\n✅ Testing correct call format:")
        print("call_history_service.add_message(")
        print("    call_id='test-123',")
        print("    speaker='user',") 
        print("    message='Hello',")
        print("    duration_ms=1000,")
        print("    was_interrupted=False")
        print(")")
        
        print(f"\n❌ WRONG call format that would cause error:")
        print("call_history_service.add_message(")
        print("    session.call_id,") 
        print("    user_text,")
        print("    ai_text,") 
        print("    stt_duration,")
        print("    llm_duration,")
        print("    tts_duration")
        print(")")
        print("  ^ This has 6 parameters but method expects 3-5")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing call_history_service: {e}")
        return False

if __name__ == "__main__":
    test_call_history_service()
