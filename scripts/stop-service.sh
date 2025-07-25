#!/bin/bash
# ================================================================================================
# LLM Translation Service - Stop Script (Unix/Linux/macOS)
# Safely stops the translation service and ngrok tunnel
# ================================================================================================

set -e

# Default values
FORCE=false
NGROK_ONLY=false
SERVICE_ONLY=false
VERBOSE=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        --ngrok-only|-n)
            NGROK_ONLY=true
            shift
            ;;
        --service-only|-s)
            SERVICE_ONLY=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --force, -f          Force stop services"
            echo "  --ngrok-only, -n     Stop only ngrok"
            echo "  --service-only, -s   Stop only translation service"
            echo "  --verbose, -v        Verbose output"
            echo "  --help, -h           Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${RED}🛑 LLM Translation Service - Stop Script${NC}"
echo -e "${RED}=========================================${NC}"

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "  ${GRAY}ℹ️  $1${NC}"
    fi
}

stop_ngrok() {
    echo -e "\n${YELLOW}🚇 Stopping ngrok tunnel...${NC}"
    
    # Find ngrok processes
    NGROK_PIDS=$(pgrep -f "ngrok" 2>/dev/null || true)
    
    if [ -n "$NGROK_PIDS" ]; then
        verbose_log "Found ngrok processes: $NGROK_PIDS"
        
        for pid in $NGROK_PIDS; do
            if [ "$FORCE" = true ]; then
                kill -9 "$pid" 2>/dev/null || true
                echo -e "  ${GREEN}✅ Force stopped ngrok process (PID: $pid)${NC}"
            else
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
                echo -e "  ${GREEN}✅ Stopped ngrok process (PID: $pid)${NC}"
            fi
        done
    else
        echo -e "  ${GRAY}ℹ️  No ngrok processes found${NC}"
    fi
    
    # Verify ngrok is stopped
    sleep 1
    REMAINING_NGROK=$(pgrep -f "ngrok" 2>/dev/null || true)
    if [ -n "$REMAINING_NGROK" ]; then
        echo -e "  ${YELLOW}⚠️  Some ngrok processes may still be running${NC}"
    else
        echo -e "  ${GREEN}✅ All ngrok processes stopped${NC}"
    fi
}

stop_translation_service() {
    echo -e "\n${YELLOW}🔴 Stopping translation service...${NC}"
    
    # Method 1: Check port 8000 usage
    verbose_log "Checking port 8000 usage..."
    PORT_PID=$(lsof -t -i:8000 2>/dev/null || true)
    
    if [ -n "$PORT_PID" ]; then
        verbose_log "Found process using port 8000: PID $PORT_PID"
        
        if [ "$FORCE" = true ]; then
            kill -9 "$PORT_PID" 2>/dev/null || true
            echo -e "  ${GREEN}✅ Force stopped process on port 8000 (PID: $PORT_PID)${NC}"
        else
            kill -TERM "$PORT_PID" 2>/dev/null || true
            sleep 3
            if kill -0 "$PORT_PID" 2>/dev/null; then
                kill -9 "$PORT_PID" 2>/dev/null || true
            fi
            echo -e "  ${GREEN}✅ Stopped process on port 8000 (PID: $PORT_PID)${NC}"
        fi
    fi
    
    # Method 2: Stop python processes that might be running the service
    verbose_log "Checking for python translation service processes..."
    PYTHON_PIDS=$(pgrep -f "python.*uvicorn\|python.*main:app\|python.*run.py" 2>/dev/null || true)
    
    if [ -n "$PYTHON_PIDS" ]; then
        for pid in $PYTHON_PIDS; do
            verbose_log "Found translation service python process: PID $pid"
            
            if [ "$FORCE" = true ]; then
                kill -9 "$pid" 2>/dev/null || true
                echo -e "  ${GREEN}✅ Force stopped python translation service (PID: $pid)${NC}"
            else
                kill -TERM "$pid" 2>/dev/null || true
                sleep 3
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
                echo -e "  ${GREEN}✅ Stopped python translation service (PID: $pid)${NC}"
            fi
        done
    fi
    
    # Verify service is stopped
    verbose_log "Verifying translation service is stopped..."
    sleep 2
    
    if curl -s --connect-timeout 3 "http://localhost:8000/api/health" >/dev/null 2>&1; then
        echo -e "  ${YELLOW}⚠️  Translation service may still be running${NC}"
    else
        echo -e "  ${GREEN}✅ Translation service stopped${NC}"
    fi
}

show_service_status() {
    echo -e "\n${CYAN}📊 Service Status Check:${NC}"
    
    # Check ngrok
    NGROK_RUNNING=$(pgrep -f "ngrok" 2>/dev/null || true)
    if [ -n "$NGROK_RUNNING" ]; then
        NGROK_COUNT=$(echo "$NGROK_RUNNING" | wc -l)
        echo -e "  🚇 Ngrok: ${YELLOW}⚠️  Still running ($NGROK_COUNT process(es))${NC}"
    else
        echo -e "  🚇 Ngrok: ${GREEN}✅ Stopped${NC}"
    fi
    
    # Check translation service
    PORT_USED=$(lsof -t -i:8000 2>/dev/null || true)
    if [ -n "$PORT_USED" ]; then
        echo -e "  🔴 Translation Service: ${YELLOW}⚠️  Port 8000 still in use${NC}"
    else
        echo -e "  🔴 Translation Service: ${GREEN}✅ Stopped${NC}"
    fi
    
    # Test service availability
    if curl -s --connect-timeout 2 "http://localhost:8000/api/health" >/dev/null 2>&1; then
        echo -e "  🏥 Health Check: ${YELLOW}⚠️  Service still responding${NC}"
    else
        echo -e "  🏥 Health Check: ${GREEN}✅ Connection refused (service stopped)${NC}"
    fi
}

# Main execution
if [ "$NGROK_ONLY" = true ]; then
    stop_ngrok
elif [ "$SERVICE_ONLY" = true ]; then
    stop_translation_service
else
    # Stop both services
    stop_ngrok
    stop_translation_service
fi

show_service_status

echo -e "\n${GREEN}🎉 Stop operation completed!${NC}"
if [ "$FORCE" = true ]; then
    echo -e "   ${GRAY}Used force termination mode${NC}"
fi

echo -e "\n${CYAN}💡 Usage examples:${NC}"
echo -e "   ./scripts/stop-service.sh                 # Stop both services"
echo -e "   ./scripts/stop-service.sh --ngrok-only    # Stop only ngrok"
echo -e "   ./scripts/stop-service.sh --service-only  # Stop only translation service"
echo -e "   ./scripts/stop-service.sh --force         # Force stop all"
echo -e "   ./scripts/stop-service.sh --verbose       # Detailed output"
