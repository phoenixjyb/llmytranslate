#!/bin/bash
# ================================================================================================
# Tailscale Setup Script for LLM Translation Service
# Configures and starts the service for Tailscale network access
# ================================================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info "🚀 Setting up LLM Translation Service for Tailscale"
echo "================================================="

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    print_error "Tailscale is not installed. Please install it first:"
    echo "  brew install tailscale"
    echo "  Or download from: https://tailscale.com/download"
    exit 1
fi

print_success "Tailscale is installed"

# Check if Tailscale is running
if ! tailscale status &> /dev/null; then
    print_warning "Tailscale is not running. Starting it now..."
    
    print_info "Starting Tailscale daemon..."
    # Try to start Tailscale service
    if command -v brew &> /dev/null; then
        sudo brew services start tailscale || {
            print_warning "Failed to start via brew, trying direct approach..."
            sudo /opt/homebrew/bin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
        }
    else
        sudo tailscaled &
    fi
    
    sleep 3
    
    print_info "Connecting to Tailscale network..."
    print_warning "This will open a browser window for authentication"
    tailscale up --accept-routes
    
    print_success "Connected to Tailscale network"
else
    print_success "Tailscale is already running"
fi

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
if [ -z "$TAILSCALE_IP" ]; then
    print_error "Failed to get Tailscale IP address"
    exit 1
fi

print_success "Tailscale IP: $TAILSCALE_IP"

# Copy Tailscale environment configuration
print_info "Setting up Tailscale configuration..."
cp .env.tailscale .env
print_success "Tailscale environment configured"

# Start the service
print_info "Starting LLM Translation Service..."
./scripts/start-service.sh --production

echo ""
print_success "🌐 Service is now accessible via Tailscale!"
echo "================================================="
echo ""
echo "📱 Access URLs:"
echo "   http://$TAILSCALE_IP:8000"
echo "   http://$(tailscale status --self=false --peers=false | head -1 | awk '{print $2}'):8000"
echo ""
echo "📚 API Documentation:"
echo "   http://$TAILSCALE_IP:8000/docs"
echo ""
echo "🔧 Environment Variables for other applications:"
echo "   export LLM_SERVICE_URL=\"http://$TAILSCALE_IP:8000\""
echo "   export LLM_APP_ID=\"demo_app_id\""
echo "   export LLM_APP_SECRET=\"demo_app_secret\""
echo ""
echo "🛠️  Management:"
echo "   Stop: Ctrl+C or ./scripts/stop-service.sh"
echo "   Logs: Check terminal output"
echo ""
print_success "Setup complete!"
