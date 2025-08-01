#!/bin/bash

echo "🚀 Setting up LLMyTranslate React Native App"

# Check if we're in the right directory
if [ ! -f "../src/main.py" ]; then
    echo "❌ Please run this script from the mobile directory within your LLMyTranslate project"
    exit 1
fi

echo "📱 Initializing React Native project..."

# Create React Native project
npx @react-native-community/cli@latest init LLMyTranslateApp --template react-native-template-typescript

echo "📦 Installing additional dependencies..."

cd LLMyTranslateApp

# Install navigation
npm install @react-navigation/native @react-navigation/bottom-tabs @react-navigation/stack
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler

# Install other dependencies
npm install @react-native-async-storage/async-storage
npm install react-native-vector-icons
npm install react-native-permissions
npm install react-native-config

# iOS specific setup
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Setting up iOS dependencies..."
    cd ios
    pod install
    cd ..
fi

echo "📋 Copying custom files..."

# Copy our custom files
cp ../App.tsx ./App.tsx
cp -r ../src ./src

echo "✅ React Native setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. cd LLMyTranslateApp"
echo "2. Update src/services/ApiService.ts with your backend URL"
echo "3. Run 'npm run android' or 'npm run ios'"
echo ""
echo "📱 For development:"
echo "- Make sure your FastAPI backend is running"
echo "- Update the API endpoint in ApiService.ts"
echo "- Test on device/emulator"
