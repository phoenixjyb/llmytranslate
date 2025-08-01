"""
Enhanced Phone Call Service with Intelligent Conversation Management
Implements smart turn-taking, context management, and intelligent interaction patterns.
"""

import asyncio
import logging
import json
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IntelligentConversationManager:
    """
    Manages intelligent conversation flow with smart turn-taking and context management.
    Provides proactive conversation management with memory limits and interruption handling.
    """
    
    def __init__(self):
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
        # Turn-taking parameters
        self.min_pause_for_response = 2.0  # Minimum pause before AI responds
        self.max_user_talk_time = 30.0  # Maximum continuous user talk time
        self.natural_break_detection = True  # Detect natural conversation breaks
        
        # Context management
        self.max_conversation_turns = 20  # Maximum turns before context reset
        self.max_total_tokens = 4000  # Approximate token limit
        self.context_reset_warning_turns = 18  # Warn before reset
        
        # Silence and timeout handling
        self.turn_timeout = 5.0  # Seconds to wait for user response
        self.max_silence_duration = 8.0  # Maximum silence before prompting
        self.conversation_timeout = 300.0  # 5 minutes total conversation timeout
        
        # Interruption handling
        self.interruption_phrases = [
            "stop", "wait", "hold on", "pause", "let me", "actually", "but", "however"
        ]
        
    def start_conversation(self, session_id: str, websocket) -> None:
        """Initialize intelligent conversation management for a session."""
        self.active_conversations[session_id] = {
            "websocket": websocket,
            "last_user_input": time.time(),
            "last_ai_response": time.time(),
            "current_turn": "ai",  # Start with AI greeting
            "user_talk_start": None,
            "ai_is_speaking": False,
            "user_is_speaking": False,
            "conversation_turns": 0,
            "total_context_length": 0,
            "silence_prompts_sent": 0,
            "conversation_started": time.time(),
            "is_active": True,
            "waiting_for_response": False,
            "user_response_pending": False,  # Add flag to track pending responses
            "pending_interruption": False,
            "last_pause_duration": 0.0,
            "conversation_history_summary": [],
            "conversation_history": [],  # Add conversation history for testing
            "last_user_stop": 0,  # Add missing fields for test compatibility
            "last_audio_activity": 0,
            "voice_activity_detected": False,
            "last_interruption": 0
        }
        
        # Start conversation with AI greeting
        asyncio.create_task(self._send_intelligent_greeting(session_id))
        
        # Start monitoring task
        asyncio.create_task(self._monitor_intelligent_conversation(session_id))
    
    async def _send_intelligent_greeting(self, session_id: str) -> None:
        """Send contextually appropriate AI greeting."""
        try:
            conversation = self.active_conversations.get(session_id)
            if not conversation:
                return
                
            # Time-based greetings
            current_hour = datetime.now().hour
            if 5 <= current_hour < 12:
                time_greeting = "Good morning"
            elif 12 <= current_hour < 17:
                time_greeting = "Good afternoon"
            elif 17 <= current_hour < 22:
                time_greeting = "Good evening"
            else:
                time_greeting = "Hello"
            
            greetings = [
                f"{time_greeting}! I'm your AI assistant. What's on your mind today?",
                f"{time_greeting}! I'm here to help. What would you like to discuss?",
                f"{time_greeting}! Thanks for calling. How can I assist you?",
                f"{time_greeting}! I'm ready to chat. What brings you here today?"
            ]
            
            import random
            greeting = random.choice(greetings)
            
            await self._send_ai_message(session_id, greeting, "greeting")
            
            conversation["current_turn"] = "user"
            conversation["waiting_for_response"] = True
            conversation["conversation_turns"] += 1
            
        except Exception as e:
            logger.error(f"Failed to send intelligent greeting: {e}")
    
    async def _monitor_intelligent_conversation(self, session_id: str) -> None:
        """Monitor conversation with intelligent turn management."""
        while session_id in self.active_conversations:
            try:
                conversation = self.active_conversations[session_id]
                
                if not conversation["is_active"]:
                    break
                
                current_time = time.time()
                await self._check_conversation_timeouts(session_id, current_time)
                await self._check_user_talk_duration(session_id, current_time)
                await self._check_context_length(session_id)
                await self._handle_intelligent_silence(session_id, current_time)
                
                await asyncio.sleep(0.5)  # Check twice per second for responsiveness
                
            except Exception as e:
                logger.error(f"Error monitoring intelligent conversation {session_id}: {e}")
                break
        
        # Cleanup
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
    
    async def _check_conversation_timeouts(self, session_id: str, current_time: float) -> None:
        """Check for various timeout conditions."""
        conversation = self.active_conversations[session_id]
        
        # Overall conversation timeout
        if current_time - conversation["conversation_started"] > self.conversation_timeout:
            await self._end_conversation(session_id, "timeout", 
                "We've been chatting for a while. Let me wrap up our conversation.")
            return
        
        # Turn timeout when waiting for user - but NOT if user has recently provided input 
        # or if there's a pending response being processed
        if (conversation["waiting_for_response"] and 
            conversation["current_turn"] == "user" and
            not conversation.get("user_response_pending", False) and  # Don't timeout if response pending
            current_time - conversation["last_ai_response"] > self.turn_timeout and
            current_time - conversation["last_user_input"] > self.turn_timeout):  # Don't timeout if recent input
            
            await self._handle_turn_timeout(session_id)
    
    async def _check_user_talk_duration(self, session_id: str, current_time: float) -> None:
        """Monitor if user is talking too long and needs gentle interruption."""
        conversation = self.active_conversations[session_id]
        
        if (conversation["user_is_speaking"] and 
            conversation["user_talk_start"] and
            current_time - conversation["user_talk_start"] > self.max_user_talk_time):
            
            await self._request_user_pause(session_id)
    
    async def _check_context_length(self, session_id: str) -> None:
        """Monitor context length and manage memory."""
        conversation = self.active_conversations[session_id]
        
        if conversation["conversation_turns"] >= self.context_reset_warning_turns:
            if conversation["conversation_turns"] == self.context_reset_warning_turns:
                await self._warn_context_reset(session_id)
            elif conversation["conversation_turns"] >= self.max_conversation_turns:
                await self._perform_context_reset(session_id)
    
    async def _handle_intelligent_silence(self, session_id: str, current_time: float) -> None:
        """Handle silence with context-aware prompts."""
        conversation = self.active_conversations[session_id]
        time_since_last_input = current_time - conversation["last_user_input"]
        
        if (conversation["waiting_for_response"] and 
            conversation["current_turn"] == "user" and
            time_since_last_input > self.max_silence_duration):
            
            await self._send_contextual_prompt(session_id)
    
    async def _request_user_pause(self, session_id: str) -> None:
        """Politely interrupt user who's talking too long."""
        try:
            conversation = self.active_conversations[session_id]
            
            interrupt_messages = [
                "Sorry to interrupt, but let me make sure I understand what you're saying so far...",
                "That's a lot of great information! Let me pause you there and ask a clarifying question...",
                "I want to make sure I'm following you. Can I summarize what I've heard so far?",
                "Hold on - let me process what you've shared. Can you give me a moment?"
            ]
            
            import random
            message = random.choice(interrupt_messages)
            
            await self._send_ai_message(session_id, message, "interruption")
            
            conversation["user_is_speaking"] = False
            conversation["user_talk_start"] = None
            conversation["pending_interruption"] = True
            
        except Exception as e:
            logger.error(f"Failed to request user pause: {e}")
    
    async def _warn_context_reset(self, session_id: str) -> None:
        """Warn user about upcoming context reset."""
        message = ("We've covered a lot of ground in our conversation! "
                  "To keep our chat focused, I might need to summarize and start fresh soon. "
                  "Is there anything specific you'd like me to remember?")
        
        await self._send_ai_message(session_id, message, "context_warning")
    
    async def _perform_context_reset(self, session_id: str) -> None:
        """Reset conversation context with user permission."""
        conversation = self.active_conversations[session_id]
        
        reset_message = ("Our conversation has gotten quite long! "
                        "To continue effectively, I'd like to summarize what we've discussed "
                        "and start with a fresh context. Is that okay with you?")
        
        await self._send_ai_message(session_id, reset_message, "context_reset_request")
        
        # Reset conversation state
        conversation["conversation_turns"] = 0
        conversation["total_context_length"] = 0
        conversation["waiting_for_response"] = True
        conversation["current_turn"] = "user"
    
    async def _send_contextual_prompt(self, session_id: str) -> None:
        """Send context-aware prompts based on conversation state."""
        conversation = self.active_conversations[session_id]
        conversation["silence_prompts_sent"] += 1
        
        if conversation["silence_prompts_sent"] == 1:
            prompts = [
                "I'm here when you're ready. What would you like to discuss?",
                "Take your time. I'm listening when you want to continue.",
                "I'm here to help. What's on your mind?"
            ]
        elif conversation["silence_prompts_sent"] == 2:
            prompts = [
                "Are you still there? I'm ready to continue our conversation.",
                "I'm still here if you'd like to keep chatting.",
                "Feel free to ask me anything or share your thoughts."
            ]
        else:
            await self._end_conversation(session_id, "no_response")
            return
        
        import random
        prompt = random.choice(prompts)
        
        await self._send_ai_message(session_id, prompt, "silence_prompt")
        
        conversation["last_user_input"] = time.time()  # Reset silence timer
    
    async def _handle_turn_timeout(self, session_id: str) -> None:
        """Handle when user doesn't respond in expected timeframe."""
        conversation = self.active_conversations[session_id]
        
        timeout_responses = [
            "I'm giving you a moment to think. Let me know when you're ready to continue.",
            "No rush! I'm here when you want to respond.",
            "Take your time. I'll wait for your response."
        ]
        
        import random
        response = random.choice(timeout_responses)
        
        await self._send_ai_message(session_id, response, "turn_timeout")
    
    async def _send_ai_message(self, session_id: str, text: str, message_type: str) -> None:
        """Send AI message with proper conversation state management."""
        try:
            conversation = self.active_conversations.get(session_id)
            if not conversation:
                return
            
            await conversation["websocket"].send_text(json.dumps({
                "type": "ai_response",
                "text": text,
                "audio_data": None,  # Will be synthesized
                "timestamp": datetime.now().isoformat(),
                "conversation_state": message_type,
                "turn_count": conversation["conversation_turns"]
            }))
            
            conversation["last_ai_response"] = time.time()
            conversation["ai_is_speaking"] = True
            
            # Estimate context length (rough approximation)
            conversation["total_context_length"] += len(text.split())
            
        except Exception as e:
            logger.error(f"Failed to send AI message: {e}")
    
    def detect_natural_break(self, text: str) -> bool:
        """Detect if text contains natural conversation breaks."""
        # Look for sentence endings with pauses
        break_patterns = [
            r'\.\s+',  # Period followed by space
            r'\?\s+',  # Question mark followed by space
            r'!\s+',   # Exclamation followed by space
            r'\.\.\.',  # Ellipsis
            r',\s+and\s+',  # Comma and "and"
            r',\s+so\s+',   # Comma and "so"
        ]
        
        for pattern in break_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def detect_interruption_intent(self, text: str) -> bool:
        """Detect if user wants to interrupt or change topic."""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in self.interruption_phrases)
    
    def start_user_speaking(self, session_id: str) -> None:
        """Mark that user has started speaking."""
        conversation = self.active_conversations.get(session_id)
        if conversation:
            conversation["user_is_speaking"] = True
            conversation["user_talk_start"] = time.time()
            conversation["ai_is_speaking"] = False
            
    def stop_user_speaking(self, session_id: str) -> None:
        """Mark when user stops speaking."""
        conversation = self.active_conversations.get(session_id)
        if conversation:
            conversation["user_is_speaking"] = False
            conversation["last_user_stop"] = time.time()
            
    def is_user_speaking(self, session_id: str) -> bool:
        """Check if user is currently speaking."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return False
        return conversation.get("user_is_speaking", False)
        
    def process_audio_chunk(self, session_id: str, audio_data: bytes) -> None:
        """Process incoming audio chunk for voice activity detection."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return
            
        # Update last audio activity
        conversation["last_audio_activity"] = time.time()
        
        # Simple voice activity detection based on audio data size
        if len(audio_data) > 100:  # Threshold for voice activity
            conversation["voice_activity_detected"] = True
        
    def add_user_message(self, session_id: str, message: str) -> None:
        """Add user message to conversation history and update conversation state."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return
            
        conversation["conversation_history"].append({
            'role': 'user',
            'content': message,
            'timestamp': time.time()
        })
        
        # Critical fix: Reset conversation state when user input is received
        conversation["waiting_for_response"] = False
        conversation["current_turn"] = "ai"  # It's now AI's turn to respond
        conversation["last_user_input"] = time.time()
        conversation["user_response_pending"] = True  # AI should respond to this message
        
    def add_assistant_message(self, session_id: str, message: str) -> None:
        """Add assistant message to conversation history."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return
            
        conversation["conversation_history"].append({
            'role': 'assistant', 
            'content': message,
            'timestamp': time.time()
        })
        
    def should_wait_for_user(self, session_id: str) -> bool:
        """Determine if we should wait for more user input."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return True
            
        current_time = time.time()
        
        # If user is currently speaking, wait
        if conversation.get("user_is_speaking", False):
            return True
            
        # If user stopped speaking recently, wait for silence threshold
        last_stop = conversation.get("last_user_stop", 0)
        if current_time - last_stop < self.min_pause_for_response:
            return True
            
        return False
        
    def should_process_turn(self, session_id: str) -> bool:
        """Determine if we should process the current turn."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return False
            
        # Always process if we have user messages - the timing logic is handled elsewhere
        history = conversation.get("conversation_history", [])
        return len(history) > 0
        
    def should_respond_now(self, session_id: str) -> bool:
        """Determine if we should respond immediately or wait for more input."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return True
            
        current_time = time.time()
        
        # If user is still speaking, don't respond yet
        if conversation.get("user_is_speaking", False):
            return False
            
        # If user stopped speaking recently, wait for the pause threshold
        last_stop = conversation.get("last_user_stop", 0)
        if last_stop > 0 and current_time - last_stop < self.min_pause_for_response:
            return False
            
        return True
        
    def should_interrupt_user(self, session_id: str) -> bool:
        """Determine if we should interrupt the user."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return False
            
        current_time = time.time()
        
        # Check if user has been speaking too long
        speaking_start = conversation.get("user_talk_start")
        if conversation.get("user_is_speaking", False) and speaking_start:
            if current_time - speaking_start > self.max_user_talk_time:
                return True
                
        return False
        
    async def interrupt_user(self, session_id: str, websocket) -> None:
        """Interrupt the user politely."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return
            
        # Send interruption message
        interruption_message = {
            "type": "ai_interruption",
            "message": "I'm sorry to interrupt, but I want to make sure I understand everything you've said so far. Could you please pause for a moment so I can respond?",
            "reason": "long_speaking_duration"
        }
        
        try:
            await websocket.send_text(json.dumps(interruption_message))
            
            # Mark user as interrupted
            conversation["last_interruption"] = time.time()
            conversation["user_is_speaking"] = False
            
        except Exception as e:
            logger.error(f"Failed to send interruption message: {e}")
            
    def get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation context with automatic pruning."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return []
            
        history = conversation.get("conversation_history", [])
        
        # Prune if too many messages (use max_conversation_turns * 2 for user+ai pairs)
        max_messages = self.max_conversation_turns * 2
        if len(history) > max_messages:
            # Keep the most recent messages
            pruned_history = history[-max_messages:]
            conversation["conversation_history"] = pruned_history
            return pruned_history
            
        return history
        
    def handle_ai_response(self, session_id: str) -> None:
        """Handle when AI completes a response."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return
            
        # Mark AI as finished responding
        conversation["ai_is_speaking"] = False
        conversation["last_ai_response"] = time.time()
        # Clear the pending response flag since AI has now responded
        conversation["user_response_pending"] = False
        
    def end_conversation(self, session_id: str) -> None:
        """End and cleanup conversation."""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            logger.info(f"Conversation ended and cleaned up for session {session_id}")
    
    def handle_user_input(self, session_id: str, user_text: str) -> Dict[str, Any]:
        """Handle user input with intelligent analysis."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return {"action": "error", "message": "Session not found"}
        
        conversation["last_user_input"] = time.time()
        conversation["user_is_speaking"] = False
        conversation["user_talk_start"] = None
        conversation["silence_prompts_sent"] = 0
        conversation["conversation_turns"] += 1
        
        # Analyze user input
        has_natural_break = self.detect_natural_break(user_text)
        wants_to_interrupt = self.detect_interruption_intent(user_text)
        
        # Check for conversation ending cues
        ending_phrases = ["goodbye", "bye", "see you", "thank you", "that's all", "end call", "hang up"]
        if any(phrase in user_text.lower() for phrase in ending_phrases):
            asyncio.create_task(self._end_conversation(session_id, "user_initiated"))
            return {"action": "end_conversation", "reason": "user_initiated"}
        
        # Check for context reset confirmation
        reset_confirmations = ["yes", "okay", "sure", "go ahead", "that's fine"]
        if (conversation.get("pending_context_reset") and 
            any(phrase in user_text.lower() for phrase in reset_confirmations)):
            return {"action": "context_reset", "confirmed": True}
        
        conversation["current_turn"] = "ai"
        conversation["waiting_for_response"] = False
        
        return {
            "action": "process_response",
            "has_natural_break": has_natural_break,
            "wants_to_interrupt": wants_to_interrupt,
            "should_respond": True
        }
    
    def handle_ai_response_complete(self, session_id: str) -> None:
        """Mark AI response as complete and ready for user turn."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return
        
        conversation["last_ai_response"] = time.time()
        conversation["ai_is_speaking"] = False
        conversation["current_turn"] = "user"
        conversation["waiting_for_response"] = True
    
    async def _end_conversation(self, session_id: str, reason: str, custom_message: str = None) -> None:
        """End conversation gracefully with appropriate farewell."""
        try:
            conversation = self.active_conversations.get(session_id)
            if not conversation:
                return
            
            if custom_message:
                farewell = custom_message
            elif reason == "timeout":
                farewell = "Our conversation time is up. Thank you for chatting with me! Have a wonderful day!"
            elif reason == "no_response":
                farewell = "I haven't heard from you in a while. Thank you for our conversation! Take care!"
            elif reason == "user_initiated":
                farewell = "Thank you for our great conversation! I enjoyed chatting with you. Goodbye!"
            elif reason == "context_limit":
                farewell = "We've had such a rich conversation! Thank you for sharing so much with me. Have a great day!"
            else:
                farewell = "Thank you for our conversation! I hope it was helpful. Have a great day!"
            
            await conversation["websocket"].send_text(json.dumps({
                "type": "conversation_end",
                "text": farewell,
                "audio_data": None,
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "conversation_summary": {
                    "duration": time.time() - conversation["conversation_started"],
                    "turns": conversation["conversation_turns"],
                    "ended_by": reason
                }
            }))
            
            conversation["is_active"] = False
            
        except Exception as e:
            logger.error(f"Failed to end conversation {session_id}: {e}")
    
    def end_session(self, session_id: str) -> None:
        """Clean up conversation management for ended session."""
        if session_id in self.active_conversations:
            self.active_conversations[session_id]["is_active"] = False
    
    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        """Get detailed conversation state for monitoring."""
        conversation = self.active_conversations.get(session_id)
        if not conversation:
            return {"status": "not_found"}
        
        current_time = time.time()
        return {
            "status": "active" if conversation["is_active"] else "inactive",
            "current_turn": conversation["current_turn"],
            "waiting_for_response": conversation["waiting_for_response"],
            "user_is_speaking": conversation["user_is_speaking"],
            "ai_is_speaking": conversation["ai_is_speaking"],
            "conversation_turns": conversation["conversation_turns"],
            "total_context_length": conversation["total_context_length"],
            "time_since_last_input": current_time - conversation["last_user_input"],
            "time_since_last_response": current_time - conversation["last_ai_response"],
            "conversation_duration": current_time - conversation["conversation_started"],
            "silence_prompts_sent": conversation["silence_prompts_sent"]
        }

# Global instance
conversation_flow_manager = IntelligentConversationManager()
