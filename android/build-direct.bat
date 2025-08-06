@echo off
REM Direct Gradle Build Script - Bypasses Wrapper Download
REM Uses locally extracted Gradle 8.4

echo 🔧 Direct Gradle Build - Phase 2A Android App
echo =============================================

REM Set UTF-8 encoding
chcp 65001 > nul

REM Set Java environment for Android Studio
set "JAVA_HOME=D:\Program Files\Android\Android Studio\jbr"
set "PATH=%JAVA_HOME%\bin;%PATH%"

REM Set Gradle home to extracted distribution
set "GRADLE_HOME=%~dp0.gradle\wrapper\dists\gradle-8.4-bin\3zae5u3bpga9bvzthql6s3mvp\gradle-8.4"
set "PATH=%GRADLE_HOME%\bin;%PATH%"

echo ☕ Java version:
java -version

echo 📂 Using Gradle at: %GRADLE_HOME%
echo.

REM Check if Gradle exists
if not exist "%GRADLE_HOME%\bin\gradle.bat" (
    echo ❌ Error: Gradle not found at %GRADLE_HOME%
    echo Please ensure Gradle 8.4 is extracted properly
    pause
    exit /b 1
)

echo 🚀 Building Android app with direct Gradle...
echo.

REM Build the app directly with gradle command
gradle assembleDebug --console=plain

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build successful! APK created:
    if exist "app\build\outputs\apk\debug\app-debug.apk" (
        dir "app\build\outputs\apk\debug\app-debug.apk"
        echo.
        echo 📱 Phase 2A implementation ready for testing!
    ) else (
        echo ⚠️  APK file not found at expected location
    )
) else (
    echo.
    echo ❌ Build failed with error code %ERRORLEVEL%
    echo Check the output above for details
)

echo.
echo 🏁 Build complete.
pause
