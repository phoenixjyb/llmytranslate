"""
Integration Example: How to Add Streaming TTS to Your Existing Phone Call System

This file shows how to integrate the streaming TTS service with your existing
phone call WebSocket system to enable real-time audio streaming.
"""

import asyncio
import json
import time
import base64
from typing import Dict, Any, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class StreamingTTSIntegration:
    """
    Integration helper to add streaming TTS to existing phone call system.
    
    This class shows how to modify your existing WebSocket handlers to use
    streaming TTS instead of the current wait-for-complete approach.
    """
    
    def __init__(self, existing_tts_service, streaming_tts_service):
        """
        Initialize with your existing services.
        
        Args:
            existing_tts_service: Your current TTS service
            streaming_tts_service: New streaming TTS service
        """
        self.existing_tts = existing_tts_service
        self.streaming_tts = streaming_tts_service
        self.use_streaming = True  # Feature flag
    
    async def enhanced_process_llm_response(
        self,
        websocket,
        session_id: str,
        user_message: str,
        llm_service,
        language: str = "en",
        voice: str = "default",
        use_streaming_tts: bool = True
    ):
        """
        Enhanced version of your existing process_llm_response function.
        
        This replaces the current approach where you wait for the complete LLM
        response before starting TTS. Instead, it streams audio as text arrives.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            user_message: User input text
            llm_service: Your LLM service
            language: Target language
            voice: Voice to use
            use_streaming_tts: Whether to use streaming TTS
        """
        try:
            if use_streaming_tts and self.use_streaming:
                # NEW: Streaming approach - audio starts immediately
                await self._stream_llm_with_tts(
                    websocket, session_id, user_message, llm_service, language, voice
                )
            else:
                # EXISTING: Traditional approach - wait for complete response
                await self._traditional_llm_with_tts(
                    websocket, session_id, user_message, llm_service, language, voice
                )
                
        except Exception as e:
            logger.error(f"❌ Enhanced LLM processing error: {e}")
            await self._send_error_response(websocket, session_id, str(e))
    
    async def _stream_llm_with_tts(
        self,
        websocket,
        session_id: str,
        user_message: str,
        llm_service,
        language: str,
        voice: str
    ):
        """
        NEW: Streaming approach - generates audio while LLM is still responding.
        
        This is the core improvement that eliminates the perceived latency.
        """
        logger.info(f"🚀 Starting streaming LLM+TTS for session {session_id}")
        
        # Send status update
        await self._send_websocket_message(websocket, {
            "type": "llm_streaming_started",
            "session_id": session_id,
            "message": "AI is thinking and will speak as thoughts form...",
            "timestamp": time.time()
        })
        
        # Get streaming LLM response
        llm_stream = await llm_service.get_streaming_response(user_message)
        
        # Track streaming metrics
        stream_start = time.time()
        total_chunks = 0
        total_text = ""
        
        # Process LLM stream with streaming TTS
        async for audio_chunk in self.streaming_tts.stream_tts_from_llm(
            llm_stream, session_id, language, voice
        ):
            total_chunks += 1
            total_text += audio_chunk.text + " "
            
            # Convert audio to base64 for WebSocket transmission
            audio_base64 = base64.b64encode(audio_chunk.audio_data).decode('utf-8')
            
            # Send audio chunk - this is the key improvement!
            await self._send_websocket_message(websocket, {
                "type": "streaming_audio_chunk",
                "session_id": session_id,
                "chunk_index": audio_chunk.index,
                "audio_data": audio_base64,
                "text_segment": audio_chunk.text,
                "content_type": audio_chunk.content_type,
                "is_final": audio_chunk.total_chunks is not None,
                "timestamp": time.time()
            })
            
            logger.debug(f"📦 Streamed chunk {audio_chunk.index}: '{audio_chunk.text[:50]}...'")
        
        # Send completion status
        total_duration = time.time() - stream_start
        await self._send_websocket_message(websocket, {
            "type": "streaming_response_complete",
            "session_id": session_id,
            "total_chunks": total_chunks,
            "total_duration_ms": round(total_duration * 1000, 2),
            "complete_text": total_text.strip(),
            "timestamp": time.time()
        })
        
        logger.info(f"✅ Streaming completed: {total_chunks} chunks in {total_duration:.2f}s")
    
    async def _traditional_llm_with_tts(
        self,
        websocket,
        session_id: str,
        user_message: str,
        llm_service,
        language: str,
        voice: str
    ):
        """
        EXISTING: Traditional approach - wait for complete response then generate audio.
        
        This is your current approach that causes the perceived latency.
        """
        logger.info(f"🐌 Using traditional LLM+TTS for session {session_id}")
        
        # Send thinking status
        await self._send_websocket_message(websocket, {
            "type": "llm_thinking",
            "session_id": session_id,
            "message": "AI is thinking...",
            "timestamp": time.time()
        })
        
        # Wait for complete LLM response (this is the bottleneck!)
        start_time = time.time()
        complete_response = await llm_service.get_complete_response(user_message)
        llm_duration = time.time() - start_time
        
        # Send text response
        await self._send_websocket_message(websocket, {
            "type": "llm_response_complete",
            "session_id": session_id,
            "text": complete_response,
            "duration_ms": round(llm_duration * 1000, 2),
            "timestamp": time.time()
        })
        
        # NOW generate audio (user has been waiting this whole time!)
        tts_start = time.time()
        audio_data = await self.existing_tts.generate_audio(complete_response, language, voice)
        tts_duration = time.time() - tts_start
        
        # Send audio
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        await self._send_websocket_message(websocket, {
            "type": "audio_response",
            "session_id": session_id,
            "audio_data": audio_base64,
            "text": complete_response,
            "tts_duration_ms": round(tts_duration * 1000, 2),
            "total_duration_ms": round((llm_duration + tts_duration) * 1000, 2),
            "timestamp": time.time()
        })
        
        logger.info(f"🐌 Traditional completed: {llm_duration:.2f}s LLM + {tts_duration:.2f}s TTS")
    
    async def _send_websocket_message(self, websocket, message: Dict[str, Any]):
        """Send WebSocket message with error handling"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ WebSocket send error: {e}")
    
    async def _send_error_response(self, websocket, session_id: str, error: str):
        """Send error response via WebSocket"""
        await self._send_websocket_message(websocket, {
            "type": "error",
            "session_id": session_id,
            "error": error,
            "timestamp": time.time()
        })

# Example: How to modify your existing WebSocket endpoint
class ExamplePhoneCallWebSocketEndpoint:
    """
    Example showing how to modify your existing phone call WebSocket endpoint.
    
    This demonstrates the integration pattern for your existing system.
    """
    
    def __init__(self, tts_service, streaming_tts_service, llm_service):
        self.integration = StreamingTTSIntegration(tts_service, streaming_tts_service)
        self.llm_service = llm_service
    
    async def handle_websocket_connection(self, websocket):
        """
        Your existing WebSocket connection handler.
        
        This shows where to integrate the streaming TTS functionality.
        """
        try:
            async for message in websocket.iter_text():
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "user_speech":
                    # User spoke - process with streaming TTS
                    await self._handle_user_speech(websocket, data)
                    
                elif message_type == "configuration":
                    # Handle configuration changes
                    await self._handle_configuration(websocket, data)
                    
                # ... other message types
                
        except Exception as e:
            logger.error(f"❌ WebSocket handler error: {e}")
    
    async def _handle_user_speech(self, websocket, data: Dict[str, Any]):
        """
        Handle user speech input - THIS IS WHERE YOU INTEGRATE STREAMING TTS.
        
        Replace your existing LLM+TTS processing with the enhanced version.
        """
        session_id = data.get("session_id", "unknown")
        user_text = data.get("text", "")
        language = data.get("language", "en")
        voice = data.get("voice", "default")
        
        logger.info(f"🎤 User speech received: '{user_text[:50]}...' (session: {session_id})")
        
        # OLD CODE:
        # llm_response = await self.llm_service.get_complete_response(user_text)
        # audio_data = await self.tts_service.generate_audio(llm_response)
        # await websocket.send_text(json.dumps({"type": "audio_response", "data": audio_data}))
        
        # NEW CODE - Use streaming TTS integration:
        await self.integration.enhanced_process_llm_response(
            websocket=websocket,
            session_id=session_id,
            user_message=user_text,
            llm_service=self.llm_service,
            language=language,
            voice=voice,
            use_streaming_tts=True  # Enable streaming
        )
    
    async def _handle_configuration(self, websocket, data: Dict[str, Any]):
        """Handle configuration changes"""
        session_id = data.get("session_id", "unknown")
        config = data.get("config", {})
        
        # Update streaming TTS settings
        if "use_streaming_tts" in config:
            self.integration.use_streaming = config["use_streaming_tts"]
            
        await self.integration._send_websocket_message(websocket, {
            "type": "configuration_updated",
            "session_id": session_id,
            "message": "Settings updated successfully",
            "timestamp": time.time()
        })

# Client-side JavaScript integration example
CLIENT_SIDE_JAVASCRIPT = '''
// Client-side JavaScript to handle streaming audio chunks
class StreamingTTSClient {
    constructor(websocketUrl) {
        this.ws = new WebSocket(websocketUrl);
        this.audioQueue = [];
        this.isPlaying = false;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        this.setupWebSocketHandlers();
    }
    
    setupWebSocketHandlers() {
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'streaming_audio_chunk':
                    this.handleAudioChunk(data);
                    break;
                    
                case 'streaming_response_complete':
                    this.handleStreamingComplete(data);
                    break;
                    
                case 'llm_streaming_started':
                    this.showThinkingIndicator();
                    break;
                    
                default:
                    console.log('Unknown message type:', data.type);
            }
        };
    }
    
    async handleAudioChunk(data) {
        // Convert base64 audio to playable format
        const audioData = atob(data.audio_data);
        const audioBuffer = this.audioContext.createBuffer(1, audioData.length, 22050);
        
        // Add to queue for seamless playback
        this.audioQueue.push({
            buffer: audioBuffer,
            text: data.text_segment,
            index: data.chunk_index
        });
        
        // Start playing if not already playing
        if (!this.isPlaying) {
            this.startAudioPlayback();
        }
        
        // Update UI with text as it arrives
        this.updateTextDisplay(data.text_segment);
    }
    
    async startAudioPlayback() {
        this.isPlaying = true;
        
        while (this.audioQueue.length > 0) {
            const chunk = this.audioQueue.shift();
            await this.playAudioChunk(chunk);
        }
        
        this.isPlaying = false;
    }
    
    async playAudioChunk(chunk) {
        return new Promise((resolve) => {
            const source = this.audioContext.createBufferSource();
            source.buffer = chunk.buffer;
            source.connect(this.audioContext.destination);
            source.onended = resolve;
            source.start();
            
            console.log(`🔊 Playing chunk ${chunk.index}: "${chunk.text}"`);
        });
    }
    
    updateTextDisplay(text) {
        const textDisplay = document.getElementById('ai-response-text');
        if (textDisplay) {
            textDisplay.textContent += text + ' ';
        }
    }
    
    showThinkingIndicator() {
        console.log('🤔 AI is thinking and will speak as thoughts form...');
        // Show thinking animation
    }
    
    handleStreamingComplete(data) {
        console.log(`✅ Streaming complete: ${data.total_chunks} chunks in ${data.total_duration_ms}ms`);
        // Hide thinking animation, show completion
    }
}

// Usage:
const client = new StreamingTTSClient('ws://localhost:8000/phone-call');
'''

# Integration instructions
INTEGRATION_INSTRUCTIONS = """
INTEGRATION INSTRUCTIONS FOR YOUR EXISTING PHONE CALL SYSTEM:

1. IMPORT THE STREAMING TTS SERVICES:
   - Copy streaming_tts_service.py to your src/services/ directory
   - Copy streaming_tts_websocket.py to your src/services/ directory

2. MODIFY YOUR EXISTING WEBSOCKET HANDLER:
   - Replace your current LLM+TTS processing with StreamingTTSIntegration
   - Use enhanced_process_llm_response() instead of your current approach
   - This enables streaming audio while LLM is still generating text

3. UPDATE YOUR LLM SERVICE:
   - Ensure your LLM service can provide streaming responses
   - Implement get_streaming_response() method that yields text chunks
   - If using Ollama, enable streaming mode in the API call

4. CLIENT-SIDE CHANGES:
   - Update your JavaScript to handle 'streaming_audio_chunk' messages
   - Implement audio queue and seamless playback system
   - Start playing audio as soon as first chunk arrives

5. BENEFITS YOU'LL SEE:
   - Dramatically reduced perceived latency
   - Audio starts playing while LLM is still thinking
   - More natural, fluid conversation experience
   - User doesn't wait for complete response before hearing AI

6. FALLBACK COMPATIBILITY:
   - Keep your existing TTS system as fallback
   - Use feature flag to enable/disable streaming
   - Graceful degradation if streaming fails

The key insight: Instead of [LLM Complete] → [TTS Complete] → [Play Audio],
you get [LLM Chunk] → [TTS Chunk] → [Play Audio] → [LLM Chunk] → [TTS Chunk] → [Play Audio]...

This creates the illusion of real-time conversation!
"""

if __name__ == "__main__":
    print("="*80)
    print("STREAMING TTS INTEGRATION GUIDE")
    print("="*80)
    print(INTEGRATION_INSTRUCTIONS)
    print("\nClient-side JavaScript example saved to variable CLIENT_SIDE_JAVASCRIPT")
    print("="*80)
