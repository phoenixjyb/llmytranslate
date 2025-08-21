#!/data/data/com.termux/files/usr/bin/bash

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
echo "  • Use models optimized for mobile (phi3:mini, qwen2:0.5b)"

# Start Ollama with realistic settings
echo "🚀 Starting Ollama with mobile optimization..."
ollama serve > ~/.ollama.log 2>&1 &

sleep 5

if pgrep -f ollama > /dev/null; then
    echo "✅ Ollama started successfully (CPU mode)"
    echo "📊 Testing with mobile-optimized model..."
    
    # Test with a realistic model
    curl -s http://localhost:11434/api/generate \
        -d '{"model": "phi3:mini", "prompt": "Hello", "stream": false}' \
        --max-time 30
else
    echo "❌ Ollama failed to start"
fi
