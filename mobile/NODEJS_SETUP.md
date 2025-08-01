# 📦 Manual Node.js Setup Guide

## 🚨 Node.js Required for React Native

Your system needs Node.js to run React Native. Here are the installation options:

### Option 1: Download from Official Site (Recommended)

1. **Visit**: https://nodejs.org/
2. **Download**: LTS version (currently 20.x)
3. **Install**: Run the .msi installer
4. **Restart**: PowerShell after installation

### Option 2: Use Chocolatey (Admin Required)

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
choco install nodejs-lts -y
```

### Option 3: Use Winget (Windows 10+)

```powershell
winget install OpenJS.NodeJS
```

## ✅ Verify Installation

After installing Node.js, restart PowerShell and check:

```powershell
node --version   # Should show v20.x.x
npm --version    # Should show 10.x.x
```

## 🚀 Continue React Native Setup

Once Node.js is installed:

```powershell
cd "C:\Users\yanbo\wSpace\llmytranslate\mobile"
.\setup-react-native.ps1
```

## 🔧 Alternative: Use Expo CLI (Simpler)

If you prefer a simpler setup without complex native dependencies:

```powershell
npm install -g @expo/cli
expo init LLMyTranslateApp --template typescript
```

This avoids Android SDK setup entirely and uses Expo's managed workflow.

## 🎯 Why React Native is Better for Your Use Case

Compared to the Kotlin/KAPT issues you were facing:

✅ **No Java version conflicts**  
✅ **Cross-platform (iOS + Android)**  
✅ **JavaScript/TypeScript only**  
✅ **Faster development cycle**  
✅ **Better debugging tools**  
✅ **Huge community support**

Your FastAPI backend integration will work seamlessly with React Native! 🚀
