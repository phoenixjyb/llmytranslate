#!/usr/bin/env python3
"""
GPU Acceleration Test Script for Samsung S24 Ultra
Tests if GPU acceleration can be properly configured for Ollama.
"""

import subprocess
import json
import sys
import os

def run_adb_command(command):
    """Run adb command and return output."""
    try:
        result = subprocess.run(['adb', 'shell'] + command.split(), 
                              capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return f"Error: {e}", False

def check_gpu_info():
    """Check GPU information from the device."""
    print("🎮 Checking GPU Information...")
    
    # Check GPU renderer
    gpu_info, success = run_adb_command("getprop ro.hardware.gpu")
    if success and gpu_info:
        print(f"GPU Hardware: {gpu_info}")
    
    # Check OpenGL renderer
    gl_renderer, success = run_adb_command("dumpsys SurfaceFlinger | grep GLES")
    if success and gl_renderer:
        print(f"OpenGL Info: {gl_renderer}")
    
    # Check Vulkan support
    vulkan_check, success = run_adb_command("pm list features | grep vulkan")
    if success and vulkan_check:
        print(f"Vulkan Support: {vulkan_check}")
    else:
        print("Vulkan: Not detected or not supported")
    
    # Check device model
    device_model, success = run_adb_command("getprop ro.product.model")
    if success:
        print(f"Device Model: {device_model}")
    
    return True

def check_termux_environment():
    """Check if Termux has the necessary environment for GPU acceleration."""
    print("\n🔧 Checking Termux Environment...")
    
    # Check if Termux is installed
    termux_check, success = run_adb_command("pm list packages | grep termux")
    if success and "com.termux" in termux_check:
        print("✅ Termux is installed")
    else:
        print("❌ Termux not found - install from F-Droid")
        return False
    
    # Check if Ollama is running
    ollama_check, success = run_adb_command("su -c 'ps aux | grep ollama'")
    if success and "ollama" in ollama_check:
        print("✅ Ollama process detected")
    else:
        print("⚠️ Ollama process not detected")
    
    return True

def generate_gpu_optimization_script():
    """Generate optimized Termux script for GPU acceleration."""
    script_content = """#!/data/data/com.termux/files/usr/bin/bash

# GPU Acceleration Setup for Samsung S24 Ultra
# Optimized for Adreno 750 GPU

echo "🎮 Setting up GPU acceleration for Ollama..."

# Set GPU environment variables
export OLLAMA_GPU=1
export OLLAMA_GPU_LAYERS=-1
export OLLAMA_VULKAN=1
export OLLAMA_FLOAT16=1
export OLLAMA_GPU_MEMORY=4GB
export OLLAMA_MAX_LOADED_MODELS=1

# Adreno-specific optimizations
export ADRENO_GPU_MEMORY_OPTIMIZATION=true
export ADRENO_SHADER_OPTIMIZATION=true
export VULKAN_MEMORY_BUDGET=3072
export GPU_THREAD_COUNT=8

# Kill existing Ollama processes
echo "🔄 Stopping existing Ollama processes..."
pkill -f ollama

# Wait for clean shutdown
sleep 2

# Start Ollama with GPU acceleration
echo "🚀 Starting Ollama with GPU acceleration..."
ollama serve &

# Wait for Ollama to start
sleep 5

# Check if Ollama is running with GPU
echo "🔍 Checking Ollama status..."
if pgrep -f ollama > /dev/null; then
    echo "✅ Ollama is running"
    
    # Test GPU acceleration with a simple request
    echo "🧪 Testing GPU acceleration..."
    curl -s http://localhost:11434/api/generate \\
        -d '{"model": "qwen2:0.5b", "prompt": "Test GPU", "stream": false}' \\
        --max-time 30 | jq '.response // "No response"'
    
    echo "📊 GPU optimization complete!"
    echo "💡 Try these optimized models:"
    echo "  • ollama pull qwen2:0.5b    # 350MB, fastest"
    echo "  • ollama pull phi3:mini     # 1.3GB, balanced"
    echo "  • ollama pull gemma2:2b     # 1.6GB, quality"
    
else
    echo "❌ Ollama failed to start"
    echo "🔧 Fallback to CPU mode..."
    export OLLAMA_GPU=0
    export OLLAMA_CPU_THREADS=4
    ollama serve &
fi
"""
    
    # Write script to local file for transfer to device
    with open('termux_gpu_setup.sh', 'w') as f:
        f.write(script_content)
    
    print(f"\n📝 Generated GPU optimization script: termux_gpu_setup.sh")
    print("📱 To install on device:")
    print("  adb push termux_gpu_setup.sh /sdcard/")
    print("  adb shell")
    print("  su")
    print("  cp /sdcard/termux_gpu_setup.sh /data/data/com.termux/files/home/")
    print("  chmod +x /data/data/com.termux/files/home/termux_gpu_setup.sh")
    print("  /data/data/com.termux/files/home/termux_gpu_setup.sh")

def main():
    print("🔍 Samsung S24 Ultra GPU Acceleration Test")
    print("=" * 50)
    
    # Check if adb is available
    try:
        subprocess.run(['adb', 'devices'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ADB not found or no device connected")
        print("📱 Connect your Samsung S24 Ultra and enable USB debugging")
        return 1
    
    # Check device connection
    devices_output = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    if 'device' not in devices_output.stdout:
        print("❌ No device detected")
        print("📱 Connect your Samsung S24 Ultra via USB")
        return 1
    
    print("✅ Device connected")
    
    # Run diagnostics
    check_gpu_info()
    check_termux_environment()
    generate_gpu_optimization_script()
    
    print("\n🎯 Next Steps:")
    print("1. Install the generated script on your device")
    print("2. Run it in Termux to enable GPU acceleration")
    print("3. Test with the LLMyTranslate app")
    print("4. Monitor performance improvements")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
