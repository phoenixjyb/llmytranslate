# TTS Service with Dual Environment Support
# Manages communication between main service (Python 3.13) and TTS service (Python 3.12)

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import hashlib
import time
import base64
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
            
            # Basic check: verify TTS subprocess script exists
            if not self.tts_script.exists():
                logger.warning(f"TTS subprocess script not found at {self.tts_script}")
                return False
            
            # Quick test: try to run Python in the TTS environment
            try:
                result = subprocess.run(
                    [str(self.tts_python), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    logger.warning(f"TTS Python environment test failed: {result.stderr}")
                    return False
                    
                logger.info(f"TTS Python environment available: {result.stdout.strip()}")
                
                # Skip the heavy TTS import test for faster startup
                # The actual TTS functionality will be tested when needed
                logger.info("TTS environment basic checks passed - assuming TTS is available")
                return True
                
            except Exception as e:
                logger.warning(f"TTS Python version check failed: {e}")
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
            logger.error(f"TTS synthesis error type: {type(e)}")
            logger.error(f"TTS synthesis error args: {e.args}")
            raise TTSError(f"TTS synthesis failed: {str(e)}")
    
    async def synthesize_speech_api(
        self,
        text: str,
        language: str = "en",
        voice: str = "default",
        speed: float = 1.0,
        tts_mode: str = "fast"
    ) -> Dict[str, Any]:
        """
        Synthesize speech and return API-formatted response.
        Supports both fast and high-quality TTS modes.
        """
        start_time = time.time()
        
        try:
            if tts_mode == "fast":
                # Use fast FFmpeg-based TTS for quick responses
                logger.info("🚀 Using Fast TTS (Windows SAPI)")
                audio_data, content_type = await self._fast_ffmpeg_tts(text, speed)
            else:
                # Use high-quality Coqui TTS for premium voices
                logger.info("🎭 Using High-Quality TTS (Coqui Neural)")
                audio_data, content_type = await self.synthesize_speech(text, language, voice, speed)
            
            # Encode audio as base64 for API response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "success": True,
                "audio_data": audio_base64,
                "content_type": content_type,
                "audio_size_bytes": len(audio_data),
                "processing_time": time.time() - start_time,
                "language": language,
                "voice": voice,
                "speed": speed,
                "tts_mode": tts_mode
            }
            
        except Exception as e:
            logger.error(f"TTS API synthesis error: {e}")
            logger.error(f"TTS API synthesis error type: {type(e)}")
            return {
                "success": False,
                "error": f"TTS synthesis error: {str(e)} (type: {type(e).__name__})",
                "content_type": None,
                "audio_data": None,
                "processing_time": time.time() - start_time
            }
    
    async def _fast_ffmpeg_tts(self, text: str, speed: float = 1.0) -> Tuple[bytes, str]:
        """
        Fast TTS using Windows built-in SAPI voices via PowerShell.
        Much faster than Coqui TTS (seconds vs minutes).
        """
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                audio_file_path = audio_file.name
            
            # Use Windows SAPI via PowerShell for fast TTS
            # Escape quotes and handle special characters in text
            escaped_text = text.replace("'", "''").replace('"', '""')
            
            powershell_cmd = f"""
            Add-Type -AssemblyName System.Speech;
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $synth.Rate = {max(-10, min(10, int((speed - 1) * 10)))};
            $synth.SetOutputToWaveFile('{audio_file_path}');
            $synth.Speak('{escaped_text}');
            $synth.Dispose();
            """
            
            # Execute PowerShell command
            process = await asyncio.create_subprocess_exec(
                'powershell', '-Command', powershell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise TTSError(f"PowerShell TTS failed: {stderr.decode()}")
            
            # Read generated audio
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Cleanup
            os.unlink(audio_file_path)
            
            logger.info(f"Fast TTS generated {len(audio_data)} bytes of audio")
            return audio_data, "audio/wav"
            
        except Exception as e:
            logger.error(f"Fast TTS error: {e}")
            # Fallback to simple silent audio
            return await self._generate_simple_silence(), "audio/wav"
    
    async def _generate_simple_silence(self) -> bytes:
        """Generate simple silence as fallback when TTS fails."""
        # Create a minimal WAV file with 1 second of silence
        sample_rate = 22050
        duration = 1  # 1 second
        samples = sample_rate * duration
        
        # Standard WAV header (44 bytes)
        wav_header = bytearray()
        wav_header.extend(b'RIFF')
        wav_header.extend((36 + samples * 2).to_bytes(4, 'little'))
        wav_header.extend(b'WAVE')
        wav_header.extend(b'fmt ')
        wav_header.extend((16).to_bytes(4, 'little'))
        wav_header.extend((1).to_bytes(2, 'little'))  # PCM
        wav_header.extend((1).to_bytes(2, 'little'))  # Mono
        wav_header.extend(sample_rate.to_bytes(4, 'little'))
        wav_header.extend((sample_rate * 2).to_bytes(4, 'little'))
        wav_header.extend((2).to_bytes(2, 'little'))
        wav_header.extend((16).to_bytes(2, 'little'))
        wav_header.extend(b'data')
        wav_header.extend((samples * 2).to_bytes(4, 'little'))
        
        # Silent audio data (all zeros)
        audio_data = wav_header + b'\x00' * (samples * 2)
        
        return bytes(audio_data)
    
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
    
    async def get_health_status(self):
        """Get TTS service health status (alias for health_check)."""
        return await self.health_check()

# Cached TTS service for backward compatibility
class CachedTTSService:
    """TTS service with caching support."""
    
    def __init__(self, cache_dir: str = "audio_cache"):
        self._service = None  # Will be set after tts_service is created
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, text: str, language: str, voice: str, speed: float, tts_mode: str = "fast") -> str:
        """Generate cache key for audio file."""
        key_string = f"{text}_{language}_{voice}_{speed}_{tts_mode}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_available(self) -> bool:
        return self._service.is_available() if self._service else False
    
    async def synthesize_speech(self, text: str, language: str = "en", voice: str = "default", speed: float = 1.0):
        if not self._service:
            raise TTSError("TTS service not initialized")
            
        # Check cache first
        cache_key = self._get_cache_key(text, language, voice, speed, "legacy")
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
    
    async def synthesize_speech_api(
        self,
        text: str,
        language: str = "en",
        voice: str = "default",
        speed: float = 1.0,
        tts_mode: str = "fast"
    ) -> Dict[str, Any]:
        """
        Synthesize speech with caching and return API-formatted response.
        Supports both fast and high-quality TTS modes.
        """
        start_time = time.time()
        cache_hit = False
        
        try:
            if not self._service:
                return {
                    "success": False,
                    "error": "TTS service not initialized",
                    "content_type": None,
                    "audio_data": None,
                    "processing_time": time.time() - start_time
                }
            
            # Check cache first (include tts_mode in cache key)
            cache_key = self._get_cache_key(text, language, voice, speed, tts_mode)
            cache_file = self.cache_dir / f"{cache_key}.wav"
            
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    audio_data = f.read()
                cache_hit = True
                content_type = "audio/wav"
            else:
                # Generate new audio using the specified TTS mode
                audio_data, content_type = await self._service.synthesize_speech_api(text, language, voice, speed, tts_mode)
                if audio_data.get("success"):
                    # Decode base64 back to bytes for caching
                    audio_bytes = base64.b64decode(audio_data["audio_data"])
                    # Cache the result
                    try:
                        with open(cache_file, 'wb') as f:
                            f.write(audio_bytes)
                        logger.info(f"TTS audio cached: {cache_key} ({tts_mode} mode)")
                    except Exception as e:
                        logger.warning(f"Failed to cache TTS audio: {e}")
                    
                    return audio_data  # Return the API response directly
                else:
                    return audio_data  # Return the error response
            
            # Encode cached audio as base64 for API response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "success": True,
                "audio_data": audio_base64,
                "content_type": content_type,
                "audio_size_bytes": len(audio_data),
                "processing_time": time.time() - start_time,
                "language": language,
                "voice": voice,
                "speed": speed,
                "tts_mode": tts_mode,
                "cache_hit": cache_hit
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_type": None,
                "audio_data": None,
                "processing_time": time.time() - start_time,
                "cache_hit": False
            }
    
    async def get_supported_languages(self):
        if not self._service:
            raise TTSError("TTS service not initialized")
        return await self._service.get_supported_languages()
    
    async def health_check(self):
        if not self._service:
            return {"status": "unavailable", "message": "TTS service not initialized"}
        return await self._service.health_check()
    
    async def get_health_status(self):
        """Get TTS service health status (alias for health_check)."""
        return await self.health_check()

# Legacy compatibility class
class TTSService:
    """Legacy compatibility class that delegates to DualEnvironmentTTSService."""
    
    def __init__(self):
        self._service = None  # Will be set after tts_service is created
    
    def is_available(self) -> bool:
        return self._service.is_available() if self._service else False
    
    async def synthesize_speech(self, text: str, language: str = "en", voice: str = "default", speed: float = 1.0):
        if not self._service:
            raise TTSError("TTS service not initialized")
        return await self._service.synthesize_speech(text, language, voice, speed)
    
    async def get_supported_languages(self):
        if not self._service:
            raise TTSError("TTS service not initialized")
        return await self._service.get_supported_languages()
    
    async def health_check(self):
        if not self._service:
            return {"status": "unavailable", "message": "TTS service not initialized"}
        return await self._service.health_check()
    
    async def get_health_status(self):
        """Get TTS service health status (alias for health_check)."""
        return await self.health_check()
    
    async def synthesize_speech_api(self, text: str, language: str = "en", voice: str = "default", speed: float = 1.0, tts_mode: str = "fast"):
        """API wrapper for synthesize_speech."""
        if not self._service:
            return {
                "success": False,
                "error": "TTS service not initialized",
                "content_type": None,
                "audio_data": None,
                "processing_time": 0
            }
        return await self._service.synthesize_speech_api(text, language, voice, speed, tts_mode)

# Global TTS service instances
tts_service = DualEnvironmentTTSService()
cached_tts_service = CachedTTSService()

# Connect the services
cached_tts_service._service = tts_service