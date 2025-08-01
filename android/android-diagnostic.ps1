# Android Build Diagnostic Script
# Helps identify and resolve common build hanging issues

param(
    [switch]$Clean,
    [switch]$Verbose,
    [switch]$Debug,
    [switch]$KillProcesses
)

Write-Host "=== Android Build Diagnostic ===" -ForegroundColor Cyan

# Kill hanging processes if requested
if ($KillProcesses) {
    Write-Host "🔄 Killing hanging processes..." -ForegroundColor Yellow
    Get-Process | Where-Object { 
        $_.ProcessName -like "*java*" -or 
        $_.ProcessName -like "*gradle*" -or 
        $_.ProcessName -like "*kotlin*" 
    } | ForEach-Object {
        Write-Host "  Killing: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Red
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

# Check system resources
Write-Host "🔍 System Resources:" -ForegroundColor Yellow
$memory = Get-WmiObject Win32_ComputerSystem
$freeMemory = Get-WmiObject Win32_OperatingSystem | Select-Object @{Name="FreeMemoryGB";Expression={[math]::Round($_.FreePhysicalMemory/1MB,2)}}
Write-Host "  Total RAM: $([math]::Round($memory.TotalPhysicalMemory/1GB,2)) GB" -ForegroundColor Gray
Write-Host "  Free RAM: $($freeMemory.FreeMemoryGB) GB" -ForegroundColor Gray

# Check disk space
$disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeSpaceGB = [math]::Round($disk.FreeSpace/1GB,2)
Write-Host "  Free Disk Space (C:): $freeSpaceGB GB" -ForegroundColor Gray

if ($freeSpaceGB -lt 5) {
    Write-Host "  ⚠️  WARNING: Low disk space may cause build hangs!" -ForegroundColor Red
}

# Check for lock files
Write-Host "🔍 Checking for lock files..." -ForegroundColor Yellow
$lockFiles = @()
if (Test-Path ".gradle") {
    $lockFiles = Get-ChildItem .gradle -Recurse -Filter "*.lock" -ErrorAction SilentlyContinue
    if ($lockFiles) {
        Write-Host "  ⚠️  Found $($lockFiles.Count) lock files:" -ForegroundColor Yellow
        $lockFiles | ForEach-Object { Write-Host "    $($_.FullName)" -ForegroundColor Red }
    } else {
        Write-Host "  ✅ No lock files found" -ForegroundColor Green
    }
}

# Clean build artifacts if requested
if ($Clean) {
    Write-Host "🧹 Cleaning build artifacts..." -ForegroundColor Yellow
    
    $cleanDirs = @(".gradle", "build", "app/build")
    foreach ($dir in $cleanDirs) {
        if (Test-Path $dir) {
            Write-Host "  Removing: $dir" -ForegroundColor Gray
            Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Clean gradle cache in user home
    $gradleUserHome = "$env:USERPROFILE\.gradle"
    if (Test-Path $gradleUserHome) {
        Write-Host "  Cleaning Gradle user cache..." -ForegroundColor Gray
        Remove-Item "$gradleUserHome\caches" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item "$gradleUserHome\daemon" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Check Java environment
Write-Host "🔍 Java Environment:" -ForegroundColor Yellow
if ($env:JAVA_HOME) {
    Write-Host "  JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Green
    
    $javaExe = "$env:JAVA_HOME\bin\java.exe"
    if (Test-Path $javaExe) {
        try {
            $javaVersion = & $javaExe -version 2>&1 | Select-String "version" | Select-Object -First 1
            Write-Host "  Java Version: $($javaVersion.Line)" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  Could not get Java version" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ⚠️  JAVA_HOME not set" -ForegroundColor Yellow
}

# Check Android SDK
Write-Host "🔍 Android SDK:" -ForegroundColor Yellow
if ($env:ANDROID_HOME) {
    Write-Host "  ANDROID_HOME: $env:ANDROID_HOME" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  ANDROID_HOME not set" -ForegroundColor Yellow
}

# Network connectivity test
Write-Host "🔍 Network Connectivity:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://services.gradle.org" -TimeoutSec 10 -UseBasicParsing
    Write-Host "  ✅ Gradle services reachable (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Cannot reach Gradle services: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "     This may cause build hangs during dependency download" -ForegroundColor Yellow
}

# Test build with timeout
Write-Host "🔧 Running diagnostic build..." -ForegroundColor Yellow

$buildArgs = @("assembleDebug")
if ($Verbose) { $buildArgs += "--info" }
if ($Debug) { $buildArgs += "--debug" }
$buildArgs += "--stacktrace"
$buildArgs += "--no-daemon"  # Disable daemon for diagnostic

Write-Host "Executing: .\gradlew.bat $($buildArgs -join ' ')" -ForegroundColor Gray

# Create a job to run the build with timeout
$job = Start-Job -ScriptBlock {
    param($BuildArgs)
    Set-Location $using:PWD
    & .\gradlew.bat @BuildArgs
} -ArgumentList $buildArgs

# Wait for job with timeout (5 minutes)
$timeout = 300
$completed = Wait-Job $job -Timeout $timeout

if ($completed) {
    $result = Receive-Job $job
    Write-Host "✅ Build completed" -ForegroundColor Green
    $result
} else {
    Write-Host "❌ Build timed out after $timeout seconds" -ForegroundColor Red
    Write-Host "🔍 This indicates a hanging build. Common causes:" -ForegroundColor Yellow
    Write-Host "  • Network connectivity issues" -ForegroundColor White
    Write-Host "  • Insufficient memory" -ForegroundColor White
    Write-Host "  • Gradle daemon issues" -ForegroundColor White
    Write-Host "  • Lock file conflicts" -ForegroundColor White
    Write-Host "  • Antivirus software interference" -ForegroundColor White
    
    # Stop the hanging job
    Stop-Job $job -ErrorAction SilentlyContinue
}

Remove-Job $job -ErrorAction SilentlyContinue

Write-Host "`n💡 Recommendations to prevent hangs:" -ForegroundColor Cyan
Write-Host "  • Ensure stable internet connection" -ForegroundColor White
Write-Host "  • Close unnecessary applications to free memory" -ForegroundColor White
Write-Host "  • Add gradle files to antivirus exclusions" -ForegroundColor White
Write-Host "  • Use .\android-diagnostic.ps1 -Clean before builds" -ForegroundColor White
Write-Host "  • Consider using offline mode: gradlew --offline assembleDebug" -ForegroundColor White
