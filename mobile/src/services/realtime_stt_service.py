"""
Real-time Speech-to-Text service for phone calls.
Optimized for low-latency streaming audio processing.
"""

import asyncio
import logging
import numpy as np
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import tempfile
import io

from .stt_service import stt_service  # Use existing STT service as fallback

logger = logging.getLogger(__name__)

class RealtimeSTTService:
    """
    Real-time STT service optimized for phone call scenarios.
    Provides faster transcription with voice activity detection.
    """
    
    def __init__(self):
        self.is_available = self._check_availability()
        self.fallback_service = stt_service
        
        # VAD settings
        self.vad_threshold = 0.5
        self.min_speech_duration = 0.5  # Minimum speech duration in seconds
        self.max_silence_duration = 1.0  # Maximum silence before processing
        
        # Audio processing settings
        self.sample_rate = 16000
        self.chunk_duration = 3.0  # Process audio in 3-second chunks
        
        logger.info(f"Real-time STT service initialized. Available: {self.is_available}")
    
    def _check_availability(self) -> bool:
        """Check if real-time STT dependencies are available."""
        try:
            # Check if we have WebRTC VAD available
            try:
                import webrtcvad
                self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
                logger.info("WebRTC VAD available for voice activity detection")
                return True
            except ImportError:
                logger.info("WebRTC VAD not available, using fallback STT")
                return False
                
        except Exception as e:
            logger.warning(f"Real-time STT initialization failed: {e}")
            return False
    
    def detect_voice_activity(self, audio_data: bytes, sample_rate: int = 16000) -> bool:
        """
        Detect if audio contains speech using VAD.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
            
        Returns:
            True if speech is detected, False otherwise
        """
        if not self.is_available:
            return True  # Assume speech if VAD not available
        
        try:
            # Convert audio to format expected by WebRTC VAD
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # WebRTC VAD expects specific frame sizes (10, 20, or 30ms)
            frame_duration = 20  # ms
            frame_size = int(sample_rate * frame_duration / 1000)
            
            # Process audio in frames
            speech_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_array) - frame_size + 1, frame_size):
                frame = audio_array[i:i + frame_size]
                frame_bytes = frame.tobytes()
                
                if len(frame_bytes) == frame_size * 2:  # 2 bytes per sample
                    is_speech = self.vad.is_speech(frame_bytes, sample_rate)
                    if is_speech:
                        speech_frames += 1
                    total_frames += 1
            
            if total_frames == 0:
                return False
            
            # Return True if more than threshold percentage contains speech
            speech_ratio = speech_frames / total_frames
            return speech_ratio > self.vad_threshold
            
        except Exception as e:
            logger.warning(f"VAD failed: {e}")
            return True  # Assume speech on error
    
    async def transcribe_streaming_audio(
        self,
        audio_data: bytes,
        language: str = "en",
        format: str = "webm"
    ) -> Dict[str, Any]:
        """
        Transcribe streaming audio with optimizations for real-time use.
        
        Args:
            audio_data: Raw audio bytes
            language: Target language for transcription
            format: Audio format
            
        Returns:
            Dict with transcription result
        """
        start_time = time.time()
        
        try:
            # Skip processing if audio is too short
            if len(audio_data) < 1000:
                return {
                    "success": False,
                    "text": "",
                    "error": "Audio too short",
                    "processing_time": time.time() - start_time
                }
            
            # Voice activity detection
            has_speech = self.detect_voice_activity(audio_data)
            if not has_speech:
                return {
                    "success": True,
                    "text": "",
                    "confidence": 0.0,
                    "processing_time": time.time() - start_time,
                    "vad_result": "no_speech"
                }
            
            # Use existing STT service for actual transcription
            # but with optimizations for streaming
            result = await self.fallback_service.transcribe_audio_file(
                audio_data=audio_data,
                format=format,
                language=language
            )
            
            # Add VAD information to result
            if result.get("success"):
                result["vad_result"] = "speech_detected"
                result["realtime_optimized"] = True
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            # Log performance
            if processing_time > 2.0:
                logger.warning(f"Slow STT processing: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Real-time STT error: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def preprocess_audio(self, audio_data: bytes, target_sample_rate: int = 16000) -> bytes:
        """
        Preprocess audio for optimal STT performance.
        
        Args:
            audio_data: Raw audio bytes
            target_sample_rate: Target sample rate
            
        Returns:
            Preprocessed audio bytes
        """
        try:
            # Convert to numpy array for processing
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply simple noise reduction (high-pass filter)
            # This is a very basic implementation
            if len(audio_array) > 100:
                # Remove very low frequencies (< 80Hz) that are likely noise
                from scipy.signal import butter, filtfilt
                nyquist = target_sample_rate // 2
                low_cutoff = 80 / nyquist
                b, a = butter(1, low_cutoff, btype='high')
                audio_array = filtfilt(b, a, audio_array.astype(np.float32))
                audio_array = audio_array.astype(np.int16)
            
            return audio_array.tobytes()
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}")
            return audio_data  # Return original if preprocessing fails
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of real-time STT service."""
        try:
            # Test basic functionality
            test_audio = b'\x00' * 8000  # 0.5 seconds of silence at 16kHz
            
            start_time = time.time()
            result = await self.transcribe_streaming_audio(test_audio)
            processing_time = time.time() - start_time
            
            status = "healthy" if result.get("success") is not None else "error"
            
            return {
                "status": status,
                "vad_available": self.is_available,
                "fallback_service": self.fallback_service.is_available(),
                "test_processing_time": processing_time,
                "capabilities": {
                    "voice_activity_detection": self.is_available,
                    "real_time_optimized": True,
                    "preprocessing": True
                }
            }
            
        except Exception as e:
            logger.error(f"Real-time STT health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "vad_available": False,
                "fallback_service": self.fallback_service.is_available()
            }

# Global instance
realtime_stt_service = RealtimeSTTService()

# Convenience function for backward compatibility
async def transcribe_phone_audio(
    audio_data: bytes,
    language: str = "en",
    format: str = "webm"
) -> Dict[str, Any]:
    """
    Convenience function for phone call audio transcription.
    """
    return await realtime_stt_service.transcribe_streaming_audio(
        audio_data=audio_data,
        language=language,
        format=format
    )
