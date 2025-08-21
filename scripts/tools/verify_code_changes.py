#!/usr/bin/env python3
"""Verify that our WebM handling code changes are in place"""

import os

def check_phone_call_code():
    """Check if our new WebM handling code is in the phone_call.py file"""
    file_path = "src/api/routes/phone_call.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for our new debug messages
    checks = [
        "🔍 Current chunk WebM check:",
        "🎯 Current chunk is WebM container - using intelligent WebM handling",
        "🎯 Final audio format for STT:",
        "📊 Accumulated:",
        "✅ Single WebM container detected"
    ]
    
    print("🔍 Checking for new WebM handling code...")
    
    all_found = True
    for check in checks:
        if check in content:
            print(f"✅ Found: {check}")
        else:
            print(f"❌ Missing: {check}")
            all_found = False
    
    # Check that old conflicting code is removed
    if "No audio format magic bytes detected, treating as raw PCM" in content:
        print("❌ Old conflicting format detection still present!")
        all_found = False
    else:
        print("✅ Old conflicting format detection removed")
    
    return all_found

if __name__ == "__main__":
    print("🔧 Verifying WebM handling code changes...")
    print("=" * 50)
    
    success = check_phone_call_code()
    
    print("=" * 50)
    if success:
        print("🎉 All code changes are in place!")
        print("💡 If the service is still showing old behavior, try restarting it.")
    else:
        print("❌ Some code changes are missing or incomplete.")
        
    print("\n🚀 To restart the service manually:")
    print("   1. Press Ctrl+C to stop current service")
    print("   2. Run: .\\start-service.ps1")
