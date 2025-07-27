#!/bin/bash
# ================================================================================================
# LLM Translation Service - Online Deployment Script
# This script configures your translation service for internet access
# ================================================================================================

# Parse command line arguments
SKIP_FIREWALL=false
TEST_ONLY=false
EXTERNAL_PORT="8080"
INTERNAL_PORT="8000"

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-firewall)
            SKIP_FIREWALL=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --external-port)
            EXTERNAL_PORT="$2"
            shift 2
            ;;
        --internal-port)
            INTERNAL_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-firewall] [--test-only] [--external-port PORT] [--internal-port PORT]"
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
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${CYAN}🌐 LLM Translation Service - Online Deployment Setup${NC}"
echo -e "${CYAN}=================================================${NC}"

# Check if running with appropriate privileges for firewall
if [[ "$SKIP_FIREWALL" == "false" ]] && [[ $EUID -ne 0 ]] && [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_warning "Root privileges may be required for firewall configuration on Linux"
    print_warning "Please run with sudo or use --skip-firewall flag"
fi

# Step 1: Check prerequisites
echo -e "\n${GREEN}🔍 Step 1: Checking Prerequisites...${NC}"

# Check if Ollama is running
if pgrep -f "ollama" > /dev/null; then
    print_success "Ollama is running"
else
    print_error "Ollama is not running. Please start Ollama first."
    print_warning "Run: ollama serve"
    exit 1
fi

# Check if Redis is available
if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null; then
    print_success "Redis is running"
else
    print_warning "Redis is not running - will use in-memory cache"
fi

# Step 2: Configure firewall
if [[ "$SKIP_FIREWALL" == "false" ]]; then
    echo -e "\n${GREEN}🔥 Step 2: Configuring Firewall...${NC}"
    
    case "$OSTYPE" in
        linux*)
            if command -v ufw &> /dev/null; then
                # Ubuntu/Debian UFW
                print_info "Configuring UFW firewall..."
                sudo ufw allow $INTERNAL_PORT/tcp comment "LLM Translation Service" 2>/dev/null || print_warning "Failed to configure UFW"
                sudo ufw allow 8001/tcp comment "LLM Translation Metrics" 2>/dev/null || print_warning "Failed to configure UFW metrics"
                print_success "UFW firewall rules configured for ports ${INTERNAL_PORT} and 8001"
            elif command -v firewall-cmd &> /dev/null; then
                # RHEL/CentOS/Fedora firewalld
                print_info "Configuring firewalld..."
                sudo firewall-cmd --permanent --add-port=${INTERNAL_PORT}/tcp 2>/dev/null || print_warning "Failed to configure firewalld"
                sudo firewall-cmd --permanent --add-port=8001/tcp 2>/dev/null || print_warning "Failed to configure firewalld"
                sudo firewall-cmd --reload 2>/dev/null || true
                print_success "Firewalld rules configured for ports ${INTERNAL_PORT} and 8001"
            elif command -v iptables &> /dev/null; then
                # Direct iptables
                print_info "Configuring iptables..."
                sudo iptables -A INPUT -p tcp --dport $INTERNAL_PORT -j ACCEPT 2>/dev/null || print_warning "Failed to configure iptables"
                sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT 2>/dev/null || print_warning "Failed to configure iptables"
                print_success "Iptables rules configured for ports ${INTERNAL_PORT} and 8001"
            else
                print_warning "No supported firewall found. Please configure manually."
            fi
            ;;
        darwin*)
            # macOS
            print_info "macOS detected. Firewall configuration may require manual setup in System Preferences."
            print_warning "Go to System Preferences > Security & Privacy > Firewall > Firewall Options"
            print_warning "Add exceptions for ports ${INTERNAL_PORT} and 8001"
            ;;
    esac
else
    echo -e "\n${YELLOW}🔥 Step 2: Skipping firewall configuration (as requested)${NC}"
fi

# Step 3: Get network information
echo -e "\n${GREEN}🌐 Step 3: Network Configuration Information...${NC}"

# Get local IP addresses
local_ips=()
case "$OSTYPE" in
    linux*)
        local_ips=($(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+'))
        if [[ ${#local_ips[@]} -eq 0 ]]; then
            local_ips=($(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'))
        fi
        ;;
    darwin*)
        local_ips=($(ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | awk '{print $2}'))
        ;;
esac

echo -e "${CYAN}📍 Your local IP addresses:${NC}"
for ip in "${local_ips[@]}"; do
    echo -e "   • $ip"
done

# Get public IP (if available)
public_ip=""
if command -v curl &> /dev/null; then
    public_ip=$(curl -s --max-time 10 "https://api.ipify.org" 2>/dev/null || echo "")
fi

if [[ -n "$public_ip" ]]; then
    echo -e "${CYAN}🌍 Your public IP address: $public_ip${NC}"
else
    print_warning "Could not retrieve public IP address"
fi

# Step 4: Display access URLs
echo -e "\n${GREEN}🔗 Step 4: Service Access Information...${NC}"

echo -e "${CYAN}📱 Local Network Access URLs:${NC}"
for ip in "${local_ips[@]}"; do
    echo -e "   • http://$ip:${INTERNAL_PORT}"
    echo -e "   • http://$ip:${INTERNAL_PORT}/docs (API Documentation)"
done

if [[ -n "$public_ip" ]]; then
    echo -e "\n${CYAN}🌍 Internet Access URLs (after router configuration):${NC}"
    echo -e "   • http://$public_ip:${EXTERNAL_PORT}"
    echo -e "   • http://$public_ip:${EXTERNAL_PORT}/docs"
fi

# Step 5: Router configuration instructions
echo -e "\n${GREEN}🔧 Step 5: Router Port Forwarding Setup...${NC}"
echo -e "${NC}To enable internet access, configure your router:${NC}"
echo -e "${YELLOW}1. Open your router admin panel (usually http://192.168.1.1 or http://192.168.0.1)${NC}"
echo -e "${YELLOW}2. Navigate to Port Forwarding / Virtual Server / NAT settings${NC}"
echo -e "${YELLOW}3. Add a new port forwarding rule:${NC}"
echo -e "   • Service Name: LLM Translation Service"
echo -e "   • External Port: ${EXTERNAL_PORT}"
if [[ ${#local_ips[@]} -gt 0 ]]; then
    echo -e "   • Internal IP: ${local_ips[0]}"
fi
echo -e "   • Internal Port: ${INTERNAL_PORT}"
echo -e "   • Protocol: TCP"
echo -e "${YELLOW}4. Save and apply the settings${NC}"

# Step 6: Security recommendations
echo -e "\n${GREEN}🛡️  Step 6: Security Recommendations...${NC}"
echo -e "${NC}For production deployment, consider:${NC}"
echo -e "${YELLOW}• Change the default SECRET_KEY in .env file${NC}"
echo -e "${YELLOW}• Set up API key authentication${NC}"
echo -e "${YELLOW}• Configure rate limiting${NC}"
echo -e "${YELLOW}• Use HTTPS with SSL certificates${NC}"
echo -e "${YELLOW}• Monitor access logs regularly${NC}"

# Step 7: Test local access (if not test-only mode)
if [[ "$TEST_ONLY" == "false" ]] && [[ ${#local_ips[@]} -gt 0 ]]; then
    echo -e "\n${GREEN}🧪 Step 7: Testing Local Access...${NC}"
    
    local_ip="${local_ips[0]}"
    test_url="http://$local_ip:${INTERNAL_PORT}"
    
    echo -e "${NC}Testing connection to $test_url...${NC}"
    
    if command -v curl &> /dev/null; then
        if curl -s --max-time 10 "$test_url" > /dev/null 2>&1; then
            print_success "Service is accessible on local network!"
        else
            print_error "Could not connect to service. Make sure it's running."
            print_warning "Start the service with: python run.py"
        fi
    else
        print_warning "curl not available for testing. Please test manually."
    fi
fi

echo -e "\n${GREEN}🎉 Online Deployment Setup Complete!${NC}"
echo -e "${CYAN}=================================================${NC}"

# Step 8: Display next steps
echo -e "\n${CYAN}📋 Next Steps:${NC}"
echo -e "${NC}1. Start the translation service: ${YELLOW}python run.py${NC}"
echo -e "${NC}2. Test local access using the URLs above${NC}"
echo -e "${NC}3. Configure router port forwarding for internet access${NC}"
echo -e "${NC}4. Test internet access from external devices${NC}"
echo -e "${NC}5. Monitor logs and performance${NC}"

echo -e "\n${CYAN}📖 For detailed documentation, see:${NC}"
echo -e "${NC}• docs/setup/PRODUCTION_SETUP_GUIDE.md${NC}"
echo -e "${NC}• docs/guides/ROUTER_SETUP_GUIDE.md${NC}"
echo -e "${NC}• docs/guides/REMOTE_ACCESS_GUIDE.md${NC}"
