#!/usr/bin/env python3
"""Simple WebM to WAV conversion test"""

import subprocess
import tempfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_webm_conversion():
    """Test WebM conversion with a sample WebM file"""
    
    # Create a minimal test WebM file
    webm_magic = b'\x1A\x45\xDF\xA3'  # WebM magic bytes
    
    # Look for existing test files first
    test_files = [f for f in os.listdir('.') if 'webm' in f.lower() or ('test' in f and f.endswith('.wav'))]
    
    print("Available test files:")
    for file in test_files:
        if os.path.isfile(file):
            with open(file, 'rb') as f:
                data = f.read(20)
                print(f"  {file}: {len(data)} bytes, magic: {data.hex()}")
                if data.startswith(webm_magic):
                    print(f"    ✅ {file} has WebM magic bytes")
                    return test_convert_file(file)
    
    print("No test WebM files found. The issue might be that FFmpeg can convert")
    print("but the actual WebM data from the phone call is corrupted or incomplete.")
    
    return False

def test_convert_file(webm_file):
    """Test converting a specific WebM file"""
    temp_wav = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp:
            temp_wav = temp.name
        
        # Test the same FFmpeg command used in the STT service
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', webm_file,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',      # Mono
            temp_wav
        ]
        
        print(f"Testing conversion: {' '.join(ffmpeg_cmd)}")
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            wav_size = os.path.getsize(temp_wav) if os.path.exists(temp_wav) else 0
            print(f"✅ Conversion successful: {wav_size} bytes")
            
            if wav_size > 1000:
                # Test with Whisper
                try:
                    import whisper
                    model = whisper.load_model("base")
                    whisper_result = model.transcribe(temp_wav, fp16=False)
                    print(f"🎤 Whisper transcription: '{whisper_result['text']}'")
                    return True
                except Exception as e:
                    print(f"❌ Whisper failed: {e}")
                    return False
            else:
                print("⚠️ WAV file too small")
                return False
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
            
    finally:
        if temp_wav and os.path.exists(temp_wav):
            os.unlink(temp_wav)

if __name__ == "__main__":
    print("🔍 Simple WebM Conversion Test")
    print("=============================")
    test_webm_conversion()
