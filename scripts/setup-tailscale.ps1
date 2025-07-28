# ================================================================================================
# Tailscale Setup Script for LLM Translation Service (PowerShell)
# Configures and starts the service for Tailscale network access
# ================================================================================================

param(
    [switch]$Help
)

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

if ($Help) {
    Write-Host "Tailscale Setup Script for LLM Translation Service"
    Write-Host "================================================="
    Write-Host ""
    Write-Host "Usage: .\setup-tailscale.ps1"
    Write-Host ""
    Write-Host "This script will:"
    Write-Host "  1. Check if Tailscale is installed and running"
    Write-Host "  2. Connect to your Tailscale network"
    Write-Host "  3. Configure your service for external access"
    Write-Host "  4. Start the service in production mode"
    Write-Host "  5. Provide access URLs and environment variables"
    exit 0
}

Write-Info "🚀 Setting up LLM Translation Service for Tailscale"
Write-Host "================================================="

# Check if Tailscale is installed
$tailscaleExe = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscaleExe) {
    Write-Error "Tailscale is not installed. Please install it first:"
    Write-Host "  Download from: https://tailscale.com/download/windows"
    Write-Host "  Or use: winget install tailscale.tailscale"
    exit 1
}

Write-Success "Tailscale is installed"

# Check if Tailscale is running
try {
    $status = & tailscale status 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Not running"
    }
    Write-Success "Tailscale is already running"
} catch {
    Write-Warning "Tailscale is not running. Starting it now..."
    
    Write-Info "Connecting to Tailscale network..."
    Write-Warning "This will open a browser window for authentication"
    
    try {
        & tailscale up --accept-routes
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to connect"
        }
        Write-Success "Connected to Tailscale network"
    } catch {
        Write-Error "Failed to connect to Tailscale"
        Write-Host "Please run 'tailscale up' manually and try again"
        exit 1
    }
}

# Get Tailscale IP
try {
    $tailscaleIP = & tailscale ip -4
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($tailscaleIP)) {
        throw "Failed to get IP"
    }
} catch {
    Write-Error "Failed to get Tailscale IP address"
    exit 1
}

Write-Success "Tailscale IP: $tailscaleIP"

# Check if Tailscale environment configuration exists
if (Test-Path ".env.tailscale") {
    Write-Info "Setting up Tailscale configuration..."
    Copy-Item ".env.tailscale" ".env" -Force
    Write-Success "Tailscale environment configured"
} else {
    Write-Warning "No .env.tailscale found, using default configuration"
}

# Start the service
Write-Info "Starting LLM Translation Service..."

# Check if start-service script exists
$startScript = $null
if (Test-Path "scripts\start-service.ps1") {
    $startScript = ".\scripts\start-service.ps1"
} elseif (Test-Path "start-service.ps1") {
    $startScript = ".\start-service.ps1"
} else {
    Write-Warning "PowerShell start script not found, trying shell script..."
    if (Test-Path "scripts\start-service.sh") {
        # Try to run shell script via WSL or Git Bash
        try {
            & bash "scripts/start-service.sh" --production
        } catch {
            Write-Error "Failed to start service. Please run the service manually."
            exit 1
        }
    } else {
        Write-Error "No start service script found"
        exit 1
    }
}

if ($startScript) {
    try {
        & $startScript -Production
    } catch {
        Write-Warning "Failed to start via PowerShell script, trying manual start..."
        Write-Info "Please start the service manually: python run.py"
    }
}

Write-Host ""
Write-Success "🌐 Service is now accessible via Tailscale!"
Write-Host "================================================="
Write-Host ""
Write-Host "📱 Access URLs:"
Write-Host "   http://$tailscaleIP:8000"
Write-Host ""
Write-Host "📚 API Documentation:"
Write-Host "   http://$tailscaleIP:8000/docs"
Write-Host ""
Write-Host "🔧 Environment Variables for other applications:"
Write-Host "   `$env:LLM_SERVICE_URL = `"http://$tailscaleIP:8000`""
Write-Host "   `$env:LLM_APP_ID = `"demo_app_id`""
Write-Host "   `$env:LLM_APP_SECRET = `"demo_app_secret`""
Write-Host ""
Write-Host "   Or for cmd/batch:"
Write-Host "   set LLM_SERVICE_URL=http://$tailscaleIP:8000"
Write-Host "   set LLM_APP_ID=demo_app_id"
Write-Host "   set LLM_APP_SECRET=demo_app_secret"
Write-Host ""
Write-Host "🛠️  Management:"
Write-Host "   Stop: Ctrl+C or .\scripts\stop-service.ps1"
Write-Host "   Logs: Check terminal output"
Write-Host ""
Write-Success "Setup complete!"

# Keep the window open if run directly
if ($Host.Name -eq "ConsoleHost") {
    Write-Host ""
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
