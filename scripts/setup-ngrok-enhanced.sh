#!/bin/bash
# Enhanced ngrok setup for LLMyTranslate Service Provider
#
# ⚠️  NOTE: This script is for the SERVICE PROVIDER side (LLMyTranslate project)
#          For CLIENT side configuration, use configure_remote_service.sh
#
# Usage: ./setup_ngrok.sh [port] [--domain custom-domain]

set -e

PORT=${1:-8080}
CUSTOM_DOMAIN=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            CUSTOM_DOMAIN="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [port] [--domain custom-domain]"
            echo "  port: Port number (default: 8080)"
            echo "  --domain: Custom ngrok domain (requires paid plan)"
            exit 0
            ;;
        *)
            if [[ $1 =~ ^[0-9]+$ ]]; then
                PORT="$1"
            fi
            shift
            ;;
    esac
done

echo "🚀 Setting up ngrok tunnel for LLMyTranslate service..."
echo "📍 Port: $PORT"
[[ -n "$CUSTOM_DOMAIN" ]] && echo "🌐 Custom domain: $CUSTOM_DOMAIN"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Install it first:"
    echo "   macOS: brew install ngrok"
    echo "   Linux: snap install ngrok"
    echo "   Or download from: https://ngrok.com/download"
    exit 1
fi

# Stop any existing ngrok processes
pkill -f "ngrok.*$PORT" 2>/dev/null || true
sleep 2

# Start ngrok tunnel
echo "📡 Starting ngrok tunnel..."
if [[ -n "$CUSTOM_DOMAIN" ]]; then
    ngrok http "$PORT" --domain="$CUSTOM_DOMAIN" --log=stdout > ngrok.log 2>&1 &
else
    ngrok http "$PORT" --log=stdout > ngrok.log 2>&1 &
fi

NGROK_PID=$!
echo "$NGROK_PID" > .ngrok_pid

# Wait for ngrok to start
echo "⏳ Waiting for ngrok to start..."
sleep 5

# Extract the public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url // empty' 2>/dev/null)

if [[ -n "$NGROK_URL" ]]; then
    echo ""
    echo "✅ ngrok tunnel is active!"
    echo "📍 Public URL: $NGROK_URL"
    echo "📍 Local URL: http://localhost:$PORT"
    echo ""
    echo "🔧 Update your translation script with:"
    echo "   export LLM_SERVICE_URL=\"$NGROK_URL\""
    echo ""
    echo "📋 To test the tunnel:"
    echo "   curl $NGROK_URL/api/health"
    echo ""
    echo "⚠️  ngrok Limitations:"
    echo "   • Free: URL changes each restart"
    echo "   • Free: 40 connections/minute"
    echo "   • Paid: Custom domains, more connections"
    echo ""
    echo "🛑 To stop: kill $NGROK_PID"
    echo "📊 Dashboard: http://localhost:4040"
    
    # Save tunnel info
    echo "$NGROK_URL" > .ngrok_url
    echo "$NGROK_PID" > .ngrok_pid
    
    cat > .ngrok_config << EOF
NGROK_URL=$NGROK_URL
NGROK_PID=$NGROK_PID
PORT=$PORT
STARTED=$(date)
EOF
else
    echo "❌ Failed to get ngrok URL"
    echo "📋 Check: tail -f ngrok.log"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi
