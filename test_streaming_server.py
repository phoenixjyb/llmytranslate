#!/usr/bin/env python3
"""
Simple test server for streaming TTS functionality
Only loads essential services to test streaming TTS integration
"""

import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(title="Streaming TTS Test Server")

# Simple streaming TTS WebSocket endpoint
@app.websocket("/ws/streaming-tts")
async def streaming_tts_websocket(websocket: WebSocket):
    """Simple streaming TTS WebSocket for testing"""
    await websocket.accept()
    logger.info("Streaming TTS WebSocket connected")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"Received message: {message.get('type', 'unknown')}")
            
            if message.get("type") == "start_streaming":
                text = message.get("text", "Hello! This is a test of streaming TTS.")
                session_id = message.get("session_id", "test_session")
                
                # Send streaming start notification
                await websocket.send_text(json.dumps({
                    "type": "tts_streaming_started",
                    "session_id": session_id,
                    "message": "AI is thinking and will speak as thoughts form..."
                }))
                
                # Simulate streaming text chunks
                chunks = text.split('. ')
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        # Simulate processing delay
                        await asyncio.sleep(0.5)
                        
                        # Send streaming audio chunk
                        await websocket.send_text(json.dumps({
                            "type": "streaming_audio_chunk",
                            "session_id": session_id,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "text": chunk.strip() + ".",
                            "audio_data": "",  # Empty for web - browser will use speechSynthesis
                            "content_type": "text/plain",
                            "is_final": i == len(chunks) - 1
                        }))
                
                # Send completion notification
                await websocket.send_text(json.dumps({
                    "type": "tts_streaming_completed",
                    "session_id": session_id,
                    "message": "Streaming TTS completed successfully",
                    "summary": {
                        "total_chunks": len(chunks),
                        "text_length": len(text)
                    }
                }))
                
            else:
                # Echo unknown message types
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message.get('type', 'unknown')}"
                }))
                
    except WebSocketDisconnect:
        logger.info("Streaming TTS WebSocket disconnected")
    except Exception as e:
        logger.error(f"Streaming TTS WebSocket error: {e}")

# Serve static web files (after WebSocket endpoints)
try:
    app.mount("/web", StaticFiles(directory="web"), name="web")
    app.mount("/", StaticFiles(directory="web", html=True), name="root")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "streaming-tts-test"}

# Root redirect
@app.get("/")
async def root():
    return {"message": "Streaming TTS Test Server", "endpoints": ["/ws/streaming-tts", "/web/streaming-tts-test.html"]}

def main():
    """Run the test server"""
    print("🧪 Starting Streaming TTS Test Server...")
    print("=" * 60)
    print("📡 WebSocket endpoint: ws://localhost:8000/ws/streaming-tts")
    print("🌐 Web test page: http://localhost:8000/web/streaming-tts-test.html")
    print("🔍 Health check: http://localhost:8000/api/health")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
