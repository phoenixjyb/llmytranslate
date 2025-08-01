# Android SDK Setup Helper
# Helps locate and configure Android SDK from Android Studio installation

param(
    [switch]$SetEnvironment,
    [switch]$CreateSdkDir,
    [string]$CustomPath
)

Write-Host "=== Android SDK Setup Helper ===" -ForegroundColor Cyan
Write-Host "Searching for Android SDK installations..." -ForegroundColor Yellow

# Function to find Android SDK
function Find-AndroidSDK {
    $searchPaths = @(
        $env:ANDROID_HOME,
        $env:ANDROID_SDK_ROOT,
        "${env:LOCALAPPDATA}\Android\Sdk",
        "D:\Android\Sdk",
        "D:\Users\$env:USERNAME\AppData\Local\Android\Sdk",
        "D:\Program Files\Android\Sdk", 
        "C:\Android\Sdk",
        "C:\Program Files\Android\Sdk",
        "${env:USERPROFILE}\AppData\Local\Android\Sdk"
    )
    
    if ($CustomPath) {
        $searchPaths = @($CustomPath) + $searchPaths
    }
    
    Write-Host "Checking SDK locations:" -ForegroundColor Gray
    
    $foundSdks = @()
    
    foreach ($path in $searchPaths) {
        if ($path) {
            Write-Host "  Checking: $path" -ForegroundColor Gray
            
            if (Test-Path $path) {
                $platformTools = Join-Path $path "platform-tools"
                $buildTools = Join-Path $path "build-tools"
                $platforms = Join-Path $path "platforms"
                
                if ((Test-Path $platformTools) -and (Test-Path $buildTools) -and (Test-Path $platforms)) {
                    Write-Host "  ✅ Valid SDK found: $path" -ForegroundColor Green
                    
                    # Get SDK details
                    $buildToolsVersions = Get-ChildItem $buildTools -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
                    $platformVersions = Get-ChildItem $platforms -Directory -ErrorAction SilentlyContinue
                    
                    $sdkInfo = @{
                        Path = $path
                        BuildTools = $buildToolsVersions | Select-Object -First 5 | ForEach-Object { $_.Name }
                        Platforms = $platformVersions | ForEach-Object { $_.Name }
                        HasAdb = Test-Path (Join-Path $platformTools "adb.exe")
                        Size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB
                    }
                    
                    $foundSdks += $sdkInfo
                } else {
                    Write-Host "  ⚠️  Directory exists but missing SDK components" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ❌ Path not found" -ForegroundColor Red
            }
        }
    }
    
    return $foundSdks
}

# Function to suggest SDK setup from Android Studio
function Suggest-AndroidStudioSDK {
    Write-Host "`n=== Android Studio SDK Setup ===" -ForegroundColor Cyan
    
    $studioPaths = @(
        "D:\Program Files\Android\Android Studio",
        "C:\Program Files\Android\Android Studio"
    )
    
    foreach ($studioPath in $studioPaths) {
        if (Test-Path $studioPath) {
            Write-Host "✅ Android Studio found: $studioPath" -ForegroundColor Green
            
            # Check if SDK Manager is available
            $sdkManagerPath = Join-Path $studioPath "bin\studio64.exe"
            if (Test-Path $sdkManagerPath) {
                Write-Host "💡 To set up Android SDK through Android Studio:" -ForegroundColor Cyan
                Write-Host "   1. Open Android Studio: $sdkManagerPath" -ForegroundColor White
                Write-Host "   2. Go to File > Settings > Appearance & Behavior > System Settings > Android SDK" -ForegroundColor White
                Write-Host "   3. Note the 'Android SDK Location' path" -ForegroundColor White
                Write-Host "   4. Install required SDK platforms and build tools" -ForegroundColor White
                Write-Host "   5. Run this script again with -CustomPath 'your-sdk-path'" -ForegroundColor White
            }
            
            return $true
        }
    }
    
    Write-Host "❌ Android Studio not found in common locations" -ForegroundColor Red
    return $false
}

# Function to create SDK directory structure
function New-AndroidSDKStructure {
    param([string]$SdkPath)
    
    Write-Host "Creating basic SDK directory structure at: $SdkPath" -ForegroundColor Cyan
    
    $directories = @(
        "platform-tools",
        "build-tools", 
        "platforms",
        "tools",
        "sources",
        "system-images"
    )
    
    try {
        foreach ($dir in $directories) {
            $fullPath = Join-Path $SdkPath $dir
            if (-not (Test-Path $fullPath)) {
                New-Item -Path $fullPath -ItemType Directory -Force | Out-Null
                Write-Host "  Created: $dir" -ForegroundColor Green
            }
        }
        
        Write-Host "✅ SDK directory structure created" -ForegroundColor Green
        Write-Host "💡 You'll need to install SDK components using Android Studio or command line tools" -ForegroundColor Cyan
        
        return $true
    } catch {
        Write-Error "Failed to create SDK structure: $_"
        return $false
    }
}

# Main execution
$foundSdks = Find-AndroidSDK

if ($foundSdks.Count -eq 0) {
    Write-Host "`n❌ No Android SDK installations found!" -ForegroundColor Red
    
    if ($CreateSdkDir) {
        $suggestedPath = if ($CustomPath) { $CustomPath } else { "D:\Android\Sdk" }
        Write-Host "Creating new SDK directory at: $suggestedPath" -ForegroundColor Yellow
        
        if (New-AndroidSDKStructure -SdkPath $suggestedPath) {
            Write-Host "✅ SDK directory created. Set ANDROID_HOME to: $suggestedPath" -ForegroundColor Green
        }
    } else {
        Suggest-AndroidStudioSDK
        Write-Host "`n💡 Options to proceed:" -ForegroundColor Cyan
        Write-Host "   • Run with -CreateSdkDir to create a new SDK directory" -ForegroundColor White
        Write-Host "   • Run with -CustomPath 'path' if you know where your SDK is" -ForegroundColor White
        Write-Host "   • Install Android SDK through Android Studio" -ForegroundColor White
    }
} else {
    Write-Host "`n✅ Found $($foundSdks.Count) Android SDK installation(s):" -ForegroundColor Green
    
    for ($i = 0; $i -lt $foundSdks.Count; $i++) {
        $sdk = $foundSdks[$i]
        Write-Host "`n[$($i + 1)] SDK Path: $($sdk.Path)" -ForegroundColor Cyan
        Write-Host "    Size: $([math]::Round($sdk.Size, 2)) GB" -ForegroundColor Gray
        Write-Host "    ADB Available: $($sdk.HasAdb)" -ForegroundColor Gray
        Write-Host "    Build Tools: $($sdk.BuildTools -join ', ')" -ForegroundColor Gray
        Write-Host "    Platforms: $($sdk.Platforms -join ', ')" -ForegroundColor Gray
    }
    
    # Use the first SDK found
    $primarySDK = $foundSdks[0].Path
    
    if ($SetEnvironment) {
        Write-Host "`n🔧 Setting environment variables for current session..." -ForegroundColor Yellow
        $env:ANDROID_HOME = $primarySDK
        $env:ANDROID_SDK_ROOT = $primarySDK
        $env:PATH = "$primarySDK\platform-tools;$primarySDK\tools;$primarySDK\tools\bin;$env:PATH"
        
        Write-Host "✅ Environment variables set:" -ForegroundColor Green
        Write-Host "   ANDROID_HOME = $env:ANDROID_HOME" -ForegroundColor White
        Write-Host "   ANDROID_SDK_ROOT = $env:ANDROID_SDK_ROOT" -ForegroundColor White
        Write-Host "   PATH updated with SDK tools" -ForegroundColor White
        
        Write-Host "`n💡 To make these permanent, add them to your system environment variables" -ForegroundColor Cyan
    } else {
        Write-Host "`n💡 To use this SDK, run:" -ForegroundColor Cyan
        Write-Host "   .\setup-android-sdk.ps1 -SetEnvironment" -ForegroundColor White
        Write-Host "`nOr set these environment variables manually:" -ForegroundColor Cyan
        Write-Host "   ANDROID_HOME = $primarySDK" -ForegroundColor White
        Write-Host "   ANDROID_SDK_ROOT = $primarySDK" -ForegroundColor White
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Current environment:" -ForegroundColor Gray
Write-Host "  ANDROID_HOME: $env:ANDROID_HOME" -ForegroundColor Gray
Write-Host "  ANDROID_SDK_ROOT: $env:ANDROID_SDK_ROOT" -ForegroundColor Gray

if ($env:ANDROID_HOME -and (Test-Path "$env:ANDROID_HOME\platform-tools\adb.exe")) {
    Write-Host "✅ Android development environment is ready!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Android development environment needs setup" -ForegroundColor Yellow
}
