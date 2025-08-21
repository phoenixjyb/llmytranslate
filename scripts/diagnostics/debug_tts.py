#!/usr/bin/env python3
"""
Debug TTS subprocess to find why it's producing 0.01 second files.
"""

import json
import tempfile
import subprocess
import os
import sys
from pathlib import Path

def debug_tts_subprocess():
    """Debug the TTS subprocess with a simple test."""
    
    print("🔍 Debugging TTS Subprocess")
    print("=" * 40)
    
    # Simple test text (no emojis)
    test_text = "Hello, this is a simple test for British accent TTS."
    
    print(f"📝 Test text: '{test_text}'")
    
    try:
        # Create temporary request file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as req_file:
            request_data = {
                "action": "synthesize",
                "text": test_text,
                "language": "en",
                "voice": "british",
                "speed": 1.0
            }
            json.dump(request_data, req_file, ensure_ascii=False, indent=2)
            request_file_path = req_file.name
        
        # Output file
        output_file_path = "debug_tts_test.wav"
        
        print(f"📁 Request file: {request_file_path}")
        print(f"📁 Output file: {output_file_path}")
        
        # Check which Python environment to use
        tts_python_candidates = [
            ".venv-tts/Scripts/python.exe",
            ".venv/Scripts/python.exe", 
            "python.exe"
        ]
        
        tts_python = None
        for candidate in tts_python_candidates:
            if os.path.exists(candidate):
                tts_python = candidate
                break
        
        if not tts_python:
            tts_python = "python.exe"
        
        print(f"🐍 Using Python: {tts_python}")
        
        # Run TTS subprocess with detailed output
        print("🎤 Running TTS subprocess...")
        
        result = subprocess.run([
            tts_python, "tts_subprocess.py", 
            request_file_path, output_file_path
        ], capture_output=True, text=True, timeout=60)
        
        print(f"📊 Return code: {result.returncode}")
        
        if result.stdout:
            print("📋 STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("❌ STDERR:")
            print(result.stderr)
        
        # Check output file
        if os.path.exists(output_file_path):
            file_size = os.path.getsize(output_file_path)
            print(f"📁 Output file created: {file_size:,} bytes")
            
            if file_size < 1000:  # Less than 1KB is probably an error
                print("⚠️ File is very small - likely TTS failed")
            else:
                print("✅ File size looks good")
        else:
            print("❌ Output file not created")
        
        # Show request file content
        print("\n📄 Request file content:")
        with open(request_file_path, 'r', encoding='utf-8') as f:
            print(f.read())
        
    except subprocess.TimeoutExpired:
        print("⏰ TTS subprocess timed out (60 seconds)")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        try:
            os.unlink(request_file_path)
        except:
            pass
    
    print("\n🔍 Debug complete. Check the output above for errors.")

if __name__ == "__main__":
    debug_tts_subprocess()
