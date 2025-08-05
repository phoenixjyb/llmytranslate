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
            # Test if we can actually load a model (requires FFmpeg)
            try:
                model = whisper.load_model("base")
                self.whisper_available = True
                logger.info("Whisper library found and tested - local STT processing available")
                return True
            except Exception as model_error:
                logger.warning(f"Whisper library found but model loading failed: {model_error}")
                logger.info("Will use browser-based STT only")
                self.whisper_available = False
                return False
        except ImportError:
            logger.info("Whisper library not found - will use browser-based STT")
            return False
    
    def retry_whisper_initialization(self) -> bool:
        """Retry Whisper initialization - useful for runtime fixes."""
        logger.info("Retrying Whisper initialization...")
        return self._check_whisper_availability()
    
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
            format: Audio format (webm, wav, mp3, raw, etc.)
            language: Language code for transcription
            
        Returns:
            Dictionary with transcription results
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Try to re-enable Whisper if it was disabled due to previous errors
            if not self.whisper_available:
                logger.info("Whisper disabled, attempting to re-enable...")
                self.retry_whisper_initialization()
            
            if self.whisper_available:
                # Use local Whisper processing
                try:
                    result = await self._transcribe_with_whisper(audio_data, format, language)
                except Exception as whisper_error:
                    logger.error(f"Whisper transcription failed: {whisper_error}")
                    # Don't disable Whisper permanently - just for this request
                    logger.warning("Whisper failed for this request, will retry on next request")
                    result = {
                        "success": False,
                        "error": f"Whisper transcription failed: {str(whisper_error)}",
                        "text": "",
                        "method": "whisper_failed",
                        "message": "Whisper transcription failed, please try again"
                    }
            else:
                # For server-side voice chat, we need actual transcription
                # If Whisper is not available, we should indicate this clearly
                result = {
                    "success": False,
                    "error": "Server-side speech recognition not available. Whisper is required for voice chat functionality.",
                    "text": "",
                    "method": "server_side_required",
                    "message": "Please use text input instead, or install Whisper for voice functionality"
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
        """Transcribe using local Whisper model with proper WebM handling."""
        import whisper
        
        # Validate audio data
        if not audio_data or len(audio_data) < 100:
            raise Exception(f"Audio data too small: {len(audio_data)} bytes")
        
        logger.info(f"Processing audio data: {len(audio_data)} bytes, format: {format}")
        logger.info(f"🔍 Format check: format='{format}', type={type(format)}")
        logger.info(f"🔍 Format == 'webm': {format == 'webm'}")
        logger.info(f"🔍 Audio starts with WebM magic: {audio_data.startswith(b'\\x1A\\x45\\xDF\\xA3')}")
        
        # Handle WebM format properly with ffmpeg
        if format == "webm":
            # Verify WebM magic bytes
            if audio_data.startswith(b'\x1A\x45\xDF\xA3'):
                logger.info("✅ Valid WebM format detected, using enhanced ffmpeg conversion")
                try:
                    logger.info("🔧 Attempting enhanced WebM processing...")
                    result = await self._process_webm_with_ffmpeg(audio_data, language)
                    logger.info(f"✅ Enhanced WebM processing completed: {result.get('method', 'unknown')}")
                    return result
                except Exception as webm_error:
                    logger.error(f"❌ Enhanced WebM FFmpeg processing failed: {webm_error}")
                    logger.info("📦 Trying alternative WebM processing approaches...")
                    
                    # Try alternative approach: force format in FFmpeg
                    try:
                        logger.info("🔧 Attempting forced WebM processing...")
                        result = await self._process_webm_with_ffmpeg_force(audio_data, language)
                        logger.info(f"✅ Forced WebM processing completed: {result.get('method', 'unknown')}")
                        return result
                    except Exception as force_error:
                        logger.error(f"❌ Force WebM processing failed: {force_error}")
                        logger.warning("📦 Falling back to raw audio processing for WebM data")
                        return await self._convert_and_transcribe(audio_data, "raw", language)
            else:
                logger.warning("Format claimed to be WebM but no magic bytes, treating as raw")
                return await self._convert_and_transcribe(audio_data, "raw", language)
        
        elif format in ["raw"]:
            # Use direct numpy processing for raw/corrupted data
            return await self._convert_and_transcribe(audio_data, "raw", language)
        else:
            # For proper audio formats (WAV, MP3), use Whisper directly
            temp_audio_path = None
            try:
                file_extension = format.lower()
                with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_audio:
                    temp_audio.write(audio_data)
                    temp_audio_path = temp_audio.name
                
                logger.info(f"Processing {format} file: {temp_audio_path}")
                
                # Load Whisper model
                model = whisper.load_model("base")
                
                # Transcribe
                result = model.transcribe(
                    temp_audio_path,
                    language=language if language != "auto" else None,
                    fp16=False
                )
                
                transcribed_text = result["text"].strip()
                
                return {
                    "success": True,
                    "text": transcribed_text,
                    "confidence": 1.0,
                    "method": "whisper_file",
                    "language_detected": result.get("language", language)
                }
                
            finally:
                if temp_audio_path:
                    try:
                        os.unlink(temp_audio_path)
                    except:
                        pass

    async def _process_webm_with_ffmpeg(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Enhanced WebM processing with volume normalization and better transcription."""
        import whisper
        import subprocess
        import tempfile
        import os
        import wave
        import numpy as np
        
        logger.info(f"🔧 Enhanced WebM processing: {len(audio_data)} bytes")
        
        temp_webm_path = None
        temp_wav_path = None
        
        try:
            # Save WebM data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_webm:
                temp_webm.write(audio_data)
                temp_webm_path = temp_webm.name
            
            # Create WAV output path
            temp_wav_path = temp_webm_path.replace('.webm', '_enhanced.wav')
            
            # Enhanced FFmpeg command with audio filters for better quality
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', temp_webm_path,
                '-vn',  # No video
                '-af', 'volume=3.0,highpass=f=80,lowpass=f=8000,dynaudnorm=p=0.9',  # Audio filters
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono
                temp_wav_path
            ]
            
            logger.info(f"🔧 Enhanced WebM conversion: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"Enhanced FFmpeg failed: {result.stderr}")
                # Try basic conversion without filters
                return await self._process_webm_basic(temp_webm_path, language)
            
            # Check if WAV file was created and has content
            if not os.path.exists(temp_wav_path):
                logger.warning("WAV file was not created, trying basic conversion")
                return await self._process_webm_basic(temp_webm_path, language)
                
            wav_size = os.path.getsize(temp_wav_path)
            
            if wav_size < 1000:
                logger.warning(f"WAV file too small ({wav_size} bytes), trying basic conversion")
                return await self._process_webm_basic(temp_webm_path, language)
            
            logger.info(f"✅ Enhanced WebM conversion successful: {wav_size} bytes")
            
            # Analyze the converted audio
            audio_analysis = self._analyze_wav_file(temp_wav_path)
            logger.info(f"📊 Audio analysis: RMS={audio_analysis.get('rms', 'N/A'):.1f}, Duration={audio_analysis.get('duration_sec', 'N/A'):.2f}s")
            
            # Load Whisper model and try multiple transcription strategies
            model = whisper.load_model("base")
            
            # Try different Whisper parameters for better transcription
            whisper_strategies = [
                {"fp16": False, "no_speech_threshold": 0.1, "temperature": 0.0},
                {"fp16": False, "no_speech_threshold": 0.05, "temperature": 0.0},
                {"fp16": False, "no_speech_threshold": 0.05, "temperature": 0.2},
                {"fp16": False, "no_speech_threshold": 0.02, "temperature": (0.0, 0.2, 0.4)},
            ]
            
            for i, strategy in enumerate(whisper_strategies):
                try:
                    logger.info(f"🎯 Trying Whisper strategy {i+1}")
                    result = model.transcribe(
                        temp_wav_path,
                        language=language if language != "auto" else None,
                        **strategy
                    )
                    
                    transcribed_text = result["text"].strip()
                    
                    if transcribed_text:
                        logger.info(f"✅ Transcription successful with strategy {i+1}: '{transcribed_text}'")
                        return {
                            "success": True,
                            "text": transcribed_text,
                            "confidence": 1.0,
                            "method": f"enhanced_webm_strategy_{i+1}",
                            "language_detected": result.get("language", language),
                            "audio_analysis": audio_analysis
                        }
                    else:
                        logger.debug(f"Strategy {i+1} returned empty transcription")
                        
                except Exception as whisper_error:
                    logger.warning(f"Whisper strategy {i+1} failed: {whisper_error}")
                    continue
            
            # If all strategies failed but we have valid audio, return success with empty text
            logger.warning("All transcription strategies returned empty results")
            return {
                "success": True,
                "text": "",
                "confidence": 0.0,
                "method": "enhanced_webm_silent",
                "language_detected": language,
                "audio_analysis": audio_analysis,
                "message": "Audio processed successfully but appears to contain silence or unclear speech"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            return await self._convert_and_transcribe(audio_data, "raw", language)
        except FileNotFoundError:
            logger.error("FFmpeg not found - cannot convert WebM")
            return await self._convert_and_transcribe(audio_data, "raw", language)
        except Exception as e:
            logger.error(f"WebM processing failed: {e}")
            return await self._convert_and_transcribe(audio_data, "raw", language)
        finally:
            # Cleanup temporary files
            for path in [temp_webm_path, temp_wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass

    async def _process_webm_with_ffmpeg_force(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Alternative WebM processing with forced format detection for browser audio."""
        import whisper
        import tempfile
        import subprocess
        import os
        
        temp_webm_path = None
        temp_wav_path = None
        
        try:
            logger.info("🔧 Trying alternative WebM processing with format forcing...")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_webm:
                temp_webm.write(audio_data)
                temp_webm_path = temp_webm.name
            
            temp_wav_path = temp_webm_path.replace('.webm', '_alt.wav')
            
            # Alternative FFmpeg command with more aggressive format detection
            ffmpeg_cmd = [
                'ffmpeg', '-y', 
                '-f', 'matroska',  # Force matroska format
                '-i', temp_webm_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono
                '-ignore_unknown',  # Ignore unknown elements
                temp_wav_path
            ]
            
            logger.info(f"Alternative WebM conversion: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Alternative FFmpeg conversion failed: {result.stderr}")
                raise Exception(f"Alternative FFmpeg failed: {result.stderr}")
            
            # Check if WAV file was created and has content
            if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) < 1000:
                logger.error("Alternative FFmpeg produced empty or invalid WAV file")
                raise Exception("Alternative FFmpeg produced invalid output")
            
            logger.info(f"✅ Alternative WebM conversion successful: {os.path.getsize(temp_wav_path)} bytes")
            
            # Load Whisper model and transcribe the WAV file
            model = whisper.load_model("base")
            
            result = model.transcribe(
                temp_wav_path,
                language=language if language != "auto" else None,
                fp16=False
            )
            
            transcribed_text = result["text"].strip()
            
            return {
                "success": True,
                "text": transcribed_text,
                "confidence": 1.0,
                "method": "whisper_webm_ffmpeg_alt",
                "language_detected": result.get("language", language)
            }
            
        except Exception as e:
            logger.error(f"Alternative WebM processing failed: {e}")
            raise e
        finally:
            # Cleanup temporary files
            for path in [temp_webm_path, temp_wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass

    async def _convert_and_transcribe(self, audio_data: bytes, source_format: str, language: str) -> Dict[str, Any]:
        """Convert raw audio data to WAV and transcribe with Whisper."""
        import whisper
        import numpy as np
        
        try:
            # If treating as raw PCM data from phone call
            if source_format == "raw":
                logger.info(f"Processing raw audio data: {len(audio_data)} bytes")
                
                # Debug: Analyze audio data characteristics
                logger.info(f"First 20 bytes: {audio_data[:20].hex()}")
                
                # Skip FFmpeg entirely - process the raw audio data directly
                try:
                    # Try to interpret as 16-bit PCM at various sample rates
                    sample_rates = [16000, 44100, 48000, 8000]  # Common sample rates
                    
                    for sample_rate in sample_rates:
                        try:
                            # Convert bytes to numpy array (16-bit signed integers)
                            if len(audio_data) % 2 != 0:
                                # Odd number of bytes, truncate last byte
                                audio_data = audio_data[:-1]
                            
                            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
                            
                            # Check if we have reasonable audio data
                            if len(audio_samples) < 160:  # Less than 0.01 seconds at 16kHz
                                continue
                            
                            # Analyze audio characteristics
                            rms = np.sqrt(np.mean((audio_samples.astype(np.float32) / 32768.0)**2))
                            non_zero_count = np.count_nonzero(audio_samples)
                            unique_values = len(np.unique(audio_samples))
                            
                            logger.info(f"Sample rate {sample_rate}Hz analysis:")
                            logger.info(f"  RMS: {rms:.6f}, Non-zero: {non_zero_count}/{len(audio_samples)}, Unique: {unique_values}")
                            logger.info(f"  Range: {np.min(audio_samples)} to {np.max(audio_samples)}")
                            logger.info(f"  Sample values: {audio_samples[:10].tolist()}")
                            
                            # Check if audio is too quiet (likely silence)
                            if rms < 0.001:
                                logger.warning(f"Audio appears silent at {sample_rate}Hz (RMS: {rms:.6f})")
                                continue
                            
                            # Check if audio has enough variation
                            if unique_values < 10:
                                logger.warning(f"Audio has very little variation at {sample_rate}Hz ({unique_values} unique values)")
                                continue
                            
                            # Normalize to float32 between -1.0 and 1.0
                            audio_float = audio_samples.astype(np.float32) / 32768.0
                            
                            # Enhanced volume normalization
                            if rms > 0:
                                # More aggressive volume boost for quiet audio
                                if rms < 0.001:
                                    boost_factor = 50.0  # Very quiet audio
                                elif rms < 0.01:
                                    boost_factor = 20.0  # Quiet audio
                                elif rms < 0.05:
                                    boost_factor = 5.0   # Moderately quiet
                                else:
                                    boost_factor = 1.0   # Normal volume
                                
                                audio_float = audio_float * boost_factor
                                # Clip to prevent distortion
                                audio_float = np.clip(audio_float, -1.0, 1.0)
                                
                                logger.info(f"Applied {boost_factor}x volume boost (original RMS: {rms:.6f})")
                            
                            # Resample to 16kHz if needed (Whisper prefers 16kHz)
                            if sample_rate != 16000:
                                # Simple resampling using scipy
                                from scipy import signal
                                target_length = int(len(audio_float) * 16000 / sample_rate)
                                audio_float = signal.resample(audio_float, target_length)
                            
                            logger.info(f"Converted raw audio: {len(audio_float)} samples at 16kHz")
                            
                            # Load Whisper model
                            model = whisper.load_model("base")
                            
                            # Use more aggressive Whisper settings for phone call audio
                            result = model.transcribe(
                                audio_float,  # Pass numpy array directly to Whisper
                                language=language if language != "auto" else None,
                                fp16=False,
                                no_speech_threshold=0.05,  # Lower threshold for quiet audio
                                temperature=0.0            # More deterministic
                            )
                            
                            transcribed_text = result["text"].strip()
                            
                            if transcribed_text:  # If we got text, this sample rate worked
                                logger.info(f"✅ Transcription successful with {sample_rate}Hz: '{transcribed_text}'")
                                return {
                                    "success": True,
                                    "text": transcribed_text,
                                    "confidence": 1.0,
                                    "method": "whisper_direct_numpy",
                                    "language_detected": result.get("language", language),
                                    "sample_rate_used": sample_rate,
                                    "audio_rms": float(rms),
                                    "audio_analysis": f"RMS:{rms:.6f}, NonZero:{non_zero_count}, Unique:{unique_values}"
                                }
                            else:
                                logger.warning(f"Empty transcription with {sample_rate}Hz, trying next...")
                                
                        except Exception as rate_error:
                            logger.warning(f"Sample rate {sample_rate}Hz failed: {rate_error}")
                            continue
                    
                    # If we get here, all sample rates failed
                    logger.warning("All sample rates failed, trying alternative approach...")
                    
                    # Try treating as 8-bit unsigned PCM
                    try:
                        audio_samples_8bit = np.frombuffer(audio_data, dtype=np.uint8)
                        # Convert to 16-bit signed
                        audio_samples = ((audio_samples_8bit.astype(np.float32) - 128) / 128 * 32767).astype(np.int16)
                        audio_float = audio_samples.astype(np.float32) / 32768.0
                        
                        logger.info(f"Trying 8-bit conversion: {len(audio_float)} samples")
                        
                        model = whisper.load_model("base")
                        result = model.transcribe(
                            audio_float,
                            language=language if language != "auto" else None,
                            fp16=False
                        )
                        
                        transcribed_text = result["text"].strip()
                        
                        return {
                            "success": True,
                            "text": transcribed_text,
                            "confidence": 1.0,
                            "method": "whisper_8bit_conversion",
                            "language_detected": result.get("language", language)
                        }
                        
                    except Exception as bit8_error:
                        logger.error(f"8-bit conversion failed: {bit8_error}")
                        raise Exception(f"Unable to process raw audio data with any format: {bit8_error}")
                                
                except Exception as raw_error:
                    logger.error(f"Raw audio processing failed: {raw_error}")
                    raise Exception(f"Unable to process audio data: {raw_error}")
            
            raise Exception(f"Unsupported source format: {source_format}")
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            # Don't disable Whisper permanently - just fail this request
            raise Exception(f"Audio processing failed: {e}")
    
    async def _process_webm_basic(self, webm_path: str, language: str) -> Dict[str, Any]:
        """Basic WebM conversion without audio filters as fallback."""
        import whisper
        import subprocess
        import os
        
        temp_wav_path = None
        
        try:
            temp_wav_path = webm_path.replace('.webm', '_basic.wav')
            
            # Basic FFmpeg command without audio filters
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', webm_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                temp_wav_path
            ]
            
            logger.info(f"🔧 Basic WebM conversion: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Basic FFmpeg conversion failed: {result.stderr}")
                raise Exception(f"Basic FFmpeg failed: {result.stderr}")
            
            if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) < 1000:
                raise Exception("Basic FFmpeg produced invalid output")
            
            logger.info(f"✅ Basic conversion successful: {os.path.getsize(temp_wav_path)} bytes")
            
            # Transcribe with Whisper
            model = whisper.load_model("base")
            result = model.transcribe(
                temp_wav_path, 
                language=language if language != "auto" else None, 
                fp16=False,
                no_speech_threshold=0.05
            )
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "confidence": 1.0,
                "method": "basic_webm_conversion",
                "language_detected": result.get("language", language)
            }
            
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass

    def _analyze_wav_file(self, wav_path: str) -> Dict[str, Any]:
        """Analyze WAV file characteristics for debugging."""
        try:
            import wave
            import numpy as np
            
            with wave.open(wav_path, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                # Convert to numpy array for analysis
                if sample_width == 2:  # 16-bit
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                elif sample_width == 1:  # 8-bit
                    audio_data = np.frombuffer(frames, dtype=np.uint8)
                else:
                    return {"error": f"Unsupported sample width: {sample_width}"}
                
                # Calculate statistics
                rms = np.sqrt(np.mean((audio_data.astype(np.float32))**2))
                max_val = np.max(np.abs(audio_data))
                zero_count = np.count_nonzero(audio_data == 0)
                
                return {
                    "sample_rate": sample_rate,
                    "channels": channels,
                    "sample_width": sample_width,
                    "duration_sec": len(audio_data) / sample_rate,
                    "rms": float(rms),
                    "max_amplitude": int(max_val),
                    "zero_percentage": zero_count / len(audio_data) * 100,
                    "total_samples": len(audio_data)
                }
                
        except Exception as e:
            return {"error": str(e)}
    
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
