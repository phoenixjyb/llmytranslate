@echo off
REM Quick Build Script for Phase 2A with Error Handling
chcp 65001 > nul

set "JAVA_HOME=D:\Program Files\Android\Android Studio\jbr"
set "GRADLE_HOME=%~dp0.gradle\wrapper\dists\gradle-8.4-bin\3zae5u3bpga9bvzthql6s3mvp\gradle-8.4"
set "PATH=%JAVA_HOME%\bin;%GRADLE_HOME%\bin;%PATH%"

echo 🔨 Phase 2A Build with Error Details...
echo Using Gradle: %GRADLE_HOME%\bin\gradle.bat

"%GRADLE_HOME%\bin\gradle.bat" assembleDebug --info --stacktrace

if %ERRORLEVEL% EQU 0 (
    echo ✅ Build completed successfully!
    if exist "app\build\outputs\apk\debug\app-debug.apk" (
        echo 📱 APK created: app\build\outputs\apk\debug\app-debug.apk
        dir "app\build\outputs\apk\debug\app-debug.apk"
    )
) else (
    echo ❌ Build failed with errors
    echo Check output above for details
)
