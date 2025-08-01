# Test TTS Dual Environment Setup
# Verifies that both environments work correctly

param(
    [switch]$TestMain,
    [switch]$TestTTS,
    [switch]$TestIntegration,
    [switch]$All
)

# Color output functions
function Write-Success($message) { Write-Host "✅ $message" -ForegroundColor Green }
function Write-Warning($message) { Write-Host "⚠️  $message" -ForegroundColor Yellow }
function Write-Info($message) { Write-Host "ℹ️  $message" -ForegroundColor Blue }
function Write-Error($message) { Write-Host "❌ $message" -ForegroundColor Red }

Write-Host "🧪 TTS Dual Environment Testing" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Test main environment (Python 3.13)
if ($TestMain -or $All) {
    Write-Info "🔄 Testing main environment (Python 3.13)..."
    
    $mainPython = ".\.venv\Scripts\python.exe"
    
    if (-not (Test-Path $mainPython)) {
        Write-Error "Main environment not found at $mainPython"
        exit 1
    }
    
    try {
        # Test Python version
        $version = & $mainPython --version
        Write-Success "Main environment: $version"
        
        # Test FastAPI import
        $importTest = & $mainPython -c "import fastapi; print('FastAPI OK')" 2>&1
        if ($importTest -like "*FastAPI OK*") {
            Write-Success "FastAPI import successful"
        } else {
            Write-Error "FastAPI import failed: $importTest"
        }
        
        # Test TTS service import (should work with fallback)
        $ttsImportTest = & $mainPython -c "from src.services.tts_service import tts_service; print('TTS Service OK')" 2>&1
        if ($ttsImportTest -like "*TTS Service OK*") {
            Write-Success "TTS service import successful"
        } else {
            Write-Error "TTS service import failed: $ttsImportTest"
        }
        
    } catch {
        Write-Error "Main environment test failed: $($_.Exception.Message)"
    }
}

# Test TTS environment (Python 3.12)
if ($TestTTS -or $All) {
    Write-Info "🔄 Testing TTS environment (Python 3.12)..."
    
    $ttsPython = ".\.venv-tts\Scripts\python.exe"
    
    if (-not (Test-Path $ttsPython)) {
        Write-Error "TTS environment not found at $ttsPython"
        Write-Warning "Run setup-tts-env.ps1 -All to create TTS environment"
        exit 1
    }
    
    try {
        # Test Python version
        $version = & $ttsPython --version
        Write-Success "TTS environment: $version"
        
        # Test TTS import
        $ttsTest = & $ttsPython -c "from TTS.api import TTS; print('Coqui TTS OK')" 2>&1
        if ($ttsTest -like "*Coqui TTS OK*") {
            Write-Success "Coqui TTS import successful"
        } else {
            Write-Error "Coqui TTS import failed: $ttsTest"
        }
        
        # Test subprocess script
        if (Test-Path "tts_subprocess.py") {
            $subprocessTest = & $ttsPython -c "import tts_subprocess; print('Subprocess script OK')" 2>&1
            if ($subprocessTest -like "*Subprocess script OK*") {
                Write-Success "TTS subprocess script accessible"
            } else {
                Write-Warning "TTS subprocess script test: $subprocessTest"
            }
        } else {
            Write-Warning "TTS subprocess script not found"
        }
        
    } catch {
        Write-Error "TTS environment test failed: $($_.Exception.Message)"
    }
}

# Test integration between environments
if ($TestIntegration -or $All) {
    Write-Info "🔄 Testing dual environment integration..."
    
    # Create test request file
    $testRequest = @{
        action = "list_models"
    } | ConvertTo-Json
    
    $testRequestFile = "test_request.json"
    $testRequest | Out-File -FilePath $testRequestFile -Encoding UTF8
    
    try {
        # Test TTS subprocess communication
        $ttsPython = ".\.venv-tts\Scripts\python.exe"
        
        if (Test-Path $ttsPython) {
            Write-Info "Testing TTS subprocess communication..."
            
            $result = & $ttsPython "tts_subprocess.py" $testRequestFile "dummy_output.wav" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "TTS subprocess communication successful"
                Write-Info "Models response:"
                $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            } else {
                Write-Error "TTS subprocess communication failed"
                Write-Error "Error output: $result"
            }
        } else {
            Write-Warning "TTS environment not available for integration test"
        }
        
    } catch {
        Write-Error "Integration test failed: $($_.Exception.Message)"
    } finally {
        # Cleanup
        Remove-Item $testRequestFile -ErrorAction SilentlyContinue
        Remove-Item "dummy_output.wav" -ErrorAction SilentlyContinue
    }
}

# Test actual TTS synthesis if both environments are working
if ($All) {
    Write-Info "🔄 Testing actual TTS synthesis..."
    
    $mainPython = ".\.venv\Scripts\python.exe"
    $ttsPython = ".\.venv-tts\Scripts\python.exe"
    
    if ((Test-Path $mainPython) -and (Test-Path $ttsPython)) {
        try {
            # Create synthesis test request
            $synthRequest = @{
                action = "synthesize"
                text = "Hello, this is a test of the dual environment TTS system."
                language = "en"
                voice = "default"
                speed = 1.0
            } | ConvertTo-Json
            
            $synthRequestFile = "test_synthesis_request.json"
            $synthOutputFile = "test_synthesis_output.wav"
            
            $synthRequest | Out-File -FilePath $synthRequestFile -Encoding UTF8
            
            Write-Info "Synthesizing test audio..."
            $synthResult = & $ttsPython "tts_subprocess.py" $synthRequestFile $synthOutputFile 2>&1
            
            if ($LASTEXITCODE -eq 0 -and (Test-Path $synthOutputFile)) {
                $audioSize = (Get-Item $synthOutputFile).Length
                Write-Success "TTS synthesis successful! Audio file: $audioSize bytes"
                
                # Test playback (optional)
                Write-Info "Audio file created at: $synthOutputFile"
                Write-Host "💡 You can play the audio file to verify quality" -ForegroundColor Yellow
            } else {
                Write-Error "TTS synthesis failed"
                Write-Error "Error: $synthResult"
            }
            
        } catch {
            Write-Error "Synthesis test failed: $($_.Exception.Message)"
        } finally {
            # Cleanup
            Remove-Item $synthRequestFile -ErrorAction SilentlyContinue
            Remove-Item $synthOutputFile -ErrorAction SilentlyContinue
        }
    } else {
        Write-Warning "Both environments needed for synthesis test"
    }
}

Write-Host ""
Write-Host "📊 Test Summary:" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan
Write-Host "Main Service:    Python 3.13 (.venv)" -ForegroundColor White
Write-Host "TTS Service:     Python 3.12 (.venv-tts)" -ForegroundColor White
Write-Host "Communication:   Subprocess + temp files" -ForegroundColor White
Write-Host ""

Write-Host "💡 Usage:" -ForegroundColor Cyan
Write-Host "  test-tts-dual-env.ps1 -All              # Run all tests" -ForegroundColor White
Write-Host "  test-tts-dual-env.ps1 -TestMain         # Test main environment only" -ForegroundColor White
Write-Host "  test-tts-dual-env.ps1 -TestTTS          # Test TTS environment only" -ForegroundColor White
Write-Host "  test-tts-dual-env.ps1 -TestIntegration  # Test communication only" -ForegroundColor White
