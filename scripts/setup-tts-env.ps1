# TTS Environment Setup Script
# Creates a separate Python 3.12 virtual environment for TTS functionality
# while keeping the main service on Python 3.13

param(
    [switch]$InstallPython312,
    [switch]$CreateTTSEnv,
    [switch]$InstallTTS,
    [switch]$TestTTS,
    [switch]$All
)

# Color output functions
function Write-Success($message) { Write-Host "✅ $message" -ForegroundColor Green }
function Write-Warning($message) { Write-Host "⚠️  $message" -ForegroundColor Yellow }
function Write-Info($message) { Write-Host "ℹ️  $message" -ForegroundColor Blue }
function Write-Error($message) { Write-Host "❌ $message" -ForegroundColor Red }

Write-Host "🎤 TTS Environment Setup - Dual Python Version Support" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Check current Python versions
Write-Info "Checking available Python versions..."
try {
    $py313 = py -3.13 --version 2>$null
    Write-Success "Python 3.13 available: $py313"
} catch {
    Write-Warning "Python 3.13 not found"
}

try {
    $py312 = py -3.12 --version 2>$null
    Write-Success "Python 3.12 available: $py312"
    $Python312Available = $true
} catch {
    Write-Warning "Python 3.12 not found - required for Coqui TTS"
    $Python312Available = $false
}

# Step 1: Install Python 3.12 if needed
if ($InstallPython312 -or ($All -and -not $Python312Available)) {
    Write-Info "🔄 Installing Python 3.12..."
    
    Write-Host "📝 Installation options:" -ForegroundColor Yellow
    Write-Host "1. Automatic via winget (recommended)" -ForegroundColor White
    Write-Host "2. Manual download from python.org" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Choose installation method (1 or 2)"
    
    if ($choice -eq "1") {
        Write-Info "Installing Python 3.12 via winget..."
        try {
            winget install Python.Python.3.12
            Write-Success "Python 3.12 installed successfully!"
            $Python312Available = $true
        } catch {
            Write-Error "Failed to install Python 3.12 via winget"
            Write-Info "Please install manually from https://www.python.org/downloads/"
            exit 1
        }
    } else {
        Write-Info "Please download and install Python 3.12 from:"
        Write-Host "https://www.python.org/downloads/release/python-3120/" -ForegroundColor Cyan
        Write-Warning "Make sure to check 'Add Python to PATH' during installation"
        Write-Host ""
        Read-Host "Press Enter after installing Python 3.12"
        
        # Verify installation
        try {
            py -3.12 --version
            Write-Success "Python 3.12 installation verified!"
            $Python312Available = $true
        } catch {
            Write-Error "Python 3.12 still not found. Please check installation."
            exit 1
        }
    }
}

# Step 2: Create TTS virtual environment
if ($CreateTTSEnv -or $All) {
    if (-not $Python312Available) {
        Write-Error "Python 3.12 required for TTS environment. Use -InstallPython312 first."
        exit 1
    }
    
    Write-Info "🔄 Creating TTS virtual environment with Python 3.12..."
    
    $ttsEnvPath = ".\.venv-tts"
    
    if (Test-Path $ttsEnvPath) {
        Write-Warning "TTS environment already exists. Removing old one..."
        Remove-Item -Recurse -Force $ttsEnvPath
    }
    
    try {
        py -3.12 -m venv $ttsEnvPath
        Write-Success "TTS virtual environment created at $ttsEnvPath"
        
        # Upgrade pip in TTS environment
        & "$ttsEnvPath\Scripts\python.exe" -m pip install --upgrade pip
        Write-Success "Pip upgraded in TTS environment"
        
    } catch {
        Write-Error "Failed to create TTS virtual environment"
        exit 1
    }
}

# Step 3: Install TTS dependencies
if ($InstallTTS -or $All) {
    $ttsEnvPath = ".\.venv-tts"
    
    if (-not (Test-Path $ttsEnvPath)) {
        Write-Error "TTS environment not found. Use -CreateTTSEnv first."
        exit 1
    }
    
    Write-Info "🔄 Installing TTS dependencies in Python 3.12 environment..."
    
    $ttsActivate = "$ttsEnvPath\Scripts\python.exe"
    
    try {
        # Install core TTS library
        Write-Info "Installing Coqui TTS..."
        & $ttsActivate -m pip install coqui-tts
        
        # Install PyTorch with CUDA support
        Write-Info "Installing PyTorch with CUDA support..."
        & $ttsActivate -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        
        # Install audio processing libraries
        Write-Info "Installing audio processing libraries..."
        & $ttsActivate -m pip install librosa soundfile numpy
        
        # Install additional dependencies
        Write-Info "Installing additional dependencies..."
        & $ttsActivate -m pip install fastapi pydantic aiofiles
        
        Write-Success "All TTS dependencies installed successfully!"
        
    } catch {
        Write-Error "Failed to install TTS dependencies"
        Write-Info "Error details: $($_.Exception.Message)"
        exit 1
    }
}

# Step 4: Test TTS installation
if ($TestTTS -or $All) {
    $ttsEnvPath = ".\.venv-tts"
    
    if (-not (Test-Path $ttsEnvPath)) {
        Write-Error "TTS environment not found."
        exit 1
    }
    
    Write-Info "🔄 Testing TTS installation..."
    
    $ttsActivate = "$ttsEnvPath\Scripts\python.exe"
    
    # Create a simple test script
    $testScript = @"
import sys
print(f"Python version: {sys.version}")
print("Testing TTS imports...")

try:
    from TTS.api import TTS
    print("✅ Coqui TTS imported successfully")
    
    # Test basic TTS functionality
    print("🔄 Testing English TTS model...")
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
    print("✅ English TTS model loaded")
    
    print("🔄 Testing Chinese TTS model...")
    tts_zh = TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC")
    print("✅ Chinese TTS model loaded")
    
    print("🎉 TTS installation test completed successfully!")
    
except Exception as e:
    print(f"❌ TTS test failed: {e}")
    sys.exit(1)
"@
    
    $testScript | Out-File -FilePath "test_tts_install.py" -Encoding UTF8
    
    try {
        & $ttsActivate "test_tts_install.py"
        Write-Success "TTS installation test passed!"
    } catch {
        Write-Error "TTS installation test failed"
    } finally {
        Remove-Item "test_tts_install.py" -ErrorAction SilentlyContinue
    }
}

# Summary and next steps
Write-Host ""
Write-Host "📊 Environment Summary:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Main Service (Python 3.13): .\.venv" -ForegroundColor White
Write-Host "TTS Service (Python 3.12):  .\.venv-tts" -ForegroundColor White
Write-Host ""

if ($All -or $InstallTTS) {
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Update TTS service to use dual environment" -ForegroundColor White
    Write-Host "2. Test TTS functionality: .\test-tts-dual-env.ps1" -ForegroundColor White
    Write-Host "3. Start services: .\start-service.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 TTS will now support both English and Chinese with high quality!" -ForegroundColor Green
}

Write-Host "💡 Usage:" -ForegroundColor Cyan
Write-Host "  setup-tts-env.ps1 -All                 # Complete setup" -ForegroundColor White
Write-Host "  setup-tts-env.ps1 -InstallPython312    # Install Python 3.12 only" -ForegroundColor White
Write-Host "  setup-tts-env.ps1 -CreateTTSEnv        # Create TTS environment only" -ForegroundColor White
Write-Host "  setup-tts-env.ps1 -InstallTTS          # Install TTS packages only" -ForegroundColor White
Write-Host "  setup-tts-env.ps1 -TestTTS             # Test TTS installation" -ForegroundColor White
