#!/bin/bash

# LLM Translation Service Startup Script (Linux/macOS)
# Compatible version of the Windows PowerShell script

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

# Script header
echo -e "${MAGENTA}"
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                        LLM Translation Service Startup                        ║"
echo "║                                 Bash Script                                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_info "Starting LLM Translation Service setup and validation..."
print_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# Check prerequisites
print_step "Checking prerequisites..."

# Check if we're in the right directory
if [[ ! -d "src" ]] || [[ ! -f "run.py" ]] || [[ ! -d ".venv" ]]; then
    print_error "Not in project directory or missing required files/folders"
    print_info "Expected: src/, run.py, .venv/"
    print_info "Current directory: $(pwd)"
    exit 1
fi
print_success "Project structure validated"

# Check Ollama installation
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null)
    print_success "Ollama found: $OLLAMA_VERSION"
else
    print_error "Ollama not installed or not in PATH"
    print_info "Please install Ollama from https://ollama.ai/"
    exit 1
fi

# Check for required model
if ollama list 2>/dev/null | grep -q "llama3.1:8b"; then
    print_success "Required model llama3.1:8b found"
else
    print_warning "Model llama3.1:8b not found"
    print_info "Run: ollama pull llama3.1:8b"
    exit 1
fi

# Check Python in virtual environment
PYTHON_PATH="./.venv/bin/python"
if [[ -f "$PYTHON_PATH" ]]; then
    PYTHON_VERSION=$($PYTHON_PATH --version 2>/dev/null)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Virtual environment Python not found at $PYTHON_PATH"
    exit 1
fi

echo

# Resolve environment conflicts
print_step "Resolving environment variable conflicts..."
unset ollama
print_success "Cleared any conflicting environment variables"
echo

# Test configuration
print_step "Testing configuration loading..."
if $PYTHON_PATH test_config.py; then
    print_success "Configuration loaded successfully"
else
    print_error "Configuration test failed"
    exit 1
fi
echo

# Show service information
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                               Service Information                              ║"
echo "╠════════════════════════════════════════════════════════════════════════════════╣"
echo "║ Service URL:     http://localhost:8000                                        ║"
echo "║ Documentation:   http://localhost:8000/docs                                   ║"
echo "║ Health Check:    http://localhost:8000/api/health                             ║"
echo "║                                                                                ║"
echo "║ Test Commands:                                                                 ║"
echo "║ curl http://localhost:8000/api/health                                         ║"
echo "║ curl -X POST http://localhost:8000/api/demo/translate \\                       ║"
echo "║      -d \"q=hello world&from=en&to=zh\"                                         ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_warning "Press Ctrl+C to stop the service"
echo

# Start the service
print_step "Starting LLM Translation Service..."
$PYTHON_PATH run.py
