# Phase 2A Android Build Test Script with UTF-8 Support
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null

Write-Host "🔧 Phase 2A Build Test Starting..." -ForegroundColor Cyan

# Set Java environment
$env:JAVA_HOME = "D:\Program Files\Android\Android Studio\jbr"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

Write-Host "☕ Java version:" -ForegroundColor Yellow
java -version

Write-Host "🔨 Building Android app..." -ForegroundColor Blue
.\gradlew.bat assembleDebug --console=plain

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Build successful! APK created:" -ForegroundColor Green
    Get-ChildItem app\build\outputs\apk\debug\ -ErrorAction SilentlyContinue
    Write-Host "📱 Phase 2A implementation ready for testing!" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed. Checking logs..." -ForegroundColor Red
    Write-Host "🔍 Recent build logs:" -ForegroundColor Yellow
    Get-ChildItem -Recurse -Filter "*.log" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-5) } | Select-Object -First 5
}

Write-Host "🏁 Build test complete." -ForegroundColor Cyan
