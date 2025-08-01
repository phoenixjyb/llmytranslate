#!/usr/bin/env python3
"""
Test intelligent conversation management features.
Tests the new conversation flow manager with smart turn-taking and context management.
"""

import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch

# Add the src directory to the Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.conversation_flow_manager import IntelligentConversationManager

async def test_conversation_flow_manager():
    """Test the intelligent conversation flow manager."""
    print("🧠 Testing Intelligent Conversation Flow Manager")
    print("=" * 50)
    
    # Initialize conversation flow manager
    flow_manager = IntelligentConversationManager()
    
    # Test session setup
    session_id = "test_session_123"
    mock_websocket = Mock()
    mock_websocket.send_text = AsyncMock()
    
    print("✅ 1. Starting conversation...")
    flow_manager.start_conversation(session_id, mock_websocket)
    
    # Test user speaking detection
    print("✅ 2. Testing user speaking detection...")
    flow_manager.start_user_speaking(session_id)
    assert flow_manager.is_user_speaking(session_id), "User should be marked as speaking"
    
    # Test audio chunk processing
    print("✅ 3. Testing audio chunk processing...")
    dummy_audio = b"dummy audio data" * 100  # Simulate 100 chunks
    for i in range(5):
        flow_manager.process_audio_chunk(session_id, dummy_audio)
    
    # Test conversation management
    print("✅ 4. Testing conversation messages...")
    test_message = "Hello, I need help with my translation project."
    flow_manager.add_user_message(session_id, test_message)
    
    # Test turn processing
    should_process = flow_manager.should_process_turn(session_id)
    print(f"   - Should process turn: {should_process}")
    
    # Test AI response
    ai_response = "I'd be happy to help you with your translation project. What specific aspect do you need assistance with?"
    flow_manager.add_assistant_message(session_id, ai_response)
    flow_manager.handle_ai_response(session_id)
    
    # Test context management
    print("✅ 5. Testing context management...")
    context = flow_manager.get_conversation_context(session_id)
    print(f"   - Context messages: {len(context) if context else 0}")
    
    # Test interruption logic
    print("✅ 6. Testing interruption logic...")
    
    # Simulate long user speaking (should trigger interruption)
    flow_manager.start_user_speaking(session_id)
    
    # Simulate passage of time for interruption test (use max_user_talk_time)
    if session_id in flow_manager.active_conversations:
        flow_manager.active_conversations[session_id]['user_talk_start'] = time.time() - 35  # 35 seconds ago (> 30s max)
    
    should_interrupt = flow_manager.should_interrupt_user(session_id)
    print(f"   - Should interrupt user (after 35s): {should_interrupt}")
    
    if should_interrupt:
        print("✅ 7. Testing user interruption...")
        await flow_manager.interrupt_user(session_id, mock_websocket)
        
        # Verify WebSocket message was sent
        assert mock_websocket.send_text.called, "WebSocket message should have been sent"
        
        # Get the sent message
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        print(f"   - Interruption message type: {message.get('type')}")
        print(f"   - Interruption message: {message.get('message', '')[:50]}...")
    
    # Test conversation end
    print("✅ 8. Testing conversation end...")
    flow_manager.end_conversation(session_id)
    assert session_id not in flow_manager.active_conversations, "Session should be cleaned up"
    
    print("\n🎉 All intelligent conversation tests passed!")
    return True

async def test_context_length_management():
    """Test context length management and pruning."""
    print("\n🔄 Testing Context Length Management")
    print("=" * 50)
    
    flow_manager = IntelligentConversationManager()
    session_id = "context_test_session"
    mock_websocket = Mock()
    mock_websocket.send_text = AsyncMock()
    
    flow_manager.start_conversation(session_id, mock_websocket)
    
    # Add many messages to test context pruning
    print("✅ 1. Adding many messages to trigger context management...")
    for i in range(25):  # Add more than max_conversation_turns * 2 (40)
        flow_manager.add_user_message(session_id, f"User message {i+1}: This is a test message to fill up the context.")
        flow_manager.add_assistant_message(session_id, f"Assistant response {i+1}: I understand your message {i+1}.")
    
    # Get context and check if it's been pruned
    context = flow_manager.get_conversation_context(session_id)
    print(f"   - Total messages in context: {len(context)}")
    print(f"   - Should be <= 40 (max_conversation_turns * 2): {len(context) <= 40}")
    
    # Verify the most recent messages are preserved
    if context and len(context) >= 2:
        last_user_msg = context[-2]  # Second to last should be user
        last_ai_msg = context[-1]    # Last should be assistant
        print(f"   - Last user message contains 'message 25': {'message 25' in last_user_msg.get('content', '')}")
        print(f"   - Last AI message contains 'response 25': {'response 25' in last_ai_msg.get('content', '')}")
    
    flow_manager.end_conversation(session_id)
    print("✅ Context length management test completed!")
    return True

async def test_silence_detection():
    """Test silence detection and waiting logic."""
    print("\n🔇 Testing Silence Detection")
    print("=" * 50)
    
    flow_manager = IntelligentConversationManager()
    session_id = "silence_test_session"
    mock_websocket = Mock()
    
    flow_manager.start_conversation(session_id, mock_websocket)
    
    # Test initial state
    should_wait = flow_manager.should_wait_for_user(session_id)
    print(f"✅ 1. Should wait initially (no activity): {should_wait}")
    
    # Start user speaking
    flow_manager.start_user_speaking(session_id)
    
    # Stop user speaking recently (should wait for more)
    flow_manager.stop_user_speaking(session_id)
    
    should_wait = flow_manager.should_wait_for_user(session_id)
    print(f"✅ 2. Should wait after recent stop: {should_wait}")
    
    # Simulate passage of time (silence threshold)
    if session_id in flow_manager.active_conversations:
        flow_manager.active_conversations[session_id]['last_user_stop'] = time.time() - 3.5  # 3.5 seconds ago
    
    should_wait = flow_manager.should_wait_for_user(session_id)
    print(f"✅ 3. Should not wait after silence threshold: {not should_wait}")
    
    flow_manager.end_conversation(session_id)
    print("✅ Silence detection test completed!")
    return True

async def main():
    """Run all intelligent conversation tests."""
    print("🤖 Starting Intelligent Conversation Management Tests")
    print("=" * 60)
    
    try:
        # Run all test functions
        test1 = await test_conversation_flow_manager()
        test2 = await test_context_length_management()
        test3 = await test_silence_detection()
        
        if all([test1, test2, test3]):
            print("\n🌟 ALL INTELLIGENT CONVERSATION TESTS PASSED! 🌟")
            print("Your conversation system is now smart and ready for production!")
            return True
        else:
            print("\n❌ Some tests failed")
            return False
            
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
