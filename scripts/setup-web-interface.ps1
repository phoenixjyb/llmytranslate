#!/usr/bin/env powershell
# ================================================================================================
# Web Translation Interface - Quick Setup Script
# Sets up and starts web-based translation service accessible from remote networks
# ================================================================================================

param(
    [string]$Mode = "local",           # local, ngrok, router
    [string]$NgrokToken = "",          # Ngrok auth token
    [switch]$OpenBrowser = $true,      # Open browser automatically
    [switch]$Production = $false,      # Production mode
    [switch]$Help = $false
)

# Color codes
$Red = [System.ConsoleColor]::Red
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan
$Gray = [System.ConsoleColor]::Gray

function Write-ColorHost($Message, $Color = $Gray) {
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-ColorHost "🌐 Web Translation Interface - Quick Setup" $Cyan
    Write-ColorHost "==========================================" $Cyan
    Write-ColorHost ""
    Write-ColorHost "Usage: .\setup-web-interface.ps1 [OPTIONS]" $Gray
    Write-ColorHost ""
    Write-ColorHost "Options:" $Yellow
    Write-ColorHost "  -Mode <local|ngrok|router>  Deployment mode (default: local)" $Gray
    Write-ColorHost "  -NgrokToken <token>         Ngrok auth token (required for ngrok mode)" $Gray
    Write-ColorHost "  -OpenBrowser               Open web interface in browser (default: true)" $Gray
    Write-ColorHost "  -Production                Use production configuration" $Gray
    Write-ColorHost "  -Help                      Show this help message" $Gray
    Write-ColorHost ""
    Write-ColorHost "Examples:" $Yellow
    Write-ColorHost "  .\setup-web-interface.ps1 -Mode local" $Gray
    Write-ColorHost "  .\setup-web-interface.ps1 -Mode ngrok -NgrokToken 'your_token_here'" $Gray
    Write-ColorHost "  .\setup-web-interface.ps1 -Mode router -Production" $Gray
    Write-ColorHost ""
    Write-ColorHost "Modes:" $Yellow
    Write-ColorHost "  local  - Local network access only (fastest setup)" $Gray
    Write-ColorHost "  ngrok  - Global access via ngrok tunnel (easiest for testing)" $Gray
    Write-ColorHost "  router - Global access via port forwarding (permanent)" $Gray
    exit 0
}

if ($Help) {
    Show-Help
}

Write-ColorHost "🌐 Web Translation Interface Setup" $Cyan
Write-ColorHost "==================================" $Cyan
Write-ColorHost "Mode: $Mode" $Yellow
Write-ColorHost ""

# Step 1: Verify prerequisites
Write-ColorHost "📋 Step 1: Checking Prerequisites..." $Yellow

# Check if translation service files exist
if (!(Test-Path "src\main.py")) {
    Write-ColorHost "❌ Translation service not found in current directory" $Red
    Write-ColorHost "💡 Please run this script from the llmytranslate root directory" $Yellow
    exit 1
}

# Check if web interface exists
if (!(Test-Path "web\index.html")) {
    Write-ColorHost "❌ Web interface files not found" $Red
    Write-ColorHost "💡 Web interface should be created automatically" $Yellow
    exit 1
}

Write-ColorHost "✅ All prerequisites found" $Green

# Step 2: Check if service is already running
Write-ColorHost "`n🔍 Step 2: Checking Service Status..." $Yellow

$serviceRunning = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($response.status -eq "healthy") {
        Write-ColorHost "✅ Translation service is already running" $Green
        $serviceRunning = $true
    }
} catch {
    Write-ColorHost "ℹ️ Translation service not running, will start it" $Gray
}

# Step 3: Start translation service if not running
if (!$serviceRunning) {
    Write-ColorHost "`n🚀 Step 3: Starting Translation Service..." $Yellow
    
    if (Test-Path "start-service.ps1") {
        if ($Production) {
            & ".\start-service.ps1" -Production
        } else {
            & ".\start-service.ps1"
        }
        
        # Wait for service to start
        Write-ColorHost "⏳ Waiting for service to start..." $Gray
        $attempts = 0
        $maxAttempts = 30
        
        do {
            Start-Sleep -Seconds 2
            $attempts++
            
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
                if ($response.status -eq "healthy") {
                    Write-ColorHost "✅ Translation service started successfully" $Green
                    $serviceRunning = $true
                    break
                }
            } catch {
                # Continue waiting
            }
            
            if ($attempts -ge $maxAttempts) {
                Write-ColorHost "❌ Translation service failed to start within timeout" $Red
                Write-ColorHost "💡 Try running: .\start-service.ps1" $Yellow
                exit 1
            }
            
            Write-ColorHost "." -NoNewline
            
        } while ($attempts -lt $maxAttempts)
        
        Write-ColorHost ""
    } else {
        Write-ColorHost "❌ start-service.ps1 not found" $Red
        Write-ColorHost "💡 Please run: python run.py" $Yellow
        exit 1
    }
}

# Step 4: Setup remote access based on mode
$webUrl = "http://localhost:8000/web/"
$apiUrl = "http://localhost:8000"

switch ($Mode.ToLower()) {
    "local" {
        Write-ColorHost "`n🏠 Step 4: Setting up Local Network Access..." $Yellow
        
        # Get local IP
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*" } | Select-Object -First 1).IPAddress
        
        if ($localIP) {
            $webUrl = "http://${localIP}:8000/web/"
            $apiUrl = "http://${localIP}:8000"
            
            Write-ColorHost "✅ Local network access configured" $Green
            Write-ColorHost "🌐 Local Network URL: $webUrl" $Cyan
            Write-ColorHost "📡 Other devices on your network can access this URL" $Gray
        } else {
            Write-ColorHost "⚠️ Could not determine local IP, using localhost" $Yellow
        }
    }
    
    "ngrok" {
        Write-ColorHost "`n🚇 Step 4: Setting up Ngrok Tunnel..." $Yellow
        
        # Check if ngrok is installed
        $ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
        if (!$ngrokPath) {
            Write-ColorHost "❌ Ngrok not found. Installing..." $Red
            
            # Try to install via chocolatey
            $chocoPath = Get-Command choco -ErrorAction SilentlyContinue
            if ($chocoPath) {
                Write-ColorHost "📦 Installing ngrok via Chocolatey..." $Gray
                choco install ngrok -y
            } else {
                Write-ColorHost "❌ Chocolatey not found. Please install ngrok manually:" $Red
                Write-ColorHost "   1. Download from: https://ngrok.com/download" $Gray
                Write-ColorHost "   2. Extract to a folder in your PATH" $Gray
                Write-ColorHost "   3. Run this script again" $Gray
                exit 1
            }
        }
        
        # Configure ngrok token if provided
        if ($NgrokToken) {
            Write-ColorHost "🔑 Configuring ngrok auth token..." $Gray
            & ngrok config add-authtoken $NgrokToken
        }
        
        # Start ngrok tunnel
        Write-ColorHost "🚀 Starting ngrok tunnel..." $Gray
        Write-ColorHost "⏳ This will create a public URL for worldwide access..." $Gray
        
        Start-Process -FilePath "ngrok" -ArgumentList "http", "8000" -WindowStyle Normal
        
        Write-ColorHost "✅ Ngrok tunnel started!" $Green
        Write-ColorHost "🌍 Your service is now accessible worldwide!" $Cyan
        Write-ColorHost "📋 Check the ngrok terminal window for your public URL" $Yellow
        Write-ColorHost "   Example: https://abc123.ngrok-free.app/web/" $Gray
        
        $webUrl = "https://[your-ngrok-url].ngrok-free.app/web/"
    }
    
    "router" {
        Write-ColorHost "`n🌐 Step 4: Router Port Forwarding Setup..." $Yellow
        
        # Configure Windows Firewall
        try {
            Write-ColorHost "🔥 Configuring Windows Firewall..." $Gray
            New-NetFirewallRule -DisplayName "Translation Service Web" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue
            Write-ColorHost "✅ Windows Firewall configured" $Green
        } catch {
            Write-ColorHost "⚠️ Failed to configure firewall (run as Administrator for auto-config)" $Yellow
        }
        
        # Get network information
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*" } | Select-Object -First 1).IPAddress
        $publicIP = try { (Invoke-RestMethod -Uri "http://ipinfo.io/ip" -TimeoutSec 5).Trim() } catch { "Unable to detect" }
        
        Write-ColorHost "📊 Network Information:" $Cyan
        Write-ColorHost "   Local IP: $localIP" $Gray
        Write-ColorHost "   Public IP: $publicIP" $Gray
        Write-ColorHost ""
        Write-ColorHost "🔧 Manual Router Configuration Required:" $Yellow
        Write-ColorHost "   1. Access your router admin panel (usually http://192.168.1.1)" $Gray
        Write-ColorHost "   2. Find 'Port Forwarding' or 'Virtual Server' settings" $Gray
        Write-ColorHost "   3. Create new rule:" $Gray
        Write-ColorHost "      - External Port: 8080 (or any port 1024-65535)" $Gray
        Write-ColorHost "      - Internal IP: $localIP" $Gray
        Write-ColorHost "      - Internal Port: 8000" $Gray
        Write-ColorHost "      - Protocol: TCP" $Gray
        Write-ColorHost "   4. Save and restart router" $Gray
        Write-ColorHost ""
        
        if ($publicIP -ne "Unable to detect") {
            $webUrl = "http://${publicIP}:8080/web/"
            Write-ColorHost "🌍 After router configuration, access via: $webUrl" $Cyan
        }
    }
    
    default {
        Write-ColorHost "❌ Unknown mode: $Mode" $Red
        Write-ColorHost "💡 Valid modes: local, ngrok, router" $Yellow
        exit 1
    }
}

# Step 5: Test web interface
Write-ColorHost "`n🧪 Step 5: Testing Web Interface..." $Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 5
    if ($response.web_interface) {
        Write-ColorHost "✅ Web interface is ready!" $Green
    }
} catch {
    Write-ColorHost "⚠️ Could not verify web interface" $Yellow
}

# Step 6: Open browser
if ($OpenBrowser -and $Mode.ToLower() -eq "local") {
    Write-ColorHost "`n🌐 Step 6: Opening Web Interface..." $Yellow
    try {
        Start-Process $webUrl
        Write-ColorHost "✅ Web interface opened in browser" $Green
    } catch {
        Write-ColorHost "⚠️ Could not open browser automatically" $Yellow
    }
}

# Final summary
Write-ColorHost "`n🎉 Setup Complete!" $Green
Write-ColorHost "=================" $Green
Write-ColorHost ""
Write-ColorHost "📍 Access Points:" $Cyan
Write-ColorHost "   🌐 Web Interface: $webUrl" $Gray
Write-ColorHost "   📚 API Documentation: ${apiUrl}/docs" $Gray
Write-ColorHost "   🏥 Health Check: ${apiUrl}/api/health" $Gray
Write-ColorHost ""
Write-ColorHost "✨ Features Available:" $Cyan
Write-ColorHost "   ✅ Chinese ↔ English translation" $Gray
Write-ColorHost "   ✅ Auto-language detection" $Gray
Write-ColorHost "   ✅ GPU-accelerated processing" $Gray
Write-ColorHost "   ✅ Real-time status monitoring" $Gray
Write-ColorHost "   ✅ Copy results to clipboard" $Gray
Write-ColorHost "   ✅ Mobile-responsive design" $Gray
Write-ColorHost ""
Write-ColorHost "🛑 To Stop Services:" $Yellow
Write-ColorHost "   .\stop-service.ps1" $Gray
Write-ColorHost ""
Write-ColorHost "📚 For detailed setup guide:" $Yellow
Write-ColorHost "   docs\guides\WEB_INTERFACE_DEPLOYMENT.md" $Gray
