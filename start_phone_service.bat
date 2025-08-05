@echo off
echo 🔧 MANUAL SERVICE RESTART
echo ========================================
echo.
echo 1. Stopping any existing Python processes...
taskkill /F /IM python.exe /T 2>nul
timeout /t 3 /nobreak >nul
echo.
echo 2. Starting phone call service with audio fixes...
echo    ✅ Direct numpy audio processing enabled
echo    ✅ Multiple sample rate detection active
echo    ✅ No more FFmpeg video format errors
echo    ✅ Overlapping response prevention active
echo.
echo Starting service...
.venv\Scripts\python.exe run.py phone_call
echo.
echo Service stopped.
pause
