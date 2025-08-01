# 🚀 React Native Development Guide

## Quick Start

### 1. Setup Environment

**Windows (PowerShell):**
```powershell
.\setup-react-native.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x setup-react-native.sh
./setup-react-native.sh
```

### 2. Configure Backend Connection

Edit `src/services/ApiService.ts`:
```typescript
// Update this to your FastAPI backend URL
const BASE_URL = 'http://your-backend-ip:8000';
```

### 3. Run the App

```bash
cd LLMyTranslateApp

# Android (requires Android SDK)
npm run android

# iOS (macOS only, requires Xcode)
npm run ios
```

## 🔧 Environment Requirements

### Android Development
- **Node.js 18+**
- **Android Studio** (for SDK and emulator)
- **Java 11** (not Java 21 - avoid KAPT issues)
- **Android SDK API 33+**

### iOS Development (macOS only)
- **Xcode 14+**
- **CocoaPods**
- **iOS Simulator**

## 📱 App Features

### Translation Screen
- **Real-time translation** between multiple languages
- **Voice input** using device microphone
- **Text-to-speech** output
- **Language detection**

### Chat Screen  
- **AI chat interface** powered by your FastAPI backend
- **Message history**
- **WebSocket support** for real-time responses
- **Voice integration**

## 🔗 Backend Integration

The app connects to your existing FastAPI backend:

- **Translation**: `/api/translate`
- **Chat**: `/api/chat`
- **TTS**: `/api/tts`
- **Language Detection**: `/api/detect-language`

## 🐛 Troubleshooting

### Common Issues

1. **Metro bundler fails to start**
   ```bash
   npx react-native start --reset-cache
   ```

2. **Android build fails**
   - Ensure Java 11 is active (not Java 21)
   - Check Android SDK installation
   - Clean build: `cd android && ./gradlew clean`

3. **iOS build fails**
   - Run `cd ios && pod install`
   - Clean Xcode build folder
   - Check provisioning profiles

4. **Can't connect to backend**
   - Check FastAPI server is running
   - Update API URL in `ApiService.ts`
   - Verify network connectivity

### Development Tips

- Use **React Native Debugger** for debugging
- Enable **Hot Reload** for faster development
- Test on **real devices** for best performance
- Use **Flipper** for network inspection

## 🚀 Why React Native?

Compared to native Android (Kotlin):

✅ **Cross-platform** - Single codebase for iOS + Android  
✅ **No Java/KAPT issues** - JavaScript/TypeScript only  
✅ **Faster development** - Hot reload, shared logic  
✅ **Mature ecosystem** - Extensive library support  
✅ **Easier debugging** - Chrome DevTools integration  

## 📦 Project Structure

```
LLMyTranslateApp/
├── src/
│   ├── services/
│   │   └── ApiService.ts      # FastAPI backend integration
│   ├── screens/
│   │   ├── TranslateScreen.tsx # Translation interface
│   │   └── ChatScreen.tsx     # Chat interface
│   └── types/
│       └── index.ts           # TypeScript definitions
├── App.tsx                    # Main app with navigation
└── package.json              # Dependencies and scripts
```

## 🔄 Next Steps

1. **Initialize** the React Native project
2. **Test** on Android emulator/device
3. **Configure** backend connection
4. **Customize** UI/UX as needed
5. **Build** release APK for distribution

This approach avoids all the Java 21 + KAPT compatibility issues while providing a modern cross-platform mobile solution! 🎉
