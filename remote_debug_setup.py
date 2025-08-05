#!/usr/bin/env python3
"""
Remote Debugging Setup for LLmyTranslate Phone Call Service
Provides ngrok URLs and debugging instructions
"""

import requests
import json
import subprocess
import sys
import time

def get_ngrok_tunnels():
    """Get active ngrok tunnels"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            return tunnels.get("tunnels", [])
    except Exception as e:
        print(f"❌ Could not connect to ngrok API: {e}")
        print("🔧 Make sure ngrok is running: ngrok http 8000")
    return []

def display_debug_info():
    """Display comprehensive debugging information"""
    print("=" * 80)
    print("🔍 REMOTE DEBUGGING SETUP FOR AUDIO CHUNKS")
    print("=" * 80)
    
    # Check local service
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Local service is running on http://localhost:8000")
        else:
            print("❌ Local service not responding")
            return
    except:
        print("❌ Local service not accessible")
        return
    
    # Get ngrok tunnels
    tunnels = get_ngrok_tunnels()
    
    if tunnels:
        print("\n🌐 NGROK TUNNELS DETECTED:")
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                public_url = tunnel.get("public_url")
                print(f"   📱 Phone Call Interface: {public_url}/web/phone-call.html")
                print(f"   🔌 WebSocket Endpoint: {public_url.replace('https:', 'wss:')}/api/phone/stream")
                
                # Test the tunnel
                try:
                    test_response = requests.get(f"{public_url}/api/health", timeout=10)
                    if test_response.status_code == 200:
                        print(f"   ✅ Tunnel is working!")
                    else:
                        print(f"   ⚠️ Tunnel responds but service may have issues")
                except:
                    print(f"   ❌ Tunnel not accessible")
    else:
        print("\n❌ No ngrok tunnels detected")
        print("🔧 Start ngrok: ngrok http 8000")
        return
    
    print("\n🧪 DEBUGGING INSTRUCTIONS:")
    print("1. Open the phone call interface in your browser")
    print("2. Open Browser Developer Tools (F12)")
    print("3. Go to Console tab")
    print("4. Test audio chunks by running: testAudioChunks()")
    print("5. Or make a real phone call and watch the console logs")
    
    print("\n🔍 WHAT TO LOOK FOR:")
    print("   📦 'Received audio chunk X/Y' messages")
    print("   🎵 'All chunks received! Combining audio...' message")
    print("   ✅ 'Audio playback started successfully' message")
    print("   ❌ Any error messages in red")
    
    print("\n🚨 COMMON ISSUES TO CHECK:")
    print("   • Base64 decoding errors")
    print("   • Audio element creation failures")
    print("   • Browser audio permissions")
    print("   • WebSocket connection drops")
    
    print("\n📊 DEBUG COMMANDS (in browser console):")
    print("   testAudioChunks()           - Test chunked audio delivery")
    print("   window.phoneCallManager     - Access the manager object")
    print("   console.clear()             - Clear console for clean testing")
    
    print("\n" + "=" * 80)

def run_ngrok_if_needed():
    """Check if ngrok is running, offer to start it"""
    tunnels = get_ngrok_tunnels()
    if not tunnels:
        print("🔧 ngrok not detected. Do you want to start it? (y/n): ", end="")
        choice = input().lower().strip()
        if choice in ['y', 'yes']:
            print("🚀 Starting ngrok...")
            try:
                # Start ngrok in background
                subprocess.Popen(["ngrok", "http", "8000"], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print("⏳ Waiting for ngrok to initialize...")
                time.sleep(3)
                
                # Check again
                tunnels = get_ngrok_tunnels()
                if tunnels:
                    print("✅ ngrok started successfully!")
                else:
                    print("❌ ngrok failed to start")
            except FileNotFoundError:
                print("❌ ngrok not found in PATH")
                print("🔧 Install ngrok: https://ngrok.com/download")

if __name__ == "__main__":
    run_ngrok_if_needed()
    display_debug_info()
