# Set up Android development environment using existing Android Studio installation
# PowerShell script to configure environment variables

Write-Host "🔧 Setting up Android Development Environment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Android Studio Java path
$androidStudioJava = "D:\Program Files\Android\Android Studio\jbr\bin"
$androidSdk = "$env:LOCALAPPDATA\Android\Sdk"

# Check if Android Studio Java exists
if (Test-Path $androidStudioJava) {
    Write-Host "✅ Found Android Studio Java at: $androidStudioJava" -ForegroundColor Green
    
    # Add to PATH for current session
    $env:PATH = "$androidStudioJava;$env:PATH"
    Write-Host "✅ Added Android Studio Java to PATH (current session)" -ForegroundColor Green
    
    # Set JAVA_HOME for current session
    $env:JAVA_HOME = "D:\Program Files\Android\Android Studio\jbr"
    Write-Host "✅ Set JAVA_HOME to: $env:JAVA_HOME" -ForegroundColor Green
} else {
    Write-Host "❌ Android Studio Java not found at: $androidStudioJava" -ForegroundColor Red
    exit 1
}

# Check Android SDK
if (Test-Path $androidSdk) {
    Write-Host "✅ Found Android SDK at: $androidSdk" -ForegroundColor Green
    
    # Set ANDROID_HOME for current session
    $env:ANDROID_HOME = $androidSdk
    Write-Host "✅ Set ANDROID_HOME to: $env:ANDROID_HOME" -ForegroundColor Green
    
    # Add platform-tools and tools to PATH
    $platformTools = "$androidSdk\platform-tools"
    $cmdlineTools = "$androidSdk\cmdline-tools\latest\bin"
    
    if (Test-Path $platformTools) {
        $env:PATH = "$platformTools;$env:PATH"
        Write-Host "✅ Added platform-tools to PATH" -ForegroundColor Green
    }
    
    if (Test-Path $cmdlineTools) {
        $env:PATH = "$cmdlineTools;$env:PATH"
        Write-Host "✅ Added cmdline-tools to PATH" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Android SDK not found at: $androidSdk" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎯 Environment Setup Complete!" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Verify installations
Write-Host "`n📋 Verification:" -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version" | Select-Object -First 1
    Write-Host "✅ Java: $($javaVersion.Line)" -ForegroundColor Green
} catch {
    Write-Host "❌ Java verification failed" -ForegroundColor Red
}

try {
    $adbVersion = adb version 2>&1 | Select-String "Android Debug Bridge" | Select-Object -First 1
    Write-Host "✅ ADB: $($adbVersion.Line)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  ADB not available (platform-tools may not be installed)" -ForegroundColor Yellow
}

Write-Host "`n💡 To make these changes permanent:" -ForegroundColor Cyan
Write-Host "   Run this script as Administrator and add -Permanent switch" -ForegroundColor Gray
Write-Host "`n🚀 Ready to build Android apps!" -ForegroundColor Green
Write-Host "   Try: .\build-android.ps1" -ForegroundColor Cyan
