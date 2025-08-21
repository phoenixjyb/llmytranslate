# Command-Line Android APK Building Guide

## ✅ **Yes! You can build Android APK without Android Studio**

The Android project is set up with **Gradle Wrapper** which allows building from command line using just the Android SDK and Java.

## 🛠️ Prerequisites

### 1. **Java Development Kit (JDK)**
```powershell
# Windows - Download and install OpenJDK 11 or 17
# From: https://adoptium.net/temurin/releases/

# After installation, set JAVA_HOME
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.8.101-hotspot"
$env:PATH += ";$env:JAVA_HOME\bin"

# Verify Java installation
java -version
javac -version
```

### 2. **Android SDK (Command Line Tools)**
```powershell
# Windows - Download Android Command Line Tools
# From: https://developer.android.com/studio#command-tools

# Extract to: C:\Android\cmdline-tools\latest\
# Set environment variables
$env:ANDROID_HOME = "C:\Android"
$env:PATH += ";$env:ANDROID_HOME\cmdline-tools\latest\bin"
$env:PATH += ";$env:ANDROID_HOME\platform-tools"

# Install required SDK components
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

## 🚀 Building APK (Command Line Only)

### Windows Commands:
```powershell
# Navigate to Android project
cd c:\Users\yanbo\wSpace\llmytranslate\android

# Build debug APK
.\gradlew.bat assembleDebug

# Build release APK (requires signing setup)
.\gradlew.bat assembleRelease

# Clean and rebuild
.\gradlew.bat clean assembleDebug

# Install on connected device
.\gradlew.bat installDebug

# List all available tasks
.\gradlew.bat tasks
```

### Mac/Linux Commands:
```bash
# Navigate to Android project
cd /path/to/llmytranslate/android

# Make gradlew executable
chmod +x gradlew

# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Clean and rebuild
./gradlew clean assembleDebug

# Install on connected device
./gradlew installDebug
```

## 📱 Using the Build Scripts

### Windows (PowerShell):
```powershell
# Use the provided build script
.\build-android.ps1 build -Clean

# Build and install in one command
.\build-android.ps1 build -Install -Clean

# Build release version
.\build-android.ps1 build -Release

# Check connected devices
.\build-android.ps1 devices
```

### Mac/Linux (Bash):
```bash
# Use the provided build script
./build-android.sh build --clean

# Build and install in one command
./build-android.sh build --install --clean

# Build release version
./build-android.sh build --release

# Check connected devices
./build-android.sh devices
```

## 📦 Output Locations

After successful build, APK files will be located at:

```
android/app/build/outputs/apk/
├── debug/
│   └── app-debug.apk           # Debug version for testing
└── release/
    └── app-release.apk         # Release version (requires signing)
```

## 🔧 Device Installation

### Connect Samsung S24 Ultra:
1. **Enable Developer Options**:
   - Settings → About phone → Tap "Build number" 7 times
   - Settings → Developer options → Enable "USB debugging"

2. **Install APK**:
```powershell
# Windows
adb devices                      # Verify device connection
adb install app\build\outputs\apk\debug\app-debug.apk

# Or use Gradle
.\gradlew.bat installDebug
```

## 🚫 **No Android Studio Required!**

### What You Get:
- ✅ **Full APK building** using Gradle command line
- ✅ **Device installation** via ADB
- ✅ **Debug and release builds**
- ✅ **Automated build scripts**
- ✅ **Dependency management**
- ✅ **Code compilation and packaging**

### What You Don't Need:
- ❌ Android Studio IDE
- ❌ Large IDE download (3GB+)
- ❌ GUI interface
- ❌ IDE-specific configurations

## 🎯 Complete Workflow Example

### 1. **Setup Environment** (One-time):
```powershell
# Install Java JDK 17
# Install Android SDK command line tools
# Set environment variables (JAVA_HOME, ANDROID_HOME)
# Accept SDK licenses: sdkmanager --licenses
```

### 2. **Build and Test** (Daily workflow):
```powershell
# Start LLMyTranslate server
.\start-service.ps1

# Build and install Android app
.\build-android.ps1 build -Install -Clean

# Test on Samsung S24 Ultra
# (App connects to server automatically)
```

### 3. **Development Iteration**:
```powershell
# Make code changes to Android app
# (Edit .kt files in android/app/src/main/java/...)

# Quick rebuild and install
.\gradlew.bat installDebug

# Test changes on device
```

## 🔍 Troubleshooting

### Common Issues:

#### **"JAVA_HOME not set"**:
```powershell
# Set Java path
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.8.101-hotspot"
java -version  # Should show Java 11 or 17
```

#### **"SDK not found"**:
```powershell
# Set Android SDK path
$env:ANDROID_HOME = "C:\Android"
$env:PATH += ";$env:ANDROID_HOME\platform-tools"
adb version  # Should show ADB version
```

#### **"Build failed"**:
```powershell
# Clean and retry
.\gradlew.bat clean
.\gradlew.bat assembleDebug --info
```

#### **"Device not found"**:
```powershell
# Check USB debugging
adb devices
# Should show: <device_id>    device
```

## 🎉 **Bottom Line**

**You can build, install, and test the Android app entirely from command line!**

- **Faster**: No need to load heavy IDE
- **Automated**: Use provided build scripts
- **Flexible**: Build from any terminal/CI system
- **Lightweight**: Only install what you need

The Android project is fully configured for command-line building with Gradle Wrapper. Just install Java + Android SDK, and you're ready to build! 🚀
