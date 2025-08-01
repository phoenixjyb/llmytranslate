# ================================================================================================
# Improved LLM Translation Service Starter
# Fixed health check and startup process
# ================================================================================================

param(
    [switch]$Production,
    [switch]$Debug,
    [switch]$Force
)

Write-Host "🚀 Starting LLM Translation Service..." -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Set working directory to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check for Python executable
$PythonExec = $null
$PythonCandidates = @(
    ".\.venv\Scripts\python.exe",
    "python.exe",
    "python3.exe",
    "py.exe"
)

foreach ($candidate in $PythonCandidates) {
    try {
        if (Test-Path $candidate -ErrorAction SilentlyContinue) {
            $PythonExec = $candidate
            break
        }
        
        # Test if command exists in PATH
        $null = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($?) {
            $PythonExec = $candidate
            break
        }
    } catch {
        continue
    }
}

if (-not $PythonExec) {
    Write-Host "❌ No Python executable found!" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and virtual environment is activated." -ForegroundColor Yellow
    exit 1
}

Write-Host "🐍 Using Python: $PythonExec" -ForegroundColor Green

# Check required files
$RequiredFiles = @("run.py", "src\main.py")
foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Required file missing: $file" -ForegroundColor Red
        exit 1
    }
}

# Set environment
if ($Production) {
    $env:ENVIRONMENT = "production"
    Write-Host "🏭 Running in PRODUCTION mode" -ForegroundColor Yellow
} else {
    $env:ENVIRONMENT = "development"
    Write-Host "🛠️  Running in DEVELOPMENT mode" -ForegroundColor Green
}

if ($Debug) {
    $env:DEBUG = "true"
    Write-Host "🐛 Debug mode enabled" -ForegroundColor Yellow
}

# Simple health check function
function Test-SimpleHealth {
    param([int]$Port = 8000, [int]$MaxAttempts = 15)
    
    Write-Host "`n🏥 Checking service health..." -ForegroundColor Cyan
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            # Try to connect to the port
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connection = $tcpClient.BeginConnect("127.0.0.1", $Port, $null, $null)
            $wait = $connection.AsyncWaitHandle.WaitOne(1000, $false)
            
            if ($wait) {
                $tcpClient.EndConnect($connection)
                $tcpClient.Close()
                
                # Port is open, try HTTP request
                try {
                    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -TimeoutSec 3 -ErrorAction SilentlyContinue
                    if ($response.StatusCode -eq 200) {
                        Write-Host "✅ Service is healthy and responding!" -ForegroundColor Green
                        return $true
                    }
                } catch {
                    # Port is open but HTTP not ready yet
                }
            } else {
                $tcpClient.Close()
            }
        } catch {
            # Connection failed
        }
        
        Write-Host "  ⏳ Waiting for service... ($i/$MaxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
    
    Write-Host "⚠️  Health check timeout - service may still be starting" -ForegroundColor Yellow
    return $false
}

# Show service information
function Show-ServiceInfo {
    param([int]$Port = 8000)
    
    Write-Host "`n🌐 Service Access Information:" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "📱 Main Interface: http://localhost:$Port" -ForegroundColor White
    Write-Host "💬 Chat Interface: http://localhost:$Port/chat" -ForegroundColor White
    Write-Host "🔄 Translate Interface: http://localhost:$Port/translate-ui" -ForegroundColor White
    Write-Host "📚 API Documentation: http://localhost:$Port/docs" -ForegroundColor White
    Write-Host "🏥 Health Check: http://localhost:$Port/api/health" -ForegroundColor White
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
    Write-Host "=================================" -ForegroundColor Cyan
}

# Check if service is already running
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "⚠️  Service appears to already be running!" -ForegroundColor Yellow
        Write-Host "If you want to restart, please stop the existing service first." -ForegroundColor Yellow
        Show-ServiceInfo -Port 8000
        exit 0
    }
} catch {
    # Service not running, continue
}

try {
    Write-Host "`n🚀 Launching service..." -ForegroundColor Cyan
    
    # Start the service directly (not in background)
    $process = Start-Process -FilePath $PythonExec -ArgumentList "run.py" -NoNewWindow -PassThru
    
    # Wait a moment for startup
    Start-Sleep -Seconds 3
    
    # Check if process is still running
    if ($process.HasExited) {
        Write-Host "❌ Service process exited unexpectedly" -ForegroundColor Red
        Write-Host "Exit code: $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }
    
    # Test connectivity
    $healthy = Test-SimpleHealth -Port 8000
    
    if ($healthy) {
        Show-ServiceInfo -Port 8000
        Write-Host "`n🎯 Service started successfully!" -ForegroundColor Green
    } else {
        Show-ServiceInfo -Port 8000
        Write-Host "`n⚠️  Service may still be initializing..." -ForegroundColor Yellow
        Write-Host "Check the service logs above for any errors." -ForegroundColor Yellow
    }
    
    # Wait for the process to complete
    $process.WaitForExit()
    
} catch {
    Write-Host "`n❌ Error starting service:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    Write-Host "`n👋 Service stopped" -ForegroundColor Cyan
}
