# LLM Translation Service Setup Script for Windows (PowerShell)

Write-Host "Setting up LLM Translation Service for Windows..." -ForegroundColor Green

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

# Copy environment configuration
Write-Host "Setting up environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file from template. Please review and update as needed." -ForegroundColor Green
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
    Write-Host "Or ensure Ollama is added to your PATH environment variable." -ForegroundColor Yellow
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
Write-Host "For documentation: http://localhost:8000/docs" -ForegroundColor Cyan
