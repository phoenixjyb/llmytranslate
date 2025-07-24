@echo off
echo Adding Ollama to Windows PATH...

REM Add Ollama to User PATH (no admin required)
for /f "usebackq tokens=2,*" %%A in (`reg query HKCU\Environment /v PATH`) do set USER_PATH=%%B

REM Check if Ollama path is already in PATH
echo %USER_PATH% | find /i "Ollama" >nul
if %errorlevel%==0 (
    echo Ollama is already in your PATH!
) else (
    echo Adding Ollama to your PATH...
    setx PATH "%USER_PATH%;C:\Users\yanbo\AppData\Local\Programs\Ollama"
    echo Done! Please restart your terminal or PowerShell for changes to take effect.
)

pause
