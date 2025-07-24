#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete startup script for LLM Translation Service
    
.DESCRIPTION
    This script handles all the setup and startup procedures for the LLM Translation Service:
    - Validates prerequisites (Ollama, Python, project structure)
    - Handles environment variable conflicts
    - Tests configuration loading
    - Starts the translation service
    
.PARAMETER ConfigTest
    Only run configuration test without starting the service
    
.PARAMETER Port
    Specify custom port (default: 8000)
    
.PARAMETER Debug
    Enable debug mode with verbose output
    
.EXAMPLE
    .\start-service.ps1
    Start the service with default settings
    
.EXAMPLE
    .\start-service.ps1 -ConfigTest
    Only test configuration without starting service
    
.EXAMPLE
    .\start-service.ps1 -Port 8080 -Debug
    Start service on port 8080 with debug output
#>

param(
    [switch]$ConfigTest,
    [int]$Port = 8000,
    [switch]$Debug
)

# Color output functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Step { param($msg) Write-Host "🔄 $msg" -ForegroundColor Blue }

# Script header
Write-Host @"
╔════════════════════════════════════════════════════════════════════════════════╗
║                        LLM Translation Service Startup                        ║
║                              Windows PowerShell                               ║
╚════════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

Write-Info "Starting LLM Translation Service setup and validation..."
Write-Info "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Function to check prerequisites
function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    # Check if we're in the right directory
    if (-not (Test-Path ".\src") -or -not (Test-Path ".\run.py") -or -not (Test-Path ".\.venv")) {
        Write-Error "Not in project directory or missing required files/folders"
        Write-Info "Expected: src/, run.py, .venv/"
        Write-Info "Current directory: $(Get-Location)"
        return $false
    }
    Write-Success "Project structure validated"
    
    # Check Ollama installation
    try {
        $ollamaVersion = ollama --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Ollama found: $ollamaVersion"
        } else {
            throw "Ollama not found"
        }
    } catch {
        Write-Error "Ollama not installed or not in PATH"
        Write-Info "Please install Ollama from https://ollama.ai/"
        return $false
    }
    
    # Check for required model
    try {
        $models = ollama list 2>$null
        if ($models -match "llama3\.1:8b") {
            Write-Success "Required model llama3.1:8b found"
        } else {
            Write-Warning "Model llama3.1:8b not found"
            Write-Info "Run: ollama pull llama3.1:8b"
            return $false
        }
    } catch {
        Write-Error "Cannot list Ollama models"
        return $false
    }
    
    # Check Python in virtual environment
    try {
        $pythonPath = ".\.venv\Scripts\python.exe"
        if (Test-Path $pythonPath) {
            $pythonVersion = & $pythonPath --version 2>$null
            Write-Success "Python found: $pythonVersion"
        } else {
            Write-Error "Virtual environment Python not found at $pythonPath"
            return $false
        }
    } catch {
        Write-Error "Cannot execute Python from virtual environment"
        return $false
    }
    
    return $true
}

# Function to handle environment conflicts
function Resolve-EnvironmentConflicts {
    Write-Step "Resolving environment variable conflicts..."
    
    # Remove conflicting ollama environment variable
    if ($env:ollama) {
        Write-Warning "Found conflicting 'ollama' environment variable"
        Remove-Item Env:\ollama -ErrorAction SilentlyContinue
        Write-Success "Removed conflicting environment variable"
    } else {
        Write-Success "No conflicting environment variables found"
    }
}

# Function to test configuration
function Test-Configuration {
    Write-Step "Testing configuration loading..."
    
    try {
        $result = & ".\.venv\Scripts\python.exe" "test_config.py" 2>&1
        if ($LASTEXITCODE -eq 0 -and $result -match "Settings loaded successfully") {
            Write-Success "Configuration loaded successfully"
            if ($Debug) {
                Write-Info "Configuration details:"
                $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
            return $true
        } else {
            Write-Error "Configuration test failed"
            Write-Host $result -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Error "Failed to run configuration test: $_"
        return $false
    }
}

# Function to start the service
function Start-TranslationService {
    param([int]$ServicePort)
    
    Write-Step "Starting LLM Translation Service on port $ServicePort..."
    
    # Set port if different from default
    if ($ServicePort -ne 8000) {
        $env:API__PORT = $ServicePort
        Write-Info "Custom port set: $ServicePort"
    }
    
    Write-Info "Service will be available at: http://localhost:$ServicePort"
    Write-Info "API Documentation: http://localhost:$ServicePort/docs"
    Write-Info "Health Check: http://localhost:$ServicePort/api/health"
    Write-Host ""
    Write-Warning "Press Ctrl+C to stop the service"
    Write-Host ""
    
    try {
        # Start the service
        & ".\.venv\Scripts\python.exe" "run.py"
    } catch {
        Write-Error "Failed to start service: $_"
        return $false
    }
}

# Function to display helpful information
function Show-ServiceInfo {
    Write-Host @"

╔════════════════════════════════════════════════════════════════════════════════╗
║                               Service Information                              ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Service URL:     http://localhost:$Port                                       ║
║ Documentation:   http://localhost:$Port/docs                                  ║
║ Health Check:    http://localhost:$Port/api/health                            ║
║                                                                                ║
║ Test Commands:                                                                 ║
║ curl http://localhost:$Port/api/health                                        ║
║ curl -X POST http://localhost:$Port/api/demo/translate \                      ║
║      -d "q=hello world&from=en&to=zh"                                         ║
╚════════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan
}

# Main execution
try {
    # Step 1: Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Error "Prerequisites check failed. Please fix the issues above."
        exit 1
    }
    Write-Host ""
    
    # Step 2: Resolve environment conflicts
    Resolve-EnvironmentConflicts
    Write-Host ""
    
    # Step 3: Test configuration
    if (-not (Test-Configuration)) {
        Write-Error "Configuration test failed. Please check your setup."
        exit 1
    }
    Write-Host ""
    
    # Step 4: If only config test requested, exit here
    if ($ConfigTest) {
        Write-Success "Configuration test completed successfully!"
        Write-Info "Service is ready to start. Run without -ConfigTest to start the service."
        exit 0
    }
    
    # Step 5: Show service information
    Show-ServiceInfo
    
    # Step 6: Start the service
    Start-TranslationService -ServicePort $Port
    
} catch {
    Write-Error "Startup script failed: $_"
    Write-Info "For detailed troubleshooting, see TESTING_PROCEDURE.md"
    exit 1
} finally {
    Write-Host ""
    Write-Info "Service startup script completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}
