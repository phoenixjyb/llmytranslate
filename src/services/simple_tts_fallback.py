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
        Create a simple TTS response with audible beep tones.
        """
        try:
            logger.info(f"TTS Fallback generating audio for: '{text}' (voice: {voice}, lang: {language})")
            
            # Create audible tones instead of silence for phone calls
            # This gives feedback that the AI is responding
            beep_wav = self._create_beep_wav(text_length=len(text))
            
            return beep_wav
            
        except Exception as e:
            logger.error(f"TTS fallback error: {e}")
            return None
    
    def _create_beep_wav(self, text_length: int = 20, sample_rate: int = 22050) -> bytes:
        """Create an audible beep tone to indicate AI response."""
        try:
            import struct
            import math
            
            # Create a pleasant beep sequence for AI responses
            duration_ms = max(800, min(3000, text_length * 80))  # 0.8-3 seconds based on text length
            num_samples = int(duration_ms * sample_rate / 1000)
            
            # Generate a gentle two-tone beep (like phone notification)
            samples = []
            fade_samples = int(sample_rate * 0.1)  # 0.1 second fade
            
            for i in range(num_samples):
                t = i / sample_rate
                
                # Create a gentle notification sound - two tones
                if i < num_samples // 2:
                    freq = 800  # First tone (higher)
                else:
                    freq = 600  # Second tone (lower)
                
                # Generate sine wave
                amplitude = 0.3  # Moderate volume
                value = amplitude * math.sin(2 * math.pi * freq * t)
                
                # Apply fade in/out for smooth sound
                if i < fade_samples:
                    value *= (i / fade_samples)
                elif i > num_samples - fade_samples:
                    remaining = num_samples - i
                    value *= (remaining / fade_samples)
                
                # Convert to 16-bit signed integer
                sample = int(value * 32767)
                samples.append(sample)
            
            # Create WAV file
            num_channels = 1
            bytes_per_sample = 2
            byte_rate = sample_rate * num_channels * bytes_per_sample
            block_align = num_channels * bytes_per_sample
            
            # WAV header
            wav_data = bytearray()
            wav_data.extend(b'RIFF')
            wav_data.extend(struct.pack('<I', 36 + len(samples) * bytes_per_sample))
            wav_data.extend(b'WAVE')
            wav_data.extend(b'fmt ')
            wav_data.extend(struct.pack('<I', 16))  # PCM format chunk size
            wav_data.extend(struct.pack('<H', 1))   # PCM format
            wav_data.extend(struct.pack('<H', num_channels))
            wav_data.extend(struct.pack('<I', sample_rate))
            wav_data.extend(struct.pack('<I', byte_rate))
            wav_data.extend(struct.pack('<H', block_align))
            wav_data.extend(struct.pack('<H', 16))  # Bits per sample
            wav_data.extend(b'data')
            wav_data.extend(struct.pack('<I', len(samples) * bytes_per_sample))
            
            # Add sample data
            for sample in samples:
                wav_data.extend(struct.pack('<h', sample))
            
            logger.info(f"Generated beep audio: {len(wav_data)} bytes, {duration_ms}ms duration")
            return bytes(wav_data)
            
        except Exception as e:
            logger.error(f"Failed to create beep audio: {e}")
            # Fall back to silent audio if beep generation fails
            return self._create_silent_wav(1000)
    
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
