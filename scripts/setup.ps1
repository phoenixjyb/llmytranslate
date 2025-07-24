# LLM Translation Service Setup Script for Windows (PowerShell)
# Updated for organized directory structure

Write-Host "Setting up LLM Translation Service for Windows..." -ForegroundColor Green

# Ensure we're in the project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
Write-Host "Working in project directory: $projectRoot" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow

# Use the correct Python path, ignoring Windows Store redirects
$pythonExe = "C:\Users\yanbo\AppData\Local\Programs\Python\Python313\python.exe"

if (Test-Path $pythonExe) {
    $pythonVersion = & $pythonExe --version 2>&1
    Write-Host "Found: $pythonVersion at $pythonExe" -ForegroundColor Green
} else {
    Write-Host "Python not found at expected location: $pythonExe" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
& $pythonExe -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Copy environment configuration
Write-Host "Setting up environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path "config\.env.example") {
        Copy-Item "config\.env.example" ".env"
        Write-Host "Created .env file from template. Please review and update as needed." -ForegroundColor Green
    } else {
        Write-Host "Warning: .env.example not found in config directory" -ForegroundColor Yellow
    }
}

# Check for Ollama
Write-Host "Checking for Ollama..." -ForegroundColor Yellow

try {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Ollama found: $ollamaVersion" -ForegroundColor Green
        
        Write-Host "Pulling default model..." -ForegroundColor Green
        ollama pull llama3.1:8b
    } else {
        throw "Ollama command failed"
    }
} catch {
    Write-Host "Ollama not found in PATH. Please install Ollama from https://ollama.ai/" -ForegroundColor Red
    Write-Host "Or run: .\scripts\add_ollama_to_path.ps1" -ForegroundColor Yellow
}

# Check for Redis
Write-Host "Checking for Redis..." -ForegroundColor Yellow
$redisExists = Get-Command redis-server -ErrorAction SilentlyContinue
if (-not $redisExists) {
    Write-Host "Redis not found. You can:" -ForegroundColor Yellow
    Write-Host "  1. Install Redis using Windows Subsystem for Linux (WSL)" -ForegroundColor Yellow
    Write-Host "  2. Use Docker: docker run -d -p 6379:6379 redis:alpine" -ForegroundColor Yellow
    Write-Host "  3. The service will work without Redis (using in-memory cache)" -ForegroundColor Yellow
} else {
    Write-Host "Redis found." -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup complete! To start the service:" -ForegroundColor Green
Write-Host "1. Activate virtual environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Start the service: python run.py" -ForegroundColor White
Write-Host "3. Access the API at: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "For production deployment, run: .\scripts\production-setup.ps1" -ForegroundColor Cyan
Write-Host "For documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📂 Project Structure:" -ForegroundColor Yellow
Write-Host "  • Documentation: .\docs\" -ForegroundColor Gray
Write-Host "  • Scripts: .\scripts\" -ForegroundColor Gray
Write-Host "  • Configuration: .\config\" -ForegroundColor Gray
Write-Host "  • Source Code: .\src\" -ForegroundColor Gray
Write-Host "  • Tests: .\tests\" -ForegroundColor Gray
Write-Host "  • Logs: .\logs\" -ForegroundColor Gray
