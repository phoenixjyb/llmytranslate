#!/bin/bash

# LLM Translation Service Deployment Script
# Supports both local and remote deployment modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEPLOYMENT_MODE="local"
AUTO_INSTALL_DEPS=false
SKIP_OLLAMA_SETUP=false
FORCE_REINSTALL=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy llmYTranslate service in local or remote mode.

OPTIONS:
    -m, --mode MODE         Deployment mode: 'local' or 'remote' (default: local)
    -a, --auto-install      Automatically install dependencies
    -s, --skip-ollama       Skip Ollama setup (if already configured)
    -f, --force             Force reinstall of dependencies
    -h, --help              Display this help message

EXAMPLES:
    # Local deployment (default)
    $0 --mode local --auto-install

    # Remote deployment with auto-install
    $0 --mode remote --auto-install
    
    # Quick local setup
    $0 -m local -a
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            DEPLOYMENT_MODE="$2"
            shift 2
            ;;
        -a|--auto-install)
            AUTO_INSTALL_DEPS=true
            shift
            ;;
        -s|--skip-ollama)
            SKIP_OLLAMA_SETUP=true
            shift
            ;;
        -f|--force)
            FORCE_REINSTALL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate deployment mode
if [[ "$DEPLOYMENT_MODE" != "local" && "$DEPLOYMENT_MODE" != "remote" ]]; then
    print_error "Invalid deployment mode: $DEPLOYMENT_MODE. Must be 'local' or 'remote'"
    exit 1
fi

print_status "Starting llmYTranslate deployment in $DEPLOYMENT_MODE mode..."

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $python_version"
    
    # Check if in correct directory
    if [[ ! -f "requirements.txt" ]] || [[ ! -d "src" ]]; then
        print_error "Please run this script from the llmYTranslate root directory"
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [[ "$FORCE_REINSTALL" == true ]] && [[ -d ".venv" ]]; then
        print_warning "Removing existing virtual environment"
        rm -rf .venv
    fi
    
    if [[ ! -d ".venv" ]]; then
        python3 -m venv .venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [[ "$FORCE_REINSTALL" == true ]]; then
        pip install --force-reinstall -r requirements.txt
    else
        pip install -r requirements.txt
    fi
    
    print_success "Python environment setup completed"
}

# Setup Ollama
setup_ollama() {
    if [[ "$SKIP_OLLAMA_SETUP" == true ]]; then
        print_warning "Skipping Ollama setup as requested"
        return
    fi
    
    print_status "Setting up Ollama..."
    
    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        print_status "Ollama is already installed"
    else
        if [[ "$AUTO_INSTALL_DEPS" == true ]]; then
            print_status "Installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            print_warning "Ollama not found. Please install it manually:"
            print_warning "curl -fsSL https://ollama.ai/install.sh | sh"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    # Start Ollama service (if not running)
    if ! pgrep -f ollama &> /dev/null; then
        print_status "Starting Ollama service..."
        ollama serve &
        sleep 3
    fi
    
    # Check available models
    print_status "Checking available models..."
    available_models=$(ollama list 2>/dev/null | grep -v "NAME" | awk '{print $1}' || true)
    
    # Pull recommended model if not available
    if [[ ! $available_models =~ "llava" ]]; then
        if [[ "$AUTO_INSTALL_DEPS" == true ]]; then
            print_status "Pulling llava model..."
            ollama pull llava:latest
        else
            print_warning "Recommended model 'llava:latest' not found"
            print_status "Available models: $available_models"
            read -p "Pull llava:latest model? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                ollama pull llava:latest
            fi
        fi
    fi
    
    print_success "Ollama setup completed"
}

# Configure environment
configure_environment() {
    print_status "Configuring environment for $DEPLOYMENT_MODE mode..."
    
    # Copy appropriate environment file
    if [[ -f ".env.$DEPLOYMENT_MODE" ]]; then
        cp ".env.$DEPLOYMENT_MODE" .env
        print_success "Environment configuration copied from .env.$DEPLOYMENT_MODE"
    else
        print_warning "No environment template found for $DEPLOYMENT_MODE mode"
        if [[ ! -f ".env" ]]; then
            # Create basic .env file
            cat > .env << EOF
# Basic configuration for $DEPLOYMENT_MODE mode
DEPLOYMENT__MODE=$DEPLOYMENT_MODE
API__HOST=$([ "$DEPLOYMENT_MODE" == "local" ] && echo "127.0.0.1" || echo "0.0.0.0")
API__PORT=8888
OLLAMA__MODEL_NAME=llava:latest
AUTH__DISABLE_SIGNATURE_VALIDATION=true
ENVIRONMENT=development
DEBUG=true
EOF
            print_success "Basic .env file created"
        fi
    fi
    
    # Get local network information for remote mode
    if [[ "$DEPLOYMENT_MODE" == "remote" ]]; then
        print_status "Detecting network configuration..."
        
        # Try to detect local IP
        local_ip=""
        if command -v ip &> /dev/null; then
            local_ip=$(ip route get 8.8.8.8 | awk '{print $7; exit}' 2>/dev/null || echo "")
        elif command -v ifconfig &> /dev/null; then
            local_ip=$(ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1 || echo "")
        fi
        
        if [[ -n "$local_ip" ]]; then
            print_status "Detected local IP: $local_ip"
            sed -i.bak "s/your-external-ip-or-domain/$local_ip/g" .env 2>/dev/null || true
        else
            print_warning "Could not auto-detect IP. Please manually update DEPLOYMENT__EXTERNAL_HOST in .env"
        fi
    fi
    
    print_success "Environment configuration completed"
}

# Test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    source .venv/bin/activate
    
    # Start service in background for testing
    python run.py &
    SERVICE_PID=$!
    
    # Wait for service to start
    sleep 5
    
    # Test health endpoint
    local port=$(grep "API__PORT" .env | cut -d'=' -f2 || echo "8888")
    local host=$(grep "API__HOST" .env | cut -d'=' -f2 || echo "127.0.0.1")
    
    if [[ "$host" == "0.0.0.0" ]]; then
        test_host="127.0.0.1"
    else
        test_host="$host"
    fi
    
    if curl -s --max-time 10 "http://$test_host:$port/api/health" > /dev/null; then
        print_success "Health check passed"
        
        # Test discovery endpoint
        if curl -s --max-time 5 "http://$test_host:$port/api/discovery/info" > /dev/null; then
            print_success "Service discovery endpoint working"
        fi
        
        # Test translation endpoint
        if curl -s --max-time 10 -X POST "http://$test_host:$port/api/trans/vip/translate" \
               -H "Content-Type: application/x-www-form-urlencoded" \
               -d "q=test&from=en&to=zh&appid=demo&salt=123&sign=dummy" > /dev/null; then
            print_success "Translation endpoint working"
        fi
        
    else
        print_error "Health check failed"
        kill $SERVICE_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop test service
    kill $SERVICE_PID 2>/dev/null || true
    wait $SERVICE_PID 2>/dev/null || true
    
    print_success "Deployment test completed successfully"
}

# Display deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo
    print_status "Deployment Information:"
    echo "  Mode: $DEPLOYMENT_MODE"
    
    local port=$(grep "API__PORT" .env | cut -d'=' -f2 || echo "8888")
    local host=$(grep "API__HOST" .env | cut -d'=' -f2 || echo "127.0.0.1")
    
    if [[ "$DEPLOYMENT_MODE" == "local" ]]; then
        echo "  Service URL: http://127.0.0.1:$port"
    else
        echo "  Internal URL: http://$host:$port"
        local external_host=$(grep "DEPLOYMENT__EXTERNAL_HOST" .env | cut -d'=' -f2 || echo "")
        if [[ -n "$external_host" && "$external_host" != "your-external-ip-or-domain" ]]; then
            echo "  External URL: http://$external_host:$port"
        fi
    fi
    
    echo
    print_status "Available endpoints:"
    echo "  Health check: /api/health"
    echo "  Translation: /api/trans/vip/translate"
    echo "  Demo: /api/demo/translate"
    echo "  Discovery: /api/discovery/info"
    echo "  Documentation: /docs"
    echo
    print_status "To start the service:"
    echo "  source .venv/bin/activate"
    echo "  python run.py"
    echo
    print_status "To integrate with systemDesign:"
    echo "  Update systemDesign configuration to point to this service"
    echo "  Use service discovery endpoint for automatic configuration"
}

# Main deployment process
main() {
    check_prerequisites
    setup_python_env
    setup_ollama
    configure_environment
    test_deployment
    show_deployment_info
}

# Run main function
main
