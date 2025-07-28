#!/bin/bash
# ================================================================================================
# Cross-Platform LLM Translation Service Starter
# OS-Aware service startup with environment variable conflict resolution
# ================================================================================================

# Parse command line arguments
PRODUCTION=false
DEBUG=false
FORCE=false
WITH_NGROK=false
WITH_TAILSCALE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            PRODUCTION=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --force)
            FORCE=true
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
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--production] [--debug] [--force] [--with-ngrok] [--with-tailscale]"
            exit 1
            ;;
    esac
done

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
function print_step() { echo -e "${BLUE}🔄 $1${NC}"; }

# Platform detection
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM_DISPLAY=$(sw_vers -productName)" "$(sw_vers -productVersion)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [[ -f /etc/os-release ]]; then
        PLATFORM_DISPLAY=$(grep "PRETTY_NAME" /etc/os-release | cut -d'"' -f2)
    else
        PLATFORM_DISPLAY="Linux $(uname -r)"
    fi
else
    PLATFORM_DISPLAY="$OSTYPE"
fi

# Script header
echo -e "${CYAN}🚀 Cross-Platform LLM Translation Service Starter${NC}"
echo -e "${CYAN}=================================================${NC}"
echo -e "${YELLOW}Platform: $PLATFORM_DISPLAY${NC}"

# Environment Variable Conflict Resolution
function resolve_environment_conflicts() {
    print_info "Resolving environment variable conflicts..."
    
    # List of environment variables that can conflict with pydantic configuration
    conflict_patterns=("OLLAMA" "REDIS" "DATABASE" "AUTH" "API")
    
    for pattern in "${conflict_patterns[@]}"; do
        # Check for exact matches and variations (using portable approach)
        pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
        pattern_upper=$(echo "$pattern" | tr '[:lower:]' '[:upper:]')
        
        for var in $(printenv | grep -E "^${pattern}[=]|^${pattern_lower}[=]|^${pattern_upper}[=]" | cut -d'=' -f1); do
            print_warning "Temporarily removing: $var"
            unset "$var"
        done
    done
}

# Cross-platform Python executable detection
function get_python_executable() {
    local python_execs=()
    
    python_execs=(
        "./.venv/bin/python"
        "./.venv/bin/python3"
        "python3"
        "python"
    )
    
    for exec in "${python_execs[@]}"; do
        if [[ -x "$exec" ]] || command -v "$exec" &> /dev/null; then
            if "$exec" --version &> /dev/null; then
                echo "$exec"
                return 0
            fi
        fi
    done
    
    print_error "No suitable Python executable found. Please ensure Python is installed and virtual environment is set up."
    exit 1
}

# Service health check
function test_service_health() {
    local port=${1:-8000}
    local max_attempts=${2:-30}
    
    print_info "Checking service health..."
    
    for ((i=1; i<=max_attempts; i++)); do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "Service is healthy and responding on port $port"
            return 0
        fi
        
        if [[ $i -le 10 ]]; then
            print_warning "Waiting for service to start... ($i/$max_attempts)"
        elif [[ $((i % 5)) -eq 0 ]]; then
            print_warning "Still waiting... ($i/$max_attempts)"
        fi
        
        sleep 2
    done
    
    print_error "Service health check failed after $max_attempts attempts"
    return 1
}

# Display service information
function show_service_info() {
    local port=${1:-8000}
    
    echo -e "\n${GREEN}🌐 Service Access Information:${NC}"
    echo -e "${GREEN}================================${NC}"
    
    # Get local IP addresses
    local local_ips=()
    if command -v ip &> /dev/null; then
        local_ips=($(ip route get 1.1.1.1 | grep -oP 'src \K\S+' 2>/dev/null))
    elif command -v ifconfig &> /dev/null; then
        local_ips=($(ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d':' -f2))
    fi
    
    echo -e "${CYAN}📱 Local Access:${NC}"
    echo -e "   http://localhost:${port}"
    echo -e "   http://127.0.0.1:${port}"
    
    if [[ ${#local_ips[@]} -gt 0 ]]; then
        echo -e "\n${CYAN}🌐 Network Access:${NC}"
        for ip in "${local_ips[@]}"; do
            echo -e "   http://${ip}:${port}"
        done
    fi
    
    echo -e "\n${CYAN}📚 Documentation:${NC}"
    echo -e "   http://localhost:${port}/docs"
    echo -e "   http://localhost:${port}/health"
    
    echo -e "\n${CYAN}🛠️  Management:${NC}"
    echo -e "   Stop: Ctrl+C"
    echo -e "   Logs: Check terminal output"
}

# Main execution
{
    print_info "Pre-flight checks..."
    
    # 1. Resolve environment conflicts
    resolve_environment_conflicts
    
    # 2. Find Python executable
    print_info "Detecting Python executable..."
    PYTHON_EXEC=$(get_python_executable)
    print_success "Using: $PYTHON_EXEC"
    
    # 3. Set environment for service
    if [[ "$PRODUCTION" == "true" ]]; then
        export ENVIRONMENT="production"
        print_warning "Running in PRODUCTION mode"
    else
        export ENVIRONMENT="development"
        print_success "Running in DEVELOPMENT mode"
    fi
    
    if [[ "$DEBUG" == "true" ]]; then
        export DEBUG="true"
        print_warning "Debug mode enabled"
    fi
    
    # 4. Verify required files
    required_files=("run.py" ".env" "src/main.py")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    print_success "All required files found"
    
    # 5. Start the service
    print_info "Starting LLM Translation Service..."
    echo -e "${CYAN}=======================================${NC}"
    
    # Start service in background for health check
    $PYTHON_EXEC run.py &
    SERVICE_PID=$!
    
    # Wait for service to start and check health
    sleep 3
    
    # Check if service started successfully
    if test_service_health 8000; then
        # Kill background process and start in foreground
        kill $SERVICE_PID 2>/dev/null || true
        wait $SERVICE_PID 2>/dev/null || true
        
        show_service_info 8000
        
        print_success "Service started successfully!"
        
        # Start ngrok if requested
        if [[ "$WITH_NGROK" == "true" ]]; then
            print_info "Starting ngrok tunnel..."
            if command -v ngrok &> /dev/null; then
                # Start ngrok in background with warning bypass
                ngrok http 8000 --log=stdout --bind-tls=true &
                NGROK_PID=$!
                
                sleep 3
                
                # Try to get ngrok URL
                if curl -s "http://localhost:4040/api/tunnels" > /dev/null 2>&1; then
                    PUBLIC_URL=$(curl -s "http://localhost:4040/api/tunnels" | grep -o '"public_url":"[^"]*"' | head -1 | cut -d'"' -f4)
                    if [[ -n "$PUBLIC_URL" ]]; then
                        print_success "Public URL: $PUBLIC_URL"
                        print_success "Direct Access: $PUBLIC_URL (bypasses warning)"
                    else
                        print_warning "Ngrok started but URL not ready yet. Check http://localhost:4040"
                    fi
                else
                    print_warning "Ngrok started but unable to get URL. Check http://localhost:4040"
                fi
            else
                print_error "Ngrok not found. Please install ngrok first."
                print_warning "Download from: https://ngrok.com/download"
            fi
        fi
        
        # Start Tailscale configuration if requested
        if [[ "$WITH_TAILSCALE" == "true" ]]; then
            print_info "Configuring Tailscale access..."
            if command -v tailscale &> /dev/null; then
                # Check if Tailscale is running
                if tailscale status &> /dev/null; then
                    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null)
                    if [[ -n "$TAILSCALE_IP" ]]; then
                        print_success "Tailscale IP: $TAILSCALE_IP"
                        print_success "Service URL: http://$TAILSCALE_IP:8000"
                        print_success "API Docs: http://$TAILSCALE_IP:8000/docs"
                        
                        # Set up Tailscale environment if available
                        if [[ -f ".env.tailscale" ]]; then
                            print_info "Using Tailscale environment configuration"
                            cp .env.tailscale .env
                        fi
                    else
                        print_warning "Unable to get Tailscale IP. Service will start normally."
                    fi
                else
                    print_warning "Tailscale is not running. Please run 'tailscale up' first."
                    print_warning "Service will start normally on localhost."
                fi
            else
                print_error "Tailscale not found. Please install Tailscale first."
                print_warning "Download from: https://tailscale.com/download"
                print_warning "Service will start normally on localhost."
            fi
        fi
        
        print_warning "Press Ctrl+C to stop the service"
        echo -e "${CYAN}=================================${NC}"
        
        # Start service in foreground
        $PYTHON_EXEC run.py
    else
        # Kill background process if health check failed
        kill $SERVICE_PID 2>/dev/null || true
        wait $SERVICE_PID 2>/dev/null || true
        
        print_error "Service failed to start properly"
        exit 1
    fi
    
} || {
    print_error "Error starting service: $?"
    exit 1
}

print_info "Service stopped"
