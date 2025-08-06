@echo off
chcp 65001 > nul
echo Starting clean build...

set JAVA_HOME=D:\Program Files\Android\Android Studio\jbr
set PATH=%JAVA_HOME%\bin;%PATH%

echo Checking for gradlew...
if exist gradlew.bat (
    echo Found gradle wrapper
    echo Cleaning project...
    .\gradlew.bat clean
    echo Building debug APK...
    .\gradlew.bat assembleDebug --stacktrace
) else (
    echo No gradle wrapper found
    dir
)
