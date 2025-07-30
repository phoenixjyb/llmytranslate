"""
Interrupt Service for Phone Call Mode
Handles real-time interruption of AI responses during phone calls
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class InterruptService:
    """Service to handle interruption of AI responses in real-time"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.interrupt_callbacks: Dict[str, Callable] = {}
        self.lock = threading.Lock()
        logger.info("Interrupt service initialized")
    
    def register_session(self, session_id: str, websocket=None) -> None:
        """Register a session for interrupt handling"""
        with self.lock:
            self.active_sessions[session_id] = {
                'websocket': websocket,
                'interrupted': False,
                'ai_speaking': False,
                'interrupt_time': None,
                'tts_task': None,
                'llm_task': None,
                'created_at': datetime.now()
            }
        logger.info(f"Session {session_id} registered for interrupt handling")
    
    def unregister_session(self, session_id: str) -> None:
        """Unregister a session from interrupt handling"""
        with self.lock:
            if session_id in self.active_sessions:
                # Cancel any ongoing tasks
                session_data = self.active_sessions[session_id]
                if session_data.get('tts_task'):
                    session_data['tts_task'].cancel()
                if session_data.get('llm_task'):
                    session_data['llm_task'].cancel()
                
                del self.active_sessions[session_id]
                if session_id in self.interrupt_callbacks:
                    del self.interrupt_callbacks[session_id]
                
        logger.info(f"Session {session_id} unregistered from interrupt handling")
    
    def set_ai_speaking(self, session_id: str, speaking: bool, task: Optional[asyncio.Task] = None) -> None:
        """Set AI speaking status for a session"""
        with self.lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['ai_speaking'] = speaking
                if task:
                    if speaking:
                        self.active_sessions[session_id]['tts_task'] = task
                    else:
                        self.active_sessions[session_id]['tts_task'] = None
    
    def set_ai_thinking(self, session_id: str, thinking: bool, task: Optional[asyncio.Task] = None) -> None:
        """Set AI thinking (LLM processing) status for a session"""
        with self.lock:
            if session_id in self.active_sessions:
                if task:
                    if thinking:
                        self.active_sessions[session_id]['llm_task'] = task
                    else:
                        self.active_sessions[session_id]['llm_task'] = None
    
    def interrupt_session(self, session_id: str) -> bool:
        """Interrupt AI response for a specific session"""
        with self.lock:
            if session_id not in self.active_sessions:
                logger.warning(f"Cannot interrupt unknown session: {session_id}")
                return False
            
            session_data = self.active_sessions[session_id]
            
            # Mark as interrupted
            session_data['interrupted'] = True
            session_data['interrupt_time'] = datetime.now()
            
            # Cancel TTS task if active
            if session_data.get('tts_task') and not session_data['tts_task'].done():
                session_data['tts_task'].cancel()
                logger.info(f"TTS task cancelled for session {session_id}")
            
            # Cancel LLM task if active
            if session_data.get('llm_task') and not session_data['llm_task'].done():
                session_data['llm_task'].cancel()
                logger.info(f"LLM task cancelled for session {session_id}")
            
            # Reset AI speaking status
            session_data['ai_speaking'] = False
            
            logger.info(f"Session {session_id} interrupted successfully")
            return True
    
    def is_interrupted(self, session_id: str) -> bool:
        """Check if a session has been interrupted"""
        with self.lock:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id].get('interrupted', False)
            return False
    
    def clear_interrupt(self, session_id: str) -> None:
        """Clear interrupt flag for a session"""
        with self.lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['interrupted'] = False
                self.active_sessions[session_id]['interrupt_time'] = None
                logger.info(f"Interrupt flag cleared for session {session_id}")
    
    def is_ai_speaking(self, session_id: str) -> bool:
        """Check if AI is currently speaking"""
        with self.lock:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id].get('ai_speaking', False)
            return False
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current status of a session"""
        with self.lock:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id].copy()
                # Don't include websocket and tasks in status
                session_data.pop('websocket', None)
                session_data.pop('tts_task', None)
                session_data.pop('llm_task', None)
                return session_data
            return None
    
    def get_all_sessions_status(self) -> Dict[str, Dict]:
        """Get status of all active sessions"""
        with self.lock:
            status = {}
            for session_id, session_data in self.active_sessions.items():
                # Create a copy without websocket and tasks
                clean_data = session_data.copy()
                clean_data.pop('websocket', None)
                clean_data.pop('tts_task', None)
                clean_data.pop('llm_task', None)
                status[session_id] = clean_data
            return status
    
    async def send_interrupt_notification(self, session_id: str, message: str = None) -> None:
        """Send interrupt notification to client"""
        with self.lock:
            if session_id in self.active_sessions:
                websocket = self.active_sessions[session_id].get('websocket')
                if websocket:
                    try:
                        notification = {
                            'type': 'interrupt',
                            'session_id': session_id,
                            'message': message or 'AI response interrupted',
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send_text(str(notification))
                        logger.info(f"Interrupt notification sent to session {session_id}")
                    except Exception as e:
                        logger.error(f"Failed to send interrupt notification: {e}")
    
    def register_interrupt_callback(self, session_id: str, callback: Callable) -> None:
        """Register a callback function to be called when session is interrupted"""
        self.interrupt_callbacks[session_id] = callback
        logger.info(f"Interrupt callback registered for session {session_id}")
    
    async def handle_interrupt_with_callback(self, session_id: str) -> bool:
        """Handle interrupt and call registered callback if available"""
        success = self.interrupt_session(session_id)
        
        if success and session_id in self.interrupt_callbacks:
            try:
                callback = self.interrupt_callbacks[session_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(session_id)
                else:
                    callback(session_id)
                logger.info(f"Interrupt callback executed for session {session_id}")
            except Exception as e:
                logger.error(f"Error executing interrupt callback: {e}")
        
        return success
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than max_age_hours"""
        current_time = datetime.now()
        expired_sessions = []
        
        with self.lock:
            for session_id, session_data in self.active_sessions.items():
                age = current_time - session_data['created_at']
                if age.total_seconds() > (max_age_hours * 3600):
                    expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            self.unregister_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)

# Global instance
interrupt_service = InterruptService()
