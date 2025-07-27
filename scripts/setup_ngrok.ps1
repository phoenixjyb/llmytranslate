# Ngrok Quick Setup Script (Windows Store Version)
# Run this after getting your auth token from https://dashboard.ngrok.com/get-started/your-authtoken

param(
    [Parameter(Mandatory=$false)]
    [string]$AuthToken,
    [switch]$SkipWarning
)

Write-Host "🔐 Setting up ngrok authentication..." -ForegroundColor Green
Write-Host "📦 Using Windows Store ngrok version 3.24" -ForegroundColor Cyan

# Check if ngrok is available
$ngrokVersion = & ngrok version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ngrok not found in PATH" -ForegroundColor Red
    Write-Host "💡 Please ensure ngrok is properly installed from Windows Store" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found: $ngrokVersion" -ForegroundColor Green

# Set auth token
ngrok config add-authtoken $AuthToken

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Auth token configured successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚇 Now starting ngrok tunnel..." -ForegroundColor Yellow
    Write-Host "📋 Your translation service will be available at the ngrok URL" -ForegroundColor Cyan
    Write-Host "🌐 Press Ctrl+C to stop the tunnel" -ForegroundColor Gray
    Write-Host ""
    
    # Start tunnel
    ngrok http 8000
} else {
    Write-Host "❌ Failed to configure auth token" -ForegroundColor Red
    Write-Host "💡 Please check your token and try again" -ForegroundColor Yellow
}
