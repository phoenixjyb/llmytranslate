"""
WebSocket Handler for Streaming TTS Integration

This module integrates the streaming TTS service with the phone call WebSocket system,
enabling real-time audio streaming as LLM generates text.
"""

import asyncio
import json
import time
import base64
from typing import Dict, Any, AsyncGenerator
import logging
from datetime import datetime

from .streaming_tts_service import StreamingTTSService, AudioChunk

logger = logging.getLogger(__name__)

class StreamingTTSWebSocketHandler:
    """
    Handles WebSocket communication for streaming TTS functionality.
    Integrates with the existing phone call system to provide real-time audio streaming.
    """
    
    def __init__(self, streaming_tts_service: StreamingTTSService):
        """
        Initialize the WebSocket handler.
        
        Args:
            streaming_tts_service: Streaming TTS service instance
        """
        self.streaming_tts = streaming_tts_service
        self.active_streams = {}  # session_id -> stream info
        
    async def handle_llm_response_with_streaming_tts(
        self,
        websocket,
        session_id: str,
        llm_text_stream: AsyncGenerator[str, None],
        language: str = "en",
        voice: str = "default",
        speed: float = 1.0,
        tts_mode: str = "fast"
    ):
        """
        Handle LLM response with streaming TTS and send audio chunks via WebSocket.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            llm_text_stream: Streaming text from LLM
            language: Target language for TTS
            voice: Voice to use
            speed: Speech speed
            tts_mode: TTS quality mode
        """
        logger.info(f"🎵 Starting streaming TTS for session {session_id}")
        
        stream_info = {
            "session_id": session_id,
            "start_time": time.time(),
            "chunk_count": 0,
            "total_audio_size": 0,
            "complete_text": "",
            "is_active": True
        }
        self.active_streams[session_id] = stream_info
        
        try:
            # Send streaming start notification
            await self._send_websocket_message(websocket, {
                "type": "tts_streaming_started",
                "session_id": session_id,
                "message": "Starting real-time speech synthesis...",
                "timestamp": time.time()
            })
            
            # Process streaming TTS
            audio_chunks = []
            first_chunk_sent = False
            
            async for audio_chunk in self.streaming_tts.stream_tts_from_llm(
                llm_text_stream, session_id, language, voice, speed, tts_mode
            ):
                # Update stream info
                stream_info["chunk_count"] += 1
                stream_info["total_audio_size"] += len(audio_chunk.audio_data)
                stream_info["complete_text"] += audio_chunk.text + " "
                
                # Convert audio to base64 for WebSocket transmission
                audio_base64 = base64.b64encode(audio_chunk.audio_data).decode('utf-8')
                
                # Send audio chunk via WebSocket
                chunk_message = {
                    "type": "audio_chunk",
                    "session_id": session_id,
                    "chunk_index": audio_chunk.index,
                    "total_chunks": audio_chunk.total_chunks,  # May be None until final chunk
                    "audio_chunk": audio_base64,
                    "text": audio_chunk.text,
                    "content_type": audio_chunk.content_type,
                    "processing_time": audio_chunk.processing_time,
                    "is_final": audio_chunk.total_chunks is not None,
                    "stream_info": {
                        "chunks_sent": stream_info["chunk_count"],
                        "total_audio_kb": round(stream_info["total_audio_size"] / 1024, 2),
                        "stream_duration": round(time.time() - stream_info["start_time"], 2)
                    },
                    "timestamp": time.time()
                }
                
                await self._send_websocket_message(websocket, chunk_message)
                
                # Send first chunk notification for UI feedback
                if not first_chunk_sent:
                    await self._send_websocket_message(websocket, {
                        "type": "first_audio_chunk",
                        "session_id": session_id,
                        "message": "First audio chunk ready, playback can begin",
                        "latency_ms": round((time.time() - stream_info["start_time"]) * 1000, 2),
                        "timestamp": time.time()
                    })
                    first_chunk_sent = True
                
                audio_chunks.append(audio_chunk)
                logger.debug(f"📦 Sent audio chunk {audio_chunk.index} ({len(audio_chunk.audio_data)} bytes)")
            
            # Send completion notification
            total_duration = time.time() - stream_info["start_time"]
            completion_message = {
                "type": "tts_streaming_completed",
                "session_id": session_id,
                "message": "Real-time speech synthesis completed",
                "summary": {
                    "total_chunks": len(audio_chunks),
                    "total_audio_size_kb": round(stream_info["total_audio_size"] / 1024, 2),
                    "total_duration_ms": round(total_duration * 1000, 2),
                    "average_chunk_size_kb": round((stream_info["total_audio_size"] / len(audio_chunks)) / 1024, 2) if audio_chunks else 0,
                    "text_length": len(stream_info["complete_text"]),
                    "processing_efficiency": round(len(stream_info["complete_text"]) / total_duration, 2)  # chars/second
                },
                "final_text": stream_info["complete_text"].strip(),
                "timestamp": time.time()
            }
            
            await self._send_websocket_message(websocket, completion_message)
            
            logger.info(
                f"✅ Streaming TTS completed for session {session_id}: "
                f"{len(audio_chunks)} chunks, "
                f"{round(stream_info['total_audio_size'] / 1024, 2)}KB, "
                f"{round(total_duration, 2)}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Streaming TTS error for session {session_id}: {e}")
            
            # Send error notification
            await self._send_websocket_message(websocket, {
                "type": "tts_streaming_error",
                "session_id": session_id,
                "error": str(e),
                "message": "Real-time speech synthesis failed",
                "timestamp": time.time()
            })
            
        finally:
            # Cleanup
            stream_info["is_active"] = False
            if session_id in self.active_streams:
                del self.active_streams[session_id]
    
    async def _send_websocket_message(self, websocket, message: Dict[str, Any]):
        """
        Safely send a message via WebSocket with error handling.
        
        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Failed to send WebSocket message: {e}")
    
    def get_stream_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current status of a streaming session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Stream status information
        """
        if session_id not in self.active_streams:
            return {"status": "not_found"}
        
        stream_info = self.active_streams[session_id]
        current_time = time.time()
        
        return {
            "status": "active" if stream_info["is_active"] else "completed",
            "session_id": session_id,
            "duration_ms": round((current_time - stream_info["start_time"]) * 1000, 2),
            "chunks_sent": stream_info["chunk_count"],
            "total_audio_kb": round(stream_info["total_audio_size"] / 1024, 2),
            "current_text_length": len(stream_info["complete_text"]),
            "processing_rate": round(len(stream_info["complete_text"]) / (current_time - stream_info["start_time"]), 2) if current_time > stream_info["start_time"] else 0
        }
    
    def stop_stream(self, session_id: str):
        """
        Stop an active streaming session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_streams:
            self.active_streams[session_id]["is_active"] = False
            logger.info(f"🛑 Stopped streaming TTS for session {session_id}")

class LLMStreamingSimulator:
    """
    Simulates LLM streaming for testing the streaming TTS WebSocket handler.
    """
    
    @staticmethod
    async def create_llm_stream(prompt: str, model: str = "gemma2:2b") -> AsyncGenerator[str, None]:
        """
        Create a realistic LLM streaming simulation.
        
        Args:
            prompt: User prompt (for context)
            model: Model name
            
        Yields:
            str: Text chunks as they would come from a real LLM
        """
        # Simulate a realistic AI response
        response_text = """
        Hello! I understand you're interested in streaming text-to-speech technology. 
        This is a fascinating area that combines natural language processing with real-time audio synthesis. 
        
        The key advantage of streaming TTS is that it dramatically reduces perceived latency. 
        Instead of waiting for the entire response to be generated before starting speech synthesis, 
        we can begin converting text to audio as soon as we have complete sentences or phrases.
        
        This approach is particularly valuable for conversational AI applications, where users expect 
        natural, fluid interactions. By streaming audio chunks, we can create the illusion of 
        real-time conversation, even when the underlying AI processing takes several seconds.
        
        The technical implementation involves several components: text chunking algorithms that 
        identify natural break points, asynchronous audio generation pipelines, and WebSocket 
        streaming protocols for real-time delivery. Each component must be carefully optimized 
        to minimize latency while maintaining audio quality.
        """
        
        # Simulate realistic typing patterns
        sentences = response_text.strip().split('. ')
        
        for sentence in sentences:
            words = sentence.split()
            current_chunk = ""
            
            for i, word in enumerate(words):
                current_chunk += word + " "
                
                # Yield chunks of varying sizes (1-4 words)
                chunk_size = 2 if i < len(words) - 1 else len(words) - i
                if (i + 1) % chunk_size == 0 or i == len(words) - 1:
                    yield current_chunk
                    current_chunk = ""
                    
                    # Simulate thinking/processing delays
                    delay = 0.1 + (0.2 if word.endswith(',') else 0.05)
                    await asyncio.sleep(delay)
            
            # Pause between sentences
            if sentence != sentences[-1]:
                yield ". "
                await asyncio.sleep(0.3)

# Integration function for existing phone call system
async def integrate_streaming_tts_with_phone_call(
    websocket,
    session_id: str,
    user_text: str,
    llm_service,
    streaming_tts_handler: StreamingTTSWebSocketHandler,
    language: str = "en",
    voice: str = "default",
    speed: float = 1.0,
    tts_mode: str = "fast"
):
    """
    Integration function to add streaming TTS to existing phone call system.
    
    This function can be called from the existing process_llm_response function
    to enable streaming TTS instead of the current wait-for-complete approach.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
        user_text: User input text
        llm_service: LLM service for generating responses
        streaming_tts_handler: Streaming TTS WebSocket handler
        language: Target language
        voice: Voice to use
        speed: Speech speed
        tts_mode: TTS quality mode
    """
    try:
        logger.info(f"🚀 Starting integrated streaming TTS for session {session_id}")
        
        # Create LLM stream (replace with actual LLM streaming call)
        llm_stream = LLMStreamingSimulator.create_llm_stream(user_text)
        
        # Process with streaming TTS
        await streaming_tts_handler.handle_llm_response_with_streaming_tts(
            websocket, session_id, llm_stream, language, voice, speed, tts_mode
        )
        
        logger.info(f"✅ Integrated streaming TTS completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Integrated streaming TTS error for session {session_id}: {e}")
        raise
