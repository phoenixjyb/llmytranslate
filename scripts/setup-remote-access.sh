#!/bin/bash
# ================================================================================================
# Remote Access Setup Script for LLM Translation Service
# Usage: ./setup_remote_access.sh [ngrok|firewall|local|info]
# ================================================================================================

# Parse command line arguments
MODE="info"

if [[ $# -gt 0 ]]; then
    case "$1" in
        ngrok|zerotier|firewall|local|info)
            MODE="$1"
            ;;
        -h|--help)
            echo "Usage: $0 [ngrok|zerotier|firewall|local|info]"
            echo "Modes:"
            echo "  info      - Show available setup modes (default)"
            echo "  local     - Get local network access info"
            echo "  ngrok     - Set up ngrok tunnel for internet access"
            echo "  zerotier  - Set up ZeroTier VPN for permanent access"
            echo "  firewall  - Configure system firewall"
            exit 0
            ;;
        *)
            echo "Error: Invalid mode '$1'"
            echo "Valid modes: ngrok, zerotier, firewall, local, info"
            exit 1
            ;;
    esac
fi

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${GREEN}🌐 LLM Translation Service - Remote Access Setup${NC}"
echo -e "${GREEN}==================================================${NC}"

case "$MODE" in
    info)
        echo -e "\n${YELLOW}📋 Available setup modes:${NC}"
        echo -e "  ${CYAN}local${NC}     - Get local network access info"
        echo -e "  ${CYAN}ngrok${NC}     - Set up ngrok tunnel for internet access"
        echo -e "  ${CYAN}zerotier${NC}  - Set up ZeroTier VPN for permanent access"
        echo -e "  ${CYAN}firewall${NC}  - Configure system firewall"
        echo -e "\n${GRAY}Usage: $0 [mode]${NC}"
        echo -e "\n${YELLOW}💡 Quick comparison:${NC}"
        echo -e "  ${GRAY}Ngrok    = Easy demos, temporary access, public URLs${NC}"
        echo -e "  ${GRAY}ZeroTier = Permanent VPN, private network, multiple devices${NC}"
        ;;
    
    local)
        echo -e "\n${YELLOW}🏠 Local Network Access Setup${NC}"
        echo -e "${YELLOW}==============================${NC}"
        
        # Get local IP addresses
        local ip_addresses=()
        case "$OSTYPE" in
            linux*)
                ip_addresses=($(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+'))
                if [[ ${#ip_addresses[@]} -eq 0 ]]; then
                    ip_addresses=($(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | grep -v '^127\|^169\.254'))
                fi
                ;;
            darwin*)
                ip_addresses=($(ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | grep -v '169.254' | awk '{print $2}'))
                ;;
        esac
        
        if [[ ${#ip_addresses[@]} -gt 0 ]]; then
            print_success "Your local IP addresses:"
            for ip in "${ip_addresses[@]}"; do
                echo -e "   ${CYAN}http://$ip:8000${NC}"
            done
            
            echo -e "\n${YELLOW}📱 Test commands for other devices on your network:${NC}"
            local primary_ip="${ip_addresses[0]}"
            echo -e "${GRAY}curl http://$primary_ip:8000/api/health${NC}"
            echo -e "${GRAY}curl -X POST \"http://$primary_ip:8000/api/demo/translate\" -H \"Content-Type: application/x-www-form-urlencoded\" -d \"q=Hello world&from=en&to=zh\"${NC}"
        else
            print_error "Could not detect local IP addresses"
            print_info "Make sure you're connected to a network"
        fi
        
        echo -e "\n${YELLOW}🔧 Quick local network setup:${NC}"
        echo -e "1. ${GRAY}Make sure the service is running: ${CYAN}./scripts/start-service.sh${NC}"
        echo -e "2. ${GRAY}Check firewall allows connections on port 8000${NC}"
        echo -e "3. ${GRAY}Test from another device using the URLs above${NC}"
        ;;
    
    ngrok)
        echo -e "\n${YELLOW}🚇 Ngrok Internet Access Setup${NC}"
        echo -e "${YELLOW}===============================${NC}"
        
        if ! command -v ngrok &> /dev/null; then
            print_error "Ngrok not found"
            echo -e "\n${YELLOW}📥 Install ngrok:${NC}"
            case "$OSTYPE" in
                darwin*)
                    echo -e "  ${GRAY}macOS: ${CYAN}brew install ngrok${NC}"
                    ;;
                linux*)
                    echo -e "  ${GRAY}Linux: Download from ${CYAN}https://ngrok.com/download${NC}"
                    echo -e "  ${GRAY}Or use snap: ${CYAN}sudo snap install ngrok${NC}"
                    ;;
            esac
            echo -e "\n${YELLOW}🔑 Setup steps:${NC}"
            echo -e "1. ${GRAY}Sign up at ${CYAN}https://dashboard.ngrok.com/signup${NC}"
            echo -e "2. ${GRAY}Get your auth token from ${CYAN}https://dashboard.ngrok.com/get-started/your-authtoken${NC}"
            echo -e "3. ${GRAY}Run: ${CYAN}ngrok config add-authtoken YOUR_TOKEN${NC}"
            echo -e "4. ${GRAY}Run: ${CYAN}./scripts/setup_ngrok.sh --auth-token YOUR_TOKEN${NC}"
        else
            local ngrok_version=$(ngrok version 2>/dev/null | head -1)
            print_success "Ngrok found: $ngrok_version"
            
            print_info "Quick setup:"
            echo -e "1. ${GRAY}Get auth token from ${CYAN}https://dashboard.ngrok.com/get-started/your-authtoken${NC}"
            echo -e "2. ${GRAY}Run: ${CYAN}./scripts/setup_ngrok.sh --auth-token YOUR_TOKEN${NC}"
            echo -e "3. ${GRAY}Or start service with ngrok: ${CYAN}./scripts/start-service.sh --with-ngrok${NC}"
        fi
        ;;
    
    zerotier)
        echo -e "\n${YELLOW}🔗 ZeroTier VPN Setup${NC}"
        echo -e "${YELLOW}====================${NC}"
        
        if ! command -v zerotier-cli &> /dev/null; then
            print_warning "ZeroTier not installed"
            echo -e "\n${YELLOW}📥 Install ZeroTier:${NC}"
            case "$OSTYPE" in
                darwin*)
                    echo -e "  ${GRAY}macOS: Download from ${CYAN}https://www.zerotier.com/download/${NC}"
                    ;;
                linux*)
                    echo -e "  ${GRAY}Linux: ${CYAN}curl -s https://install.zerotier.com | sudo bash${NC}"
                    ;;
            esac
        else
            print_success "ZeroTier is installed"
            local zt_status=$(zerotier-cli info 2>/dev/null)
            if [[ $? -eq 0 ]]; then
                echo -e "  ${GRAY}Status: $zt_status${NC}"
            fi
        fi
        
        echo -e "\n${YELLOW}🔧 Setup steps:${NC}"
        echo -e "1. ${GRAY}Create account at ${CYAN}https://my.zerotier.com/${NC}"
        echo -e "2. ${GRAY}Create a new network${NC}"
        echo -e "3. ${GRAY}Join network: ${CYAN}sudo zerotier-cli join NETWORK_ID${NC}"
        echo -e "4. ${GRAY}Authorize device in ZeroTier Central${NC}"
        echo -e "5. ${GRAY}Access service via ZeroTier IP${NC}"
        ;;
    
    firewall)
        echo -e "\n${YELLOW}🔥 Firewall Configuration${NC}"
        echo -e "${YELLOW}=========================${NC}"
        
        case "$OSTYPE" in
            linux*)
                if command -v ufw &> /dev/null; then
                    print_info "Configuring UFW firewall..."
                    echo -e "  ${GRAY}Allow port 8000: ${CYAN}sudo ufw allow 8000/tcp${NC}"
                    echo -e "  ${GRAY}Check status: ${CYAN}sudo ufw status${NC}"
                elif command -v firewall-cmd &> /dev/null; then
                    print_info "Configuring firewalld..."
                    echo -e "  ${GRAY}Allow port 8000: ${CYAN}sudo firewall-cmd --permanent --add-port=8000/tcp${NC}"
                    echo -e "  ${GRAY}Reload: ${CYAN}sudo firewall-cmd --reload${NC}"
                elif command -v iptables &> /dev/null; then
                    print_info "Configuring iptables..."
                    echo -e "  ${GRAY}Allow port 8000: ${CYAN}sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT${NC}"
                else
                    print_warning "No supported firewall found"
                fi
                ;;
            darwin*)
                print_info "macOS firewall configuration:"
                echo -e "1. ${GRAY}Open System Preferences > Security & Privacy${NC}"
                echo -e "2. ${GRAY}Click Firewall tab${NC}"
                echo -e "3. ${GRAY}Click Firewall Options${NC}"
                echo -e "4. ${GRAY}Add Python to allowed applications${NC}"
                echo -e "5. ${GRAY}Or disable firewall for testing${NC}"
                ;;
        esac
        
        echo -e "\n${YELLOW}🧪 Test firewall:${NC}"
        echo -e "  ${GRAY}From another device: ${CYAN}curl http://YOUR_IP:8000/api/health${NC}"
        ;;
esac

echo -e "\n${GREEN}🎉 Remote access setup information provided!${NC}"
echo -e "${GRAY}For more detailed setup guides, check the docs/ directory${NC}"
