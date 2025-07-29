"""
TTS API routes for the LLM Translation Service.
Provides text-to-speech functionality with translation integration.
"""

from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
import time

from ...services.tts_service import tts_service, cached_tts_service
from ...services.translation_service import translation_service
from ...models.schemas import TTSRequest, TTSResponse


# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass

logger = MockLogger()

router = APIRouter()


@router.post("/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    text: str = Form(..., description="Text to convert to speech"),
    language: str = Form(default="en", description="Language code (en, zh, etc.)"),
    voice_speed: float = Form(default=1.0, description="Voice speed (0.5-2.0)"),
    output_format: str = Form(default="wav", description="Audio format (wav, mp3)"),
    use_cache: bool = Form(default=True, description="Use cached results if available")
) -> TTSResponse:
    """
    Convert text to speech using local TTS models.
    
    Supports multiple languages and voice customization.
    Returns base64-encoded audio data.
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(
            "TTS request received",
            request_id=request_id,
            text_length=len(text),
            language=language,
            voice_speed=voice_speed
        )
        
        # Validate input parameters
        if len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        if not (0.5 <= voice_speed <= 2.0):
            raise HTTPException(status_code=400, detail="Voice speed must be between 0.5 and 2.0")
        
        # Choose service based on cache preference (temporarily force no cache for debugging)
        service = tts_service  # Force use of main service for now
        
        # Synthesize speech using API method
        result = await service.synthesize_speech_api(
            text=text,
            language=language,
            voice="default",  # Use default voice
            speed=voice_speed
        )
        
        if not result['success']:
            error_msg = result.get('error', 'Unknown TTS error')
            if not error_msg or error_msg.strip() == '':
                error_msg = 'TTS synthesis failed with empty error message'
            
            logger.error(
                "TTS synthesis failed",
                request_id=request_id,
                error=error_msg,
                result=result  # Log the full result for debugging
            )
            raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {error_msg}")
        
        logger.info(
            "TTS synthesis completed",
            request_id=request_id,
            processing_time=result['processing_time'],
            audio_size=result.get('audio_size_bytes', 0),
            cache_hit=result.get('cache_hit', False)
        )
        
        # Prepare response matching TTSResponse schema
        response_data = {
            "success": result['success'],
            "audio_base64": result.get('audio_data'),  # Rename to match schema
            "format": result.get('content_type', 'audio/wav'),  # Rename to match schema
            "processing_time": result['processing_time'],
            "text_length": len(text),  # Add required field
            "language": result['language'],
            "voice_speed": result['speed'],  # Rename to match schema
            "model_used": "coqui-tts",
            "audio_size_bytes": result.get('audio_size_bytes'),
            "cache_hit": result.get('cache_hit', False),
            "error": result.get('error')
        }
        
        return TTSResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "TTS request exception",
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tts/translate-and-speak")
async def translate_and_speak(
    text: str = Form(..., description="Text to translate and speak"),
    from_lang: str = Form(..., description="Source language code"),
    to_lang: str = Form(..., description="Target language code"),
    voice_speed: float = Form(default=1.0, description="Voice speed (0.5-2.0)"),
    translation_mode: str = Form(default="succinct", description="Translation mode (succinct/verbose)"),
    use_cache: bool = Form(default=True, description="Use cached results if available")
) -> Dict[str, Any]:
    """
    Translate text and convert the translation to speech in one request.
    
    This is the most useful endpoint for combining translation and TTS.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Translate-and-speak request received",
            request_id=request_id,
            text_length=len(text),
            from_lang=from_lang,
            to_lang=to_lang
        )
        
        # Step 1: Translate the text
        translation_start = time.time()
        translation_result = await translation_service.translate_text(
            text=text,
            source_lang=from_lang,
            target_lang=to_lang,
            translation_mode=translation_mode
        )
        translation_time = time.time() - translation_start
        
        if not translation_result.get('success', False):
            raise HTTPException(
                status_code=500, 
                detail=f"Translation failed: {translation_result.get('error', 'Unknown error')}"
            )
        
        translated_text = translation_result.get('translation', '')
        if not translated_text:
            raise HTTPException(status_code=500, detail="Translation returned empty result")
        
        # Step 2: Convert translation to speech
        tts_start = time.time()
        service = cached_tts_service if use_cache else tts_service
        
        tts_result = await service.synthesize_speech(
            text=translated_text,
            language=to_lang,
            voice_speed=voice_speed,
            output_format='wav'
        )
        tts_time = time.time() - tts_start
        
        if not tts_result['success']:
            raise HTTPException(
                status_code=500, 
                detail=f"TTS failed: {tts_result.get('error', 'Unknown error')}"
            )
        
        total_time = time.time() - start_time
        
        logger.info(
            "Translate-and-speak completed",
            request_id=request_id,
            translation_time=translation_time,
            tts_time=tts_time,
            total_time=total_time
        )
        
        return {
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'audio_base64': tts_result['audio_base64'],
            'audio_format': tts_result['format'],
            'source_language': from_lang,
            'target_language': to_lang,
            'voice_speed': voice_speed,
            'translation_mode': translation_mode,
            'performance': {
                'translation_time': translation_time,
                'tts_time': tts_time,
                'total_time': total_time,
                'translation_cache_hit': translation_result.get('cache_hit', False),
                'tts_cache_hit': tts_result.get('cache_hit', False)
            },
            'detailed_timing': {
                'translation_ms': round(translation_time * 1000, 2),
                'tts_ms': round(tts_time * 1000, 2),
                'total_ms': round(total_time * 1000, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Translate-and-speak exception",
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tts/languages")
async def get_available_languages():
    """Get list of available TTS languages and models."""
    try:
        languages = await tts_service.get_available_languages()
        return {
            'success': True,
            'languages': languages,
            'total_count': len(languages)
        }
    except Exception as e:
        logger.error("Failed to get TTS languages", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tts/health")
async def tts_health_check():
    """Check TTS service health and status."""
    try:
        health_status = await tts_service.get_health_status()
        
        # Add cache statistics
        if hasattr(cached_tts_service, 'get_cache_stats'):
            cache_stats = await cached_tts_service.get_cache_stats()
            health_status['cache_stats'] = cache_stats
        
        return {
            'success': True,
            'status': 'healthy' if health_status.get('tts_available', False) else 'unavailable',
            'details': health_status
        }
        
    except Exception as e:
        logger.error("TTS health check failed", error=str(e))
        return {
            'success': False,
            'status': 'error',
            'error': str(e)
        }


@router.post("/tts/cache/clear")
async def clear_tts_cache():
    """Clear TTS cache (admin endpoint)."""
    try:
        if hasattr(cached_tts_service, 'clear_cache'):
            await cached_tts_service.clear_cache()
        
        return {
            'success': True,
            'message': 'TTS cache cleared successfully'
        }
    except Exception as e:
        logger.error("Failed to clear TTS cache", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tts/demo")
async def tts_demo():
    """Demo endpoint to test TTS functionality."""
    demo_texts = {
        'en': "Hello! This is a demonstration of text-to-speech synthesis.",
        'zh': "你好！这是文本转语音合成的演示。"
    }
    
    results = {}
    
    for lang, text in demo_texts.items():
        try:
            result = await tts_service.synthesize_speech(
                text=text,
                language=lang,
                voice_speed=1.0
            )
            
            if result['success']:
                # Don't return full audio data in demo, just metadata
                results[lang] = {
                    'success': True,
                    'text': text,
                    'processing_time': result['processing_time'],
                    'audio_size_bytes': result.get('audio_size_bytes', 0),
                    'model_used': result.get('model_used', lang)
                }
            else:
                results[lang] = {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            results[lang] = {
                'success': False,
                'error': str(e)
            }
    
    return {
        'demo_results': results,
        'instructions': {
            'synthesize': 'POST /api/tts/synthesize with text, language, voice_speed',
            'translate_and_speak': 'POST /api/tts/translate-and-speak with text, from_lang, to_lang',
            'languages': 'GET /api/tts/languages for available languages',
            'health': 'GET /api/tts/health for service status'
        }
    }
