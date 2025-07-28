#!/bin/bash
# ================================================================================================
# Start LLM Translation Service with Tailscale Configuration
# ================================================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info "🚀 Starting LLM Translation Service with Tailscale"
echo "================================================="

# Check if Tailscale is connected
if tailscale status &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip -4)
    print_success "Tailscale connected - IP: $TAILSCALE_IP"
    
    # Use Tailscale configuration
    if [ -f ".env.tailscale" ]; then
        cp .env.tailscale .env
        print_success "Using Tailscale configuration"
    else
        print_warning "Tailscale config not found, using default"
    fi
else
    print_warning "Tailscale not connected. Service will only be available locally."
    print_info "Run ./scripts/setup-tailscale.sh to configure Tailscale access"
fi

# Start the service
print_info "Starting service..."
./scripts/start-service.sh --production

if [ ! -z "$TAILSCALE_IP" ]; then
    echo ""
    print_success "🌐 Service accessible via Tailscale at:"
    echo "   http://$TAILSCALE_IP:8000"
    echo "   http://$TAILSCALE_IP:8000/docs"
fi
