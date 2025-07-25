# Ngrok Quick Setup Script
# Run this after getting your auth token from https://dashboard.ngrok.com/get-started/your-authtoken

param(
    [Parameter(Mandatory=$true)]
    [string]$AuthToken
)

Write-Host "🔐 Setting up ngrok authentication..." -ForegroundColor Green

# Add ngrok to PATH for current session
$ngrokPath = "C:\Users\yanbo\AppData\Local\Microsoft\WinGet\Links"
$env:PATH = "$env:PATH;$ngrokPath"

# Set auth token
& "$ngrokPath\ngrok.exe" config add-authtoken $AuthToken

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Auth token configured successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚇 Now starting ngrok tunnel..." -ForegroundColor Yellow
    Write-Host "📋 Your translation service will be available at the ngrok URL" -ForegroundColor Cyan
    Write-Host ""
    
    # Start tunnel
    & "$ngrokPath\ngrok.exe" http 8000
} else {
    Write-Host "❌ Failed to configure auth token" -ForegroundColor Red
    Write-Host "💡 Please check your token and try again" -ForegroundColor Yellow
}
