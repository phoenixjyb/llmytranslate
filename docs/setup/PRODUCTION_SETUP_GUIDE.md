# Production Server Setup Guide for Windows

## 🌐 Internet-Accessible Translation Server Setup

This guide will help you turn your Windows PC into a publicly accessible translation server.

## 📋 Prerequisites

- ✅ LLM Translation Service running locally
- ✅ Windows PC with stable internet connection
- ✅ Router admin access for port forwarding
- ✅ Basic networking knowledge

## 🔧 Step-by-Step Setup

### 1. **Network Configuration**

#### A. Static Local IP (Recommended)
```powershell
# Check current IP configuration
ipconfig /all

# Set static IP (replace with your network details)
netsh interface ip set address "Wi-Fi" static 192.168.1.100 255.255.255.0 192.168.1.1
netsh interface ip set dns "Wi-Fi" static 8.8.8.8
```

#### B. Router Port Forwarding
1. Access router admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Navigate to Port Forwarding/Virtual Server
3. Add new rule:
   - **Service Name**: LLM Translation
   - **External Port**: 8080 (or your choice)
   - **Internal IP**: Your PC's static IP
   - **Internal Port**: 8000
   - **Protocol**: TCP

#### C. Dynamic DNS (if no static public IP)
**Option 1: Free DDNS Services**
- NoIP.com
- DuckDNS.org
- Dynu.com

**Option 2: Cloudflare Tunnel (Recommended)**
```powershell
# Install Cloudflare Tunnel
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### 2. **Security Setup**

#### A. Windows Firewall Configuration
```powershell
# Allow inbound connections on port 8000
New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# For HTTPS (port 443)
New-NetFirewallRule -DisplayName "LLM Translation HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```

#### B. HTTPS/TLS Setup
We'll use Nginx as reverse proxy with SSL certificates.

### 3. **Production Configuration**

#### A. Environment Variables for Production
Create `.env.production`:
```env
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-super-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Rate Limiting (more restrictive for public access)
REQUESTS_PER_MINUTE=30
REQUESTS_PER_HOUR=500
REQUESTS_PER_DAY=5000

# CORS (restrict to known domains)
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8001
```

#### B. Enhanced Security Configuration
```python
# Add to src/core/config.py
class SecuritySettings(BaseSettings):
    """Enhanced security settings for production."""
    
    # IP filtering
    allowed_ips: List[str] = Field(default=[], description="Allowed IP addresses")
    blocked_ips: List[str] = Field(default=[], description="Blocked IP addresses")
    
    # Geographic restrictions
    allowed_countries: List[str] = Field(default=[], description="Allowed country codes")
    
    # API abuse protection
    max_request_size: int = Field(default=1024*1024, description="Max request size in bytes")
    max_text_length: int = Field(default=10000, description="Max translation text length")
    
    # SSL/TLS
    ssl_keyfile: Optional[str] = Field(None, description="SSL private key file")
    ssl_certfile: Optional[str] = Field(None, description="SSL certificate file")
```

## 🚀 Quick Production Setup Script

Let me create automated setup scripts for you:

### Windows Production Setup (PowerShell)
```powershell
# production-setup.ps1
param(
    [string]$Domain = "localhost",
    [int]$Port = 8000,
    [switch]$EnableHTTPS = $false
)

Write-Host "Setting up Production LLM Translation Server..." -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Please run as Administrator for full setup" -ForegroundColor Red
    exit 1
}

# Configure Windows Firewall
Write-Host "Configuring Windows Firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Force

# Install required tools
Write-Host "Installing required tools..." -ForegroundColor Yellow

# Check if Chocolatey is installed
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Install Nginx for reverse proxy
choco install nginx -y

# Create production configuration
Write-Host "Creating production configuration..." -ForegroundColor Yellow
# Production config creation code here...

Write-Host "Production setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure your router port forwarding" -ForegroundColor White
Write-Host "2. Set up DDNS or get static IP" -ForegroundColor White
Write-Host "3. Run: .\start-production.ps1" -ForegroundColor White
```

## 🔒 Security Recommendations

### Critical Security Measures:
1. **Never expose without HTTPS** in production
2. **Strong API key authentication** required
3. **Rate limiting** to prevent abuse
4. **Regular security updates** for all components
5. **Monitor logs** for suspicious activity
6. **Backup configuration** and data regularly

### Optional but Recommended:
- **VPN access only** for admin functions
- **IP whitelisting** for known clients
- **Geographic restrictions** if needed
- **DDoS protection** (Cloudflare)
- **Web Application Firewall** (WAF)

## 📊 Monitoring & Maintenance

### Health Monitoring:
```powershell
# health-check.ps1
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get
if ($response.status -eq "healthy") {
    Write-Host "Service is healthy" -ForegroundColor Green
} else {
    Write-Host "Service issue detected" -ForegroundColor Red
    # Restart service logic here
}
```

### Log Monitoring:
- Monitor API usage patterns
- Track error rates
- Watch for abuse attempts
- Performance metrics

## 🌍 Access Methods for Clients

Once set up, clients can access via:

1. **Direct IP**: `http://your-public-ip:8080`
2. **Domain**: `http://yourdomain.com` (with DDNS)
3. **HTTPS**: `https://yourdomain.com` (with SSL)

## ⚠️ Important Considerations

### Legal & Compliance:
- **Terms of Service**: Define usage limits
- **Privacy Policy**: Data handling disclosure
- **Liability**: Usage responsibility
- **Regional Laws**: Translation service regulations

### Technical Limitations:
- **Bandwidth**: Monitor usage vs. internet plan
- **Hardware**: Ensure adequate CPU/Memory for concurrent users
- **Ollama Models**: Large models need significant RAM
- **Storage**: Log files and cache management

### Cost Considerations:
- **Electricity**: 24/7 operation costs
- **Internet**: Potential overage charges
- **Domain/SSL**: Annual renewal costs
- **Backup Storage**: Cloud backup expenses

Would you like me to create specific scripts for any of these components?
