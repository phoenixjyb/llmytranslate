"""
Streaming TTS WebSocket Route

Provides real-time text-to-speech streaming for web clients.
Converts LLM text responses into chunked audio streams for fluid conversation experience.
"""

import json
import time
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from ...services.ollama_client import OllamaClient

# Initialize services
router = APIRouter()
ollama_client = OllamaClient()

# Session management for streaming TTS
streaming_sessions = {}

class StreamingTTSSession:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.session_id = f"streaming_tts_{int(time.time() * 1000)}"
        self.conversation_history = []
        self.is_active = False
        self.start_time = time.time()
        
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

async def safe_websocket_send(websocket: WebSocket, data: Dict[str, Any]):
    """Safely send data via WebSocket."""
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(json.dumps(data))
        else:
            print(f"❌ WebSocket not connected, skipping message: {data.get('type', 'unknown')}")
    except Exception as e:
        print(f"❌ Failed to send WebSocket message: {e}")

@router.websocket("/ws/streaming-tts")
async def streaming_tts_websocket(websocket: WebSocket):
    """
    Production WebSocket endpoint for streaming TTS functionality.
    
    Integrates with the main chat interface for real-time audio responses.
    
    Message Types:
    - start_streaming_chat: Start streaming TTS for a chat message (production)
    - streaming_tts_request: Start streaming TTS for a message (legacy)
    - tts_streaming_started: Indicates streaming has begun
    - streaming_audio_chunk: Individual audio/text chunks  
    - tts_streaming_completed: Final completion notification
    - tts_streaming_error: Error during streaming
    - ping/pong: Connection health checks
    """
    await websocket.accept()
    session = StreamingTTSSession(websocket)
    streaming_sessions[session.session_id] = session
    
    print(f"🎵 Production Streaming TTS WebSocket connected: {session.session_id}")
    
    try:
        while True:
            # Receive message from web client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            print(f"📥 Production streaming message: {message_type}")
            
            if message_type == "start_streaming_chat":
                # Production chat interface request
                await handle_streaming_tts_request(websocket, session, message)
                
            elif message_type == "streaming_tts_request":
                # Legacy test interface request
                await handle_streaming_tts_request(websocket, session, message)
                
            elif message_type == "ping":
                # Connection health check
                await safe_websocket_send(websocket, {
                    "type": "pong",
                    "timestamp": time.time(),
                    "session_id": session.session_id
                })
                
            else:
                print(f"🎵 Unknown message type: {message_type}")
                await safe_websocket_send(websocket, {
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "session_id": session.session_id
                })
                
    except WebSocketDisconnect:
        print(f"🔌 Production Streaming TTS WebSocket disconnected: {session.session_id}")
    except Exception as e:
        print(f"❌ Production Streaming TTS WebSocket error: {e}")
        await safe_websocket_send(websocket, {
            "type": "tts_streaming_error",
            "error": str(e),
            "session_id": session.session_id
        })
    finally:
        # Cleanup session
        if session.session_id in streaming_sessions:
            del streaming_sessions[session.session_id]
        print(f"🧹 Production Streaming TTS session cleaned up: {session.session_id}")

async def handle_streaming_tts_request(websocket: WebSocket, session: StreamingTTSSession, message: Dict[str, Any]):
    """Handle streaming TTS request from web client."""
    user_message = message.get("message", "").strip()
    conversation_id = message.get("conversation_id")
    model = message.get("model", "gemma2:2b")
    voice_settings = message.get("voice_settings", {})
    
    if not user_message:
        await safe_websocket_send(websocket, {
            "type": "tts_streaming_error", 
            "error": "Empty message received"
        })
        return
    
    try:
        # Add user message to history
        session.add_to_history("user", user_message)
        
        # Send streaming started notification
        await safe_websocket_send(websocket, {
            "type": "tts_streaming_started",
            "message": "AI is thinking and will speak as thoughts form...",
            "session_id": session.session_id,
            "timestamp": time.time()
        })
        
        # Prepare conversation context as single prompt
        conversation_prompt = ""
        
        # Add recent conversation history (last 10 messages)
        for msg in session.conversation_history[-10:]:
            role = msg["role"].title()
            content = msg["content"]
            conversation_prompt += f"{role}: {content}\\n"
        
        # Add current user message
        conversation_prompt += f"User: {user_message}\\nAssistant:"
        
        print(f"🤖 Getting LLM response for: {user_message[:50]}...")
        
        # Get LLM response
        llm_start_time = time.time()
        llm_response = await ollama_client.chat_completion(
            message=conversation_prompt,
            model=model
        )
        
        llm_duration = time.time() - llm_start_time
        
        if not llm_response.get("success", False):
            raise Exception(f"LLM processing failed: {llm_response.get('error', 'Unknown error')}")
        
        ai_text = llm_response["response"]
        
        # Add AI response to history
        session.add_to_history("assistant", ai_text)
        
        print(f"🎵 Starting streaming TTS for response: {ai_text[:50]}...")
        
        # Split response into chunks for streaming
        chunks = split_text_for_streaming(ai_text)
        total_chunks = len(chunks)
        
        print(f"📦 Split into {total_chunks} chunks for streaming")
        
        # Send streaming audio chunks
        for i, chunk in enumerate(chunks):
            await safe_websocket_send(websocket, {
                "type": "streaming_audio_chunk",
                "session_id": session.session_id,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "text": chunk,
                "audio_chunk": "",  # Web client uses Speech Synthesis API
                "content_type": "text/plain",
                "processing_time": 0.1,
                "is_final": i == total_chunks - 1,
                "timestamp": time.time(),
                "voice_settings": voice_settings
            })
            
            # Small delay between chunks for natural flow
            await asyncio.sleep(0.3)
            print(f"🎵 Sent chunk {i+1}/{total_chunks}: '{chunk[:30]}...'")
        
        # Send completion notification
        await safe_websocket_send(websocket, {
            "type": "tts_streaming_completed",
            "session_id": session.session_id,
            "message": "Streaming TTS completed successfully",
            "summary": {
                "total_chunks": total_chunks,
                "total_duration_ms": round(llm_duration * 1000, 2),
                "text_length": len(ai_text),
                "model_used": model
            },
            "session_info": {
                "conversation_id": conversation_id,
                "session_duration": time.time() - session.start_time
            },
            "timestamp": time.time()
        })
        
        # Record performance metrics (optional)
        print(f"📊 Performance: {llm_duration:.2f}s for {len(user_message)} chars input, {len(ai_text)} chars output")
        
        print(f"✅ Streaming TTS completed: {total_chunks} chunks, {llm_duration:.2f}s")
        
    except Exception as e:
        print(f"❌ Streaming TTS error: {e}")
        await safe_websocket_send(websocket, {
            "type": "tts_streaming_error",
            "session_id": session.session_id,
            "error": str(e),
            "message": "Streaming TTS failed",
            "timestamp": time.time()
        })

def split_text_for_streaming(text: str) -> List[str]:
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
        
        # Check if chunk is getting too long (optimal for web TTS)
        if len(candidate_chunk) > 80 and current_chunk:
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
    
    # Further split very long chunks
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > 120:
            # Split by commas or other natural breaks
            sub_chunks = chunk.split(', ')
            temp_chunk = ""
            for sub in sub_chunks:
                if len(temp_chunk + sub) > 100 and temp_chunk:
                    final_chunks.append(temp_chunk.strip())
                    temp_chunk = sub
                    if sub != sub_chunks[-1]:
                        temp_chunk += ', '
                else:
                    temp_chunk += sub
                    if sub != sub_chunks[-1]:
                        temp_chunk += ', '
            if temp_chunk.strip():
                final_chunks.append(temp_chunk.strip())
        else:
            final_chunks.append(chunk)
    
    return final_chunks

# Health check endpoint for streaming TTS
@router.get("/api/streaming-tts/health")
async def streaming_tts_health():
    """Health check for streaming TTS service."""
    return {
        "status": "healthy",
        "service": "streaming-tts",
        "active_sessions": len(streaming_sessions),
        "timestamp": time.time()
    }

@router.get("/api/streaming-tts/stats")
async def streaming_tts_stats():
    """Get detailed statistics about active streaming TTS sessions."""
    active_sessions = [
        {
            "session_id": session.session_id,
            "start_time": session.start_time,
            "conversation_length": len(session.conversation_history),
            "is_active": session.is_active,
            "duration": time.time() - session.start_time
        }
        for session in streaming_sessions.values()
        if session.is_active
    ]
    
    return {
        "active_sessions": len(active_sessions),
        "total_sessions": len(streaming_sessions),
        "sessions": active_sessions,
        "timestamp": time.time()
    }

print("🎵 Production Streaming TTS routes loaded and ready!")
