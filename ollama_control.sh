#!/data/data/com.termux/files/usr/bin/bash

# Quick Ollama Status and Control Script
# For Samsung S24 Ultra with GPU acceleration

case "$1" in
    "start")
        echo "🚀 Starting Ollama with GPU acceleration..."
        if ! pgrep -f "ollama serve" > /dev/null; then
            ollama serve > ~/.ollama.log 2>&1 &
            sleep 3
            if pgrep -f "ollama serve" > /dev/null; then
                echo "✅ Ollama started successfully"
            else
                echo "❌ Failed to start Ollama"
            fi
        else
            echo "ℹ️ Ollama is already running"
        fi
        ;;
    
    "stop")
        echo "🛑 Stopping Ollama..."
        pkill -f ollama
        sleep 2
        if ! pgrep -f "ollama serve" > /dev/null; then
            echo "✅ Ollama stopped"
        else
            echo "⚠️ Some Ollama processes may still be running"
        fi
        ;;
    
    "restart")
        echo "🔄 Restarting Ollama..."
        pkill -f ollama
        sleep 2
        ollama serve > ~/.ollama.log 2>&1 &
        sleep 3
        if pgrep -f "ollama serve" > /dev/null; then
            echo "✅ Ollama restarted successfully"
        else
            echo "❌ Failed to restart Ollama"
        fi
        ;;
    
    "status")
        echo "📊 Ollama Status Check:"
        if pgrep -f "ollama serve" > /dev/null; then
            echo "  ✅ Status: RUNNING"
            echo "  🎮 GPU: $(echo $OLLAMA_GPU | sed 's/1/ENABLED/g' | sed 's/0/DISABLED/g')"
            echo "  🧠 GPU Layers: $OLLAMA_GPU_LAYERS"
            echo "  💾 GPU Memory: $OLLAMA_GPU_MEMORY"
            echo "  🔥 Vulkan: $(echo $OLLAMA_VULKAN | sed 's/1/ENABLED/g' | sed 's/0/DISABLED/g')"
            
            # Test connectivity
            if curl -s http://localhost:11434/api/tags > /dev/null; then
                echo "  🌐 API: RESPONSIVE"
                echo "  📋 Available models:"
                curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*' | cut -d'"' -f4 | sed 's/^/    • /'
            else
                echo "  ⚠️ API: NOT RESPONSIVE"
            fi
        else
            echo "  ❌ Status: NOT RUNNING"
        fi
        
        echo ""
        echo "  📁 Log file: ~/.ollama.log"
        if [ -f ~/.ollama.log ]; then
            echo "  📜 Recent log entries:"
            tail -n 3 ~/.ollama.log | sed 's/^/    /'
        fi
        ;;
    
    "logs")
        echo "📋 Ollama Logs (last 20 lines):"
        echo "================================"
        if [ -f ~/.ollama.log ]; then
            tail -n 20 ~/.ollama.log
        else
            echo "No log file found at ~/.ollama.log"
        fi
        ;;
    
    "models")
        echo "🧠 Available Models:"
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*' | cut -d'"' -f4 | sed 's/^/  • /'
        else
            echo "❌ Cannot connect to Ollama API"
        fi
        ;;
    
    *)
        echo "🎮 Ollama GPU Control Script for Samsung S24 Ultra"
        echo "=================================================="
        echo "Usage: $0 {start|stop|restart|status|logs|models}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Ollama with GPU acceleration"
        echo "  stop    - Stop Ollama"
        echo "  restart - Restart Ollama"
        echo "  status  - Show detailed status and configuration"
        echo "  logs    - Show recent Ollama logs"
        echo "  models  - List available models"
        echo ""
        echo "Quick status check:"
        if pgrep -f "ollama serve" > /dev/null; then
            echo "  ✅ Ollama is currently RUNNING"
        else
            echo "  ❌ Ollama is currently NOT RUNNING"
        fi
        ;;
esac
