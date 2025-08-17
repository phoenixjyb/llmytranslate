"""
Android Streaming TTS Integration

This module integrates streaming TTS with the existing Android WebSocket endpoint
to provide real-time audio streaming for Android devices.
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from src.models.phone_call import PhoneCallSession

logger = logging.getLogger(__name__)

async def handle_android_streaming_text_input(websocket, message: Dict):
    """
    Enhanced Android text input handler with streaming TTS support.
    
    This function extends the existing Android text processing to support
    streaming TTS when the client requests it.
    """
    session_id = message["session_id"]
    user_text = message.get("text", "").strip()
    use_streaming_tts = message.get("use_streaming_tts", False)
    
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
            # NEW: Streaming TTS approach for Android
            await process_android_with_streaming_tts(websocket, session, user_text)
        else:
            # EXISTING: Traditional approach (use existing function)
            from src.api.routes.android import handle_android_text_input
            await handle_android_text_input(websocket, message)
            
    except Exception as e:
        logger.error(f"Android streaming processing error: {e}")
        await safe_android_send(websocket, {
            "type": "error",
            "message": f"Processing failed: {str(e)}",
            "session_id": session_id
        })

async def process_android_with_streaming_tts(websocket, session, user_text: str):
    """
    Process Android text input with streaming TTS support.
    """
    session_id = session.session_id
    
    try:
        # Send processing status
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
        
        # Prepare conversation context for LLM
        conversation_context = []
        
        # Add kid-friendly prompt if enabled
        if session.settings.get("kid_friendly", False):
            system_prompt = "You are a helpful, educational AI assistant for children. Keep responses appropriate, fun, and educational."
            conversation_context.append({"role": "system", "content": system_prompt})
        
        # Add recent conversation history (last 10 messages)
        for msg in session.conversation_history[-10:]:
            conversation_context.append(msg)
        
        # Get streaming LLM response
        async def create_android_llm_stream():
            """Create streaming LLM response for Android"""
            # Simulate LLM streaming by processing text in chunks
            # In production, this would connect to your Ollama streaming endpoint
            response_text = await get_llm_response_for_android(conversation_context, session.settings)
            
            # Split response into natural chunks for streaming
            sentences = response_text.split('. ')
            for sentence in sentences:
                if sentence.strip():
                    # Add punctuation back if it was stripped
                    chunk = sentence.strip()
                    if not chunk.endswith('.') and sentence != sentences[-1]:
                        chunk += '. '
                    
                    yield chunk
                    await asyncio.sleep(0.1)  # Small delay to simulate real streaming
        
        # Process streaming TTS chunks
        complete_text = ""
        chunk_index = 0
        
        async for text_chunk in create_android_llm_stream():
            complete_text += text_chunk
            
            # Send streaming audio chunk to Android
            await safe_android_send(websocket, {
                "type": "streaming_audio_chunk",
                "session_id": session_id,
                "chunk_index": chunk_index,
                "text": text_chunk,
                "audio_chunk": "",  # Android will use native TTS
                "content_type": "text/plain",
                "processing_time": 0.1,
                "is_final": False,
                "timestamp": time.time()
            })
            
            chunk_index += 1
            logger.debug(f"🎵 Sent Android streaming chunk {chunk_index}: '{text_chunk[:30]}...'")
        
        # Send completion notification
        await safe_android_send(websocket, {
            "type": "tts_streaming_completed",
            "session_id": session_id,
            "message": "AI response complete",
            "total_chunks": chunk_index,
            "complete_text": complete_text.strip(),
            "timestamp": time.time()
        })
        
        # Add AI response to conversation history
        session.conversation_history.append({
            "role": "assistant",
            "content": complete_text.strip(),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"✅ Android streaming TTS completed: {chunk_index} chunks, {len(complete_text)} chars")
        
    except Exception as e:
        logger.error(f"❌ Android streaming TTS error: {e}")
        await safe_android_send(websocket, {
            "type": "tts_streaming_error",
            "session_id": session_id,
            "error": str(e),
            "message": "Streaming TTS failed",
            "timestamp": time.time()
        })

async def get_llm_response_for_android(conversation_context, settings):
    """
    Get LLM response for Android - this should integrate with your existing LLM service.
    """
    try:
        # This should call your existing Ollama client
        from src.services.ollama_client import ollama_client
        
        llm_response = await ollama_client.chat_completion(
            messages=conversation_context,
            model=settings.get("model", "gemma2:270m"),
            stream=False
        )
        
        if llm_response.get("success", False):
            return llm_response["response"]
        else:
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
            
    except Exception as e:
        logger.error(f"LLM processing error for Android: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again."

async def safe_android_send(websocket, message: Dict[str, Any]):
    """
    Safely send WebSocket message to Android client.
    """
    try:
        await websocket.send_text(json.dumps(message))
    except Exception as e:
        logger.error(f"❌ Failed to send Android WebSocket message: {e}")

# Integration function for existing Android endpoint
async def enhance_android_endpoint_with_streaming_tts():
    """
    Instructions for integrating streaming TTS with existing Android endpoint.
    
    To integrate, modify your existing Android WebSocket message handler:
    
    1. Check for 'use_streaming_tts' in the incoming message
    2. If true, call handle_android_streaming_text_input() instead of regular handler
    3. Android client will receive streaming_audio_chunk messages
    4. Android TTS service can play chunks immediately using native TTS
    """
    return {
        "integration_point": "src/api/routes/android.py",
        "function": "handle_android_text_input",
        "modification": "Add streaming TTS support check",
        "benefits": [
            "Real-time audio streaming to Android",
            "Reduced perceived latency",
            "Native Android TTS integration",
            "Backward compatibility maintained"
        ]
    }
