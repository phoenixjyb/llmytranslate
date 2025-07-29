# Speech-to-Text Service
# Handles voice input conversion to text for voice chat functionality

import asyncio
import logging
import tempfile
import subprocess
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
import base64

logger = logging.getLogger(__name__)

class STTError(Exception):
    """Custom STT exception."""
    pass

class SpeechToTextService:
    """
    Speech-to-Text service that can handle audio file conversion to text.
    Supports both browser-based Web Speech API and local Whisper processing.
    """
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.whisper_available = False
        
        # Check if we can use OpenAI Whisper (optional local processing)
        self._check_whisper_availability()
        
        if self.whisper_available:
            logger.info("✅ Whisper STT available for local processing")
        else:
            logger.info("ℹ️ Using browser-based speech recognition (Web Speech API)")
    
    def _check_whisper_availability(self) -> bool:
        """Check if Whisper is available for local STT processing."""
        try:
            # Try to import whisper (if installed)
            import whisper
            self.whisper_available = True
            logger.info("Whisper library found - local STT processing available")
            return True
        except ImportError:
            logger.info("Whisper library not found - will use browser-based STT")
            return False
    
    def is_available(self) -> bool:
        """Check if STT service is available (always true, fallback to browser)."""
        return True
    
    async def transcribe_audio_file(
        self,
        audio_data: bytes,
        format: str = "webm",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_data: Raw audio file bytes
            format: Audio format (webm, wav, mp3, etc.)
            language: Language code for transcription
            
        Returns:
            Dictionary with transcription results
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            if self.whisper_available:
                # Use local Whisper processing
                result = await self._transcribe_with_whisper(audio_data, format, language)
            else:
                # Return placeholder for browser-based processing
                result = {
                    "success": True,
                    "text": "",
                    "confidence": 1.0,
                    "method": "browser_web_speech_api",
                    "message": "Audio received, use browser Web Speech API for transcription"
                }
            
            result["processing_time"] = asyncio.get_event_loop().time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"STT transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": asyncio.get_event_loop().time() - start_time
            }
    
    async def _transcribe_with_whisper(
        self,
        audio_data: bytes,
        format: str,
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model."""
        import whisper
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name
        
        try:
            # Load Whisper model (base model for speed vs accuracy balance)
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(
                temp_audio_path,
                language=language if language != "auto" else None
            )
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "confidence": 1.0,  # Whisper doesn't provide confidence scores
                "method": "whisper_local",
                "language_detected": result.get("language", language)
            }
            
        finally:
            # Cleanup
            try:
                os.unlink(temp_audio_path)
            except:
                pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform STT service health check."""
        return {
            "status": "healthy",
            "whisper_available": self.whisper_available,
            "methods_available": [
                "browser_web_speech_api",
                "whisper_local" if self.whisper_available else None
            ],
            "message": "STT service ready"
        }

# Global STT service instance
stt_service = SpeechToTextService()
