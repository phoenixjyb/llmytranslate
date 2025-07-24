@echo off
echo Setting up LLM Translation Service for Windows...

REM Check Python version
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo Python not found! Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Copy environment configuration
echo Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo Created .env file from template. Please review and update as needed.
)

REM Check for Ollama
echo Checking for Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama not found. Please install Ollama from https://ollama.ai/
    echo Then run: ollama pull llama3.1:8b
) else (
    echo Ollama found. Pulling default model...
    ollama pull llama3.1:8b
)

echo.
echo Setup complete! To start the service:
echo 1. Activate virtual environment: .venv\Scripts\activate.bat
echo 2. Start the service: python run.py
echo 3. Access the API at: http://localhost:8000
echo.
echo For documentation: http://localhost:8000/docs
pause
