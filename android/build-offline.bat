@echo off
echo Building Android app with Gradle wrapper in offline mode...
gradlew.bat assembleDebug --offline
echo Build completed with exit code: %ERRORLEVEL%
pause
