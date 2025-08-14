# 🤖 Android Termux Streaming TTS Test Guide

## 📱 **NEW APK Ready: `llmytranslate-termux-streaming-test.apk`**

### ✅ **What's Updated:**
- ✅ Direct Termux Ollama integration (`127.0.0.1:11434`)
- ✅ Enhanced streaming TTS with real-time chunks
- ✅ Localhost discovery for Termux services
- ✅ Optimized connection handling for Android ↔ Termux

---

## 🚀 **Quick Test Steps:**

### 1. **Install the New APK**
```bash
# On your Android, install the updated APK
adb install llmytranslate-termux-streaming-test.apk
# OR transfer and install manually
```

### 2. **Make Sure Termux Ollama is Running**
```bash
# In Termux on your phone:
ollama serve

# In another Termux session:
ollama run gemma2:2b
```

### 3. **Test Streaming TTS**
1. Open the updated LLMyTranslate Android app
2. Look for "🚀 Native mode enabled - Termux Ollama connected" message
3. Type any message and watch for real-time streaming TTS!

---

## 🎯 **What to Test:**

### ✅ **Connection Test:**
- App should auto-detect Termux Ollama at `127.0.0.1:11434`
- Should show "Termux Ollama connected" in status

### ✅ **Streaming TTS Test:**
- Send message: "Hello! Testing streaming TTS."
- Watch for: **Text appears + Voice speaks simultaneously**
- Listen for: **AI speaking as it thinks** (not waiting for complete response)

### ✅ **Real-time Performance:**
- Messages should start playing audio within 1-2 seconds
- Audio should continue streaming while text builds up
- Should hear natural speech flow

---

## 🐛 **Troubleshooting:**

### If "Native mode" doesn't connect:
```bash
# In Termux, check Ollama is accessible:
curl http://127.0.0.1:11434/api/version

# Should return: {"version":"0.10.1"}
```

### If streaming TTS doesn't work:
1. Check app logs for "WebSocket connected" messages
2. Try toggling TTS on/off in app settings
3. Restart both Termux and Android app

### If audio doesn't play:
1. Check Android volume settings
2. Try different TTS voices in Android settings
3. Enable "streaming TTS" toggle in app

---

## 📊 **Expected Results:**

✅ **SUCCESS INDICATORS:**
- "🚀 Native mode enabled" message on app start
- Real-time text + audio streaming
- Sub-2-second response times
- Continuous audio flow (not choppy)

❌ **FAILURE INDICATORS:**
- "🌐 Web mode" (means Termux not detected)
- Audio only after complete text
- Long delays (>5 seconds)
- Choppy or broken audio

---

## 🎉 **This Test Proves:**

1. **Android ↔ Termux Integration** ✅
2. **Streaming TTS Infrastructure** ✅  
3. **Real-time AI Conversations** ✅
4. **Native Performance** ✅

---

**Ready to test! Install the APK and let's see streaming TTS in action! 🎵**
