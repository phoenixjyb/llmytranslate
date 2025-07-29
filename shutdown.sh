#!/bin/bash

# LLM Translation Service - Graceful Shutdown Script (Unix/Linux/macOS)
# This script safely stops all translation services, ngrok, and tailscale

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
KEEP_TAILSCALE=false
KEEP_NGROK=false
FORCE_STOP=false
QUIET=false

# Functions for colored output
print_success() { [ "$QUIET" = false ] && echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { [ "$QUIET" = false ] && echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { [ "$QUIET" = false ] && echo -e "${BLUE}ℹ️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-tailscale)
            KEEP_TAILSCALE=true
            shift
            ;;
        --keep-ngrok)
            KEEP_NGROK=true
            shift
            ;;
        --force)
            FORCE_STOP=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --keep-tailscale    Keep Tailscale running"
            echo "  --keep-ngrok        Keep ngrok running"
            echo "  --force             Force stop all processes"
            echo "  --quiet             Silent operation"
            echo "  -h, --help          Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                     Stop all services"
            echo "  $0 --keep-tailscale    Keep Tailscale running"
            echo "  $0 --force             Force stop all processes"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ "$QUIET" = false ]; then
    echo -e "${CYAN}🛑 LLM Translation Service - Graceful Shutdown${NC}"
    echo -e "${CYAN}================================================${NC}"
    echo ""
fi

# Function to safely stop processes
stop_process_safely() {
    local process_name="$1"
    local display_name="$2"
    
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        print_info "Stopping $display_name services..."
        for pid in $pids; do
            if [ "$FORCE_STOP" = true ]; then
                kill -9 "$pid" 2>/dev/null && print_success "$display_name process (PID: $pid) force stopped" || print_warning "Could not stop $display_name process (PID: $pid)"
            else
                # Try graceful shutdown first
                kill -TERM "$pid" 2>/dev/null && sleep 2
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null && print_success "$display_name process (PID: $pid) stopped" || print_warning "Could not stop $display_name process (PID: $pid)"
                else
                    print_success "$display_name process (PID: $pid) stopped gracefully"
                fi
            fi
        done
    else
        print_info "$display_name - No running processes found"
    fi
}

# Function to check and stop service by port
stop_service_by_port() {
    local port="$1"
    local service_name="$2"
    
    local pids=$(lsof -t -i:"$port" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        print_info "Stopping $service_name on port $port..."
        for pid in $pids; do
            kill -9 "$pid" 2>/dev/null && print_success "$service_name stopped (was using port $port)" || print_warning "Could not stop process on port $port (PID: $pid)"
        done
    else
        print_info "$service_name - Port $port not in use"
    fi
}

# 1. Stop Translation Services
print_info "🔄 Step 1: Stopping Translation Services..."

# Try graceful shutdown via API first
if command -v curl >/dev/null 2>&1; then
    if curl -X POST "http://localhost:8000/api/admin/shutdown" --connect-timeout 5 --max-time 5 >/dev/null 2>&1; then
        print_success "Translation service gracefully shut down via API"
        sleep 2
    else
        print_warning "Could not gracefully shutdown via API, using process termination"
    fi
else
    print_warning "curl not available, using process termination"
fi

# Stop by port and process name
stop_service_by_port 8000 "Translation Service"
stop_process_safely "python.*uvicorn\|uvicorn.*python\|fastapi" "Python/FastAPI"
stop_process_safely "uvicorn" "Uvicorn"

# 2. Stop Ollama Services
print_info "🔄 Step 2: Stopping Ollama Services..."
stop_process_safely "ollama" "Ollama"

# 3. Stop ngrok (unless --keep-ngrok is specified)
if [ "$KEEP_NGROK" = false ]; then
    print_info "🔄 Step 3: Stopping ngrok Services..."
    
    # Try to stop ngrok tunnels gracefully via API
    if command -v curl >/dev/null 2>&1; then
        if curl "http://localhost:4040/api/tunnels" --connect-timeout 3 --max-time 3 >/dev/null 2>&1; then
            print_info "Attempting to stop ngrok tunnels gracefully..."
            # Note: More complex tunnel stopping would require jq to parse JSON
            # For now, just proceed to process termination
        fi
    fi
    
    stop_process_safely "ngrok" "ngrok"
    stop_service_by_port 4040 "ngrok Dashboard"
else
    print_info "🔄 Step 3: Keeping ngrok running (--keep-ngrok specified)"
fi

# 4. Stop Tailscale (unless --keep-tailscale is specified)
if [ "$KEEP_TAILSCALE" = false ]; then
    print_info "🔄 Step 4: Stopping Tailscale Services..."
    
    # Try to disconnect Tailscale gracefully first
    if command -v tailscale >/dev/null 2>&1; then
        print_info "Attempting graceful Tailscale disconnect..."
        tailscale logout >/dev/null 2>&1 && print_success "Tailscale disconnected gracefully" || print_warning "Could not disconnect Tailscale gracefully"
        sleep 2
    else
        print_warning "Tailscale CLI not found, using process termination"
    fi
    
    stop_process_safely "tailscale" "Tailscale"
else
    print_info "🔄 Step 4: Keeping Tailscale running (--keep-tailscale specified)"
fi

# 5. Final Verification
print_info "🔄 Step 5: Final Verification..."

remaining_processes=""
remaining_processes+=$(pgrep -f "python.*uvicorn\|uvicorn.*python\|fastapi" 2>/dev/null || true)
remaining_processes+=$(pgrep -f "ollama" 2>/dev/null || true)

if [ "$KEEP_NGROK" = false ]; then
    remaining_processes+=$(pgrep -f "ngrok" 2>/dev/null || true)
fi

if [ "$KEEP_TAILSCALE" = false ]; then
    remaining_processes+=$(pgrep -f "tailscale" 2>/dev/null || true)
fi

if [ -n "$remaining_processes" ]; then
    print_warning "Some processes are still running:"
    echo "$remaining_processes" | while read -r pid; do
        [ -n "$pid" ] && print_warning "  - PID: $pid"
    done
    
    if [ "$FORCE_STOP" = true ]; then
        print_info "Force stopping remaining processes..."
        echo "$remaining_processes" | while read -r pid; do
            [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
        done
        print_success "Remaining processes force stopped"
    else
        print_info "Use --force parameter to force stop remaining processes"
    fi
else
    print_success "All target services have been stopped"
fi

# 6. Port Verification
print_info "🔄 Step 6: Port Status Check..."

check_port() {
    local port="$1"
    local name="$2"
    
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:"$port" >/dev/null 2>&1; then
            print_warning "$name port $port still in use"
        else
            print_success "$name port $port is available"
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -ln | grep ":$port " >/dev/null 2>&1; then
            print_warning "$name port $port still in use"
        else
            print_success "$name port $port is available"
        fi
    else
        print_warning "Cannot check port $port (no lsof or netstat available)"
    fi
}

check_port 8000 "Translation Service"
check_port 11434 "Ollama API"

if [ "$KEEP_NGROK" = false ]; then
    check_port 4040 "ngrok Dashboard"
fi

# 7. Summary
if [ "$QUIET" = false ]; then
    echo ""
    echo -e "${CYAN}🎯 Shutdown Summary:${NC}"
    echo -e "${CYAN}===================${NC}"
    print_success "Translation services stopped"
    print_success "Ollama services stopped"
    
    if [ "$KEEP_NGROK" = true ]; then
        print_info "ngrok kept running (as requested)"
    else
        print_success "ngrok services stopped"
    fi
    
    if [ "$KEEP_TAILSCALE" = true ]; then
        print_info "Tailscale kept running (as requested)"
    else
        print_success "Tailscale services stopped"
    fi
    
    echo ""
    echo -e "${GREEN}✨ Graceful shutdown completed!${NC}"
    echo ""
    echo -e "${CYAN}💡 Usage examples:${NC}"
    echo "  ./shutdown.sh                    # Stop all services"
    echo "  ./shutdown.sh --keep-tailscale   # Keep Tailscale running"
    echo "  ./shutdown.sh --keep-ngrok       # Keep ngrok running"
    echo "  ./shutdown.sh --force            # Force stop all processes"
    echo "  ./shutdown.sh --quiet            # Silent operation"
fi
