# 📦 Node.js Installation Script for React Native

Write-Host "🚀 Installing Node.js for React Native Development" -ForegroundColor Green

# Check if Chocolatey is installed
try {
    choco --version | Out-Null
    Write-Host "✅ Chocolatey found" -ForegroundColor Green
} catch {
    Write-Host "❌ Chocolatey not found. Installing Chocolatey first..." -ForegroundColor Yellow
    
    # Install Chocolatey
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    Write-Host "✅ Chocolatey installed" -ForegroundColor Green
}

Write-Host "📦 Installing Node.js LTS..." -ForegroundColor Green
choco install nodejs-lts -y

Write-Host "🔄 Refreshing environment variables..." -ForegroundColor Yellow
refreshenv

Write-Host "✅ Node.js installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 Verifying installation..." -ForegroundColor Cyan

# Test Node.js installation
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Node.js not found in PATH. Please restart PowerShell and try again." -ForegroundColor Red
    Write-Host "Or manually add Node.js to your PATH environment variable." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Restart PowerShell (to refresh environment)" -ForegroundColor White
Write-Host "2. cd to mobile directory" -ForegroundColor White
Write-Host "3. Run .\setup-react-native.ps1 again" -ForegroundColor White
