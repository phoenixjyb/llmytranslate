#!/bin/bash
# Stop ngrok tunnel and cleanup

echo "🛑 Stopping ngrok tunnel..."

# Kill ngrok process if PID file exists
if [[ -f ".ngrok_pid" ]]; then
    NGROK_PID=$(cat .ngrok_pid)
    if kill "$NGROK_PID" 2>/dev/null; then
        echo "✅ Stopped ngrok process: $NGROK_PID"
    else
        echo "⚠️  Process $NGROK_PID not found (may have already stopped)"
    fi
    rm -f .ngrok_pid
fi

# Kill any remaining ngrok processes
pkill -f "ngrok http" 2>/dev/null && echo "✅ Cleaned up remaining ngrok processes" || true

# Cleanup files
rm -f .ngrok_url .ngrok_config ngrok.log

echo "🧹 Cleanup complete!"

# Show how to restart
echo ""
echo "📋 To restart ngrok:"
echo "   ./tools/scripts/setup_ngrok.sh"
