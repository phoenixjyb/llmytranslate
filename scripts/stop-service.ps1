# ================================================================================================
# LLM Translation Service - Stop Script
# Safely stops the translation service and ngrok tunnel
# ================================================================================================

param(
    [switch]$Force,
    [switch]$NgrokOnly,
    [switch]$ServiceOnly,
    [switch]$Verbose
)

Write-Host "🛑 LLM Translation Service - Stop Script" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Red

function Write-VerboseOutput {
    param([string]$Message)
    if ($Verbose) {
        Write-Host "  ℹ️  $Message" -ForegroundColor Gray
    }
}

function Stop-NgrokService {
    Write-Host "`n🚇 Stopping ngrok tunnel..." -ForegroundColor Yellow
    
    # Method 1: Try graceful shutdown via API
    try {
        Write-VerboseOutput "Attempting graceful shutdown via ngrok API..."
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-VerboseOutput "Ngrok web interface accessible, attempting API shutdown..."
            # Ngrok doesn't have a direct shutdown API, so we'll proceed to process termination
        }
    } catch {
        Write-VerboseOutput "Ngrok API not accessible, proceeding to process termination..."
    }
    
    # Method 2: Stop ngrok processes
    $ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
    if ($ngrokProcesses) {
        Write-VerboseOutput "Found $($ngrokProcesses.Count) ngrok process(es)"
        foreach ($process in $ngrokProcesses) {
            try {
                if ($Force) {
                    Stop-Process -Id $process.Id -Force
                    Write-Host "  ✅ Force stopped ngrok process (PID: $($process.Id))" -ForegroundColor Green
                } else {
                    $process.CloseMainWindow()
                    Start-Sleep -Seconds 2
                    if (!$process.HasExited) {
                        Stop-Process -Id $process.Id -Force
                    }
                    Write-Host "  ✅ Stopped ngrok process (PID: $($process.Id))" -ForegroundColor Green
                }
            } catch {
                Write-Host "  ⚠️  Could not stop ngrok process (PID: $($process.Id)): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  ℹ️  No ngrok processes found" -ForegroundColor Gray
    }
    
    # Verify ngrok is stopped
    Start-Sleep -Seconds 1
    $remainingNgrok = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
    if ($remainingNgrok) {
        Write-Host "  ⚠️  Some ngrok processes may still be running" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ All ngrok processes stopped" -ForegroundColor Green
    }
}

function Stop-TranslationService {
    Write-Host "`n🔴 Stopping translation service..." -ForegroundColor Yellow
    
    # Method 1: Check port 8000 usage
    Write-VerboseOutput "Checking port 8000 usage..."
    $portInfo = netstat -ano | Select-String ":8000.*LISTENING"
    
    if ($portInfo) {
        $portInfo | ForEach-Object {
            $line = $_.Line.Trim()
            $parts = $line -split '\s+'
            $processId = $parts[-1]
            
            Write-VerboseOutput "Found process using port 8000: PID $processId"
            
            try {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-VerboseOutput "Process details: $($process.ProcessName) (PID: $processId)"
                    
                    if ($Force) {
                        Stop-Process -Id $processId -Force
                        Write-Host "  ✅ Force stopped process on port 8000 (PID: $processId)" -ForegroundColor Green
                    } else {
                        # Try graceful shutdown first
                        try {
                            $process.CloseMainWindow()
                            Start-Sleep -Seconds 3
                            if (!$process.HasExited) {
                                Stop-Process -Id $processId -Force
                            }
                            Write-Host "  ✅ Stopped process on port 8000 (PID: $processId)" -ForegroundColor Green
                        } catch {
                            Stop-Process -Id $processId -Force
                            Write-Host "  ✅ Force stopped process on port 8000 (PID: $processId)" -ForegroundColor Green
                        }
                    }
                }
            } catch {
                Write-Host "  ⚠️  Could not stop process (PID: $processId): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    # Method 2: Stop python processes that might be running the service
    Write-VerboseOutput "Checking for python translation service processes..."
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    
    foreach ($process in $pythonProcesses) {
        try {
            # Check if this is likely our translation service
            $commandLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
            if ($commandLine -and ($commandLine -like "*uvicorn*" -or $commandLine -like "*main:app*" -or $commandLine -like "*translation*" -or $commandLine -like "*run.py*")) {
                Write-VerboseOutput "Found translation service python process: PID $($process.Id)"
                
                if ($Force) {
                    Stop-Process -Id $process.Id -Force
                    Write-Host "  ✅ Force stopped python translation service (PID: $($process.Id))" -ForegroundColor Green
                } else {
                    try {
                        $process.CloseMainWindow()
                        Start-Sleep -Seconds 3
                        if (!$process.HasExited) {
                            Stop-Process -Id $process.Id -Force
                        }
                        Write-Host "  ✅ Stopped python translation service (PID: $($process.Id))" -ForegroundColor Green
                    } catch {
                        Stop-Process -Id $process.Id -Force
                        Write-Host "  ✅ Force stopped python translation service (PID: $($process.Id))" -ForegroundColor Green
                    }
                }
            }
        } catch {
            Write-VerboseOutput "Could not check python process (PID: $($process.Id)): $($_.Exception.Message)"
        }
    }
    
    # Method 3: Verify service is stopped
    Write-VerboseOutput "Verifying translation service is stopped..."
    Start-Sleep -Seconds 2
    
    try {
        $testResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($testResponse) {
            Write-Host "  ⚠️  Translation service may still be running (responded to health check)" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ Translation service stopped (no response to health check)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✅ Translation service stopped (connection refused)" -ForegroundColor Green
    }
}

function Show-ServiceStatus {
    Write-Host "`n📊 Service Status Check:" -ForegroundColor Cyan
    
    # Check ngrok
    $ngrokRunning = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
    if ($ngrokRunning) {
        Write-Host "  🚇 Ngrok: ⚠️  Still running ($($ngrokRunning.Count) process(es))" -ForegroundColor Yellow
    } else {
        Write-Host "  🚇 Ngrok: ✅ Stopped" -ForegroundColor Green
    }
    
    # Check translation service
    $portUsed = netstat -ano | Select-String ":8000.*LISTENING"
    if ($portUsed) {
        Write-Host "  🔴 Translation Service: ⚠️  Port 8000 still in use" -ForegroundColor Yellow
    } else {
        Write-Host "  🔴 Translation Service: ✅ Stopped" -ForegroundColor Green
    }
    
    # Test service availability
    try {
        $testResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($testResponse) {
            Write-Host "  🏥 Health Check: ⚠️  Service still responding" -ForegroundColor Yellow
        } else {
            Write-Host "  🏥 Health Check: ✅ No response (service stopped)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  🏥 Health Check: ✅ Connection refused (service stopped)" -ForegroundColor Green
    }
}

# Main execution
try {
    if ($NgrokOnly) {
        Stop-NgrokService
    } elseif ($ServiceOnly) {
        Stop-TranslationService
    } else {
        # Stop both services
        Stop-NgrokService
        Stop-TranslationService
    }
    
    Show-ServiceStatus
    
    Write-Host "`n🎉 Stop operation completed!" -ForegroundColor Green
    if ($Force) {
        Write-Host "   Used force termination mode" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "`n❌ Error during stop operation: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Try running with -Force parameter for force termination" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n💡 Usage examples:" -ForegroundColor Cyan
Write-Host "   .\scripts\stop-service.ps1                 # Stop both services"
Write-Host "   .\scripts\stop-service.ps1 -NgrokOnly      # Stop only ngrok"
Write-Host "   .\scripts\stop-service.ps1 -ServiceOnly    # Stop only translation service"
Write-Host "   .\scripts\stop-service.ps1 -Force          # Force stop all"
Write-Host "   .\scripts\stop-service.ps1 -Verbose        # Detailed output"
