# 🔍 Termux Connection Debug Guide

## 📱 **New Debug APK: `llmytranslate-termux-debug.apk`**

### ❌ **Issue:** "Native process failed, using web fallback"

This means your Android app can't connect to the Ollama server in Termux at `127.0.0.1:11434`.

---

## 🔧 **Quick Diagnosis Steps:**

### 1. **Install Debug APK**
```bash
# Install the enhanced debug version
adb install llmytranslate-termux-debug.apk
```

### 2. **Check Termux Ollama Status**
```bash
# In Termux, check if Ollama is running:
curl -v http://127.0.0.1:11434/api/version
curl -v http://localhost:11434/api/version

# Expected response:
# {"version":"0.10.1"}
```

### 3. **Test from Android App**
1. Open the updated app
2. Look for **detailed debug information** in the chat
3. The app will now show:
   - ✅/❌ Network permissions
   - ✅/❌ Each localhost variation tested
   - ✅/❌ Ollama endpoint responses
   - ✅/❌ External connectivity test

---

## 🎯 **What the Debug Will Show:**

### ✅ **Expected Success:**
```
🔍 TERMUX CONNECTION DEBUG
📱 Network Permissions:
   INTERNET: ✅ GRANTED

🌐 Testing Localhost Variations:
   http://127.0.0.1:11434: ✅ SUCCESS (HTTP 200)
   
🤖 Testing Ollama Endpoints:
   http://127.0.0.1:11434/api/version: ✅ {"version":"0.10.1"}
   http://127.0.0.1:11434/api/tags: ✅ 1 models found
```

### ❌ **Common Failures:**

**Ollama Not Running:**
```
   http://127.0.0.1:11434: ❌ CONNECTION REFUSED
```
**Solution:** Run `ollama serve` in Termux

**Network Permission Issue:**
```
📱 Network Permissions:
   INTERNET: ❌ DENIED  
```
**Solution:** Grant internet permission in Android Settings

**Wrong Address:**
```
   http://127.0.0.1:11434: ❌ UNKNOWN HOST
```
**Solution:** Try different localhost addresses

---

## 🚀 **Most Likely Fixes:**

### **Fix 1: Start Ollama in Termux**
```bash
# In Termux:
ollama serve

# Keep this running, then in another Termux session:
ollama run gemma2:2b
```

### **Fix 2: Check Ollama Binding**
```bash
# Make sure Ollama binds to all interfaces, not just localhost
# In Termux:
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### **Fix 3: Test Ollama Accessibility**
```bash
# Test if Ollama responds:
curl http://127.0.0.1:11434/api/version
curl http://localhost:11434/api/version

# Should return: {"version":"0.10.1"}
```

---

## 📊 **What to Report Back:**

After installing the debug APK, tell me:

1. **What the debug output shows** (copy the full debug text from the app)
2. **What happens when you run** `curl http://127.0.0.1:11434/api/version` **in Termux**
3. **Whether Ollama is running** with `ollama serve`

This will help pinpoint exactly why the native connection is failing!

---

**Install the debug APK and share the debug output! 🔍**
