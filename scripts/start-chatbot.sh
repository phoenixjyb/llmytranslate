#!/bin/bash
# ================================================================================================
# Cross-Platform Chatbot Service Starter - Unix Edition (Linux/macOS)
# Extends existing translation service with chatbot functionality
# Provides full cross-platform support with Unix optimizations
# ================================================================================================

set -e

# Default values
CHAT_ONLY=false
PRODUCTION=false
DEBUG=false
WITH_NGROK=false
WITH_TAILSCALE=false
FORCE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Usage function
usage() {
    echo "🤖 LLM Chatbot Service - Unix Edition"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --chat-only         Start only chatbot service on port 8001"
    echo "  --production        Run in production mode with optimizations"
    echo "  --debug             Run in debug mode with verbose logging"
    echo "  --with-ngrok        Enable Ngrok tunnel for public access"
    echo "  --with-tailscale    Enable Tailscale VPN access"
    echo "  --force             Force restart if service is running"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --production --with-tailscale"
    echo "  $0 --chat-only --debug"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --chat-only)
            CHAT_ONLY=true
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --with-ngrok)
            WITH_NGROK=true
            shift
            ;;
        --with-tailscale)
            WITH_TAILSCALE=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            usage
            ;;
    esac
done

echo -e "${CYAN}🤖 LLM Chatbot Service - Unix Edition${NC}"
echo -e "${CYAN}======================================${NC}"

# Platform detection
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
if [[ "$PLATFORM" == "darwin" ]]; then
    PLATFORM_DISPLAY="macOS $(sw_vers -productVersion 2>/dev/null || echo 'Unknown')"
elif [[ "$PLATFORM" == "linux" ]]; then
    PLATFORM_DISPLAY="Linux $(uname -r)"
else
    PLATFORM_DISPLAY="Unix-like ($(uname -s))"
fi

echo -e "${YELLOW}Platform: $PLATFORM_DISPLAY${NC}"

# Logging function
log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Environment variable conflict resolution
resolve_environment_conflicts() {
    log_info "Resolving environment variable conflicts..."
    
    local conflict_patterns=("OLLAMA" "REDIS" "DATABASE" "AUTH" "API" "CHATBOT")
    
    for pattern in "${conflict_patterns[@]}"; do
        # Check for exact matches and variations
        for var_name in $(env | grep -E "^${pattern}(_|$|=)" | cut -d= -f1 2>/dev/null || true); do
            if [[ -n "$var_name" ]]; then
                log_warning "Temporarily removing conflicting variable: $var_name"
                unset "$var_name"
            fi
        done
    done
}

# Cross-platform Python executable detection
get_python_executable() {
    local python_execs=(
        "./.venv/bin/python"
        "./.venv/bin/python3"
        "python3"
        "python"
    )
    
    for exec in "${python_execs[@]}"; do
        if command -v "$exec" >/dev/null 2>&1; then
            echo "$exec"
            return 0
        fi
    done
    
    log_error "No suitable Python executable found. Please ensure Python is installed and virtual environment is set up."
    exit 1
}

# Environment setup for chatbot
set_chatbot_environment() {
    log_info "Setting up chatbot environment..."
    
    # Core chatbot settings
    export CHATBOT__ENABLED=true
    export CHATBOT__DEFAULT_MODEL="gemma3:latest"
    export CHATBOT__MAX_CONVERSATIONS=100
    export CHATBOT__MAX_CONVERSATION_HISTORY=50
    export CHATBOT__CONVERSATION_TIMEOUT=3600
    
    # Platform-specific settings
    if [[ "$PLATFORM" == "darwin" ]]; then
        export PLATFORM__TYPE="macos"
    elif [[ "$PLATFORM" == "linux" ]]; then
        export PLATFORM__TYPE="linux"
    else
        export PLATFORM__TYPE="unix"
    fi
    
    export CHATBOT__STORAGE_PATH="auto"  # Will use platform-appropriate path
    
    # Integration settings
    export CHATBOT__TRANSLATION_INTEGRATION=true
    export CHATBOT__SHARED_OLLAMA_CLIENT=true
    export CHATBOT__SHARED_CACHE=true
    
    # Feature flags
    export DEPLOYMENT__FEATURES="translation,chatbot"
    export DEPLOYMENT__CROSS_PLATFORM=true
    
    # Performance settings
    export CHATBOT__CONCURRENT_CONVERSATIONS=10
    export CHATBOT__RESPONSE_TIMEOUT=30
    export CHATBOT__MEMORY_LIMIT_MB=500
    
    # Web interface
    export CHATBOT__WEB_INTERFACE=true
    export CHATBOT__WEB_PORT=8001
    
    if [[ "$PRODUCTION" == true ]]; then
        export ENVIRONMENT=production
        export DEBUG=false
        export CHATBOT__LOG_LEVEL=INFO
        log_success "Production mode enabled"
    else
        export ENVIRONMENT=development
        export DEBUG=true
        export CHATBOT__LOG_LEVEL=DEBUG
        log_success "Development mode enabled"
    fi
    
    if [[ "$DEBUG" == true ]]; then
        export CHATBOT__LOG_LEVEL=DEBUG
        export LOGGING__LOG_LEVEL=DEBUG
        log_success "Debug logging enabled"
    fi
}

# Service health check
test_service_health() {
    local port=${1:-8000}
    local max_attempts=${2:-30}
    
    log_info "Checking service health on port $port..."
    
    for ((i=1; i<=max_attempts; i++)); do
        if command -v curl >/dev/null 2>&1; then
            if curl -s "http://localhost:$port/api/health" >/dev/null 2>&1; then
                log_success "Service is healthy and responding on port $port"
                return 0
            fi
        elif command -v nc >/dev/null 2>&1; then
            if nc -z localhost "$port" 2>/dev/null; then
                log_success "Service is responding on port $port"
                return 0
            fi
        fi
        
        if [[ $i -le 10 ]]; then
            log_info "Waiting for service to start... ($i/$max_attempts)"
        elif [[ $((i % 5)) -eq 0 ]]; then
            log_info "Still waiting... ($i/$max_attempts)"
        fi
        
        sleep 2
    done
    
    log_error "Service health check failed after $max_attempts attempts"
    return 1
}

# Display service information
show_chatbot_service_info() {
    local port=${1:-8000}
    local chat_port=${2:-8001}
    
    echo ""
    log_success "🤖 Chatbot Service Access Information:"
    echo "======================================="
    
    # Get local IP address
    local local_ip=""
    if command -v ip >/dev/null 2>&1; then
        local_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    elif command -v ifconfig >/dev/null 2>&1; then
        local_ip=$(ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | sed 's/addr://')
    fi
    
    echo ""
    log_info "📱 Local Access:"
    if [[ "$CHAT_ONLY" == true ]]; then
        echo "   🤖 Chatbot: http://localhost:${chat_port}"
        echo "   🤖 Chat API: http://localhost:${chat_port}/api/chat"
    else
        echo "   🔄 Translation: http://localhost:${port}"
        echo "   🤖 Chatbot: http://localhost:${port}/api/chat"
    fi
    
    if [[ -n "$local_ip" ]]; then
        echo ""
        log_info "🌐 Network Access:"
        if [[ "$CHAT_ONLY" == true ]]; then
            echo "   🤖 Chatbot: http://${local_ip}:${chat_port}"
        else
            echo "   🔄 Translation + Chat: http://${local_ip}:${port}"
        fi
    fi
    
    echo ""
    log_info "📚 API Documentation:"
    if [[ "$CHAT_ONLY" == true ]]; then
        echo "   📖 Docs: http://localhost:${chat_port}/docs"
        echo "   🏥 Health: http://localhost:${chat_port}/api/chat/health"
    else
        echo "   📖 Docs: http://localhost:${port}/docs"
        echo "   🏥 Health: http://localhost:${port}/api/health"
        echo "   🤖 Chat Health: http://localhost:${port}/api/chat/health"
    fi
    
    echo ""
    log_info "🛠️  Management:"
    echo "   Stop: Ctrl+C"
    echo "   Logs: Check terminal output"
    echo "   Platform: $PLATFORM_DISPLAY"
}

# Main execution function
main() {
    log_info "🔍 Pre-flight checks..."
    
    # 1. Resolve environment conflicts
    resolve_environment_conflicts
    
    # 2. Find Python executable
    log_info "🐍 Detecting Python executable..."
    PYTHON_EXEC=$(get_python_executable)
    log_success "Using: $PYTHON_EXEC"
    
    # 3. Set environment for chatbot service
    set_chatbot_environment
    
    # 4. Verify required files exist
    log_info "📁 Verifying project structure..."
    
    local required_files=(
        "src/main.py"
        "src/api/routes/chatbot.py"
        "src/services/chatbot_service.py"
        "src/models/chat_schemas.py"
        "src/storage/conversation_manager.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "$file"
        else
            log_error "$file (missing)"
            exit 1
        fi
    done
    
    echo ""
    log_info "🚀 Starting LLM Chatbot Service..."
    echo "===================================="
    
    if [[ "$CHAT_ONLY" == true ]]; then
        log_info "🤖 Starting Chatbot-only mode..."
        log_info "Port: 8001 (Chatbot only)"
        
        # Test health check
        if test_service_health 8001; then
            show_chatbot_service_info 8000 8001
        fi
        
        # Start chatbot-only service
        exec "$PYTHON_EXEC" -m uvicorn src.main:app \
            --host 0.0.0.0 \
            --port 8001 \
            --app-dir . \
            ${DEBUG:+--reload}
    else
        log_info "🔄 Starting Full Service (Translation + Chatbot)..."
        log_info "Port: 8000 (Translation + Chatbot)"
        
        # Check if existing start-service.sh exists
        if [[ -f "./scripts/start-service.sh" ]]; then
            log_success "📜 Using existing service launcher with chatbot enabled"
            
            # Build arguments for existing script
            local service_args=()
            [[ "$PRODUCTION" == true ]] && service_args+=(--production)
            [[ "$DEBUG" == true ]] && service_args+=(--debug)
            [[ "$WITH_NGROK" == true ]] && service_args+=(--with-ngrok)
            [[ "$WITH_TAILSCALE" == true ]] && service_args+=(--with-tailscale)
            [[ "$FORCE" == true ]] && service_args+=(--force)
            
            exec ./scripts/start-service.sh "${service_args[@]}"
        else
            log_warning "📜 Direct service startup (scripts/start-service.sh not found)"
            
            # Health check first
            if test_service_health 8000; then
                show_chatbot_service_info 8000
            fi
            
            # Start service directly
            exec "$PYTHON_EXEC" -m uvicorn src.main:app \
                --host 0.0.0.0 \
                --port 8000 \
                ${DEBUG:+--reload}
        fi
    fi
}

# Error handling
trap 'log_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"
