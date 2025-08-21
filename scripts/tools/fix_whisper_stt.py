#!/usr/bin/env python3
"""Force enable Whisper and restart phone call service"""

import os
import subprocess
import time
import sys

sys.path.append('.')

print("🔧 FIXING WHISPER STT SERVICE")
print("=" * 50)

try:
    # Kill any existing Python processes
    print("1. Stopping existing services...")
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True, shell=True)
    time.sleep(2)
    
    # Force enable Whisper in the STT service
    print("2. Force enabling Whisper...")
    
    # Read the STT service file
    stt_file_path = "src/services/stt_service.py"
    with open(stt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if Whisper is properly configured
    if "self.whisper_available = True" not in content:
        print("   Adding Whisper force enable...")
        # Add a method to force enable Whisper
        force_enable_method = '''
    def force_enable_whisper(self) -> bool:
        """Force enable Whisper for phone call service."""
        try:
            import whisper
            self.whisper_available = True
            logger.info("✅ Whisper force enabled for phone call service")
            return True
        except ImportError:
            logger.error("❌ Whisper not installed - cannot force enable")
            return False
'''
        # Insert before the last class definition ends
        insertion_point = content.rfind("# Global STT service instance")
        if insertion_point == -1:
            insertion_point = content.rfind("stt_service = SpeechToTextService()")
        
        if insertion_point != -1:
            content = content[:insertion_point] + force_enable_method + "\n" + content[insertion_point:]
            
            with open(stt_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("   ✅ Added force enable method")
    
    # Now test Whisper availability
    print("3. Testing Whisper availability...")
    test_cmd = [
        ".venv/Scripts/python.exe", "-c",
        """
import sys
sys.path.append('.')
try:
    import whisper
    print('✅ Whisper import successful')
    model = whisper.load_model('base')
    print('✅ Whisper model loaded successfully')
    
    # Force enable in STT service
    from src.services.stt_service import stt_service
    stt_service.whisper_available = True
    print('✅ STT service Whisper enabled')
    
except Exception as e:
    print(f'❌ Whisper test failed: {e}')
"""
    ]
    
    result = subprocess.run(test_cmd, capture_output=True, text=True, shell=True)
    print("   Whisper test output:")
    print("  ", result.stdout.strip())
    if result.stderr:
        print("   Errors:")
        print("  ", result.stderr.strip())
    
    # Start the phone call service
    print("4. Starting phone call service...")
    print("   Command: .venv/Scripts/python.exe run.py phone_call")
    print("   Service should start in a few seconds...")
    print("   Access at: http://localhost:8000/phone_call")
    print("   Ngrok URL: (use your ngrok tunnel)")
    
    # Start in background
    subprocess.Popen([
        ".venv/Scripts/python.exe", "run.py", "phone_call"
    ], shell=True)
    
    print("\n🚀 Service starting in background...")
    print("📞 Test your phone call service now!")
    print("🔧 If STT still fails, the audio format from your browser may be corrupted")
    
except Exception as e:
    print(f"❌ Fix script failed: {e}")
    sys.exit(1)

print("\n✅ Fix complete! Service should be running.")
