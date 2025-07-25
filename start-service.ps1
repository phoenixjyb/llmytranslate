# ================================================================================================
# LLM Translation Service - Main Launcher
# This script redirects to the actual startup script in the scripts/ folder
# ================================================================================================

Write-Host "🚀 LLM Translation Service Launcher" -ForegroundColor Cyan
Write-Host "Redirecting to main startup script..." -ForegroundColor Yellow
Write-Host ""

# Pass all parameters to the main script
& ".\scripts\start-service.ps1" @args
