#!/usr/bin/env powershell
<#
.SYNOPSIS
Cross-Platform Chatbot Service Starter - Windows Edition

.DESCRIPTION
Extends existing translation service with chatbot functionality.
Provides full cross-platform support with Windows optimizations.

.PARAMETER ChatOnly
Start only the chatbot service on port 8001

.PARAMETER Production
Run in production mode with optimizations

.PARAMETER Debug  
Run in debug mode with verbose logging

.PARAMETER WithNgrok
Enable Ngrok tunnel for public access

.PARAMETER WithTailscale
Enable Tailscale VPN access

.EXAMPLE
.\start-chatbot.ps1 -Production -WithTailscale
Start chatbot with translation service in production mode with Tailscale

.EXAMPLE  
.\start-chatbot.ps1 -ChatOnly -Debug
Start only chatbot service in debug mode
#>

param(
    [switch]$ChatOnly,
    [switch]$Production,
    [switch]$Debug,
    [switch]$WithNgrok,
    [switch]$WithTailscale,
    [switch]$Force
)

Write-Host "🤖 LLM Chatbot Service - Windows Edition" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Platform detection
$PlatformDisplay = (Get-CimInstance Win32_OperatingSystem).Caption
Write-Host "Platform: $PlatformDisplay" -ForegroundColor Yellow

# Environment Variable Conflict Resolution (reuse from existing service)
function Resolve-EnvironmentConflicts {
    Write-Host "`n🔧 Resolving environment variable conflicts..." -ForegroundColor Cyan
    
    $conflictingVars = @{}
    $conflictPatterns = @('OLLAMA', 'REDIS', 'DATABASE', 'AUTH', 'API', 'CHATBOT')
    
    foreach ($pattern in $conflictPatterns) {
        $conflicts = Get-ChildItem Env: | Where-Object { 
            $_.Name -eq $pattern -or 
            $_.Name -eq $pattern.ToLower() -or
            $_.Name -eq $pattern.ToUpper()
        }
        
        foreach ($conflict in $conflicts) {
            $originalName = $conflict.Name
            $originalValue = $conflict.Value
            $conflictingVars[$originalName] = $originalValue
            Remove-Item "Env:\$originalName" -ErrorAction SilentlyContinue
            Write-Host "  ⚠️  Temporarily removed: $originalName" -ForegroundColor Yellow
        }
    }
    
    return $conflictingVars
}

# Cross-platform Python executable detection (reuse existing logic)
function Get-PythonExecutable {
    $pythonExecs = @(
        ".\.venv\Scripts\python.exe",
        ".\.venv\Scripts\python3.exe", 
        "python.exe",
        "python3.exe",
        "py.exe"
    )
    
    foreach ($exec in $pythonExecs) {
        try {
            if (Test-Path $exec -ErrorAction SilentlyContinue) {
                return $exec
            }
            
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

# Environment setup for chatbot
function Set-ChatbotEnvironment {
    Write-Host "`n⚙️  Setting up chatbot environment..." -ForegroundColor Cyan
    
    # Core chatbot settings
    $env:CHATBOT__ENABLED = "true"
    $env:CHATBOT__DEFAULT_MODEL = "gemma3:latest"
    $env:CHATBOT__MAX_CONVERSATIONS = "100"
    $env:CHATBOT__MAX_CONVERSATION_HISTORY = "50"
    $env:CHATBOT__CONVERSATION_TIMEOUT = "3600"
    
    # Platform-specific settings
    $env:PLATFORM__TYPE = "windows"
    $env:CHATBOT__STORAGE_PATH = "auto"  # Will use Windows APPDATA
    
    # Integration settings
    $env:CHATBOT__TRANSLATION_INTEGRATION = "true"
    $env:CHATBOT__SHARED_OLLAMA_CLIENT = "true"
    $env:CHATBOT__SHARED_CACHE = "true"
    
    # Feature flags
    $env:DEPLOYMENT__FEATURES = "translation,chatbot"
    $env:DEPLOYMENT__CROSS_PLATFORM = "true"
    
    # Performance settings
    $env:CHATBOT__CONCURRENT_CONVERSATIONS = "10"
    $env:CHATBOT__RESPONSE_TIMEOUT = "30"
    $env:CHATBOT__MEMORY_LIMIT_MB = "500"
    
    # Web interface
    $env:CHATBOT__WEB_INTERFACE = "true"
    $env:CHATBOT__WEB_PORT = "8001"
    
    if ($Production) {
        $env:ENVIRONMENT = "production"
        $env:DEBUG = "false"
        $env:CHATBOT__LOG_LEVEL = "INFO"
        Write-Host "  ✅ Production mode enabled" -ForegroundColor Green
    } else {
        $env:ENVIRONMENT = "development"
        $env:DEBUG = "true" 
        $env:CHATBOT__LOG_LEVEL = "DEBUG"
        Write-Host "  ✅ Development mode enabled" -ForegroundColor Green
    }
    
    if ($Debug) {
        $env:CHATBOT__LOG_LEVEL = "DEBUG"
        $env:LOGGING__LOG_LEVEL = "DEBUG"
        Write-Host "  ✅ Debug logging enabled" -ForegroundColor Green
    }
}

# Service health check (cross-platform)
function Test-ServiceHealth {
    param([int]$Port = 8000, [int]$MaxAttempts = 30)
    
    Write-Host "`n🏥 Checking service health..." -ForegroundColor Cyan
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $result = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
            if ($result.TcpTestSucceeded) {
                Write-Host "  ✅ Service is healthy and responding on port $Port" -ForegroundColor Green
                return $true
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
    
    Write-Host "  ❌ Service health check failed after $MaxAttempts attempts" -ForegroundColor Red
    return $false
}

# Display service information
function Show-ChatbotServiceInfo {
    param([int]$Port = 8000, [int]$ChatPort = 8001)
    
    Write-Host "`n🤖 Chatbot Service Access Information:" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Green
    
    # Get local IP addresses
    $localIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.IPAddress -ne "127.0.0.1" -and $_.PrefixOrigin -eq "Dhcp" 
    } | Select-Object -ExpandProperty IPAddress
    
    Write-Host "`n📱 Local Access:" -ForegroundColor Cyan
    if ($ChatOnly) {
        Write-Host "   🤖 Chatbot: http://localhost:${ChatPort}" -ForegroundColor White
        Write-Host "   🤖 Chat API: http://localhost:${ChatPort}/api/chat" -ForegroundColor White
    } else {
        Write-Host "   🔄 Translation: http://localhost:${Port}" -ForegroundColor White
        Write-Host "   🤖 Chatbot: http://localhost:${Port}/api/chat" -ForegroundColor White
    }
    
    if ($localIPs.Count -gt 0) {
        Write-Host "`n🌐 Network Access:" -ForegroundColor Cyan
        foreach ($ip in $localIPs) {
            if ($ChatOnly) {
                Write-Host "   🤖 Chatbot: http://${ip}:${ChatPort}" -ForegroundColor White
            } else {
                Write-Host "   🔄 Translation + Chat: http://${ip}:${Port}" -ForegroundColor White
            }
        }
    }
    
    Write-Host "`n📚 API Documentation:" -ForegroundColor Cyan
    if ($ChatOnly) {
        Write-Host "   📖 Docs: http://localhost:${ChatPort}/docs" -ForegroundColor White
        Write-Host "   🏥 Health: http://localhost:${ChatPort}/api/chat/health" -ForegroundColor White
    } else {
        Write-Host "   📖 Docs: http://localhost:${Port}/docs" -ForegroundColor White
        Write-Host "   🏥 Health: http://localhost:${Port}/api/health" -ForegroundColor White
        Write-Host "   🤖 Chat Health: http://localhost:${Port}/api/chat/health" -ForegroundColor White
    }
    
    Write-Host "`n🛠️  Management:" -ForegroundColor Cyan
    Write-Host "   Stop: Ctrl+C" -ForegroundColor White
    Write-Host "   Logs: Check terminal output" -ForegroundColor White
    Write-Host "   Platform: Windows (PowerShell)" -ForegroundColor White
}

# Main execution
try {
    Write-Host "`n🔍 Pre-flight checks..." -ForegroundColor Cyan
    
    # 1. Resolve environment conflicts
    $null = Resolve-EnvironmentConflicts
    
    # 2. Find Python executable
    Write-Host "`n🐍 Detecting Python executable..." -ForegroundColor Cyan
    $pythonExec = Get-PythonExecutable
    Write-Host "   Using: $pythonExec" -ForegroundColor Green
    
    # 3. Set environment for chatbot service
    Set-ChatbotEnvironment
    
    # 4. Verify required files exist
    Write-Host "`n📁 Verifying project structure..." -ForegroundColor Cyan
    
    $requiredFiles = @(
        "src\main.py",
        "src\api\routes\chatbot.py",
        "src\services\chatbot_service.py", 
        "src\models\chat_schemas.py",
        "src\storage\conversation_manager.py"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Host "   ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $file (missing)" -ForegroundColor Red
            throw "Required file missing: $file"
        }
    }
    
    Write-Host "`n🚀 Starting LLM Chatbot Service..." -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    
    if ($ChatOnly) {
        Write-Host "🤖 Starting Chatbot-only mode..." -ForegroundColor Cyan
        Write-Host "Port: 8001 (Chatbot only)" -ForegroundColor Yellow
        
        # Start chatbot-only service
        Start-Process -FilePath $pythonExec -ArgumentList @(
            "-m", "uvicorn", 
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--app-dir", ".",
            $(if ($Debug) { "--reload" } else { "" })
        ) -NoNewWindow -Wait
    } else {
        Write-Host "🔄 Starting Full Service (Translation + Chatbot)..." -ForegroundColor Cyan
        Write-Host "Port: 8000 (Translation + Chatbot)" -ForegroundColor Yellow
        
        # Use existing start-service.ps1 but with chatbot enabled
        $serviceArgs = @()
        if ($Production) { $serviceArgs += "-Production" }
        if ($Debug) { $serviceArgs += "-Debug" }
        if ($WithNgrok) { $serviceArgs += "-WithNgrok" }
        if ($WithTailscale) { $serviceArgs += "-WithTailscale" }
        if ($Force) { $serviceArgs += "-Force" }
        
        if (Test-Path ".\scripts\start-service.ps1") {
            Write-Host "   📜 Using existing service launcher with chatbot enabled" -ForegroundColor Green
            & ".\scripts\start-service.ps1" @serviceArgs
        } else {
            Write-Host "   🚀 Starting service directly..." -ForegroundColor Yellow
            
            # Health check first
            if (Test-ServiceHealth -Port 8000) {
                Show-ChatbotServiceInfo -Port 8000
            }
            
            # Start service directly
            & $pythonExec -m uvicorn src.main:app --host 0.0.0.0 --port 8000 $(if ($Debug) { "--reload" })
        }
    }
    
} catch {
    Write-Host "`n❌ Error starting chatbot service: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "   1. Ensure Python virtual environment is activated" -ForegroundColor White
    Write-Host "   2. Run: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "   3. Check if Ollama is running: ollama list" -ForegroundColor White
    Write-Host "   4. Verify port 8000/8001 is not in use" -ForegroundColor White
    exit 1
} finally {
    Write-Host "`n👋 Chatbot Service session ended" -ForegroundColor Cyan
}
