# Android Development Environment Setup (Command Line Only)
# PowerShell script to setup minimal Android development environment

param(
    [switch]$SkipJava,
    [switch]$SkipAndroidSDK,
    [switch]$CheckOnly
)

Write-Host "🚀 Android Development Environment Setup" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

function Test-JavaInstallation {
    Write-Host "`n☕ Checking Java installation..." -ForegroundColor Yellow
    
    # First check if java is in PATH
    try {
        $javaVersion = java -version 2>&1 | Select-String "version"
        if ($javaVersion) {
            Write-Host "✅ Java found in PATH: $($javaVersion.Line)" -ForegroundColor Green
            
            # Check if it's a suitable version (11 or higher)
            $versionNumber = ($javaVersion.Line -split '"')[1]
            $majorVersion = ($versionNumber -split '\.')[0]
            if ([int]$majorVersion -ge 11) {
                Write-Host "✅ Java version is suitable for Android development" -ForegroundColor Green
                return $true
            } else {
                Write-Host "⚠️  Java version $majorVersion is too old. Need Java 11 or higher." -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "⚠️  Java not found in PATH, checking Android Studio..." -ForegroundColor Yellow
    }
    
    # Check Android Studio bundled JDK
    $androidStudioJava = "D:\Program Files\Android\Android Studio\jbr\bin\java.exe"
    if (Test-Path $androidStudioJava) {
        try {
            $javaVersion = & $androidStudioJava -version 2>&1 | Select-String "version"
            if ($javaVersion) {
                Write-Host "✅ Java found in Android Studio: $($javaVersion.Line)" -ForegroundColor Green
                Write-Host "   Location: $androidStudioJava" -ForegroundColor Cyan
                
                # Check version
                $versionNumber = ($javaVersion.Line -split '"')[1]
                $majorVersion = ($versionNumber -split '\.')[0]
                if ([int]$majorVersion -ge 11) {
                    Write-Host "✅ Android Studio Java version is suitable for development" -ForegroundColor Green
                    return $true
                }
            }
        } catch {
            Write-Host "❌ Cannot execute Android Studio Java" -ForegroundColor Red
        }
    }
    
    Write-Host "❌ No suitable Java installation found" -ForegroundColor Red
    return $false
}

function Test-AndroidSDK {
    Write-Host "`n🤖 Checking Android SDK..." -ForegroundColor Yellow
    
    # Check standard locations for Android SDK
    $sdkLocations = @(
        $env:ANDROID_HOME,
        "$env:LOCALAPPDATA\Android\Sdk",
        "C:\Android\Sdk"
    )
    
    foreach ($sdkPath in $sdkLocations) {
        if ($sdkPath -and (Test-Path $sdkPath)) {
            Write-Host "✅ Android SDK found: $sdkPath" -ForegroundColor Green
            
            # Check if platform-tools exists
            $adbPath = Join-Path $sdkPath "platform-tools\adb.exe"
            if (Test-Path $adbPath) {
                Write-Host "✅ ADB found: $adbPath" -ForegroundColor Green
                
                # Set ANDROID_HOME if not already set
                if (-not $env:ANDROID_HOME -or $env:ANDROID_HOME -ne $sdkPath) {
                    Write-Host "ℹ️  Setting ANDROID_HOME to: $sdkPath" -ForegroundColor Cyan
                    $env:ANDROID_HOME = $sdkPath
                }
                
                return $true
            } else {
                Write-Host "⚠️  ADB not found. Platform tools may not be installed." -ForegroundColor Yellow
                Write-Host "   SDK Path: $sdkPath" -ForegroundColor Gray
                return $false
            }
        }
    }
    
    Write-Host "❌ Android SDK not found in standard locations" -ForegroundColor Red
    return $false
}

function Show-JavaInstallInstructions {
    Write-Host "`n📋 Java Installation Instructions:" -ForegroundColor Cyan
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host "Option 1 - Use Android Studio's Java (Recommended):" -ForegroundColor Green
    Write-Host "   Your Android Studio includes Java 21. Add to PATH:" -ForegroundColor White
    Write-Host '   PATH += "D:\Program Files\Android\Android Studio\jbr\bin"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2 - Install separate OpenJDK:" -ForegroundColor Yellow
    Write-Host "1. Download OpenJDK 17 (LTS) from:" -ForegroundColor White
    Write-Host "   https://adoptium.net/temurin/releases/" -ForegroundColor Blue
    Write-Host ""
    Write-Host "2. Install using the MSI installer" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Set environment variables:" -ForegroundColor White
    Write-Host "   JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-17.x.x.x-hotspot" -ForegroundColor Gray
    Write-Host "   PATH += %JAVA_HOME%\bin" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Restart PowerShell and verify:" -ForegroundColor White
    Write-Host "   java -version" -ForegroundColor Gray
    Write-Host "   javac -version" -ForegroundColor Gray
}

function Show-AndroidSDKInstructions {
    Write-Host "`n📋 Android SDK Installation Instructions:" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "1. Download Android Command Line Tools from:" -ForegroundColor White
    Write-Host "   https://developer.android.com/studio#command-tools" -ForegroundColor Blue
    Write-Host ""
    Write-Host "2. Extract to: C:\Android\cmdline-tools\latest\" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Set environment variables:" -ForegroundColor White
    Write-Host "   ANDROID_HOME = C:\Android" -ForegroundColor Gray
    Write-Host "   PATH += %ANDROID_HOME%\cmdline-tools\latest\bin" -ForegroundColor Gray
    Write-Host "   PATH += %ANDROID_HOME%\platform-tools" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Install required components:" -ForegroundColor White
    Write-Host "   sdkmanager --licenses" -ForegroundColor Gray
    Write-Host "   sdkmanager ""platform-tools"" ""platforms;android-34"" ""build-tools;34.0.0""" -ForegroundColor Gray
    Write-Host ""
    Write-Host "5. Verify installation:" -ForegroundColor White
    Write-Host "   adb version" -ForegroundColor Gray
}

function Show-QuickStart {
    Write-Host "`n🎯 Quick Start Guide:" -ForegroundColor Green
    Write-Host "=====================" -ForegroundColor Green
    Write-Host "After setup is complete, you can:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. Build Android APK:" -ForegroundColor White
    Write-Host "   .\build-android.ps1 build" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Build and install on device:" -ForegroundColor White
    Write-Host "   .\build-android.ps1 build -Install" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Check connected devices:" -ForegroundColor White
    Write-Host "   .\build-android.ps1 devices" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Start LLMyTranslate server:" -ForegroundColor White
    Write-Host "   .\start-service.ps1" -ForegroundColor Gray
}

# Main execution
if ($CheckOnly) {
    Write-Host "🔍 Environment Check Mode" -ForegroundColor Magenta
}

$javaOK = Test-JavaInstallation
$androidOK = Test-AndroidSDK

Write-Host "`n📊 Environment Status:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Java JDK:     $(if ($javaOK) { '✅ Ready' } else { '❌ Missing' })" -ForegroundColor $(if ($javaOK) { 'Green' } else { 'Red' })
Write-Host "Android SDK:  $(if ($androidOK) { '✅ Ready' } else { '❌ Missing' })" -ForegroundColor $(if ($androidOK) { 'Green' } else { 'Red' })

if ($javaOK -and $androidOK) {
    Write-Host "`n🎉 Environment is ready for Android development!" -ForegroundColor Green
    Show-QuickStart
    exit 0
}

if ($CheckOnly) {
    Write-Host "`nRun without -CheckOnly to see installation instructions." -ForegroundColor Yellow
    exit 1
}

# Show installation instructions for missing components
if (-not $javaOK -and -not $SkipJava) {
    Show-JavaInstallInstructions
}

if (-not $androidOK -and -not $SkipAndroidSDK) {
    Show-AndroidSDKInstructions
}

if (-not $javaOK -or -not $androidOK) {
    Write-Host "`n⚠️  Please install missing components and run this script again." -ForegroundColor Yellow
    Write-Host "Or use -CheckOnly to just check current status." -ForegroundColor Gray
    exit 1
}
