# LLMyTranslate React Native App

A cross-platform mobile app for LLMyTranslate built with React Native.

## Prerequisites

- Node.js 18+ 
- React Native CLI or Expo CLI
- For iOS: Xcode (Mac only)
- For Android: Android Studio

## Quick Start

```bash
# Install dependencies
npm install

# iOS (Mac only)
npx react-native run-ios

# Android
npx react-native run-android

# Or with Expo
expo start
```

## Features

- 🌐 Real-time translation
- 🎤 Voice chat integration  
- 📱 Native mobile UI
- 🔄 WebSocket connection to FastAPI backend
- 🎯 Cross-platform compatibility

## Backend Integration

Connects to your FastAPI backend at:
- Local: `http://localhost:8000`
- Remote: Configurable endpoint

## Project Structure

```
src/
├── components/     # Reusable components
├── screens/        # App screens
├── services/       # API and WebSocket services
├── hooks/          # Custom React hooks
├── types/          # TypeScript types
└── utils/          # Utility functions
```

## API Integration

Uses the same endpoints as your web interface:
- `/api/optimized/translate` - Translation
- `/api/chat/message` - Chat messages
- `/api/tts/synthesize` - Text-to-speech
- WebSocket for real-time communication
