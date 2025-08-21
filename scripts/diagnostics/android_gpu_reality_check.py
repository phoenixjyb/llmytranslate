#!/usr/bin/env python3
"""
Android GPU Acceleration Reality Check for Ollama
Investigates the actual feasibility of GPU acceleration in Termux on Android
"""

import subprocess
import json
import sys

def check_ollama_gpu_support():
    """Check what GPU acceleration Ollama actually supports on Android."""
    print("🔍 Investigating Ollama GPU Support on Android...")
    print("=" * 60)
    
    # Check if device supports GPU compute
    print("📱 Device GPU Capabilities:")
    
    # Check OpenCL support
    opencl_check, success = run_adb_command("find /system -name '*OpenCL*' 2>/dev/null")
    if success and opencl_check:
        print(f"  OpenCL libraries: {opencl_check}")
    else:
        print("  ❌ OpenCL: Not found in system")
    
    # Check Vulkan compute
    vulkan_check, success = run_adb_command("pm list features | grep vulkan")
    if success and vulkan_check:
        print(f"  ✅ Vulkan: {vulkan_check}")
    else:
        print("  ❌ Vulkan: Not supported")
    
    # Check if Termux has access to GPU
    print("\n🔧 Termux GPU Access:")
    termux_gpu, success = run_adb_command("su -c 'ls -la /dev/dri /dev/mali* /dev/kgsl* 2>/dev/null'")
    if success and termux_gpu:
        print(f"  GPU device nodes: {termux_gpu}")
    else:
        print("  ❌ No GPU device nodes accessible to Termux")
    
    # Check Ollama build info
    print("\n📦 Ollama Build Information:")
    print("  Ollama on Android/ARM64 typically:")
    print("  • Built for CPU inference (ARM64)")
    print("  • No GPU acceleration in standard builds")
    print("  • Requires specific GPU libraries not available in Termux")

def check_android_gpu_reality():
    """Check the reality of GPU acceleration on Android."""
    print("\n🎮 Android GPU Acceleration Reality:")
    print("=" * 50)
    
    print("❌ Major Limitations:")
    print("  1. Termux runs in userspace without GPU driver access")
    print("  2. Android sandboxing prevents direct GPU access")
    print("  3. Ollama binaries don't include Android GPU support")
    print("  4. CUDA not available on mobile ARM GPUs")
    print("  5. OpenCL/Vulkan compute requires root + custom drivers")
    
    print("\n✅ What Actually Works:")
    print("  1. CPU optimization (NEON instructions)")
    print("  2. Memory optimization")
    print("  3. Threading optimization")
    print("  4. Model quantization")
    
    print("\n🔬 Alternative Approaches:")
    print("  1. Use smaller, quantized models")
    print("  2. Optimize CPU performance instead")
    print("  3. Use cloud GPU inference")
    print("  4. Use Android-native ML frameworks (TensorFlow Lite)")

def run_adb_command(command):
    """Run adb command and return output."""
    try:
        result = subprocess.run(['adb', 'shell'] + command.split(), 
                              capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return f"Error: {e}", False

def generate_realistic_optimization():
    """Generate realistic optimization recommendations."""
    print("\n🚀 Realistic Performance Optimization:")
    print("=" * 50)
    
    optimization_script = """#!/data/data/com.termux/files/usr/bin/bash

# Realistic CPU Optimization for Ollama on Android
# Focus on what actually works on mobile devices

echo "🔧 Applying realistic mobile optimizations..."

# CPU optimization (what actually works)
export OLLAMA_NUM_PARALLEL=1          # Single model at a time
export OLLAMA_MAX_LOADED_MODELS=1     # Memory conservation
export OLLAMA_HOST=127.0.0.1:11434    # Local only
export OLLAMA_ORIGINS="*"              # Allow app access
export OLLAMA_MAX_QUEUE=5              # Limit queue size

# CPU threading optimization for mobile ARM
export OLLAMA_NUM_THREAD=$(nproc)     # Use all CPU cores
export OMP_NUM_THREADS=$(nproc)       # OpenMP threading

# Memory optimization
export OLLAMA_KEEP_ALIVE=5m           # Keep model loaded for 5 minutes
export OLLAMA_MAX_VRAM=0              # Don't try to use GPU memory

# Disable GPU attempts (be honest about capabilities)
export OLLAMA_GPU_LAYERS=0
export OLLAMA_GPU=0

echo "✅ Mobile CPU optimization complete"
echo "💡 For best performance:"
echo "  • Use quantized models (Q4 or Q8)"
echo "  • Keep models under 1GB for smooth performance"
echo "  • Close other apps to free memory"
echo "  • Use models optimized for mobile (gemma2:270m, phi3:mini, qwen2:0.5b)"

# Start Ollama with realistic settings
echo "🚀 Starting Ollama with mobile optimization..."
ollama serve > ~/.ollama.log 2>&1 &

sleep 5

if pgrep -f ollama > /dev/null; then
    echo "✅ Ollama started successfully (CPU mode)"
    echo "📊 Testing with mobile-optimized model..."
    
    # Test with a realistic model
    curl -s http://localhost:11434/api/generate \\
        -d '{"model": "gemma2:270m", "prompt": "Hello", "stream": false}' \\
        --max-time 30
else
    echo "❌ Ollama failed to start"
fi
"""
    
    with open('realistic_mobile_optimization.sh', 'w') as f:
        f.write(optimization_script)
    
    print("📝 Generated realistic optimization script: realistic_mobile_optimization.sh")

def main():
    print("🔍 Android GPU Acceleration Reality Check")
    print("Investigating Ollama GPU support on Android devices")
    print("=" * 60)
    
    check_ollama_gpu_support()
    check_android_gpu_reality()
    generate_realistic_optimization()
    
    print("\n🎯 Honest Conclusion:")
    print("=" * 30)
    print("❌ GPU acceleration for Ollama in Termux is NOT reliably available")
    print("✅ Focus on CPU optimization and smaller models instead")
    print("🚀 Expected realistic performance:")
    print("  • gemma2:270m (270MB): 0.5-2 seconds response (FASTEST)")
    print("  • phi3:mini (1.3GB): 2-5 seconds response")
    print("  • qwen2:0.5b (350MB): 1-3 seconds response")
    print("  • gemma2:2b (1.6GB): 3-8 seconds response")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
