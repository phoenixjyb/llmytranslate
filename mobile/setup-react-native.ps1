# 📱 LLMyTranslate React Native Setup

echo "🚀 Setting up LLMyTranslate React Native App"

# Check if we're in the right directory
if (!(Test-Path "../src/main.py")) {
    Write-Host "❌ Please run this script from the mobile directory within your LLMyTranslate project" -ForegroundColor Red
    exit 1
}

Write-Host "📱 Initializing React Native project..." -ForegroundColor Green

# Create React Native project
npx @react-native-community/cli@latest init LLMyTranslateApp --template react-native-template-typescript

Write-Host "📦 Installing additional dependencies..." -ForegroundColor Green

Set-Location LLMyTranslateApp

# Install navigation
npm install @react-navigation/native @react-navigation/bottom-tabs @react-navigation/stack
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler

# Install other dependencies
npm install @react-native-async-storage/async-storage
npm install react-native-vector-icons
npm install react-native-permissions
npm install react-native-config

Write-Host "📋 Copying custom files..." -ForegroundColor Green

# Copy our custom files
Copy-Item ../App.tsx ./App.tsx -Force
Copy-Item -Path ../src -Destination ./ -Recurse -Force

Write-Host "✅ React Native setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Yellow
Write-Host "1. cd LLMyTranslateApp"
Write-Host "2. Update src/services/ApiService.ts with your backend URL"
Write-Host "3. Run 'npm run android' (requires Android SDK)"
Write-Host ""
Write-Host "📱 For development:" -ForegroundColor Cyan
Write-Host "- Make sure your FastAPI backend is running"
Write-Host "- Update the API endpoint in ApiService.ts"
Write-Host "- Test on device/emulator"
Write-Host ""
Write-Host "🔧 Troubleshooting:" -ForegroundColor Magenta
Write-Host "- If Android build fails, ensure Java 11 is used (not Java 21)"
Write-Host "- For iOS builds, you need macOS and Xcode"
Write-Host "- Check React Native environment setup guide if issues persist"
