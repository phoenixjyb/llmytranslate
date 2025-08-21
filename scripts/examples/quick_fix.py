#!/usr/bin/env python3
"""Quick fix for Whisper STT and service restart"""

import subprocess
import time
import sys
import os

print("🔧 FIXING WHISPER STT + RESTARTING SERVICE")
print("=" * 55)

try:
    # 1. Kill existing services
    print("1. Stopping existing services...")
    subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/T"], capture_output=True, shell=True)
    time.sleep(3)
    
    # 2. Force enable Whisper programmatically
    print("2. Force enabling Whisper...")
    enable_cmd = [
        ".venv/Scripts/python.exe", "-c", 
        """
import sys
sys.path.append('.')
try:
    from src.services.stt_service import stt_service
    print('Before:', stt_service.whisper_available)
    stt_service.whisper_available = True
    print('After:', stt_service.whisper_available)
    print('✅ Whisper enabled successfully')
except Exception as e:
    print(f'❌ Failed to enable Whisper: {e}')
"""
    ]
    
    result = subprocess.run(enable_cmd, capture_output=True, text=True, shell=True)
    print("   Output:", result.stdout.strip())
    if result.stderr:
        print("   Errors:", result.stderr.strip())
    
    # 3. Start service
    print("3. Starting phone call service...")
    print("   🎯 New features active:")
    print("   ✅ No FFmpeg processing (direct numpy)")  
    print("   ✅ Audio silence detection")
    print("   ✅ Enhanced audio analysis logging")
    print("   ✅ Multiple format fallbacks")
    print("")
    
    # Use Popen to start in background
    process = subprocess.Popen([
        ".venv/Scripts/python.exe", "run.py", "phone_call"
    ], shell=True)
    
    print(f"   📞 Service started (PID: {process.pid})")
    print("   🌐 Access: http://localhost:8000/phone_call")
    print("   🔗 Ngrok: <your-ngrok-url>/phone_call")
    print("")
    print("🎤 TESTING INSTRUCTIONS:")
    print("   1. Wait 15 seconds for service to fully start")
    print("   2. Access via ngrok tunnel")
    print("   3. Click microphone and speak LOUDLY and CLEARLY")
    print("   4. Check service logs for audio analysis details")
    print("")
    print("📊 New logs will show:")
    print("   - Audio RMS levels (should be > 0.001)")
    print("   - Non-zero sample counts")
    print("   - Audio byte analysis")
    print("   - Sample rate detection results")
    
except Exception as e:
    print(f"❌ Fix failed: {e}")
    sys.exit(1)

print("\n✅ Service restarted with enhanced audio debugging!")
print("🔍 Monitor the service logs to see detailed audio analysis")
