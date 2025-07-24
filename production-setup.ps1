# Production Server Setup Script for Windows
# Transforms your Windows PC into an internet-accessible translation server

param(
    [string]$Domain = "localhost",
    [int]$Port = 8000,
    [int]$ExternalPort = 8080,
    [switch]$EnableHTTPS = $false,
    [switch]$InstallNginx = $true,
    [string]$AllowedIPs = "",
    [switch]$SetupDDNS = $false
)

Write-Host "🌐 LLM Translation Server - Production Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Administrator privileges required for full setup" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green

# 1. System Information
Write-Host "`n📊 System Information:" -ForegroundColor Yellow
$computerName = $env:COMPUTERNAME
$localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*" | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"})[0].IPAddress
$publicIP = try { (Invoke-RestMethod -Uri "https://ipinfo.io/ip" -TimeoutSec 10).Trim() } catch { "Unable to detect" }

Write-Host "Computer Name: $computerName" -ForegroundColor White
Write-Host "Local IP: $localIP" -ForegroundColor White
Write-Host "Public IP: $publicIP" -ForegroundColor White

# 2. Configure Windows Firewall
Write-Host "`n🔥 Configuring Windows Firewall..." -ForegroundColor Yellow

try {
    # Remove existing rules if any
    Remove-NetFirewallRule -DisplayName "LLM Translation Service" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "LLM Translation HTTPS" -ErrorAction SilentlyContinue
    
    # Add new firewall rules
    New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Profile Any
    Write-Host "✅ Firewall rule added for port $Port" -ForegroundColor Green
    
    if ($EnableHTTPS) {
        New-NetFirewallRule -DisplayName "LLM Translation HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow -Profile Any
        Write-Host "✅ Firewall rule added for HTTPS (port 443)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Firewall configuration failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Install Chocolatey (if not present)
Write-Host "`n🍫 Checking Chocolatey installation..." -ForegroundColor Yellow
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey package manager..." -ForegroundColor Yellow
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "✅ Chocolatey installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Chocolatey installation failed: $($_.Exception.Message)" -ForegroundColor Red
        $InstallNginx = $false
    }
} else {
    Write-Host "✅ Chocolatey already installed" -ForegroundColor Green
}

# 4. Install Nginx (if requested)
if ($InstallNginx) {
    Write-Host "`n🌐 Installing Nginx reverse proxy..." -ForegroundColor Yellow
    try {
        choco install nginx -y
        Write-Host "✅ Nginx installed successfully" -ForegroundColor Green
        
        # Create nginx configuration
        $nginxConfig = @"
events {
    worker_connections 1024;
}

http {
    upstream translation_backend {
        server 127.0.0.1:$Port;
    }
    
    # Rate limiting
    limit_req_zone `$binary_remote_addr zone=api:10m rate=30r/m;
    
    server {
        listen $ExternalPort;
        server_name $Domain;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        
        # Client body size limit
        client_max_body_size 1M;
        
        location / {
            # Apply rate limiting
            limit_req zone=api burst=10 nodelay;
            
            proxy_pass http://translation_backend;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            proxy_pass http://translation_backend/api/health;
        }
    }
}
"@
        
        $nginxConfPath = "C:\tools\nginx\conf\nginx.conf"
        if (Test-Path "C:\tools\nginx\conf\") {
            $nginxConfig | Out-File -FilePath $nginxConfPath -Encoding UTF8
            Write-Host "✅ Nginx configuration created" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ Nginx installation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 5. Create production environment configuration
Write-Host "`n⚙️ Creating production configuration..." -ForegroundColor Yellow

$prodEnvConfig = @"
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=$Port
API_WORKERS=4

# Security
SECRET_KEY=$(([System.Web.Security.Membership]::GeneratePassword(32, 8)))
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Rate Limiting (more restrictive for public access)
REQUESTS_PER_MINUTE=30
REQUESTS_PER_HOUR=500
REQUESTS_PER_DAY=5000

# CORS (adjust as needed)
CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/production.log

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8001

# Public access settings
PUBLIC_ACCESS=true
REQUIRE_API_KEY=true
"@

$prodEnvConfig | Out-File -FilePath ".env.production" -Encoding UTF8
Write-Host "✅ Production environment configuration created" -ForegroundColor Green

# 6. Create production startup script
Write-Host "`n🚀 Creating production startup script..." -ForegroundColor Yellow

$startupScript = @"
# Production Startup Script
# Starts the LLM Translation Service in production mode

Write-Host "🚀 Starting LLM Translation Service (Production Mode)" -ForegroundColor Green

# Activate virtual environment
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Copy production environment
Copy-Item ".env.production" ".env" -Force
Write-Host "✅ Production environment loaded" -ForegroundColor Green

# Start Nginx (if installed)
if (Get-Command nginx -ErrorAction SilentlyContinue) {
    try {
        Start-Process "nginx" -WorkingDirectory "C:\tools\nginx" -WindowStyle Hidden
        Write-Host "✅ Nginx reverse proxy started" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Nginx start failed: `$(`$_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Start the translation service
Write-Host "🌐 Starting translation service on http://0.0.0.0:$Port" -ForegroundColor Cyan
Write-Host "📊 Access via: http://$localIP`:$ExternalPort (local network)" -ForegroundColor White
if ('$publicIP' -ne 'Unable to detect') {
    Write-Host "🌍 Access via: http://$publicIP`:$ExternalPort (internet - requires port forwarding)" -ForegroundColor White
}
Write-Host "📖 API docs: http://$localIP`:$ExternalPort/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow

# Start the service with production settings
python run.py
"@

$startupScript | Out-File -FilePath "start-production.ps1" -Encoding UTF8
Write-Host "✅ Production startup script created" -ForegroundColor Green

# 7. Create monitoring script
Write-Host "`n📊 Creating monitoring script..." -ForegroundColor Yellow

$monitorScript = @"
# Health Monitoring Script
# Checks service health and restarts if needed

param([switch]`$Continuous = `$false)

function Test-ServiceHealth {
    try {
        `$response = Invoke-RestMethod -Uri "http://localhost:$Port/api/health" -Method Get -TimeoutSec 10
        if (`$response.status -eq "healthy") {
            Write-Host "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - ✅ Service is healthy" -ForegroundColor Green
            return `$true
        } else {
            Write-Host "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - ⚠️ Service unhealthy: `$(`$response.status)" -ForegroundColor Yellow
            return `$false
        }
    } catch {
        Write-Host "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - ❌ Service not responding: `$(`$_.Exception.Message)" -ForegroundColor Red
        return `$false
    }
}

if (`$Continuous) {
    Write-Host "🔄 Starting continuous health monitoring..." -ForegroundColor Cyan
    while (`$true) {
        Test-ServiceHealth
        Start-Sleep -Seconds 60
    }
} else {
    Test-ServiceHealth
}
"@

$monitorScript | Out-File -FilePath "monitor-health.ps1" -Encoding UTF8
Write-Host "✅ Health monitoring script created" -ForegroundColor Green

# 8. Display setup summary and next steps
Write-Host "`n🎉 Production Setup Complete!" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

Write-Host "`n📋 Setup Summary:" -ForegroundColor Cyan
Write-Host "• Firewall configured for port $Port" -ForegroundColor White
Write-Host "• Production environment created (.env.production)" -ForegroundColor White
Write-Host "• Startup script created (start-production.ps1)" -ForegroundColor White
Write-Host "• Health monitoring script created (monitor-health.ps1)" -ForegroundColor White
if ($InstallNginx) {
    Write-Host "• Nginx reverse proxy installed and configured" -ForegroundColor White
}

Write-Host "`n🔧 Next Steps:" -ForegroundColor Yellow
Write-Host "1. 🌐 Configure Router Port Forwarding:" -ForegroundColor White
Write-Host "   - External Port: $ExternalPort → Internal IP: $localIP → Internal Port: $Port" -ForegroundColor Gray
Write-Host "   - Protocol: TCP" -ForegroundColor Gray

Write-Host "`n2. 🔗 Set up Dynamic DNS (Optional):" -ForegroundColor White
Write-Host "   - Visit NoIP.com, DuckDNS.org, or Dynu.com" -ForegroundColor Gray
Write-Host "   - Create free hostname like: myserver.ddns.net" -ForegroundColor Gray

Write-Host "`n3. 🚀 Start the Service:" -ForegroundColor White
Write-Host "   .\start-production.ps1" -ForegroundColor Gray

Write-Host "`n4. 🔒 Security Recommendations:" -ForegroundColor White
Write-Host "   - Set up HTTPS/SSL for production use" -ForegroundColor Gray
Write-Host "   - Configure strong API keys" -ForegroundColor Gray
Write-Host "   - Monitor logs regularly" -ForegroundColor Gray
Write-Host "   - Keep system updated" -ForegroundColor Gray

Write-Host "`n📱 Access Information:" -ForegroundColor Cyan
Write-Host "Local Network: http://$localIP`:$ExternalPort" -ForegroundColor White
if ($publicIP -ne "Unable to detect") {
    Write-Host "Internet: http://$publicIP`:$ExternalPort (after port forwarding)" -ForegroundColor White
}
Write-Host "API Documentation: /docs" -ForegroundColor Gray
Write-Host "Health Check: /api/health" -ForegroundColor Gray

Write-Host "`n⚠️ Important Notes:" -ForegroundColor Yellow
Write-Host "• Ensure your internet plan supports server hosting" -ForegroundColor Gray
Write-Host "• Monitor bandwidth usage" -ForegroundColor Gray
Write-Host "• Consider electricity costs for 24/7 operation" -ForegroundColor Gray
Write-Host "• Set up automated backups" -ForegroundColor Gray

Write-Host "`nProduction setup complete! 🌟" -ForegroundColor Green
