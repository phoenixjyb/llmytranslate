# Gradle Manual Installation Script
# Downloads and installs Gradle locally to bypass network issues during build

param(
    [string]$GradleVersion = "8.4",
    [string]$InstallPath = "C:\gradle"
)

Write-Host "=== Gradle Manual Installer ===" -ForegroundColor Cyan
Write-Host "Installing Gradle $GradleVersion to $InstallPath" -ForegroundColor Yellow

# Create installation directory
if (-not (Test-Path $InstallPath)) {
    New-Item -Path $InstallPath -ItemType Directory -Force | Out-Null
    Write-Host "✅ Created installation directory: $InstallPath" -ForegroundColor Green
}

$gradleDir = Join-Path $InstallPath "gradle-$GradleVersion"

# Check if already installed
if (Test-Path $gradleDir) {
    Write-Host "✅ Gradle $GradleVersion already installed at $gradleDir" -ForegroundColor Green
    
    # Test the installation
    $gradleBin = Join-Path $gradleDir "bin\gradle.bat"
    if (Test-Path $gradleBin) {
        Write-Host "Testing Gradle installation..." -ForegroundColor Yellow
        try {
            $version = & $gradleBin --version 2>$null | Select-String "Gradle"
            if ($version) {
                Write-Host "✅ Gradle is working: $($version.Line)" -ForegroundColor Green
                
                # Update PATH for current session
                $gradleBinDir = Join-Path $gradleDir "bin"
                if ($env:PATH -notlike "*$gradleBinDir*") {
                    $env:PATH = "$gradleBinDir;$env:PATH"
                    Write-Host "✅ Added Gradle to PATH for current session" -ForegroundColor Green
                }
                
                Write-Host "`n💡 To make Gradle permanently available:" -ForegroundColor Cyan
                Write-Host "   Add to system PATH: $gradleBinDir" -ForegroundColor White
                Write-Host "`n💡 To use with Android project:" -ForegroundColor Cyan
                Write-Host "   Run: gradle assembleDebug (instead of gradlew)" -ForegroundColor White
                
                return
            }
        } catch {
            Write-Host "⚠️  Installation found but not working, reinstalling..." -ForegroundColor Yellow
        }
    }
}

# Download URL
$downloadUrl = "https://services.gradle.org/distributions/gradle-$GradleVersion-bin.zip"
$zipFile = Join-Path $InstallPath "gradle-$GradleVersion-bin.zip"

Write-Host "Downloading Gradle from: $downloadUrl" -ForegroundColor Yellow

# Try different download methods
$downloadSuccess = $false

# Method 1: Try PowerShell Invoke-WebRequest with extended timeout
try {
    Write-Host "Trying PowerShell download..." -ForegroundColor Gray
    $ProgressPreference = 'SilentlyContinue'  # Disable progress bar for better performance
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile -TimeoutSec 300 -ErrorAction Stop
    $downloadSuccess = $true
    Write-Host "✅ Downloaded via PowerShell" -ForegroundColor Green
} catch {
    Write-Host "❌ PowerShell download failed: $_" -ForegroundColor Red
}

# Method 2: Try curl if PowerShell failed
if (-not $downloadSuccess -and (Get-Command curl -ErrorAction SilentlyContinue)) {
    try {
        Write-Host "Trying curl download..." -ForegroundColor Gray
        & curl -L --connect-timeout 30 --max-time 600 -o $zipFile $downloadUrl
        if ($LASTEXITCODE -eq 0 -and (Test-Path $zipFile)) {
            $downloadSuccess = $true
            Write-Host "✅ Downloaded via curl" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ curl download failed: $_" -ForegroundColor Red
    }
}

# Method 3: Try wget if available
if (-not $downloadSuccess -and (Get-Command wget -ErrorAction SilentlyContinue)) {
    try {
        Write-Host "Trying wget download..." -ForegroundColor Gray
        & wget --timeout=30 --tries=3 -O $zipFile $downloadUrl
        if ($LASTEXITCODE -eq 0 -and (Test-Path $zipFile)) {
            $downloadSuccess = $true
            Write-Host "✅ Downloaded via wget" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ wget download failed: $_" -ForegroundColor Red
    }
}

if (-not $downloadSuccess) {
    Write-Error "❌ Failed to download Gradle. Network connectivity issues detected."
    Write-Host "`n💡 Alternative solutions:" -ForegroundColor Cyan
    Write-Host "   1. Download manually from: $downloadUrl" -ForegroundColor White
    Write-Host "   2. Save as: $zipFile" -ForegroundColor White
    Write-Host "   3. Run this script again" -ForegroundColor White
    Write-Host "`n   Or try using a VPN/different network connection" -ForegroundColor Yellow
    exit 1
}

# Extract the zip file
Write-Host "Extracting Gradle..." -ForegroundColor Yellow

try {
    # Remove existing directory if it exists
    if (Test-Path $gradleDir) {
        Remove-Item $gradleDir -Recurse -Force
    }
    
    # Extract using Expand-Archive
    Expand-Archive -Path $zipFile -DestinationPath $InstallPath -Force
    
    # Verify extraction
    if (Test-Path $gradleDir) {
        Write-Host "✅ Gradle extracted successfully" -ForegroundColor Green
        
        # Clean up zip file
        Remove-Item $zipFile -Force
        Write-Host "✅ Cleaned up download file" -ForegroundColor Green
        
        # Test the installation
        $gradleBin = Join-Path $gradleDir "bin\gradle.bat"
        if (Test-Path $gradleBin) {
            Write-Host "Testing Gradle installation..." -ForegroundColor Yellow
            try {
                $version = & $gradleBin --version 2>$null | Select-String "Gradle"
                if ($version) {
                    Write-Host "✅ Gradle installation successful: $($version.Line)" -ForegroundColor Green
                    
                    # Update PATH for current session
                    $gradleBinDir = Join-Path $gradleDir "bin"
                    $env:PATH = "$gradleBinDir;$env:PATH"
                    Write-Host "✅ Added Gradle to PATH for current session" -ForegroundColor Green
                    
                    Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
                    Write-Host "Gradle installed to: $gradleDir" -ForegroundColor White
                    Write-Host "Gradle binary: $gradleBin" -ForegroundColor White
                    Write-Host "`n💡 Usage:" -ForegroundColor Cyan
                    Write-Host "   Direct: $gradleBin assembleDebug" -ForegroundColor White
                    Write-Host "   With PATH: gradle assembleDebug" -ForegroundColor White
                    Write-Host "`n💡 To make permanent, add to system PATH:" -ForegroundColor Cyan
                    Write-Host "   $gradleBinDir" -ForegroundColor White
                } else {
                    Write-Error "❌ Gradle installation appears corrupted"
                }
            } catch {
                Write-Error "❌ Gradle installation test failed: $_"
            }
        } else {
            Write-Error "❌ Gradle binary not found after extraction"
        }
    } else {
        Write-Error "❌ Gradle directory not found after extraction"
    }
} catch {
    Write-Error "❌ Failed to extract Gradle: $_"
    
    # Clean up on failure
    if (Test-Path $zipFile) {
        Remove-Item $zipFile -Force
    }
}
