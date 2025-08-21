# Cross-Platform Android Development Guide

## 🌍 Platform Compatibility

The LLMyTranslate Android app can be developed on **both Windows and Mac** environments. Android Studio is fully cross-platform and provides identical functionality across operating systems.

## 🖥️ Windows Development Setup

### Prerequisites
- **Windows 10/11** (64-bit)
- **8GB RAM minimum** (16GB recommended)
- **4GB disk space** for Android Studio + SDK

### Installation Steps
1. **Download Android Studio**
   - Visit [developer.android.com/studio](https://developer.android.com/studio)
   - Download "Android Studio for Windows"
   - Run the `.exe` installer

2. **Android Studio Setup Wizard**
   - Choose "Standard" installation
   - Allow it to download Android SDK, platform tools, and emulator
   - SDK will install to: `%LOCALAPPDATA%\Android\Sdk`

3. **Configure SDK**
   - Open SDK Manager in Android Studio
   - Install "Android 14 (API 34)" platform
   - Install "Android SDK Build-Tools 34.0.0"

### Windows-Specific Commands
```powershell
# Navigate to project
cd C:\Users\yanbo\wSpace\llmytranslate\android

# Build project
.\gradlew.bat assembleDebug

# Install on device
.\gradlew.bat installDebug

# Use build script
..\build-android.ps1 build -Install -Clean
```

## 🍎 Mac Development Setup

### Prerequisites
- **macOS 10.14+** (macOS 12+ recommended)
- **8GB RAM minimum** (16GB recommended for M1/M2 Macs)
- **4GB disk space** for Android Studio + SDK

### Installation Steps
1. **Download Android Studio**
   - Visit [developer.android.com/studio](https://developer.android.com/studio)
   - **Intel Macs**: Download standard Mac version
   - **Apple Silicon (M1/M2/M3)**: Download Apple Silicon version
   - Open the `.dmg` file and drag to Applications

2. **Android Studio Setup Wizard**
   - Choose "Standard" installation
   - Allow it to download Android SDK, platform tools, and emulator
   - SDK will install to: `~/Library/Android/sdk`

3. **Configure SDK**
   - Open SDK Manager in Android Studio
   - Install "Android 14 (API 34)" platform
   - Install "Android SDK Build-Tools 34.0.0"

### Mac-Specific Commands
```bash
# Navigate to project
cd /path/to/llmytranslate/android

# Build project
./gradlew assembleDebug

# Install on device
./gradlew installDebug

# Use build script (make executable first)
chmod +x ../build-android.sh
../build-android.sh build --install --clean
```

## 🔧 Common Setup Tasks (Both Platforms)

### 1. Enable Developer Options on Samsung S24 Ultra
1. Go to **Settings** → **About phone**
2. Tap **Build number** 7 times
3. Go back to **Settings** → **Developer options**
4. Enable **USB debugging**
5. Enable **Stay awake**

### 2. Connect Device
```bash
# Check if device is recognized (both platforms)
adb devices

# Should show:
# List of devices attached
# <device_id>    device
```

### 3. First Build Test
1. Open Android Studio
2. Open the `android/` folder as a project
3. Wait for Gradle sync to complete
4. Click the green "Run" button or use keyboard shortcut:
   - **Windows**: Ctrl+R
   - **Mac**: Cmd+R

## 🔄 Cross-Platform File Structure

The Android project structure is identical on both platforms:

```
android/
├── app/
│   ├── build.gradle.kts         # Works on both platforms
│   ├── src/main/AndroidManifest.xml
│   └── src/main/java/com/llmytranslate/android/
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
├── gradlew                      # For Mac/Linux
├── gradlew.bat                  # For Windows
└── build.gradle.kts
```

## 🚀 Build Scripts

### Windows (PowerShell)
Use `build-android.ps1`:
```powershell
# Basic build
.\build-android.ps1 build

# Build and install with clean
.\build-android.ps1 build -Install -Clean

# Release build
.\build-android.ps1 build -Release
```

### Mac (Bash)
Use `build-android.sh`:
```bash
# Basic build
./build-android.sh build

# Build and install with clean
./build-android.sh build --install --clean

# Release build
./build-android.sh build --release
```

## 💡 Development Tips

### Both Platforms
- **Use Android Studio's built-in terminal** for consistent command experience
- **Gradle wrapper** ensures same build environment regardless of platform
- **Source control** works identically (Git, etc.)
- **Debugging tools** are platform-agnostic

### Windows-Specific
- Use **PowerShell** (not Command Prompt) for better Unicode support
- **Windows Defender** may slow builds - add exclusion for project folder
- **File paths** use backslashes but Gradle handles this automatically

### Mac-Specific
- **Apple Silicon Macs** run Android emulator much faster
- **Spotlight** can interfere with builds - add project to exclusions
- **File paths** use forward slashes natively

## 🐛 Troubleshooting

### Common Issues (Both Platforms)
```bash
# Clear Gradle cache
./gradlew clean

# Refresh dependencies
./gradlew --refresh-dependencies

# Check connected devices
adb devices
```

### Windows-Specific Issues
```powershell
# If gradlew.bat doesn't work
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Check Java version
java -version
```

### Mac-Specific Issues
```bash
# If permission denied on gradlew
chmod +x gradlew

# Check Java version
java -version

# For M1/M2 Macs with Rosetta issues
arch -arm64 ./gradlew assembleDebug
```

## 📱 Samsung S24 Ultra Specific

### Features Available on Both Development Platforms
- **USB Debugging** works identically
- **ADB commands** are cross-platform
- **Samsung TTS** testing works on both
- **Performance profiling** available in Android Studio

### Testing Commands
```bash
# Test TTS (both platforms)
adb shell am start -a android.speech.tts.engine.INSTALL_TTS_DATA

# Check Samsung TTS
adb shell dumpsys tts

# Monitor app logs
adb logcat | grep LLMyTranslate
```

## ✅ Verification Checklist

After setup on either platform:
- [ ] Android Studio opens without errors
- [ ] SDK Manager shows Android 14 (API 34) installed
- [ ] `adb devices` shows Samsung S24 Ultra
- [ ] Project syncs successfully in Android Studio
- [ ] Build script runs without errors
- [ ] App installs and launches on device

---

**Bottom Line**: Choose the platform you're most comfortable with. The Android development experience is identical on Windows and Mac, and you can even switch between platforms during development if needed!

## 🔄 Cross-Platform Development Workflow

### Complete Development Session

#### Windows Development:
```powershell
# 1. Start LLMyTranslate backend service
.\start-service.ps1 -Debug

# 2. Open Android Studio and import android/ project
# 3. Connect Samsung S24 Ultra via USB

# 4. Build and install Android app
.\build-android.ps1 build -Install -Clean

# 5. Monitor service in another terminal
.\scripts\service-status.ps1 -Continuous

# 6. Test app connection
# Open app on phone, verify WebSocket connection to http://<YOUR_IP>:8000

# 7. Stop services when done
.\stop-service.ps1
```

#### Mac Development:
```bash
# 1. Start LLMyTranslate backend service
./start-service.sh --debug

# 2. Open Android Studio and import android/ project
# 3. Connect Samsung S24 Ultra via USB

# 4. Build and install Android app
chmod +x ./build-android.sh
./build-android.sh build --install --clean

# 5. Monitor service in another terminal
./scripts/service-status.sh --continuous

# 6. Test app connection
# Open app on phone, verify WebSocket connection to http://<YOUR_IP>:8000

# 7. Stop services when done
./stop-service.sh
```

### Service Integration

Both platforms provide identical backend service functionality:

#### Backend Service Features:
- **WebSocket Communication**: Real-time messaging with Android app
- **Android API Routes**: Optimized endpoints for mobile communication
- **Phase 4 Components**: Optimized LLM, performance monitoring, quality control
- **Cross-Platform**: Identical functionality on Windows, macOS, Linux

#### Network Configuration:
- **Local Access**: `http://localhost:8000`
- **Network Access**: `http://<DEV_MACHINE_IP>:8000`
- **Android WebSocket**: `ws://<DEV_MACHINE_IP>:8000/api/android/stream`

### Development Tips

#### Both Platforms:
1. **Keep service running** during Android development for real-time testing
2. **Use service monitoring** to see Android app connections in real-time
3. **Check network connectivity** between development machine and Samsung S24 Ultra
4. **Update Android app settings** with correct server IP address

#### Platform-Specific Advantages:

**Windows Development**:
- Great Samsung device integration (many Samsung tools are Windows-first)
- PowerShell provides excellent automation capabilities
- Easy integration with existing Windows development workflows

**Mac Development**:
- Apple Silicon Macs run Android emulator incredibly fast
- Unix-based environment familiar to many developers
- Excellent for cross-platform mobile development workflows

### Quick Verification Checklist

After setting up on either platform:
- [ ] LLMyTranslate service starts without errors
- [ ] Service responds to `http://localhost:8000/api/health`
- [ ] Android Studio builds project successfully
- [ ] Samsung S24 Ultra shows up in `adb devices`
- [ ] Android app installs and launches on device
- [ ] App successfully connects to WebSocket server
- [ ] Real-time messaging works between app and service

### Troubleshooting Cross-Platform Issues

#### Service Connection Problems:
```bash
# Check if service is accessible from network
curl http://<DEV_MACHINE_IP>:8000/api/health

# Verify firewall allows port 8000
# Windows: Check Windows Firewall settings
# Mac: Check System Preferences > Security & Privacy > Firewall
```

#### Android Build Issues:
```bash
# Clear all caches and rebuild
# Windows: .\build-android.ps1 clean; .\build-android.ps1 build
# Mac: ./build-android.sh clean; ./build-android.sh build

# Check Android SDK installation in Android Studio
# Tools > SDK Manager > verify Android 14 (API 34) is installed
```

#### Network Connectivity:
```bash
# Ensure phone and development machine are on same network
# Check IP addresses match the expected range
# Test connectivity: ping <DEV_MACHINE_IP> from phone's browser
```
