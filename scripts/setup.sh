#!/bin/bash
# ================================================================================================
# LLM Translation Service Setup Script for Unix/Linux/macOS
# Updated for organized directory structure and enhanced functionality
# ================================================================================================

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${GREEN}Setting up LLM Translation Service for Unix/Linux/macOS...${NC}"

# Ensure we're in the project root directory
PROJECT_ROOT=$(dirname "$(dirname "$(realpath "$0")")")
cd "$PROJECT_ROOT"
echo -e "${CYAN}Working in project directory: $PROJECT_ROOT${NC}"

# Check Python version
print_info "Checking Python version..."

# Find the best Python executable
PYTHON_EXEC=""
for python_cmd in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$python_cmd" &> /dev/null; then
        VERSION_CHECK=$($python_cmd -c "import sys; print(sys.version_info[:2])" 2>/dev/null)
        if [[ $? -eq 0 ]]; then
            MAJOR=$(echo $VERSION_CHECK | cut -d'(' -f2 | cut -d',' -f1)
            MINOR=$(echo $VERSION_CHECK | cut -d',' -f2 | tr -d ' )')
            if [[ $MAJOR -eq 3 ]] && [[ $MINOR -ge 10 ]]; then
                PYTHON_EXEC="$python_cmd"
                PYTHON_VERSION=$($python_cmd --version 2>&1)
                print_success "Found: $PYTHON_VERSION at $(which $python_cmd)"
                break
            fi
        fi
    fi
done

if [[ -z "$PYTHON_EXEC" ]]; then
    print_error "Python 3.10+ not found"
    print_warning "Please install Python 3.10+ from your package manager or https://python.org"
    exit 1
fi

# Create virtual environment
print_info "Creating virtual environment..."
$PYTHON_EXEC -m venv .venv

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
$PYTHON_EXEC -m pip install --upgrade pip

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Create logs directory if it doesn't exist
if [[ ! -d "logs" ]]; then
    mkdir -p logs
    print_success "Created logs directory"
fi

# Copy environment configuration
print_info "Setting up environment configuration..."
if [[ ! -f ".env" ]]; then
    if [[ -f "config/.env.example" ]]; then
        cp "config/.env.example" ".env"
        print_success "Created .env file from template. Please review and update as needed."
    else
        print_warning ".env.example not found in config directory"
    fi
fi

# Check for Ollama
print_info "Checking for Ollama..."

if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null)
    print_success "Ollama found: $OLLAMA_VERSION"
    
    print_info "Pulling default model..."
    ollama pull llama3.1:8b || print_warning "Failed to pull model - you may need to do this manually"
else
    print_error "Ollama not found in PATH. Please install Ollama from https://ollama.ai/"
    case "$OSTYPE" in
        darwin*)
            print_warning "For macOS: Use the installer from https://ollama.ai/download"
            ;;
        linux*)
            print_warning "For Linux: curl -fsSL https://ollama.ai/install.sh | sh"
            ;;
    esac
fi

# Check for Redis
print_info "Checking for Redis..."
if command -v redis-server &> /dev/null; then
    print_success "Redis found."
    
    # Try to start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        print_info "Starting Redis server..."
        if command -v systemctl &> /dev/null; then
            sudo systemctl start redis 2>/dev/null || redis-server --daemonize yes 2>/dev/null || true
        else
            redis-server --daemonize yes 2>/dev/null || true
        fi
    fi
else
    print_warning "Redis not found. You can:"
    case "$OSTYPE" in
        darwin*)
            print_warning "  1. Install with Homebrew: brew install redis"
            print_warning "  2. Use Docker: docker run -d -p 6379:6379 redis:alpine"
            ;;
        linux*)
            print_warning "  1. Install with package manager: sudo apt-get install redis-server (Ubuntu/Debian)"
            print_warning "  2. Install with package manager: sudo yum install redis (RHEL/CentOS)"
            print_warning "  3. Use Docker: docker run -d -p 6379:6379 redis:alpine"
            ;;
    esac
    print_warning "  4. The service will work without Redis (using in-memory cache)"
fi

echo ""
print_success "Setup complete! To start the service:"
echo -e "${NC}1. Activate virtual environment: ${YELLOW}source .venv/bin/activate${NC}"
echo -e "${NC}2. Start the service: ${YELLOW}python run.py${NC}"
echo -e "${NC}3. Access the API at: ${YELLOW}http://localhost:8000${NC}"
echo ""
echo -e "${CYAN}For production deployment, run: ${YELLOW}./scripts/production-setup.sh${NC}"
echo -e "${CYAN}For documentation: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}📂 Project Structure:${NC}"
echo -e "${NC}  • Documentation: ${YELLOW}./docs/${NC}"
echo -e "${NC}  • Scripts: ${YELLOW}./scripts/${NC}"
echo -e "${NC}  • Configuration: ${YELLOW}./config/${NC}"
echo -e "${NC}  • Source Code: ${YELLOW}./src/${NC}"
echo -e "${NC}  • Tests: ${YELLOW}./tests/${NC}"
echo -e "${NC}  • Logs: ${YELLOW}./logs/${NC}"
