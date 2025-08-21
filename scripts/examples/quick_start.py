#!/usr/bin/env python3
"""Quick start script for phone call service with improvements"""

import subprocess
import sys
import os

def start_service():
    """Start the phone call service with the improvements"""
    
    print("🚀 Starting Phone Call Service with Anti-Overlap Improvements...")
    print("=" * 60)
    
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Use the virtual environment Python
    python_exe = "C:/Users/yanbo/wSpace/llmytranslate/.venv/Scripts/python.exe"
    
    try:
        print("✅ Starting service...")
        print(f"📁 Project directory: {project_dir}")
        print(f"🐍 Python executable: {python_exe}")
        print("")
        print("🎯 Key improvements active:")
        print("   - Processing locks prevent overlapping responses")
        print("   - Audio queuing for smoother experience")
        print("   - Enhanced noise cancellation")
        print("   - Faster response times")
        print("")
        print("🌐 Service will be available at:")
        print("   - Local: http://localhost:8000")
        print("   - Phone call: http://localhost:8000/phone-call")
        print("")
        print("Press Ctrl+C to stop the service")
        print("=" * 60)
        
        # Start the service
        subprocess.run([python_exe, "run.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start service: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_service()
