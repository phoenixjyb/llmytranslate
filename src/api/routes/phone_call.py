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
import random
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.websockets import WebSocketState
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
from ...services.smart_interrupt_manager import smart_interrupt_manager
from ...services.connection_pool_manager import connection_pool_manager
from ...services.conversation_flow_manager import conversation_flow_manager
from ...services.ollama_client import ollama_client

# Import WebSocket utilities
from ...utils.websocket_utils import safe_websocket_send

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
    
    # Remove emojis
    text = emoji_pattern.sub(r'', text)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    
    # Remove special characters that might cause TTS issues
    text = re.sub(r'[^\w\s\.,!?\'\"-:;()]', ' ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

async def enhance_audio_for_phone_call(audio_data: bytes) -> bytes:
    """
    Enhance audio quality specifically for phone call STT processing with noise reduction.
    
    Args:
        audio_data: Raw audio bytes
        
    Returns:
        Enhanced audio bytes with noise reduction and normalization
    """
    try:
        import numpy as np
        from scipy import signal
        
        # Convert bytes to numpy array for processing
        try:
            # More robust audio sample interpretation
            # First try 16-bit, then 8-bit if that fails
            audio_samples = None
            
            try:
                # Try 16-bit first (most common)
                if len(audio_data) % 2 == 0:  # Must be even number of bytes for 16-bit
                    audio_samples = np.frombuffer(audio_data, dtype=np.int16)
                    logger.info(f"Successfully interpreted as 16-bit audio: {len(audio_samples)} samples")
                else:
                    # Trim one byte to make it even
                    audio_data = audio_data[:-1]
                    audio_samples = np.frombuffer(audio_data, dtype=np.int16)
                    logger.info(f"Trimmed and interpreted as 16-bit audio: {len(audio_samples)} samples")
            except ValueError as e:
                logger.warning(f"16-bit interpretation failed: {e}, trying 8-bit")
                # Try 8-bit as fallback
                audio_samples = np.frombuffer(audio_data, dtype=np.uint8).astype(np.int16)
                # Convert 8-bit unsigned to 16-bit signed
                audio_samples = (audio_samples - 128) * 256
                logger.info(f"Interpreted as 8-bit audio: {len(audio_samples)} samples")
            
            if audio_samples is None or len(audio_samples) < 100:  # Too short to process
                logger.info("Audio too short for enhancement, returning original")
                return audio_data
            
            # Convert to float for processing
            audio_float = audio_samples.astype(np.float32) / 32768.0
            
            # Apply noise reduction techniques
            
            # 1. High-pass filter to remove low-frequency noise (below 100 Hz)
            try:
                # Estimate sample rate (common rates: 16kHz, 44.1kHz, 48kHz)
                # For phone calls, usually 16kHz or 8kHz
                estimated_sample_rate = min(16000, len(audio_samples) * 4)  # Conservative estimate
                nyquist = estimated_sample_rate / 2
                low_cutoff = min(100 / nyquist, 0.4)  # Ensure cutoff is valid
                
                if low_cutoff < 0.5:  # Only apply if cutoff frequency is reasonable
                    b, a = signal.butter(2, low_cutoff, btype='high')
                    audio_float = signal.filtfilt(b, a, audio_float)
                    logger.info("Applied high-pass filter for noise reduction")
            except Exception as filter_error:
                logger.warning(f"High-pass filter failed: {filter_error}")
            
            # 2. Simple noise gate (reduce very quiet sounds)
            noise_threshold = 0.01  # Adjust based on your needs
            audio_float = np.where(np.abs(audio_float) < noise_threshold, 
                                 audio_float * 0.1, audio_float)
            
            # 3. Volume normalization
            max_amplitude = np.max(np.abs(audio_float))
            if max_amplitude > 0:
                # Normalize to 70% of max to avoid clipping
                audio_float = audio_float * (0.7 / max_amplitude)
            
            # 4. Apply gentle compression to reduce dynamic range
            compressed_audio = np.sign(audio_float) * np.power(np.abs(audio_float), 0.7)
            
            # Convert back to int16
            enhanced_samples = np.clip(compressed_audio * 32767, -32768, 32767).astype(np.int16)
            enhanced_bytes = enhanced_samples.tobytes()
            
            logger.info(f"Audio enhancement completed: {len(audio_data)} -> {len(enhanced_bytes)} bytes")
            return enhanced_bytes
            
        except Exception as processing_error:
            logger.warning(f"Audio sample processing failed: {processing_error}")
            return audio_data
        
    except ImportError:
        logger.warning("NumPy/SciPy not available for advanced audio processing")
        # Basic fallback - just return original audio
        return audio_data
        
    except Exception as e:
        logger.warning(f"Audio enhancement failed: {e}")
        return audio_data

# Aggressive heartbeat function for long operations
async def maintain_aggressive_heartbeat(websocket: WebSocket, session_id: str):
    """Maintain aggressive heartbeat during long operations to prevent WebSocket timeout."""
    try:
        heartbeat_count = 0
        while heartbeat_count < 30:  # Max 30 heartbeats (60 seconds)
            # 🔧 CRITICAL FIX: Check connection BEFORE any operations
            if (not websocket or 
                not hasattr(websocket, 'client_state') or 
                websocket.client_state != WebSocketState.CONNECTED):
                print(f"💔 WebSocket disconnected before heartbeat {heartbeat_count + 1} for {session_id}")
                break
                
            await asyncio.sleep(2)  # Very aggressive 2-second heartbeat
            heartbeat_count += 1
            
            # Check if WebSocket is still connected
            try:
                # More robust connection check
                if (websocket and 
                    hasattr(websocket, 'client_state') and 
                    websocket.client_state == WebSocketState.CONNECTED):
                    
                    # Additional check: try a simple send operation
                    await safe_websocket_send(websocket, {
                        "type": "heartbeat",
                        "session_id": session_id,
                        "count": heartbeat_count,
                        "timestamp": time.time()
                    })
                    print(f"💓 Heartbeat {heartbeat_count} sent for session {session_id}")
                else:
                    print(f"💔 WebSocket disconnected, stopping heartbeat for {session_id}")
                    break
                    
            except Exception as check_error:
                print(f"💔 Heartbeat check failed: {check_error}")
                # If we can't send heartbeat, connection is likely dead
                break
                
    except asyncio.CancelledError:
        print(f"💓 Heartbeat cancelled for session {session_id}")
        raise  # Re-raise to properly handle cancellation
    except Exception as e:
        print(f"💔 Heartbeat task ended: {e}")
        logger.warning(f"Heartbeat task ended: {e}")

# Global heartbeat task tracking
heartbeat_tasks = {}

async def start_heartbeat_task(websocket: WebSocket, session_id: str):
    """Start heartbeat task and track it for proper cleanup."""
    # Cancel any existing heartbeat task for this session
    if session_id in heartbeat_tasks:
        heartbeat_tasks[session_id].cancel()
    
    # Start new heartbeat task
    task = asyncio.create_task(maintain_aggressive_heartbeat(websocket, session_id))
    heartbeat_tasks[session_id] = task
    return task

async def stop_heartbeat_task(session_id: str):
    """Stop and clean up heartbeat task for a session."""
    if session_id in heartbeat_tasks:
        task = heartbeat_tasks[session_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected when cancelling
        del heartbeat_tasks[session_id]
        print(f"🛑 Heartbeat task stopped for session {session_id}")

# Process Status Helper Functions
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

async def _process_queued_audio(websocket: WebSocket, session_id: str, combined_audio: bytes):
    """Process queued audio chunks in the background."""
    try:
        logger.info(f"Processing queued audio for session {session_id}: {len(combined_audio)} bytes")
        
        # Create a simplified message for processing
        queue_message = {
            "type": "audio_data",
            "session_id": session_id,
            "audio_data": base64.b64encode(combined_audio).decode()
        }
        
        # Process this audio with a lower priority (don't wait for completion)
        await handle_optimized_audio_data(websocket, queue_message)
        
    except Exception as e:
        logger.warning(f"Failed to process queued audio for session {session_id}: {e}")

from ...storage.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/phone", tags=["phone-call"])

# CRITICAL DEBUG: This should appear during module import/startup
logger.info("🚨🚨🚨 PHONE_CALL.PY MODULE LOADED - NEW CODE VERSION! 🚨🚨🚨")
logger.info("🔥 If you see this message, the updated code is being imported correctly!")

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
    
    # Add fields for conversation flow management
    silence_count: int = 0
    accumulated_text: str = ""
    
    class Config:
        # Allow extra fields for dynamic attributes
        extra = "allow"

class PhoneCallSettings(BaseModel):
    language: str = "en"
    model: str = "gemma2:2b"
    speed: float = 1.0
    kid_friendly: bool = False
    background_music: bool = True
    voice: str = "default"
    noise_reduction: bool = True  # Enable noise reduction by default
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
            "noise_reduction": True,  # Enable by default
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
        
        # Conversation flow tracking
        self.silence_counts: Dict[str, int] = {}  # Track silence per session
        self.accumulated_texts: Dict[str, str] = {}  # Track accumulated text per session
        self.accumulated_audio: Dict[str, List[bytes]] = {}  # Queue audio chunks for processing
        
        # Processing locks to prevent overlapping responses
        self.processing_locks: Dict[str, asyncio.Lock] = {}  # Processing locks per session
        self.last_response_times: Dict[str, float] = {}  # Track last response time per session
        
        # CRITICAL: Track active AI responses to prevent overlap
        self.active_ai_responses: set[str] = set()  # Sessions currently generating AI responses
    
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
        self.silence_counts[session_id] = 0  # Initialize silence counter
        self.accumulated_texts[session_id] = ""  # Initialize accumulated text
        self.accumulated_audio[session_id] = []  # Initialize audio queue
        self.processing_locks[session_id] = asyncio.Lock()  # Initialize processing lock
        self.last_response_times[session_id] = 0.0  # Initialize last response time
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
            if session_id in self.silence_counts:
                del self.silence_counts[session_id]
            if session_id in self.accumulated_texts:
                del self.accumulated_texts[session_id]
            if session_id in self.accumulated_audio:
                del self.accumulated_audio[session_id]
            if session_id in self.processing_locks:
                del self.processing_locks[session_id]
            if session_id in self.last_response_times:
                del self.last_response_times[session_id]
            
            # CRITICAL: Clean up active AI response tracking
            self.active_ai_responses.discard(session_id)
            logger.info(f"🧹 Cleaned up ACTIVE AI response tracking for session {session_id}")
    
    async def _save_conversation(self, session: PhoneCallSession):
        """Save phone call conversation to storage."""
        try:
            conversation_id = f"phone-{session.session_id}"
            
            # Create conversation with the model used
            model_used = session.settings.get("model", "gemma2:2b")
            self.conversation_manager.create_conversation(model=model_used)
            
            # Add all messages to the conversation
            for interaction in session.conversation_history:
                if interaction.get("type") == "user_speech":
                    message = {
                        "role": "user",
                        "content": interaction["content"],
                        "timestamp": interaction["timestamp"],
                        "metadata": {"type": "phone_call", "audio_duration": interaction.get("audio_duration")}
                    }
                    self.conversation_manager.add_message(conversation_id, message)
                elif interaction.get("type") == "ai_response":
                    message = {
                        "role": "assistant", 
                        "content": interaction["content"],
                        "timestamp": interaction["timestamp"],
                        "metadata": {"type": "phone_call", "processing_time": interaction.get("processing_time")}
                    }
                    self.conversation_manager.add_message(conversation_id, message)
            
            # Save the conversation
            self.conversation_manager.save_conversation(conversation_id)
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
    logger.info("🚨🚨🚨 WEBSOCKET CONNECTION: NEW HEARTBEAT CODE VERSION LOADED! 🚨🚨🚨")
    logger.info("💓 HEARTBEAT SYSTEM: Active with 3-second intervals during processing")
    await websocket.accept()
    session_id = None
    call_start_time = time.time()
    last_ping_time = time.time()
    
    async def send_heartbeat():
        """Send periodic ping to keep connection alive during long operations."""
        nonlocal last_ping_time
        current_time = time.time()
        if current_time - last_ping_time > 10:  # Send ping every 10 seconds
            try:
                # FastAPI WebSocket doesn't have ping(), use send_text with ping message instead
                await safe_websocket_send(websocket, {
                    "type": "ping",
                    "timestamp": current_time
                })
                last_ping_time = current_time
                logger.debug(f"💓 Sent WebSocket ping for session {session_id}")
            except Exception as e:
                logger.warning(f"Failed to send WebSocket ping: {e}")
    
    try:
        # Phase 4: Check initial service quality
        initial_quality = get_overall_quality()
        if initial_quality.value == "poor":
            # await quality_monitor.attempt_service_recovery()  # TODO: Implement
            logger.warning("Service quality is poor")
            
        logger.info(f"Starting phone call WebSocket with quality: {initial_quality.value}")
        
        while True:
            # Send heartbeat if needed
            await send_heartbeat()
            
            # Receive message from client with timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                message = json.loads(data)
            except asyncio.TimeoutError:
                # Continue the loop to send heartbeat if needed
                continue
            except Exception as e:
                logger.error(f"Error receiving WebSocket data: {e}")
                break
            
            message_type = message.get("type")
            session_id = message.get("session_id")
            
            # CRITICAL DEBUG: Log every message received
            logger.info(f"🔥 WEBSOCKET ROUTER: Received type='{message_type}', session='{session_id}', keys={list(message.keys())}")
            
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
                
                # Phase 4: Just get the optimal model (no warmup)
                model = settings.get("model", "gemma2:2b")
                logger.info(f"Using optimal model: {model} for session {session_id}")
                
                # Start proactive conversation management
                conversation_flow_manager.start_conversation(session_id, websocket)
                logger.info(f"Started intelligent conversation flow management for session {session_id}")
                
            elif message_type == "audio_data":
                # Smart interruption: Mark user as speaking when audio data arrives
                await smart_interrupt_manager.start_user_speaking(session_id, websocket)
                conversation_flow_manager.start_user_speaking(session_id)
                logger.info(f"Received audio_data message for session {session_id}")
                
                # CRITICAL DEBUG: About to call handle_optimized_audio_data
                logger.info("🔥 ROUTER: About to call handle_optimized_audio_data with overlap prevention!")
                
                # Phase 4: Enhanced audio processing with performance tracking
                await handle_optimized_audio_data(websocket, message)
                
            elif message_type == "interrupt":
                # Handle both manual and smart interruptions
                await smart_interrupt_manager.manual_interrupt(session_id, websocket)
                await handle_interrupt(websocket, message)
                
            elif message_type == "settings_update":
                await handle_settings_update(websocket, message)
                
            elif message_type == "user_stop_speaking":
                # NEW: Handle user stop speaking signal for smart interruption
                await smart_interrupt_manager.stop_user_speaking(session_id)
                conversation_flow_manager.stop_user_speaking(session_id)
                logger.info(f"User stopped speaking in session {session_id}")
                
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
                    await smart_interrupt_manager.start_user_speaking(session_id, websocket)
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
            
            # 🔧 CRITICAL FIX: Stop heartbeat task to prevent continued sending
            await stop_heartbeat_task(session_id)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        
        # Phase 4: Record error
        if session_id:
            call_duration = time.time() - call_start_time
            performance_monitor.record_call_end(session_id, success=False)
            
            # 🔧 CRITICAL FIX: Stop heartbeat task on any error
            await stop_heartbeat_task(session_id)
            
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
        # 🔧 CRITICAL FIX: Ensure cleanup always happens, including heartbeat task
        if session_id:
            # Stop heartbeat task to prevent any orphaned tasks
            await stop_heartbeat_task(session_id)
            
            phone_manager.end_session(session_id)
            # Clean up conversation flow management
            conversation_flow_manager.end_conversation(session_id)
            logger.info(f"🧹 Finally block: Cleaned up session {session_id} and stopped heartbeat tasks")

# Phase 3 & 4: Helper function for interruptible LLM responses with optimization
async def get_interruptible_llm_response(session: PhoneCallSession, user_text: str, 
                                        conversation_context: list, background_music_task=None, websocket=None):
    """Get optimized LLM response with smart interrupt support and performance monitoring."""
    session_id = session.session_id
    
    async def maintain_websocket_heartbeat(task, websocket, interval=10):
        """Maintain WebSocket connection during long operations by sending periodic pings."""
        if not websocket:
            return await task
            
        try:
            while not task.done():
                await asyncio.sleep(interval)
                if not task.done():
                    try:
                        # FastAPI WebSocket doesn't have ping(), use send_text with ping message instead
                        await safe_websocket_send(websocket, {
                            "type": "heartbeat",
                            "timestamp": time.time()
                        })
                        logger.debug(f"💓 Sent heartbeat ping during LLM processing for session {session_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send heartbeat ping: {e}")
                        break
            return await task
        except Exception as e:
            logger.error(f"Error in heartbeat maintenance: {e}")
            return await task
    
    try:
        # Phase 4: Start performance monitoring
        performance_monitor.record_call_start(session_id, getattr(session, 'user_id', None), 
                                            session.settings.get('kid_friendly', False))
        
        # Phase 4: Select optimal model for phone call
        kid_friendly_mode = session.settings.get('kid_friendly', False) if isinstance(session.settings, dict) else False
        language = session.settings.get('language', 'en') if isinstance(session.settings, dict) else 'en'
        
        optimal_model = optimized_llm_service.get_optimal_model_for_phone_call(
            kid_friendly=kid_friendly_mode,
            language=language
        )
        
        logger.info(f"Using optimized model: {optimal_model} for session {session_id}")
        
        # Create interruptible LLM task
        llm_start_time = time.time()
        
        # Phase 4: Use optimized LLM service with timeout and performance tracking
        try:
            llm_task = asyncio.create_task(optimized_llm_service.fast_completion(
                message=user_text,
                model=optimal_model,
                conversation_context=conversation_context,
                timeout=30.0  # Extended timeout for more reliable phone calls
            ))
        except AttributeError:
            # Fallback if fast_completion doesn't exist
            logger.warning("fast_completion method not available, using basic completion")
            llm_task = asyncio.create_task(optimized_llm_service.get_completion(
                prompt=user_text,
                model=optimal_model,
                temperature=0.7,
                max_tokens=150
            ))
        
        # Register LLM task for both interrupt services
        interrupt_service.set_ai_thinking(session.session_id, True, llm_task)
        
        # NEW: Register with smart interrupt manager
        await smart_interrupt_manager.start_ai_response(session_id, llm_task)
        
        try:
            # Enhanced: Maintain WebSocket heartbeat during LLM processing
            if websocket:
                logger.info(f"🔄 Starting LLM processing with WebSocket heartbeat for session {session_id}")
                llm_response = await maintain_websocket_heartbeat(llm_task, websocket, interval=3)
            else:
                llm_response = await llm_task
            
            # Clear AI response tracking on successful completion
            await smart_interrupt_manager.stop_ai_response(session_id)
            
        except asyncio.CancelledError:
            # Handle smart interruption gracefully
            logger.info(f"LLM task cancelled due to user interruption for session {session_id}")
            await smart_interrupt_manager.stop_ai_response(session_id)
            return None, 0.0  # Return None to indicate interruption
            
        except asyncio.TimeoutError:
            # Phase 4: Handle timeout with fallback
            logger.warning(f"LLM timeout for session {session_id}, attempting fallback")
            quality_monitor.record_service_performance("llm", 8.0, False, "timeout")
            await smart_interrupt_manager.stop_ai_response(session_id)
            
            # Try emergency fallback
            fallback_model = "gemma2:2b"  # Consistent model for better performance
            try:
                llm_task = asyncio.create_task(optimized_llm_service.fast_completion(
                    message=user_text,
                    model=fallback_model,
                    conversation_context=conversation_context[-3:],  # Shorter context
                    timeout=15.0  # Extended fallback timeout
                ))
            except AttributeError:
                # Use basic completion if fast_completion doesn't exist
                logger.warning("Using basic completion for fallback")
                llm_task = asyncio.create_task(optimized_llm_service.get_completion(
                    prompt=user_text,
                    model=fallback_model,
                    temperature=0.7,
                    max_tokens=100
                ))
            
            # Register fallback task with smart interrupt manager
            await smart_interrupt_manager.start_ai_response(session_id, llm_task)
            
            try:
                llm_response = await llm_task
                await smart_interrupt_manager.stop_ai_response(session_id)
                logger.info(f"Fallback successful with {fallback_model}")
            except asyncio.TimeoutError:
                # Ultimate fallback - simple response
                logger.error(f"All LLM attempts failed for session {session_id}")
                # Generate a simple fallback response
                fallback_responses = [
                    "I hear you. Could you tell me more about that?",
                    "That's interesting. What else would you like to discuss?",
                    "I understand. How can I help you with that?",
                    "Thanks for sharing. What's on your mind?",
                    "I see. Could you elaborate on that?"
                ]
                import random
                fallback_text = random.choice(fallback_responses)
                logger.info(f"Using fallback response: {fallback_text}")
                return fallback_text, 0.5
                
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
        llm_success = llm_response.get("success", False) if isinstance(llm_response, dict) else bool(llm_response)
        
        # Handle different response formats
        if isinstance(llm_response, dict):
            if llm_success:
                ai_text = llm_response.get("response", llm_response.get("text", str(llm_response)))
            else:
                error_msg = llm_response.get("error", "Unknown LLM error")
                logger.error(f"LLM error: {error_msg}")
                raise Exception(f"LLM processing failed: {error_msg}")
        elif isinstance(llm_response, str):
            ai_text = llm_response
            llm_success = True
        else:
            logger.error(f"Unexpected LLM response format: {type(llm_response)}")
            raise Exception(f"Unexpected LLM response format: {type(llm_response)}")
        
        if not ai_text or not ai_text.strip():
            raise Exception("LLM returned empty response")
        
        performance_monitor.record_llm_performance(
            session_id=session_id,
            duration=llm_duration,
            model=optimal_model,
            input_length=len(user_text),
            output_length=len(ai_text),
            success=llm_success,
            error=None
        )
        
        # Phase 4: Record quality metrics
        quality_level = quality_monitor.record_service_performance(
            "llm", llm_duration, llm_success, None
        )
        
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
        
        # Return a graceful fallback response instead of None
        fallback_responses = [
            "I'm having trouble understanding right now. Could you repeat that?",
            "Sorry, I didn't catch that. What did you say?",
            "Let me try again. What would you like to talk about?",
            "I apologize for the confusion. How can I help you?"
        ]
        import random
        fallback_text = random.choice(fallback_responses)
        logger.info(f"Using error fallback response: {fallback_text}")
        return fallback_text, 1.0

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
        
        await safe_websocket_send(websocket, {
            "type": "status",
            "message": "Phone call connected successfully",
            "session_id": session_id,
            "call_id": call_id,
            "kid_friendly_mode": settings.kid_friendly
        })
        
        # Send initial greeting if kid-friendly mode
        if settings.kid_friendly:
            greeting = kid_friendly_service.kid_friendly_prompts[
                'chinese' if settings.language in ['zh', 'chinese'] else 'english'
            ]['greeting']
            
            await safe_websocket_send(websocket, {
                "type": "ai_message",
                "message": greeting,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"Phone call session started: {session_id} (kid-friendly: {settings.kid_friendly})")
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Failed to start call: {str(e)}"
        }))

async def handle_audio_data(websocket: WebSocket, message: Dict):
    """Handle incoming audio data for transcription and processing."""
    logger.info("🚨 OLD FUNCTION: handle_audio_data called - THIS SHOULD NOT BE HAPPENING!")
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
        
        # Apply our WebM format detection fix here too
        webm_detected = buffered_audio.startswith(b'\x1A\x45\xDF\xA3')
        audio_format = "webm" if webm_detected else "raw"
        
        stt_result = await realtime_stt_service.transcribe_streaming_audio(
            audio_data=buffered_audio,
            format=audio_format,  # Use detected format instead of hardcoded "webm"
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
                    session, user_text, conversation_context, background_music_task, websocket
                )
                if ai_text is None:  # Interrupted
                    return
        else:
            # Normal mode with interrupt support
            ai_text, llm_processing_time = await get_interruptible_llm_response(
                session, user_text, conversation_context, background_music_task, websocket
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
        
        # Enhanced: Send TTS start notification to keep WebSocket alive
        print("🔄 DEBUG: Sending tts_started notification")
        await safe_websocket_send(websocket, {
            "type": "tts_started",
            "message": "Converting text to speech...",
            "session_id": session_id,
            "text_length": len(ai_text),
            "timestamp": time.time()
        })
        
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
            
            # Enhanced: Send TTS completion notification
            print("🔄 DEBUG: Sending tts_completed notification")
            await safe_websocket_send(websocket, {
                "type": "tts_completed",
                "message": "Audio ready, sending...",
                "session_id": session_id,
                "audio_size": len(tts_result.get("audio_data", "")) if tts_result else 0,
                "timestamp": time.time()
            })
            
            # Enhanced: Stop aggressive heartbeat
            print("💓 Stopping aggressive heartbeat task...")
            if 'heartbeat_task' in locals():
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                
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
        
        # Phase 4: Select optimal model for faster first response
        model = settings_data.get("model", "gemma2:2b")
        logger.info(f"Selected optimal model: {model} for phone call session {session_id}")
        
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
    logger.info("🚨 FUNCTION START: handle_optimized_audio_data called")
    logger.info("🚨🚨🚨 NEW CODE VERSION - RESTART SUCCESSFUL! 🚨🚨🚨")
    session_id = message["session_id"]
    
    # CRITICAL EARLY CHECK: Prevent overlapping responses IMMEDIATELY
    if session_id in phone_manager.active_ai_responses:
        logger.warning(f"🚫 EARLY BLOCK: Session {session_id} already has active AI response - DROPPING audio immediately")
        await safe_websocket_send(websocket, {
            "type": "status",
            "message": "AI is still responding, please wait...",
            "session_id": session_id
        })
        return
    
    session = phone_manager.get_session(session_id)
    
    if not session:
        await safe_websocket_send(websocket, {
            "type": "error", 
            "message": "Session not found"
        })
        return
    
    # CRITICAL FIX: Check if AI is already responding for this session
    if session_id in phone_manager.active_ai_responses:
        logger.warning(f"🚫 Session {session_id} already has active AI response - DROPPING audio to prevent overlap")
        await safe_websocket_send(websocket, {
            "type": "status",
            "message": "AI is still responding, please wait...",
            "session_id": session_id
        })
        return
    
    # Prevent overlapping responses using processing lock
    processing_lock = phone_manager.processing_locks.get(session_id)
    if not processing_lock:
        logger.warning(f"No processing lock found for session {session_id}")
        return
    
    # Check if we're already processing a request
    if processing_lock.locked():
        logger.info(f"Session {session_id} already processing - DROPPING this audio chunk to prevent overlap")
        
        # Send immediate acknowledgment to user
        await safe_websocket_send(websocket, {
            "type": "status",
            "message": "Still processing previous request...",
            "session_id": session_id
        })
        
        # CRITICAL FIX: Return early to prevent multiple concurrent AI responses
        logger.warning(f"Dropping audio chunk for session {session_id} - AI already responding")
        return
    
    try:
        # Acquire lock to prevent multiple simultaneous processing
        async with processing_lock:
            # Check minimum time between responses (prevent rapid-fire responses)
            current_time = time.time()
            last_response_time = phone_manager.last_response_times.get(session_id, 0)
            min_response_interval = 0.5  # Reduced to 0.5 seconds for faster response
            
            if current_time - last_response_time < min_response_interval:
                logger.info(f"Response too soon for session {session_id} - sending quick acknowledgment")
                # Send immediate acknowledgment instead of blocking
                await safe_websocket_send(websocket, {
                    "type": "status", 
                    "message": "Processing...",
                    "session_id": session_id
                })
                return
            
            # Update last response time
            phone_manager.last_response_times[session_id] = current_time
            
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
                await safe_websocket_send(websocket, {
                    "type": "error",
                    "message": "Missing audio data (expected 'audio_data' or 'audio' field)",
                    "stage": "transfer"
                })
                return
                
            audio_data = base64.b64decode(audio_data_field)
            
            # Store audio in conversation flow manager for intelligent processing
            conversation_flow_manager.process_audio_chunk(session_id, audio_data)
            
            # Phase 4: Record audio processing start (using existing method)
            logger.info(f"Processing audio data: {len(audio_data)} bytes")
            logger.debug(f"Session settings type: {type(session.settings)}")
            logger.debug(f"Session settings: {session.settings}")
            
            # Phase 2: Apply noise reduction if enabled (enhanced) - SIMPLIFIED for speed
            # Apply noise reduction only if enabled and not WebM format
            # WebM containers should not be processed as raw audio
            if session.settings.get("noise_reduction", True) and not audio_data.startswith(b'\x1A\x45\xDF\xA3'):
                try:
                    logger.info("Applying fast noise reduction (non-WebM audio)")
                    # Use only the fast enhance_audio_for_phone_call function
                    audio_data = await enhance_audio_for_phone_call(audio_data)
                    logger.info(f"Fast noise reduction applied, audio size: {len(audio_data)} bytes")
                except Exception as noise_error:
                    logger.warning(f"Fast noise reduction failed: {noise_error}, using original audio")
            elif audio_data.startswith(b'\x1A\x45\xDF\xA3'):
                logger.info("🎯 Skipping noise reduction for WebM container data")
            
            # REMOVED: Additional audio_processor.reduce_noise() to speed up processing            # Check if we should interrupt the user (but still process the audio)
            should_interrupt = conversation_flow_manager.should_interrupt_user(session_id)
            if should_interrupt:
                logger.info(f"Interrupting user for session {session_id}")
                await conversation_flow_manager.interrupt_user(session_id, websocket)
                # Continue processing this audio chunk even after interruption
            
            # Phase 2: Check for interrupts - TEMPORARILY DISABLED FOR WEBM TESTING
            # if session.settings.get("interrupt_detection", False) and interrupt_service.is_ai_thinking(session_id):
            #     interrupt_detected = await interrupt_service.detect_interrupt(session_id, audio_data)
            #     if interrupt_detected:
            #         logger.info(f"Interrupt detected for session {session_id}")
            #         await send_stage_error(websocket, "stt", "Interrupted by user")
            #         return
            
            # Continue with rest of processing...
            # (The rest of the function continues normally)
            logger.info(f"Interrupting user for session {session_id}")
            await conversation_flow_manager.interrupt_user(session_id, websocket)
            # Continue processing this audio chunk even after interruption
        
        # Phase 2: Check for interrupts - TEMPORARILY DISABLED FOR WEBM TESTING  
        # if session.settings.get("interrupt_detection", False) and interrupt_service.is_ai_thinking(session_id):
        #     interrupt_detected = await interrupt_service.detect_interrupt(session_id, audio_data)
        #     if interrupt_detected:
        #         logger.info(f"Interrupt detected for session {session_id}")
        #         await send_stage_error(websocket, "stt", "Interrupted by user")
        #         return
        
        # Phase 4: Optimized Speech-to-Text with performance tracking
        stt_start_time = time.time()
        
        # First, detect the audio format from the current chunk
        audio_format = "webm"  # Default assumption from phone call WebSocket
        
        # Check format of current chunk BEFORE any accumulation
        current_chunk_webm = audio_data.startswith(b'\x1A\x45\xDF\xA3')  # Use same magic bytes as debugging section
        logger.info(f"🔍 Current chunk WebM check: {current_chunk_webm}")
        
        # Check if we have accumulated audio from queued chunks
        if session_id in phone_manager.accumulated_audio and phone_manager.accumulated_audio[session_id]:
            logger.info(f"Processing accumulated audio chunks for session {session_id}")
            
            # If current chunk is WebM container format, handle intelligently
            if current_chunk_webm:
                logger.info("🎯 Current chunk is WebM container - using intelligent WebM handling")
                
                # Check if accumulated chunks are also WebM containers
                accumulated_chunks = phone_manager.accumulated_audio[session_id]
                accumulated_webm_count = sum(1 for chunk in accumulated_chunks if chunk.startswith(b'\x1A\x45\xDF\xA3'))
                
                logger.info(f"📊 Accumulated: {len(accumulated_chunks)} chunks, {accumulated_webm_count} WebM containers")
                
                # If we have multiple WebM containers, use the latest complete one
                if accumulated_webm_count > 0:
                    logger.info("🔄 Multiple WebM containers detected - using latest complete container")
                    # Use current chunk as it's the most recent complete WebM container
                    audio_data = audio_data
                    audio_format = "webm"
                else:
                    logger.info("🔧 Accumulated raw chunks + WebM container - using WebM container only")
                    # Previous chunks were raw/incomplete, current is complete WebM
                    audio_data = audio_data
                    audio_format = "webm"
                
                # Clear accumulated audio
                phone_manager.accumulated_audio[session_id] = []
                
            else:
                # Current chunk is not WebM - check if accumulated chunks contain WebM
                accumulated_chunks = phone_manager.accumulated_audio[session_id]
                webm_chunks = [chunk for chunk in accumulated_chunks if chunk.startswith(b'\x1A\x45\xDF\xA3')]
                
                if webm_chunks:
                    logger.info(f"🎯 Found {len(webm_chunks)} WebM containers in accumulated audio")
                    # Use the last WebM container found
                    audio_data = webm_chunks[-1]
                    audio_format = "webm"
                    logger.info("✅ Using latest WebM container from accumulated audio")
                else:
                    logger.info("📦 No WebM containers found - proceeding with raw accumulation")
                    # Normal raw audio accumulation
                    all_audio_chunks = accumulated_chunks + [audio_data]
                    combined_audio = b''.join(all_audio_chunks)
                    audio_data = combined_audio
                    audio_format = "raw"
                    logger.info(f"Combined raw audio size: {len(audio_data)} bytes")
                
                # Clear accumulated audio
                phone_manager.accumulated_audio[session_id] = []
        else:
            # No accumulated audio - determine format from current chunk
            if current_chunk_webm:
                audio_format = "webm"
                logger.info("✅ Single WebM container detected")
            else:
                # Check for other formats
                if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:20]:
                    audio_format = "wav"
                    logger.info("✅ WAV format detected")
                elif audio_data.startswith(b'ID3') or audio_data.startswith(b'\xFF\xFB'):
                    audio_format = "mp3"
                    logger.info("✅ MP3 format detected")
                else:
                    audio_format = "raw"
                    logger.info("📦 No container format detected - treating as raw PCM")
        
        logger.info(f"🎯 Final audio format for STT: {audio_format}, data size: {len(audio_data)} bytes")
        
        # At this point, audio_format is determined by our intelligent WebM handling above
        # and audio_data contains the properly selected audio data
        
        stt_result = await stt_client.transcribe_audio_file(
            audio_data, 
            format=audio_format,  # Use format determined by intelligent WebM handling
            language=session.settings.get("language", "en")
        )
        
        stt_duration = time.time() - stt_start_time
        
        # Extract text from STT result
        user_text = stt_result.get("text", "").strip() if stt_result.get("success") else ""
        
        # Handle STT errors
        if not stt_result.get("success", False):
            error_msg = stt_result.get("error", "STT processing failed")
            logger.error(f"STT failed for session {session_id}: {error_msg}")
            await send_stage_error(websocket, "stt", error_msg)
            return
        
        # Phase 4: Record STT performance with correct audio duration
        # Get actual audio duration from STT analysis, fallback to byte-based estimation
        audio_analysis = stt_result.get("audio_analysis", {})
        actual_audio_duration = audio_analysis.get("duration_sec")
        
        if actual_audio_duration is None:
            # Fallback: Estimate duration from bytes (assuming 16kHz 16-bit mono)
            # WebM audio is typically 48kHz, but we'll use a conservative estimate
            estimated_duration = len(audio_data) / (16000 * 2)  # 16kHz * 2 bytes per sample
            logger.warning(f"🔧 No duration_sec in STT result, estimating: {estimated_duration:.2f}s from {len(audio_data)} bytes")
            actual_audio_duration = estimated_duration
            
        performance_monitor.record_stt_performance(
            session_id=session_id,
            duration=stt_duration,
            audio_length=actual_audio_duration,  # Use actual duration in seconds, not bytes!
            success=bool(user_text and user_text.strip())
        )
        
        if not user_text or not user_text.strip():
            logger.info(f"No speech detected in session {session_id}")
            await send_stage_error(websocket, "stt", "No speech detected")
            # Mark user as stopped speaking when no text detected
            conversation_flow_manager.stop_user_speaking(session_id)
            
            # Don't return immediately - instead use silence detection to check if user is done
            # Add silence tracking to session using manager
            phone_manager.silence_counts[session_id] = phone_manager.silence_counts.get(session_id, 0) + 1
            
            # If we have accumulated user text and enough silence, process it
            accumulated_text = phone_manager.accumulated_texts.get(session_id, "")
            silence_count = phone_manager.silence_counts.get(session_id, 0)
            
            if (accumulated_text.strip() and silence_count >= 2):  # 2 consecutive silences
                
                logger.info(f"Processing accumulated text after silence: '{accumulated_text}'")
                user_text = accumulated_text.strip()
                phone_manager.accumulated_texts[session_id] = ""
                phone_manager.silence_counts[session_id] = 0
                
                # Continue with processing the accumulated text
            else:
                return
        else:
            # Reset silence count when we get text
            phone_manager.silence_counts[session_id] = 0
            
            # Enhanced sentence accumulation logic with EMERGENCY INTERRUPT
            accumulated_text = phone_manager.accumulated_texts.get(session_id, "")
            
            # EMERGENCY INTERRUPT: Check for "okaydokay" repeated twice
            emergency_keywords = ["okaydokay okaydokay", "okayokday okayokday", "okay dokay okay dokay"]
            user_text_lower = user_text.lower().strip()
            
            is_emergency_interrupt = any(keyword in user_text_lower for keyword in emergency_keywords)
            
            if is_emergency_interrupt:
                logger.info(f"🚨 EMERGENCY INTERRUPT DETECTED: '{user_text}' - Forcing immediate response")
                
                # EMERGENCY ACTIONS:
                # 1. Clear accumulated text
                phone_manager.accumulated_texts[session_id] = ""
                
                # 2. Mark any active AI response as completed (force clear)
                if session_id in phone_manager.active_ai_responses:
                    phone_manager.active_ai_responses.discard(session_id)
                    logger.info(f"🚫 EMERGENCY: Cleared active AI response for session {session_id}")
                
                # 3. Send immediate stop signal to client
                await safe_websocket_send(websocket, {
                    "type": "emergency_interrupt",
                    "message": "Emergency interrupt activated - stopping current audio",
                    "session_id": session_id
                })
                
                # 4. Set interrupt text for processing
                user_text = "Please stop and listen to me now."
                # Skip accumulation and process immediately
            else:
                # Add new text to accumulated text
                if accumulated_text:
                    phone_manager.accumulated_texts[session_id] = accumulated_text + " " + user_text
                else:
                    phone_manager.accumulated_texts[session_id] = user_text
                
                accumulated_text = phone_manager.accumulated_texts[session_id]
                logger.info(f"Accumulated text: '{accumulated_text}'")
                
                # IMPROVED: Smart sentence completion detection
                complete_sentence_indicators = ['.', '!', '?']
                has_sentence_ending = any(indicator in accumulated_text for indicator in complete_sentence_indicators)
                
                # Check if accumulated text seems complete (length + indicators)
                is_substantial_input = len(accumulated_text.strip()) >= 10  # At least 10 characters
                is_likely_complete = has_sentence_ending or len(accumulated_text.split()) >= 5  # 5+ words or sentence ending
                
                # Only process if we have substantial and likely complete input
                if is_substantial_input and is_likely_complete:
                    user_text = accumulated_text.strip()
                    phone_manager.accumulated_texts[session_id] = ""
                    logger.info(f"Processing complete sentence: '{user_text}'")
                else:
                    logger.info(f"Accumulating more text... Current: '{accumulated_text}' (waiting for completion)")
                    return  # Wait for more input
            # pause_indicators = [',', ':', 'and', 'but', 'so', 'then', 'also']
            
            # text_lower = user_text.lower().strip()
            # accumulated_lower = accumulated_text.lower().strip()
            
            # Determine if we should respond now
            # should_respond_now = (
            #     # Ends with sentence terminator
            #     user_text.strip().endswith(tuple(complete_sentence_indicators)) or
            #     # Accumulated text is getting long
            #     len(accumulated_text.split()) >= 8 or
            #     # Contains question words (likely a complete question)
            #     any(word in accumulated_lower.split()[:3] for word in ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'should', 'do', 'does', 'is', 'are']) or
            #     # Contains greeting/farewell
            #     any(word in text_lower for word in ['hello', 'hi', 'hey', 'goodbye', 'bye', 'thanks', 'thank you'])
            # )
            
            # if not should_respond_now:
            #     logger.info(f"Waiting for more input... current: '{accumulated_text[:50]}...'")
            #     # Send acknowledgment but don't respond yet
            #     await safe_websocket_send(websocket, {
            #         "type": "speech_received",
            #         "message": f"Listening... ({len(accumulated_text.split())} words)",
            #         "session_id": session_id
            #     })
            #     return
            
            # Use the accumulated text for response
            # user_text = accumulated_text.strip()
            # phone_manager.accumulated_texts[session_id] = ""
        
        # Mark user as stopped speaking and add text to conversation
        conversation_flow_manager.stop_user_speaking(session_id)
        conversation_flow_manager.add_user_message(session_id, user_text)
        
        # SIMPLIFIED: Skip conversation flow manager check for now - always respond
        # Check if we should respond now or wait for more input
        # should_respond = conversation_flow_manager.should_respond_now(session_id)
        # if not should_respond:
        #     logger.info(f"Received user input, but waiting for pause before responding: {user_text[:30]}...")
        #     # Send acknowledgment but don't generate response yet
        #     await websocket.send_text(json.dumps({
        #         "type": "speech_received",
        #         "message": f"Received: {user_text[:50]}..."
        #     }))
        #     return
        
        logger.info(f"FORCING LLM PROCESSING for user input: '{user_text}'")  # Debug
        
        # STT completed successfully
        await send_stage_completed(websocket, "stt", f"Recognized: {user_text[:50]}...")
        await send_stage_active(websocket, "llm", "AI is processing your message...")
        
        logger.info(f"User said ({stt_duration:.2f}s): {user_text}")
        
        # Get conversation context from flow manager (with pruning if needed)
        conversation_context = conversation_flow_manager.get_conversation_context(session_id)
        
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
        
        # Update session conversation history with managed context
        if conversation_context:
            session.conversation_history = conversation_context
        else:
            # Add to conversation history
            session.conversation_history.append({"role": "user", "content": user_text})
        
        # Update conversation flow with user input
        conversation_flow_manager.handle_user_input(session_id, final_user_message)
        
        # CRITICAL: Mark session as having active AI response to prevent overlaps
        phone_manager.active_ai_responses.add(session_id)
        logger.info(f"🚀 Marked session {session_id} as having ACTIVE AI response")
        
        try:
            # Enhanced: Send immediate acknowledgment to keep WebSocket alive
            print("🔄 DEBUG: Sending processing_started notification")
            await safe_websocket_send(websocket, {
                "type": "processing_started",
                "message": "AI is processing your request...",
                "session_id": session_id,
                "timestamp": time.time()
            })
            
            # Enhanced: Start aggressive heartbeat during processing
            print("💓 Starting aggressive heartbeat task...")
            heartbeat_task = await start_heartbeat_task(websocket, session_id)
            
            # Phase 4: Get optimized LLM response with enhanced monitoring
            ai_text, llm_duration = await get_interruptible_llm_response(
                session, final_user_message, session.conversation_history, None, websocket
            )
            
            # Enhanced: Send intermediate update after LLM completion
            print("🔄 DEBUG: Sending llm_completed notification")
            await safe_websocket_send(websocket, {
                "type": "llm_completed",
                "message": "Generating audio...",
                "session_id": session_id,
                "text_preview": ai_text[:100] + "..." if len(ai_text) > 100 else ai_text,
                "timestamp": time.time()
            })
            
        except Exception as llm_error:
            # Clear active AI response on error
            phone_manager.active_ai_responses.discard(session_id)
            logger.error(f"LLM error for session {session_id}: {llm_error}")
            raise
        
        # Handle case where LLM response failed or was interrupted
        if ai_text is None or not ai_text.strip():
            logger.warning("LLM response was None or empty, using fallback")
            await send_stage_error(websocket, "llm", "Response generation failed")
            
            # Send a simple acknowledgment instead of failing completely
            await safe_websocket_send(websocket, {
                "type": "ai_response",
                "text": "I'm sorry, I didn't quite understand that. Could you try again?",
                "session_id": session_id,
                "timing": {
                    "stt": stt_duration,
                    "llm": 0.5,
                    "tts": 0.0,
                    "total": stt_duration + 0.5
                }
            })
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
        
        try:
            # Use the correct TTS service method for British accent
            logger.info(f"Starting TTS synthesis for text: '{clean_text[:50]}...'")
            
            # Create TTS task with heartbeat maintenance
            tts_task = asyncio.create_task(tts_client.synthesize_speech_api(
                text=clean_text,
                language=session.settings.get("language", "en"),
                voice=session.settings.get("voice", "default"),
                speed=session.settings.get("speed", 1.0),
                tts_mode="fast"  # Use fast mode for phone calls
            ))
            
            # Maintain WebSocket heartbeat during TTS processing
            logger.info(f"🔄 Starting TTS processing with WebSocket heartbeat for session {session_id}")
            
            async def maintain_tts_heartbeat():
                try:
                    while not tts_task.done():
                        await asyncio.sleep(3)  # Check every 3 seconds
                        if not tts_task.done():
                            try:
                                # FastAPI WebSocket doesn't have ping(), use send_text with ping message instead
                                await safe_websocket_send(websocket, {
                                    "type": "heartbeat",
                                    "timestamp": time.time()
                                })
                                logger.debug(f"💓 Sent heartbeat ping during TTS processing for session {session_id}")
                            except Exception as e:
                                logger.warning(f"Failed to send TTS heartbeat ping: {e}")
                                break
                except Exception as e:
                    logger.error(f"Error in TTS heartbeat maintenance: {e}")
            
            # Run TTS and heartbeat concurrently
            heartbeat_task = asyncio.create_task(maintain_tts_heartbeat())
            try:
                audio_response = await tts_task
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            logger.info(f"TTS response received: {type(audio_response)}, success: {audio_response.get('success') if isinstance(audio_response, dict) else 'N/A'}")
            
            # Extract audio data from response
            if audio_response and audio_response.get("success"):
                # Handle both response formats
                audio_base64 = audio_response.get("audio_data") or audio_response.get("audio_base64", "")
                if audio_base64:
                    try:
                        audio_response = base64.b64decode(audio_base64)
                        logger.info(f"Successfully decoded TTS audio: {len(audio_response)} bytes")
                    except Exception as decode_error:
                        logger.error(f"Failed to decode TTS audio: {decode_error}")
                        audio_response = None
                else:
                    logger.warning("TTS response success but no audio data found")
                    audio_response = None
            else:
                logger.warning(f"TTS response failed or invalid: {audio_response}")
                audio_response = None
                
        except Exception as e:
            logger.warning(f"Primary TTS service failed: {e}. Using fallback TTS service.")
            # Use fallback TTS service
            try:
                audio_response = await simple_tts_fallback.synthesize_speech(
                    clean_text,
                    voice=session.settings.get("voice", "default"),
                    language=session.settings.get("language", "en")
                )
                if audio_response:
                    logger.info(f"Fallback TTS succeeded: {len(audio_response)} bytes")
                else:
                    logger.warning("Fallback TTS returned no audio")
            except Exception as fallback_error:
                logger.error(f"Fallback TTS service also failed: {fallback_error}")
                audio_response = None
        
        tts_duration = time.time() - tts_start_time
        
        # Phase 4: Record TTS performance
        performance_monitor.record_tts_performance(
            session_id=session_id,
            duration=tts_duration,
            text_length=len(ai_text),
            audio_duration=len(audio_response) / 16000.0 if audio_response else 0.0,  # Estimate duration from bytes
            success=bool(audio_response),
            error=None if audio_response else "No audio generated"
        )
        
        if not audio_response:
            logger.error("TTS processing failed - no audio generated")
            await send_stage_error(websocket, "tts", "TTS processing failed")
            
            # Send a text-only response as fallback
            await safe_websocket_send(websocket, {
                "type": "ai_response",
                "text": ai_text,
                "session_id": session_id,
                "timing": {
                    "stt": stt_duration,
                    "llm": llm_duration,
                    "tts": tts_duration,
                    "total": total_duration
                },
                "error": "TTS audio generation failed, text-only response"
            })
            return
        
        # TTS completed successfully
        await send_stage_completed(websocket, "tts", "Audio ready for playback")
        
        # Phase 4: Calculate total interaction time and quality
        total_duration = time.time() - interaction_start_time
        current_quality = get_overall_quality()
        
        # Send optimized response
        if audio_response:
            audio_base64 = base64.b64encode(audio_response).decode()
        else:
            audio_base64 = ""
        
        response_data = {
            "type": "ai_response",
            "text": ai_text,
            "session_id": session_id,
            "timing": {
                "stt": stt_duration,
                "llm": llm_duration,
                "tts": tts_duration,
                "total": total_duration
            },
            "optimization": {
                "quality": current_quality.value,
                "model_used": session.settings.get("model", "gemma2:2b"),
                "performance_score": performance_monitor.get_session_score(session_id) if hasattr(performance_monitor, 'get_session_score') else 0.85
            }
        }
        
        # Only add audio if available
        if audio_base64:
            response_data["audio"] = audio_base64
        
        # CRITICAL: Track that AI is about to start responding (for smart interruption)
        logger.info(f"🤖 Sending AI response for session {session_id}")
        
        # Enhanced: Verify WebSocket connection before sending audio response
        from fastapi.websockets import WebSocketState
        if not websocket or websocket.client_state != WebSocketState.CONNECTED:
            logger.error(f"❌ CRITICAL: WebSocket disconnected before sending audio response for session {session_id}")
            logger.error(f"WebSocket state: {getattr(websocket, 'client_state', 'unknown')}")
            
            # Clear active response tracking since we can't send
            phone_manager.active_ai_responses.discard(session_id)
            return  # Exit early to prevent error
        
        # Enhanced: Send a pre-flight test message to verify connection
        print("🔄 Sending pre-flight connection test...")
        preflight_success = await safe_websocket_send(websocket, {
            "type": "preflight_test",
            "session_id": session_id,
            "timestamp": time.time()
        })
        
        # 🔧 ENHANCED: Don't fail if client has disconnected after receiving previous audio
        # This is normal behavior - user may close connection after hearing the response
        if not preflight_success:
            logger.info(f"⚠️ Pre-flight test failed - client may have disconnected (normal for session {session_id})")
            phone_manager.active_ai_responses.discard(session_id)
            return
        
        # Enhanced: Send audio in smaller chunks to prevent large payload timeouts
        if audio_base64 and len(audio_base64) > 50000:  # If audio is large (>50KB)
            print(f"🔄 Large audio detected ({len(audio_base64)} chars), sending in chunks...")
            chunk_size = 30000  # 30KB chunks
            total_chunks = (len(audio_base64) + chunk_size - 1) // chunk_size
            
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(audio_base64))
                chunk = audio_base64[start_idx:end_idx]
                
                chunk_data = {
                    "type": "audio_chunk",
                    "session_id": session_id,
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "audio_chunk": chunk,
                    "text": response_data.get("text", "") if i == 0 else "",  # Only send text with first chunk
                    "timing": response_data.get("timing", {}) if i == 0 else {}
                }
                
                chunk_success = await safe_websocket_send(websocket, chunk_data)
                if not chunk_success:
                    logger.error(f"❌ Failed to send audio chunk {i+1}/{total_chunks}")
                    phone_manager.active_ai_responses.discard(session_id)
                    return
                else:
                    print(f"✅ Sent audio chunk {i+1}/{total_chunks}")
                    
            print(f"✅ All {total_chunks} audio chunks sent successfully")
            phone_manager.active_ai_responses.discard(session_id)
            return
        
        # Send the response using enhanced safe send
        send_success = await safe_websocket_send(websocket, response_data)
        
        if send_success:
            # Mark that AI response has been sent (smart interrupt manager will track playback)
            logger.info(f"✅ AI response sent successfully for session {session_id}")
        else:
            logger.error(f"❌ Failed to send AI response for session {session_id}")
        
        # CRITICAL: Clear active AI response tracking to allow next request
        phone_manager.active_ai_responses.discard(session_id)
        logger.info(f"🏁 Cleared ACTIVE AI response flag for session {session_id}")
        
        # Phase 4: Record interaction success (using existing methods)
        # The individual component performance is already recorded above
        logger.info(f"Interaction completed: total={total_duration:.2f}s, stt={stt_duration:.2f}s, llm={llm_duration:.2f}s, tts={tts_duration:.2f}s")
        
        # Phase 3: Save to call history
        # Add user message
        call_history_service.add_message(
            session.call_id, 
            "user", 
            user_text, 
            int(stt_duration * 1000),  # Convert to milliseconds
            False
        )
        
        # Add AI response
        call_history_service.add_message(
            session.call_id, 
            "assistant", 
            ai_text, 
            int((llm_duration + tts_duration) * 1000),  # Convert to milliseconds
            False
        )
        
        logger.info(f"Optimized interaction completed ({total_duration:.2f}s, quality: {current_quality.value})")
        
        # Process any queued audio chunks after main response is completed
        queued_audio = phone_manager.accumulated_audio.get(session_id, [])
        if queued_audio:
            logger.info(f"Processing {len(queued_audio)} queued audio chunks for session {session_id}")
            # Clear the queue
            phone_manager.accumulated_audio[session_id] = []
            
            # Combine all queued audio chunks
            combined_audio = b''.join(queued_audio)
            if len(combined_audio) > 1000:  # Only process if we have substantial audio
                logger.info(f"Scheduling processing of combined queued audio: {len(combined_audio)} bytes")
                # Schedule processing of combined audio (don't await to avoid blocking)
                asyncio.create_task(_process_queued_audio(websocket, session_id, combined_audio))
            
    except Exception as e:
        logger.error(f"Error in optimized audio processing: {e}")
        
        # CRITICAL: Clear active AI response tracking on error to prevent deadlock
        phone_manager.active_ai_responses.discard(session_id)
        logger.warning(f"🚨 Cleared ACTIVE AI response flag for session {session_id} due to error")
        
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
        phone_manager.end_session(session_id)
        interrupt_service.unregister_session(session_id)
        
        # NEW: Clean up smart interrupt manager
        smart_interrupt_manager.cleanup_session(session_id)
        
        # Clean up conversation flow manager
        conversation_flow_manager.end_conversation(session_id)
        
        # Send comprehensive session summary
        await safe_websocket_send(websocket, {
            "type": "session_ended",
            "session_id": session_id,
            "duration": call_duration,
            "performance_summary": session_summary,
            "message": "Phone call session ended successfully"
        })
        
        logger.info(f"Optimized session {session_id} ended after {call_duration:.2f}s")
        
    except Exception as e:
        logger.error(f"Error ending optimized session: {e}")
        await safe_websocket_send(websocket, {
            "type": "error",
            "message": f"Error ending session: {str(e)}"
        })

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
