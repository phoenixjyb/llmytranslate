# LLMyTranslate Android Build Script
# PowerShell script for building and deploying the Android app

param(
    [string]$Action = "build",
    [switch]$Install,
    [switch]$Clean,
    [switch]$Release,
    [switch]$Debug = $true
)

$AndroidDir = Join-Path $PSScriptRoot "android"
$BuildType = if ($Release) { "Release" } else { "Debug" }

Write-Host "=== LLMyTranslate Android Builder ===" -ForegroundColor Cyan
Write-Host "Build Type: $BuildType" -ForegroundColor Yellow
Write-Host "Android Directory: $AndroidDir" -ForegroundColor Gray

# Check if Android directory exists
if (-not (Test-Path $AndroidDir)) {
    Write-Error "Android directory not found: $AndroidDir"
    exit 1
}

# Check Java installation
Write-Host "Checking Java installation..." -ForegroundColor Yellow

# Function to test Java installation
function Test-JavaVersion {
    param([string]$JavaPath = "java")
    
    try {
        if ($JavaPath -eq "java") {
            $javaVersion = java -version 2>&1 | Select-String "version"
        } else {
            $javaVersion = & $JavaPath -version 2>&1 | Select-String "version"
        }
        
        if ($javaVersion) {
            $versionLine = $javaVersion.Line
            $versionNumber = ($versionLine -split '"')[1]
            $majorVersion = ($versionNumber -split '\.')[0]
            
            Write-Host "✅ Java found: $versionLine" -ForegroundColor Green
            
            if ([int]$majorVersion -ge 11) {
                Write-Host "✅ Java version $majorVersion is suitable for Android development" -ForegroundColor Green
                return $true
            } else {
                Write-Host "⚠️  Java version $majorVersion is too old (need 11+)" -ForegroundColor Yellow
                return $false
            }
        }
    } catch {
        return $false
    }
    return $false
}

# Try system Java first
$javaWorking = Test-JavaVersion

# If system Java not working, try Android Studio Java
if (-not $javaWorking) {
    Write-Host "System Java not found, checking Android Studio..." -ForegroundColor Yellow
    $androidStudioJava = "D:\Program Files\Android\Android Studio\jbr\bin\java.exe"
    
    if (Test-Path $androidStudioJava) {
        $javaWorking = Test-JavaVersion -JavaPath $androidStudioJava
        
        if ($javaWorking) {
            # Set up environment to use Android Studio Java
            $env:JAVA_HOME = "D:\Program Files\Android\Android Studio\jbr"
            $env:PATH = "D:\Program Files\Android\Android Studio\jbr\bin;$env:PATH"
            Write-Host "✅ Using Android Studio Java for build" -ForegroundColor Green
        }
    }
}

if (-not $javaWorking) {
    Write-Error "❌ No suitable Java installation found. Please install Java 11+ or check Android Studio installation."
    Write-Host "💡 Suggestion: Run .\setup-android-dev.ps1 to check your environment" -ForegroundColor Cyan
    exit 1
}
    } else {
        throw "Java not found"
    }
} catch {
    Write-Host "❌ Java not found or not in PATH" -ForegroundColor Red
    Write-Host "Please install OpenJDK 11 or 17:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://adoptium.net/temurin/releases/" -ForegroundColor Cyan
    Write-Host "  2. Set JAVA_HOME environment variable" -ForegroundColor Cyan
    Write-Host "  3. Add JAVA_HOME\bin to PATH" -ForegroundColor Cyan
    Write-Host "  4. Restart PowerShell and try again" -ForegroundColor Cyan
    exit 1
}

# Check Android SDK (optional but recommended)
if ($env:ANDROID_HOME) {
    Write-Host "✅ ANDROID_HOME set: $env:ANDROID_HOME" -ForegroundColor Green
} else {
    Write-Host "⚠️  ANDROID_HOME not set (optional for building)" -ForegroundColor Yellow
    Write-Host "   For device installation, install Android SDK Command Line Tools" -ForegroundColor Gray
}

# Navigate to Android directory
Set-Location $AndroidDir

switch ($Action.ToLower()) {
    "build" {
        Write-Host "Building Android APK..." -ForegroundColor Green
        
        if ($Clean) {
            Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
            & .\gradlew.bat clean
        }
        
        $buildTask = if ($Release) { "assembleRelease" } else { "assembleDebug" }
        & .\gradlew.bat $buildTask
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Build successful!" -ForegroundColor Green
            
            $apkPath = if ($Release) {
                "app\build\outputs\apk\release\app-release.apk"
            } else {
                "app\build\outputs\apk\debug\app-debug.apk"
            }
            
            if (Test-Path $apkPath) {
                Write-Host "📱 APK created: $apkPath" -ForegroundColor Cyan
                
                if ($Install) {
                    Write-Host "Installing APK on connected device..." -ForegroundColor Yellow
                    $installTask = if ($Release) { "installRelease" } else { "installDebug" }
                    & .\gradlew.bat $installTask
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "✅ App installed successfully!" -ForegroundColor Green
                    } else {
                        Write-Error "❌ Installation failed!"
                    }
                }
            }
        } else {
            Write-Error "❌ Build failed!"
        }
    }
    
    "install" {
        Write-Host "Installing app on connected device..." -ForegroundColor Green
        $installTask = if ($Release) { "installRelease" } else { "installDebug" }
        & .\gradlew.bat $installTask
    }
    
    "test" {
        Write-Host "Running tests..." -ForegroundColor Green
        & .\gradlew.bat test
    }
    
    "clean" {
        Write-Host "Cleaning build artifacts..." -ForegroundColor Green
        & .\gradlew.bat clean
    }
    
    "sync" {
        Write-Host "Syncing Gradle dependencies..." -ForegroundColor Green
        & .\gradlew.bat --refresh-dependencies
    }
    
    "devices" {
        Write-Host "Checking connected devices..." -ForegroundColor Green
        adb devices
    }
    
    "logs" {
        Write-Host "Showing app logs (press Ctrl+C to stop)..." -ForegroundColor Green
        adb logcat | Select-String "LLMyTranslate"
    }
    
    default {
        Write-Host "Usage: .\build-android.ps1 [Action] [Options]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  build    - Build the APK (default)"
        Write-Host "  install  - Install APK on connected device"
        Write-Host "  test     - Run unit tests"
        Write-Host "  clean    - Clean build artifacts"
        Write-Host "  sync     - Sync Gradle dependencies"
        Write-Host "  devices  - List connected devices"
        Write-Host "  logs     - Show app logs"
        Write-Host ""
        Write-Host "Options:" -ForegroundColor Cyan
        Write-Host "  -Install   - Install after building"
        Write-Host "  -Clean     - Clean before building"
        Write-Host "  -Release   - Build release version"
        Write-Host "  -Debug     - Build debug version (default)"
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Green
        Write-Host "  .\build-android.ps1 build -Install -Clean"
        Write-Host "  .\build-android.ps1 build -Release"
        Write-Host "  .\build-android.ps1 devices"
        Write-Host "  .\build-android.ps1 logs"
    }
}

Write-Host ""
Write-Host "=== Build Script Complete ===" -ForegroundColor Cyan
