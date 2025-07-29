"""
Voice Chat API routes.
Handles voice-to-voice conversations using STT + LLM + TTS pipeline.
"""

import asyncio
import base64
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import time

from ...services.stt_service import stt_service
from ...services.tts_service import tts_service
from ...services.ollama_client import ollama_client
from ...models.schemas import TTSResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice-chat", tags=["voice-chat"])

@router.post("/conversation")
async def voice_conversation(
    audio_file: UploadFile = File(...),
    language: str = Form("en"),
    voice: str = Form("default"),
    speed: float = Form(1.0),
    model: str = Form("llama3.2")
):
    """
    Complete voice-to-voice conversation:
    1. Convert speech to text (STT)
    2. Process with LLM
    3. Convert response to speech (TTS)
    """
    start_time = time.time()
    
    try:
        # Step 1: Speech to Text
        logger.info("🎤 Processing voice input...")
        audio_data = await audio_file.read()
        
        stt_result = await stt_service.transcribe_audio_file(
            audio_data=audio_data,
            format=audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'webm',
            language=language
        )
        
        if not stt_result["success"]:
            raise HTTPException(status_code=400, detail=f"Speech recognition failed: {stt_result.get('error', 'Unknown error')}")
        
        user_text = stt_result["text"]
        if not user_text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        logger.info(f"🎤 User said: {user_text}")
        
        # Step 2: LLM Processing
        logger.info("🤖 Processing with LLM...")
        llm_response = await ollama_client.chat_completion(
            message=user_text,
            model=model,
            stream=False
        )
        
        if not llm_response.get("success", False):
            raise HTTPException(status_code=500, detail=f"LLM processing failed: {llm_response.get('error', 'Unknown error')}")
        
        ai_text = llm_response["response"]
        logger.info(f"🤖 AI responds: {ai_text}")
        
        # Step 3: Text to Speech
        logger.info("🔊 Converting response to speech...")
        tts_result = await tts_service.synthesize_speech_api(
            text=ai_text,
            language=language,
            voice=voice,
            speed=speed
        )
        
        if not tts_result["success"]:
            raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {tts_result.get('error', 'Unknown error')}")
        
        # Compile complete response
        total_time = time.time() - start_time
        
        return TTSResponse(
            success=True,
            audio_base64=tts_result["audio_data"],
            content_type=tts_result["content_type"],
            audio_size_bytes=tts_result["audio_size_bytes"],
            text_length=len(ai_text),
            processing_time=total_time,
            language=language,
            voice=voice,
            voice_speed=speed,
            text_input=user_text,
            text_response=ai_text,
            stt_time=stt_result.get("processing_time", 0),
            llm_time=llm_response.get("processing_time", 0),
            tts_time=tts_result.get("processing_time", 0),
            conversation_flow={
                "user_speech": user_text,
                "ai_response": ai_text,
                "pipeline": ["STT", "LLM", "TTS"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice conversation error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice conversation failed: {str(e)}")

@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = Form("en")
):
    """
    Transcribe audio to text only (STT endpoint).
    """
    try:
        audio_data = await audio_file.read()
        
        result = await stt_service.transcribe_audio_file(
            audio_data=audio_data,
            format=audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'webm',
            language=language
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.get("/health")
async def voice_chat_health():
    """
    Check voice chat service health.
    """
    try:
        # Check all components
        stt_health = await stt_service.health_check()
        tts_health = await tts_service.health_check()
        
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
            tts_health["status"] != "healthy" or 
            ollama_health["status"] != "healthy"):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "components": {
                "stt": stt_health,
                "tts": tts_health, 
                "llm": ollama_health
            },
            "capabilities": {
                "voice_input": stt_health["status"] == "healthy",
                "text_chat": ollama_health["status"] == "healthy",
                "voice_output": tts_health["status"] == "healthy",
                "full_voice_chat": overall_status == "healthy"
            }
        }
        
    except Exception as e:
        logger.error(f"Voice chat health check error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/capabilities")
async def get_voice_capabilities():
    """
    Get available voice chat capabilities and settings.
    """
    try:
        # Get TTS capabilities
        tts_languages = await tts_service.get_supported_languages()
        
        # Get LLM models
        ollama_models = []
        try:
            health_result = await ollama_client.health_check()
            if health_result.get("status") == "healthy":
                ollama_models = health_result.get("models", [])
        except Exception as e:
            logger.warning(f"Could not get Ollama models: {e}")
        
        return {
            "stt": {
                "available": stt_service.is_available(),
                "methods": ["browser_web_speech_api", "whisper_local"],
                "languages_supported": ["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko", "auto"]
            },
            "tts": tts_languages,
            "llm": {
                "available": len(ollama_models) > 0,
                "models": ollama_models
            },
            "voice_chat": {
                "pipeline": ["Speech-to-Text", "Language Model", "Text-to-Speech"],
                "supported_audio_formats": ["webm", "wav", "mp3", "m4a"]
            }
        }
        
    except Exception as e:
        logger.error(f"Get capabilities error: {e}")
        raise HTTPException(status_code=500, detail=f"Could not get capabilities: {str(e)}")
