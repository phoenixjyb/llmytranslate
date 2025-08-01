# LLMyTranslate Android Build Script
# PowerShell script for building and deploying the Android app

param(
    [string]$Action = "build",
    [switch]$Install,
    [switch]$Clean,
    [switch]$Release,
    [switch]$Debug = $true,
    [switch]$Verbose,
    [switch]$ShowProgress = $true
)

$AndroidDir = Join-Path $PSScriptRoot "..\..\android"
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
    
    # Check multiple possible Android Studio locations
    $androidStudioPaths = @(
        "D:\Program Files\Android\Android Studio\jbr\bin\java.exe",
        "C:\Program Files\Android\Android Studio\jbr\bin\java.exe",
        "${env:LOCALAPPDATA}\Android\Sdk\java\bin\java.exe"
    )
    
    foreach ($studioJava in $androidStudioPaths) {
        if (Test-Path $studioJava) {
            $javaWorking = Test-JavaVersion -JavaPath $studioJava
            
            if ($javaWorking) {
                # Set up environment to use Android Studio Java
                $studioJavaHome = Split-Path (Split-Path $studioJava)
                $env:JAVA_HOME = $studioJavaHome
                $env:PATH = "$studioJavaHome\bin;$env:PATH"
                Write-Host "✅ Using Android Studio Java: $studioJavaHome" -ForegroundColor Green
                break
            }
        }
    }
}

if (-not $javaWorking) {
    Write-Error "❌ No suitable Java installation found. Please install Java 11+ or check Android Studio installation."
    Write-Host "💡 Suggestion: Run .\setup-android-dev.ps1 to check your environment" -ForegroundColor Cyan
    exit 1
}

# Check Android SDK (optional but recommended)
Write-Host "Checking Android SDK..." -ForegroundColor Yellow

# Function to find Android SDK
function Find-AndroidSDK {
    $sdkPaths = @(
        $env:ANDROID_HOME,
        $env:ANDROID_SDK_ROOT,
        "${env:LOCALAPPDATA}\Android\Sdk",
        "D:\Android\Sdk",
        "D:\Program Files\Android\Sdk",
        "C:\Android\Sdk",
        "C:\Program Files\Android\Sdk"
    )
    
    foreach ($sdkPath in $sdkPaths) {
        if ($sdkPath -and (Test-Path $sdkPath) -and (Test-Path "$sdkPath\platform-tools")) {
            return $sdkPath
        }
    }
    return $null
}

$foundSDK = Find-AndroidSDK

if ($foundSDK) {
    Write-Host "✅ Android SDK found: $foundSDK" -ForegroundColor Green
    $env:ANDROID_HOME = $foundSDK
    $env:ANDROID_SDK_ROOT = $foundSDK
    $env:PATH = "$foundSDK\platform-tools;$foundSDK\tools;$foundSDK\tools\bin;$env:PATH"
} else {
    Write-Host "⚠️  Android SDK not found in common locations" -ForegroundColor Yellow
    Write-Host "   Checking if gradle wrapper can download SDK automatically..." -ForegroundColor Gray
    Write-Host "   For device installation, you may need to:" -ForegroundColor Cyan
    Write-Host "   1. Install Android SDK Command Line Tools" -ForegroundColor Cyan
    Write-Host "   2. Set ANDROID_HOME environment variable" -ForegroundColor Cyan
}

# Navigate to Android directory
Set-Location $AndroidDir

# Enhanced Gradle handling
Write-Host "Checking Gradle wrapper..." -ForegroundColor Yellow

# Function to find Android Studio Gradle
function Find-AndroidStudioGradle {
    $gradlePaths = @(
        "D:\Program Files\Android\Android Studio\plugins\gradle\lib",
        "C:\Program Files\Android\Android Studio\plugins\gradle\lib"
    )
    
    foreach ($gradlePath in $gradlePaths) {
        if (Test-Path $gradlePath) {
            $gradleJars = Get-ChildItem "$gradlePath\gradle-*.jar" -ErrorAction SilentlyContinue
            if ($gradleJars) {
                Write-Host "✅ Found Android Studio Gradle: $gradlePath" -ForegroundColor Green
                return $gradlePath
            }
        }
    }
    return $null
}

$studioGradle = Find-AndroidStudioGradle

# Check if gradlew wrapper exists
if (-not (Test-Path ".\gradlew.bat")) {
    Write-Host "⚠️  Gradle wrapper not found. Creating basic gradle.properties..." -ForegroundColor Yellow
    
    # Create basic gradle.properties to avoid network timeouts
    $gradlePropsContent = @"
# Gradle build properties for LLMyTranslate Android
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true

# Use offline mode if network issues persist
# org.gradle.offline=true

# Android build settings
android.useAndroidX=true
android.enableJetifier=true
"@
    
    New-Item -Path "gradle.properties" -ItemType File -Value $gradlePropsContent -Force | Out-Null
    Write-Host "✅ Created gradle.properties with optimized settings" -ForegroundColor Green
}

# Function to run Gradle with enhanced error handling and verbose logging
function Invoke-GradleWrapper {
    param([string]$Task, [switch]$OfflineMode = $false, [switch]$Verbose = $false)
    
    # Check for local Gradle installation first
    $localGradle = $null
    $gradlePaths = @(
        "C:\gradle\gradle-8.4\bin\gradle.bat",
        "C:\gradle\gradle-8.3\bin\gradle.bat",
        "C:\gradle\gradle-8.2\bin\gradle.bat"
    )
    
    foreach ($gradlePath in $gradlePaths) {
        if (Test-Path $gradlePath) {
            $localGradle = $gradlePath
            Write-Host "✅ Using local Gradle: $gradlePath" -ForegroundColor Green
            break
        }
    }
    
    # Check system PATH for gradle
    if (-not $localGradle) {
        try {
            $null = Get-Command gradle -ErrorAction Stop
            $localGradle = "gradle"
            Write-Host "✅ Using system Gradle from PATH" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  No local Gradle found, using wrapper" -ForegroundColor Yellow
        }
    }
    
    $gradleArgs = @($Task)
    
    if ($OfflineMode) {
        $gradleArgs += "--offline"
        Write-Host "🔄 Running Gradle in offline mode..." -ForegroundColor Cyan
    }
    
    # Add detailed logging options
    $gradleArgs += "--stacktrace"
    if ($Verbose) {
        $gradleArgs += "--info"
        Write-Host "📝 Verbose logging enabled" -ForegroundColor Cyan
    } else {
        # Show lifecycle events for progress indication
        $gradleArgs += "--console=plain"
    }
    
    # Add parallel builds for performance
    $gradleArgs += "--parallel"
    
    # Display build information
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "⏰ Started at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
    
    if ($localGradle) {
        if ($localGradle -eq "gradle") {
            Write-Host "🚀 Executing: gradle $($gradleArgs -join ' ')" -ForegroundColor Green
        } else {
            Write-Host "🚀 Executing: $localGradle $($gradleArgs -join ' ')" -ForegroundColor Green
        }
    } else {
        Write-Host "🚀 Executing: .\gradlew.bat $($gradleArgs -join ' ')" -ForegroundColor Green
    }
    
    Write-Host "💡 Tip: First build may take 5-15 minutes (downloading dependencies)" -ForegroundColor Yellow
    Write-Host "🔍 Watch for these key stages:" -ForegroundColor Cyan
    Write-Host "   • Gradle daemon startup" -ForegroundColor White
    Write-Host "   • Dependency resolution" -ForegroundColor White
    Write-Host "   • Configuration phase" -ForegroundColor White
    Write-Host "   • Task execution" -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    try {
        $startTime = Get-Date
        
        if ($localGradle) {
            if ($localGradle -eq "gradle") {
                gradle @gradleArgs
            } else {
                & $localGradle @gradleArgs
            }
        } else {
            .\gradlew.bat @gradleArgs
        }
        
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "⏰ Completed at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
        Write-Host "⌛ Total duration: $("{0:mm\:ss}" -f $duration)" -ForegroundColor Gray
        Write-Host "📊 Exit code: $LASTEXITCODE" -ForegroundColor Gray
        
        return $LASTEXITCODE
    } catch {
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Error "❌ Gradle execution failed: $_"
        Write-Host "⏰ Failed at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Red
        return 1
    }
}

switch ($Action.ToLower()) {
    "build" {
        Write-Host "Building Android APK..." -ForegroundColor Green
        
        if ($Clean) {
            Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
            $cleanResult = Invoke-GradleWrapper -Task "clean" -Verbose:$Verbose
            if ($cleanResult -ne 0) {
                Write-Host "⚠️  Clean failed, but continuing with build..." -ForegroundColor Yellow
            }
        }
        
        $buildTask = if ($Release) { "assembleRelease" } else { "assembleDebug" }
        Write-Host "🔨 Running build task: $buildTask" -ForegroundColor Cyan
        
        # Add pre-build information
        Write-Host "📋 Build Configuration:" -ForegroundColor Yellow
        Write-Host "   • Build Type: $(if ($Release) { 'Release' } else { 'Debug' })" -ForegroundColor White
        Write-Host "   • Verbose Logging: $Verbose" -ForegroundColor White
        Write-Host "   • Clean Build: $Clean" -ForegroundColor White
        Write-Host "   • Install After Build: $Install" -ForegroundColor White
        
        # Try normal build first
        $buildResult = Invoke-GradleWrapper -Task $buildTask -Verbose:$Verbose
        
        # If build fails due to network issues, try offline mode
        if ($buildResult -ne 0) {
            Write-Host "⚠️  Build failed, trying offline mode..." -ForegroundColor Yellow
            $buildResult = Invoke-GradleWrapper -Task $buildTask -OfflineMode -Verbose:$Verbose
        }
        
        if ($buildResult -eq 0) {
            Write-Host "✅ Build successful!" -ForegroundColor Green
            
            $apkPath = if ($Release) {
                "app\build\outputs\apk\release\app-release.apk"
            } else {
                "app\build\outputs\apk\debug\app-debug.apk"
            }
            
            if (Test-Path $apkPath) {
                Write-Host "📱 APK created: $apkPath" -ForegroundColor Cyan
                
                if ($Install) {
                    Write-Host "📲 Installing APK on connected device..." -ForegroundColor Yellow
                    $installTask = if ($Release) { "installRelease" } else { "installDebug" }
                    $installResult = Invoke-GradleWrapper -Task $installTask -Verbose:$Verbose
                    
                    if ($installResult -eq 0) {
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
        $result = Invoke-GradleWrapper -Task $installTask -Verbose:$Verbose
        if ($result -ne 0) { exit $result }
    }
    
    "test" {
        Write-Host "Running tests..." -ForegroundColor Green
        $result = Invoke-GradleWrapper -Task "test" -Verbose:$Verbose
        if ($result -ne 0) { exit $result }
    }
    
    "clean" {
        Write-Host "Cleaning build artifacts..." -ForegroundColor Green
        $result = Invoke-GradleWrapper -Task "clean" -Verbose:$Verbose
        if ($result -ne 0) { exit $result }
    }
    
    "sync" {
        Write-Host "Syncing Gradle dependencies..." -ForegroundColor Green
        $result = Invoke-GradleWrapper -Task "--refresh-dependencies" -Verbose:$Verbose
        if ($result -ne 0) { exit $result }
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
