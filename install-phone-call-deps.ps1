#!/usr/bin/env powershell
# Phone Call Mode - Phase 2 Dependencies Installation Script

Write-Host "📞 Installing Phone Call Mode Phase 2 Dependencies..." -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "requirements-phone-call.txt")) {
    Write-Host "❌ Please run this script from the llmytranslate root directory" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found. Please create .venv first." -ForegroundColor Red
    exit 1
}

Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

Write-Host "📦 Installing Phase 2 dependencies..." -ForegroundColor Yellow
pip install -r requirements-phone-call.txt

Write-Host "🧪 Testing installations..." -ForegroundColor Yellow

# Test WebRTC VAD
Write-Host "  Testing WebRTC VAD..." -NoNewline
$vad_test = python -c "
try:
    import webrtcvad
    print('✅ WebRTC VAD available')
except ImportError:
    print('⚠️ WebRTC VAD not available (optional)')
except Exception as e:
    print(f'❌ WebRTC VAD error: {e}')
" 2>$null

if ($vad_test) {
    Write-Host $vad_test
} else {
    Write-Host "⚠️ WebRTC VAD test failed (optional dependency)" -ForegroundColor Yellow
}

# Test scipy
Write-Host "  Testing scipy..." -NoNewline
$scipy_test = python -c "
try:
    import scipy.signal
    print('✅ Scipy available')
except ImportError:
    print('⚠️ Scipy not available (optional)')
except Exception as e:
    print(f'❌ Scipy error: {e}')
" 2>$null

if ($scipy_test) {
    Write-Host $scipy_test
} else {
    Write-Host "⚠️ Scipy test failed (optional dependency)" -ForegroundColor Yellow
}

# Test numpy
Write-Host "  Testing numpy..." -NoNewline
$numpy_test = python -c "
try:
    import numpy
    print('✅ Numpy available')
except ImportError:
    print('❌ Numpy not available (required)')
except Exception as e:
    print(f'❌ Numpy error: {e}')
" 2>$null

if ($numpy_test) {
    Write-Host $numpy_test
} else {
    Write-Host "❌ Numpy test failed" -ForegroundColor Red
}

# Test phone call import
Write-Host "  Testing phone call routes..." -NoNewline
$phone_test = python -c "
try:
    from src.api.routes import phone_call
    print('✅ Phone call routes importable')
except Exception as e:
    print(f'❌ Phone call import error: {e}')
" 2>$null

if ($phone_test) {
    Write-Host $phone_test
} else {
    Write-Host "❌ Phone call routes test failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Phase 2 dependency installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📞 You can now:" -ForegroundColor Cyan
Write-Host "   1. Start the server: .venv\Scripts\python.exe run.py" -ForegroundColor White
Write-Host "   2. Access phone calls: http://localhost:8000/phone-call" -ForegroundColor White
Write-Host "   3. Test the health check: http://localhost:8000/api/phone/health" -ForegroundColor White
Write-Host ""
Write-Host "🔊 Note: For best performance, ensure your microphone is working" -ForegroundColor Yellow
Write-Host "    and grant browser permissions for microphone access." -ForegroundColor Yellow
