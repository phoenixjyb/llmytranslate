# Set Java Environment Variables Permanently
# This script adds Android Studio's Java to system environment variables

param(
    [switch]$UserOnly,
    [switch]$SystemWide = $true
)

Write-Host "=== Java Environment Setup ===" -ForegroundColor Cyan

# Java paths to check
$javaPaths = @(
    "D:\Program Files\Android\Android Studio\jbr",
    "C:\Program Files\Android\Android Studio\jbr"
)

$javaHome = $null
foreach ($path in $javaPaths) {
    if (Test-Path "$path\bin\java.exe") {
        $javaHome = $path
        Write-Host "✅ Found Java at: $javaHome" -ForegroundColor Green
        break
    }
}

if (-not $javaHome) {
    Write-Error "❌ Java not found in expected locations. Please check Android Studio installation."
    exit 1
}

# Test Java version
try {
    $javaVersion = & "$javaHome\bin\java.exe" -version 2>&1 | Select-String "version" | Select-Object -First 1
    Write-Host "📋 Java Version: $($javaVersion.Line)" -ForegroundColor Green
} catch {
    Write-Error "❌ Could not execute Java. Path may be incorrect."
    exit 1
}

# Function to set environment variables
function Set-EnvironmentVariable {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Target = "User"
    )
    
    try {
        [System.Environment]::SetEnvironmentVariable($Name, $Value, $Target)
        Write-Host "✅ Set $Name = $Value ($Target)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Failed to set $Name ($Target): $_" -ForegroundColor Red
        return $false
    }
}

# Function to update PATH
function Add-ToPath {
    param(
        [string]$NewPath,
        [string]$Target = "User"
    )
    
    try {
        $currentPath = [System.Environment]::GetEnvironmentVariable("PATH", $Target)
        
        # Check if path already exists
        if ($currentPath -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ -eq $NewPath }) {
            Write-Host "⚠️  $NewPath already in PATH ($Target)" -ForegroundColor Yellow
            return $true
        }
        
        # Add to beginning of PATH
        $newPathValue = "$NewPath;$currentPath"
        [System.Environment]::SetEnvironmentVariable("PATH", $newPathValue, $Target)
        Write-Host "✅ Added $NewPath to PATH ($Target)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Failed to update PATH ($Target): $_" -ForegroundColor Red
        return $false
    }
}

Write-Host "🔧 Setting environment variables..." -ForegroundColor Yellow

if ($UserOnly) {
    Write-Host "Setting for current user only..." -ForegroundColor Cyan
    $success1 = Set-EnvironmentVariable -Name "JAVA_HOME" -Value $javaHome -Target "User"
    $success2 = Add-ToPath -NewPath "$javaHome\bin" -Target "User"
} else {
    Write-Host "Attempting to set system-wide (requires administrator)..." -ForegroundColor Cyan
    
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    
    if ($isAdmin) {
        Write-Host "✅ Running as administrator" -ForegroundColor Green
        $success1 = Set-EnvironmentVariable -Name "JAVA_HOME" -Value $javaHome -Target "Machine"
        $success2 = Add-ToPath -NewPath "$javaHome\bin" -Target "Machine"
    } else {
        Write-Host "⚠️  Not running as administrator, setting for user only" -ForegroundColor Yellow
        $success1 = Set-EnvironmentVariable -Name "JAVA_HOME" -Value $javaHome -Target "User"
        $success2 = Add-ToPath -NewPath "$javaHome\bin" -Target "User"
    }
}

# Also set for current session
$env:JAVA_HOME = $javaHome
$env:PATH = "$javaHome\bin;$env:PATH"
Write-Host "✅ Set for current PowerShell session" -ForegroundColor Green

# Verify the setup
Write-Host "`n🔍 Verifying setup..." -ForegroundColor Yellow

try {
    $testJava = & java -version 2>&1 | Select-String "version" | Select-Object -First 1
    Write-Host "✅ java command works: $($testJava.Line)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  java command not yet available in PATH (restart terminal)" -ForegroundColor Yellow
}

Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "JAVA_HOME = $javaHome" -ForegroundColor White
Write-Host "Added to PATH: $javaHome\bin" -ForegroundColor White

if ($success1 -and $success2) {
    Write-Host "`n✅ Environment variables set successfully!" -ForegroundColor Green
    Write-Host "💡 You may need to restart applications/terminals to see changes" -ForegroundColor Yellow
    
    # Offer to restart current terminal
    Write-Host "`n🔄 Options:" -ForegroundColor Cyan
    Write-Host "1. Restart this PowerShell session" -ForegroundColor White
    Write-Host "2. Open new PowerShell window" -ForegroundColor White
    Write-Host "3. Restart VS Code" -ForegroundColor White
    Write-Host "4. Continue with current session (variables set temporarily)" -ForegroundColor White
} else {
    Write-Host "`n❌ Some environment variables failed to set" -ForegroundColor Red
    Write-Host "💡 Try running as administrator or use -UserOnly flag" -ForegroundColor Yellow
}

# Test build readiness
Write-Host "`n🚀 Testing Android build readiness..." -ForegroundColor Cyan
$buildReady = $true

# Check Java
if (Test-Path "$javaHome\bin\java.exe") {
    Write-Host "✅ Java executable found" -ForegroundColor Green
} else {
    Write-Host "❌ Java executable not found" -ForegroundColor Red
    $buildReady = $false
}

# Check Android SDK
if ($env:ANDROID_HOME -and (Test-Path "$env:ANDROID_HOME\platform-tools")) {
    Write-Host "✅ Android SDK configured" -ForegroundColor Green
} else {
    Write-Host "⚠️  Android SDK not configured (run setup-android-sdk.ps1)" -ForegroundColor Yellow
}

# Check Gradle
if (Test-Path "C:\gradle\gradle-8.4\bin\gradle.bat") {
    Write-Host "✅ Gradle installation found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Local Gradle not found (will use wrapper)" -ForegroundColor Yellow
}

if ($buildReady) {
    Write-Host "`n🎯 Ready to build Android app!" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. cd to android project directory" -ForegroundColor White
    Write-Host "2. Run: .\dev\android-setup\build-android.ps1 -Verbose" -ForegroundColor White
} else {
    Write-Host "`n⚠️  Additional setup needed before building" -ForegroundColor Yellow
}
