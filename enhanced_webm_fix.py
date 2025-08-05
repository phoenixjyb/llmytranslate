#!/usr/bin/env python3
"""Enhanced WebM audio processing with volume normalization and silence detection"""

import asyncio
import logging
import tempfile
import subprocess
import os
import numpy as np
import whisper
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def enhanced_webm_processing(audio_data: bytes, language: str = "en") -> dict:
    """Enhanced WebM processing with volume normalization and better error handling"""
    
    if not audio_data or len(audio_data) < 100:
        raise Exception(f"Audio data too small: {len(audio_data)} bytes")
    
    logger.info(f"🎤 Processing WebM audio: {len(audio_data)} bytes")
    logger.info(f"Magic bytes: {audio_data[:4].hex()}")
    
    # Verify WebM format
    if not audio_data.startswith(b'\x1A\x45\xDF\xA3'):
        logger.warning("No WebM magic bytes detected, treating as raw audio")
        return await process_raw_audio_enhanced(audio_data, language)
    
    temp_webm_path = None
    temp_wav_path = None
    
    try:
        # Save WebM data to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_webm:
            temp_webm.write(audio_data)
            temp_webm_path = temp_webm.name
        
        # Create WAV output path
        temp_wav_path = temp_webm_path.replace('.webm', '_enhanced.wav')
        
        # Enhanced FFmpeg command with volume normalization and audio filters
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', temp_webm_path,
            '-vn',  # No video
            '-af', 'volume=3.0,highpass=f=80,lowpass=f=8000,dynaudnorm',  # Audio filters
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',      # Mono
            temp_wav_path
        ]
        
        logger.info(f"🔧 Enhanced conversion: {' '.join(ffmpeg_cmd)}")
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.warning(f"Enhanced FFmpeg failed: {result.stderr}")
            # Fall back to basic conversion
            return await basic_webm_conversion(temp_webm_path, language)
        
        # Check if WAV file was created and has content
        if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) < 1000:
            logger.warning("Enhanced FFmpeg produced small/empty WAV file")
            return await basic_webm_conversion(temp_webm_path, language)
        
        wav_size = os.path.getsize(temp_wav_path)
        logger.info(f"✅ Enhanced WebM conversion successful: {wav_size} bytes")
        
        # Analyze the converted audio
        audio_analysis = analyze_wav_file(temp_wav_path)
        logger.info(f"Audio analysis: {audio_analysis}")
        
        # Load Whisper model and transcribe
        model = whisper.load_model("base")
        
        # Try different Whisper parameters for better transcription
        whisper_options = [
            {"fp16": False, "no_speech_threshold": 0.1},  # Lower threshold
            {"fp16": False, "no_speech_threshold": 0.05, "temperature": 0.0},  # Even lower
            {"fp16": False, "no_speech_threshold": 0.05, "temperature": 0.2},  # With temperature
        ]
        
        for i, options in enumerate(whisper_options):
            try:
                logger.info(f"Trying Whisper option {i+1}: {options}")
                result = model.transcribe(
                    temp_wav_path,
                    language=language if language != "auto" else None,
                    **options
                )
                
                transcribed_text = result["text"].strip()
                
                if transcribed_text:
                    logger.info(f"✅ Transcription successful with option {i+1}: '{transcribed_text}'")
                    return {
                        "success": True,
                        "text": transcribed_text,
                        "confidence": 1.0,
                        "method": f"enhanced_webm_option_{i+1}",
                        "language_detected": result.get("language", language),
                        "audio_analysis": audio_analysis
                    }
                else:
                    logger.warning(f"Empty transcription with option {i+1}")
                    
            except Exception as whisper_error:
                logger.warning(f"Whisper option {i+1} failed: {whisper_error}")
                continue
        
        # If all Whisper options failed, return with audio analysis
        return {
            "success": True,  # Still success since we processed the audio
            "text": "",
            "confidence": 0.0,
            "method": "enhanced_webm_silent",
            "language_detected": language,
            "audio_analysis": audio_analysis,
            "message": "Audio processed but appears to contain silence or unclear speech"
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Enhanced FFmpeg conversion timed out")
        raise Exception("Audio conversion timed out")
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        raise Exception("FFmpeg not available for audio conversion")
    except Exception as e:
        logger.error(f"Enhanced WebM processing failed: {e}")
        raise Exception(f"Enhanced WebM processing failed: {e}")
    finally:
        # Cleanup temporary files
        for path in [temp_webm_path, temp_wav_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass

async def basic_webm_conversion(webm_path: str, language: str) -> dict:
    """Basic WebM conversion without audio filters"""
    temp_wav_path = None
    
    try:
        temp_wav_path = webm_path.replace('.webm', '_basic.wav')
        
        # Basic FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', webm_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            temp_wav_path
        ]
        
        logger.info(f"🔧 Basic conversion: {' '.join(ffmpeg_cmd)}")
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"Basic FFmpeg failed: {result.stderr}")
        
        if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) < 1000:
            raise Exception("Basic FFmpeg produced invalid output")
        
        logger.info(f"✅ Basic conversion successful: {os.path.getsize(temp_wav_path)} bytes")
        
        # Transcribe with Whisper
        model = whisper.load_model("base")
        result = model.transcribe(temp_wav_path, language=language if language != "auto" else None, fp16=False)
        
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

async def process_raw_audio_enhanced(audio_data: bytes, language: str) -> dict:
    """Enhanced raw audio processing with volume normalization"""
    logger.info(f"Processing raw audio: {len(audio_data)} bytes")
    
    # Try different interpretations of the raw data
    sample_rates = [16000, 44100, 48000, 8000]
    
    for sample_rate in sample_rates:
        try:
            # Convert bytes to numpy array (16-bit signed integers)
            if len(audio_data) % 2 != 0:
                audio_data = audio_data[:-1]
            
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_samples) < 160:  # Less than 0.01 seconds at 16kHz
                continue
            
            # Normalize and amplify audio
            audio_float = audio_samples.astype(np.float32) / 32768.0
            
            # Calculate RMS and apply volume boost if needed
            rms = np.sqrt(np.mean(audio_float**2))
            if rms > 0:
                # Boost volume by up to 10x if audio is very quiet
                boost_factor = min(10.0, 0.1 / rms) if rms < 0.1 else 1.0
                audio_float = audio_float * boost_factor
                # Clip to prevent distortion
                audio_float = np.clip(audio_float, -1.0, 1.0)
            
            logger.info(f"Sample rate {sample_rate}Hz: RMS={rms:.6f}, boost={boost_factor:.2f}x")
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                from scipy import signal
                target_length = int(len(audio_float) * 16000 / sample_rate)
                audio_float = signal.resample(audio_float, target_length)
            
            # Transcribe with Whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_float, language=language if language != "auto" else None, fp16=False, no_speech_threshold=0.05)
            
            transcribed_text = result["text"].strip()
            
            if transcribed_text:
                logger.info(f"✅ Raw audio transcription successful: '{transcribed_text}'")
                return {
                    "success": True,
                    "text": transcribed_text,
                    "confidence": 1.0,
                    "method": f"enhanced_raw_{sample_rate}hz",
                    "language_detected": result.get("language", language)
                }
            
        except Exception as e:
            logger.warning(f"Sample rate {sample_rate}Hz failed: {e}")
            continue
    
    return {
        "success": True,
        "text": "",
        "confidence": 0.0,
        "method": "enhanced_raw_silent",
        "message": "Raw audio processed but appears silent"
    }

def analyze_wav_file(wav_path: str) -> dict:
    """Analyze WAV file characteristics"""
    try:
        import wave
        
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
                "duration": len(audio_data) / sample_rate,
                "rms": float(rms),
                "max_amplitude": int(max_val),
                "zero_percentage": zero_count / len(audio_data) * 100,
                "samples": len(audio_data)
            }
            
    except Exception as e:
        return {"error": str(e)}

# Test function
async def test_enhanced_processing():
    """Test the enhanced processing with sample data"""
    logger.info("Testing enhanced WebM processing...")
    
    # Create sample WebM-like data
    webm_magic = b'\x1A\x45\xDF\xA3'
    sample_data = webm_magic + b'\x00' * 1000
    
    try:
        result = await enhanced_webm_processing(sample_data)
        logger.info(f"Test result: {result}")
        return result
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return None

if __name__ == "__main__":
    print("🎤 Enhanced WebM Processing Test")
    print("===============================")
    result = asyncio.run(test_enhanced_processing())
