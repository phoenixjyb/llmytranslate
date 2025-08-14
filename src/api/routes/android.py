"""
Android-specific API routes for LLMyTranslate.
Optimized for native Android STT/TTS with text-only WebSocket communication.
"""

import asyncio
import json
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...services.ollama_client import ollama_client
from ...services.conversation_flow_manager import conversation_flow_manager
from ...services.kid_friendly_service import kid_friendly_service
from ...services.call_history_service import call_history_service
from ...services.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/android", tags=["android"])

class AndroidSession:
    """Android-specific session management."""
    
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.start_time = time.time()
        self.settings = {
            "language": "en-US",
            "kid_friendly": False,
            "model": "gemma2:2b",
            "use_native_stt": True,
            "use_native_tts": True,
            "audio_transfer": False
        }
        self.conversation_history = []
        self.last_activity = time.time()

class AndroidSessionManager:
    """Manages Android app sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, AndroidSession] = {}
        
    def create_session(self, websocket: WebSocket) -> str:
        session_id = f"android_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = AndroidSession(session_id, websocket)
        logger.info(f"Created Android session: {session_id}")
        return session_id
        
    def get_session(self, session_id: str) -> Optional[AndroidSession]:
        return self.sessions.get(session_id)
        
    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Removed Android session: {session_id}")

# Global session manager
android_manager = AndroidSessionManager()

async def safe_android_send(websocket: WebSocket, data: dict):
    """Safely send data via WebSocket for Android clients."""
    try:
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_text(json.dumps(data))
            return True
    except Exception as e:
        logger.error(f"Failed to send Android WebSocket message: {e}")
        return False

@router.websocket("/stream")
async def android_websocket(websocket: WebSocket):
    """
    Android-optimized WebSocket endpoint for text-only communication.
    No audio transfer - uses native Android STT/TTS.
    """
    await websocket.accept()
    session_id = None
    
    try:
        logger.info("Android WebSocket connection established")
        
        while True:
            # Receive message from Android app
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            session_id = message.get("session_id")
            
            logger.info(f"Android message: type={message_type}, session={session_id}")
            
            if message_type == "session_start":
                session_id = await handle_android_session_start(websocket, message)
                
            elif message_type == "text_input":
                await handle_android_text_input(websocket, message)
                
            elif message_type == "settings_update":
                await handle_android_settings_update(websocket, message)
                
            elif message_type == "session_end":
                await handle_android_session_end(websocket, message)
                break
                
            else:
                await safe_android_send(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"Android WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Android WebSocket error: {e}")
        await safe_android_send(websocket, {
            "type": "error", 
            "message": f"Server error: {str(e)}"
        })
    finally:
        if session_id:
            android_manager.remove_session(session_id)

async def handle_android_session_start(websocket: WebSocket, message: Dict) -> str:
    """Initialize Android session with optimized settings."""
    session_id = android_manager.create_session(websocket)
    session = android_manager.get_session(session_id)
    
    # Apply Android-specific settings
    settings = message.get("settings", {})
    session.settings.update(settings)
    
    # Start conversation management
    conversation_flow_manager.start_conversation(session_id, websocket)
    
    # Send confirmation with session info
    await safe_android_send(websocket, {
        "type": "session_started",
        "session_id": session_id,
        "server_info": {
            "version": "android_optimized",
            "features": ["native_stt", "native_tts", "text_only", "fast_llm"],
            "models_available": ["gemma2:2b"]
        },
        "settings": session.settings
    })
    
    # Send kid-friendly greeting if enabled
    if session.settings.get("kid_friendly", False):
        greeting = kid_friendly_service.get_kid_friendly_greeting(
            session.settings.get("language", "en")
        )
        await safe_android_send(websocket, {
            "type": "ai_message",
            "text": greeting,
            "session_id": session_id
        })
    
    logger.info(f"Android session started: {session_id}")
    return session_id

async def handle_android_text_input(websocket: WebSocket, message: Dict):
    """Process text input from Android STT and generate AI response with optional streaming TTS."""
    session_id = message["session_id"]
    user_text = message.get("text", "").strip()
    use_streaming_tts = message.get("use_streaming_tts", False)  # NEW: Check for streaming TTS request
    
    if not user_text:
        await safe_android_send(websocket, {
            "type": "error",
            "message": "Empty text input received"
        })
        return
    
    session = android_manager.get_session(session_id)
    if not session:
        await safe_android_send(websocket, {
            "type": "error",
            "message": "Session not found"
        })
        return
    
    try:
        # Update last activity
        session.last_activity = time.time()
        
        if use_streaming_tts:
            # NEW: Use streaming TTS approach
            await process_android_with_streaming_tts(websocket, session, user_text)
        else:
            # EXISTING: Traditional approach
            await process_android_traditional(websocket, session, user_text)
            
    except Exception as e:
        logger.error(f"Android text processing error: {e}")
        await safe_android_send(websocket, {
            "type": "error",
            "message": f"Processing failed: {str(e)}",
            "session_id": session_id
        })

async def process_android_with_streaming_tts(websocket: WebSocket, session, user_text: str):
    """NEW: Process Android text input with streaming TTS support."""
    session_id = session.session_id
    
    try:
        # Send streaming start notification
        await safe_android_send(websocket, {
            "type": "tts_streaming_started",
            "message": "AI is thinking and will speak as thoughts form...",
            "session_id": session_id,
            "timestamp": time.time()
        })
        
        # Add to conversation history
        session.conversation_history.append({
            "role": "user",
            "content": user_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Prepare conversation context as a single prompt
        conversation_prompt = ""
        
        # Add kid-friendly prompt if enabled
        if session.settings.get("kid_friendly", False):
            system_prompt = kid_friendly_service.get_kid_friendly_prompt_prefix(
                session.settings.get("language", "en")
            )
            conversation_prompt += f"System: {system_prompt}\n\n"
        
        # Add recent conversation history (last 10 messages)
        for msg in session.conversation_history[-10:]:
            role = msg["role"].title()
            content = msg["content"]
            conversation_prompt += f"{role}: {content}\n"
        
        # Add current user message
        conversation_prompt += f"User: {user_text}\nAssistant:"
        
        # Get LLM response
        llm_start_time = time.time()
        llm_response = await ollama_client.chat_completion(
            message=conversation_prompt,
            model=session.settings.get("model", "gemma2:2b")
        )
        
        llm_duration = time.time() - llm_start_time
        
        if not llm_response.get("success", False):
            raise Exception(f"LLM processing failed: {llm_response.get('error', 'Unknown error')}")
        
        ai_text = llm_response["response"]
        clean_ai_text = clean_text_for_android_tts(ai_text)
        
        # Split response into chunks for streaming
        chunks = split_text_for_streaming(clean_ai_text)
        total_chunks = len(chunks)
        
        # Send streaming audio chunks
        for i, chunk in enumerate(chunks):
            await safe_android_send(websocket, {
                "type": "streaming_audio_chunk",
                "session_id": session_id,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "text": chunk,
                "audio_chunk": "",  # Android uses native TTS, no audio data needed
                "content_type": "text/plain",
                "processing_time": 0.1,
                "is_final": i == total_chunks - 1,
                "timestamp": time.time()
            })
            
            # Small delay between chunks for natural flow
            await asyncio.sleep(0.2)
            logger.debug(f"🎵 Sent Android chunk {i+1}/{total_chunks}: '{chunk[:30]}...'")
        
        # Send completion notification
        await safe_android_send(websocket, {
            "type": "tts_streaming_completed",
            "session_id": session_id,
            "message": "AI response complete",
            "summary": {
                "total_chunks": total_chunks,
                "total_duration_ms": round(llm_duration * 1000, 2),
                "text_length": len(clean_ai_text)
            },
            "timestamp": time.time()
        })
        
        # Add to conversation history
        session.conversation_history.append({
            "role": "assistant",
            "content": ai_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Record performance metrics
        performance_monitor.record_llm_performance(
            session_id=session_id,
            duration=llm_duration,
            model=session.settings.get("model", "gemma2:2b"),
            input_length=len(user_text),
            output_length=len(ai_text),
            success=True
        )
        
        logger.info(f"✅ Android streaming TTS completed: {total_chunks} chunks, {llm_duration:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Android streaming TTS error: {e}")
        await safe_android_send(websocket, {
            "type": "tts_streaming_error",
            "session_id": session_id,
            "error": str(e),
            "message": "Streaming TTS failed",
            "timestamp": time.time()
        })

async def process_android_traditional(websocket: WebSocket, session, user_text: str):
    """EXISTING: Traditional Android text processing (maintain compatibility)."""
    session_id = session.session_id
    
    # Send processing status
    await safe_android_send(websocket, {
        "type": "processing_started", 
        "message": "AI is thinking...",
        "session_id": session_id
    })
    
    # Add to conversation history
    session.conversation_history.append({
        "role": "user",
        "content": user_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Prepare conversation context as a single prompt
    conversation_prompt = ""
    
    # Add kid-friendly prompt if enabled
    if session.settings.get("kid_friendly", False):
        system_prompt = kid_friendly_service.get_kid_friendly_prompt_prefix(
            session.settings.get("language", "en")
        )
        conversation_prompt += f"System: {system_prompt}\n\n"
    
    # Add recent conversation history (last 10 messages)
    for msg in session.conversation_history[-10:]:
        role = msg["role"].title()
        content = msg["content"]
        conversation_prompt += f"{role}: {content}\n"
    
    # Add current user message
    conversation_prompt += f"User: {user_text}\nAssistant:"
    
    # Start LLM processing timer
    llm_start_time = time.time()
    
    # Get AI response
    llm_response = await ollama_client.chat_completion(
        message=conversation_prompt,
        model=session.settings.get("model", "gemma2:2b")
    )
    
    llm_duration = time.time() - llm_start_time
    
    if not llm_response.get("success", False):
        raise Exception(f"LLM processing failed: {llm_response.get('error', 'Unknown error')}")
    
    ai_text = llm_response["response"]
    
    # Clean text for better TTS (remove emojis, fix formatting)
    clean_ai_text = clean_text_for_android_tts(ai_text)
    
    # Add to conversation history
    session.conversation_history.append({
        "role": "assistant", 
        "content": ai_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Send AI response to Android
    await safe_android_send(websocket, {
        "type": "ai_response",
        "text": clean_ai_text,
        "original_text": ai_text,
        "session_id": session_id,
        "timing": {
            "llm_processing": llm_duration,
            "total_processing": time.time() - llm_start_time
        },
        "use_native_tts": True  # Signal Android to use native TTS
    })
    
    # Record performance metrics
    performance_monitor.record_llm_performance(
        session_id=session_id,
        duration=llm_duration,
        model=session.settings.get("model", "gemma2:2b"),
        input_length=len(user_text),
        output_length=len(ai_text),
        success=True
    )
    
    logger.info(f"Android conversation processed in {llm_duration:.2f}s: {user_text[:50]}...")

def split_text_for_streaming(text: str) -> list[str]:
    """Split text into natural chunks for streaming TTS."""
    # Split by sentences first
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Add the sentence to current chunk
        candidate_chunk = current_chunk + sentence
        
        # If adding punctuation back
        if sentence != sentences[-1]:
            candidate_chunk += '. '
        
        # Check if chunk is getting too long
        if len(candidate_chunk) > 100 and current_chunk:
            # Save current chunk and start new one
            chunks.append(current_chunk.strip())
            current_chunk = sentence
            if sentence != sentences[-1]:
                current_chunk += '. '
        else:
            current_chunk = candidate_chunk
    
    # Add final chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Ensure we have at least one chunk
    if not chunks:
        chunks = [text]
    
    return chunks

async def handle_android_settings_update(websocket: WebSocket, message: Dict):
    """Update session settings from Android app."""
    session_id = message["session_id"]
    session = android_manager.get_session(session_id)
    
    if not session:
        await safe_android_send(websocket, {
            "type": "error",
            "message": "Session not found"
        })
        return
    
    new_settings = message.get("settings", {})
    session.settings.update(new_settings)
    
    await safe_android_send(websocket, {
        "type": "settings_updated",
        "settings": session.settings,
        "session_id": session_id
    })
    
    logger.info(f"Android settings updated: {session_id}")

async def handle_android_session_end(websocket: WebSocket, message: Dict):
    """End Android session and cleanup."""
    session_id = message["session_id"]
    session = android_manager.get_session(session_id)
    
    if session:
        # Save conversation to history
        duration = time.time() - session.start_time
        call_history_service.save_call_history(
            session_id=session_id,
            user_id="android_user",  # Could be enhanced with actual user management
            start_time=datetime.fromtimestamp(session.start_time),
            end_time=datetime.now(),
            duration=duration,
            conversation_data=session.conversation_history,
            call_type="android_text_chat"
        )
        
        # End conversation management
        conversation_flow_manager.end_conversation(session_id)
        
        # Remove session
        android_manager.remove_session(session_id)
    
    await safe_android_send(websocket, {
        "type": "session_ended",
        "session_id": session_id,
        "message": "Session ended successfully"
    })

def clean_text_for_android_tts(text: str) -> str:
    """Clean text for optimal Android TTS synthesis."""
    import re
    
    # Remove emojis (Android TTS handles them better than server TTS)
    emoji_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    
    # Fix common formatting issues
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold markdown
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic markdown
    text = re.sub(r'`(.*?)`', r'\1', text)        # Remove code markdown
    text = re.sub(r'\s+', ' ', text)              # Normalize whitespace
    
    return text.strip()

# REST API endpoints for Android app

@router.get("/health")
async def android_health_check():
    """Health check endpoint for Android app."""
    return {
        "status": "healthy",
        "service": "android_api",
        "features": ["text_chat", "native_stt", "native_tts"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/discover")
async def android_service_discovery():
    """Service discovery endpoint for Android network scanning."""
    return {
        "service_name": "LLMyTranslate",
        "service_type": "llm_translation",
        "version": "android_optimized",
        "websocket_endpoint": "/api/android/stream",
        "capabilities": {
            "text_chat": True,
            "voice_chat": True,
            "translation": True,
            "kid_friendly": True,
            "native_stt_supported": True,
            "native_tts_supported": True
        },
        "models": ["gemma2:2b"],
        "languages": ["en-US", "zh-CN", "es-ES", "fr-FR", "de-DE"]
    }

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    settings: Optional[Dict] = None

@router.post("/chat")
async def android_simple_chat(request: ChatRequest):
    """Simple REST endpoint for Android text chat (non-WebSocket)."""
    try:
        # Create temporary session for REST chat
        temp_session_id = f"rest_{uuid.uuid4().hex[:8]}"
        
        # Use default settings
        settings = request.settings or {
            "model": "gemma2:2b",
            "language": "en-US",
            "kid_friendly": False
        }
        
        # Prepare conversation context as a single prompt
        conversation_prompt = ""
        if settings.get("kid_friendly", False):
            system_prompt = kid_friendly_service.get_kid_friendly_prompt_prefix(
                settings.get("language", "en")
            )
            conversation_prompt += f"System: {system_prompt}\n\n"
        
        conversation_prompt += f"User: {request.message}\nAssistant:"
        
        # Get AI response
        llm_response = await ollama_client.chat_completion(
            message=conversation_prompt,
            model=settings.get("model", "gemma2:2b")
        )
        
        if not llm_response.get("success", False):
            raise HTTPException(status_code=500, detail="LLM processing failed")
        
        ai_text = llm_response["response"]
        clean_ai_text = clean_text_for_android_tts(ai_text)
        
        return {
            "success": True,
            "response": clean_ai_text,
            "original_response": ai_text,
            "session_id": temp_session_id,
            "processing_time": llm_response.get("processing_time", 0),
            "model_used": settings.get("model", "gemma2:2b")
        }
        
    except Exception as e:
        logger.error(f"Android REST chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
