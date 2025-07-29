# TTS Service with Dual Environment Support
# Manages communication between main service (Python 3.13) and TTS service (Python 3.12)

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class TTSError(Exception):
    """Custom TTS exception."""
    pass

class DualEnvironmentTTSService:
    """
    TTS Service that handles dual Python environment communication.
    Main service runs on Python 3.13, TTS subprocess runs on Python 3.12.
    """
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.tts_env_path = self.workspace_root / ".venv-tts"
        self.tts_python = self.tts_env_path / "Scripts" / "python.exe"
        self.tts_script = self.workspace_root / "tts_subprocess.py"
        
        # Check if TTS environment exists
        self.tts_available = self._check_tts_environment()
        
        if self.tts_available:
            logger.info("✅ TTS environment found - high quality TTS enabled")
        else:
            logger.warning("⚠️ TTS environment not found - TTS features disabled")
    
    def _check_tts_environment(self) -> bool:
        """Check if TTS environment and dependencies are available."""
        try:
            if not self.tts_env_path.exists():
                logger.warning(f"TTS environment not found at {self.tts_env_path}")
                return False
            
            if not self.tts_python.exists():
                logger.warning(f"TTS Python executable not found at {self.tts_python}")
                return False
            
            # Test if TTS is importable
            result = subprocess.run(
                [str(self.tts_python), "-c", "from TTS.api import TTS; print('OK')"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and "OK" in result.stdout:
                return True
            else:
                logger.warning(f"TTS import test failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"TTS environment check failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if TTS service is available."""
        return self.tts_available
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "en",
        voice: str = "default",
        speed: float = 1.0
    ) -> Tuple[bytes, str]:
        """
        Synthesize speech using the TTS subprocess.
        
        Returns:
            Tuple of (audio_data, content_type)
        """
        if not self.tts_available:
            raise TTSError("TTS service not available. Please run setup-tts-env.ps1 to install TTS environment.")
        
        try:
            # Create temporary files for communication
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as request_file:
                request_data = {
                    "action": "synthesize",
                    "text": text,
                    "language": language,
                    "voice": voice,
                    "speed": speed
                }
                json.dump(request_data, request_file, ensure_ascii=False)
                request_file_path = request_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                audio_file_path = audio_file.name
            
            try:
                # Run TTS subprocess
                result = await asyncio.create_subprocess_exec(
                    str(self.tts_python),
                    str(self.tts_script),
                    request_file_path,
                    audio_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown TTS error"
                    logger.error(f"TTS subprocess failed: {error_msg}")
                    raise TTSError(f"TTS synthesis failed: {error_msg}")
                
                # Read generated audio file
                with open(audio_file_path, 'rb') as f:
                    audio_data = f.read()
                
                return audio_data, "audio/wav"
                
            finally:
                # Cleanup temporary files
                try:
                    os.unlink(request_file_path)
                    os.unlink(audio_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise TTSError(f"TTS synthesis failed: {str(e)}")
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages and voices."""
        if not self.tts_available:
            return {
                "available": False,
                "languages": {},
                "message": "TTS service not available"
            }
        
        try:
            # Create temporary file for request
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as request_file:
                request_data = {"action": "list_models"}
                json.dump(request_data, request_file, ensure_ascii=False)
                request_file_path = request_file.name
            
            try:
                # Run TTS subprocess
                result = await asyncio.create_subprocess_exec(
                    str(self.tts_python),
                    str(self.tts_script),
                    request_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"TTS models list failed: {error_msg}")
                    return {
                        "available": False,
                        "languages": {},
                        "error": error_msg
                    }
                
                # Parse response
                response_data = json.loads(stdout.decode())
                return response_data
                
            finally:
                try:
                    os.unlink(request_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error getting TTS models: {e}")
            return {
                "available": False,
                "languages": {},
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform TTS service health check."""
        if not self.tts_available:
            return {
                "status": "unavailable",
                "tts_environment": False,
                "message": "TTS environment not found or not properly configured"
            }
        
        try:
            # Test basic TTS functionality
            test_result = await self.synthesize_speech("Test", "en")
            
            return {
                "status": "healthy",
                "tts_environment": True,
                "python_version": "3.12 (subprocess)",
                "test_synthesis": "passed",
                "audio_size": len(test_result[0]) if test_result else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "tts_environment": True,
                "error": str(e),
                "message": "TTS environment found but synthesis failed"
            }

# Cached TTS service for backward compatibility
class CachedTTSService:
    """TTS service with caching support."""
    
    def __init__(self, cache_dir: str = "audio_cache"):
        self._service = tts_service
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, text: str, language: str, voice: str, speed: float) -> str:
        """Generate cache key for audio file."""
        key_string = f"{text}_{language}_{voice}_{speed}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_available(self) -> bool:
        return self._service.is_available()
    
    async def synthesize_speech(self, text: str, language: str = "en", voice: str = "default", speed: float = 1.0):
        # Check cache first
        cache_key = self._get_cache_key(text, language, voice, speed)
        cache_file = self.cache_dir / f"{cache_key}.wav"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            logger.info(f"TTS cache hit for: {text[:50]}...")
            return audio_data, "audio/wav"
        
        # Generate new audio
        audio_data, content_type = await self._service.synthesize_speech(text, language, voice, speed)
        
        # Cache the result
        try:
            with open(cache_file, 'wb') as f:
                f.write(audio_data)
            logger.info(f"TTS audio cached: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache TTS audio: {e}")
        
        return audio_data, content_type
    
    async def get_supported_languages(self):
        return await self._service.get_supported_languages()
    
    async def health_check(self):
        return await self._service.health_check()

# Global TTS service instance
tts_service = DualEnvironmentTTSService()

# Create cached TTS service instance
cached_tts_service = CachedTTSService()

# Fallback class for compatibility
class TTSService:
    """Legacy compatibility class that delegates to DualEnvironmentTTSService."""
    
    def __init__(self):
        self._service = tts_service
    
    def is_available(self) -> bool:
        return self._service.is_available()
    
    async def synthesize_speech(self, text: str, language: str = "en", voice: str = "default", speed: float = 1.0):
        return await self._service.synthesize_speech(text, language, voice, speed)
    
    async def get_supported_languages(self):
        return await self._service.get_supported_languages()
    
    async def health_check(self):
        return await self._service.health_check()

# Cached TTS service for backward compatibility
class CachedTTSService(TTSService):
    """TTS service with caching support."""
    
    def __init__(self, cache_dir: str = "audio_cache"):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, text: str, language: str, voice: str, speed: float) -> str:
        """Generate cache key for audio file."""
        key_string = f"{text}_{language}_{voice}_{speed}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def synthesize_speech(self, text: str, language: str = "en", voice: str = "default", speed: float = 1.0):
        # Check cache first
        cache_key = self._get_cache_key(text, language, voice, speed)
        cache_file = self.cache_dir / f"{cache_key}.wav"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            logger.info(f"TTS cache hit for: {text[:50]}...")
            return audio_data, "audio/wav"
        
        # Generate new audio
        audio_data, content_type = await super().synthesize_speech(text, language, voice, speed)
        
        # Cache the result
        try:
            with open(cache_file, 'wb') as f:
                f.write(audio_data)
            logger.info(f"TTS audio cached: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache TTS audio: {e}")
        
        return audio_data, content_type
