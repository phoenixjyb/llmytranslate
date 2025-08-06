@echo off
chcp 65001 > nul
echo Starting clean build...

set JAVA_HOME=C:\Program Files\Android\Android Studio\jbr
set GRADLE_HOME=C:\Users\yanbo\Downloads\gradle-8.4
set PATH=%GRADLE_HOME%\bin;%JAVA_HOME%\bin;%PATH%

echo Java Version:
java -version

echo Gradle Version:
gradle -version

echo Cleaning project...
gradle clean

echo Building with stacktrace...
gradle assembleDebug --stacktrace
