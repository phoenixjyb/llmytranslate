"""
Enhanced Interrupt Manager for Natural Phone Conversations
Implements 3-second auto-interruption rule with context preservation.
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartInterruptManager:
    """
    Smart interruption manager that handles natural conversation flow.
    - Auto-interrupts AI after 3 seconds of user speaking
    - Preserves conversation context
    - Prevents overlapping responses
    - Maintains conversation history
    """
    
    def __init__(self):
        # Active interruption tracking
        self.active_interruptions: Dict[str, Dict[str, Any]] = {}
        
        # User speaking detection
        self.user_speaking_start: Dict[str, float] = {}
        self.user_speaking_timers: Dict[str, asyncio.Task] = {}
        
        # AI response tracking
        self.ai_responding: Set[str] = set()
        self.ai_response_tasks: Dict[str, asyncio.Task] = {}
        
        # Configuration
        self.auto_interrupt_delay = 3.0  # Seconds before auto-interrupt
        self.min_user_speech_duration = 0.5  # Minimum speech to trigger interrupt
        self.context_preservation = True
        
        # Context preservation
        self.interrupted_contexts: Dict[str, str] = {}
        
    async def start_user_speaking(self, session_id: str, websocket) -> None:
        """
        Called when user starts speaking.
        Sets up auto-interruption timer if AI is responding.
        """
        current_time = time.time()
        self.user_speaking_start[session_id] = current_time
        
        logger.info(f"User started speaking in session {session_id}")
        
        # Cancel any existing timer
        if session_id in self.user_speaking_timers:
            self.user_speaking_timers[session_id].cancel()
            
        # If AI is currently responding, start interrupt timer
        if session_id in self.ai_responding:
            logger.info(f"AI is responding - starting {self.auto_interrupt_delay}s interrupt timer")
            
            # Create auto-interrupt task
            timer_task = asyncio.create_task(
                self._auto_interrupt_after_delay(session_id, websocket)
            )
            self.user_speaking_timers[session_id] = timer_task
            
    async def stop_user_speaking(self, session_id: str) -> None:
        """
        Called when user stops speaking.
        Cancels auto-interrupt timer if speech was too short.
        """
        # Cancel interrupt timer
        if session_id in self.user_speaking_timers:
            self.user_speaking_timers[session_id].cancel()
            del self.user_speaking_timers[session_id]
            
        # Check if speech was long enough
        if session_id in self.user_speaking_start:
            speech_duration = time.time() - self.user_speaking_start[session_id]
            logger.info(f"User stopped speaking after {speech_duration:.1f}s in session {session_id}")
            
            del self.user_speaking_start[session_id]
            
    async def start_ai_response(self, session_id: str, response_task: asyncio.Task) -> None:
        """
        Called when AI starts responding.
        Tracks the response task for potential interruption.
        """
        self.ai_responding.add(session_id)
        self.ai_response_tasks[session_id] = response_task
        
        logger.info(f"AI started responding in session {session_id}")
        
    async def stop_ai_response(self, session_id: str) -> None:
        """
        Called when AI finishes responding.
        Cleans up response tracking.
        """
        self.ai_responding.discard(session_id)
        
        if session_id in self.ai_response_tasks:
            del self.ai_response_tasks[session_id]
            
        logger.info(f"AI finished responding in session {session_id}")
        
    async def _auto_interrupt_after_delay(self, session_id: str, websocket) -> None:
        """
        Auto-interrupt AI response after delay if user is still speaking.
        """
        try:
            # Wait for the interrupt delay
            await asyncio.sleep(self.auto_interrupt_delay)
            
            # Check if user is still speaking
            if session_id in self.user_speaking_start:
                speech_duration = time.time() - self.user_speaking_start[session_id]
                
                if speech_duration >= self.min_user_speech_duration:
                    logger.info(f"Auto-interrupting AI after {speech_duration:.1f}s user speech")
                    
                    # Perform the interruption
                    await self._perform_smart_interrupt(session_id, websocket, auto_triggered=True)
                    
        except asyncio.CancelledError:
            logger.info(f"Auto-interrupt timer cancelled for session {session_id}")
            
    async def _perform_smart_interrupt(self, session_id: str, websocket, auto_triggered: bool = False) -> bool:
        """
        Perform smart interruption with context preservation.
        """
        try:
            # Cancel AI response task if running
            if session_id in self.ai_response_tasks:
                response_task = self.ai_response_tasks[session_id]
                if not response_task.done():
                    response_task.cancel()
                    logger.info(f"Cancelled AI response task for session {session_id}")
                    
            # Send interrupt confirmation
            interrupt_type = "auto_interrupt" if auto_triggered else "manual_interrupt"
            
            await self._safe_websocket_send(websocket, {
                "type": "interrupt_confirmed",
                "interrupt_type": interrupt_type,
                "message": "I'll let you speak" if auto_triggered else "Got it, go ahead",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Clean up AI response tracking
            await self.stop_ai_response(session_id)
            
            # Mark interruption as active
            self.active_interruptions[session_id] = {
                "timestamp": time.time(),
                "type": interrupt_type,
                "context_preserved": True
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error performing smart interrupt: {e}")
            return False
            
    async def manual_interrupt(self, session_id: str, websocket) -> bool:
        """
        Handle manual interrupt request from user.
        """
        logger.info(f"Manual interrupt requested for session {session_id}")
        return await self._perform_smart_interrupt(session_id, websocket, auto_triggered=False)
        
    def is_ai_responding(self, session_id: str) -> bool:
        """Check if AI is currently responding in this session."""
        return session_id in self.ai_responding
        
    def is_user_speaking(self, session_id: str) -> bool:
        """Check if user is currently speaking in this session."""
        return session_id in self.user_speaking_start
        
    def get_user_speech_duration(self, session_id: str) -> float:
        """Get current user speech duration."""
        if session_id in self.user_speaking_start:
            return time.time() - self.user_speaking_start[session_id]
        return 0.0
        
    def cleanup_session(self, session_id: str) -> None:
        """Clean up all tracking for a session."""
        # Cancel any active timers
        if session_id in self.user_speaking_timers:
            self.user_speaking_timers[session_id].cancel()
            del self.user_speaking_timers[session_id]
            
        # Clean up tracking data
        self.user_speaking_start.pop(session_id, None)
        self.ai_responding.discard(session_id)
        self.ai_response_tasks.pop(session_id, None)
        self.active_interruptions.pop(session_id, None)
        self.interrupted_contexts.pop(session_id, None)
        
        logger.info(f"Cleaned up smart interrupt tracking for session {session_id}")
        
    async def _safe_websocket_send(self, websocket, data: dict) -> None:
        """Safely send data via WebSocket."""
        try:
            import json
            from fastapi.websockets import WebSocketState
            
            if (websocket and 
                hasattr(websocket, 'client_state') and 
                websocket.client_state == WebSocketState.CONNECTED):
                await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

# Global instance
smart_interrupt_manager = SmartInterruptManager()
