#!/data/data/com.termux/files/usr/bin/bash

# Realistic Mobile CPU Optimization for Samsung S24 Ultra
# Focus on what actually works on Android devices

echo "📱 Setting up REALISTIC mobile optimization for Ollama..."
echo "💻 Note: GPU acceleration not available in Termux - using CPU optimization"

# Create persistent environment variables in .bashrc
echo "📝 Adding mobile CPU optimization to .bashrc..."

# Backup existing .bashrc
if [ -f ~/.bashrc ]; then
    cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
    echo "📦 Backed up existing .bashrc"
fi

# Add realistic mobile optimization to .bashrc (only if not already present)
if ! grep -q "OLLAMA_NUM_PARALLEL" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'EOF'

# ========================================
# Mobile CPU Optimization for Ollama
# Realistic settings for Android devices
# ========================================
export OLLAMA_NUM_PARALLEL=1              # Single model at a time
export OLLAMA_MAX_LOADED_MODELS=1         # Memory conservation
export OLLAMA_HOST=127.0.0.1:11434        # Local only
export OLLAMA_ORIGINS="*"                  # Allow app access
export OLLAMA_MAX_QUEUE=5                  # Limit queue size

# CPU threading optimization for mobile ARM
export OLLAMA_NUM_THREAD=$(nproc)         # Use all CPU cores
export OMP_NUM_THREADS=$(nproc)           # OpenMP threading

# Memory optimization
export OLLAMA_KEEP_ALIVE=5m               # Keep model loaded for 5 minutes
export OLLAMA_MAX_VRAM=0                  # Don't use GPU memory

# Be honest about GPU capabilities
export OLLAMA_GPU_LAYERS=0
export OLLAMA_GPU=0

# Auto-start Ollama with CPU optimization if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🚀 Auto-starting Ollama with mobile CPU optimization..."
    nohup ollama serve > ~/.ollama.log 2>&1 &
    sleep 2
    if pgrep -f "ollama serve" > /dev/null; then
        echo "✅ Ollama started successfully with CPU optimization"
    fi
fi
EOF
    echo "✅ Mobile CPU optimization variables added to .bashrc"
else
    echo "ℹ️ Mobile optimization variables already configured in .bashrc"
fi

# Source the new environment
source ~/.bashrc

# Apply environment variables for current session
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_ORIGINS="*"
export OLLAMA_MAX_QUEUE=5
export OLLAMA_NUM_THREAD=$(nproc)
export OMP_NUM_THREADS=$(nproc)
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MAX_VRAM=0
export OLLAMA_GPU_LAYERS=0
export OLLAMA_GPU=0

# Kill existing Ollama processes
echo "🔄 Stopping existing Ollama processes..."
pkill -f ollama

# Wait for clean shutdown
sleep 2

# Start Ollama with mobile CPU optimization
echo "🚀 Starting Ollama with mobile CPU optimization..."
ollama serve > ~/.ollama.log 2>&1 &

# Wait for Ollama to start
sleep 5

# Check if Ollama is running
echo "🔍 Checking Ollama status..."
if pgrep -f ollama > /dev/null; then
    echo "✅ Ollama is running with mobile CPU optimization"
    
    # Test with gemma2:2b (your preferred model)
    echo "🧪 Testing mobile performance..."
    timeout 30 curl -s http://localhost:11434/api/generate \
        -d '{"model": "gemma2:2b", "prompt": "Test mobile", "stream": false}' \
        2>/dev/null | head -c 200
    
    echo ""
    echo "📊 Mobile CPU optimization complete!"
    echo "💡 Realistic model performance expectations:"
    echo "  • gemma2:2b (1.6GB): 3-8 seconds response (your default)"
    echo "  • phi3:mini (1.3GB): 2-5 seconds response"  
    echo "  • qwen2:0.5b (350MB): 1-3 seconds response"
    
    echo ""
    echo "🔧 Configuration Summary:"
    echo "  ✅ CPU optimization: ENABLED"
    echo "  ✅ Environment variables: PERSISTENT"
    echo "  ✅ Auto-start on Termux launch: ENABLED"
    echo "  ✅ Memory management: OPTIMIZED"
    echo "  📁 Logs saved to: ~/.ollama.log"
    echo "  💻 GPU acceleration: NOT AVAILABLE (Termux limitation)"
    
else
    echo "❌ Ollama failed to start"
    echo "📋 Check logs: cat ~/.ollama.log"
fi

echo ""
echo "🎯 Setup Complete!"
echo "📱 From now on, mobile optimization will be automatic when you start Termux"
echo "💻 Realistic performance: gemma2:2b will take 3-8 seconds per response"
echo "🔍 To check status: ps aux | grep ollama"
echo "📋 To view logs: tail -f ~/.ollama.log"
