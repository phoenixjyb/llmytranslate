# Quick test script for LLM Translation Service (PowerShell)
# Usage: .\test_endpoints.ps1

$BaseURL = "http://localhost:8000"

Write-Host "🚀 Testing LLM Translation Service" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

Write-Host ""
Write-Host "1. 🔍 Health Check:" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseURL/api/health" -Method Get
    $health | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. 📋 Service Info:" -ForegroundColor Yellow
try {
    $info = Invoke-RestMethod -Uri "$BaseURL/" -Method Get
    $info | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Service info failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. 🌍 Demo Translation (Hello world):" -ForegroundColor Yellow
try {
    $body1 = @{
        q = "Hello world"
        from = "en"
        to = "zh"
    }
    $result1 = Invoke-RestMethod -Uri "$BaseURL/api/demo/translate" -Method Post -Body $body1
    $result1 | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Translation 1 failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. 🌍 Demo Translation (How are you?):" -ForegroundColor Yellow
try {
    $body2 = @{
        q = "How are you?"
        from = "en" 
        to = "zh"
    }
    $result2 = Invoke-RestMethod -Uri "$BaseURL/api/demo/translate" -Method Post -Body $body2
    $result2 | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Translation 2 failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Test completed!" -ForegroundColor Green
