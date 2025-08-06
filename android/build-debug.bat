@echo off
echo Building Android app with detailed output...
gradlew.bat assembleDebug --offline --info
echo Build completed with exit code: %ERRORLEVEL%
pause
