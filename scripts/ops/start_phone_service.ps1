#!/usr/bin/env pwsh

Write-Host "🚀 Starting Phone Call Service with All Fixes Applied..." -ForegroundColor Green

# Navigate to project directory
Set-Location "C:/Users/yanbo/wSpace/llmytranslate"

# Activate virtual environment and start service
& "C:/Users/yanbo/wSpace/llmytranslate/.venv/Scripts/python.exe" run.py phone_call

Write-Host "✅ Phone Call Service Started!" -ForegroundColor Green
