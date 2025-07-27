#!/bin/bash
# ================================================================================================
# Ngrok Quick Setup Script (Unix/Linux/macOS Version)
# Run this after getting your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
# ================================================================================================

# Parse command line arguments
AUTH_TOKEN=""
SKIP_WARNING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auth-token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        --skip-warning)
            SKIP_WARNING=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 --auth-token TOKEN [--skip-warning]"
            echo "  --auth-token TOKEN    Your ngrok auth token from dashboard"
            echo "  --skip-warning        Skip warning about auth token (use with caution)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --auth-token TOKEN [--skip-warning]"
            exit 1
            ;;
    esac
done

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${GREEN}🔐 Setting up ngrok authentication...${NC}"
echo -e "${CYAN}📦 Detecting ngrok installation${NC}"

# Check if ngrok is available
if ! command -v ngrok &> /dev/null; then
    print_error "Ngrok not found in PATH"
    print_warning "Please install ngrok first:"
    case "$OSTYPE" in
        darwin*)
            print_warning "  macOS: brew install ngrok"
            ;;
        linux*)
            print_warning "  Linux: Download from https://ngrok.com/download"
            print_warning "  Or use snap: sudo snap install ngrok"
            ;;
    esac
    exit 1
fi

NGROK_VERSION=$(ngrok version 2>/dev/null | head -1)
print_success "Found: $NGROK_VERSION"

# Check if auth token is provided
if [[ -z "$AUTH_TOKEN" ]] && [[ "$SKIP_WARNING" == "false" ]]; then
    print_error "Auth token is required"
    print_warning "Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    print_warning "Then run: $0 --auth-token YOUR_TOKEN"
    exit 1
fi

# Set auth token if provided
if [[ -n "$AUTH_TOKEN" ]]; then
    print_info "Configuring auth token..."
    if ngrok config add-authtoken "$AUTH_TOKEN" 2>/dev/null; then
        print_success "Auth token configured successfully!"
    else
        print_error "Failed to configure auth token"
        print_warning "Please check your token and try again"
        exit 1
    fi
fi

echo ""
print_info "🚇 Now starting ngrok tunnel..."
print_info "📋 Your translation service will be available at the ngrok URL"
print_info "🌐 Press Ctrl+C to stop the tunnel"
echo ""

# Start tunnel
exec ngrok http 8000
