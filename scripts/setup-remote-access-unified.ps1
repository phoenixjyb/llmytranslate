# ================================================================================================
# Unified Remote Access Setup Script for LLM Translation Service (PowerShell)
# This script combines and enhances existing remote access options
# Usage: .\setup-remote-access-unified.ps1 [tailscale|ngrok|local|info]
# ================================================================================================

param(
    [ValidateSet("tailscale", "ngrok", "local", "info", "help")]
    [string]$Mode = "info",
    
    [int]$Port = 8000,
    
    [switch]$Help
)

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

if ($Help -or $Mode -eq "help") {
    Write-Host "Usage: .\setup-remote-access-unified.ps1 [Mode] [-Port <port>]"
    Write-Host ""
    Write-Host "Modes:"
    Write-Host "  info      - Show available setup modes (default)"
    Write-Host "  local     - Get local network access info"
    Write-Host "  tailscale - Set up Tailscale VPN for secure private access"
    Write-Host "  ngrok     - Set up ngrok tunnel for public internet access"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Port     - Service port (default: 8000)"
    Write-Host "  -Help     - Show this help message"
    exit 0
}

function Show-Info {
    Write-Host "🔧 LLMyTranslate Remote Access Setup" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Available remote access methods:"
    Write-Host ""
    Write-Host "🔒 Tailscale (Recommended for regular use)" -ForegroundColor Green
    Write-Host "   ✅ Private & secure VPN"
    Write-Host "   ✅ Stable IP addresses"
    Write-Host "   ✅ Fast direct connections"
    Write-Host "   ✅ Free for personal use"
    Write-Host "   ❌ Requires client installation"
    Write-Host "   Usage: .\setup-remote-access-unified.ps1 tailscale"
    Write-Host ""
    Write-Host "🌍 ngrok (Good for quick sharing)" -ForegroundColor Yellow
    Write-Host "   ✅ Public internet access"
    Write-Host "   ✅ No client setup needed"
    Write-Host "   ✅ Great for demos"
    Write-Host "   ❌ URLs change on restart"
    Write-Host "   ❌ Connection limits"
    Write-Host "   Usage: .\setup-remote-access-unified.ps1 ngrok"
    Write-Host ""
    Write-Host "🏠 Local Network" -ForegroundColor Magenta
    Write-Host "   ✅ Simple setup"
    Write-Host "   ✅ Fast local connections"
    Write-Host "   ❌ Same network only"
    Write-Host "   Usage: .\setup-remote-access-unified.ps1 local"
    Write-Host ""
    Write-Info "Service port: $Port"
}

function Setup-Local {
    Write-Info "Setting up local network access..."
    
    # Get local IP addresses
    $localIPs = @()
    try {
        $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
            $_.IPAddress -ne "127.0.0.1" -and 
            $_.IPAddress -notlike "169.254.*" -and
            $_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual"
        }
        $localIPs = $networkAdapters | Select-Object -ExpandProperty IPAddress
    } catch {
        Write-Warning "Could not automatically detect IP addresses"
        $localIPs = @("192.168.1.100")  # Fallback example
    }
    
    Write-Host ""
    Write-Success "Local network access configured!"
    Write-Host ""
    Write-Host "📍 Access URLs:"
    Write-Host "   Localhost: http://localhost:$Port"
    Write-Host "   Local IPs:"
    foreach ($ip in $localIPs) {
        Write-Host "     http://$ip:$Port"
    }
    Write-Host ""
    Write-Host "🔧 Client Configuration:"
    Write-Host "   PowerShell: `$env:LLM_SERVICE_URL = `"http://localhost:$Port`""
    Write-Host "   CMD: set LLM_SERVICE_URL=http://localhost:$Port"
    Write-Host "   Or use any of the local IP addresses above"
}

function Setup-Tailscale {
    Write-Info "Setting up Tailscale VPN access..."
    
    # Use the dedicated Tailscale script
    if (Test-Path "scripts\setup-tailscale.ps1") {
        & .\scripts\setup-tailscale.ps1
    } elseif (Test-Path "scripts\setup_tailscale.ps1") {
        & .\scripts\setup_tailscale.ps1
    } else {
        Write-Error "Tailscale setup script not found at scripts\setup-tailscale.ps1"
        Write-Info "You can create it or run the shell version if available"
        exit 1
    }
}

function Setup-Ngrok {
    Write-Info "Setting up ngrok tunnel access..."
    
    # Use the ngrok script
    $ngrokScript = $null
    if (Test-Path "scripts\setup-ngrok.ps1") {
        $ngrokScript = ".\scripts\setup-ngrok.ps1"
    } elseif (Test-Path "scripts\setup-ngrok.ps1") {
        $ngrokScript = ".\scripts\setup-ngrok.ps1"
    }
    
    if ($ngrokScript) {
        & $ngrokScript -Port $Port
    } else {
        Write-Warning "ngrok PowerShell script not found, trying shell script..."
        if (Test-Path "scripts\setup-ngrok-enhanced.sh") {
            try {
                & bash "scripts/setup-ngrok-enhanced.sh" $Port
            } catch {
                Write-Error "Failed to run shell script. Please install ngrok manually."
            }
        } elseif (Test-Path "scripts\setup-ngrok.sh") {
            try {
                & bash "scripts/setup-ngrok.sh"
            } catch {
                Write-Error "Failed to run shell script. Please install ngrok manually."
            }
        } else {
            Write-Error "ngrok setup script not found"
            Write-Info "Please install ngrok manually from: https://ngrok.com/download"
            exit 1
        }
    }
}

# Main execution
switch ($Mode) {
    "info" { Show-Info }
    "local" { Setup-Local }
    "tailscale" { Setup-Tailscale }
    "ngrok" { Setup-Ngrok }
}

if ($Mode -ne "info") {
    Write-Host ""
    Write-Info "🔗 For client configuration, see the systemDesign project:"
    Write-Info "   Run: .\tools\scripts\configure_remote_service.ps1"
}
