@echo off
echo Building Android app with online mode to download Kotlin 1.9.0...
gradlew.bat assembleDebug
echo Build completed with exit code: %ERRORLEVEL%
pause
