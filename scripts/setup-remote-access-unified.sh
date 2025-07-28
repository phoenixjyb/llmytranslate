#!/bin/bash
# ================================================================================================
# Unified Remote Access Setup Script for LLM Translation Service
# This script combines and enhances existing remote access options
# Usage: ./setup_remote_access_unified.sh [tailscale|ngrok|local|info]
# ================================================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
DEFAULT_PORT=8000
PORT=${PORT:-$DEFAULT_PORT}

# Parse command line arguments
MODE="info"
if [[ $# -gt 0 ]]; then
    case "$1" in
        tailscale|ngrok|local|info)
            MODE="$1"
            ;;
        -h|--help)
            echo "Usage: $0 [tailscale|ngrok|local|info]"
            echo "Modes:"
            echo "  info      - Show available setup modes (default)"
            echo "  local     - Get local network access info"
            echo "  tailscale - Set up Tailscale VPN for secure private access"
            echo "  ngrok     - Set up ngrok tunnel for public internet access"
            echo ""
            echo "Environment variables:"
            echo "  PORT      - Service port (default: 8888)"
            exit 0
            ;;
        *)
            print_error "Unknown mode: $1"
            print_info "Run with --help for usage information"
            exit 1
            ;;
    esac
fi

show_info() {
    echo "🔧 LLMyTranslate Remote Access Setup"
    echo "===================================="
    echo ""
    print_info "Available remote access methods:"
    echo ""
    echo "🔒 Tailscale (Recommended for regular use)"
    echo "   ✅ Private & secure VPN"
    echo "   ✅ Stable IP addresses"
    echo "   ✅ Fast direct connections"
    echo "   ✅ Free for personal use"
    echo "   ❌ Requires client installation"
    echo "   Usage: $0 tailscale"
    echo ""
    echo "🌍 ngrok (Good for quick sharing)"
    echo "   ✅ Public internet access"
    echo "   ✅ No client setup needed"
    echo "   ✅ Great for demos"
    echo "   ❌ URLs change on restart"
    echo "   ❌ Connection limits"
    echo "   Usage: $0 ngrok"
    echo ""
    echo "🏠 Local Network"
    echo "   ✅ Simple setup"
    echo "   ✅ Fast local connections"
    echo "   ❌ Same network only"
    echo "   Usage: $0 local"
    echo ""
    print_info "Service port: $PORT"
}

setup_local() {
    print_info "Setting up local network access..."
    
    # Get local IP addresses
    LOCAL_IPS=$(hostname -I 2>/dev/null || ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | awk '{print $2}' | head -3)
    
    echo ""
    print_success "Local network access configured!"
    echo ""
    echo "📍 Access URLs:"
    echo "   Localhost: http://localhost:$PORT"
    echo "   Local IPs:"
    for ip in $LOCAL_IPS; do
        echo "     http://$ip:$PORT"
    done
    echo ""
    echo "🔧 Client Configuration:"
    echo "   Set LLM_SERVICE_URL=http://localhost:$PORT"
    echo "   Or use any of the local IP addresses above"
}

setup_tailscale() {
    print_info "Setting up Tailscale VPN access..."
    
    # Use the dedicated Tailscale script
    if [[ -f "scripts/setup_tailscale.sh" ]]; then
        chmod +x scripts/setup_tailscale.sh
        ./scripts/setup_tailscale.sh --port "$PORT"
    else
        print_error "Tailscale setup script not found at scripts/setup_tailscale.sh"
        exit 1
    fi
}

setup_ngrok() {
    print_info "Setting up ngrok tunnel access..."
    
    # Use the enhanced ngrok script
    if [[ -f "scripts/setup-ngrok-enhanced.sh" ]]; then
        chmod +x scripts/setup-ngrok-enhanced.sh
        ./scripts/setup-ngrok-enhanced.sh "$PORT"
    elif [[ -f "scripts/setup-ngrok.sh" ]]; then
        chmod +x scripts/setup-ngrok.sh
        ./scripts/setup-ngrok.sh
    else
        print_error "ngrok setup script not found"
        exit 1
    fi
}

# Main execution
case $MODE in
    info)
        show_info
        ;;
    local)
        setup_local
        ;;
    tailscale)
        setup_tailscale
        ;;
    ngrok)
        setup_ngrok
        ;;
esac

if [[ $MODE != "info" ]]; then
    echo ""
    print_info "🔗 For client configuration, see the systemDesign project:"
    print_info "   Run: ./tools/scripts/configure_remote_service.sh"
fi
