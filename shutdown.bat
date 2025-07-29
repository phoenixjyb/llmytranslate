@echo off
REM LLM Translation Service - Graceful Shutdown Script (Batch Version)
REM This script safely stops all translation services, ngrok, and tailscale

setlocal enabledelayedexpansion

echo.
echo ========================================================
echo   LLM Translation Service - Graceful Shutdown
echo ========================================================
echo.

REM Parse command line arguments
set KEEP_TAILSCALE=0
set KEEP_NGROK=0
set FORCE_STOP=0
set QUIET=0

:parse_args
if "%~1"=="" goto start_shutdown
if /i "%~1"=="--keep-tailscale" set KEEP_TAILSCALE=1
if /i "%~1"=="--keep-ngrok" set KEEP_NGROK=1
if /i "%~1"=="--force" set FORCE_STOP=1
if /i "%~1"=="--quiet" set QUIET=1
if /i "%~1"=="/?" goto show_help
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo Usage: shutdown.bat [options]
echo.
echo Options:
echo   --keep-tailscale    Keep Tailscale running
echo   --keep-ngrok        Keep ngrok running  
echo   --force             Force stop all processes
echo   --quiet             Silent operation
echo   --help, -h, /?      Show this help
echo.
echo Examples:
echo   shutdown.bat                     Stop all services
echo   shutdown.bat --keep-tailscale    Keep Tailscale running
echo   shutdown.bat --force             Force stop all processes
goto :eof

:start_shutdown

echo [INFO] Step 1: Stopping Translation Services...

REM Try graceful API shutdown first
if !QUIET!==0 echo [INFO] Attempting graceful API shutdown...
curl -X POST http://localhost:8000/api/admin/shutdown >nul 2>&1
if !errorlevel!==0 (
    if !QUIET!==0 echo [SUCCESS] Translation service shut down gracefully
    timeout /t 2 >nul
) else (
    if !QUIET!==0 echo [WARNING] Could not shutdown via API, using process termination
)

REM Stop Python/FastAPI processes
if !QUIET!==0 echo [INFO] Stopping Python processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    if !QUIET!==0 echo [INFO] Stopping Python process PID: %%i
    taskkill /pid %%i /f >nul 2>&1
    if !errorlevel!==0 (
        if !QUIET!==0 echo [SUCCESS] Python process %%i stopped
    )
)

REM Stop Uvicorn processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq uvicorn.exe" /fo table /nh 2^>nul') do (
    if !QUIET!==0 echo [INFO] Stopping Uvicorn process PID: %%i
    taskkill /pid %%i /f >nul 2>&1
    if !errorlevel!==0 (
        if !QUIET!==0 echo [SUCCESS] Uvicorn process %%i stopped
    )
)

echo [INFO] Step 2: Stopping Ollama Services...

REM Stop Ollama processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq ollama.exe" /fo table /nh 2^>nul') do (
    if !QUIET!==0 echo [INFO] Stopping Ollama process PID: %%i
    taskkill /pid %%i /f >nul 2>&1
    if !errorlevel!==0 (
        if !QUIET!==0 echo [SUCCESS] Ollama process %%i stopped
    )
)

if !KEEP_NGROK!==0 (
    echo [INFO] Step 3: Stopping ngrok Services...
    
    REM Stop ngrok processes
    for /f "tokens=2" %%i in ('tasklist /fi "imagename eq ngrok.exe" /fo table /nh 2^>nul') do (
        if !QUIET!==0 echo [INFO] Stopping ngrok process PID: %%i
        taskkill /pid %%i /f >nul 2>&1
        if !errorlevel!==0 (
            if !QUIET!==0 echo [SUCCESS] ngrok process %%i stopped
        )
    )
) else (
    echo [INFO] Step 3: Keeping ngrok running (--keep-ngrok specified)
)

if !KEEP_TAILSCALE!==0 (
    echo [INFO] Step 4: Stopping Tailscale Services...
    
    REM Try graceful Tailscale logout first
    if exist "C:\Program Files\Tailscale\tailscale.exe" (
        if !QUIET!==0 echo [INFO] Attempting graceful Tailscale disconnect...
        "C:\Program Files\Tailscale\tailscale.exe" logout >nul 2>&1
        timeout /t 2 >nul
        if !QUIET!==0 echo [SUCCESS] Tailscale disconnected gracefully
    )
    
    REM Stop Tailscale processes
    for /f "tokens=1,2" %%i in ('tasklist /fi "imagename eq tailscale*" /fo table /nh 2^>nul') do (
        if !QUIET!==0 echo [INFO] Stopping Tailscale process: %%i PID: %%j
        taskkill /pid %%j /f >nul 2>&1
        if !errorlevel!==0 (
            if !QUIET!==0 echo [SUCCESS] Tailscale process %%j stopped
        )
    )
    
    REM Also check for tailscaled service
    for /f "tokens=2" %%i in ('tasklist /fi "imagename eq tailscaled.exe" /fo table /nh 2^>nul') do (
        if !QUIET!==0 echo [INFO] Stopping tailscaled process PID: %%i
        taskkill /pid %%i /f >nul 2>&1
        if !errorlevel!==0 (
            if !QUIET!==0 echo [SUCCESS] tailscaled process %%i stopped
        )
    )
) else (
    echo [INFO] Step 4: Keeping Tailscale running (--keep-tailscale specified)
)

echo [INFO] Step 5: Final Verification...

REM Check for remaining processes
set FOUND_PROCESSES=0
for /f "tokens=1,2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    echo [WARNING] Python process still running: %%i PID: %%j
    set FOUND_PROCESSES=1
)

for /f "tokens=1,2" %%i in ('tasklist /fi "imagename eq ollama.exe" /fo table /nh 2^>nul') do (
    echo [WARNING] Ollama process still running: %%i PID: %%j
    set FOUND_PROCESSES=1
)

if !KEEP_NGROK!==0 (
    for /f "tokens=1,2" %%i in ('tasklist /fi "imagename eq ngrok.exe" /fo table /nh 2^>nul') do (
        echo [WARNING] ngrok process still running: %%i PID: %%j
        set FOUND_PROCESSES=1
    )
)

if !KEEP_TAILSCALE!==0 (
    for /f "tokens=1,2" %%i in ('tasklist /fi "imagename eq tailscale*" /fo table /nh 2^>nul') do (
        echo [WARNING] Tailscale process still running: %%i PID: %%j
        set FOUND_PROCESSES=1
    )
)

if !FOUND_PROCESSES!==0 (
    echo [SUCCESS] All target services have been stopped
) else (
    echo [WARNING] Some processes are still running
    if !FORCE_STOP!==1 (
        echo [INFO] Force parameter not specified. Use --force to force stop remaining processes
    )
)

echo [INFO] Step 6: Port Status Check...

REM Check if ports are still in use
netstat -ano | findstr ":8000" >nul 2>&1
if !errorlevel!==0 (
    echo [WARNING] Translation Service port 8000 still in use
) else (
    echo [SUCCESS] Translation Service port 8000 is available
)

netstat -ano | findstr ":11434" >nul 2>&1
if !errorlevel!==0 (
    echo [WARNING] Ollama API port 11434 still in use
) else (
    echo [SUCCESS] Ollama API port 11434 is available
)

if !KEEP_NGROK!==0 (
    netstat -ano | findstr ":4040" >nul 2>&1
    if !errorlevel!==0 (
        echo [WARNING] ngrok Dashboard port 4040 still in use
    ) else (
        echo [SUCCESS] ngrok Dashboard port 4040 is available
    )
)

if !QUIET!==0 (
    echo.
    echo ========================================================
    echo   Shutdown Summary:
    echo ========================================================
    echo [SUCCESS] Translation services stopped
    echo [SUCCESS] Ollama services stopped
    
    if !KEEP_NGROK!==1 (
        echo [INFO] ngrok kept running ^(as requested^)
    ) else (
        echo [SUCCESS] ngrok services stopped
    )
    
    if !KEEP_TAILSCALE!==1 (
        echo [INFO] Tailscale kept running ^(as requested^)
    ) else (
        echo [SUCCESS] Tailscale services stopped
    )
    
    echo.
    echo [SUCCESS] Graceful shutdown completed!
    echo.
    echo Usage examples:
    echo   shutdown.bat                     Stop all services
    echo   shutdown.bat --keep-tailscale    Keep Tailscale running
    echo   shutdown.bat --keep-ngrok        Keep ngrok running
    echo   shutdown.bat --force             Force stop all processes
    echo   shutdown.bat --quiet             Silent operation
)

endlocal
pause
