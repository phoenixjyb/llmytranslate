"""
Global Emergency Interrupt Handler
Provides overlap prevention and emergency keyword detection
"""

import logging
import time
from typing import Set, Dict

logger = logging.getLogger(__name__)

class GlobalInterruptHandler:
    """Singleton class to handle overlapping responses and emergency interrupts globally"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.active_sessions: Set[str] = set()
            self.last_response_times: Dict[str, float] = {}
            self._initialized = True
            logger.info("🚨 GLOBAL INTERRUPT HANDLER: Initialized overlap prevention!")
    
    def check_emergency_interrupt(self, text: str) -> bool:
        """Check if text contains emergency interrupt keywords"""
        if not text:
            return False
            
        text_lower = text.lower().strip()
        emergency_keywords = [
            "okaydokay okaydokay", 
            "okayokday okayokday",
            "okay dokay okay dokay",
            "stop stop",
            "emergency interrupt"
        ]
        
        is_emergency = any(keyword in text_lower for keyword in emergency_keywords)
        
        if is_emergency:
            logger.info(f"🚨 EMERGENCY INTERRUPT DETECTED: '{text[:50]}...'")
            
        return is_emergency
    
    def can_process_request(self, session_id: str) -> bool:
        """Check if session can process new request (overlap prevention)"""
        current_time = time.time()
        
        # Check if session already has active response
        if session_id in self.active_sessions:
            logger.warning(f"🚫 OVERLAP BLOCKED: Session {session_id} already active")
            return False
        
        # Check minimum time between responses
        last_time = self.last_response_times.get(session_id, 0)
        min_interval = 0.5  # 500ms minimum between responses
        
        if current_time - last_time < min_interval:
            logger.warning(f"🚫 RATE LIMITED: Session {session_id} too frequent")
            return False
            
        return True
    
    def start_processing(self, session_id: str):
        """Mark session as actively processing"""
        self.active_sessions.add(session_id)
        self.last_response_times[session_id] = time.time()
        logger.info(f"🚀 PROCESSING: Session {session_id} marked as ACTIVE")
    
    def finish_processing(self, session_id: str):
        """Mark session as finished processing"""
        self.active_sessions.discard(session_id)
        logger.info(f"✅ FINISHED: Session {session_id} processing complete")
    
    def emergency_clear(self, session_id: str):
        """Emergency clear for interrupt scenarios"""
        self.active_sessions.discard(session_id)
        logger.info(f"🚨 EMERGENCY CLEAR: Session {session_id} force cleared")

# Global singleton instance
global_interrupt_handler = GlobalInterruptHandler()
