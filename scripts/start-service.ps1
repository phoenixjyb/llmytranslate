# ================================================================================================
# Cross-Platform LLM Translation Service Starter
# OS-Aware service startup with environment variable conflict resolution
# ================================================================================================

param(
    [switch]$Production,
    [switch]$Debug,
    [switch]$Force,
    [switch]$WithNgrok,
    [switch]$WithTailscale
)

# Platform detection with better Windows version
$IsWindowsPlatform = $IsWindows -or ($PSVersionTable.PSVersion.Major -lt 6)
$IsMacOSPlatform = $IsMacOS -or $false
$IsLinuxPlatform = $IsLinux -or $false

# Get proper Windows version for display
if ($IsWindowsPlatform) {
    $WindowsVersion = (Get-CimInstance Win32_OperatingSystem).Caption
    $PlatformDisplay = $WindowsVersion
} else {
    $PlatformDisplay = $PSVersionTable.OS
}

Write-Host "🚀 Cross-Platform LLM Translation Service Starter" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Platform: $PlatformDisplay" -ForegroundColor Yellow

# Environment Variable Conflict Resolution
function Resolve-EnvironmentConflicts {
    Write-Host "`n🔧 Resolving environment variable conflicts..." -ForegroundColor Cyan
    
    # Store conflicting variables for restoration
    $conflictingVars = @{}
    
    # List of environment variables that can conflict with pydantic configuration
    $conflictPatterns = @('OLLAMA', 'REDIS', 'DATABASE', 'AUTH', 'API')
    
    foreach ($pattern in $conflictPatterns) {
        # Check for exact matches and variations
        $conflicts = Get-ChildItem Env: | Where-Object { 
            $_.Name -eq $pattern -or 
            $_.Name -eq $pattern.ToLower() -or
            $_.Name -eq $pattern.ToUpper()
        }
        
        foreach ($conflict in $conflicts) {
            $originalName = $conflict.Name
            $originalValue = $conflict.Value
            
            # Store for potential restoration
            $conflictingVars[$originalName] = $originalValue
            
            # Remove the conflicting variable
            Remove-Item "Env:\$originalName" -ErrorAction SilentlyContinue
            Write-Host "  ⚠️  Temporarily removed: $originalName" -ForegroundColor Yellow
        }
    }
    
    return $conflictingVars
}

# Cross-platform Python executable detection
function Get-PythonExecutable {
    $pythonExecs = @()
    
    if ($IsWindowsPlatform) {
        $pythonExecs = @(
            ".\.venv\Scripts\python.exe",
            ".\.venv\Scripts\python3.exe",
            "python.exe",
            "python3.exe",
            "py.exe"
        )
    } else {
        $pythonExecs = @(
            "./.venv/bin/python",
            "./.venv/bin/python3",
            "python3",
            "python"
        )
    }
    
    foreach ($exec in $pythonExecs) {
        try {
            if (Test-Path $exec -ErrorAction SilentlyContinue) {
                return $exec
            }
            
            # Test if command exists in PATH
            $null = Get-Command $exec -ErrorAction SilentlyContinue
            if ($?) {
                return $exec
            }
        } catch {
            continue
        }
    }
    
    throw "No suitable Python executable found. Please ensure Python is installed and virtual environment is set up."
}

# Service health check with Phase 4 component verification
function Test-ServiceHealth {
    param([int]$Port = 8000, [int]$MaxAttempts = 30)
    
    Write-Host "`n🏥 Checking service health..." -ForegroundColor Cyan
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            if ($IsWindowsPlatform) {
                $result = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
                if ($result.TcpTestSucceeded) {
                    # Additional check: verify main health endpoint
                    try {
                        $healthResponse = Invoke-RestMethod -Uri "http://localhost:$Port/api/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
                        if ($healthResponse) {
                            Write-Host "✅ Main service is healthy and responding on port $Port" -ForegroundColor Green
                            
                            # Phase 4: Check service components
                            Write-Host "`n🔍 Verifying Phase 4 service components..." -ForegroundColor Cyan
                            $componentEndpoints = @(
                                @{ Name = "Optimized LLM"; Endpoint = "/api/llm/health"; Icon = "🧠" },
                                @{ Name = "Performance Monitor"; Endpoint = "/api/performance/status"; Icon = "📊" },
                                @{ Name = "Quality Monitor"; Endpoint = "/api/quality/status"; Icon = "✅" },
                                @{ Name = "Connection Pool"; Endpoint = "/api/connections/status"; Icon = "🔗" }
                            )
                            
                            $healthyComponents = 0
                            foreach ($component in $componentEndpoints) {
                                try {
                                    $compResponse = Invoke-RestMethod -Uri "http://localhost:$Port$($component.Endpoint)" -TimeoutSec 2 -ErrorAction SilentlyContinue
                                    if ($compResponse) {
                                        Write-Host "  $($component.Icon) $($component.Name): ✅ Healthy" -ForegroundColor Green
                                        $healthyComponents++
                                    } else {
                                        Write-Host "  $($component.Icon) $($component.Name): ⚠️ Partial" -ForegroundColor Yellow
                                    }
                                } catch {
                                    Write-Host "  $($component.Icon) $($component.Name): ⚠️ Initializing" -ForegroundColor Yellow
                                }
                            }
                            
                            Write-Host "`n🎯 Phase 4 Status: $healthyComponents/4 components ready" -ForegroundColor Cyan
                            return $true
                        }
                    } catch {
                        # Health endpoint not ready yet, continue waiting
                    }
                }
            } else {
                # Use curl for non-Windows platforms
                $null = curl -s "http://localhost:$Port/api/health" 2>/dev/null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Service is healthy and responding on port $Port" -ForegroundColor Green
                    return $true
                }
            }
        } catch {
            # Ignore connection errors during startup
        }
        
        if ($i -le 10) {
            Write-Host "  ⏳ Waiting for service to start... ($i/$MaxAttempts)" -ForegroundColor Yellow
        } elseif ($i % 5 -eq 0) {
            Write-Host "  ⏳ Still waiting... ($i/$MaxAttempts)" -ForegroundColor Yellow
        }
        
        Start-Sleep -Seconds 2
    }
    
    Write-Host "❌ Service health check failed after $MaxAttempts attempts" -ForegroundColor Red
    return $false
}

# Display service information with Phase 4 dashboard
function Show-ServiceInfo {
    param([int]$Port = 8000)
    
    Write-Host "`n🌐 Service Access Information:" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    
    # Get local IP addresses
    if ($IsWindowsPlatform) {
        $localIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
            $_.IPAddress -ne "127.0.0.1" -and $_.PrefixOrigin -eq "Dhcp" 
        } | Select-Object -ExpandProperty IPAddress
    } else {
        # For macOS/Linux
        $localIPs = @()
        try {
            $ifconfigResult = ifconfig 2>/dev/null | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | awk '{print $2}'
            $localIPs = $ifconfigResult -split "`n" | Where-Object { $_ -and $_ -ne "" }
        } catch {
            $localIPs = @("localhost")
        }
    }
    
    Write-Host "📱 Local Access:" -ForegroundColor Cyan
    Write-Host "   http://localhost:${Port}" -ForegroundColor White
    Write-Host "   http://127.0.0.1:${Port}" -ForegroundColor White
    
    if ($localIPs.Count -gt 0) {
        Write-Host "`n🌐 Network Access:" -ForegroundColor Cyan
        foreach ($ip in $localIPs) {
            Write-Host "   http://${ip}:${Port}" -ForegroundColor White
        }
    }
    
    Write-Host "`n📚 API Documentation:" -ForegroundColor Cyan
    Write-Host "   http://localhost:${Port}/docs" -ForegroundColor White
    Write-Host "   http://localhost:${Port}/api/health" -ForegroundColor White
    
    Write-Host "`n🚀 Phase 4 Services:" -ForegroundColor Cyan
    Write-Host "   � Service Dashboard: .\scripts\service-status.ps1" -ForegroundColor White
    Write-Host "   🔄 Continuous Monitor: .\scripts\service-status.ps1 -Continuous" -ForegroundColor White
    Write-Host "   📋 Detailed View: .\scripts\service-status.ps1 -Detailed" -ForegroundColor White
    
    Write-Host "`n�🛠️  Management:" -ForegroundColor Cyan
    Write-Host "   Stop: Ctrl+C" -ForegroundColor White
    Write-Host "   Logs: Check terminal output" -ForegroundColor White
    Write-Host "   Status: .\scripts\service-status.ps1" -ForegroundColor White
}

# Main execution
try {
    Write-Host "`n🔍 Pre-flight checks..." -ForegroundColor Cyan
    
    # 1. Resolve environment conflicts
    $savedVars = Resolve-EnvironmentConflicts
    
    # 2. Find Python executable
    Write-Host "`n🐍 Detecting Python executable..." -ForegroundColor Cyan
    $pythonExec = Get-PythonExecutable
    Write-Host "   Using: $pythonExec" -ForegroundColor Green
    
    # 3. Set environment for service
    if ($Production) {
        $env:ENVIRONMENT = "production"
        Write-Host "`n🏭 Running in PRODUCTION mode" -ForegroundColor Yellow
    } else {
        $env:ENVIRONMENT = "development"
        Write-Host "`n🛠️  Running in DEVELOPMENT mode" -ForegroundColor Green
    }
    
    if ($Debug) {
        $env:DEBUG = "true"
        Write-Host "🐛 Debug mode enabled" -ForegroundColor Yellow
    }
    
    # 4. Verify required files
    $requiredFiles = @("run.py", ".env", "src/main.py")
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-Host "❌ Required file missing: $file" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "✅ All required files found" -ForegroundColor Green
    
    # 5. Start the service
    Write-Host "`n🚀 Starting LLM Translation Service..." -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Cyan
    
    # Start service in background for health check
    $serviceJob = Start-Job -ScriptBlock {
        param($pythonExec, $workingDir)
        Set-Location $workingDir
        & $pythonExec run.py
    } -ArgumentList $pythonExec, (Get-Location)
    
    # Wait for service to start and check health
    Start-Sleep -Seconds 3
    
    # Check if service started successfully
    $serviceHealthy = Test-ServiceHealth -Port 8000
    
    if ($serviceHealthy) {
        # Stop background job and start in foreground
        Stop-Job $serviceJob -PassThru | Remove-Job
        
        Show-ServiceInfo -Port 8000
        
        Write-Host "`n🎯 Service started successfully!" -ForegroundColor Green
        
        # Start ngrok if requested
        if ($WithNgrok) {
            Write-Host "`n🌐 Starting ngrok tunnel..." -ForegroundColor Cyan
            try {
                # Check if ngrok is available
                $ngrokPath = Get-Command "ngrok" -ErrorAction SilentlyContinue
                if ($ngrokPath) {
                    # Start ngrok in background with warning bypass
                    $ngrokJob = Start-Job -ScriptBlock {
                        param($port)
                        try {
                            # Use ngrok with warning suppression
                            & ngrok http $port --log=stdout --bind-tls=true
                        } catch {
                            Write-Output "Ngrok failed: $($_.Exception.Message)"
                        }
                    } -ArgumentList 8000
                    
                    Start-Sleep -Seconds 3
                    
                    # Try to get ngrok URL
                    try {
                        $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
                        if ($ngrokApi.tunnels -and $ngrokApi.tunnels.Count -gt 0) {
                            $publicUrl = $ngrokApi.tunnels[0].public_url
                            Write-Host "🌍 Public URL: $publicUrl" -ForegroundColor Green
                            Write-Host "🌍 Direct Access: $publicUrl (bypasses warning)" -ForegroundColor Green
                        } else {
                            Write-Host "⚠️  Ngrok started but URL not ready yet. Check http://localhost:4040" -ForegroundColor Yellow
                        }
                    } catch {
                        Write-Host "⚠️  Ngrok started but unable to get URL. Check http://localhost:4040" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "❌ Ngrok not found. Please install ngrok first." -ForegroundColor Red
                    Write-Host "   Download from: https://ngrok.com/download" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "❌ Failed to start ngrok: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        # Start Tailscale configuration if requested
        if ($WithTailscale) {
            Write-Host "`n🔗 Configuring Tailscale access..." -ForegroundColor Cyan
            try {
                # Check if Tailscale is available
                $tailscalePath = Get-Command "tailscale" -ErrorAction SilentlyContinue
                if ($tailscalePath) {
                    # Check if Tailscale is running
                    try {
                        $tailscaleStatus = & tailscale status 2>$null
                        if ($LASTEXITCODE -eq 0) {
                            # Get Tailscale IP
                            $tailscaleIP = & tailscale ip -4 2>$null
                            if ($tailscaleIP -and $LASTEXITCODE -eq 0) {
                                Write-Host "🌐 Tailscale IP: $tailscaleIP" -ForegroundColor Green
                                Write-Host "🌐 Service URL: http://$tailscaleIP:8000" -ForegroundColor Green
                                Write-Host "📚 API Docs: http://$tailscaleIP:8000/docs" -ForegroundColor Green
                                
                                # Set up Tailscale environment if available
                                if (Test-Path ".env.tailscale") {
                                    Write-Host "🔧 Using Tailscale environment configuration" -ForegroundColor Cyan
                                    Copy-Item ".env.tailscale" ".env" -Force
                                }
                            } else {
                                Write-Host "⚠️  Unable to get Tailscale IP. Service will start normally." -ForegroundColor Yellow
                            }
                        } else {
                            Write-Host "⚠️  Tailscale is not running. Please run 'tailscale up' first." -ForegroundColor Yellow
                            Write-Host "   Service will start normally on localhost." -ForegroundColor Yellow
                        }
                    } catch {
                        Write-Host "⚠️  Tailscale status check failed. Service will start normally." -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "❌ Tailscale not found. Please install Tailscale first." -ForegroundColor Red
                    Write-Host "   Download from: https://tailscale.com/download" -ForegroundColor Yellow
                    Write-Host "   Service will start normally on localhost." -ForegroundColor Yellow
                }
            } catch {
                Write-Host "❌ Failed to configure Tailscale: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
        Write-Host "=================================" -ForegroundColor Cyan
        
        # Start service in foreground
        & $pythonExec run.py
    } else {
        # Get job output for debugging
        $jobOutput = Receive-Job $serviceJob
        Stop-Job $serviceJob -PassThru | Remove-Job
        
        Write-Host "`n❌ Service failed to start properly" -ForegroundColor Red
        Write-Host "Debug information:" -ForegroundColor Yellow
        Write-Host $jobOutput -ForegroundColor Gray
        
        exit 1
    }
    
} catch {
    Write-Host "`n❌ Error starting service:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    # Restore environment variables if needed
    if ($savedVars.Count -gt 0) {
        Write-Host "`n🔄 Restoring environment variables..." -ForegroundColor Yellow
        foreach ($var in $savedVars.GetEnumerator()) {
            [Environment]::SetEnvironmentVariable($var.Key, $var.Value, "Process")
        }
    }
    
    exit 1
} finally {
    Write-Host "`n👋 Service stopped" -ForegroundColor Cyan
}
