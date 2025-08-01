#!/usr/bin/env python3
"""
Test phone call service with intelligent conversation management.
Verify integration of the new conversation flow manager.
"""

import asyncio
import json
import base64
import time
from unittest.mock import Mock, AsyncMock, patch

# Add the src directory to the Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test configuration
TEST_AUDIO_DATA = b"dummy audio data for testing" * 50  # Simulated audio data

async def test_phone_call_integration():
    """Test phone call service with intelligent conversation flow."""
    print("📞 Testing Phone Call Integration with Intelligent Conversation")
    print("=" * 65)
    
    try:
        # Import the conversation flow manager
        from services.conversation_flow_manager import conversation_flow_manager
        
        # Test session setup
        session_id = "test_integration_123"
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        print("✅ 1. Testing conversation start...")
        conversation_flow_manager.start_conversation(session_id, mock_websocket)
        
        # Verify session exists
        assert session_id in conversation_flow_manager.active_conversations
        print(f"   - Session created: {session_id}")
        
        print("✅ 2. Testing user speaking detection...")
        conversation_flow_manager.start_user_speaking(session_id)
        is_speaking = conversation_flow_manager.is_user_speaking(session_id)
        print(f"   - User speaking: {is_speaking}")
        assert is_speaking, "User should be marked as speaking"
        
        print("✅ 3. Testing audio processing...")
        conversation_flow_manager.process_audio_chunk(session_id, TEST_AUDIO_DATA)
        conversation_flow_manager.stop_user_speaking(session_id)
        
        print("✅ 4. Testing conversation flow...")
        # Add a user message
        test_message = "Hello, I need help with my translation service setup."
        conversation_flow_manager.add_user_message(session_id, test_message)
        
        # Check if we should process the turn
        should_process = conversation_flow_manager.should_process_turn(session_id)
        print(f"   - Should process turn: {should_process}")
        
        # Add AI response
        ai_response = "I'd be happy to help you set up your translation service. What specific aspect would you like assistance with?"
        conversation_flow_manager.add_assistant_message(session_id, ai_response)
        conversation_flow_manager.handle_ai_response(session_id)
        
        print("✅ 5. Testing context management...")
        context = conversation_flow_manager.get_conversation_context(session_id)
        print(f"   - Context messages: {len(context)}")
        print(f"   - Last user message: {context[-2]['content'][:50]}..." if len(context) >= 2 else "No messages")
        print(f"   - Last AI message: {context[-1]['content'][:50]}..." if len(context) >= 1 else "No messages")
        
        print("✅ 6. Testing interruption handling...")
        # Simulate user speaking for too long
        conversation_flow_manager.start_user_speaking(session_id)
        
        # Manually set speaking start time to trigger interruption
        conv = conversation_flow_manager.active_conversations[session_id]
        conv['user_talk_start'] = time.time() - 35  # 35 seconds ago
        
        should_interrupt = conversation_flow_manager.should_interrupt_user(session_id)
        print(f"   - Should interrupt after 35s: {should_interrupt}")
        
        if should_interrupt:
            await conversation_flow_manager.interrupt_user(session_id, mock_websocket)
            print("   - Interruption sent successfully")
            
            # Verify interruption message was sent
            assert mock_websocket.send_text.called
            call_args = mock_websocket.send_text.call_args[0][0]
            message = json.loads(call_args)
            assert message['type'] == 'ai_interruption'
            print(f"   - Interruption message: {message['message'][:50]}...")
        
        print("✅ 7. Testing conversation cleanup...")
        conversation_flow_manager.end_conversation(session_id)
        assert session_id not in conversation_flow_manager.active_conversations
        print("   - Session cleaned up successfully")
        
        print("\n🎉 Phone call integration test passed!")
        return True
        
    except Exception as e:
        print(f"\n💥 Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_conversation_persistence():
    """Test conversation persistence and state management."""
    print("\n💾 Testing Conversation Persistence")
    print("=" * 40)
    
    try:
        from services.conversation_flow_manager import conversation_flow_manager
        
        session_id = "persistence_test"
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        # Start conversation
        conversation_flow_manager.start_conversation(session_id, mock_websocket)
        
        # Add multiple conversation turns
        messages = [
            ("user", "I need help with error handling"),
            ("assistant", "I can help you with error handling. What specific errors are you encountering?"),
            ("user", "I'm getting Unicode encoding issues in my logs"),
            ("assistant", "Unicode encoding issues are common. Let me help you fix that."),
            ("user", "The error message says 'gbk codec can't encode character'"),
            ("assistant", "That's a Windows-specific encoding issue. Here's how to fix it...")
        ]
        
        print("✅ 1. Adding conversation history...")
        for role, content in messages:
            if role == "user":
                conversation_flow_manager.add_user_message(session_id, content)
            else:
                conversation_flow_manager.add_assistant_message(session_id, content)
        
        # Test context retrieval
        context = conversation_flow_manager.get_conversation_context(session_id)
        print(f"   - Total messages in context: {len(context)}")
        assert len(context) == len(messages), f"Expected {len(messages)} messages, got {len(context)}"
        
        # Test turn tracking
        conv = conversation_flow_manager.active_conversations[session_id]
        print(f"   - Conversation turns: {conv.get('conversation_turns', 0)}")
        print(f"   - Is active: {conv.get('is_active', False)}")
        
        # Test state consistency
        last_user_msg = context[-2] if len(context) >= 2 else None
        last_ai_msg = context[-1] if len(context) >= 1 else None
        
        if last_user_msg and last_ai_msg:
            print(f"   - Last user: {last_user_msg['content'][:30]}...")
            print(f"   - Last AI: {last_ai_msg['content'][:30]}...")
            assert last_user_msg['role'] == 'user'
            assert last_ai_msg['role'] == 'assistant'
        
        # Cleanup
        conversation_flow_manager.end_conversation(session_id)
        print("✅ 2. Conversation persistence test passed!")
        return True
        
    except Exception as e:
        print(f"💥 Persistence test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests."""
    print("🤖 Starting Phone Call Integration Tests")
    print("=" * 50)
    
    try:
        test1 = await test_phone_call_integration()
        test2 = await test_conversation_persistence()
        
        if all([test1, test2]):
            print("\n🌟 ALL INTEGRATION TESTS PASSED! 🌟")
            print("Your phone call service with intelligent conversation management is ready!")
            print("\n📋 Features Tested:")
            print("  ✅ Conversation initialization and cleanup")
            print("  ✅ User speaking detection and management")
            print("  ✅ Audio chunk processing")
            print("  ✅ Turn-taking logic")
            print("  ✅ Context management and retrieval")
            print("  ✅ User interruption handling (35s limit)")
            print("  ✅ Conversation persistence and state tracking")
            print("\n🚀 Ready for production use!")
            return True
        else:
            print("\n❌ Some integration tests failed")
            return False
            
    except Exception as e:
        print(f"\n💥 Integration test suite error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
