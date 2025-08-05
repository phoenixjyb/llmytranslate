#!/usr/bin/env python3
"""
Test script for British accent TTS with emoji and special character handling.
"""

import sys
import os
import json
import tempfile
import subprocess
from pathlib import Path

def test_tts_british_accent():
    """Test TTS with British accent and special character cleaning."""
    
    # Test text with emojis, markdown, and special characters
    test_texts = [
        "Hello! 😊 This is a test with emojis 🎉 and **bold text** that should be cleaned.",
        "What's the weather like today? ☀️🌧️ It's quite lovely, isn't it? 🇬🇧",
        "I can't believe it's working!!! 🚀🚀🚀 Amazing... ***fantastic*** `code snippet` here.",
        "Visit https://example.com for more info! ~~strikethrough~~ text here.",
        "Simple test without any special characters or emojis."
    ]
    
    print("🇬🇧 Testing British Accent TTS with Special Character Cleaning")
    print("=" * 60)
    
    for i, test_text in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}: {test_text}")
        print("-" * 40)
        
        try:
            # Create temporary files with proper UTF-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as req_file:
                request_data = {
                    "action": "synthesize",
                    "text": test_text,
                    "language": "en",  # Will use British accent
                    "voice": "british",
                    "speed": 1.0
                }
                json.dump(request_data, req_file, ensure_ascii=False, indent=2)
                request_file_path = req_file.name
            
            # Output audio file
            output_file_path = f"test_british_tts_{i}.wav"
            
            # Run TTS subprocess
            print(f"🎤 Generating speech to: {output_file_path}")
            
            # Set up Python path for TTS environment
            tts_python = ".venv-tts/Scripts/python.exe" if os.path.exists(".venv-tts/Scripts/python.exe") else "python"
            
            result = subprocess.run([
                tts_python, "tts_subprocess.py", 
                request_file_path, output_file_path
            ], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                print("✅ TTS synthesis successful!")
                if os.path.exists(output_file_path):
                    file_size = os.path.getsize(output_file_path)
                    print(f"📁 Output file: {output_file_path} ({file_size:,} bytes)")
                else:
                    print("⚠️ Output file not found")
            else:
                print(f"❌ TTS synthesis failed!")
                print(f"Error: {result.stderr}")
                
            # Print subprocess logs
            if result.stdout:
                print(f"📋 TTS Logs:\n{result.stdout}")
                
        except subprocess.TimeoutExpired:
            print("⏰ TTS synthesis timed out")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            # Cleanup request file
            try:
                os.unlink(request_file_path)
            except:
                pass
    
    print("\n🎯 Test Summary:")
    print("- British accent should be used for English")
    print("- Emojis and special characters should be cleaned")
    print("- Audio files should be generated successfully")
    print("\n🎧 Play the generated .wav files to test audio quality!")

if __name__ == "__main__":
    test_tts_british_accent()
