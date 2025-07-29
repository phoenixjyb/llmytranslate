# TTS Installation Script for LLM Translation Service
# This script installs TTS dependencies with GPU support

param(
    [switch]$CPUOnly,
    [switch]$SkipTorch,
    [switch]$EdgeTTSOnly
)

Write-Host "🎤 Installing TTS Support for LLM Translation Service" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# Activate virtual environment
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "⚠️  Virtual environment not found. Please run setup.ps1 first." -ForegroundColor Red
    exit 1
}

if ($EdgeTTSOnly) {
    Write-Host "🔄 Installing Edge TTS (lightweight option)..." -ForegroundColor Yellow
    pip install edge-tts soundfile numpy
    
    Write-Host "✅ Edge TTS installed successfully!" -ForegroundColor Green
    Write-Host "💡 Edge TTS provides free Microsoft voices without GPU requirements." -ForegroundColor Blue
    exit 0
}

# Install PyTorch first (unless skipped)
if (-not $SkipTorch) {
    if ($CPUOnly) {
        Write-Host "🔄 Installing PyTorch (CPU-only)..." -ForegroundColor Yellow
        pip install torch torchvision torchaudio
    } else {
        Write-Host "🔄 Installing PyTorch with CUDA support..." -ForegroundColor Yellow
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    }
}

# Install Coqui TTS
Write-Host "🔄 Installing Coqui TTS..." -ForegroundColor Yellow
pip install -r requirements-tts.txt

# Test installation
Write-Host "🔄 Testing TTS installation..." -ForegroundColor Yellow
python test_tts_integration.py

Write-Host "✅ TTS installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart your translation service: .\start-service.ps1" -ForegroundColor White
Write-Host "2. Test TTS endpoints at: http://localhost:8000/api/tts/demo" -ForegroundColor White
Write-Host "3. Try translate-and-speak: POST /api/tts/translate-and-speak" -ForegroundColor White
Write-Host ""
Write-Host "📖 Available TTS endpoints:" -ForegroundColor Cyan
Write-Host "  POST /api/tts/synthesize - Convert text to speech" -ForegroundColor White
Write-Host "  POST /api/tts/translate-and-speak - Translate and speak in one request" -ForegroundColor White
Write-Host "  GET  /api/tts/languages - List available TTS languages" -ForegroundColor White
Write-Host "  GET  /api/tts/health - Check TTS service status" -ForegroundColor White
