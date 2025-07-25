# ================================================================================================
# LLM Translation Service - Service Management Script
# This script helps start, stop, and manage the translation service
# ================================================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs")]
    [string]$Action,
    
    [switch]$Production,
    [switch]$Docker,
    [string]$LogTail = "50"
)

Write-Host "🔧 LLM Translation Service - Service Management" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

$serviceName = "LLM Translation Service"
$servicePort = 8000
$metricsPort = 8001

function Test-ServiceRunning {
    param([int]$Port)
    
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Get-ServiceStatus {
    $isRunning = Test-ServiceRunning -Port $servicePort
    $metricsRunning = Test-ServiceRunning -Port $metricsPort
    
    Write-Host "`n📊 Service Status:" -ForegroundColor Green
    
    if ($isRunning) {
        Write-Host "✅ Translation Service: Running on port $servicePort" -ForegroundColor Green
        
        # Try to get service info
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$servicePort" -UseBasicParsing -TimeoutSec 5
            $serviceInfo = $response.Content | ConvertFrom-Json
            Write-Host "   Name: $($serviceInfo.name)" -ForegroundColor White
            Write-Host "   Version: $($serviceInfo.version)" -ForegroundColor White
        } catch {
            Write-Host "   (Could not retrieve service details)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Translation Service: Not running" -ForegroundColor Red
    }
    
    if ($metricsRunning) {
        Write-Host "✅ Metrics Service: Running on port $metricsPort" -ForegroundColor Green
    } else {
        Write-Host "❌ Metrics Service: Not running" -ForegroundColor Red
    }
    
    # Check Ollama
    $ollamaProcess = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue
    if ($ollamaProcess) {
        Write-Host "✅ Ollama: Running (PID: $($ollamaProcess.Id -join ', '))" -ForegroundColor Green
    } else {
        Write-Host "❌ Ollama: Not running" -ForegroundColor Red
    }
    
    # Check Redis
    $redisRunning = Test-ServiceRunning -Port 6379
    if ($redisRunning) {
        Write-Host "✅ Redis: Running on port 6379" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis: Not running (using in-memory cache)" -ForegroundColor Yellow
    }
}

function Start-TranslationService {
    Write-Host "`n🚀 Starting Translation Service..." -ForegroundColor Green
    
    # Check if already running
    if (Test-ServiceRunning -Port $servicePort) {
        Write-Host "⚠️  Service is already running on port $servicePort" -ForegroundColor Yellow
        return
    }
    
    # Check prerequisites
    $ollamaProcess = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue
    if (-not $ollamaProcess) {
        Write-Host "❌ Ollama is not running. Starting Ollama..." -ForegroundColor Red
        try {
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Write-Host "✅ Ollama started" -ForegroundColor Green
            Start-Sleep -Seconds 3
        } catch {
            Write-Host "❌ Failed to start Ollama. Please start it manually: ollama serve" -ForegroundColor Red
            return
        }
    }
    
    if ($Docker) {
        Write-Host "🐳 Starting with Docker Compose..." -ForegroundColor Cyan
        try {
            docker-compose up -d
            Write-Host "✅ Docker containers started" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to start Docker containers" -ForegroundColor Red
            return
        }
    } else {
        Write-Host "🐍 Starting Python service..." -ForegroundColor Cyan
        
        # Clear conflicting environment variables
        if ($env:ollama) {
            Write-Host "⚠️  Removing conflicting 'ollama' environment variable" -ForegroundColor Yellow
            Remove-Item Env:\ollama -ErrorAction SilentlyContinue
        }
        
        # Set environment
        $env:PYTHONPATH = (Get-Location).Path
        
        if ($Production) {
            $env:ENVIRONMENT = "production"
            Write-Host "🏭 Running in PRODUCTION mode" -ForegroundColor Yellow
        } else {
            $env:ENVIRONMENT = "development"
            Write-Host "🛠️  Running in DEVELOPMENT mode" -ForegroundColor Yellow
        }
        
        try {
            # Start the service in background using virtual environment Python
            $job = Start-Job -ScriptBlock {
                param($workDir)
                Set-Location $workDir
                & ".\.venv\Scripts\python.exe" "run.py"
            } -ArgumentList (Get-Location).Path
            
            Write-Host "✅ Service started (Job ID: $($job.Id))" -ForegroundColor Green
            
            # Wait a moment and check if it started successfully
            Start-Sleep -Seconds 3
            
            if (Test-ServiceRunning -Port $servicePort) {
                Write-Host "✅ Service is now accessible on port $servicePort" -ForegroundColor Green
            } else {
                Write-Host "❌ Service failed to start properly" -ForegroundColor Red
                Write-Host "Check job output: Receive-Job -Id $($job.Id)" -ForegroundColor Yellow
            }
            
        } catch {
            Write-Host "❌ Failed to start service: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

function Stop-TranslationService {
    Write-Host "`n🛑 Stopping Translation Service..." -ForegroundColor Green
    
    if ($Docker) {
        Write-Host "🐳 Stopping Docker containers..." -ForegroundColor Cyan
        try {
            docker-compose down
            Write-Host "✅ Docker containers stopped" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to stop Docker containers" -ForegroundColor Red
        }
    } else {
        # Stop Python processes running the service
        $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
            $_.ProcessName -like "*python*"
        }
        
        if ($pythonProcesses) {
            Write-Host "🐍 Stopping Python service processes..." -ForegroundColor Cyan
            foreach ($proc in $pythonProcesses) {
                try {
                    $proc | Stop-Process -Force
                    Write-Host "✅ Stopped process PID: $($proc.Id)" -ForegroundColor Green
                } catch {
                    Write-Host "⚠️  Could not stop process PID: $($proc.Id)" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "ℹ️  No Python service processes found" -ForegroundColor Blue
        }
        
        # Stop any background jobs
        $jobs = Get-Job | Where-Object { $_.State -eq "Running" }
        if ($jobs) {
            Write-Host "🔄 Stopping background jobs..." -ForegroundColor Cyan
            $jobs | Stop-Job
            $jobs | Remove-Job
            Write-Host "✅ Background jobs stopped" -ForegroundColor Green
        }
    }
    
    # Verify service is stopped
    Start-Sleep -Seconds 2
    if (-not (Test-ServiceRunning -Port $servicePort)) {
        Write-Host "✅ Service stopped successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Service may still be running on port $servicePort" -ForegroundColor Yellow
    }
}

function Show-ServiceLogs {
    Write-Host "`n📋 Service Logs (last $LogTail lines):" -ForegroundColor Green
    
    $logFile = "logs\translation_service.log"
    
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail $LogTail
    } else {
        Write-Host "⚠️  Log file not found at $logFile" -ForegroundColor Yellow
        
        # Try to get job output if running as job
        $jobs = Get-Job | Where-Object { $_.State -eq "Running" }
        if ($jobs) {
            Write-Host "📄 Job Output:" -ForegroundColor Cyan
            foreach ($job in $jobs) {
                Write-Host "--- Job ID: $($job.Id) ---" -ForegroundColor Yellow
                Receive-Job -Id $job.Id
            }
        }
    }
}

# Main script execution
switch ($Action.ToLower()) {
    "start" {
        Start-TranslationService
        Get-ServiceStatus
    }
    "stop" {
        Stop-TranslationService
    }
    "restart" {
        Stop-TranslationService
        Start-Sleep -Seconds 2
        Start-TranslationService
        Get-ServiceStatus
    }
    "status" {
        Get-ServiceStatus
    }
    "logs" {
        Show-ServiceLogs
    }
}

Write-Host "`n🔧 Service Management Complete!" -ForegroundColor Cyan
