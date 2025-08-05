"""
Phone Call API routes.
Handles real-time phone call conversations using WebSocket + STT + LLM + TTS pipeline.
"""

import asyncio
import json
import logging
import uuid
import base64
import io
import time
import re
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...services.stt_service import stt_service
from ...services.realtime_stt_service import realtime_stt_service
from ...services.tts_service import tts_service
from ...services.background_music_service import background_music_service
from ...services.kid_friendly_service import kid_friendly_service
from ...services.interrupt_service import interrupt_service
from ...services.call_history_service import call_history_service
from ...services.optimized_llm_service import optimized_llm_service
from ...services.performance_monitor import performance_monitor
from ...services.quality_monitor import quality_monitor
from ...services.connection_pool_manager import connection_pool_manager
from ...services.conversation_flow_manager import conversation_flow_manager
from ...services.ollama_client import ollama_client

# Phase 4: Service client aliases for optimization handlers
stt_client = stt_service
tts_client = tts_service
audio_processor = background_music_service  # Placeholder - needs audio processing service

# Import TTS fallback for when main TTS is not available
from ...services.simple_tts_fallback import simple_tts_fallback

def clean_text_for_tts(text: str) -> str:
    """
    Clean text for TTS by removing emojis, special symbols, and formatting.
    
    Args:
        text: Raw text that may contain emojis and special characters
        
    Returns:
        Cleaned text suitable for TTS synthesis
    """
    # Remove emojis and emoticons
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub('', text)
    
    # Remove common markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'_(.*?)_', r'\1', text)        # _underline_ -> underline
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code` -> code
    
    # Remove excessive punctuation and symbols
    text = re.sub(r'[^\w\s\.,!?;:\-\'"()]', ' ', text)  # Keep basic punctuation
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove leading/trailing punctuation that might confuse TTS
    text = text.strip('.,!?;:')
    
    return text

# Process Status Helper Functions
async def safe_websocket_send(websocket: WebSocket, data: dict):
    """Safely send data via WebSocket, checking connection state first."""
    try:
        # Check if WebSocket is still connected (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)
        if websocket.client_state == 1:  # 1 = OPEN
            await websocket.send_text(json.dumps(data))
            return True
        else:
            logger.warning(f"WebSocket not open (state: {websocket.client_state}), skipping send")
            return False
    except Exception as e:
        logger.error(f"Failed to send WebSocket message: {e}")
        return False

async def send_process_status(websocket: WebSocket, stage: str, status: str, details: str = ""):
    """Send process status update to the frontend."""
    await safe_websocket_send(websocket, {
        "type": "process_status",
        "stage": stage,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

async def send_stage_active(websocket: WebSocket, stage: str, details: str = ""):
    """Mark a stage as active."""
    await send_process_status(websocket, stage, "active", details)

async def send_stage_completed(websocket: WebSocket, stage: str, details: str = ""):
    """Mark a stage as completed."""
    await send_process_status(websocket, stage, "completed", details)

async def send_stage_error(websocket: WebSocket, stage: str, error: str):
    """Mark a stage as error."""
    await send_process_status(websocket, stage, "error", f"Error: {error}")

# Phase 4: Helper function for quality monitoring
def get_overall_quality():
    """Get overall service quality from quality monitor."""
    quality_report = quality_monitor.get_quality_report()
    # Extract overall quality from report or return default
    overall_quality = quality_report.get('overall_quality', 'good')
    
    # Create a simple quality object
    class QualityLevel:
        def __init__(self, value):
            self.value = value
    
    return QualityLevel(overall_quality)
from ...storage.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/phone", tags=["phone-call"])

# CRITICAL DEBUG: This is the MOBILE version - should NOT appear in main service!
logger.info("🚨🚨🚨 MOBILE PHONE_CALL.PY MODULE LOADED - WRONG FILE! 🚨🚨🚨")
logger.info("❌ ERROR: Main service is importing mobile version instead of main version!")

# Phone call session models
class PhoneCallSession(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    call_id: Optional[str] = None  # Phase 3: Link to call history
    status: str = "idle"  # idle, dialing, connected, ended
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    settings: Dict[str, Any] = {}
    conversation_history: list = []

class PhoneCallSettings(BaseModel):
    language: str = "en"
    model: str = "gemma2:2b"
    speed: float = 1.0
    kid_friendly: bool = False
    background_music: bool = True
    voice: str = "default"
    noise_reduction: bool = False
    interrupt_detection: bool = False
    
    class Config:
        # Allow extra fields but ignore them
        extra = "ignore"
    
    @classmethod
    def create_with_defaults(cls, data: Dict[str, Any]) -> 'PhoneCallSettings':
        """Create PhoneCallSettings with proper defaults, handling None values."""
        # Clean the data by removing None values and using defaults
        clean_data = {}
        for key, value in data.items():
            if value is not None:
                clean_data[key] = value
        
        # Ensure critical fields have proper defaults
        defaults = {
            "language": "en",
            "model": "gemma2:2b", 
            "speed": 1.0,
            "kid_friendly": False,
            "background_music": True,
            "voice": "default",
            "noise_reduction": False,
            "interrupt_detection": False
        }
        
        # Apply defaults for missing or None values
        for key, default_value in defaults.items():
            if key not in clean_data or clean_data[key] is None:
                clean_data[key] = default_value
        
        return cls(**clean_data)

class PhoneCallManager:
    """Manages active phone call sessions with enhanced audio processing."""
    
    def __init__(self):
        self.active_sessions: Dict[str, PhoneCallSession] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}  # Buffer audio chunks per session
        self.conversation_manager = ConversationManager()
        
        # Audio processing settings
        self.audio_chunk_duration = 3.0  # seconds
        self.min_audio_length = 1000  # bytes
        self.max_buffer_size = 10  # max chunks to buffer
    
    def create_session(self, session_id: str, settings: PhoneCallSettings) -> PhoneCallSession:
        """Create a new phone call session."""
        session = PhoneCallSession(
            session_id=session_id,
            status="dialing",
            start_time=datetime.now(),
            settings=settings.dict()
        )
        self.active_sessions[session_id] = session
        self.audio_buffers[session_id] = []  # Initialize audio buffer
        return session
    
    def get_session(self, session_id: str) -> Optional[PhoneCallSession]:
        """Get an active session by ID."""
        return self.active_sessions.get(session_id)
    
    def end_session(self, session_id: str):
        """End a phone call session with Phase 3 cleanup."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = "ended"
            session.end_time = datetime.now()
            
            # Phase 3: End call history tracking
            if hasattr(session, 'call_id') and session.call_id:
                call_history_service.end_call(session.call_id)
            
            # Phase 3: Unregister from interrupt service
            interrupt_service.unregister_session(session_id)
            
            # Save conversation to storage
            if session.conversation_history:
                asyncio.create_task(self._save_conversation(session))
            
            # Clean up
            del self.active_sessions[session_id]
            if session_id in self.websockets:
                del self.websockets[session_id]
            if session_id in self.audio_buffers:
                del self.audio_buffers[session_id]
    
    async def _save_conversation(self, session: PhoneCallSession):
        """Save phone call conversation to storage."""
        try:
            conversation_id = f"phone-{session.session_id}"
            messages = []
            
            for interaction in session.conversation_history:
                if interaction.get("type") == "user_speech":
                    messages.append({
                        "role": "user",
                        "content": interaction["content"],
                        "timestamp": interaction["timestamp"],
                        "metadata": {"type": "phone_call", "audio_duration": interaction.get("audio_duration")}
                    })
                elif interaction.get("type") == "ai_response":
                    messages.append({
                        "role": "assistant", 
                        "content": interaction["content"],
                        "timestamp": interaction["timestamp"],
                        "metadata": {"type": "phone_call", "processing_time": interaction.get("processing_time")}
                    })
            
            await self.conversation_manager.save_conversation(
                conversation_id=conversation_id,
                messages=messages,
                model_used=session.settings.get("model", "gemma2:2b"),
                title=f"Phone Call - {session.start_time.strftime('%Y-%m-%d %H:%M')}"
            )
            logger.info(f"Saved phone call conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to save phone call conversation: {e}")
    
    def add_audio_chunk(self, session_id: str, audio_data: bytes) -> bool:
        """
        Add audio chunk to session buffer and return True if ready for processing.
        """
        if session_id not in self.audio_buffers:
            return False
        
        buffer = self.audio_buffers[session_id]
        buffer.append(audio_data)
        
        # Keep buffer size manageable
        if len(buffer) > self.max_buffer_size:
            buffer.pop(0)  # Remove oldest chunk
        
        # Check if we have enough audio to process
        total_size = sum(len(chunk) for chunk in buffer)
        return total_size >= self.min_audio_length * 2  # 2x minimum for better quality
    
    def get_buffered_audio(self, session_id: str) -> bytes:
        """
        Get and clear buffered audio for processing.
        """
        if session_id not in self.audio_buffers:
            return b''
        
        buffer = self.audio_buffers[session_id]
        if not buffer:
            return b''
        
        # Combine all chunks
        combined_audio = b''.join(buffer)
        
        # Clear buffer
        buffer.clear()
        
        return combined_audio

# Global phone call manager
phone_manager = PhoneCallManager()

@router.websocket("/stream")
async def phone_call_websocket(websocket: WebSocket):
    """Enhanced WebSocket endpoint for real-time phone call communication with Phase 4 optimization."""
    await websocket.accept()
    session_id = None
    call_start_time = time.time()
    
    try:
        # Phase 4: Check initial service quality
        initial_quality = get_overall_quality()
        if initial_quality.value == "poor":
            # await quality_monitor.attempt_service_recovery()  # TODO: Implement
            logger.warning("Service quality is poor")
            
        logger.info(f"Starting phone call WebSocket with quality: {initial_quality.value}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            session_id = message.get("session_id")
            
            # Debug: Log all incoming messages to help diagnose audio input issues
            logger.info(f"Received WebSocket message: type={message_type}, session_id={session_id}, keys={list(message.keys()) if message else 'None'}")
            
            if message_type == "session_start":
                # Phase 4: Enhanced session start with optimization setup
                await handle_optimized_session_start(websocket, message)
                phone_manager.websockets[session_id] = websocket
                
                # Phase 4: Initialize performance monitoring for session
                user_id = message.get("user_id")
                kid_friendly = message.get("settings", {}).get("kid_friendly", False)
                performance_monitor.record_call_start(session_id, user_id, kid_friendly)
                
                # Phase 4: Setup connection pooling
                settings = message.get("settings", {})
                if settings.get("connection_pooling", True):
                    # Use the actual method that exists
                    connection_pool_manager.optimize_for_phone_calls()
                    logger.info("Connection pooling optimized for phone calls")
                
                # Phase 4: Pre-warm optimized LLM
                model = settings.get("model", "gemma2:2b")
                await optimized_llm_service.warmup_models()
                
                # Start proactive conversation management
                conversation_flow_manager.start_conversation(session_id, websocket)
                logger.info(f"Started intelligent conversation flow management for session {session_id}")
                
            elif message_type == "audio_data":
                # Mark user as speaking when audio data arrives
                conversation_flow_manager.start_user_speaking(session_id)
                logger.info(f"Received audio_data message for session {session_id}")
                
                # Phase 4: Enhanced audio processing with performance tracking
                await handle_optimized_audio_data(websocket, message)
                
            elif message_type == "interrupt":
                await handle_interrupt(websocket, message)
                
            elif message_type == "settings_update":
                await handle_settings_update(websocket, message)
                
            elif message_type == "ping":
                # Phase 4: Enhanced ping with performance stats
                await handle_optimized_ping(websocket, message)
                
            elif message_type == "session_end":
                # Phase 4: Enhanced session end with performance summary
                await handle_optimized_session_end(websocket, message, call_start_time)
                break
                
            else:
                # Handle unknown message types - check if it contains audio data
                if message.get("audio_data") or message.get("audio"):
                    logger.info(f"Treating unknown message type '{message_type}' as audio data")
                    # Mark user as speaking when audio data arrives
                    conversation_flow_manager.start_user_speaking(session_id)
                    
                    # Process as audio data
                    await handle_optimized_audio_data(websocket, message)
                else:
                    logger.warning(f"Unknown message type: {message_type}, keys: {list(message.keys())}")
                    await safe_websocket_send(websocket, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        # Phase 4: Record disconnection
        if session_id:
            call_duration = time.time() - call_start_time
            performance_monitor.record_call_end(session_id, success=False)
            performance_monitor.record_audio_issue(session_id, "disconnect", f"Duration: {call_duration:.2f}s")
            
            # Clean up conversation flow manager
            conversation_flow_manager.end_conversation(session_id)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        
        # Phase 4: Record error
        if session_id:
            call_duration = time.time() - call_start_time
            performance_monitor.record_call_end(session_id, success=False)
            
            # Clean up conversation flow manager on error
            conversation_flow_manager.end_conversation(session_id)
            performance_monitor.record_audio_issue(session_id, "websocket_error", f"Error: {str(e)}, Duration: {call_duration:.2f}s")
        
        # Only try to send error message if WebSocket is still connected
        try:
            if websocket.client_state != 3:  # 3 = DISCONNECTED
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Connection error: {str(e)}"
                }))
        except Exception as send_error:
            logger.warning(f"Failed to send error message: {send_error}")
    finally:
        if session_id:
            phone_manager.end_session(session_id)
            # Clean up conversation flow management
            conversation_flow_manager.end_conversation(session_id)
            logger.info(f"Cleaned up session {session_id}")

# Phase 3 & 4: Helper function for interruptible LLM responses with optimization
async def get_interruptible_llm_response(session: PhoneCallSession, user_text: str, 
                                        conversation_context: list, background_music_task=None):
    """Get optimized LLM response with interrupt support and performance monitoring."""
    session_id = session.session_id
    
    print(f"DEBUG: get_interruptible_llm_response called with user_text: '{user_text}'")  # Explicit debug print
    
    try:
        # Phase 4: Start performance monitoring
        performance_monitor.record_call_start(session_id, getattr(session, 'user_id', None), 
                                            session.settings.get('kid_friendly', False))
        
        # Phase 4: Select optimal model for phone call
        kid_friendly_mode = session.settings.get('kid_friendly', False)
        optimal_model = optimized_llm_service.get_optimal_model_for_phone_call(
            kid_friendly=kid_friendly_mode,
            language=session.settings.get('language', 'en')
        )
        
        logger.info(f"Using optimized model: {optimal_model} for session {session_id}")
        
        # Create interruptible LLM task
        llm_start_time = time.time()
        
        # Phase 4: Use optimized LLM service with timeout and performance tracking
        llm_task = asyncio.create_task(optimized_llm_service.fast_completion(
            message=user_text,
            model=optimal_model,
            conversation_context=conversation_context,
            timeout=30.0  # Extended timeout for more reliable phone calls
        ))
        
        # Register LLM task for interrupt handling
        interrupt_service.set_ai_thinking(session.session_id, True, llm_task)
        
        try:
            llm_response = await llm_task
        except asyncio.TimeoutError:
            # Phase 4: Handle timeout with fallback
            logger.warning(f"LLM timeout for session {session_id}, attempting fallback")
            quality_monitor.record_service_performance("llm", 8.0, False, "timeout")
            
            # Try emergency fallback
            fallback_model = "gemma2:2b"  # Faster fallback model
            llm_task = asyncio.create_task(optimized_llm_service.fast_completion(
                message=user_text,
                model=fallback_model,
                conversation_context=conversation_context[-3:],  # Shorter context
                timeout=15.0  # Extended fallback timeout
            ))
            
            try:
                llm_response = await llm_task
                logger.info(f"Fallback successful with {fallback_model}")
            except asyncio.TimeoutError:
                # Ultimate fallback - simple response
                logger.error(f"All LLM attempts failed for session {session_id}")
                return None, 0.0
                
        except asyncio.CancelledError:
            # Task was interrupted
            logger.info(f"LLM task interrupted for session {session.session_id}")
            await interrupt_service.send_interrupt_notification(
                session.session_id, "AI response interrupted"
            )
            return None, 0.0
        finally:
            interrupt_service.set_ai_thinking(session.session_id, False)
            # Cancel background music if it's running
            if background_music_task:
                background_music_task.cancel()
        
        llm_end_time = time.time()
        llm_duration = llm_end_time - llm_start_time
        
        # Phase 4: Record performance metrics
        llm_success = llm_response.get("success", False)
        performance_monitor.record_llm_performance(
            session_id=session_id,
            duration=llm_duration,
            model=optimal_model,
            input_length=len(user_text),
            output_length=len(llm_response.get("response", "")),
            success=llm_success,
            error=llm_response.get("error") if not llm_success else None
        )
        
        # Phase 4: Record quality metrics
        quality_level = quality_monitor.record_service_performance(
            "llm", llm_duration, llm_success, llm_response.get("error")
        )
        
        if not llm_success:
            raise Exception(f"LLM processing failed: {llm_response.get('error', 'Unknown error')}")
        
        ai_text = llm_response["response"]
        
        logger.info(f"Phone call AI response ({llm_duration:.2f}s, quality: {quality_level.value}): {ai_text}")
        
        return ai_text, llm_duration
        
    except Exception as e:
        logger.error(f"Error in optimized LLM response generation: {e}")
        
        # Phase 4: Record failure
        performance_monitor.record_llm_performance(
            session_id=session_id,
            duration=time.time() - llm_start_time if 'llm_start_time' in locals() else 0.0,
            model=optimal_model if 'optimal_model' in locals() else "unknown",
            input_length=len(user_text),
            output_length=0,
            success=False,
            error=str(e)
        )
        
        return None, 0.0

async def handle_session_start(websocket: WebSocket, message: Dict):
    """Handle phone call session start with Phase 3 enhancements."""
    session_id = message["session_id"]
    settings_data = message.get("settings", {})
    user_id = message.get("user_id", "anonymous")
    
    try:
        settings = PhoneCallSettings.create_with_defaults(settings_data)
        session = phone_manager.create_session(session_id, settings)
        session.status = "connected"
        session.user_id = user_id
        
        # Phase 3: Register with interrupt service
        interrupt_service.register_session(session_id, websocket)
        
        # Phase 3: Start call history tracking
        call_id = call_history_service.start_call(
            user_id=user_id,
            session_id=session_id,
            kid_friendly_mode=settings.kid_friendly,
            language=settings.language
        )
        session.call_id = call_id
        
        # Phase 3: Set up kid-friendly mode if enabled
        if settings.kid_friendly:
            logger.info(f"Kid-friendly mode enabled for session {session_id}")
        
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Phone call connected successfully",
            "session_id": session_id,
            "call_id": call_id,
            "kid_friendly_mode": settings.kid_friendly
        }))
        
        # Send initial greeting if kid-friendly mode
        if settings.kid_friendly:
            greeting = kid_friendly_service.kid_friendly_prompts[
                'chinese' if settings.language in ['zh', 'chinese'] else 'english'
            ]['greeting']
            
            await websocket.send_text(json.dumps({
                "type": "ai_message",
                "message": greeting,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))
        
        logger.info(f"Phone call session started: {session_id} (kid-friendly: {settings.kid_friendly})")
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Failed to start call: {str(e)}"
        }))

async def handle_audio_data(websocket: WebSocket, message: Dict):
    """Handle incoming audio data for transcription and processing."""
    session_id = message["session_id"]
    
    # Validate audio data exists - check both possible field names
    if "audio" not in message and "audio_data" not in message:
        logger.error("Missing audio data in message")
        await websocket.send_text(json.dumps({
            "type": "error", 
            "message": "Missing audio data"
        }))
        return
        
    # Support both field names for backward compatibility
    audio_data = message.get("audio") or message.get("audio_data")
    timestamp = message.get("timestamp", datetime.now().isoformat())
    
    session = phone_manager.get_session(session_id)
    if not session:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Session not found"
        }))
        return
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Add to audio buffer
        is_ready = phone_manager.add_audio_chunk(session_id, audio_bytes)
        
        if not is_ready:
            # Not enough audio yet, continue buffering
            return
        
        # Get buffered audio for processing
        buffered_audio = phone_manager.get_buffered_audio(session_id)
        
        # Skip processing if audio is too short
        if len(buffered_audio) < 2000:  # Increased minimum size
            return
        
        # Send status update to show we're processing
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Processing audio...",
            "session_id": session_id
        }))
        
        # Step 1: Speech to Text using real-time service
        stt_start_time = time.time()
        stt_result = await realtime_stt_service.transcribe_streaming_audio(
            audio_data=buffered_audio,
            format="webm",
            language=session.settings.get("language", "en")
        )
        stt_end_time = time.time()
        
        if not stt_result["success"]:
            logger.warning(f"STT failed: {stt_result.get('error', 'Unknown error')}")
            return
            
        user_text = stt_result["text"].strip()
        if not user_text:
            return  # Skip if no speech detected
        
        # Log transcription with timing
        logger.info(f"Phone call transcription ({stt_end_time - stt_start_time:.2f}s): {user_text}")
        
        # Send transcription to client
        await websocket.send_text(json.dumps({
            "type": "transcription",
            "text": user_text,
            "session_id": session_id,
            "processing_time": stt_end_time - stt_start_time
        }))
        
        # Add to conversation history
        session.conversation_history.append({
            "type": "user_speech",
            "content": user_text,
            "timestamp": timestamp,
            "audio_duration": len(buffered_audio) / 16000,  # Approximate duration
            "stt_time": stt_end_time - stt_start_time
        })
        
        # Step 2: Process with LLM
        await process_llm_response(websocket, session, user_text)
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Audio processing failed: {str(e)}"
        }))
        
        # Reset audio buffer on error
        if session_id in phone_manager.audio_buffers:
            phone_manager.audio_buffers[session_id].clear()

async def process_llm_response(websocket: WebSocket, session: PhoneCallSession, user_text: str):
    """Process user input with LLM and generate response."""
    try:
        # Send background music if enabled
        background_music_task = None
        if session.settings.get("background_music", True):
            background_music_task = asyncio.create_task(
                send_background_music(websocket, session.session_id)
            )
        
        # Phase 3: Enhanced kid-friendly system prompt and topic validation
        system_prompt = ""
        if session.settings.get("kid_friendly", False):
            system_prompt = kid_friendly_service.get_kid_friendly_prompt_prefix(
                session.settings.get("language", "en")
            )
        
        # Build conversation context
        conversation_context = []
        if system_prompt:
            conversation_context.append({"role": "system", "content": system_prompt})
        
        # Add recent conversation history for context
        for interaction in session.conversation_history[-6:]:  # Last 6 interactions for context
            if interaction["type"] == "user_speech":
                conversation_context.append({"role": "user", "content": interaction["content"]})
            elif interaction["type"] == "ai_response":
                conversation_context.append({"role": "assistant", "content": interaction["content"]})
        
        # Add current user message
        conversation_context.append({"role": "user", "content": user_text})
        
        # Phase 3: Check for inappropriate topics in kid-friendly mode
        if session.settings.get("kid_friendly", False):
            if not kid_friendly_service.validate_topic(user_text):
                redirect_message = kid_friendly_service.get_topic_redirect_message(
                    session.settings.get("language", "en")
                )
                ai_text = redirect_message
                llm_processing_time = 0.0
                logger.info(f"Redirected inappropriate topic in kid-friendly mode")
            else:
                # Get LLM response with interrupt support
                ai_text, llm_processing_time = await get_interruptible_llm_response(
                    session, user_text, conversation_context, background_music_task
                )
                if ai_text is None:  # Interrupted
                    return
        else:
            # Normal mode with interrupt support
            ai_text, llm_processing_time = await get_interruptible_llm_response(
                session, user_text, conversation_context, background_music_task
            )
            if ai_text is None:  # Interrupted
                return
        
        # Phase 3: Apply kid-friendly filtering if enabled
        if session.settings.get("kid_friendly", False):
            original_text = ai_text
            ai_text = kid_friendly_service.filter_response(
                ai_text, session.settings.get("language", "en")
            )
            ai_text = kid_friendly_service.enhance_for_kids(
                ai_text, session.settings.get("language", "en")
            )
            
            # Log if content was filtered
            if original_text != ai_text:
                kid_friendly_service.log_kid_interaction(
                    session.session_id, user_text, ai_text, True
                )
                logger.info(f"Applied kid-friendly filtering to response")
        
        # Step 3: Text to Speech with interrupt support
        tts_start_time = time.time()
        
        # Phase 3: Create interruptible TTS task
        tts_task = asyncio.create_task(tts_service.synthesize_speech_api(
            text=ai_text,
            language=session.settings.get("language", "en"),
            voice=session.settings.get("voice", "default"),
            speed=session.settings.get("speed", 1.0),
            tts_mode="fast"  # Use fast mode for phone calls
        ))
        
        # Register TTS task for interrupt handling
        interrupt_service.set_ai_speaking(session.session_id, True, tts_task)
        
        try:
            tts_result = await tts_task
        except asyncio.CancelledError:
            # TTS was interrupted
            logger.info(f"TTS task interrupted for session {session.session_id}")
            await interrupt_service.send_interrupt_notification(
                session.session_id, "Speech synthesis interrupted"
            )
            return
        finally:
            interrupt_service.set_ai_speaking(session.session_id, False)
        
        tts_end_time = time.time()
        
        if not tts_result["success"]:
            raise Exception(f"TTS failed: {tts_result.get('error', 'Unknown error')}")
        
        # Phase 3: Add message to call history
        if hasattr(session, 'call_id'):
            call_history_service.add_message(
                call_id=session.call_id,
                speaker="user",
                message=user_text,
                duration_ms=0,
                was_interrupted=False
            )
            call_history_service.add_message(
                call_id=session.call_id,
                speaker="ai",
                message=ai_text,
                duration_ms=int((tts_end_time - tts_start_time) * 1000),
                was_interrupted=interrupt_service.is_interrupted(session.session_id)
            )
        
        # Add to conversation history
        session.conversation_history.append({
            "type": "ai_response",
            "content": ai_text,
            "timestamp": datetime.now().isoformat(),
            "processing_time": llm_processing_time,
            "tts_time": tts_end_time - tts_start_time
        })
        
        # Send response to client
        await websocket.send_text(json.dumps({
            "type": "ai_response",
            "text": ai_text,
            "audio": tts_result["audio_data"],
            "session_id": session.session_id,
            "timing": {
                "llm_time": llm_processing_time,
                "tts_time": tts_end_time - tts_start_time,
                "total_time": llm_processing_time + (tts_end_time - tts_start_time)
            }
        }))
        
    except Exception as e:
        logger.error(f"LLM processing error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"AI processing failed: {str(e)}"
        }))

async def send_background_music(websocket: WebSocket, session_id: str):
    """Send background music during AI processing."""
    try:
        # Wait a short delay before starting music
        await asyncio.sleep(0.5)
        
        # Get background music
        music = await background_music_service.get_background_music(duration=15.0)
        
        if music and music.get("audio_data"):
            await websocket.send_text(json.dumps({
                "type": "background_music",
                "audio": music["audio_data"],
                "format": music.get("format", "wav"),
                "volume": music.get("volume", 0.3),
                "session_id": session_id
            }))
        
    except asyncio.CancelledError:
        # Background music was cancelled (normal when LLM finishes quickly)
        pass
    except Exception as e:
        logger.warning(f"Background music error: {e}")

async def handle_interrupt(websocket: WebSocket, message: Dict):
    """Handle user interrupt request with Phase 3 enhancements."""
    session_id = message["session_id"]
    
    # Phase 3: Use interrupt service to stop AI processing
    success = await interrupt_service.handle_interrupt_with_callback(session_id)
    
    if success:
        await websocket.send_text(json.dumps({
            "type": "interrupt_confirmed",
            "message": "AI processing stopped",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Clear any interrupt flags for next interaction
        interrupt_service.clear_interrupt(session_id)
        
        logger.info(f"Phone call interrupted successfully: {session_id}")
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to interrupt AI",
            "session_id": session_id
        }))
        logger.warning(f"Failed to interrupt phone call: {session_id}")

async def handle_settings_update(websocket: WebSocket, message: Dict):
    """Handle settings update during call."""
    session_id = message["session_id"]
    new_settings = message.get("settings", {})
    
    session = phone_manager.get_session(session_id)
    if session:
        session.settings.update(new_settings)
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Settings updated",
            "session_id": session_id
        }))
        logger.info(f"Phone call settings updated: {session_id}")

async def handle_session_end(websocket: WebSocket, message: Dict):
    """Handle phone call session end with Phase 3 enhancements."""
    session_id = message["session_id"]
    
    session = phone_manager.get_session(session_id)
    
    # Phase 3: End call history tracking
    if session and hasattr(session, 'call_id'):
        call_history_service.end_call(session.call_id)
        logger.info(f"Call history ended for call_id: {session.call_id}")
    
    # Phase 3: Unregister from interrupt service
    interrupt_service.unregister_session(session_id)
    
    # End the session
    phone_manager.end_session(session_id)
    
    await websocket.send_text(json.dumps({
        "type": "session_ended",
        "message": "Phone call ended successfully",
        "session_id": session_id,
        "call_summary": {
            "duration": str(datetime.now() - session.start_time) if session and session.start_time else "Unknown",
            "messages_exchanged": len(session.conversation_history) if session else 0
        }
    }))
    
    logger.info(f"Phone call session ended: {session_id}")

@router.post("/dial")
async def start_phone_call(settings: PhoneCallSettings):
    """Start a new phone call session."""
    try:
        session_id = f"phone-{uuid.uuid4().hex[:8]}"
        session = phone_manager.create_session(session_id, settings)
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "status": session.status,
            "message": "Phone call session created. Connect via WebSocket."
        })
        
    except Exception as e:
        logger.error(f"Failed to start phone call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start phone call: {str(e)}")

@router.post("/hangup/{session_id}")
async def end_phone_call(session_id: str):
    """End a phone call session."""
    try:
        session = phone_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        phone_manager.end_session(session_id)
        
        return JSONResponse({
            "success": True,
            "message": "Phone call ended successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end phone call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end phone call: {str(e)}")

@router.get("/status/{session_id}")
async def get_call_status(session_id: str):
    """Get status of a phone call session."""
    session = phone_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return JSONResponse({
        "session_id": session.session_id,
        "status": session.status,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "conversation_length": len(session.conversation_history),
        "settings": session.settings
    })

@router.get("/history")
async def get_call_history(limit: int = 10):
    """Get recent phone call history."""
    try:
        # Get conversations that start with "phone-" prefix
        conversations = await phone_manager.conversation_manager.list_conversations(limit=limit * 2)
        
        phone_calls = [
            conv for conv in conversations 
            if conv.conversation_id.startswith("phone-")
        ][:limit]
        
        return JSONResponse({
            "success": True,
            "calls": [
                {
                    "session_id": call.conversation_id.replace("phone-", ""),
                    "start_time": call.created_at.isoformat(),
                    "title": call.title,
                    "message_count": call.message_count,
                    "duration": f"{call.message_count // 2:02d}:00"  # Rough estimate
                }
                for call in phone_calls
            ]
        })
        
    except Exception as e:
        logger.error(f"Failed to get call history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call history: {str(e)}")

@router.get("/health")
async def phone_call_health():
    """Check phone call service health."""
    try:
        # Check dependencies
        stt_health = await stt_service.health_check()
        realtime_stt_health = await realtime_stt_service.health_check()
        tts_health = await tts_service.health_check()
        music_health = await background_music_service.health_check()
        
        # Check Ollama
        ollama_health = {"status": "unknown"}
        try:
            health_result = await ollama_client.health_check()
            ollama_health = {
                "status": health_result.get("status", "unknown"),
                "models_available": len(health_result.get("models", []))
            }
        except Exception as e:
            ollama_health = {"status": "error", "error": str(e)}
        
        overall_status = "healthy"
        if (stt_health["status"] != "healthy" or 
            realtime_stt_health["status"] != "healthy" or
            tts_health["status"] != "healthy" or 
            ollama_health["status"] != "healthy"):
            overall_status = "degraded"
        
        return JSONResponse({
            "status": overall_status,
            "active_sessions": len(phone_manager.active_sessions),
            "components": {
                "stt": stt_health,
                "realtime_stt": realtime_stt_health,
                "tts": tts_health,
                "background_music": music_health,
                "llm": ollama_health
            },
            "capabilities": {
                "real_time_calls": overall_status == "healthy",
                "websocket_support": True,
                "multi_user": True,
                "kid_friendly_mode": True,
                "background_music": music_health["status"] in ["healthy", "limited"],
                "voice_interruption": True,
                "audio_buffering": True
            }
        })
        
    except Exception as e:
        logger.error(f"Phone call health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Phase 3: New API endpoints for advanced features

@router.get("/history/{user_id}")
async def get_user_call_history(user_id: str, limit: int = 20, offset: int = 0):
    """Get call history for a specific user."""
    try:
        calls = call_history_service.get_call_history(user_id, limit, offset)
        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "calls": calls,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        logger.error(f"Failed to get call history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call history: {str(e)}")

@router.get("/call/{call_id}")
async def get_call_details(call_id: str):
    """Get detailed information about a specific call."""
    try:
        call_details = call_history_service.get_call_details(call_id)
        if not call_details:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return JSONResponse({
            "success": True,
            "call": call_details
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call details: {str(e)}")

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get statistics for a user's phone calls."""
    try:
        stats = call_history_service.get_user_stats(user_id)
        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")

@router.post("/search")
async def search_calls(user_id: str, search_term: str, limit: int = 10):
    """Search calls by message content."""
    try:
        calls = call_history_service.search_calls(user_id, search_term, limit)
        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "search_term": search_term,
            "calls": calls
        })
    except Exception as e:
        logger.error(f"Failed to search calls: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search calls: {str(e)}")

@router.get("/active-sessions")
async def get_active_sessions():
    """Get status of all active phone call sessions."""
    try:
        sessions_status = interrupt_service.get_all_sessions_status()
        active_sessions = []
        
        for session_id, status in sessions_status.items():
            session = phone_manager.get_session(session_id)
            if session:
                active_sessions.append({
                    "session_id": session_id,
                    "user_id": getattr(session, 'user_id', 'unknown'),
                    "status": session.status,
                    "start_time": session.start_time.isoformat() if session.start_time else None,
                    "kid_friendly_mode": session.settings.get("kid_friendly", False),
                    "ai_speaking": status.get("ai_speaking", False),
                    "interrupted": status.get("interrupted", False),
                    "conversation_length": len(session.conversation_history)
                })
        
        return JSONResponse({
            "success": True,
            "active_sessions": active_sessions,
            "total_active": len(active_sessions)
        })
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active sessions: {str(e)}")

# Phase 4: Optimized handler functions with performance monitoring

async def handle_optimized_session_start(websocket: WebSocket, message: Dict):
    """Enhanced session start with Phase 4 optimization features."""
    session_id = message["session_id"]
    settings_data = message.get("settings", {})
    user_id = message.get("user_id", "anonymous")
    
    try:
        settings = PhoneCallSettings.create_with_defaults(settings_data)
        session = phone_manager.create_session(session_id, settings)
        session.status = "connected"
        session.user_id = user_id
        
        # Phase 4: Validate and optimize settings
        optimization_level = settings_data.get("optimization_level", "balanced")
        connection_pooling = settings_data.get("connection_pooling", True)
        
        # Phase 3: Register with interrupt service
        interrupt_service.register_session(session_id, websocket)
        
        # Phase 3: Start call history tracking
        call_id = call_history_service.start_call(
            user_id=user_id,
            session_id=session_id,
            kid_friendly_mode=settings.kid_friendly,
            language=settings.language
        )
        session.call_id = call_id
        
        # Phase 4: Setup optimization services
        if connection_pooling:
            # Use the actual method that exists
            connection_pool_manager.optimize_for_phone_calls()
            logger.info("Connection pooling optimized for phone calls")
        
        # Phase 4: Pre-warm optimized LLM for faster first response
        model = settings_data.get("model", "gemma2:2b")
        await optimized_llm_service.warmup_models()
        
        # Phase 4: Get current service quality
        current_quality = get_overall_quality()
        
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Phone call connected successfully with optimization",
            "session_id": session_id,
            "call_id": call_id,
            "kid_friendly_mode": settings.kid_friendly,
            "optimization": {
                "level": optimization_level,
                "connection_pooling": connection_pooling,
                "quality": current_quality.value,
                "model_warmed": True
            }
        }))
        
        # Send initial greeting if kid-friendly mode
        if settings.kid_friendly:
            await websocket.send_text(json.dumps({
                "type": "ai_message",
                "message": "Hi there! I'm your friendly AI assistant. How can I help you today?"
            }))
        
        logger.info(f"Optimized session {session_id} started for user {user_id} with quality {current_quality.value}")
        
    except Exception as e:
        logger.error(f"Failed to start optimized session: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Failed to start session: {str(e)}"
        }))

async def handle_optimized_audio_data(websocket: WebSocket, message: Dict):
    """Enhanced audio processing with Phase 4 performance optimization."""
    session_id = message["session_id"]
    session = phone_manager.get_session(session_id)
    
    if not session:
        await websocket.send_text(json.dumps({
            "type": "error", 
            "message": "Session not found"
        }))
        return
    
    try:
        # Phase 4: Start comprehensive performance tracking
        interaction_start_time = time.time()
        
        # Send process status: Transfer completed, starting STT
        await send_stage_completed(websocket, "transfer", "Audio data received")
        await send_stage_active(websocket, "stt", "Converting speech to text...")
        
        # Decode audio data - handle missing audio_data gracefully and support both field names
        audio_data_field = message.get("audio_data") or message.get("audio")
        if not audio_data_field:
            logger.error("Missing audio_data or audio field in message")
            await send_stage_error(websocket, "transfer", "Missing audio data")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Missing audio data (expected 'audio_data' or 'audio' field)",
                "stage": "transfer"
            }))
            return
            
        audio_data = base64.b64decode(audio_data_field)
        
        # Store audio in conversation flow manager for intelligent processing
        conversation_flow_manager.process_audio_chunk(session_id, audio_data)
        
        # Phase 4: Record audio processing start (using existing method)
        logger.info(f"Processing audio data: {len(audio_data)} bytes")
        logger.debug(f"Session settings type: {type(session.settings)}")
        logger.debug(f"Session settings: {session.settings}")
        
        # Phase 2: Apply noise reduction if enabled
        if session.settings.get("noise_reduction", False):
            audio_data = await audio_processor.reduce_noise(audio_data)
        
        # Check if we should interrupt the user (but still process the audio)
        should_interrupt = conversation_flow_manager.should_interrupt_user(session_id)
        if should_interrupt:
            logger.info(f"Interrupting user for session {session_id}")
            await conversation_flow_manager.interrupt_user(session_id, websocket)
            # Continue processing this audio chunk even after interruption
        
        # Phase 2: Check for interrupts
        if session.settings.get("interrupt_detection", False) and interrupt_service.is_ai_thinking(session_id):
            interrupt_detected = await interrupt_service.detect_interrupt(session_id, audio_data)
            if interrupt_detected:
                logger.info(f"Interrupt detected for session {session_id}")
                await send_stage_error(websocket, "stt", "Interrupted by user")
                return
        
        # Phase 4: Optimized Speech-to-Text with performance tracking
        stt_start_time = time.time()
        
        stt_result = await stt_client.transcribe_audio_file(
            audio_data, 
            format="wav",  # Assuming WAV format from browser
            language=session.settings.get("language", "en")
        )
        
        stt_duration = time.time() - stt_start_time
        
        # DEBUG: Print entire STT result
        print(f"DEBUG: Full STT result: {stt_result}")
        
        # Extract text from STT result
        user_text = stt_result.get("text", "").strip() if stt_result.get("success") else ""
        print(f"DEBUG: Extracted user_text: '{user_text}'")
        
        # Handle STT errors
        if not stt_result.get("success", False):
            error_msg = stt_result.get("error", "STT processing failed")
            logger.error(f"STT failed for session {session_id}: {error_msg}")
            await send_stage_error(websocket, "stt", error_msg)
            return
        
        # Phase 4: Record STT performance
        performance_monitor.record_stt_performance(
            session_id=session_id,
            duration=stt_duration,
            audio_length=len(audio_data),
            success=bool(user_text and user_text.strip())
        )
        
        if not user_text or not user_text.strip():
            logger.info(f"No speech detected in session {session_id}")
            await send_stage_error(websocket, "stt", "No speech detected")
            # Mark user as stopped speaking when no text detected
            conversation_flow_manager.stop_user_speaking(session_id)
            return
        
        # Mark user as stopped speaking and add text to conversation
        conversation_flow_manager.stop_user_speaking(session_id)
        conversation_flow_manager.add_user_message(session_id, user_text)
        
        # Check if we should respond now or wait for more input
        should_respond = conversation_flow_manager.should_respond_now(session_id)
        if not should_respond:
            logger.info(f"Received user input, but waiting for pause before responding: {user_text[:30]}...")
            # Send acknowledgment but don't generate response yet
            await websocket.send_text(json.dumps({
                "type": "speech_received",
                "message": f"Received: {user_text[:50]}..."
            }))
            return
        
        # STT completed successfully
        await send_stage_completed(websocket, "stt", f"Recognized: {user_text[:50]}...")
        await send_stage_active(websocket, "llm", "AI is processing your message...")
        
        logger.info(f"User said ({stt_duration:.2f}s): {user_text}")
        print(f"DEBUG: User text received: '{user_text}'")  # Explicit debug print
        
        # Get conversation context from flow manager (with pruning if needed)
        conversation_context = conversation_flow_manager.get_conversation_context(session_id)
        print(f"DEBUG: Full conversation context: {conversation_context}")
        
        # Extract the complete user message from conversation context
        # Get all recent user messages that haven't been responded to yet
        complete_user_message = ""
        if conversation_context:
            # Find all consecutive user messages at the end
            user_messages = []
            for msg in reversed(conversation_context):
                if msg.get("role") == "user":
                    user_messages.append(msg.get("content", ""))
                else:
                    break
            
            # Combine user messages in correct order
            if user_messages:
                complete_user_message = " ".join(reversed(user_messages))
        
        # Use complete message or fallback to current chunk
        final_user_message = complete_user_message.strip() if complete_user_message.strip() else user_text
        print(f"DEBUG: Final combined user message: '{final_user_message}'")
        
        # Update session conversation history with managed context
        if conversation_context:
            session.conversation_history = conversation_context
        else:
            # Add to conversation history
            session.conversation_history.append({"role": "user", "content": user_text})
        
        # Update conversation flow with user input
        conversation_flow_manager.handle_user_input(session_id, final_user_message)
        
        # Phase 4: Get optimized LLM response with enhanced monitoring
        print(f"DEBUG: About to call LLM with final_user_message: '{final_user_message}'")  # Explicit debug print
        ai_text, llm_duration = await get_interruptible_llm_response(
            session, final_user_message, session.conversation_history
        )
        
        if ai_text is None:
            # Response was interrupted or failed
            await send_stage_error(websocket, "llm", "Response interrupted or failed")
            return
        
        # LLM completed successfully
        await send_stage_completed(websocket, "llm", f"Generated response: {ai_text[:50]}...")
        await send_stage_active(websocket, "tts", "Converting text to speech...")
        
        # Add AI response to conversation
        session.conversation_history.append({"role": "assistant", "content": ai_text})
        
        # Add AI response to conversation flow manager
        conversation_flow_manager.add_assistant_message(session_id, ai_text)
        
        # Update conversation flow with AI response completion
        conversation_flow_manager.handle_ai_response(session_id)
        
        # Phase 4: Optimized Text-to-Speech with performance tracking and fallback
        tts_start_time = time.time()
        
        # Clean text for TTS (remove emojis, formatting, etc.)
        clean_text = clean_text_for_tts(ai_text)
        print(f"DEBUG: Original AI text: '{ai_text}'")
        print(f"DEBUG: Cleaned text for TTS: '{clean_text}'")
        
        try:
            audio_response = await tts_client.synthesize_speech(
                clean_text,
                voice=session.settings.voice,
                language=session.settings.language,
                optimization_level=session.settings.get("optimization_level", "balanced")
            )
        except Exception as e:
            logger.warning(f"Primary TTS service failed: {e}. Using fallback TTS service.")
            # Use fallback TTS service
            try:
                audio_response = await simple_tts_fallback.synthesize_speech(
                    clean_text,
                    voice=session.settings.voice,
                    language=session.settings.language
                )
            except Exception as fallback_error:
                logger.error(f"Fallback TTS service also failed: {fallback_error}")
                audio_response = None
        
        tts_duration = time.time() - tts_start_time
        
        # Phase 4: Record TTS performance
        performance_monitor.record_tts_performance(
            session_id=session_id,
            duration=tts_duration,
            text_length=len(ai_text),
            audio_length=len(audio_response) if audio_response else 0,
            success=bool(audio_response),
            voice=session.settings.voice,
            language=session.settings.language
        )
        
        if not audio_response:
            await send_stage_error(websocket, "tts", "TTS processing failed")
            await safe_websocket_send(websocket, {
                "type": "error",
                "message": "TTS processing failed",
                "stage": "tts"
            })
            return
        
        # TTS completed successfully
        await send_stage_completed(websocket, "tts", "Audio ready for playback")
        
        # Phase 4: Calculate total interaction time and quality
        total_duration = time.time() - interaction_start_time
        current_quality = get_overall_quality()
        
        # Send optimized response
        audio_base64 = base64.b64encode(audio_response).decode()
        
        await safe_websocket_send(websocket, {
            "type": "ai_response",
            "audio": audio_base64,
            "text": ai_text,
            "timing": {
                "stt": stt_duration,
                "llm": llm_duration,
                "tts": tts_duration,
                "total": total_duration
            },
            "optimization": {
                "quality": current_quality.value,
                "model_used": session.settings.get("model", "gemma2:2b"),
                "performance_score": performance_monitor.get_session_score(session_id)
            }
        })
        
        # Phase 4: Record interaction success (using existing methods)
        # The individual component performance is already recorded above
        logger.info(f"Interaction completed: total={total_duration:.2f}s, stt={stt_duration:.2f}s, llm={llm_duration:.2f}s, tts={tts_duration:.2f}s")
        
        # Phase 3: Save to call history
        call_history_service.add_message(
            session.call_id, 
            user_text, 
            ai_text, 
            stt_duration, 
            llm_duration, 
            tts_duration
        )
        
        logger.info(f"Optimized interaction completed ({total_duration:.2f}s, quality: {current_quality.value})")
        
    except Exception as e:
        logger.error(f"Error in optimized audio processing: {e}")
        
        # Send process error status
        await send_stage_error(websocket, "llm", f"Processing failed: {str(e)}")
        
        # Phase 4: Record failed interaction
        total_duration = time.time() - interaction_start_time if 'interaction_start_time' in locals() else 0.0
        
        # Record audio processing error
        performance_monitor.record_audio_issue(session_id, "processing_error", str(e))
        logger.error(f"Audio processing failed: {e} (duration: {total_duration:.2f}s)")
        
        await safe_websocket_send(websocket, {
            "type": "error",
            "message": f"Audio processing error: {str(e)}",
            "stage": "processing"
        })

async def handle_optimized_ping(websocket: WebSocket, message: Dict):
    """Enhanced ping handler with performance statistics."""
    session_id = message.get("session_id")
    
    try:
        # Phase 4: Get comprehensive system status
        current_quality = get_overall_quality()
        session_stats = performance_monitor.get_session_summary(session_id) if session_id else None
        system_health = performance_monitor.get_system_health()
        
        response = {
            "type": "pong",
            "timestamp": time.time(),
            "quality": current_quality.value,
            "system_health": {
                "cpu_usage": system_health.get("cpu_percent", 0),
                "memory_usage": system_health.get("memory_percent", 0),
                "service_status": "healthy" if current_quality.value != "poor" else "degraded"
            }
        }
        
        if session_id:
            response["session_id"] = session_id
            if session_stats:
                response["session_performance"] = session_stats
        
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        logger.error(f"Error in optimized ping: {e}")
        await websocket.send_text(json.dumps({
            "type": "pong",
            "error": str(e)
        }))

async def handle_optimized_session_end(websocket: WebSocket, message: Dict, call_start_time: float):
    """Enhanced session end with performance summary."""
    session_id = message["session_id"]
    session = phone_manager.get_session(session_id)
    
    try:
        call_duration = time.time() - call_start_time
        
        # Phase 4: Generate comprehensive performance summary
        session_summary = performance_monitor.get_session_summary(session_id)
        
        # Phase 3: End call history tracking
        if session and hasattr(session, 'call_id'):
            call_history_service.end_call(session.call_id)
        
        # Phase 4: Record session end with metrics
        performance_monitor.record_call_end(
            session_id=session_id,
            success=True
        )
        
        # Phase 4: Cleanup optimization resources
        if session and session.settings.get("connection_pooling", True):
            # Cleanup is handled automatically by the connection pool manager
            logger.info("Connection pool cleanup completed")
        
        # Cleanup session
        phone_manager.remove_session(session_id)
        interrupt_service.unregister_session(session_id)
        
        # Clean up conversation flow manager
        conversation_flow_manager.end_conversation(session_id)
        
        # Send comprehensive session summary
        await websocket.send_text(json.dumps({
            "type": "session_ended",
            "session_id": session_id,
            "duration": call_duration,
            "performance_summary": session_summary,
            "message": "Phone call session ended successfully"
        }))
        
        logger.info(f"Optimized session {session_id} ended after {call_duration:.2f}s")
        
    except Exception as e:
        logger.error(f"Error ending optimized session: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error ending session: {str(e)}"
        }))

@router.post("/interrupt/{session_id}")
async def interrupt_session(session_id: str):
    """Interrupt an active phone call session."""
    try:
        success = interrupt_service.interrupt_session(session_id)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Session {session_id} interrupted successfully"
            })
        else:
            raise HTTPException(status_code=404, detail="Session not found or not interruptible")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to interrupt session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to interrupt session: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_data(days_to_keep: int = 90):
    """Clean up old call history and expired sessions."""
    try:
        # Clean up old calls
        calls_cleaned = call_history_service.cleanup_old_calls(days_to_keep)
        
        # Clean up expired sessions
        sessions_cleaned = interrupt_service.cleanup_expired_sessions(24)  # 24 hours
        
        return JSONResponse({
            "success": True,
            "calls_cleaned": calls_cleaned,
            "sessions_cleaned": sessions_cleaned,
            "message": f"Cleaned up {calls_cleaned} old calls and {sessions_cleaned} expired sessions"
        })
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")
