@echo off
echo Building LLMyTranslate Android App (Phase 2A)...
echo Kotlin 1.9.20 + Compose 1.5.4 + Native STT/TTS
echo.

REM Clean previous build
echo Cleaning previous build...
.\gradlew.bat clean

REM Build APK
echo Building debug APK...
.\gradlew.bat assembleDebug

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ BUILD SUCCESSFUL!
    echo APK Location: app\build\outputs\apk\debug\app-debug.apk
    for %%A in (app\build\outputs\apk\debug\app-debug.apk) do echo APK Size: %%~zA bytes
    echo.
    echo Ready for Samsung S24 Ultra deployment!
) else (
    echo.
    echo ❌ BUILD FAILED with exit code: %ERRORLEVEL%
)

pause
