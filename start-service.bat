@echo off
setlocal enabledelayedexpansion

:: Simple batch script to start LLM Translation Service
:: This is a simplified version of start-service.ps1

echo.
echo ================================================================
echo                LLM Translation Service Startup
echo                      Windows Batch Script  
echo ================================================================
echo.

:: Check if in correct directory
if not exist "src" (
    echo [ERROR] src directory not found. Are you in the project root?
    pause
    exit /b 1
)

if not exist "run.py" (
    echo [ERROR] run.py not found. Are you in the project root?
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [ERROR] Virtual environment not found. Please set up .venv first.
    pause
    exit /b 1
)

echo [INFO] Project structure validated
echo.

:: Remove conflicting environment variable
set ollama=
echo [INFO] Cleared conflicting environment variables
echo.

:: Test configuration
echo [INFO] Testing configuration...
".\.venv\Scripts\python.exe" test_config.py
if errorlevel 1 (
    echo [ERROR] Configuration test failed
    pause
    exit /b 1
)
echo [SUCCESS] Configuration loaded successfully
echo.

:: Show service information
echo ================================================================
echo                      Service Information
echo ================================================================
echo Service URL:     http://localhost:8000
echo Documentation:   http://localhost:8000/docs
echo Health Check:    http://localhost:8000/api/health
echo.
echo Test Commands:
echo curl http://localhost:8000/api/health
echo curl -X POST http://localhost:8000/api/demo/translate -d "q=hello world&from=en&to=zh"
echo.
echo Press Ctrl+C to stop the service
echo ================================================================
echo.

:: Start the service
echo [INFO] Starting LLM Translation Service...
".\.venv\Scripts\python.exe" run.py

pause
