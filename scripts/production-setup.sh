#!/bin/bash
# ================================================================================================
# Production Server Setup Script for Unix/Linux/macOS
# Transforms your system into an internet-accessible translation server
# Updated for organized directory structure
# ================================================================================================

# Parse command line arguments
DOMAIN="localhost"
PORT=8000
EXTERNAL_PORT=8080
ENABLE_HTTPS=false
INSTALL_NGINX=true
ALLOWED_IPS=""
SETUP_DDNS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --external-port)
            EXTERNAL_PORT="$2"
            shift 2
            ;;
        --enable-https)
            ENABLE_HTTPS=true
            shift
            ;;
        --no-nginx)
            INSTALL_NGINX=false
            shift
            ;;
        --allowed-ips)
            ALLOWED_IPS="$2"
            shift 2
            ;;
        --setup-ddns)
            SETUP_DDNS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --domain DOMAIN          Domain name (default: localhost)"
            echo "  --port PORT             Internal port (default: 8000)"
            echo "  --external-port PORT    External port (default: 8080)"
            echo "  --enable-https          Enable HTTPS configuration"
            echo "  --no-nginx              Skip nginx installation"
            echo "  --allowed-ips IPS       Comma-separated allowed IPs"
            echo "  --setup-ddns            Setup dynamic DNS"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

echo -e "${CYAN}🌐 LLM Translation Server - Production Setup${NC}"
echo -e "${CYAN}==========================================${NC}"

# Ensure we're in the project root directory
PROJECT_ROOT=$(dirname "$(dirname "$(realpath "$0")")")
cd "$PROJECT_ROOT"
echo -e "${GREEN}Working in project directory: $PROJECT_ROOT${NC}"

# Check if running with appropriate privileges
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root - some operations may not be necessary"
else
    print_info "Running as regular user - some operations may require sudo"
fi

# 1. System Information
echo -e "\n${YELLOW}📊 System Information:${NC}"
COMPUTER_NAME=$(hostname)
LOCAL_IP=""
PUBLIC_IP=""

# Get local IP
case "$OSTYPE" in
    linux*)
        LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
        if [[ -z "$LOCAL_IP" ]]; then
            LOCAL_IP=$(hostname -I | awk '{print $1}')
        fi
        ;;
    darwin*)
        LOCAL_IP=$(ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)
        ;;
esac

# Get public IP
if command -v curl &> /dev/null; then
    PUBLIC_IP=$(curl -s --max-time 10 "https://ipinfo.io/ip" 2>/dev/null || echo "Unable to detect")
else
    PUBLIC_IP="curl not available"
fi

echo -e "${WHITE}Computer Name: $COMPUTER_NAME${NC}"
echo -e "${WHITE}Local IP: $LOCAL_IP${NC}"
echo -e "${WHITE}Public IP: $PUBLIC_IP${NC}"

# 2. Configure System Firewall
echo -e "\n${YELLOW}🔥 Configuring System Firewall...${NC}"

case "$OSTYPE" in
    linux*)
        if command -v ufw &> /dev/null; then
            print_info "Configuring UFW firewall..."
            if [[ $EUID -eq 0 ]] || sudo -n true 2>/dev/null; then
                sudo ufw allow $PORT/tcp comment "LLM Translation Service" 2>/dev/null || print_warning "Failed to configure UFW"
                sudo ufw allow $EXTERNAL_PORT/tcp comment "LLM Translation External" 2>/dev/null || print_warning "Failed to configure UFW external"
                if [[ "$ENABLE_HTTPS" == "true" ]]; then
                    sudo ufw allow 443/tcp comment "HTTPS" 2>/dev/null || print_warning "Failed to configure HTTPS"
                fi
                print_success "Firewall rules configured"
            else
                print_warning "Sudo required for firewall configuration"
                echo -e "  ${GRAY}Run manually: sudo ufw allow $PORT/tcp${NC}"
            fi
        elif command -v firewall-cmd &> /dev/null; then
            print_info "Configuring firewalld..."
            if [[ $EUID -eq 0 ]] || sudo -n true 2>/dev/null; then
                sudo firewall-cmd --permanent --add-port=$PORT/tcp 2>/dev/null || print_warning "Failed to configure firewalld"
                sudo firewall-cmd --permanent --add-port=$EXTERNAL_PORT/tcp 2>/dev/null || print_warning "Failed to configure firewalld"
                sudo firewall-cmd --reload 2>/dev/null || true
                print_success "Firewalld rules configured"
            else
                print_warning "Sudo required for firewall configuration"
            fi
        else
            print_warning "No supported firewall found"
        fi
        ;;
    darwin*)
        print_info "macOS detected - manual firewall configuration may be needed"
        print_warning "Check System Preferences > Security & Privacy > Firewall"
        ;;
esac

# 3. Install and Configure Nginx (if requested)
if [[ "$INSTALL_NGINX" == "true" ]]; then
    echo -e "\n${YELLOW}🌐 Setting up Nginx reverse proxy...${NC}"
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        print_info "Installing nginx..."
        case "$OSTYPE" in
            linux*)
                if command -v apt-get &> /dev/null; then
                    sudo apt-get update && sudo apt-get install -y nginx
                elif command -v yum &> /dev/null; then
                    sudo yum install -y nginx
                elif command -v dnf &> /dev/null; then
                    sudo dnf install -y nginx
                else
                    print_error "Package manager not supported. Please install nginx manually."
                fi
                ;;
            darwin*)
                if command -v brew &> /dev/null; then
                    brew install nginx
                else
                    print_error "Homebrew not found. Please install nginx manually."
                fi
                ;;
        esac
    else
        print_success "Nginx already installed"
    fi
    
    # Create nginx configuration
    if command -v nginx &> /dev/null; then
        print_info "Creating nginx configuration..."
        
        NGINX_CONFIG="/tmp/llm-translation.conf"
        cat > "$NGINX_CONFIG" << EOF
server {
    listen $EXTERNAL_PORT;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Enable CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
    }
    
    # Handle preflight requests
    location ~ ^/api/.*$ {
        if (\$request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 200;
        }
        
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        
        # Copy to nginx sites directory
        case "$OSTYPE" in
            linux*)
                if [[ -d "/etc/nginx/sites-available" ]]; then
                    sudo cp "$NGINX_CONFIG" "/etc/nginx/sites-available/llm-translation"
                    sudo ln -sf "/etc/nginx/sites-available/llm-translation" "/etc/nginx/sites-enabled/"
                elif [[ -d "/etc/nginx/conf.d" ]]; then
                    sudo cp "$NGINX_CONFIG" "/etc/nginx/conf.d/llm-translation.conf"
                fi
                ;;
            darwin*)
                if [[ -d "/usr/local/etc/nginx/servers" ]]; then
                    sudo cp "$NGINX_CONFIG" "/usr/local/etc/nginx/servers/llm-translation.conf"
                fi
                ;;
        esac
        
        rm -f "$NGINX_CONFIG"
        print_success "Nginx configuration created"
        
        # Test and reload nginx
        if nginx -t 2>/dev/null; then
            sudo systemctl reload nginx 2>/dev/null || sudo service nginx reload 2>/dev/null || brew services restart nginx 2>/dev/null
            print_success "Nginx reloaded successfully"
        else
            print_error "Nginx configuration test failed"
        fi
    fi
else
    print_info "Skipping nginx installation (--no-nginx specified)"
fi

# 4. Setup HTTPS (if requested)
if [[ "$ENABLE_HTTPS" == "true" ]]; then
    echo -e "\n${YELLOW}🔐 Setting up HTTPS...${NC}"
    
    if command -v certbot &> /dev/null; then
        print_info "Certbot found - can setup Let's Encrypt SSL"
        echo -e "  ${GRAY}Run: sudo certbot --nginx -d $DOMAIN${NC}"
    else
        print_warning "Certbot not found. Install it for automatic SSL setup:"
        case "$OSTYPE" in
            linux*)
                echo -e "  ${GRAY}Ubuntu/Debian: sudo apt-get install certbot python3-certbot-nginx${NC}"
                echo -e "  ${GRAY}RHEL/CentOS: sudo yum install certbot python3-certbot-nginx${NC}"
                ;;
            darwin*)
                echo -e "  ${GRAY}macOS: brew install certbot${NC}"
                ;;
        esac
    fi
fi

# 5. Create systemd service (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "\n${YELLOW}🔧 Creating systemd service...${NC}"
    
    SERVICE_FILE="/tmp/llm-translation.service"
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=LLM Translation Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_ROOT/.venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    if [[ $EUID -eq 0 ]] || sudo -n true 2>/dev/null; then
        sudo cp "$SERVICE_FILE" "/etc/systemd/system/llm-translation.service"
        sudo systemctl daemon-reload
        sudo systemctl enable llm-translation.service
        print_success "Systemd service created and enabled"
        echo -e "  ${GRAY}Start with: sudo systemctl start llm-translation${NC}"
        echo -e "  ${GRAY}Check status: sudo systemctl status llm-translation${NC}"
    else
        print_warning "Sudo required for systemd service creation"
        echo -e "  ${GRAY}Service file created at: $SERVICE_FILE${NC}"
    fi
    
    rm -f "$SERVICE_FILE"
fi

# 6. Router Setup Instructions
echo -e "\n${YELLOW}🔧 Router Port Forwarding Setup:${NC}"
echo -e "${WHITE}To enable internet access, configure your router:${NC}"
echo -e "1. ${GRAY}Open router admin panel (usually http://192.168.1.1)${NC}"
echo -e "2. ${GRAY}Navigate to Port Forwarding / Virtual Server${NC}"
echo -e "3. ${GRAY}Add rule: External port $EXTERNAL_PORT → Internal IP $LOCAL_IP → Internal port $EXTERNAL_PORT${NC}"
echo -e "4. ${GRAY}Save and apply settings${NC}"

# 7. Security Recommendations
echo -e "\n${YELLOW}🛡️ Security Recommendations:${NC}"
echo -e "• ${GRAY}Change default SECRET_KEY in .env file${NC}"
echo -e "• ${GRAY}Set up API key authentication${NC}"
echo -e "• ${GRAY}Configure rate limiting${NC}"
echo -e "• ${GRAY}Use HTTPS in production${NC}"
echo -e "• ${GRAY}Monitor access logs regularly${NC}"
echo -e "• ${GRAY}Keep system and dependencies updated${NC}"

# 8. Final URLs and Testing
echo -e "\n${GREEN}🎉 Production Setup Complete!${NC}"
echo -e "${CYAN}===========================================${NC}"

echo -e "\n${YELLOW}📍 Access URLs:${NC}"
echo -e "• ${WHITE}Local: http://localhost:$PORT${NC}"
echo -e "• ${WHITE}Network: http://$LOCAL_IP:$EXTERNAL_PORT${NC}"
if [[ "$PUBLIC_IP" != "Unable to detect" ]] && [[ "$PUBLIC_IP" != "curl not available" ]]; then
    echo -e "• ${WHITE}Internet: http://$PUBLIC_IP:$EXTERNAL_PORT (after router config)${NC}"
fi

echo -e "\n${YELLOW}🧪 Test Commands:${NC}"
echo -e "${GRAY}curl http://$LOCAL_IP:$EXTERNAL_PORT/api/health${NC}"
echo -e "${GRAY}curl -X POST \"http://$LOCAL_IP:$EXTERNAL_PORT/api/demo/translate\" -H \"Content-Type: application/x-www-form-urlencoded\" -d \"q=Hello world&from=en&to=zh\"${NC}"

echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "1. ${GRAY}Start the service: ${CYAN}./scripts/start-service.sh --production${NC}"
echo -e "2. ${GRAY}Test local access using URLs above${NC}"
echo -e "3. ${GRAY}Configure router port forwarding${NC}"
echo -e "4. ${GRAY}Test internet access from external devices${NC}"
echo -e "5. ${GRAY}Monitor logs and performance${NC}"

echo -e "\n${CYAN}📖 Documentation: docs/setup/PRODUCTION_SETUP_GUIDE.md${NC}"
