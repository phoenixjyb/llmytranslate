# LLMyTranslate Android App

A native Android application for Samsung S24 Ultra that integrates with the LLMyTranslate server infrastructure to provide real-time text and voice translation conversations.

## Features

### Phase 1 (Current Implementation)
- ✅ **Text Chat Interface**: Material Design 3 UI with message bubbles
- ✅ **WebSocket Communication**: Real-time text messaging with server
- ✅ **Native Architecture**: Optimized for Samsung S24 Ultra
- ✅ **Settings Screen**: Server configuration and audio preferences
- ✅ **Navigation**: Clean navigation between chat, voice, and settings

### Phase 2 (Coming Soon)
- 🔄 **Native Speech Recognition**: On-device STT for ultra-low latency
- 🔄 **Samsung Neural TTS**: High-quality voice synthesis
- 🔄 **Real-time Voice Chat**: Interrupt-capable voice conversations
- 🔄 **Local Ollama Integration**: Direct communication with Termux Ollama

## Prerequisites

### Development Environment (Windows & Mac Compatible)
- **Android Studio**: Latest version (Hedgehog 2023.1.1 or newer)
  - **Windows**: Download from [developer.android.com](https://developer.android.com/studio)
  - **Mac**: Available for Intel and Apple Silicon (M1/M2/M3)
- **Android SDK**: API level 34 (Android 14)
- **Kotlin**: 1.9.0+ (bundled with Android Studio)
- **Gradle**: 8.0+ (bundled with Android Studio)
- **Java**: JDK 11 or higher (bundled with Android Studio)

### Target Device
- **Samsung Galaxy S24 Ultra** (recommended)
- **Android 14+**
- **Termux** with Ollama and gemma2:2b model (for local AI)

### Server Requirements
- LLMyTranslate server running with Android API routes
- WebSocket endpoint accessible from device
- Network connectivity between phone and server

## Setup Instructions

### 1. Install Android Studio

#### Windows:
```powershell
# Download Android Studio from developer.android.com
# Run the installer and follow the setup wizard
# Android Studio will automatically install:
# - Android SDK
# - Platform tools (ADB)
# - Emulator
# - Kotlin plugin
```

#### Mac:
```bash
# Download Android Studio from developer.android.com
# For Intel Macs: android-studio-ide-*-mac.dmg
# For Apple Silicon: android-studio-ide-*-mac_arm.dmg
# Drag to Applications folder and run setup wizard
```

### 2. Clone and Open Project
```bash
# The android/ folder is already in your LLMyTranslate workspace
cd /path/to/llmytranslate/android
```

Open the `android` folder in Android Studio as a project.

### 3. Sync Dependencies

#### Windows (PowerShell):
```powershell
# In Android Studio terminal or command line
.\gradlew.bat sync
```

#### Mac/Linux (Terminal):
```bash
# In Android Studio terminal or command line
./gradlew sync
```

### 3. Configure Server Connection
Update the server URL in the settings or modify the default in `SettingsScreen.kt`:
```kotlin
var serverUrl by remember { mutableStateOf("ws://YOUR_SERVER_IP:8080") }
```

### 4. Build and Install

#### Windows (PowerShell):
```powershell
# Build debug APK
.\gradlew.bat assembleDebug

# Install on connected device
.\gradlew.bat installDebug

# Or build and install in one step
.\gradlew.bat build installDebug

# Using the provided build script
..\build-android.ps1 build -Install -Clean
```

#### Mac/Linux (Terminal):
```bash
# Build debug APK
./gradlew assembleDebug

# Install on connected device
./gradlew installDebug

# Or build and install in one step
./gradlew build installDebug
```

## Project Structure

```
android/
├── app/                          # Main application module
│   ├── src/main/
│   │   ├── java/com/llmytranslate/android/
│   │   │   ├── MainActivity.kt                # Main app entry
│   │   │   ├── ui/
│   │   │   │   ├── chat/                     # Chat fragment and UI
│   │   │   │   ├── voice/                    # Voice call fragment
│   │   │   │   ├── settings/                 # Settings fragment
│   │   │   │   └── components/               # Reusable UI components
│   │   │   ├── services/
│   │   │   │   ├── WebSocketService.kt       # WebSocket connection
│   │   │   │   ├── AudioService.kt           # Audio recording/playback
│   │   │   │   ├── STTService.kt            # Android Speech Recognition
│   │   │   │   └── TTSService.kt            # Android Text-to-Speech
│   │   │   ├── utils/
│   │   │   │   ├── NetworkManager.kt         # Network discovery
│   │   │   │   ├── PermissionManager.kt      # Runtime permissions
│   │   │   │   └── AudioProcessor.kt         # Audio processing
│   │   │   ├── models/
│   │   │   │   ├── Message.kt               # Chat message model
│   │   │   │   ├── Session.kt               # Call session model
│   │   │   │   └── Settings.kt              # App settings model
│   │   │   └── repository/
│   │   │       ├── ChatRepository.kt         # Chat data management
│   │   │       └── SettingsRepository.kt     # Settings persistence
│   │   ├── res/                             # Resources (layouts, strings, etc.)
│   │   └── AndroidManifest.xml              # App manifest
│   ├── build.gradle.kts                     # Module build configuration
│   └── proguard-rules.pro                   # ProGuard configuration
├── gradle/                                  # Gradle wrapper
├── build.gradle.kts                         # Project build configuration
├── settings.gradle.kts                      # Project settings
├── local.properties                         # Local SDK paths
└── README.md                               # This file
```

## Features

### Phase 1: Core Features
- [x] WebSocket connection to LLMyTranslate server
- [x] Text-based chat functionality
- [x] Network discovery for automatic server connection
- [x] Basic Material Design 3 UI

### Phase 2: Native Audio (In Progress)
- [ ] Native Android STT integration
- [ ] Native Android TTS integration
- [ ] Real-time voice conversation
- [ ] Audio recording and playback

### Phase 3: Advanced Features (Planned)
- [ ] Conversation history persistence
- [ ] Kid-friendly mode with parental controls
- [ ] Multiple language support
- [ ] Offline mode capabilities

### Phase 4: Termux Integration (Planned)
- [ ] Direct Termux API integration
- [ ] Local-only mode (bypass server)
- [ ] Enhanced privacy features
- [ ] Battery optimization

## Technical Specifications

### Minimum Requirements
- Android 8.0 (API 26) or higher
- 2GB RAM
- Network connectivity (WiFi or cellular)
- Microphone and speaker permissions

### Optimized For
- Samsung S24 Ultra (Android 14, API 34)
- Samsung Neural TTS voices
- On-device speech recognition
- High-resolution displays

### Dependencies
- Kotlin 1.9+
- Jetpack Compose (UI)
- OkHttp (networking)
- WebSocket support
- Android Speech API
- Android TextToSpeech API
- Hilt (dependency injection)
- Room (local database)

## Development Setup

### Prerequisites (Cross-Platform)
1. **Install Android Studio** (latest stable)
   - **Windows**: Download from developer.android.com
   - **Mac**: Available for Intel and Apple Silicon
2. **Install Android SDK API 34+** (included with Android Studio)
3. **Ensure your LLMyTranslate server is running**
4. **Connect Samsung S24 Ultra via USB debugging**

### Platform-Specific Build Instructions

#### Windows (PowerShell):
```powershell
# Connect device and check
adb devices

# Build and install using gradlew
.\gradlew.bat installDebug

# Or use the PowerShell build script
..\build-android.ps1 build -Install -Clean
```

#### Mac (Terminal):
```bash
# Connect device and check
adb devices

# Build and install using gradlew
./gradlew installDebug

# Or use the bash build script
chmod +x ../build-android.sh
../build-android.sh build --install --clean
```

### Build Instructions
```bash
# Clone the project (if not already done)
cd llmytranslate/android

# Build debug APK
./gradlew assembleDebug

# Install to connected device
./gradlew installDebug

# Run tests
./gradlew test
```

### Server Configuration
The app will automatically discover your LLMyTranslate server on the local network. Ensure:
1. Server is running on port 8000 (default)
2. Android device is on the same WiFi network
3. Firewall allows connections to port 8000

## Architecture

### Data Flow
```
User Speech → Android STT → WebSocket → LLMyTranslate Server → Termux Ollama → AI Response → WebSocket → Android TTS → Audio Output
```

### Key Components
1. **WebSocketService**: Manages real-time communication with server
2. **STTService**: Handles native Android speech recognition
3. **TTSService**: Manages Android text-to-speech synthesis
4. **NetworkManager**: Discovers and connects to LLMyTranslate server
5. **ChatRepository**: Manages conversation data and persistence

## Performance Optimizations

### Network Optimization
- Text-only WebSocket communication (no audio streaming)
- Automatic reconnection with exponential backoff
- Local server discovery to minimize latency

### Audio Optimization
- Native Android STT (faster than server-side processing)
- Samsung Neural TTS voices (high quality, low latency)
- On-device processing (no network dependency for audio)

### Battery Optimization
- Efficient WebSocket connection management
- Background processing limits
- Audio recording only when needed

## Privacy Features

### Local Processing
- Speech recognition on-device (Samsung S24 Ultra)
- Text-to-speech on-device
- No audio data transmitted over network

### Data Protection
- Conversations stored locally only
- Optional server-side chat history
- No cloud dependencies

## Configuration

### Default Settings
```json
{
  "server_discovery": true,
  "auto_connect": true,
  "language": "en-US",
  "voice_speed": 1.0,
  "kid_friendly": false,
  "native_stt": true,
  "native_tts": true,
  "conversation_history": true
}
```

### Customization Options
- Server IP address (manual configuration)
- Language preferences (English, Chinese, Spanish, etc.)
- Voice settings (speed, pitch, voice selection)
- Kid-friendly mode toggle
- Audio quality settings

## Testing

### Unit Tests
- Service layer testing
- Network communication testing
- Audio processing testing

### Integration Tests
- End-to-end conversation flow
- Server communication testing
- Audio pipeline testing

### Device Testing
- Samsung S24 Ultra specific features
- Cross-device compatibility
- Performance benchmarking

## Deployment

### Debug Build
For development and testing on Samsung S24 Ultra.

### Release Build
Production-ready APK with:
- Code obfuscation
- Resource optimization
- Signed with release key

### Distribution
- Direct APK installation
- Potential Google Play Store distribution
- Enterprise/internal distribution

## Troubleshooting

### Common Issues
1. **Server not found**: Check WiFi connection and firewall
2. **Audio not working**: Verify microphone permissions
3. **Connection drops**: Check network stability
4. **Slow responses**: Verify Termux Ollama is running

### Debug Tools
- In-app network diagnostics
- Connection status indicators
- Performance monitoring
- Log export functionality

---

**Status**: Phase 1 Implementation  
**Last Updated**: August 1, 2025  
**Target Device**: Samsung S24 Ultra  
**Integration**: LLMyTranslate Server + Termux Ollama
