#!/bin/bash
# ================================================================================================
# LLM Translation Service - Service Management Script
# This script helps start, stop, and manage the translation service
# ================================================================================================

# Parse command line arguments
ACTION=""
PRODUCTION=false
DOCKER=false
LOG_TAIL="50"

while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|status|logs)
            ACTION="$1"
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        --docker)
            DOCKER=true
            shift
            ;;
        --log-tail)
            LOG_TAIL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [start|stop|restart|status|logs] [--production] [--docker] [--log-tail N]"
            echo "Actions:"
            echo "  start    - Start the translation service"
            echo "  stop     - Stop the translation service"
            echo "  restart  - Restart the translation service"
            echo "  status   - Show service status"
            echo "  logs     - Show service logs"
            echo "Options:"
            echo "  --production  - Run in production mode"
            echo "  --docker      - Use Docker for operations"
            echo "  --log-tail N  - Show last N log lines (default: 50)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [start|stop|restart|status|logs] [--production] [--docker] [--log-tail N]"
            exit 1
            ;;
    esac
done

if [[ -z "$ACTION" ]]; then
    echo "Error: Action is required"
    echo "Usage: $0 [start|stop|restart|status|logs] [options]"
    exit 1
fi

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${CYAN}🔧 LLM Translation Service - Service Management${NC}"
echo -e "${CYAN}===============================================${NC}"

SERVICE_NAME="LLM Translation Service"
SERVICE_PORT=8000
METRICS_PORT=8001

function test_service_running() {
    local port=$1
    case "$OSTYPE" in
        linux*|darwin*)
            if lsof -ti :$port > /dev/null 2>&1; then
                return 0
            else
                return 1
            fi
            ;;
        *)
            # Fallback using curl
            if curl -s --max-time 2 "http://localhost:$port" > /dev/null 2>&1; then
                return 0
            else
                return 1
            fi
            ;;
    esac
}

function get_service_status() {
    local is_running=false
    local metrics_running=false
    
    if test_service_running $SERVICE_PORT; then
        is_running=true
    fi
    
    if test_service_running $METRICS_PORT; then
        metrics_running=true
    fi
    
    echo -e "\n${GREEN}📊 Service Status:${NC}"
    
    if [[ "$is_running" == "true" ]]; then
        print_success "Translation Service: Running on port $SERVICE_PORT"
        
        # Try to get service info
        if command -v curl &> /dev/null; then
            SERVICE_INFO=$(curl -s --max-time 5 "http://localhost:$SERVICE_PORT" 2>/dev/null)
            if [[ $? -eq 0 ]] && [[ -n "$SERVICE_INFO" ]]; then
                if command -v jq &> /dev/null; then
                    SERVICE_NAME_INFO=$(echo "$SERVICE_INFO" | jq -r '.name' 2>/dev/null)
                    SERVICE_VERSION=$(echo "$SERVICE_INFO" | jq -r '.version' 2>/dev/null)
                    if [[ "$SERVICE_NAME_INFO" != "null" ]]; then
                        echo -e "   ${WHITE}Name: $SERVICE_NAME_INFO${NC}"
                    fi
                    if [[ "$SERVICE_VERSION" != "null" ]]; then
                        echo -e "   ${WHITE}Version: $SERVICE_VERSION${NC}"
                    fi
                else
                    echo -e "   ${YELLOW}(Install jq for detailed service info)${NC}"
                fi
            else
                echo -e "   ${YELLOW}(Could not retrieve service details)${NC}"
            fi
        fi
    else
        print_error "Translation Service: Not running"
    fi
    
    if [[ "$metrics_running" == "true" ]]; then
        print_success "Metrics Service: Running on port $METRICS_PORT"
    else
        echo -e "   ${YELLOW}⚠️  Metrics Service: Not running${NC}"
    fi
    
    # Check related processes
    echo -e "\n${CYAN}🔍 Related Processes:${NC}"
    
    # Check Python processes
    local python_pids=($(pgrep -f "python.*run.py" 2>/dev/null))
    python_pids+=($(pgrep -f "uvicorn" 2>/dev/null))
    
    if [[ ${#python_pids[@]} -gt 0 ]]; then
        echo -e "   ${GREEN}Python Service Processes:${NC}"
        for pid in "${python_pids[@]}"; do
            local cmdline=$(ps -p "$pid" -o args= 2>/dev/null | head -c 80)
            echo -e "     ${WHITE}PID $pid: $cmdline${NC}"
        done
    else
        echo -e "   ${YELLOW}No Python service processes found${NC}"
    fi
    
    # Check ngrok
    local ngrok_pids=($(pgrep -f "ngrok" 2>/dev/null))
    if [[ ${#ngrok_pids[@]} -gt 0 ]]; then
        echo -e "   ${GREEN}Ngrok Tunnel:${NC}"
        for pid in "${ngrok_pids[@]}"; do
            echo -e "     ${WHITE}PID $pid: Active${NC}"
        done
        
        # Try to get ngrok URL
        if command -v curl &> /dev/null; then
            NGROK_INFO=$(curl -s --max-time 2 "http://localhost:4040/api/tunnels" 2>/dev/null)
            if [[ $? -eq 0 ]] && command -v jq &> /dev/null; then
                PUBLIC_URL=$(echo "$NGROK_INFO" | jq -r '.tunnels[0].public_url' 2>/dev/null)
                if [[ "$PUBLIC_URL" != "null" ]] && [[ -n "$PUBLIC_URL" ]]; then
                    echo -e "     ${WHITE}Public URL: $PUBLIC_URL${NC}"
                fi
            fi
        fi
    else
        echo -e "   ${YELLOW}No ngrok tunnel active${NC}"
    fi
}

function start_service() {
    echo -e "\n${GREEN}🚀 Starting $SERVICE_NAME...${NC}"
    
    # Check if already running
    if test_service_running $SERVICE_PORT; then
        print_warning "Service is already running on port $SERVICE_PORT"
        return 0
    fi
    
    # Set environment
    if [[ "$PRODUCTION" == "true" ]]; then
        export ENVIRONMENT="production"
        print_info "Starting in PRODUCTION mode"
    else
        export ENVIRONMENT="development"
        print_info "Starting in DEVELOPMENT mode"
    fi
    
    if [[ "$DOCKER" == "true" ]]; then
        print_info "Starting with Docker..."
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d
        elif command -v docker &> /dev/null; then
            docker run -d -p $SERVICE_PORT:$SERVICE_PORT llm-translation-service
        else
            print_error "Docker not found"
            return 1
        fi
    else
        print_info "Starting with Python..."
        
        # Find Python executable
        local python_exec=""
        for python_cmd in "./.venv/bin/python" "python3" "python"; do
            if command -v "$python_cmd" &> /dev/null; then
                python_exec="$python_cmd"
                break
            fi
        done
        
        if [[ -z "$python_exec" ]]; then
            print_error "Python not found"
            return 1
        fi
        
        print_info "Using Python: $python_exec"
        print_info "Starting service in background..."
        
        nohup $python_exec run.py > logs/service.log 2>&1 &
        local service_pid=$!
        
        echo $service_pid > .service.pid
        print_success "Service started with PID: $service_pid"
        
        # Wait a moment and check if it started successfully
        sleep 3
        if test_service_running $SERVICE_PORT; then
            print_success "Service is now running on port $SERVICE_PORT"
        else
            print_error "Service failed to start. Check logs for details."
            return 1
        fi
    fi
}

function stop_service() {
    echo -e "\n${RED}🛑 Stopping $SERVICE_NAME...${NC}"
    
    # Use our stop script if available
    if [[ -f "./scripts/stop-service.sh" ]]; then
        print_info "Using stop-service.sh script..."
        ./scripts/stop-service.sh --service-only
    else
        # Manual stop
        local port_pids=()
        case "$OSTYPE" in
            linux*|darwin*)
                port_pids=($(lsof -ti :$SERVICE_PORT 2>/dev/null))
                ;;
        esac
        
        if [[ ${#port_pids[@]} -gt 0 ]]; then
            for pid in "${port_pids[@]}"; do
                kill -TERM "$pid" 2>/dev/null
                print_success "Stopped process PID: $pid"
            done
        else
            print_warning "No service processes found on port $SERVICE_PORT"
        fi
    fi
    
    # Clean up PID file
    if [[ -f ".service.pid" ]]; then
        rm -f .service.pid
    fi
}

function restart_service() {
    echo -e "\n${YELLOW}🔄 Restarting $SERVICE_NAME...${NC}"
    stop_service
    sleep 2
    start_service
}

function show_logs() {
    echo -e "\n${CYAN}📜 Service Logs (last $LOG_TAIL lines):${NC}"
    
    if [[ -f "logs/service.log" ]]; then
        tail -n "$LOG_TAIL" logs/service.log
    elif [[ "$DOCKER" == "true" ]]; then
        if command -v docker-compose &> /dev/null; then
            docker-compose logs --tail="$LOG_TAIL"
        else
            print_warning "Docker compose not available for logs"
        fi
    else
        print_warning "No log file found at logs/service.log"
        print_info "Service may be running in foreground mode"
    fi
}

# Main execution
case "$ACTION" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        get_service_status
        ;;
    logs)
        show_logs
        ;;
esac

echo -e "\n${GREEN}🎉 Service management operation completed!${NC}"
