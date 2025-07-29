# LLM Translation Service - Graceful Shutdown Script
# This script safely stops all translation services, ngrok, and tailscale

param(
    [switch]$Force,
    [switch]$KeepTailscale,
    [switch]$KeepNgrok,
    [switch]$Quiet
)

# Color output functions
function Write-Success($message) { if (-not $Quiet) { Write-Host "✅ $message" -ForegroundColor Green } }
function Write-Warning($message) { if (-not $Quiet) { Write-Host "⚠️  $message" -ForegroundColor Yellow } }
function Write-Info($message) { if (-not $Quiet) { Write-Host "ℹ️  $message" -ForegroundColor Blue } }
function Write-Error($message) { Write-Host "❌ $message" -ForegroundColor Red }

if (-not $Quiet) {
    Write-Host "🛑 LLM Translation Service - Graceful Shutdown" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
}

# Function to safely stop processes
function Stop-ProcessSafely {
    param(
        [string]$ProcessName,
        [string]$DisplayName,
        [switch]$Force
    )
    
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*$ProcessName*" }
    
    if ($processes) {
        Write-Info "Stopping $DisplayName services..."
        foreach ($proc in $processes) {
            try {
                if ($Force) {
                    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                } else {
                    # Try graceful shutdown first
                    $proc.CloseMainWindow()
                    Start-Sleep -Seconds 2
                    if (-not $proc.HasExited) {
                        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                    }
                }
                Write-Success "$DisplayName process (PID: $($proc.Id)) stopped"
            }
            catch {
                Write-Warning "Could not stop $DisplayName process (PID: $($proc.Id)): $($_.Exception.Message)"
            }
        }
    } else {
        Write-Info "$DisplayName - No running processes found"
    }
}

# Function to check and stop service by port
function Stop-ServiceByPort {
    param(
        [int]$Port,
        [string]$ServiceName
    )
    
    try {
        $connections = netstat -ano | findstr ":$Port"
        if ($connections) {
            $pids = $connections | ForEach-Object { 
                ($_ -split '\s+')[4] 
            } | Where-Object { $_ -match '^\d+$' } | Select-Object -Unique
            
            foreach ($processId in $pids) {
                if ($processId -and $processId -ne "0") {
                    try {
                        $process = Get-Process -Id $processId -ErrorAction Stop
                        Write-Info "Stopping $ServiceName on port $Port (PID: $processId)"
                        Stop-Process -Id $processId -Force -ErrorAction Stop
                        Write-Success "$ServiceName stopped (was using port $Port)"
                    }
                    catch {
                        Write-Warning "Could not stop process on port $Port (PID: ${processId}): $($_.Exception.Message)"
                    }
                }
            }
        } else {
            Write-Info "$ServiceName - Port $Port not in use"
        }
    }
    catch {
        Write-Warning "Error checking port $Port for ${ServiceName}: $($_.Exception.Message)"
    }
}

# 1. Stop Translation Services (FastAPI/Uvicorn)
Write-Info "🔄 Step 1: Stopping Translation Services..."

# Try graceful shutdown via API first
try {
    $null = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/shutdown" -Method POST -TimeoutSec 5 -ErrorAction Stop
    Write-Success "Translation service gracefully shut down via API"
    Start-Sleep -Seconds 2
}
catch {
    Write-Warning "Could not gracefully shutdown via API, using process termination"
}

# Stop by port and process name
Stop-ServiceByPort -Port 8000 -ServiceName "Translation Service"
Stop-ProcessSafely -ProcessName "python" -DisplayName "Python/FastAPI" -Force:$Force
Stop-ProcessSafely -ProcessName "uvicorn" -DisplayName "Uvicorn" -Force:$Force

# 2. Stop Ollama Services
Write-Info "🔄 Step 2: Stopping Ollama Services..."
Stop-ProcessSafely -ProcessName "ollama" -DisplayName "Ollama" -Force:$Force

# 3. Stop ngrok (unless KeepNgrok is specified)
if (-not $KeepNgrok) {
    Write-Info "🔄 Step 3: Stopping ngrok Services..."
    
    # Stop ngrok tunnels gracefully via API
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 3 -ErrorAction Stop
        foreach ($tunnel in $tunnels.tunnels) {
            try {
                Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels/$($tunnel.name)" -Method DELETE -TimeoutSec 3
                Write-Success "ngrok tunnel '$($tunnel.name)' stopped gracefully"
            }
            catch {
                Write-Warning "Could not stop tunnel '$($tunnel.name)' gracefully"
            }
        }
    }
    catch {
        Write-Warning "Could not connect to ngrok API, using process termination"
    }
    
    Stop-ProcessSafely -ProcessName "ngrok" -DisplayName "ngrok" -Force:$Force
    Stop-ServiceByPort -Port 4040 -ServiceName "ngrok Dashboard"
} else {
    Write-Info "🔄 Step 3: Keeping ngrok running (--KeepNgrok specified)"
}

# 4. Stop Tailscale (unless KeepTailscale is specified)
if (-not $KeepTailscale) {
    Write-Info "🔄 Step 4: Stopping Tailscale Services..."
    
    # Try to disconnect Tailscale gracefully first
    $tailscalePaths = @(
        "C:\Program Files\Tailscale\tailscale.exe",
        "C:\Program Files (x86)\Tailscale\tailscale.exe",
        "$env:LOCALAPPDATA\Tailscale\tailscale.exe"
    )
    
    $tailscaleFound = $false
    foreach ($path in $tailscalePaths) {
        if (Test-Path $path) {
            try {
                Write-Info "Attempting graceful Tailscale disconnect..."
                & $path logout *>$null
                Start-Sleep -Seconds 2
                Write-Success "Tailscale disconnected gracefully"
                $tailscaleFound = $true
                break
            }
            catch {
                Write-Warning "Could not disconnect Tailscale gracefully: $($_.Exception.Message)"
            }
        }
    }
    
    if (-not $tailscaleFound) {
        Write-Warning "Tailscale CLI not found, using process termination"
    }
    
    Stop-ProcessSafely -ProcessName "tailscale" -DisplayName "Tailscale" -Force:$Force
} else {
    Write-Info "🔄 Step 4: Keeping Tailscale running (--KeepTailscale specified)"
}

# 5. Final Verification
Write-Info "🔄 Step 5: Final Verification..."

$remainingProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*uvicorn*" -or 
    $_.ProcessName -like "*ollama*" -or 
    ($_.ProcessName -like "*ngrok*" -and -not $KeepNgrok) -or
    ($_.ProcessName -like "*tailscale*" -and -not $KeepTailscale)
}

if ($remainingProcesses) {
    Write-Warning "Some processes are still running:"
    $remainingProcesses | ForEach-Object {
        Write-Host "  - $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Yellow
    }
    
    if ($Force) {
        Write-Info "Force stopping remaining processes..."
        $remainingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Success "Remaining processes force stopped"
    } else {
        Write-Info "Use -Force parameter to force stop remaining processes"
    }
} else {
    Write-Success "All target services have been stopped"
}

# 6. Port Verification
Write-Info "🔄 Step 6: Port Status Check..."

$portsToCheck = @(
    @{Port = 8000; Name = "Translation Service" },
    @{Port = 11434; Name = "Ollama API" }
)

if (-not $KeepNgrok) {
    $portsToCheck += @{Port = 4040; Name = "ngrok Dashboard" }
}

foreach ($portCheck in $portsToCheck) {
    $portInUse = netstat -ano | findstr ":$($portCheck.Port)" | Select-Object -First 1
    if ($portInUse) {
        Write-Warning "$($portCheck.Name) port $($portCheck.Port) still in use"
    } else {
        Write-Success "$($portCheck.Name) port $($portCheck.Port) is available"
    }
}

# 7. Summary
if (-not $Quiet) {
    Write-Host ""
    Write-Host "🎯 Shutdown Summary:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Success "Translation services stopped"
    Write-Success "Ollama services stopped"
    
    if ($KeepNgrok) {
        Write-Info "ngrok kept running (as requested)"
    } else {
        Write-Success "ngrok services stopped"
    }
    
    if ($KeepTailscale) {
        Write-Info "Tailscale kept running (as requested)"
    } else {
        Write-Success "Tailscale services stopped"
    }
    
    Write-Host ""
    Write-Host "✨ Graceful shutdown completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Usage examples:" -ForegroundColor Cyan
    Write-Host "  .\shutdown.ps1                    # Stop all services"
    Write-Host "  .\shutdown.ps1 -KeepTailscale     # Keep Tailscale running"
    Write-Host "  .\shutdown.ps1 -KeepNgrok         # Keep ngrok running"
    Write-Host "  .\shutdown.ps1 -Force             # Force stop all processes"
    Write-Host "  .\shutdown.ps1 -Quiet             # Silent operation"
}
