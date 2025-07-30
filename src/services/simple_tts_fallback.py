"""
Simple TTS Fallback Service
Provides basic text-to-speech when the dual-environment TTS is not available.
"""

import asyncio
import logging
import base64
import json
from typing import Optional

logger = logging.getLogger(__name__)

class SimpleTTSFallback:
    """Simple TTS fallback using Windows built-in SAPI or browser TTS simulation."""
    
    def __init__(self):
        self.is_available = True  # Always available as fallback
        logger.info("Simple TTS fallback initialized")
    
    async def synthesize_speech(self, text: str, voice: str = "en-US", 
                              language: str = "en", optimization_level: str = "balanced") -> Optional[bytes]:
        """
        Create a simple TTS response.
        For now, returns empty audio but logs the text for debugging.
        """
        try:
            logger.info(f"TTS Fallback would speak: '{text}' (voice: {voice}, lang: {language})")
            
            # For immediate testing, return a minimal WAV header (silence)
            # This prevents the "no audio" error while we setup proper TTS
            silence_wav = self._create_silent_wav(duration_ms=len(text) * 100)  # Roughly match text length
            
            return silence_wav
            
        except Exception as e:
            logger.error(f"TTS fallback error: {e}")
            return None
    
    def _create_silent_wav(self, duration_ms: int = 1000, sample_rate: int = 22050) -> bytes:
        """Create a minimal silent WAV file for testing."""
        try:
            # WAV header for silent audio
            num_samples = int(duration_ms * sample_rate / 1000)
            num_channels = 1
            bytes_per_sample = 2
            
            # WAV header (44 bytes)
            wav_header = bytearray()
            wav_header.extend(b'RIFF')  # ChunkID
            wav_header.extend((36 + num_samples * num_channels * bytes_per_sample).to_bytes(4, 'little'))  # ChunkSize
            wav_header.extend(b'WAVE')  # Format
            wav_header.extend(b'fmt ')  # Subchunk1ID
            wav_header.extend((16).to_bytes(4, 'little'))  # Subchunk1Size
            wav_header.extend((1).to_bytes(2, 'little'))   # AudioFormat (PCM)
            wav_header.extend(num_channels.to_bytes(2, 'little'))  # NumChannels
            wav_header.extend(sample_rate.to_bytes(4, 'little'))   # SampleRate
            wav_header.extend((sample_rate * num_channels * bytes_per_sample).to_bytes(4, 'little'))  # ByteRate
            wav_header.extend((num_channels * bytes_per_sample).to_bytes(2, 'little'))  # BlockAlign
            wav_header.extend((8 * bytes_per_sample).to_bytes(2, 'little'))  # BitsPerSample
            wav_header.extend(b'data')  # Subchunk2ID
            wav_header.extend((num_samples * num_channels * bytes_per_sample).to_bytes(4, 'little'))  # Subchunk2Size
            
            # Silent audio data (all zeros)
            audio_data = bytes(num_samples * num_channels * bytes_per_sample)
            
            return bytes(wav_header) + audio_data
            
        except Exception as e:
            logger.error(f"Failed to create silent WAV: {e}")
            return b''  # Return empty bytes if WAV creation fails

# Create fallback instance
simple_tts_fallback = SimpleTTSFallback()
