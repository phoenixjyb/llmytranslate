#!/usr/bin/env python3
"""Simple service restart with fixes"""

import subprocess
import time
import sys

print("🔧 RESTARTING PHONE CALL SERVICE WITH AUDIO FIXES")
print("=" * 60)

try:
    # 1. Stop existing services
    print("1. Stopping existing Python services...")
    subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/T"], 
                  capture_output=True, shell=True)
    time.sleep(3)
    
    # 2. Start the service
    print("2. Starting phone call service...")
    print("   🎯 Key improvements applied:")
    print("   ✅ Direct numpy audio processing (no FFmpeg for raw data)")
    print("   ✅ Multiple sample rate detection (16kHz, 44.1kHz, 48kHz, 8kHz)")
    print("   ✅ 8-bit and 16-bit audio format support")
    print("   ✅ Whisper direct array processing (no temp files)")
    print("   ✅ Overlapping response prevention")
    print("")
    
    # Start service in background
    process = subprocess.Popen([
        ".venv/Scripts/python.exe", "run.py", "phone_call"
    ], shell=True)
    
    print(f"   📞 Service starting (PID: {process.pid})")
    print("   🌐 Service URL: http://localhost:8000/phone_call")
    print("   🔗 Use your ngrok tunnel for remote access")
    print("")
    print("🚀 Service is starting...")
    print("   ⏳ Give it 10-15 seconds to fully initialize")
    print("   🎤 Then test speaking into your microphone")
    print("   📝 Audio should now be properly transcribed!")
    
except Exception as e:
    print(f"❌ Restart failed: {e}")
    sys.exit(1)

print("\n✅ Service restart initiated!")
print("💡 If STT still fails, check browser microphone permissions")
