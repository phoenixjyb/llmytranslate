# ================================================================================================
# LLM Translation Service - Stop Launcher
# This script redirects to the actual stop script in the scripts/ folder
# ================================================================================================

Write-Host "🛑 LLM Translation Service Stop Launcher" -ForegroundColor Red
Write-Host "Redirecting to main stop script..." -ForegroundColor Yellow
Write-Host ""

# Pass all parameters to the main script
& ".\scripts\stop-service.ps1" @args
