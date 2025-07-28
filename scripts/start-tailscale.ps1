# ================================================================================================
# Start LLM Translation Service with Tailscale Configuration (PowerShell)
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
    Write-Host "Start LLM Translation Service with Tailscale Configuration"
    Write-Host "========================================================="
    Write-Host ""
    Write-Host "Usage: .\start-tailscale.ps1"
    Write-Host ""
    Write-Host "This script will:"
    Write-Host "  1. Check if Tailscale is connected"
    Write-Host "  2. Use Tailscale configuration if available"
    Write-Host "  3. Start the translation service"
    exit 0
}

Write-Info "🚀 Starting LLM Translation Service with Tailscale"
Write-Host "================================================="

# Check if Tailscale is connected
try {
    $tailscaleIP = & tailscale ip -4 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrEmpty($tailscaleIP)) {
        Write-Success "Tailscale connected - IP: $tailscaleIP"
        
        # Use Tailscale configuration
        if (Test-Path ".env.tailscale") {
            Copy-Item ".env.tailscale" ".env" -Force
            Write-Success "Using Tailscale configuration"
        } else {
            Write-Warning "Tailscale config not found, using default"
        }
    } else {
        throw "Not connected"
    }
} catch {
    Write-Warning "Tailscale not connected. Service will only be available locally."
    Write-Info "Run .\scripts\setup-tailscale.ps1 to configure Tailscale access"
    $tailscaleIP = $null
}

# Start the service
Write-Info "Starting service..."

# Check for available start scripts
$startScript = $null
if (Test-Path "scripts\start-service.ps1") {
    $startScript = ".\scripts\start-service.ps1"
    & $startScript -Production
} elseif (Test-Path "start-service.ps1") {
    $startScript = ".\start-service.ps1"
    & $startScript -Production
} else {
    Write-Warning "PowerShell start script not found, trying shell script..."
    if (Test-Path "scripts\start-service.sh") {
        try {
            & bash "scripts/start-service.sh" --production
        } catch {
            Write-Error "Failed to start service via shell script"
            Write-Info "Please start the service manually: python run.py"
        }
    } else {
        Write-Info "Starting service directly..."
        if (Test-Path "run.py") {
            python run.py
        } else {
            Write-Error "No run.py found. Please start the service manually."
        }
    }
}

if ($tailscaleIP) {
    Write-Host ""
    Write-Success "🌐 Service accessible via Tailscale at:"
    Write-Host "   http://$tailscaleIP:8000"
    Write-Host "   http://$tailscaleIP:8000/docs"
}
